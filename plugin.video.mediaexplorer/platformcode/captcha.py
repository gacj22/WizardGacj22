# -*- coding: utf-8 -*-
import xbmc
import xbmcgui

from core.libs import *


class Captcha(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.result = ''
        self.path = ''
        skin = 'Estuary' if xbmc.getSkinDir() == 'skin.estuary' else 'Default'
        self.mediapath = os.path.join(sysinfo.runtime_path, 'resources', 'skins', skin, 'media')

    def start(self, url):
        logger.trace()
        data = httptools.downloadpage(url).data
        self.path = os.path.join(sysinfo.data_path, 'captcha1.jpg')
        open(self.path, 'wb').write(data)
        self.doModal()
        return self.result

    def onInit(self):
        logger.trace()
        if int(xbmcgui.__version__.replace('.', '')) <= 2250:
            self.setCoordinateResolution(5)
        # Control Edit del xml hace que se cierre Kodi al hacer getText() en android
        # Como alternativa añadimos un control por codigo encima de este para solucionar el problema
        self.EditControl = xbmcgui.ControlEdit(
            x=445,
            y=392,
            width=390,
            height=30,
            label='',
            _alignment=2,
            focusTexture=os.path.join(self.mediapath, 'Controls', 'InputFO.png'),
            noFocusTexture=os.path.join(self.mediapath, 'Controls', 'InputNF.png')
        )
        self.EditControl.setPosition(445, 392)
        self.EditControl.setWidth(390)
        self.EditControl.setHeight(30)
        self.addControl(self.EditControl)

        self.getControl(10004).setImage(self.path)
        # self.setFocusId(self.getControl(10004))
        self.setFocus(self.EditControl)

    def onClick(self, control):
        logger.trace()
        if control in (10006, 10003):
            self.result = None
            os.remove(self.path)
            self.close()

        elif control == 10007:
            # self.result = self.getControl(10004).getText()
            self.result = self.EditControl.getText()
            os.remove(self.path)
            self.close()

    def onAction(self, action):
        logger.trace()
        action = action.getId()
        c_id = self.getFocusId()
        c_control = self.getFocus()

        if action in [10, 92]:
            self.onClick(10006)

        # Accion 1: Flecha izquierda
        elif action == 1:
            if c_id == 10007:
                self.setFocusId(10006)

        # Accion 2: Flecha derecha
        elif action == 2:
            if c_id == 10006:
                self.setFocusId(10007)

        # Accion 4: Flecha arriba
        elif action == 3:
            if c_id in (10006, 10007):
                # self.setFocusId(10004)
                self.setFocus(self.EditControl)
            elif c_control == self.EditControl:
                self.setFocusId(10003)

        # Accion 4: Flecha abajo
        elif action == 4:
            # if c_id == 10004:
            if c_control == self.EditControl:
                self.setFocusId(10007)
            elif c_id == 10003:
                self.setFocus(self.EditControl)
