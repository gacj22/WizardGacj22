# -*- coding: utf-8 -*-
from core.libs import *

def get_video_url(item):
    logger.trace()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    if "video was deleted" in data:
        return ResolveError(0)

    sources = scrapertools.find_single_match(data, 'sources:.\[(.*?)]')
    sources = scrapertools.find_multiple_matches(sources, '"http([^"]+)')
    res = scrapertools.find_single_match(data, 'labels:.{([^}]+)')
    res = {int(k):v for k,v in scrapertools.find_multiple_matches(res, "(\d+):.'(.*?)'")}

    for n, url in enumerate(sources):
        itemlist.append(Video(url='http' + url, res=res[n]))

    return itemlist