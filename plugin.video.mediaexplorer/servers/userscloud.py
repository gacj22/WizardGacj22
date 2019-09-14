# -*- coding: utf-8 -*-
from core.libs import *


def get_video_url(item):
    logger.trace()
    itemlist = list()

    post = {
        'id': item.url.split('/')[-1],
        'method_free': 'Descarga Gratis',
        'op': 'download1'
    }

    data = httptools.downloadpage(item.url, post=post).data

    if not data or \
            "Not Found" in data or \
            "File was deleted" in data or \
            "The file you are trying to download is no longer available" in data:
        return ResolveError(0)

    url = scrapertools.find_single_match(data, '(http[^\n\s<>]+\.mp4)')

    if url:
        itemlist.append(Video(url=url))

    return itemlist
