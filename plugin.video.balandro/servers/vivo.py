# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger
import base64


def get_video_url(page_url, url_referer=''):
    logger.info("url=" + page_url)
    video_urls = []

    data = httptools.downloadpage(page_url).data
    # ~ logger.debug(data)

    if not 'data-stream=' in data:
        return 'El archivo ha sido eliminado o no existe'

    stream = scrapertools.find_single_match(data, 'data-stream="([^"]+)')
    try:
        media_url = base64.b64decode(stream)
        video_urls.append(['mp4', media_url])
    except:
        pass

    return video_urls
