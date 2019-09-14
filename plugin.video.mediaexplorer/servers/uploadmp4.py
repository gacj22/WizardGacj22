# -*- coding: utf-8 -*-
from core.libs import *

def get_video_url(item):
    logger.trace()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '"label":"([^"]+)","type":"([^"]+)","file":"([^"]+)"'
    for res, type, url in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(Video(url=url, res=res, type= 'MP4' if 'mp4' in type else type))

    return itemlist

