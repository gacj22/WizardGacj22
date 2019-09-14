# -*- coding: utf-8 -*-
from core.libs import *

HOST = 'https://www.cliver.to'

LNG = Languages({
    Languages.es: ['es'],
    Languages.la: ['lat', 'es_la'],
    Languages.sub_es: ['vose']
})


def mainlist(item):
    logger.trace()
    itemlist = list()

    new_item = item.clone(
        type='label',
        label="Películas",
        category='movie',
        banner='banner/movie.png',
        icon='icon/movie.png',
        poster='poster/movie.png'
    )
    itemlist.append(new_item)
    itemlist.extend(menupeliculas(new_item))

    new_item = item.clone(
        type='label',
        label="Series",
        category='tvshow',
        banner='banner/tvshow.png',
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
        action="contents",
        label="Estrenos",
        type="item",
        post={'tipo':'estrenos'},
        group=True,
        content_type='movies'
    ))

    itemlist.append(item.clone(
        action="contents",
        label="Novedades",
        post={'tipo':'index'},
        type="item",
        group=True,
        content_type='movies'
    ))

    itemlist.append(item.clone(
        action="generos",
        label="Géneros",
        url=HOST,
        type="item",
        group=True
    ))

    itemlist.append(item.clone(
        action="search",
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
        label="Mas vistas",
        post={'tipo': 'mas-vistas-series'},
        type="item",
        group=True,
        content_type='tvshows'
    ))

    itemlist.append(item.clone(
        action="contents",
        label="Nuevos episodios",
        post={'tipo': 'nuevos-capitulos'},
        type="item",
        group=True,
        content_type='episodes'
    ))

    itemlist.append(item.clone(
        action="generos",
        label="Géneros",
        url=HOST + '/series/',
        type="item",
        group=True
    ))

    itemlist.append(item.clone(
        action="search",
        label="Buscar",
        query=True,
        type='search',
        group=True,
        content_type='tvshows'
    ))

    return itemlist


def generos(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    data = scrapertools.find_single_match(data, '<div class="generos">(.*?)<div class="anios">')

    patron = '<a href="([^"]+)"><span class="cat">([^<]+)</span>'
    for url, title in scrapertools.find_multiple_matches(data, patron):
        if item.category == 'movie':
            item.content_type = 'movies'
            item.post = {'tipo': 'genero'}
        else:
            item.content_type = 'tvshows'
            item.post = {'tipo': 'generosSeries'}

        itemlist.append(item.clone(
            label=title,
            url=url,
            action='contents'))

    return sorted(itemlist, key=lambda x: x.label)


def search(item):
    logger.trace()
    item.category = 'movie' if item.content_type == 'movies' else 'tvshow'
    query = item.query.replace(" ", "+")
    item.post = {
        'tipo': 'buscador' if item.content_type == 'movies' else 'buscadorSeries',
        'adicional': query
        }
    item.url = HOST + '/buscar/?txt=%s' % query
    return contents(item)


def contents(item):
    logger.trace()
    itemlist = list()

    post = item.post if item.post else {}

    if 'pagina' not in post:
        post['pagina'] = 0

    if post.get('tipo','').startswith('genero'):
        post['adicional'] = scrapertools.find_single_match(item.url, '/genero/([^/]+)')

    data = httptools.downloadpage(HOST + '/frm/cargar-mas.php', post=post).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    if item.content_type == 'episodes':
        patron = '<img src="([^"]+)".*?<a href="([^"]+)"><h2>([^<]+)</h2></a><span>([^<]+)</span>'
        for thumb, url, tvshowtitle, title in scrapertools.find_multiple_matches(data, patron):
            num_season, num_episode = scrapertools.get_season_and_episode(title)

            itemlist.append(item.clone(
                tvshowtitle=tvshowtitle,
                label=tvshowtitle,
                url=url,
                thumb=thumb,
                action="findvideos",
                episode=num_episode,
                season=num_season,
                type='episode',
                content_type='servers'
            ))

    else:
        patron = '<div class="portada-p"><a href="([^"]+)"><img src="([^"]+)" alt="([^"]+)">' \
                 '(?:<div class="idiomas">)?(.*?)<div class="titulo-p">.*?<span>(\d{4})'
        for url, poster, title, aux, year in scrapertools.find_multiple_matches(data, patron):
            new_item = item.clone(
                title=title,
                url=url,
                poster=poster,
                year=year,
                type=item.category,
                action='seasons',
                content_type = 'seasons'
            )

            if item.content_type == 'movies':
                lng = scrapertools.find_multiple_matches(aux, '<div class="([^"]+)"></div>')
                new_item.lang=[LNG.get(l) for l in lng]
                new_item.action='findvideos'
                new_item.content_type='servers'

            itemlist.append(new_item)

    # Paginador
    if (item.post.get('tipo') == 'index' and len(itemlist) == 12) or len(itemlist) == 18:
        new_item = item.clone(type='next')
        new_item.post['pagina']+= 1

        itemlist.append(new_item)


    return itemlist


def seasons(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    patron = '<div class="contenido-menu-s" id="temp-(\d+)">'
    for num_season in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            season=int(num_season),
            tvshowtitle=item.title,
            title='Temporada %s' % num_season,
            action="episodes",
            type='season',
            content_type='episodes'))

    return itemlist


def episodes(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<img src="([^"]+)"></div><div class="mic-cont"><div class="mic-cont-header">' \
             '<div class="mic-cont-header-titulo">([^<]+)</div></div><p>([^<]+)</p></div>' \
             '<div class="mic-play" data-id="([^"]+)'

    for thumb, title, plot, data_id in scrapertools.find_multiple_matches(data, patron):
        num_season, num_episode = scrapertools.get_season_and_episode(title)

        if num_season == item.season:
            itemlist.append(item.clone(
                #data_id=data_id,
                title=title.split('-')[1].strip(),
                thumb=thumb,
                action="findvideos",
                episode=num_episode,
                season=num_season,
                type='episode',
                plot= plot,
                content_type='servers'
            ))

    return itemlist


def findvideos(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data

    if item.type=='movie':
        data = httptools.downloadpage(
            HOST + '/frm/obtener-enlaces-pelicula.php',
            post={'pelicula': scrapertools.find_single_match(data,"'datoAdicional': '(\d*)'")}).data

        for lng, v in eval(data).items():
            for enlace in v:
                url = eval(httptools.downloadpage(
                    'https://directvideo.stream/getFile.php',
                    post={'hash':enlace['token']}).data)['url'].replace('\\','')

                if url:
                    itemlist.append(item.clone(
                        url=url,
                        action='play',
                        type='server',
                        lang=LNG.get(lng),
                        stream=True
                    ))

    else:
        patron = '<div class="mic-play".*?data-numcap="%s" data-numtemp="%s".*?data-idiomas="([^"]+)([^>]+)>'\
                 % (item.episode, item.season)
        lng, urls = scrapertools.find_single_match(data, patron)

        for i in lng.split(','):
            itemlist.append(item.clone(
                url=scrapertools.find_single_match(urls, 'data-url-%s="([^"]+)"' % i.replace('_','-')),
                action='play',
                type='server',
                lang=LNG.get(i),
                stream=True
            ))

    return servertools.get_servers_itemlist(itemlist)

