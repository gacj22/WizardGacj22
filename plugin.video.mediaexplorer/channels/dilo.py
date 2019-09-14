# -*- coding: utf-8 -*-
from core.libs import *

MOVIE_HOST = 'https://www.yape.nu'
TVSHOW_HOST = 'https://www.dilo.nu'

LNG = Languages({
    Languages.es: ['es'],
    Languages.en: ['en'],
    Languages.la: ['la'],
    Languages.sub_es: ['en_es']
})

QLT = Qualities({
    Qualities.rip: ['DVD Rip', 'HD Rip', 'rip', 'hdrip', 'hdrvrip'],
    Qualities.hd: ['HD 720', 'hd720'],
    Qualities.sd: ['dvdfull'],
    Qualities.hd_full: ['HD 1080p', 'hdfull', 'hd1080'],
    Qualities.scr: ['BR Screener', 'BR Screnner', 'TS Screener', 'TS Screnner',
             'DVD Screener', 'DVD Screnner', 'TS Screener HQ', 'TS Screnner HQ',
             'Cam', 'screener']
})


def mainlist(item):
    logger.trace()
    itemlist = list()

    new_item = item.clone(
        type='label',
        label="Películas Yape",
        category='movie',
        banner='banner/movie.png',
        icon='icon/movie.png',
        poster='poster/movie.png'
    )
    itemlist.append(new_item)
    itemlist.extend(menu_movies(new_item))

    new_item = item.clone(
        type='label',
        label="Series Dilo",
        category='tvshow',
        banner='banner/tvshow.png',
        icon='icon/tvshow.png',
        poster='poster/tvshow.png'
    )
    itemlist.append(new_item)
    itemlist.extend(menu_tvshows(new_item))

    return itemlist


def menu_movies(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        action="list_all",
        label="Novedades",
        type="item",
        category='movie',
        group=True,
        content_type='movies'
    ))

    itemlist.append(item.clone(
        action="list_all",
        label="Más populares de la semana",
        url=MOVIE_HOST + '/catalogue?sort=mosts-week&page=1',
        type="item",
        category='movie',
        group=True,
        content_type='movies'
    ))

    itemlist.append(item.clone(
        action="list_all",
        label="Últimas actualizaciones",
        url=MOVIE_HOST + '/catalogue?sort=time_update&page=1',
        type="item",
        category='movie',
        group=True,
        content_type='movies'
    ))

    itemlist.append(item.clone(
        action="genres",
        label="Géneros",
        url=MOVIE_HOST + "/catalogue",
        type="item",
        category='movie',
        group=True
    ))

    itemlist.append(item.clone(
        action="search",
        label="Buscar",
        query=True,
        type='search',
        category='movie',
        group=True,
        content_type='movies'
    ))

    return itemlist


def menu_tvshows(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        action="newest_episodes",
        label="Nuevos episodios",
        type="item",
        group=True,
        content_type='episodes'
    ))

    itemlist.append(item.clone(
        action="list_all",
        label="Nuevas series",
        type="item",
        category='tvshow',
        group=True,
        content_type='tvshows'
    ))

    itemlist.append(item.clone(
        action="list_all",
        label="Más populares de la semana",
        url=TVSHOW_HOST + '/catalogue?sort=mosts-week',
        type="item",
        category='tvshow',
        group=True,
        content_type='tvshows'
    ))

    itemlist.append(item.clone(
        action="genres",
        label="Géneros",
        url=TVSHOW_HOST + "/catalogue",
        type="item",
        category='tvshow',
        group=True
    ))

    itemlist.append(item.clone(
        action="search",
        label="Buscar",
        query=True,
        type='search',
        category='tvshow',
        group=True,
        content_type='tvshows'
    ))

    return itemlist


