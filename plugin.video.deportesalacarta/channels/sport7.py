# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para sport7
#------------------------------------------------------------
import re
import os
import sys
from core import httptools
from core import scrapertools
from core import logger
from core import config
import xbmc
from core import filetools
from core.item import Item
from core import servertools
from core.scrapertools import decodeHtmlentities as dhe
import time
 
__channel__ = "sport7"
song = os.path.join(config.get_runtime_path() , "music", 'pantera - this love.mp3')
host ="https://sport7.co"
 
 
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
    logger.info("deportesalacarta.sport7 mainlist")
    itemlist = []
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
    url = "http://translate.google.com/translate?depth=1&nv=1&rurl=translate.google.com&sl=ru&tl=es&u=https://sport7.co"
    data = dhe(httptools.downloadpage(url, follow_redirects=False).data )#.decode('cp1251').encode('utf8')
    ## Petición 2
    url = scrapertools.get_match(data, ' src="([^"]+)" name=c ')
    data = dhe(httptools.downloadpage(url, follow_redirects=False).data)#.decode('cp1251').encode('utf8')
    ## Petición 3
    url = scrapertools.get_match(data, 'URL=([^"]+)"')
    data = dhe(httptools.downloadpage(url).data)#.decode('cp1251').encode('utf8')
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    logger.info( "pocoyo")
    logger.info (data)
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
     
     
     
    patrondata = 'Mostrar todos los partidos(.*?)Рекомендуем посмотреть'
    matchesdata = re.compile(patrondata,re.DOTALL).findall(data)
    logger.info("pacopepe")
    logger.info(str(matchesdata))
    for bloque_data in matchesdata:
         
        logger.info("pacopepe")
        patronpartidos = 'text-align: left">[^<]+</span>([^<]+</span>)(.*?)<div class="middle data">'
        matchespartidos = re.compile(patronpartidos,re.DOTALL).findall(bloque_data)
        logger.info(str(matchespartidos))
        for fecha, bloque_partidos in matchespartidos:
            fecha= re.sub(r'de \w+</span>','',fecha)
            logger.info( "tusmuertos")
            logger.info(bloque_partidos)
            #itemlist.append( Item(channel=__channel__, title=fecha,action="mainlist",url="",thumbnail ="",fanart ="",folder=False) )
            patron = 'src=([^"]+)>.*?<span class=time>(\d+:\d+)</span>.*?http.*?http.*?(https://sport.*?)>(.*?)</a>'
            matches = re.compile(patron,re.DOTALL).findall(bloque_partidos)
            for thumbnail, hora, url, title in matches:
                logger.info ("jaimito")
                logger.info(thumbnail)
                if not "Spain" in thumbnail and not "England" in thumbnail and not "Germany" in thumbnail and not "Italy" in thumbnail and not "lch" in thumbnail:continue
                fulltitle = "[COLOR darkorange][B]"+title+"[/B][/COLOR]"
                tiempo = re.compile('(\d+):(\d+)',re.DOTALL).findall(hora)
                logger.info( "manolo" )
                for horas, minutos in tiempo:
                    if  horas== "00":
                        horas = horas.replace("00","24")
                 
                    check =re.compile('(\d)\d',re.DOTALL).findall(horas)
                    if "0"in check:
                        horas = horas.replace("0","")
                        horas = 24 + int(horas)
                     
                    wrong_time =int(horas)
                    value = 1
                    correct_time = wrong_time - value
                    if correct_time == 23:
                       dates = re.compile('(.*?)(\d+)(.*)',re.DOTALL).findall(fecha)
                       for d, days,m in dates:
                           dia = int(days) - 1
                           date = d+" "+str(dia) + m
                     
                    else :
                       date= fecha
                    if correct_time > 24:
                       correct_time = int(correct_time) - 24
                     
                    correct_time = '%02d' % int(correct_time)
                    ok_time = correct_time +":"+ minutos
                    print "guay"
                    print ok_time
                  
                if "24:" in ok_time:
                    ok_time =ok_time.replace("24:","00:")
                 
                 
                from time import gmtime, strftime
                get_date=strftime("%Y-%m-%d %H:%M:%S", time.localtime())
         
                ok_date_hour =re.compile('(\d+)-(\d+)-(\d+) (\d+:\d+:\d+)',re.DOTALL).findall(get_date)
                for year,mes,day,hour in ok_date_hour:
                    current_day =day+"/"+mes+"/"+year
                    current_hour = hour
                    today =scrapertools.get_match(current_day,'(\d+)/\d+/\d+')
                    check_match_hour = scrapertools.get_match(ok_time,'(\d+):\d+')
                    check_match_minute = scrapertools.get_match(ok_time,'\d+:(\d+)')
                    check_today_hour = scrapertools.get_match(current_hour,'(\d+):\d+')
                    check_today_minute = scrapertools.get_match(current_hour,'\d+:(\d+)')
                    check_match_end_live = int (check_match_hour) + 2
                    check_match_end = int (check_today_hour) - 2
                    print "pepe"
                    print check_match_hour
                    print check_match_end
                    print check_match_end_live
                if day in date and int(check_match_hour) < int(check_today_hour) and int(check_today_hour)>= int(check_match_end_live) :
                   continue
                if day in date and int(check_match_hour) == int(check_today_hour) and int(check_match_minute) <= int(check_today_minute) or day in date and int(check_match_hour) < int(check_today_hour) and int(check_today_hour)< int(check_match_end_live) :
                     
                     
                    tiempo = ok_time
                    dia = scrapertools.get_match(date, '\d+')
                    mes = scrapertools.get_match(date, '\d+\s*(?:de\s*|)([A-z]+)')
                    mes = month_convert(mes.title())
                    mes = str(mes).zfill(2)
                    dia_mes = dia+"/"+mes
                    dia_mes =re.sub(r'</span>','',dia_mes)
                    evento = re.sub(r" - "," vs ",title)
                    extra = "live"
                    title = "[COLOR darkorange][B]"+title+"[/B][/COLOR]"+ " " +"[COLOR crimson][B]DIRECTO!![/B][/COLOR]"
                else :
                   tiempo = ok_time
                   dia = scrapertools.get_match(date, '\d+')
                   mes = scrapertools.get_match(date, '\d+\s*(?:de\s*|)([A-z]+)')
                   mes = month_convert(mes.title())
                   mes = str(mes).zfill(2)
                   dia_mes = dia+"/"+mes
                   dia_mes =re.sub(r'</span>','',dia_mes)
                   evento =  re.sub(r" - "," vs ",title)
                   title = "[COLOR firebrick][B]"+ok_time+"[/B][/COLOR]" +"  "+"[COLOR deepskyblue]"+"("+dia_mes.strip()+")"+"[/COLOR]" + " " + "[COLOR olivedrab][B]"+title+"[/B][/COLOR]"
                   extra = "nolive"
                 
                print "amoooo"
                print url
                itemlist.append( Item(channel=__channel__, title="     "+title,action="enlaces",url=url,thumbnail =thumbnail,fanart ="http://s6.postimg.org/uo85sphn5/sport7fanart.jpg",extra=extra,fulltitle = fulltitle,deporte="futbol", evento=evento, date=dia_mes, time=tiempo,context="info_partido",folder=True) )
 
 
         
 
     
     
    return itemlist
 
