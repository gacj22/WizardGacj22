# -*- coding: utf-8 -*-
from core.libs import *
import js2py


def get_video_url(item):
    logger.trace()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    post = {
        'op': 'download2',
        'id': scrapertools.find_single_match(data, '<input.*?name="id" value="([^"]+)">'),
        'fname': scrapertools.find_single_match(data, '<input.*?name="fname" value="([^"]+)">'),
    }

    data = httptools.downloadpage(item.url, post).data

    url = scrapertools.find_single_match(data, "window.open\('([^']+)'\)")
    itemlist.append(Video(url=url))

    return itemlist
