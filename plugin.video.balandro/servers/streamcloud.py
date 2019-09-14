# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger


def get_video_url(page_url, url_referer=''):
    logger.info("url=" + page_url)
    video_urls = []

    # Lo pide una vez
    headers = [['User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14']]
    data = httptools.downloadpage(page_url, headers=headers).data

    if "<h1>404 Not Found</h1>" in data or "<h1>File Not Found</h1>" in data or "<h1>Archivo no encontrado</h1>" in data:
        return "El archivo no existe o ha sido borrado"

    try:
        media_url = scrapertools.get_match(data, 'file\: "([^"]+)"')
    except:
        post = ""
        matches = scrapertools.find_multiple_matches(data, '<input.*?name="([^"]+)".*?value="([^"]*)">')
        for inputname, inputvalue in matches:
            post += inputname + "=" + inputvalue + "&"
        post = post.replace("op=download1", "op=download2")
        data = httptools.downloadpage(page_url, post=post).data
        # ~ logger.debug(data)

        if 'id="justanotice"' in data:
            logger.info("data=" + data)
            logger.info("Ha saltado el detector de adblock")
            return []

        # Extrae la URL
        media_url = scrapertools.get_match(data, 'file\: "([^"]+)"')

    video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:], media_url+"|Referer="+page_url])

    return video_urls
