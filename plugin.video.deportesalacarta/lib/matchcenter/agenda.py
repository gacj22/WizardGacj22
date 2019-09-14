# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
#------------------------------------------------------------

import re
import xbmc
import xbmcgui
import urllib
import marcadores

from core import config
from core import filetools


class detailsDialog(xbmcgui.WindowXMLDialog):

    def onInit(self):
        self.datos = []
        self.dia = 0
        self.url = "deporte"
        self.data_c = ""
        self.setCoordinateResolution(2)

        xbmc.executebuiltin("ClearProperty(no-games,Home)")
        self.getControl(32540).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","goal.png"))
        self.reset_buttons(33503)
        xbmc.executebuiltin("SetProperty(loading-script-matchcenter-agenda,1,home)")
        self.setAgenda()
        xbmc.executebuiltin("ClearProperty(loading-script-matchcenter-agenda,Home)")
        self.ligas = [['primera', 'la-liga'], ['premier', 'premier-league'], ['serie_a', 'calcio-serie-a'], ['bundesliga', 'bundesliga'],
                      ['champions', 'liga-campeones'], ['ligue1', 'ligue-1'], ['segunda', 'segunda-division-espana'],
                      ['eleague', 'europa-league'], ['20130624110336', 'automovilismo'], ['20130724090914', 'balonmano'], ['20130627010504', 'ciclismo'],
                      ['20130723062518', 'futbol-americano'], ['20130627015342', 'futbol-sala'], ['20130724083030-bola', 'golf'], ['20130629041459', 'motociclismo'],
                      ['20141020014900', 'padel'], ['20130720113150', 'rugby'], ['20140610071226', 'deportes-de-invierno'], ['20130723120551', 'futbol-playa']]
        items_ligas = []
        i = 0
        for thumb, liga in self.ligas:
            item = xbmcgui.ListItem(liga)
            if i < 8:
                thumb = "http://www.resultados-futbol.com/media/img/league_logos/%s.png" % thumb
            else:
                thumb = "http://static.futbolenlatv.com/img/%s-%s.png" % (thumb, liga)
            item.setArt({'thumb': thumb})
            item.setProperty('thumb', thumb)
            items_ligas.append(item)
            i += 1
        self.getControl(32503).addItems(items_ligas)


    def setAgenda(self):
        self.getControl(33500).setText("")
        self.getControl(33501).setVisible(False)
        self.getControl(33502).setVisible(False)
        self.items = []
        if not self.datos:
            self.datos, self.data_c = marcadores.get_agenda(self.url, self.data_c)

        if self.datos:
            for k, value in self.datos[self.dia].items():
                for v in value:
                    item = xbmcgui.ListItem("")
                    item.setProperty('hora', v["hora"])
                    item.setProperty('icono', v["icono"])
                    item.setProperty('titulo', v["titulo"])
                    item.setProperty('subtitle', v["subtitle"])
                    if len(v["info_evento"]) == 1:
                        item.setProperty('info', v["info_evento"][0])
                    else:
                        item.setProperty('local', v["info_evento"][0])
                        item.setProperty('img_local', urllib.quote(v["info_evento"][1], safe=":/"))
                        item.setProperty('img_visitante', urllib.quote(v["info_evento"][2], safe=":/"))
                        item.setProperty('visitante', v["info_evento"][3])
                    for i, c in enumerate(v["canales"]):
                        item.setProperty('canal%s' % str(i+1), c[0])
                        item.setProperty('canalt%s' % str(i+1), c[1])
                        if i == 2:
                            break
                    
                    item.setProperty('icono', v["icono"])
                    if self.url == "deporte":
                        deporte = re.split(r"\d+-", v["icono"])[1].replace(".png", "").replace("bola-", "").capitalize()
                        deporte = deporte.replace("Futbol", "Fútbol").replace("-", " ")
                        item.setProperty('deporte', deporte)
                            
                    self.items.append(item)

        self.getControl(32500).reset()
        xbmc.executebuiltin("ClearProperty(no-games,Home)")
        self.getControl(32500).addItems(self.items)
        if self.items:
            self.setFocusId(32500)
            self.getControl(33500).setText(self.datos[self.dia].keys()[0])

        if self.dia == 0:
            self.getControl(33501).setVisible(False)
        else:
            self.getControl(33501).setVisible(True)
        if self.dia == len(self.datos) - 1:
            self.getControl(33502).setVisible(False)
        else:
            self.getControl(33502).setVisible(True)


    def onClick(self,controlId):
        if controlId == 33501:
            self.dia -= 1
            self.setAgenda()
        if controlId == 33502:
            self.dia += 1
            self.setAgenda()
        if controlId == 33503:
            self.url = "deporte"
            self.datos = []
            self.dia = 0
            self.setAgenda()
            self.reset_buttons(33503)
        if controlId == 33504:
            self.url = ""
            self.datos = []
            self.dia = 0
            self.setAgenda()
            self.reset_buttons(33504)
        if controlId == 33505:
            self.url = "deporte/baloncesto"
            self.datos = []
            self.dia = 0
            self.setAgenda()
            self.reset_buttons(33505)
        if controlId == 33506:
            self.url = "deporte/tenis"
            self.datos = []
            self.dia = 0
            self.setAgenda()
            self.reset_buttons(33506)
        if controlId == 32503:
            prefix = self.getControl(32503).getSelectedItem().getLabel()
            if "resultados-futbol" in self.getControl(32503).getSelectedItem().getProperty("thumb"):
                self.url = "competicion/%s" % prefix
            else:
                self.url = "deporte/%s" % prefix

            self.datos = []
            self.dia = 0
            self.setAgenda()
            self.reset_buttons(0)


    def reset_buttons(self, bt_except):
        buttons = [33503, 33504, 33505, 33506]
        for b in buttons:
            if b == bt_except:
                self.getControl(b).setEnabled(False)
            else:
                self.getControl(b).setEnabled(True)


def start(window):
    main = detailsDialog('script-matchcenter-Agenda.xml', config.get_runtime_path())
    main.doModal()
    del main
    window.doModal()
