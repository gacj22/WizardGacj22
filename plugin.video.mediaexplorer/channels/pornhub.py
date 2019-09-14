# -*- coding: utf-8 -*-
from core.libs import *

def mainlist(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        action='videos',
        label='Útimos videos',
        url='http://es.pornhub.com/video?o=cm',
        content_type='videos'
    ))

    itemlist.append(item.clone(
        action='listcategorias',
        label='Listado categorias',
        url="http://es.pornhub.com/categories?o=al",
        content_type='items'
    ))

    itemlist.append(item.clone(
        action='search',
        label='Buscar',
        content_type='videos',
        category='adult',
        query=True
    ))

    return itemlist


def videos(item):
    logger.trace()
    itemlist = list()

    # Descarga la página
    data = httptools.downloadpage(item.url).data
    videodata = scrapertools.find_single_match(data, 'videos search-video-thumbs(.*?)<div class="reset"></div>')

    # Extrae las peliculas
    patron = '<div class="phimage">.*?'
    patron += '<a href="([^"]+)" title="([^"]+).*?'
    patron += 'data-mediumthumb="([^"]+)".*?'
    patron += '<var class="duration">([^<]+)</var>(.*?)</div>.*?'

    matches = re.compile(patron, re.DOTALL).findall(videodata)
    for url, title, thumbnail, duration, scrapedhd in matches:
        title = title.replace("&amp;amp;", "&amp;") + " (" + duration + ")"

        scrapedhd = scrapertools.find_single_match(scrapedhd, '<span class="hd-thumbnail">(.*?)</span>')
        if scrapedhd == 'HD':
            title += ' [HD]'

        itemlist.append(item.clone(
            action='play',
            title=title,
            url=urlparse.urljoin(item.url, url),
            thumb=thumbnail,
            folder=False,
            type='video'
        ))

    if itemlist:
        # Paginador
        matches = re.compile('<li class="page_next"><a href="([^"]+)"', re.DOTALL).findall(data)
        if matches:
            itemlist.append(item.clone(
                action='videos',
                url=urlparse.urljoin(item.url, matches[0].replace('&amp;', '&')),
                type='next'
            ))

    return itemlist


def listcategorias(item):
    logger.trace()
    itemlist = list()

    # Descarga la página
    data = httptools.downloadpage(item.url).data
    data =  re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    data = scrapertools.find_single_match(data, '<div id="categoriesStraightImages">(.*?)</ul>')

    # Extrae las categorias
    patron = '<li class="cat_pic" data-category=".*?'
    patron += '<a href="([^"]+)".*?'
    patron += '<img\s?src="([^"]+)".*?'
    patron += 'alt="([^"]+)"'

    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, thumbnail, label in matches:
        if "?" in url:
            url = urlparse.urljoin(item.url, url + "&o=cm")
        else:
            url = urlparse.urljoin(item.url, url + "?o=cm")

        itemlist.append(item.clone(
            action='videos',
            label=label,
            poster=thumbnail,
            url=url,
            content_type='videos',
            type='item'
        ))

    itemlist.sort(key=lambda x: x.label)
    return itemlist


def search(item):
    logger.trace()
    item.url = "http://es.pornhub.com/video/search?search=%s&o=mr" % item.query
    return videos(item)


def play(item):
    logger.trace()
    itemlist = list()

    # Descarga la página
    data = httptools.downloadpage(item.url).data

    json = jsontools.load_json(scrapertools.find_single_match(data, 'var flashvars_[^{]+(.*?);'))
    for v in json['mediaDefinitions']:
        if v['format'] in ['upsell', 'dash']:
            # Premium
            continue

        itemlist.append(Video(url=v['videoUrl'], res='%sp' % v['quality'], type=v['format']))


    return sorted(itemlist, key=lambda x: int(x.res[:-1]) if x.res else 0, reverse=True)
