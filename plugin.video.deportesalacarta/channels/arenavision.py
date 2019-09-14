# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para arenavision
#------------------------------------------------------------
import re
import os

from core import scrapertools
from core import logger
from core import config
from platformcode import platformtools
from core.item import Item
from core import servertools
import xbmc
import xbmcgui
from core import httptools

ventana = None
select = None
__channel__ = "arenavision"

host = "https://arenavision.in"
song = os.path.join(config.get_runtime_path(), 'music', 'best-day-of-my-life.mp3')
cookies = config.get_setting("cookies", "arenavision")
if cookies:
    cookies = {'Cookie': cookies}


def agendaglobal(item):
    itemlist = []
    try:
        item.url = "https://arenavision.in/-schedule"
        item.thumbnail = "http://s6.postimg.org/as7g0t9qp/STREAMSPORTAGENDA.png"
        item.fanart = "http://s6.postimg.org/5utvfp7rl/streamsportonairfan.jpg"
        itemlist = mainlist(item)
        if itemlist[-1].action == "mainlist":
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []
    
    return itemlist


def mainlist(item):
    logger.info("deportesalacarta.arenavision schedule")

    itemlist = []
    check=xbmc.getInfoLabel('ListItem.Title')
   
    if item.channel != __channel__:
        item.channel = __channel__
        config.set_setting("cookies", "", "arenavision")
    else:
        xbmc.executebuiltin('xbmc.PlayMedia('+song+')')
    
    # Descarga la página
    try:
        data = get_data(host, cookies)
        if "document.cookie='" in data:
            cookie = scrapertools.find_single_match(data, "document.cookie='([^']+)'")
            config.set_setting("cookies", cookie, "arenavision")
            global cookies
            cookies = {'Cookie': cookie}
            data = get_data(host, cookies)
    except:
        data = ""

    if not data or not re.search("(?i)>EVENTS GUIDE", data):
        global host
        host = host.replace(".in", ".ru")
        data = get_data(host, cookies)
        if "document.cookie='" in data:
            cookie = scrapertools.find_single_match(data, "document.cookie='([^']+)'")
            config.set_setting("cookies", cookie, "arenavision")
            global cookies
            cookies = {'Cookie': cookie}
            data = get_data(host, cookies)

    item.url = host + scrapertools.find_single_match(data, '(?i)href="([^"]+)"[^>]*>EVENTS GUIDE')
    data = get_data(item.url, cookies)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|<br />","",data)
    patron_bloque = '</style><p></p>(.*?)Brusells'
    matchesenlaces = re.compile(patron_bloque,re.DOTALL).findall(data)
    
    for pepe in matchesenlaces:
        patron = 'auto-style3.*?>(\d+/\d+/\d+).*?auto-style3.*?>(.*?)(?:CET|CEST).*?auto-style3.*?>(.*?)</td>.*?auto-style3.*?>(.*?)</td>.*?auto-style3.*?>(.*?)</td>.*?auto-style3.*?>(.*?)</td>'
        matches = re.compile(patron,re.DOTALL).findall(pepe)

        for dia , hora, deportes,competicion, partido, av_leng in matches:
            hora = hora.strip()
            av_leng = re.sub(r"<br />\n\t\t","--",av_leng)
            date=scrapertools.get_match(dia,'(\d+/\d+)/')
            time= hora
            evento = partido
            deporte = deportes
            if  "SOCCER" in deporte:
                evento = evento.replace("-", " vs ")
                deporte = "futbol"
            dia = "[COLOR darkkhaki][B]"+date+"[/B][/COLOR]"
            hora = "[COLOR chartreuse][B]"+hora+"[/B][/COLOR]"
            deportes = "[COLOR burlywood][B]"+deportes+"[/B][/COLOR]"
            partido = "[COLOR orangered][B]"+partido+"[/B][/COLOR]"
            competicion = "[COLOR darkgoldenrod][B]"+competicion+"[/B][/COLOR]"
            espacio = "[COLOR floralwhite]--[/COLOR]"
            title = dia+espacio+hora+espacio+"[COLOR beige][B][[/B][/COLOR]"+ deportes +"[COLOR beige][B]][/B][/COLOR]"+espacio+partido +espacio+ "[COLOR gainsboro][B]([/B][/COLOR]"+competicion+"[COLOR gainsboro][B])[/B][/COLOR]"
            #title = re.sub(r"<br />","",title)
            itemlist.append( Item(channel=__channel__, title=title,action="enlaces",url = "",extra= av_leng , thumbnail= "http://s6.postimg.org/csumvetu9/arenavisionthumb.png",fanart="http://s6.postimg.org/e965djwr5/arenavisionfan.jpg",fulltitle= partido,date=date, time=time, evento=evento, deporte=deporte, context="info_partido", folder=False) )
    return itemlist

