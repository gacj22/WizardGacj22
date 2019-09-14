# -*- coding: utf-8 -*-
from core.libs import *

M_HOST = 'http://gnula.nu'
T_HOST = 'https://gnula.se'

LNG = Languages({
    Languages.es: ['vc', 'castellano', 'es'],
    Languages.la: ['vl', 'latino', 'la'],
    Languages.vos: ['vs', 'vose'],
    Languages.en: ['en']
})

QLT = Qualities({
    Qualities.scr: ['ts', 'tc-hq', 'ts-hq', 'br-s', 'dvd-s', 'cam', 'web-s'],
    Qualities.hd: ['hd-r', 'hd-tv', 'hdtv', 'micro-hd-720p'],
    Qualities.hd_full: ['micro-hd-1080p', 'br-r'],
    Qualities.rip: ['dvd-r']
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

    from core import anticaptcha
    if not anticaptcha.add_item(itemlist):
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
        action="newest",
        label="Novedades",
        url=M_HOST,
        type="item",
        group=True,
        content_type='movies'))

    itemlist.append(item.clone(
        action="movies",
        label="Estrenos",
        url=M_HOST + "/peliculas-de-estreno/lista-de-peliculas-online-parte-1/",
        type="item",
        group=True,
        content_type='movies'))

    itemlist.append(item.clone(
        action="movies",
        label="Recomendadas",
        url=M_HOST + "/peliculas-online/lista-de-peliculas-recomendadas/",
        type="item",
        group=True,
        content_type='movies'))

    itemlist.append(item.clone(
        action="generos",
        label="Géneros",
        url=M_HOST + "/generos/lista-de-generos/",
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


def movie_search(item):
    logger.trace()
    itemlist = list()
    data = httptools.downloadpage('https://cse.google.es/cse.js?sa=G&hpg=1&cx=014793692610101313036:vwtjajbclpq').data
    cse_token = scrapertools.find_single_match(data, '"cse_token": "([^"]+)')

    if not item.url:
        item.url = 'https://cse.google.com/cse/element/v1?' \
                   'rsz=filtered_cse' \
                   '&num=20&' \
                   'hl=es&' \
                   'source=gcsc&' \
                   'gss=.es&' \
                   'cx=014793692610101313036:vwtjajbclpq&' \
                   'q=%s&' \
                   'safe=off&cse_tok=%s&' \
                   'exp=csqr,4231019&callback=google.search.cse.api15976' \
                   '&start=0' % (item.query, cse_token)

    data = httptools.downloadpage(item.url, no_decode=True).data
    data = jsontools.load_json(scrapertools.find_single_match(data,"google.search.cse.api15976\((.*?)\);"))

    for result in data['results']:
        if not result['titleNoFormatting'].startswith('Ver'):
            continue
        try:
            title, year = scrapertools.find_single_match(result['titleNoFormatting'], 'Ver (.*?)(?: \((\d{4})\))? online')
            itemlist.append(item.clone(
                title=title,
                url=result['clicktrackUrl'].split('url?q=')[1].split('&')[0],
                type='movie',
                poster=httptools.get_cloudflare_headers(result['richSnippet']['cseImage']['src']),
                content_type='servers',
                action='findvideos',
                year=year
            ))
        except:
            continue

    # Paginador
    next_url = re.sub(r'(start=)(\d+)', lambda m: '%s%s' % (m.group(1), int(m.group(2)) + 20), item.url)
    if next_url and itemlist:
        itemlist.append(item.clone(url=next_url, type='next'))

    return itemlist


def generos(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url,use_proxy= settings.get_setting('use_proxy', __file__)).data

    patron = '<strong>([^<]+)</strong> \[<a href="([^"]+/generos/lista-de-peliculas-del-genero-[^/]+/)"'

    for genre, url in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            action='movies',
            label=genre,
            url=url,
            content_type='movies'
        ))

    return sorted(itemlist, key=lambda i: i.label)


