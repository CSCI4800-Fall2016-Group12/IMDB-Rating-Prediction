import re
import time
import scrapy
import random
import json
import locale
import urllib2

from movie.items import MoviePeopleItem

class ImdbPeopleUrlsProvider():
    def __init__(self):
        pass

    def prepare_movie_people_urls(self):
        with open("imdb_output.json", "r") as f:
            movies = json.load(f)
        urls = ['http://www.imdb.com/title/' + m['imdb_id'] + '/fullcredits' for m in movies]
        return urls


class ImdbPeopleSpider(scrapy.Spider):
    name = "imdb_people"
    allowed_domains = ["imdb.com"]
    start_urls = ImdbPeopleUrlsProvider().prepare_movie_people_urls() # there are 5000+ movies

    locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' ) 

    def extract_text(self, xpath, response):
        path = "{}/text()".format(xpath)
        return response.xpath(path).extract()

    def get_movie_id_from_url(self, url):
        # sample imdb movie url: http://www.imdb.com/title/tt0068646/?ref_=nv_sr_1
        # we need to return "tt0068646"
        if url is None:
            return None
        return re.search("(tt[0-9]{7})", url).group()

    def get_person_name_id_from_url(self, url):
        # sample imdb person url: http://www.imdb.com/name/nm0000338/?ref_=tt_ov_dr
        # we need to return "nm0000338"
        if url is None:
            return None
        return re.search("(nm[0-9]{7})", url).group()

    def parse(self, response):
        item = MoviePeopleItem()
        item['movie_imdb_people_link'] = response.url
        item['imdb_id'] = self.get_movie_id_from_url(response.url)

        # ---------------------------------------------------------------------------------------------------
        
        base_url = "http://www.imdb.com"

        try:
            # extract all ODD table rows from the cast list
            cast_name_list_from_odd_rows = response.xpath('//table[@class="cast_list"]/tr[@class="odd"]/td[@class="itemprop"]/a/span[@class="itemprop"]/text()').extract()
            cast_name_href_list_from_odd_rows = response.xpath('//table[@class="cast_list"]/tr[@class="odd"]/td[@class="itemprop"]/a/@href').extract()
            links_from_odd_rows = [base_url + e for e in cast_name_href_list_from_odd_rows]
            pairs_for_odd_rows = zip(cast_name_list_from_odd_rows, links_from_odd_rows)

            # extract all EVEN table rows from the cast list
            cast_name_list_from_even_rows = response.xpath('//table[@class="cast_list"]/tr[@class="even"]/td[@class="itemprop"]/a/span[@class="itemprop"]/text()').extract()
            cast_name_href_list_from_even_rows = response.xpath('//table[@class="cast_list"]/tr[@class="even"]/td[@class="itemprop"]/a/@href').extract()
            links_from_even_rows = [base_url + e for e in cast_name_href_list_from_even_rows]
            pairs_for_even_rows = zip(cast_name_list_from_even_rows, links_from_even_rows)

            # combine the two lists
            cast_name_link_pairs = pairs_for_odd_rows + pairs_for_even_rows

            # convert list of pairs to dictionary
            cast_info = []
            for p in cast_name_link_pairs:
                name, link = p[0], p[1]
                actor = {}
                actor["actor_name"] = name
                actor["actor_link"] = link
                actor["name_id"] = self.get_person_name_id_from_url(link)

                cast_info.append(actor)
        except:
            cast_info = None

        item['cast_info'] = cast_info

        # ---------------------------------------------------------------------------------------------------
        try:
			
            writer_name_list = response.xpath('//h4[contains(text(),"Writing Credits")]/following-sibling::node()[count(.|//h4[@id="cast"]/preceding-sibling::node())=count(//h4[@id="cast"]/preceding-sibling::node())]//td[@class="name"]/a/text()').extract()
            writer_name_href_list = response.xpath('//h4[contains(text(),"Writing Credits")]/following-sibling::node()[count(.|//h4[@id="cast"]/preceding-sibling::node())=count(//h4[@id="cast"]/preceding-sibling::node())]//td[@class="name"]/a/@href').extract()
            writer_credit_list = response.xpath('//h4[contains(text(),"Writing Credits")]/following-sibling::node()[count(.|//h4[@id="cast"]/preceding-sibling::node())=count(//h4[@id="cast"]/preceding-sibling::node())]//td[@class="credit"]/text()').extract()
            writer_links = [base_url + e for e in writer_name_href_list]

            # convert list of pairs to dictionary
            writer_info = []
            for p in zip(writer_name_list, writer_links, writer_credit_list):
                name, link, credit = p[0], p[1], p[2]
                writer = {}
                writer["writer_name"] = name
                writer["writer_link"] = link
                writer["writer_credit"] = credit
                writer["name_id"] = self.get_person_name_id_from_url(link)

                writer_info.append(writer)
        except:
            writer_info = None

        item['writer_info'] = writer_info
        
        # ---------------------------------------------------------------------------------------------------
        yield item
