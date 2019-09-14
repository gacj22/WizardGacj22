# -*- coding: utf-8 -*-

from core import httptools, scrapertools, jsontools
from platformcode import logger

# ~ https://www.adslzone.net/2019/06/19/openload-no-funciona-dominio/
# ~ Alternativas a Openload.co : Openload.pw, Oload.stream, Oload.tv, Oload.club y Oload.life

def get_video_url(page_url, url_referer=''):
    logger.info()
    itemlist = []
    page_url = page_url.replace('openload.co/', 'oload.tv/')

    header = {}
    if "|" in page_url:
        page_url, referer = page_url.split("|", 1)
        header = {'Referer': referer}
    elif url_referer != '':
        header = {'Referer': url_referer}

    data = httptools.downloadpage(page_url, cookies=False, headers=header).data
    # ~ logger.debug(data)

    # Verificar si existe
    file_id = scrapertools.find_single_match(data, 'fileid="([^"]+)"')
    if not file_id:
        return 'El archivo no existe o ha sido borrado'

    # ~ url_api = 'https://api.oload.tv/1/file/info?file=' + file_id
    # ~ verif = httptools.downloadpage(url_api).data
    # ~ mida = scrapertools.find_single_match(verif, '"size":"([^"]+)"')
    # ~ if len(mida) <= 4:
        # ~ logger.debug(verif)
        # ~ return 'El archivo no está disponible'


    subtitle = scrapertools.find_single_match(data, '<track kind="captions" src="([^"]+)" srclang="es"')
    try:
        code = scrapertools.find_single_match(data, '<p style="" id="[^"]+">(.*?)</p>' )
        if code == '': code = scrapertools.find_single_match(data, '<p id="[^"]+" style="">(.*?)</p>' )
        _0x59ce16 = eval(scrapertools.find_single_match(data, '_0x59ce16=([^;]+)').replace('parseInt', 'int'))
        _1x4bfb36 = eval(scrapertools.find_single_match(data, '_1x4bfb36=([^;]+)').replace('parseInt', 'int'))
        parseInt  = eval(scrapertools.find_single_match(data, '_0x30725e,(\(parseInt.*?)\),').replace('parseInt', 'int'))
        url = decode(code, parseInt, _0x59ce16, _1x4bfb36)
        if url == '': return itemlist

        url = httptools.downloadpage(url, only_headers=True, follow_redirects=False).headers.get('location')

        extension = scrapertools.find_single_match(url, '(\..{,3})\?')
        itemlist.append([extension, url, 0, subtitle])

    except:
        logger.info('Falla decodificación Openload')

    # ~ logger.debug(itemlist)
    return itemlist


def decode(code, parseInt, _0x59ce16, _1x4bfb36):
    logger.info()
    import math

    _0x1bf6e5 = ''
    ke = []

    for i in range(0, len(code[0:9*8]),8):
        ke.append(int(code[i:i+8],16))

    _0x439a49 = 0
    _0x145894 = 0

    while _0x439a49 < len(code[9*8:]):
        _0x5eb93a = 64
        _0x896767 = 0
        _0x1a873b = 0
        _0x3c9d8e = 0
        while True:
            if _0x439a49 + 1 >= len(code[9*8:]):
                _0x5eb93a = 143;

            _0x3c9d8e = int(code[9*8+_0x439a49:9*8+_0x439a49+2], 16)
            _0x439a49 +=2

            if _0x1a873b < 6*5:
                _0x332549 = _0x3c9d8e & 63
                _0x896767 += _0x332549 << _0x1a873b
            else:
                _0x332549 = _0x3c9d8e & 63
                _0x896767 += int(_0x332549 * math.pow(2, _0x1a873b))

            _0x1a873b += 6
            if not _0x3c9d8e >= _0x5eb93a: break

        # _0x30725e = _0x896767 ^ ke[_0x145894 % 9] ^ _0x59ce16 ^ parseInt ^ _1x4bfb36
        _0x30725e = _0x896767 ^ ke[_0x145894 % 9] ^ parseInt ^ _1x4bfb36
        _0x2de433 = _0x5eb93a * 2 + 127

        for i in range(4):
            _0x3fa834 = chr(((_0x30725e & _0x2de433) >> (9*8/ 9)* i) - 1)
            if _0x3fa834 != '$':
                _0x1bf6e5 += _0x3fa834
            _0x2de433 = (_0x2de433 << (9*8/ 9))

        _0x145894 += 1

    if _0x1bf6e5 == '': return ''
    url = "https://oload.tv/stream/%s?mime=true" % _0x1bf6e5
    return url
