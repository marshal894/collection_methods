from scrapy.http import HtmlResponse
from urllib.parse import urlencode
import scrapy
import re
import json
from copy import deepcopy
from instagramparser.items import InstagramparserItem
from instagramparser.user_config import INSTA_LOGIN, INSTA_PASS


class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['instagram.com']
    start_urls = ['https://www.instagram.com/']
    inst_login_url = 'https://www.instagram.com/accounts/login/ajax/'
    inst_login = INSTA_LOGIN
    inst_pswd = INSTA_PASS
    query_hash_posts = '8c2a529969ee035a5063f2fc8602a0fd'
    graphql_url = 'https://www.instagram.com/graphql/query/?'

    def parse(self, response: HtmlResponse):
        csrf = self.fetch_csrf_token(response.text)
        yield scrapy.FormRequest(
            self.inst_login_url,
            method='POST',
            callback=self.login,
            formdata={'username': self.inst_login,
                      'enc_password': self.inst_pswd},
            headers={'X-CSRFToken': csrf}
        )

    def login(self, response: HtmlResponse):
        for people in self.parse_users:
            parse_user = people['user']
            gen_user = people['gen_user']
            j_data = response.json()
            if j_data['authenticated']:
                yield response


    def parse_user_data(self, response: HtmlResponse, username, gen_user):
        user_id = self.fetch_user_id(response.text, username)
        variables = {'id': user_id,
                     'first': 12}
        url_posts = f'{self.graphql_url}query_hash={self.query_hash_posts}&{urlencode(variables)}'
        yield response.follow(url_posts,
                              callback=self.user_posts_parse,
                              cb_kwargs={'username': username,
                                         'gen_user': gen_user,
                                         'user_id': user_id,
                                         'variables': deepcopy(variables)
                                         },
                              headers={'User-Agent': 'Instagram 155.0.0.37.107'}
                              )

    def user_posts_parse(self, response: HtmlResponse, username, gen_user, user_id, variables):
        j_data = response.json()
        page_info = j_data.get('data').get('user').get('edge_owner_to_timeline_media').get('page_info')
        if page_info.get('has_next_page'):
            variables['after'] = page_info['end_cursor']

        url_posts = f'{self.graphql_url}query_hash={self.query_hash_posts}&{urlencode(variables)}'
        yield response.follow(url_posts,
                              callback=self.user_posts_parse,
                              cb_kwargs={'username': username,
                                         'gen_user': gen_user,
                                         'user_id': user_id,
                                         'variables': deepcopy(variables)
                                         }
                              )

        posts = j_data.get('data').get('user').get('edge_owner_to_timeline_media').get('edges')
        for post in posts:
            item = InstagramparserItem(
                username=username,
                gen_user=gen_user,
                user_id=user_id,
                photo=post['node']['display_url'],
                likes=post['node']['edge_media_preview_like']['count'],
                post_data=post['node']
            )
            yield item


    def fetch_csrf_token(self, text):
        matched = re.search('\"csrf_token\":\"\\w+\"', text).group()
        return matched.split(':').pop().replace(r'"', '')


    def fetch_user_id(self, text, username):
        matched = re.search(
            '{\"id\":\"\\d+\",\"username\":\"%s\"}' % username, text
 ).group()
        return json.loads(matched)