# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger
from lib import jsunpack


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    data = httptools.downloadpage(page_url).data
    # ~ logger.debug(data)

    if "Video not found..." in data:
        return 'El archivo ya no está presente en el servidor'
    if "Video removed for inactivity..." in data:
        return 'El video ha sido retirado por inactividad'

    packed = scrapertools.find_multiple_matches(data, "(?s)<script>\s*eval(.*?)\s*</script>")
    for pack in packed:
        unpacked = jsunpack.unpack(pack)
        # ~ logger.debug(unpacked)

        videos = scrapertools.find_multiple_matches(unpacked, 'var vldAb="([^"]+)')
        for video in videos:
            if not video.startswith('//'): continue
            video_urls.append(["mp4", 'https:' + video])

    return video_urls
