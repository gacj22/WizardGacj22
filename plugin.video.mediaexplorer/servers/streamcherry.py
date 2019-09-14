# -*- coding: utf-8 -*-
from core.libs import *


def get_video_url(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data

    if "File not found" in data:
        return ResolveError(0)

    for code, key, res in scrapertools.find_multiple_matches(data, "src:d\('([^']+)',(\d+)\),height:(\d+)"):
        itemlist.append(Video(url=decode(code, int(key)), res=res, type='mp4'))

    return itemlist


def decode(code, key):
    k = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='[::-1]
    url = ''
    code = re.sub(r'[^A-Za-z0-9+/=]', '', code)

    for i in range(0, len(code), 4):

        url += chr((k.index(code[i]) << 0x2 | k.index(code[i + 1]) >> 0x4) ^ key)

        if k.index(code[i + 2]) != 0x40:
            url += chr((k.index(code[i + 1]) & 0xf) << 0x4 | k.index(code[i + 2]) >> 0x2)

        if k.index(code[i + 3]) != 0x40:
            url += chr((k.index(code[i + 2]) & 0x3) << 0x6 | k.index(code[i + 3]))

    return "http:" + url
