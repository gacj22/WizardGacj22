# -*- coding: utf-8 -*-
from core.libs import *


def get_video_url(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data

    if "Page not found" in data or "File was deleted" in data or "404 Not Found" in data:
        return ResolveError(0)

    if "Video is processing now" in data:
        return ResolveError(1)

    for url, res in scrapertools.find_multiple_matches(data, 'src:\s*"([^"]+)".*?res:\s*"(\d+)'):
        itemlist.append(Video(url=url, res=res))

    return itemlist
