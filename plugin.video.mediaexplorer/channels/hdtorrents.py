# -*- coding: utf-8 -*-
from core.libs import *
import unicodedata

HOST = 'https://www.hdtorrents.info'

LNG = Languages({
    Languages.es: ['Español'],
    Languages.la: ['Latino'],
    Languages.vos: ['VO']
})

QLT = Qualities({
    Qualities.rip: ['hdrip'],
    Qualities.uhd: ['4k'],
    Qualities.hd: ['720p'],
    Qualities.hd_full: ['1080p', 'microhd', 'bluray rip', 'hd'],
    Qualities.m3d: ['3d'],
    Qualities.scr: ['ts screener', 'dvd rip']
})


def mainlist(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        action="movies",
        label="Novedades",
        type="item",
        content_type='movies'
    ))

    itemlist.append(item.clone(
        action="movies",
        label="Top ten torrents",
        url=HOST + '/torrents',
        type="item",
        content_type='movies'
    ))

    itemlist.append(item.clone(
        action="portada",
        label="En portada",
        url=HOST,
        type="item",
        content_type='movies'
    ))

    itemlist.append(item.clone(
        action="tags_qlt",
        label="Filtrar por calidad",
        url=HOST,
        type="item",
        category='movie'
    ))

    itemlist.append(item.clone(
        action="search",
        label="Buscar",
        query=True,
        type='search',
        content_type='movies'
    ))

    return itemlist


def tags_qlt(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, 'tagsdescargas">(.*?)header_info">')

    patron = '<a href="(?P<url>[^"]+)" rel="tag" class="">(?P<tag>[^<]+)</a></li>'

    for result in re.compile(patron, re.DOTALL).finditer(data):
        itemlist.append(item.clone(
            action="movies",
            label=result.group('tag'),
            quality=QLT.get(result.group('tag').lower()),
            url=result.group('url'),
            type='item',
            content_type='movies'
        ))

    return sorted(itemlist, key=lambda i: i.quality.level, reverse=True)


def movies(item):
    logger.trace()
    itemlist = list()
    auxdict = dict()

    if not item.url:
        item.url = HOST + '/torrents'

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = 'class="%s\s?"><a(?: title="([^"]+)")? href="([^"]+)"(?: title="([^"]+)")?.*?src="([^"]+)"'

    if item.label == "Top ten torrents":
        agrupar = False
        patron = patron % "mostread"

    elif item.query:
        agrupar = True
        patron = patron % "moditemfdb"

    else:
        agrupar = True
        patron = patron % "blogitem"

    i = 0
    for title1, url, title2, poster in scrapertools.find_multiple_matches(data, patron):
        title = title1 or title2
        idioma, calidad, title = idioma_calidad(title)

        new_item = item.clone(
                    action='findvideos',
                    title=title,
                    url=[HOST + url],
                    poster=poster.replace('t.jpg', '.jpg'),
                    type='movie',
                    quality=[QLT.get(calidad)],
                    lang= [LNG.get(idioma)],
                    content_type='servers'
                )

        if not agrupar:
            label_extra = {"sublabel": " -MicroHD-",
                           "color": "yellow",
                           "value": "True"} if calidad == 'microhd' else None

            auxdict[i] = (i, new_item.clone(label_extra=label_extra))
            i += 1

        else:
            key = normalizar(title)
            if not key in auxdict:
                auxdict[key] = (i, new_item.clone())
                i += 1

            else:
                orden, it = auxdict[key]
                q_aux = it.quality[:]
                l_aux = it.lang[:]
                u_aux = it.url[:]
                u_aux.append(HOST + url)

                if QLT.get(calidad) not in it.quality:
                    q_aux.append(QLT.get(calidad))

                if LNG.get(idioma) not in it.lang:
                    l_aux.append(LNG.get(idioma))

                auxdict[key] = (orden, it.clone(
                    url=u_aux,
                    lang=l_aux,
                    quality=sorted(q_aux, key=lambda q: q.level, reverse=True)
                ))

    for orden, it in sorted(auxdict.values(), key=lambda x: x[0]):
        itemlist.append(it.clone(label_extra=it.label_extra if it.label_extra else None))

    if item.label != "Top ten torrents":
        next_page = scrapertools.find_single_match(data, '<a href="(?P<next_page>[^"]+)" '
                                                         'title="Siguiente">Siguiente</a>')
        if next_page and itemlist:
            itemlist.append(item.clone(
                url=HOST + next_page,
                label=item.label,
                type='next'
            ))

    return itemlist


