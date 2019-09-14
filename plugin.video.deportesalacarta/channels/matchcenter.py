# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
#------------------------------------------------------------


import xbmcgui
import xbmc
from lib.matchcenter import agenda
from lib.matchcenter import livef1
from lib.matchcenter import livemotos
from lib.matchcenter import livescores
from lib.matchcenter import leaguetables
from lib.matchcenter import news
from lib.matchcenter import portadas
from lib.matchcenter import tweets
from lib.matchcenter import tweetsbuscar_user
from lib.matchcenter import tweet

from core import config
from core import filetools

main = None
    
TWITTER_MENU = {
    "buscar" : {"label" : "Buscar", "icon" : filetools.join(config.get_runtime_path(),"resources","images","matchcenter","twittersrch.png"), "order": 2},
    "hashtag" : {"label" : "Hashtags", "icon" : filetools.join(config.get_runtime_path(),"resources","images","matchcenter","hashtag.png"), "order": 1},
    "persona" : {"label" : "Persona", "icon" : filetools.join(config.get_runtime_path(),"resources","images","matchcenter","user.png"), "order": 0},
    "trending" : {"label" : "Trending Topic", "icon" : filetools.join(config.get_runtime_path(),"resources","images","matchcenter","trending.png"), "order": 3}
    }


MAIN_MENU = {
    "livescores" : {"label" : "Marcadores", "icon" : filetools.join(config.get_runtime_path(),"resources","images","matchcenter","marcador.png"), "order": 0},
    "tables" : {"label" : "Clasificaciones", "icon" : filetools.join(config.get_runtime_path(),"resources","images","matchcenter","tables.png"), "order": 2},
    "twitter" : {"label" : "Twitter", "icon" : filetools.join(config.get_runtime_path(),"resources","images","matchcenter","twitterlg.png"), "order": 1},
    "noticias" : {"label" : "Noticias", "icon" : filetools.join(config.get_runtime_path(),"resources","images","matchcenter","noticias.png"), "order": 3},
    "portadas" : {"label" : "Portadas", "icon" : filetools.join(config.get_runtime_path(),"resources","images","matchcenter","portada.png"), "order": 4},
    "agenda" : {"label" : "Agenda Deportiva", "icon" : filetools.join(config.get_runtime_path(),"resources","images","matchcenter","agenda.png"), "order": 5},
    "f1" : {"label" : "Fórmula 1", "icon" : filetools.join(config.get_runtime_path(),"resources","images","matchcenter","f1.png"), "order": 6},
    "motos" : {"label" : "Motociclismo", "icon" : filetools.join(config.get_runtime_path(),"resources","images","matchcenter","motos.png"), "order": 7}
    }

MOTOS_MENU = {
    "motogp" : {"label" : "MotoGP", "icon" : filetools.join(config.get_runtime_path(),"resources","images","matchcenter","motogp.png"), "order": 0},
    "moto2" : {"label" : "Moto2", "icon" : filetools.join(config.get_runtime_path(),"resources","images","matchcenter","moto2.png"), "order": 1},
    "moto3" : {"label" : "Moto3", "icon" : filetools.join(config.get_runtime_path(),"resources","images","matchcenter","moto3.png"), "order": 2}
    }


class Main(xbmcgui.WindowXMLDialog):
    
    def __init__( self, *args, **kwargs ):
        self.items = []
        self.open = kwargs.get("open")

    def onInit(self):
        self.setCoordinateResolution(2)
        # from lib.matchcenter import marcadores
        # self.comments, self.times = marcadores.get_data_f1()

        if self.open:
            for menuentry in MAIN_MENU.keys():
                item = xbmcgui.ListItem(MAIN_MENU[menuentry]["label"])
                item.setProperty("thumb",str(MAIN_MENU[menuentry]["icon"]))
                item.setProperty("identifier",str(menuentry))
                item.setProperty("order", str(MAIN_MENU[menuentry]["order"]))
                self.items.append(item)

            self.items.sort(key=lambda it:int(it.getProperty("order")))
            self.getControl(32500).addItems(self.items)
            self.setFocusId(32500)
            self.open = False

    def onClick(self,controlId):
        if controlId == 32500:
            identifier = self.getControl(32500).getSelectedItem().getProperty("identifier")
            if identifier == "livescores":
                self.close()
                livescores.start(self)
            elif identifier == "tables":
                self.close()
                leaguetables.start(self)
            elif identifier == "twitter":
                self.close()
                main_twitter = Main_twitter('script-matchcenter-MainMenu.xml',config.get_runtime_path(),open=True)
                main_twitter.doModal()
                del main_twitter
            elif identifier == "noticias":
                self.close()
                news.start(self)
            elif identifier == "portadas":
                self.close()
                portadas.start(self)
            elif identifier == "agenda":
                self.close()
                agenda.start(self)
            elif identifier == "f1":
                self.close()
                livef1.start(self)
            elif identifier == "motos":
                self.close()
                main_motos = Main_motos('script-matchcenter-MainMenu.xml',config.get_runtime_path(),open=True)
                main_motos.doModal()
                del main_motos


    def onAction(self,action):
        #exit
        global main
        if action.getId() == 92 or action.getId() == 10:
            main.close()
            del main
        if action.getId() == 117:
            config.open_settings()


