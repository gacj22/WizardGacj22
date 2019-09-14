# -*- coding: utf-8 -*-
from core.libs import *

def get_video_url(item):
    logger.trace()
    itemlist = []
    
    data = httptools.downloadpage(item.url).data
    
    if "<h1>404 Not Found</h1>" in data:
        return ResolveError(0)


    post = {}
    matches = scrapertools.find_multiple_matches(data, '<input.*?name="([^"]+)".*?value="([^"]*)">')
    for inputname, inputvalue in matches:
        post[inputname] = inputvalue
        
    post['op'] = 'download2'
    
    data = httptools.downloadpage(item.url, post=post).data
    url = scrapertools.find_single_match(data, 'file\: "([^"]+)"')

    itemlist.append(Video(url=url + '|Referer=' + item.url))

    return itemlist