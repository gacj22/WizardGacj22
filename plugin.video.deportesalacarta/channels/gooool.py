# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para Gooool
#------------------------------------------------------------
import os, re, datetime
from core import logger
from core import httptools
from core import config
from core import scrapertools
from core import servertools
from core.item import Item
from core.scrapertools import decodeHtmlentities as dhe

__channel__ = "gooool"
host = "http://gooool.org/"


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone(title="Agenda/Directos", url=host, action="agenda", fanart="http://i.imgur.com/wjjQ1PN.jpg"))
    itemlist.append(item.clone(title="Resúmenes/Partidos - Fútbol", url=host, action="futbol", fanart="http://i.imgur.com/wjjQ1PN.jpg"))
    itemlist.append(item.clone(title="Resúmenes/Partidos - Deportes", url=host, action="deportes", fanart="http://i.imgur.com/wjjQ1PN.jpg"))

    return itemlist


def agendaglobal(item):
    itemlist = []
    try:
        item.channel = __channel__
        item.url = host
        item.thumbnail = "http://i.imgur.com/xfZ3TS4.png"
        item.fanart = "http://i.imgur.com/wjjQ1PN.jpg"
        itemlist = agenda(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def agenda(item):
    logger.info()
    itemlist = []
    
    data = translate(item.url)

    listas = {}
    i = 0
    patron = '<\/span> <span style=color:yellow><u><span.*?>.*?(\d+)\s*(.*?)' \
             '</span>(.*?)(?:left"><span style=color:yellow>|<span>Cerrar lista de traducciones<\/span>)'
    bloques = scrapertools.find_multiple_matches(data, patron)
    for dia, mes, bloque in bloques:
        mes = re.sub(r'(?i)\s*de\s*', '', mes)
        mes = month_convert(mes.title())
        mes = str(mes).zfill(2)
        dia = dia.zfill(2)
        patron = '>(\d+:\d+)</span>.*?src=(.*?) alt.*?u=(http://gooool.org[^&]+)&' \
                 '.*?<span style=color:white>.*?<span style=color:white>([^<]+)</span>'
        matches = scrapertools.find_multiple_matches(bloque, patron)
        listas[str(i)] = []
        for hora, thumbnail, url, partido in matches:
            partido = partido.replace(" - ", " vs ")
            horas, minutos = hora.split(":")
            fecha_actual = datetime.datetime.today()
            try:
                fecha_partido = datetime.datetime(fecha_actual.year, int(mes), int(dia),
                                                  int(horas), int(minutos))
            except:
                fecha_partido = datetime.datetime(fecha_actual.year, int(mes), int(dia),
                                  int(horas), 30)
            fecha_partido = fecha_partido - datetime.timedelta(hours=1)
            hora = fecha_partido.strftime("%H:%M")
            date = fecha_partido.strftime("%d/%m")

            if fecha_partido <= fecha_actual:
                if (fecha_partido + datetime.timedelta(hours=2, minutes=30)) < fecha_actual:
                    continue
                scrapedtitle = "[B][COLOR red]"+date+" "+hora+"[/COLOR][COLOR darkorange] " + partido + "[/COLOR][/B]"
            else:
                scrapedtitle = "[B][COLOR green]"+date+" "+hora+"[/COLOR][COLOR darkorange] " + partido + "[/COLOR][/B]"

            scrapedthumbnail = host + thumbnail
            listas[str(i)].append(item.clone(title=scrapedtitle, action="findlives", url=url, thumbnail=scrapedthumbnail, date=date, time=hora, evento=partido, deporte="futbol", context="info_partido"))
        listas[str(i)].sort(key=lambda item: item.time)
        i += 1
    
    
    if not listas:
        itemlist.append(item.clone(title="No hay partidos programados en la agenda", action=""))
    else:
        for i in range(0, len(listas)):
            itemlist.extend(listas[str(i)])

    return itemlist


def futbol(item):
    logger.info()
    itemlist = []
    
    data = translate(item.url)

    bloque = scrapertools.find_single_match(data, '<ul id=hbul2(.*?)</ul>')
    patron = 'href.*?href=.*?u=(http://gooool.org/news[^&]+)&.*?>(.*?)</a>'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for url, liga in matches:
        liga = liga.replace("transferencia", "Programas").decode("utf-8").title()
        title = "[COLOR blue]%s[/COLOR]" % liga
        itemlist.append(item.clone(title=title, action="videos", url=url))
    bloque = scrapertools.find_single_match(data, '<ul id=hbul3(.*?)</ul>')
    patron = 'href.*?href=.*?u=(http://gooool.org/news[^&]+)&.*?>(.*?)</a>'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for url, liga in matches:
        title = "[COLOR blue]%s[/COLOR]" % liga
        itemlist.append(item.clone(title=title, action="videos", url=url))
    
    return itemlist


def deportes(item):
    logger.info()
    itemlist = []
    
    data = translate(item.url)

    bloque = scrapertools.find_single_match(data, '<ul id=hbul5(.*?)</ul>')
    patron = 'href.*?href=.*?u=(http://gooool.org/news[^&]+)&.*?>(.*?)</a>'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for url, liga in matches:
        liga = liga.replace("transferencia", "Programas").decode("utf-8").title()
        url = url
        title = "[COLOR blue]%s[/COLOR]" % liga
        itemlist.append(item.clone(title=title, action="videos", url=url))
    itemlist.insert(-1, item.clone(title="[COLOR blue]Hockey[/COLOR]", action="videos", url="http://gooool.org/news/nhl_nhl/"))
    
    return itemlist

def videos(item):
    logger.info()
    itemlist = []
    
    data = translate(item.url)

    patron = '<div class="item nuclear".*?u=(http://gooool.org/news[^&]+)&.*?(?:</span> ([^<]+)</span>|src=(.*?)\s.*?alt="([^"]+)")'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url, title, thumbnail, title2 in matches:
        if not title:
            title = title2
        title = title.replace("gira", "jornada")
        title = "[COLOR blue]%s[/COLOR]" % title
        if thumbnail:
            thumbnail = host + thumbnail
        else:
            thumbnail = item.thumbnail
        itemlist.append(item.clone(title=title, action="findvideos", url=url, thumbnail=thumbnail))

    next_page = scrapertools.find_single_match(data, '<div class=pager>.*?\d</span>.*?u=(http://gooool.org/news[^&]+)&')
    if next_page:
        itemlist.append(item.clone(title=">> Siguiente Página", url=next_page, action="videos"))
    
    return itemlist


def findlives(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    patron = '<a href="(sop://[^"]+)".*?</a>.*?(\d+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    if matches:
        itemlist.append(item.clone(title="[COLOR blue]Sopcast[/COLOR]", action=""))
        for url, bitrate in matches:
            scrapedtitle = "   [COLOR darkorange]" + item.evento + " [/COLOR][COLOR blue][" + bitrate + "kbps][/COLOR]"
            itemlist.append(item.clone(title=scrapedtitle, action="play", server="p2p", url=url))
    patron = '<a href="(acestream://[^"]+)".*?</a>.*?(\d+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    if matches:
        itemlist.append(item.clone(title="[COLOR red]Acestream[/COLOR]", action=""))
        for url, bitrate in matches:
            scrapedtitle = "   [COLOR darkorange]" + item.evento + " [/COLOR][COLOR red][" + bitrate + "kbps][/COLOR]"
            itemlist.append(item.clone(title=scrapedtitle, action="play", server="p2p", url=url))

    if not itemlist:
        itemlist.append(item.clone(title="No hay enlaces disponibles. Inténtalo de nuevo más tarde", text_color="gold", action=""))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    if item.server == "p2p":
        fulltitle = "[COLOR darkorange]"+item.evento+"[/COLOR]"
        url = item.url+"|"+fulltitle
        itemlist.append(item.clone(url=url))
    else:
        itemlist.append(item.clone())
    
    return itemlist

def translate(url_translate):
    #### Opción 1: 'follow_redirects=False'
    ## Petición 1
    url = "http://translate.google.com/translate?depth=1&nv=1&rurl=translate.google.com&sl=ru&tl=es&u=" + url_translate
    data = dhe(httptools.downloadpage(url, follow_redirects=False).data)
    ## Petición 2
    url = scrapertools.get_match(data, ' src="([^"]+)" name=c ')
    data = dhe(httptools.downloadpage(url, follow_redirects=False).data)
    ## Petición 3
    url = scrapertools.get_match(data, 'URL=([^"]+)"')
    data = dhe(httptools.downloadpage(url).data)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    
    return data

def month_convert(mes):
    try:
        return { 'January': 1, 'February': 2, 'March': 3, 'April':4, 'May' : 5, 'June' : 6, 'July' : 7, 'August' : 8, 'September' : 9, 'October' : 10, 'November' : 11, 'December' : 12 }[mes]
    except:
        return { 'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril':4, 'Mayo' : 5, 'Junio' : 6, 'Julio' : 7, 'Agosto' : 8, 'Septiembre' : 9, 'Octubre' : 10, 'Noviembre' : 11, 'Diciembre' : 12 }[mes]
