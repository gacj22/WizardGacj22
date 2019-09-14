# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para 9score
#------------------------------------------------------------

import re
import datetime
from core import logger
from core import config
from core import httptools
from core import scrapertools
from core.item import Item

__channel__ = "ninescore"
host = "http://www.9score.com"


def mainlist(item):
    logger.info("deportesalacarta.channels.9score mainlist")
    itemlist = []

    itemlist.append(Item(channel=__channel__, title="Agenda/Directos" , action="agenda", url="http://www.9score.com/live-football-sopcast-link.html", thumbnail="http://s6.postimg.org/as7g0t9qp/STREAMSPORTAGENDA.png",fanart="http://s6.postimg.org/5utvfp7rl/streamsportonairfan.jpg", folder=True))
    itemlist.append(Item(channel=__channel__, title="Partidos Completos" , action="partidos", url="http://www.9score.com/fullmatch", thumbnail="http://s6.postimg.org/5w3t949ld/streamsportsfutbolthumb.png",fanart="http://s6.postimg.org/sm2y23ssx/streamsportsfutbolfan.jpg", folder=True))
    itemlist.append(Item(channel=__channel__, title="Resúmenes" , action="resumenes", url="http://www.9score.com/highlights", thumbnail="http://s6.postimg.org/5w3t949ld/streamsportsfutbolthumb.png",fanart="http://s6.postimg.org/sm2y23ssx/streamsportsfutbolfan.jpg", folder=True))

    return itemlist

def agendaglobal(item):
    itemlist = []
    try:
        item.channel = __channel__
        item.url = "http://www.9score.com/live-football-sopcast-link.html"
        item.thumbnail = "http://s6.postimg.org/as7g0t9qp/STREAMSPORTAGENDA.png"
        item.fanart = "http://s6.postimg.org/5utvfp7rl/streamsportonairfan.jpg"
        itemlist = agenda(item)
        if itemlist[-1].action == "agenda":
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def agenda(item):
    logger.info("deportesalacarta.channels.9score agenda")
    itemlist = []
    thumbs = {'Russian Premier League':'russia','Premier League':'apl','La Liga':'La_Liga','Serie A':'serie_a',
              'Bundesliga':'bundesliga','Ligue 1':'ligue-1','Champions League':'lch','Europa League':'le',
              'Eredivisie':'gollandija','Primeira Liga':'portugalija'}
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t", '', data)

    bloque = scrapertools.find_multiple_matches(data, '<div class="date_time column"><span(.*?)</li>')
    for match in bloque:
        patron = 'starttime time">(\d+):(\d+)<.*?endtime time">(.*?)<' \
                 '.*?alt="([^"]+)" src="([^"]+)".*?alt="([^"]+)" src="([^"]+)"' \
                 '.*?live_btn column"><a href="([^"]+)".*?style="color:#([^;]+)'
        matches = scrapertools.find_multiple_matches(match, patron)
        for hora, minutos, date, team1, team1image, team2, team2image, scrapedurl, live in matches:
            scrapedthumbnail = host+team1image.replace('small/','big/').replace('.jpg','.png')
            if "no_image" in scrapedthumbnail:
                scrapedthumbnail = host+team2image.replace('small/','big/').replace('.jpg','.png')
                if "no_image" in scrapedthumbnail: scrapedthumbnail = item.thumbnail

            scrapedurl = host+scrapedurl
            team1 = scrapertools.decodeHtmlentities(team1)
            team2 = scrapertools.decodeHtmlentities(team2)
            evento = team1+" vs "+team2
            fulltitle = "[COLOR darkorange]"+team1+" vs "+team2+"[/COLOR]"
            dia, mes = date.split("/")
            fecha_partido = datetime.datetime(datetime.datetime.today().year, int(mes), int(dia), int(hora), int(minutos))
            hora_partido = fecha_partido + datetime.timedelta(hours=2)
            hora = hora_partido.strftime("%H:%M")
            date = fecha_partido.strftime("%d/%m")
        
            if "3434" in live:
                fecha = "[COLOR green]["+date+"] "+hora+" [/COLOR]"
            else:
                fecha = "[COLOR red]["+date+"] "+hora+" [/COLOR]"

            scrapedtitle = fecha + fulltitle
            itemlist.append(Item(channel=__channel__, title=scrapedtitle, url=scrapedurl, action="p2p", thumbnail=scrapedthumbnail, fanart=item.fanart, fulltitle=fulltitle, folder=True,
                                 date=date, time=hora, evento=evento, deporte="futbol", context="info_partido"))
    
    next_page = scrapertools.find_single_match(data, 'rel="next" href="([^"]+)"')
    if len(next_page) > 0:
        itemlist.append(Item(channel=__channel__, title=">> Siguiente", url=host+next_page, action="agenda", thumbnail=item.thumbnail, fanart=item.fanart, folder=True))

    return itemlist


