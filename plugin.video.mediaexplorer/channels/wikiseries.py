# -*- coding: utf-8 -*-
from core.libs import *

HOST = 'http://www.wikiseriesonline.nu'

LNG = Languages({
    Languages.es: ['espanol', '3', 'espa%25C3%25B1ol', 'español'],
    Languages.en: ['ingles', '5', 'english'],
    Languages.la: ['latino', '1'],
    Languages.sub_es: ['subtitulado', '4'],
    Languages.vo: ['vo']
})

QLT = Qualities({
    Qualities.hd: ['3', '5', 'hd-720p', 'hd'],
    Qualities.sd: ['1', '2'],
    Qualities.hd_full: ['4', 'hd-1080p']
})

def mainlist(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        action="newest_episodes",
        label="Nuevos episodios",
        url=HOST + '/category/episode',
        type="item",
        content_type='episodes'
    ))

    itemlist.append(item.clone(
        action="newest_tvshows",
        label="Nuevas series",
        url=HOST + '/category/serie',
        type="item",
        category='tvshow',
        content_type='tvshows'
    ))

    itemlist.append(item.clone(
        action="search",
        label="Buscar series",
        query=True,
        type='search',
        category='tvshow',
        content_type='tvshows'
    ))

    itemlist.append(item.clone(type="label"))
    itemlist.append(item.clone(
        label="Series por género:",
        type="label",
        category='tvshow',
        content_type='tvshows'
    ))


    for url, label in [("/category/accion", "Acción"), ("/category/anime", "Animación"), ("/category/aventura", "Aventura"),
              ("/category/ciencia-ficcion", "Ciencia Ficción"), ("/category/comedia", "Comedia"),
              ("/category/crimen", "Crimen"), ("/category/drama", "Drama"), ("/category/fantasia", "Fantasía"),
              ("/category/belico", "Guerra"), ("/category/horror", "Horror"), ("/category/misterio", "Misterio"),
              ("/category/romance", "Romance"), ("/category/suspenso", "Suspense")]:

        itemlist.append(item.clone(
            action="newest_tvshows",
            label=label,
            url=HOST + url,
            type="item",
            category='tvshow',
            group=True,
            content_type='tvshows'
        ))

    return itemlist


def newest_tvshows(item):
    logger.trace()
    itemlist = list()

    if not item.url:
        item.url = HOST + '/category/serie'

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}", "", data)

    patron = '<div class="poster-image-container">.*?src="([^"]+).*?' \
             '<a class="info-title one-line" href="([^"]+)" title="([^"]+)'

    for poster, url, title in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            action='seasons',
            label=title,
            tvshowtitle=title,
            title=title,
            url=url,
            poster=poster,
            type='tvshow',
            content_type='seasons'))


    next_page= scrapertools.find_single_match(data, '<a class="nextpostslink" rel="next" href="([^"]+)"')
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
    data = re.sub(r"\n|\r|\t|\s{2}", "", data)

    for num_season in scrapertools.find_multiple_matches(data, '<ul class="ep-list" id="ep-list-(\d+)"'):
        itemlist.append(item.clone(
            action="episodes",
            season=int(num_season),
            type='season',
            content_type='episodes'
        ))

    return itemlist


def episodes(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}", "", data)

    patron = '>%sx(\d+)</a></div><a class="ep-list-info" href="([^"]+)"><div class="ep-title"><span class="name">' \
             '([^<]+)<.*?<div class="ep-availability">(.*?)<div class="ep-list-indicators">' % item.season
    for num_episode, url, title, langs in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            title=title,
            url=url,
            action="findvideos",
            episode=int(num_episode),
            lang=[LNG.get(l) for l in
                  scrapertools.find_multiple_matches(langs, 'title="([^"]+)"')],
            thumb=None,
            type='episode',
            content_type='servers'
        ))

    return itemlist


