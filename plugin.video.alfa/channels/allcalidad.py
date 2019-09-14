# -*- coding: utf-8 -*-

from channelselector import get_thumb
from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger


IDIOMAS = {'Latino': 'Latino'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['rapidvideo', 'streamango', 'fastplay', 'flashx', 'openload', 'vimeo', 'netutv']


__channel__='allcalidad'

host = "https://allcalidad.net"

try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
except:
    __modo_grafico__ = True


def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []
    itemlist.append(Item(channel = item.channel, title = "Novedades", action = "peliculas", url = host, thumbnail = get_thumb("newest", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Por género", action = "generos_years", url = host, extra = "Genero", thumbnail = get_thumb("genres", auto = True) ))
    itemlist.append(Item(channel = item.channel, title = "Por año", action = "generos_years", url = host, extra = ">Año<", thumbnail = get_thumb("year", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Favoritas", action = "favorites", url = host + "/favorites", thumbnail = get_thumb("favorites", auto = True) ))
    itemlist.append(Item(channel = item.channel, title = ""))
    itemlist.append(Item(channel = item.channel, title = "Buscar", action = "search", url = host + "/?s=", thumbnail = get_thumb("search", auto = True)))
    autoplay.show_option(item.channel, itemlist)
    return itemlist

def favorites(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '(?s)short_overlay.*?<a href="([^"]+)'
    patron += '.*?img.*?src="([^"]+)'
    patron += '.*?title="([^"]+).*?'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url, thumbnail, titulo in matches:
        idioma = "Latino"
        mtitulo = titulo + " (" + idioma + ")"
        itemlist.append(item.clone(channel = item.channel,
                                   action = "findvideos",
                                   title = mtitulo,
                                   contentTitle = titulo,
                                   thumbnail = thumbnail,
                                   url = url,
                                   contentType="movie",
                                   language = idioma
                                   ))
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    url_pagina = scrapertools.find_single_match(data, 'next" href="([^"]+)')
    if url_pagina != "":
        pagina = "Pagina: " + scrapertools.find_single_match(url_pagina, "page/([0-9]+)")
        itemlist.append(Item(channel = item.channel, action = "peliculas", title = pagina, url = url_pagina))
    return itemlist


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas','latino']:
            item.url = host
        elif categoria == 'infantiles':
            item.url = host + '/category/animacion/'
        elif categoria == 'terror':
            item.url = host + '/category/torror/'
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
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    item.extra = "busca"
    if texto != '':
        return peliculas(item)
    else:
        return []


def generos_years(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '(?s)%s(.*?)</ul></div>' %item.extra
    bloque = scrapertools.find_single_match(data, patron)
    patron  = 'href="([^"]+)'
    patron += '">([^<]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for url, titulo in matches:
        if not url.startswith("http"): url = host + url
        itemlist.append(Item(channel = item.channel,
                             action = "peliculas",
                             title = titulo,
                             url = url
                             ))
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    matches = scrapertools.find_multiple_matches(data, '(?s)shortstory cf(.*?)rate_post')
    for datos in matches:
        url = scrapertools.find_single_match(datos, 'href="([^"]+)')
        titulo = scrapertools.find_single_match(datos, 'short_header">([^<]+)').strip()
        datapostid = scrapertools.find_single_match(datos, 'data-postid="([^"]+)')
        thumbnail = scrapertools.find_single_match(datos, 'img w.*?src="([^"]+)')
        post = 'action=get_movie_details&postID=%s' %datapostid
        data1 = httptools.downloadpage(host + "/wp-admin/admin-ajax.php", post=post).data
        idioma = "Latino"
        mtitulo = titulo + " (" + idioma + ")"
        year = scrapertools.find_single_match(data1, "Año:.*?(\d{4})")
        if year:
            mtitulo += " (" + year + ")"
            item.infoLabels['year'] = int(year)
        itemlist.append(item.clone(channel = item.channel,
                                   action = "findvideos",
                                   title = mtitulo,
                                   contentTitle = titulo,
                                   thumbnail = thumbnail,
                                   url = url,
                                   contentType="movie",
                                   language = idioma
                                   ))
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    url_pagina = scrapertools.find_single_match(data, 'next" href="([^"]+)')
    if url_pagina != "":
        pagina = "Pagina: " + scrapertools.find_single_match(url_pagina, "page/([0-9]+)")
        itemlist.append(Item(channel = item.channel, action = "peliculas", title = pagina, url = url_pagina))
    return itemlist


def findvideos(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, 'var data = {([^\}]+)}')
    action, dataurl = scrapertools.find_single_match(bloque, "(?is)action : '([^']+)'.*?postID, .*?(\w+) : dataurl")
    if not item.infoLabels["year"]:
        item.infoLabels["year"] = scrapertools.find_single_match(data, 'dateCreated.*?(\d{4})')
        if "orig_title" in data:
            contentTitle = scrapertools.find_single_match(data, 'orig_title.*?>([^<]+)<').strip()
            if contentTitle != "":
                item.contentTitle = contentTitle
    bloque = scrapertools.find_single_match(data, '(?s)<div class="bottomPlayer">(.*?)<script>')
    match = scrapertools.find_multiple_matches(bloque, '(?is)data-Url="([^"]+).*?data-postId="([^"]*)')
    for d_u, datapostid in match:
        page_url = host + "/wp-admin/admin-ajax.php"
        post = "action=%s&postID=%s&%s=%s" %(action, datapostid, dataurl, d_u)
        data = httptools.downloadpage(page_url, post=post).data
        url = scrapertools.find_single_match(data, '(?i)src="([^"]+)')
        titulo = "Ver en: %s"
        text_color = "white"
        if "goo.gl" in url:
            url = httptools.downloadpage(url, follow_redirects=False, only_headers=True).headers.get("location", "")
        if "youtube" in url:
            titulo = "Ver trailer: %s"
            text_color = "yellow"
        if "ad.js" in url or "script" in url or "jstags.js" in url or not datapostid:
            continue
        elif "vimeo" in url:
            url += "|" + "http://www.allcalidad.com"
        itemlist.append(
                 item.clone(channel = item.channel,
                 action = "play",
                 text_color = text_color,
                 title = titulo,
                 url = url
                 ))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if itemlist and item.contentChannel != "videolibrary":
        itemlist.append(Item(channel = item.channel))
        itemlist.append(item.clone(channel="trailertools", title="Buscar Tráiler", action="buscartrailer", context="",
                                   text_color="magenta"))
        # Opción "Añadir esta película a la biblioteca de KODI"
        if config.get_videolibrary_support():
            itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="green",
                                 action="add_pelicula_to_library", url=item.url, thumbnail = item.thumbnail,
                                 contentTitle = item.contentTitle
                                 ))
    return itemlist


def play(item):
    item.thumbnail = item.contentThumbnail
    return [item]
