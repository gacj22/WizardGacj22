# -*- coding: utf-8 -*-

from core import httptools, scrapertools
from platformcode import logger
import re


def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    data = httptools.downloadpage(page_url).data

    if 'File does not exist on this server' in data:
        return 'El archivo no existe'
    elif 'File has expired and does not exist anymore on this server' in data:
        return 'El archivo ha sido eliminado'

    match = re.search('(.+)/v/(\w+)/file.html', page_url)
    domain = match.group(1)

    patron = 'getElementById\(\'dlbutton\'\).href\s*=\s*(.*?);'
    media_url = scrapertools.find_single_match(data, patron)
    numbers = scrapertools.find_single_match(media_url, '\((.*?)\)')
    url = media_url.replace(numbers, "'%s'" % eval(numbers))
    url = eval(url)

    mediaurl = '%s%s' % (domain, url)
    extension = "." + mediaurl.split('.')[-1]
    video_urls.append([extension, mediaurl])

    return video_urls
