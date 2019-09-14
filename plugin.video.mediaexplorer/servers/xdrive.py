# -*- coding: utf-8 -*-
from core.libs import *


def get_video_url(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, 'source src="([^"]+)"')

    if url:
        itemlist.append(Video(url=url.split('?')[0]))
    return itemlist
