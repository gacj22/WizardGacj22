# -*- coding: utf-8 -*-
from core.libs import *

HOST = 'https://seriesblanco.info'

LNG = Languages({
    Languages.es: ['es'],
    Languages.sub_es: ['sub'],
    Languages.la: ['la']
})

QLT = Qualities({
    Qualities.hd_full: ['1080p', 'micro-hd-1080p'],
    Qualities.hd: ['micro-hd-720p', 'hdtv', 'hd-720p'],
    Qualities.sd: ['360p']
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
        action="content",
        label="Novedades",
        url=HOST + "/ultimas-peliculas/",
        type="item",
        group=True,
        content_type='movies'
    ))

    ''' TODO de momento no funcionan en las peliculas
    itemlist.append(item.clone( 
        action="generos",
        label="Géneros",
        url=HOST,
        group=True,
        type="item"
    ))'''

    itemlist.append(item.clone(
        action="search",
        label="Buscar",
        query=True,
        type='search',
        category='tvshow',
        group=True,
        content_type='movies'
    ))

    return itemlist


def menuseries(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        action="newest_episodes",
        label="Nuevos Episodios",
        url=HOST,
        type="item",
        group=True,
        content_type='episodes'
    ))

    itemlist.append(item.clone(
        action="content",
        label="Nuevas series",
        url=HOST + "/ultimas-series/",
        type="item",
        group=True,
        content_type='tvshows'
    ))

    itemlist.append(item.clone(
        action="tvshows_az",
        label="Listado alfabético",
        type="item",
        url=HOST,
        group=True,
        content_type='tvshows'
    ))

    itemlist.append(item.clone(
        action="generos",
        label="Géneros",
        url=HOST,
        group=True,
        type="item"
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


def content(item):
    logger.trace()
    itemlist = list()

    if not item.url and item.category == 'tvshow':
        item.url = HOST + "/ultimas-series/"
    elif not item.url:
        item.url = HOST + "/ultimas-peliculas/"

    data = downloadpage(item.url)
    patron = '<a data-toggle="tooltip" title="([^"]+)" class="loop-items" href="([^"]+)".*?src="([^"]+)"'

    for title, url, poster in scrapertools.find_multiple_matches(data, patron):
        new_item = item.clone(
            title=title,
            url=url,
            poster=poster.replace('-105x151', ''))

        if item.category == 'tvshow':
            new_item.action='seasons'
            new_item.type='tvshow'
            new_item.content_type='seasons'
            new_item.tvshowtitle=title
            new_item.label = title

        else:
            new_item.action = 'findvideos_movies'
            new_item.type = 'movie'
            new_item.content_type = 'servers'

        itemlist.append(new_item)

    next_page = scrapertools.find_single_match(data,
                                               '</li><li class=.page-item.><a (?:class="next page-numbers" |)href="([^"]+)')
    if next_page:
        itemlist.append(item.clone(
            url=next_page,
            type='next'
        ))

    return itemlist


def tvshows_az(item):
    logger.trace()
    itemlist = list()

    for letra in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        itemlist.append(item.clone(
            action="content",
            label=letra,
            type="item",
            content_type='tvshows',
            url=HOST + "/lista-de-series/%s/" % letra
        ))

    return itemlist


def search(item):
    logger.trace()
    if item.content_type == 'tvshows':
        item.url = "%s/?s=%s&post_type=ficha" % (HOST, item.query.replace(" ", "+"))
        item.category = 'tvshow'
    else:
        item.url = "%s/?s=%s&post_type=pelicula" % (HOST, item.query.replace(" ", "+"))
        item.category = 'movie'

    return content(item)


def generos(item):
    logger.trace()
    itemlist = list()

    data = downloadpage(item.url)

    if item.category == 'tvshow':
        patron = '<span class="sidebar-nav-mini-hide">Series</span></a><ul>(.*?)</ul>'
    else:
        patron = '<span class="sidebar-nav-mini-hide">Películas</span></a><ul>(.*?)</ul>'

    generos = scrapertools.find_multiple_matches(scrapertools.find_single_match(data, patron),
                                                 '<a href="([^"]+)">([^<]+)</a>')

    for genero in sorted(generos, key= lambda i:i[1]):
        itemlist.append(item.clone(
            action="content",
            label=genero[1],
            type="item",
            content_type='tvshows' if item.category == 'tvshow' else 'movies',
            url=genero[0]
        ))

    return itemlist


def seasons(item):
    logger.trace()
    itemlist = list()

    data = downloadpage(item.url)

    if not item.plot:
        item.plot = scrapertools.find_single_match(data,
                                                   '<div class="tab-pane" id="example-tabs-profile"><p>(.*?)</p>')

    patron = '<div class="block-title open-tab" style="margin-bottom: 0;">.*?Temporada (\d+).*?' \
             '</div>.*?<tbody>.+?</tbody>'
    for num_season in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            action="episodes",
            season=int(num_season),
            type='season',
            plot=item.plot,
            content_type='episodes'
        ))

    return itemlist


