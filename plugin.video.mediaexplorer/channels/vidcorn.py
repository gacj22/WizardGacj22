# -*- coding: utf-8 -*-
from core.libs import *

HOST = 'https://vidcorn.tv'

LNG = Languages({
    Languages.es: ['es'],
    Languages.en: ['en'],
    Languages.la: ['lat'],
    Languages.sub_es: ['sub_es'],
    Languages.sub_en: ['sub_en']
})

QLT = Qualities({
    Qualities.rip: ['RIP'],
    Qualities.hd: ['HD 720'],
    Qualities.hd_full: ['HD 1080'],
    Qualities.scr: ['Screener']
})


def is_logged():
    logger.trace()
    data = httptools.downloadpage(HOST).data
    if scrapertools.find_single_match(data, 'data-user-logged-in="([^"]+)') == 'true':
        return True
    else:
        return False


def login():
    logger.trace()

    if is_logged():
        return True

    if not settings.get_setting('user', __file__) or not settings.get_setting('user', __file__):
        return False

    # Intento Recaptcha Forzado
    result = '03AOLTBLTHVVNy6ihPatokMDF8dZMNPyewMwoftuYbP3w38Mi3pr2LHcF6mWUOlQPPnkgMwbFCo6cNflmhzIqykJirNt9wMxX-AUF4UzejJxMo94ionWP5hwJYWv770Figkn8OnD2D4yZrljTSOOgpOgD1QF-WUgemzCnqStv25i7jQtLzGJNin10MzZUgXy4BjJ5QDJ8fpHB1B_tg0PsZt-YZ4UymRtm3bsAnUx3FX1BLm9xbNvrgqf-RbBy5DOt5B_Gh919DdLKSs2aLMC6jWzHHZxuHShGe_FrdUOUD2s-SeeN7ezcnl-C_qpK7n8AmVFPqdT0PG1Fb'

    post = {'username': settings.get_setting('user', __file__),
            'password': settings.get_setting('password', __file__),
            'g-recaptcha-response': result}
    
    if 'success' in httptools.downloadpage(HOST + '/services/login', post=post).data:
        return True
    else:
        logger.debug("Fallo del Recaptcha Forzado")

    # Recaptcha Anti-Captcha
    data = httptools.downloadpage(HOST).data
    site_key = scrapertools.find_single_match(data, '<div[^>]+ class="g-recaptcha[^"]+" data-sitekey="([^"]+)">')
    #logger.debug(site_key)
    result = platformtools.show_recaptcha(HOST, site_key)

    post = {
        'username': settings.get_setting('user'),
        'password': settings.get_setting('password'),
        'g-recaptcha-response': result}

    if 'success' in httptools.downloadpage(HOST + '/services/login', post=post).data:
        return True
    else:
        return False


def mainlist(item):
    logger.trace()
    itemlist = list()

    # Advertencias
    if not settings.get_setting('user', __file__) or not settings.get_setting('user', __file__):
        itemlist.append(Item(
            label="Es necesario estar registrado en Vidocorn.com e introducir sus datos en la configuración.   ",
            type='user'
        ))

    # from core import anticaptcha
    # anticaptcha.add_item(itemlist)

    # Menu
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
        action="listado",
        label="Actualizadas",
        type="item",
        group=True,
        content_type='movies',
        order_by=8,
        page=0
    ))

    '''itemlist.append(item.clone(
        action="listado",
        label="Añadidas recientemente",
        type="item",
        group=True,
        content_type='movies',
        order_by=4,
        page=0
    ))'''

    itemlist.append(item.clone(
        action="listado",
        label="Mas vistas esta semana",
        type="item",
        group=True,
        content_type='movies',
        order_by=6,
        page=0
    ))

    itemlist.append(item.clone(
        action="generos",
        label="Por género",
        type="item",
        group=True,
        order_by=8,
        url=HOST + '/peliculas'
    ))

    itemlist.append(item.clone(
        action="listado",
        label="Buscar",
        query=True,
        type='search',
        group=True,
        order_by=8,
        page=0,
        content_type='movies'
    ))

    return itemlist


