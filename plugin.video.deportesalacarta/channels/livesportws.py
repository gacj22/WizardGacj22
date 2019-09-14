# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para livesporws
#------------------------------------------------------------
import urlparse, re
import os

from core import httptools
from core import scrapertools
from core import logger
from core import config
import xbmc

from core.item import Item
from core import servertools
from core.scrapertools import decodeHtmlentities as dhe
import datetime

__channel__ = "livesportws"
song = os.path.join(config.get_runtime_path(), "music", 'lookingforu2.mp3')
host ="http://livesport.ws"

def agendaglobal(item):
    itemlist = []
    try:
        itemlist = mainlist(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []
    
    return itemlist


def mainlist(item):
    logger.info("deportesalacarta.livesportsws lista")
    itemlist = []
    import xbmc
    check=xbmc.getInfoLabel('ListItem.Title')
    
    if item.channel != __channel__:
        item.channel = __channel__
    else:
       if not xbmc.Player().isPlaying():
          xbmc.executebuiltin('xbmc.PlayMedia('+song+')')
    
    
    
    """
        Lo que ocurre con
        url = http://translate.googleusercontent.com/translate_c?depth=1&nv=1&rurl=translate.google.com&sl=ru&tl=es&u=http://lfootball.ws/&usg=ALkJrhgzJfI1TDn3BxGgPbjgAHHS7J0i9g
        Redirecciones:
        1. http://translate.google.com/translate?depth=1&nv=1&rurl=translate.google.com&sl=ru&tl=es&u=http://lfootball.ws/
        2. http://translate.googleusercontent.com/translate_p?nv=1&rurl=translate.google.com&sl=ru&tl=es&u=http://lfootball.ws/&depth=2&usg=ALkJrhgAAAAAVupk4tLINTbmU7JrcQdl0G4V3LtnRM1n
        3. http://translate.googleusercontent.com/translate_c?depth=2&nv=1&rurl=translate.google.com&sl=ru&tl=es&u=http://lfootball.ws/&usg=ALkJrhhhRDwHSDRDN4t27cX5CYZLFFQtmA
        Lo que significa que necesitamos una key nueva cada vez en el argumento "usg" y para llegar a la url 3 debemos hacer la petición 1 y 2 con 'follow_redirects=False' o con la convinación de 'follow_redirects=False' y 'header_to_get="location"'
        """
    
    #### Opción 1: 'follow_redirects=False'
    ## Petición 1
    url = "http://translate.google.com/translate?depth=1&nv=1&rurl=translate.google.com&sl=ru&tl=es&u=http://livesport.ws/football"
    data = dhe(httptools.downloadpage(url, follow_redirects=False).data)#.decode('cp1251').encode('utf8')
    ## Petición 2
    url = scrapertools.get_match(data, ' src="([^"]+)" name=c ')
    data = dhe(httptools.downloadpage(url, follow_redirects=False).data)#.decode('cp1251').encode('utf8')
    ## Petición 3
    url = scrapertools.get_match(data, 'URL=([^"]+)"')
    data = dhe(httptools.downloadpage(url).data)#.decode('cp1251').encode('utf8')
    """
        #### Opción 2: 'follow_redirects=False' y 'header_to_get="location"'
        ## Petición 1
        url = "http://translate.google.com/translate?depth=1&nv=1&rurl=translate.google.com&sl=ru&tl=es&u=http://lfootball.ws/"
        data = dhe( scrapertools.downloadpage(url,follow_redirects=False) )#.decode('cp1251').encode('utf8')
        ## Petición 2
        url = scrapertools.get_match(data, ' src="([^"]+)" name=c ')
        url = scrapertools.get_header_from_response(url, header_to_get="location")
        ## Petición 3
        data = dhe( scrapertools.cachePage(url ) )#.decode('cp1251').encode('utf8')
        """
    
    
    
    patrondata = '</h1></div>(.*?)</h2>'
    matchesdata = re.compile(patrondata,re.DOTALL).findall(data)
    for bloque_data in matchesdata:
        
        for bloque_data in matchesdata:
            patrondaygame = '<span class=text>.*?<span class=text>(.*?)</span></a>(.*?)</span> --></li></ul></div>'
            matchesdaygame = re.compile(patrondaygame,re.DOTALL).findall(bloque_data)

            for day , bloque_games in matchesdaygame:
                day = re.sub(r"</span>|<i class=ico><span>de</span></i>|<span class=text>|de","",day)
                day = day.replace("actuales","Hoy")
                day = scrapertools.htmlclean(day)
                dia = scrapertools.get_match(day, '(\d+)')
                mes = re.sub(r"(?i)de |hoy |ayer |mañana |el |día ", "", day)
                mes_ = scrapertools.find_single_match(mes, '\d+\s*([A-z]+)')
                if not mes_:
                    mes_ = scrapertools.find_single_match(mes, '([A-z]+)\s*\d+,')
                mes = mes_.title()
                mes = month_convert(mes)
                mes = str(mes).zfill(2)
                
                if "hoy" in day or "Hoy" in day:
                    day = day.replace(day,"[COLOR yellow][B]"+day+"[/B][/COLOR]")
                elif "Ayer" in day or "ayer" in day:
                      day = day.replace(day,"[COLOR darkgoldenrod][B]"+day+"[/B][/COLOR]")
                else:
                     day = day.replace(day,"[COLOR greenyellow][B]"+day+"[/B][/COLOR]")
                itemlist.append( Item(channel=__channel__, title=day,action="mainlist",url="",fanart="http://www.easywallprints.com/upload/designs/background-with-soccer-balls-zoom-1.jpg",thumbnail="http://s6.postimg.org/3yl2y4adt/livesportagenda.png",folder=False) )
                
                patron = 'es&u=(.*?)&usg.*?id=event-(.*?)>(.*?)</i>.*?<span class=competition>.*?<span class=competition>(.*?)</span></a>.*?<i class="separator">.*?</span>(.*?)</span>.*?src=(.*?)>.*?src=(.*?)>.*?text-align: left">.*?</span>(.*?)</span>.*?<i class="live-broadcasting-status-(\d)"'#'<a class="link" href="([^"]+)" title="(.*?)".*?<span class="liga"><span>(.*?)</span></span>.*?<span class="date"><span>(.*?)</span></span>'
                matches = re.compile(patron,re.DOTALL).findall(bloque_games)
                for url_info,id_event, hora,competition,team1,thumbnail,fanart,team2 , status in matches:
                    team1 = re.sub(r"-"," ",team1)
                    team2=  re.sub(r"-"," ",team2)
                    competition = re.sub(r"\.","",competition)
                    
                    
                    if status == "4":
                        continue
                    
                    if "00:" in hora:
                        hora = hora.replace("00:","24:")
                    
                    if not "LIVE" in hora:
                       time= re.compile('(\d+):(\d+)',re.DOTALL).findall(hora)
                       for horas, minutos in time:
                           wrong_time =int(horas)
                           value = 1
                           correct_time = wrong_time - value
                           correct_time = str(correct_time)
                           hora = correct_time +":"+ minutos
                           
                           
                    
                
                    if "OFFLINE" in hora:
                        extra = hora
                        title = team1+"-"+team2+"____"
                        title = title.title()
                        fulltitle =title.replace(title,"[COLOR burlywood][B]"+title+"[/B][/COLOR]")
                        title= title.replace(title,"[COLOR burlywood]"+title+"[/COLOR]")
                        action = "mainlist"
                        folder = False
                        evento = ""
                        time = ""
                        fecha = ""
                    else:
                        if "hoy" in day or "Hoy" in day:
                            title = team1+" - "+team2
                            title = title.title()
                            fulltitle =title.replace(title,"[COLOR deepskyblue][B]"+title+"[/B][/COLOR]")
                            if "LIVE" in hora:
                               import time
                               
                               time = "live"
                               fecha = dia+"/"+str(mes)
                               fecha = fecha.strip()
                               evento = team1+" vs "+team2
                               extra= hora
                               hora = u'\u006C\u0456\u0475\u04BC!!'.encode('utf-8')
                               hora = hora.replace(hora,"[COLOR crimson][B]"+hora+"[/B][/COLOR]")
                               
                            else:
                                evento = team1+" vs "+team2
                                time = hora.strip()
                                fecha = dia+"/"+str(mes)
                                fecha = fecha.strip()
                                extra = hora
                                hora = hora.replace(hora,"[COLOR aquamarine][B]"+hora+"[/B][/COLOR]")
                          
                            title = hora+ "  " + title.replace(title,"[COLOR deepskyblue]"+title+"[/COLOR]")+ "[COLOR floralwhite]"+" "+"("+competition+")"+"[/COLOR]"
                            action = "enlaces"
                            folder = True
                        else:
                            title = team1+" - "+team2
                            evento = team1+" vs "+team2
                            time = hora
                            fecha = dia+"/"+mes
                            title = title.title()
                            fulltitle =title.replace(title,"[COLOR mediumaquamarine][B]"+title+"[/B][/COLOR]")
                            title = "[COLOR aquamarine][B]"+hora+"[/B][/COLOR]"+ "  " + title.replace(title,"[COLOR mediumaquamarine]"+title+"[/COLOR]")+ "[COLOR paleturquoise]"+" "+"("+competition+")"+"[/COLOR]"
                            action = "enlaces"
                            folder = True
                            extra = hora
                            
                    post_id = scrapertools.get_match(url_info,'http.*?livesport.ws\/(.*?)-')
                    url = "http://livesport.ws/engine/modules/sports/sport_refresh.php?from=event&event_id="+id_event+"&tab_id=0&post_id="+post_id
                    
                    itemlist.append( Item(channel=__channel__, title="     "+title,action=action,url=url,thumbnail =urlparse.urljoin(host,thumbnail),fanart =urlparse.urljoin(host,fanart),fulltitle = fulltitle,extra =extra,date=fecha, time=time, evento=evento, context="info_partido",deporte="futbol",folder=folder) )

    return itemlist

def enlaces(item):
    logger.info("deportesalacarta.livesportws enlaces")
    itemlist = []

    data = httptools.downloadpage(item.url).data
    #data= re.sub(r"\\","",data)
    
    
    patronbloque = 'print:(.*?)-.*?<img src=.*?"([^"]+)"(.*?)<\\\/tbody'
    matchesbloque = re.compile(patronbloque,re.DOTALL).findall(data)
    
    if len(matchesbloque)==0:
       
       if item.extra == "LIVE":
          itemlist.append( Item(channel=__channel__, title="[COLOR firebrick][B]No hay enlaces Acestream/Sopcast[/B][/COLOR]",action="mainlist",url="",thumbnail="http://s6.postimg.org/vq2l1wz2p/noacestreamsopcast.png",fanart="http://s6.postimg.org/806rhis29/livesportnolinks.jpg",folder=False) )
       else:
          title = "Aun no hay enlaces. Pruebe mas tarde".title()
          itemlist.append( Item(channel=__channel__, title="[COLOR lightseagreen][B]"+title+"[/B][/COLOR]",action="mainlist",url="",thumbnail="http://s6.postimg.org/3n87z3jbl/livesportnolinkyetthumb.png",fanart ="http://s6.postimg.org/l1sg7dggh/livesportnolinskyet.jpg",folder=False) )
    for tipo ,image, bloque_tipo in matchesbloque:
        tipo = tipo.title()
        if tipo =="Sopcast":
           tipo = tipo.replace(tipo,"[COLOR skyblue][B]"+tipo+"[/B][/COLOR]")
           thumbnail = "http://s6.postimg.org/734xme5xt/sopcast.png"
        else:
           thumbnail = "http://s6.postimg.org/hq3soxkep/acestream.png"
           tipo = tipo.replace(tipo,"[COLOR palegreen][B]"+tipo+"[/B][/COLOR]")
        itemlist.append( Item(channel=__channel__, title=tipo,action="mainlist",url="",thumbnail=thumbnail,fanart="http://s6.postimg.org/f9nqmhh8v/livesportslinkmatch.jpg",folder=False) )
        patron = '<img src=.*?"([^"]+)".*?<td class=.*?"speed.*?">(.*?)<.*?td>.*?<td class=.*?"channel.*?">(.*?)<.*?td>.*?<td class.*?"format.*?">(.*?)<.*?td>.*?<a href=.*?"(.*?)"'
        matches= re.compile(patron,re.DOTALL).findall(bloque_tipo)

        for idioma,bibrate,channel,calidad,link in matches:
            idioma = re.sub(r"\\","",idioma)
            
            channel = u''+channel+''
            channel = channel.decode("unicode_escape").encode("utf-8")
            
            if  "1080" in calidad:
               calidad =calidad.replace(calidad,"[COLOR crimson][B]"+calidad+"[/B][/COLOR]")
            elif "720" in calidad:
               calidad =calidad =calidad.replace(calidad,"[COLOR goldenrod][B]"+calidad+"[/B][/COLOR]")
            else:
               calidad =calidad =calidad.replace(calidad,"[COLOR chocolate][B]"+calidad+"[/B][/COLOR]")
            title = "[COLOR cadetblue][B]"+channel+"[/B][/COLOR]" +"  "+"("+calidad+"/"+"[COLOR mediumseagreen][B]"+bibrate+"[/B][/COLOR]"+")"
            link = re.sub (r"\\","",link)

            itemlist.append( Item(channel=__channel__, title=title,action="play",url=link,thumbnail =urlparse.urljoin(host,idioma),fanart ="http://s6.postimg.org/r5em50w3z/livesportslinksyes.jpg",fulltitle = item.fulltitle,folder=True) )


    return itemlist

def play(item):
    logger.info("deportesalacarta.lfootballws play")
    itemlist = []

    xbmc.executebuiltin('xbmc.PlayMedia(Stop)')
    fulltitle = item.fulltitle
    # Se incluye el título en la url para pasarlo al conector
    url= item.url + "|" + fulltitle
    
    itemlist.append(Item(channel=__channel__, title=item.title, server="p2p", url=url, action="play", folder=False))
    
    return itemlist




def month_convert(mes):
    return{ 'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril':4, 'Mayo' : 5, 'Junio' : 6, 'Julio' : 7, 'Agosto' : 8, 'Septiembre' : 9, 'Octubre' : 10, 'Noviembre' : 11, 'Diciembre' : 12 }[mes]
