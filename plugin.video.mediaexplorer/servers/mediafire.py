# -*- coding: utf-8 -*-
from core.libs import *


def get_video_url(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data

    if "Invalid or Deleted File" in data:
        return ResolveError(0)

    elif "File Removed for Violation" in data:
        return ResolveError(0)

    url = scrapertools.find_single_match(data, 'kNO\s*=\s*"([^"]+)"')
    if url:
        itemlist.append(Video(url=url))

    return itemlist
