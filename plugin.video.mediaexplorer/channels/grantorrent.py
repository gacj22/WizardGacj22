# -*- coding: utf-8 -*-
from core.libs import *

HOST = 'https://grantorrent.net/'

LNG = Languages({
    Languages.es: ['espaniol']
})

QLT = Qualities({
    Qualities.rip: ['br-line', 'dvdrip', 'hdrip'],
    Qualities.uhd: ['4k', '4k hdr'],
    Qualities.m3d: ['3d'],
    Qualities.hd_full: ['bdremux-1080p', 'bluray-1080p', 'microhd-1080p', 'hd 1080p'],
    Qualities.hd: ['hd 720p', 'bluray-720p'],
    Qualities.scr: ['br-screener', 'screener']
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

    itemlist.append(item.clone(
            action="config",
            label="Configuración",
            folder=False,
            category='all',
            type='setting'
        ))

    return itemlist


def config(item):
    platformtools.show_settings(item=item)


def menupeliculas(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        action="movies",
        label="Novedades",
        url=HOST,
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
        action="newest_episodes",
        label="Nuevos episodios",
        url=HOST + '/series/',
        type="item",
        group=True,
        content_type='tvshows',
        banner='banner/episode.png',
        icon='icon/episode.png',
        poster='poster/episode.png'
    ))

    itemlist.append(item.clone(
        action="generos",
        label="Géneros",
        url=HOST + '/series/',
        type="item",
        group=True
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

def generos(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url, use_proxy= settings.get_setting('use_proxy', __file__)).data
    patron = '<a href="([^"]+)"><li class="categorias">([^<]+)'

    for url, genre in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            action='movies_2' if item.category =='movie' else 'tvshows',
            label=genre,
            url=url,
            content_type='movies' if item.category =='movie' else 'tvshows'
        ))

    return itemlist


def movies(item):
    logger.trace()
    itemlist = list()
    aux = {}
    i = 0

    if not item.url:
        item.url = HOST

    data = httptools.downloadpage(item.url, use_proxy= settings.get_setting('use_proxy', __file__)).data

    patron = '<div class="imagen-post"> <a href="([^"]+)"><img src="([^"]+)".*?<div class="bloque-superior"> ' \
             '([^<]+)<div class="imagen-idioma"> <img src=".*?/icono_([^\.]+).*?' \
             '<div class="bloque-inferior">(.*?)</div>'

    for url, poster, qlt, lang, title in scrapertools.find_multiple_matches(data, patron):
        title = re.sub('<.*?>', '', title.strip())

        # Eliminar duplicados dentro de la misma pagina
        # Pre: las diferentes opciones tienen el mismo idioma y la misma url
        if title not in aux:
            aux[title] = {'title':title,
                          'url':url,
                          'poster':poster,
                          'lang':[LNG.get(lang)],
                          'qlt': QLT.get(qlt.lower()),
                          'i':i}
            i += 1

        elif  QLT.get(qlt.lower()).level > aux[title]['qlt'].level:
            # Encontrado con mejor calidad
            aux[title]['qlt']= QLT.get(qlt.lower())


    for v in sorted(aux.values(), key=lambda x:x['i']):
        itemlist.append(item.clone(
            action= 'findvideos',
            title= v['title'],
            url= v['url'],
            poster= v['poster'],
            type='movie',
            content_type= 'servers',
            quality= v['qlt'],
            lang= v['lang']
        ))

    next_page = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)">Siguiente</a>')
    if itemlist and next_page:
        itemlist.append(item.clone(
            url=next_page,
            type='next'))

    return itemlist


def movies_2(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url, use_proxy= settings.get_setting('use_proxy', __file__)).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<div class="imagen-post">\s?<a href="([^"]+)"><img src="([^"]+)".*?<div class="bloque-inferior">(.*?)</div>'

    for url, poster, title in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            action= 'findvideos',
            title= title.strip(),
            url= url,
            poster= poster,
            type='movie',
            content_type= 'servers'
        ))

    next_page = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)">Siguiente</a>')
    if itemlist and next_page:
        itemlist.append(item.clone(
            url=next_page,
            type='next'))

    return itemlist


