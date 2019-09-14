# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    data = httptools.downloadpage(page_url).data
    # ~ logger.debug(data)

    if 'File has been removed or does not exist!' in data:
        return 'El archivo no existe o ha sido borrado'

    url = scrapertools.find_single_match(data, "file\s*:\s*'([^']+)")
    if url == '': url = scrapertools.find_single_match(data, 'file\s*:\s*"([^"]+)')

    if url != '':
        video_urls.append(["%s" % url[-3:], url])

    return video_urls
