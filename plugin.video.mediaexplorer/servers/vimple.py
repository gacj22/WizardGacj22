# -*- coding: utf-8 -*-
# TODO: No encuentro ningún enlace qque funcione parece que todos han sido borrados
from core.libs import *


def get_video_url(item):
    logger.trace()
    itemlist = list()

    req = httptools.downloadpage(item.url)

    if '"title":"Video Not Found"' in req.data:
        return ResolveError(0)

    url = scrapertools.find_single_match(req.data, '"video"[^,]+,"url":"([^"]+)"').replace('\\', '')

    headers = {
        'User-Agent': httptools.default_headers['User-Agent'],
        'Cookie' : '__cfduid=%s; UniversalUserID=%s' % (
            req.cookies.get('__cfduid', ''),
            req.cookies.get('UniversalUserID', '')
        )
    }

    itemlist.append(Video(url=url, headers=headers))

    return itemlist
