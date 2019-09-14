# -*- coding: utf-8 -*-

from core import httptools, scrapertools, jsontools
from platformcode import logger


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % (page_url))
    video_urls = []

    # Carga la página para coger las cookies
    data = httptools.downloadpage(page_url).data

    # Nueva url
    url = page_url.replace("embed/", "").replace(".html", ".json")

    # Carga los datos y los headers
    resp = httptools.downloadpage(url)
    if '"error":"video_not_found"' in resp.data or '"error":"Can\'t find VideoInstance"' in resp.data:
        return 'El archivo no existe o ha sido borrado'

    data = jsontools.load(resp.data)
    if 'videos' not in data: return []

    # La cookie video_key necesaria para poder visonar el video
    cookie_video_key = scrapertools.find_single_match(resp.headers["set-cookie"], '(video_key=[a-f0-9]+)')

    # Formar url del video + cookie video_key
    for videos in data['videos']:
        media_url = videos['url'] + "|Referer=https://my1.imgsmail.ru/r/video2/uvpv3.swf?75&Cookie=" + cookie_video_key
        if not media_url.startswith("http"):
            media_url = "http:" + media_url
        quality = " %s" % videos['key']
        video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:] + quality, media_url])

    try:
        video_urls.sort(key=lambda video_urls: int(video_urls[0].rsplit(" ", 2)[1][:-1]))
    except:
        pass

    return video_urls
