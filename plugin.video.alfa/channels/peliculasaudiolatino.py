# -*- coding: utf-8 -*-

import re
import urlparse

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import logger, config

HOST = 'http://verpeliculasenlatino.com'


def mainlist(item):
    logger.info()

    itemlist = []
    itemlist.append(
        Item(channel=item.channel, title="Recién agregadas", action="peliculas", url=HOST + "/ultimas-agregadas.html",
             viewmode="movie"))
    itemlist.append(Item(channel=item.channel, title="Recién actualizadas", action="peliculas",
                         url=HOST + "/recien-actualizadas.html", viewmode="movie"))
    itemlist.append(
        Item(channel=item.channel, title="Las más vistas", action="peliculas", url=HOST + "/las-mas-vistas.html",
             viewmode="movie"))
    itemlist.append(Item(channel=item.channel, title="Listado por géneros", action="generos", url=HOST))
    itemlist.append(Item(channel=item.channel, title="Listado por años", action="anyos", url=HOST))
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search"))

    return itemlist


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas','latino']:
            item.url = HOST
        elif categoria == 'infantiles':
            item.url = HOST + '/genero/animacion.html'
        elif categoria == 'terror':
            item.url = HOST + '/genero/terror.html'
        itemlist = peliculas(item)
        if ">> Página siguiente" in itemlist[-1].title:
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def peliculas(item):
    logger.info()

    # Descarga la página
    data = httptools.downloadpage(item.url).data

    # Extrae las entradas de la pagina seleccionada
    patron = '<td><a href="([^"]+)"><img src="([^"]+)" class="[^"]+" alt="([^"]+)"'

    matches = re.compile(patron, re.DOTALL).findall(data)
    itemlist = []

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        url = urlparse.urljoin(item.url, scrapedurl)
        title = scrapedtitle.strip()
        thumbnail = urlparse.urljoin(item.url, scrapedthumbnail)
        plot = ""

        # Añade al listado
        itemlist.append(
            Item(channel=item.channel, action="findvideos", title=title, contentTitle=title, url=url, thumbnail=thumbnail,
                 plot=plot, folder=True))

    # Extrae la marca de siguiente página
    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)"><span class="icon-chevron-right">')
    if next_page != "":
        itemlist.append(Item(channel=item.channel, action="peliculas", title=">> Página siguiente",
                             url=urlparse.urljoin(item.url, next_page).replace("/../../", "/"), viewmode="movie",
                             folder=True))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    # Descarga la página
    data = httptools.downloadpage(item.url).data
    # Limita el bloque donde buscar
    data = scrapertools.find_single_match(data, '<table class="generos"(.*?)</table>')
    # Extrae las entradas
    matches = re.compile('<a href="([^"]+)">([^<]+)<', re.DOTALL).findall(data)
    for match in matches:
        scrapedurl = urlparse.urljoin(item.url, match[0])
        scrapedtitle = match[1].strip()
        scrapedthumbnail = ""
        scrapedplot = ""
        # logger.info(scrapedtitle)

        itemlist.append(Item(channel=item.channel, action="peliculas", title=scrapedtitle, url=scrapedurl,
                             thumbnail=scrapedthumbnail, plot=scrapedplot, folder=True, viewmode="movie"))

    itemlist = sorted(itemlist, key=lambda Item: Item.title)
    return itemlist


def anyos(item):
    logger.info()
    itemlist = []

    # Descarga la página
    data = httptools.downloadpage(item.url).data
    # Limita el bloque donde buscar
    data = scrapertools.find_single_match(data, '<table class="years"(.*?)</table>')
    # Extrae las entradas 
    matches = re.compile('<a href="([^"]+)">([^<]+)<', re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        url = urlparse.urljoin(item.url, scrapedurl)
        title = scrapedtitle
        thumbnail = ""
        plot = ""
        itemlist.append(
            Item(channel=item.channel, action="peliculas", title=title, url=url, thumbnail=thumbnail, plot=plot,
                 folder=True, viewmode="movie"))

    return itemlist


def search(item, texto):
    logger.info()
    itemlist = []

    texto = texto.replace(" ", "+")
    try:
        # Series
        item.url = HOST + "/busqueda.php?q=%s"
        item.url = item.url % texto
        item.extra = ""
        itemlist.extend(peliculas(item))
        itemlist = sorted(itemlist, key=lambda Item: Item.title)

        return itemlist

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def findvideos(item):
    logger.info()
    # Descarga la página

    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, '<div class="opciones">(.*?)<div id="sidebar"')

    title = item.title
    scrapedthumbnail = item.thumbnail
    itemlist = []

    patron = '<span class="infotx">([^<]+)</span></th[^<]+'
    patron += '<th align="left"><img src="[^"]+" width="\d+" alt="([^"]+)"[^<]+</th[^<]+'
    patron += '<th align="left"><img[^>]+>([^<]+)</th[^<]+'
    patron += '<th class="slink" align="left"><div id="btnp"><a href="[^"]+" onClick="[^h]+([^\']+)\''

    matches = re.compile(patron, re.DOTALL).findall(data)
    for servidor, idioma, calidad, scrapedurl in matches:
        url = scrapedurl
        server = servertools.get_server_name(servidor)
        title = "Enlace encontrado en %s" % (server)
        if idioma == 'Ingles Subtitulado':
            idioma = 'vose'
        itemlist.append(Item(channel=item.channel, action="play", title=title, contentTitle=item.contentTitle, url=url,
                             thumbnail=scrapedthumbnail, language=idioma, quality=calidad, server=server))
    if itemlist:
        itemlist.append(Item(channel=item.channel))
        itemlist.append(item.clone(channel="trailertools", title="Buscar Tráiler", action="buscartrailer",
                                   text_color="magenta"))
        # Opción "Añadir esta película a la biblioteca de KODI"
        if config.get_videolibrary_support():
            itemlist.append(Item(channel=item.channel, title="Añadir pelicula a la videoteca", text_color="green",
                                 action="add_pelicula_to_library", url=item.url, thumbnail=item.thumbnail,
                                 contentTitle=item.contentTitle))
    return itemlist


def play(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, 'src="(' + HOST + '/show/[^"]+)"')
    data = httptools.downloadpage(data, headers=[['User-Agent', 'Mozilla/5.0'], ['Accept-Encoding', 'gzip, deflate'],
                                                 ['Referer', HOST], ['Connection', 'keep-alive']]).data
    videoUrl = scrapertools.find_single_match(data, '(?i)<IFRAME.*?SRC="([^"]+)"')
    goo = scrapertools.find_single_match(videoUrl, '://([^/]+)/')
    if (goo == 'goo.gl'):
        videoUrl = httptools.downloadpage(videoUrl, follow_redirects=False, only_headers=True).headers["location"]
        server = scrapertools.find_single_match(videoUrl, '://([^/]+)/')
    # logger.info("videoUrl = "+videoUrl)
    enlaces = servertools.findvideos(videoUrl)
    if enlaces:
        thumbnail = servertools.guess_server_thumbnail(videoUrl)
        # Añade al listado de XBMC
        itemlist.append(
            Item(channel=item.channel, action="play", title=item.title, contentTitle=item.contentTitle, url=enlaces[0][1],
                 server=enlaces[0][2], thumbnail=thumbnail, folder=False))

    return itemlist
