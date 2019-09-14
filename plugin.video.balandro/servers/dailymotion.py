# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    resp = httptools.downloadpage(page_url, cookies=False)
    # ~ logger.debug(data)

    if 'Contenido rechazado' in resp.data or resp.code == 404:
        return 'El archivo no existe o ha sido borrado'

    cookie = {'Cookie': resp.headers["set-cookie"]}
    data = resp.data.replace("\\", "")
    subtitle = scrapertools.find_single_match(data, '"subtitles":.*?"es":.*?urls":\["([^"]+)"')
    qualities = scrapertools.find_multiple_matches(data, '"([^"]+)":(\[\{"type":".*?\}\])')

    for calidad, urls in qualities:
        patron = '"type":"(?:video|application)/([^"]+)","url":"([^"]+)"'
        matches = scrapertools.find_multiple_matches(urls, patron)
        for stream_type, stream_url in matches:
            stream_type = stream_type.replace('x-mpegURL', 'm3u8')
            if stream_type == "mp4":
                stream_url = httptools.downloadpage(stream_url, headers=cookie, only_headers=True,
                                                    follow_redirects=False).headers.get("location", stream_url)
            else:
                data_m3u8 = httptools.downloadpage(stream_url).data
                stream_url_http = scrapertools.find_single_match(data_m3u8, '(http:.*?\.m3u8)')
                if stream_url_http:
                    stream_url = stream_url_http

            video_urls.append(["%sp .%s" % (calidad, stream_type), stream_url, 0, subtitle])

    return video_urls
