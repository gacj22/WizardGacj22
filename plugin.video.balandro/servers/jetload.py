# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger


def get_video_url(page_url, url_referer=''):
    logger.info("url=" + page_url)
    video_urls = []

    data = httptools.downloadpage(page_url).data
    # ~ logger.debug(data)

    if "file can't be found" in data:
        return 'El fichero no existe o ha sido borrado'
    
    srv = scrapertools.find_single_match(data, 'id="srv" value="([^"]+)"')
    srv_id = scrapertools.find_single_match(data, 'id="srv_id" value="([^"]+)"')
    file_name = scrapertools.find_single_match(data, 'id="file_name" value="([^"]+)"')

    if not file_name:
        return 'El fichero no se encuentra'

    if srv_id:
        post = 'file_name=%s.mp4&srv=%s' % (file_name, srv_id)
        url = httptools.downloadpage('https://jetload.net/api/download', post=post).data
        if url.startswith('http'):
            video_urls.append(['mp4', url])

    elif srv:
        archive = scrapertools.find_single_match(data, 'id="archive" value="([^"]+)"')
        
        if archive == '1': url = srv + '/v2/schema/archive/' + file_name
        else: url = srv + '/v2/schema/' + file_name

        video_urls.append(['360P', url + '/min.m3u8'])
        video_urls.append(['480P', url + '/low.m3u8'])
        video_urls.append(['720P', url + '/med.m3u8'])

    # ~ if video_urls:
        # ~ file_id = scrapertools.find_single_match(data, 'id="file_id" value="([^"]+)"')
        # ~ data = httptools.downloadpage('https://jetload.net/api/get/subtitles/' + file_id).data
        # ~ logger.debug(data)

    return video_urls
