# -*- coding: utf-8 -*-
from core.libs import *

HOST = 'https://www.seriespapaya.net'

LNG = Languages({
    Languages.es: ['es'],
    Languages.en: ['in'],
    Languages.la: ['lat'],
    Languages.vos: ['sub']
})

QLT = Qualities({
    Qualities.hd_full: ['1080p HD'],
    Qualities.hd: ['720p HD'],
    Qualities.sd: ['360p', '480p']
})

def mainlist(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        action="newest_tvshows",
        label="Nuevas series",
        url=HOST,
        type="item",
        category='tvshow',
        content_type='tvshows'
    ))

    itemlist.append(item.clone(
        action="newest_episodes",
        label="Nuevos episodios",
        url=HOST,
        type="item",
        content_type='episodes'
    ))

    itemlist.append(item.clone(
        action="episodes_estrenos",
        label="Capitulos de estreno en español",
        url=HOST + '/estreno-serie-castellano/',
        type="item",
        lang=LNG.get('es'),
        content_type='episodes'
    ))

    itemlist.append(item.clone(
        action="episodes_estrenos",
        label="Capitulos de estreno en latino",
        url=HOST + '/estreno-serie-espanol-latino/',
        type="item",
        lang=LNG.get('lat'),
        content_type='episodes'
    ))

    itemlist.append(item.clone(
        action="episodes_estrenos",
        label="Capitulos de estreno subtitulados",
        url=HOST + '/estreno-serie-sub-espanol/',
        type="item",
        lang=LNG.get('sub'),
        content_type='episodes'
    ))

    itemlist.append(item.clone(
        action="abc",
        label="Series por orden alfabético",
        url=HOST,
        type="item"
    ))

    # "Buscar"
    itemlist.append(item.clone(
        action="search",
        label="Buscar",
        query=True,
        type='search',
        category='tvshow',
        content_type='tvshows'
    ))

    '''itemlist.append(item.clone(
        action="config",
        label="Configuración",
        folder=False,
        category='all',
        type='setting'
    ))'''

    return itemlist

'''
def config(item):
    platformtools.show_settings(item=item)
'''


def abc(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<li><a title="([^"]+)" href="([^"]+)">([^<]+)'

    for label, url, letra in scrapertools.find_multiple_matches(data, patron):

        itemlist.append(item.clone(
            action="tvshows_abc",
            label=label,
            letra= letra.lower() if letra !='0-9' else 'num',
            group_no=0,
            type="item"
        ))

    return itemlist


def tvshows_abc(item):
    logger.trace()
    itemlist = list()

    url = HOST + "/autoload_process.php"
    post= {
        "group_no": item.group_no,
        "letra": item.letra}

    data = httptools.downloadpage(url, post).data
    patron = '(?s)<img src="([^"]+).*?href="([^"]+)[^>]+>([^<]+).*?(\d{4})'

    for poster, url, title, year in scrapertools.find_multiple_matches(data,patron):
        itemlist.append(item.clone(
            action='seasons',
            label=title,
            tvshowtitle=title,
            title=title,
            year=year,
            url=HOST + '/' + url,
            poster=HOST + '/' + poster,
            type='tvshow',
            content_type='seasons'))

    if item.group_no < 23 and len(itemlist) == 8:
        itemlist.append(item.clone(
            group_no=item.group_no + 1,
            type='next'
        ))

    return itemlist


def newest_tvshows(item):
    logger.trace()
    itemlist = list()

    if not item.url:
        item.url = HOST

    data = httptools.downloadpage(item.url).data
    patron = '<h2>Series Nuevas</h2>(.*?)<div class="clearfix">'

    data = scrapertools.find_single_match(data, patron)
    patron = '<a title="([^"]+).*?href="([^"]+).*?src="([^"]+)'

    for title, url, poster in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            action='seasons',
            label=title,
            tvshowtitle=title,
            title=title,
            url=HOST + '/' + url,
            poster=HOST + '/' + poster,
            type='tvshow',
            content_type='seasons'))

    return itemlist


