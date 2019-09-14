# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger
from lib import jsunpack


def get_video_url(page_url, url_referer=''):
    logger.info("url=" + page_url)
    video_urls = []

    resp = httptools.downloadpage(page_url)
    if resp.code == 404:
        return 'El archivo no existe o ha sido borrado'

    data = resp.data
    # ~ logger.debug(data)
    
    video_urls = extraer_videos(data)

    if len(video_urls) == 0:
        enc_data = scrapertools.find_single_match(data, "type='text/javascript'>(.*?)</script>")
        if enc_data:
            try:
                data = jsunpack.unpack(enc_data)
                # ~ logger.debug(data)
                video_urls = extraer_videos(data)
            except:
                pass

    return video_urls


def extraer_videos(data):
    video_urls = []

    sources = scrapertools.find_single_match(data, "<source(.*?)</source")
    matches = scrapertools.find_multiple_matches(sources, 'src="([^"]+)')
    for url in matches:
        quality = 'm3u8'
        video_url = url
        if 'label' in url:
            url = url.split(',')
            video_url = url[0]
            quality = url[1].replace('label:','')
        video_urls.append([quality, video_url])
    return video_urls
