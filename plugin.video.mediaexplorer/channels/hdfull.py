# -*- coding: utf-8 -*-
from core.libs import *

host = settings.get_setting('host', __file__, getvalue=True)

LNG = Languages({
    Languages.sub_es: ['sub', 'espsub', 'engsub'],
    Languages.es: ['spa', 'esp'],
    Languages.en: ['eng'],
    Languages.la: ['lat']
})

QLT = Qualities({
    Qualities.rip: ['dvdrip', 'rhdtv'],
    Qualities.hd_full: ['hd1080m', 'hd1080'],
    Qualities.hd: ['hd720m', 'hdtv', 'hd720'],
    Qualities.scr: ['dvdscr', 'ts', 'cam']
})


def mainlist(item):
    logger.trace()

    itemlist = list()

    new_item = item.clone(
        type='label',
        label="Películas",
        url=host,
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
        url=host,
        category='tvshow',
        thumb='thumb/tvshow.png',
        icon='icon/tvshow.png',
        poster='poster/tvshow.png',
    )
    itemlist.append(new_item)
    itemlist.extend(menuseries(new_item))

    if settings.get_setting('account', __file__) and login():
        itemlist.append(item.clone(
            action="menuusuario",
            label="Items Usuario",
            category='all',
            type='user'
        ))

    else:
        itemlist.append(Item(
            label="Habilita tu cuenta para activar los items de usuario...",
            category='all',
            type='warning'
        ))

    itemlist.append(item.clone(
        action="config",
        label="Configuración",
        folder=False,
        category='all',
        type='setting'
    ))

    return itemlist


def config(item):
    v = platformtools.show_settings(item=item)
    platformtools.itemlist_refresh()
    return v


def login():
    logger.trace()

    data = httptools.downloadpage(host).data

    patron = '<input type=\'hidden\' name=\'__csrf_magic\' value="([^"]+)" />'
    sid = scrapertools.find_single_match(data, patron)
    post = {
        '__csrf_magic': sid,
        'username': settings.get_setting('user', __file__),
        'password': settings.get_setting('password', __file__),
        'action': 'login'
    }

    data = httptools.downloadpage(host, post=post).data

    if 'Bienvenido %s' % settings.get_setting('user', __file__) not in data:
        platformtools.dialog_notification('HDFull', 'Login incorrecto')
        return False
    else:
        return True


def menuusuario(item):
    logger.trace()
    itemlist = list()

    itemlist.append(Item(
        label="Peliculas",
        type='label',
        icon='icon/movie.png'
    ))

    itemlist.append(item.clone(
        action="user_movies",
        label="Favoritas",
        url=host + "/a/my?target=movies&action=favorite",
        content_type='movies',
        group=True,
        type="item"
    ))

    itemlist.append(item.clone(
        action="user_movies",
        label="Pendientes",
        url=host + "/a/my?target=movies&action=pending",
        content_type='movies',
        group=True,
        type='item'
    ))

    itemlist.append(item.clone(
        action="user_movies",
        label="Vistas",
        url=host + "/a/my?target=movies&action=seen",
        content_type='movies',
        group=True,
        type='item'
    ))

    itemlist.append(Item(label="Series",
                         type='label',
                         icon='icon/tvshow.png'
                         ))

    itemlist.append(item.clone(
        action="user_tvshows",
        label="Para ver",
        url=host + "/a/my?target=shows&action=watch",
        content_type='movies',
        group=True,
        type='item'
    ))

    itemlist.append(item.clone(
        action="user_tvshows",
        label="Siguiendo",
        url=host + "/a/my?target=shows&action=following",
        content_type='movies',
        group=True,
        type='item'
    ))

    itemlist.append(item.clone(
        action="user_tvshows",
        label="Favoritas",
        url=host + "/a/my?target=shows&action=favorite",
        content_type='movies',
        group=True,
        type='item'
    ))

    itemlist.append(item.clone(
        action="user_tvshows",
        label="Pendientes",
        url=host + "/a/my?target=shows&action=pending",
        content_type='movies',
        group=True,
        type='item'
    ))

    itemlist.append(item.clone(
        action="user_tvshows",
        label="Recomendadas",
        url=host + "/a/my?target=shows&action=recommended",
        content_type='movies',
        group=True,
        type='item'
    ))

    itemlist.append(item.clone(
        action="user_tvshows",
        label="Finalizadas",
        url=host + "/a/my?target=shows&action=seen",
        content_type='movies',
        group=True,
        type='item'
    ))

    return itemlist


