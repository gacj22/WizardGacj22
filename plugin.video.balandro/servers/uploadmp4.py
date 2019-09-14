# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    data = httptools.downloadpage(page_url).data
    # ~ logger.debug(data)

    if '<title>Error -' in data:
        return 'El archivo no existe o ha sido borrado'

    scraped = scrapertools.find_single_match(data, '"label":"([^"]+)","type":"[^"]*","file":"([^"]+)')
    if scraped:
        video_urls.append(['%s' % scraped[0], scraped[1]])
    else:
        url = scrapertools.find_single_match(data, '"file"\s*:\s*"([^"]+)')
        if url != '':
            video_urls.append(['MP4', url])

    return video_urls
