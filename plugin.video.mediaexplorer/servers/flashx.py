# -*- coding: utf-8 -*-
import base64

from core.libs import *


def get_video_url(item):
    logger.trace()
    itemlist = []

    video_id = scrapertools.find_single_match(item.url, '[^/]+//[^/]+/[^-=]+(?:-|=)([0-9a-z]+)')

    item.url = 'https://www.flashx.tv/playvideo-%s.html?playvid' % video_id
    data = httptools.downloadpage(item.url, headers={'referer': 'https://www.flashx.tv/embed-%s.html' % video_id}).data

    file_id = base64.b64encode(scrapertools.find_single_match(data, "'file_id', '([^']+)'"))

    if 'Too many views.' in data:
        return ResolveError(4)

    if 'NOT FOUND' in data:
        return ResolveError(0)

    if 'normal.mp4' not in data:
        httptools.downloadpage('https://www.flashx.to/counter.cgi?c2=%s&fx=%s' % (video_id, file_id))
        httptools.downloadpage('https://www.flashx.tv/flashx.php?ss=yes&f=fail&fxfx=6')
        data = httptools.downloadpage(item.url).data

    matches = scrapertools.find_multiple_matches(data, "{src: '([^']+)'.*?,label: '([^']+)',res: ([\d]+)")
    for url, label, res in matches:
        itemlist.append(Video(url=url, res='%sp' % res))

    return itemlist
