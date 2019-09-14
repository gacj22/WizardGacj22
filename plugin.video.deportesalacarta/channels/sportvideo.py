# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para Sport-Video
#------------------------------------------------------------
from core import logger
from core import config
from core import httptools
from core import scrapertools
from core.item import Item

__channel__ = "sportvideo"
host_sport = "http://www.sport-video.org.ua/"


def mainlist(item):
    logger.info("deportesalacarta.channels.sportvideo mainlist")
    itemlist = []
    itemlist.append(Item(channel=__channel__, title="Novedades" , action="novedades", url="http://www.sport-video.org.ua/index.html", thumbnail=item.thumbnail, fanart=item.fanart, page=1))
    itemlist.append(Item(channel=__channel__, title="Archivo" , action="archive", url="http://www.sport-video.org.ua/index.html", thumbnail=item.thumbnail, fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Categorías" , action="categoria", url="http://www.sport-video.org.ua/index.html", thumbnail=item.thumbnail, fanart=item.fanart))

    return itemlist

def novedades(item):
    logger.info("deportesalacarta.channels.sportvideo novedades")
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.decodeHtmlentities(data)
    data = data.replace("\n","").replace("\t","")

    bloque = scrapertools.find_multiple_matches(data, '(ayer.*?)<div id="L')
    for match in bloque:
        if "TORRENT" not in match: continue
        position = scrapertools.find_single_match(match, 'ayer.*?top:(.*?)px')
        scrapedthumbnail = scrapertools.find_single_match(match, 'javascript.*?src="([^"]+)"')
        scrapedurl = scrapertools.find_single_match(match, '<a href=".\/([^"]+)" title="TORRENT">')
        scrapedtitle = scrapertools.find_single_match(match, 'class="style[\d+]">(.*?)</a>')
        scrapedtitle = scrapedtitle.replace(" at "," vs ")
        scrapedtitle = " [COLOR gold]"+scrapedtitle.rsplit(" ",1)[0]+"[/COLOR] [COLOR brown]"+scrapedtitle.rsplit(" ",1)[1]+"[/COLOR]"
        scrapedthumbnail = host_sport + scrapedthumbnail
        scrapedurl = host_sport + scrapedurl
        itemlist.append(Item(channel=__channel__, title=scrapedtitle, url=scrapedurl, action="play", server="torrent", thumbnail=scrapedthumbnail, order=int(position), fanart=item.fanart, folder=False))

    itemlist.sort(key=lambda item: item.order)

    page = item.page + 1
    next_page = scrapertools.find_single_match(data, '<a href="./([^"]+)" class="style2">'+str(page)+'</a>')
    if next_page != "":
        scrapedurl = host_sport + next_page
        itemlist.append(Item(channel=__channel__, title=">> Siguiente", url=scrapedurl, action="novedades", page=page, thumbnail=item.thumbnail, fanart=item.fanart, folder=True))

    return itemlist

def categoria(item):
    logger.info("deportesalacarta.channels.sportvideo categoria")
    itemlist = []

    itemlist.append(Item(channel=__channel__, title="Fútbol", url=host_sport + "soccer.html", action="novedades", page=1, thumbnail=item.thumbnail, fanart=item.fanart, folder=True))
    itemlist.append(Item(channel=__channel__, title="Baloncesto", url=host_sport + "basketball.html", action="novedades", page=1, thumbnail=item.thumbnail, fanart=item.fanart, folder=True))
    itemlist.append(Item(channel=__channel__, title="Fútbol Americano", url=host_sport + "americanfootball.html", action="novedades", page=1, thumbnail=item.thumbnail, fanart=item.fanart, folder=True))
    itemlist.append(Item(channel=__channel__, title="Rugby", url=host_sport + "rugby.html", action="novedades", page=1, thumbnail=item.thumbnail, fanart=item.fanart, folder=True))
    itemlist.append(Item(channel=__channel__, title="Hockey", url=host_sport + "hockey.html", action="novedades", page=1, thumbnail=item.thumbnail, fanart=item.fanart, folder=True))
    itemlist.append(Item(channel=__channel__, title="AFL/Fútbol Gaélico", url=host_sport + "gaelic.html", action="novedades", page=1, thumbnail=item.thumbnail, fanart=item.fanart, folder=True))
    itemlist.append(Item(channel=__channel__, title="Otros Deportes", url=host_sport + "other.html", action="novedades", page=1, thumbnail=item.thumbnail, fanart=item.fanart, folder=True))

    return itemlist

def archive(item):
    logger.info("deportesalacarta.channels.sportvideo archive")
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.decodeHtmlentities(data)
    data = data.replace("\n","").replace("\t","")

    urls = []
    months = {'JANUARY':'ENERO', 'FEBRUARY':'FEBRERO', 'MARCH':'MARZO', 'APRIL':'ABRIL',
              'MAY':'MAYO', 'JUNE':'JUNIO', 'JULY':'JULIO', 'AUGUST':'AGOSTO',
              'SEPTEMBER':'SEPTIEMBRE', 'OCTOBER':'OCTUBRE', 'NOVEMBER':'NOVIEMBRE', 'DECEMBER':'DICIEMBRE'}
    bloque = scrapertools.find_single_match(data, '(<ul id="TabMenu2">.*?</body>)')
    matches = scrapertools.find_multiple_matches(bloque, '<a href="./([^"]+)"><img.*?alt="([^"]+)"')
    for i, match in enumerate(matches):
        if "RSS" in match[1]: continue
        scrapedurl = host_sport + match[0]
        if scrapedurl in urls: continue
        urls.append(scrapedurl)
        month = scrapertools.find_single_match(match[1], '[A-z]+')
        scrapedtitle = match[1].replace(month, months[month])
        itemlist.append(Item(channel=__channel__, title=scrapedtitle, url=scrapedurl, action="novedades", page=1, thumbnail=item.thumbnail, fanart=item.fanart, folder=True))

    return itemlist
