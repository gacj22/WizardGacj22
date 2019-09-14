# -*- coding: utf-8 -*-
from core.libs import *


def get_video_url(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    id = scrapertools.find_single_match(data, 'id="videolink">([^<]+)')

    if not id:
        return ResolveError(0)

    itemlist.append(Video(url='https://verystream.com/gettoken/%s?mime=true' % id))

    return itemlist