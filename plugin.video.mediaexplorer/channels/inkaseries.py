# -*- coding: utf-8 -*-
from core.libs import *

LNG = Languages({
    Languages.es: ['castellano', 'español'],
    Languages.la: ['latino'],
    Languages.vos: ['subtitulado', 'subtitulada']
})

QLT = Qualities({
    Qualities.hd: ['HD Real 720', 'HD', 'BluRay', 'HD Real 720p'],
    Qualities.rip: ['Dvd Rip', 'HDRip', 'bdrip', 'Dvdrip', 'HD Rip 480p', 'HD Rip 320', 'HD Rip'],

    Qualities.sd: ['dvdfull', 'SD'],
    Qualities.hd_full: ['hdfull', 'hd1080', 'FULLHD', 'Full HD 1080p', 'Full HD 1080'],
    Qualities.scr: ['screener', 'TSHQ', 'Cam', 'Dvdq', 'Ts Screener hq', 'DVDScreener']
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
    HOST = 'https://www.inkapelis.com'

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
    HOST = 'https://www.inkaseries.net'

    itemlist.append(item.clone(
        action="tvshows",
        label="Nuevas series",
        url=HOST + "/ultimas-series-agregadas/",
        type="item",
        group=True,
        content_type='tvshows'
    ))

    itemlist.append(item.clone(
        action="newest_episodes",
        label="Episodios de estreno",
        url=HOST + '/ultimos-capitulos-agregados/',
        type="item",
        group=True,
        content_type='episodes'
    ))

    itemlist.append(item.clone(
        action="tvshows",
        label="Series más vistas",
        url=HOST + "/categoria/series-mas-vistas/",
        type="item",
        group=True,
        content_type='tvshows'
    ))

    itemlist.append(item.clone(
        action="tvshows",
        label="Temporadas actualizadas",
        url=HOST + '/ultimas-temporadas-agregadas/',
        type="item",
        group=True,
        content_type='seasons'
    ))

    # "Series por género"
    itemlist.append(item.clone(
        action="generos",
        label="Géneros",
        url=HOST,
        group=True,
        type="item"
    ))

    # "Buscar"
    itemlist.append(item.clone(
        action="search",
        label="Buscar",
        query=True,
        type='search',
        group=True,
        category='tvshow',
        content_type='tvshows'
    ))

    return itemlist

def generos(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data

    if item.category == 'movie':
        patron = '<li class="cat-item cat-item-\d+"><a href="([^"]+)[^>]+>([^<]+)<b>([^<]+)'

        for url, label, num in scrapertools.find_multiple_matches(data, patron):
            label = label.replace('Películas para Niños', 'Infantiles').strip()
            if label in ['Actualizadas', 'Cartelera', 'Uncategorized', 'Destacadas', 'Estrenos', 'Foreign',
                         'Próximos Estrenos', 'Suspenso'] or len(num)<2:
                continue

            itemlist.append(item.clone(
                action="movies",
                label="%s (%s)" %(label, num),
                type="item",
                content_type='movies',
                url=url
            ))
    else:
        patron = '<li><a href="([^"]+)"><span class="glyphicon glyphicon-expand" aria-hidden="true">' \
                 '<\/span> <i>([^<]+)<\/i> <b>(\d+)'
        for url, label, num in scrapertools.find_multiple_matches(data, patron):
            if label in ['Destacadas', 'Recomendadas', 'Series más vistas', 'Soap', 'Uncategorized'] \
                    or int(num.replace('.', '')) < 11:
                continue

            itemlist.append(item.clone(
                action="tvshows",
                label="%s (%s)" % (label, num),
                type="item",
                content_type='tvshows',
                url=url
            ))

    return sorted(itemlist, key=lambda i: i.label)


def search(item):
    logger.trace()
    if item.content_type == 'movies':
        item.url = "https://www.inkapelis.com/?s=%s" % item.query.replace(" ", "+")
        return movies(item)
    else:
        item.url = "https://www.inkaseries.net/?s=%s" % item.query.replace(" ", "+")
        return tvshows(item)


def movies(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    data2 = scrapertools.find_single_match(data,'<div class="showpost4 posthome">(.*?)<div class="clear"></div>')
    patron = '<div class="poster-media-card ([^"]+)"><a href="([^"]+)" title="([^"]+)".*?<div class="poster">(.*?)' \
             '<div class="poster-image-container">.*?src="([^"]+)"'

    for calidad, url, title, langs, poster in scrapertools.find_multiple_matches(data2, patron):
        langs = scrapertools.find_multiple_matches(re.sub(r'<div class="idiomes', '', langs), '<div class="([^"]+)">')
        itemlist.append(item.clone(
            action='findvideos',
            title=title,
            url=url,
            poster=poster,
            quality=list({QLT.get(q.split()[0]) for q in calidad.split(',')}),
            lang=[LNG.get(l.lower().split()[0]) for l in langs if l != ' '],
            type='movie',
            content_type='servers'
        ))

    # Si es necesario añadir paginacion
    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)"\s?><i class="glyphicon glyphicon-chevron-right"')
    if next_page and itemlist:
        itemlist.append(item.clone(
            url=next_page,
            type='next'
        ))

    return itemlist


def tvshows(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<div class="col-md-80 lado2"><div class="list_f"><div class="tiulo-c">(.*?)</div><div class="clear">'

    data = scrapertools.find_single_match(data, patron)
    patron = '<a class="poster" href="([^"]+)" title="([^"]+)">.*?src="([^"]+).*?<span class="generos?">([^<]*)'

    for url, title, poster, extra in scrapertools.find_multiple_matches(data, patron):
        if '/ultimas-temporadas-agregadas/' in item.url:
            url, season = scrapertools.find_single_match(url, '(.*?)\/temporada-(\d+)')

            new_item = item.clone(
                action='episodes',
                label=extra,
                tvshowtitle=extra,
                title=extra,
                url=url,
                season=int(season),
                poster=poster,
                type='season',
                content_type='episodes')

        else:
            new_item = item.clone(
                action='seasons',
                label=title,
                tvshowtitle=title,
                title=title,
                url=url,
                poster=poster,
                type='tvshow',
                content_type='seasons')

        itemlist.append(new_item)

    # Si es necesario añadir paginacion
    next_page = scrapertools.find_single_match(data, '<div class="pagination ">.*?class="last".*?<a href="([^"]+)')
    if next_page and itemlist:
        itemlist.append(item.clone(
            url=next_page,
            type='next'
        ))

    return itemlist


def seasons(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    patron = '<li class="larr fSeason season season-(.*?)<li class="episode episode-'

    for season in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            action="episodes",
            season=int(scrapertools.find_single_match(season, "Temporada (\d+)")),
            type='season',
            content_type='episodes'
        ))

    return itemlist


def episodes(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<div class="episode-guide">(.*?)<div class="col-md-4 padl0">'

    data = scrapertools.find_single_match(data, patron)
    patron = '<tr><td><a href="([^"]+)" title="([^"]+)".*?<td>(.*?)</td></tr>'

    for url, episode, langs in scrapertools.find_multiple_matches(data, patron):
        num_season, num_episode = scrapertools.get_season_and_episode(episode.replace(',',''))

        if num_season and num_season == item.season:
            itemlist.append(item.clone(
                title=item.tvshowtitle,
                url= url,
                action="findvideos",
                episode=num_episode,
                season=num_season,
                lang=[LNG.get(l.lower()) for l in scrapertools.find_multiple_matches(langs, 'title="([^"]+)"')],
                type='episode',
                content_type='servers'
            ))

    return itemlist


def newest_episodes(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<div class="col-md-80 lado2"><div class="list_f"><div class="tiulo-c">(.*?)</div><div class="clear">'

    data = scrapertools.find_single_match(data, patron)
    patron = '<img src="([^"]*).*?<span class="genero">([^<]*)</span><h3 class="name"><a href="([^"]+)[^>]+>([^<]+)'

    for thumb, episode, url, title  in scrapertools.find_multiple_matches(data, patron):
        num_season, num_episode = scrapertools.get_season_and_episode(episode.replace('-', ''))

        new_item = item.clone(
            label=title,
            tvshowtitle=title,
            url= url,
            action="findvideos",
            episode=num_episode,
            season=num_season,
            type='episode',
            content_type='servers')

        if thumb:
            new_item.thumb = thumb.strip().replace("w185", "original")

        itemlist.append(new_item)

    return itemlist


def findvideos(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    if item.category == 'tvshows':
        for tipo in ['online', 'descarga']:
            data2 = scrapertools.find_single_match(data, '<div id="%s".*?<tbody>(.*?)</tbody>' % tipo)
            patron = '<tr><td><a href="([^"]+).*?<td>.+?<td>([^<]+)</td><td>([^<]+)</td>'
            for url, lang, qlt in scrapertools.find_multiple_matches(data2, patron):
                itemlist.append(item.clone(
                    url=url,
                    action='play',
                    type='server',
                    lang=LNG.get(lang.lower()),
                    quality=QLT.get(qlt),
                    stream=(tipo == 'online')
                ))
    else:
        for tipo in ['olmt', 'dlnmt']:
            data2 = scrapertools.find_single_match(data,
                                            '<div class="table-responsive dlmt" id="%s".*?<tbody>(.*?)</tbody>' % tipo)
            patron = '<tr><td><a href="([^"]+).*?<td>.+?<td>([^<]+)</td><td>([^<]+)</td>'
            for url, lang, qlt in scrapertools.find_multiple_matches(data2, patron):
                itemlist.append(item.clone(
                    url=url,
                    action='play',
                    type='server',
                    lang=LNG.get(lang.lower()),
                    quality=QLT.get(qlt),
                    stream=(tipo == 'olmt')
                ))

    return servertools.get_servers_itemlist(itemlist)
