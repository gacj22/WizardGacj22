# -*- coding: utf-8 -*-
from core.libs import *


def get_video_url(item):
    logger.trace()
    itemlist = []
    try:
        from megaserver import Client
    except Exception, e:
        return str(e)
    c = Client(url=item.url, is_playing_fnc=platformtools.is_playing)

    files = c.get_files()

    # si hay mas de 5 archivos crea un playlist con todos
    if len(files) > 5:
        itemlist.append(Video(url=c.get_play_list()))
    else:
        for f in files:
            itemlist.append(Video(url=f["url"]))

    return itemlist
