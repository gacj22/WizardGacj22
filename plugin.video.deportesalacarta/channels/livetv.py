# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para livetv
#------------------------------------------------------------
import urlparse,re
import os

from core import httptools
from core import scrapertools
from core import logger
from core import config

from core.item import Item
from core import servertools
import xbmc
from core.scrapertools import decodeHtmlentities as dhe
import time
import datetime

__channel__ = "livetv"


host ="http://livetv.sx/es"
song = os.path.join(config.get_runtime_path(), 'music', 'imagine-dragons.mp3')


def mainlist(item):
    logger.info("deportesalacarta.livetv mainlist")
    itemlist = []

    xbmc.executebuiltin('xbmc.PlayMedia('+song+')')
    
    #Live
    item.url = "http://livetv.sx/es/allupcomingsports"
    itemlist.append( Item(channel=__channel__, title="[COLOR red][B]LIVE!![/B][/COLOR]" , action="scraper_live", url=host, thumbnail="http://s6.postimg.org/brzwms041/LIVE.png", fanart="http://s6.postimg.org/lqkv999jl/321238_1024x768_www_The_Wallpapers_org.jpg"))
    
    # Main options
    item.url = "http://livetv.sx/es/allupcomingsports"
    data = dhe(httptools.downloadpage(item.url).data)
    patronmain ='<table width="100%" cellpadding=12 cellspacing=0>(.*?)<span class="sltitle">'
    matchesmain = re.compile(patronmain,re.DOTALL).findall(data)
    
    for main in matchesmain:
    
        patron = '<td background.*?href="([^"]+)".*?src="([^"]+)".*?<a class="main".*?><b>(.*?)</b></a>'
        matches = re.compile(patron,re.DOTALL).findall(main)
        for url,thumbnail,deporte in matches:
            if deporte== "Fútbol":
                extra = "http://s6.postimg.org/a2qtepkep/fotbal.jpg"
                deporte ="[COLOR palegreen][B]"+deporte+"[/B][/COLOR]"
            else:
                extra= "http://s6.postimg.org/fs71z0qkx/B9317206944_Z_1_20150503001849_000_GNEAM3_I82_1_0.jpg"
                deporte ="[COLOR skyblue][B]"+deporte+"[/B][/COLOR]"
            itemlist.append( Item(channel=__channel__, title=deporte,action="scraper",url = urlparse.urljoin(host,url),thumbnail= thumbnail,fanart="http://s6.postimg.org/lqkv999jl/321238_1024x768_www_The_Wallpapers_org.jpg",extra=extra,folder=True) )
        

    
    
    return itemlist


def agendaglobal(item):
    itemlist = []
    if item.deporte != "futbol":
        url = "http://livetv.sx/ajax/getaul.php"
        if "hoy" in item.title:
            post = "chk0=true&chk1=false&chk2=false&chk3=false&chk4=false&lng=es"
        elif "mañana" in item.title:
            post = "chk0=false&chk1=true&chk2=false&chk3=false&chk4=false&lng=es"
        elif "directo" in item.title:
            post = "chk0=false&chk1=false&chk2=false&chk3=false&chk4=false&lng=es"
        else:
            post = "chk0=true&chk1=true&chk2=true&chk3=true&chk4=true&lng=es"
        data = dhe(httptools.downloadpage(url, post=post).data)
        patron ='<a class="main".*?><b>(.*?)</b>(.*?)</td></tr></table>'
        bloques = scrapertools.find_multiple_matches(data, patron)
        for deporte, bloque in bloques:
            if deporte != "Fútbol":
                patron = '<td width=34 align="center" valign="top">.*?alt="([^"]+)" src="([^"]+)".*?<a class.*?href="([^"]+)">(.*?)</a>.*?<span class="evdesc">(.*?) a (\d+:\d+)'
                matches = scrapertools.find_multiple_matches(bloque, patron)
                for info, thumbnail, scrapedurl, title, fecha, hora in matches:
                    if deporte == "Diverso":
                        deporte = info
                    fecha = fecha.strip()
                    dia = scrapertools.get_match(fecha, '(\d+)')
                    mes = scrapertools.get_match(fecha, 'de ([A-z]+)')
                    mes = month_convert(mes.title())
                    mes = str(mes).zfill(2)
                    date = dia+"/"+mes
                    title = title.replace("&ndash;"," vs ")
                    evento = title
                    url = urlparse.urljoin(host, scrapedurl)
                    extra= "http://s6.postimg.org/fs71z0qkx/B9317206944_Z_1_20150503001849_000_GNEAM3_I82_1_0.jpg"
                    itemlist.append(Item(channel=__channel__, title=title, action="enlaces", url=url, extra=extra, fanart=extra, thumbnail=thumbnail, deporte=deporte, evento=evento, date=date, time=hora))

    else:
        item.extra = "http://s6.postimg.org/a2qtepkep/fotbal.jpg"
        item.url = "http://livetv.sx/es/allupcomingsports/1/"
        try:
            itemlist = scraper(item)
        except:
            import sys
            for line in sys.exc_info():
                logger.error("{0}".format(line))
            return []

    return itemlist

