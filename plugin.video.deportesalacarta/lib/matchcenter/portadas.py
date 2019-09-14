# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
#------------------------------------------------------------

import xbmcgui
import marcadores

from core import config


class detailsDialog(xbmcgui.WindowXMLDialog):

    def onInit(self):
        self.setCoordinateResolution(2)
        self.getControl(32503).setVisible(False)
        self.portada = 0
        self.imagenes = []
        self.setPortada()

    def setPortada(self):
        if not self.imagenes:
            self.portadas = marcadores.get_portadas()
            for thumb in self.portadas:
                self.imagenes.append(thumb)

        if not self.imagenes:
            from platformcode import platformtools
            platformtools.dialog_ok("No hay portadas disponibles", "Inténtalo de nuevo más tarde")
            self.close()

        self.getControl(32501).setImage(self.imagenes[self.portada])
        self.setFocusId(32502)
        self.getControl(32503).setVisible(True)
        if len(self.imagenes) == 1:
            self.getControl(32502).setVisible(False)
            self.getControl(32503).setVisible(False)

    def onClick(self,controlId):
        if controlId == 32502 or controlId == 32503:
            if self.portada == len(self.imagenes) - 1:
                self.portada = 0
            else:
                self.portada += 1
            self.setPortada()


def start(window):
    main = detailsDialog('script-matchcenter-Portadas.xml', config.get_runtime_path())
    main.doModal()
    del main
    window.doModal()
