# -*- coding: utf-8 -*-
from core.libs import *


def get_video_url(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data

    if "File was deleted" in data or "File not found" in data:
        return ResolveError(0)

    url = scrapertools.find_single_match(data, '<meta property="og:video" content="([^"]+)"')
    url = urlparse.urljoin('https://www.yourupload.com', url)
    headers = {'Referer': item.url}
    itemlist.append(Video(url=url, headers=headers))
    return itemlist