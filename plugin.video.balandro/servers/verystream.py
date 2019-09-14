# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger


def normalizar_url(page_url):
    vid = scrapertools.find_single_match(page_url, "verystream.com/(?:stream|e)/([A-z0-9]+)")
    return 'https://verystream.com/e/%s/' % vid


def get_video_url(page_url, url_referer=''):
    logger.info("url=" + page_url)
    video_urls = []

    page_url = normalizar_url(page_url)

    data = httptools.downloadpage(page_url).data
    # ~ logger.debug(data)

    # ~ from lib import aadecode
    # ~ js = scrapertools.find_single_match(data, "<script>ﾟωﾟ(.*?)</script>")
    # ~ decoded = aadecode.decode(js)
    # ~ logger.debug(decoded)
        # ~ var srclink = '/gettoken/' + $('#videolink').text() + '?mime=true';
    
    vid = scrapertools.find_single_match(data, 'id="videolink">([^<]+)')
    if vid:
        url = 'https://verystream.com/gettoken/%s?mime=true' % vid
        video_urls.append(["mp4 [verystream]", url])

    return video_urls
