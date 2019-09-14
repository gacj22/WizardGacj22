# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
#------------------------------------------------------------

import xbmcgui
import xbmc
import matchhistory
import marcadores

from core import filetools
from core import config


class detailsDialog(xbmcgui.WindowXMLDialog):

    def onInit(self):
        self.setCoordinateResolution(2)
        self.ligas = [['primera', 'primera'], ['premier', 'premier'], ['serie_a', 'serie_a'], ['bundesliga', 'bundesliga'], ['ligue_1', 'ligue1'], ['segunda', 'segunda'],
                 ['holanda', 'holanda'], ['portugal', 'liga_nos'], ['rusia', 'liga_rusa'], ['primera_division_argentina', 'primera_argentina'],
                 ['usa', 'mls'], ['brasil', 'serie_a_brasil']]
        items_ligas = []
        for liga, thumb in self.ligas:
            item = xbmcgui.ListItem(liga)
            thumb = "http://www.resultados-futbol.com/media/img/league_logos/%s.png" % thumb
            item.setArt({'thumb': thumb})
            items_ligas.append(item)
        self.getControl(32503).addItems(items_ligas)
        self.setFocusId(32503)
        self.getControl(32540).setImage(filetools.join(config.get_runtime_path(), "resources", "images", "matchcenter", "goal.png"))
        xbmc.executebuiltin("SetProperty(loading-script-matchcenter-tables,1,home)")


    def setTable(self, liga):
        self.getControl(32501).reset()
        self.getControl(32505).reset()
        self.getControl(32505).setVisible(False)

        self.clasif, self.temps = marcadores.get_table(liga)
        self.getControl(32500).setLabel(self.clasif[0]["liga"])
        self.table = []
        for team in self.clasif:
            item = xbmcgui.ListItem(team["team"])
            item.setArt({ 'thumb': team["img"] })
            item.setProperty('url',team["url"])
            
            item.setProperty('position', team["pos"])        
            item.setProperty('totalgames', team["pj"])
            item.setProperty('totalwins', team["win"])
            item.setProperty('totaldraws', team["draw"])
            item.setProperty('totallosts', team["lose"])
            item.setProperty('goalsscored', team["gf"])
            item.setProperty('goalsconceeded', team["gc"])
            item.setProperty('goaldifference', str(int(team["gf"]) - int(team["gc"])))
            item.setProperty('points', team["pts"])
            item.setProperty('color', "MatchCenter/button-%s.png" % team["color"])
            self.table.append(item)
            
        self.getControl(32501).addItems(self.table)
        self.setFocusId(32501)

        temporadas = []
        for i, temp in enumerate(self.temps):
            if temp["select"]:
                xbmc.executebuiltin("SetProperty(temporada,%s,Home)" % temp["temp"])
                index = i
                continue
            item = xbmcgui.ListItem(temp["temp"])
            item.setProperty("url", temp["url"])
            temporadas.append(item)
        self.getControl(32505).addItems(temporadas)
        self.getControl(32505).selectItem(index)

        xbmc.executebuiltin("ClearProperty(loading-script-matchcenter-tables,Home)")
        return


    def onClick(self,controlId):
        if controlId == 32501:
            equipo = self.getControl(32501).getSelectedItem().getProperty("url")
            liga = self.getControl(32501).getSelectedItem().getProperty("liga")
            matchhistory.start(equipo)
        elif controlId == 32503:
            liga = self.getControl(32503).getSelectedItem().getLabel()
            self.setTable(liga)
        elif controlId == 32504:
            if xbmc.getCondVisibility("Control.IsVisible(32505)"):
                self.getControl(32505).setVisible(False)
            else:
                self.getControl(32505).setVisible(True)
                self.setFocusId(32505)
        elif controlId == 32505:
            temporada = self.getControl(32505).getSelectedItem().getProperty("url")
            self.setTable(temporada)            


def start(window):
    main = detailsDialog('script-matchcenter-LeagueTables.xml', config.get_runtime_path())
    main.doModal()
    del main
    window.doModal()
