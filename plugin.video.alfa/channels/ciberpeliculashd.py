# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb
__channel__='ciberpeliculashd'

host = "http://ciberpeliculashd.net"

try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
except:
    __modo_grafico__ = True


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel = item.channel, title = "Películas", text_bold = True, folder = False))
    itemlist.append(Item(channel = item.channel, title = "   Novedades", action = "peliculas", url = host + "/?peli=1",
                         thumbnail=get_thumb('newest', auto=True)))
    itemlist.append(Item(channel = item.channel, title = "   Por género", action = "filtro", url = host,
                         extra = "categories", thumbnail=get_thumb('genres', auto=True)))
    itemlist.append(Item(channel = item.channel, title = "   Por calidad", action = "filtro", url = host,
                         extra = "qualitys", thumbnail=get_thumb('quality', auto=True)))
    itemlist.append(Item(channel = item.channel, title = "   Por idioma", action = "filtro", url = host,
                         extra = "languages", thumbnail=get_thumb('language', auto=True)))
    itemlist.append(Item(channel = item.channel, title = "   Por año", action = "filtro", url = host,
                         extra = "years", thumbnail=get_thumb('year', auto=True)))
    itemlist.append(Item(channel = item.channel, title = ""))
    itemlist.append(Item(channel = item.channel, title = "Series", text_bold = True, folder = False))
    itemlist.append(Item(channel = item.channel, title = "   Novedades", action = "series",
                         url = host +"/series/?peli=1", thumbnail=get_thumb('newest', auto=True)))
    itemlist.append(Item(channel = item.channel, title = ""))
    itemlist.append(Item(channel = item.channel, title = "Buscar", action = "search", url = host + "/?s=",
                         thumbnail=get_thumb('search', auto=True)))
    return itemlist


def series(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, 'loop-posts series.*?panel-pagination pagination-bottom')
    patron  = 'a href="([^"]+).*?'
    patron += '((?:http|https)://image.tmdb.org[^"]+).*?'
    patron += 'title="([^"]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        itemlist.append(Item(action = "capitulos",
                             channel = item.channel,
                             thumbnail = scrapedthumbnail,
                             title = scrapedtitle,
                             contentSerieName = scrapedtitle,
                             url = scrapedurl
                             ))
    if itemlist:
        tmdb.set_infoLabels(itemlist)
        page = int(scrapertools.find_single_match(item.url,"peli=([0-9]+)")) + 1
        next_page = scrapertools.find_single_match(item.url,".*?peli=")
        next_page += "%s" %page
        itemlist.append(Item(action = "series",
                             channel = item.channel,
                             title = "Página siguiente >>",
                             url = next_page
                             ))
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    itemlist = capitulos(item)
    return itemlist


def capitulos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, 'Lista de Temporadas.*?Content principal')
    patron  = '<a href="([^"]+).*?'
    patron += '<span>(.*?)</span>'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapedtitle.strip()
        s_e = scrapertools.get_season_and_episode(scrapedurl.replace("-",""))
        if s_e != "":
            season = s_e.split("x")[0]
            episode = s_e.split("x")[1]
        else:
            season = episode = ""
        scrapedtitle = s_e + " - " + scrapedtitle
        item.infoLabels["episode"] = episode
        item.infoLabels["season"] = season
        itemlist.append(item.clone(action = "findvideos",
                             title = scrapedtitle,
                             url = scrapedurl
                             ))
    tmdb.set_infoLabels(itemlist)
    if config.get_videolibrary_support():
        itemlist.append(Item(channel=item.channel, title =""))
        itemlist.append(item.clone(action = "add_serie_to_library",
                             channel = item.channel,
                             extra = "episodios",
                             title = '[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                             url = item.url
                             ))
    return itemlist


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas','latino']:
            item.url = host + "/?peli=1"
        elif categoria == 'infantiles':
            item.url = host + '/categories/animacion/?peli=1'
        elif categoria == 'terror':
            item.url = host + '/categories/terror/?peli=1'
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
    item.url = item.url + texto + "&peli=1"
    item.extra = "busca"
    if texto != '':
        return peliculas(item)
    else:
        return []


