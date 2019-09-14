# -*- coding: utf-8 -*-
from core.libs import *


def get_video_url(item):
    logger.trace()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    url = scrapertools.find_single_match(data, 'type="video/mp4" src="([^"]+)"')

    if url:
        itemlist.append(Video(url=url))

    return itemlist