def genres(item):
    logger.trace()
    itemlist = list()

    HOST = MOVIE_HOST if item.category == 'movie' else TVSHOW_HOST

    data = httptools.downloadpage(item.url).data
    patron = 'genre\[\]"><label class="custom-control-label" for="(?P<nomge>' \
             '[^"-]+).*?>(?P<genre>[^<]+)</label>'

    for result in re.compile(patron, re.DOTALL).finditer(data):
        itemlist.append(item.clone(
            action="list_all",
            label=result.group('genre').strip(),
            url=HOST + '/catalogue?genre[]=%s' % result.group('nomge'),
            type='item',
            content_type='movies' if item.category == 'movie' else 'tvshows'

        ))

    return sorted(itemlist, key=lambda i: i.label)


def list_all(item):
    logger.trace()
    itemlist = list()

    HOST = MOVIE_HOST if item.category == 'movie' else TVSHOW_HOST

    if not item.url:
        item.url = HOST + '/catalogue?sort=latest&page=1'

    data = httptools.downloadpage(item.url).data
    if item.category == 'movie':
        patron = 'mb-3"><a\shref="(?P<url>[^"]+)"\stitle.*?<img src="' \
             '(?P<poster>[^"]+)"\sclass.*?"text-white">(?P<title>[^<]+)' \
             '</div>.*?-size-13">(?P<year>[\d]+).*?rounded-right">' \
             '(?P<qlt>[^<]+)</span>.*?class="mt-2">(?P<plot>.*?)</div>'
    else:
        patron = 'mb-3"><a href="(?P<url>[^"]+)" class="shadow-sm d-block.*?' \
             '<img src="(?P<poster>[^"]+).*?<div class="text-white txt-s' \
             'ize-14 font-weight-500">(?P<title>[^<]+)</div><div class="' \
             'txt-gray-200 txt-size-12">(?P<year>\d+).*?<div class="desc' \
             'ription">(?P<plot>.*?)</div>'

    for result in re.compile(patron, re.DOTALL).finditer(data):
        new_item = item.clone(
            action='findvideos' if item.category == 'movie' else 'seasons',
            title=result.group('title'),
            url=result.group('url'),
            poster=result.group('poster'),
            plot=result.group('plot').strip(),
            year=result.group('year'),
            quality=QLT.get(result.group('qlt').strip()) if
                item.category == 'movie' else None,
            type='movie' if item.category == 'movie' else 'tvshow',
            content_type='servers' if item.category == 'movie' else 'seasons'
        )
        itemlist.append(new_item)

    next_page = scrapertools.find_single_match(data, '<li\sclass="page-item">'
                '<a\shref="([^"]+)"\saria-label="Netx">')
    if next_page:
        itemlist.append(item.clone(
            url=HOST + '/catalogue' + next_page,
            type='next'
        ))

    return itemlist


def seasons(item):
    logger.trace()
    itemlist = list()

    item.id = scrapertools.find_single_match(httptools.downloadpage
        (item.url).data, '"item_id": (\d+)')
    data = httptools.downloadpage(TVSHOW_HOST + '/api/web/seasons.php',
        {'item_id': item.id}, {'referer': item.url}).data
    patron = '"number":"(?P<season>[^"]+)","permalink":"(?P<url>[^"]+)".*?"picture":"(?P<poster>[^"]*)"'

    for result in re.compile(patron, re.DOTALL).finditer(data):
        itemlist.append(item.clone(
            action="episodes",
            season=int(result.group('season')),
            type='season',
            poster=('https://cdn.dilo.nu/resize/poster/250x350@' +
                result.group('poster')) if result.group('poster')
                else item.poster,
            content_type='episodes'
        ))

    return itemlist


