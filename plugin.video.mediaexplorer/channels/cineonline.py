# -*- coding: utf-8 -*-
from core.libs import *

HOST = 'https://www.cine-online.eu/'

LNG = Languages({
    Languages.en: ['en', 'Ingles', 'Dual Esp/Ing'],
    Languages.es: ['Castellano', 'Español', 'Cast', 'Dual Esp/Ing'],
    Languages.la: ['Latino', 'Lat'],
    Languages.sub_es: ['Sub', 'Subtitulado']
})

QLT = Qualities({
    Qualities.scr: ['Cam', 'TS-Screener HQ'],
    Qualities.hd: ['HD', 'HD 720p'],
    Qualities.hd_full: ['HD 1080p', 'Bluray'],
    Qualities.rip: ['DVD-Rip']
})


def mainlist(item):
    logger.trace()
    itemlist = list()

    new_item = item.clone(
        type='label',
        label="Películas",
        category='movie',
        thumb='thumb/movie.png',
        icon='icon/movie.png',
        poster='poster/movie.png'
    )
    itemlist.append(new_item)
    itemlist.extend(menupeliculas(new_item))

    new_item = item.clone(
        type='label',
        label="Series",
        category='tvshow',
        thumb='thumb/tvshow.png',
        icon='icon/tvshow.png',
        poster='poster/tvshow.png',
    )
    itemlist.append(new_item)
    itemlist.extend(menuseries(new_item))

    new_item = item.clone(
        type='label',
        label="Adultos",
        category='adult',
        thumb='thumb/adult.png',
        icon='icon/adult.png',
        poster='poster/adult.png',
        adult=True
    )
    itemlist.append(new_item)
    itemlist.extend(menuadultos(new_item))

    return itemlist


def menupeliculas(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        action="contents",
        label="Español",
        url=HOST + "/tag/castellano/",
        type="item",
        group=True,
        lang=[Languages.es],
        content_type='movies'))

    itemlist.append(item.clone(
        action="contents",
        label="Latino",
        url=HOST + "/tag/latino/",
        type="item",
        group=True,
        lang=[Languages.la],
        content_type='movies'))

    itemlist.append(item.clone(
        action="contents",
        label="Subtitulado",
        url=HOST + "/tag/subtitulado/",
        type="item",
        group=True,
        lang=[Languages.vos],
        content_type='movies'))

    itemlist.append(item.clone(
        action="generos",
        label="Géneros",
        url=HOST,
        type="item",
        group=True
    ))

    itemlist.append(item.clone(
        action="movie_search",
        label="Buscar",
        query=True,
        type='search',
        group=True,
        content_type='movies'
    ))

    return itemlist


def menuseries(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        action="contents",
        label="Mas populares",
        url=HOST + "serie/",
        type="item",
        group=True,
        content_type='tvshows'))

    itemlist.append(item.clone(
        action="newest_episodes",
        label="Nuevos episodios",
        url=HOST + "episodios/",
        type="item",
        group=True,
        content_type='episodes'))

    itemlist.append(item.clone(
        action="generos_tvshow",
        label="Géneros",
        type="item",
        group=True,
        url=HOST
    ))

    itemlist.append(item.clone(
        action="tv_search",
        label="Buscar",
        query=True,
        type='search',
        group=True,
        content_type='tvshows'
    ))
    return itemlist


def menuadultos(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        action="contents",
        label="Últimos vídeos",
        url=HOST + "/tag/18-adultos/",
        type="item",
        group=True,
        content_type='movies'))

    itemlist.append(item.clone(
        action="adult_search",
        label="Buscar",
        query=True,
        type='search',
        group=True,
        content_type='movies'
    ))

    return itemlist


def movie_search(item):
    logger.trace()

    itemlist = contents(item.clone(
        url=HOST + '/?s=%s' % item.query
    ))
    itemlist = filter(lambda x: x.type == 'movie', itemlist)

    return itemlist


def tv_search(item):
    logger.trace()

    itemlist = contents(item.clone(
        url=HOST + '/?s=%s' % item.query
    ))
    itemlist = filter(lambda x: x.type == 'tvshow', itemlist)

    return itemlist


def adult_search(item):
    logger.trace()

    itemlist = contents(item.clone(
        url=HOST + '/?s=%s' % item.query
    ))
    itemlist = filter(lambda x: x.type == 'video', itemlist)

    return itemlist


def generos(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data

    patron = '<a href="(https://www.cine-online.eu/categoria/[^/]+/)".*?>([^<>]+)</a>'

    for url, genre in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            action='contents',
            label=genre,
            url=url,
            content_type='movies'
        ))

    return itemlist


def generos_tvshow(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    patron = '<a href="(https://www.cine-online.eu/series/categoria/[^/]+/)".*?>([^<>]+)</a>'

    for url, genre in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            action='contents',
            label=genre,
            url=url,
            content_type='movies'
        ))

    return itemlist


