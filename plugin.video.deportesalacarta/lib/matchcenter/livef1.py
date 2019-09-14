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
import infodrivers

from core import filetools
from core import config
from core import httptools
from core import scrapertools
from core import jsontools


class detailsDialog(xbmcgui.WindowXMLDialog):
    def __init__( self, *args, **kwargs ):
        self.standalone = kwargs["standalone"]
        self.isRunning = True


    def onInit(self):
        self.setCoordinateResolution(2)
        self.temporada = ""
        self.url = ""
        self.race = 0
        self.session = ""
        self.load = True
        self.load_plus = True
        self.data = ""
        self.live = True
        self.index = 0
        self.items = []
        self.comentario = 0
        self.check_info = False
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
            self.tweet = 0
            self.last_id = ""
            self.live_feed = False
            xbmc.executebuiltin("ClearProperty(loading-script-matchcenter-livef1_feed,Home)")
            self.select_bf = "000"
            self.data_d = ""
            self.data_race = ""
            self.data_driver = ""
            self.getTweets()
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
        xbmc.executebuiltin("SetProperty(loading-script-matchcenter-livef1,1,home)")
        xbmc.executebuiltin("ClearProperty(hide,Home)")
        self.status = ""

        import random
        images = ['green', 'install', 'blue', 'starting', 'temp']
        self.getControl(32540).setImage(filetools.join(config.get_runtime_path(), "resources", "images", "matchcenter", "%s.gif" % images[random.randint(0,4)]))
        self.getControl(32501).reset()
        self.getControl(32601).setLabel("")

        if self.load_plus:
            self.getControl(32503).reset()
            self.getControl(32505).reset()
            self.getControl(32505).setVisible(False)
            self.seasons, self.races, self.data = marcadores.get_calendario_f1(self.temporada)
            items_races = []
            i = 0
            for url, thumb, race, fecha, winner in self.races:
                item = xbmcgui.ListItem(race)
                item.setProperty('title', race)
                item.setProperty('url', url)
                item.setProperty('fecha', fecha)
                if not fecha:
                    temp = self.temporada
                    if not temp:
                        temp = self.seasons[0][0]
                    q = "+".join([winner, race, temp]) + "+trophy"
                    img = self.get_bing_images(q)
                    item.setProperty('winner', img)

                item.setArt({'thumb': thumb})
                items_races.append(item)
                if fecha and not self.race:
                    self.race = i
                i += 1

            self.getControl(32503).addItems(items_races)

            temporadas = []
            index = 0
            i = 0
            for temp, url in self.seasons:
                item = xbmcgui.ListItem(temp)
                item.setProperty("temp", temp)
                item.setProperty("url", url)
                if temp == self.temporada:
                    index = i
                    continue
                temporadas.append(item)
                i += 1

            if not self.temporada:
                self.temporada = temporadas[0].getProperty("temp")
                temporadas.pop(0)

            self.getControl(32505).addItems(temporadas)
            self.getControl(32505).selectItem(index)
            xbmc.executebuiltin("SetProperty(temporada,%s,Home)" % self.temporada)

        self.getControl(32503).selectItem(self.race)
        self.setFocusId(32503)

        if self.load:
            self.times = marcadores.get_data_f1(self.url, data=self.data)
            
            self.getControl(32500).setLabel("Mundial de Fórmula 1 %s" % self.temporada)
            country = self.times["circuit"]["country"].replace("UAE", "United Arab Emirates").replace(" ", "-").lower()
            self.getControl(32520).setImage("http://www.sofascore.com/bundles/sofascoreweb/images/backgrounds/formula-1/%s.jpg" % country)
            self.getControl(32521).setLabel("Nombre: [COLOR red]%s[/COLOR]" % self.times["circuit"]["name"])
            self.getControl(32522).setLabel("Longitud: [COLOR red]%s metros[/COLOR]" % self.times["circuit"]["length"])
            self.getControl(32523).setLabel("Distancia Total: [COLOR red]%s metros[/COLOR]" % self.times["circuit"]["distance"])
            self.getControl(32524).setLabel("Nº de vueltas: [COLOR red]%s[/COLOR]" % self.times["circuit"]["laps"])
            self.getControl(32525).setLabel("Récord del circuito: [COLOR red]%s[/COLOR]" % self.times["circuit"]["lap_record"])
            self.getControl(32600).setLabel(self.times["circuit"]["gp"])
            q = "%s+circuit+map+f1" % self.times["circuit"]["gp"].replace(" ", "+")
            self.images = self.get_bing_images(q, 'multiple')

        pilotos = ['hamilton', 'vettel', 'bottas', 'massa', 'alonso', 'raikkonen', 'kvyat', 'hulkenberg', 'sainz',
                   'grosjean', 'perez', 'ocon', 'ricciardo', 'verstappen', 'stroll', 'vandoorne', 'magnussen',
                   'palmer', 'ericsson', 'wehrlein', 'button', 'rosberg', 'maldonado', 'webber', 'sutil', 'gutierrez',
                   'bianchi', 'chilton', 'resta', 'vergne', 'garde', 'kobayashi', 'stevens', 'nasr', 'merhi', 'rossi',
                   'haryanto', 'lotterer']
        teams = ['Ferrari', 'Mercedes', 'Williams', 'Red Bull', 'Renault', 'Toro Rosso', 'Haas', 'Sauber', 'Force India', 'Mclaren']
        self.table = []
        for i, s in enumerate(self.times["sessions"]):
            session = self.times["active"]
            if self.session:
                session = self.session
            if s["type"] == session:
                self.session = session
                fecha = s["time"]
                self.status = s["status"]
                j = 1
                for d in s["drivers"]:
                    item = xbmcgui.ListItem(d["driver"]["name"])
                    piloto = d["driver"]["name"].rsplit(" ", 1)[1]
                    piloto = piloto.replace("Räikkönen", "Raikkonen").lower()
                    thumb = ""
                    if piloto in pilotos:
                        if pilotos.index(piloto) < 20:
                            thumb = "http://soymotor.com/sites/default/files/styles/node_gallery_thumbnail/public/imagenes/piloto/pilotos-2017-f1-soymotor-2-%s.png" % piloto
                        item.setProperty('url', 'http://soymotor.com/pilotos/%s' % d["driver"]["name"].replace("Räikkönen", "Raikkonen").replace(" ", "-").lower())
                    if not thumb:
                        q = d["driver"]["name"] + "+portrait+formula1"
                        thumb = self.get_bing_images(q, tipo="t")
                    
                    item.setArt({'thumb': thumb})
                    item.setProperty('short', d["driver"]["shortName"])
                    item.setProperty('team', d["team"]["name"])
                    if self.temporada == "2017" or d["team"]["name"] in teams:
                        car = d["team"]["name"].replace(" ", "-").replace("Mclaren", "McLaren")
                        item.setProperty('car', 'https://www.formula1.com/content/fom-website/en/championship/teams/%s/_jcr_content/teamCar.img.jpg' % car)
                        item.setProperty('team_thumb', "http://www.sofascore.com/images/team-logo/formula-1_%s.png" % d["team"]["id"])
                    else:
                        item.setProperty('team_t', "http://www.sofascore.com/images/team-logo/formula-1_%s.png" % d["team"]["id"])
                    item.setProperty('duration', str(d.get("duration", "")))
                    item.setProperty('gap', str(d.get("gap", "")))
                    item.setProperty('laps', str(d.get("laps", "")))
                    item.setProperty('rank', str(d.get("rank", str(j))))
                    item.setProperty('rank3', str(d.get("rank3", "")))
                    item.setProperty('q1', str(d.get("q1", "")))
                    item.setProperty('q2', str(d.get("q2", "")))
                    item.setProperty('q3', str(d.get("q3", "")))
                    grid = ""
                    if d.get("grid"):
                        dif = int(item.getProperty("rank")) - d["grid"]
                        if dif < 0:
                            grid = "%s [COLOR green](%+d)[/COLOR]" % (str(d["grid"]), dif)
                        elif dif > 0:
                            grid = "%s [COLOR red](%+d)[/COLOR]" % (str(d["grid"]), dif)
                        else:
                            grid = "%s [COLOR blue](=)[/COLOR]" % str(d["grid"])
                    item.setProperty('grid', grid)
                    item.setProperty('pits', str(d.get("pits", "")))

                    self.table.append(item)
                    j += 1

        if self.table:
            self.getControl(32501).addItems(self.table)
            if self.status != "inprogress":
                self.live = False
                
        elif self.session != "qualifying":
            self.live = False
            try:
                fecha = datetime.datetime.fromtimestamp(int(fecha)).strftime('%d-%m-%Y a las %H:%M')
                self.getControl(32601).setLabel("Sesión prevista para el %s" % fecha)
            except:
                self.getControl(32601).setLabel("Sesión sin datos")

        self.setFocusId(32501)
        if self.session == "qualifying":
            xbmc.executebuiltin("SetProperty(hide,1,Home)")
            self.getControl(32531).setEnabled(False)
        else:
            xbmc.executebuiltin("ClearProperty(hide,Home)")
            if not self.times["sessions"][-1].get("drivers"):
                self.getControl(32531).setEnabled(False)

        titulo = {'race': 'Carrera', 'qualifying': 'Calificación', 'qualifying3': 'Q3', 'qualifying2': 'Q2',
                  'qualifying1': 'Q1', 'practice3': 'Libres 3', 'practice2': 'Libres 2', 'practice1': 'Libres 1'}
        self.getControl(32538).setLabel(titulo[self.session])
        xbmc.executebuiltin("ClearProperty(loading-script-matchcenter-livef1,Home)")
        self.load = False
        self.load_plus = False
        sessions = ['race', 'qualifying3', 'qualifying2', 'qualifying1', 'practice3', 'practice2', 'practice1']
        if self.session in sessions:
            index = 32530
            if self.session != "race":
                index = 32531
            self.getControl(index+sessions.index(self.session)).setEnabled(False)

        return


    def setLive(self):
        if not self.items:
            xbmc.executebuiltin("SetProperty(loading-script-matchcenter-livef1,1,home)")
        length = len(self.items)

        self.comments, self.times, self.datos, self.bandera, self.live = marcadores.get_live_f1()
        if not self.live:
            self.isRunning = False

        if "bfinalizada" in self.bandera:   
            self.getControl(32502).setImage("http://i.imgur.com/ExfeHEU.png")
            self.getControl(32512).setVisible(False)
            self.getControl(32513).setVisible(False)
        elif "amarilla" in self.bandera:
            self.getControl(32502).setImage("http://i.imgur.com/R904LGh.png")
            self.getControl(32512).setVisible(False)
            self.getControl(32513).setVisible(False)
        elif "negra" in self.bandera or "black" in self.bandera:
            self.getControl(32502).setImage("http://i.imgur.com/aQXYKtw.png")
            self.getControl(32512).setVisible(False)
            self.getControl(32513).setVisible(False)
        elif "bsafetycar" in self.bandera:
            self.getControl(32512).setVisible(True)
            self.getControl(32513).setVisible(False)
        elif "bvirtualsafetycar" in self.bandera:
            self.getControl(32512).setVisible(False)
            self.getControl(32513).setVisible(True)
        else:
            self.getControl(32502).setImage("http://i.imgur.com/hIGKGp9.png")
            self.getControl(32512).setVisible(False)
            self.getControl(32513).setVisible(False)

        if self.times and type(self.times) is dict:
            texto = []
            label = "[COLOR fuchsia]%s[/COLOR]" % self.datos.split("|")[0]
            if "Carrera" in self.datos and not "bfinalizada" in self.bandera:
                label = "[COLOR fuchsia]Carrera LAP %s: [/COLOR]" % self.times["1"]["vueltas"]
            elif "Carrera" in self.datos:
                label = "[COLOR fuchsia]Carrera Finalizada: [/COLOR]"
                
            for i in range(1, 21):
                if not self.times.get(str(i)):
                    break
                piloto = self.times[str(i)]["piloto"].strip().rsplit(" ", 1)[1][:3].upper().replace("VER", "VES")
                text = "%s. [COLOR white]%s[/COLOR] " % (self.times[str(i)]["posicion"], piloto)
                if self.times[str(i)]["diferencia"].strip() != '+ 0"000':
                    text += "[COLOR blue]%s[/COLOR] " % self.times[str(i)]["diferencia"].strip()
                else:
                    text += "[COLOR blue]%s[/COLOR] " % self.times[str(i)]["tiempo"].strip()
                texto.append(text)
            label += "[COLOR red]|[/COLOR] ".join(texto)
            self.getControl(32500).setLabel(label)

        if self.comments and len(self.comments) > length:
            self.items = []
            for com in self.comments:
                item = xbmcgui.ListItem(com[1])
                item.setProperty("hora", com[0])
                self.items.append(item)

            if self.items:
                self.getControl(32503).reset()
                self.getControl(32503).addItem(self.items[0])
        elif not self.comments:
            self.getControl(32503).setVisible(False)
            self.getControl(32505).setVisible(False)
            xbmc.executebuiltin("ClearProperty(loading-script-matchcenter-livef1,Home)")
            self.getControl(32507).setVisible(True)

        if self.items:
            xbmc.executebuiltin("ClearProperty(loading-script-matchcenter-livef1,Home)")


    def onClick(self,controlId):
        if not self.standalone:
            if controlId >= 32530 and controlId <= 32537:
                sessions = ['race', 'qualifying', 'qualifying3', 'qualifying2', 'qualifying1', 'practice3', 'practice2', 'practice1']
                self.session = sessions[controlId-32530]
                for i in range(32530, 32538):
                    if i == controlId:
                        self.getControl(controlId).setEnabled(False)
                    else:
                        self.getControl(i).setEnabled(True)
                self.live = True
                self.setTable()
            elif controlId == 32503:
                select = self.getControl(32503).getSelectedItem()
                self.url = select.getProperty("url")
                self.session = ""
                self.race = self.getControl(32503).getSelectedPosition()
                self.load = True
                self.data = ""
                for i in range(32530, 32538):
                    self.getControl(i).setEnabled(True)
                self.setTable()
            elif controlId == 32504:
                if xbmc.getCondVisibility("Control.IsVisible(32505)"):
                    self.getControl(32505).setVisible(False)
                else:
                    self.getControl(32505).setVisible(True)
                    self.setFocusId(32505)
            elif controlId == 32505:
                select = self.getControl(32505).getSelectedItem()
                self.session = ""
                self.temporada = select.getProperty("temp")
                self.race = 0
                self.load = True
                self.load_plus = True
                self.data = ""
                for i in range(32530, 32538):
                    self.getControl(i).setEnabled(True)
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
                    infodrivers.start(url, select.getProperty("team_thumb"), select.getProperty("team"))

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
                self.setFocusId(32507)
            elif controlId == 32508:
                self.loop = 3



    def onAction(self,action):
        if action.getId() == 92 or action.getId() == 10:
            self.isRunning = False
            self.live_feed = False
            self.close()
        elif self.standalone and not self.live_feed and action.getId() in [1, 2]:
            import random
            xbmc.executebuiltin("SetProperty(loading-script-matchcenter-livef1_feed,1,Home)")
            self.getControl(32508).setVisible(True)
            self.getControl(32509).setVisible(True)
            self.live_feed = True
            index = 0
            self.count = random.randint(0, 5)
            self.loop = 0
            feed = ""
            tipo = [['pos', '', 'Posición'], ['tyres', '', 'Ruedas'], ['speed', 'orange', 'Velocidad'], ['pits', 'purple', 'Paradas'], ['points', 'indigo', 'Puntos'], ['bestlap', 'red', 'V.Rápida']]
            while self.live_feed:
                if self.live or not feed:
                    feed, carrera, self.data_race = marcadores.get_feed(self.data_race)
                    self.getControl(32511).setLabel(carrera)
                    xbmc.executebuiltin("SetProperty(loading-script-matchcenter-flash,1,Home)")

                if not feed:
                    self.live_feed = False
                    break
                items_feed = []
                self.getControl(32508).reset()
                loop = self.loop
                lapbest = 0
                ilap = 0
                for k, v in feed.items():
                    if lapbest == 0:
                        lapbest = v["laptime"]
                        ilap = k
                    elif v["laptime"] < lapbest:
                        lapbest = v["laptime"]
                        ilap = k

                    item = xbmcgui.ListItem(k)
                    lap = str(v["lap"])
                    color = "%s"
                    if v["status"] in [2, 3] or (v["status"] == 1 and "Carrera" not in self.datos and self.live):
                        lap = "PIT"
                    elif v["status"] == 1 and "Carrera" in self.datos:
                        lap = "×"
                        color = "[COLOR gray]%s[/COLOR]"
                    elif v["status"]  == 4:
                        lap = "FIN"
                    item.setProperty('lap', color % lap)

                    if v["gap"] < 0:
                        gap = str(v["gap"])
                        if "-" in gap:
                            gap = gap.split(".")[0][1:] + "L"
                        item.setProperty('gap', color % gap)
                    elif v.get("interval") and type(v.get("interval")) is float and v.get("interval") != 0.0:
                        gap = str(v["interval"])[:-1]
                        item.setProperty('gap', color % gap)
                    else:
                        gap = '%.2f' % v["gap"]
                        if gap == "0.00":
                            gap = ""
                        item.setProperty('gap', color % gap)                        

                    laptime = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(v["laptime"]), "%M:%S:%f")[:-3]
                    item.setProperty('laptime', color % laptime)
                    item.setProperty('pits', color % str(v["pits"]))
                    variable = tipo[self.count]
                    if variable[0] == "tyres":
                        if len(v["tyres"]) >= 3:
                            item.setProperty('tyre1', str(v["tyres"][-3]))
                            item.setProperty('tyre2', str(v["tyres"][-2]))
                            item.setProperty('tyre3', str(v["tyres"][-1]))
                        elif len(v["tyres"]) == 2:
                            item.setProperty('tyre1', str(v["tyres"][0]))
                            item.setProperty('tyre2', str(v["tyres"][1]))
                        elif len(v["tyres"]) == 1:
                            item.setProperty('tyre1', str(v["tyres"][0]))

                    elif variable[0] == "pos":
                        value = v.get("pos", 0)
                        if value > 0:
                            item.setProperty('variable', "[COLOR green]+%s[/COLOR]" % value)
                        elif value < 0:
                            item.setProperty('variable', "[COLOR crimson]%s[/COLOR]" % value)
                        else:
                            item.setProperty('variable', "[COLOR white]0[/COLOR]")
                    elif variable[0] == "bestlap":
                        if v["bestlap"] != 0:
                            bestlap = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(v["bestlap"]), "%M:%S:%f")[:-3]
                            item.setProperty('variable', "[COLOR %s]%s[/COLOR]" % (variable[1], bestlap))
                        else:
                            item.setProperty('variable', "[COLOR %s]%s[/COLOR]" % (variable[1], laptime))
                    else:
                        item.setProperty('variable', "[COLOR %s]%s[/COLOR]" % (variable[1], str(v.get(variable[0], ""))))

                    piloto = v["driver"].rsplit(".", 1)[1][:3]
                    item.setProperty('piloto', color % piloto)
                    item.setProperty('driver', v["driver"])
                    item.setProperty('color', "[COLOR FF%s]I[/COLOR]" % v["color"])
                    items_feed.append(item)
                items_feed.sort(key=lambda it:int(it.getLabel()))
                for it in items_feed:
                    if it.getLabel() == str(ilap):
                        it.setProperty("background", filetools.join(config.get_runtime_path(), 'resources', 'skins', 'Default', 'media', 'MatchCenter', 'marco_minm.png'))

                self.getControl(32509).reset()
                self.getControl(32509).addItem(xbmcgui.ListItem(tipo[self.count][2]))
                self.getControl(32508).addItems(items_feed)
                self.setFocusId(32508)
                self.getControl(32508).selectItem(index)
                for i in range(8):
                    xbmc.sleep(200)
                    xbmc.executebuiltin("ClearProperty(loading-script-matchcenter-flash,Home)")
                    xbmc.sleep(800)
                    if not self.live_feed or self.loop != loop:
                        break
                index = self.getControl(32508).getSelectedPosition()
                self.loop += 1
                if self.loop >= 3:
                    self.loop = 0
                    self.count += 1
                    if self.count == 6:
                        self.count = 0

        elif self.standalone and self.live_feed and action.getId() in [1, 2]:
            self.live_feed = False
            xbmc.executebuiltin("ClearProperty(loading-script-matchcenter-livef1_feed,Home)")
            xbmc.executebuiltin("ClearProperty(loading-script-matchcenter-flash,Home)")
            self.setFocusId(32503)
        elif self.standalone and xbmc.getCondVisibility("Control.IsVisible(32510)") and action.getId() == 117:
            self.set_Info(True)
        elif self.standalone and self.check_info and self.getFocusId() == 32508:
            self.set_Info(False)


    def set_Info(self, close):
        self.select = self.getControl(32508).getSelectedItem()
        change = (self.select.getProperty("driver") != self.select_bf)
        if xbmc.getCondVisibility("Control.IsVisible(32514)") and not change and close:
            self.getControl(32514).setVisible(False)
            self.getControl(32515).setVisible(False)
            self.getControl(32516).setVisible(False)
            self.getControl(32517).setVisible(False)
            self.check_info = False
        else:
            self.getControl(32514).setVisible(True)
            self.getControl(32515).setVisible(True)
            self.getControl(32516).setVisible(True)
            self.getControl(32517).setVisible(True)
            self.check_info = True
            self.select = self.getControl(32508).getSelectedItem()
            thumb, casco, self.data_d, nombre, equipo, nacido, self.data_driver = marcadores.get_data_pilotof1(self.data_d, self.select.getProperty("driver"), self.data_driver)
            text = "%s - %s" % (nombre, equipo)
            self.getControl(32515).setLabel(text)
            self.getControl(32516).setImage(thumb)
            self.getControl(32517).setImage(casco)
            self.getControl(32518).setLabel(nacido)
            self.select_bf = self.select.getProperty("driver")


    def getTweets(self):
        self.check_reply = ""
        self.tweetitems = []
        self.hash = config.get_setting("search_livef1")
        if not self.hash:
            self.hash = "@SoyMotor"
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
        f1file = filetools.join(config.get_data_path(), 'matchcenter', 'matchcenter_f1.json')
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


def start(window):
    if xbmc.getCondVisibility("Player.HasMedia"):
        standalone = True
        script = 'script-matchcenter-LiveF1-mini.xml'
        xbmc.executebuiltin("Dialog.Close(videoosd, true)")
    else:
        standalone = False
        script = 'script-matchcenter-LiveF1.xml'
    main = detailsDialog(script, config.get_runtime_path(), standalone=standalone)
    main.doModal()
    del main
    window.doModal()