def episodes(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(TVSHOW_HOST + '/api/web/episodes.php',
           {'item_id': item.id, 'season_number': item.season},
           {'referer': item.url}).data
    patron = '"number":"(?P<num_episode>[^"]+)","name":"(?P<title>[^"]*)' \
             '","permalink":"(?P<url>[^"]+)","picture":"(?P<thumb>[^"]*)"' \
             ',"description":"(?P<plot>[^"]*)","audio":"(?P<langs>[^}]*)'

    for result in re.compile(patron, re.DOTALL).finditer(data):
        langs = [LNG.get(l) for l in scrapertools.find_multiple_matches(
                result.group('langs')[:-1].replace('\\', ''), '<img src="htt'
                'ps://cdn.dilo.nu/languajes/(.*?)\.png')]
        if langs:
            itemlist.append(item.clone(
                title=result.group('title'),
                url='%s/%s/' % (TVSHOW_HOST, result.group('url')),
                action="findvideos",
                episode=int(result.group('num_episode')),
                lang=langs,
                type='episode',
                content_type='servers'
            ))

    return itemlist


def newest_episodes(item):
    logger.trace()
    itemlist = list()

    if not item.url:
        item.url = TVSHOW_HOST + '/ajax/getEpisodes.php?audio=all'

    data = httptools.downloadpage(item.url, {'referer': TVSHOW_HOST}).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = 'mb-3"><a class="media" href="(?P<url>[^"]+).*?src="' \
             '(?P<thumb>[^"]+).*?<div class="font-weight-500 txt-size-16 ' \
             'text-truncate" style="max-width: 97%">(?P<title>[^<]+)</div>' \
             '<div>(?P<season_episode>[^<]+)</div>'

    for result in re.compile(patron, re.DOTALL).finditer(data):
        num_season, num_episode = scrapertools.get_season_and_episode(
            result.group('season_episode'))
        itemlist.append(item.clone(
            tvshowtitle=result.group('title'),
            label=result.group('title'),
            thumb=result.group('thumb').replace('90x60@', '448x256@'),
            url=result.group('url'),
            action="findvideos",
            episode=num_episode,
            season=num_season,
            type='episode',
            content_type='servers'
        ))

    total = len(itemlist)
    ini = item.next_page if item.next_page else 0
    item.next_page = ini + 25
    itemlist = itemlist[ini:item.next_page]

    if total > item.next_page:
        itemlist.append(item.clone(
            type='next'
        ))

    return itemlist


def search(item):
    logger.trace()

    HOST = MOVIE_HOST if item.category == 'movie' else TVSHOW_HOST

    if not item.url:
        item.url = HOST + '/search?s=%s&page=1' % item.query.replace(" ", "%20")

    return list_all(item)


def findvideos(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    if item.category == 'movie':
        patron = 'data-link="(?P<url>[^"]+)">.*?class="font-weight-500\smb-' \
             '1">(?P<server>[^<]+)</div>.*?nu//languajes/(?P<lang>.*?)\.png' \
             '".*?rounded\sc\d+">(?P<qlt>[^<]+)</span>.*?display:\snone">' \
             '(?P<tipo>[^<]+)</span></div>'
    else:
        patron = 'data-link="(?P<url>[^"]+)">.*?class="font-weight-500">' \
        '(?P<server>[^<]+)</div>.*?nu//languajes/(?P<lang>.*?)\.png".*?d' \
        'isplay:\snone">(?P<tipo>[^<]+)</span></div>'

    for result in re.compile(patron, re.DOTALL).finditer(data):
        itemlist.append(item.clone(
            url=result.group('url'),
            server=result.group('server').strip().lower(),
            action='play',
            lang=LNG.get(result.group('lang')),
            quality=QLT.get(result.group('qlt').strip()) if
                item.category == 'movie' else None,
            type='server',
            stream=(result.group('tipo').startswith('Reproducir'))
        ))

    return servertools.get_servers_from_id(itemlist)


def play(item):
    logger.trace()

    data = httptools.downloadpage(item.url).data
    url_src = scrapertools.find_single_match(data, 'src="([^"]+)')
    if 'api/redirect.php?' in url_src:
        item.url = httptools.downloadpage(url_src, headers={'Referer': item.url}, follow_redirects=False).headers['location']

    elif url_src:
        item.url = url_src
    logger.debug(item.url)
    servertools.normalize_url(item)
    return item


