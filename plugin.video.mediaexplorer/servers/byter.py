# -*- coding: utf-8 -*-
from core.libs import *


def get_video_url(item):
    logger.trace()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    url = scrapertools.find_single_match(data, '(http[^\n]+\.mp4)')

    if url:
        itemlist.append(Video(url=url))

    return itemlist
