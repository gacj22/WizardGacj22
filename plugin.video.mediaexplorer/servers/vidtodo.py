# -*- coding: utf-8 -*-
from core.libs import *
import js2py


def get_video_url(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url, headers={'Referer':item.referer}).data
    #logger.debug(data)
    if "Page not found" in data or "File was deleted" in data or "404 Not Found" in data:
        return ResolveError(0)

    packed = scrapertools.find_single_match(data, "<script type='text/javascript'>eval(.*?)</script>")
    logger.debug(packed)
    data = js2py.eval_js(packed)
    logger.debug(data)
    sources = scrapertools.find_single_match(data, 'sources:\s?(\[.*?\]+)')
    logger.debug(sources)
    for url, res in scrapertools.find_multiple_matches(sources, 'file:"([^"]+)",label:"([^"]+)"'):
        itemlist.append(Video(url=url, res=res))

    return itemlist


