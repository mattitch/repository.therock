# -*- coding: utf-8 -*-
import urllib, time
import requests
import xbmc, xbmcgui
from lib import util, downloadregistry
import URLDownloader

class ChannelPlayer():
    servers =  ({'name':util.T(30700),'host':"deu.SmoothStreams.tv"},  # European Server Mix
                  {'name':util.T(30701),'host':"deu-nl.SmoothStreams.tv"},  # European NL Mix
                  {'name':util.T(30702),'host':"deu-uk.SmoothStreams.tv"},  # European UK Mix
                  {'name':util.T(30718),'host':"deu-de.SmoothStreams.tv"},  # European DE Mix
                  {'name':util.T(30703),'host':"deu-uk1.SmoothStreams.tv"},  # EU UK1 (io)
                  {'name':util.T(30704),'host':"deu-uk2.SmoothStreams.tv"},  # EU UK2 (100TB)
                  {'name':util.T(30705),'host':"deu-nl1.SmoothStreams.tv"},  # EU NL1 (i3d)
                  {'name':util.T(30706),'host':"deu-nl2.SmoothStreams.tv"},  # EU NL2 (i3d)
                  {'name':util.T(30707),'host':"deu-nl3.SmoothStreams.tv"},  # EU NL3 (Ams)
                  {'name':util.T(30708),'host':"dna.SmoothStreams.tv"},  # US/CA Server Mix
                  {'name':util.T(30709),'host':"dnae.SmoothStreams.tv"},  # US/CA East Server Mix
                  {'name':util.T(30710),'host':"dnaw.SmoothStreams.tv"},  # US/CA West Server Mix
                  {'name':util.T(30711),'host':"dnae1.SmoothStreams.tv"},  # US/CA East (NJ)
                  {'name':util.T(30712),'host':"dnae2.SmoothStreams.tv"},  # US/CA East (VA)
                  {'name':util.T(30713),'host':"dnae3.SmoothStreams.tv"},  # US/CA East (MTL)
                  {'name':util.T(30714),'host':"dnae4.SmoothStreams.tv"},  # US/CA East (TOR)
                  {'name':util.T(30719),'host':"dnae6.SmoothStreams.tv"},  # US/CA East (NY)
                  {'name':util.T(30715),'host':"dnaw1.SmoothStreams.tv"},  # US/CA West (PHX,AZ)
                  {'name':util.T(30716),'host':"dnaw2.SmoothStreams.tv"},  # US/CA West (LA,CA)
                  {'name':util.T(30720),'host':"dnaw3.SmoothStreams.tv"},  # US/CA West (SJ,CA)
                  {'name':util.T(30721),'host':"dnaw4.smoothstreams.tv"},  # US/CA West (CHI)
                  {'name':util.T(30717),'host':"dap.SmoothStreams.tv"}  #  Asia - Singapore
    )

    # Kodi version check for SSL
    kodi_version = int(xbmc.getInfoLabel('System.BuildVersion').split('.', 1)[0])
    if (kodi_version < 17):
        HASH_LOGIN = 'http://auth.smoothstreams.tv/hash_api.php?site={site}&username={user}&password={password}'
        MMA_HASH_LOGIN = 'http://www.MMA-TV.net/loginForm.php?username={user}&password={password}&site={site}'
        services = (
            {'name':'Change Required', 'site':"viewus",     'rtmp_port':3655, 'hls_port':9100, 'login':HASH_LOGIN,     'servers':servers, 'servers_sett':'server'},
            {'name':'Live247.tv',       'site':"view247",    'rtmp_port':3625, 'hls_port':9100, 'login':HASH_LOGIN,     'servers':servers, 'servers_sett':'server'},
            {'name':'StarStreams',      'site':"viewss",     'rtmp_port':3665, 'hls_port':9100, 'login':HASH_LOGIN,     'servers':servers, 'servers_sett':'server'},
            {'name':'MMA SR+',          'site':"viewmmasr",  'rtmp_port':3635, 'hls_port':9100, 'login':MMA_HASH_LOGIN, 'servers':servers, 'servers_sett':'server'},
            {'name':'StreamTVnow',      'site':"viewstvn",   'rtmp_port':3615, 'hls_port':9100, 'login':HASH_LOGIN,     'servers':servers, 'servers_sett':'server'}
        )
    else:
        HASH_LOGIN = 'https://auth.smoothstreams.tv/hash_api.php?site={site}&username={user}&password={password}'
        MMA_HASH_LOGIN = 'https://www.MMA-TV.net/loginForm.php?username={user}&password={password}&site={site}'
        services = (
            {'name':'Change Required', 'site':"viewus",     'rtmp_port':3655, 'hls_port':443, 'login':HASH_LOGIN,     'servers':servers, 'servers_sett':'server'},
            {'name':'Live247.tv',       'site':"view247",    'rtmp_port':3625, 'hls_port':443, 'login':HASH_LOGIN,     'servers':servers, 'servers_sett':'server'},
            {'name':'StarStreams',      'site':"viewss",     'rtmp_port':3665, 'hls_port':443, 'login':HASH_LOGIN,     'servers':servers, 'servers_sett':'server'},
            {'name':'MMA SR+',          'site':"viewmmasr",  'rtmp_port':3635, 'hls_port':443, 'login':MMA_HASH_LOGIN, 'servers':servers, 'servers_sett':'server'},
            {'name':'StreamTVnow',      'site':"viewstvn",   'rtmp_port':3615, 'hls_port':443, 'login':HASH_LOGIN,     'servers':servers, 'servers_sett':'server'}
        )

    def __init__(self,user_agent=util.USER_AGENT):
        self.userAgent = user_agent
        self.player = xbmc.Player()
        self.session = requests.Session()

    def _play(self,url,item):
        self.player.play(url,item,util.getSetting('show_video_preview',True) and util.getSetting('start_video_preview',False),0)

    def play(self,item):
        if item._ssType == 'PROGRAM':
            if item.isAiring():
                self.playFromProgram(item)
            else:
                self.playFromChannel(item.channelParent)
        else:
            program = item.currentProgram()
            if program:
                self.playFromProgram(program)
            else:
                self.playFromChannel(item)

    def playFromProgram(self,program):
        url = self.getChanUrl(program.channel)
        item = xbmcgui.ListItem(program.title)
        info = {'Title': program.title,
                'Genre': program.category,
                'Plot':program.description or program.title,
                'Studio':'{0} ({1})'.format(program.network,program.channelName)
        }
        item.setInfo('video', info)
        self._play(url,item)

    def playFromChannel(self,channel):
        url = self.getChanUrl(channel['id'])
        item = xbmcgui.ListItem(channel['display-name'])
        item.setInfo('video', {'Title': channel['display-name'], 'Genre': 'Unknown'})
        self._play(url,item)

    def playRecording(self,item):
        url = item.path
        title = u'Recording: {0}'.format(item.display)
        item = xbmcgui.ListItem(title)
        item.setInfo('video', {'Title': title, 'Genre': 'Unknown'})
        self._play(url,item)

    def canDownload(self):
        return URLDownloader.canDownload()

    def getFilename(self,base):
        filename = xbmcgui.Dialog().input(util.T(30104),base)
        if not filename: return
        filename = filename.decode('utf-8')
        return filename

    def getDownloadPath(self):
        if not util.getSetting("download_path"):
            self.showMessage(util.T(30600), util.T(30601))
            util.ADDON.openSettings()

        return util.getSetting("download_path")

    def download(self,item):
        duration = 0
        program = None
        if item._ssType == 'PROGRAM':
            program = item
        else:
            program = item.currentProgram()

        if program and program.isAiring():
            url = self.getChanUrl(program.channel,force_hls=True,for_download=True)
            duration = program.minutesLeft()
            title = program.title + time.strftime(' - %H:%M:%S'.format(util.TIME_DISPLAY),time.localtime())
        else:
            if program: item = item.channelParent #Selected program but it is not airing, use channel info
            url = self.getChanUrl(item['id'],force_hls=True,for_download=True)
            title = item['display-name'] + time.strftime(' - %b %d {0}'.format(util.TIME_DISPLAY),time.localtime())

        filename = self.getFilename(title)
        if not filename: return
        title = filename
        filename = util.cleanFilename(filename) #In case the user added something unsafe

        minutes = xbmcgui.Dialog().numeric(0,util.T(30105),str(duration or 120))

        if not minutes:
            util.LOG("No duration set")
            return None

        if len(url) > 10:
            download_path = self.getDownloadPath()
            if download_path:
                callback = 'RunScript(script.smoothstreams,DOWNLOAD_CALLBACK,{download})'
                download = URLDownloader.download(url,download_path,filename,title,int(minutes),util.getSetting('direct_record',True),callback=callback)
                with downloadregistry.DownloadRegistry() as dr:
                    dr.add(download)

    def schedule(self,program):
        item = URLDownloader.ScheduleItem()
        filename = self.getFilename(program.title)
        item.display = filename
        item.filename = util.cleanFilename(filename) #In case the user added something unsafe

        minutes = xbmcgui.Dialog().numeric(0,util.T(30105),str(program.epg.duration))

        if not minutes:
            util.LOG("No duration set")
            return None
        item.minutes = int(minutes)
        downloadPath = self.getDownloadPath()
        if not downloadPath: return
        item.targetPath = downloadPath
        item.url = self.getChanUrl(program.channel,force_rtmp=True,for_download=True)
        item.direct = util.getSetting('direct_record',True)
        item.start = program.start
        URLDownloader.schedule(item)
        with downloadregistry.DownloadRegistry() as dr:
            dr.add(item)

    def stopDownload(self):
        URLDownloader.stopDownloading()

    def isDownloading(self):
        return URLDownloader.isDownloading()

    @property
    def serviceIDX(self):
        idx = util.getSetting("service",0)
        if idx >= len(self.services):
            idx = len(self.services) - 1
        return idx

    @property
    def service(self):
        return self.services[self.serviceIDX]

    def getChanUrl(self, chan, force_rtmp=False, for_download=False, force_hls=False):
        service = self.service
        server = service['servers'][util.getSetting(service['servers_sett'],0)]

        if util.getSetting("high_def",True):
            quality = "q1"  # HD - 2800k
        elif True:
            quality = "q2"  # LD - 1250k
        else:
            quality = "q3"  # Mobile - 400k ( Not in settings)

        credentials = self.login()
        if not credentials: return

        if not force_hls and (force_rtmp or util.getSetting("server_type",0) == 0): # and not server.get('temp_force_hls'):
            util.LOG('Using {0}'.format(service['name']))

            chan_template = 'rtmp://{server}:{port}/{site}?user_agent={user_agent}&wmsAuthSign={hash}/ch{channel:02d}{quality}.stream'

            if not for_download: chan_template += ' live=1 timeout=20'
            url = chan_template.format(
                server=server['host'],
                port=service['rtmp_port'],
                site=service['site'],
                channel=chan,
                quality=quality,
                user_agent=urllib.quote(self.userAgent.replace('/','_')),
                **credentials
            )

        else:
            util.LOG('Using {0}'.format(service['name']))
            # Kodi version check for SSL
            kodi_version = int(xbmc.getInfoLabel('System.BuildVersion').split('.', 1)[0])
            if (kodi_version < 17):
                chan_template = 'http://{server}:{port}/{site}/ch{channel:02d}{quality}.stream/playlist.m3u8?wmsAuthSign={hash}'
            else:
                chan_template = 'https://{server}:{port}/{site}/ch{channel:02d}{quality}.stream/playlist.m3u8?wmsAuthSign={hash}'

            url = chan_template.format(
                server=server['host'],
                port=server.get('port', service['hls_port']),
                site=service['site'],
                channel=chan,
                quality=quality,
                **credentials
            )

        return url

    def loadHash(self):
        vHash = util.getSetting("SHash_{0}".format(self.serviceIDX))
        if not vHash: return None
        expires = util.getSetting("SHashExp_{0}".format(self.serviceIDX),0)
        if time.time() > expires - 60: return None
        return vHash

    def getHash(self):
        util.LOG("Logging in for hash...")

        uname = util.getSetting("username")
        pword = util.getSetting("user_password")

        url = self.service['login'].format(user=uname, password=pword, site=self.service['site'])

        post_data = {"username": uname, "password": pword, "site": self.service['site']}

        self.session.headers.update({'referer': url})
        res = self.session.post(url,data=post_data)

        try:
            result = res.json()
            if 'code' in result and result['code'] == '1':
                vHash = result['hash']
                valid = result['valid']
                util.setSetting("SHash_{0}".format(self.serviceIDX),vHash)
                util.setSetting("SHashExp_{0}".format(self.serviceIDX),time.time() + (valid * 60))
                util.LOG("Login complete")
                return vHash
        except Exception as e:
            result = res.text
            util.LOG("Error parsing login result: " + repr(e) + " - " + repr(result))
            return None

        if "error" in result:
            self.showMessage(util.T(30600) + " " + util.T(30603), result["error"])
        else:
            self.showMessage(util.T(30600), util.T(30603))

        util.LOG("Login failure: " + repr(result))
        return None

    def login(self):
        credentials = {'hash':None, 'user':None, 'password':None}

        vHash = self.loadHash()
        if not vHash: vHash = self.getHash()
        if not vHash: return None
        credentials['hash'] = vHash

        return credentials

    def resetTokens(self):
        pass

    def safeDecodeUnicode(self, data): #TODO: Replace this with something better
        try:
            return data.decode("utf-8")
        except:
            try:
                return data.decode("utf-8", "ignore")
            except:
                return repr(data)

    def showMessage(self, heading, message):
        #duration = ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10][int(self.settings.getSetting('notification_length'))]) * 1000
        duration = 5
        xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % (heading, message, duration))

    def averageList(self, lst):
        util.LOG(repr(lst))
        avg_ping = 0
        avg_ping_cnt = 0
        for p in lst:
            try:
                avg_ping += float(p)
                avg_ping_cnt += 1
            except:
                util.LOG("Couldn't convert %s to float" % repr(p))
        return avg_ping / avg_ping_cnt

    def testServers(self, update_settings=True):
        if not util.getSetting("auto_server",False): return None

        service = self.service

        util.LOG("Original server: {0} - {1}".format(service['servers'][util.getSetting(service['servers_sett'],0)]['host'],util.getSetting(service['servers_sett'],0)))

        import re, subprocess
        res = None
        ping = False
        with util.xbmcDialogProgress('Testing servers...') as prog:
            for i, server in enumerate(service['servers']):
                if not prog.update( int((100.0/len(service['servers'])) * i), 'Testing servers...', '', server['name']):
                    util.setSetting("auto_server", False)
                    return
                ping_results = False
                try:
                    if xbmc.getCondVisibility('system.platform.windows'):
                        p = subprocess.Popen(["ping", "-n", "4", server['host']], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                    else:
                        p = subprocess.Popen(["ping", "-c", "4", server['host']], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    ping_results = re.compile("time=(.*?)ms").findall(p.communicate()[0])
                except:
                    util.LOG("Platform doesn't support ping. Disable auto server selection")
                    util.setSetting("auto_server", False)
                    return None

                if ping_results:
                    util.LOG("Server %s - %s: n%s" % (i, server['host'], repr(ping_results)))
                    avg_ping = self.averageList(ping_results)
                    if avg_ping != 0:
                        if avg_ping < ping or not ping:
                            res = i
                            ping = avg_ping
                            if update_settings:
                                util.LOG("Updating settings")
                                util.setSetting("server", str(i))
                    else:
                        util.LOG("Couldn't get ping")

        if res != None:
            xbmcgui.Dialog().ok('Done','Server with lowest ping ({0}) set to:'.format(ping),'',service['servers'][res]['name'])
        util.setSetting("auto_server", False)
        util.LOG("Done %s: %s" % (service['servers'][res]['name'], ping))
        return res

def downloadCallback(data):
    with downloadregistry.DownloadRegistry() as dr:
        dr.updateItem(URLDownloader.Download.deSerialize(data))
