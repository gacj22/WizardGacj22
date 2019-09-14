# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger


def get_video_url(page_url, url_referer=''):
    logger.info("url=" + page_url)
    video_urls = []

    data = httptools.downloadpage(page_url).data
    # ~ logger.debug(data)

    if '404 Not Found' in data or 'File is no longer available' in data:
        return 'El archivo ha sido eliminado o no existe'

    url = scrapertools.find_single_match(data, 'src\s*:\s*"([^"]+)')
    if url != '':
        video_urls.append(['mp4', url])

    return video_urls
