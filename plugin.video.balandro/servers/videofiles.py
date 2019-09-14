# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger


def get_video_url(page_url, url_referer=''):
    logger.info("url=" + page_url)
    video_urls = []

    data = httptools.downloadpage(page_url).data
    # ~ logger.debug(data)

    espera = scrapertools.find_single_match(data, '<span id="cxc">(\d+)</span>')
    if espera:
        import time
        from platformcode import platformtools
        platformtools.dialog_notification('Cargando videofiles', 'Espera de %s segundos requerida' % espera)
        time.sleep(int(espera))

    post = ''
    matches = scrapertools.find_multiple_matches(data, '<input type="hidden" name="([^"]+)" value="([^"]*)">')
    for inputname, inputvalue in matches:
        post += inputname + "=" + inputvalue + "&"
    post += 'imhuman=Proceed+to+video'
    data = httptools.downloadpage(page_url, post=post).data
    # ~ logger.debug(data)

    matches = scrapertools.find_multiple_matches(data, '{src: "([^"]+)", type: "([^"]+)", res: ([\d]+), label: "([^"]+)"')
    for url, typ, lbl, res in matches:
        video_urls.append(['%sp' % res, url])
    
    video_urls.reverse() # calidad increscendo
    return video_urls
