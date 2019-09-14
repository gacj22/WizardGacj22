# -*- coding: utf-8 -*-
# -*- Channel PeliculonHD -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import base64

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from lib import jsunpack
from core.item import Item
from channels import filtertools
from channels import autoplay
from platformcode import config, logger


IDIOMAS = {'mx': 'Latino', 'dk':'Latino', 'es': 'Castellano', 'en': 'VOSE', 'gb':'VOSE'}
list_language = IDIOMAS.values()

list_quality = []

list_servers = [
    'directo',
    'openload',
    'rapidvideo',
    'jawcloud',
    'cloudvideo',
    'upvid',
    'vevio',
    'gamovideo'
]

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'peliculonhd')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'peliculonhd')

host = 'https://peliculonhd.tv/'

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title='Peliculas', action='menu_movies',
                         thumbnail= get_thumb('movies', auto=True)))
    itemlist.append(Item(channel=item.channel, title='Series', url=host+'ver-serie', action='list_all', type='tv',
                         thumbnail= get_thumb('tvshows', auto=True)))
    itemlist.append(
        item.clone(title="Buscar", action="search", url=host + '?s=', thumbnail=get_thumb("search", auto=True),
                   extra='movie'))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def menu_movies(item):
    logger.info()

    itemlist=[]

    itemlist.append(Item(channel=item.channel, title='Todas', url=host + 'ver-pelicula', action='list_all',
                         thumbnail=get_thumb('all', auto=True), type='movie'))
    itemlist.append(Item(channel=item.channel, title='Genero', action='section',
                         thumbnail=get_thumb('genres', auto=True), type='movie'))
    itemlist.append(Item(channel=item.channel, title='Por Año', action='section',
                         thumbnail=get_thumb('year', auto=True), type='movie'))

    return itemlist

def get_source(url, referer=None):
    logger.info()
    if referer is None:
        data = httptools.downloadpage(url).data
    else:
        data = httptools.downloadpage(url, headers={'Referer':referer}).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def get_language(lang_data):
    logger.info()
    language = []
    lang_list = scrapertools.find_multiple_matches(lang_data, '/flags/(.*?).png\)')
    for lang in lang_list:
        if lang == 'en':
            lang = 'vose'
        if lang not in language:
            language.append(lang)
    return language

def section(item):
    logger.info()
    itemlist=[]
    duplicados=[]
    full_data = get_source(host+'/'+item.type)
    if 'Genero' in item.title:
        data = scrapertools.find_single_match(full_data, '<a href="#">Genero</a>(.*?)</ul>')
    elif 'Año' in item.title:
        data = scrapertools.find_single_match(full_data, '<a href="#">Año</a>(.*?)</ul>')
    patron = '<a href="([^"]+)">([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle
        plot=''
        url = scrapedurl
        if not scrapedurl.startswith('http'):
            url = host+scrapedurl
        if title not in duplicados and title.lower() != 'proximamente':
            itemlist.append(Item(channel=item.channel, url=url, title=title, plot=plot, action='list_all',
                                 type=item.type))
            duplicados.append(title)

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)

    if item.type ==  'movie':
        patron = '<article id="post-\d+" class="item movies"><div class="poster">.*?<img src="([^"]+)" alt="([^"]+)">.*?'
        patron += '"quality">([^<]+)</span><\/div>\s?<a href="([^"]+)">.*?</h3>.*?<span>([^<]+)</'
        matches = re.compile(patron, re.DOTALL).findall(data)

        for scrapedthumbnail, scrapedtitle, quality, scrapedurl, year in matches:

            year = scrapertools.find_single_match(year,'(\d{4})')
            title = '%s [%s] [%s]' % (scrapedtitle, year, quality)
            contentTitle = scrapedtitle
            thumbnail = scrapedthumbnail
            url = scrapedurl
            #language = get_language(lang_data)

            if 'proximamente' not in quality.lower():
                itemlist.append(item.clone(action='findvideos',
                                title=title,
                                url=url,
                                thumbnail=thumbnail,
                                quality=quality,
                                contentTitle= contentTitle,
                                type=item.type,
                                infoLabels={'year':year}))

    elif item.type ==  'tv':
        patron = '<article id="post-\d+" class="item tvshows"><div class="poster">.*?<img src="([^"]+)" '
        patron += 'alt="([^"]+)">.*?<a href="([^"]+)">.*?</h3>.*?<span>([^<]+)</'
        matches = re.compile(patron, re.DOTALL).findall(data)

        for scrapedthumbnail, scrapedtitle, scrapedurl, year in matches:
            title = scrapedtitle
            contentSerieName = scrapedtitle
            thumbnail = scrapedthumbnail
            url = scrapedurl

            itemlist.append(item.clone(action='seasons',
                            title=title,
                            url=url,
                            thumbnail=thumbnail,
                            contentSerieName=contentSerieName,
                            type=item.type,
                            infoLabels={'year':year}))

    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    #  Paginación

    if item.type != 'movie':
        item.type = 'tv'
    url_next_page = scrapertools.find_single_match(data,'<link rel="next" href="([^ ]+)" />')
    url_next_page = 'https:'+ url_next_page
    if url_next_page:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, type=item.type, action='list_all'))

    return itemlist

def seasons(item):
    logger.info()

    itemlist=[]

    data=get_source(item.url)
    patron='Temporada \d+'
    matches = re.compile(patron, re.DOTALL).findall(data)

    infoLabels = item.infoLabels
    for season in matches:
        season = season.lower().replace('temporada','')
        infoLabels['season']=season
        title = 'Temporada %s' % season
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseasons',
                             infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'episodios':
        itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                     action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))

    return itemlist

