# -*- coding: utf-8 -*-
# -*- Channel PoseidonHD -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib
from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from channels import filtertools
from channels import autoplay
from platformcode import config, logger


IDIOMAS = {'mx': 'Latino', 'dk':'Latino', 'es': 'Castellano', 'en': 'VOSE', 'gb':'VOSE', 'de':'Alemán'}
list_language = IDIOMAS.values()

list_quality = ['HD', 'SD', 'CAM']

list_servers = [
    'directo',
    'gvideo',
    'openload',
    'streamango',
    'rapidvideo'
]

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'poseidonhd')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'poseidonhd')

host = 'https://poseidonhd.co/'

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title='Peliculas', action='menu_movies',
                         thumbnail= get_thumb('movies', auto=True)))
    itemlist.append(Item(channel=item.channel, title='Series', url=host+'tvshows', action='list_all', type='tvshows',
                         thumbnail= get_thumb('tvshows', auto=True)))
    itemlist.append(
        item.clone(title="Buscar", action="search", url=host + '?s=', thumbnail=get_thumb("search", auto=True),
                   extra='movie'))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def menu_movies(item):
    logger.info()

    itemlist=[]

    itemlist.append(Item(channel=item.channel, title='Todas', url=host + 'movies', action='list_all',
                         thumbnail=get_thumb('all', auto=True), type='movies'))
    itemlist.append(Item(channel=item.channel, title='Genero', action='section',
                         thumbnail=get_thumb('genres', auto=True), type='movies'))
    itemlist.append(Item(channel=item.channel, title='Por Año', action='section',
                         thumbnail=get_thumb('year', auto=True), type='movies'))

    return itemlist

