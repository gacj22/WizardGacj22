# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger
import re


def get_video_url(page_url, url_referer=''):
    logger.info("url=" + page_url)
    video_urls = []

    if '/player?' not in page_url:
        nid = scrapertools.find_single_match(page_url, "https://(?:vidcloud.co|vcstream.to)/(?:embed|v)/([a-z0-9]+)")
        page_url = 'https://vidcloud.co/player?fid=%s&page=embed' % nid

    resp = httptools.downloadpage(page_url)
    # ~ logger.debug(resp.data)

    if resp.code == 404:
        return 'El archivo no existe o ha sido borrado'

    data = resp.data.replace('\\\\', '\\').replace('\\','')

    matches = re.compile('"file":"([^"]+)"', re.DOTALL).findall(data)
    for url in matches:
        if not ".vtt" in url:
            video_urls.append(['mp4', url])

    return video_urls
