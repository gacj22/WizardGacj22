# -*- coding: utf-8 -*-
from core.libs import *

def get_video_url(item):
    logger.trace()
    itemlist = []

    itemlist.append(Video(url=item.url))
    
    return itemlist