# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para torrenttv
#------------------------------------------------------------
import urllib, re
import os

from core import httptools
from core import scrapertools
from core import logger
from core import config

from core.item import Item
from core import servertools
from core.scrapertools import decodeHtmlentities as dhe
import xbmc

__channel__ = "torrenttv"

host ="http://super-pomoyka.us.to/trash/ttv-list/ttv.m3u"
song=os.path.join(config.get_runtime_path(), 'music', 'Queen We Are The Champions.mp3')


def mainlist(item):
    logger.info("deportesalacarta.torrenttv mainlist")
    itemlist = []
    
    xbmc.executebuiltin('xbmc.PlayMedia('+song+')')
    itemlist.append(item.clone(title="Lista 1 (Super-pomoyka)", action="lista1", url=host))
    itemlist.append(item.clone(title="Lista 2 (Tuchkatv)", action="lista2", url="http://tuchkatv.ru/sportivnye/", thumbnail="http://tuchkatv.ru/templates/TuchkaTV/images/logo.png"))
    itemlist.append(item.clone(title="Lista 3 (Torrent-tv.org)", action="lista3", url="http://torrent-tv.org/browse-sport-videos-1-title.html"))
    itemlist.append(item.clone(title="Lista 4 (Torrent-tv.gr)", action="lista4", url="http://www.torrent-tv.gr/sport.php"))
    itemlist.append(item.clone(title="Lista 5 (Torrent-tv.ru)", action="lista5", url="http://torrent-tv.ru/category.php?cat=4", thumbnail="http://i.imgur.com/5Jk19Dl.jpg?1"))
    itemlist.append(item.clone(title="Lista 6 (Dvb-p)", action="lista6", url="http://dvb-p.com/es/live-tv/deportes-en-vivo-es/", thumbnail="http://dvb-p.com/wp/wp-content/themes/dvb-p/img/logo.png"))
    itemlist.append(item.clone(title="Lista 7 (Allfon.org)", action="lista7", url="http://allfon.org/", thumbnail="http://i.imgur.com/MDvaGZV.png"))
    
    return itemlist


def lista1(item):
    logger.info("deportesalacarta.torrenttv lista1")
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    patron = 'EXTINF.*?,(.*?) \((Спорт)\).*?(acestream.*?)#'
    matches = re.compile(patron,re.DOTALL).findall(data)
    
    for nombre,tipo, url  in matches:
        title = "[COLOR darkorange][B]"+nombre+"[/B][/COLOR]"
        
        if "acestream" in title:
           print "eliminado"
        else:
             itemlist.append( Item(channel=__channel__, title=title,action="play",url = url,thumbnail="http://s6.postimg.org/imesq7i4x/ttvlogo.png",fanart="http://s6.postimg.org/hy5y79jf5/Nike_soccer_wallpapers_HD_01_1280x720.jpg",fulltitle = title,folder=False) )

    return itemlist


def lista2(item):
    logger.info("deportesalacarta.torrenttv lista2")
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data += httptools.downloadpage("http://tuchkatv.ru/hd/sportivnye-hd/").data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    matches = scrapertools.find_multiple_matches(data, '<div class="maincont">(?:<div class="gray">|)<a href="([^"]+)"')
    urls = []
    for url in matches:
        urls.append(url)

    data = translate(item.url)
    data += translate("http://tuchkatv.ru/hd/sportivnye-hd/")

    patron = '(?i)<div class=maincont>(<div class=gray>|).*?<img (?:title="(.*?)\s*(?:online|Online|onine|").*?src=(.*?png)|src=(.*?png).*?title="(?:"|(.*?)\s*(?:online|Online|onine|")))'
    matches = scrapertools.find_multiple_matches(data, patron)
    i = 0
    for estado, title1, thumb1, thumb2, title2 in matches:
        if not title1:
            if not title2:
                title2 = thumb2.rsplit("/", 1)[1]
                title = scrapertools.find_single_match(title2, '_[\d]*(.*?).png')
            else:
                title = title2
            thumb = "http://tuchkatv.ru" + thumb2
        else:
            title = title1
            thumb = thumb1
        title = re.sub(r"(?i)see |watch |channel ", "", title).capitalize()
        if estado:
            scrapedtitle = "[COLOR red]" + title + "[/COLOR]"
        else:
            scrapedtitle = "[COLOR green]" + title + "[/COLOR]"
        scrapedtitle = scrapertools.htmlclean(scrapedtitle)
        itemlist.append(item.clone(title=scrapedtitle, action="play", url=urls[i], thumbnail=thumb, fulltitle=title, extra="lista2"))
        i += 1

    itemlist.sort(key=lambda item: item.fulltitle)

    return itemlist


