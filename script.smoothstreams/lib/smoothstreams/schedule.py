# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import requests
import os
import re
import time, datetime
import timeutils
import xbmc, xbmcgui
import json
import htmlentitydefs
from lib import util

def fix_text(text):
    try:
        return htmlentitydecode(text.encode('ISO 8859-1').decode('utf-8'))
    except:
        util.DEBUG_LOG('Encoding fix failed for: {0} - assuming utf-8'.format(repr(text)))
        return htmlentitydecode(text)


def htmlentitydecode(s):
    if not '&' in s:
        return s

    return re.sub('&(%s);' % '|'.join(htmlentitydefs.name2codepoint),
        lambda m: unichr(htmlentitydefs.name2codepoint[m.group(1)]), s)


    re.sub()

# Kodi version check for SSL
kodi_version = int(xbmc.getInfoLabel('System.BuildVersion').split('.', 1)[0])
if (kodi_version < 17):
    JSONTVURL = 'http://fast-guide.smoothstreams.tv/feed.json'
else:
    JSONTVURL = 'https://fast-guide.smoothstreams.tv/feed.json'

LOGOBASE = '{0}'

JSONFILE = os.path.join(util.PROFILE,"SmoothStreams.json")
JSONFILE_ERROR = os.path.join(util.PROFILE,"SmoothStreams.json.error")

SPORTS_TABLE = { 'soccer':          {'name':'World Football',   'color':'1E9C2A'},
                 'nfl':             {'name':'American Football','color':'E85F10'},
                 'football':        {'name':'American Football','color':'E85F10'},
                 'american football':{'name':'American Football','color':'E85F10'},
                 'world football':  {'name':'World Football',   'color':'1E9C2A'},
                 'cfb':             {'name':'NCAAF',            'color':'E85F10'},
                 'ncaaf':           {'name':'NCAAF',            'color':'E85F10'},
                 'mlb':             {'name':'Baseball',         'color':'D49F24'},
                 'baseball':        {'name':'Baseball',         'color':'D49F24'},
                 'nba':             {'name':'NBA',              'color':'FC4F3D'},
                 'basketball':      {'name':'NBA',              'color':'FC4F3D'},
                 'boxing':          {'name':'Boxing & MMA',     'color':'808080'}, #white
                 'mma':             {'name':'Boxing & MMA',     'color':'808080'}, #white
                 'boxing + mma':    {'name':'Boxing & MMA',     'color':'808080'}, #white
                 'tennis':          {'name':'Tennis',           'color':'00A658'},
                 'f1':              {'name':'Motor Sports',     'color':'D10404'},
                 'motor sports':    {'name':'Motor Sports',     'color':'D10404'},
                 'racing':          {'name':'Motor Sports',     'color':'D10404'},
                 'wrestling':       {'name':'Wrestling',        'color':'9C793D'},
                 'rugby':           {'name':'Rugby',            'color':'A5AB24'},
                 'other':           {'name':'Other Sports',     'color':'808080'}, #white
                 'other sports':    {'name':'Other Sports',     'color':'808080'}, #white
                 'golf':            {'name':'Golf',             'color':'1EBD06'},
                 'cricket':         {'name':'Cricket',          'color':'3DB800'},
                 'tv':              {'name':'TV Shows',         'color':'845191'},
                 'general tv':      {'name':'TV Shows',         'color':'845191'},
                 'tv shows':        {'name':'TV Shows',         'color':'845191'},
                 'nascar':          {'name':'Nascar',           'color':'D10404'},
                 'nhl':             {'name':'Ice Hockey',       'color':'1373D4'},
                 'hockey':          {'name':'Ice Hockey',       'color':'1373D4'},
                 'ice hockey':      {'name':'Ice Hockey',       'color':'1373D4'},
                 'cbb':             {'name':'NCAAB',            'color':'B0372A'},
                 'ncaab':           {'name':'NCAAB',            'color':'B0372A'},
                 'olympics':        {'name':'Olympics',         'color':'808080'} }  #white

SUBCATS = { 'NCAAF':     'American Football',
            'NFL':       'American Football',
            'NBA':       'Basketball',
            'NCAAB':     'Basketball',
            'Formula 1': 'Motor Sports',
            'Nascar':    'Motor Sports',
            'General TV':'TV Shows'
}

CATSUBS = { 'American Football':('NCAAF','NFL'),
            'Basketball':('NBA','NCAAB'),
            'Motor Sports':('Formula 1','Nascar'),

}

#==============================================================================
# SSChannel
#==============================================================================
class SSChannel(dict):
    _ssType = 'CHANNEL'
    def init(self, displayname,logo,ID):
        self['ID'] = ID
        self['display-name'] = displayname
        self['logo'] = logo
        return self

    def currentProgram(self):
        for p in self.get('programs',[]):
            if p.isAiring(): return p
        return None

    @property
    def title(self):
        return self['display-name']

