# -*- coding: utf-8 -*-
from core.libs import *
import base64

HOST = 'https://repelis.live'

LNG = Languages({
    Languages.en: ['ingles'],
    Languages.es: ['espanol', 'Castellano'],
    Languages.la: ['latino', 'Latino'],
    Languages.sub_es: ['subtitulado', 'Subtitulado']
})

QLT = Qualities({
    Qualities.scr: ['Ts Screener', 'Cam', 'BR-Screener'],
    Qualities.hd: ['HD Real 720'],
    Qualities.hd_full: ['HD Real 1080p'],
    Qualities.rip: ['HD Rip 320', 'Dvd Rip']
})


def mainlist(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        action="movies",
        label="Novedades",
        url=HOST,
        type="item",
        content_type='movies'
    ))

    itemlist.append(item.clone(
        action="movies",
        label="Estrenos",
        url=HOST + "/category/estrenos/",
        type="item",
        content_type='movies'
    ))

    itemlist.append(item.clone(
        action="movies",
        label="Películas en Español",
        url=HOST + '/pelis-castellano/',
        type="item",
        lang=[LNG.es],
        content_type='movies'
    ))

    itemlist.append(item.clone(
        action="movies",
        label="Películas en Latino",
        url=HOST + '/pelis-latino/',
        type="item",
        lang=[LNG.la],
        content_type='movies'
    ))

    itemlist.append(item.clone(
        action="movies",
        label="Películas subtituladas",
        url=HOST + '/pelis-subtitulado/',
        type="item",
        lang=[LNG.sub_es],
        content_type='movies'
    ))

    itemlist.append(item.clone(
        action="years",
        label="Años",
        url=HOST,
        type="item"
    ))

    itemlist.append(item.clone(
        action="generos",
        label="Géneros",
        url=HOST,
        type="item"
    ))

    itemlist.append(item.clone(
        action="search",
        label="Buscar",
        query=True,
        type='search',
        content_type='movies'
    ))

    return itemlist


def search(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(HOST + '/?s=%s' % item.query, ).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<li class="col-md-12 itemlist"><div class="list-score">([^<]+)</div><div class="col-xs-2">' \
             '<div class="row"> <a href="([^"]+)" title="([^"]+)"><div class="box-imagen">(?:<div class="audio">(.*?)' \
             '</div>)? <img src="([^"]+)".*?<p class="main-info-list">Pelicula del ([^<]+)</p>' \
             '<p class="text-list">([^<]+)</p>'

    for rat, url, title, language, poster, year, plot in scrapertools.find_multiple_matches(data, patron):
        lng = scrapertools.find_multiple_matches(language, 'class="([^"]+)"')

        if rat == year: # N/A peliculas de Adultos
            continue

        itemlist.append(item.clone(
            title=re.sub(r"(\(\d{4}\))", "", title).strip(),
            url=url,
            poster=poster,
            year=year,
            plot=plot,
            type='movie',
            content_type='servers',
            action='findvideos',
            lang=[LNG.get(l) for l in lng]
        ))

    # Paginador
    next_url = scrapertools.find_single_match(data, '<a href="([^"]+)" ><i class="glyphicon glyphicon-chevron-right" '
                                                    'aria-hidden="true"></i></a>')
    if next_url:
        itemlist.append(item.clone(url=next_url, type='next'))

    return itemlist


def years(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data

    patron = '<option value="([^"]+)">(\d{4})</option>'

    for url, year in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            action='movies',
            label=year,
            url=url,
            content_type='movies',
            year=year
        ))

    return itemlist


def generos(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data

    data = scrapertools.find_single_match(
        data,
        '<div id="categories-2" class="col-xs-12 widget widget_categories">(.*?)<div class="menu-anos-container">'
    )

    patron = '<li class="cat-item cat-item-[^"]+"><a href="([^"]+)">([^<]+)</a></li>'

    skip = ['película de la televisión', 'Proximos Estrenos', 'Uncategorized']

    for url, genre in scrapertools.find_multiple_matches(data, patron):
        # Filtrado de categorias
        if genre in skip:
            continue

        itemlist.append(item.clone(
            action='movies',
            label=genre,
            url=url,
            content_type='movies'
        ))

    return itemlist


def movies(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url or HOST).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<div class="col-mt-5 postsh"><div class="poster-media-card"> <a href="([^"]+)" title="([^"]+)">' \
             '<div class="poster"><div class="title"> <span class="under-title">([^<]+)</span> <span class="anio" ' \
             'style="position: relative;top: -186px;">([^<]+)</span></div>(?:<div class="audio">' \
             '(.*?)</div>)?<div class="poster-image-container">.*?src="([^"]+)"'

    for url, title, category, year, language, poster in scrapertools.find_multiple_matches(data, patron):

        lng = scrapertools.find_multiple_matches(language, 'class="([^"]+)"')

        if category == 'Eroticas':
            continue

        new_item = item.clone(
            title=re.sub(r"(\(\d{4}\))", "", title).strip(),
            url=url,
            poster=poster,
            year=year,
            type='movie',
            content_type='servers',
            action='findvideos',
            lang=item.lang or [LNG.get(l) for l in lng]
        )

        itemlist.append(new_item)

    # Paginador
    next_url = scrapertools.find_single_match(data,
                                              '<a href="([^"]+)"><i class="glyphicon glyphicon-chevron-right" '
                                              'aria-hidden="true"></i></a>')
    if next_url:
        itemlist.append(item.clone(url=next_url, type='next'))

    return itemlist


def findvideos(item):
    logger.trace()
    itemlist = list()
    logger.debug(item.url)
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    logger.debug(data)
    patron = 'href="#embed(\d*)" data-src="([^"]+)" class="([^" ]+).*?"'
    for num, url, lang in scrapertools.find_multiple_matches(data, patron):
        if lang == 'Trailer':
            continue

        qlt = scrapertools.find_single_match(
            data,
            '<div class="tab-pane reproductor repron[^"]+" id="embed%s">.*?<div class="calishow">([^<]+)</div>' % num
        )
        logger.debug(qlt)
        try:
            b_64 = urllib.unquote_plus(scrapertools.find_single_match(url, 'redirect/\?id=([^&]+)')).replace('_', '/')
            b_64 = b_64 + '=' * (4 - len(b_64) % 4)
            url = base64.b64decode(b_64)
        except Exception:
            url = httptools.downloadpage(url.replace('/?', '?'), headers={'Referer': item.url},
                                         follow_redirects=False).headers['location']

        new_item = item.clone(
            url=url,
            type='server',
            lang=LNG.get(lang),
            quality=QLT.get(qlt),
            action='play',
            headers={'Referer': HOST} if 'streamango' in url or 'openload' in url else None
        )

        if not item.lang or new_item.lang in item.lang:
            itemlist.append(new_item)

    return servertools.get_servers_itemlist(itemlist)
