# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
#------------------------------------------------------------

import xbmcgui
import xbmc
import tweets
import os
import re
import time

from core import filetools
from core import config
from core import scrapertools
from core.scrapertools import decodeHtmlentities as dhe
from core import httptools
from datetime import datetime
from threading import Thread

exit_loop = False


class detailsDialog(xbmcgui.WindowXMLDialog):
        
    def __init__( self, *args, **kwargs ):
        self.author = kwargs["author"]
        self.author_rn = kwargs["author_rn"]
        self.profilepic = kwargs["profilepic"]
        self.banner = kwargs["banner"]
        self.text = kwargs["text"]
        self.text_toreply = kwargs["text_toreply"]
        self.phrase = kwargs["phrase"]
        self.profilepic_toreply = kwargs["profilepic_toreply"]
        self.url = kwargs["url"]
        self.timedelta = kwargs["timedelta"]
        self.content = kwargs["content"]
        try:
            self.content = dhe(scrapertools.htmlclean(self.content))
        except:
            pass
        self.img = kwargs["img"]
        self.rt = kwargs["rt"]
        self.profilepic_rt = kwargs["profilepic_rt"].replace('_normal','')
        self.banner_rt = kwargs["banner_rt"]
        self.reply_rt = kwargs["reply_rt"]
        self.profilepic_rtr = kwargs["profilepic_rtr"]
        self.fav = kwargs["fav"]
        self.mention_text = kwargs ["mention_text"]
        self.mention_profilepic = kwargs["mention_profilepic"]
        self.mention_banner = kwargs["mention_banner"]
        self.videos = kwargs["videos"]
        self.images = kwargs["images"]

        self.rt_rt = kwargs["rt_rt"]
        self.fav_rt = kwargs["fav_rt"]
        self.mention_rt = kwargs["mention_rt"]
        self.mention_fav = kwargs["mention_fav"]
        self.mention_name = kwargs["mention_name"]
        self.title = kwargs["title"]
        self.text_rt = kwargs["text_rt"]
        try:
            self.title = dhe(scrapertools.htmlclean(self.title))
        except:
            pass
        self.name_toreply = kwargs["name_toreply"]
        self.name_rt = kwargs["name_rt"]
        self.minm_text = kwargs["minm_text"]
        self.minm_name = kwargs["minm_name"]
        self.minm_profilepic = kwargs["minm_profilepic"]

        self.followers= kwargs["followers"]
        self.friends=kwargs["friends"]
        self.location=kwargs["location"]
        self.go_tweet = kwargs["go_tweet"]
        self.thumb = kwargs["thumb"]
        torrents_path = filetools.join(config.get_library_path(), 'gifs')
        
        if not os.path.exists(torrents_path):
            os.mkdir(torrents_path)
        self.gif = torrents_path

        if self.videos:
           self.content= None
           self.img=None

        osAndroid = xbmc.getCondVisibility('system.platform.android')
        if self.videos and "/tweet_video/" in self.videos and not osAndroid:
            dialog = xbmcgui.DialogProgressBG()
            dialog.create("[COLOR crimson]Cargando [/COLOR]"+ "[COLOR springgreen][B]Gif[/B][/COLOR]", "[COLOR yellow]Espere...[/COLOR]")
            dialog.update(20)
            os.chdir(torrents_path)
            from sys import platform
            import subprocess
            if platform.startswith("linux"):
                ffmpeg = filetools.join(config.get_runtime_path(), 'lib', 'matchcenter', 'Linux', 'ffmpeg')
                dialog.update(60)
                subprocess.call(ffmpeg + ' -i '+self.videos + ' -vf fps=20,scale=320:-1:flags=lanczos,palettegen=stats_mode=full  palette.png', shell=True)
                subprocess.call(ffmpeg + ' -i '+self.videos + ' -i palette.png -lavfi  "fps=20,scale=320:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=sierra2_4a" giftoguapo.gif', shell=True)

            elif platform == "darwin":
                ffmpeg = filetools.join(config.get_runtime_path(), 'lib', 'matchcenter', 'Mac', 'ffmpeg') 
                ffmpeg = re.sub(r' ', '\ ',ffmpeg)
                dialog.update(60)
                subprocess.call(ffmpeg + ' -i '+self.videos + ' -vf fps=20,scale=320:-1:flags=lanczos,palettegen=stats_mode=full  palette.png', shell=True)
                subprocess.call(ffmpeg + ' -i '+self.videos + ' -i palette.png -lavfi  "fps=20,scale=320:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=sierra2_4a" giftoguapo.gif', shell=True)
            
            elif platform == "win32" or platform == "cygwin":
                ffmpeg = filetools.join(config.get_runtime_path(), 'lib', 'matchcenter', 'Windows', 'ffmpeg.exe')
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                dialog.update(60)
                subprocess.call([ffmpeg, "-i", self.videos, "-vf", "fps=20,scale=320:-1:flags=lanczos,palettegen=stats_mode=full", "palette.png"], startupinfo=startupinfo, shell=True)
                subprocess.call([ffmpeg, "-i", self.videos, "-i", "palette.png", "-lavfi", "fps=20,scale=320:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=sierra2_4a", "giftoguapo.gif"], startupinfo=startupinfo, shell=True)

            dialog.update(100)
            self.thumb = filetools.join(torrents_path, "giftoguapo.gif")
            dialog.close()

        if self.content and not self.img and not self.images and not self.url or self.content and (not self.img or self.img == "") and str(self.images)=="[]" and (not self.url or not ".jpg"in self.url):
            self.img = "http://imgur.com/n53ZdBC.png"


    def onInit(self):
        self.setCoordinateResolution(2)
        self.getControl(32601).setVisible(False)
        self.getControl(33524).setVisible(False)
        self.getControl(33525).setVisible(False)
        self.getControl(33526).setVisible(False)
        self.getControl(33527).setVisible(False)
        self.getControl(33528).setVisible(False)
        self.getControl(33529).setVisible(False)
        self.getControl(33530).setVisible(False)
        self.getControl(33531).setVisible(False)
        self.getControl(33532).setVisible(False)
        self.getControl(33533).setVisible(False)
        self.getControl(33534).setVisible(False)
        self.getControl(33535).setVisible(False)
        self.getControl(33536).setVisible(False)
        self.getControl(33537).setVisible(False)
        self.settweets(self.author,self.author_rn, self.profilepic, self.timedelta, self.text,self.banner_rt,self.profilepic_rt,self.url,self.reply_rt,self.profilepic_rtr,self.videos,self.images,self.content,self.img,self.text_toreply,self.profilepic_toreply,self.mention_text,self.mention_profilepic,self.mention_banner,self.rt_rt,self.fav_rt,self.mention_rt,self.mention_fav,self.mention_name,self.title,self.name_toreply,self.name_rt,self.text_rt,self.minm_text,self.minm_name,self.minm_profilepic,self.followers,self.friends,self.location,self.go_tweet,self.thumb,self.gif)

    def settweets(self, profilepic, author,author_rn, delta, text,banner_rt,profilepic_rt,url,reply_rt,profilepic_rtr,videos,images,content,img,profilepic_toreply,text_toreply,mention_text,mention_banner,mention_profilepic,rt_rt,fav_rt,mention_rt,mention_fav,mention_name,title,name_toreply,name_rt,text_rt,minm_text,minm_name,minm_profilepic,followers,friends,location,go_tweet,thumb,gif):
        if self.profilepic_rt or profilepic_toreply:
            self.getControl(32503).setImage(self.profilepic)
            self.getControl(32500).setLabel(self.author)
            self.check_tp = None
        else:
            self.getControl(32503).setImage("")   
            self.getControl(32500).setLabel(self.author_rn)   
            self.getControl(32587).setImage(self.profilepic)
            self.getControl(32588).setLabel(self.author)
            self.check_tp = "ok"

        self.getControl(32530).addLabel("[COLOR powderblue]"+self.phrase+"[/COLOR]")
        if self.profilepic_rt or self.check_tp:
            if self.check_tp:
                if self.location == "":
                    self.location = "No.jpg"
                self.getControl(32531).setLabel(self.rt)
                self.getControl(32532).setLabel(self.fav)
                self.getControl(32533).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","rt_tweet.gif"))
                self.getControl(32534).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","fav_twitter.gif"))
                self.getControl(32591).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","seg_sigani.gif"))

                self.getControl(32592).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","siguiendo.png"))
                self.getControl(32593).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","seguidores.png"))

                self.getControl(32596).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","ciudad.png"))
                self.getControl(32594).setLabel(self.followers)
                self.getControl(32595).setLabel(self.friends)
                self.getControl(32597).addLabel(self.location)
            else:
                self.getControl(32531).setLabel(self.rt_rt)
                self.getControl(32532).setLabel(self.fav_rt)
                self.getControl(32533).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","rt_tweet.gif"))
                self.getControl(32534).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","fav_twitter.gif"))
                self.getControl(32582).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","birdtwitter.gif"))
                self.getControl(32583).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","retweet.png"))
        else:   
            self.getControl(32526).setLabel(self.rt)
            self.getControl(32527).setLabel(self.fav)
            self.getControl(32583).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter",""))
            self.getControl(32528).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","rt_tweet.gif"))
            self.getControl(32529).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","fav_twitter.gif"))

        if self.mention_text:
            if self.text_toreply:
                self.getControl(32565).setLabel(self.mention_rt)
                self.getControl(32566).setLabel(self.mention_fav)
                self.getControl(32567).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","rt_tweet.gif"))
                self.getControl(32568).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","fav_twitter.gif")) 
            else:      
                self.getControl(32535).setLabel(self.mention_rt)
                self.getControl(32536).setLabel(self.mention_fav)
                self.getControl(32537).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","rt_tweet.gif"))
                self.getControl(32538).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","fav_twitter.gif"))
          
        if self.mention_text:
            if self.minm_text:
                self.getControl(32586).setText("@"+self.minm_name)
                self.getControl(32585).setText(self.minm_text)
                self.getControl(32584).setImage(self.minm_profilepic)
                self.content = None
                self.img = None
                self.images = None
                self.url=None
            if self.profilepic_rt: 
                self.getControl(32546).addLabel(self.text) 
                self.getControl(32547).setLabel(self.name_rt)
                self.getControl(32539).setText(self.mention_name)
                self.getControl(32521).setText(self.mention_text)
                self.getControl(32519).setImage(self.mention_profilepic)
                self.getControl(32520).setImage(self.mention_banner)
            elif self.text_toreply:
                self.getControl(32560).addLabel(self.text) 
                self.getControl(32564).setText(self.mention_name)
                self.getControl(32563).setText(self.mention_text)
                self.getControl(32562).setImage(self.mention_profilepic)
                self.getControl(32561).setImage(self.mention_banner)
            else:
                self.getControl(32525).addLabel(self.text)
                self.getControl(32539).setText(self.mention_name) 
                self.getControl(32521).setText(self.mention_text)
                self.getControl(32519).setImage(self.mention_profilepic)
                self.getControl(32520).setImage(self.mention_banner)
            if self.content or self.images and not self.profilepic_rt:
                if self.img: 
                    self.getControl(32522).setImage(self.img)
                else:
                    if self.text_toreply:
                        if self.images: 
                            if len(images)==1: 
                                if self.content: 
                                    self.getControl(32579).setImage(self.images[0])
                                else:
                                    self.getControl(32578).setImage(self.images[0])  
                            elif len(images)==2:
                                self.getControl(32569).setImage(self.images[0])
                                self.getControl(32570).setImage(self.images[1])
                            elif len(images)==3:
                                self.getControl(32571).setImage(self.images[0])
                                self.getControl(32572).setImage(self.images[1])
                                self.getControl(32573).setImage(self.images[2])
                            elif len(images)>=4:
                                self.getControl(32574).setImage(self.images[0])  
                                self.getControl(32575).setImage(self.images[1])
                                self.getControl(32576).setImage(self.images[2])
                                self.getControl(32577).setImage(self.images[3])
                        else:
                            if self.url:
                                self.getControl(32522).setImage(self.url[0])
                    else:
                        if self.images: 
                            check_content = ""
                            if self.content:
                                check_content = "yes"
                            if len(images) == 1 or check_content != "":  
                                if self.content:
                                    self.getControl(32522).setImage(self.images[0])
                                else:
                                    self.getControl(32559).setImage(self.images[0])  
                            elif len(images)==2:
                                self.getControl(32554).setImage(self.images[0])
                                self.getControl(32555).setImage(self.images[1])
                            elif len(images)==3:
                                self.getControl(32556).setImage(self.images[0])
                                self.getControl(32557).setImage(self.images[1])
                                self.getControl(32558).setImage(self.images[2])
                            elif len(images)>=4:
                                self.getControl(32550).setImage(self.images[0])  
                                self.getControl(32551).setImage(self.images[1])
                                self.getControl(32552).setImage(self.images[2])
                                self.getControl(32553).setImage(self.images[3])
                        else:
                            if self.url:
                                self.getControl(32522).setImage(self.url[0])
                if self.content:
                    if not self.text_toreply:            
                        self.getControl(32523).setText(self.content)
                        self.getControl(32541).addLabel("[B]"+self.title+"[/B]") 
                    else:
                        self.getControl(32580).setText(self.content)
                        self.getControl(32581).addLabel("[B]"+self.title+"[/B]")
            elif self.content or self.images and self.profilepic_rt:
                if self.img: 
                    self.getControl(32544).setImage(self.img)
                else:
                    if self.images: 
                        self.getControl(32544).setImage(self.images[0])
                    else:
                        if self.url:
                            self.getControl(32544).setImage(self.url[0])
                    self.getControl(32523).setText(self.content)
            else:
                if self.images:
                    if len(images)==1:
                        self.getControl(32524).setImage(self.images[0])
                    elif len(images)==2:
                        self.getControl(32514).setImage(self.images[0])
                        self.getControl(32515).setImage(self.images[1])
                    elif len(images)==3:
                        self.getControl(32599).setImage(self.images[0])
                        self.getControl(32600).setImage(self.images[1])
                        self.getControl(32516).setImage(self.images[2])
                    elif len(images)>=4:
                        self.getControl(32510).setImage(self.images[0])  
                        self.getControl(32511).setImage(self.images[1])
                        self.getControl(32512).setImage(self.images[2])
                        self.getControl(32513).setImage(self.images[3])   
        else:
            if profilepic_rt:
                self.text_rt = "[COLOR yellow]"+self.text_rt+"[/COLOR]"
                self.getControl(32501).setText(self.text_rt)
            else:   
                self.getControl(32501).setText(self.text)       

        if self.text_toreply:
            self.getControl(32517).setText(self.text_toreply)
            self.getControl(32518).setImage(self.profilepic_toreply)
            self.getControl(32543).setLabel(self.name_toreply)
            self.getControl(32601).setVisible(True) 
            self.setFocusId(32601)
        if self.banner_rt:
            self.getControl(32502).setImage(self.banner_rt)
        elif self.banner: 
            self.getControl(32502).setImage(self.banner)
        else:
            self.getControl(32502).setImage(filetools.join(config.get_runtime_path(),"resources","skins",
                                            "Default","media","MatchCenter","dialog-bg-solid.png"))
        if self.profilepic_rt and not self.mention_text :
            self.getControl(32504).setImage(self.profilepic_rt)
            self.getControl(32548).setLabel(self.name_rt)
        else:
            self.getControl(32545).setImage(self.profilepic_rt)
        if self.content and not self.mention_text:
            if self.img: 
               self.getControl(32508).setImage(self.img)
            else:
                if self.images: 
                    self.getControl(32508).setImage(self.images[0])
                else:
                    if self.url:
                        self.getControl(32508).setImage(self.url[0])
            self.getControl(32509).setText(self.content)
            self.getControl(32549).addLabel("[B]"+self.title+"[/B]")

        else:
            if self.images and not self.mention_text and not self.videos:
                if len(images)==1:
                    self.getControl(32505).setImage(self.images[0])
                elif len(images)==2:
                    self.getControl(32514).setImage(self.images[0])
                    self.getControl(32515).setImage(self.images[1])
                elif len(images)==3:
                    self.getControl(32599).setImage(self.images[0])
                    self.getControl(32600).setImage(self.images[1])
                    self.getControl(32516).setImage(self.images[2])
                elif len(images)>=4:
                    self.getControl(32510).setImage(self.images[0])  
                    self.getControl(32511).setImage(self.images[1])
                    self.getControl(32512).setImage(self.images[2])
                    self.getControl(32513).setImage(self.images[3])
            else:
                if self.url and not self.profilepic_rtr:
                    if len(url)==1:
                        self.getControl(32505).setImage(self.url[0])
                    elif len(url)==2:
                        self.getControl(32514).setImage(self.url[0])
                        self.getControl(32515).setImage(self.url[1])
                    elif len(url)==3:
                        self.getControl(32599).setImage(self.url[0])
                        self.getControl(32600).setImage(self.url[1])
                        self.getControl(32516).setImage(self.url[3])
                    elif len(url)>=4:
                        self.getControl(32510).setImage(self.url[0])  
                        self.getControl(32511).setImage(self.url[1])
                        self.getControl(32512).setImage(self.url[2])
                        self.getControl(32513).setImage(self.url[3])    
                else:
                    if self.profilepic_rtr:  
                        self.getControl(32506).setImage(self.profilepic_rtr)
                        self.getControl(32507).setText(self.reply_rt)
                self.setFocusId(32601)

        if self.videos:
            if "i/videos" in self.videos:
                vp = httptools.downloadpage(self.videos).data
                self.videos = scrapertools.find_single_match(vp, 'video_url.*?(http.*?)&')
                self.videos = re.sub(r'\\', '', self.videos)
            
            if "youtube" in self.videos or "youtu.be" in self.videos or "periscope" in self.videos or "vine" in self.videos:
                if "periscope" in self.videos:
                    pd = httptools.downloadpage(self.videos).data
                    thumb = scrapertools.find_single_match(pd, 'property="og:image" content="([^<]+)"')
                    self.thumb = re.sub(r'amp;', '', thumb)
                    video = scrapertools.find_single_match(pd, 'property="og:url" content="([^<]+)"') 
                    if "undefined" in video:
                        self.videos = "novideo"	  
                        self.thumb = filetools.join(config.get_runtime_path(),"resources","images","matchcenter","periscopenotfound.jpg")
                elif "vine" in self.videos:
                    dialog = xbmcgui.DialogProgressBG()
                    dialog.create("[COLOR crimson]Cargando[/COLOR]"+ "[COLOR springgreen][B] Vine[/B][/COLOR]", "[COLOR yellow]Espere........[/COLOR]")
                    from core import jsontools
                    id_vine = scrapertools.find_single_match(self.videos, 'vine.co/v/([A-z0-9]+)')
                    url_proxy = "https://archive.vine.co/posts/%s.json" % id_vine
                    url = "https://de.hideproxy.me/includes/process.php?action=update"
                    post = "u=%s&proxy_formdata_server=de&allowCookies=1&encodeURL=1&encodePage=0&stripObjects=0&stripJS=0&go=" % url_proxy
                    dialog.update(50)
                    while True:
                        response = httptools.downloadpage(url, post, follow_redirects=False)
                        if response.headers.get("location"):
                            url = response.headers["location"]
                            post = ""
                        else:
                            data = response.data
                            break

                    data = jsontools.load_json(data)
                    if "videoUrl" in data:
                       dialog.update(100)
                       dialog.close()
                       self.videos = data["videoUrl"]
                       self.thumb = data["thumbnailUrl"]
                    else:
                       dialog.update(100)
                       dialog.close() 
                       self.videos = "vine.co/novideo"
                       self.thumb = "http://imgur.com/s4DW4hp.jpg"
                else:  
                    video = re.sub(r'&.*', '', self.videos)
                    thumb = scrapertools.find_single_match(video,'v=([0-9A-Za-z_-]{11})')
                    if thumb == "":
                       thumb = scrapertools.find_single_match(video,'be/([0-9A-Za-z_-]{11})')
                    self.thumb = "http://img.youtube.com/vi/%s/0.jpg" % thumb
            if "vimeo" in self.videos or "dailymotion" in self.videos:
                data_v = httptools.downloadpage(self.videos).data
                self.thumb = scrapertools.find_single_match(data_v, ' <meta property="og:image:secure_url" content="([^"]+)"')
                if not self.thumb and "vimeo" in self.videos:
                    self.thumb = scrapertools.find_single_match(data_v, '"thumbs":\{.*?:"([^"]+)"')
                if not self.thumb and "dailymotion" in self.videos:
                    self.thumb = scrapertools.find_single_match(data_v, '"poster_url":"([^"]+)"').replace("\\", "")                    

            if self.thumb and not self.mention_text:
                self.getControl(33525).setImage(self.thumb)
                self.getControl(33525).setVisible(True)      
            else:
                if len(self.images) == 0: 
                    self.getControl(32559).setImage(self.thumb)
                self.getControl(33526).setVisible(True)
                self.getControl(33526).setAnimations([('conditional', 'effect=zoom start=0% end=100% center=auto delay=700 time=2000 condition=true tween=elastic',),('unfocus', 'effect=zoom start=110% end=100% center=auto time=700 tween=elastic easing=out',), ('focus', 'effect=zoom start=80% end=110% time=200 center=auto',),('WindowClose','effect=rotatey center=500 start=0% end=-300% time=800 condition=true',)])
                if "periscope" in self.videos:
                    self.getControl(33526).setAnimations([('conditional', 'effect=zoom start=0% end=100% center=auto delay=1200 time=1000 condition=true tween=elastic',),('unfocus', 'effect=zoom start=110% end=100% center=auto time=700 tween=elastic easing=out',), ('focus', 'effect=zoom start=80% end=110% time=200 center=auto',),('WindowClose','effect=rotatey center=500 start=0% end=-300% time=800 condition=true',)])
                    self.getControl(33529).setVisible(True)
                elif "vimeo" in self.videos:
                    self.getControl(33526).setAnimations([('conditional', 'effect=zoom start=0% end=100% center=auto delay=1200 time=1000 condition=true tween=elastic',),('unfocus', 'effect=zoom start=110% end=100% center=auto time=700 tween=elastic easing=out',), ('focus', 'effect=zoom start=80% end=110% time=200 center=auto',),('WindowClose','effect=rotatey center=500 start=0% end=-300% time=800 condition=true',)])
                    self.getControl(33531).setVisible(True)
                elif "dailymotion" in self.videos:
                    self.getControl(33526).setAnimations([('conditional', 'effect=zoom start=0% end=100% center=auto delay=1200 time=1000 condition=true tween=elastic',),('unfocus', 'effect=zoom start=110% end=100% center=auto time=700 tween=elastic easing=out',), ('focus', 'effect=zoom start=80% end=110% time=200 center=auto',),('WindowClose','effect=rotatey center=500 start=0% end=-300% time=800 condition=true',)])
                    self.getControl(33533).setVisible(True)
                elif "youtube" in self.videos:
                    self.getControl(33526).setAnimations([('conditional', 'effect=zoom start=0% end=100% center=auto delay=1200 time=1000 condition=true tween=elastic',),('unfocus', 'effect=zoom start=110% end=100% center=auto time=700 tween=elastic easing=out',), ('focus', 'effect=zoom start=80% end=110% time=200 center=auto',),('WindowClose','effect=rotatey center=500 start=0% end=-300% time=800 condition=true',)])
                    self.getControl(33535).setVisible(True)
                elif "vine" in self.videos:
                    self.getControl(33526).setAnimations([('conditional', 'effect=zoom start=0% end=100% center=auto delay=1200 time=1000 condition=true tween=elastic',),('unfocus', 'effect=zoom start=110% end=100% center=auto time=700 tween=elastic easing=out',), ('focus', 'effect=zoom start=80% end=110% time=200 center=auto',),('WindowClose','effect=rotatey center=500 start=0% end=-300% time=800 condition=true',)])
                    self.getControl(33537).setVisible(True)
                if "novideo" in self.videos:
                    self.getControl(33526).setVisible(False)
            if not "/tweet_video/" in self.videos:
                self.getControl(33524).setVisible(True)
                self.getControl(33524).setAnimations([('conditional', 'effect=zoom start=0% end=100% center=auto delay=700 time=2000 condition=true tween=elastic',),('unfocus', 'effect=zoom start=110% end=100% center=auto time=700 tween=elastic easing=out',), ('focus', 'effect=zoom start=80% end=110% time=200 center=auto',),('WindowClose','effect=rotatey center=500 start=0% end=-300% time=800 condition=true',)])
                if "periscope" in self.videos:
                    self.getControl(33524).setAnimations([('conditional', 'effect=zoom start=0% end=100% center=auto delay=1200 time=1000 condition=true tween=elastic',),('unfocus', 'effect=zoom start=110% end=100% center=auto time=700 tween=elastic easing=out',), ('focus', 'effect=zoom start=80% end=110% time=200 center=auto',),('WindowClose','effect=rotatey center=500 start=0% end=-300% time=800 condition=true',)])
                    self.getControl(33528).setVisible(True)
                elif "vimeo" in self.videos:
                      self.getControl(33524).setAnimations([('conditional', 'effect=zoom start=0% end=100% center=auto delay=1200 time=1000 condition=true tween=elastic',),('unfocus', 'effect=zoom start=110% end=100% center=auto time=700 tween=elastic easing=out',), ('focus', 'effect=zoom start=80% end=110% time=200 center=auto',),('WindowClose','effect=rotatey center=500 start=0% end=-300% time=800 condition=true',)])
                      self.getControl(33530).setVisible(True)
                elif "dailymotion" in self.videos:
                      self.getControl(33524).setAnimations([('conditional', 'effect=zoom start=0% end=100% center=auto delay=1200 time=1000 condition=true tween=elastic',),('unfocus', 'effect=zoom start=110% end=100% center=auto time=700 tween=elastic easing=out',), ('focus', 'effect=zoom start=80% end=110% time=200 center=auto',),('WindowClose','effect=rotatey center=500 start=0% end=-300% time=800 condition=true',)])
                      self.getControl(33532).setVisible(True)
                elif "youtube" in self.videos:
                      self.getControl(33524).setAnimations([('conditional', 'effect=zoom start=0% end=100% center=auto delay=1200 time=1000 condition=true tween=elastic',),('unfocus', 'effect=zoom start=110% end=100% center=auto time=700 tween=elastic easing=out',), ('focus', 'effect=zoom start=80% end=110% time=200 center=auto',),('WindowClose','effect=rotatey center=500 start=0% end=-300% time=800 condition=true',)])
                      self.getControl(33534).setVisible(True)
                elif "vine" in self.videos:
                     self.getControl(33524).setAnimations([('conditional', 'effect=zoom start=0% end=100% center=auto delay=1200 time=1000 condition=true tween=elastic',),('unfocus', 'effect=zoom start=110% end=100% center=auto time=700 tween=elastic easing=out',), ('focus', 'effect=zoom start=80% end=110% time=200 center=auto',),('WindowClose','effect=rotatey center=500 start=0% end=-300% time=800 condition=true',)])
                     self.getControl(33536).setVisible(True)
                if "novideo" in self.videos:
                    self.getControl(33524).setVisible(False)
            else:
                self.getControl(33527).setVisible(True)

            if xbmc.getCondVisibility('[Control.IsVisible(33524)]'):
                self.setFocusId(33524)
            else:
                self.setFocusId(33526)
        elif xbmc.getCondVisibility('[Control.IsVisible(32601)]'):
            self.setFocusId(32601)
        else:
            self.setFocusId(32500)


    def onClick(self,controlId):
        if controlId == 32601: 
           take_tweet = tweets.start(self.go_tweet)
        elif controlId == 33524 or controlId == 33526:
            url = self.videos
            main = videoDialog('script-matchcenter-VideoTwitter.xml', config.get_runtime_path(), url=url)
            main.doModal()
            del main
        elif controlId == 32500 or controlId == 32588 or controlId == 32547 or controlId == 32548 or controlId == 32543:
            hashtag = self.getControl(controlId).getLabel().replace("[B]", "").replace("[/B]", "")
            if hashtag.startswith("@"):
                hashtag = hashtag[1:]
            tweets.start("persona", hashtag, save_hashtag=False)


    def onAction(self,action):
        if action.getId() == 92 or action.getId() == 10:
            try:
                if os.path.exists(filetools.join(self.gif, "giftoguapo.gif")):
                    os.remove(filetools.join(self.gif, "giftoguapo.gif"))
                if os.path.exists(filetools.join(self.gif, "palette.png")):
                    os.remove(filetools.join(self.gif, "palette.png"))
            except:
                pass
            self.close()


