# -*- coding: utf-8 -*-
from core.libs import *
import xbmcgui

class Dialog_img_yesno(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.return_value = None
        self.heading = ''
        self.img = ''
        self.msg = ''
        self.yes_label = ''
        self.no_label = ''
        self.no_show = False


    def start(self, img, heading='', msg='', no_show = True, yes_label ='Aceptar', no_label='Cancelar'):
        logger.trace()

        self.img = img
        self.heading = heading
        self.msg = msg
        self.yes_label = yes_label
        self.no_label = no_label
        self.no_show = no_show

        self.doModal()
        return self.return_value


    def onInit(self):
        logger.trace()
        if int(xbmcgui.__version__.replace('.', '')) <= 2250:
            self.setCoordinateResolution(5)

        self.getControl(10002).setLabel(self.heading)
        self.getControl(10004).setImage(self.img)
        self.getControl(10005).setLabel(self.msg)
        self.getControl(10006).setLabel(self.yes_label)
        self.getControl(10007).setLabel(self.no_label)
        self.getControl(10007).setVisible(self.no_show)

        self.setFocus(self.getControl(10006))


    def onClick(self, control):
        logger.trace()

        if control == 10006:
            # Aceptar
            self.return_value = True
            self.close()

        elif control in [10003, 10007]:
            # Cancelar
            self.return_value = False
            self.close()