def normalizar(s):
    s = s.lower()
    if isinstance(s, str):
        s = s.decode('utf-8')

    return ''.join((c for c in unicodedata.normalize('NFD',unicode(s)) if unicodedata.category(c) != 'Mn'))


def search(item):
    logger.trace()

    if not item.url:
        item.url = HOST + '/buscar?searchword=%s&ordering=&searchphrase=all&limit=40' % item.query.replace(" ", "+")

    return movies(item)


def idioma_calidad(title):
    title = re.sub(r" -| 3D| \*.*?\*| DTS", "", title).strip()
    calidad = scrapertools.find_single_match(title, '\[([^\]]+)\]$')

    if calidad:
        title = title.replace(' [%s]' % calidad, '')
        calidad = calidad.lower()
    else:
        calidad = "Desconocida"

    idioma = scrapertools.find_single_match(title, '\(([^\)]+)\)$')

    if idioma:
        title = title.replace(' (%s)' % idioma, '')
    else:
        idioma = 'Español'

    return idioma, calidad, title


def portada(item):
    logger.trace()
    itemlist = list()
    auxdict = dict()

    data = httptools.downloadpage(item.url).data
    patron = '<a href="[^"]+" title="([^"]+)".*?src="([^"]+)"'

    for title, poster in scrapertools.find_multiple_matches(data, patron):
        idioma, calidad, title = idioma_calidad(title)
        key = normalizar(title)
        if not key in auxdict:
            auxdict[key]=item.clone(
                action='findvideos',
                title=title,
                poster=poster,
                type='movie',
                content_type='servers')

    threads = list()
    for item in auxdict.values():
        t = Thread(target=sub_busqueda, args=[item, itemlist])

        t.setDaemon(True)
        t.start()
        threads.append(t)

    while [t for t in threads if t.isAlive()]:
        time.sleep(0.5)

    return itemlist


def sub_busqueda(item, itemlist):
    list_urls = list()
    idiomas = set()
    calidades = set()

    if len(item.title) < 3:
        url = item.url
        patron = '<a href="(?P<url>[^"]+)" title="(?P<title>[^"]+)".*?src="[^"]+"'
    else:
        url = HOST + '/buscar?searchword=%s&ordering=&searchphrase=all&limit=20' % item.title[:50]
        patron = 'class="moditemfdb"><a title="(?P<title>[^"]+)" href="(?P<url>[^"]+)"'

    data = httptools.downloadpage(url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    for result in re.compile(patron, re.DOTALL).finditer(data):
        idioma, calidad, title = idioma_calidad(result.group('title'))

        if normalizar(title) == normalizar(item.title):
            list_urls.append(HOST + result.group('url'))
            idiomas.add(LNG.get(idioma))
            calidades.add(QLT.get(calidad))

    if list_urls:
        itemlist.append(item.clone(
            url= list_urls,
            quality=sorted(list(calidades), key=lambda c: c.level, reverse=True),
            lang=list(idiomas)
        ))

    return itemlist


def findvideos(item):
    logger.trace()
    itemlist = list()

    for link in item.url:
        data = httptools.downloadpage(link).data
        data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

        title, url = scrapertools.find_single_match(data, '<title>([^<]+)- HD Torrents</title>.*?'
                                                          'download"><p><a href="([^"]+)" rel=')

        idioma, calidad, title = idioma_calidad(title)

        itemlist.append(item.clone(
            action='play',
            url=url,
            quality=QLT.get(calidad),
            lang=LNG.get(idioma),
            label_extra={"sublabel": " -MicroHD-",
                         "color": "yellow",
                         "value": "True"} if calidad == 'microhd' else None,
            server='torrent',
            type='server'
        ))

    return servertools.get_servers_from_id(itemlist)


def play(item):
    logger.trace()
    item.url = scrapertools.find_single_match(httptools.downloadpage(HOST + item.url).data, 'click <a href="'
                                                                                          '([^"]+)"><strong>')
    return item


