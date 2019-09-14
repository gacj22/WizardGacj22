# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para Elgoles
#------------------------------------------------------------

import re
import datetime
from core import logger
from core import config
from core import httptools
from core import scrapertools
from core.item import Item

__channel__ = "elgoles"
host = "http://elgoles.ru"


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(Item(channel=__channel__, title="Agenda/Directos" , action="agenda", url=host, thumbnail="http://s6.postimg.org/as7g0t9qp/STREAMSPORTAGENDA.png",fanart="http://s6.postimg.org/5utvfp7rl/streamsportonairfan.jpg"))
    itemlist.append(Item(channel=__channel__, title="Canales" , action="canales", thumbnail="http://i.imgur.com/Vqf0tmU.jpg",fanart="http://s6.postimg.org/sm2y23ssx/streamsportsfutbolfan.jpg"))

    return itemlist


def agendaglobal(item):
    itemlist = []
    try:
        item.channel = __channel__
        item.url = host
        item.thumbnail = "http://i.imgur.com/Vqf0tmU.jpg"
        item.fanart = "http://s6.postimg.org/5utvfp7rl/streamsportonairfan.jpg"
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

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t", '', data)
    logger.info(data)

    patron = '<span class=\s*t\s*>(\d+):(\d+)<.*?<img src=(.*?)\s*/>' \
             '.*?href=([^>]+)>([^<]+)</a>.*?<td>\s*(.*?)\s*</td>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for hora, minutos, thumb, scrapedurl, title, tipo in matches:
        if tipo != "Acestream":
            continue
        scrapedthumbnail = host + thumb

        scrapedtitle = "[COLOR darkorange]%s:%s[/COLOR] [COLOR green]%s[/COLOR]" % (hora, minutos, title)
        try:
            if ":" in title:
                title = title.split(":", 1)[1]
            title = re.sub(r" - ", "-", title)
            team1, team2 = title.split("-")
            evento = team1+" vs "+team2
            deporte = "futbol"
        except:
            evento = ""
            deporte = ""

        date = datetime.datetime.today()

        fecha_partido = datetime.datetime(date.year, date.month, date.day, int(hora), int(minutos))
        hora = fecha_partido.strftime("%H:%M")
        date = fecha_partido.strftime("%d/%m")

        itemlist.append(Item(channel=__channel__, title=scrapedtitle, url=scrapedurl, action="play", thumbnail=scrapedthumbnail, fanart=item.fanart,
                             date=date, time=hora, evento=evento, deporte=deporte, context="info_partido"))

    return itemlist


def canales(item):
    logger.info()
    itemlist = []
    for i in range(1, 11):
        url = host + "/canal-%s/" % i
        itemlist.append(item.clone(action="play", url=url, title="Canal %s" % i, server="p2p"))

    return itemlist

    
def play(item):
    from core import servertools
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t", '', data)

    url = servertools.findvideosbyserver(data, "p2p")
    if url:
        url = url[0][1]
        itemlist.append(item.clone(url=url, server="p2p"))

    return itemlist
