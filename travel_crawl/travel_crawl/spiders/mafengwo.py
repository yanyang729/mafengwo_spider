# -*- encoding:utf-8 -*-
from __future__ import unicode_literals, absolute_import
import scrapy, requests, json, math, time, os, urllib
from bs4 import BeautifulSoup
from travel_crawl.items import GonglveItem, QAItem
import socket
from scrapy import Selector
from .constants import KEYWORDS

class Data_Crawl(scrapy.Spider):
    name = 'mafengwo'  # -爬虫名：一爬虫对应一名字
    allowed_domains = ['www.mafengwo.cn', 'pagelet.mafengwo.cn']  # 爬取网址域名
    start_urls = KEYWORDS  # -输入爬取的目的地或者关键字
    host = "http://www.mafengwo.cn/search/s.php?q="

    def start_requests(self):
        """
        location is search keywords
        """
        for key in self.start_urls:
            qa_url = "http://www.mafengwo.cn/qa/ajax_qa/more?type=0&mddid=&tid=&sort=0&key={}&page=0".format(key)
            yield scrapy.Request(qa_url, meta={'page_num': 0, 'key': key}, callback=self.parse_qa)

        page_num = 50  # -*- 网页中设置呈现页面最多为50页 -*-
        for i in range(len(self.start_urls)):
            for j in range(1, page_num + 1):
                yield scrapy.Request(self.host + self.start_urls[i] + "&p=" + str(j) + "&t=article_gonglve&kt=0",
                                     meta={'type': 0, "keyword": self.start_urls[i]}, callback=self.parse_info)

    def parse_qa(self, response):
        page_num = response.meta['page_num']
        key = response.meta['key']
        d = json.loads(response.body_as_unicode())
        html = d['data']['html'].strip()
        ids = Selector(text=html).xpath("//div[@class='cate-share-pop _j_share_pop hide clearfix']/@data-qid").extract()

        for id in ids:
            question_url = 'http://www.mafengwo.cn/wenda/detail-{}.html'.format(id)
            yield scrapy.Request(question_url, meta={'url': question_url, 'id': id}, callback=self.parse_qa_detail)

        if page_num < 5:
            url = "http://www.mafengwo.cn/qa/ajax_qa/more?type=0&mddid=&tid=&sort=0&key={}&page={}".format(key,
                                                                                                           page_num + 1)
            print('next 20 questions...')
            yield scrapy.Request(url=url, meta={'page_num': page_num + 1, 'key': key}, callback=self.parse_qa)

    def parse_qa_detail(self, res):
        item = QAItem()

        item['url'] = res.meta['url']
        id = res.meta['id']
        try:
            item['title'] = res.xpath('//*[@id="_js_askDetail"]/div[1]/div[1]/h1/text()').extract()[0].strip()
        except IndexError:
            print('no title')
            item['title'] = ''
        try:
            item['question'] = res.xpath('//*[@id="_js_askDetail"]/div[1]/div[2]/text()').extract()[0].strip()
        except IndexError:
            print('no question body')
            item['question'] = ''
        try:
            item['time'] = res.xpath('//*[@id="_js_askDetail"]/div[1]/div[3]/div[2]/span/span/text()').extract()[
                0].strip()
        except IndexError:
            print('no time')
            item['time'] = ''
        try:
            item['owner'] = res.xpath('//*[@id="_js_askDetail"]/div[1]/div[3]/div[2]/a[2]/text()').extract()[0].strip()
        except IndexError:
            print('no owner')
            item['owner'] = ''
        try:
            item['view'] = res.xpath('//*[@id="_js_askDetail"]/div[2]/div[2]/span[1]/text()').extract()[0].strip()
        except IndexError:
            print('no view')
            item['view'] = ''

        try:
            answer_count = int(res.xpath('//*[@id="_j_anum"]/text()').extract()[0].strip())
        except IndexError:
            print('no answer')
            answer_count = 0
            item['answers'] = []

        page_count = answer_count / 15 + 1

        for i in range(page_count):
            commets_api = 'http://www.mafengwo.cn/qa/ajax_qa/moreAnswer?page={}&qid={}'.format(i, id)
            yield scrapy.Request(url=commets_api, meta={'item': item}, callback=self.parse_wenda_api)

    def parse_wenda_api(self, response):
        item = response.meta['item']
        d = json.loads(response.body_as_unicode())
        html = d['data']['html'].strip()

        if not item.get('answers', 0):
            item['answers'] = []

        answers = Selector(text=html).xpath('//*[@class="_j_long_answer_item"]').extract()
        for a in answers:
            answer = ' '.join(Selector(text=a).xpath('//text()').extract())
            answer = answer.strip()
            item['answers'].append(answer)

        yield item

    ########################################################################

    def parse_info(self, response):
        try:
            ids = response.xpath('//div[@class="ct-text "]/h3/a/@href').re(r'\d+')
            urls = response.xpath('//div[@class="ct-text "]/h3/a/@href').extract()
            titles = response.xpath('//div[@class="ct-text "]/h3/a/text()').extract()
            times = response.xpath(
                '//*[@id="_j_search_result_left"]/div/div/ul/li/div/div[2]/ul/li[3]/text()').extract()
            times = [x.strip() for x in times]
        except:
            print('--------------- NO VALUE ------------')
            return

        type = response.meta['type']

        if type == 0:
            for i in range(len(ids)):
                item = GonglveItem()
                item['id'] = ids[i]
                item['keyword'] = response.meta['keyword']
                item['url'] = urls[i]
                item['title'] = titles[i]
                item['time'] = times[i]
                yield scrapy.Request(
                    url=urls[i], meta={'item': item, 'type': type}, callback=self.parse_gonglve
                )

    def parse_gonglve(self, response):
        type = response.meta['type']

        if type == 0:
            item = response.meta['item']
            item['view'] = \
                response.xpath('/html/body/div[2]/div[2]/div[1]/div[1]/div[1]/span[1]/em/text()').extract()[0].split()[
                    -1]
            item['images'] = response.xpath('/html/body/div[2]/div[2]/div[1]/div[2]/div/img/@data-src').extract()
            item['body'] = [x.strip() for x in
                            response.xpath('/html/body/div[2]/div[2]/div[1]/div[2]/div/div/text()').extract()]
            item['subtitle'] = response.xpath('//h2').extract()[:-1]

            urls = []
            for page in range(10):
                url = 'http://www.mafengwo.cn/gonglve/ziyouxing/detail/comments?gid={}&page={}'.format(item['id'], page)
                urls.append(url)

            for url in urls:
                yield scrapy.Request(url, meta={'item': item}, callback=self.parse_gonglve_comment)

    def parse_gonglve_comment(self, response):
        item = response.meta['item']
        html = json.loads(response.body_as_unicode())['html']
        comments = Selector(text=html).xpath("//*[contains(@class, 'com-cont')]/text()").extract()
        if not item.get('comments', False):
            item['comments'] = []
        item['comments'].extend(comments)
        yield item
