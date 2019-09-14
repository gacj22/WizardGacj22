# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger


def get_video_url(page_url, url_referer=''):
    logger.info("url=" + page_url)
    video_urls = []

    resp = httptools.downloadpage(page_url)
    if resp.code == 500:
        return 'Error de servidor, inténtelo más tarde'
    if resp.code == 404:
        return 'El archivo no existe o ha sido borrado'
    if not resp.data or "urlopen error [Errno 1]" in str(resp.code):
        return 'El archivo no está disponible'
    if "Object not found" in resp.data:
        return 'El archivo no existe o ha sido borrado'
    data = resp.data
    # ~ logger.debug(data)

    post = "confirm.x=77&confirm.y=76&block=1"
    if "Please click on this button to open this video" in data:
        data = httptools.downloadpage(page_url, post=post).data

    match = scrapertools.find_multiple_matches(data, 'https://www.rapidvideo.com/e/[^"]+')
    if match:
        for url1 in match:
           res = scrapertools.find_single_match(url1, '=(\w+)')
           data = httptools.downloadpage(url1).data
           if "Please click on this button to open this video" in data:
               data = httptools.downloadpage(url1, post=post).data
           url = scrapertools.find_single_match(data, 'source src="([^"]+)')
           ext = scrapertools.get_filename_from_url(url)[-4:]
           video_urls.append(['%s %s' % (ext, res), url])

    else:
        match = scrapertools.find_multiple_matches(data, '<source src="([^"]+)" type="([^"]+)" label="([^"]+)"')
        for url, tipo, lbl in match:
            video_urls.append(['%s %s' % (tipo, lbl), url])

    return video_urls
