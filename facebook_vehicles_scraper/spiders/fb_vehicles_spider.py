# -*- coding: utf-8 -*-

import json
from datetime import datetime

from scrapy import Spider, FormRequest


class FacebookVehiclesSpider(Spider):
    name = 'fb_vehicles_spider'
    base_url = 'https://www.facebook.com/'
    graph_url_t = 'https://web.facebook.com/api/graphql/'
    vehicles_url = 'https://web.facebook.com/marketplace/london/vehicles'

    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': f'../output/facebook_vehicles_{datetime.today().strftime("%d%b%y")}.csv',
        # 'FEED_EXPORT_FIELDS': []
    }

    headers = {
        'authority': 'web.facebook.com',
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36',
        'content-type': 'application/x-www-form-urlencoded',
        'accept': '*/*',
        'origin': 'https://web.facebook.com',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://web.facebook.com/marketplace/london/vehicles?exact=false',
        'accept-language': 'en-US,en;q=0.9',
        'cookie': 'locale=en_GB;',
        # 'cookie': 'sb=dVDyXZmkAjwmYwMNHlSdiHeJ; datr=dVDyXbL8oto3YqmWOalz3HhJ; locale=en_GB; fr=0tt0x32SHMxNF9Ldy.AWUIuRX723VICxqHovdFgXvm2Rc.Beh8Fb.Gf.F9s.0.0.BfbKNR.; wd=1366x669',
    }

    variables = {
        'buyLocation': {'latitude': 51.5141, 'longitude': -0.1094},
        'categoryIDArray': [807311116002614],
        'count': 200,
        'cursor': '{"basic":{"item_index":0},"ads":{"items_since_last_ad":0,"items_retrieved":0,"ad_index":0,"ad_slot":0,"dynamic_gap_rule":0,"counted_organic_items":0,"average_organic_score":0,"is_dynamic_gap_rule_set":false,"first_organic_score":0,"is_dynamic_initial_gap_set":false,"iterated_organic_items":0,"top_organic_score":0,"feed_slice_number":11,"feed_retrieved_items":135,"ad_req_id":0,"refresh_ts":0,"cursor_id":53093,"mc_id":0},"boosted_ads":{"items_since_last_ad":0,"items_retrieved":0,"ad_index":0,"ad_slot":0,"dynamic_gap_rule":0,"counted_organic_items":0,"average_organic_score":0,"is_dynamic_gap_rule_set":false,"first_organic_score":0,"is_dynamic_initial_gap_set":false,"iterated_organic_items":0,"top_organic_score":0,"feed_slice_number":0,"feed_retrieved_items":0,"ad_req_id":0,"refresh_ts":0,"cursor_id":0,"mc_id":0},"lightning":{"initial_request":false,"top_unit_item_ids":null,"ranking_signature":null,"qid":null}}',
        'filterSortingParams': None, 'marketplaceBrowseContext': 'CATEGORY_FEED',
        'marketplaceID': None, 'numericVerticalFields': [], 'numericVerticalFieldsBetween': [],
        'priceRange': [0, 214748364700], 'radius': 65000, 'scale': 1,
        'sellerID': None, 'stringVerticalFields': []
    }

    data = {
        'av': '0',
        '__user': '0',
        '__a': '1',
        '__dyn': '7xe6HwkEowBwRyWwHBWo2vwAxu13wIwk8KewSwMwNw9G2S0wE2ywUx609vCwjE1xoswaq3a1ey87i0n2US2G2Caw9m8wsU9k2CE6q0Mo5W3e9wFwHwlEjxG0y8jwGzEao7a222SUbElxm0zK5o4q0Gogw',
        '__csr': '',
        '__req': '3i',
        '__beoa': '1',
        '__pc': 'EXP1:comet_pkg',
        'dpr': '1',
        '__ccg': 'MODERATE',
        '__rev': '1002720574',
        '__s': 'b2eyv4:61gluv:cpuy2g',
        '__hsi': '6876214806985214658-0',
        '__comet_req': '1',
        'lsd': 'AVrB9_JN',
        'jazoest': '2635',
        '__spin_r': '1002720574',
        '__spin_b': 'trunk',
        '__spin_t': '1600993519',
        'fb_api_caller_class': 'RelayModern',
        'fb_api_req_friendly_name': 'CometMarketplaceCategoryContentPaginationQuery',
        'variables': json.dumps(variables),
        'server_timestamps': 'true',
        'doc_id': '5039317692760562'
    }

    def start_requests(self):
        yield FormRequest(url=self.graph_url_t, formdata=self.data, meta={'handle_httpstatus_all': True})

    def parse(self, response):
        data = json.loads(response.text)
        feed = data['data']['viewer']['marketplace_feed_stories']

        for e in feed['edges']:
            node = e['node']
            node.pop('tracking')
            node.pop('id')

            listing = node.pop('listing', {})
            listing_name = listing.pop('__typename')
            primary_listing_photo = listing.pop('primary_listing_photo')
            formatted_price = listing.pop('formatted_price')
            location = listing.pop('location')
            custom_sub_titles = listing.pop('custom_sub_titles_with_rendering_flags')
            pre_recorded_videos = listing.pop('pre_recorded_videos')
            delivery_types = listing.pop('delivery_types')
            seller = listing.pop('marketplace_listing_seller')
            story = listing.pop('story')

            node.update(listing)
            node['listing_name'] = listing_name
            image = primary_listing_photo['image']['uri']
            node['image_urls'] = [image] if image else []
            node['price'] = formatted_price['text']

            geo_code = location['reverse_geocode']
            node['location'] = ', '.join([geo_code['city'], geo_code['state']])

            node['custom_sub_titles'] = ', '.join(e['subtitle'] for e in custom_sub_titles)
            node['delivery_types'] = ', '.join(delivery_types)

            node['seller_id'] = seller['id']
            node['seller_type'] = seller['__typename']
            node['seller_name'] = seller['name']
            node['story_url'] = story['url']

            yield node

        if not feed['page_info']['has_next_page']:
            print("No Next Page")
            return
        self.variables['cursor'] = feed['page_info']['end_cursor']
        self.data['variables'] = json.dumps(self.variables)
        yield FormRequest(url=self.graph_url_t, formdata=self.data, meta=response.meta)
