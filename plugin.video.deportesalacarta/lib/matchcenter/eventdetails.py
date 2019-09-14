# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
#------------------------------------------------------------


import xbmcgui
import xbmc
import re
import marcadores
import infoplayers
import tweets
from threading import Thread

from core import filetools
from core import config
from core import httptools
from core.scrapertools import *


class detailsDialog(xbmcgui.WindowXMLDialog):
        
    def __init__( self, *args, **kwargs ):
        self.isRunning = True
        self.url = kwargs["url"]
        self.liga = kwargs["liga"]
        self.controls = []
        self.lista = "eventos"
        self.url_videos = {}
        self.url_news = {}
        self.coach1 = ""
        self.coach2 = ""
        self.hashtag = ""
        self.twitter1 = ""
        self.twitter2 = ""
        

    def onInit(self):
        self.setCoordinateResolution(2)
        self.getControl(33556).setVisible(False)
        self.getControl(33557).setVisible(False)
        self.getControl(33559).setVisible(False)
        self.getControl(33560).setVisible(False)
        goal = filetools.join(config.get_runtime_path(), 'resources', 'images', 'matchcenter', 'goal.png')
        news = filetools.join(config.get_runtime_path(), 'resources', 'images', 'matchcenter', 'tables.png')
        reload = filetools.join(config.get_runtime_path(), 'resources', 'images', 'matchcenter', 'sub.png')
        self.getControl(33541).setImage(goal)
        self.getControl(33542).setImage(news)
        self.getControl(33550).setImage(reload)
        self.setEventDetails()

    def setEventDetails(self, reload=False):
        xbmc.executebuiltin("SetProperty(no-stats,1,Home)")
        xbmc.executebuiltin("SetProperty(no-stadium,1,Home)")
        xbmc.executebuiltin("SetProperty(no-comments,1,Home)")
        xbmc.executebuiltin("SetProperty(no-videos,1,Home)")
        xbmc.executebuiltin("SetProperty(loading-videos,1,Home)")
        xbmc.executebuiltin("SetProperty(no-news,1,Home)")
        xbmc.executebuiltin("SetProperty(loading-news,1,Home)")
        xbmc.executebuiltin("ClearProperty(has_lineups,Home)")
        xbmc.executebuiltin("SetProperty(has_details,1,home)")
        self.match = marcadores.get_info(self.url, reload)

        if not reload:
            self.coach1 = self.match["coach1"]
            self.coach2 = self.match["coach2"]
            self.twitter1 = self.match["twitter1"]
            self.twitter2 = self.match["twitter2"]
            if self.match["nombre_corto1"] and self.match["nombre_corto2"]:
                self.hashtag = "#%s%s" % (self.match["nombre_corto1"], self.match["nombre_corto2"])

        if self.twitter1:
            self.getControl(33556).setVisible(True)
            self.getControl(33557).setVisible(True)
            self.getControl(33558).setLabel("@"+self.twitter1)
        if self.twitter2:
            self.getControl(33559).setVisible(True)
            self.getControl(33560).setVisible(True)
            self.getControl(33561).setLabel("@"+self.twitter2)
        if self.hashtag:
            self.getControl(33562).setLabel(self.hashtag)

        header = self.liga + " - " + self.match["jornada"]
        matchHomeGoals = self.match["score1"]
        matchAwayGoals = self.match["score2"]
        matchpercent = 0.0

        if "'" in self.match["minuto"]:
            try:
                matchpercent = float(int((float(self.match["minuto"].replace("'",""))/90)*100))
            except:
                import traceback
                xbmc.log(traceback.format_exc())
        else:
            if re.search(r'(?i)aplazado', self.match['minuto']):
                matchpercent = 0.0
            elif re.search(r'(?i)finalizado', self.match['minuto']):
                matchpercent = 100.0

        if re.search(r'(?i)finalizado', self.match['minuto']):
            status = filetools.join(config.get_runtime_path(),"resources","images","matchcenter","redstatus.png")
        elif "'" in self.match["minuto"]:
            status = filetools.join(config.get_runtime_path(),"resources","images","matchcenter","greenstatus.png")
        else:
            status = filetools.join(config.get_runtime_path(),"resources","images","matchcenter","yellowstatus.png")

        self.getControl(33509).setText(self.match["t1am"])
        if int(self.match["t1am"]) < 10:
            self.getControl(33509).setPosition(115, 130)
        self.getControl(33510).setText(self.match["t1roj"])
        self.getControl(33511).setText(self.match["t2am"])
        if int(self.match["t2am"]) < 10:
            self.getControl(33511).setPosition(1065, 130)
        self.getControl(33512).setText(self.match["t2roj"])

        self.getControl(32500).setLabel(header)
        
        self.getControl(32501).setImage(self.match["thumb1"])
        self.getControl(32503).setLabel(self.match["name1"])
        self.getControl(32504).setImage(self.match["thumb2"])
        self.getControl(32506).setLabel(self.match["name2"])

        if matchHomeGoals:
            self.getControl(32507).setLabel(matchHomeGoals+"-"+matchAwayGoals)
        else:
            self.getControl(32507).setLabel(self.match["hora"])
        
        self.getControl(32508).setLabel(self.translatematch(self.match["minuto"]))

        self.getControl(32509).setImage(status)
        self.getControl(32510).setPercent(matchpercent)

        estadio = self.match["estadio"]
        if self.match["stadium"].get("asistencia"):
            estadio += " - %s" % self.match["stadium"]["asistencia"]
        self.getControl(32511).setLabel(estadio)
        if self.match["ref"]:
            self.getControl(32512).setLabel("[COLOR selected]Árbitro: [/COLOR]" + self.match["ref"])

        if self.lista == "eventos":
            self.setEvents()
        elif self.lista == "stats":
            self.setStats()
        elif self.lista == "comments":
            self.setComments()
        elif self.lista == "videos":
            self.setVideos()
        elif self.lista == "news":
            self.setNews()

        if not self.match["stats"]:
            self.getControl(33516).setEnabled(False)
        if not self.match["stadium"] and not self.match["tv"]:
            self.getControl(33517).setEnabled(False)
        if not self.match["cronica"]:
            self.getControl(33518).setEnabled(False)
        if not self.match["videos"]:
            self.getControl(33519).setEnabled(False)
        if not self.match["news"]:
            self.getControl(33520).setEnabled(False)

        if self.match["tv"]:
            self.getControl(33517).setLabel("Estadio / TV")


    def setEvents(self):
        hometeamevents = []
        awayteamevents = []
        for evento in self.match["eventos"]:
            if evento["equipo"] == "l":
                hometeamevents.append([evento["desc"], evento["img"], evento["minuto"], evento["evento"], evento["url"]])
            else:
                awayteamevents.append([evento["desc"], evento["img"], evento["minuto"], evento["evento"], evento["url"]])


        self.getControl(32516).reset()
        items = []
        if hometeamevents:
            for evento in hometeamevents:
                item = xbmcgui.ListItem(evento[0])
                item.setProperty("eventlabel", evento[0])
                item.setProperty("eventimg", evento[1])
                item.setProperty("eventtime",evento[2] + "':")
                item.setProperty("evento", evento[3])
                item.setProperty("url", evento[4])
                items.append(item)
        else:
            item = xbmcgui.ListItem("")
            item.setProperty("eventlabel", " -- Sin info de eventos disponible --")
            items.append(item)
        
        self.getControl(32516).addItems(items)

        self.getControl(32517).reset()
        items = []
        if awayteamevents:
            for evento in awayteamevents:
                item = xbmcgui.ListItem(evento[0])
                item.setProperty("eventlabel", evento[0])
                item.setProperty("eventimg", evento[1])
                item.setProperty("eventtime",evento[2] + "':")
                item.setProperty("evento", evento[3])
                item.setProperty("url", evento[4])
                items.append(item)
        else:
            item = xbmcgui.ListItem("")
            item.setProperty("eventlabel", " -- Sin info de eventos disponible --")
            items.append(item)

        self.getControl(32517).addItems(items)

        self.setFocusId(32526)


    def setStats(self):
        estadisticas = []
        for stats in self.match["stats"]:
            item = xbmcgui.ListItem(stats["tipo"])
            item.setProperty("statl", stats["tipo"])
            if int(stats["l"].replace("%", "")) > int(stats["v"].replace("%", "")):
                item.setProperty("numberl", "[COLOR dimgray][B]%s[/B][/COLOR]" % stats["l"])
            else:
                item.setProperty("numberl", stats["l"])
            
            item.setProperty("statv", stats["tipo"])
            if int(stats["v"].replace("%", "")) > int(stats["l"].replace("%", "")):
                item.setProperty("numberv", "[COLOR dimgray][B]%s[/B][/COLOR]" % stats["v"])
            else:
                item.setProperty("numberv", stats["v"])
            estadisticas.append(item)

        self.getControl(33521).reset()
        if estadisticas:
            self.getControl(33521).addItems(estadisticas)
            xbmc.executebuiltin("ClearProperty(no-stats,Home)")
            self.setFocusId(32521)
        else:
            self.setFocusId(33516)

    def setStadium(self):
        st = self.match["stadium"]
            
        item = xbmcgui.ListItem(st["stadium"])
        item.setProperty("name", st["stadium"])
        item.setProperty("img", st["img_stadium"])
        datos = [st["asistencia"], st["capacidad"], st["dimen"], st["inagura"]]
        item.setProperty("datos", "\n".join(filter(None, datos)))

        self.getControl(33522).reset()
        self.getControl(33522).addItem(item)

        self.getControl(33526).reset()
        teles = []
        tv = self.match["tv"]
        for tele in tv:
            item = xbmcgui.ListItem(tele["nombre"])
            item.setProperty("name", tele["nombre"])
            item.setProperty("logo", tele["logo"])
            teles.append(item)

        if teles:
            self.getControl(33526).addItems(teles)

        self.setFocusId(33522)


    def setComments(self):
        comments = []
        for comment in self.match["cronica"]:
            item = xbmcgui.ListItem(comment["text"])
            item.setProperty("ico", comment["ico"])
            item.setProperty("time", comment["time"])
            if comment["destaca"]:
                item.setProperty("destaca", comment["text"])
            elif comment["bold"]:
                item.setProperty("bold", comment["text"])
            else:
                item.setProperty("text", comment["text"])

            comments.append(item)

        self.getControl(33523).reset()
        if comments:
            self.getControl(33523).addItems(comments)
            xbmc.executebuiltin("ClearProperty(no-comments,Home)")
            self.setFocusId(33523)
        else:
            self.setFocusId(33518)

    def setVideos(self):
        xbmc.executebuiltin("ClearProperty(loading-videos,Home)")
        videos = []
        for v in self.match["videos"]:
            item = xbmcgui.ListItem(v["title"])
            v["url"] = v["url"].replace("rutube.ru/player.swf?hash=", "rutube.ru/video/")
            if not self.url_videos.get(v["url"]):
                if "sporttube" in v["url"]:
                    data_v = httptools.downloadpage(v["url"]).data
                    if "Video not found" not in data_v:
                        img = find_single_match(data_v, 'poster="([^"]+)"')
                        url = find_single_match(data_v, '<source src="([^"]+)"')
                        self.url_videos[v["url"]] = {"url": url, "img": img}
                    else:
                        self.url_videos[v["url"]] = {"url": "Not found"}
                        continue
                elif "wao3iewu" in v["url"]:
                    data = httptools.downloadpage(v["url"]).data
                    url = find_single_match(data, '<source src="([^"]+)"')
                    self.url_videos[v["url"]] = {"url": url}
                elif "videa.hu" in v["url"]:
                    url = v["url"].replace("player?v=", "videaplayer_get_xml.php?v=") + "&start=0&enablesnapshot=0&referrer="
                    data = httptools.downloadpage(url).data
                    img = "http://" + find_single_match(data, '<poster_src>.*?//(.*?)<')
                    url = "http://" + find_single_match(data, 'streamable="1".*?>.*?//(.*?)<')
                    self.url_videos[v["url"]] = {"url": url, "img": img}
                else:
                    img = ""
                    from core import servertools
                    devuelve = servertools.findvideos(v["url"], True)
                    if devuelve:
                        servers_module = __import__("servers." + devuelve[0][2])
                        server_module = getattr(servers_module, devuelve[0][2])
                        urls = server_module.get_video_url(devuelve[0][1])
                        url = urls[0][1]
                        self.url_videos[v["url"]] = {"url": url}
                    else:
                        self.url_videos[v["url"]] = {"url": "Not found"}
                        continue
            else:
                if self.url_videos.get(v["url"])["url"] == "Not found":
                    continue
                img = self.url_videos.get(v["url"])["img"]
                url = self.url_videos.get(v["url"])["url"]

            item.setProperty("img", img)
            item.setProperty("url", url)
            item.setProperty("title", v["title"])
            videos.append(item)

        xbmc.executebuiltin("SetProperty(loading-videos,1,Home)")
        self.getControl(33524).reset()
        if videos:
            self.getControl(33524).addItems(videos)
            xbmc.executebuiltin("ClearProperty(no-videos,Home)")
            self.setFocusId(33524)
        else:
            item = xbmcgui.ListItem("No encontrado")
            item.setProperty("title", "Vídeos eliminados o no disponibles")
            self.getControl(33524).addItem(item)
            self.setFocusId(33519)


    def setNews(self):
        xbmc.executebuiltin("ClearProperty(loading-news,Home)")
        news = []
        for n in self.match["news"]:
            item = xbmcgui.ListItem(n["title"])
            if not self.url_news.get(n["url"]):
                data_n = httptools.downloadpage(n["url"]).data
                img = find_single_match(data_n, 'name="og:image" content="([^"]+)"')
                text1 = find_single_match(data_n, '<p class="teaser">(.*?)</p>')
                if text1:
                    text1 = "[B]%s[/B]\n" % text1
                text = find_single_match(data_n, '<div class="ni-text-body">(.*?)<!-- START LIST -->')
                text = text1 + htmlclean(text.replace("</p>", "\n"))
                self.url_news[n["url"]] = {"text": text, "img": img}
            else:
                img = self.url_news.get(n["url"])["img"]
                text = self.url_news.get(n["url"])["text"]
                
            item.setProperty("img", img)
            item.setProperty("text", text)
            item.setProperty("date", n["date"])
            item.setProperty("title", n["title"])
            news.append(item)

        xbmc.executebuiltin("SetProperty(loading-news,1,Home)")
        self.getControl(33525).reset()
        if news:
            self.getControl(33525).addItems(news)
            xbmc.executebuiltin("ClearProperty(no-news,Home)")
            self.setFocusId(32525)
        else:
            self.setFocusId(33520)
        

    def setLineUps(self, team):
        xbmc.executebuiltin("ClearProperty(has_details,Home)")
        self.getControl(32519).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","pitch.png"))
        xbmc.executebuiltin("SetProperty(has_lineups,1,home)")

        self.current_lineup = team
        
        if team == "team1":
            self.teamname = self.match["name1"]
            self.formationlabel = self.match[team]["formation"]
            self.thumb = self.match["thumb1"]

            self.getControl(32527).setLabel("Equipo Visitante")
        else:
            self.teamname = self.match["name2"]
            self.formationlabel = self.match[team]["formation"]
            self.thumb = self.match["thumb2"]

            self.getControl(32527).setLabel("Equipo Local")

        self.getControl(32522).setLabel("Once Inicial:")
        self.getControl(32523).setLabel("Suplentes:")

        self.getControl(32521).setLabel(self.teamname)
        self.getControl(32520).setImage(self.thumb)

        if self.formationlabel:
            self.getControl(32518).setLabel(self.formationlabel)

        if team == "team1" and self.coach1:
            self.getControl(32526).setLabel("[COLOR selected]" + "Entrenador:[/COLOR] " + self.coach1)
        elif team == "team2" and self.coach2:
            self.getControl(32526).setLabel("[COLOR selected]" + "Entrenador:[/COLOR] " + self.coach2)

        starters = []
        for jug in self.match[team]["once"]:
            item = xbmcgui.ListItem('[COLOR gold]%s.[/COLOR] %s' % (jug["num"], jug["name"]))
            item.setProperty('url', jug["url"])
            starters.append(item)

        self.getControl(32524).reset()
        self.getControl(32524).addItems(starters)

        subs = []
        for jug in self.match[team]["supl"]:
            item = xbmcgui.ListItem('[COLOR gold]%s.[/COLOR] %s' % (jug["num"], jug["name"]))
            item.setProperty('url', jug["url"])
            subs.append(item)

        self.getControl(32525).reset()
        self.getControl(32525).addItems(subs)

        pitch = self.getControl(32519)
        pitchPosition = pitch.getPosition()
        pitchHeight = pitch.getHeight()
        pitchWidth = pitch.getWidth()

        if self.formationlabel:
            from core import jsontools
            json_formations = filetools.join(config.get_runtime_path(),"resources","formations.dict")
            formationsjson = eval(filetools.read(json_formations))
            formation = formationsjson[self.formationlabel]["once"]
        else:
            formation = None

        if formation:
            for i, pos in enumerate(formation):
                image_size = self.getShirtHeight(pitchHeight, pos[1])
                image_x = int(pos[0]*float(pitchWidth))+int(0.15*image_size)
                image_y =  int(pos[1]*float(pitchHeight))+int(0.15*image_size)
                self.getControl(33600+i).setPosition(image_x,image_y)
                self.getControl(33600+i).setWidth(image_size)
                self.getControl(33600+i).setHeight(image_size)
                self.getControl(33600+i).setImage(self.match[team]["once"][i]["img"])
                label = self.get_label(self.getControl(33600+i), "[B]" + self.match[team]["once"][i]["name"] + "[/B]")
                self.addControl(label)
                self.controls.append(label)
                label.setEnabled(False)

        self.setFocusId(32524)

    def resetControls(self):
        for i in range(33600, 33611):
            try:
                self.getControl(i).setImage("")
            except:
                pass
        self.removeControls(self.controls)
        self.controls = []


    def stopRunning(self):
        self.isRunning = False
        xbmc.executebuiltin("ClearProperty(has_lineups,Home)")
        xbmc.executebuiltin("ClearProperty(has_details,Home)")
        self.close()

    def onAction(self,action):
        if action.getId() == 92 or action.getId() == 10:
            self.stopRunning()

    def onClick(self,controlId):
        if controlId == 32514:
            if self.controls:
                self.resetControls()
            self.setLineUps("team1")
        elif controlId == 32515:
            if self.controls:
                self.resetControls()
            self.setLineUps("team2")
        elif controlId == 32528:
            if self.controls: 
                self.resetControls()
            self.setEventDetails(reload=True)
        elif controlId == 32527:
            if self.controls: 
                self.resetControls()
            if self.current_lineup == "team1":
                self.setLineUps("team2")
            else:
                self.setLineUps("team1")
        elif controlId == 33515:
            self.lista = "eventos"
            self.reset_buttons(33515)
            self.setEvents()
        elif controlId == 33516:
            self.lista = "stats"
            self.reset_buttons(33516)
            self.setStats()
        elif controlId == 33517:
            self.lista = "stadium"
            self.reset_buttons(33517)
            self.setStadium()
            self.setFocusId(33515)
        elif controlId == 33518:
            self.lista = "comments"
            self.reset_buttons(33518)
            self.setComments()
        elif controlId == 33519:
            self.lista = "videos"
            self.reset_buttons(33519)
            self.setVideos()
        elif controlId == 33520:
            self.lista = "news"
            self.reset_buttons(33520)
            self.setNews()
        elif controlId == 33551:
            self.lista = "eventos"
            self.reset_buttons(33515)
            self.setEventDetails(reload=True)
        elif controlId == 33525:
            select = self.getControl(33525).getSelectedItem()
            img = select.getProperty("img")
            title = select.getProperty("title")
            text = select.getProperty("text")
            main = newsDialog('script-matchcenter-News.xml', config.get_runtime_path(), img=img, text=text, title=title)
            main.doModal()
            del main
        elif controlId == 33524:
            select = self.getControl(33524).getSelectedItem()
            url = select.getProperty("url")
            main = videoDialog('script-matchcenter-Video.xml', config.get_runtime_path(), url=url)
            main.doModal()
            del main
        elif controlId == 32524 or controlId == 32525 or controlId == 32516 or controlId == 32517:
            select = self.getControl(controlId).getSelectedItem()
            url = select.getProperty("url")
            if url:
                infoplayers.start(url)
        elif controlId == 33557:
            tweets.start("persona", self.twitter1)
        elif controlId == 33559:
            tweets.start("persona", self.twitter2)
        elif controlId == 33562:
            buscar = self.hashtag + " OR #" + self.match["name1"] + self.match["name2"]
            if self.twitter1:
                buscar += " OR @" + self.twitter1
            if self.twitter2:
                buscar += " OR @" + self.twitter2
            tweets.start("hashtag", buscar)


    def reset_buttons(self, bt_except):
        buttons = [33515, 33516, 33517, 33518, 33519, 33520]
        for b in buttons:
            if b == bt_except:
                self.getControl(b).setEnabled(False)
            else:
                self.getControl(b).setEnabled(True)

        if not self.match["stats"]:
            self.getControl(33516).setEnabled(False)
        if not self.match["stadium"] and not self.match["tv"]:
            self.getControl(33517).setEnabled(False)
        if not self.match["cronica"]:
            self.getControl(33518).setEnabled(False)
        if not self.match["videos"]:
            self.getControl(33519).setEnabled(False)
        if not self.match["news"]:
            self.getControl(33520).setEnabled(False)

        lista = [32516, 32517, 33521, 33522, 33523, 33524, 33525, 33526]
        for l in lista:
            try:
                self.getControl(l).reset()
            except:
                pass

        xbmc.executebuiltin("SetProperty(no-stats,1,Home)")
        xbmc.executebuiltin("SetProperty(no-stadium,1,Home)")
        xbmc.executebuiltin("SetProperty(no-comments,1,Home)")
        xbmc.executebuiltin("SetProperty(no-videos,1,Home)")
        xbmc.executebuiltin("SetProperty(no-news,1,Home)")


    def getShirtHeight(self, pitchHeigh, positionPercent):
        shirtHeightPercent = 0.06*positionPercent + 0.1204
        return int(shirtHeightPercent*pitchHeigh)


    def get_label(self, imagecontrol, label):
        image_position = imagecontrol.getPosition()
        image_height = imagecontrol.getHeight()
        image_width = imagecontrol.getWidth()

        label_x = int(image_position[0]-0.5*image_width)
        label_y = int(image_position[1]+image_height-0.02*image_height)
        label_height = int(0.2*image_height)
        label_width = int(2*image_width)
        return xbmcgui.ControlButton(label_x, label_y, label_width, label_height, label, '', '', 0, 0, 0x00000002, "font10", "0xFFEB9E17", "0xFFEB9E17")


    def translatematch(self, string):
        if string.lower() == "finalizado": return "Finalizado"
        elif string.lower() == "des": return "Descanso"
        elif string.lower() == "aplazado": return "Aplazado"
        elif "'" in string: return string
        else: return "Por empezar"


