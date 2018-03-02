# -*- coding: utf-8 -*-
import requests
import urllib
import util
from smoothstreams.dateutil import parser as du_parser
import datetime
class SSTwitterFeed(object):
    sig = 'eG1tcXRpMm9ZU3lzUUN2R1JaY3E5RmFIYjpBUnA0dGY3azNUYUdmeURGNHhOZ2xyc213UXBpcGx0TDdZcExRZVZVemtwUHdEQ0JmTA=='
    authURL = 'https://api.twitter.com/oauth2/token'
    feedURL = 'https://api.twitter.com/1.1/search/tweets.json?q={0}'.format(urllib.quote('from:SmoothStreamsTV'))

    def __init__(self):
        self._token = None

    @property
    def token(self):
        if self._token: return self._token
        r = requests.post(    self.authURL,
                              headers={'Authorization':'Basic {0}'.format(self.sig),
                              'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8'},
                              data={'grant_type':'client_credentials'}
        )
        data = r.json()
        self._token = data.get('access_token')
        return self._token

    def getFeed(self):
        r = requests.get(    self.feedURL,
                             headers={'Authorization':'Bearer {0}'.format(self.token)}
        )
        data = r.json()
        return data['statuses']

    def tweetIsNew(self,status):
        if util.getSetting('last_tweet_id') != str(status['id']):
            return True
        return False

    def getLatestTweet(self,or_saved=False):
        try:
            statuses = self.getFeed()
            status = statuses[0]
            if not self.tweetIsNew(status): return or_saved and util.getSetting('last_tweet_text') or ''
            try:
                dt = du_parser.parse(status['created_at'])
                dateDisp = datetime.datetime.strftime(dt,'%b %d')
            except:
                util.ERROR(repr(status.get('created_at')))
                dateDisp = '?'
            text = '[B]{0}:[/B] {1}'.format(dateDisp, status['text'])
            util.setSetting('last_tweet_id',status['id'])
            util.setSetting('last_tweet_text',text)
            return text
        except:
            util.ERROR()
            return ''
