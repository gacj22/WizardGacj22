# -*- coding: utf-8 -*-

from core.libs import *

def get_video_url(item):
    logger.trace()
    itemlist = []
    if settings.get_setting('premium', __file__):
        post = {
                    'id': settings.get_setting('user', __file__),
                    'pw': settings.get_setting('password', __file__)
               }

        httptools.downloadpage('http://uploaded.net/io/login', post=post)

        url = httptools.downloadpage(item.url, follow_redirects=False, only_headers=True).headers.get('location','')
        
        if not url:
            return ResolveError(2)
        if 'uploaded.net/410' in url:
            return ResolveError(0)
        elif 'uploaded.net/404' in url:
            return ResolveError(0)
        
        itemlist.append(Video(url=url))
    else:
        return ResolveError(3)
        
        
    return itemlist