def newest_episodes(item):
    logger.trace()
    itemlist = list()

    if not item.url:
        item.url = HOST + '/category/episode'

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}", "", data)

    patron = '<div class="poster-image-container">.*?src="([^"]+).*?' \
             '<a class="info-title one-line" href="([^"]+)" title="([^"]+)'

    for poster, url, title in scrapertools.find_multiple_matches(data, patron):
        title = title.replace('×','x')
        season, episode = scrapertools.get_season_and_episode(title)
        tvshowtitle = re.sub(r"%sx%02d" %(season, episode),'',title).strip()

        itemlist.append(item.clone(
            action='findvideos',
            tvshowtitle=tvshowtitle,
            label=tvshowtitle,
            season=season,
            episode=episode,
            url=url,
            poster=poster,
            thumb=None,
            type='episode',
            content_type='servers'))

    next_page = scrapertools.find_single_match(data, '<a class="nextpostslink" rel="next" href="([^"]+)"')
    if next_page and itemlist:
        itemlist.append(item.clone(
            url=next_page,
            type='next'
        ))

    return itemlist


def findvideos(item):
    logger.trace()
    itemlist = list()
    list_urls = list()

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}", "", data)

    patron = '<tr id=row\d+ data-type="(\d+)" data-lgn="(\d+)" data-qa="(\d+)" data-link="([^"]+)'
    for tipo, lang, qlt, url in scrapertools.find_multiple_matches(data, patron):
        if url not in list_urls:
            list_urls.append(url)

            itemlist.append(item.clone(
                url=url,
                action='play',
                type='server',
                lang=LNG.get(lang),
                quality=QLT.get(qlt.lower()),
                stream=(tipo == '1')
            ))


    for url in scrapertools.find_multiple_matches(data, 'class="a-player"\s*href="([^"]+)'):
        data = httptools.downloadpage(HOST + url).data
        data = re.sub(r"\n|\r|\t|\s{2}", "", data)

        embeidos = list()
        embeidos.extend(scrapertools.find_multiple_matches(data,
                        '<div class="cont-video"><h2[^>]*>(.*?)</h2>.*?<iframe.*?src="([^"]+)"'))

        embeidos.extend(scrapertools.find_multiple_matches(data,
                        '<div class="row box-repro-title"><b>(.*?)</b>.*?'
                        '<div class="embed-responsive embed-responsive-16by9"><iframe src="([^"]+)"', re.IGNORECASE))

        for tag, url in embeidos:
            if url not in list_urls:
                list_urls.append(url)
                try:
                    tag = tag.lower().replace('hd 720p',  'hd-720p')
                    t = re.sub(r"%s|%sx%02d|temporada|ver|online" % (item.tvshowtitle.lower(),item.season, item.episode), '', tag).strip().split()
                    lang = t[-2]
                    qlt = t[-1]

                except:
                    logger.debug('Imposible obtener la calidad y el idioma de: %s' % tag)
                    lang = qlt = 'unk'

                itemlist.append(item.clone(
                    url=url,
                    action='play',
                    type='server',
                    lang=LNG.get(lang),
                    quality=QLT.get(qlt)
                ))

    if itemlist:
        return servertools.get_servers_itemlist(itemlist)

    url_trailer = scrapertools.find_single_match(data, '<a class="popup-trailer"href="([^"]+)"')
    if url_trailer:
        itemlist.append(item.clone(
            url=url_trailer,
            action='play',
            type='server'
        ))

        itemlist = servertools.get_servers_itemlist(itemlist)
        itemlist[0].servername += ' (Trailer)'

    return itemlist


def search(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage("http://www.wikiseriesonline.nu/wp-content/themes/wikiSeries/searchajaxresponse.php",
                                  post = {'n': item.query.replace(" ", "+")}).data
    data = re.sub(r"\n|\r|\t|\s{2}", "", data)

    patron = '<a href="([^"]+)">.*?src="([^"]+).*?<span class="titleinst">([^<]+)</span>' \
             '<span class="titleinst year">(\d{4})<'

    for url, poster, title, year in scrapertools.find_multiple_matches(data, patron):
        itemlist.append(item.clone(
            action='seasons',
            label=title,
            tvshowtitle=title,
            title=title,
            year=year,
            url=url,
            poster=poster.replace('-113x162', ''),
            type='tvshow',
            content_type='seasons'))

    return itemlist
