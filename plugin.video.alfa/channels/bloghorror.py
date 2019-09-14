# -*- coding: utf-8 -*-
# -*- Channel BlogHorror -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import os
import re

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

host = 'http://bloghorror.com/'
fanart = 'http://bloghorror.com/wp-content/uploads/2015/04/bloghorror-2017-x.jpg'

def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def mainlist(item):
    logger.info()

    itemlist = []

    itemlist.append(Item(channel=item.channel, fanart=fanart, title="Todas", action="list_all",
                         url=host+'/category/terror', thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, fanart=fanart, title="Asiaticas", action="list_all",
                         url=host+'/category/asiatico', thumbnail=get_thumb('asiaticas', auto=True)))

    itemlist.append(Item(channel=item.channel, fanart=fanart, title = 'Buscar', action="search", url=host + '?s=', pages=3,
                         thumbnail=get_thumb('search', auto=True)))

    return itemlist


def list_all(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    patron = '<article id="post-\d+".*?data-background="([^"]+)".*?href="([^"]+)".*?<h3.*?internal">([^<]+)'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedurl, scrapedtitle in matches:
        url = scrapedurl
        title = scrapertools.find_single_match(scrapedtitle, '(.*?)(?:|\(|\| )\d{4}').strip()
        year = scrapertools.find_single_match(scrapedtitle, '(\d{4})')
        thumbnail = scrapedthumbnail
        new_item = Item(channel=item.channel, fanart=fanart, title=title, url=url, action='findvideos',
                        thumbnail=thumbnail, infoLabels={'year':year})

        new_item.contentTitle=title
        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Paginacion

    if itemlist != []:

        next_page = scrapertools.find_single_match(data, 'page-numbers current.*?<a class="page-numbers" href="([^"]+)"')
        if next_page != '':
            itemlist.append(Item(channel=item.channel, fanart=fanart, action="list_all", title='Siguiente >>>', url=next_page))
        else:
            item.url=next_page

    return itemlist



def section(item):
    logger.info()

    itemlist = []
    data=get_source(host)
    if item.title == 'Generos':
        data = scrapertools.find_single_match(data, 'tabindex="0">Generos<.*?</ul>')
    elif 'Años' in item.title:
        data = scrapertools.find_single_match(data, 'tabindex="0">Año<.*?</ul>')

    patron = 'href="([^"]+)">([^<]+)</a>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, title in matches:

        itemlist.append(Item(channel=item.channel, fanart=fanart, title=title, url=url, action='list_all', pages=3))

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []
    full_data = get_source(item.url)
    data = scrapertools.find_single_match(full_data, '>FICHA TECNICA:<.*?</ul>')
    #patron = '(?:bold|strong>|<br/>|<em>)([^<]+)(?:</em>|<br/>).*?="(magnet[^"]+)"'
    patron = '(?:<em>|<br/><em>|/> )(DVD|720|1080)(?:</em>|<br/>|</span>).*?="(magnet[^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    if len(matches) == 0:
        patron = '<a href="(magnet[^"]+)"'
        matches = re.compile(patron, re.DOTALL).findall(full_data)

    patron_sub = 'href="(http://www.subdivx.com/bajar.php[^"]+)"'
    sub_url = scrapertools.find_single_match(full_data, patron_sub)
    sub_num = scrapertools.find_single_match(sub_url, 'u=(\d+)')

    if sub_url == '':
        sub = ''
        lang = 'VO'
    else:
        try:
            sub = get_sub_from_subdivx(sub_url, sub_num)
        except:
            sub = ''
        lang = 'VOSE'

    try:

        for quality, scrapedurl in matches:
            if quality.strip() not in ['DVD', '720', '1080']:
                quality = 'DVD'
            url = scrapedurl
            if not config.get_setting('unify'):
                title = ' [Torrent] [%s] [%s]' % (quality, lang)
            else:
                title = 'Torrent'

            itemlist.append(Item(channel=item.channel, fanart=fanart, title=title, url=url, action='play',
                                 server='torrent', quality=quality, language=lang, infoLabels=item.infoLabels,
                                 subtitle=sub))

    except:
        for scrapedurl in matches:
            quality = 'DVD'
            url = scrapedurl
            if not config.get_setting('unify'):
                title = ' [Torrent] [%s] [%s]' % (quality, lang)
            else:
                title = 'Torrent'
            itemlist.append(Item(channel=item.channel, fanart=fanart, title=title, url=url, action='play',
                                 server='torrent', quality=quality, language=lang, infoLabels=item.infoLabels,
                                 subtitle=sub))

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(Item(channel=item.channel,
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url,
                             action="add_pelicula_to_library",
                             extra="findvideos",
                             contentTitle=item.contentTitle
                             ))

    return itemlist


def search(item, texto):
    logger.info()
    itemlist = []
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    if texto != '':
        try:
            return list_all(item)
        except:
            itemlist.append(item.clone(url='', title='No hay elementos...', action=''))
            return itemlist

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas', 'terror', 'torrent']:
            item.url = host
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def get_sub_from_subdivx(sub_url, sub_num):
    logger.info()

    import xbmc
    from time import sleep
    import urlparse
    sub_dir = os.path.join(config.get_data_path(), 'temp_subs')

    if os.path.exists(sub_dir):
        for sub_file in os.listdir(sub_dir):
            old_sub = os.path.join(sub_dir, sub_file)
            os.remove(old_sub)

    sub_data = httptools.downloadpage(sub_url, follow_redirects=False)

    if 'x-frame-options' not in sub_data.headers:
        sub_url = 'http://subdivx.com/sub%s/%s' % (sub_num, sub_data.headers['location'])
        sub_url = sub_url.replace('http:///', '')
        sub_data = httptools.downloadpage(sub_url).data

        fichero_rar = os.path.join(config.get_data_path(), "subtitle.rar")
        outfile = open(fichero_rar, 'wb')
        outfile.write(sub_data)
        outfile.close()
        xbmc.executebuiltin("XBMC.Extract(%s, %s/temp_subs)" % (fichero_rar, config.get_data_path()))
        sleep(1)
        if len(os.listdir(sub_dir)) > 0:
            sub = os.path.join(sub_dir, os.listdir(sub_dir)[0])
        else:
            sub = ''
    else:
        logger.info('sub no valido')
        sub = ''
    return sub