#==============================================================================
# SSProgram
#==============================================================================
class SSProgram(object):
    _ssType = 'PROGRAM'
    #==============================================================================
    # EPGData
    #==============================================================================
    class EPGData(object):
        def __init__(self,program):
            self.program = program
            self.color = SPORTS_TABLE.get(program.category.lower(),{}).get('color','808080')
            self.colorGIF = util.makeColorGif(self.color,os.path.join(util.COLOR_GIF_PATH,'{0}.gif'.format(self.color)))
            self.duration = (program.duration)/60
            self.quality = ''

        def update(self):
            if self.program.quality:
                if '720p' in self.program.quality:
                    self.quality = 'script-smoothstreams-hd_720p.png'
                elif '1080i' in self.program.quality:
                    self.quality = 'script-smoothstreams-hd_1080i.png'
            self.versions = '[CR]'.join(self.program.versions)

            localTZ = timeutils.LOCAL_TIMEZONE
            nowDT = timeutils.nowLocal()

            self.start = (self.program.start - self.program.startOfDay)/60
            self.stop = self.start + self.duration

            sDT = datetime.datetime.fromtimestamp(self.program.start,tz=localTZ)
            eDT = datetime.datetime.fromtimestamp(self.program.stop,tz=localTZ)
            if sDT.day == nowDT.day:
                startDisp = datetime.datetime.strftime(sDT,util.TIME_DISPLAY)
            else:
                startDisp = datetime.datetime.strftime(sDT,'%a {0}'.format(util.TIME_DISPLAY))
            if eDT.day == nowDT.day:
                endDisp = datetime.datetime.strftime(eDT,util.TIME_DISPLAY)
            else:
                endDisp = datetime.datetime.strftime(eDT,'%a {0}'.format(util.TIME_DISPLAY))
            self.startDisp = startDisp
            self.timeDisplay = '{0} - {1}  ({2})'.format(startDisp,endDisp,self.program.displayDuration)

    def __init__(self,pid,data,start_of_day):
        self.start = timeutils.convertStringToUTCTimestamp(data['time'])
        self.stop = timeutils.convertStringToUTCTimestamp(data['end_time'])
        self.channel = int(data['channel'])
        self.title = fix_text(data['name'])
        self.network = data.get('network','')
        self.language = data.get('language','')[:2].upper()
        self.description = fix_text(data.get('description',''))
        self.channelName = ''
        self.channelParent = None

        version = data.get('version')
        self.versions = version and version.split(' ; ') or []

        self.pid = str(pid)
        self.subcategory = None
        if 'category' in data:  # stopgap for category.
            cat = data['category'] or 'None'
            if cat == '0': cat = 'Other Sports'
            if cat in SUBCATS:
                self.subcategory = cat
                cat = SUBCATS[cat]
            self.category = cat.replace('&amp;', '&')
        else:
            self.category = 'None'

        self.quality = data.get('quality') or None

        self.setDuration()

        self.epg = SSProgram.EPGData(self)

        self.update(start_of_day)

    def localStart(self):
        return self.start

    def setDuration(self):
        self.duration = self.stop - self.start

        if self.duration > 31536000: #Fix for stop year being wrong. May happen as new years approaches
            fixed = timeutils.fixWrongYear(self.stop)
            self.stop = timeutils.convertStringToUTCTimestamp(fixed)
            self.duration = self.stop - self.start
            util.DEBUG_LOG('Bad year for "{0}" ({1}) stop time: {2} fixed: {3}'.format(self.title,self.channel,self.stop,fixed))

        self.displayDuration = timeutils.durationString(self.start,self.stop)

    def update(self,start_of_day):
        self.startOfDay = start_of_day
        self.epg.update()

    def isAiring(self):
        timeInDay = timeutils.timeInDayLocalSeconds()/60
        return self.epg.start <= timeInDay and self.epg.stop >= timeInDay

    def minutesLeft(self):
        if not self.isAiring(): return 0
        timeInDay = timeutils.timeInDayLocalSeconds()/60
        return self.epg.stop - timeInDay