def newest(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url or M_HOST, use_proxy= settings.get_setting('use_proxy', __file__)).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    data = scrapertools.find_single_match(data,
            '<strong>NOVEDADES DE PELÍCULAS</strong>(.*?)<div class="widget-content">')

    patron = '<a href="([^"]+)"><img alt="[^"]+" title="(.*?) \((\d{4})\) \[(.*?)\] \[(.*?)\][^"]+" src="([^"]+)" ' \
             'width="98" height="140"'

    for url, title, year, lng, qlt, poster in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            title=title.split('(')[0].strip(),
            url=url,
            poster=httptools.get_cloudflare_headers(poster),
            type='movie',
            content_type='servers',
            action='findvideos',
            year=year,
            quality=QLT.get(qlt.lower()),
            lang=[LNG.get(l.lower().strip().split(' ')[0]) for l in lng.split(',')]
        ))


    return itemlist


def movies(item):
    logger.trace()
    itemlist = list()

    if not item.index:
        item.index = 0
    #item.url = M_HOST + '/peliculas-online/lista-de-peliculas-online-parte-1/'
    data = httptools.downloadpage(item.url,use_proxy= settings.get_setting('use_proxy', __file__)).data
    #logger.debug(data)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)


    patron = '<a class="Ntooltip" href="([^"]+)">([^"]+)<span><br /><img src="([^"]+)"></span></a>' \
             '\s+(?:\((\d{4})\)\s+)?\[<span style="color: #33ccff;">[^<]+</span>(.*?)' \
             '\[<span style="color: #ffcc99;">([^<]+)</span>\]'

    results = scrapertools.find_multiple_matches(data, patron)

    for url, title, poster, year, langs, qlt in results[item.index:item.index + 40]:
        itemlist.append(item.clone(
            title=title,
            url=url,
            poster=httptools.get_cloudflare_headers(poster),
            type='movie',
            content_type='servers',
            action='findvideos',
            quality=QLT.get(qlt.lower()),
            lang=[LNG.get(l.lower()) for l in scrapertools.find_multiple_matches(langs, '\(([^)]+)\)')],
            year=year
        ))

    # Paginador
    if len(results[item.index + 40:]):
        itemlist.append(item.clone(type='next', index=item.index + 40))
    else:
        current_page = scrapertools.find_single_match(data, '\(parte (\d+)\)</span>: Parte \[')
        if current_page:
            next_url = scrapertools.find_single_match(
                data,
                'Parte.*?\[<a href="([^"]+)">%s</a>\]</p>' % (int(current_page) + 1)
            )
            if next_url:
                itemlist.append(item.clone(url=next_url, type='next'))

    return itemlist



# Seccion Series
def generos_tvshow(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url,use_proxy= settings.get_setting('use_proxy', __file__)).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<li>\s?<h3> <a href="([^"]+)">([^<]+)</a> </h3><p>(\d+)</p></li>'

    for url, genre, cant in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            action='tvshows_genre',
            label='%s (%s)' % (genre, cant),
            url=T_HOST + url,
            content_type='tvshows'
        ))

    return sorted(itemlist, key=lambda i: i.label)

def tv_search(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(
        T_HOST + '/buscar/serie/',
        post={
            'key': item.query,
            'keyword': 'title',
            'genre': ''
        },
        use_proxy = True
    ).data

    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<li class="nth-child1n"><figure>\s?<a href="([^"]+)" title="([^"]+)"><img src="([^"]+)" alt="" /></a>' \
             '<figcaption>[^<]+</figcaption>\s?</figure><aside>\s?<h2><a href="[^"]+" title="[^"]+">[^"]+</a></h2>'

    for url, title, poster in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            title=title,
            url=T_HOST + url,
            poster=httptools.get_cloudflare_headers(poster),
            action="seasons",
            type='tvshow',
            content_type='seasons'
        ))

    return itemlist


