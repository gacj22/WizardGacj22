# -*- coding: utf-8 -*-
# -*- Channel Yape -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

from channelselector import get_thumb
from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger, platformtools


idio = {'https://cdn.yape.nu//languajes/la.png': 'LAT','https://cdn.yape.nu//languajes/es.png': 'ESP','https://cdn.yape.nu//languajes/en_es.png': 'VOSE'}
cali = {'TS Screnner': 'TS Screnner', 'HD 1080p': 'HD 1080p','TS Screener HQ':'TS Screener HQ', 'BR Screnner':'BR Screnner','HD Rip':'HD Rip','DVD Screnner':'DVD Screnner', 'DVD Rip':'DVD Rip', 'HD 720':'HD 720'}

list_language = idio.values()
list_quality = cali.values()
list_servers = ['streamango', 'powvideo', 'openload', 'streamplay', 'vidoza', 'clipwaching']


__channel__='yape'

host = "https://yape.nu"

try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
except:
    __modo_grafico__ = True


def mainlist(item):
    logger.info()
    data = httptools.downloadpage(host + "/catalogue?sort=latest").data
    total = scrapertools.find_single_match(data, 'class="font-weight-bold mr-2">([^<]+)')
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []
    itemlist.append(Item(channel = item.channel, title = "Actualizadas", action = "peliculas", url = host + "/catalogue?sort=time_update&page=", page=1, thumbnail = get_thumb("updated", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Mas vistas", action = "peliculas", url = host + "/catalogue?sort=mosts-today&page=", page=1, thumbnail = get_thumb("more watched", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Ultimas agregadas - (Total películas: %s)" %total, action = "peliculas", url = host + "/catalogue?sort=latest&page=", page=1, thumbnail = get_thumb("last", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Por género", action = "generos", url = host, extra = "Genero", thumbnail = get_thumb("genres", auto = True) ))
    itemlist.append(Item(channel = item.channel, title = ""))
    itemlist.append(Item(channel = item.channel, title = "Buscar", action = "search", url = host + "/search?term=", thumbnail = get_thumb("search", auto = True)))
    itemlist.append(item.clone(title="Configurar canal...", text_color="gold", action="configuracion", folder=False))
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def configuracion(item):
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


def search(item, texto):
    logger.info()
    item.url = host + "/search?s=%s&page=" %texto
    item.extra = "busca"
    item.page = 1
    if texto != '':
        return peliculas(item)
    else:
        return []


def peliculas(item):
    logger.info()
    itemlist = []
    url = item.url + str(item.page)
    data = httptools.downloadpage(url).data
    patron  = 'class="col-lg-2 col-md-3 col-6 mb-3">.*?href="([^"]+).*?'
    patron += 'title="([^"]+).*?'
    patron += 'src="([^"]+).*?'
    patron += 'txt-size-13">([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail, scrapedyear in matches:
        scrapedtitle = scrapedtitle.replace("Ver ","").replace(" Completa Online Gratis","")
        itemlist.append(Item(channel = item.channel,
                             action = "findvideos",
                             contentTitle = scrapedtitle,
                             infoLabels = {'year':scrapedyear},
                             thumbnail = scrapedthumbnail,
                             title = scrapedtitle + " (%s)" %scrapedyear,
                             url = scrapedurl
                             ))
    tmdb.set_infoLabels(itemlist)
    #pagination
    if len(itemlist)>0:
        itemlist.append(Item(channel = item.channel,
                             action = "peliculas",
                             page = item.page + 1,
                             title = "Página siguiente >>",
                             url = item.url
                             ))
    return itemlist
    
    
def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas','latino']:
            item.url = host + "/catalogue?sort=latest?page="
            item.page=1
        elif categoria == 'infantiles':
            item.url = host + '/genre/animacion?page'
            item.page = 1
        elif categoria == 'terror':
            item.url = host + 'genre/terror?page='
            item.page = 1
        itemlist = peliculas(item)
        if "Pagina" in itemlist[-1].title:
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def generos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = 'dropdown-item py-1 px-2" href="([^"]+)"'
    patron += '>([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url, titulo in matches:
        itemlist.append(Item(channel = item.channel,
                             action = "peliculas",
                             title = titulo,
                             url = url + "?page=",
                             page = 1
                             ))
    return itemlist


def findvideos(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, 'Descargar</span>(.*?)Te recomendamos')
    if bloque == "[]":
        return []
    patron  = 'sv_([^_]+).*?'
    patron += 'link="([^"]+).*?'
    patron += 'juM9Fbab.*?src="([^"]+).*?'
    patron += 'rounded c.">([^<]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedserver, scrapedurl, scrapedlanguage, scrapedquality in matches:
        titulo = "Ver en: " + scrapedserver.capitalize() + " (%s)(%s)" %(cali[scrapedquality], idio[scrapedlanguage])
        itemlist.append(
                 item.clone(action = "play",
                 language = idio[scrapedlanguage],
                 quality = cali[scrapedquality],
                 title = titulo,
                 url = scrapedurl
                 ))
    itemlist.sort(key=lambda it: (it.language, it.server))
    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if itemlist:
        itemlist.append(Item(channel = item.channel))
        itemlist.append(item.clone(channel="trailertools", title="Buscar Tráiler", action="buscartrailer", context="",
                                   text_color="magenta"))
        # Opción "Añadir esta película a la biblioteca de KODI"
        if item.extra != "library":
            if config.get_videolibrary_support():
                itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="green",
                                     action="add_pelicula_to_library", url=item.url, thumbnail = item.thumbnail,
                                     contentTitle = item.contentTitle
                                     ))
    return itemlist


def play(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, 'iframe class="" src="([^"]+)')
    item.url = url = httptools.downloadpage(url, follow_redirects=False, only_headers=True).headers.get("location", "")
    itemlist.append(item.clone())
    itemlist = servertools.get_servers_itemlist(itemlist)
    itemlist[0].thumbnail = item.contentThumbnail
    return itemlist
