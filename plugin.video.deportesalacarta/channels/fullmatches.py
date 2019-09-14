# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para Full Matches & Shows
#------------------------------------------------------------

from core import logger
from core import config
from core import httptools
from core import scrapertools
from core.item import Item
from core import servertools

__channel__ = "fullmatches"


def mainlist(item):
    logger.info("deportesalacarta.channels.fullmatches mainlist")
    itemlist = []
    itemlist.append(Item(channel=__channel__, title="Novedades" , action="novedades", url="http://www.fullmatchesandshows.com/", thumbnail=item.thumbnail, fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Competiciones" , action="categorias", url="http://www.fullmatchesandshows.com/", thumbnail=item.thumbnail, fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Buscar..."      , action="search", thumbnail=item.thumbnail, fanart=item.fanart))

    return itemlist

def search(item,texto):
    logger.info("deportesalacarta.channels.fullmatches search")
    itemlist = []
    item.url = "http://www.fullmatchesandshows.com/?s=" + texto
    return busqueda(item)

def novedades(item):
    logger.info("deportesalacarta.channels.fullmatches novedades")
    itemlist = []
    if item.url.startswith("action"):
        data = httptools.downloadpage("http://www.fullmatchesandshows.com/wp-admin/admin-ajax.php?td_theme_name=Newspaper&v=6.5.1", post=item.url).data
        data = scrapertools.decodeHtmlentities(data)
        data = data.replace("\\","")
        current_page = scrapertools.find_single_match(item.url, 'td_current_page=(\d+)&')
        max_page = item.extra
        next_page = ""
    else:
        data = httptools.downloadpage(item.url).data
        data = scrapertools.decodeHtmlentities(data)
        current_page = "1"
        max_page = 0
        next_page = scrapertools.find_single_match(data, '<a href="([^"]+)"><i class="td-icon-menu-right">')
        if next_page == "":
            block = scrapertools.find_single_match(data, 'id="next-page-([^"]+)"')
            if block:
                max_page = scrapertools.find_single_match(data, block+'.max_num_pages\s*=\s*"([^"]+)"')
                atts = "&td_atts="+scrapertools.find_single_match(data, block+".atts\s*=\s*'([^']+)'")
                id = "&td_block_id="+scrapertools.find_single_match(data, block+'.id\s*=\s*"([^"]+)"')
                type = "&block_type="+scrapertools.find_single_match(data, block+'.block_type\s*=\s*"([^"]+)"')
                column = "&td_column_number="+scrapertools.find_single_match(data, block+'.td_column_number\s*=\s*"([^"]+)"')
                item.url = "action=td_ajax_block"+ atts + id + column + "&td_current_page="+ current_page + type

    matches = scrapertools.find_multiple_matches(data, '<div class="td-block-span4">.*?<div class="td-module-thumb"><a href="([^"]+)".*?title="([^"]+)".*?data-lazy-src="(.*?)(?:"|\?resize)')
    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        logger.info(scrapedthumbnail)
        scrapedtitle = scrapedtitle.replace("Highlights","Resumen").replace("Full Match", "Partido Completo")
        itemlist.append(Item(channel=__channel__, title=scrapedtitle, url=scrapedurl, action="findvideos", thumbnail=scrapedthumbnail, folder=True))


    if int(current_page) < int(max_page) and next_page == "":
        page = int(current_page) + 1
        next_page = item.url.replace('td_current_page='+current_page, 'td_current_page='+str(page))

    if next_page != "": itemlist.append(Item(channel=__channel__, title=">> Siguiente", url=next_page, action="novedades", extra=max_page, thumbnail=item.thumbnail, folder=True))

    return itemlist

def entradas(item):
    logger.info("deportesalacarta.channels.fullmatches entradas")
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.decodeHtmlentities(data)

    if item.extra == "1":
        matches = scrapertools.find_multiple_matches(data, '(?:<div class="td_module_mx|<div class="td-block-span4">).*?<div class="td-module-thumb"><a href="([^"]+)".*?title="([^"]+)".*?src="(.*?)(?:"|\?resize)')
    else:
        matches = scrapertools.find_multiple_matches(data, '<div class="td-block-span4">.*?<div class="td-module-thumb"><a href="([^"]+)".*?title="([^"]+)".*?src="(.*?)(?:"|\?resize)')
    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        scrapedtitle = scrapedtitle.replace("Highlights","Resumen").replace("Full Match", "Partido Completo")
        itemlist.append(Item(channel=__channel__, title=scrapedtitle, url=scrapedurl, action="findvideos", thumbnail=scrapedthumbnail, folder=True))

    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)"><i class="td-icon-menu-right">')
    if next_page != "":
        itemlist.append(Item(channel=__channel__, title=">> Siguiente", url=next_page, action="novedades", thumbnail=item.thumbnail, folder=True))

    return itemlist

def categorias(item):
    logger.info("deportesalacarta.channels.fullmatches categorias")
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.decodeHtmlentities(data)

    bloque = scrapertools.find_single_match(data, '(<ul class="sub-menu">.*?</ul>)')

    matches = scrapertools.find_multiple_matches(bloque, '<a href="([^"]+)">(.*?)</a>')
    for scrapedurl, scrapedtitle in matches:
        if scrapedtitle == "La Liga": scrapedurl = "http://www.fullmatchesandshows.com/category/la-liga/"
        if scrapedtitle == "Champions League": continue
        if "category/" in scrapedurl: action = "entradas"
        else: action = "novedades"
        itemlist.append(Item(channel=__channel__, title=scrapedtitle, url=scrapedurl, action=action, thumbnail=item.thumbnail, extra= "1", folder=True))

    post = 'action=td_ajax_block&td_atts={"custom_title":"Latest Highlights and Full Matches","limit":"18","td_ajax_filter_type"' \
           ':"td_category_ids_filter","td_filter_default_txt":"All","ajax_pagination":"next_prev","td_ajax_filter_ids"' \
           ':"499,2,79,28,49,94,65,23,55,432","category_ids":"94, 65, 218, 233","class":"td_block_id_1991998159 td_uid_1_57080d828ccaf_rand"}' \
           '&td_block_id=td_uid_1_57080d828ccaf&td_column_number=3&td_current_page=1&block_type=td_block_3&td_filter_value=%s'

    itemlist.insert(4, Item(channel=__channel__, title="Champions League", url=post % "49", action="novedades", extra="10", thumbnail=item.thumbnail, folder=True))
    itemlist.insert(5, Item(channel=__channel__, title="Europa League", url=post % "55", action="novedades", extra="10", thumbnail=item.thumbnail, folder=True))
    itemlist.append(Item(channel=__channel__, title="Shows", url=post % "65", action="novedades", extra="10", thumbnail=item.thumbnail, folder=True))
    itemlist.append(Item(channel=__channel__, title="Competiciones de Inglaterra", url=post % "499", action="novedades", extra="10", thumbnail=item.thumbnail, folder=True))
    itemlist.append(Item(channel=__channel__, title="Competiciones de España", url=post % "2", action="novedades", extra="10", thumbnail=item.thumbnail, folder=True))
    itemlist.append(Item(channel=__channel__, title="Competiciones de Italia", url=post % "28", action="novedades", extra="10", thumbnail=item.thumbnail, folder=True))
    itemlist.append(Item(channel=__channel__, title="Competiciones de Alemania", url=post % "79", action="novedades", extra="10", thumbnail=item.thumbnail, folder=True))
    itemlist.append(Item(channel=__channel__, title="Competiciones de Francia", url=post % "23", action="novedades", extra="10", thumbnail=item.thumbnail, folder=True))

    return itemlist

def findvideos(item):
    logger.info("deportesalacarta.channels.fullmatches findvideos")
    itemlist = []
    if item.extra == "":
        data = httptools.downloadpage(item.url).data
        data = scrapertools.decodeHtmlentities(data)
        matches = scrapertools.find_multiple_matches(data, 'id="item(\d+)">.*?<div.*?>(.*?)</div>')
        if len (matches) > 1:
            for scrapedurl, scrapedtitle in matches:
                scrapedtitle = scrapedtitle \
                            .replace("HL ", "Resumen ").replace("Extended","Extendido") \
                            .replace("1st half ", "1ª parte ").replace("2nd half ","2ª parte ") \
                            .replace("Pre-Match", "Pre-partido").replace("Post-Match","Post-Partido") \
                            .replace("Title","Pre-partido/Post-Partido").replace("ET/Penalties (if any)", "Prórroga/Penaltis (si los hay)")
                url = item.url + scrapedurl
                itemlist.append(Item(channel=__channel__, title=scrapedtitle, url=url, action="findvideos", thumbnail=item.thumbnail, extra="play", folder=True))
        else:
            itemlist = servertools.find_video_items(data=data)
            for item in itemlist:
                item.channel = __channel__
    else:
        data = httptools.downloadpage(item.url).data
        itemlist = servertools.find_video_items(data=data)
        for item in itemlist:
            item.channel = __channel__

    return itemlist

def busqueda(item):
    logger.info("deportesalacarta.channels.fullmatches busqueda")
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.decodeHtmlentities(data)

    matches = scrapertools.find_multiple_matches(data, '<div class="td-block-span6">.*?<div class="td-module-thumb"><a href="([^"]+)".*?title="([^"]+)".*?src="(.*?)(?:"|\?resize)')
    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        itemlist.append(Item(channel=__channel__, title=scrapedtitle, url=scrapedurl, action="findvideos", thumbnail=scrapedthumbnail, folder=True))


    next_page = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)"')
    if len (next_page) > 0:
        itemlist.append(Item(channel=__channel__, title=">> Siguiente", url=next_page, action="busqueda", thumbnail=item.thumbnail, folder=True))

    return itemlist
