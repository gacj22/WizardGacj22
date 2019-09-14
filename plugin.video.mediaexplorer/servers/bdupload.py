# -*- coding: utf-8 -*-
from core.libs import *
# TODO: No funciona, solo admite una conexion simulanea, insuficiente para reproducir un .mp4


def get_video_url(item):
    logger.trace()
    itemlist = list()

    post = {
        'id': item.url.split('/')[-1],
        'op': 'download2'
    }

    data = httptools.downloadpage(item.url, post=post).data
    url = scrapertools.find_single_match(data, '(http[^\n\s<>]+\.mp4)')

    if url:
        itemlist.append(Video(url=url))

    return itemlist
