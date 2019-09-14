# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from channels import filtertools, autoplay
from platformcode import config, logger
from channelselector import get_thumb

host = 'http://www.ultrapeliculashd.com'

thumbletras = {'#': 'https://s32.postimg.cc/drojt686d/image.png',
               'a': 'https://s32.postimg.cc/llp5ekfz9/image.png',
               'b': 'https://s32.postimg.cc/y1qgm1yp1/image.png',
               'c': 'https://s32.postimg.cc/vlon87gmd/image.png',
               'd': 'https://s32.postimg.cc/3zlvnix9h/image.png',
               'e': 'https://s32.postimg.cc/bgv32qmsl/image.png',
               'f': 'https://s32.postimg.cc/y6u7vq605/image.png',
               'g': 'https://s32.postimg.cc/9237ib6jp/image.png',
               'h': 'https://s32.postimg.cc/812yt6pk5/image.png',
               'i': 'https://s32.postimg.cc/6nbbxvqat/image.png',
               'j': 'https://s32.postimg.cc/axpztgvdx/image.png',
               'k': 'https://s32.postimg.cc/976yrzdut/image.png',
               'l': 'https://s32.postimg.cc/fmal2e9yd/image.png',
               'm': 'https://s32.postimg.cc/m19lz2go5/image.png',
               'n': 'https://s32.postimg.cc/b2ycgvs2t/image.png',
               'o': 'https://s32.postimg.cc/c6igsucpx/image.png',
               'p': 'https://s32.postimg.cc/jnro82291/image.png',
               'q': 'https://s32.postimg.cc/ve5lpfv1h/image.png',
               'r': 'https://s32.postimg.cc/nmovqvqw5/image.png',
               's': 'https://s32.postimg.cc/zd2t89jol/image.png',
               't': 'https://s32.postimg.cc/wk9lo8jc5/image.png',
               'u': 'https://s32.postimg.cc/w8s5bh2w5/image.png',
               'v': 'https://s32.postimg.cc/e7dlrey91/image.png',
               'w': 'https://s32.postimg.cc/fnp49k15x/image.png',
               'x': 'https://s32.postimg.cc/dkep1w1d1/image.png',
               'y': 'https://s32.postimg.cc/um7j3zg85/image.png',
               'z': 'https://s32.postimg.cc/jb4vfm9d1/image.png'
               }

tcalidad = {'1080P': 'https://s21.postimg.cc/4h1s0t1wn/hd1080.png',
            '720P': 'https://s12.postimg.cc/lthu7v4q5/hd720.png', "HD": "https://s27.postimg.cc/m2dhhkrur/image.png"}


IDIOMAS = {'Latino': 'LAT', 'Español': 'CAST', 'SUB':'VOSE'}
list_language = IDIOMAS.values()
list_quality = ['default', '1080p']
list_servers = ['openload','directo']

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'ultrapeliculashd')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'ultrapeliculashd')

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Todas",
                         action="lista",
                         thumbnail=get_thumb('all', auto=True),
                         url=host + '/movies/'
                         ))

    itemlist.append(Item(channel=item.channel, title="Generos",
                         action="generos",
                         url=host,
                         thumbnail=get_thumb('genres', auto=True)
                         ))

    itemlist.append(Item(channel=item.channel, title="Alfabetico",
                         action="seccion",
                         url=host,
                         thumbnail=get_thumb('alphabet', auto=True),
                         extra='alfabetico'
                         ))

    itemlist.append(Item(channel=item.channel, title="Buscar",
                         action="search",
                         url=host + '/?s=',
                         thumbnail=get_thumb('search', auto=True)
                         ))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def lista(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    if item.extra != 'buscar':
        patron = '<article id=.*?<img src=(.*?) alt=(.*?)>.*?<a href=(.*?)>.*?</h3><span>(.*?)<'
    else:
        patron = '<article><div class=image>.*?<a href=(.*?)\/><img src=(.*?) alt=(.*?) \/>.*?year>(.*?)<\/span>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedtitle, scrapedurl, scrapedyear in matches:
        if item.extra == 'buscar':
            aux = scrapedthumbnail
            scrapedthumbnail=scrapedtitle
            scrapedtitle = scrapedurl
            scrapedurl =  aux


        url = scrapedurl
        thumbnail = scrapedthumbnail
        contentTitle = re.sub(r'\d{4}', '', scrapedtitle)
        contentTitle = contentTitle.replace('|', '')
        contentTitle = contentTitle.strip(' ')
        title = scrapertools.decodeHtmlentities(contentTitle)
        year = scrapedyear
        fanart = ''


        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, contentTitle=item.title, url=url,
                             thumbnail=thumbnail, fanart=fanart, infoLabels={'year': year}))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    # Paginacion

    if itemlist != []:
        actual_page_url = item.url
        next_page = scrapertools.find_single_match(data, '<link rel=next href=(.*?) />')
        if next_page != '':
            itemlist.append(Item(channel=item.channel, action="lista", title='Siguiente >>>', url=next_page,
                                 thumbnail='https://s16.postimg.cc/9okdu7hhx/siguiente.png'))
    return itemlist


