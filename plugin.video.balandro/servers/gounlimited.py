# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger
from lib import jsunpack

def normalizar_url(page_url):
    vid = scrapertools.find_single_match(page_url, "gounlimited.to/(?:embed-|)([A-z0-9]+)")
    return "https://gounlimited.to/embed-" + vid + ".html"


def get_video_url(page_url, url_referer=''):
    logger.info("url=" + page_url)
    video_urls = []

    page_url = normalizar_url(page_url)

    data = httptools.downloadpage(page_url).data
    # ~ logger.debug(data)

    packer = scrapertools.find_single_match(data, "<script type='text/javascript'>(eval.function.p,a,c,k,e,d..*?)</script>")
    if packer:
        data = jsunpack.unpack(packer)
        # ~ logger.debug(data)

    mp4 = scrapertools.find_single_match(data, 'sources:\["([^"]+)')
    if mp4: video_urls.append(["mp4", mp4])

    return video_urls
