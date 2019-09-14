# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger, platformtools
from lib import jsunpack


def normalizar_url(page_url):
    vid = scrapertools.find_single_match(page_url, "flix555.com/(?:embed-|)([A-z0-9]+)")
    return 'https://flix555.com/embed-%s.html' % vid


def get_video_url(page_url, url_referer=''):
    logger.info()
    itemlist = []

    page_url = normalizar_url(page_url)

    resp = httptools.downloadpage(page_url)
    if resp.code == 503:
        return 'Servidor temporalmente fuera de servicio'
    if resp.code == 404 or '<b>File Not Found</b>' in resp.data:
        return 'El vídeo no está disponible'
    # ~ logger.info(resp.data)

    packed = scrapertools.find_single_match(resp.data, "<script type=[\"']text/javascript[\"']>(eval.*?)</script>")
    if packed:
        unpacked = jsunpack.unpack(packed)
        # ~ logger.info(unpacked)

        tracks = scrapertools.find_single_match(unpacked, 'tracks:\[(.*?)\]')
        subtitle = scrapertools.find_single_match(tracks, 'file\s*:\s*"([^"]*)')
        if 'empty.srt' in subtitle: subtitle = ''

        sources = scrapertools.find_single_match(unpacked, 'sources:\[(.*?)\]')
        matches = scrapertools.find_multiple_matches(sources, 'file\s*:\s*"([^"]*)"\s*,\s*label\s*:\s*"([^"]*)"')
        if matches:
            for url, lbl in matches:
                itemlist.append(['[%s]' % lbl, url, 0, subtitle])

    itemlist.reverse() # calidad increscendo
    return itemlist