def menupeliculas(item):
    logger.trace()

    itemlist = list()

    itemlist.append(item.clone(
        action="movies",
        label="ABC",
        url=host + "/peliculas/abc",
        type="item",
        group=True,
        content_type='movies'
    ))

    itemlist.append(item.clone(
        action="movies",
        label="Nuevas",
        url=host + "/peliculas/date",
        type="item",
        group=True,
        content_type='movies'
    ))

    itemlist.append(item.clone(
        action="movies",
        label="Actualizadas",
        url=host + "/peliculas-actualizadas",
        type="item",
        group=True,
        content_type='movies'
    ))

    itemlist.append(item.clone(
        action="movies",
        label="Rating IMDB",
        url=host + "/peliculas/imdb_rating",
        type="item",
        group=True,
        content_type='movies'
    ))

    itemlist.append(item.clone(
        action="generos",
        label="Géneros",
        url=host,
        type="item",
        group=True
    ))

    itemlist.append(item.clone(
        action="movie_search",
        label="Buscar",
        url=host,
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
        action="tvshows",
        label="Nuevas",
        url=host + "/series",
        type="item",
        group=True,
        content_type='tvshows'
    ))

    itemlist.append(item.clone(
        action="tvshows",
        label="Rating IMDB",
        url=host + "/series/imdb_rating",
        type="item",
        group=True,
        content_type='tvshows'
    ))

    itemlist.append(item.clone(
        action="series_az",
        type="item",
        group=True,
        label="ABC"
    ))

    itemlist.append(item.clone(
        action="generos_tvshow",
        label="Géneros",
        type="item",
        group=True,
        url=host
    ))

    itemlist.append(item.clone(
        action="tv_search",
        label="Buscar",
        url=host,
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
    data = scrapertools.find_single_match(data, '<li class="dropdown"><a href="%s/peliculas"(.*?)</ul>' % host)

    patron = '<li><a href="([^"]+)">([^<]+)</a></li>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, genre in matches:
        itemlist.append(item.clone(
            action='movies',
            label=genre,
            url=urlparse.urljoin(item.url, url),
            content_type='movies'
        ))

    return itemlist


def generos_tvshow(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, '<li class="dropdown"><a href="%s/series"(.*?)</ul>' % host)

    patron = '<li><a href="([^"]+)">([^<]+)</a></li>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, genre in matches:
        itemlist.append(item.clone(
            action='tvshows',
            label=genre,
            url=urlparse.urljoin(item.url, url),
            content_type='tvshows'
        ))

    return itemlist


def movies(item):
    logger.trace()
    itemlist = list()

    if settings.get_setting('account', __file__):
        state = jsontools.load_json(httptools.downloadpage(host + '/a/status/all').data)
    else:
        state = {}

    data = httptools.downloadpage(item.url).data

    patron = '<a href="(?P<url>[^"]+)" class="spec-border-ie".*?' \
             '<img.*?src="(?P<thumb>[^"]+)".*?title="(?P<title>[^"]+)".*?' \
             '(?P<lang>(?:<img src="[^<]+)+<\/div>)[^<]+<div class="right">.*?' \
             '(?:<div class="rating">(?P<rat>[^<])+.*?>(?P<dec>[^<]+)<.*?)?setFavorite\(\d,\s*(?P<id>\d+)\s*,'

    for result in re.compile(patron, re.DOTALL).finditer(data):
        itemlist.append(item.clone(
            action='findvideos',
            label=result.group('title'),
            url=urlparse.urljoin(item.url, result.group('url')),
            poster=result.group('thumb').replace("/tthumb/130x190/", "/tthumb/130x190/"),
            lang=[LNG.get(l) for l in
                  scrapertools.find_multiple_matches(result.group('lang'), 'src=".*?/([^./]+).png"')],
            rating='%s.%s' % (result.group('rat') or '0', result.group('dec') or '0'),
            title=result.group('title'),
            type='movie',
            content_type='servers',
            hdfullid=result.group('id'),
            hdfulltype='movies',
            label_extra={"sublabel": " [F]", "color": "yellow", "value": "True"} if result.group('id') in state.get(
                'favorites', {}).get('movies', []) else "",
            watched=status_watched(state, 'movies', result.group('id')) == 1
        ))

    # Paginador
    next_url = scrapertools.find_single_match(data, '<a href="([^"]+)">&raquo;</a>')
    if next_url:
        itemlist.append(item.clone(
            action=item.action,
            url=urlparse.urljoin(item.url, next_url),
            type='next'
        ))

    return itemlist


def tvshows(item):
    logger.trace()
    itemlist = list()

    if settings.get_setting('account', __file__):
        state = jsontools.load_json(httptools.downloadpage(host + '/a/status/all').data)
    else:
        state = {}

    data = httptools.downloadpage(item.url).data

    patron = '<a href="(?P<url>[^"]+)" class="spec-border-ie".*?' \
             '<img.*?src="(?P<thumb>[^"]+)".*?title="(?P<title>[^"]+)".*?' \
             '(?:<div class="rating">(?P<rat>[^<])+.*?>(?P<dec>[^<]+)<.*?)?' \
             'setFavorite\(\d,\s*(?P<id>\d+)\s*,'

    for result in re.compile(patron, re.DOTALL).finditer(data):
        itemlist.append(item.clone(
            action='seasons',
            label=result.group('title'),
            url=urlparse.urljoin(item.url, result.group('url')),
            poster=result.group('thumb').replace("/tthumb/130x190/", "/tthumb/130x190/"),
            type='tvshow',
            content_type='seasons',
            rating='%s.%s' % (result.group('rat') or '0', result.group('dec') or '0'),
            title=result.group('title'),
            hdfullid=result.group('id'),
            hdfulltype='shows',
            label_extra={"sublabel": " [F]", "color": "yellow", "value": "True"} if result.group('id') in state.get(
                'favorites', {}).get(
                'shows', []) else "",
            watched=status_watched(state, 'shows', result.group('id')) == 3
        ))

    # Paginador
    next_url = scrapertools.find_single_match(data, '<a href="([^"]+)">&raquo;</a>')
    if next_url:
        itemlist.append(item.clone(action='tvshows',
                                   url=urlparse.urljoin(item.url, next_url),
                                   type='next'
                                   ))
    return itemlist


def seasons(item):
    logger.trace()
    itemlist = list()

    if settings.get_setting('account', __file__):
        state = jsontools.load_json(httptools.downloadpage(host + '/a/status/all').data)

        itemlist.append(item.clone(
            label=(
                'HDFull: Añadir a favoritos',
                'HDFull: Quitar de favoritos'
            )[item.hdfullid in state['favorites'][item.hdfulltype]],
            action='favorito',
            type='label',
            hdfullstatus=('1', '-1')[item.hdfullid in state['favorites'][item.hdfulltype]]
        ))

        itemlist.append(item.clone(
            label=(
                'HDFull: Marcar como pendiente',
                'HDFull: Quitar marca',
                'HDFull: Marcar como siguiendo',
                'HDFull: Marcar como finalizada')[status_watched(state, item.hdfulltype, item.hdfullid)],
            action='status',
            type='label',
            hdfullstatus=(2, 0, 3, 1)[status_watched(state, item.hdfulltype, item.hdfullid)]
        ))

    data = httptools.downloadpage(item.url).data

    patron = '<a href=\'(?P<url>[^\']+)\' rel="bookmark".*?' \
             '<img.*?original-title="(?P<title>[^"]+)".*?src="(?P<thumb>[^"]+)" />'

    for result in re.compile(patron, re.DOTALL).finditer(data):
        itemlist.append(item.clone(
            action='episodes',
            label=result.group('title'),
            url=urlparse.urljoin(item.url, result.group('url') + '/'),
            poster=result.group('thumb').replace("/tthumb/130x190/", "/tthumb/130x190/"),
            type='season',
            content_type='episodes',
            tvshowtitle=item.title,
            season=int(result.group('title').split(' ')[1])
        ))

    if settings.get_setting('account', __file__) and len(itemlist) == 2:
        # No se han encontrado temporadas
        itemlist = []

    return itemlist


def episodes(item):
    logger.trace()
    itemlist = list()

    if settings.get_setting('account', __file__):
        state = jsontools.load_json(httptools.downloadpage(host + '/a/status/all').data)
    else:
        state = {}

    post = {
        'action': 'season',
        'show': item.hdfullid,
        'season': item.season
    }

    episode_list = jsontools.load_json(
        httptools.downloadpage(urlparse.urljoin(item.url, '/a/episodes'), post=post).data
    )

    for episode in episode_list:
        itemlist.append(item.clone(
            action='findvideos',
            label=str(episode['title'].get('es', episode['title']['en'])).strip('" '),
            url=urlparse.urljoin(item.url, 'episodio-%s' % episode['episode']),
            thumb=urlparse.urljoin(host, '/tthumb/130x190/' + episode['thumbnail']),
            lang=[LNG.get(l.lower()) for l in episode['languages']],
            type='episode',
            content_type='servers',
            episode=int(episode['episode']),
            title=str(episode['title'].get('es', episode['title']['en'])).strip('" '),
            hdfulltype='episodes',
            hdfullid=episode['id'],
            favorite=episode['id'] in state.get('favorites', {}).get('episodes', []),
            # watched=int(state.get('status', {}).get('episodes', {}).get(episode['id'], 0)) == 1
            watched=status_watched(state, 'episodes', episode['id']) == 1
        ))

    return itemlist


def newest_episodes(item):
    logger.trace()
    itemlist = list()

    if settings.get_setting('account', __file__):
        state = jsontools.load_json(httptools.downloadpage(host + '/a/status/all').data)
    else:
        state = {}

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<div class="item" style="text-align:center">.*?'
    patron += '<a href="(?P<url>[^"]+)" class=".*?'
    patron += 'src="(?P<thumb>[^"]+).*?'
    patron += '<div class="left">(?P<lang>.*?)<div class="right">.*?'
    patron += '<div class="rating">(?P<season>[^<]+).*?'
    patron += '<b class="sep">x</b>(?P<episode>[^<]+).*?'
    patron += 'title="(?P<title>[^"]+).*?'
    patron += 'data-seen="(?P<id>[^"]+)'

    for result in re.compile(patron, re.DOTALL).finditer(data):
        tvshowstitle = result.group('title').split('-', 1)[0].strip()
        new_item = item.clone(
            action='findvideos',
            tvshowtitle=tvshowstitle,
            label=tvshowstitle,
            type='episode',
            content_type='servers',
            url=result.group('url'),
            thumb=scrapertools.find_single_match(result.group('thumb'), 'src=([^&]+)'),
            lang=[LNG.get(l) for l in
                  scrapertools.find_multiple_matches(result.group('lang'), 'src=".*?/([^./]+).png"')],
            season=int(result.group('season')),
            episode=int(result.group('episode')),
            hdfulltype='episodes',
            hdfullid=result.group('id'),
            favorite=result.group('id') in state.get('favorites', {}).get('episodes', []),
            # watched=int(state.get('status', {}).get('episodes', {}).get(result.group('id'), 0)) == 1
            watched=status_watched(state, 'episodes', result.group('id')) == 1
        )
        itemlist.append(new_item)

    return itemlist


def user_movies(item):
    logger.trace()
    itemlist = list()

    state = jsontools.load_json(httptools.downloadpage(host + '/a/status/all').data)

    url, post = item.url.split("?")
    data = httptools.downloadpage(url, post=post).data

    movie_list = jsontools.load_json(data)

    for movie in movie_list:
        itemlist.append(item.clone(
            action='findvideos',
            label=movie['title'].get('es', movie['title']['en']).strip(),
            url=urlparse.urljoin(host, '/pelicula/' + movie['perma']),
            poster=urlparse.urljoin(host, '/tthumb/130x190/' + movie.get('thumbnail', movie['thumb'])),
            type='movie',
            content_type='servers',
            hdfullid=movie['id'],
            hdfulltype='movies',
            title=movie['title'].get('es', movie['title']['en']).strip(),
            favorite=movie['id'] in state.get('favorites', {}).get('movies', []),
            # watched=int(state.get('status', {}).get('movies', {}).get(movie['id'], 0)) == 1
            watched=status_watched(state, 'movies', movie['id']) == 1
        ))

    return itemlist


def user_tvshows(item):
    logger.trace()
    itemlist = list()

    state = jsontools.load_json(httptools.downloadpage(host + '/a/status/all').data)

    url, post = item.url.split("?")
    data = httptools.downloadpage(url, post=post).data

    tvshow_list = jsontools.load_json(data)

    for tvshow in tvshow_list:
        itemlist.append(item.clone(
            action='seasons',
            label=tvshow['title'].get('es', tvshow['title']['en']).strip(),
            url=urlparse.urljoin(host, '/serie/' + tvshow['permalink']),
            poster=urlparse.urljoin(host, '/tthumb/130x190/' + tvshow.get('thumbnail')),
            type='tvshow',
            content_type='seasons',
            hdfullid=tvshow['id'],
            hdfulltype='shows',
            title=tvshow['title'].get('es', tvshow['title']['en']).strip(),
            favorite=tvshow['id'] in state.get('favorites', {}).get('tvshows', []),
            # watched=int(state.get('status', {}).get('tvshows', {}).get(tvhosw['id'], 0)) == 3
            watched=status_watched(state, 'tvshows', tvshow['id']) == 3
        ))

    return itemlist


def tv_search(item):
    logger.trace()
    itemlist = list()

    if settings.get_setting('account', __file__):
        state = jsontools.load_json(httptools.downloadpage(host + '/a/status/all').data)
    else:
        state = {}

    data = httptools.downloadpage(host).data
    post = {
        '__csrf_magic': scrapertools.find_single_match(data, '.__csrf_magic. value="(sid:[^"]+)"'),
        'menu': 'search',
        'query': item.query
    }

    data = httptools.downloadpage(host + '/buscar', post=post).data

    patron = '<a href="(?P<url>[^"]+)" class="spec-border-ie".*?' \
             '<img class=".*?show-thumbnail".*?src="(?P<thumb>[^"]+)".*?' \
             '(?:<div class="rating">(?P<rat>[^<])+.*?>(?P<dec>[^<]+)<.*?)?' \
             'title="(?P<title>[^"]+)".*?setFavorite\(\d,\s*(?P<id>\d+)\s*,'

    for result in re.compile(patron, re.DOTALL).finditer(data):
        itemlist.append(item.clone(
            action='seasons',
            label=result.group('title'),
            url=urlparse.urljoin(item.url, result.group('url')),
            poster=result.group('thumb').replace("/tthumb/130x190/", "/tthumb/130x190/"),
            type='tvshow',
            content_type='seasons',
            rating='%s.%s' % (result.group('rat') or '0', result.group('dec') or '0'),
            title=result.group('title'),
            hdfullid=result.group('id'),
            hdfulltype='shows',
            favorite=result.group('id') in state.get('favorites', {}).get('shows', []),
            # watched=int(state.get('status', {}).get('shows', {}).get(result.group('id'), 0)) == 3
            watched=status_watched(state, 'shows', result.group('id')) == 3
        ))

    return itemlist


def movie_search(item):
    logger.trace()
    itemlist = list()

    if settings.get_setting('account', __file__):
        state = jsontools.load_json(httptools.downloadpage(host + '/a/status/all').data)
    else:
        state = {}

    data = httptools.downloadpage(host).data
    post = {
        '__csrf_magic': scrapertools.find_single_match(data, '.__csrf_magic. value="(sid:[^"]+)"'),
        'menu': 'search',
        'query': item.query
    }

    data = httptools.downloadpage(host + '/buscar', post=post).data

    patron = '<a href="(?P<url>[^"]+)" class="spec-border-ie".*' \
             '?<img class=".*?spec-border".*?src="(?P<thumb>[^"]+)".*?' \
             '(?:<div class="rating">(?P<rat>[^<])+.*?>(?P<dec>[^<]+)<.*?)?' \
             'title="(?P<title>[^"]+)".*?setFavorite\(\d,\s*(?P<id>\d+)\s*,'

    for result in re.compile(patron, re.DOTALL).finditer(data):
        itemlist.append(item.clone(
            action='findvideos',
            label=result.group('title'),
            url=urlparse.urljoin(item.url, result.group('url')),
            poster=result.group('thumb').replace("/tthumb/130x190/", "/tthumb/130x190/"),
            type='movie',
            content_type='servers',
            rating='%s.%s' % (result.group('rat') or '0', result.group('dec') or '0'),
            title=result.group('title'),
            hdfullid=result.group('id'),
            hdfulltype='movies',
            favorite=result.group('id') in state.get('favorites', {}).get('movies', []),
            # watched=int(state.get('status', {}).get('movies', {}).get(result.group('id'), 0)) == 1
            watched=status_watched(state, 'movies', result.group('id')) == 1
        ))

    return itemlist


def series_az(item):
    logger.trace()

    itemlist = list()

    for letra in "ABCDEFGHIJKLMNOPQRSTUVWXYZ#":
        itemlist.append(item.clone(
            action='tvshows',
            label=letra,
            url=urlparse.urljoin(host, '/series/abc/' + letra.replace('#', '9')),
            content_type='tvshows'
        ))

    return itemlist


def findvideos(item):
    logger.trace()

    itemlist = list()
    import base64

    if settings.get_setting('account', __file__):
        state = jsontools.load_json(httptools.downloadpage(host + '/a/status/all').data)

        if not state:
            state = {"favorites": {
                "movies": [],
                "shows": [],
                "episodes": []
            },
                "status": {
                    "movies": [],
                    "shows": [],
                    "episodes": []
                }}

        if item.hdfulltype == 'movies':
            itemlist.append(item.clone(
                label=(
                    'HDFull: Añadir a favoritos',
                    'HDFull: Quitar de favoritos'
                )[item.hdfullid in state['favorites']['movies']],
                action='favorito',
                type='label',
                hdfullstatus=(1, -1)[item.hdfullid in state['favorites'][item.hdfulltype]]
            ))

            itemlist.append(item.clone(
                label=(
                    'HDFull: Marcar como visto',
                    'HDFull: Marcar como pendiente',
                    'HDFull: Quitar marca'
                    # )[int(state['status']['movies'].get(item.hdfullid, 0))],
                )[status_watched(state, 'movies', item.hdfullid)],
                action='status',
                type='label',
                # hdfullstatus=(1, 2, 0)[int(state['status'][item.hdfulltype].get(item.hdfullid, 0))]
                hdfullstatus=(1, 2, 0)[status_watched(state, item.hdfulltype, item.hdfullid)]
            ))

        if item.hdfulltype == 'episodes':
            itemlist.append(item.clone(
                label=(
                    'HDFull: Marcar como visto',
                    'HDFull: Quitar marca'
                    # )[int(state['status'][item.hdfulltype].get(item.hdfullid, 0))],
                )[status_watched(state, item.hdfulltype, item.hdfullid)],
                action='status',
                type='label',
                hdfullstatus=(1, 0)[status_watched(state, item.hdfulltype, item.hdfullid)]
            ))

    key = settings.get_setting('key', __file__)

    if not key:
        data_js = httptools.downloadpage(host + "/templates/hdfull/js/jquery.hdfull.view.min.js").data
        key = scrapertools.find_single_match(data_js, 'JSON.parse\(atob.*?substrings\((.*?)\)')
        settings.set_setting('key', key, __file__)

    data = httptools.downloadpage(item.url).data
    data_obf = scrapertools.find_single_match(data, 'var ad = \'([^\']+)\';')
    decoded = base64.b64decode(data_obf)

    servers = jsontools.load_json(obfs(decoded, 126 - int(key)))
    decoder = Decoder()
    for server in servers:
        data = decoder.get(server['provider'], server['code'])
        itemlist.append(item.clone(
            action='play',
            url=data['link'],
            type='server',
            lang=LNG.get(server['lang'].lower()),
            quality=QLT.get(server['quality']),
            stream=data['stream']
        ))

    itemlist = servertools.get_servers_itemlist(itemlist)

    if settings.get_setting('account', __file__) and \
            (item.hdfulltype == 'movies' and len(itemlist) == 2) or \
            (item.hdfulltype == 'episodes' and len(itemlist) == 1):
        # No se han encontrado servidores
        itemlist = []

    return itemlist


def status(item):
    logger.trace()
    types = {
        'movies': 2,
        'shows': 1,
        'episodes': 3
    }

    post = {
        'target_id': item.hdfullid,
        'target_type': types[item.hdfulltype],
        'target_status': item.hdfullstatus
    }

    httptools.downloadpage(host + "/a/status", post=post)
    platformtools.itemlist_refresh()


def favorito(item):
    logger.trace()
    types = {
        'movies': 2,
        'shows': 1
    }
    post = {
        'like_id': item.hdfullid,
        'like_type': types[item.hdfulltype],
        'vote': item.hdfullstatus
    }

    httptools.downloadpage(host + "/a/favorite", post=post)
    platformtools.itemlist_refresh()


def status_watched(state, type, id):
    logger.trace()
    col = state.get('status', {}).get(type, {})
    if not isinstance(col, dict):
        col = dict()

    return int(col.get(id, 0))


def play(item):
    logger.trace()
    # TODO: Marcar como vista en HDFull
    return item


def obfs(data, key, n=126):
    chars = list(data)
    for i in range(0, len(chars)):
        c = ord(chars[i])
        if c <= n:
            number = (ord(chars[i]) + key) % n
            chars[i] = chr(number)

    return "".join(chars)


class Decoder:
    def __init__(self):
        self.witdh = '920'
        self.height = '360'
        self.code = httptools.downloadpage(host + '/js/providers.js').data
        self.code = re.sub(r'\\x([0-F]+)', lambda x: chr(int(x.group(1), 16)), self.code)
        self.varname, values, self.code = re.compile('var (_0x[0-f]+)=(\[.*?\]);(.*)').findall(self.code)[0]
        self.values = eval(values)
        self.code = re.sub('%s\[([\d]+)\]' % self.varname, lambda x: repr(self.values[int(x.group(1))]), self.code)
        self.result = {}
        self.compose()

    def compose(self):
        result = {}

        for code, prov in re.compile("p\[(\d+)\]\s*=\s*{(.*?)};").findall(self.code):
            t = re.compile('"t":([^,]+)').findall(prov)[0]
            link = re.compile('"l":function.*?return \'(.*?)\'').findall(prov)[0] + '%s'
            result[str(eval(code))] = {
                'stream': True if t == "'s'" else False,
                'link': link
            }

        self.result = result

    def get(self, index, video_id):
        import copy
        value = copy.deepcopy(self.result[index])
        value['link'] = value['link'] % video_id
        return value