def scraper(item):
    logger.info("deportesalacarta.livetv scraper")
    
    itemlist = []
    
    # Descarga la página
    
    data = httptools.downloadpage(item.url).data
    
    patron_bloque = '<table align="center" width="90%"></tr><tr><td colspan=4 height=48>(.*?)Archivo de transmisiones'
    matchesenlaces = re.compile(patron_bloque,re.DOTALL).findall(data)
    for pepe in matchesenlaces:
        patron = '<td width=34 align="center" valign="top">.*?src="([^"]+)".*?<a class.*?href="([^"]+)">(.*?)</a>.*?<span class="evdesc">(.*?)<br>(.*?)</span>'
        matches = re.compile(patron,re.DOTALL).findall(pepe)

        for thumbnail , ficha, title, fecha, info in matches:
            xbmc.log("zorro")
            xbmc.log(thumbnail)
            fecha = fecha.strip()
            dia = scrapertools.get_match(fecha, '(\d+)')
            mes = scrapertools.get_match(fecha, 'de ([^<]+) a')
            mes = mes.title()
            mes = month_convert(mes)
            mes = str(mes).zfill(2)
            time = scrapertools.get_match(fecha, '\d+:\d+')
            date = dia+"/"+str(mes)
            info = info.strip()
            title= re.sub(r"-","",title)
            title = title.replace(" &ndash; "," vs ")
            xbmc.log("titleeeee")
            xbmc.log (title)
            evento = title
            fecha ="[COLOR gold][B]"+fecha+"[/B][/COLOR]"
            info = "[COLOR orange][B]"+info+"[/B][/COLOR]"
            fanart = item.extra
            if item.extra =="http://s6.postimg.org/a2qtepkep/fotbal.jpg" :
               encuentro ="[COLOR palegreen][B]"+title+"[/B][/COLOR]"
               extra = "futbol"
            else:
               encuentro ="[COLOR skyblue][B]"+title+"[/B][/COLOR]"
               extra = item.title.replace("[COLOR skyblue][B]", "").replace("[/B][/COLOR]", "")
            encuentro = fecha+ "--"+encuentro+"--"+ info

            itemlist.append( Item(channel=__channel__, title=encuentro, action="enlaces", url=urlparse.urljoin(host,ficha), thumbnail=thumbnail, fanart=fanart, extra=extra, fulltitile=title, date=date, time=time, evento=evento, deporte=extra,context="info_partido",folder=True) )
    return itemlist

def scraper_live(item):
    logger.info("deportesalacarta.livetv scraper")
    
    itemlist = []
    
    # Descarga la página
    
    data = httptools.downloadpage(item.url).data
    
    
    patron_bloque = '<span class="date">Hoy.*?</span>(.*?)ensenar todo'
    matchesenlaces = re.compile(patron_bloque,re.DOTALL).findall(data)
    for pepe in matchesenlaces:
        patron = 'alt.*?src="([^"]+)".*?href="([^"]+)">([^"]+)</a>.*?<span class="evdesc">(\d+:\d+) \(([^"]+)\)'
        matches = re.compile(patron,re.DOTALL).findall(pepe)
        
        for thumbnail, url,title, hora, info in matches:
            xbmc.log("osstiiiaaaa")
            xbmc.log(thumbnail)
            try:
               check = scrapertools.get_match(thumbnail,'http.*?icons\/(\w\w\.)')
               deporte = "futbol"
            except:
               deporte="pepe"
            fecha = datetime.datetime.today()
            fecha = fecha.strftime("%d/%m")
            time = "live"
            date = fecha
            title = title.replace(" &ndash; "," vs")
            evento = title
            info = info.strip()
            hora = hora.strip()
            info = "("+info+")"
            hora = "[COLOR yellow][B]"+hora+"[/B][/COLOR]"
            info = "[COLOR orange][B]"+info+"[/B][/COLOR]"
            title ="[COLOR red][B]"+title+"[/B][/COLOR]"
            encuentro = hora +"--"+title +" "+ info
            
            
            xbmc.log("mojonpami")
            xbmc.log(deporte)
            itemlist.append( Item(channel=__channel__, title=encuentro,action="enlaces",url = urlparse.urljoin(host,url),thumbnail= thumbnail,extra="live",fulltitle= title,fanart= "http://s6.postimg.org/fs71z0qkx/B9317206944_Z_1_20150503001849_000_GNEAM3_I82_1_0.jpg",date=date, time=time, evento=evento,context="info_partido", deporte=deporte,folder=True) )
    return itemlist