def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
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
    data = get_source(host)

    if 'Genero' in item.title:
        patron = '<li class="cat-item cat-item-\d+"><a href="([^"]+)">(.*?)/i>'
    elif 'Año' in item.title:
        patron = '<li><a href="(.*?release.*?)">(.*?)</a>'
    elif 'Calidad' in item.title:
        patron = 'menu-item-object-dtquality menu-item-\d+"><a href="([^"]+)">(.*?)</a>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle
        plot=''
        if 'Genero' in item.title:
            quantity =  scrapertools.find_single_match(scrapedtitle,'</a> <i>(.*?)<')
            title = scrapertools.find_single_match(scrapedtitle,'(.*?)</')
            title = title
            plot = '%s elementos' % quantity.replace('.','')
        else:
            title = scrapedtitle
        if title not in duplicados:
            itemlist.append(Item(channel=item.channel, url=scrapedurl, title=title, plot=plot, action='list_all',
                                 type=item.type))
            duplicados.append(title)

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    if item.type ==  'movies':
        patron = '<article id="post-\d+" class="item movies"><div class="poster"><img src="([^"]+)" alt="([^"]+)">.*?'
        patron += 'quality">([^<]+)</span> <\/div><a href="([^"]+)">.*?'
        patron += '<\/h3><span>([^>]+)<\/span><\/div>.*?flags(.*?)metadata'
        matches = re.compile(patron, re.DOTALL).findall(data)

        for scrapedthumbnail, scrapedtitle, quality, scrapedurl, year, lang_data in matches:


            title = '%s [%s] [%s]' % (scrapedtitle, year, quality)
            contentTitle = scrapedtitle
            thumbnail = scrapedthumbnail
            url = scrapedurl
            language = get_language(lang_data)

            itemlist.append(item.clone(action='findvideos',
                            title=title,
                            url=url,
                            thumbnail=thumbnail,
                            contentTitle=contentTitle,
                            language=language,
                            quality=quality,
                            infoLabels={'year':year}))

    elif item.type ==  'tvshows':
        patron = '<article id="post-\d+" class="item tvshows"><div class="poster"><img src="([^"]+)" alt="([^"]+)">.*?'
        patron += '<a href="([^"]+)">.*?<\/h3><span>([^<]+)<\/span><\/div>'
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
                            infoLabels={'year':year}))

    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    #  Paginación

    url_next_page = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)" />')
    if url_next_page:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, action='list_all'))

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

    if config.get_videolibrary_support() and len(itemlist) > 0:
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
    patron='class="numerando">%s - (\d+)</div><div class="episodiotitle"><a href="([^"]+)">(.*?)<' % item.infoLabels['season']
    matches = re.compile(patron, re.DOTALL).findall(data)

    infoLabels = item.infoLabels

    for scrapedepisode, scrapedurl, scrapedtitle in matches:

        infoLabels['episode'] = scrapedepisode
        url = scrapedurl
        title = '%sx%s - %s' % (infoLabels['season'], infoLabels['episode'], scrapedtitle)

        itemlist.append(Item(channel=item.channel, title= title, url=url, action='findvideos', infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def findvideos(item):
    logger.info()
    subs = ''
    itemlist = []
    
    data = get_source(item.url)
    selector_url = scrapertools.find_multiple_matches(data, 'class="metaframe rptss" src="([^"]+)"')

    for lang in selector_url:
        data = get_source('https:'+lang)
        urls = scrapertools.find_multiple_matches(data, 'data-playerid="([^"]+)">')
        lang = scrapertools.find_single_match(lang, 'lang=(.*)?')
        language = IDIOMAS[lang]

        if language == 'VOSE':
            sub = scrapertools.find_single_match(str(urls), "sub=([^']+)")
            try:
                subs = urllib.unquote(sub)
            except:
                subs = sub

        if item.contentType == 'episode':
            quality = 'SD'
        else:
            quality = item.quality

        for url in urls:

            if 'index' in url:
                try:
                    file_id = scrapertools.find_single_match(url, 'file=(.*?)&')
                    post = {'link': file_id}
                    post = urllib.urlencode(post)
                    hidden_url = 'https://streamango.poseidonhd.co/repro/plugins/gkpluginsphp.php'
                    dict_vip_url = httptools.downloadpage(hidden_url, post=post).json
                    url = dict_vip_url['link']
                    if 'hls1.openloadpremium' in url:
                        continue

                except:
                    continue
            else:
                try:

                    if 'openload' in url:
                        file_id = scrapertools.find_single_match(url, 'h=(\w+)')
                        post = {'h': file_id}
                        post = urllib.urlencode(post)
                        hidden_url = 'https://streamango.poseidonhd.co/repro/openload/api.php'
                        json_data = httptools.downloadpage(hidden_url, post=post, follow_redirects=False).json
                        url = json_data.get('url', '')
                        #url = scrapertools.find_single_match(data_url, "VALUES \('[^']+','([^']+)'")
                        if not url:
                            continue
                    elif 'goto.php' in url:
                        file_id = scrapertools.find_single_match(url, 'url=(\w+)')
                        post = {'url': file_id}
                        post = urllib.urlencode(post)
                        hidden_url = 'https://streamango.poseidonhd.co/repro/r.php'
                        data_url = httptools.downloadpage(hidden_url, post=post, follow_redirects=False)
                        url = data_url.headers['location']
                    
                    else:
                        new_data = httptools.downloadpage('https:'+url).data
                        file_id = scrapertools.find_single_match(new_data, 'value="([^"]+)"')
                        post = {'url': file_id}
                        post = urllib.urlencode(post)
                        hidden_url = 'https://streamango.poseidonhd.co/repro/r.php'
                        data_url = httptools.downloadpage(hidden_url, post=post, follow_redirects=False)
                        url = data_url.headers['location']
                except:
                    continue
            url = url.replace(" ", "%20")
            itemlist.append(item.clone(title = '[%s] [%s]', url=url, action='play',
                            language=language, quality=quality, subtitle=subs))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % (x.server.capitalize(), x.language))

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
    patron = '<article>.*?<a href="([^"]+)"><img src="([^"]+)" alt="([^"]+)" />.*?meta.*?year">([^<]+)<(.*?)<p>(.*?)</p>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumb, scrapedtitle, year, lang_data, scrapedplot in matches:

        title = scrapedtitle
        url = scrapedurl
        thumbnail = scrapedthumb
        plot = scrapedplot
        language = get_language(lang_data)
        if language:
            action = 'findvideos'
        else:
            action = 'seasons'

        new_item=Item(channel=item.channel, title=title, url=url, thumbnail=thumbnail, plot=plot,
                             action=action,
                             language=language, infoLabels={'year':year})
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
            item.url = host + 'movies'
        elif categoria == 'infantiles':
            item.url = host + 'genre/animacion/'
        elif categoria == 'terror':
            item.url = host + 'genre/terror/'
        item.type='movies'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
