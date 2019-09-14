# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
#------------------------------------------------------------

import xbmcgui
import xbmc
import eventdetails
import marcadores

from core import filetools
from core import config


class detailsDialog(xbmcgui.WindowXMLDialog):
        
    def __init__( self, *args, **kwargs ):
        self.equipo = kwargs["equipo"]

    def onInit(self):
        self.setCoordinateResolution(2)
        self.setHistory(self.equipo)

    def setHistory(self, equipo):
        self.getControl(32540).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","goal.png"))
        xbmc.executebuiltin("SetProperty(loading-script-matchcenter-history,1,home)")
        self.final, self.next = marcadores.get_team_matches(equipo)

        items = []
        for match in self.next:
            item = xbmcgui.ListItem(match["team1"] + "|" + match["team2"])
            item.setProperty("local", match["team1"])
            item.setProperty("visitante", match["team2"])
            item.setProperty('competicion', match["torneo"])
            item.setProperty('escudo1', match["img1"])
            item.setProperty('escudo2', match["img2"])
            item.setProperty('url', match["url"])
            item.setProperty('fecha', match["fecha"])
            item.setProperty("result","[B]" + match["score"].replace("-", "VS") + "[/B]")
            items.append(item)
        self.getControl(32502).addItems(items)

        items = []
        for match in self.final:
            item = xbmcgui.ListItem(match["team1"] + "|" + match["team2"])
            item.setProperty("local", match["team1"])
            item.setProperty("visitante", match["team2"])
            item.setProperty('competicion', match["torneo"])
            item.setProperty('escudo1', match["img1"])
            item.setProperty('escudo2', match["img2"])
            item.setProperty('url', match["url"])
            item.setProperty('fecha', match["fecha"])
            item.setProperty("result","[B]" + match["score"] + "[/B]")
            items.append(item)
        items.reverse()
        self.getControl(32503).addItems(items)

        xbmc.executebuiltin("ClearProperty(loading-script-matchcenter-history,Home)")
        xbmc.executebuiltin("SetProperty(has_history,1,home)")

    def onClick(self,controlId):
        if controlId == 32502:
            url = self.getControl(32502).getSelectedItem().getProperty("url")
            torneo = self.getControl(32502).getSelectedItem().getProperty("competicion")
            eventdetails.showDetails(url, torneo)
        elif controlId == 32503:
            url = self.getControl(32503).getSelectedItem().getProperty("url")
            torneo = self.getControl(32503).getSelectedItem().getProperty("competicion")
            eventdetails.showDetails(url, torneo)

def start(equipo):
    main = detailsDialog('script-matchcenter-MatchHistory.xml', config.get_runtime_path(), equipo=equipo)
    main.doModal()
    del main