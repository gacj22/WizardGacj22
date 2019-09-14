# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger
from lib import jsunpack


def get_video_url(page_url, url_referer=''):
    logger.info("url=" + page_url)
    video_urls = []
    
    headers = {}
    if url_referer: headers['Referer'] = url_referer

    data = httptools.downloadpage(page_url, headers=headers).data
    # ~ logger.debug(data)
    
    packed = scrapertools.find_single_match(data, "<script type=[\"']text/javascript[\"']>(eval.*?)</script>")
    if packed:
        data = jsunpack.unpack(packed)
        # ~ logger.info(data)

    data = scrapertools.find_single_match(data, 'sources:\s*\[(.*?)\]')
    
    matches = scrapertools.find_multiple_matches(data, '"label"\s*:\s*"([^"]+)"\s*,\s*"type"\s*:\s*"([^"]+)"\s*,\s*"file"\s*:\s*"([^"]+)')
    for lbl, tipo, url in matches:
        video_urls.append(['%s %s' % (tipo, lbl), url])

    return video_urls