def newest_episodes(item):
    logger.trace()
    itemlist = list()

    if not item.url:
        item.url = HOST

    data = httptools.downloadpage(item.url).data
    patron = '<h2>Estrenos: Nuevos Capitulos</h2>(.*?)<div class="clearfix">'

    data = scrapertools.find_single_match(data, patron)
    patron = '<a title="([^"]+)" href="([^"]+).*?src="([^"]+)'

    for title, url, poster in scrapertools.find_multiple_matches(data, patron):
        num_season, num_episode = scrapertools.get_season_and_episode(title)
        tvshowtitle=title.split('-')[0].strip()
        itemlist.append(item.clone(
            tvshowtitle=tvshowtitle,
            label=tvshowtitle,
            poster=HOST + '/' + poster,
            url=HOST + '/' + url,
            action="findvideos",
            episode=num_episode,
            season=num_season,
            type='episode',
            content_type='servers'
        ))

    return itemlist


def seasons(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    patron = '<div style="cursor:pointer">.*?Temporada (\d+)'

    for season in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            action="episodes",
            season=int(season),
            type='season',
            content_type='episodes'
        ))

    return itemlist


def episodes(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<a class="visco" href="([^"]+)"><[^>]+([^<]+).*?<div class="ucapaudio">(.*?)</div>'

    for url, season_episode, langs in scrapertools.find_multiple_matches(data, patron):
        num_season, num_episode = scrapertools.get_season_and_episode(season_episode)

        if num_season and num_season == item.season:
            itemlist.append(item.clone(
                title=item.tvshowtitle,
                url= HOST + '/' + url,
                action="findvideos",
                episode=num_episode,
                season=num_season,
                lang=[LNG.get(l) for l in scrapertools.find_multiple_matches(langs, '<img src="images/s-([^.]+)')],
                type='episode',
                content_type='servers'
            ))

    return itemlist


def episodes_estrenos(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = 'onclick="location.href=\'([^\']+).*?background-image: url\(\'([^\']+).*?' \
             '<strong>(\d+)</strong>x<strong>(\d+)</strong>.*?<div style="font-size[^>]+>"([^"]+)'

    for url, poster, season, episode, tvshowtitle in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            label=tvshowtitle,
            tvshowtitle=tvshowtitle,
            url=HOST + '/' + url,
            poster=HOST + '/' + poster,
            action="findvideos",
            episode=int(episode),
            season=int(season),
            type='episode',
            content_type='servers'
        ))

    # Paginacion
    if not item.page:
        item.page = 0
    max = len(itemlist)
    itemlist = itemlist[item.page:item.page + 35]
    if item.page + 35 < max:
        itemlist.append(item.clone(page=item.page + 35, type='next'))

    return itemlist


def findvideos(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<div class="didioma"><img src="images/([^.]+).*?<img src=[^>]+>([^<]+)' \
             '.*?<a href="([^"]+).*?<img src="images/([^.]+).*?<div class="dcalidad">([^<]+)'

    for lang, server, url, tipo, qlt in scrapertools.find_multiple_matches(data, patron):
        lang = LNG.get(lang)
        if item.lang and type(item.lang) != list and item.lang != lang:
            continue

        itemlist.append(item.clone(
            url=HOST + '/' + url,
            server=server.strip().lower(),
            action='play',
            type='server',
            lang=lang,
            quality=QLT.get(qlt),
            stream=(tipo == 'reproducir')
        ))

    return servertools.get_servers_from_id(itemlist)


def play(item):
    logger.trace()
    data = httptools.downloadpage(item.url).data

    item.url = scrapertools.find_single_match(data, "location.href='([^']+)")
    servertools.normalize_url(item)

    return item


def search(item):
    logger.trace()
    itemlist = list()

    url =  HOST + "/buscar.php?dataType=json&term=%s" % item.query.replace(" ", "+")

    data = httptools.downloadpage(url).data
    data = jsontools.load_json(data)
    if data:
        for tvshow in data.get("myData",[]):
            itemlist.append(item.clone(
                action='seasons',
                tvshowtitle=tvshow["titulo"],
                title=tvshow["titulo"],
                url=HOST + '/' + tvshow["urla"],
                poster=HOST + '/' + tvshow["img"],
                type='tvshow',
                content_type='seasons'))

    return itemlist