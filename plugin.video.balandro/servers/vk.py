# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger
import urllib


def normalizar_url(page_url):
    try:
        oid, nid = scrapertools.find_single_match(page_url, "oid=(\d+)&id=(\d+)")
        return 'https://vk.com/video%s_%s' % (oid, nid)
    except:
        return page_url


def get_video_url(page_url, url_referer=''):
    logger.info("url=" + page_url)
    video_urls = []

    page_url = normalizar_url(page_url)
    
    data = httptools.downloadpage('https://getvideo.org/en').data
    token = scrapertools.find_single_match(data, '<meta name="csrf-token" content="([^"]+)')

    post = {'ajax': '1', 'token': token, 'url': page_url}
    data = httptools.downloadpage('https://getvideo.org/en/get_video', post=urllib.urlencode(post)).data

    matches = scrapertools.find_multiple_matches(data, ' href="([^"]+)" class="[^"]*" data="([^"]+)')
    for url, lbl in matches:
        url_final = urllib.unquote(url.split('&url=')[1])
        if url_final:
            video_urls.append([lbl, url_final])

    video_urls.reverse()
    return video_urls
