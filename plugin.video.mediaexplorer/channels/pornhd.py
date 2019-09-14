# -*- coding: utf-8 -*-
from core.libs import *

HOST = "https://www.pornhd.com"

def mainlist(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        action='videos',
        label='Útimos videos',
        type='item',
        url=HOST,
        content_type='videos'
    ))

    itemlist.append(item.clone(
        action='videos',
        label='Los más valorados',
        type='item',
        url=HOST + '/?order=top-rated',
        content_type='videos'
    ))

    itemlist.append(item.clone(
        action='videos',
        label='Los más vistos',
        type='item',
        url=HOST + '/?order=most-popular',
        content_type='videos'
    ))

    itemlist.append(item.clone(
        action='listcategorias',
        label='Categorias',
        type='item',
        url=HOST + '/category?order=alphabetical',
        content_type='items'
    ))

    itemlist.append(item.clone(
        action='listcanales',
        label='Canales',
        type='item',
        url=HOST + "/channel",
        content_type='items'
    ))

    itemlist.append(item.clone(
        action='listpornstar',
        label='PornStars',
        type='item',
        url=HOST + "/pornstars",
        content_type='items'
    ))

    itemlist.append(item.clone(
        action='search',
        label='Buscar',
        type='search',
        content_type='videos',
        category='adult',
        query=True
    ))

    return itemlist


def videos(item):
    logger.trace()
    itemlist = list()
    logger.debug(item.url)

    # Descarga la página
    data = httptools.downloadpage(item.url).data

    # Extrae las peliculas
    patron = '<a class="thumb videoThumb popTrigger" href="([^"]+)"><img alt="([^"]+)".*?src="(.*?\.jpg)"' \
             '.*?<time>([^<]+)</time>'

    for url, title, thumbnail, duracion in scrapertools.find_multiple_matches(data, patron):
        if "data-original=" in thumbnail:
            thumbnail = scrapertools.find_single_match(thumbnail + '"', 'data-original="([^"]+)')

        itemlist.append(item.clone(
            action='play',
            title=title,
            url=HOST + url,
            thumb=thumbnail,
            folder=False,
            type='video'
        ))

    if itemlist:
        # Paginador
        next_page = scrapertools.find_single_match(data, '<li class="next ">  <span class="icon jsFilter js-link" data-query-key="page" data-query-value="(\d+)"></span>  </li>')
        if next_page:
            page = scrapertools.find_single_match(item.url,'(page=\d+)')
            if page:
                url = item.url.replace(page, 'page=%s' % next_page)
            else:
                #url=urlparse.urljoin(item.url, '?page=2')
                if '?' in item.url:
                    url = item.url + '&page=2'
                else:
                    url = item.url + '?page=2'

            logger.debug(url)
            itemlist.append(item.clone(
                action='videos',
                url=url,
                type='next'
            ))

    return itemlist


def listcategorias(item):
    logger.trace()
    itemlist = list()

    # Descarga la página
    data = httptools.downloadpage(item.url).data

    # Extrae las categorias
    patron = '<li class="category"><a href="([^"]+)".*?data-original="([^"]+)".*?</span>([^<]+)</a></li>'
    for url, thumbnail, label in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            action='videos',
            label=label.strip(),
            poster=thumbnail,
            url=HOST + url,
            content_type='videos',
            type='item'
        ))

    return itemlist


def listcanales(item):
    logger.trace()
    itemlist = list()

    # Descarga la página
    data = httptools.downloadpage(item.url).data

    # Extrae las categorias
    patron = '<li><a href="([^"]+)".*?<img src="([^"]+)".*?<span class="name">([^<]+)</span></a></li>'
    for url, thumbnail, label in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            action='videos',
            label=label.strip(),
            poster=thumbnail,
            url=HOST + url,
            content_type='videos',
            type='item'
        ))

    return itemlist


def listpornstar(item):
    logger.trace()
    itemlist = list()

    # Descarga la página
    data = httptools.downloadpage(item.url).data

    # Extrae las categorias
    patron = '<li class="pornstar"><a href="([^"]+)".*?data-original="([^"]+)" height="134" width="113" alt="([^"]+)"'
    for url, thumbnail, label in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            action='videos',
            label=label.strip(),
            poster=thumbnail,
            url=HOST + url,
            content_type='videos',
            type='item'
        ))

    return itemlist


def search(item):
    logger.trace()
    item.url = HOST + "/search?search=" + item.query
    return videos(item)


def play(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, 'sources:\s*{(.*?)}')

    for res, url in scrapertools.find_multiple_matches(data, '"([^"]+)":"([^"]+)"'):
        url = httptools.downloadpage(HOST + url.replace('\\',''), headers={'Referer': item.url}, follow_redirects= False, only_headers=True).headers['location']
        itemlist.append(Video(url=url, res=res))

    return sorted(itemlist, key=lambda x: int(x.res[:-1]) if x.res else 0, reverse=True)
