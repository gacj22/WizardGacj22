# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
#------------------------------------------------------------

import xbmcgui
import xbmc
import datetime
import marcadores
import re
import tweetacces
import tweet

from core import httptools
from core.scrapertools import *
from core import filetools
from core import config

hashtag_file = filetools.join(config.get_data_path(), 'matchcenter', "hashtag.txt")
search_file = filetools.join(config.get_data_path(), 'matchcenter', "search_twitter.txt")
person_file = filetools.join(config.get_data_path(), 'matchcenter', "person_twitter.txt")


class TwitterDialog(xbmcgui.WindowXMLDialog):
        
    def __init__( self, *args, **kwargs ):
        self.isRunning = True
        self.hash = kwargs["hash"]
        self.standalone = kwargs["standalone"]
        self.tipo = kwargs["tipo"]
        self.equipo = kwargs["equipo"]
        self.teamObjs = {}
        self.last_id = ""
        self.tweet = 0
        self.wait = 0
        self.tweetitems = []
        self.filtro_rt = ""
        self.isRunningScores = False
        self.livescores = False


    def onInit(self):
        self.setCoordinateResolution(2)
        self.getControl(32552).setVisible(False)
        if self.standalone:
            self.getControl(33501).setVisible(False)

        if not self.standalone:
            if self.tipo == "go_reply":
                self.getControl(32542).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","birdtwitter.gif")) 
                self.getControl(32544).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","goal.png"))
                self.getControl(32543).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","twitterloadingfanart.jpg"))
            else:
                self.getControl(32540).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","goal.png"))
                self.getControl(32543).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","twitterloadingfanart.jpg"))
                self.getControl(32541).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","twitterloading.gif"))
        else:
            if self.tipo == "go_reply":
                self.getControl(32553).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","Twitterpajaroto.gif"))
            else:
                self.getControl(32540).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","goal.png"))
                self.getControl(32541).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","birdtwitter.gif"))
        xbmc.executebuiltin("SetProperty(loading-script-matchcenter-twitter,1,home)")
        self.getTweets()

        update_times = [0, 0.2, 0.4, 1, 2]
        twitter_update_time = update_times[int(config.get_setting("update_tweets"))]
        xbmc.executebuiltin("ClearProperty(loading-script-matchcenter-twitter,Home)")
        i=0
        if twitter_update_time and self.standalone:
            while self.isRunning:
                if self.wait*1000 >= twitter_update_time*60*1000:
                    if self.tweet < 19:
                        self.getControl(32501).removeItem(0)
                        self.tweet += 1
                        xbmc.sleep(100)
                        self.getControl(32501).addItem(self.tweetitems[self.tweet])
                    else:
                        self.tweet = 0
                        self.last_id = ""
                        self.getTweets()
                    self.wait = 0
                xbmc.sleep(1000)
                self.wait += 1

    def getTweets(self):
        self.check_reply = ""
        self.tweetitems = []
        if self.tipo == "persona" or self.equipo:
            if self.hash.startswith("@"):
                self.getControl(32500).setLabel(self.hash)
            else:
                self.getControl(32500).setLabel("@"+self.hash)
        elif self.tipo == "go_reply":
            self.getControl(32500).setLabel("[COLOR gold][B]Cargando tweet...[/B][/COLOR]")
            self.getControl(32500).setAnimations([('conditional', 'effect=fade start=0% end=100% time=300 loop=true condition=true',)])
            self.getControl(32552).setVisible(True)
        else:
            if " OR " in self.hash:
                self.getControl(32500).setLabel(self.hash.split(" OR ")[0])
            else:
                self.getControl(32500).setLabel(self.hash)
        if not self.standalone:
            if self.tipo == "go_reply":
               self.getControl(32553).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","Twitterpajaroto.gif"))
            else:
                self.getControl(32503).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","twitter_sm.png"))
            if self.tipo != "persona":
                self.getControl(32504).setImage(filetools.join(config.get_runtime_path(),"resources","skins",
                                                "Default","media","MatchCenter","dialog-bg-solid.png"))
        error = ""
        if self.tipo == "hashtag":
            tweets = tweet.get_tweets(None, self.hash, None, None, max_id=self.last_id, filtro_rt=self.filtro_rt)
        elif self.tipo == "busqueda":
            tweets = tweet.get_tweets(None, None, self.hash, None, max_id=self.last_id, filtro_rt=self.filtro_rt)
        elif self.tipo == "persona" or self.equipo:
            try:
                tweets, total = tweet.get_tweets(self.hash, None, None, None, max_id=self.last_id, filtro_rt=self.filtro_rt)
            except:
                tweets= None

            if tweets == "No autorizado":
                error = "Acceso no autorizado. No se puede mostrar el timeline"
                tweets = []
            if not self.standalone and tweets:
                banner = tweets[0]["banner"]
                if banner:
                    self.getControl(32502).setImage(banner)
                else:
                    self.getControl(32504).setImage(filetools.join(config.get_runtime_path(),"resources","skins",
                                                    "Default","media","MatchCenter","dialog-bg-solid.png"))
        else:
            tweets = tweet.get_tweets(None, None, None, self.hash, max_id=self.last_id)
            self.check_reply = "yes"
        if self.check_reply == "":
            try:
                self.last_id = tweets[-1]['id']
            except:
                self.last_id = "notuser"

        if "notuser" in self.hash or "notuser" in self.last_id or not tweets or "''" in self.hash and not error:
            if not self.standalone:
                self.getControl(32546).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","twitterloadingfanart.jpg"))
                self.getControl(32545).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","nouserfound.gif"))
                self.getControl(32547).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","nouserfoundtext.png"))
                if self.tipo == "hashtag":
                    if self.hash == "notuser":
                        self.getControl(32548).addLabel("[COLOR crimson][B]                  El hashtag no puede estar vacío...[/B][/COLOR]")
                    else:
                        self.hash = "notuser"
                        self.getControl(32548).addLabel("[COLOR yellow][B]                  Hashtag no encontrado. Trata de afinar con el nombre o prueba en la sección \"Trending Topic\"...[/B][/COLOR]")
                elif self.tipo == "busqueda":
                    if self.hash == "notuser":
                        self.getControl(32548).addLabel("[COLOR crimson][B]                  La búsqueda no puede estar vacía...[/B][/COLOR]")
                    else:
                        self.getControl(32548).addLabel("[COLOR yellow][B]                  No hay datos para esa búsqueda...[/B][/COLOR]")
                elif self.tipo == "persona" or self.equipo:
                    if self.hash == "notuser":
                        self.getControl(32548).addLabel("[COLOR crimson][B]                  El usuario no puede estar vacío...[/B][/COLOR]")
                    elif self.hash == "''":
                        self.getControl(32548).addLabel("[COLOR orange][B]                  NO existe ese usuario...[/B][/COLOR]")
                    else:   
                        self.getControl(32548).addLabel("[COLOR yellow][B]                  Usuario no encontrado. Trata de afinar con el nombre o prueba en la sección \"Buscar\"...[/B][/COLOR]")
            else:
                self.getControl(32542).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","nouserfound.gif"))
                self.getControl(32543).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","nouserfoundtext.png"))
                if self.tipo == "hashtag":
                    if self.hash == "notuser":
                        self.getControl(32544).addLabel("[COLOR crimson][B]                  El hashtag no puede estar vacío...[/B][/COLOR]")
                    else:
                        self.hash = "notuser"
                        self.getControl(32544).addLabel("[COLOR yellow][B]                  Hashtag no encontrado. Trata de afinar con el nombre o prueba en la sección \"Trending Topic\"...[/B][/COLOR]")
                elif self.tipo == "busqueda":
                    if self.hash == "notuser":
                        self.getControl(32544).addLabel("[COLOR crimson][B]                  La búsqueda no puede estar vacía...[/B][/COLOR]")
                    else:
                        self.getControl(32544).addLabel("[COLOR yellow][B]                  No hay datos para esa búsqueda...[/B][/COLOR]")
                elif self.tipo == "persona" or self.equipo:
                    if self.hash == "notuser":
                        self.getControl(32544).addLabel("[COLOR crimson][B]                  El usuario no puede estar vacío...[/B][/COLOR]")
                    elif self.hash == "''":
                        self.getControl(32544).addLabel("[COLOR orange][B]                  NO existe ese usuario...[/B][/COLOR]")
                    else:   
                        self.getControl(32544).addLabel("[COLOR yellow][B]                  Usuario no encontrado. Trata de afinar con el nombre o prueba en la sección \"Buscar\"...[/B][/COLOR]")
            self.isRunning = False
            self.hash = "notuser"
        if tweets:
            for _tweet in tweets:
                video_link = _tweet["videos"]
                try:
                    video = video_link[0]["url"]
                except:
                    video = ""
                try:
                    images = ", ".join(_tweet["images"])
                except:
                    images = []
                pepe = _tweet["twittercl"]
                td = self.get_timedelta_string(datetime.datetime.utcnow() - _tweet["date"])
                text = _tweet["text"].replace("\n", " ")
                phrase =_tweet["phrase"].replace("\n", " ")
                try:
                    item = xbmcgui.ListItem(text)
                except:
                    try:
                        item = xbmcgui.ListItem(text.encode('unicode-escape'))
                    except:        
                        item = xbmcgui.ListItem("Error cargando tweet...lo sentimos :(")

                item.setProperty("profilepic", _tweet["profilepic"])
                item.setProperty("author_rn","[B]" + _tweet["author_rn"] + "[/B]")
                item.setProperty("author","[B]" +"@" + _tweet["author"] + "[/B]")
                item.setProperty("timedelta", td)
                banner = _tweet["banner"]
                item.setProperty("text", text)
                item.setProperty("phrase", phrase)
                item.setProperty("twittercl", str(_tweet["twittercl"]))
                item.setProperty("url", str(_tweet["url"]))
                item.setProperty("banner", banner)
                item.setProperty("fav", _tweet["fav"])
                item.setProperty("rt", _tweet["rt"])
                item.setProperty("profilepic_rt", _tweet["profilepic_rt"])
                item.setProperty("profilepic_rtr", _tweet["profilepic_rtr"])
                item.setProperty("reply_rt", _tweet["reply_rt"])
                item.setProperty("banner_rt", _tweet["banner_rt"])
                item.setProperty("videos", video)
                item.setProperty("images", images)
                item.setProperty("profilepic_toreply", _tweet["profilepic_toreply"])
                item.setProperty("text_toreply", _tweet["text_toreply"])
                item.setProperty("mention_text", _tweet["mention_text"])
                item.setProperty("mention_profilepic", _tweet["mention_profilepic"])
                item.setProperty("mention_banner", _tweet["mention_banner"])
                item.setProperty("mention_url", str(_tweet["mention_url"]))
                item.setProperty("rt_rt", _tweet["rt_rt"])
                item.setProperty("fav_rt", _tweet["fav_rt"])
                item.setProperty("mention_rt", str(_tweet["mention_rt"]))
                item.setProperty("mention_fav", str(_tweet["mention_fav"]))
                item.setProperty("mention_name","[B]" +"@" + str( _tweet["mention_name"]) + "[/B]")
                item.setProperty("name_toreply","[B]" +"@" + str( _tweet["name_toreply"]) + "[/B]")
                item.setProperty("name_rt","[B]" +"@" + str( _tweet["name_rt"]) + "[/B]")
                item.setProperty("text_rt", _tweet["text_rt"])
                item.setProperty("minm_text", _tweet["minm_text"])
                item.setProperty("minm_name", _tweet["minm_name"])
                item.setProperty("minm_profilepic", _tweet["minm_profilepic"])
                item.setProperty("followers", str(_tweet["followers"]))
                item.setProperty("friends", str(_tweet["friends"]))
                item.setProperty("location", _tweet["location"])
                item.setProperty("go_tweet", unicode(_tweet["go_tweet"]))
                item.setProperty("thumb", _tweet["thumb"])
                self.tweetitems.append(item)
        self.getControl(32501).reset()
        if self.tweetitems:
            if self.standalone:
                self.getControl(32501).addItem(self.tweetitems[0])
            else:
                self.getControl(32501).addItems(self.tweetitems)

            self.setFocusId(32501)
        elif not self.tweetitems and self.tipo == "persona" and error:
            item = xbmcgui.ListItem(error)
            item.setProperty("text", error)
            self.getControl(32501).addItem(item)
            self.setFocusId(32501)
        if self.check_reply != "":
            self.onClick(32501)
        return


    def reset(self):
        file_save = hashtag_file
        if self.tipo == "busqueda":
            file_save = search_file
        elif self.tipo == "persona":
            file_save = person_file
        if filetools.exists(file_save):
            filetools.remove(file_save)
            self.stopRunning()
        return


    def stopRunning(self):
        self.isRunning = False
        self.isRunningScores = False
        self.close()


    def onAction(self,action):
        if action.getId() == 92 or action.getId() == 10:
            if self.hash == "notuser":
                self.stopRunning()
                self.reset()
            else:
                self.stopRunning()


    def onClick(self,controlId):
        if controlId == 32501:
            if not self.standalone:
                self.getControl(32542).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","birdtwitter.gif"))
                self.getControl(32540).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter",""))
                self.getControl(32541).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter",""))
                if self.check_reply != "":
                    self.getControl(32543).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter",""))
                else:
                    self.getControl(32543).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter",""))
                self.getControl(32544).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","goal.png"))
                self.getControl(32549).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter",""))
                self.getControl(32550).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter",""))
                self.getControl(32551).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter",""))
            else:
                self.getControl(32540).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","goal.png"))
                self.getControl(32541).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","birdtwitter.gif"))
            xbmc.executebuiltin("SetProperty(loading-script-matchcenter-Twitter,1,home)")
            check_url = ""
            url_short = ""
            title = ""
            videos = ""
            mention_text = self.getControl(controlId).getSelectedItem().getProperty("mention_text").replace("\n", " ")
            mention_profilepic = self.getControl(controlId).getSelectedItem().getProperty("mention_profilepic")
            mention_banner = self.getControl(controlId).getSelectedItem().getProperty("mention_banner")
            if mention_banner:
               mention_banner = mention_banner + '/1500x500'
            mention_url = self.getControl(controlId).getSelectedItem().getProperty("mention_url")
            text_toreply = self.getControl(controlId).getSelectedItem().getProperty("text_toreply")
            profilepic_toreply = self.getControl(controlId).getSelectedItem().getProperty("profilepic_toreply")
            text = self.getControl(controlId).getSelectedItem().getProperty("text")
            timedelta = self.getControl(controlId).getSelectedItem().getProperty("timedelta")
            author_rn = self.getControl(controlId).getSelectedItem().getProperty("author_rn")
            author = self.getControl(controlId).getSelectedItem().getProperty("author")
            phrase = self.getControl(controlId).getSelectedItem().getProperty("phrase")                     
            profilepic = self.getControl(controlId).getSelectedItem().getProperty("profilepic")
            banner = self.getControl(controlId).getSelectedItem().getProperty("banner")
            if banner:
                banner += '/1500x500'
            twittercl = self.getControl(controlId).getSelectedItem().getProperty("twittercl")

            if mention_text:
                twittercl = mention_url
            twittercl = twittercl.replace("dai.ly/", "www.dailymotion.com/embed/video/")
            if twittercl != "" and not "pbs.twimg.com/media" in str(twittercl):
                if "youtube" in twittercl or "youtu.be" in twittercl or "vine.co/" in twittercl or "periscope" in twittercl or ("vimeo.com" in twittercl and not "vimeo.com/user" in twittercl) or "dailymotion" in twittercl:
                    videos = twittercl
                    data_tcl = ""
                try:
                    data_tcl = httptools.downloadpage(twittercl)
                    if data_tcl.headers.get("location"):
                        data_tcl = httptools.downloadpage(data_tcl.headers.get("location"))
                    else:
                        data_tcl = data_tcl.data

                except:
                    content = ""
                    data_tcl = ""
                if data_tcl != "":
                    data_tcl = re.sub(r'\0','', data_tcl)
                    data_tcl = re.sub(r"\s{2}", "", data_tcl)
                    if "fb.me" in twittercl: 
                        check_video = find_single_match(data_tcl, 'url" content="(.*?)"')
                        check_video = check_video.replace("dai.ly/", "www.dailymotion.com/embed/video/")
                        if "youtube" in check_video or "youtu.be" in check_video or "vine.co/" in check_video or "periscope" in check_video or ("vimeo.com" in check_video and not "vimeo.com/user" in check_video) or "dailymotion" in check_video:
                            videos = check_video
                            data_tcl = ""
                    else:  
                        try:
                            check_video = find_single_match(data_tcl, '"og:video:url" content="(.*?)"')
                            check_video = check_video.replace("dai.ly/", "www.dailymotion.com/embed/video/")
                            if check_video == "":
                                check_video = find_single_match(data_tcl, '"og:url" content="(.*?)"')
                            if "youtube" in check_video or "youtu.be" in check_video or "vine.co/" in check_video or "periscope" in check_video or ("vimeo.com" in check_video and not "vimeo.com/user" in check_video) or "dailymotion" in check_video:
                                videos = check_video
                                data_tcl = ""
                        except: 
                            pass
                    title = find_single_match(data_tcl, 'title" content="([^<]+)"')
                    if title == "":
                        title = find_single_match(data_tcl, 'content="([^<]+)" property="og:title"')
                    if title == "":
                        title = find_single_match(data_tcl, '<title>([^<]+)<\/title')
                    content = find_single_match(data_tcl, '"twitter:description" content="([^<]+)"')
                    if content == "":
                        content = find_single_match(data_tcl, 'description" content="([^<]+)')
                    if content == "":
                        content=find_single_match(data_tcl, 'content="([^<]+)" property="og:description"') 
                    if content == "":
                        content = find_single_match(data_tcl, 'og:description" content="([^<]+)"')
                    if content == "":
                        content = find_single_match(data_tcl, '<p>([^<]+)/p>')

                    img = find_single_match(data_tcl, 'image" content="([^<]+)"')
                    if img == "":
                        img = find_single_match(data_tcl, 'content="([^<]+)" property="og:image"')
                    if img == "":
                        img = find_single_match(data_tcl, 'og:image" content="([^<]+)"')
                    if content == "":
                        url_short = find_single_match(data_tcl, 'URL=([^"]+)')
                        url_short = url_short.replace("dai.ly/", "www.dailymotion.com/embed/video/")
                        if "periscope" in url_short or "vimeo" in url_short or "youtube" in url_short or "youtu.be" in url_short or "vine.co/" in url_short or "periscope" in url_short or ("vimeo.com" in url_short and not "vimeo.com/user" in url_short) or "dailymotion" in url_short:
                            videos = check_video
                            data_short = ""
                            videos = url_short
                        else:
                            try:
                                data_short = httptools.downloadpage(url_short).data
                                data_short = re.sub(r'\0', '', data_short)
                                data_short = re.sub(r"\s{2}", "", data_short)
                                if "fb.me" in url_short:
                                    try:
                                       videos=find_single_match(data_short, '<link rel="canonical" href="([^<]+)"')
                                    except:
                                        pass
                                else:
                                    if not "twitter.com" in url_short or "twitter" in url_short and "og:image:user_generated" in data_short:
                                        title = find_single_match(data_short, 'title" content="([^<]+)"')
                                        if title == "":
                                            title = find_single_match(data_short, 'content="([^<]+)" property="og:title"')
                                        if title == "":
                                            title = find_single_match(data_short, '<title>([^<]+)<\/title')
                                        content = find_single_match(data_short, 'twitter:description" content="([^<]+)"')
                                        if content == "":
                                            content = find_single_match(data_short, 'description" content="([^<]+)"')
                                        if content == "":
                                            content = find_single_match(data_short, 'content="([^<]+)" property="og:description"')
                                        if content == "":
                                            content = find_single_match(data_short, '<p>([^<]+)</p>')
                                        img = find_single_match(data_short, 'image" content="([^<]+)"')
                                        if img == "":
                                            img = find_single_match(data_short, 'content="([^<]+)" property="og:image"')
                                        if img == "":
                                            img = find_single_match(data_short, 'og:image" content="([^<]+)"')
                                 
                                        if content == "" and "twitter" in str(twittercl):
                                            content = None
                                            img = None
                                            title = None
                                            check_url = "yes"
                                    else:
                                        content = None
                                        img = None
                                        check_url = "yes"
                            except:
                                content = None
                                img = None
                                check_url = "yes"
                else:
                    content = None
                    img = None
                    if "twitter" in str(twittercl):
                      check_url = "yes"

            else:
                content = None
                img = None
                if "twitter" in str(twittercl):
                    check_url = "yes" 
            if img and "profile_images" in img:
                content = None
                img = None
            if "twitter.com" in twittercl:
                content = ""
            
            rt = self.getControl(controlId).getSelectedItem().getProperty("rt")
            profilepic_rt = self.getControl(controlId).getSelectedItem().getProperty("profilepic_rt")
            banner_rt = self.getControl(controlId).getSelectedItem().getProperty("banner_rt") 
            if banner_rt:
                banner_rt += '/1500x500'
            
            text_rt = self.getControl(controlId).getSelectedItem().getProperty("text_rt")
            if text_rt:
                text_rt = text_rt.replace("\n", " ")
            fav = self.getControl(controlId).getSelectedItem().getProperty("fav")
            if not videos:
                videos = self.getControl(controlId).getSelectedItem().getProperty("videos")
            
            images = self.getControl(controlId).getSelectedItem().getProperty("images")
            images = re.sub(r",", "", images)
            images = images.split()
            if mention_url and str(images) == "[]":
                if "pbs.twimg.com" in mention_url:
                    images = mention_url.split()
            url = self.getControl(controlId).getSelectedItem().getProperty("url")
            if str(url) == "None":
                if "twitter.com" in twittercl: 
                    url = twittercl
                elif "twitter.com" in url_short:
                    url = url_short
                else:
                    url = ""
            if str(videos) == "" and not "youtube" in str(url) and not "youtu.be" in str(url):
                url_video = find_single_match(url, '/(\d+)')
                if url_video:
                    url_video = "https://twitter.com/i/videos/" + url_video
                    data_video = httptools.downloadpage(url_video).data
                    check_url_video = find_single_match(data_video, '<link rel="stylesheet" href="([^"]+)"')
                    if check_url_video != "":
                        videos = url_video
                        url = ""
                        content = None
                if not videos:
                    check_url = "nv"
            else:
                content = None
            
            if check_url == "yes" or mention_text and check_url == "nv":
                url = twittercl
            url = str(url).replace("dai.ly/", "www.dailymotion.com/embed/video/")
            if "youtube" in str(url) or "youtu.be" in str(url) or "vine.co/" in str(url) or "periscope" in str(url) or ("vimeo.com" in str(url) and not "vimeo.com/user" in str(url)) or "dailymotion" in str(url):
                videos = url
            if (url != "" and check_url == "yes" and not img) or (url != "" and check_url == "nv" and not img):
                if not "youtube" in url and not "youtu.be" in url:
                    try:
                        data_url = httptools.downloadpage(url)
                        if data_url.headers.get("location"):
                            data_url = httptools.downloadpage(data_url.headers.get("location"))
                        else:
                            data_url = data_url.data
                    except:
                        content = ""
                        data_url= ""

                    if data_url != "":
                        data_url = re.sub(r"\0", "", data_url)
                        if "twitter" in str(url) and "og:image:user_generated" in data_url:
                            url = find_multiple_matches(data_url, 'image" content="([^"]+)"')
                            if str(images) == "[]":
                                images = url
                                content = ""
                                title = ""
                        elif not ("twitter" or  "pbs.twimg.com") in str(url):
                            data_url = re.sub(r"\s{2}", "", data_url)
                            title = find_single_match(data_url, 'title" content="([^<]+)"')
                            if title == "":
                                title = find_single_match(data_url, 'content="([^<]+)" property="og:title"')
                            if title == "":
                                title = find_single_match(data_url, '<title>([^<]+)<\/title')
                            content = find_single_match(data_url, 'twitter:description" content="([^<]+)"')
                            if content == "":
                                content = find_single_match(data_url, 'description" content="([^<]+)"')
                            if content == "":
                                content = find_single_match(data_url, 'content="([^<]+)" property="og:description"')
                            if content == "":
                                content = find_single_match(data_url, '<p>([^<]+)</p>')
                            img = find_single_match(data_url, 'image" content="([^"]+)"')
                            if img == "":
                                img = find_single_match(data_url, 'content="([^<]+)" property="og:image"')
                            if img == "":
                                img = find_single_match(data_url, 'og:image" content="([^<]+)"')

                            if content == "":
                                try:
                                    url_short = find_single_match(data_url, 'URL=([^"]+)')
                                    data_short = httptools.downloadpage(url_short).data
                                    data_short = re.sub(r"\s{2}", "", data_short)
                                    if "twitter" in url_short and "og:image:user_generated" in data_short:
                                        url = find_multiple_matches(data_short, 'image" content="([^"]+)"')
                                        if str(images) == "[]":
                                            images = url
                                            content = ""
                                            title = ""
                                    elif not "twitter" in url_short:
                                        title = find_single_match(data_short, 'title" content="([^<]+)"')
                                        if title == "":
                                            title = find_single_match(data_short, 'content="([^<]+)" property="og:title"')
                                        if title == "":
                                            title = find_single_match(data_short, '<title>([^<]+)<\/title')
                                        content = find_single_match(data_short, 'twitter:description" content="([^<]+)"')
                                        if content == "":
                                            content = find_single_match(data_short, 'description" content="([^<]+)"')
                                        if content == "":
                                            content = find_single_match(data_short, 'content="([^<]+)" property="og:description"')
                                        if content == "":
                                            content = find_single_match(data_short, '<p>([^<]+)</p>')
                                        img = find_single_match(data_short, 'image" content="([^"]+)"')
                                        if img == "":
                                            img = find_single_match(data_short, 'content="([^<]+)" property="og:image"')
                                        if img == "":
                                            img = find_single_match(data_short, 'og:image" content="([^<]+)"')
                                
                                    else:
                                        title = None
                                        content = None
                                        img = None
                                except:
                                    title = None
                                    content = None
                                    img = None
                        else:
                            if str(images) == "[]":
                                images = []
                                images.append(url)
            if str(images) != "[]" and images != "":
               img = None
               url = None

            reply_rt = self.getControl(controlId).getSelectedItem().getProperty("reply_rt")
            profilepic_rtr = self.getControl(controlId).getSelectedItem().getProperty("profilepic_rtr")
            rt_rt = self.getControl(controlId).getSelectedItem().getProperty("rt_rt")
            fav_rt = self.getControl(controlId).getSelectedItem().getProperty("fav_rt")
            mention_rt = self.getControl(controlId).getSelectedItem().getProperty("mention_rt")
            mention_fav = self.getControl(controlId).getSelectedItem().getProperty("mention_fav")
            mention_name = self.getControl(controlId).getSelectedItem().getProperty("mention_name")
            name_toreply = self.getControl(controlId).getSelectedItem().getProperty("name_toreply")
            name_rt = self.getControl(controlId).getSelectedItem().getProperty("name_rt")
            minm_text = self.getControl(controlId).getSelectedItem().getProperty("minm_text")
            minm_name = self.getControl(controlId).getSelectedItem().getProperty("minm_name")
            minm_profilepic = self.getControl(controlId).getSelectedItem().getProperty("minm_profilepic")
            followers = self.getControl(controlId).getSelectedItem().getProperty("followers")
            friends = self.getControl(controlId).getSelectedItem().getProperty("friends")
            location = self.getControl(controlId).getSelectedItem().getProperty("location")
            go_tweet = self.getControl(controlId).getSelectedItem().getProperty("go_tweet")
            thumb = self.getControl(controlId).getSelectedItem().getProperty("thumb")

            if content:
                try:
                    test_content = unicode(content, "utf-8")
                    content = unicode(content, "utf-8", errors="replace").encode("utf-8")
                except:
                    content = unicode(content, "latin1", errors="replace").encode("utf-8")
                    if "\xc3" in content:
                        content = unicode(content, "utf-8", errors="replace").encode("utf-8")
            if title:
                try:
                    test_title = unicode(title, "utf-8")
                    title = unicode(title, "utf-8", errors="replace").encode("utf-8")
                except:
                    title = unicode(title, "latin1", errors="replace").encode("utf-8")
                    if "\xc3" in title:
                        title = unicode(title, "utf-8", errors="replace").encode("utf-8")
            xbmc.executebuiltin("ClearProperty(loading-script-matchcenter-twitter,Home)")
            tweetacces.start(rt,fav,videos,images,profilepic,timedelta,author_rn,author,phrase,text,banner,banner_rt,profilepic_rt,url,reply_rt,profilepic_rtr,content,img,profilepic_toreply,text_toreply,mention_text,mention_profilepic,mention_banner,rt_rt,fav_rt,mention_fav,mention_rt,mention_name,title,name_toreply,name_rt,text_rt,minm_text,minm_name,minm_profilepic,followers,friends,location,go_tweet,thumb)
            if self.check_reply == "yes":
                self.stopRunning()
                self.close()
            self.setFocusId(32501)
        elif controlId == 32514:
            self.reset()
        elif controlId == 32515:
            if not self.standalone:
                self.getControl(32549).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","moretweets.gif"))
                self.getControl(32540).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter",""))
                self.getControl(32541).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter",""))
                self.getControl(32543).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","twitterloadingfanart.jpg"))
                self.getControl(32550).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","moretweetsfan.gif"))
                self.getControl(32542).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter",""))
                self.getControl(32544).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter",""))
                self.getControl(32551).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","cargando+t.png"))

            xbmc.executebuiltin("SetProperty(loading-script-matchcenter-Twitter,1,home)")
            if self.standalone:
                self.wait = 0
                if self.tweet < 19:
                    self.getControl(32501).removeItem(0)
                    self.tweet += 1
                    xbmc.sleep(100)
                    self.getControl(32501).addItem(self.tweetitems[self.tweet])
                else:
                    self.tweet = 0
                    self.last_id = ""
                    self.getTweets()
            else:
                self.getTweets()
            self.setFocusId(32501)

            xbmc.executebuiltin("ClearProperty(loading-script-matchcenter-twitter,Home)")
        elif controlId == 32516 or controlId == 32517:
            if not self.standalone:
                self.getControl(32549).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","moretweets.gif"))
                self.getControl(32540).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter",""))
                self.getControl(32541).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter",""))
                self.getControl(32543).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","twitterloadingfanart.jpg"))
                self.getControl(32550).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","moretweetsfan.gif"))
                self.getControl(32542).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter",""))
                self.getControl(32544).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter",""))
                self.getControl(32551).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","cargando+t.png"))

            xbmc.executebuiltin("SetProperty(loading-script-matchcenter-Twitter,1,home)")
            if self.standalone:
                self.wait = 0
                self.tweet = 0
            self.last_id = ""
            if controlId == 32517:
                if self.filtro_rt:
                    self.filtro_rt = ""
                    self.getControl(32517).setLabel("Ocultar RTs")
                else:
                    self.filtro_rt = "retweets"
                    self.getControl(32517).setLabel("Mostrar RTs")

            self.getTweets()

            xbmc.executebuiltin("ClearProperty(loading-script-matchcenter-twitter,Home)")
        elif controlId == 32566 or controlId == 33501:
            if not self.livescores:
                self.livescores = True
                self.initLivescores()
            else:
                self.livescores = False
                self.isRunningScores = False
                controls = [33500, 33501, 33502, 33503]
                for c in controls:
                    self.getControl(c).setVisible(False)


    def get_timedelta_string(self, td):
        if td.days > 0:
            return "(Hace " + str(td.days) + " " + self.get_days_string(td.days) + ")"
        else:
            hours = td.seconds/3600
            if hours > 0:
                minutes = (td.seconds - hours*3600)/60
                if minutes > 0:
                    return "(Hace " + str(hours) + " " + self.get_hour_string(hours) + " y " + str(minutes) + " " + self.get_minutes_string(minutes) + ")"
                else:
                    return "(Hace " + str(hours) + " " + self.get_hour_string(hours) + ")"
            else:
                minutes = td.seconds/60
                if minutes > 0:
                    seconds = td.seconds - minutes*60
                    return "(Hace " + str(minutes) + " " + self.get_minutes_string(minutes) + " y " + str(seconds) + " " + self.get_seconds_string(seconds) + ")"
                else:
                    return "(Hace " + str(td.seconds) + " " + self.get_seconds_string(td.seconds) + ")"


    def get_days_string(self, days):
        if days == 1:
            return "día"
        else:
            return "días"


    def get_hour_string(self, hours):
        if hours == 1:
            return "hora"
        else:
            return "horas"


    def get_minutes_string(self, minutes):
        if minutes == 1:
            return "minuto"
        else:
            return "minutos"


    def get_seconds_string(self, seconds):
        if seconds == 1:
            return "segundo"
        else:
            return "segundos"


    def initLivescores(self):
        self.isRunningScores = True
        now = datetime.datetime.today()
        self.url = "http://www.resultados-futbol.com/livescore"
        self.filtro = ""
        self.refresh_score = []
        self.onlive = False
        self.resultados = {}
        self.livescoresThread()
        import threading
        t = threading.Thread(target=self.updatethread)
        t.setDaemon(True) 
        t.start()


    def livescoresThread(self):
        self.livescoresdata = marcadores.get_matches(self.url)
        self.setLivescores()
        return

    def updatethread(self):
        update_times = [0, 1, 2, 5, 10]
        livescores_update_time = update_times[int(config.get_setting("update_scores"))]
        i = 0
        if livescores_update_time:
            while self.isRunningScores:
                if (float(i*200)/(livescores_update_time*60*1000)).is_integer() and i != 0:
                    if self.onlive:
                        new_scores = marcadores.refresh_score()
                        for key, value in new_scores.items():
                            for it in self.items:
                                if key == it.getProperty("matchid"):
                                    result = it.getProperty("result").replace(" ", "")
                                    if result == value:
                                        continue
                                    if result == "-":
                                        result = "0-0"
                                        
                                    self.resultados[it.getProperty("matchid")] = value.split("-")[0] + " - " + value.split("-")[1]
                                    if value == "0-0":
                                        continue
                                    if (value.split("-")[0] != result.split("-")[0]) and (value.split("-")[1] != result.split("-")[1]):
                                        result = "[COLOR red]%s[/COLOR] - [COLOR red]%s[/COLOR]" % (value.split("-")[0], value.split("-")[1])
                                    elif value.split("-")[0] != result.split("-")[0]:
                                        result = "[COLOR red]%s[/COLOR] - %s" % (value.split("-")[0], value.split("-")[1])
                                    else:
                                        result = "%s - [COLOR red]%s[/COLOR]" % (value.split("-")[0], value.split("-")[1])
                                    self.refresh_score.append("Goooooooool en el %s %s %s"
                                                              % (it.getProperty("hometeam_long"),
                                                                 result, it.getProperty("awayteam_long")))
                                    continue
                    self.livescoresThread()
                xbmc.sleep(200)
                i += 1
        
    def setLivescores(self):
        self.getControl(33500).setLabel("")
        self.getControl(33502).setLabel("")
        self.next = ""
        self.prev = ""

        fin = 0
        juego = 0
        por_empezar = 0
        self.onlive = False
        now = datetime.datetime.today()
        self.items = []
        if self.livescoresdata:
            controls = [33500, 33501, 33502]
            for c in controls:
                self.getControl(c).setVisible(True)

            for partido in self.livescoresdata:
                if not partido.get("liga"):
                    continue
                item = xbmcgui.ListItem()
                if self.resultados.get(partido["matchid"]):
                    result = self.resultados[partido["matchid"]]
                else:
                    result = partido["score"]
                    
                item.setProperty('result', result)
                item.setProperty('hometeam_long', partido["team1"])
                item.setProperty('awayteam_long', partido["team2"])

                estado = partido["estado"]
                if re.search(r'(?i)Finalizado', estado) and partido["priority"] == 1:
                    try:
                        h, m = partido["hora"].split(":")
                        time_match = datetime.datetime(now.year, now.month, now.day, int(h), int(m))
                        diferencia = now - time_match
                        if diferencia.total_seconds() <= 7200:
                            estado = marcadores.get_minutos(partido["url"])
                    except:
                        pass

                item.setProperty('order', "-7")
                if "'" in estado:
                    if partido["priority"] == 1 or partido["priority"] == 2:
                        item.setProperty('order', estado.replace("'",""))
                else:
                    if re.search(r'(?i)Des', estado):
                        if partido["priority"] == 1 or partido["priority"] == 2:
                            item.setProperty('order', "45")
                    elif re.search(r'(?i)Aplazado', estado):
                        if partido["priority"] == 1:
                            item.setProperty('order', "-5")
                        elif partido["priority"] == 2:
                            item.setProperty('order', "-6")
                    elif re.search(r'(?i)Finalizado', estado):
                        if partido["priority"] == 1:
                            item.setProperty('order', "-2")
                        elif partido["priority"] == 2:
                            item.setProperty('order', "-4")
                    else:
                        if partido["priority"] == 1:
                            item.setProperty('order', "-1")
                        elif partido["priority"] == 2:
                            item.setProperty('order', "-3")
                if partido["priority"] != 1:
                    continue

                item.setProperty("matchid", partido["matchid"])
                if "'" in estado or re.search(r'(?i)Des', estado):
                    self.onlive = True
                if not re.search(r"(?i)finalizado|aplazado|Des|'", estado):
                    estado = partido["hora"]
                    result = " - "
                texto = "[COLOR darkorange]%s:[/COLOR] %s [COLOR white]%s[/COLOR] %s" % (estado, partido["team1"], result, partido["team2"])
                item.setProperty("texto", texto)
                self.items.append(item)
        
        if self.items:
            self.items.sort(key=lambda it:int(it.getProperty('order')), reverse=True)

            label = ""
            for it in self.items:
                label += it.getProperty("texto") + "  |  "
            self.getControl(33500).setLabel(label)
            if self.refresh_score:
                import threading
                t = threading.Thread(target=self.aviso_gol)
                t.setDaemon(True) 
                t.start()


    def aviso_gol(self):
        from random import randint
        images = ['balon_gol', 'gol_porteria', 'gol_corner']
        while self.refresh_score:
            self.getControl(33503).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","%s.gif" % images[randint(0, 2)]))
            self.getControl(33502).setLabel(self.refresh_score[0])
            self.getControl(33503).setVisible(True)
            self.getControl(33502).setAnimations([('conditional', 'effect=slide end=-1000 time=12000 condition=true')])
            self.getControl(33503).setAnimations([('conditional', 'effect=slide end=-1000 time=12000 condition=true')])
            for i in range(0, 12):
                if i % 2 == 0:
                    self.getControl(33502).setLabel(self.refresh_score[0].replace("[COLOR white]", "[COLOR red]"))
                else:
                    self.getControl(33502).setLabel(self.refresh_score[0].replace("[COLOR red]", "[COLOR white]"))
                if not self.isRunningScores:
                    self.refresh_score = []
                    break
                xbmc.sleep(1000)
            if len(self.refresh_score) > 1:
                self.refresh_score = self.refresh_score[1:]
            else:
                self.refresh_score = []

            self.getControl(33503).setVisible(False)
            self.getControl(33502).setLabel("")


