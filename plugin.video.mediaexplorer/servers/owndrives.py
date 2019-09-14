# -*- coding: utf-8 -*-
from core.libs import *
import base64
import random
import string
import math

def get_video_url(item):
    logger.trace()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    
    if 'Archive no Encontrado' in data:
        return ResolveError(0)

    params = scrapertools.find_multiple_matches(data, 'input.*?name="([^"]*)" value="([^"]*)"')

    data = httptools.downloadpage(item.url, post=dict(params)).data
    key = scrapertools.find_single_match(data, 'data-sitekey="([^"]+)"')


    #itemlist.append(Video(url=url, type=type))

    return itemlist


digs = string.digits + string.letters
def int2base(x, base):
    if x < 0:
        sign = -1
    elif x == 0:
        return digs[0]
    else:
        sign = 1

    x *= sign
    digits = []

    while x:
        digits.append(digs[x % base])
        x /= base

    if sign < 0:
        digits.append('-')

    digits.reverse()

    return ''.join(digits)
