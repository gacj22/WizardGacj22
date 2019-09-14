# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para myfootball
#------------------------------------------------------------

import os, re, datetime
from core import logger
from core import config
from core import scrapertools
from core import servertools
from core.item import Item
from core.scrapertools import decodeHtmlentities as dhe
from core import httptools

__channel__ = "myfootball"
host = "http://www.myfootball.ws/"


def mainlist(item):
    logger.info("deportesalacarta.channels.myfootball mainlist")
    itemlist = []

    itemlist.append(item.clone(title="Agenda/Directos", url=host, action="agenda", fanart="http://i.imgur.com/P2bDueX.jpg"))
    itemlist.append(item.clone(title="Resúmenes/Partidos - Novedades", url=host, action="futbol", fanart="http://i.imgur.com/P2bDueX.jpg"))
    itemlist.append(item.clone(title="Resúmenes/Partidos - Categorías", url=host, action="cat", fanart="http://i.imgur.com/P2bDueX.jpg"))

    return itemlist


def agendaglobal(item):
    itemlist = []
    try:
        item.channel = __channel__
        item.url = host
        item.thumbnail = "http://i.imgur.com/4ITXqhc.png"
        item.fanart = "http://i.imgur.com/P2bDueX.jpg"
        itemlist = agenda(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def agenda(item):
    logger.info("deportesalacarta.channels.myfootball agenda")
    itemlist = []
    
    thumbs = {'ukraine':'upl','russia':'russia','england':'apl','spaine':'La_Liga','italy':'serie_a',
              'germany':'bundesliga','france':'ligue-1','UEFA_Champions_League_logo.svg':'lch','el':'le',
              'netherland':'gollandija','portugal':'portugalija'}
    data = translate(item.url)
    data_ru = httptools.downloadpage(item.url).data

    enlaces = scrapertools.find_multiple_matches(data_ru, '<div class="rewievs_tab1">\s*<a href="(http://www.myfootball.ws[^"]+)"')

    dia, mes, bloque = scrapertools.find_single_match(data, '(?i)emisiones</span>.*?(\d+) (?:(?i)de) (\w+)[^<]+</span>(.*?)Ocultar la tradu')
    mes = month_convert(mes.title())
    mes = str(mes).zfill(2)
    dia = dia.zfill(2)
    patron = 'src=([^>]+)>.*?<\/span>\s*([^<]+)<.*?(\d+:\d+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    i = 0
    for thumb, partido, hora in matches:
        partido = partido.replace(" - ", " vs ")
        partido = partido[0].upper() + partido[1:]
        horas, minutos = hora.split(":")
        fecha_actual = datetime.datetime.today()
        fecha_partido = datetime.datetime(fecha_actual.year, int(mes), int(dia),
                                          int(horas), int(minutos))
        fecha_partido = fecha_partido - datetime.timedelta(hours=1)
        hora = fecha_partido.strftime("%H:%M")
        date = fecha_partido.strftime("%d/%m")

        if fecha_partido <= fecha_actual:
            if (fecha_partido + datetime.timedelta(hours=2, minutes=30)) < fecha_actual:
                i += 1
                continue
            scrapedtitle = "[B][COLOR red]"+date+" "+hora+"[/COLOR][COLOR darkorange] " + partido + "[/COLOR][/B]"
        else:
            scrapedtitle = "[B][COLOR green]"+date+" "+hora+"[/COLOR][COLOR darkorange] " + partido + "[/COLOR][/B]"

        try:
            thumb_temp = thumb.rsplit(".",1)[0].rsplit("/",1)[1].replace("flag_", "")
            thumb = "http://www.myfootball.ws/DPYrOE/table/new2/" + thumbs[thumb_temp]+".png"
        except:
            pass

        url = enlaces[i]
        itemlist.append(item.clone(title=scrapedtitle, action="findlives", url=url, thumbnail=thumb, date=date, time=hora, evento=partido, deporte="futbol", context="info_partido"))
        i += 1
    
    if not itemlist:
        itemlist.append(item.clone(title="No hay partidos programados en la agenda", action=""))
    else:
        itemlist.sort(key=lambda item: item.time)
    return itemlist


def findlives(item):
    logger.info("deportesalacarta.channels.myfootball findlives")
    itemlist = []

    data = translate(item.url)
    patron = '<a href=(sop://[^>]+)>.*?href.*?>\s*(-[^<]+)<\/span>'
    matches = scrapertools.find_multiple_matches(data, patron)
    if matches:
        itemlist.append(item.clone(title="[COLOR blue]Sopcast[/COLOR]", action=""))
        for url, bitrate in matches:
            bitrate = bitrate.replace("kbit / s", "kbps")
            scrapedtitle = "   [COLOR darkorange]" + item.evento + " [/COLOR][COLOR blue]" + bitrate + "[/COLOR]"
            itemlist.append(item.clone(title=scrapedtitle, action="play", server="p2p", url=url))
    patron = '<a href=(acestream://[^>]+)>.*?href.*?>\s*(-[^<]+)<\/span>'
    matches = scrapertools.find_multiple_matches(data, patron)
    if matches:
        itemlist.append(item.clone(title="[COLOR red]Acestream[/COLOR]", action=""))
        for url, bitrate in matches:
            bitrate = bitrate.replace("kbit / s", "kbps")
            scrapedtitle = "   [COLOR darkorange]" + item.evento + " [/COLOR][COLOR red]" + bitrate + "[/COLOR]"
            itemlist.append(item.clone(title=scrapedtitle, action="play", server="p2p", url=url))

    if not itemlist:
        itemlist.append(item.clone(title="No hay enlaces disponibles. Inténtalo de nuevo más tarde", text_color="gold", action=""))

    return itemlist

def futbol(item):
    logger.info("deportesalacarta.channels.myfootball futbol")
    itemlist = []
    
    data_ru = httptools.downloadpage(item.url).data
    enlaces = scrapertools.find_multiple_matches(data_ru, '<div class="baseform1">\s*<a href="(http://www.myfootball.ws[^"]+)"')
    data = translate(item.url)

    bloque = scrapertools.find_single_match(data, '(?i)TODAS LAS OPINIONES(.*?)<div class=catPages')

    patron = '<div class=baseform1><table class=infTable.*?src=(.*?)\s+.*?<\/span>.*?<\/span>.*?>(.*?)<\/span>'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    i = 0
    for thumb, title in matches:
        if not thumb.startswith("http"):
            thumb = host + thumb
        title = re.sub(r'(?i)ronda|tour', 'jornada', title).replace("éter", "programa").replace("turísticos", "")
        title = "[COLOR blue]%s[/COLOR]" % title
        url = enlaces[i]
        itemlist.append(item.clone(title=title, action="findvideos", url=url, thumbnail=thumb))
        i += 1
    
    next_page = scrapertools.find_single_match(data, 'u=([^>]+)>»<')
    if next_page:
        itemlist.append(item.clone(title=">> Página Siguiente", url=next_page))
    
    return itemlist


def cat(item):
    logger.info("deportesalacarta.channels.myfootball cat")
    itemlist = []
    thumbs = {'Ucrania':'upl','Rusia':'russia','Inglaterra':'apl','España':'La_Liga','Italia':'serie_a',
              'Alemania':'bundesliga','Francia':'ligue-1','Champions':'lch','Europa league':'le',
              'Campeonato mundial':'chm_2018','Campeonato de europa':'euro_2016'}
    
    data = translate(item.url)
    patron = '<a class=class2 href=\S+u=([^&]+).*?>([^<]+)<\/a><\/span>\s*<\/td>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url, title in matches:
        titulo = title.replace("programa", "Programas").capitalize()
        title = "[COLOR blue]%s[/COLOR]" % titulo
        try:
            thumb = "http://www.myfootball.ws/DPYrOE/table/new2/" + thumbs[titulo]+".png"
        except:
            thumb = item.thumbnail
        itemlist.append(item.clone(title=title, action="futbol", url=url, thumbnail=thumb))
    
    return itemlist


def play(item):
    logger.info("deportesalacarta.channels.myfootball play")
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
    return{ 'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril':4, 'Mayo' : 5, 'Junio' : 6, 'Julio' : 7, 'Agosto' : 8, 'Septiembre' : 9, 'Octubre' : 10, 'Noviembre' : 11, 'Diciembre' : 12 }[mes]
