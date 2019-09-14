# -*- coding: utf-8 -*-
import xbmcgui
import xbmc
from core.libs import *


class Recaptcha(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        self.result = {}
        self.referer = None
        self.key = None
        self.headers = {}
        self.url = None
        self.token = None
        self.image = None
        self.message = None

    def start(self, key, referer):
        logger.trace()
        self.referer = referer
        self.key = key
        self.headers = {'Referer': self.referer}

        api_js = httptools.downloadpage("http://www.google.com/recaptcha/api.js?hl=es").data
        version = scrapertools.find_single_match(api_js, 'po.src\s*=\s*\'(.*?)\';').split("/")[5]
        self.url = "http://www.google.com/recaptcha/api/fallback?k=%s&hl=es&v=%s&t=2&ff=true" % (self.key, version)

        data = httptools.downloadpage(self.url, headers=self.headers).data
        if 'Habilita JavaScript' in data or 'Se ha producido un error' in data:
            return False
        self.doModal()

        # Reload
        if self.result == {}:
            skin = 'Estuary' if xbmc.getSkinDir() == 'skin.estuary' else 'Default'
            self.result = Recaptcha("Recaptcha.xml", sysinfo.runtime_path, skin).start(self.key, self.referer)

        return self.result

    def update_window(self):
        logger.trace()
        data = httptools.downloadpage(self.url, headers=self.headers).data
        self.message = scrapertools.find_single_match(data,
                                                      '<div class="rc-imageselect-desc[^"]*">(.*?)(?:</label>|</div>)')
        self.token = scrapertools.find_single_match(data, 'name="c" value="([^"]+)"')
        self.image = "http://www.google.com/recaptcha/api2/payload?k=%s&c=%s" % (self.key, self.token)
        self.result = {}
        self.getControl(10007).setImage(self.image)
        self.getControl(10003).setText(self.message.replace("<strong>", "[B]").replace("</strong>", "[/B]"))
        self.setFocusId(10005)

    def onInit(self):
        logger.trace()
        if int(xbmcgui.__version__.replace('.', '')) <= 2250:
            self.setCoordinateResolution(5)
        self.update_window()

    def onClick(self, control):
        logger.trace()
        if control == 10005:
            self.result = None
            self.close()

        elif control == 10006:
            self.result = {}
            self.close()

        elif control == 10004:
            self.result = [int(k) for k in range(9) if self.result.get(k, False) is True]
            post = "c=%s" % self.token

            for r in self.result:
                post += "&response=%s" % r

            data = httptools.downloadpage(self.url, post, headers=self.headers).data
            self.result = scrapertools.find_single_match(data, '<div class="fbc-verification-token">.*?>([^<]+)<')
            if self.result:
                platformtools.dialog_notification("Captcha Correcto", "La verificación ha concluido")
                self.close()
            else:
                self.result = {}
                self.close()
        else:
            self.result[control - 10008] = not self.result.get(control - 10008, False)

    def onAction(self, action):
        logger.trace()
        if action.getId() in (10, 92):
            self.result = None
        xbmcgui.WindowXMLDialog.onAction(self, action)