def start(rt=None,fav=None,videos=None,images=None,profilepic=None,timedelta=None,author_rn=None,author=None,phrase=None,text=None,banner=None,banner_rt=None,profilepic_rt=None,url=None,reply_rt=None,profilepic_rtr=None,content=None,img=None,profilepic_toreply=None,text_toreply=None,mention_text=None,mention_profilepic=None,mention_banner=None,rt_rt=None,fav_rt=None,mention_rt=None,mention_fav=None,mention_name=None,title=None,name_toreply=None,name_rt=None,text_rt=None,minm_text=None,minm_name=None,minm_profilepic=None,followers=None,friends=None,location=None,go_tweet=None,thumb=None):
    main = detailsDialog('script-matchcenter-Tweetsacces.xml', config.get_runtime_path(), rt=rt,fav=fav,videos=videos,images=images,profilepic=profilepic,timedelta= timedelta,author=author,author_rn=author_rn,phrase=phrase,text=text,banner=banner,banner_rt=banner_rt,profilepic_rt=profilepic_rt,url=url,reply_rt=reply_rt,profilepic_rtr=profilepic_rtr,content=content,img=img,profilepic_toreply=profilepic_toreply,text_toreply=text_toreply,mention_text=mention_text,mention_profilepic=mention_profilepic,mention_banner=mention_banner,rt_rt=rt_rt,fav_rt=fav_rt,mention_rt=mention_rt,mention_fav=mention_fav,mention_name=mention_name,title=title,name_toreply=name_toreply,name_rt=name_rt,text_rt=text_rt,minm_text=minm_text,minm_name=minm_name,minm_profilepic=minm_profilepic,followers=followers,friends=friends,location=location,go_tweet=go_tweet,thumb=thumb)
    main.doModal()
    del main


