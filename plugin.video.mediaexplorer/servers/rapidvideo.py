# -*- coding: utf-8 -*-
from core.libs import *


def get_video_url(item):
    logger.trace()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    if 'Object not found' in data or 'We are sorry!' in data:
        return ResolveError(0)

    patron = '<source src="([^"]+).*?data-res="([^"]+)"'
    for url, res in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(Video(url=url, res=res, type=url.split('.')[-1]))

    return itemlist