def menuseries(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        action="listado",
        label="Actualizadas",
        type="item",
        group=True,
        content_type='tvshows',
        order_by=8,
        page=0
    ))

    '''itemlist.append(item.clone(
        action="listado",
        label="Añadidas recientemente",
        type="item",
        group=True,
        content_type='tvshows',
        order_by=4,
        page=0
    ))'''

    itemlist.append(item.clone(
        action="listado",
        label="Mas vistas esta semana",
        type="item",
        group=True,
        content_type='tvshows',
        order_by=6,
        page=0
    ))

    itemlist.append(item.clone(
        action="generos",
        label="Por género",
        type="item",
        group=True,
        order_by=8,
        url=HOST + '/series'
    ))

    itemlist.append(item.clone(
        action="listado",
        label="Buscar",
        query=True,
        type='search',
        group=True,
        order_by=8,
        page=0,
        content_type='tvshows'
    ))

    return itemlist


def config(item):
    v = platformtools.show_settings(item=item)
    platformtools.itemlist_refresh()
    return v


def generos(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    patron = '<li data-value="([^"]+)"><a >([^<]+)</a>'

    for value, title in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            label=title,
            filter_by=value,
            content_type='tvshows' if '/series' in item.url else 'movies',
            page=0,
            action='listado'))

    return sorted(itemlist, key=lambda x: x.label)


def listado(item):
    logger.trace()
    itemlist = list()

    data_type = 'peliculas' if item.content_type == 'movies' else 'series'

    if item.movie_gender:
        # Venimos del buscador por generos
        del item.movie_gender
        item.filter_by = item.url

    url = HOST + '/services/fetch_pages'
    post = {
        'page': item.page,
        'data_type': data_type,
        'filter_by': 'all' if not item.filter_by else item.filter_by,
        'order_by': item.order_by,
        'keyword': 0 if not item.query else item.query,
        'optradio': 0
    }

    data = httptools.downloadpage(url, post=post).data
    patron = '(?s)<div data-type="%s" data-item="([^"]+).*?href="([^"]+).*?' % data_type
    patron += 'data-original="([^?]+).*?alt="([^"]+).*?class="year">(\d{4})'

    for id, url, poster, title, year in scrapertools.find_multiple_matches(data, patron):
        new_item = item.clone(
            label=title,
            url=HOST + url,
            poster=poster.replace('small', 'default'),
            vidcornid=id,
            title=title,
            year=year
        )

        if item.content_type == 'movies':
            new_item.action = 'findvideos'
            new_item.type = 'movie'
            new_item.content_type = 'servers'

        else:
            new_item.action = 'seasons'
            new_item.type = 'tvshow'
            new_item.content_type = 'seasons'
            new_item.tvshowtitle = title

        itemlist.append(new_item)

    # Paginacion
    if "$('#load_more_button').show();" in data:
        itemlist.append(item.clone(
            page=int(item.page) + 1,
            type='next'
        ))

    return itemlist


def seasons(item):
    logger.trace()
    itemlist = list()

    url = HOST + '/services/fetch_links'
    post = {
        'movie': item.vidcornid,
        'data_type': 'series'
    }

    data = httptools.downloadpage(url, post=post).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<a class="temporada" data-season="([^"]+)" data-toggle="collapse" data-parent="#accordion" ' \
             'href="#([^"]+).*?<div id="accordion-body" class="panel-body">(.*?)</div> <!-- panel end-->'

    if not is_logged():
        for season, url, body in scrapertools.find_multiple_matches(data, patron):
            # Añadimos la temporadas sin comprobar si hay almenos un episodio con enlaces
            itemlist.append(item.clone(
                label="Temporada %s" % season,
                url=url,
                season=int(season),
                action="episodes",
                type='season',
                content_type='episodes'
            ))

    else:
        for season, url, body in scrapertools.find_multiple_matches(data, patron):
            for enlaces in scrapertools.find_multiple_matches(body,
                                                              '''<small data-toggle="tooltip" title="(\d+) enlaces"'''):
                if int(enlaces) > 0:
                    # Añadimos la temporadas si hay almenos un episodio con enlaces
                    itemlist.append(item.clone(
                        label="Temporada %s" % season,
                        url=url,
                        season=int(season),
                        action="episodes",
                        type='season',
                        content_type='episodes'
                    ))
                    break

    return itemlist