def tvshows(item):
    logger.trace()
    itemlist = list()
    aux = []

    data = httptools.downloadpage(item.url, use_proxy= settings.get_setting('use_proxy', __file__)).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<div class="imagen-post"><a href="[^"]+"><img src="([^"]+)".*?<div class="bloque-inferior">([^<]+)</div>'

    for poster, title in scrapertools.find_multiple_matches(data, patron):
        if not "Temporada" in title:
            continue

        title = title.split(" Temporada")[0][:-3].strip()
        # Agrupar por series
        if title not in aux:
            aux.append(title)
            itemlist.append(item.clone(
                action='seasons',
                tvshowtitle=title,
                title=title,
                extra=title,
                url=HOST + '/series/?s=%s' % title.replace(" ", "+").replace( "’", "%27"),
                poster=poster,
                type='tvshow',
                content_type='seasons'))

    next_page = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)">Siguiente</a>')
    if itemlist and next_page:
        itemlist.append(item.clone(
            url=next_page.replace('/series/series/', '/series/'),
            type='next'))

    return itemlist


def newest_episodes(item):
    logger.trace()
    itemlist = list()

    if not item.url:
        item.url = HOST + '/series/'

    data = httptools.downloadpage(item.url, use_proxy= settings.get_setting('use_proxy', __file__)).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<div class="imagen-post"><a href="([^"]+)"><img src="([^"]+)".*?<div class="bloque-superior">([^<]+)' \
             '<div class="imagen-idioma"><img src=".*?/icono_([^\.]+).*?<div class="bloque-inferior">' \
             '([^<]+)<br>([^<]+)</div>'

    for url, poster, qlt, lang, tvshowtitle, season_episode in scrapertools.find_multiple_matches(data, patron):
        # Obtenemos numero de temporada
        try:
            num_season = re.findall('(^\d+)',season_episode.strip())[0]
        except:
            # Numero de temporada no encontrada, saltamos esta entrada
            continue

        # Obtenemos los numeros de episodios
        num_episode = scrapertools.find_multiple_matches(season_episode[len(num_season):], "(\d+)")
        num_episode = [int(n) for n in num_episode]

        new_item = item.clone(
            tvshowtitle=tvshowtitle.strip(),
            label=tvshowtitle.strip(),
            poster=poster,
            url=url,
            action="findvideos",
            episode=num_episode[0],
            season=int(num_season),
            type='episode',
            content_type='servers')

        if len(num_episode) > 1:
            # Multiepisodios
            new_item.multi_episodes = range(num_episode[0], num_episode[1] + 1)
            new_item.action = 'episodes'

        itemlist.append(new_item)


    next_page = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)">Siguiente</a>')
    if itemlist and next_page:
        itemlist.append(item.clone(
            url=next_page,
            type='next'))

    return itemlist


def seasons(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url, use_proxy= settings.get_setting('use_proxy', __file__)).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<div class="imagen-post"><a href="([^"]+)".*?<div class="bloque-inferior">(.*?)</div>'

    for url, title in scrapertools.find_multiple_matches(data, patron):
        if not "Temporada" in title:
            continue

        title, season = title.split(" Temporada ")
        if title[:-4] == item.extra:
            itemlist.append(item.clone(
                url=url,
                action="episodes",
                season=int(season),
                type='season',
                content_type='episodes'
            ))


    return sorted(itemlist, key=lambda i: i.season)