def showDetails(url, liga):
    main = detailsDialog('script-matchcenter-EventDetails.xml', config.get_runtime_path(), url=url, liga=liga)
    main.doModal()
    del main


class newsDialog(xbmcgui.WindowXMLDialog):
        
    def __init__( self, *args, **kwargs ):
        self.img = kwargs["img"]
        self.text = kwargs["text"]
        self.title = kwargs["title"]

    def onInit(self):
        self.setCoordinateResolution(2)
        self.getControl(32500).setImage(self.img)
        self.getControl(32501).setText(self.text)
        self.getControl(32502).setText(self.title)
        pos = self.getControl(32502).getHeight()
        self.getControl(32501).setPosition(440, 390+pos)
        self.getControl(32501).setHeight(600-390+pos)
        xbmc.executebuiltin("ClearProperty(no-text,Home)")
        if not self.text:
            xbmc.executebuiltin("SetProperty(no-text,1,Home)")

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
        self.getControl(7).setVisible(False)
        self.getControl(13).setVisible(False)
        self.getControl(1).setVisible(True)
        self.getControl(11).setVisible(True)
        xlistitem = xbmcgui.ListItem(path=self.url)
        pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        pl.clear()
        pl.add(self.url, xlistitem)
        self.player = xbmc.Player()
        self.player.play(pl, windowed=True)
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
              
    def in_out(self):
        global exit_loop
        self.getControl(14).setVisible(True)
        while datetime.now().second % 8 != 0:
            if exit_loop or not xbmc.Player().isPlaying():
                break
        self.getControl(14).setVisible(False)