def start(item):
    global main
    main = Main('script-matchcenter-MainMenu.xml',config.get_runtime_path(),open=True)
    main.doModal()


class Main_twitter(xbmcgui.WindowXMLDialog):
    
    def __init__( self, *args, **kwargs ):
        self.items = []
        self.open = kwargs.get("open")

    def onInit(self):
        self.setCoordinateResolution(2)
        self.getControl(30000).setLabel("Twitter")

        equipos = [["Alaves", "1108"], ["AthleticClub", "621"], ["Atleti", "13"], ["FCBarcelona_es", "131"],
                   ["RealBetis", "150"], ["rccelta_oficial", "940"], ["RCDeportivo", "897"], ["sdeibar", "1533"],
                   ["RCDEspanyol", "714"], ["GranadaCdeF", "16795"], ["UDLP_Oficial", "472"], ["CDLeganes", "1244"],
                   ["MalagaCF", "1084"], ["CAOsasuna", "331"], ["realmadrid", "418"], ["RealSociedad", "681"],
                   ["SevillaFC", "368"], ["realsporting", "2448"], ["valenciacf", "1049"], ["VillarrealCF", "1050"] 
                   ]
        
        if self.open:
            if int(config.get_setting("team_tweet")) != 0:
                team_twitter, team_ico = equipos[int(config.get_setting("team_tweet"))-1]
                team_ico = "http://tmssl.akamaized.net//images/wappen/big/%s.png" % team_ico
                TWITTER_MENU[team_twitter] = {"label": "@"+team_twitter, "icon": team_ico, "order": 4}
            for menuentry in TWITTER_MENU.keys():
                item = xbmcgui.ListItem(TWITTER_MENU[menuentry]["label"])
                item.setProperty("thumb",str(TWITTER_MENU[menuentry]["icon"]))
                item.setProperty("identifier",str(menuentry))
                item.setProperty("order",str(TWITTER_MENU[menuentry]["order"]))
                self.items.append(item)

            self.items.sort(key=lambda it:int(it.getProperty("order")))
            self.getControl(32500).addItems(self.items)
            self.setFocusId(32500)
            self.open = False

    def onClick(self,controlId):
        if controlId == 32500:
            identifier = self.getControl(32500).getSelectedItem().getProperty("identifier")
            if identifier == "buscar":
                self.close()
                dialog = xbmcgui.Dialog()
                if dialog.yesno('[COLOR skyblue][B]Busqueda en Twitter[/B][/COLOR]', '[COLOR cadetblue]¿Qué tipo de busqueda quieres realizar?[/COLOR]','', "",'[COLOR floralwhite][B]En tweets[/B][/COLOR]','[COLOR cyan][B]Por Users[/B][/COLOR]'):
                    tweetsbuscar_user.start()
                else:
                    tweets.start("busqueda")
                self.doModal()
            elif identifier == "persona" or identifier == "hashtag":
                self.close()
                tweets.start(identifier)
                self.doModal()
            elif identifier == "trending":
                self.close()
                lista_tt = tweet.get_trends()
                elegido = xbmcgui.Dialog().select("Ahora es TT en España", lista_tt)
                if elegido > -1:
                    tweets.start("hashtag", lista_tt[elegido].encode("utf-8","ignore"))
                self.doModal()
            else:
                self.close()
                tweets.start(identifier, identifier, False, True)
                self.doModal()


    def onAction(self,action):
        global main
        if action.getId() == 92 or action.getId() == 10:
            self.close()
            main.doModal()

        if action.getId() == 117:
            twitter_history = tweet.get_twitter_history()
            if twitter_history:
                twitter_history = list(reversed(twitter_history))
                twitter_title = []
                for t in twitter_history:
                    twitter_title.append(t.split("|")[0])
                choice = xbmcgui.Dialog().select("Escoge una búsqueda del historial", twitter_title)
                if choice > -1:
                    self.close()
                    hash, action = twitter_history[choice].split("|")
                    if action == "hashtag":
                        tweets.start("hashtag", hash)
                    elif action == "busqueda":
                        tweets.start("busqueda", hash)
                    else:
                        tweets.start("persona", hash)
                    self.doModal()
            else:
                xbmcgui.Dialog().ok("Match Center","No hay historial de Twitter disponible")

class Main_motos(xbmcgui.WindowXMLDialog):
    
    def __init__( self, *args, **kwargs ):
        self.items = []
        self.open = kwargs.get("open")

    def onInit(self):
        self.setCoordinateResolution(2)

        if self.open:
            for menuentry in MOTOS_MENU.keys():
                item = xbmcgui.ListItem(MOTOS_MENU[menuentry]["label"])
                item.setProperty("thumb",str(MOTOS_MENU[menuentry]["icon"]))
                item.setProperty("identifier",str(menuentry))
                item.setProperty("order", str(MOTOS_MENU[menuentry]["order"]))
                self.items.append(item)

            self.items.sort(key=lambda it:int(it.getProperty("order")))
            self.getControl(32500).addItems(self.items)
            self.setFocusId(32500)
            self.open = False

    def onClick(self,controlId):
        if controlId == 32500:
            identifier = self.getControl(32500).getSelectedItem().getProperty("identifier")
            self.close()
            livemotos.start(self, mode=identifier)


    def onAction(self,action):
        global main
        if action.getId() == 92 or action.getId() == 10:
            self.close()
            main.doModal()