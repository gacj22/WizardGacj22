# -*- coding: utf-8 -*-

from core import httptools, scrapertools, jsontools
from platformcode import logger, platformtools


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    
    page_url = page_url.replace('/embed#', '/#')
    try:
        from lib.megaserver import Client
        c = Client(url=page_url, is_playing_fnc=platformtools.is_playing)
        files = c.get_files()

        # si hay mas de 5 archivos crea un playlist con todos
        if len(files) > 5:
            media_url = c.get_play_list()
            video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:], media_url])
        else:
            for f in files:
                media_url = f["url"]
                video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:], media_url])

    except Exception as inst:
        msg = str(inst)
        # ~ logger.error(msg)
        if 'Enlace no válido' in msg or 'módulos de criptografía' in msg: return msg
        else: return 'No se puede resolver el enlace'

    return video_urls
