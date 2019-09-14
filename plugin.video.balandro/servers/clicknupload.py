# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger
import urllib


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    data = httptools.downloadpage(page_url).data
    # ~ logger.debug(data)

    post = {
        'op': 'download2',
        'id': scrapertools.find_single_match(data, '<input type="hidden" name="id" value="([^"]+)'),
        'fname': scrapertools.find_single_match(data, '<input type="hidden" name="fname" value="([^"]+)'),
    }

    data = httptools.downloadpage(page_url, post=urllib.urlencode(post)).data
    # ~ logger.debug(data)

    url = scrapertools.find_single_match(data, "window.open\('([^']+)")
    if url:
        video_urls.append(["mp4", url])

    return video_urls
