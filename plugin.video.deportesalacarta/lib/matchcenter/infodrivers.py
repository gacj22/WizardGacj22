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
        self.thumb = kwargs["thumb"]
        self.team = kwargs["team"]
        self.controls = []
        self.lista = ""
        self.url_news = {}
        self.idx_foto = 0
        self.news = []

    def onInit(self):
        self.setCoordinateResolution(2)
        self.getControl(33560).setEnabled(False)
        self.getControl(33559).setVisible(False)
        self.getControl(33572).setVisible(False)
        xbmc.executebuiltin("SetProperty(no-trayectoria,1,Home)")
        xbmc.executebuiltin("SetProperty(no-news,1,Home)")
        xbmc.executebuiltin("SetProperty(loading-news,1,Home)")
        news = filetools.join(config.get_runtime_path(), 'resources', 'images', 'matchcenter', 'tables.png')
        self.getControl(33542).setImage(news)
        self.setInfo()

    def setInfo(self):
        self.driver = marcadores.get_driver_data(self.url)

        self.getControl(33550).setImage(self.thumb)
        self.getControl(33551).setLabel(self.team)
        self.getControl(33552).setImage(self.driver["banner"])
        self.getControl(33553).setLabel("%s %s" % (self.driver["dorsal"], self.driver["nombre"]))

        if self.driver["images"]:
            self.getControl(33554).setImage(self.driver["images"][0])
        else:
            self.getControl(33554).setImage("")

        if len(self.driver["images"]) > 1:
            self.getControl(33559).setVisible(True)

        if self.driver["ficha"] and not self.lista:
            self.lista = "ficha"
            
        if self.lista == "ficha":
            self.setFicha()
        elif self.lista != "ficha" and self.driver["ficha"]:
            self.getControl(33560).setEnabled(True)
            
        elif self.lista == "stats":
            self.setStats()
        elif self.lista == "bio":
            self.setBio()
        elif self.lista == "news":
            self.setNews()
            
        if not self.driver["stats"]:
            self.getControl(33561).setEnabled(False)
        if not self.driver["info"]:
            self.getControl(33562).setEnabled(False)
        if not self.driver["news"]:
            self.getControl(33563).setEnabled(False)


    def setFicha(self):
        datos = []
        datos2 = []
        for i, dato in enumerate(self.driver["ficha"]):
            item = xbmcgui.ListItem("")
            label = "[COLOR darkorange]%s:[/COLOR]  %s" % (dato[0], dato[1])
            item.setProperty("label", label)
            if i % 2 == 0:
                datos.append(item)
            else:
                datos2.append(item)

        self.getControl(33568).reset()
        self.getControl(33569).reset()
        if datos:
            self.getControl(33568).addItems(datos)
            self.getControl(33569).addItems(datos2)
            self.setFocusId(33568)

    def setStats(self):
        trayect = []
        if self.driver["stats"]:
            xbmc.executebuiltin("ClearProperty(no-trayectoria,Home)")
            for year, t in self.driver["stats"].items():
                item = xbmcgui.ListItem(year)
                item.setProperty("equipo", t["equipo"])
                item.setProperty("pos", t["pos"])
                item.setProperty("chasis", t["chasis"])
                item.setProperty("motor", t["motor"])
                item.setProperty("neuma", t["neuma"])
                vict = t["vict"]
                if not vict:
                    vict = "0"
                item.setProperty("vict", vict)
                poles = t["poles"]
                if not poles:
                    poles = "0"
                item.setProperty("poles", poles)
                vr = t["vr"]
                if not vr:
                    vr = "0"
                item.setProperty("vr", vr)
                item.setProperty("puntos", t["puntos"])
                item.setProperty("gps", t["gps"])
                trayect.append(item)

        self.getControl(33565).reset()
        if trayect:
            trayect.sort(key=lambda it:int(it.getLabel()), reverse=True)
            self.getControl(33565).addItems(trayect)
            self.setFocusId(33565)


    def setBio(self):
        self.getControl(33571).setText("[B]%s[/B]" % self.driver["info"]["title"])
        self.getControl(33572).setVisible(True)
        self.getControl(33572).setText(self.driver["info"]["bio"])


    def setNews(self, index=0):
        xbmc.executebuiltin("ClearProperty(loading-news,Home)")
        if not self.news:
            self.getControl(33570).reset()
            self.news, self.next_news = marcadores.get_driver_news(self.driver["news"])
        else:
            self.getControl(33570).removeItem(self.getControl(33570).size()-1)
            self.news, self.next_news = marcadores.get_driver_news(self.next_news)
        news = []
        for url, title, img, fecha in self.news:
            item = xbmcgui.ListItem(title)
            item.setProperty("img", img)
            item.setProperty("title", title)
            item.setProperty("date", fecha)
            item.setProperty("url", url)
            news.append(item)

        if self.next_news:
            item = xbmcgui.ListItem("Más Noticias")
            item.setProperty("title", "Más Noticias")
            item.setProperty("img", "http://i.imgur.com/PQEYlfX.png")
            news.append(item)

        xbmc.executebuiltin("SetProperty(loading-news,1,Home)")
        if news:
            self.getControl(33570).addItems(news)
            xbmc.executebuiltin("ClearProperty(no-news,Home)")
            if index:
                self.getControl(33570).selectItem(index)
            self.setFocusId(33570)


    def onClick(self,controlId):
        if controlId == 33560:
            self.lista = "ficha"
            self.reset_buttons(33560)
            self.setFicha()
        elif controlId == 33561:
            self.lista = "stats"
            self.reset_buttons(33561)
            self.setStats()
        elif controlId == 33562:
            self.lista = "bio"
            self.reset_buttons(33562)
            self.setBio()
        elif controlId == 33563:
            self.lista = "news"
            self.reset_buttons(33563)
            self.setNews()
        elif controlId == 33570:
            select = self.getControl(33570).getSelectedItem()
            if select.getLabel() == "Más Noticias":
                self.setNews(index=self.getControl(33570).getSelectedPosition())
            else:
                img = select.getProperty("img")
                title = select.getProperty("title")
                url = select.getProperty("url")
                text = marcadores.get_content_news(url)
                main = newsDialog('script-matchcenter-News.xml', config.get_runtime_path(), img=img, text=text, title=title)
                main.doModal()
                del main
        elif controlId == 33559:
            if self.idx_foto == len(self.driver["images"]) - 1:
                self.idx_foto = 0
            else:
                self.idx_foto += 1
            self.getControl(33554).setImage(self.driver["images"][self.idx_foto])


    def reset_buttons(self, bt_except):
        buttons = [33560, 33561, 33562, 33563]
        for b in buttons:
            if b == bt_except:
                self.getControl(b).setEnabled(False)
            else:
                self.getControl(b).setEnabled(True)

        if not self.driver["stats"]:
            self.getControl(33561).setEnabled(False)
        if not self.driver["info"]:
            self.getControl(33562).setEnabled(False)
        if not self.driver["news"]:
            self.getControl(33563).setEnabled(False)

        lista = [33565, 33566, 33567, 33568, 33569, 33570]
        for l in lista:
            try:
                self.getControl(l).reset()
            except:
                pass

        xbmc.executebuiltin("SetProperty(no-trayectoria,1,Home)")
        xbmc.executebuiltin("SetProperty(no-news,1,Home)")
        self.getControl(33571).setText("")
        self.getControl(33572).setText("")
        self.getControl(33572).setVisible(False)


def start(url, thumb, team):
    ventana = infoDialog('script-matchcenter-InfoDrivers.xml', config.get_runtime_path(), url=url, thumb=thumb, team=team)
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