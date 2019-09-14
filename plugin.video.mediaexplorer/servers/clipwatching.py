# -*- coding: utf-8 -*-
from core.libs import *
import js2py


def get_video_url(item):
    logger.trace()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    if "404 File not found!" in data:
        return ResolveError(0)

    unpacked = js2py.eval_js(scrapertools.find_single_match(data, "<script type=.text/javascript.>eval(.*?)</script>"))

    for url, res in scrapertools.find_multiple_matches(unpacked, '{file:"([^"]+)",label:"([^"]+)"}'):
        itemlist.append(Video(url=url, res=res))

    return itemlist