def partidos(item):
    logger.info("deportesalacarta.channels.9score partidos")
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t", '', data)

    patron = '<div class="cover">.*?href="([^"]+)".*?title="([^"]+)".*?' \
             'src="([^"]+)".*?longdate">(\d+)-(\d+)-(\d+)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail, mes, dia, year in matches:
        scrapedurl = host + scrapedurl
        scrapedthumbnail = host + scrapedthumbnail
        scrapedtitle = "[COLOR darkorange]"+scrapedtitle+"[/COLOR] [COLOR red]["+dia+"/"+mes+"/"+year+"][/COLOR]"
        itemlist.append(Item(channel=__channel__, title=scrapedtitle, url=scrapedurl, action="findvideos", thumbnail=scrapedthumbnail, fanart=item.fanart, folder=True))
    
    next_page = scrapertools.find_single_match(data, '<span class=\'current\'>[^<]+</span><a href="([^"]+)"')
    if len(next_page) > 0:
        itemlist.append(Item(channel=__channel__, title=">> Siguiente", url=host+next_page, action="partidos", thumbnail=item.thumbnail, fanart=item.fanart, folder=True))
    return itemlist

    
def resumenes(item):
    logger.info("deportesalacarta.channels.9score resumenes")
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t", '', data)

    bloque = scrapertools.find_multiple_matches(data, '<div class="date_time column"><span(.*?)</li>')
    for match in bloque:
        patron = 'shortdate">(.*?)<.*?alt="([^"]+)" src="([^"]+)"' \
                 '.*?alt="([^"]+)" src="([^"]+)".*?play_btn column"><a href="([^"]+)"'
        matches = scrapertools.find_multiple_matches(match, patron)
        for fecha, team1, team1image, team2, team2image, scrapedurl in matches:
            scrapedthumbnail = host+team1image.replace('small/','big/').replace('.jpg','.png')
            if "no_image" in scrapedthumbnail:
                scrapedthumbnail = host+team2image.replace('small/','big/').replace('.jpg','.png')
                if "no_image" in scrapedthumbnail: scrapedthumbnail = item.thumbnail

            scrapedurl = host+scrapedurl
            fulltitle = "[COLOR darkorange]"+team1+" vs "+team2+"[/COLOR]"
            fecha = "[COLOR red]["+fecha+"][/COLOR] "
            scrapedtitle = fecha + fulltitle
            itemlist.append(Item(channel=__channel__, title=scrapedtitle, url=scrapedurl, action="findvideos", thumbnail=scrapedthumbnail, fanart=item.fanart, fulltitle=fulltitle, folder=True))
    
    next_page = scrapertools.find_single_match(data, '<span class=\'current\'>[^<]+</span><a href="([^"]+)"')
    if len(next_page) > 0:
        itemlist.append(Item(channel=__channel__, title=">> Siguiente", url=host+next_page, action="resumenes", thumbnail=item.thumbnail, fanart=item.fanart, folder=True))
    return itemlist


def p2p(item):
    logger.info("deportesalacarta.channels.9score p2p")
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t", '', data)

    try:
        patron = "<td align='left'.*?>([^<]+)</a>.*?>([^<]+)</a>.*?>([^<]+)</a>"
        matches = scrapertools.find_multiple_matches(data, patron)

        acestream = False
        sopcast = False
        for scrapedurl, idioma, bitrate in matches:
            if not scrapedurl.startswith('sop') and not scrapedurl.startswith('acestream'): continue
            if scrapedurl.startswith('sop') and not sopcast:
                itemlist.append(Item(channel=__channel__, title="[COLOR green]Enlaces SOPCAST:[/COLOR]", url="", action="", thumbnail=item.thumbnail, fanart=item.fanart, folder=False))
                sopcast = True
            if scrapedurl.startswith('acestream') and not acestream:
                itemlist.append(Item(channel=__channel__, title="[COLOR green]Enlaces ACESTREAM:[/COLOR]", url="", action="", thumbnail=item.thumbnail, fanart=item.fanart, folder=False))
                acestream = True
            scrapedtitle = "     "+item.fulltitle
            if idioma != "" and idioma != "n/a":
                idioma = idioma.replace('tiếng Nga','Ruso').replace('tiếng TBN','Español').replace('tiếng Anh','Inglés')
                scrapedtitle += " [COLOR sienna]["+idioma+"][/COLOR]"
            if bitrate != "" and bitrate != "n/a":
                scrapedtitle += " [COLOR orangered]("+bitrate+")[/COLOR]"
            scrapedurl += "|"+item.fulltitle
            itemlist.append(Item(channel=__channel__, title=scrapedtitle, url=scrapedurl, action="play", server="p2p", thumbnail=item.thumbnail, fanart=item.fanart, folder=False))
    except:
        pass

    if len(itemlist) == 0:
        itemlist.append(Item(channel=__channel__, title="[COLOR green]No hay enlaces disponibles todavía para este partido[/COLOR]", url="", action="", thumbnail=item.thumbnail, fanart=item.fanart, folder=False))

    return itemlist
