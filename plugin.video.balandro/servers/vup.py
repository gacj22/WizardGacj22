# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger


def get_video_url(page_url, url_referer=''):
    logger.info("url=" + page_url)
    video_urls = []
    
    resp = httptools.downloadpage(page_url)
    # ~ logger.debug(resp.data)
    
    if 'no longer exists' in resp.data or 'to copyright issues' in resp.data:
        return 'El archivo ha sido eliminado o no existe'

    data = scrapertools.find_single_match(resp.data, 'sources:\s*\[(.*?)\]')
    
    matches = scrapertools.find_multiple_matches(data, '"(http[^"]+)"')
    for url in matches:
        extension = scrapertools.get_filename_from_url(url)[-4:]
        video_urls.append([extension, url])

    return video_urls
