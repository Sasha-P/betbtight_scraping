from collections import OrderedDict

import scrapy


TODAY = 'today'


class BetBrightSpiderXPath(scrapy.Spider):
    name = 'betbright-xpath'
    start_urls = [
        'https://www.betbright.com/',
    ]

    def parse(self, response):
        for href in response.xpath('//a[@class="horse-racing"]/@href').extract():
            yield scrapy.Request(response.urljoin(href), callback=self.parse_horse_racing)

    def parse_horse_racing(self, response):
        for href in response.xpath('//li[@class="opened_menu"]/ul/li/a/@href').extract():
            if TODAY in href:
                yield scrapy.Request(response.urljoin(href), callback=self.parse_horse_racing_today)

    def parse_horse_racing_today(self, response):
        for href in response.xpath('//li[@class="opened_menu"]/ul/li/a/@href').extract():
            if TODAY in href and not href.endswith(TODAY):
                yield scrapy.Request(response.urljoin(href), callback=self.parse_horse_racing_today_location)

    def parse_horse_racing_today_location(self, response):
        for href in response.xpath('//table[@class="racing"]/tr/td/a[contains(@class,"blue_link2_sports")]/@href').extract():
            yield scrapy.Request(response.urljoin(href), callback=self.parse_horse_racing_today_place)

    def parse_horse_racing_today_place(self, response):
        for href in response.xpath('//li[last()][@class="opened_menu"]/ul/li/a/@href').extract():
            if response.url in href:
                yield scrapy.Request(response.urljoin(href), callback=self.parse_horse_racing_today_race)

    def parse_horse_racing_today_race(self, response):
        participants = []
        participants_no = int(response.xpath('//@data-participants-no').extract_first())
        for participant_no in range(participants_no):
            participants.append({
                'participant_id': response.xpath('(//ul[@data-participant-id=$val]//@data-selection-id)[last()]', val=participant_no+1).extract_first(),
                'participant_name': response.xpath('//ul[@data-participant-id=$val]//div[@class="horse-information-name"]/text()', val=participant_no+1).extract_first(),
                'participant_odds': response.xpath('//ul[@data-participant-id=$val]//a[@class="bet_now_btn "]/text() | //ul[@data-participant-id=$val]//a[@class="bet_now_btn"]/text()', val=participant_no+1).extract_first()
            })

        yield OrderedDict({
            'track_name': response.xpath('//div[@class="event-name"]/text()').re(r'(.*)\s\d?\d:\d\d')[0],
            'race_start': response.xpath('//@data-start-date-time').extract_first(),
            'race_id': response.xpath('//@data-event-id').extract_first(),
            'participants': participants
        })
