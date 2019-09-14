# -*- coding: utf-8 -*-

import re
import urlparse

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

IDIOMAS = {'latino': 'Latino', 'castellano': 'Castellano', 'portugues': 'Portugues'}
list_language = IDIOMAS.values()
list_quality = ['1080p']
list_servers = [
    
    'gounlimited',
    'verystream',
    'mega',
    'vidcloud',
    'torrent',
    'rapidvideo',
    'streamango',
    'openload',
    'torrent'
]

host = 'http://www.cinecalidad.to'
thumbmx = 'http://flags.fmcdn.net/data/flags/normal/mx.png'
thumbes = 'http://flags.fmcdn.net/data/flags/normal/es.png'
thumbbr = 'http://flags.fmcdn.net/data/flags/normal/br.png'
current_lang = ''

site_list = ['', 'cinecalidad.to/', 'cinecalidad.to/espana/', 'cinemaqualidade.to/']
site = config.get_setting('filter_site', channel='cinecalidad')
site_lang = 'http://www.%s' % site_list[site]

def mainlist(item):
    logger.info()
    
    itemlist = []
    idioma2 = "destacadas"
    
    if site > 0:
        item.action = 'submenu'
        item.host = site_lang
        return submenu(item)


    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []

    itemlist.append(
        item.clone(title="CineCalidad Latino",
                   action="submenu",
                   host="http://www.cinecalidad.to/",
                   thumbnail=thumbmx))

    itemlist.append(item.clone(title="CineCalidad Castellano",
                               action="submenu",
                               host="http://www.cinecalidad.to/espana/",
                               thumbnail=thumbes))

    itemlist.append(
        item.clone(title="CineCalidad Portugues",
                   action="submenu",
                   host="http://www.cinemaqualidade.to/",
                   thumbnail=thumbbr))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def submenu(item):
    idioma = 'peliculas'
    idioma2 = "destacada"
    host = item.host
    if item.host == "http://www.cinemaqualidade.to/":
        idioma = "filmes"
        idioma2 = "destacado"
    logger.info()
    itemlist = []

    itemlist.append(Item(channel=item.channel,
                         title=idioma.capitalize(),
                         action="peliculas",
                         url=host,
                         thumbnail=get_thumb('movies', auto=True),
                         fanart='https://s8.postimg.cc/6wqwy2c2t/peliculas.png',
                         ))
    itemlist.append(Item(channel=item.channel,
                         title="Destacadas",
                         action="peliculas",
                         url=host + "/genero-" + idioma + "/" + idioma2 + "/",
                         thumbnail=get_thumb('hot', auto=True),
                         fanart='https://s30.postimg.cc/humqxklsx/destacadas.png',
                         ))
    itemlist.append(Item(channel=item.channel,
                         title="Generos",
                         action="generos",
                         url=host + "/genero-" + idioma,
                         thumbnail=get_thumb('genres', auto=True),
                         fanart='https://s3.postimg.cc/5s9jg2wtf/generos.png',
                         ))
    itemlist.append(Item(channel=item.channel,
                         title="Por Año",
                         action="anyos",
                         url=host + idioma + "-por-ano",
                         thumbnail=get_thumb('year', auto=True),
                         fanart='https://s8.postimg.cc/7eoedwfg5/pora_o.png',
                         ))
    itemlist.append(Item(channel=item.channel,
                         title="Buscar",
                         action="search",
                         thumbnail=get_thumb('search', auto=True),
                         url=host + '/?s=',
                         fanart='https://s30.postimg.cc/pei7txpa9/buscar.png',
                         host=item.host,
                         ))
    if site > 0:
        autoplay.init(item.channel, list_servers, list_quality)
        
        itemlist.append(Item(channel=item.channel,
                         title="Configurar Canal...",
                         text_color="turquoise",
                         action="settingCanal",
                         thumbnail=get_thumb('setting_0.png'),
                         url='',
                         fanart=get_thumb('setting_0.png')
                         ))
        
        autoplay.show_option(item.channel, itemlist)

    return itemlist

def settingCanal(item):
    from platformcode import platformtools
    platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return

def anyos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<a href=([^>]+)>([^<]+)</a><br'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        url = urlparse.urljoin(item.url, scrapedurl)
        title = scrapedtitle
        thumbnail = item.thumbnail
        plot = item.plot
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title=title,
                 url=url,
                 thumbnail=thumbnail,
                 plot=plot,
                 fanart=item.thumbnail,
                 language=item.language
                 ))

    return itemlist


