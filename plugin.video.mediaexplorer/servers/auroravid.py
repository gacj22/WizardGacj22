# -*- coding: utf-8 -*-
from core.libs import *


def get_video_url(item):
    logger.trace()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    if "This file no longer exists on our servers" in data:
        return ResolveError(0)
    elif "is being converted" in data:
        return ResolveError(1)

    urls = scrapertools.find_multiple_matches(data, 'src\s*:\s*[\'"]([^\'"]+)[\'"]') or \
        scrapertools.find_multiple_matches(data, '<source src=[\'"]([^\'"]+)[\'"]')

    for url in urls:
        if url.endswith(".mpd"):
            video_id = scrapertools.find_single_match(url, '/dash/(.*?)/')
            url = "http://www.auroravid.to/download.php?file=mm%s.mp4" % video_id

        url = re.sub(r'/dl(\d)*/', '/dl/', url)

        itemlist.append(Video(url=url))

    return itemlist
