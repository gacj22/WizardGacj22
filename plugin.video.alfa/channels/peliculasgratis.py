# -*- coding: utf-8 -*-

import os
import re
import urllib

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger


host = "http://peliculasgratis.biz"

CALIDADES = {"micro1080p": "[COLOR plum]Micro1080p[/COLOR]", "dvds": "[COLOR lime]Dvds[/COLOR]",
             "hdrip": "[COLOR dodgerblue]Hdrip[/COLOR]", "dvdrip": "[COLOR crimson]Dvdrip[/COLOR]",
             "hdts": "[COLOR aqua]Hdts[/COLOR]", "bluray-line": "[COLOR lightslategray]Bluray-line[/COLOR]",
             "hdtv-rip": "[COLOR black]Hdtv-rip[/COLOR]", "micro720p": "[COLOR yellow]Micro720p[/COLOR]",
             "ts-hq": "[COLOR mediumspringgreen]Ts-Hq[/COLOR]", "camrip": "[COLOR royalblue]Camp-Rip[/COLOR]",
             "webs": "[COLOR lightsalmon]Webs[/COLOR]", "hd": "[COLOR mediumseagreen]HD[/COLOR]"}
IDIOMAS = {"castellano": "[COLOR yellow]Castellano[/COLOR]", "latino": "[COLOR orange]Latino[/COLOR]",
           "vose": "[COLOR lightsalmon]Subtitulada[/COLOR]", "vo": "[COLOR crimson]Ingles[/COLOR]",
           "en": "[COLOR crimson]Ingles[/COLOR]"}

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="[COLOR lightskyblue][B]Películas[/B][/COLOR]", action="scraper", url=host,
                               thumbnail="http://imgur.com/fN2p6qH.png", fanart="http://imgur.com/b8OuBR2.jpg",
                               contentType="movie"))
    itemlist.append(itemlist[-1].clone(title="[COLOR lightskyblue][B]   Más vistas[/B][/COLOR]", action="scraper",
                                       url= host + "/catalogue?order=most_viewed",
                                       thumbnail="http://imgur.com/fN2p6qH.png", fanart="http://imgur.com/b8OuBR2.jpg",
                                       contentType="movie"))
    itemlist.append(itemlist[-1].clone(title="   [COLOR lightskyblue][B]Recomendadas[/B][/COLOR]", action="scraper",
                                       url=host + "/catalogue?order=most_rated",
                                       thumbnail="http://imgur.com/fN2p6qH.png",
                                       fanart="http://imgur.com/b8OuBR2.jpg", contentType="movie"))
    itemlist.append(itemlist[-1].clone(title="[COLOR lightskyblue][B]   Actualizadas[/B][/COLOR]", action="scraper",
                                       url= host + "/catalogue?",
                                       thumbnail="http://imgur.com/fN2p6qH.png", fanart="http://imgur.com/b8OuBR2.jpg",
                                       contentType="movie"))
    itemlist.append(itemlist[-1].clone(title="[COLOR lightskyblue][B]   Género[/B][/COLOR]", action="genero",
                                       url= host,
                                       thumbnail="http://imgur.com/fN2p6qH.png", fanart="http://imgur.com/b8OuBR2.jpg",
                                       contentType="movie"))
    itemlist.append(itemlist[-1].clone(title="[COLOR lightskyblue][B]Series[/B][/COLOR]", action="scraper",
                                       url= host + "/lista-de-series",
                                       thumbnail="http://imgur.com/Jia27Uc.png", fanart="http://imgur.com/b8OuBR2.jpg",
                                       contentType="tvshow"))
    itemlist.append(itemlist[-1].clone(title="[COLOR lightskyblue][B]Buscar[/B][/COLOR]", action = "",
                                       thumbnail="http://imgur.com/mwTwfN7.png", fanart="http://imgur.com/b8OuBR2.jpg"))
    itemlist.append(
        itemlist[-1].clone(title="[COLOR lightskyblue][B]   Buscar Película[/B][/COLOR]", action="search", url="",
                           thumbnail="http://imgur.com/mwTwfN7.png", fanart="http://imgur.com/b8OuBR2.jpg",
                           contentType="movie"))
    itemlist.append(
        itemlist[-1].clone(title="[COLOR lightskyblue][B]   Buscar Serie[/B][/COLOR]", action="search", url="",
                           thumbnail="http://imgur.com/mwTwfN7.png", fanart="http://imgur.com/b8OuBR2.jpg",
                           contentType="tvshow"))

    return itemlist


