import re
import time
import scrapy
import random
import json
import locale
import urllib2

from movie.items import MovieItem


class ImdbMovieUrlsProvider():
    def __init__(self):
        pass

    def prepare_movie_urls(self):
        with open("fetch_imdb_url.json", "r") as f:
            movies = json.load(f)
        urls = [m['movie_imdb_link'] for m in movies]
        return urls


class ImdbSpider(scrapy.Spider):
    name = "imdb"
    allowed_domains = ["imdb.com"]
    start_urls = ImdbMovieUrlsProvider().prepare_movie_urls() # there are 5000+ movies

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
        item = MovieItem()
        item['movie_imdb_link'] = response.url
        item['imdb_id'] = self.get_movie_id_from_url(response.url)

        # ---------------------------------------------------------------------------------------------------
        try:
            movie_title = response.xpath('//div[@class="title_wrapper"]/h1/text()').extract()[0]
        except:
            movie_title = None
        item['movie_title'] = movie_title

        # ---------------------------------------------------------------------------------------------------
        try:
            title_year = response.xpath('//*[@id="titleYear"]/a/text()').extract()[0]
        except:
            title_year = None
        item['title_year'] = title_year

        # ---------------------------------------------------------------------------------------------------
        try:
            genres = response.xpath('//div[@itemprop="genre"]//a/text()').extract()
        except:
            genres = None
        item['genres'] = genres

        # ---------------------------------------------------------------------------------------------------
        try:
            country = response.xpath('//div[@id="titleDetails"]/div/a[contains(@href, "country")]/text()').extract()
        except:
            country = None
        item['country'] = country

        # ---------------------------------------------------------------------------------------------------
        try:
            language = response.xpath('//div[@id="titleDetails"]/div/a[contains(@href, "language")]/text()').extract()
        except:
            language = None
        item['language'] = language

        # ---------------------------------------------------------------------------------------------------
        try:
            plot_keywords = response.xpath('//a/span[@itemprop="keywords"]/text()').extract()
        except:
            plot_keywords = None
        item['plot_keywords'] = plot_keywords

        # ---------------------------------------------------------------------------------------------------
        try:
            storyline = response.xpath('//div[@id="titleStoryLine"]/div[@itemprop="description"]/p/text()').extract()[0]
        except:
            storyline = None
        item['storyline'] = storyline

        # ---------------------------------------------------------------------------------------------------
        try:
            color = response.xpath('//a[contains(@href, "colors=")]/text()').extract()
        except:
            color = None
        item['color'] = color

        # ---------------------------------------------------------------------------------------------------
        try:
            budget = response.xpath('//h4[contains(text(), "Budget:")]/following-sibling::node()/descendant-or-self::text()').extract()
        except:
            budget = None
        item['budget'] = budget

        # ---------------------------------------------------------------------------------------------------
        try:
            gross = response.xpath('//h4[contains(text(), "Gross:")]/following-sibling::node()/descendant-or-self::text()').extract()
        except:
            gross = None
        item['gross'] = gross

        # ---------------------------------------------------------------------------------------------------
        try:
            user_review_score = response.xpath("//span[@itemprop='ratingValue']/text()").extract()
        except:
            user_review_score = None
        item['user_review_score'] = user_review_score
        
        # ---------------------------------------------------------------------------------------------------
        try:
            critic_review_score = response.xpath('//div[contains(@class,"metacriticScore")]/span/text()').extract()
        except:
            critic_review_score = None
        item['critic_review_score'] = critic_review_score

        # ---------------------------------------------------------------------------------------------------
        try:
            num_voted_users = response.xpath('//span[@itemprop="ratingCount"]/text()').extract()[0]
            num_voted_users = locale.atoi(num_voted_users)
        except:
            num_voted_users = None
        item['num_voted_users'] = num_voted_users

        # ---------------------------------------------------------------------------------------------------
        try:
            duration = response.xpath('//time[@itemprop="duration"]/text()').extract()
        except:
            duration = None
        item['duration'] = duration

        # ---------------------------------------------------------------------------------------------------
        try:
            aspect_ratio = response.xpath('//h4[contains(text(), "Aspect Ratio:")]/following-sibling::node()/descendant-or-self::text()').extract()
            # preprocess movie aspect ratio.
            ratio = ""
            for s in aspect_ratio:
                s = s.strip()
                if len(s) != 0:
                    ratio = s
                    break
            aspect_ratio = ratio
        except:
            aspect_ratio = None
        
        item['aspect_ratio'] = aspect_ratio

        # ---------------------------------------------------------------------------------------------------
        try:
            content_rating = response.xpath('//meta[@itemprop="contentRating"]/following-sibling::node()/descendant-or-self::text()').extract()
        except:
            content_rating = None
        item['content_rating'] = content_rating

        # ---------------------------------------------------------------------------------------------------
        try:
            num_user_for_reviews = response.xpath('//span/a[contains(@href, "reviews")]/text()').extract()[0]
            # preprocess "num_user_for_reviews". Convert "2,238 user" to number 2238
            num_user_for_reviews = locale.atoi(num_user_for_reviews.split(" ")[0])
        except:
            num_user_for_reviews = None
        item['num_user_for_reviews'] = num_user_for_reviews

        # ---------------------------------------------------------------------------------------------------
        try:
            num_critic_for_reviews = response.xpath('//span/a[contains(@href, "externalreviews")]/text()').extract()[0]
            # preprocess "num_critic_for_reviews". Convert "234 critics" to number 234
            num_critic_for_reviews = locale.atoi(num_critic_for_reviews.split(" ")[0])
        except:
            num_critic_for_reviews = None
        item['num_critic_for_reviews'] = num_critic_for_reviews

        # ---------------------------------------------------------------------------------------------------
        # (2) get names and links of directors
        base_url = "http://www.imdb.com"
        
        try:
            director_name = response.xpath('//span[@itemprop="director"]/a/span/text()').extract()[0]

            director_partial_link = response.xpath('//span[@itemprop="director"]/a/@href').extract()[0]
            director_full_link = base_url + director_partial_link

            director_info = {}
            director_info["director_name"] = director_name
            director_info["director_link"] = director_full_link
            director_info["name_id"] = self.get_person_name_id_from_url(director_full_link)

        except:
            director_info = None
        
        item['director_info'] = director_info

        # ---------------------------------------------------------------------------------------------------
        yield item