def start(tipo, twitterhash=None, standalone=False, equipo=False, save_hashtag=True):
    file_save = hashtag_file
    if tipo == "busqueda":
        file_save = search_file
    elif tipo == "persona":
        file_save = person_file
    else:
        if tipo != "hashtag" and not equipo:
            twitterhash = tipo
            tipo = "go_reply"

    if not twitterhash:
        userInput = True
        if filetools.exists(file_save):
            from core import jsontools
            twitter_data = jsontools.load_json(filetools.read(file_save))
            twitterhash = twitter_data["hash"]
            userInput = False
    else:
        userInput = False

    if userInput:
        dialog = xbmcgui.Dialog()
        if tipo == "hashtag":
            twitterhash = dialog.input("Introduce un hashtag de Twitter", type=xbmcgui.INPUT_ALPHANUM)
        elif tipo == "busqueda":
            twitterhash = dialog.input("Introduce la búsqueda", type=xbmcgui.INPUT_ALPHANUM)
        elif tipo == "persona":
            twitterhash = dialog.input("¿A quién quieres buscar?", type=xbmcgui.INPUT_ALPHANUM)

        if len(twitterhash) != 0:
            if tipo == "hashtag" and not twitterhash.startswith("#"):
                twitterhash = "#"+twitterhash
            elif tipo == "busqueda":
                twitterhash = twitterhash.replace("#","")
            elif tipo == "persona":
                twitterhash = twitterhash.replace("@","")
        else:
            twitterhash = "notuser"
             

    if twitterhash and twitterhash != "notuser" and twitterhash != "''" and save_hashtag:
        #Save twitter hashtag
        if tipo == "hashtag":
            if twitterhash.startswith("#"):
                tweet.add_hashtag_to_twitter_history(twitterhash, tipo)
                tweet.savecurrenthash(twitterhash, file_save)
            else:
                tweet.add_hashtag_to_twitter_history("#"+twitterhash, tipo)
                tweet.savecurrenthash("#"+twitterhash, file_save)
        elif tipo == "persona":
            if twitterhash.startswith("@"):
                tweet.add_hashtag_to_twitter_history(twitterhash, tipo)
                tweet.savecurrenthash(twitterhash, file_save)
            else:
                tweet.add_hashtag_to_twitter_history("@"+twitterhash, tipo)
                tweet.savecurrenthash("@"+twitterhash, file_save)
        elif tipo == "busqueda":
            tweet.add_hashtag_to_twitter_history(twitterhash.replace("#", ""), tipo)
            tweet.savecurrenthash(twitterhash.replace("#", ""), file_save)

    if xbmc.getCondVisibility("Player.HasMedia"):
        main = TwitterDialog('script-matchcenter-Twitter_mini.xml', config.get_runtime_path(), hash=twitterhash, standalone=True, tipo=tipo, equipo=equipo)
        xbmc.executebuiltin("Dialog.Close(videoosd, true)")
    else:
        main = TwitterDialog('script-matchcenter-Twitter.xml', config.get_runtime_path(), hash=twitterhash, standalone=False, tipo=tipo, equipo=equipo)
    main.doModal()
    del main