def enlaces(item):
    logger.info("deportesalacarta.arenavision scraper")
    itemlist = []
    datos = item.extra
    global ventana
    ventana = TextBox1(datos=datos, item= item)
    ventana.doModal()

ACTION_SELECT_ITEM = 7
ACTION_GESTURE_SWIPE_LEFT = 511
ACTION_MOUSE_LEFT_CLICK = 100
ACTION_MOUSE_RIGHT_CLICK = 101
ACTION_PREVIOUS_MENU = 10
OPTIONS_OK = 5
OPTION_PANEL = 6
class TextBox1( xbmcgui.WindowDialog ):
        """ Create a skinned textbox window """
        def __init__( self, *args, **kwargs):
            self.datos = kwargs.get('datos')
            self.item =  kwargs.get('item')
            item = self.item
            self.background = xbmcgui.ControlImage( -40, -40, 1500, 830, 'https://s6.postimg.org/dx5tgv5e9/arenavfondo.png')
            self.addControl(self.background)
            xbmc.executebuiltin('Action(Select)')
        
        
        def onAction(self, action):
            if action == ACTION_PREVIOUS_MENU or action.getId() == ACTION_GESTURE_SWIPE_LEFT or action == 110 or action == 92:
                global ventana
                self.close()
                del ventana
                
        
            elif action == ACTION_SELECT_ITEM  :
                if xbmc.Player().isPlayingVideo():
                   xbmc.log("pepezno")
                   self.close()
                
                else:
                   
                   check_skin =xbmc.getSkinDir()
                   
                   datos = self.datos
                   item = self.item
                   fulltitle = item.fulltitle
                   global select
                   select=Select('DialogSelect.xml',datos,fulltitle)
            
                   select.doModal()
                   if not "confluence" in check_skin:
                      if xbmc.Player().isPlayingVideo():
                         xbmc.sleep(550)
                         self.close()
                         xbmc.sleep(550)
                      else:
                         self.close()
                   if "confluence" in check_skin:
                       xbmc.sleep(550)
                       self.close()
                       xbmc.sleep(550)
                    

