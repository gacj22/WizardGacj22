# -*- coding: utf-8 -*-

import re
import urlparse

from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core import tmdb
from channels import autoplay
from platformcode import config, logger

HOST = 'http://seriesdanko.to/'
IDIOMAS = {'es': 'Español', 'la': 'Latino', 'vos': 'VOS', 'vo': 'VO'}
list_idiomas = IDIOMAS.values()
list_servers = ['streamcloud', 'powvideo', 'gamovideo', 'streamplay', 'openload', 'flashx', 'nowvideo', 'thevideo']
list_quality = ['SD', 'MicroHD', 'HD/MKV']



def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="Novedades", action="novedades", url=HOST))
    itemlist.append(Item(channel=item.channel, title="Más vistas", action="mas_vistas", url=HOST))
    itemlist.append(Item(channel=item.channel, title="Listado Alfabético", action="listado_alfabetico", url=HOST))
    itemlist.append(Item(channel=item.channel, title="Todas las series", action="listado_completo", url=HOST))
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search",
                         url=urlparse.urljoin(HOST, "all.php")))

    itemlist = filtertools.show_option(itemlist, item.channel, list_idiomas, list_quality)

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def newest(categoria):
    logger.info("categoria: %s" % categoria)
    itemlist = []

    if categoria == 'series':
        itemlist = novedades(Item(url = HOST))

    return itemlist

def novedades(item):
    logger.info()

    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|<Br>|<BR>|<br>|<br/>|<br />|-\s", "", data)
    data = re.sub(r"<!--.*?-->", "", data)
    data = scrapertools.find_single_match(data, "<div class='main section' id='main'>(.*?)</ul>")
    patron = "<div class='post-header'>(.*?)</span>"
    matches = re.compile(patron, re.DOTALL).findall(data)

    for serie_data in matches:
        scrapedtitle = scrapertools.find_single_match(serie_data, "title='([^']+)'")
        scrapedurl = scrapertools.find_single_match(serie_data, 'href="([^"]+)"')
        scrapedthumb = scrapertools.find_single_match(serie_data, "src='([^']+)'")
        title = scrapertools.decodeHtmlentities(scrapedtitle)
        language=''
        title = title.replace ('Disponible','')
        title = title.replace('Ya', '')
        title = title.strip()

        show = scrapertools.find_single_match(title, "^(.+?) \d+[x|X]\d+")

        itemlist.append(Item(channel=item.channel, title=title, url=urlparse.urljoin(HOST, scrapedurl), show=show,
                             action="episodios", thumbnail=scrapedthumb,
                             context=filtertools.context(item, list_idiomas, list_quality), language=language))

    return itemlist


def mas_vistas(item):
    logger.info()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|<Br>|<BR>|<br>|<br/>|<br />|-\s", "", data)
    data = re.sub(r"<!--.*?-->", "", data)
    patron = "<div class='widget HTML' id='HTML3'.+?<div class='widget-content'>(.*?)</div>"
    data = scrapertools.find_single_match(data, patron)
    item.data = data
    item.first = 0
    return series_seccion(item)


def listado_completo(item):
    logger.info()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|<Br>|<BR>|<br>|<br/>|<br />|-\s", "", data)
    data = re.sub(r"<!--.*?-->", "", data)
    patron = '<div class="widget HTML" id="HTML10".+?<div class="widget-content">(.*?)</div>'
    data = scrapertools.find_single_match(data, patron)
    item.first = 0
    item.data = data
    return series_seccion(item)


def series_seccion(item):
    logger.info()

    itemlist = []
    next_page = ''
    data = item.data
    data = data.replace('ahref', 'a href')
    patron = "<a href='([^']+)'.*?>(.*?)</a>"
    matches = re.compile(patron, re.DOTALL).findall(data)
    if int(item.first)+20 < len(matches):
        limit = int(item.first)+20
        next_page = limit + 1
    else:
        limit = len(matches)
    for scrapedurl, scrapedtitle in matches[item.first:limit]:
        itemlist.append(Item(channel=item.channel, action="episodios", title=scrapedtitle, show=scrapedtitle,
                             url=urlparse.urljoin(HOST, scrapedurl),
                             context=filtertools.context(item, list_idiomas, list_quality)))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    #pagination

    if next_page !='':
        itemlist.append(Item(channel=item.channel, action="series_seccion", title='Siguiente >>>', data=item.data,
        first=next_page))

    return itemlist


def listado_alfabetico(item):
    logger.info()

    itemlist = []

    for letra in '0ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        itemlist.append(Item(channel=item.channel, action="series_por_letra", title=letra,
                             url=urlparse.urljoin(HOST, "series.php?id=%s" % letra)))

    return itemlist



def series_por_letra(item):
    logger.info("letra = {0}".format(item.title))
    data = httptools.downloadpage(item.url).data

    shows = re.findall("<a href='(?P<url>[^']+)' title='Capitulos de: (?P<title>.+?)'><img.+?src='(?P<img>[^']+)", data)
    itemlist = []
    for url, title, img in shows:
        itemlist.append(item.clone(title=title, url=urlparse.urljoin(HOST, url), action="episodios", thumbnail=img,
                                   show=title, context=filtertools.context(item, list_idiomas, list_quality)))
    return itemlist