class videoDialog(xbmcgui.WindowXMLDialog):
    def __init__( self, *args, **kwargs ):
        self.url = kwargs["url"]
        self.player = None

    def onInit(self):
        self.setCoordinateResolution(2)
        self.getControl(14).setVisible(False)
        self.getControl(11).setVisible(False)
        self.getControl(10).setVisible(False)
        self.getControl(6).setVisible(False)
        self.getControl(12).setVisible(False)
        self.getControl(1).setVisible(False)
        self.getControl(16).setVisible(False)
        self.getControl(17).setVisible(False)
        self.getControl(18).setVisible(False)
        self.getControl(19).setVisible(False)
        self.getControl(20).setVisible(False)
        self.getControl(21).setVisible(False)
        self.getControl(22).setVisible(False)
        self.getControl(23).setVisible(False)
        self.url = self.url.replace("youtu.be/", "www.youtube.com/watch?v=")
        if "youtube" in self.url or "vine.co/" in self.url or "periscope" in self.url:
            from core import servertools
            try:
                if "youtube" in self.url:
                    dialog = xbmcgui.DialogProgressBG()
                    dialog.create("[COLOR crimson]Cargando[/COLOR]"+ "[COLOR floralwhite][B] You[/B][/COLOR]"+"[COLOR red][B]tube[/B][/COLOR]", "[COLOR yellow]Espere........[/COLOR]")
                    self.getControl(7).setVisible(False)
                    self.getControl(13).setVisible(False)
                    self.getControl(1).setVisible(True)
                    self.getControl(11).setVisible(True)
                    self.getControl(20).setVisible(True)
                    self.getControl(21).setVisible(True)
                    urls, puede, motivo = servertools.resolve_video_urls_for_playing("youtube", self.url)
                    dialog.update(60)
                    if puede:
                        url = urls[-1][1]
                        dialog.update(100)
                elif "periscope" in self.url:
                    self.getControl(6).setVisible(True)
                    self.getControl(7).setVisible(True)
                    self.getControl(12).setVisible(True)
                    dialog = xbmcgui.DialogProgressBG()
                    dialog.create("[COLOR crimson]Cargando[/COLOR]"+ "[COLOR skyblue][B] Periscope[/B][/COLOR]", "[COLOR yellow]Espere........[/COLOR]")

                    dialog.update(30)
                    from lib import youtube_dl
                    ydl = youtube_dl.YoutubeDL({'outtmpl': u'%(id)s%(ext)s', 'no_color': True, 'ie_key': 'periscope'})
                    result = ydl.extract_info(self.url, download=False)
                    dialog.update(50)
                    if 'formats' in result:
                        for entry in result['formats']:
                            url = entry['url']
                            if entry['http_headers'].get('Cookie'):
                                cookie = entry['http_headers']['Cookie'] 
                                url += "|Cookie=" + cookie
                                
                            dialog.update(80)
                            if not "live" in url or "-replay-direct-live" in url:
                                self.getControl(1).setVisible(True)
                                self.getControl(11).setVisible(True)
                            else:
                                self.getControl(13).setVisible(True)
                            dialog.update(100)
                else:
                    url = self.url
                    self.getControl(7).setVisible(False)
                    self.getControl(13).setVisible(False)
                    self.getControl(1).setVisible(True)
                    self.getControl(11).setVisible(True)
                    self.getControl(22).setVisible(True)
                    self.getControl(23).setVisible(True)
                xlistitem = xbmcgui.ListItem(path=url)
                pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
                pl.clear()
                pl.add(url, xlistitem)
                self.player = xbmc.Player()
                try:
                    self.player.play(pl, windowed=True)
                except:
                    try: 
                        dialog.close()
                    except:
                        xbmc.log("no dialog")
                    xbmc.executebuiltin('Notification([COLOR yellow][B]Video[/B][/COLOR], [COLOR green][B]'+'no disponible'.upper()+'[/B][/COLOR],5000,"http://imgur.com/GbCETlA.png")')
                if xbmc.Player().isPlaying:
                    try: 
                        dialog.close()
                    except:
                        xbmc.log("no dialog")
                while xbmc.Player().isPlaying():
                    xbmc.sleep(1000)
                self.close()
            except:
                try: 
                    dialog.close()
                except:
                    xbmc.log("no dialog")
                self.close()
        elif "vimeo" in self.url or "dailymotion" in self.url:
            from core import servertools
            try:
                server = "vimeo"
                color = "skyblue"
                if not "vimeo" in self.url:
                    server = "dailymotion"
                    color = "dodgerblue"
                    self.getControl(18).setVisible(True)
                    self.getControl(19).setVisible(True)
                else:
                    self.getControl(16).setVisible(True)
                    self.getControl(17).setVisible(True)
                dialog = xbmcgui.DialogProgressBG()
                dialog.create("[COLOR crimson]Cargando [/COLOR]"+ "[COLOR %s][B] %s[/B][/COLOR]" % (color,server.capitalize()), "[COLOR yellow]Espere........[/COLOR]")
                self.getControl(7).setVisible(False)
                self.getControl(13).setVisible(False)
                self.getControl(1).setVisible(True)
                self.getControl(11).setVisible(True)
                try:
                    urls = servertools.findvideosbyserver(self.url, server)
                    if urls:
                        urls, puede, motivo = servertools.resolve_video_urls_for_playing(server, urls[0][1])
                except:
                    try:
                        link = httptools.downloadpage(self.url).data
                        self.url = scrapertools.find_single_match(link,'"og:video:url" content="(.*?)"')
                        urls = servertools.findvideosbyserver(self.url, server)
                        if urls:
                            urls, puede, motivo = servertools.resolve_video_urls_for_playing(server, urls[0][1])
                    except:
                        pass
                dialog.update(60)
                if puede:
                    url = urls[-1][1]
                    dialog.update(100)
                xlistitem = xbmcgui.ListItem(path=self.url)
                pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
                pl.clear()
                pl.add(url, xlistitem)
                self.player = xbmc.Player()
                try:
                    self.player.play(pl, windowed=True)
                except:
                    try: 
                        dialog.close()
                    except:
                        xbmc.log("no dialog")  
                    xbmc.executebuiltin('Notification([COLOR yellow][B]Video[/B][/COLOR], [COLOR green][B]'+'no disponible'.upper()+'[/B][/COLOR],5000,"http://imgur.com/GbCETlA.png")') 
                if xbmc.Player().isPlaying:
                    try: 
                        dialog.close()
                    except:
                        xbmc.log("no dialog")
                while xbmc.Player().isPlaying():
                    xbmc.sleep(1000)
                self.close()
            except:
                try: 
                    dialog.close()
                except:
                    xbmc.log("no dialog")
                self.close()
                xbmc.executebuiltin('Notification([COLOR yellow][B]Video[/B][/COLOR], [COLOR green][B]'+'no disponible'.upper()+'[/B][/COLOR],5000,"http://imgur.com/GbCETlA.png")')    
        else:
            self.getControl(7).setVisible(False)
            self.getControl(13).setVisible(False)
            self.getControl(1).setVisible(True)
            self.getControl(11).setVisible(True)
            xlistitem = xbmcgui.ListItem(path=self.url)
            pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            pl.clear()
            pl.add(self.url, xlistitem)
            self.player = xbmc.Player()
            try:
                self.player.play(pl, windowed=True)
            except:                    
                xbmc.executebuiltin('Notification([COLOR yellow][B]Video[/B][/COLOR], [COLOR green][B]'+'no disponible'.upper()+'[/B][/COLOR],5000,"http://imgur.com/GbCETlA.png")')
            while xbmc.Player().isPlaying():
                xbmc.sleep(1000)
            self.close()


    def onAction(self, action):
        global exit_loop
        if action.getId() == 92 or action.getId() == 10:
            if self.player:
                exit_loop = True
                if xbmc.getCondVisibility('Control.IsVisible(10)'): 
                    self.getControl(10).setVisible(False)
                else:
                    self.getControl(10).setVisible(True)
        elif action.getId() == 107:
            if self.player:
                exit_loop = False  
                self.th = Thread(target=self.in_out)
                self.th.setDaemon(True)
                self.th.start()
        elif 1 <= action.getId() <= 4 and not xbmc.getCondVisibility('[Control.IsVisible(14)]'):
            self.getControl(14).setVisible(True)
            if xbmc.getCondVisibility('[Control.IsVisible(9)]'):
                self.setFocusId(29)
            else:
                self.setFocusId(24)
            exit_loop = False  
            self.th = Thread(target=self.in_out)
            self.th.setDaemon(True)
            self.th.start()  

              
    def in_out(self):
        global exit_loop
        self.getControl(14).setVisible(True)
        while datetime.now().second % 8 != 0:
            if exit_loop or not xbmc.Player().isPlaying():
                break
        self.getControl(14).setVisible(False)