ACTION_GESTURE_SWIPE_LEFT = 511
ACTION_SELECT_ITEM = 7
ACTION_MOVE_RIGHT = 2
ACTION_MOVE_LEFT = 1
ACTION_PREVIOUS_MENU = 10
ACTION_MOUSE_LEFT_CLICK = 100
ACTION_MOUSE_RIGHT_CLICK = 101
OPTIONS_OK = 5
OPTION_PANEL = 6
class Select(xbmcgui.WindowXMLDialog):
       def __init__( self, item,datos,fulltitle ):
           
           self.datos = datos
           self.fulltitle = fulltitle

       def onInit(self):
           try:
              self.control_list = self.getControl(6)
              self.getControl(5).setNavigation(self.control_list, self.control_list, self.control_list, self.control_list)
              self.getControl(3).setEnabled(0)
              self.getControl(3).setVisible(0)
           except:
                pass
           self.getControl(1).setLabel("[COLOR orange][B]Selecciona Canal...[/B][/COLOR]")
           self.getControl(5).setLabel("[COLOR tomato][B]Cerrar[/B][/COLOR]")
           self.control_list.reset()
           items = []
           host_replace = False
           try:
              data = get_data(host, cookies)
           except:
              data = ""
           if not data:
              global host
              host = host.replace(".in", ".ru")
              data = get_data(host, cookies)

           self.datos = re.sub(r" ","-",self.datos)
           patron = '(.*?)\[(.*?)\]'
           matches = re.compile(patron,re.DOTALL).findall(self.datos)
           
           if len(matches)==0 :
               av= "[COLOR crimson][B]Sin canal[/B][/COLOR]"
               thumbnail="http://s6.postimg.org/vq2l1wz2p/noacestreamsopcast.png"
               item = xbmcgui.ListItem(str(av))
               item.setArt({"thumb":str(thumbnail)})
               items.append(item)
           for canales, idioma in matches:
                matchescanales = canales[:-1].split("-")
                for av in matchescanales:
                    url = scrapertools.find_single_match(data, '(?i)href="([^"]+)"[^>]*>ArenaVision\s*%s\s*<' % av)
                    if not "S" in av:
                       thumbnail ="https://s6.postimg.org/hq3soxkep/acestream.png"
                       av = re.sub(r'S|-','',av)
                       title = "[COLOR crimson]AV[/COLOR]"+" "+"[COLOR floralwhite]"+av+"[/COLOR]"+ " "+"[COLOR palegreen]Idioma[/COLOR]"+" "+"[COLOR palegreen]"+idioma+"[/COLOR]"
                    else:
                       av = re.sub(r'S|-','',av)
                       thumbnail = "https://s6.postimg.org/734xme5xt/sopcast.png"
                       title = "[COLOR crimson]AV[/COLOR]"+" "+"[COLOR floralwhite]"+av+"[/COLOR]"+ " "+"[COLOR deepskyblue]Idioma[/COLOR]"+" "+"[COLOR deepskyblue]"+idioma+"[/COLOR]"
                    #av = av + "("+idioma+")"
                    self.url = url
                    item = xbmcgui.ListItem(str(title))
                    try:
                       item.setArt({"thumb":str(thumbnail)})
                    except:
                       item.setThumbnailImage(thumbnail)
                    item.setProperty("url",url)
                    items.append(item)
           self.getControl(6).addItems(items)
           self.setFocusId(6)

       def onAction(self,action):
           if action.getId() == ACTION_PREVIOUS_MENU or action.getId() == ACTION_GESTURE_SWIPE_LEFT or action == 110 or action == 92:
                global select, ventana
                borrar = [select, ventana]
                for window in borrar:
                    window.close()
                    del window
                xbmc.sleep(300)
                xbmc.executebuiltin('Action(PreviousMenu)')

                
       def onClick(self,controlId):
           if controlId == OPTION_PANEL:
               xbmc.executebuiltin('xbmc.PlayMedia(Stop)')
               self.list = self.getControl(6)
               selecitem=self.list.getSelectedItem()
               url = selecitem.getProperty("url")
               data = get_data(url, cookies)
               url = servertools.findvideosbyserver(data, "p2p")
               if len(url) > 1:
                   enlaces = []
                   for u in url:
                       enlaces.append(u[1])
                   xbmc.log(str(enlaces))
                   selection = xbmcgui.Dialog().select("Selecciona un enlace", enlaces)
                   if selection > 0:
                       url = url[selection][1]
               elif url:
                   url = url[0][1]

               #Creamos el item para platformtools
               item =Item()
               item.fulltitle = self.fulltitle
               item.url = url + "|" + item.fulltitle
               item.server = "p2p"

               config.set_setting("arenavision_play", False, "arenavision")
               from threading import Thread
               t = Thread(target=platformtools.play_video, args=[item])
               t.start()
               close = False
               while True:
                xbmc.sleep(500)
                try:
                    if not t.is_alive() and not config.get_setting("arenavision_play", "arenavision"):
                        break
                    elif not t.is_alive() and config.get_setting("arenavision_play", "arenavision"):
                        xbmc.executebuiltin('Action(PreviousMenu)')
                        break
                except:
                    if not t.isAlive() and not config.get_setting("arenavision_play", "arenavision"):
                        break
                    elif not t.isAlive() and config.get_setting("arenavision_play", "arenavision"):
                        xbmc.executebuiltin('Action(PreviousMenu)')
                        break
       
       
           elif controlId == OPTIONS_OK or controlId == 99:
                global select, ventana
                borrar = [select, ventana]
                for window in borrar:
                    window.close()
                    del window
                xbmc.sleep(300)
                xbmc.executebuiltin('Action(PreviousMenu)')