def enlaces(item):
    logger.info("deportesalacarta.livetv enlaces")
    xbmc.executebuiltin( "Container.Update" )
    if not xbmc.Player().isPlaying():
        xbmc.sleep(20)
        xbmc.executebuiltin('xbmc.PlayMedia('+song+')')
    
    itemlist = []
    data = dhe(httptools.downloadpage(item.url).data)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    if "<i id=\"whelint\" style=\"line-height: 150%;\">" in data:
        
        if item.extra =="futbol":
           fanart = "http://s6.postimg.org/56n6n0k9d/Wembley.jpg"
        else:
           fanart ="http://s6.postimg.org/naq77nhxt/Sport_Wallpaper_HD_3000x2250.jpg"
        itemlist.append( Item(channel=__channel__, title="[COLOR orangered][B]Las referencias de la transmisión van a ser publicadas no más tarde de media hora de su principio[/B][/COLOR]",thumbnail="http://s6.postimg.org/p3t3vz34h/Panasonic_AJ_HDX900.png",fanart= fanart,folder=False) )
    else:
        if '<span class="lnkt">AceStream Links</span>' in data:
            patronacestream = '<span class="lnkt">AceStream Links</span>(.*?)<a name="comments"></a>'
            matchesacestream = re.compile(patronacestream,re.DOTALL).findall(data)
         
            for bloque_acestream in matchesacestream:
                patron ='<td width=16><img title.*?src="([^"]+)"></a></td>.*?<a href="(acestream:.*?)"'
                matches= re.compile(patron,re.DOTALL).findall(bloque_acestream)
                for idioma, url in matches:
                    #if velocidad == "":
                    #  velocidad = "S/N"
                    
                    itemlist.append( Item(channel=__channel__, title="[COLOR yellow][B]Enlaces Acestream[/B][/COLOR]",action="play",url = url,thumbnail = idioma,fanart ="http://s6.postimg.org/e5hudsej5/Nou_Camp_Stadium_Barcelona_Football_Wallpapers_H.jpg",fulltitle= item.fulltitle,folder=False) )
        else:
             itemlist.append( Item(channel=__channel__, title="[COLOR yellow][B]No hay elaces Acetream[/B][/COLOR]",thumbnail = "http://s6.postimg.org/c2c0jv441/torrent_stream_logo_300x262.png",fanart="http://s6.postimg.org/ttnmybjip/5499731408_42e3876093_b.jpg",folder=False) )
        #Enlaces Sopcast
        if "<span class=\"lnkt\">SopCast Links" in data:
            
            patronsopcast = '<span class="lnkt">SopCast Links</span>(.*?)<a name="comments"></a>'
            matchessopcast = re.compile(patronsopcast,re.DOTALL).findall(data)

            for bloque_sopcast in matchessopcast:
                patron ='<td width=16><img title.*?src="([^"]+)".*?title=.*?>([^<]+)</td>.*?<a href="(sop:.*?)"'
                matches= re.compile(patron,re.DOTALL).findall(bloque_sopcast)
                for idioma,bibrate,url in matches:
                    
                    title = "[COLOR aquamarine][B]Enlace Sopcast[/B][/COLOR]"+" ("+"[COLOR green][B]"+bibrate+"[/B][/COLOR]"+")"
                    itemlist.append( Item(channel=__channel__, title=title,action="play",url = url,thumbnail =idioma,fanart="http://s6.postimg.org/e5hudsej5/Nou_Camp_Stadium_Barcelona_Football_Wallpapers_H.jpg",fulltitle=item.fulltitle,folder=False) )
                        
        else:
    
            itemlist.append( Item(channel=__channel__, title="[COLOR aquamarine][B]No hay elaces Sopcast[/B][/COLOR]",thumbnail ="http://s6.postimg.org/v9z5ggmfl/sopcast.jpg",fanart= "http://s6.postimg.org/ttnmybjip/5499731408_42e3876093_b.jpg",folder=False) )
                        
                        

    return itemlist

def play(item):
    logger.info("deportesalacarta.livetv play")
    itemlist = []

    xbmc.executebuiltin('xbmc.PlayMedia(Stop)')
    fulltitle= item.fulltitle

    # Se incluye el título en la url para pasarlo al conector
    url= item.url + "|" + fulltitle
    itemlist.append(Item(channel=__channel__, title=item.title, server="p2p", url=url, action="play", folder=False))

    return itemlist

def month_convert(mes):
    return{ 'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril':4, 'Mayo' : 5, 'Junio' : 6, 'Julio' : 7, 'Agosto' : 8, 'Septiembre' : 9, 'Octubre' : 10, 'Noviembre' : 11, 'Diciembre' : 12 }[mes]
