# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
#------------------------------------------------------------

import xbmcgui
import xbmc
import marcadores

from core import httptools
from core import config
from core.scrapertools import *


class detailsDialog(xbmcgui.WindowXMLDialog):

    def onInit(self):
        self.setCoordinateResolution(2)
        self.page = 0
        self.items = {}
        self.url = ""
        self.setNews()

    def setNews(self):
        self.getControl(32515).setVisible(False)
        self.getControl(32516).setVisible(False)
        if self.items.get(self.page):
            items_news = self.items[self.page]["items"]
            self.news = {}
        else:
            self.news = marcadores.get_news(self.url)
            items_news = []
            for k, v in self.news.items():
                if k == "next_page":
                    continue
                item = xbmcgui.ListItem(v["title"])
                item.setArt({'thumb': v["thumb"]})
                item.setProperty('thumb', v["thumb"])
                item.setProperty('date', v["date"])
                item.setProperty('subtitle', v["subtitle"])
                item.setProperty('url', v["url"])
                item.setProperty('order', str(k))
                items_news.append(item)

            items_news.sort(key=lambda it: int(it.getProperty("order")))
            self.items[self.page] = {"items": items_news, "next_page": self.news.get("next_page", "")}

        self.getControl(32501).addItems(items_news)
        self.setFocusId(32501)
        if self.items[self.page]["next_page"]:
            self.url = self.items[self.page]["next_page"]
            self.getControl(32516).setVisible(True)
        if self.page > 0:
            self.getControl(32515).setVisible(True)


    def onClick(self,controlId):
        if controlId == 32501:
            select = self.getControl(32501).getSelectedItem()
            data_n = httptools.downloadpage(select.getProperty("url")).data
            text1 = find_single_match(data_n, '<p class="teaser">(.*?)</p>')
            if text1:
                text1 = "[B]%s[/B]\n" % text1
            text = find_single_match(data_n, '<div class="ni-text-body">(.*?)<!-- START LIST -->')
            text = text1 + htmlclean(text.replace("</p>", "\n"))
            img = select.getProperty("thumb")
            title = select.getLabel()
            main = newsDialog('script-matchcenter-News.xml', config.get_runtime_path(), img=img, text=text, title=title)
            main.doModal()
            del main
        elif controlId == 32515:
            self.getControl(32501).reset()
            self.page -= 1
            self.setNews()
        elif controlId == 32516:
            self.getControl(32501).reset()
            self.page += 1
            self.setNews()


def start(window):
    main = detailsDialog('script-matchcenter-NewsMain.xml', config.get_runtime_path())
    main.doModal()
    del main
    window.doModal()


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
