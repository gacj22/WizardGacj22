# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger


def normalizar_url(page_url):
    vid = scrapertools.find_single_match(page_url, "(?:vimeo.com/|player.vimeo.com/video/)([0-9]+)")
    return 'https://player.vimeo.com/video/%s' % vid

def get_video_url(page_url, url_referer=''):
    logger.info("url=" + page_url)
    video_urls = []
    
    page_url = normalizar_url(page_url)

    data = httptools.downloadpage(page_url).data
    # ~ logger.debug(data)
    
    patron = '"width":(\d+),"mime":"([^"]+)","fps":\d+,"url":"([^"]+)","cdn":"[^"]+","quality":"([^"]+)","id":\d+,"origin":"[^"]+","height":(\d+)'

    matches = scrapertools.find_multiple_matches(data, patron)
    # ~ for width, mime, url, quality, height in matches:
    for width, mime, url, quality, height in sorted(matches, key=lambda x: int(x[4])):

        video_urls.append(['%s %s' % (mime, quality), url])

    return video_urls
