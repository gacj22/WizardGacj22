# -*- coding: utf-8 -*-
# -*- Channel Ver-peliculas -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib
import urlparse

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from channels import filtertools, autoplay
from core import tmdb

__channel__ = "ver-peliculas"

host = "https://ver-peliculas.co/"

IDIOMAS = {'Latino':'Lat', 'Castellano':'Cast', 'Subtitulada':'VOSE'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['directo', 'openload',  'streamango', 'rapidvideo']

try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
except:
    __modo_grafico__ = True

def mainlist(item):
    logger.info()

    itemlist = list()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(
        Item(channel=item.channel,
             title="Peliculas",
             action="listado",
             url=host + "peliculas/",
             thumbnail=get_thumb("channels_movie.png")))
    itemlist.append(
        Item(channel=item.channel,
             title="Español",
             action="listado",
             url=host + "peliculas/en-espanol/",
             thumbnail = get_thumb("channels_spanish.png")))
    itemlist.append(
        Item(channel=item.channel,
             title="Latino",
             action="listado",
             url=host + "peliculas/en-latino/",
             thumbnail=get_thumb("channels_latino.png")))
    itemlist.append(
        Item(channel=item.channel,
             title="Subtituladas",
             action="listado",
             url=host + "peliculas/subtituladas/",
             thumbnail=get_thumb("channels_vos.png")))
    itemlist.append(
        Item(channel=item.channel,
             title="Generos",
             action="categories",
             url=host,
             thumbnail=get_thumb('genres', auto=True)
             ))
    itemlist.append(
        Item(channel=item.channel,
             title="Buscar",
             action="search",
             url=host + "/buscar/",
             thumbnail=get_thumb("search.png")))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def categories(item):
    logger.info()
    itemlist = []

    data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url).data)
    section = scrapertools.find_single_match(data, '<ul class="sub-menu">(.*?)</ul>')

    matches = re.compile('<li><a href="([^"]+)"[^>]+>(.*?)</a>', re.DOTALL).findall(section)

    for url, title in matches:
        itemlist.append(Item(channel=item.channel,
                             action="listado",
                             title=title,
                             url=url
                             ))

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto + '.html'
    if texto != '':
        return listado(item)

def listado(item):
    logger.info()
    itemlist = []
    data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url).data)
    pattern = '<a href="([^"]+)"[^>]+><img (?:src)?(?:data-original)?="([^"]+)".*?alt="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, pattern)
    for url, thumb, title in matches:
        year = scrapertools.find_single_match(url, '-(\d+)-online')
        #title = title.replace("Película", "", 1).partition(" /")[0].partition(":")[0]
        title = title.replace("Película", "", 1).partition(" /")[0]
        itemlist.append(Item(channel=item.channel,
                             action="findvideos",
                             title=title,
                             infoLabels={"year": year},
                             url=url,
                             thumbnail=thumb,
                             contentTitle=title.strip()
                             ))
    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    pagination = scrapertools.find_single_match(data, '<ul class="pagination">(.*?)</ul>')
    if pagination:
        next_page = scrapertools.find_single_match(pagination, '<a href="#">\d+</a>.*?<a href="([^"]+)">')
        if next_page:
            url = urlparse.urljoin(host, next_page)
            itemlist.append(Item(channel=item.channel,
                                 action="listado",
                                 title=">> Página siguiente",
                                 url=url,
                                 thumbnail=get_thumb("next.png")))
    return itemlist


def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def findvideos(item):
    logger.info()
    duplicated = []
    itemlist = []
    data = get_source(item.url)
    video_info = scrapertools.find_single_match(data, "load_player\('([^']+).*?([^']+)")
    movie_info = scrapertools.find_single_match(item.url,
                                            'http.:\/\/ver-peliculas\.(io|org|co)\/peliculas\/(\d+)-(.*?)-\d{4}-online\.')

    if movie_info:
        movie_host = movie_info[0]
        movie_id = scrapertools.find_single_match(data,'id=idpelicula value=(.*?)>')
        movie_name = scrapertools.find_single_match(data,'id=nombreslug value=(.*?)>')
        sub = scrapertools.find_single_match(data, 'id=imdb value=(.*?)>')
        sub = '%s/subtix/%s.srt' % (movie_host, sub)
        url_base = 'https://ver-peliculas.%s/core/api.php?id=%s&slug=%s' % (movie_host, movie_id, movie_name)
        json_data = httptools.downloadpage(url_base).json
        video_list = json_data['lista']
        for videoitem in video_list:
            video_base_url = host.replace('.io', '.%s' % movie_host) + 'core/videofinal.php'
            if video_list[videoitem] != None:
                video_lang = video_list[videoitem]
                languages = ['latino', 'spanish', 'subtitulos', 'subtitulosp']
                for lang in languages:
                    if lang not in video_lang:
                        continue
                    if video_lang[lang] != None:
                        if not isinstance(video_lang[lang], int):
                            video_id = video_lang[lang][0]["video"]
                            post = {"video": video_id, "sub": sub}
                            post = urllib.urlencode(post)
                            playlist = httptools.downloadpage(video_base_url, post=post).json
                            sources = playlist[['playlist'][0]]
                            server = playlist['server']
                            for video_link in sources:
                                url = video_link['sources']
                                if url not in duplicated and server!='drive':

                                    if lang == 'spanish':
                                        lang = 'Castellano'
                                    elif 'sub' in lang:
                                        lang = 'Subtitulada'
                                    lang = lang.capitalize()
                                    title = 'Ver en %s [' + lang + ']'
                                    thumbnail = servertools.guess_server_thumbnail(server)
                                    itemlist.append(item.clone(title=title,
                                                               url=url,
                                                               thumbnail=thumbnail,
                                                               action='play',
                                                               language=IDIOMAS[lang]
                                                               ))
                                    duplicated.append(url)
    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    itemlist = sorted(itemlist, key=lambda i: i.language)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(
            Item(channel=item.channel,
                 title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                 url=item.url,
                 action="add_pelicula_to_library",
                 extra="findvideos",
                 contentTitle=item.contentTitle
                 ))

    return itemlist


def play(item):
    item.thumbnail = item.contentThumbnail
    return [item]


def newest(category):
    logger.info()
    item = Item()
    try:
        if category == 'peliculas':
            item.url = host + "peliculas/"
        elif category == 'infantiles':
            item.url = host + 'categorias/peliculas-de-animacion.html'
        itemlist = listado(item)
        if itemlist[-1].title == '>> Página siguiente':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

    return itemlist
