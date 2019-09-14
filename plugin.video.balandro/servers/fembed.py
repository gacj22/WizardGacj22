# -*- coding: utf-8 -*-

from core import httptools, scrapertools, jsontools
from platformcode import logger


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    page_url = page_url.replace("/v/","/api/source/").replace("/f/","/api/source/")

    data = httptools.downloadpage(page_url, post={}).data
    data = jsontools.load(data)
    # ~ logger.debug(data)
    
    if 'data' not in data or 'success' not in data: return 'Vídeo no encontrado'
    if not data['success']: return 'Vídeo no encontrado o eliminado'

    for videos in data['data']:
        if 'file' in videos:
            url = videos['file'] if videos['file'].startswith('http') else 'https://www.fembed.com' + videos['file']
            video_urls.append([videos['label'], url])

    return video_urls
