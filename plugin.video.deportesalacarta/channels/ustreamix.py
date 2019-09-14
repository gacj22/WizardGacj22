# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para Ustreamix
# ------------------------------------------------------------

from base64 import b64decode as b64

import re

from core import config
from core import httptools
from core import logger
from core import scrapertools


def mainlist(item):
    logger.info()
    itemlist = entradas(item)

    return itemlist


def entradas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage("http://v2.ustreamix.com").data
    bloque = scrapertools.find_single_match(data, '<h3>Channel Listing</h3>(.*?)</div>')
    if re.search(r'(?i)Your Request is too Often', data) or not bloque:
        import time
        time.sleep(5)
        data = httptools.downloadpage("http://v2.ustreamix.com").data

    bloque = scrapertools.find_single_match(data, '<h3>Channel Listing</h3>(.*?)</div>')
    patron = '<p><a href="([^"]+)".*?>\s*(.*?)\s*<span class="status_live">(.*?)</span>'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for url, title, subt in matches:
        url = "http://v2.ustreamix.com%s" % url
        title = "%s  [COLOR limegreen][%s][/COLOR]" % (title.capitalize(), subt)
        itemlist.append(item.clone(action="play", title=title, url=url))

    itemlist.sort(key=lambda it: it.title)
    return itemlist
    

def play(item):
    itemlist = []

    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, '<script>var.*?var.*?(\[.*?\])')
    #logger.info(data)
    values = scrapertools.find_multiple_matches(bloque, '"([^"]+)"')
    number = scrapertools.find_single_match(data, 'String.fromCharCode.*?(\d+)\);')
    result = ""
    for v in values:
        deco = re.sub(r'(\D)', '', b64(v))
        result += chr(int(deco) - int(number))
    #logger.info(result)
    url = scrapertools.find_single_match(result, "var stream = '([^']+)'")
    url_token = scrapertools.find_single_match(result, 'src="(http://tmg[^"]+)"')
    data = httptools.downloadpage(url_token, headers={'Referer': item.url}).data
    token = scrapertools.find_single_match(data, 'jdtk="([^"]+)"')

    itemlist.append(item.clone(action="play", url=url+token+"|User-Agent=Mozilla/5.0"))

    return itemlist
