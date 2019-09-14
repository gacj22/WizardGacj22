# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para TUGOLEADA
# http://blog.tvalacarta.info/plugin-xbmc/deportesalacarta/
#------------------------------------------------------------
import re
import datetime

from core import httptools
from core import scrapertools
from core import servertools
from core import logger
from core import config
from core.item import Item

__channel__ = "tugoleada"

host = "http://tumarcador.xyz/"


def mainlist(item):
    logger.info("deportesalacarta.channels.tugoleada mainlist")
    itemlist = []

    itemlist.append(Item(channel=__channel__, title="Agenda/Directos", action="entradas", url="http://www.elitegol.com", thumbnail="http://i.imgur.com/DegBUpj.png",fanart="http://i.imgur.com/bCn8lHB.jpg?1"))
    itemlist.append(Item(channel=__channel__, title="Canales Web/Html5", action="canales", url=host, thumbnail="http://i.imgur.com/DegBUpj.png",fanart="http://i.imgur.com/bCn8lHB.jpg?1"))

    return itemlist


def agendaglobal(item):
    itemlist = []
    try:
        item.channel = __channel__
        item.url = "http://www.elitegol.com"
        item.thumbnail="http://i.imgur.com/DegBUpj.png"
        item.fanart="http://i.imgur.com/bCn8lHB.jpg?1"
        itemlist = entradas(item)
        for item_global in itemlist:
            if item_global.action == "":
                itemlist.remove(item_global)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def canales(item):
    logger.info("deportesalacarta.channels.tugoleada canales")
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    bloque = scrapertools.find_single_match(data, '<ul class="dropdown-menu"(.*?)</ul>')
    patron = '<a href="([^"]+)">(.*?)</a>'
    matches = scrapertools.find_multiple_matches(bloque, patron)

    for scrapedurl, scrapedtitle  in matches:
        scrapedurl = host[:-1] + scrapedurl.replace("..", "")
        scrapedtitle = "[COLOR darkorange]"+scrapedtitle.strip()+"[/COLOR] [COLOR green]["+ \
                       item.title.replace('Canales ','')+"][/COLOR]"
        itemlist.append(Item(channel=__channel__, title=scrapedtitle, action="play", url=scrapedurl, thumbnail=item.thumbnail, fanart=item.fanart, folder=False))

    return itemlist


def entradas(item):
    logger.info("deportesalacarta.channels.tugoleada entradas")
    itemlist = []

    data = httptools.downloadpage(host).data
    bloque = scrapertools.find_single_match(data, '<div class="col-md-12">(.*?)</div>')
    try:
        matches = scrapertools.find_multiple_matches(bloque, '(?i)<p.*?>(?:<img.*?>|)(.*?CANAL\s*(\d+))</p>')
        for scrapedtitle, canal in matches:
            url = host + "canal" + canal
            scrapedtitle = "[COLOR green]%s[/COLOR]" % scrapedtitle
            itemlist.append(item.clone(title=scrapedtitle, url=url, action="play"))
    except:
        import traceback
        logger.info(traceback.format_exc())
        matches = []
        
    if not itemlist:
        matches = scrapertools.find_multiple_matches(data, 'src="(https://i.gyazo.com[^"]+)"')
        for i, imagen in enumerate(matches):
            title = "Agenda: Imagen " + str(i+1) +" (Click para agrandar)"
            itemlist.append(item.clone(title=title, url=imagen, thumbnail=imagen, action="abrir_imagen", folder=False))

    matches = scrapertools.find_multiple_matches(data, '(?i)<h1>([^<]+)</h1>')
    for title in matches:
        itemlist.append(item.clone(title=title, action="", folder=False))        


    return itemlist


def abrir_imagen(item):
    import xbmc
    return xbmc.executebuiltin('ShowPicture('+item.url+')')


def play(item):
    itemlist = []
    data = httptools.downloadpage(item.url, follow_redirects=False)
    if data.headers.get("refresh") or data.headers.get("location"):
        import urllib
        if data.headers.get("refresh"):
            url = scrapertools.find_single_match(data.headers["refresh"], '(?i)URL=(.*)')
        else:
            url = data.headers["location"]
        url = urllib.unquote_plus(url.replace("https://url.rw/?", ""))
        data = httptools.downloadpage(url, headers={'Referer': item.url}).data
        embedurl = scrapertools.find_single_match(data, "<iframe.*?src=\s*['\"]([^'\"]+)['\"]")
        data = httptools.downloadpage(embedurl, headers={'Referer': url}).data
    else:
        data = data.data

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0",
               "Referer": item.url}
    if "Web" in item.title:
        iframe = scrapertools.find_single_match(data, '<iframe.*?src="(http://tumarcador.xyz/red[^"]+)"')
        if iframe:
            data = httptools.downloadpage(iframe, headers=headers, replace_headers=True).data

        videourl = scrapertools.find_single_match(data, "(?:source:|source src=)\s*['\"]([^'\"]+)['\"]")
        if not videourl:
            baseurl, var_url, lasturl = scrapertools.find_single_match(data, 'return\(\[([^\[]+)\].*?\+\s*([A-z]+)\.join.*?"([^"]+)"\)\.innerHTML')
            auth = scrapertools.find_single_match(data, var_url+'\s*=\s*\[([^\[]+)\]')
            lasturl = scrapertools.find_single_match(data, lasturl+'\s*>\s*([^<]+)<')
            videourl = baseurl + auth + lasturl
            videourl = re.sub(r'"|,|\\', '', videourl)

        videourl += "|User-Agent=%s" % headers["User-Agent"]
        itemlist.append(Item(channel=__channel__, title=item.title, server="directo", url=videourl, action="play", folder=False))
    else:
        lista = servertools.findvideosbyserver(data, 'p2p')
        if lista:
            itemlist.append(Item(channel=__channel__, title=item.title, server="p2p", url=lista[0][1], action="play", folder=False))
    return itemlist
