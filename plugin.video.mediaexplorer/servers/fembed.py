# -*- coding: utf-8 -*-
from core.libs import *


def get_video_url(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url, post={}).data

    if "Video not found" in data:
        return ResolveError(0)

    data = jsontools.load_json(data)
    if data.get("success"):
        for video in data["data"]:
            itemlist.append(Video(url=video['file'], res=video['label'], type=video['type']))
    else:
        # Falló por otro motivo
        return ResolveError(data["data"])

    return itemlist