def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseasons(tempitem)

    return itemlist

def episodesxseasons(item):
    logger.info()

    itemlist = []

    data=get_source(item.url)
    data = data.replace('"','\'')

    patron="class='numerando'>%s - (\d+)</div><div class='episodiotitle'>.?<a href='([^']+)'>([^<]+)<" % item.infoLabels['season']
    matches = re.compile(patron, re.DOTALL).findall(data)

    infoLabels = item.infoLabels

    for scrapedepisode, scrapedurl, scrapedtitle in matches:

        infoLabels['episode'] = scrapedepisode
        url = scrapedurl
        title = '%sx%s - %s' % (infoLabels['season'], infoLabels['episode'], scrapedtitle)

        itemlist.append(Item(channel=item.channel, title= title, url=url, action='findvideos', type='tv',
                             infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def findvideos(item):
    logger.info()
    from lib import generictools
    itemlist = []
    data = get_source(item.url)
    data = data.replace("'",'"')
    patron = 'data-type="([^"]+)" data-post="(\d+)" data-nume="(\d+).*?img src=\"([^"]+)\"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for type, id, option, lang in matches:
        lang = scrapertools.find_single_match(lang, '.*?/flags/(.*?).png')
        quality = ''
        if lang not in IDIOMAS:
            lang = 'en'
        if not config.get_setting('unify'):
            title = ' [%s]' % IDIOMAS[lang]
        else:
            title = ''

        post = {'action': 'doo_player_ajax', 'post': id, 'nume': option, 'type':type}

        test_url = '%swp-admin/admin-ajax.php' % host
        new_data = httptools.downloadpage(test_url, post=post, headers={'Referer':item.url}).data
        test_url = scrapertools.find_single_match(new_data, "src='([^']+)'")
        if 'xyz' in test_url:
            new_data = get_source(test_url, item.url)
            patron = "addiframe\('([^']+)'"
            matches = scrapertools.find_multiple_matches(new_data, patron)

            for test_url in matches:
                if 'play.php' in test_url:
                    new_data = get_source(test_url)
                    enc_data = scrapertools.find_single_match(new_data, '(eval.*?)</script')
                    try:
                        dec_data = jsunpack.unpack(enc_data)
                    except:
                        pass
                    url = scrapertools.find_single_match(dec_data, 'src="([^"]+)"')
                elif 'embedvip' in test_url:
                    from lib import generictools
                    new_data = get_source(test_url)
                    try:
                        dejuiced = generictools.dejuice(new_data)
                    except:
                        pass
                    url = scrapertools.find_single_match(dejuiced, '"file":"([^"]+)"')
                if url != '':
                    itemlist.append(
                        Item(channel=item.channel, url=url, title='%s' + title, action='play', quality=quality,
                             language=IDIOMAS[lang], infoLabels=item.infoLabels))
        else:
            new_data = get_source(test_url, item.url)
            patron = 'data-embed="([^"]+)" data-issuer="([^"]+)" data-signature="([^"]+)"'
            matches = scrapertools.find_multiple_matches(new_data, patron)

            for st, vt, tk in matches:
                post = {'streaming':st, 'validtime':vt, 'token':tk}
                new_url = '%sedge-data/' % 'https://peliculonhd.net/'
                json_data = httptools.downloadpage(new_url, post=post, headers = {'Referer':test_url}).json
                try:
                    if 'peliculonhd' not in json_data['url']:
                        url = json_data['url']
                    else:
                        new_data = get_source(json_data['url'], test_url)
                        url = scrapertools.find_single_match(new_data, 'src: "([^"]+)"')
                        url = url.replace('download', 'preview')
                except:
                    url = ''
                if url != '':
                    itemlist.append(Item(channel=item.channel, url=url, title='%s'+title, action='play', quality=quality,
                                         language=IDIOMAS[lang], infoLabels=item.infoLabels))


    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Requerido para Filtrar enlaces

    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    itemlist = sorted(itemlist, key=lambda it: it.language)

    if item.contentType != 'episode':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                     action="add_pelicula_to_library", extra="findvideos", contentTitle=item.contentTitle))

    return itemlist

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto

    if texto != '':
        return search_results(item)
    else:
        return []

def search_results(item):
    logger.info()

    itemlist=[]

    data=get_source(item.url)

    patron = '<article>.*?<a href="([^"]+)">.*?<img src="([^"]+)" alt="([^"]+)".*?<span class="(tvshows|movies)".*?'
    patron += '"meta".*?"year">([^<]+)<(.*?)<p>([^<]+)</p>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumb, scrapedtitle, type, year, lang_data, scrapedplot in matches:

        title = scrapedtitle
        url = scrapedurl
        thumbnail = scrapedthumb.replace('-150x150', '')
        plot = scrapedplot
        language = get_language(lang_data)
        type = re.sub('shows|s', '', type)
        if language:
            action = 'findvideos'
        else:
            action = 'seasons'

        new_item=Item(channel=item.channel, title=title, url=url, thumbnail=thumbnail, plot=plot,
                             action=action, type=type, language=language, infoLabels={'year':year})
        if new_item.action == 'findvideos':
            new_item.contentTitle = new_item.title
        else:
            new_item.contentSerieName = new_item.title

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas']:
            item.url = host + 'ver/'
        elif categoria == 'infantiles':
            item.url = host + 'genero/animacion/'
        elif categoria == 'terror':
            item.url = host + 'genero/terror/'
        elif categoria == 'documentales':
            item.url = host + 'genero/terror/'
        item.type='movie'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
