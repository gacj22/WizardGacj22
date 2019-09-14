# -*- coding: utf-8 -*-
from core.libs import *

HOST = 'https://www.cumlouder.com/es'


def mainlist(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        type='label',
        label='Producciones CumLouder:'))

    itemlist.append(item.clone(
        group=True,
        type="item",
        action='videos',
        label='Útimos videos',
        url=HOST + '/series/novedades',
        content_type='videos'
    ))

    itemlist.append(item.clone(
        group=True,
        type="item",
        action='listcategorias',
        label='Categorías',
        url=HOST,
        content_type='items'
    ))

    itemlist.append(item.clone(
        group=True,
        type="item",
        action='listchicas',
        label='Chicas',
        url=HOST + '/chicas/',
        content_type='items'
    ))

    itemlist.append(item.clone())
    itemlist.append(item.clone(
        type='label',
        label='Otros videos:'))

    itemlist.append(item.clone(
        group=True,
        type="item",
        action='videos',
        label='Útimos videos',
        url=HOST + '/porno/',
        content_type='videos'
    ))

    itemlist.append(item.clone(
        group=True,
        type="item",
        action='listcategorias_otros',
        label='Categorías',
        url=HOST + '/categorias/',
        content_type='items'
    ))

    itemlist.append(item.clone())
    itemlist.append(item.clone(
        action='search',
        label='Buscar',
        content_type='videos',
        category='adult',
        query=True,
        type='search'
    ))

    return itemlist


def listcategorias(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = r'<a onclick="tmClickVideo\(\d+, \'home-categorias\'\);" href="([^"]+)" itemprop="url" ' \
             'class="muestra-escena home-categories" title=""><img.*?data-lazy="([^"]+)" itemprop="image" ' \
             'class="thumb lazy" width="229" height="255" alt="" title="" /><h2 itemprop="name">([^<]+)</h2>'

    for url, thumb, label in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            action='videos',
            label=unicode(label, 'utf8').capitalize().encode('utf8'),
            poster=thumb,
            url=urlparse.urljoin(HOST, url),
            content_type='videos',
            type='item'
        ))

    return sorted(itemlist, key=lambda x: x.label)


def listcategorias_otros(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    patron = 'class="muestra-escena muestra-categoria show-tag" href="([^"]+)" title="([^"]+)".*?' \
             '<img class="thumb lazy".*?data-lazy="([^"]+)'

    for url, label, thumb in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            action='videos',
            label=label,
            poster=thumb,
            url=urlparse.urljoin(HOST, url),
            content_type='videos',
            type='item'
        ))

    return sorted(itemlist, key=lambda x: x.label)



def listchicas(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    patron = '(?s)class="muestra-escena muestra-pornostar show-girl" href="([^"]+)" title="([^"]+)".*?' \
             '<img class="thumb lazy".*?data-lazy="([^"]+).*?<span class="videos"> <span class="ico-videos sprite">' \
             '</span>([^<]+)</span>.*?<span class="puntaje"> <span class="ico-puntaje sprite"></span>([^<]+)</span>'

    for url, label, thumb, num, ranking in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            action='videos',
            label='%s (%s) [%s]' % (label, ranking.strip(), num.strip()),
            poster=thumb,
            url=urlparse.urljoin(HOST, url),
            content_type='videos',
            type='item'
        ))

    # Paginador
    url_next = scrapertools.find_single_match(data, '<a href="([^"]+)" rel="nofollow">Siguiente »</a>')
    if url_next:
        itemlist.append(item.clone(
            action='videos',
            url=urlparse.urljoin(HOST, url_next),
            type='next'
        ))

    return itemlist


def videos(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url,add_referer=True).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<a class="muestra-escena" href="([^"]+)".*?data-lazy="([^"]+)".*?title="([^"]+)".*?' \
             '<span class="ico-minutos sprite"></span>([^<]+)</span>(.*?)</a>'

    for url, thumb, title, time, qlt in scrapertools.find_multiple_matches(data, patron):
        if not thumb.startswith('http'):
            thumb = 'https:' + thumb

        if "hd sprite" in qlt:
            title = "%s [%s]" % (title, 'HD')

        itemlist.append(item.clone(
            action='play',
            title="%s (%s)" % (title, time),
            url=urlparse.urljoin(HOST, url),
            thumb=thumb.replace('ep1.jpg', 'ep.jpg'),
            folder=False,
            type='video'
        ))

    # Paginador
    url_next = scrapertools.find_single_match(data, '<a href="([^"]+)"[^>]*>Siguiente »</a>')
    if url_next:
        itemlist.append(item.clone(
            action='videos',
            url= urlparse.urljoin(HOST, url_next),
            type='next'
        ))

    return itemlist


def search(item):
    logger.trace()
    return videos(item.clone(url=HOST + '/buscar?q=%s' % item.query))


def play(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    patron = '''<source src="([^"]+).*?res='([^']+)'''

    for url, res in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(Video(url='https:' + url.replace('&amp;', '&'), res=res))

    return sorted(itemlist, key=lambda x: int(x.res) if x.res else 0, reverse=True)