#==============================================================================
# Schedule
#==============================================================================
class Schedule:
    def __init__(self):
        self.sscachejson(age=3600)
        self.seenCategories = []
        self.seenSubCategories = []

    @classmethod
    def sscachejson(cls,force=False,age=14400):
        """Try and update the JSONTV cache."""

        util.LOG("CacheJSON: Running...")
        if (force or not os.path.isfile(JSONFILE) or (os.path.getsize(JSONFILE) < 1) or (time.time() - os.stat(JSONFILE).st_mtime > age)):  # under 1 byte or over age old (default 4 hours).
            for first in (True,False):
                if force:
                    util.LOG("CacheJSON: Refresh forced. Fetching...")
                else:
                    util.LOG("CacheJSON: File does not exist, is too small or old. Fetching...")

                try:
                    response = requests.get(JSONTVURL,headers={'User-Agent':util.USER_AGENT,'Accept-Encoding':''}) #Accept-Encoding: '' prevents Accept-Encoding: gzip, deflate which for some reason gets us old data
                    response.encoding = 'utf-8'
                    util.LOG("CacheJSON: Fetched JSONTVURL")
                except Exception as e:
                    if first:
                        util.LOG("CacheJSON: Failed - retrying...")
                        continue
                    else:
                        util.ERROR("CacheJSON: Failed to open: {0} ({1})".format(JSONTVURL, e))
                        util.notify('Schedule Fetching Error','{0}'.format(e))
                    return False
                try:
                    json.loads(response.text)
                except Exception as e:  # if there is an exception, report and return.
                    util.ERROR("CacheJSON: ERROR PARSING received JSON: {0}".format(e))
                    try:
                        with open(JSONFILE_ERROR,'w') as f: f.write(response.text)
                    except:
                        util.ERROR()
                    if first:
                        util.LOG("CacheJSON: Failed - retrying...")
                        continue
                    else:
                        util.notify('Schedule Parsing Error','{0}'.format(e))
                    return False
                # if XML verifies, write to cachefile.
                with open(JSONFILE, 'w') as cache:
                    try:
                        cache.writelines(response.text)
                        util.LOG("CacheJSON: Wrote JSONTVURL to cache.")
                    except Exception as e:
                        util.LOG("CacheJSON: ERROR writing JSONTVURL to cache :: {0}".format(e))
                        return False

                return True
        else:
            util.LOG("CacheJSON: JSON file is good.")
            return False


    ######################
    # INTERNAL FUNCTIONS #
    ######################

    def _categories(self, optcategory=None):
        """Dictionary of valid SmoothStreams categories. Keys are names."""

        # conditional return of dict or check keys..
        if optcategory:  # if we have optcategory
            if optcategory in SPORTS_TABLE:  # return value.
                return SPORTS_TABLE[optcategory]['name']
            else:  # no key found.
                return None
        else:  # no optcategory so return keys.
            return SPORTS_TABLE.keys()

    def _fixchannel(self, chan):
        """Fix channel string by stripping leading channel number."""

        chan = re.sub('^\d+.*?-.*?(?=\w)', '', chan)  # \d\d- gone.
        return chan

    def _chanlookup(self, channel):
        """Returns the 24/7 channel value (validated) for a given channel."""

        chandict = dict((item['id'], self._fixchannel(item['display-name'])) for item in self.readChannels())
        return chandict[int(channel)]

    def _getChannel(self,channels,cid): #TODO: Something faster
        for c in channels:
            if c[u'id'] == cid:
                return c

    def _readJSON(self):
        if not os.path.exists(JSONFILE):
            util.LOG('No schedule file!')
            return None
        # open file.
        for first in (True,False):
            try:
                with open(JSONFILE) as json_file:
                    return json.load(json_file)
            except:
                if first:
                    util.ERROR('Failed to read json file - re-fetching...')
                    self.sscachejson(force=True)
                else:
                    util.ERROR('Failed to read json file on second attempt - giving up')
        return None

    def readChannels(self):
        """Read all channels in the file."""
        tree = self._readJSON()
        if not tree: return None
        # container for output.
        tmp_channels = {}
        channels = []
        # iterate over items.
        for (k, v) in tree.items():
            cid = int(k)
            displayname = v['name']
            logo = LOGOBASE.format(v['img'])
            tmp_channels[cid] = SSChannel().init(displayname,logo, v.get('channel_id'))
        for cid in sorted(tmp_channels.keys()):
            tmp = tmp_channels[cid]
            tmp['id'] = cid
            channels.append(tmp)
        return channels

    def readProgramData(self):
        """Return a list of SSProgram objects"""
        tree = self._readJSON()
        if not tree: return {}
        return tree

    ####################
    # PUBLIC FUNCTIONS #
    ####################

    def epg(self,start_of_day):
        channels = self.readChannels()
        if channels == None:
            util.notify('Failed to get schedule','Please try again later')
            return []
        pid = 1
        for k,v in self.readProgramData().items():
            if not 'items' in v: continue

            for elem in v['items']:
                program = SSProgram(pid,elem,start_of_day)
                channel = self._getChannel(channels, program.channel)
                program.channelParent = channel
                if not 'programs' in channel: channel['programs'] = []
                programs = channel['programs']

                if not program.category in self.seenCategories: self.seenCategories.append(program.category)
                if program.subcategory and not program.subcategory in self.seenSubCategories: self.seenSubCategories.append(program.subcategory)
                program.channelName = channel['display-name']
                programs.append(program)
                pid+=1

        return channels

    def categories(self,subs=False):
        if not subs: return sorted(self.seenCategories)
        cats = []
        for c in sorted(self.seenCategories):
            cats.append(c)
            if c in CATSUBS:
                for s in CATSUBS[c]:
                    if s in self.seenSubCategories:
                        cats.append('- ' + s)
        return cats
