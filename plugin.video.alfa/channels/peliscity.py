# -*- coding: utf-8 -*-

import re
import urllib

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger

host = "https://www.pelisvips.com"

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Ultimas", action="agregadas",
                         url= host, viewmode="movie_with_plot", thumbnail = get_thumb("last", auto = True)))
    itemlist.append(Item(channel=item.channel, title="Género", action="porGenero_Idioma", tipo = "g", url= host, thumbnail = get_thumb("genres", auto = True)))
    itemlist.append(Item(channel=item.channel, title="Audio", action="porGenero_Idioma", tipo = "a", url= host, thumbnail = get_thumb("audio", auto = True)))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url= host + "/?s=", thumbnail = get_thumb("search", auto = True)))

    return itemlist


def porGenero_Idioma(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, 'culas por %s(.*?)slidebar-item' %item.tipo)
    patron = 'href="([^"]+).*?span>([^<]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for urlgen, titulo in matches:
        itemlist.append(Item(channel=item.channel, action="agregadas", title=titulo, url=urlgen, folder=True,
                             viewmode="movie_with_plot"))

    return itemlist


def search(item, texto):
    logger.info()
    texto_post = texto.replace(" ", "+")
    item.url = host + "/?s=" + texto_post
    try:
        return listaBuscar(item)
    # Se captura la excepcion, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def listaBuscar(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<li class="itemlist".*?href="([^"]+)".*?'
    patron += 'src="([^"]+)".*?'
    patron += 'title="([^"]+)".*?'
    patron += 'text-list">([^<]+)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url, thumbnail, title, sinopsis in matches:
        itemlist.append(Item(channel=item.channel, action="findvideos", title=title + " ", contentTitle=title, url=url,
                             thumbnail=thumbnail, show=title, plot=sinopsis))
    return itemlist


def agregadas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, '<div id="movie-list"(.*?)<div class="pagination movie-pagination')
    patron  = '(?is)href="([^"]+)".*?'
    patron += 'class="_format"> <span class=".*?>([^<]+)<.*?'
    patron += 'src="([^"]+)".*?'
    patron += 'alt="([^"]+)".*?'
    patron += '<div class="_audio">(.*?)/div.*?'
    patron += 'label_year">([^ ]+) '
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedquality, scrapedthumbnail, scrapedtitle, scrapedaudio, scrapedyear in matches:
        title = scrapedtitle + " (%s)" %scrapedyear
        itemlist.append(Item(channel = item.channel,
                             action = 'findvideos',
                             contentTitle = scrapedtitle,
                             infoLabels = {'year':scrapedyear},
                             quality = scrapedquality,
                             thumbnail = scrapedthumbnail,
                             title = title,
                             url = scrapedurl
                             ))
    tmdb.set_infoLabels(itemlist, True)
    next_page = scrapertools.find_single_match(data, "next'.*?href='([^']+)'")
    itemlist.append(Item(channel=item.channel, action="agregadas", title='Pagina Siguiente >>',
                         url=next_page.strip(),
                         viewmode="movie_with_plot"))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    # Descarga la pagina
    data = httptools.downloadpage(item.url).data
    patron = 'cursor: hand" rel="(.*?)".*?class="optxt"><span>(.*?)<.*?width.*?class="q">(.*?)</span'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedidioma, scrapedcalidad in matches:
        title = "%s [" + scrapedcalidad + "][" + scrapedidioma +"]"
        quality = scrapedcalidad
        language = scrapedidioma
        if "pelisup.com" in scrapedurl:
            scrapedurl = scrapedurl.replace("/v/","/api/source/")
            post = urllib.urlencode({"r":item.url,"d":"www.pelisup.com"})
            json_data = httptools.downloadpage(scrapedurl, post=post).json
            for dataj in json_data["data"]:
                itemlist.append(
                    item.clone(channel=item.channel, action="play", title=title + " - %s" %dataj["label"], contentTitle=item.title, url="https://www.pelisup.com" + dataj["file"],
                         quality= quality, language=language, extra = item.thumbnail))
            scrapedurl = "omina.farlante1"  # para ya no agregar al itemlist
        if not ("omina.farlante1" in scrapedurl or "404" in scrapedurl):
            itemlist.append(
                item.clone(channel=item.channel, action="play", title=title, contentTitle=item.title, url=scrapedurl,
                     quality= quality, language=language, extra = item.thumbnail))
    tmdb.set_infoLabels(itemlist, True)
    itemlist=servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # Opción "Añadir esta película a la biblioteca de KODI"
    if itemlist and item.contentChannel != "videolibrary":
        if config.get_videolibrary_support():
            itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="green",
                                 action="add_pelicula_to_library", url=item.url, thumbnail = item.thumbnail,
                                 contentTitle=item.title
                                 ))
    return itemlist


def play(item):
    logger.info()
    item.thumbnail = item.extra
    return [item]

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host

        elif categoria == 'documentales':
            item.url = host + "/genero/documental/"

        elif categoria == 'infantiles':
            item.url = host + "/genero/animacion/"

        elif categoria == 'terror':
            item.url = host + "/genero/terror/"

        elif categoria == 'castellano':
            item.url = host + "/idioma/espanol-castellano/"

        elif categoria == 'latino':
            item.url = host + "/idioma/espanol-latino/"

        itemlist = agregadas(item)

        if itemlist[-1].action == "agregadas":
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