def contents(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<div id="[^"]+" class="item"><a href="([^"]+)">.*?'
    patron += '<img src="([^"]+)".*?<b class="icon-star"></b></b>([^<]+)</span>.*?'
    patron += '<span class="ttx">([^<]+).*?'
    patron += '<div class="fixyear"><h2>([^<]+)</h2>(?:<span class="year">(\d{4})?[^<]*</span>)?'

    for url, pic, rating, plot, title, year in scrapertools.find_multiple_matches(data, patron):
        if 'Temporada' in title:
            continue

        if title.startswith('Ver '):
            title = title.replace('Ver ', '')

        title = re.sub(r"[O|o]nline", "", title).strip()

        new_item = item.clone(
            title=title,
            url=url,
            poster=pic,
            year=year,
            plot=plot,
            rating=rating)

        if '/serie/' in url:
            new_item.type = 'tvshow'
            new_item.content_type = 'seasons'
            new_item.tvshowtitle = title
            new_item.action = 'seasons'

        elif not year:
            new_item.type = 'video'
            new_item.content_type = 'servers'
            new_item.action = 'findvideos'
            new_item.adult = True
        else:
            new_item.type = 'movie'
            new_item.content_type = 'servers'
            new_item.action = 'findvideos'

        itemlist.append(new_item)

    # Paginador
    next_url = scrapertools.find_single_match(data, '<div class="pag_b"><a href="([^"]+)"')
    if next_url:
        itemlist.append(item.clone(url=next_url, type='next'))

    return itemlist


def seasons(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<div class="se-q"><span class="se-t">([^<]+)'

    for num_season in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            season=int(num_season),
            title="Temporada %s" % num_season,
            year="",
            action="episodes",
            type='season',
            content_type='episodes'))

    return itemlist


def episodes(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<div class="numerando">([^<]+)</div><div class="episodiotitle"><a href="([^"]+)">([^<]+)</a>'

    for numerando, url, title in scrapertools.find_multiple_matches(data, patron):
        season, episode = scrapertools.get_season_and_episode(numerando.replace(' ', ''))
        if item.season != season:
            continue

        itemlist.append(item.clone(
            title=title,
            action="findvideos",
            url=url,
            episode=episode,
            type='episode',
            content_type='servers'))

    return itemlist


def newest_episodes(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<td class="bb"><a href="([^"]+)">([^<]+)</a> <span>([^<]+).*?'
    patron += '<img src="([^"]+).*?<p>([^<]+).*?'
    patron += '<td class="cc"><a href="[^"]+">([^<]+)<'

    for url, tvshowtitle, season_episode, thumb, plot, title in scrapertools.find_multiple_matches(data, patron):
        season, episode = scrapertools.get_season_and_episode(season_episode.replace(' ', ''))

        itemlist.append(item.clone(
            tvshowtitle=tvshowtitle,
            label='%s - %s' % (tvshowtitle, title),
            title=title,
            action="findvideos",
            multipage=True,
            season=season,
            episode=episode,
            type='episode',
            plot=plot,
            thumb=thumb.strip(),
            poster='',
            url=url,
            content_type='servers'))

    # Paginador
    next_url = scrapertools.find_single_match(data, '<div class="pag_b"><a href="([^"]+)"')
    if next_url:
        itemlist.append(item.clone(url=next_url, type='next'))

    return itemlist


def findvideos(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<div style="display: none" id="plays-(\d+)">([^<]+)</div>'
    for num, enc in scrapertools.find_multiple_matches(data, patron):
        if not enc.strip():
            continue

        iframe = httptools.downloadpage(urlparse.urljoin(item.url, '/ecrypt'), post={'nombre': enc}).data
        url = scrapertools.find_single_match(iframe, '(?:src|SRC)="([^"]+)"')
        lng = scrapertools.find_single_match(
            data,
            '<li><a[^>]+href="#[^"]+%s" ?>([^<]+)</a></li>' % num
        ).strip()

        if ' ' in lng:
            lng, qlt = lng.split(' ')
        else:
            qlt = ''
        if item.lang and LNG.get(lng) not in item.lang and LNG.get(lng) != item.lang:
            continue

        itemlist.append(item.clone(
            url=url,
            type='server',
            action='play',
            lang=LNG.get(lng),
            quality=QLT.get(qlt)
        ))

    patron = '<a href="(https://www.cine-online.eu/encrypt\?link=[^"]+)".*?' \
             '<span class="a"><b class="[^"]+"></b>[^<]+</span>' \
             '<span class="b">[^>]+>([^<]+)</span><span class="c">([^<]+)</span><span class="d">([^<]+)</span></a>'

    for url, server, lng, qlt in scrapertools.find_multiple_matches(data, patron):
        iframe = httptools.downloadpage(url).data
        url = scrapertools.find_single_match(iframe, "window.location='([^']+)'")

        if not url:
            url = scrapertools.find_single_match(iframe, '(?:iframe src|IFRAME SRC)="([^"]+)"')

        if url.split('//')[1].split('/')[0] in [
            'cpmlink.net',
            'oke.io',
            'adshort.im',
            'ouo.io',
            'shink.me',
        ]:
            continue

        if item.lang and LNG.get(lng) not in item.lang and LNG.get(lng) != item.lang:
            continue

        itemlist.append(item.clone(
            url=url,
            type='server',
            action='play',
            lang=LNG.get(lng),
            quality=QLT.get(qlt)
        ))

    itemlist = servertools.get_servers_itemlist(itemlist)

    return itemlist
