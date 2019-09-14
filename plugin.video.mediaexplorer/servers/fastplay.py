# -*- coding: utf-8 -*-
from core.libs import *
import js2py


def get_video_url(item):
    logger.trace()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    if "Object not found" in data or "404 Not Found" in data:
        return ResolveError(0)

    packed = scrapertools.find_single_match(data, "<script type='text/javascript'>eval(.*?)</script>")
    data = js2py.eval_js(packed)

    videos = scrapertools.find_multiple_matches(data, 'file\s*:\s*"([^"]+)",label:"(.*?)"')
    subtitle = scrapertools.find_single_match(data, 'tracks:\s*\[{file:"(.*?)"')

    for url, res in videos:
        itemlist.append(Video(
            url=url,
            res=res,
            subtitle=urlparse.urljoin("http://fastplay.cc", subtitle),
            headers={'Referer': item.url}
        ))

    return itemlist
