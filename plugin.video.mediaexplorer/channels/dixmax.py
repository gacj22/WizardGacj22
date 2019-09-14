# -*- coding: utf-8 -*-
from core.libs import *

HOST = 'https://dixmax.com/'

LNG = Languages({
    Languages.es: ['Castellano'],
    Languages.en: ['Ingles'],
    Languages.la: ['Latino'],
    #Languages.vos: ['vos'],
    Languages.sub_es: ['sub_Castellano'],
    Languages.sub_en: ['sub_Ingles'],
    Languages.sub_la: ['sub_Latino']
})

QLT = Qualities({
    Qualities.rip: ['rip'],
    Qualities.hd: ['hd 720'],
    Qualities.hd_full: ['hd 1080'],
    Qualities.scr: ['ts-screener', 'tc-screener', 'cam']
})


"""
def logout():
    # TODO only debug
    httptools.downloadpage(HOST + '/logout.php')
    logger.debug(is_logged())
"""


def is_logged():
    logger.trace()
    if HOST + '?view=perfil">' in httptools.downloadpage(HOST).data:
        return True
    else:
        return False


def login():
    logger.trace()

    if is_logged():
        return True

    post = {
        'username': settings.get_setting('user', __file__),
        'password': settings.get_setting('password', __file__),
        'remember': '0'
    }
    httptools.downloadpage(HOST + '/login.php', post=post)

    if 'Sesion iniciada correctamente!' in httptools.downloadpage(HOST + '/session.php?action=1', post=post).data:
        return True
    else:
        platformtools.dialog_notification('DixMax', 'Login incorrecto')
        return False


def config(item):
    v = platformtools.show_settings()
    platformtools.itemlist_refresh()
    return v


def mainlist(item):
    logger.trace()
    itemlist = list()

    # Advertencias
    if not settings.get_setting('user', __file__) or not settings.get_setting('user', __file__) or not login():
        itemlist.append(Item(
            label="Es necesario estar registrado en DixMax.com e introducir sus datos en la configuración.   ",
            type='user'
        ))

        itemlist.append(item.clone(
            action="config",
            label="Configuración",
            folder=False,
            category='all',
            type='setting'
        ))

    else:
        # Menu
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

        itemlist.append(item.clone(
            action="config",
            label="Configuración",
            folder=False,
            type='setting'
        ))

    return itemlist


def menupeliculas(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        action="contents",
        label="Populares",
        url= HOST + 'v2/movies/page/1',
        type="item",
        group=True,
        content_type='movies'
    ))

    itemlist.append(item.clone(
        action="generos",
        label="Géneros",
        url=HOST + 'v2/movies',
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
        label="Populares",
        url=HOST + 'v2/series/page/1',
        type="item",
        group=True,
        content_type = 'tvshows'
    ))

    itemlist.append(item.clone(
        action="generos",
        label="Géneros",
        url=HOST + 'v2/series',
        type="item",
        group=True
    ))

    itemlist.append(item.clone(
        action="search",
        label="Buscar",
        query=True,
        type='search',
        group=True,
        content_type = 'tvshows'
    ))

    return itemlist


def generos(item):
    logger.trace()
    itemlist = list()

    generos = {'Acción': 20, 'Animación':57, 'Anime':386, 'Aventura':29, 'Bélico':102, 'Ciencia ficción':41,
               'Cine negro':61, 'Comedia':8, 'Crimen':4, 'Drama':3, 'Fantástico':28, 'Infantil':60, 'Intriga':14,
               'Musical':71, 'Romance':25, 'Terror':44, 'Thriller':2}

    for genero,value in generos.items():
        new_item = item.clone(
            label=genero,
            action="contents",
            url = item.url + '/page/1?year_from=1900&year_to=2019&tmdb_from=0.0&tmdb_to=10.0&genre=%s' % value
        )
        itemlist.append(new_item)

    return sorted(itemlist, key=lambda i: i.label)