def generos(item):
    tgenero = {"Comedia": "https://s7.postimg.cc/ne9g9zgwb/comedia.png",
               "Suspenso": "https://s13.postimg.cc/wmw6vl1cn/suspenso.png",
               "Drama": "https://s16.postimg.cc/94sia332d/drama.png",
               "Acción": "https://s3.postimg.cc/y6o9puflv/accion.png",
               "Aventura": "https://s10.postimg.cc/6su40czih/aventura.png",
               "Romance": "https://s15.postimg.cc/fb5j8cl63/romance.png",
               "Fantas\xc3\xada": "https://s13.postimg.cc/65ylohgvb/fantasia.png",
               "Infantil": "https://s23.postimg.cc/g5rmazozv/infantil.png",
               "Ciencia ficción": "https://s9.postimg.cc/diu70s7j3/cienciaficcion.png",
               "Terror": "https://s7.postimg.cc/yi0gij3gb/terror.png",
               "Com\xc3\xa9dia": "https://s7.postimg.cc/ne9g9zgwb/comedia.png",
               "Suspense": "https://s13.postimg.cc/wmw6vl1cn/suspenso.png",
               "A\xc3\xa7\xc3\xa3o": "https://s3.postimg.cc/y6o9puflv/accion.png",
               "Fantasia": "https://s13.postimg.cc/65ylohgvb/fantasia.png",
               "Fic\xc3\xa7\xc3\xa3o cient\xc3\xadfica": "https://s9.postimg.cc/diu70s7j3/cienciaficcion.png"}
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<li id=menu-item-.*? class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-.*?'
    patron +='"><a href=([^>]+)>([^<]+)<\/a></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        url = urlparse.urljoin(item.url, scrapedurl)
        title = scrapedtitle
        thumbnail = ''
        plot = item.plot
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title=title, url=url,
                 thumbnail=thumbnail,
                 plot=plot,
                 fanart=item.thumbnail,
                 language=item.language
                 ))

    return itemlist


def peliculas(item):
    logger.info()
    global current_lang
    itemlist = []

    if 'cinemaqualidade' in item.url:
        current_lang = 'portugues'
    elif 'espana' in item.url:
        current_lang = 'castellano'
    elif 'cinecalidad' in item.url:
        current_lang = 'latino'


    data = httptools.downloadpage(item.url).data
    patron = '<div class="home_post_cont.*? post_box">.*?<a href=([^>]+)>.*?src=([^ ]+).*?'
    patron += 'title="(.*?) \((.*?)\).*?".*?p&gt;(.*?)&lt'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedyear, scrapedplot in matches:
        url = urlparse.urljoin(item.url, scrapedurl)
        contentTitle = scrapedtitle
        title = scrapedtitle + ' (' + scrapedyear + ')'
        thumbnail = scrapedthumbnail
        plot = scrapedplot
        year = scrapedyear
        language = current_lang.capitalize()
        if item.gb_search:
            title += " (%s)" % language
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 title=title,
                 url=url,
                 thumbnail=thumbnail,
                 plot=plot,
                 fanart='https://s31.postimg.cc/puxmvsi7v/cinecalidad.png',
                 contentTitle=contentTitle,
                 infoLabels={'year': year},
                 language=language,
                 context=autoplay.context
                 ))

    try:
        patron = "<link rel=next href=([^>]+)>"
        next_page = re.compile(patron, re.DOTALL).findall(data)
        itemlist.append(Item(channel=item.channel,
                             action="peliculas",
                             title="Página siguiente >>",
                             url=next_page[0],
                             fanart='https://s31.postimg.cc/puxmvsi7v/cinecalidad.png',
                             language=item.language
                             ))

    except:
        pass
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def dec(item, dec_value):
    link = []
    val = item.split(' ')
    link = map(int, val)
    for i in range(len(link)):
        link[i] = link[i] - int(dec_value)
        real = ''.join(map(chr, link))
    return (real)