def menuseries(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        action="abc",
        label="ABC",
        url=T_HOST,
        type="item",
        group=True,
        content_type='items'
    ))

    itemlist.append(item.clone(
        action="newest_episodes",
        label="Nuevos episodios",
        url=T_HOST + '/inc/index.php?bloque=1&idioma=all&page=1',
        type="item",
        group=True,
        content_type='episodes'
    ))

    itemlist.append(item.clone(
        action="generos_tvshow",
        label="Géneros",
        type="item",
        group=True,
        url=T_HOST + '/lista-de-generos/'
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



def abc(item):
    logger.trace()
    itemlist = list()

    for letra in '0ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        if letra == '0':
            letra = '0-9'
        itemlist.append(item.clone(
            title=letra,
            action='tvshows',
            url=T_HOST + '/lista-de-series/%s' % letra,
            type='item',
            content_type='tvshows'
        ))

    return itemlist


def tvshows_genre(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url,use_proxy= settings.get_setting('use_proxy', __file__)).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<li class="[^"]+"><figure><a title="[^"]+" href="([^"]+)"><img class="thumb" src="([^"]+)" ' \
             'alt="[^"]+" /><figcaption>[^<]+</figcaption></a></figure><h3> <a title="[^"]+" href="[^"]+">' \
             '([^"]+)</a> </h3> <p class="date">(\d{4}) \| [^<]+</p><p class="excerpt">([^<]+)</p><p class="generos">' \
             '.*?</p></li>'

    for url, poster, title, year, plot in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            title=title.strip(),
            url=T_HOST + url.replace('/ficha/', '/capitulos/'),
            poster=httptools.get_cloudflare_headers(poster),
            action="seasons",
            type='tvshow',
            content_type='seasons',
            year=year,
            plot=plot
        ))

    # Paginador
    next_url = scrapertools.find_single_match(data, '<a href="([^"]+)">></a>')
    if next_url:
        itemlist.append(item.clone(url=T_HOST + next_url, type='next'))

    return itemlist


def tvshows(item):
    logger.trace()
    itemlist = list()

    if not item.index:
        item.index = 0

    data = httptools.downloadpage(item.url,use_proxy= settings.get_setting('use_proxy', __file__)).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    data = scrapertools.find_single_match(
        data,
        '<ul id="list-container" class="dictionary-list">(.*?)<div class="paginator"></div>'
    )

    patron = '<li> <a href="([^"]+)" title="(.*?)(?: \((\d{4})\))?">[^>]+</a> </li>'

    results = scrapertools.find_multiple_matches(data, patron)

    for url, title, year in results[item.index:item.index + 40]:
        itemlist.append(item.clone(
            title=title,
            year=year,
            url=T_HOST + url,
            action="seasons",
            type='tvshow',
            content_type='seasons'
        ))

    # Paginador
    if len(results[item.index + 40:]):
        itemlist.append(item.clone(type='next', index=item.index + 40))

    return itemlist


def seasons(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url,use_proxy= settings.get_setting('use_proxy', __file__)).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<strong class="season_title">Temporada (\d+)</strong> <span class="accordion-status">'

    poster = scrapertools.find_single_match(data, '<meta property="og:image" content="([^"]+)" />')

    for num_season in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            season=int(num_season),
            title="Temporada %s" % num_season,
            year="",
            poster=httptools.get_cloudflare_headers(poster),
            action="episodes",
            type='season',
            content_type='episodes'
        ))

    return itemlist