def enlaces(item):
    logger.info("deportesalacarta.sport7 enlaces")
    itemlist = []
    print "lopera"
    print item.fulltitle
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    print "caca"
    print data
    '''if "Скоро здесь будет" in data :
        title = "Aun no hay enlaces. Pruebe mas tarde".title()
        itemlist.append( Item(channel=__channel__, title="[COLOR lightseagreen][B]"+title+"[/B][/COLOR]",action="mainlist",url="",thumbnail="http://s6.postimg.org/3n87z3jbl/livesportnolinkyetthumb.png",fanart ="http://s6.postimg.org/l1sg7dggh/livesportnolinskyet.jpg",folder=False) )'''
 
    patron= '<img class="img-bt" alt="(.*?) \d+".*?src="([^"]+).*?target="_blank" href="([^"]+).*?<div class="rc">(.*?)</div>'
    matches =re.compile(patron,re.DOTALL).findall(data)
    if len(matches) == 0:
        if item.extra == "live":
           itemlist.append( Item(channel=__channel__, title="[COLOR firebrick][B]No hay enlaces Acestream/Sopcast[/B][/COLOR]",action="mainlist",url="",thumbnail="http://s33.postimg.org/c4guv3q1r/sport7nolinksthumb.png",fanart="http://s33.postimg.org/sc0gx0k9r/sport7nolinksfan.jpg",folder=False) )
        else :
              title = "Aun no hay enlaces. Pruebe mas tarde".title()
              itemlist.append( Item(channel=__channel__, title="[COLOR mediumspringgreen][B]"+title+"[/B][/COLOR]",action="mainlist",url="",thumbnail="http://s33.postimg.org/5jfmbp1nj/sport7nolinkyetthumb.png",fanart ="http://s6.postimg.org/6srzxmt1t/sport7fanartnoenlacesyet.jpg",folder=False) )
    for tipo, thumbnail, link, bibrate in matches:
        print "joder"
        print bibrate
        if tipo == "Sopcast":
           tipo = "[COLOR aquamarine][B]"+tipo+"[/B][/COLOR]"
           thumbnail= "http://s6.postimg.org/v9z5ggmfl/sopcast.jpg"
        else:
            tipo = "[COLOR yellow][B]"+tipo+"[/B][/COLOR]"
            thumbnail= "http://s6.postimg.org/c2c0jv441/torrent_stream_logo_300x262.png"
        if bibrate == "0 kbps" or "-" in bibrate:
           bibrate = "[COLOR forestgreen]No Bitrate[/COLOR]"
        title = tipo + "  "+ "[COLOR chartreuse]"+bibrate+"[/COLOR]"
        if "down.png" in thumbnail:
           continue
        itemlist.append( Item(channel=__channel__, title=title,action="play",url=link,thumbnail=thumbnail,fanart="http://s6.postimg.org/3s6k3cscx/sport7fangame.jpg",fulltitle = item.fulltitle,folder=False) )
 
 
 
    return itemlist
 
def play(item):
    logger.info("deportesalacarta.sport7 play")
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    item.url =scrapertools.get_match(data,'<a href="([^"]+)"')
 
    xbmc.executebuiltin('xbmc.PlayMedia(Stop)')
    fulltitle = item.fulltitle
     
    # Se incluye el título en la url para pasarlo al conector
    url= item.url + "|" + fulltitle
     
    itemlist.append(Item(channel=__channel__, title=item.title, server="p2p", url=url, action="play", folder=False))
     
    return itemlist
 
def month_convert(mes):
    if mes == "Ene":
        mes = "Enero"
    try:
     return{ 'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril':4, 'Mayo' : 5, 'Junio' : 6, 'Julio' : 7, 'Agosto' : 8, 'Septiembre' : 9, 'Octubre' : 10, 'Noviembre' : 11, 'Diciembre' : 12 }[mes]
    except:
        import datetime
 
        month = datetime.datetime.now().strftime("%m")
 
        return month
