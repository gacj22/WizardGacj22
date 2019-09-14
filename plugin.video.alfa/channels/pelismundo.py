# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Alfa addon - KODI Plugin
# Canal para pelismundo
# https://github.com/alfa-addon
# ------------------------------------------------------------

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger

host = "https://www.pelisvips.com"
idiomas = {"Castellano":"CAST","Subtitulad":"VOSE","Latino":"LAT"}

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel = item.channel, title = "Recientes", action = "peliculas", url = host))
    itemlist.append(Item(channel = item.channel, title = "Por audio", action = "filtro", url = host, filtro = "Películas por audio"))
    itemlist.append(Item(channel = item.channel, title = "Por género", action = "filtro", url = host, filtro = "Películas por género"))
    itemlist.append(Item(channel = item.channel))
    itemlist.append(Item(channel = item.channel, title = "Buscar", action = "search", url = host))
    return itemlist


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host
        elif categoria == 'infantiles':
            item.url = host + '/genero/infantil/'
        elif categoria == 'terror':
            item.url = host + '/genero/terror/'
        elif categoria == 'castellano':
            item.url = host +'/lenguaje/castellano/'
        elif categoria == 'latino':
            item.url = host +'/lenguaje/latino/'
        itemlist = peliculas(item)
        itemlist = peliculas(item)
        if "Pagina" in itemlist[-1].title:
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def search(item, texto):
    logger.info()
    item.url += "?s="
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    try:
        return sub_search(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def sub_search(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = 'search-results-content infinite.*?</ul>'
    bloque = scrapertools.find_single_match(data, patron)
    patron  = '(?s)href="([^"]+)".*?'
    patron += 'title="([^"]+)".*?'
    patron += 'src="([^"]+)".*?'
    patron += 'Idioma(.*?)Cal'
    patron += 'idad(.*?<)\/'
    match = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail, scrapedlanguages, scrapedquality in match:
        year = scrapertools.find_single_match(scrapedtitle, '[0-9]{4}')
        scrapedquality = scrapertools.find_single_match(scrapedquality, 'rel="tag">([^<]+)<')
        st = scrapertools.find_single_match(scrapedtitle, '(?i)Online.*')
        scrapedtitle = scrapedtitle.replace(st, "")
        st = scrapertools.find_single_match(scrapedtitle, '\(.*?\)')
        scrapedtitle = scrapedtitle.replace(st, "")
        title = scrapedtitle
        if year:
            title += "(" + year + ")"
        if scrapedquality:
            title += " (" + scrapedquality + ")"
        idiomas_disponibles = []
        idiomas_disponibles1 = ""
        for lang in idiomas.keys():
            if lang in scrapedlanguages:
                idiomas_disponibles.append(idiomas[lang])
        if idiomas_disponibles:
            idiomas_disponibles1 = "[" + "/".join(idiomas_disponibles) + "]"
        title += " %s" %idiomas_disponibles1
        itemlist.append(Item(channel = item.channel,
                             action = "findvideos",
                             title = title,
                             contentTitle = scrapedtitle,
                             thumbnail = scrapedthumbnail,
                             quality = scrapedquality,
                             language = idiomas_disponibles,
                             infoLabels={"year": year},
                             url = scrapedurl
                             ))
    tmdb.set_infoLabels(itemlist)
    url_pagina = scrapertools.find_single_match(data, 'next" href="([^"]+)')
    if url_pagina != "":
        pagina = "Pagina: " + scrapertools.find_single_match(url_pagina, "page/([0-9]+)")
        itemlist.append(Item(channel = item.channel, action = "peliculas", title = pagina, url = url_pagina))
    return itemlist

    
def filtro(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = 'class="sbi-header">%s.*?</ul>' %item.filtro
    bloque = scrapertools.find_single_match(data, patron)
    patron = '(?s)href="([^"]+)".*?'
    patron += '</span>([^<]+)</a>'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for url, title in matches:
        if "eroticas" in title and config.get_setting("adult_mode") == 0:
            continue
        logger.debug('la url: %s' %url)
        itemlist.append(item.clone(action = "peliculas",
                                   title = title.title(),
                                   url = url
                                   ))
    return itemlist

def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = 'movie-list" class="clearfix.*?pagination movie-pagination clearfix'
    bloque = scrapertools.find_single_match(data, patron)
    patron  = '(?s)href="([^"]+)".*?'
    patron += 'title="([^"]+)".*?'
    patron += 'class="mq([^"]+)".*?'
    patron += 'src="([^"]+)".*?'
    patron += '_audio(.*?)class.*?'
    patron += 'label_year">([^<]+)<'
    match = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedtitle, scrapedquality, scrapedthumbnail, scrapedlanguages, year in match:
        year = scrapertools.find_single_match(year, '[0-9]{4}')
        st = scrapertools.find_single_match(scrapedtitle, '(?i)Online.*')
        scrapedtitle = scrapedtitle.replace(st, "").strip()
        st = scrapertools.find_single_match(scrapedtitle, '\(.*?\)')
        scrapedtitle = scrapedtitle.replace(st, "")
        title = scrapedtitle
        if year:
            title += " (" + year + ")"
        if scrapedquality:
            title += " (" + scrapedquality + ")"
        idiomas_disponibles = []
        for lang in idiomas.keys():
            if lang in scrapedlanguages:
                idiomas_disponibles.append(idiomas[lang])
        idiomas_disponibles1 = ""
        if idiomas_disponibles:
            idiomas_disponibles1 = "[" + "/".join(idiomas_disponibles) + "]"
        title += " %s" %idiomas_disponibles1
        itemlist.append(Item(channel = item.channel,
                             action = "findvideos",
                             title = title,
                             contentTitle = scrapedtitle,
                             thumbnail = scrapedthumbnail,
                             quality = scrapedquality,
                             language = idiomas_disponibles,
                             infoLabels={"year": year},
                             url = scrapedurl
                             ))
    tmdb.set_infoLabels(itemlist)
    url_pagina = scrapertools.find_single_match(data, 'next" href="([^"]+)')
    if url_pagina != "":
        pagina = "Pagina: " + scrapertools.find_single_match(url_pagina, "page/([0-9]+)")
        itemlist.append(Item(channel = item.channel, action = "peliculas", title = pagina, url = url_pagina))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = 'SegundaParte.*?ventana-flotante'
    bloque = scrapertools.find_single_match(data, patron)
    patron  = 'hand" rel="([^"]+)".*?'
    patron += 'optxt"><span>([^<]+)</span>.*?'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedlanguage in matches:
        if "youtube" in scrapedurl:
            scrapedurl += "&"
        title = "Ver en: %s " + "(" + scrapedlanguage + ")"
        if "pelisvips.com" in scrapedurl :
            d1 = httptools.downloadpage(scrapedurl).data
            bloque = scrapertools.find_single_match( d1, 'sources.*?script')
            scrapedurl = scrapertools.find_single_match(bloque, "file': '([^']+)'")
        if "pelisup.com" in scrapedurl:
            id = scrapertools.find_single_match(scrapedurl, '.com/v/(\w+)')
            post = "r=&d=www.pelisup.com"
            d1 = httptools.downloadpage("https://www.pelisup.com/api/source/%s" %id, post=post).json
            d1 = d1["data"]
            for data in d1:
                title = "Ver en: %s " + "(" + data["label"] + ") (" + scrapedlanguage + ")"
                itemlist.append(item.clone(action = "play",
                                           title = title,
                                           language = scrapedlanguage,
                                           quality = item.quality,
                                           url = data["file"]
                                           ))
        else:
            itemlist.append(item.clone(action = "play",
                                       title = title,
                                       language = scrapedlanguage,
                                       quality = item.quality,
                                       url = scrapedurl
                                       ))
    tmdb.set_infoLabels(itemlist)
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    if itemlist and item.contentChannel != "videolibrary":
        itemlist.append(Item(channel = item.channel))
        itemlist.append(item.clone(channel="trailertools", title="Buscar Tráiler", action="buscartrailer", context="",
                                   text_color="magenta"))
        if config.get_videolibrary_support():
            itemlist.append(item.clone(title="Añadir a la videoteca", text_color="green",
                                 action="add_pelicula_to_library", url=item.url, contentTitle = item.contentTitle
                                 ))
    return itemlist


def play(item):
    item.thumbnail = item.contentThumbnail
    return [item]