def episodes(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url,use_proxy= settings.get_setting('use_proxy', __file__)).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<tr><td class="episode-title"> <span class="downloads allkind" title="[^"]+"></span> ' \
             '<a target="_blank" href="([^"]+)"> <strong>(\d+)x(\d+) </strong> - ([^<]+) </a> </td><td>[^<]+' \
             '</td><td class="episode-lang" style="text-align: center;">(.*?)</td><td class="score">'

    poster = scrapertools.find_single_match(data, '<meta property="og:image" content="([^"]+)" />')

    for url, season, episode, title, langs in scrapertools.find_multiple_matches(data, patron):
        if item.season != int(season):
            continue

        itemlist.append(item.clone(
            title=title,
            action="findvideos",
            url=url,
            poster=httptools.get_cloudflare_headers(poster),
            episode=int(episode),
            type='episode',
            content_type='servers',
            lang=[LNG.get(l.lower()) for l in scrapertools.find_multiple_matches(langs, '/img/lng/([^.]+)\.png')]
        ))

    return itemlist


def newest_episodes(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url or T_HOST + '/inc/index.php?bloque=1&idioma=all&page=1',use_proxy= settings.get_setting('use_proxy', __file__)).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<td><a href="([^"]+)"><img width="105px" height="151px" src="([^"]+)" ' \
             'title="([^"]+)" alt="[^"]+"></img></a></td>'

    for url, thumb, title in scrapertools.find_multiple_matches(data, patron):
        season, episode = url.split('/')[-3:-1]

        itemlist.append(item.clone(
            tvshowtitle=title,
            label=title,
            label_extra={'sublabel': ' - %s', 'value': 'eval(item.title)'},
            action="findvideos",
            url=url,
            season=int(season),
            episode=int(episode),
            type='episode',
            thumb=httptools.get_cloudflare_headers(thumb),
            content_type='servers'
        ))

    # Paginador
    next_url = re.sub(r'(page=)(\d+)', lambda m: '%s%s' % (m.group(1), int(m.group(2)) + 1), item.url)
    if next_url and itemlist:
        itemlist.append(item.clone(url=next_url, type='next'))

    return itemlist


def findvideos(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url,use_proxy= settings.get_setting('use_proxy', __file__)).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    if item.type == 'episode':
        patron = '<tr class="po"><td class="episode-server" data-value="0"> <a data-id="[^"]+" href="([^"]+)" ' \
                 'target="_blank" rel="nofollow"><img src="[^"]+" height="22" width="22" alt="[^"]+" />([^"]+)</a> ' \
                 '</td><td class="episode-server-img"><img src="https://www.google.com/s2/favicons\?domain=' \
                 '[^"]+" />([^"]+)</td><td class="episode-lang"><img src="https://gnula.se/img/lng/' \
                 '([^.]+)\.png" /> </td>.*?<td class="episode-notes">([^"]+)</td>'
        for url, modo, server, lng, qlt in scrapertools.find_multiple_matches(data, patron):
            itemlist.append(item.clone(
                url=url,
                type='server',
                action='play',
                lang=LNG.get(lng.lower()),
                quality=QLT.get(qlt.lower()),
                server=server.split('.')[0].lower().strip(),
                stream=modo.strip() == 'Reproducir'
            ))

        itemlist = servertools.get_servers_from_id(itemlist)
    else:
        if '<em>opción ' in data:
            patron = '<em>opción \d, ([^,]+), ([^<]+)</em></p>(.*?)<div style="clear:both;">'
            for lng, qlt, enlaces, in scrapertools.find_multiple_matches(data, patron):
                for url in scrapertools.find_multiple_matches(enlaces, '(?:src|href)="(http[^"]+)"'):
                    itemlist.append(item.clone(
                        url=url,
                        type='server',
                        action='play',
                        lang=LNG.get(lng.lower()),
                        quality=QLT.get(qlt.lower())
                    ))
        else:
            patron = '<strong>Ver película online</strong> \[<span style="color: #ff0000;">([^<]+)' \
                     '</span>](.*?)<div style="clear:both;">'
            info, enlaces = scrapertools.find_single_match(data, patron)
            info = info.replace(" ", "").split(',')
            for url in scrapertools.find_multiple_matches(enlaces, '(?:src|href)="(http[^"]+)" (?:target|frameborder)='
                                                                   '"[^"]+"(?! class="broken_link")'):

                itemlist.append(item.clone(
                    url=url,
                    type='server',
                    action='play',
                    lang=LNG.get(info[1].lower()),
                    quality=QLT.get(info[2].lower())
                ))

        itemlist = servertools.get_servers_itemlist(itemlist)

    return itemlist


def play(item):
    logger.trace()
    if not item.url.startswith(T_HOST):
        return

    data = httptools.downloadpage(item.url,use_proxy= settings.get_setting('use_proxy', __file__)).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    site_key = scrapertools.find_single_match(data, '<div class="g-recaptcha" data-sitekey="([^"]+)">')
    result = platformtools.show_recaptcha(item.url, site_key)
    if not result:
        return ResolveError(7)

    post = {
        'g-recaptcha-response': result,
        'submit': 'Reproducir'
    }
    item.url = httptools.downloadpage(item.url, post=post, follow_redirects=False, only_headers=True, use_proxy= settings.get_setting('use_proxy', __file__)).headers.get('location', '')
    if item.url:
        servertools.normalize_url(item)
        return item

    else:
        return ResolveError(6)