def lista3(item):
    logger.info("deportesalacarta.torrenttv lista3")
    itemlist = []

    data = translate(item.url)

    patron = '<span class=pm-video-li-thumb-info>.*?href=.*?u=(.*?)&usg.*?src=([^\s]+) alt="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        scrapedtitle = "[COLOR darkorange]" + scrapedtitle + "[/COLOR]"
        itemlist.append(item.clone(title=scrapedtitle, action="play", url=scrapedurl, thumbnail=scrapedthumbnail, fulltitle=scrapedtitle, extra="lista3"))

    return itemlist


def lista4(item):
    logger.info("deportesalacarta.torrenttv lista4")
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '<div class="playlist-item" tId="([^"]+)">.*?>(.*?)</a>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle in matches:
        scrapedurl = "acestream://" + scrapedurl
        scrapedtitle = "[COLOR darkorange]" + scrapedtitle + "[/COLOR]"
        itemlist.append(item.clone(title=scrapedtitle, action="play", url=scrapedurl, fulltitle=scrapedtitle))

    return itemlist


def lista5(item):
    logger.info("deportesalacarta.torrenttv lista5")
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '<div class="best-channels-content".*?href="([^"]+)".*?src="([^"]+)".*?<strong>\s*(.*?)\s+</strong>.*?src="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, thumb_logo, scrapedtitle, scrapedthumbnail  in matches:
        if "no_cadre.jpg" in scrapedthumbnail:
            scrapedthumbnail = "http://torrent-tv.ru/" + thumb_logo

        scrapedurl = "http://torrent-tv.ru/" + scrapedurl
        scrapedtitle = "[COLOR darkorange]" + scrapedtitle + "[/COLOR]"
        itemlist.append(item.clone(title=scrapedtitle, action="play", url=scrapedurl, fulltitle=scrapedtitle, thumbnail=scrapedthumbnail, extra="lista5"))

    return itemlist


def lista6(item):
    logger.info("deportesalacarta.torrenttv lista6")
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = "checkEngineVersion\(\s*'([^']+)', '([^']+)'"
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedtitle, scrapedurl  in matches:
        scrapedurl = "acestream://" + scrapedurl
        scrapedtitle = "[COLOR darkorange]" + scrapedtitle + "[/COLOR]"
        itemlist.append(item.clone(title=scrapedtitle, action="play", url=scrapedurl, fulltitle=scrapedtitle))

    itemlist.sort(key=lambda item: item.title)
    return itemlist


def lista7(item):
    logger.info("deportesalacarta.torrenttv lista7")
    itemlist = []

    data = translate(item.url)
    
    bloque = scrapertools.find_multiple_matches(data,'<article>(.*?)</article>')[-1]
    patron = 'href=.*?u=(.*?)&usg.*?src=(?:"|)([^\s"]+)(?:"|) alt="[^"]+" title="([^"]+)"'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        scrapedurl = urllib.unquote(scrapedurl.replace("https", "http"))
        scrapedthumbnail = "http://allfon.org"+scrapedthumbnail
        scrapedtitle = "[COLOR darkorange]" + scrapedtitle + "[/COLOR]"
        itemlist.append(item.clone(title=scrapedtitle, action="play", url=scrapedurl, thumbnail=scrapedthumbnail, fulltitle=scrapedtitle, extra="lista7"))

    return itemlist


def play(item):
    logger.info("deportesalacarta.torrenttv go")
    itemlist = []
    xbmc.executebuiltin('xbmc.PlayMedia(Stop)')
    fulltitle = item.fulltitle
    if item.extra == "":
        # Se incluye el título en la url para pasarlo al conector
        url= item.url + "|" + fulltitle
        itemlist.append(Item(channel=__channel__, title=item.title, server="p2p", url=url, action="play", folder=False))
    else:
        data = httptools.downloadpage(item.url).data
        if item.extra == "lista3":
            iframe = scrapertools.find_single_match(data, '<iframe src="([^"]+)"')
            data = httptools.downloadpage(iframe).data

        urls = servertools.findvideosbyserver(data, "p2p")
        if urls:
            url = urls[0][1] + "|" + fulltitle
            itemlist.append(Item(channel=__channel__, title=item.title, server="p2p", url=url, action="play", folder=False))
    
    return itemlist


def translate(url_translate):
    #### Opción 1: 'follow_redirects=False'
    ## Petición 1
    url = "http://translate.google.com/translate?depth=1&nv=1&rurl=translate.google.com&sl=ru&tl=en&u=" + url_translate
    data = dhe(httptools.downloadpage(url, follow_redirects=False).data)
    ## Petición 2
    url = scrapertools.get_match(data, ' src="([^"]+)" name=c ')
    data = dhe(httptools.downloadpage(url, follow_redirects=False).data)
    ## Petición 3
    url = scrapertools.get_match(data, 'URL=([^"]+)"')
    data = dhe(httptools.downloadpage(url).data)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    
    return data