def generos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    patron = 'genres menu-item-.*?><a href=(.*?)>(.*?)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        thumbnail = ''
        fanart = ''
        title = scrapedtitle
        url = scrapedurl
        if scrapedtitle not in ['PRÓXIMAMENTE', 'EN CINE']:
            itemlist.append(Item(channel=item.channel, action="lista",
                                 title=title,
                                 contentTitle=item.title,
                                 url=url,
                                 thumbnail=thumbnail,
                                 fanart=fanart
                                 ))
    return itemlist


def seccion(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    patron = 'glossary=(.*?)>(.*?)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedid, scrapedtitle in matches:
        thumbnail = ''
        if scrapedtitle.lower() in thumbletras:
            thumbnail = thumbletras[scrapedtitle.lower()]
        fanart = ''
        title = scrapedtitle
        id = scrapedid

        itemlist.append(
            Item(channel=item.channel, action="alpha", title=title, contentTitle=item.title, thumbnail=thumbnail,
                 fanart=fanart, id = id))
    return itemlist

def alpha(item):
    logger.info()

    itemlist = []

    url = 'https://www.ultrapeliculashd.com/wp-json/dooplay/glossary/?term=%s&nonce=4e850b7d59&type=all' % item.id
    dict_data = httptools.downloadpage(url).json
    if 'error' not in dict_data:
        for elem in dict_data:
            elem = dict_data[elem]
            itemlist.append(Item(channel=item.channel, action='findvideos', title = elem['title'], url=elem['url'],
                                 thumbnail=elem['img']))
    return itemlist


def get_source(url, referer=None):
    logger.info()
    if referer is None:
        data = httptools.downloadpage(url).data
    else:
        data = httptools.downloadpage(url, headers={'Referer':referer}).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def findvideos(item):
    from lib import jsunpack
    logger.info()
    itemlist = []
    full_data = get_source(item.url)

    patron = '<div id="([^"]+)" class="play-box-iframe.*?src="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(full_data)
    for option, video_url in matches:
        language = scrapertools.find_single_match(full_data, '"#%s">.*?-->(.*?)(?:\s|<)' % option)
        if 'sub' in language.lower():
            language = 'SUB'
        language = IDIOMAS[language]
        quality = ''
        # if 'waaw.tv' in video_url:
        #     continue
        # data = httptools.downloadpage(video_url, follow_redirects=False, headers={'Referer': item.url}).data
        #
        # if 'hideload' in video_url:
        #     quality = ''
        #     new_id = scrapertools.find_single_match(data, "var OLID = '([^']+)'")
        #     new_url = 'https://www.ultrapeliculashd.com/hideload/?ir=%s' % new_id[::-1]
        #     data = httptools.downloadpage(new_url, follow_redirects=False, headers={'Referer': video_url}).headers
        #     url = data['location']+"|%s" % video_url
        # elif 'd.php' in video_url:
        #     data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
        #     quality = '1080p'
        #     packed = scrapertools.find_single_match(data, '<script>(eval\(.*?)eval')
        #     unpacked = jsunpack.unpack(packed)
        #     url = scrapertools.find_single_match(unpacked, '"file":("[^"]+)"')
        # elif 'drive' in video_url:
        #     quality = '1080p'
        #     data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
        #     url = scrapertools.find_single_match(data, 'src="([^"]+)"')
        #
        if not config.get_setting("unify"):
            title = ' [%s] [%s]' % (quality, language)
        else:
            title = ''

        new_item = (Item(channel=item.channel, title='%s'+title, url=video_url, action='play', quality=quality,
                         language=language,  infoLabels=item.infoLabels))
        itemlist.append(new_item)


    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title %  i.server.capitalize())

    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)
    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                 action="add_pelicula_to_library", extra="findvideos", contentTitle=item.contentTitle))

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    try:
        if texto != '':
            item.extra = 'buscar'
            return lista(item)
        else:
            return []
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    item.extra = 'estrenos/'
    try:
        if categoria in ['peliculas','latino']:
            item.url = host + '/genre/estrenos/'

        elif categoria == 'infantiles':
            item.url = host + '/genre/animacion/'

        elif categoria == 'terror':
            item.url = host + '/genre/terror/'

        itemlist = lista(item)
        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
