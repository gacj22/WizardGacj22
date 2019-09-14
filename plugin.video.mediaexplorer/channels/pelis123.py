# -*- coding: utf-8 -*-
from core.libs import *
import base64
import binascii
from lib.aes import AESModeOfOperationCBC
import hashlib

HOST = "https://pelis123.tv"

LNG = Languages({
    Languages.sub_es: ['subtitulado'],
    Languages.es: ['castellano'],
    Languages.en: ['english'],
    Languages.la: ['latino dub'],
})

QLT = Qualities({
    Qualities.hd_full: ['hd 1080'],
    Qualities.hd: ['hd'],
    Qualities.rip: ['hd rip', 'sd', 'hd-rip'],
    Qualities.scr: ['cam-ts', 'cam'],
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

    return itemlist


def menupeliculas(item):
    logger.trace()

    itemlist = list()

    itemlist.append(item.clone(
        label='Novedades',
        action='content',
        content_type='movies',
        type="item",
        group=True
    ))

    itemlist.append(item.clone(
        label='Destacadas',
        action='content',
        url=HOST + '/search.html?type=movies&hot=featured&order=last_update&order_by=asc',
        content_type='movies',
        type="item",
        group=True
    ))

    itemlist.append(item.clone(
        label='Generos',
        action='generos',
        url=HOST,
        content_type='items',
        type="item",
        group=True
    ))

    itemlist.append(item.clone(
        label='Buscar',
        action='search',
        content_type='movies',
        query=True,
        type='search',
        group=True
    ))
    return itemlist


def menuseries(item):
    logger.trace()

    itemlist = list()

    itemlist.append(item.clone(
        label='Últimos Episodios',
        action='content',
        content_type='episodes',
        type="item",
        group=True
    ))

    itemlist.append(item.clone(
        label='Nuevas Series',
        action='content',
        url=HOST + '/series.html',
        content_type='tvshows',
        type="item",
        group=True
    ))

    itemlist.append(item.clone(
        label='Generos',
        action='generos',
        url=HOST,
        content_type='items',
        type="item",
        group=True
    ))

    itemlist.append(item.clone(
        label='Buscar',
        action='search',
        content_type='tvshows',
        query=True,
        type='search',
        group=True
    ))
    return itemlist


def search(item):
    logger.trace()
    item.url = HOST + '/search.html?q=%s&type=%s' % (item.query ,
                                            ('movies' if item.content_type == 'movies' else 'series'))
    return content(item)


def generos(item):
    logger.trace()
    itemlist = []

    data = scrapertools.find_single_match(httptools.downloadpage(item.url).data,
                                          '<a href="#">Género</a>(.*?)<a href="#">Country</a>')

    for url, name in scrapertools.find_multiple_matches(data, '<a href="([^"]+)">([^<]+)</a>'):
        itemlist.append(item.clone(
            label=name,
            url=url + ('?type=movies' if item.category == 'movie' else '?type=series&order=title&order_by=asc'),
            content_type='movies' if item.category == 'movie' else 'tvshows',
            action='content'
        ))

    return itemlist


def content(item):
    logger.trace()
    itemlist = []
    list_series = list()

    if not item.url:
        item.url = (HOST + '/search.html?type=%s&order=last_update&order_by=asc') \
                   % ('movies' if item.content_type == 'movies' else 'series')

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<div class="tray-item" episode-tag="\[([^\]]+).*?<a href="([^"]+).*?src="([^"]+)"></a>' \
             '<div class="tray-item-description"><div class="tray-item-title">([^<]+)</div>.*?' \
             '<div class="tray-item-quality">([^<]+)</div><div class="tray-item-episode">([^<]+).*?' \
             '<span class=.badge badge-success.>País</span>.*?<br><br>(.*?)" data-original-title=".*?\((\d{4})'

    for lng, url, poster, title, qlt, duration, plot, year in scrapertools.find_multiple_matches(data, patron):
        title = (scrapertools.find_single_match(title, "(.*) S\d+") or title).strip()

        new_item = item.clone(
            action='findvideos',
            title=title,
            url=url,
            quality=QLT.get(qlt.lower().strip()),
            lang=[LNG.get(l) for l in lng.replace('"','').lower().split(',')],
            plot=plot,
            year=year)

        if item.content_type == 'movies':
            new_item.type='movie'
            new_item.poster = urllib.unquote(poster)
            new_item.content_type = 'servers'

        elif item.content_type == 'tvshows':
            if title.lower() in list_series:
                continue
            list_series.append(title.lower())
            new_item.label = new_item.tvshowtitle = title
            new_item.poster = urllib.unquote(poster)
            new_item.action='seasons'
            new_item.type = 'tvshow'
            new_item.content_type='seasons'

        else:
            new_item.label = new_item.tvshowtitle = new_item.title
            new_item.type='episode'
            new_item.thumb=urllib.unquote(poster)
            new_item.season, new_item.episode = scrapertools.get_season_and_episode(duration)

        itemlist.append(new_item)

    # Paginador
    max_page = scrapertools.find_multiple_matches(data, 'class="btn btn-outline-primary waves-effect[^>]+>(\d+)<')
    max_page.sort(key=lambda x: int(x), reverse=True)
    page_actual = int(scrapertools.find_single_match(item.url, '&page=(\d+)') or '1')

    if itemlist and max_page and max_page[0] >= page_actual + 1 :
        if item.url.endswith('.html'):
            item.url += '?'

        if not '&page=' in item.url:
            next_url = item.url + '&page=2'
        else:
            next_url = item.url.replace('&page=%s' % page_actual, '&page=%s' % (page_actual + 1))

        itemlist.append(item.clone(url=next_url, type='next'))

    return itemlist


def seasons(item):
    logger.trace()
    itemlist = []
    seasons = []

    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, '<div class="list-season">(.*?)<div class="info-embed">')

    if data:
        seasons = scrapertools.find_multiple_matches(data, 'href="([^"]+)" class="btn btn-outline-dark btn-sm">Temporada (\d+)</a>')
        # Añadir temporada actual
        seasons.append((item.url, scrapertools.find_single_match(item.url, '-season-(\d+)-')))

    for season in sorted(seasons, key=lambda x: int(x[1])):
        itemlist.append(item.clone(
            url=season[0],
            title='Temporada %s' % season[1],
            season=int(season[1]),
            type='season',
            action='episodes',
            content_type='episodes',
            tvshowtitle=item.title
        ))

    return itemlist


def episodes(item):
    logger.trace()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    item.url = scrapertools.find_single_match(data, '<link rel="canonical" href="([^"]+)"')
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<div class="watch-playlist-item.*?data-episode="([^"]+)"><a href="([^"]+)".*?src="([^"]+)".*?' \
             '<div class="watch-playlist-tag">(.*?)</div></a>'

    for episode, url, thumb, lang in scrapertools.find_multiple_matches(data, patron):
        lng = scrapertools.find_multiple_matches(lang, 'alt="([^"]+)"')
        itemlist.append(item.clone(
            url=url,
            type='episode',
            lang=[LNG.get(l.lower()) for l in lng],
            action='findvideos',
            thumb=thumb,
            content_type='servers',
            title='Episodio %s' % episode,
            episode=int(episode)
        ))

    return itemlist


def findvideos(item):
    logger.trace()
    itemlist = list()
    threads = list()

    data = httptools.downloadpage(item.url).data
    post = {
        'episode': item.episode or '',
        'movie_id': scrapertools.find_single_match(item.url, '([a-z0-9A-Z]+-[a-z0-9A-Z]+)\.html$')
    }
    headers = {
        'X-CSRF-TOKEN': scrapertools.find_single_match(data, '<meta name="csrf-token" content="([^"]+)')
    }

    sources = jsontools.load_json(httptools.downloadpage(HOST + '/ajax/watch/list', post=post, headers=headers).data)

    for la, v in sources.get('list',{}).items():
        for server, urls in v.items():
            for u in urls:
                new_item = item.clone(
                    url=u,
                    type='server',
                    lang=LNG.get(la.lower()),
                    action='play',
                    server='directo' if server == "Server 4" else None,
                    servername='Pelis123' if server == "Server 4" else None)

                t = Thread(target=get_server,
                           args=[new_item, itemlist])

                t.setDaemon(True)
                t.start()
                threads.append(t)

    while [t for t in threads if t.isAlive()]:
        time.sleep(0.3)

    return servertools.get_servers_itemlist(itemlist)


def get_server(item, itemlist):
    try:
        data = httptools.downloadpage(item.url).data
        url = scrapertools.find_single_match(data, 'iframe src\s*=\s*["|\']([^"\']+)["|\']')

        if not url:
            url = scrapertools.find_single_match(data, 'source src\s*=\s*["|\']([^"\']+)["|\']')

        if url:
            itemlist.append(item.clone(url=url))
    except:
        pass