def episodes(item):
    logger.trace()
    itemlist = list()
    item.thumb = ''

    data = downloadpage(item.url)

    patron = '<tr><td>.*?href="([^"]+)"[^>]+>([^<]+)</a></td><td class="text-center">(.*?)</td>'
    for url, title, langs in scrapertools.find_multiple_matches(data, patron):
        num_season, num_episode = scrapertools.get_season_and_episode(title)

        if item.season == num_season:
            itemlist.append(item.clone(
                title=item.tvshowtitle,
                url=url,
                action="findvideos_tvshows",
                episode=num_episode,
                lang=[LNG.get(l) for l in
                      scrapertools.find_multiple_matches(langs, 'src=".*?/language/([^\.]+)\.png"')],
                type='episode',
                content_type='servers'
            ))

    return itemlist


def newest_episodes(item):
    logger.trace()
    itemlist = list()
    item.thumb = ''

    if not item.url:
        item.url = HOST

    data = downloadpage(item.url)
    data = scrapertools.find_single_match(data, 'Qué están viendo(.*?)Capítulos estrenados recientemente')

    patron = 'title="([^"]+)".*?href="([^"]+)".*?src="([^"]+)".*?src="([^"]+)".*?' \
             '<div style="padding:0 3px; font-size:10px; background-color: #0084ef ;' \
             'color: #fff;position: absolute; top:5px; right: 40px;">([^<]+)'

    for title, url, poster, lang, qlt in scrapertools.find_multiple_matches(data, patron):
        season_episode = scrapertools.get_season_and_episode(title)
        if season_episode:
            season, episode = season_episode
            title = scrapertools.find_single_match(title, "(.*?)\s%dx%02d" % (season, episode))

            new_item = item.clone(
                label=title,
                tvshowtitle=title,
                action="findvideos_tvshows",
                lang=[LNG.get(scrapertools.find_single_match(lang, 'language/([^\.]+)\.png$'))],
                quality=[QLT.get(qlt.lower())],
                url=url,
                poster=poster.replace('-105x151', ''),
                season=season,
                episode=episode,
                type='episode',
                content_type='servers')

            itemlist.append(new_item)

    return itemlist


def findvideos_tvshows(item):
    logger.trace()
    itemlist = list()

    data = downloadpage(item.url)

    patron = '>([^<]+)</td><td width="84">.*?<td width="200" class="linkComent">.*?data-enlace="([^"]+)"' \
             ' data-language="([^"]+)" data-tipo="([^"]+)"'

    for qlt,url, lang, tipo in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            url=url,
            action='play',
            type='server',
            lang=LNG.get(lang),
            quality=QLT.get(qlt.lower()),
            stream=('online' == tipo)
        ))

    return servertools.get_servers_itemlist(itemlist)


def findvideos_movies(item):
    logger.trace()
    itemlist = list()

    data = downloadpage(item.url)

    patron = '<td width="45"><img src=".*?/language/([^\.]+)\.png".*?<img src="https://www\.google\.com/s2/favicons\?domain=([^"]+)".*?' \
             '<i class="icon-play"></i> ([^<]+)'

    for lang, url, tipo in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            url=url,
            action='play',
            type='server',
            lang=LNG.get(lang),
            stream=('Reproducir' == tipo)
        ))

    return servertools.get_servers_itemlist(itemlist)


def downloadpage(*args, **kwargs):
    logger.trace()

    data = httptools.downloadpage(*args, **kwargs).data
    if 'Error al establecer' in data:
        logger.debug('Error al establecer...')
        time.sleep(3)
        data = httptools.downloadpage(*args, **kwargs).data

    return re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)