''' patron = '(AV\d+)'
    matches = re.compile(patron,re.DOTALL).findall(item.extra)
    for (i , f) in enumerate(matches):
        if "AV" in f:
            a = re.compile('AV(\d+)',re.DOTALL).findall(f)
            for (b,c) in enumerate(a):
                   
                   
                if c== "9" or c =="8" or c =="7" or c =="6" or c =="5" or c =="4" or c =="3" :
                    c= " "+c
                   
                if c <= "20" :
                    matches[i] = f.replace(f,"[COLOR crimson][B]"+matches[i]+"[/B][/COLOR]")+ "[COLOR palegreen][B]  Acestream[/B][/COLOR]"
                else:
                    matches[i] = f.replace(f,"[COLOR crimson][B]"+matches[i]+"[/B][/COLOR]")+ "[COLOR deepskyblue][B]  Sopcast[/B][/COLOR]"
            
            
        get_url= [(i,x) for i, x in enumerate(matches)]
        get_url = repr(get_url)
            #get_url= re.sub(r"\[COLOR.*?\]\[.*?]|\[.*?\]\[/COLOR\].*?\[.*?\]\[/COLOR\]","",get_url)
        print "marco"
        print get_url
        fulltitle =item.fulltitle
        print "pacopepe"
        print fulltitle
    index = xbmcgui.Dialog().select("[COLOR orange][B]Selecciona Canal...[/B][/COLOR]", matches)
        
    if index != -1:
        index =str(index)
        print "kkkk"
        print get_url
        if index == 0:
            catch_url=scrapertools.get_match(get_url,'\('+index+',.*?\'\[COLOR crimson\]\[B\](.*?)\[')
        catch_url=scrapertools.get_match(get_url,''+index+',.*?\'\[COLOR crimson\]\[B\](.*?)\[')
        url =urlparse.urljoin(host,catch_url)
            
        import xbmc
        xbmc.executebuiltin('xbmc.PlayMedia(Stop)')
        ### Esto sustituye a la función go
        data = scrapertools.cache_page(url)
        patron = '\*INFO.*?Click.*?<a href="([^"]+)"'
        url = scrapertools.find_single_match(data, patron)
        item.url = url +"|" + fulltitle
        print "tu vieja"
        print item.url
        item.server = "p2p"        
        platformtools.play_video(item)
			
    else:
        import xbmc
        xbmc.executebuiltin( "XBMC.Container.Update" )
        return


def press():
    import xbmc
    xbmc.executebuiltin('Action(Select)')'''

def get_data(url_orig, cookie):
    try:
        response = httptools.downloadpage(url_orig, headers=cookie)
        if not response.data or "urlopen error [Errno 1]" in str(response.code):
            raise Exception
        return response.data
    except:
        import urllib
        post = {"address":url_orig}
        if cookie:
            post["options"] = [{"man":"--cookie","attribute": cookie.get("Cookie", "")}]
        from core import jsontools
        data = httptools.downloadpage("http://onlinecurl.com/").data
        token = scrapertools.find_single_match(data, '<meta name="csrf-token" content="([^"]+)"')
        
        headers = {'X-Requested-With': 'XMLHttpRequest', 'X-CSRF-Token': token, 'Referer': 'http://onlinecurl.com/'}
        post = "curl_request=" + urllib.quote(jsontools.dump_json(post)) + "&email="
        response = httptools.downloadpage("http://onlinecurl.com/onlinecurl", post=post, headers=headers).data
        data = jsontools.load_json(response).get("body", "")

        return data