def genero(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = 'Películas por géneros<u class="fa fa-sort-down.*?fa fa-sort-down'
    bloque = scrapertools.find_single_match(data, patron)
    patron  = 'href="([^"]+).*?'
    patron += '</i>([^<]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedtitle in matches:
        if "Adultos" in scrapedtitle and config.get_setting("adult_mode") == 0:
            continue
        itemlist.append(Item(channel = item.channel,
                             action = "scraper",
                             contentType = "movie",
                             title = scrapedtitle,
                             url = scrapedurl
                             ))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/%s" % texto
    if item.contentType == '': item.contentType = 'movie'
    try:
        return scraper(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def scraper(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    bloque_enlaces = scrapertools.find_single_match(data, '<h1 class="titulo-h1">(.*?)<\/i>Anuncios')
    if item.contentType != "movie":
        patron  = '<a class="i" href="([^"]+)".*?'
        patron += 'src="([^"]+)".*?'
        patron += 'alt="([^"]+)".*?'
        patron += '<div class="l">(.*?)<\/a><h3>.*?'
        patron += '(completa)">.*?'
        patron += '<span>(.*?)<\/span>'
        action = "findvideos_series"
    else:
        patron  = '<a class="i" href="([^"]+)".*?'
        patron += 'src="([^"]+)".*?'
        patron += 'alt="([^"]+)".*?'
        patron += '">([^<]+)<.*?'
        patron += '<div class="l">(.*?)<\/a><h3>.*?'
        patron += '<\/a><\/h3> <span>(.*?)<'
        action = "findvideos"
    matches = scrapertools.find_multiple_matches(bloque_enlaces, patron)
    for url, thumb, title, quality, check_idioma, year in matches:
        year = year.strip()
        title_fan = title
        title_item = "[COLOR cornflowerblue][B]" + title + "[/B][/COLOR]"
        if item.contentType != "movie":
            title = title
            idiomas = ''
        else:
            if quality == "ts":
                quality = re.sub(r'ts', 'ts-hq', quality)
            if CALIDADES.get(quality):
                quality = CALIDADES.get(quality)
            else:
                quality = quality
            idiomas = scrapertools.find_multiple_matches(check_idioma, '<div class="id (.*?)">')
            title = title
        itemlist.append(
            Item(channel=item.channel, title=title, contentTitle=title, url=host + url, action=action, thumbnail=thumb,
                 fanart="http://imgur.com/nqmJozd.jpg", extra=title_fan + "|" + title_item + "|" + year, show=title,
                 contentType=item.contentType, folder=True, language = idiomas, infoLabels={"year":year}))
    ## Paginación
    tmdb.set_infoLabels(itemlist)
    if year:
        next = scrapertools.find_single_match(data, 'href="([^"]+)" title="Siguiente página">')
        if len(next) > 0:
            url = next
            if not "http" in url:
                url = host + url
            itemlist.append(
                Item(channel=item.channel, action="scraper", title="[COLOR floralwhite][B]Siguiente[/B][/COLOR]",
                     url=url, thumbnail="http://imgur.com/jhRFAmk.png", fanart="http://imgur.com/nqmJozd.jpg",
                     extra=item.extra, contentType=item.contentType, folder=True))
    return itemlist


def findvideos_series(item):
    logger.info()
    itemlist = []
    check_temp = []
    data = httptools.downloadpage(item.url + "/episodios").data
    try:
        temp, bloque_enlaces = scrapertools.find_single_match(data, 'Temporada (\d+)(.*?)Temporada')
    except:
        if "no se agregaron" in data:
            temp = bloque_enlaces = ""
        else:
            temp, bloque_enlaces = scrapertools.find_single_match(data, 'Temporada (\d+)(.*?)<div class="enlaces">')
    if temp != "":
        item.infoLabels["season"] = temp
        itemlist.append(item.clone(title="[COLOR darkturquoise]Temporada[/COLOR] " + "[COLOR beige]" + temp + "[/COLOR]",
                             folder=False))
    capitulos = scrapertools.find_multiple_matches(bloque_enlaces, 'href="([^"]+)".*?Episodio (\d+) - ([^<]+)')
    for url, epi, title in capitulos:
        if epi == "1":
            if epi in str(check_temp):
                temp = int(temp) + 1
                item.infoLabels["season"] = temp
                item.infoLabels["episode"] = 0
                itemlist.append(item.clone(title="[COLOR darkturquoise]Temporada[/COLOR] " + "[COLOR beige]" + str(
                                           temp) + "[/COLOR]", folder=False
                                           ))
        check_temp.append([epi])
        item.infoLabels["season"] = temp
        item.infoLabels["episode"] = epi
        itemlist.append(item.clone(title="     [COLOR cyan]Episodio[/COLOR] " + "[COLOR darkcyan]" + epi + "[/COLOR]" + " - " + "[COLOR cadetblue]" + title + "[/COLOR]",
                             url=url, action="findvideos", thumbnail="",
                             extra="", contentType=item.contentType, folder=True))
    tmdb.set_infoLabels(itemlist)
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if item.extra != "dd" and item.extra != "descarga":
        if item.contentType != "movie":
            bloque_links = scrapertools.find_single_match(data, '<div class="links">(.*?)<\/i>Selecciona un')
            if bloque_links == "":
                bloque_links = scrapertools.find_single_match(data, '<div class="links">(.*?)<div class="enlaces">')
        else:
            bloque_links = scrapertools.find_single_match(data, '<div class="links">(.*?)<\/i>Descargar')
            if bloque_links == "":
                bloque_links = scrapertools.find_single_match(data, '<div class="links">(.*?)<div class="enlaces">')
        patron  = '<a class="goto" rel="nofollow".*?data-id="([^<]+)".*?'
        patron += 'src="([^"]+)">'
        patron += '([^<]+)<.*?'
        patron += 'src="([^"]+)'
        patron += '">([^<]+).*?'
        patron += '<span>([^<]+)'
        links = scrapertools.find_multiple_matches(bloque_links, patron)
        for id, thumb, server, idiomapng, idioma, calidad in links:
            idioma = idioma.strip()
            calidad = calidad.lower()
            calidad = re.sub(r' ', '-', calidad)
            if calidad == "ts":
                calidad = re.sub(r'ts', 'ts-hq', calidad)
            url = host + "/goto/"
            url_post = urllib.urlencode({'id': id})
            server_name = scrapertools.find_single_match(server, '(\w+)\.').replace("waaw","netutv")
            server_parameters = servertools.get_server_parameters(server_name)
            icon_server = server_parameters.get("thumbnail", "")
            extra = "online"
            title = server_name + " (" + calidad + ") (" + idioma + ")"
            itemlist.append(item.clone(title=title, url=url, action="play", thumbnail = icon_server,
                                 folder=True, id=url_post, language=idioma,
                                 quality=calidad, server = server_name))
    else:
        bloque_dd = scrapertools.find_single_match(data, '<\/i>Descargar(.*?)<div class="enlaces">')
        links_dd = scrapertools.find_multiple_matches(bloque_dd,
                                                      '<a class="low".*?data-id="(.*?)".*?src="([^"]+)">([^<]+)<.*?src[^<]+>([^<]+).*?<span>([^<]+)')
        for id, thumb, server, idioma, calidad in links_dd:
            idioma = idioma.strip()
            calidad = calidad.lower()
            calidad = re.sub(r' ', '-', calidad)
            if calidad == "ts":
                calidad = re.sub(r'ts', 'ts-hq', calidad)
            if CALIDADES.get(calidad):
                calidad = CALIDADES.get(calidad)
            else:
                calidad = "[COLOR brown]" + calidad + "[/COLOR]"
            if IDIOMAS.get(idioma):
                idioma = IDIOMAS.get(idioma)
            else:
                idioma = "[COLOR brown]" + idioma + "[/COLOR]"
            url = host + "/goto/"
            data_post = urllib.urlencode({'id': id})
            server_name = scrapertools.find_single_match(server, '(.*?)\.').strip()
            icon_server = os.path.join(config.get_runtime_path(), "resources", "images", "servers",
                                       "server_" + server_name + ".png")
            icon_server = icon_server.replace('streamin', 'streaminto')
            icon_server = icon_server.replace('ul', 'uploadedto')
            if not os.path.exists(icon_server):
                icon_server = thumb
            extra = "descarga"
            itemlist.append(
                item.clone(title="[COLOR floralwhite][B]" + server + "[/B][/COLOR] " + calidad + " " + idioma, url=url,
                           action="play", thumbnail=icon_server, id=data_post))
    if item.infoLabels["year"]:
        tmdb.set_infoLabels(itemlist)
    if item.contentType == "movie" and item.extra != "descarga" and item.extra != "online":
        if config.get_videolibrary_support() and len(itemlist) > 0:
            itemlist.append(Item(channel=item.channel, title="Añadir película a la videoteca",
                                 action="add_pelicula_to_library", url=item.url, text_color="green",
                                 infoLabels={'title': item.contentTitle}, thumbnail="http://imgur.com/xjrGmVM.png",
                                 contentTitle=item.contentTitle,
                                 extra=extra))
    if item.extra != "dd" and item.extra != "descarga" and item.extra != "online":
        bloque_dd = scrapertools.find_single_match(data, '<\/i>Descargar(.*?)<div class="enlaces">')
        if bloque_dd:
            itemlist.append(item.clone(title="[COLOR aqua][B]Ver enlaces Descarga[/B][/COLOR] ", action="findvideos",
                                       thumbnail=thumb, fanart="", contentType=item.contentType, bloque_dd=bloque_dd,
                                       extra="dd"))
    return itemlist


def play(item):
    itemlist = []
    data = httptools.downloadpage(item.url, post=item.id ).data
    url = scrapertools.find_single_match(data, '<a rel="nofollow" href="([^"]+)"')
    itemlist.append(item.clone(server = "", url = url))
    itemlist = servertools.get_servers_itemlist(itemlist)
    for videoitem in itemlist:
        videoitem.thumbnail = item.contentThumbnail
    return itemlist
