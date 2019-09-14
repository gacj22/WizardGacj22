# -*- coding: utf-8 -*-
from core.libs import *

HOST = settings.get_setting('host', __file__, getvalue=True)

services = {
    "OnlineUpToBox": 'http://uptobox.com/%s',
    "OnlineYourUpload": 'https://www.yourupload.com/watch/%s',
    "TheVideoMe": 'https://thevideo.me/embed-%s.html',
    "OnlineFilesCDN": 'http://filescdn.com/%s',
    "Trailer": 'https://www.youtube.com/watch?v=%s',
    "OnlineMega": "https://mega.nz/#!%s",
    "OnlineFembed": "https://www.fembed.com/v/%s",
    "OnlineUsersCloud": 'http://userscloud.com/%s',
    "OnlineUsersFiles": 'http://usersfiles.com/%s',
    'OnlineOkRu': 'http://ok.ru/video/%s',
    "OnlineOpenload": 'https://openload.co/f/%s',
    "OnlineStreamango": "http://streamango.com/embed/%s",
    "OnlineRapidVideo": "https://www.rapidvideo.com/e/%s",
    "UploadedTo": 'http://uploaded.net/file/%s',
    "TurboBit": 'http://turbobit.net/%s.html',
    "1fichier": 'https://1fichier.com/?%s',
    "OnlineGD": HOST + '/protect/gdredirect.php?l=%s',
    "Mega":  HOST + '/protect/v.html?i=%s',
    "BitTorrent":  HOST + '/protect/v.html?i=%s',
    "MediaFire":  HOST + '/protect/v.html?i=%s'
}


def mainlist(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        label='Novedades',
        action='movies',
        type="item",
        content_type='movies',
        url=HOST + '/espana/'
    ))

    itemlist.append(item.clone(
        label='Destacadas',
        action='movies',
        type="item",
        content_type='movies',
        url=HOST + '/espana/genero-peliculas/destacada/'
    ))

    itemlist.append(item.clone(
        label='Generos',
        action='categorias',
        type="item",
        content_type='items',
        url=HOST + '/espana/'
    ))

    itemlist.append(item.clone(
        label='Buscar',
        action='search',
        content_type='movies',
        query=True,
        type='search'
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
    platformtools.show_settings(item=item)


def search(item):
    logger.trace()
    item.url = HOST + '/espana/?s=%s' % item.query
    return movies(item)


def categorias(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url, use_proxy= settings.get_setting('use_proxy', __file__)).data
    patron = '<li id=menu-item-[^>]+><a href=([^>]+)>([^<]+)</a></li>'

    for url, label in sorted(scrapertools.find_multiple_matches(data, patron), key=lambda x: x[1]):
        if label in ['× Cerrar', '☰ Menú', 'Películas por año']:
            continue

        itemlist.append(item.clone(
            action='movies',
            label=label.strip(),
            url=url,
            content_type='movies'
        ))

    return itemlist


def movies(item):
    logger.trace()
    itemlist = list()

    if not item.url.startswith(HOST):
        item.url = HOST + item.url

    data = httptools.downloadpage(item.url, use_proxy= settings.get_setting('use_proxy', __file__)).data

    patron = '<div class="home_post_cont[^"]+">\s*<a href=(?P<url>[^">]+).*?src=(?P<poster>[^\s]+).*?' \
             'title="(?P<title>[^"]+)(?P<year>\([\d]+\)).*?".*?<p>(?P<plot>[^<]+)</p>'

    for result in re.compile(patron, re.DOTALL).finditer(data):
        itemlist.append(item.clone(
            action='findvideos',
            title=result.group('title').strip(),
            url=result.group('url'),
            poster=result.group('poster'),
            type='movie',
            content_type='servers',
            plot=result.group('plot'),
            year=result.group('year').strip('()')
        ))

    # Paginador
    next_url = scrapertools.find_single_match(data, "<link rel=next href=([^>]+)>")
    if next_url:
        itemlist.append(item.clone(
            action='movies',
            url=next_url,
            type='next'
        ))

    return itemlist


def findvideos(item):
    logger.trace()
    itemlist = list()

    for url, link, service_data  in scrapertools.find_multiple_matches(httptools.downloadpage(item.url,
                                                use_proxy= settings.get_setting('use_proxy', __file__)).data,
                                                '<a href="?([^;|"]+). target=_blank class=(.*?) service=([^>]+)'):

        if "Trailer data=" in service_data or "/vip/v.php?" in url:
            continue

        if 'data=' in service_data:
            url = get_server_url(scrapertools.find_single_match(service_data, 'data="([^"]+)"'),
                                 service_data.split(' ')[0])

        if url:
            if '/protect/v.' in url:
                data = httptools.downloadpage(
                    HOST + '/protect/contenido.php?i=%s' % url.split('=')[1],
                    use_proxy= settings.get_setting('use_proxy', __file__)).data
                url = scrapertools.find_single_match(data, 'href="([^"]+)"')

            itemlist.append(item.clone(
                action='play',
                url=url,
                type='server',
                stream = False if link == 'link' else True
            ))

    return servertools.get_servers_itemlist(itemlist)


def get_server_url(video_id, service_id):
    logger.trace()
    video_id = ''.join(map(chr, [int(x) -2 for x in video_id.split(' ')]))

    try:
        return services[service_id] % video_id
    except KeyError:
        logger.debug("service %s no encontrado" % service_id)
        return None