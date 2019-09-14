# -*- coding: utf-8 -*-
from core.libs import *

res = {
    'mobile': '144p',
    'lowest': '240p',
    'low': '360p',
    'sd': '480p',
    'hd': '720p',
    'full': '1080p'
}


def get_video_url(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data

    if "copyrightsRestricted" in data or "COPYRIGHTS_RESTRICTED" in data:
        return ResolveError(0)

    elif "notFound" in data:
        return ResolveError(0)

    patron = '{\\\\"name\\\\":\\\\"(?P<res>[^"]+)\\\\",\\\\"url\\\\":\\\\"(?P<url>[^"]+)\\\\"'

    for result in re.compile(patron, re.DOTALL).finditer(data):
        itemlist.append(Video(
            url=result.group('url').replace('\\\\u0026', '&'),
            res=res[result.group('res')],
            type='.mp4'
        ))

    return itemlist
