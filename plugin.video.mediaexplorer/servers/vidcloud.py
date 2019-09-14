# -*- coding: utf-8 -*-
from core.libs import *

def get_video_url(item):
    logger.trace()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    if scrapertools.find_single_match(data, '"status"\s*:\s*(true|false)') != 'true':
        return ResolveError(0)

    data = data.replace('\\\\', '\\').replace('\\', '')
    sources = scrapertools.find_single_match(data,'sources\s*=\s*\[(.*?)]')
    subtitle = scrapertools.find_single_match(data,'tracks\s*=.*?"file":"([^"]+)".*?]')

    for url in scrapertools.find_multiple_matches(sources, '"file":"([^"]+)"'):
        itemlist.append(Video(url=url, subtitle=subtitle))

    return itemlist