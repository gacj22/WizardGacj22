# -*- coding: utf-8 -*-
# -*- Channel Rexpelis -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
from channelselector import get_thumb
from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger, platformtools


#idio = {'es-mx': 'LAT','es-es': 'ESP','en': 'VO'}
#cali = {'poor': 'SD','low': 'SD','medium': 'HD','high': 'HD'}

list_language = ['LAT']
list_quality = []
list_servers = ['fembed', 'verystream','directo','rapidvideo',
                'streamango', 'fastplay', 'openload']


__channel__='rexpelis'

host = "https://www.rexpelis.com"
headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:67.0) Gecko/20100101 Firefox/67.0'}
try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
except:
    __modo_grafico__ = True


def mainlist(item):
    logger.info()
    itemlist = []
    
    autoplay.init(item.channel, list_servers, list_quality)
    
    data = httptools.downloadpage(host, headers=headers).data
    
    matches = scrapertools.find_multiple_matches(data, 'cant-genre">(\d+)')
    cantidad = 0

    
    for cantidad1 in matches:
        cantidad += int(cantidad1)
    
    itemlist.append(Item(channel=item.channel, title="Actualizadas", action="peliculas",
                         url=host, page=1, type ="movie", thumbnail=thumb("updated")))
    
    itemlist.append(Item(channel=item.channel, title="Estrenos", action="estrenos",
                         url=host + "/estrenos",
                         page=1, thumbnail=thumb("premieres")))
    
    itemlist.append(Item(channel=item.channel, title="Por género (Total películas: %s)" %cantidad,
                         action="generos", url=host, extra="Genero", thumbnail=thumb("genres")))
    
    itemlist.append(Item(channel=item.channel, title="Por año", action="annos",
                         url=host, extra="Genero", thumbnail=thumb("year")))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search",
                         url=host + "/search?term=", thumbnail=thumb("search")))
    
    itemlist.append(item.clone(title="Configurar canal...", text_color="gold",
                               action="configuracion", folder=False))
    
    autoplay.show_option(item.channel, itemlist)
    
    return itemlist


def configuracion(item):
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


def search(item, texto):
    logger.info()
    item.url = host + "/suggest?que=" + texto
    item.extra = "busca"
    item.page = 1
    item.texto = texto
    if texto != '':
        return sub_search(item)
    else:
        return []


def sub_search(item):
    logger.info()
    itemlist = []
    url = item.url
    
    data = httptools.downloadpage(item.url, headers=headers).data

    headers.update({'X-Requested-With': 'XMLHttpRequest'})
    token = scrapertools.find_single_match(data, 'csrf-token" content="([^"]+)')
    data_js = httptools.downloadpage(item.url + "&_token=" + token, headers=headers).json
    for js in data_js["data"]["m"]:
        js["title"] = quitano(js["title"])
        itemlist.append(Item(channel = item.channel,
                             action = "findvideos",
                             contentTitle = js["title"],
                             infoLabels = {'year': js["release_year"]},
                             thumbnail = js["cover"],
                             title = js["title"] + " (%s)" %js["release_year"],
                             url = js["slug"]
                             ))
    
    tmdb.set_infoLabels(itemlist)
    
    return itemlist


def estrenos(item):
    logger.info()
    itemlist = []
    
    data = httptools.downloadpage(item.url, headers=headers).data
    
    patron  = 'item-pelicula.*?href="([^"]+).*?'
    patron += 'src="([^"]+).*?'
    patron += 'text-center">([^<]+).*?'
    patron += '<p>([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    
    for scrapedurl, scrapedthumbnail, scrapedyear, scrapedtitle in matches:
        scrapedtitle = scrapedtitle.replace("Película ","")
        scrapedtitle = quitano(scrapedtitle)
        itemlist.append(Item(channel = item.channel,
                             action = "findvideos",
                             contentTitle = scrapedtitle,
                             infoLabels = {'year':scrapedyear},
                             thumbnail = scrapedthumbnail,
                             title = scrapedtitle + " (%s)" %scrapedyear,
                             url = scrapedurl,
                             language = 'LAT'
                             ))
    tmdb.set_infoLabels(itemlist)
    return itemlist


