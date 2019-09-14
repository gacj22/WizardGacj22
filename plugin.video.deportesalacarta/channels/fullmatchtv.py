# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para FullMatchTV
#------------------------------------------------------------

from core import httptools
from core import logger
from core import config
from core import scrapertools
from core.item import Item

__channel__ = "fullmatchtv"


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=__channel__, title="Novedades" , action="novedades", url="http://fullmatchtv.com/", thumbnail=item.thumbnail, fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Deportes" , action="categorias", url="http://fullmatchtv.com/", thumbnail=item.thumbnail, fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Buscar..."      , action="search", thumbnail=item.thumbnail, fanart=item.fanart))

    return itemlist

def search(item,texto):
    logger.info()
    itemlist = []
    item.url = "http://fullmatchtv.com/?s=" + texto
    return busqueda(item)

def novedades(item):
    logger.info()
    itemlist = []
    if item.url.startswith("action"):
        data = httptools.downloadpage("http://fullmatchtv.com/wp-admin/admin-ajax.php?td_theme_name=Newspaper&v=6.6.2", post=item.url).data
        data = scrapertools.decodeHtmlentities(data)
        data = data.replace("\\","")
        current_page = scrapertools.find_single_match(item.url, 'td_current_page=(\d+)&')
        if item.title != "Novedades":
            is_next_page = scrapertools.find_single_match(data, '"td_hide_next":(\w+)\}')
            if is_next_page == "false": max_page = int(item.extra) + 1
            else: max_page = item.extra
        else:
            max_page = item.extra
    else:
        data = httptools.downloadpage(item.url).data
        data = scrapertools.decodeHtmlentities(data)
        current_page = "1"
        block = scrapertools.find_single_match(data, 'id="next-page-([^"]+)"')
        if block != "":
            max_page = scrapertools.find_single_match(data, block+'.max_num_pages = "([^"]+)"')
            atts = "&td_atts="+scrapertools.find_single_match(data, block+".atts = '([^']+)'")
            id = "&td_block_id="+scrapertools.find_single_match(data, block+'.id = "([^"]+)"')
            type = "&block_type="+scrapertools.find_single_match(data, block+'.block_type = "([^"]+)"')
            column = "&td_column_number="+scrapertools.find_single_match(data, block+'.td_column_number = "([^"]+)"')
            item.url = "action=td_ajax_block"+ atts + id + column + "&td_current_page="+ current_page + type
        else:
            max_page = 0

    if item.extra == "1" : patron = '(?:<div class="td_module_mx|<div class="td-block-span6">).*?<div class="td-module-thumb"><a href="([^"]+)".*?title="([^"]+)".*?src="([^"]+)".*?datetime.*?>(\w+) (\d+), (\d+)</time>'
    else: patron = '<div class="td-block-span(?:6|4)">.*?<div class="td-module-thumb"><a href="([^"]+)".*?title="([^"]+)".*?src="([^"]+)".*?datetime.*?>(\w+) (\d+), (\d+)</time>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail, mes, dia, year in matches:
        from time import strptime
        mes = str(strptime(mes,'%b').tm_mon)
        fecha = "[COLOR indianred]["+dia+"/"+mes+"/"+year+"][/COLOR] "
        scrapedtitle = fecha + "[COLOR darkorange]"+scrapedtitle+"[/COLOR]"
        itemlist.append(Item(channel=__channel__, title=scrapedtitle, url=scrapedurl, action="findvideos", thumbnail=scrapedthumbnail, fanart=item.fanart))

    if int(current_page) < int(max_page):
        next_page = int(current_page) + 1
        item.url = item.url.replace('td_current_page='+current_page, 'td_current_page='+str(next_page))
        itemlist.append(Item(channel=__channel__, title=">> Siguiente", url=item.url, action="novedades", extra=next_page, thumbnail=item.thumbnail, fanart=item.fanart))

    return itemlist

def categorias(item):
    logger.info()
    itemlist = []

    post = 'action=td_ajax_block&td_atts={"custom_title":"Latest Videos","limit":"10","td_ajax_filter_type"' \
           ':"td_category_ids_filter","ajax_pagination":"next_prev",' \
           '"class":"td_uid_4_57177265efb00_rand"}' \
           '&td_block_id=td_uid_4_57177265efb00&td_column_number=2&td_current_page=1&block_type=td_block_3&td_filter_value=%s'


    itemlist.append(Item(channel=__channel__, title="Baloncesto", url=post % "114", action="novedades", thumbnail=item.thumbnail, extra="1", fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Fútbol", url=post % "119", action="novedades", thumbnail=item.thumbnail, extra="1", fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Fútbol Americano", url=post % "115", action="novedades", thumbnail=item.thumbnail, extra="1", fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Béisbol (MLB)", url=post % "116", action="novedades", thumbnail=item.thumbnail, extra="1", fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Motor", url=post % "1110", action="novedades", thumbnail=item.thumbnail, extra="1", fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="NHL", url=post % "117", action="novedades", thumbnail=item.thumbnail, extra="1", fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Rugby", url=post % "120", action="novedades", thumbnail=item.thumbnail, extra="1", fanart=item.fanart))
    itemlist.append(Item(channel=__channel__, title="Otros Deportes", url=post % "1150", action="novedades", thumbnail=item.thumbnail, extra="1", fanart=item.fanart))

    return itemlist

def busqueda(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.decodeHtmlentities(data)

    matches = scrapertools.find_multiple_matches(data, '<div class="td-module-thumb"><a href="([^"]+)".*?title="([^"]+)".*?src="([^"]+)".*?datetime.*?>(\w+) (\d+), (\d+)</time>')
    for scrapedurl, scrapedtitle, scrapedthumbnail, mes, dia, year in matches:
        from time import strptime
        mes = str(strptime(mes,'%b').tm_mon)
        fecha = "[COLOR indianred]["+dia+"/"+mes+"/"+year+"][/COLOR] "
        scrapedtitle = fecha + "[COLOR darkorange]"+scrapedtitle+"[/COLOR]"
        scrapedthumbnail = scrapedthumbnail.replace("150x150","324x160")
        itemlist.append(Item(channel=__channel__, title=scrapedtitle, url=scrapedurl, action="findvideos", thumbnail=scrapedthumbnail))


    next_page = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)"')
    if next_page:
        itemlist.append(Item(channel=__channel__, title=">> Siguiente", url=next_page, action="busqueda", thumbnail=item.thumbnail, fanart=item.fanart))

    return itemlist
