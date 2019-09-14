# -*- coding: utf-8 -*-
# -*- Channel VeryStream Movies -*-
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
from channels import autoplay
from platformcode import config, logger

list_quality = []

list_servers = ['verystream', 'gounlimited', 'openload',
                'vidlox', 'flix555', 'clipwatching',
                'streamango', 'xstream']


host = 'https://verystreamtv.com/'

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title='Peliculas', action='menu_movies',
                         thumbnail= get_thumb('movies', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title='Series', url=host+'tvseries/',
                         action='list_all',
                         thumbnail= get_thumb('tvshows', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search",
                         url=host + '?s=', thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def menu_movies(item):
    logger.info()

    itemlist=[]

    itemlist.append(Item(channel=item.channel, title='Últimas', url=host + 'movies', action='list_all',
                         thumbnail=get_thumb('last', auto=True)))
    itemlist.append(Item(channel=item.channel, title='Genero', action='section',
                         thumbnail=get_thumb('genres', auto=True)))
    itemlist.append(Item(channel=item.channel, title='Por Año', action='section',
                         thumbnail=get_thumb('year', auto=True)))

    return itemlist

def get_source(url, post=None):
    logger.info()
    data = httptools.downloadpage(url, post=post).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


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
            itemlist.append(Item(channel=item.channel, url=scrapedurl, title=title,
                                 plot=plot, action='list_all'))
            duplicados.append(title)

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    patron = '<article id="post-(\d+)" class="item ([^"]+)">.*?'
    patron += '<img src="([^"]+)" alt="([^"]+)">.*?'
    patron += 'star2"></span> ([^<]+)</div>.*?<a href="([^"]+)">.*?'
    patron += '<span>(\d{4})</span>.*?"texto">([^<]+)</div>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for v_id, typo, thumbnail, scrapedtitle, rating, url, year, plot in matches:

        title = re.sub(r'\s*\((\d{4})\)$', '', scrapedtitle)
        contentTitle = title
        
        if not config.get_setting('unify'):
            rcolor = color_rating(rating)
            title += ' [COLOR grey](%s)[/COLOR] [COLOR %s](%s)[/COLOR]' % (
                        year, rcolor, rating)

        thumbnail = re.sub("(w\d+/)", "original/", thumbnail)

        new_item = Item(channel=item.channel,
                        title=title,
                        url=url,
                        thumbnail=thumbnail,
                        plot=plot,
                        v_id=v_id,
                        language='VO',
                        infoLabels = {'year':year})

        if typo == 'movies':
            new_item.action = 'findvideos'
            new_item.contentTitle = contentTitle
        
        else:
            new_item.action = 'seasons'
            new_item.contentSerieName = contentTitle

        itemlist.append(new_item)

    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    #  Paginación

    url_next_page = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)" />')
    if url_next_page:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, action='list_all'))

    return itemlist

