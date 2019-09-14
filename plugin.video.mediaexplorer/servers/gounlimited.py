# -*- coding: utf-8 -*-
from core.libs import *
import js2py


def get_video_url(item):
    logger.trace()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    unpacked = js2py.eval_js(scrapertools.find_single_match(data, "<script type=.text/javascript.>eval(.*?)</script>"))
    url = scrapertools.find_single_match(unpacked, 'sources:\["([^"]+)"\]')
    itemlist.append(Video(url=url))

    return itemlist
