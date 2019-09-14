# -*- coding: utf-8 -*-
from core.libs import *


def get_video_url(item):
    logger.trace()
    itemlist = []

    video_id = scrapertools.find_single_match(item.url, "[^/]+//[^/]+/([a-zA-Z]+)")
    data = httptools.downloadpage('http://www.adnstream.com/get_playlist.php?lista=video&param=%s&c=463' % video_id)

    url = scrapertools.find_single_match(data, "<jwplayer:file>([^<]+)</jwplayer:file>")
    itemlist.append(Video(url=url))

    return itemlist
