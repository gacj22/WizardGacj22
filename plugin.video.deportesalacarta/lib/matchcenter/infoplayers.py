# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
#------------------------------------------------------------

import xbmcgui
import xbmc
import re
import marcadores

from core import filetools
from core import config
from core import httptools
from core.scrapertools import *


class infoDialog(xbmcgui.WindowXMLDialog):
    def __init__( self, *args, **kwargs ):
        self.isRunning = True
        self.url = kwargs["url"]
        self.controls = []
        self.lista = ""
        self.url_news = {}
        self.idx_foto = 0

    def onInit(self):
        self.setCoordinateResolution(2)
        self.getControl(33560).setEnabled(False)
        self.getControl(33556).setVisible(False)
        self.getControl(33557).setVisible(False)
        self.getControl(33559).setVisible(False)
        xbmc.executebuiltin("SetProperty(no-trayectoria,1,Home)")
        xbmc.executebuiltin("SetProperty(no-news,1,Home)")
        xbmc.executebuiltin("SetProperty(loading-news,1,Home)")
        news = filetools.join(config.get_runtime_path(), 'resources', 'images', 'matchcenter', 'tables.png')
        self.getControl(33542).setImage(news)
        self.setInfo(self.url)

    def setInfo(self, url):
        self.getControl(33601).reset()
        self.getControl(33601).setVisible(False)
        self.info = marcadores.get_player_info(url)
        temps = []
        for i, temp in enumerate(self.info["seasons"]):
            if temp["select"]:
                xbmc.executebuiltin("SetProperty(temporada,%s,Home)" % temp["season"])
                index = i
                continue
            item = xbmcgui.ListItem(temp["season"])
            item.setProperty("url", temp["url"])
            temps.append(item)

        if temps:
            self.getControl(33601).addItems(temps)
            self.getControl(33601).selectItem(index)
        
        self.getControl(33550).setImage(self.info["escudo"])
        self.getControl(33551).setLabel(self.info["equipo"])
        self.getControl(33552).setLabel(self.info["temp"].replace("Temporada ", ""))
        self.getControl(33553).setLabel(self.info["nombre"])

        if self.info["fotos"]:
            self.getControl(33554).setImage(self.info["fotos"][0])
        else:
            self.getControl(33554).setImage("")

        datos = []
        count = 0
        for i, dato in enumerate(self.info["ficha"]):
            if i == 0:
                item = xbmcgui.ListItem("")
                item.setProperty("dato1", dato)
            elif i % 2 == 0:
                item = xbmcgui.ListItem("")
                item.setProperty("dato1", dato)
                if i == len(self.info["ficha"]) - 1:
                    datos.append(item)
            else:
                item.setProperty("dato2", dato)
                datos.append(item)


        self.getControl(33555).reset()
        self.getControl(33555).addItems(datos)
        if self.info["twitter"]:
            self.getControl(33556).setVisible(True)
            self.getControl(33557).setVisible(True)
            self.getControl(33558).setLabel("@"+self.info["twitter"])

        if len(self.info["fotos"]) > 1:
            self.getControl(33559).setVisible(True)

        if self.info["stats"] and not self.lista:
            self.lista = "stats"
            
        if self.lista == "stats":
            self.setStats()
        elif self.lista != "stats" and self.info["stats"]:
            self.getControl(33560).setEnabled(True)
            
        elif self.lista == "trayectoria":
            self.setTrayectoria()
        elif self.lista == "titulos":
            self.setTitulos()
        elif self.lista == "efeme":
            self.setEfeme()
        elif self.lista == "news":
            self.setNews()
            
        if not self.info["historico"] and not self.info["trayectoria"]:
            self.getControl(33561).setEnabled(False)
        if not self.info["titulos"]:
            self.getControl(33562).setEnabled(False)
        if not self.info["efeme"]:
            self.getControl(33563).setEnabled(False)
        if not self.info["news"]:
            self.getControl(33564).setEnabled(False)


    def setStats(self):
        estadisticas = []
        for stats in self.info["stats"]:
            item = xbmcgui.ListItem(stats["liga"])
            item.setProperty("liga", stats["liga"])
            item.setProperty("logo", stats["img"])
            item.setProperty("pj", stats["pj"])
            item.setProperty("titu", stats["titu"])
            item.setProperty("compl", stats["compl"])
            item.setProperty("supl", stats["supl"])
            item.setProperty("minutos", stats["minutos"])
            item.setProperty("tam", stats["tam"])
            item.setProperty("troj", stats["troj"])
            item.setProperty("asist", stats["asist"])
            item.setProperty("goles", stats["goles"])
            estadisticas.append(item)

        self.getControl(33565).reset()
        if estadisticas:
            self.getControl(33565).addItems(estadisticas)
            xbmc.executebuiltin("ClearProperty(no-stats,Home)")
            self.setFocusId(33565)
        else:
            self.setFocusId(33560)

    def setTrayectoria(self):
        trayect = []
        if self.info["trayectoria"]:
            xbmc.executebuiltin("ClearProperty(no-trayectoria,Home)")
            for t in self.info["trayectoria"]:
                item = xbmcgui.ListItem(t["equipo"])
                item.setProperty("equipo", t["equipo"])
                item.setProperty("temp", t["temp"])
                item.setProperty("div", t["div"])
                item.setProperty("edad", t["edad"])
                item.setProperty("pj", t["pj"])
                item.setProperty("titu", t["titu"])
                item.setProperty("compl", t["compl"])
                item.setProperty("entra", t["entra"])
                item.setProperty("sale", t["sale"])
                item.setProperty("tam", t["tam"])
                item.setProperty("troj", t["troj"])
                item.setProperty("goles", t["goles"])
                item.setProperty("minutos", t["minutos"])
                trayect.append(item)
        else:
            self.getControl(33592).setLabel("HISTÓRICO DE EQUIPOS")
            for t in self.info["historico"]:
                item = xbmcgui.ListItem(t["equipo"])
                label = "%s - Temporadas: %s" % (t["equipo"], t["seasons"])
                item.setProperty("equipo2", label)
                item.setProperty("logo", t["img"])
                trayect.append(item)
                
        self.getControl(33566).reset()
        if trayect:
            self.getControl(33566).addItems(trayect)
            xbmc.executebuiltin("ClearProperty(no-stats,Home)")
            self.setFocusId(33566)
        else:
            self.setFocusId(33561)


    def setTitulos(self):
        copas = {'Champions League': '4', 'Liga BBVA': '11', 'Copa del Rey': '94', 'Supercopa de España': '93',
                 'Europa League': '7', 'Mundial de Clubes': '318', 'Mundial': '101', 'Eurocopa': '102',
                 'Premier League': '12', 'Bundesliga': '10', 'Serie A': '13', 'Eredivisie': '16',
                 'Copa Inglesa': '29', 'Copa de la Liga Inglesa': '47'}
        copas2 = {'Balón de Oro': '', 'Bota de Oro': '', 'Supercopa de Europa': ''}
        titulos = []
        for tit in self.info["titulos"]:
            item = xbmcgui.ListItem(tit["titulo"])
            item.setProperty("titulo", tit["titulo"])
            item.setProperty("seasons", tit["seasons"])

            if copas2.get(tit["copa"]):
                copa = "http://tmssl.akamaized.net/images/titel/verybigquad/195.png"
            elif copas.get(tit["copa"]):
                copa = "http://tmssl.akamaized.net/images/erfolge/verybigquad/%s.png" % copas[tit["copa"]]
            else:
                copa = "http://tmssl.akamaized.net/images/erfolge/verybigquad/default.png"
            item.setProperty("copa", copa)

            titulos.append(item)

        self.getControl(33567).reset()
        if titulos:
            self.getControl(33567).addItems(titulos)
            self.setFocusId(33567)
        else:
            self.setFocusId(33562)

    def setEfeme(self):
        efeme = []
        efeme2 = []
        for i, efe in enumerate(self.info["efeme"]):
            item = xbmcgui.ListItem(efe["desc"])
            label = "[COLOR darkorange]%s:[/COLOR]  %s" % (efe["desc"], efe["value"])
            item.setProperty("label", label)
            if i % 2 == 0:
                efeme.append(item)
            else:
                efeme2.append(item)

        self.getControl(33568).reset()
        self.getControl(33569).reset()
        if efeme:
            self.getControl(33568).addItems(efeme)
            self.getControl(33569).addItems(efeme2)
            self.setFocusId(33568)
        else:
            self.setFocusId(33563)


    def setNews(self):
        xbmc.executebuiltin("ClearProperty(loading-news,Home)")
        news = []
        for n in self.info["news"]:
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
        self.getControl(33570).reset()
        if news:
            self.getControl(33570).addItems(news)
            xbmc.executebuiltin("ClearProperty(no-news,Home)")
            self.setFocusId(33570)
        else:
            self.setFocusId(33564)


    def onClick(self,controlId):
        if controlId == 33560:
            self.lista = "stats"
            self.reset_buttons(33560)
            self.setStats()
        elif controlId == 33561:
            self.lista = "trayectoria"
            self.reset_buttons(33561)
            self.setTrayectoria()
        elif controlId == 33562:
            self.lista = "titulos"
            self.reset_buttons(33562)
            self.setTitulos()
        elif controlId == 33563:
            self.lista = "efeme"
            self.reset_buttons(33563)
            self.setEfeme()
        elif controlId == 33564:
            self.lista = "news"
            self.reset_buttons(33564)
            self.setNews()
        elif controlId == 33570:
            select = self.getControl(33570).getSelectedItem()
            img = select.getProperty("img")
            title = select.getProperty("title")
            text = select.getProperty("text")
            main = newsDialog('script-matchcenter-News.xml', config.get_runtime_path(), img=img, text=text, title=title)
            main.doModal()
            del main
        elif controlId == 33557:
            import tweets
            tweets.start("persona", self.info["twitter"])
        elif controlId == 33559:
            if self.idx_foto == len(self.info["fotos"]) - 1:
                self.idx_foto = 0
            else:
                self.idx_foto += 1
            self.getControl(33554).setImage(self.info["fotos"][self.idx_foto])
        elif controlId == 33600:
            if xbmc.getCondVisibility("Control.IsVisible(33601)"):
                self.getControl(33601).setVisible(False)
            else:
                self.getControl(33601).setVisible(True)
        elif controlId == 33601:
            temporada = self.getControl(33601).getSelectedItem().getProperty("url")
            self.setInfo(temporada)  


    def reset_buttons(self, bt_except):
        buttons = [33560, 33561, 33562, 33563, 33564]
        for b in buttons:
            if b == bt_except:
                self.getControl(b).setEnabled(False)
            else:
                self.getControl(b).setEnabled(True)

        if not self.info["historico"] and not self.info["trayectoria"]:
            self.getControl(33561).setEnabled(False)
        if not self.info["titulos"]:
            self.getControl(33562).setEnabled(False)
        if not self.info["efeme"]:
            self.getControl(33563).setEnabled(False)
        if not self.info["news"]:
            self.getControl(33564).setEnabled(False)

        lista = [33565, 33566, 33567, 33568, 33569, 33570]
        for l in lista:
            try:
                self.getControl(l).reset()
            except:
                pass

        xbmc.executebuiltin("SetProperty(no-trayectoria,1,Home)")
        xbmc.executebuiltin("SetProperty(no-news,1,Home)")
        self.getControl(33592).setLabel("")


def start(url):
    ventana = infoDialog('script-matchcenter-InfoPlayers.xml', config.get_runtime_path(), url=url)
    ventana.doModal()
    del ventana


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