def contents(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<div class="col-6 col-sm-4 col-lg-3 col-xl-2"><div class="card">\s?<div class="card__cover">\s?<span class="card__play_2">[^>]+>(\d+)</a>\s?</span>(.*?)data-src-lazy="([^"]+)"[^>]+>\s?</a>\s?</div><div class="card__content">\s?<h3 class="card__title"><a href="([^"]+)">([^<]+)'

    for year, qlt, poster, url, title in scrapertools.find_multiple_matches(data, patron):
        qlt = scrapertools.find_single_match(qlt,'&quality=([^"]+)')
        if qlt:
            new_item = item.clone(
                type= item.category,
                title= title,
                poster= poster.replace('/w185/', '/original/'),
                year=year,
                quality=QLT.get(qlt.lower()),
                url= HOST + url
            )

            if item.category == 'movie':
                new_item.action = 'findvideos'
                new_item.content_type = 'servers'
            else:
                new_item.action = 'seasons'
                new_item.content_type = 'seasons'
                new_item.tvshowtitle = title

            itemlist.append(new_item)

    if itemlist:
        try:
            next_url = scrapertools.find_single_match(data, '/page/(\d+)')
            next_url = item.url.replace('/page/' + next_url, '/page/%s' % (int(next_url) + 1))
            itemlist.append(item.clone(url=next_url, type='next'))
        except:
            pass


    return itemlist


def seasons(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    patron = 'onclick="setMarkedSeasonModal\((\d+), (\d+), (\d+)\);"'

    if item.quality: del item.quality

    for season, id, episodes in scrapertools.find_multiple_matches(data, patron):
        if int(episodes) > 0:
            itemlist.append(item.clone(
                season=int(season),
                title="Temporada %s" % season,
                action="episodes",
                type='season',
                dixmax_id=id,
                content_type='episodes'
            ))

    return itemlist


def episodes(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    patron = "verEnlaces2\('[^']+',%s,'([^']+)','([^']+)',%s,(\d+),'([^']+)'"  % (item.dixmax_id, item.season)

    for title, thumb, episode, fanart in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            title=title,
            thumb=thumb.replace('/w185/', '/original/'),
            fanart=fanart,
            action="findvideos",
            episode=int(episode),
            type='episode',
            content_type='servers'
        ))

    return itemlist


def search(item):
    logger.trace()
    itemlist = list()
    url= HOST + 'api/private/get/search?query=%s&limit=40&f=0' % item.query.replace(" ", "+")

    try:
        data = httptools.downloadpage(url).data
        for f in jsontools.load_json(data)["result"]["ficha"]["fichas"]:
            if f['adult'] and  not settings.get_setting('adult_mode'):
                continue

            if (item.category == 'movie' and f['isSerie']=='0') or (item.category == 'tvshow' and f['isSerie']=='1'):
                new_item = item.clone(
                    type=item.category,
                    title=f['title'],
                    plot=f['sinopsis'],
                    poster='https://image.tmdb.org/t/p/original' + f['poster'],
                    thumb='https://image.tmdb.org/t/p/original' + f['cover'],
                    year=f['year'],
                    dixmax_id=f['id']
                )

                if item.category == 'movie':
                    new_item.action = 'findvideos'
                    new_item.content_type = 'servers'
                    new_item.url= HOST + '/v2/movie/' + f['id']
                else:
                    new_item.action = 'seasons'
                    new_item.content_type = 'seasons'
                    new_item.tvshowtitle = f['title']
                    new_item.url = HOST + '/v2/serie/' + f['id']

                itemlist.append(new_item)
    except:
        pass

    return itemlist


def findvideos(item):
    logger.trace()
    itemlist = list()

    try:
        if item.category == 'movie':
            post = {'id': item.url.split('/')[-1],
                    'i': 'false'}

        else:
            post = {'id': item.dixmax_id,
                    'i': 'true',
                    't': item.season,
                    'e': item.episode}

        data = httptools.downloadpage(HOST + '/api/private/get_links.php', post).data
        sources = jsontools.load_json(data)

    except:
        return itemlist
    #logger.debug(sources)

    if item.season and item.episode:
        sources = filter(lambda x: x['temporada']==str(item.season) and x['episodio']==str(item.episode),sources)

    for source in sources:
        itemlist.append(item.clone(
            type='server',
            action='play',
            lang=LNG.get(source['audio'] if source.get('sub').lower() in ['sin subtitulos', 'otros', ''] else 'sub_' + source['audio']),
            quality=QLT.get('ts-screener' if source['sonido'] == 'Screener' else source['calidad'].lower()),
            url=source['link'],
            date=datetime.datetime.strptime(source['fecha'], "%Y-%m-%d %H:%M:%S")
        ))

    return servertools.get_servers_itemlist(sorted(itemlist, key=lambda i: i.date, reverse=True))