def generos(item):
    logger.info()
    itemlist = []
    
    data = httptools.downloadpage(item.url, headers=headers).data
    bloque = scrapertools.find_single_match(data, "genressomb.*?</ul>")
    
    patron  = 'href="([^"]+)".*?'
    patron += '</i>([^<]+).*?'
    patron += 'cant-genre">([^<]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    
    for url, titulo, cantidad in matches:
        
        slug = scrapertools.find_single_match(url, "/genero/(.*)")
        
        itemlist.append(Item(channel = item.channel,
                             action = "peliculas",
                             page = 1,
                             slug = slug,
                             title = titulo + "(%s)" %cantidad,
                             type = "genre",
                             url = url
                             ))
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    
    data = httptools.downloadpage(item.url, headers=headers).data

    headers.update({'X-Requested-With': 'XMLHttpRequest'})
    
    token = scrapertools.find_single_match(data, 'csrf-token" content="([^"]+)')
    post = "page=%s&type=%s&_token=%s&slug=%s" %(item.page, item.type, token, item.slug)
    if item.slug:
        post += "&slug=%s" %item.slug
    
    data = httptools.downloadpage(host + "/pagination", post=post, headers=headers).data
    
    patron  = '(?s)href="([^"]+)".*?'
    patron += 'src="([^"]+)".*?'
    patron += 'text-center">([^<]+).*?'
    patron += '<p>([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    
    for scrapedurl, scrapedthumbnail, scrapedyear, scrapedtitle in matches:
        scrapedtitle = quitano(scrapedtitle)
        itemlist.append(Item(channel = item.channel,
                             action = "findvideos",
                             contentTitle = scrapedtitle,
                             infoLabels = {'year':scrapedyear},
                             thumbnail = scrapedthumbnail,
                             title = scrapedtitle + " (%s)" %scrapedyear,
                             url = scrapedurl,
                             language= 'LAT'
                             ))
    tmdb.set_infoLabels(itemlist)
    #pagination
    if len(itemlist)>0:
        itemlist.append(Item(channel = item.channel,
                             action = "peliculas",
                             page = item.page + 1,
                             title = "Página siguiente >>",
                             type = item.type,
                             slug = item.slug,
                             url = item.url
                             ))
    return itemlist


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    item.slug = ""
    try:
        if categoria in ['peliculas','latino']:
            item.url = host
            item.page=1
        elif categoria == 'infantiles':
            item.url = host + '/genero/animacion'
            item.page = 1
        elif categoria == 'terror':
            item.url = host + '/genero/terror'
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


def annos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, headers=headers).data
    bloque = scrapertools.find_single_match(data, 'div class="years.*?</ul>')
    patron  = 'href="([^"]+)"'
    patron += '>([^<]+).*?'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for url, titulo in matches:
        itemlist.append(Item(channel = item.channel,
                             action = "peliculas",
                             page = 1,
                             slug = titulo,
                             title = titulo,
                             type = "year",
                             url = url
                             ))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    
    data = httptools.downloadpage(item.url, headers=headers).data
    
    patron  = 'data-player-id="([^"]+)".*?<a href.*?>([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    
    for scrapedid, title in matches:
        
        player = '%s/player/embed/movie/%s' % (host, scrapedid)
        
        new_data = httptools.downloadpage(player, headers=headers).data
        scrapedurl = scrapertools.find_single_match(new_data, 'src="([^"]+)"')
        
        if "VIP" in title: title = "fembed"
        titulo = "Ver en %s" %title.capitalize()
        
        itemlist.append(
                 item.clone(action = "play",
                 title = titulo,
                 url = scrapedurl
                 ))
    
    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if itemlist and item.contentChannel != "videolibrary":
        #itemlist.append(Item(channel = item.channel))
        #itemlist.append(item.clone(channel="trailertools", title="Buscar Tráiler", action="buscartrailer", context="",
        #                           text_color="magenta"))
        # Opción "Añadir esta película a la videoteca de KODI"
        if config.get_videolibrary_support():
            itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="gold",
                                 action="add_pelicula_to_library", url=item.url, thumbnail = item.thumbnail,
                                 contentTitle = item.contentTitle
                                ))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    if "rexpelis.com" in item.url:
        data = httptools.downloadpage(item.url, headers=headers).data
        url = scrapertools.find_single_match(data, '<iframe src="([^"]+)')
        headers = {"Referer":item.url}
        item.url = httptools.downloadpage(url, follow_redirects=False, only_headers=True, headers=headers).headers.get("location", "")
    if "vadacloud" in item.url:
       id = scrapertools.find_single_match(item.url, 'id=(\w+)')
       item.url = "https://vadacloud.com/hls/%s/%s.playlist.m3u8" %(id, id)
    itemlist.append(item.clone())
    itemlist = servertools.get_servers_itemlist(itemlist)
    item.thumbnail = item.contentThumbnail
    return itemlist

def thumb(img_title):
    return get_thumb(img_title, auto=True)

def quitano(title):
    # Quita el año que muestran en el título en la página, para que funcione bien tmdb
    t = re.sub('\(\s*\d{4}\s*\)',"", title)

    if ' / ' in title:
        t = t.split(' / ')[0]
    t = re.sub('\d{4}$',"", t)
    return t.strip()
