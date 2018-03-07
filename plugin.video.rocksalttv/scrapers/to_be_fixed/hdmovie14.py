"""
    Death Streams Addon
    Copyright (C) 2017 Mr Blamo.Blamo

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import datetime
import re
import urllib
import urlparse
import kodi
import log_utils  # @UnusedImport
import dom_parser
import dom_parser2
import client
from deaths_lib.utils2 import i18n
from deaths_lib import source_utils
from deaths_lib import scraper_utils
from deaths_lib.constants import FORCE_NO_MATCH
from deaths_lib.constants import VIDEO_TYPES
import scraper

BASE_URL = 'http://movieocean.net'

class Flixanity_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.base_url = kodi.get_setting('%s-base_url' % (self.get_name()))

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.TVSHOW, VIDEO_TYPES.EPISODE, VIDEO_TYPES.MOVIE])

    @classmethod
    def get_name(cls):
        return 'MovieOcean'

    def resolve_link(self, link):
        return link

    def format_source_label(self, item):
        return '[%s] %s' % (item['quality'], item['host'])

    def get_sources(self, video):
        source_url = self.get_url(video)
        sources = []
        if source_url and source_url != FORCE_NO_MATCH:
            url = urlparse.urljoin(self.base_url, source_url)
            html = self._http_get(url, cache_limit=.5)
            for fragment in dom_parser.parse_dom(html, 'div', {'class': 'player_wraper'}):
                iframe_url = dom_parser.parse_dom(fragment, 'iframe', ret='src')
                if iframe_url:
                    url = urlparse.urljoin(self.base_url, iframe_url[0])
                    html = self._http_get(url, cache_limit=.5)
                    for match in re.finditer('"(?:url|src)"\s*:\s*"([^"]+)[^}]+"res"\s*:\s*([^,]+)', html):
                        stream_url, height = match.groups()
                        host = self._get_direct_hostname(stream_url)
                        if host == 'gvideo':
                            quality = scraper_utils.gv_get_quality(stream_url)
                        else:
                            quality = scraper_utils.height_get_quality(height)
                        stream_url += '|User-Agent=%s' % (scraper_utils.get_ua())
                        source = {'multi-part': False, 'url': stream_url, 'host': host, 'class': self, 'quality': quality, 'views': None, 'rating': None, 'direct': True}
                        sources.append(source)

        return sources

    def get_url(self, video):
        return self._default_get_url(video)

    def search(self, video_type, title, year, season=''):
        try: season = int(season)
        except: season = 0
        
        results = self.__list(title)
        results = []
        if not results:
            results = self.__search(title, season)

        filtered_results = []
        norm_title = scraper_utils.normalize_title(title)
        for result in results:
            if norm_title in scraper_utils.normalize_title(result['title']) and (not season or season == int(result['season'])):
                result['title'] = '%s - Season %s [%s]' % (result['title'], result['season'], result['q_str'])

        search_url = urlparse.urljoin(self.base_url, '/search/')
        search_key = title.lower()
        if year: search_key += ' %s' % (year)
        search_url += urllib.quote_plus(search_key)
        html = self._http_get(search_url, cache_limit=1)
        
        # detect search results redirect
        meta = dom_parser.parse_dom(html, 'meta', {'property': 'og:url'}, ret='content')
        if meta:
            match_url = meta[0]
            if '/watch/' in match_url:
                match_title = title
                match_year = year
                page_title = dom_parser.parse_dom(html, 'title')
                if page_title:
                    match = re.search('(?:Watch\s+)?(.*?)\s+(\d{4})', page_title[0], re.I)
                    if match:
                        match_title, match_year = match.groups()
                        
                match_url = re.sub('-season-\d+', '', match_url)
                match_title = match_title.strip()
                results = [{'title': match_title, 'year': match_year, 'url': scraper_utils.pathify_url(match_url)}]
        
        # collect search results if no redirect found
        seen_urls = {}
        if not results:
                for item in dom_parser.parse_dom(html, 'div', {'class': 'caption'}):
                    match = re.search('href="([^"]+)[^>]+>(.*?)</a>', item)
                    if match:
                        match_url, match_title = match.groups()
                        is_season = re.search('-season-\d+', match_url)
                        if video_type == VIDEO_TYPES.TVSHOW and is_season:
                            match_url = re.sub('-season-\d+', '', match_url)
                            if match_url in seen_urls: continue
                            seen_urls[match_url] = True
                        elif video_type == VIDEO_TYPES.MOVIE and not is_season:
                            pass
                        else:
                            continue
        
                        match_title = re.sub('</?[^>]*>', '', match_title)
                        match = re.search('-(\d{4})$', match_url)
                        if match:
                            match_year = match.group(1)
                        else:
                            match_year = ''
                        
                        if not year or not match_year or year == match_year:
                            result = {'title': scraper_utils.cleanse_title(match_title), 'year': match_year, 'url': scraper_utils.pathify_url(match_url)}
                            results.append(result)

        return results

    def _get_episode_url(self, show_url, video):
        season_url = show_url + '-season-%s/' % (video.season)
        url = urlparse.urljoin(self.base_url, season_url)
        html = self._http_get(url, allow_redirect=False, cache_limit=.5)
        if html != '/':
            url = urlparse.urljoin(self.base_url, html)
            html = self._http_get(url, allow_redirect=False, cache_limit=.5)
            if int(video.episode) == 1:
                return scraper_utils.pathify_url(url)
            else:
                pattern = 'location\.href=&quot;([^&]*season-%s[^/]*/%s)&quot;' % (video.season, video.episode)
                match = re.search(pattern, html)
                if match:
                    return scraper_utils.pathify_url(match.group(1))