def seasons(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    patron = "class='title'>Season (\d+)"
    matches = re.compile(patron, re.DOTALL).findall(data)

    infoLabels = item.infoLabels
    for season in matches:
        infoLabels['season']=season
        title = 'Season %s' % season
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseasons',
                             infoLabels=infoLabels, v_id=item.v_id))
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
    infoLabels = item.infoLabels

    data = get_source(item.url)

    if not item.v_id:
        item.v_id = scrapertools.find_single_match(data,'data-id="(\d+)"')
    
    patron = "class='numerando'>%s " % item.infoLabels['season']
    patron += "- (\d+)</div>.*?<a href='([^']+)'>(.*?)<"
    
    matches = re.compile(patron, re.DOTALL).findall(data)

    

    for scrapedepisode, url, scrapedtitle in matches:

        infoLabels['episode'] = scrapedepisode

        title = '%sx%s - %s' % (infoLabels['season'], infoLabels['episode'], scrapedtitle)

        itemlist.append(Item(channel=item.channel, title= title, url=url,
                             action='findvideos', v_id=item.v_id, infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def findvideos(item):
    logger.info()

    servers = {'xstream': 'xstreamcdn'}
    server_url = {'verystream': 'https://verystream.com/e/%s',
                  'gounlimited': 'https://gounlimited.to/embed-%s.html',
                  'openload': 'https://openload.co/embed/%s',
                  'vidcloud': 'https://vidcloud.icu/load.php?id=%s',
                  'vidlox': 'https://vidlox.me/embed-%s.html',
                  'flix555': 'https://flix555.com/embed-%s.html',
                  'clipwatching': 'https://clipwatching.com/embed-%s.html',
                  'streamango': 'https://streamango.com/embed/%s',
                  'xstream': 'https://www.xstreamcdn.com/v/%s'}

    itemlist = []


    if not item.v_id:
        page = get_source(item.url)
        page = re.sub('"|\'', '', page)
        item.v_id = scrapertools.find_single_match(page,'data-id=(\d+)')
    
    if not '/movies/' in item.url:
        ep = item.infoLabels['episode']
        ses = item.infoLabels['season']
        
        url = '%swp-content/themes/dooplay/vs_player.php?id=%s&tv=1&s=%s&e=%s' % (
                host, item.v_id, ses, ep)
    else:
        url = '%swp-content/themes/dooplay/vs_player.php?id=%s&tv=0&s=0&e=0' % (host, item.v_id)
    
    url_spider = httptools.downloadpage(url).url
    url_oload1 = httptools.downloadpage(url_spider, headers={'Referer': url_spider}).url
    url_oload = re.sub('video/(.*)', 'watch/', url_oload1)
    
    data = httptools.downloadpage(url_oload, headers={'Referer': url_oload1}).data

    if 'Video not found' in data:
        title = '[COLOR tomato][B]Aún no hay enlaces disponibles para este video[/B][/COLOR]'
        itemlist.append(item.clone(title = title, action=''))
        return itemlist
    matches = scrapertools.find_multiple_matches(data, 'data-id="([^"]+)">([^<]+)')

    for id_, server in matches:

        title = '[COLOR yellowgreen]%s[/COLOR]' % server.capitalize()
        url = server_url.get(server, '')
        if url:
            url = url % id_
        server = servers.get(server, server)
        itemlist.append(item.clone(title = title, url=url, action='play',
                            language='VO', server=server))

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)


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
    patron = '<article>.*?<a href="([^"]+)"><img src="([^"]+)" alt="([^"]+)" />'
    patron += '<span class="([^"]+)".*?IMDb (.*?)</.*?year">([^<]+)<.*?<p>(.*?)</p>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, scrapedthumb, scrapedtitle, typo, rating, year, plot in matches:

        title = re.sub(r'\s*\((\d{4})\)$', '', scrapedtitle)
        contentTitle = title
        
        if not config.get_setting('unify'):
            rcolor = color_rating(rating)
            title += ' [COLOR grey](%s)[/COLOR] [COLOR %s](%s)[/COLOR]' % (
                        year, rcolor, rating)

        
        thumbnail = re.sub("(w\d+/)", "original/", scrapedthumb)
        
        new_item=Item(channel=item.channel, title=title, url=url, 
                      thumbnail=thumbnail, plot=plot,
                      language='VO', infoLabels={'year':year})
        
        if typo == 'movies':
            new_item.contentTitle = contentTitle
            new_item.action = 'findvideos'
        
        else:
            new_item.contentSerieName = contentTitle
            new_item.action = 'seasons'
            if not config.get_setting('unify'):
                new_item.title += '[COLOR blue] (Serie)[/COLOR]'

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def color_rating(rating):
    try:
        rating_f = float(rating)
        if rating_f < 5: color = "tomato"
        elif rating_f >= 7: color = "palegreen"
        else: color = "ivory"
    except:
        color = "ivory"
    return color