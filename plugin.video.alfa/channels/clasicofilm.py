# -*- coding: utf-8 -*-

import re

from core import jsontools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, platformtools, logger
from channelselector import get_thumb

host = "http://www.classicofilm.com/"
# Configuracion del canal
__modo_grafico__ = config.get_setting('modo_grafico', 'clasicofilm')
__perfil__ = config.get_setting('perfil', 'clasicofilm')

# Fijar perfil de color            
perfil = [['0xFFFFE6CC', '0xFFFFCE9C', '0xFF994D00'],
          ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E'],
          ['0xFF58D3F7', '0xFF2E9AFE', '0xFF2E64FE']]

if __perfil__ - 1 >= 0:
    color1, color2, color3 = perfil[__perfil__ - 1]
else:
    color1 = color2 = color3 = ""


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Películas", text_color=color2, action="", text_bold=True))
    itemlist.append(item.clone(action="peliculas", title="      Novedades",
                               url = host + "feeds/posts/summary?start-index=1&max-results=20&alt=json-in-script&callback=finddatepost",
                               thumbnail=get_thumb('newest', auto=True), text_color=color1))
    #itemlist.append(item.clone(action="generos", title="      Por géneros", url=host,
    #                           thumbnail=get_thumb('genres', auto=True), text_color=color1))
    itemlist.append(item.clone(title="", action=""))
    itemlist.append(item.clone(action="search", title="Buscar...", text_color=color3,
                               thumbnail=get_thumb('search', auto=True)))
    itemlist.append(item.clone(action="configuracion", title="Configurar canal...", text_color="gold", folder=False))
    return itemlist


def configuracion(item):
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "%20")
    item.url = host + "search?q=%s" % texto
    try:
        return busqueda(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host + "feeds/posts/summary?start-index=1&max-results=20&alt=json-in-script&callback=finddatepost"
            item.action = "peliculas"
            itemlist = peliculas(item)
            if itemlist[-1].action == "peliculas":
                itemlist.pop()
    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    item.text_color = color2
    # Descarga la página
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, 'finddatepost\((\{.*?\]\}\})\);')
    data = jsontools.load(data)["feed"]
    for entry in data["entry"]:
        bb=jsontools.dump(entry["author"])
        aa=scrapertools.find_single_match(bb, '(?s)src": "([^"]+)')
        if "Enviar comentarios" in entry: continue
        for link in entry["link"]:
            if link["rel"] == "alternate":
                title = link["title"]
                url = link["href"]
                break
        thumbnail = "https:" + bb 
        thumbnail = thumbnail.replace("s72-c/", "")
        try:
            title_split = re.split(r"\s*\((\d)", title, 1)
            year = title_split[1] + scrapertools.find_single_match(title_split[2], '(\d{3})\)')
            contentTitle = title_split[0]
        except:
            contentTitle = title
            year = ""
        if not "DVD" in title and not "HDTV" in title and not "HD-" in title and not "HDtv" in title:
            continue
        infolabels = {'year': year}
        new_item = item.clone(action="findvideos", title=title, contentTitle=contentTitle,
                              url=url, thumbnail=thumbnail, infoLabels=infolabels,
                              contentType="movie")
        itemlist.append(new_item)
    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    actualpage = int(scrapertools.find_single_match(item.url, 'start-index=(\d+)'))
    totalresults = int(data["openSearch$totalResults"]["$t"])
    if actualpage + 20 < totalresults:
        url_next = item.url.replace("start-index=" + str(actualpage), "start-index=" + str(actualpage + 20))
        itemlist.append(Item(channel=item.channel, action=item.action, title=">> Página Siguiente", url=url_next))
    return itemlist


def busqueda(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = """post-title entry-titl.*?href='([^']+)'"""
    patron += """>([^<]+).*?"""
    patron += """src="([^"]+)"""
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        year = scrapertools.find_single_match(scrapedtitle, "\(([0-9]{4})\)")
        ctitle = scrapedtitle.split("(")[0].strip()
        itemlist.append(item.clone(action = "findvideos",
                                   contentTitle = ctitle,
                                   infoLabels = {"year" : year},
                                   thumbnail = scrapedthumbnail,
                                   title = scrapedtitle,
                                   url = scrapedurl
                                   ))
    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    return itemlist


def generos(item):
    logger.info()
    itemlist = []
    # Descarga la página
    data = httptools.downloadpage(item.url).data
    patron = '<b>([^<]+)</b><br\s*/>\s*<script src="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedtitle, scrapedurl in matches:
        scrapedurl = scrapedurl.replace("&amp;","&")
        scrapedurl = scrapedurl.replace("max-results=500", "start-index=1&max-results=20") \
            .replace("recentpostslist", "finddatepost")
        itemlist.append(Item(channel=item.channel, action="peliculas", title=scrapedtitle, url=scrapedurl,
                             thumbnail=item.thumbnail, text_color=color3))
    itemlist.sort(key=lambda x: x.title)
    return itemlist


def decodifica_id(txt):
    res = ''
    for i in range(0, len(txt), 3):
        res += '\\u0' + txt[i:i+3]
    return res.decode('unicode-escape') #Ej: {"v":"9KD2iEmiYLsF"}


def findvideos(item):
    logger.info()
    itemlist = []
    if item.infoLabels["tmdb_id"]:
        tmdb.set_infoLabels_item(item, __modo_grafico__)
    data = httptools.downloadpage(item.url).data
    if "data:text/javascript;base64" in data:
        div_id = scrapertools.find_single_match(data, '<div id="([0-9a-fA-F]+)"')
        # ~ logger.info(div_id)
        vid_id = scrapertools.find_single_match(decodifica_id(div_id), ':"([^"]+)"')
        # ~ logger.info(vid_id)
        itemlist.append(item.clone(url='http://netu.tv/watch_video.php?v='+vid_id, server='netutv', action='play'))
    else:
        iframe = scrapertools.find_single_match(data, '<iframe width="720".*?src="([^"]+)"')
        data = data.replace("googleusercontent","malo")  # para que no busque enlaces erroneos de gvideo
        if "goo.gl/" in iframe:
            data += httptools.downloadpage(iframe, follow_redirects=False, only_headers=True).headers.get("location", "")
        itemlist = servertools.find_video_items(item, data)
    if config.get_videolibrary_support():
        itemlist.append(item.clone(action="add_pelicula_to_library", title="Añadir película a la videoteca"))
    return itemlist