def episodes(item):
    logger.trace()
    itemlist = list()
    aux = {}

    data = httptools.downloadpage(item.url, use_proxy= settings.get_setting('use_proxy', __file__)).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<div id="London" class="tabcontent active"><p>([^<]+).*?' \
             '<tbody>(.*?)</tbody>'
    plot, tbody = scrapertools.find_single_match(data, patron)

    patron = '<img src="https://grantorrent.net/wp-content/uploads/2016/09/icono_([^\.]+).*?' \
             '<td>%s([^<]+)</td><td>([^<]+)</td><td>' % item.season

    for lang, episode, qlt in scrapertools.find_multiple_matches(data, patron):
        episode = [int(n) for n in scrapertools.find_multiple_matches(episode, "(\d+)")]
        if len(episode) > 1:
            episode = range(episode[0], episode[1] + 1)

        for num_episode in episode:
            # Agrupamos por episodio
            if num_episode not in aux:
                aux[num_episode] = {'episode':num_episode,
                                'plot': plot,
                                'qlt': [qlt],
                                'lang':[lang]}
            else:
                if qlt not in aux[num_episode]['qlt']:
                    aux[num_episode]['qlt'].append(qlt)
                if lang not in aux[num_episode]['lang']:
                    aux[num_episode]['lang'].append(qlt)

    if aux:
        # Si hay episodios en el listado ...
        if item.multi_episodes:
            # Filtramos por episodios
            aux = dict((k,aux[k]) for k in item.multi_episodes)
            item.multi_episodes = []

        for v in sorted(aux.values(), key=lambda x:x['episode']):
            itemlist.append(item.clone(
                plot=item.plot or plot,
                action="findvideos",
                type='episode',
                content_type='servers',
                episode=v['episode'],
                lang=[LNG.get(l) for l in v['lang']],
                quality=[QLT.get(q.lower()) for q in v['qlt']]
            ))

    else:
        # Si no hay episodios suelto: buscamos temporadas completas
        item.thumb = item.poster
        patron = '<img src="https://grantorrent.net/wp-content/uploads/2016/09/icono_([^\.]+).*?' \
                 '<td>Temporada %s Completa</td><td>([^<]+)</td><td><a class="link" href="([^"]+)' % item.season

        for lang, qlt, url in scrapertools.find_multiple_matches(data, patron):
            itemlist.append(item.clone(
                group=True,
                plot=item.plot or plot,
                url=url,
                action='play',
                type='server',
                server='torrent',
                lang=LNG.get(lang),
                quality= QLT.get(qlt.lower())
            ))

        if itemlist:
            itemlist.insert(0, item.clone(type='label', label="Temporada %s Completa" % item.season))
            itemlist = servertools.get_servers_from_id(itemlist)

    return itemlist


def tv_search(item):
    logger.trace()

    if not item.url:
        item.url = HOST + '/series/?s=%s' % item.query.replace(" ", "+")

    return tvshows(item)


def movie_search(item):
    logger.trace()

    if not item.url:
        item.url =  HOST + '/?s=%s' % item.query.replace(" ", "+")

    return movies_2(item)


def findvideos(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url, use_proxy= settings.get_setting('use_proxy', __file__)).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    if not data or '<title>Página no encontrada' in data:
        logger.debug("Pagina no encontrada: " + item.url)
        return itemlist

    patron = '<div id="London" class="tabcontent active"><p>([^<]+).*?' \
             '<tbody>(.*?)</tbody>'
    plot, tbody= scrapertools.find_single_match(data, patron)

    if item.type == 'movie':
        patron = '<img src="https://grantorrent.net/wp-content/uploads/2016/09/icono_([^\.]+).*?' \
                 '<td>([^<]+)</td><td>([^<]+)<.*?href="([^"]+)'
        for lang, qlt, size, url in scrapertools.find_multiple_matches(tbody, patron):
            n = float(scrapertools.find_single_match(size, '(\d[.\d]*)')) * 1024

            itemlist.append(item.clone(
                plot=item.plot or plot,
                url=url,
                action='play',
                type='server',
                server='torrent',
                lang=LNG.get(lang),
                quality= QLT.get(qlt.lower()),
                size= n * 1024 if 'Gb' in size else n
            ))

    elif item.type == 'episode':
        patron = '<img src="https://grantorrent.net/wp-content/uploads/2016/09/icono_([^\.]+).*?' \
                 '<td>%s([^<]+)</td><td>([^<]+)</td><td><a class="link" href="([^"]+)' % item.season

        for lang, episode, qlt, url in scrapertools.find_multiple_matches(tbody, patron):
            episode = [int(n) for n in scrapertools.find_multiple_matches(episode, "(\d+)")]
            if len(episode) > 1:
                episode = range(episode[0], episode[1] + 1)

            if item.episode in episode:
                itemlist.append(item.clone(
                    plot=item.plot or plot,
                    url=url,
                    action='play',
                    type='server',
                    server='torrent',
                    lang=LNG.get(lang),
                    quality= QLT.get(qlt.lower())
                ))

    return servertools.get_servers_from_id(itemlist)