def episodes(item):
    logger.trace()
    itemlist = list()

    url = HOST + '/services/fetch_links'
    post = {
        'movie': item.vidcornid,
        'data_type': 'series'
    }

    data = httptools.downloadpage(url, post=post).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    data = scrapertools.find_single_match(data, '<div id="%s"(.*?)<!-- -capitulos end -->' % item.url)
    patron = '''<div data-episodio="([^"]+)".*?<span class='num_ep'>(\d+).*?<span class='nom_ep'>([^<]+)'''

    if not is_logged():
        for vidcornid, num_episode, title in scrapertools.find_multiple_matches(data, patron):
            # Añadimos el episodio sin verificar si almenos hay un enlace
            itemlist.append(item.clone(
                title=title,
                action="findvideos",
                vidcornid=vidcornid,
                episode=int(num_episode),
                type='episode',
                content_type='servers'
            ))
    else:
        patron += '''.*?<small data-toggle="tooltip" title="(\d+)'''
        for vidcornid, num_episode, title, enlaces in scrapertools.find_multiple_matches(data, patron):
            if int(enlaces) > 0:
                # Añadimos el episodio si almenos hay un enlace
                itemlist.append(item.clone(
                    title=title,
                    action="findvideos",
                    vidcornid=vidcornid,
                    episode=int(num_episode),
                    type='episode',
                    content_type='servers'
                ))

    return itemlist


def findvideos(item):
    logger.trace()
    itemlist = list()

    if not login():
        from core import anticaptcha
        anticaptcha.add_item(itemlist)
        return itemlist

    if item.mediatype == 'episode':
        url = HOST + '/services/fetch_links_from_episode'
        post = {
            'episode': item.vidcornid,
            'filters': 'all-all-all-all-add_date'
        }
        patron2 = '(?s)<a style="display.*?href="([^"]+).*?<span\s*class="link-img"><img alt="([^\.]+).*?class="link-lang">' \
                  '.*?src="/assets/img/flags/flanguage/([^\.]+).*?class="link-sub">(.*?)' \
                  '</img>.*?class="link-quality"><small>([^<]+)'
    else:
        url = HOST + '/services/fetch_links'
        post = {
            'movie': item.vidcornid,
            'filters': 'all-all-all-all-add_date',
            'data_type': 'peliculas'
        }
        patron2 = '(?s)<a style="display.*?href="([^"]+).*?<span class="link-img"><img alt="([^\.]+).*?class="link-lang">' \
                  '<img src="/assets/img/flags/flanguage/([^\.]+).*?class="link-sub">(.*?)' \
                  '</img>.*?class="link-quality">([^<]+)'

    data = httptools.downloadpage(url, post=post).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = ['<div class="link-option-head">(.*?)<div id="descarga">',
              '<div id="descarga">(.*?)</li></a></div>']

    for i, p in enumerate(patron):
        data2 = scrapertools.find_single_match(data, p)
        for url, server, lang, sub, qlt in scrapertools.find_multiple_matches(data2, patron2):
            if sub:
                sub = scrapertools.find_single_match(sub, 'src="/assets/img/flags/fsub/([^\.]+)')
                if lang not in ['es', 'lat'] and sub != 'other':
                    lang = 'sub_' + sub

            itemlist.append(item.clone(
                url=HOST + url,
                action='play',
                server=server.lower(),
                type='server',
                lang=LNG.get(lang),
                quality=QLT.get(qlt),
                stream=(i == 0)
            ))

    itemlist = servertools.get_servers_from_id(itemlist)

    return itemlist


def play(item):
    logger.trace()

    data = httptools.downloadpage(item.url).data
    patron = 'class="btn btn-primary btn-lg" target="_blank" href="([^"]+)'
    url = HOST + scrapertools.find_single_match(data, patron)

    data = httptools.downloadpage(url, follow_redirects=False, only_headers=True)
    item.url = data.headers.get('location', '')
    servertools.normalize_url(item)

    return item
