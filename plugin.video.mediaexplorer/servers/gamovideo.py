# -*- coding: utf-8 -*-
from core.libs import *
import js2py


def get_video_url(item):
    logger.trace()
    itemlist = []

    headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0',
               'Referer': item.referer,
               'Cookie': 'pfm=1;sugamun=1;'}
    data = httptools.downloadpage(item.url, headers=headers).data

    if 'File was deleted' in data or 'File was locked by administrator' in data:
        return ResolveError(0)
    elif 'Video is processing now' in data:
        return ResolveError(1)
    elif "File is awaiting for moderation" in data:
        return ResolveError(1)
    elif 'Video encoding error' in data:
        return ResolveError(5)

    packed = scrapertools.find_single_match(data, "<script type='text/javascript'>eval(.*?)</script>")
    if packed:
        unpacked = js2py.eval_js(packed)

        video_url = scrapertools.find_single_match(unpacked, 'file:"([^"]+v.mp4)"')
        #logger.debug(video_url)
        if video_url:
            itemlist.append(Video(url=video_url))

        rtmp = scrapertools.find_single_match(unpacked, 'file:"(rtmp://.*?)/(mp4:[^"]+)"')
        #logger.debug(rtmp)
        if len(rtmp) == 2:
            itemlist.append(Video(url=rtmp[0] + "/ playpath=" + rtmp[1] +
                                      " swfUrl=http://gamovideo.com/player61/jwplayer.flash.swf"))

    return itemlist