def filtro(item):
    logger.info()
    itemlist = []
    filter = ""
    filter_end = "data-uk-dropdown"
    if item.extra == "categories":
        filter = "genero"
    elif item.extra == "qualitys":
        filter = "calidad"
    elif item.extra == "languages":
        filter = "audio"
    elif item.extra == "years":
        filter = "ano"
        filter_end = "<div style"
    filter = host + "/?" + filter + "="
    data = httptools.downloadpage(item.url).data
    patron = 'uk-button btn-filter %s.*?%s' %(item.extra, filter_end)
    bloque = scrapertools.find_single_match(data, patron)
    patron  = 'id="([^"]+).*?'
    patron += 'label for.*?>([^<]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for url, titulo in matches:
        url = filter + url
        itemlist.append(Item(channel = item.channel,
                             action = "peliculas",
                             title = titulo,
                             url = url + "&peli=1"
                             ))
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    infoLabels = dict()
    filter = "uk-icon-angle-right next"
    if item.extra == "busca":
        filter = '<div class="post">'
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, '%s.*?panel-pagination pagination-bottom' %(filter))
    patron  = 'a href="([^"]+)".*?'
    patron += 'img alt="([^"]+)".*?'
    patron += '((?:http|https)://image.tmdb.org[^"]+)".*?'
    patron += 'a href="([^"]+)".*?'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail, scrapedurl1 in matches:
        scrapedtitle = scrapedtitle.replace(" Online imagen","").replace("Pelicula ","")
        year = scrapertools.find_single_match(scrapedtitle, "\(([0-9]+)\)")
        if year:
            year = int(year)
        else:
            year = 0
        contentTitle = scrapertools.find_single_match(scrapedtitle, "(.*?) \(")
        if "serie" in scrapedurl:
            action = "capitulos"
            infoLabels ['tvshowtitle'] = scrapedtitle
        else:
            action = "findvideos"
            infoLabels ['tvshowtitle'] = ""
        infoLabels ['year'] = year
        itemlist.append(Item(action = action,
                             channel = item.channel,
                             contentTitle = contentTitle,
                             thumbnail = scrapedthumbnail,
                             infoLabels = infoLabels,
                             title = scrapedtitle,
                             url = scrapedurl
                             ))
    if itemlist:
        tmdb.set_infoLabels(itemlist)
        page = int(scrapertools.find_single_match(item.url,"peli=([0-9]+)")) + 1
        next_page = scrapertools.find_single_match(item.url,".*?peli=")
        next_page += "%s" %page
        itemlist.append(Item(action = "peliculas",
                             channel = item.channel,
                             title = "Página siguiente >>",
                             url = next_page
                             ))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '(?i)src=&quot;([^&]+)&'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl in matches:
        if ".gif" in scrapedurl:
            continue
        title = "Ver en: %s"
        itemlist.append(item.clone(action = "play",
                                   title = title,
                                   url = scrapedurl
                                   ))
    tmdb.set_infoLabels(itemlist)
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    if itemlist:
        itemlist.append(Item(channel = item.channel))
        itemlist.append(item.clone(channel="trailertools", title="Buscar Tráiler", action="buscartrailer", context="",
                                   text_color="magenta"))
        # Opción "Añadir esta película a la videoteca de KODI"
        if item.contentChannel != "videolibrary":
            if config.get_videolibrary_support():
                itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="green",
                                     action="add_pelicula_to_library", url=item.url, thumbnail = item.thumbnail,
                                     contentTitle = item.contentTitle
                                     ))
    return itemlist


def play(item):
    item.thumbnail = item.contentThumbnail
    return [item]
