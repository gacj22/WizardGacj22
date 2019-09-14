# -*- coding: utf-8 -*-

import urlparse

from core import httptools
from core import scrapertools
from platformcode import config, logger

host = "https://www.javwhores.com"


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="lista", title="Nuevos Vídeos", url=host + "/latest-updates/"))
    itemlist.append(item.clone(action="lista", title="Mejor Valorados", url=host + "/top-rated/"))
    itemlist.append(item.clone(action="lista", title="Más Vistos", url=host + "/most-popular/"))
    itemlist.append(item.clone(action="categorias", title="Categorías", url=host + "/categories/"))
    itemlist.append(item.clone(title="Buscar...", action="search"))
    itemlist.append(item.clone(action="configuracion", title="Configurar canal...", text_color="gold", folder=False))
    return itemlist


def configuracion(item):
    from platformcode import platformtools
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


def search(item, texto):
    logger.info()
    item.url = "%s/search/%s/" % (host, texto)
    item.extra = texto
    try:
        return lista(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    action = "play"
    if config.get_setting("menu_info", "javtasty"):
        action = "menu_info"
    # PURGA los PRIVATE 
    patron  = 'div class="video-item\s+".*?href="([^"]+)".*?'
    patron += 'data-original="([^"]+)" '
    patron += 'alt="([^"]+)"(.*?)fa fa-clock-o"></i>([^<]+)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle, quality, duration in matches:
        scrapedurl = urlparse.urljoin(host, scrapedurl)
        scrapedtitle = scrapedtitle.strip()
        if duration:
            scrapedtitle = "%s - %s" % (duration.strip(), scrapedtitle)
        if '>HD<' in quality:
            scrapedtitle += "  [COLOR red][HD][/COLOR]"
        itemlist.append(item.clone(action=action, title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail,
                                   fanart=scrapedthumbnail))
    # Extrae la marca de siguiente página
    next_page = scrapertools.find_single_match(data, 'next"><a href="([^"]+)')
    if next_page:
        itemlist.append(item.clone(action="lista", title=">> Página Siguiente", url=host + next_page))
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '(?s)<a class="item" href="([^"]+)".*?'
    patron += 'src="([^"]+)" '
    patron += 'alt="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        scrapedurl = urlparse.urljoin(host, scrapedurl)
        scrapedthumbnail = urlparse.urljoin(host, scrapedthumbnail)
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail,
                                   fanart=scrapedthumbnail))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    videourl = scrapertools.find_single_match(data, "video_alt_url2:\s*'([^']+)'")
    if videourl:
        itemlist.append(['.mp4 HD [directo]', videourl])
    videourl = scrapertools.find_single_match(data, "video_alt_url:\s*'([^']+)'")
    if videourl:
        itemlist.append(['.mp4 HD [directo]', videourl])
    videourl = scrapertools.find_single_match(data, "video_url:\s*'([^']+)'")
    if videourl:
        itemlist.append(['.mp4 [directo]', videourl])
    if item.extra == "play_menu":
        return itemlist, data
    return itemlist


def menu_info(item):
    logger.info()
    itemlist = []
    video_urls, data = play(item.clone(extra="play_menu"))
    itemlist.append(item.clone(action="play", title="Ver -- %s" % item.title, video_urls=video_urls))
    matches = scrapertools.find_multiple_matches(data, '<a href="([^"]+)" class="item" rel="screenshots"')
    for i, img in enumerate(matches):
        if i == 0:
            continue
        title = "Imagen %s" % (str(i))
        itemlist.append(item.clone(action="", title=title, thumbnail=img, fanart=img))
    return itemlist
