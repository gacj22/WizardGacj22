# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
#------------------------------------------------------------

import re
import xbmcgui
import xbmc
import datetime
import matchhistory
import marcadores
import infopilotos
import time

from core import filetools
from core import config
from core import httptools
from core import scrapertools
from core import jsontools


class detailsDialog(xbmcgui.WindowXMLDialog):
    def __init__( self, *args, **kwargs ):
        self.standalone = kwargs["standalone"]
        self.modalidad = kwargs["modalidad"]
        self.isRunning = True


    def onInit(self):
        self.setCoordinateResolution(2)
        self.url = ""
        self.race = None
        self.session = 0
        self.load = True
        self.load_plus = True
        self.data = ""
        self.live = True
        self.index = 0
        self.items = []
        self.comentario = 0
        self.check_info = False
        self.data_d = ""
        if self.standalone:
            self.getControl(32507).setVisible(False)
            self.getControl(32508).setVisible(False)
            self.getControl(32509).setVisible(False)
            self.getControl(32512).setVisible(False)
            self.getControl(32513).setVisible(False)
            self.getControl(32514).setVisible(False)
            self.getControl(32515).setVisible(False)
            self.getControl(32516).setVisible(False)
            self.getControl(32517).setVisible(False)
            self.getControl(32518).setVisible(False)
            self.tweet = 0
            self.last_id = ""
            self.live_feed = False
            xbmc.executebuiltin("ClearProperty(loading-script-matchcenter-livemoto_feed,Home)")
            self.getTweets()
            self.url_gp = ""
            self.select_bf = "000"
            self.setLive()
        else:
            self.setTable()

        import threading
        t = threading.Thread(target=self.update)
        t.setDaemon(True) 
        t.start()

    def update(self):
        i = 0
        if self.standalone:
            while self.isRunning:
                if (float(i*200)/(0.5*60*1000)).is_integer() and i != 0:
                    self.setLive()
                    i = 0
                xbmc.sleep(200)
                i += 1


    def setTable(self):
        xbmc.executebuiltin("SetProperty(loading-script-matchcenter-livemotos,1,home)")

        self.getControl(32540).setImage(filetools.join(config.get_runtime_path(), "resources", "images", "matchcenter", "moto.gif"))
        self.getControl(32501).reset()
        self.getControl(32601).setLabel("")

        if self.load_plus:
            self.getControl(32503).reset()
            self.circuitos = marcadores.get_calendario_motos()
            items_races = []
            i = 0
            for fecha, title, url, circuit, country, img, finish in self.circuitos:
                item = xbmcgui.ListItem(circuit)
                item.setProperty('title', circuit)
                item.setProperty('url', url)
                item.setProperty('fecha', fecha)
                item.setProperty('img', img)
                item.setArt({'thumb': country})
                items_races.append(item)
                if not finish and self.race is None:
                    self.race = i
                i += 1

            self.getControl(32503).addItems(items_races)

            if self.modalidad == "motogp":
                sesiones = ['Carrera', 'WUP', 'Q2', 'Q1', 'Libres 4', 'Libres 3', 'Libres 2', 'Libres 1']
                items_ses = []
                for ses in sesiones:
                    item = xbmcgui.ListItem(ses)
                    item.setProperty("name", "ostia")
                    items_ses.append(item)
            else:
                sesiones = ['Carrera', 'WUP', 'Q1', 'Libres 3', 'Libres 2', 'Libres 1']
                items_ses = []
                for ses in sesiones:
                    item = xbmcgui.ListItem(ses)
                    items_ses.append(item)
            self.getControl(32510).addItems(items_ses)


        self.getControl(32503).selectItem(self.race)
        self.setFocusId(32503)
        self.url = self.circuitos[self.race][2]

        if self.load:
            self.circuit = marcadores.get_circuit_data(self.url, self.modalidad)
            self.getControl(32500).setLabel("Mundial de %s 2017" % self.modalidad.capitalize().replace("Motogp", "MotoGP"))
            self.getControl(32520).setImage(self.circuitos[self.race][5])
            self.getControl(32521).setLabel("Nombre: [COLOR red]%s[/COLOR]" % self.circuitos[self.race][3])
            self.getControl(32522).setText(self.circuit["data"]["desc"])
            if self.circuit["data"]["record"]:
                self.getControl(32525).setLabel("Récord del circuito: [COLOR red]%s[/COLOR]" % self.circuit["data"]["record"])
            else:
                self.getControl(32525).setLabel("")
            self.getControl(32600).setLabel(self.circuitos[self.race][1])
            q = "%s+circuit+map+moto" % self.circuitos[self.race][3].replace(" ", "+")
            self.images = self.get_bing_images(q, 'multiple')
                
        self.table = []
        for i, s in enumerate(self.circuit["sesiones"]):
            if i == self.session:
                if s[2].startswith("http"):
                    s_data = marcadores.get_session_data(s[2])
                    for ses in s_data:
                        thumb, moto, self.data_d = marcadores.get_data_piloto(self.data_d, ses["name"], self.modalidad)
                        item = xbmcgui.ListItem(ses["name"])
                        item.setProperty('team', ses["team"])
                        item.setProperty('marca', ses["marca"])
                        item.setProperty('thumb', thumb)
                        item.setArt({'thumb': thumb})
                        item.setProperty('moto', moto)
                        item.setProperty('url', ses["url"])
                        if s[0] == "Carrera":
                            item.setProperty('dato', ses["dato"])
                        item.setProperty('pos', ses.get("pos", "-"))
                        item.setProperty('gap', ses["gap"])
                        item.setProperty('km', ses["km"])
                        item.setProperty('country', ses["country"])
                        self.table.append(item)
                    break
                else:
                    fecha = s[2]
                    self.getControl(32601).setLabel("Sesión prevista para el %s" % fecha)
                    break

        if self.table:
            self.getControl(32501).addItems(self.table)
            self.setFocusId(32501)

        self.getControl(32538).setLabel(self.circuit["sesiones"][self.session][0])
        xbmc.executebuiltin("ClearProperty(loading-script-matchcenter-livemotos,Home)")
        self.load = False
        self.load_plus = False

        return


    def setLive(self):
        if not self.items:
            xbmc.executebuiltin("SetProperty(loading-script-matchcenter-livemotos,1,home)")
        length = len(self.items)
        if not self.url_gp:
            self.url_gp, sesiones, self.gp, self.numero = marcadores.get_live_moto()
            modalidad = self.modalidad.capitalize().replace("Motogp", "MotoGP")
            self.sesionlive = ""
            for s in sesiones[modalidad]:
                if s["status"] not in ["WaitStart", "Ended"]:
                    self.sesionlive = s
            if not self.sesionlive:
                self.live = False
                for s in sesiones[modalidad]:
                    if s["status"] == "Ended":
                        self.sesionlive = s

            try:
                self.pilotos, self.times = marcadores.get_live_details_moto(self.sesionlive["id"])
            except:
                import traceback
                xbmc.log(traceback.format_exc())
                self.pilotos = None
                self.times = []
        else:
            try:
                pilot, self.times = marcadores.get_live_details_moto(self.sesionlive["id"], False)
            except:
                self.times = []

        if not self.live:
            self.isRunning = False

        if not self.live:   
            self.getControl(32502).setImage("http://i.imgur.com/ExfeHEU.png")
            self.getControl(32512).setVisible(False)
            self.getControl(32513).setVisible(False)
        else:
            self.getControl(32502).setImage("http://i.imgur.com/hIGKGp9.png")
            self.getControl(32512).setVisible(False)
            self.getControl(32513).setVisible(False)

        if self.times:
            texto = []
            self.tipo = self.sesionlive["name"].rsplit("_", 1)[1].replace("RAC", "RACE").replace("WUP1", "WUP").replace("RACE1", "RACE")
            label = "[COLOR fuchsia]%s - %s" % (self.gp, self.tipo)
            if self.tipo == "RACE" and self.live:
                label += "[/COLOR] LAP %s/%s: " % (str(self.sesionlive["laps"]-self.sesionlive["remain"]), self.sesionlive["laps"])
            elif not self.live:
                label += "[/COLOR] FIN: "
            else:
                label += "[/COLOR] [COLOR red]LIVE:[/COLOR] "

            for i, t in enumerate(self.times):
                piloto = self.pilotos[t["number"]]["name"].replace(" ", "")[:3].upper()
                text = "  %s. [COLOR white]%s[/COLOR] " % (str(i+1), piloto)
                if t["pos"] == "100":
                    text += "[COLOR gray]DNF[/COLOR] "
                elif self.tipo != "RACE":
                    text += "[COLOR blue]%s[/COLOR] " % t["gap_t"]
                else:
                    text += "[COLOR blue]%s[/COLOR] " % t["gap"]
                texto.append(text)
            label += "[COLOR red]|[/COLOR] ".join(texto)
            self.getControl(32500).setLabel(label)

        self.comments = []
        if self.tipo == "RACE":
            self.comments = marcadores.get_comments_motos(self.modalidad.lower(), self.numero)

        if self.comments and len(self.comments) > length:
            self.items = []
            for com in self.comments:
                item = xbmcgui.ListItem(com[1])
                if com[0]:
                    item.setProperty("hora", "Vuelta\n%s" % com[0])
                item.setProperty("thumb", com[2])
                self.items.append(item)

            if self.items:
                self.getControl(32503).reset()
                self.getControl(32503).addItem(self.items[0])
        elif not self.comments:
            self.getControl(32503).setVisible(False)
            self.getControl(32505).setVisible(False)
            xbmc.executebuiltin("ClearProperty(loading-script-matchcenter-livemotos,Home)")
            self.getControl(32507).setVisible(True)

        if self.items:
            xbmc.executebuiltin("ClearProperty(loading-script-matchcenter-livemotos,Home)")


    def onClick(self,controlId):
        if not self.standalone:
            if controlId == 32510:
                self.session = self.getControl(32510).getSelectedPosition()
                self.live = True
                self.setTable()
            elif controlId == 32503:
                select = self.getControl(32503).getSelectedItem()
                self.url = select.getProperty("url")
                self.session = 0
                self.race = self.getControl(32503).getSelectedPosition()
                self.load = True
                self.data = ""
                self.setTable()
            elif controlId == 32519:
                if self.images:
                    self.getControl(32520).setImage(self.images[self.index])
                    self.index += 1
                    if self.index == len(self.images):
                        self.index = 0
            elif controlId == 32501:
                select = self.getControl(32501).getSelectedItem()
                url = select.getProperty("url")
                if url:
                    infopilotos.start(url, select.getProperty("thumb"), select.getProperty("team"), select.getProperty("moto"))

        else:
            if controlId == 32503:
                self.getControl(32503).removeItem(0)
                if self.comentario + 1 == len(self.items):
                    self.comentario = 0
                    self.getControl(32503).addItem(self.items[0])
                else:
                    self.comentario += 1
                    self.getControl(32503).addItem(self.items[self.comentario])
            elif controlId == 32504:
                if xbmc.getCondVisibility("Control.IsVisible(32501)"):
                    self.getControl(32501).setVisible(False)
                    self.getControl(32500).setVisible(False)
                else:
                    self.getControl(32501).setVisible(True)
                    self.getControl(32500).setVisible(True)
            elif controlId == 32505:
                if xbmc.getCondVisibility("Control.IsVisible(32503)"):
                    self.getControl(32503).setVisible(False)
                else:
                    self.getControl(32503).setVisible(True)
                    self.getControl(32507).setVisible(False)
            elif controlId == 32506:
                if xbmc.getCondVisibility("Control.IsVisible(32507)"):
                    self.getControl(32507).setVisible(False)
                else:
                    self.getControl(32507).setVisible(True)
                    self.getControl(32503).setVisible(False)
            elif controlId == 32507:
                if self.tweet < 19:
                    self.getControl(32507).removeItem(0)
                    self.tweet += 1
                    xbmc.sleep(100)
                    self.getControl(32507).addItem(self.tweetitems[self.tweet])
                else:
                    self.tweet = 0
                    self.last_id = ""
                    self.getTweets()
            elif controlId == 32508:
                self.loop = 7


    def onAction(self,action):            
        if action.getId() == 92 or action.getId() == 10:
            self.isRunning = False
            self.live_feed = False
            self.close()
        elif self.standalone and not self.live_feed and action.getId() in [1, 2]:
            xbmc.executebuiltin("SetProperty(loading-script-matchcenter-livemoto_feed,1,Home)")
            self.getControl(32508).setVisible(True)
            self.getControl(32509).setVisible(True)
            self.getControl(32511).setLabel("%s - %s - %s" % (self.modalidad.capitalize().replace("Motogp", "MotoGP"), self.gp, self.tipo))
            self.live_feed = True
            index = 0
            self.count = 0
            self.loop = 0
            tipos = [['sectors', '', 'Sectores'], ['bestlap', 'red', 'V.Rápida'], ['motor', '', 'Marca']]
            if self.tipo == "RACE":
                tipos.append(['pos', '', 'Posición'])
            p, feed = marcadores.get_live_details_moto(self.sesionlive["id"], False)
            inicio = time.time()
            items_feed = []
            while self.live_feed:
                fin = time.time()
                if (fin - inicio) > 30 and self.sesionlive["status"] != "Ended":
                    p, feed = marcadores.get_live_details_moto(self.sesionlive["id"], False)
                    inicio = time.time()
                if (not feed or (items_feed and self.sesionlive["status"] == "Ended")) and not xbmc.getCondVisibility("Control.IsVisible(32510)"):
                    self.live_feed = False
                    break
                items_feed = []
                self.getControl(32508).reset()
                loop = self.loop
                for i, f in enumerate(feed):
                    item = xbmcgui.ListItem(str(i+1))
                    lap = str(f["lap"])
                    color = "%s"
                    if str(f["pos"]) == "100":
                        lap = "DNF"
                        color = "[COLOR gray]%s[/COLOR]"
                    if f["pit"] == "Pit":
                        lap = "PIT"
                    item.setProperty('lap', color % lap)

                    gap = str(f["gap_t"]).replace(" Laps", "L").replace("+", "")
                    if ":" in gap:
                        gap = gap[:6]
                    item.setProperty('gap', color % gap)

                    item.setProperty('laptime', color % str(f["laptime"]))
                    if f["pit"] == "Pit":
                        color_b = "4"
                    elif f["status_lap"] == "NO_IMPROVEMENT":
                        color_b = "1"
                    elif f["status_lap"] == "PERSONAL_BEST":
                        color_b = "3"
                    elif f["status_lap"] == "FASTEST":
                        color_b = "2"
                    else:
                        color_b = "4"
                    item.setProperty("background%s" % color_b, filetools.join(config.get_runtime_path(), 'resources', 'skins', 'Default', 'media', 'MatchCenter', 'marco_minm.png'))
                    
                    variable = tipos[self.count]
                    if variable[0] == "sectors":
                        for j in range(len(f["sectors"])):
                            if f["sectors"][j] == "NO_IMPROVEMENT":
                                color_b = "red"
                            elif f["sectors"][j] == "PERSONAL_BEST":
                                color_b = "orange"
                            elif f["sectors"][j] == "FASTEST":
                                color_b = "green"
                            else:
                                color_b = ""
                            back = filetools.join(config.get_runtime_path(), 'resources', 'skins', 'Default', 'media', 'MatchCenter', 'sector_%s.png' % color_b)
                            item.setProperty('sector%s' % str(j+1), back)
                    elif variable[0] == "pos":
                        value = (i + 1) - int(f["grid"])
                        if value > 0:
                            item.setProperty('variable', "[COLOR green]+%s[/COLOR]" % value)
                        elif value < 0:
                            item.setProperty('variable', "[COLOR crimson]%s[/COLOR]" % value)
                        else:
                            item.setProperty('variable', "[COLOR white]0[/COLOR]")
                    elif variable[0] == "motor":
                        item.setProperty('team', self.pilotos[f["number"]]["team"])
                    elif variable[0] == "bestlap":
                        item.setProperty('variable', "[COLOR %s]%s[/COLOR]" % (variable[1], str(f["bestlap"])))

                    piloto = self.pilotos[f["number"]]["name"].replace(" ", "")[:3].upper()
                    item.setProperty('piloto', color % piloto)
                    item.setProperty('numero', f["number"])
                    items_feed.append(item)
                items_feed.sort(key=lambda it:int(it.getLabel()))

                self.getControl(32509).reset()
                self.getControl(32509).addItem(xbmcgui.ListItem(tipos[self.count][2]))
                self.getControl(32508).addItems(items_feed)
                self.setFocusId(32508)
                self.getControl(32508).selectItem(index)
                for i in range(6):
                    if not self.live_feed or self.loop != loop:
                        break
                    xbmc.sleep(1000)
                index = self.getControl(32508).getSelectedPosition()
                self.loop += 1
                if self.loop >= 7:
                    self.loop = 0
                    self.count += 1
                    if self.count == len(tipos):
                        self.count = 0

        elif self.standalone and xbmc.getCondVisibility("Control.IsVisible(32510)") and action.getId() in [1, 2]:
            self.live_feed = False
            xbmc.executebuiltin("ClearProperty(loading-script-matchcenter-livemoto_feed,Home)")
            self.setFocusId(32503)
        elif self.standalone and xbmc.getCondVisibility("Control.IsVisible(32510)") and action.getId() == 117:
            self.set_Info(True)
        elif self.standalone and self.check_info and self.getFocusId() == 32508:
            self.set_Info(False)


    def set_Info(self, close):
        self.select = self.getControl(32508).getSelectedItem()
        change = (self.select.getProperty("numero") != self.select_bf)
        if xbmc.getCondVisibility("Control.IsVisible(32514)") and not change and close:
            self.getControl(32514).setVisible(False)
            self.getControl(32515).setVisible(False)
            self.getControl(32516).setVisible(False)
            self.getControl(32517).setVisible(False)
            self.getControl(32518).setVisible(False)
            self.check_info = False
        else:
            self.getControl(32514).setVisible(True)
            self.getControl(32515).setVisible(True)
            self.getControl(32516).setVisible(True)
            self.getControl(32517).setVisible(True)
            self.getControl(32518).setVisible(True)
            self.check_info = True
            self.select = self.getControl(32508).getSelectedItem()
            text = self.pilotos[self.select.getProperty("numero")]["full"]
            text += " - " + unicode(self.pilotos[self.select.getProperty("numero")]["team_name"], "utf-8")
            self.getControl(32515).setLabel(text)
            if self.modalidad == "motogp":
                thumb = "http://media.foxsports.com.au/match-centre/v8-supercars/images/drivers/icons/%s.jpg" % self.pilotos[self.select.getProperty("numero")]["id"]
                self.getControl(32516).setImage(thumb)
                moto = "http://media.foxsports.com.au/match-centre/v8-supercars/images/drivers/cars/%s.jpg" % self.pilotos[self.select.getProperty("numero")]["id"]
                self.getControl(32517).setImage(moto)
            else:
                thumb, moto, self.data_d = marcadores.get_data_piloto(self.data_d, self.pilotos[self.select.getProperty("numero")]["full"], self.modalidad)
                self.getControl(32516).setImage(thumb)
                self.getControl(32517).setImage(moto)
            f1, f2, f3 = self.pilotos[self.select.getProperty("numero")]["birth"].split("-")
            text = "%s-%s-%s" % (f3, f2, f1)
            text += "  |  %s cm/%s kg" % (self.pilotos[self.select.getProperty("numero")]["h"], self.pilotos[self.select.getProperty("numero")]["w"])
            self.getControl(32518).setLabel(text)
            self.select_bf = self.select.getProperty("numero")


    def getTweets(self):
        self.check_reply = ""
        self.tweetitems = []
        self.hash = config.get_setting("search_livemoto")
        if not self.hash:
            self.hash = "@movistar_motogp"
        import tweet
        if self.hash.startswith("#"):
            tweets = tweet.get_tweets(None, self.hash, None, None, max_id=self.last_id)
        elif self.hash.startswith("@"):
            try:
                tweets, total = tweet.get_tweets(self.hash, None, None, None, max_id=self.last_id)
            except:
                tweets= None
        else:
            tweets = tweet.get_tweets(None, None, self.hash, None, max_id=self.last_id)

        if tweets:
            self.last_id = tweets[-1]['id']
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
        self.getControl(32507).reset()
        if self.tweetitems:
            self.getControl(32507).addItem(self.tweetitems[0])

        return


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


    def get_bing_images(self, q, mode="single", tipo="m"):
        thumb = ""
        f1file = filetools.join(config.get_data_path(), 'matchcenter', 'matchcenter_moto.json')
        data_bing = filetools.read(f1file)
        if data_bing:
            data_bing = jsontools.load_json(data_bing)
            thumb = data_bing.get(q, "")
        else:
            data_bing = {}

        if not thumb:
            data_img = httptools.downloadpage("http://www.bing.com/images/search?q=%s" % q.replace(" ", "+")).data
            if mode == "single":
                thumb = scrapertools.find_single_match(data_img, tipo+'url&quot;:&quot;(.*?)&quot;')
            else:
                thumb = scrapertools.find_multiple_matches(data_img, tipo+'url&quot;:&quot;(.*?)&quot;')
            data_bing[q] = thumb
            filetools.write(f1file, jsontools.dump_json(data_bing))
        
        return thumb


def start(window, mode):
    if xbmc.getCondVisibility("Player.HasMedia"):
        standalone = True
        script = 'script-matchcenter-LiveMotos-mini.xml'
        xbmc.executebuiltin("Dialog.Close(videoosd, true)")
    else:
        standalone = False
        script = 'script-matchcenter-LiveMotos.xml'
    main = detailsDialog(script, config.get_runtime_path(), standalone=standalone, modalidad=mode)
    main.doModal()
    del main
    window.doModal()