def findvideos(item):
    servidor = {"http://uptobox.com/": "uptobox",
                "http://userscloud.com/": "userscloud",
                "https://my.pcloud.com/publink/show?code=": "pcloud",
                "http://thevideos.tv/": "thevideos",
                "http://ul.to/": "uploadedto",
                "http://turbobit.net/": "turbobit",
                "http://www.cinecalidad.to/protect/v.html?i=": "cinecalidad",
                "http://www.mediafire.com/download/": "mediafire",
                "https://www.youtube.com/watch?v=": "youtube",
                "http://thevideos.tv/embed-": "thevideos",
                "//www.youtube.com/embed/": "youtube",
                "http://ok.ru/video/": "okru",
                "http://ok.ru/videoembed/": "okru",
                "http://www.cinemaqualidade.com/protect/v.html?i=": "cinemaqualidade.com",
                "http://usersfiles.com/": "usersfiles",
                "https://depositfiles.com/files/": "depositfiles",
                "http://www.nowvideo.sx/video/": "nowvideo",
                "http://vidbull.com/": "vidbull",
                "http://filescdn.com/": "filescdn",
                "https://www.yourupload.com/watch/": "yourupload",
                "http://www.cinecalidad.to/protect/gdredirect.php?l=": "directo",
                "https://openload.co/embed/": "openload",
                "https://streamango.com/embed/f/": "streamango",
                "https://www.rapidvideo.com/embed/": "rapidvideo",
                }


    logger.info()
    itemlist = []
    duplicados = []

    if 'cinemaqualidade' in item.url:
        lang = 'portugues'
    elif 'espana' in item.url:
        lang = 'castellano'
    elif 'cinecalidad' in item.url:
        lang = 'latino'

    data = httptools.downloadpage(item.url).data
    patron = 'target=_blank.*? service=.*? data="(.*?)"><li>(.*?)<\/li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    server_url = {'YourUpload': 'https://www.yourupload.com/embed/',
                  'Openload': 'https://openload.co/embed/',
                  'TVM': 'https://thevideo.me/embed-',
                  'Streamango': 'https://streamango.com/embed/',
                  'RapidVideo': 'https://www.rapidvideo.com/embed/',
                  'Trailer': 'https://www.youtube.com/embed/',
                  'BitTorrent': '',
                  'Mega': 'https://mega.nz/#!',
                  'MediaFire': '',
                  'Fembed': 'https://www.fembed.com/v/',
                  'Verystream': 'https://verystream.com/e/',
                  'Gounlimited': 'https://gounlimited.to/embed-',
                  'Clipwatching': 'https://clipwatching.com/embed-',
                  'Vidcloud': 'https://vidcloud.co/embed/'}
    dec_value = scrapertools.find_single_match(data, 'String\.fromCharCode\(parseInt\(str\[i\]\)-(\d+)\)')
    torrent_link = scrapertools.find_single_match(data, '<a href=".*?/protect/v\.php\?i=([^"]+)"')
    subs = scrapertools.find_single_match(data, '<a id=subsforlink href=(.*?) ')
    if torrent_link != '':
        import urllib
        base_url = '%s/protect/v.php' % host
        post = {'i': torrent_link, 'title': item.title}
        post = urllib.urlencode(post)
        headers = {'Referer': item.url}
        protect = httptools.downloadpage(base_url + '?' + post, headers=headers).data
        url = scrapertools.find_single_match(protect, 'value="(magnet.*?)"')
        server = 'torrent'

        title = item.contentTitle + ' (%s)' % server
        quality = '1080p'
        language = IDIOMAS[lang]

        new_item = Item(channel=item.channel,
                        action='play',
                        title=title,
                        contentTitle=item.contentTitle,
                        url=url,
                        language=language,
                        thumbnail=item.thumbnail,
                        quality=quality,
                        server=server
                        )
        itemlist.append(new_item)

    for video_cod, server_id in matches:
        thumbnail = item.thumbnail
        if server_id not in ['MediaFire', 'TVM'] or server.lower() not in duplicados:
            video_id = dec(video_cod, dec_value)

        if server_id in server_url:
            server = server_id.lower()
            
            if server_id in ['Gounlimited', 'Clipwatching']:
                url = server_url[server_id] + video_id + '.html'
            else:
                url = server_url[server_id] + video_id
        
        title = item.contentTitle + ' (%s)' % server
        quality = '1080p'

        if server_id not in ['MediaFire', 'TVM']:

            language = [IDIOMAS[lang], 'VOSE']
            if server not in duplicados:
                new_item = Item(channel=item.channel,
                                action='play',
                                title=title,
                                contentTitle=item.contentTitle,
                                url=url,
                                language= language,
                                thumbnail=thumbnail,
                                quality=quality,
                                server=server,
                                subtitle=subs
                                )
                itemlist.append(new_item)
                duplicados.append(server)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    # itemlist.append(trailer_item)
    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(
            Item(channel=item.channel,
                 title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                 url=item.url,
                 action="add_pelicula_to_library",
                 extra="findvideos",
                 contentTitle=item.contentTitle,
                 ))

    return itemlist


def get_urls(item, link):
    logger.info()
    url = 'http://www.cinecalidad.to/ccstream/ccstream.php'
    headers = dict()
    headers["Referer"] = item.url
    post = 'link=%s' % link

    dict_data = httptools.downloadpage(url, post=post, headers=headers).json
    return dict_data['link']


def play(item):
    logger.info()
    itemlist = []
    if 'juicyapi' not in item.url:
        itemlist = servertools.find_video_items(data=item.url)

        for videoitem in itemlist:
            videoitem.title = item.contentTitle
            videoitem.contentTitle = item.contentTitle
            videoitem.thumbnail = item.thumbnail
            videoitem.channel = item.channel
            videoitem.subtitle = item.subtitle
    else:
        itemlist.append(item)

    return itemlist


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas','latino']:
            item.url = 'http://www.cinecalidad.to'
        elif categoria == 'infantiles':
            item.url = 'http://www.cinecalidad.to/genero-peliculas/infantil/'
        elif categoria == 'terror':
            item.url = 'http://www.cinecalidad.to/genero-peliculas/terror/'
        elif categoria == 'castellano':
            item.url = 'http://www.cinecalidad.to/espana/'
        itemlist = peliculas(item)
        if itemlist[-1].title == 'Página siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

def search(item, texto):
    logger.info()
    itemlist = []

    texto = texto.replace(" ", "-")
    
    if item.host != '':
        host_list = [item.host]
    
    else:
        item.gb_search = True
        host_list = ['http://www.cinecalidad.to/espana/', 'http://www.cinecalidad.to/']
    
    for host_name in host_list:
        item.url = host_name + '?s=' + texto
        if texto != '':
            itemlist.extend(peliculas(item))
    
    return itemlist