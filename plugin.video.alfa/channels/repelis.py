# -*- coding: utf-8 -*-
# -*- Channel Repelis -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

from channelselector import get_thumb
from channels import autoplay
from channels import filtertools
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger, platformtools


idio = {'es-mx': 'LAT','es-es': 'ESP','en': 'VO'}
cali = {'poor': 'SD','low': 'SD','medium': 'HD','high': 'HD'}

list_language = idio.values()
list_quality = ["SD","HD"]
list_servers = ['rapidvideo', 'streamango', 'fastplay', 'openload', 'netu', 'vidoza', 'uptobox']


__channel__='repelis'

host = "https://repelisgo.com"

try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
except:
    __modo_grafico__ = True


def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []
    itemlist.append(Item(channel = item.channel, title = "Destacadas", action = "destacadas", url = host, thumbnail = get_thumb("hot", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Agregadas recientemente", action = "peliculas", url = host + "/explorar?page=", page=1, thumbnail = get_thumb("last", auto = True)))
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


def destacadas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = 'Películas destacadas(.*?)</section>'
    bloque = scrapertools.find_single_match(data, patron)
    patron  = 'href="([^"]+).*?'
    patron += 'title="([^"]+).*?'
    patron += 'data-src="([^"]+).*?'
    patron += 'data-year="([^"]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail, scrapedyear in matches:
        scrapedtitle = scrapedtitle.replace("Película ","")
        itemlist.append(Item(channel = item.channel,
                             action = "findvideos",
                             contentTitle = scrapedtitle,
                             infoLabels = {'year':scrapedyear},
                             thumbnail = host + scrapedthumbnail,
                             title = scrapedtitle + " (%s)" %scrapedyear,
                             url = host + scrapedurl
                             ))
    tmdb.set_infoLabels(itemlist)
    return itemlist
    
    
def peliculas(item):
    logger.info()
    itemlist = []
    url = item.url
    headers = [
    ['Content-Type', 'application/json']
    ]
    if item.extra != "busca":
        url = item.url + str(item.page)
        data = httptools.downloadpage(url, post="", headers=headers).data
        bloquex = scrapertools.find_single_match(data, 'window.__NUXT__={.*?movies":(.*?\])')
        dict = jsontools.load(bloquex)
    else:
        dd = httptools.downloadpage(host + "/graph", post=jsontools.dump(item.post), headers=headers).data
        dict = jsontools.load(dd)["data"]["movies"]
    for datos in dict:
        scrapedurl = host + "/pelicula/" + datos["slug"] + "-" + datos["id"]
        scrapedtitle = datos["title"].replace("Película ","")
        scrapedthumbnail = host + "/_images/posters/" + datos["poster"] + "/180x270.jpg"
        scrapedyear = scrapertools.find_single_match(datos["releaseDate"],'\d{4}')
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
            item.url = host + "/explorar?page="
            item.page=1
        elif categoria == 'infantiles':
            item.url = host + '/genero/animacion-WYXS9?page'
            item.page = 1
        elif categoria == 'terror':
            item.url = host + 'genero/terror-dVbSb?page='
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


def search(item, texto):
    logger.info()
    item.url = item.url + texto
    item.extra = "busca"
    item.page = 1
    item.texto = texto
    item.post = {"query":"\n          query ($term: String) {\n            movies: allMovies(search: $term) {\n              id\n              slug\n              title\n              rating\n              releaseDate\n              released\n              poster\n              nowPlaying\n            }\n          }\n        ","variables":{"term":"%s" %texto}}
    if texto != '':
        return peliculas(item)
    else:
        return []


def generos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, "Géneros.*?</ul>")
    patron  = 'href="([^"]+)"'
    patron += '>([^<]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for url, titulo in matches:
        itemlist.append(Item(channel = item.channel,
                             action = "peliculas",
                             title = titulo,
                             url = host + url + "?page=",
                             page = 1
                             ))
    return itemlist


def findvideos(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, ',"mirrors":(.*?\])')
    if bloque == "[]":
        return []
    dict = jsontools.load(bloque)
    urlx = httptools.downloadpage(host + dict[0]["url"])   #Para que pueda saltar el cloudflare, se tiene que descargar la página completa
    for datos in dict:
        url1 = datos["url"]
        hostname = scrapertools.find_single_match(datos["hostname"].replace("www.",""), "(.*?)\.")
        if "repelisgo" in hostname or "repelis.io" in datos["hostname"]: continue
        if hostname == "my": hostname = "mailru"
        titulo = "Ver en: " + hostname.capitalize() + " (" + cali[datos["quality"]] + ") (" + idio[datos["audio"]] + ")"
        itemlist.append(
                 item.clone(channel = item.channel,
                 action = "play",
                 language = idio[datos["audio"]],
                 quality = cali[datos["quality"]],
                 server = "",
                 title = titulo,
                 url = url1
                 ))
    itemlist.sort(key=lambda it: (it.language, it.server))
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
    logger.info()
    itemlist = []
    #headers = {"}
    url1 = httptools.downloadpage(host + item.url, follow_redirects=False, only_headers=True).headers.get("location", "")
    itemlist.append(item.clone(url=url1))
    itemlist = servertools.get_servers_itemlist(itemlist)
    itemlist[0].thumbnail = item.contentThumbnail
    return itemlist
