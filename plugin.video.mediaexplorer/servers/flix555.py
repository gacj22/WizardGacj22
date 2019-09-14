# -*- coding: utf-8 -*-
from core.libs import *
import js2py

def get_video_url(item):
    logger.trace()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    packed = scrapertools.find_single_match(data, "<script type='text/javascript'>eval(.*?)</script>")

    sources, sub = scrapertools.find_single_match(js2py.eval_js(packed), 'sources:(\[[^\]]+]).*?tracks:(\[[^\]]+])')
    sub = scrapertools.find_single_match(sub, 'file:"([^"]+)"')

    for s in scrapertools.find_multiple_matches(sources, 'file:"([^"]+)",label:"([^"]+)"'):
        itemlist.append(Video(url=s[0], res=s[1], subtitle=sub if not sub.endswith("empty.srt") else None))

    return itemlist