def search(item, texto):
    logger.info("texto=%s" % texto)

    itemlist = []

    try:
        data = httptools.downloadpage(item.url).data
        shows = re.findall("<a href='(?P<url>/serie.php\?serie=[0-9]+)'[^>]*>(?P<title>[^<]*{0}[^<]*)".format(texto),
                           data, re.IGNORECASE)
        for url, title in shows:
            itemlist.append(item.clone(title=title, url=urlparse.urljoin(HOST, url), action="episodios", show=title,
                                       context=filtertools.context(item, list_idiomas, list_quality)))

        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)

    return itemlist


def episodios(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|<Br>|<BR>|<br>|<br/>|<br />|-\s", "", data)
    data = re.sub(r"<!--.*?-->", "", data)

    data = re.sub(r"a> <img src=/assets/img/banderas/", "a><idioma>", data)
    data = re.sub(r"<img src=/assets/img/banderas/", "|", data)
    data = re.sub(r"\.png border='\d+' height='\d+' width='\d+'[^>]+>\s+<", "</idioma><", data)
    data = re.sub(r"\.png border='\d+' height='\d+' width='\d+'[^>]+>", "", data)

    patron = '<div id="T1".*?'
    patron += "<img src='([^']+)'"
    matches = re.compile(patron, re.DOTALL).findall(data)
    if len(matches) > 0:
        thumbnail = matches[0]
    else:
        thumbnail = item.thumbnail

    patron = "<a href='([^']+)'>(.*?)</a><idioma>(.*?)</idioma>"
    matches = re.compile(patron, re.DOTALL).findall(data)

    infoLabels = item.infoLabels
    for scrapedurl, scrapedtitle, scrapedidioma in matches:
        idioma = ""
        filter_langs = []
        for i in scrapedidioma.split("|"):
            idioma += " [" + IDIOMAS.get(i, "OVOS") + "]"
            filter_langs.append(IDIOMAS.get(i, "OVOS"))
        season_episode = scrapertools.get_season_and_episode(scrapedtitle)
        title = '%s %s %s' % (season_episode, scrapedtitle, idioma)
        season_episode = season_episode.split('x')
        infoLabels['season'] = season_episode[0]
        infoLabels['episode'] = season_episode[1]


        itemlist.append(Item(channel=item.channel, title=title, url=urlparse.urljoin(HOST, scrapedurl),
                             action="findvideos", show=item.show, thumbnail=thumbnail, plot="", language=filter_langs,
                             infoLabels=infoLabels))


    itemlist = filtertools.get_links(itemlist, item, list_idiomas, list_quality)
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Opción "Añadir esta serie a la videoteca de XBMC"
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(item.clone(title="Añadir esta serie a la videoteca", action="add_serie_to_library",
                                   extra="episodios"))

    return itemlist


def findvideos(item):
    logger.info()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|<Br>|<BR>|<br>|<br/>|<br />|-\s", "", data)
    data = re.sub(r"<!--.*?-->", "", data)

    online = re.findall('<table class=.+? cellpadding=.+? cellspacing=.+?>(.+?)</table>', data,
                        re.MULTILINE | re.DOTALL)

    itemlist = []

    try:
        filtro_enlaces = config.get_setting("filterlinks", item.channel)
    except:
        filtro_enlaces = 2


    if filtro_enlaces != 0:
        itemlist.extend(parse_videos(item, "Ver", online[0]))

    if filtro_enlaces != 1:
        itemlist.extend(parse_videos(item, "Descargar", online[1]))


    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_idiomas, list_quality)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist


def parse_videos(item, tipo, data):
    logger.info()

    itemlist = []

    pattern = "<td.+?<img src='/assets/img/banderas/([^\.]+).+?</td><td.+?>(.*?)</td><td.+?" \
              "<img src='/assets/img/servidores/([^\.]+).+?</td><td.+?href='([^']+)'.+?>.*?</a></td>" \
              "<td.+?>(.*?)</td>"

    links = re.findall(pattern, data, re.MULTILINE | re.DOTALL)

    for language, date, server, link, quality in links:

        if quality == "":
            quality = "SD"
        title = "%s en %s [%s] [%s] (%s)" % (tipo, server, IDIOMAS.get(language, "OVOS"), quality, date)

        itemlist.append(Item(channel=item.channel, title=title, url=urlparse.urljoin(HOST, link), action="play",
                             show=item.show, language=IDIOMAS.get(language, "OVOS"), quality=quality,
                             contentTitle=item.title, server=server))

    return itemlist


def play(item):
    logger.info("play url=%s" % item.url)

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|<Br>|<BR>|<br>|<br/>|<br />|-\s", "", data)
    #patron = '<div id="url2".*?><a href="([^"]+)">.+?</a></div>'
    patron = '<a target="_blank" href="(.*?)">'
    url = scrapertools.find_single_match(data, patron)

    itemlist = servertools.find_video_items(data=url)
    titulo = scrapertools.find_single_match(item.contentTitle, "^(.*?)\s\[.+?$")
    if titulo:
        titulo += " [%s]" % item.language

    for videoitem in itemlist:
        if titulo:
            videoitem.title = titulo
        else:
            videoitem.title = item.title
        videoitem.channel = item.channel

    return itemlist
