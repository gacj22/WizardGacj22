# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger
from lib import jsunpack


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    data = httptools.downloadpage(page_url).data
    # ~ logger.debug(data)

    if "File Not Found" in data or "File was deleted" in data:
        return 'El archivo ya no está presente en el servidor'

    packed = scrapertools.find_single_match(data, "text/javascript'>(.*?)\s*</script>")
    if packed:
        unpacked = jsunpack.unpack(packed)
        # ~ logger.debug(unpacked)
        videos = scrapertools.find_multiple_matches(unpacked, 'file:"([^"]+).*?label:"([^"]+)')
        for video, label in videos:
            if ".jpg" not in video:
                video_urls.append([label, video])

        video_urls.sort(key=lambda it: int(it[0].replace('p','')))

    return video_urls
