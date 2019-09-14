# -*- coding: utf-8 -*-
from core.libs import *


def get_video_url(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    time.sleep(int(scrapertools.find_single_match(data, '<span id="cxc">(\d+)</span>') or '0'))

    post = {'imhuman':'Proceed to video'}
    for name, value in scrapertools.find_multiple_matches(data, '<input type="hidden" name="([^"]+)" value="([^"]*)">'):
        post[name] = value

    data = httptools.downloadpage(item.url, post=post).data
    for url, res in scrapertools.find_multiple_matches(data, '{src: "([^"]+)".*?res: (\d+)'):
        itemlist.append(Video(url=url, res=res, type=url.split('.')[-1]))

    return itemlist

