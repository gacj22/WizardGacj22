# -*- coding: utf-8 -*-

import re, urllib

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb

host = 'https://retroseriestv.com/'


def mainlist(item):
    return mainlist_series(item)

def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title='Todas las series', action='list_all', url=host + 'seriestv/' ))

    itemlist.append(item.clone( title='Series por género', action='generos' ))
    itemlist.append(item.clone( title='Series por año de lanzamiento', action='anyos' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(host + 'seriestv/').data

    patron = '<li class="cat-item cat-item-[^"]+"><a href="([^"]+)">([^<]+)</a> <i>([^<]+)</i></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, title, cantidad in matches:
        if cantidad == '0': continue
        itemlist.append(item.clone( action="list_all", title='%s (%s)' % (title, cantidad), url=url ))

    return itemlist

def anyos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(host + 'seriestv/').data

    patron = '<a href="%slanzamiento/(\d+)/"' % host
    matches = re.compile(patron, re.DOTALL).findall(data)

    for year in matches:
        itemlist.append(item.clone( action="list_all", title=year, url=host+'lanzamiento/%s/' % year ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    if '<div class="dt_mainmeta">' in data: data = data.split('<div class="dt_mainmeta">')[0]

    matches = re.compile('<article(.*?)</article>', re.DOTALL).findall(data)
    for data_show in matches:
        thumb = scrapertools.find_single_match(data_show, ' src="([^"]+)')
        url, title = scrapertools.find_single_match(data_show, '<h3><a href="([^"]+)">([^<]+)')
        year = scrapertools.find_single_match(data_show, '<span>(\d{4})</span>')
        if not year: year = '-'
        plot = scrapertools.find_single_match(data_show, '<div class="texto">(.*?)</div>')
        
        itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, 
                                    contentType='tvshow', contentSerieName=title, 
                                    infoLabels={'year': year, 'plot': scrapertools.htmlclean(plot)} ))

    tmdb.set_infoLabels(itemlist)

    next_page = scrapertools.find_single_match(data, ' href="([^"]+)"\s*><span class="icon-chevron-right')
    if next_page:
        itemlist.append(item.clone( url=next_page, title='Siguiente >>' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    matches = re.compile("<span class='title'>Temporada (\d+)", re.DOTALL).findall(data)
    for numtempo in matches:
        itemlist.append(item.clone( action='episodios', title='Temporada %s' % numtempo, 
                                    contentType='season', contentSeason=numtempo ))
        
    tmdb.set_infoLabels(itemlist)

    return itemlist


# Si una misma url devuelve los episodios de todas las temporadas, definir rutina tracking_all_episodes para acelerar el scrap en trackingtools.
def tracking_all_episodes(item):
    return episodios(item)

def episodios(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    matches = re.compile("<li class='mark-\d+'><div class='imagen'>(.*?)</li>", re.DOTALL).findall(data)
    for data_epi in matches:
        # ~ logger.debug(data_epi)

        try:
            season, episode = scrapertools.find_single_match(data_epi, "<div class='numerando'>(\d+)\s*-\s*(\d+)")
        except:
            continue

        if item.contentSeason and item.contentSeason != int(season):
            continue

        thumb = scrapertools.find_single_match(data_epi, " src='([^']+)")
        url, title = scrapertools.find_single_match(data_epi, " href='([^']+)'>([^<]+)")
        titulo = '%sx%s %s' % (season, episode, title)

        itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb, 
                                    contentType='episode', contentSeason=season, contentEpisodeNumber=episode ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def detectar_server(servidor):
    #TODO? verificar servers
    srv = servidor.lower()
    if srv == 'waaw' or srv == 'netu': srv = 'netutv'
    return srv

def findvideos(item):
    logger.info()
    itemlist = []

    IDIOMAS = {'es':'Esp', 'mx':'Lat', 'ar':'Lat', 'pe':'Lat', 'en':'Eng', 'gb':'Eng', 'vose':'VOSE', 'vos':'VOS', 'fr':'Fra', 'jp':'Jap'}

    data = httptools.downloadpage(item.url).data

    patron = "data-type='([^']+)' data-post='(\d+)' data-nume='(\d+)'.*?<span class='title'>([^<]+).*?<span class='server'>([^.<]+).*?img src='([^']+)'"
    matches = re.compile(patron, re.DOTALL).findall(data)
    if not matches:
        patron = 'data-type="([^"]+)" data-post="(\d+)" data-nume="(\d+)".*?<span class="title">([^<]+).*?<span class="server">([^.<]+).*?img src=\'([^\']+)\''
        matches = re.compile(patron, re.DOTALL).findall(data)
    
    for dtype, dpost, dnume, titulo, servidor, lang in matches:
        lang = scrapertools.find_single_match(lang, '.*?/flags/(.*?)\.png')

        itemlist.append(Item( channel = item.channel, action = 'play', server = detectar_server(servidor),
                              title = '', dtype = dtype, dpost = dpost, dnume = dnume, 
                              language = IDIOMAS.get(lang, lang)
                       ))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    post = urllib.urlencode( {'action': 'doo_player_ajax', 'post': item.dpost, 'nume': item.dnume, 'type': item.dtype} )
    data = httptools.downloadpage(host + 'wp-admin/admin-ajax.php', post=post, headers={'Referer':item.url}).data

    url = scrapertools.find_single_match(data, "src='([^']+)'")

    if url.startswith(host):
        locationurl = httptools.downloadpage(url, follow_redirects=False, only_headers=True).headers.get('location', '')
        if locationurl != '':
            try:
                b64url = scrapertools.find_single_match(locationurl, "y=(.*)")
                if b64url != '': url = base64.b64decode(b64url)
                else: url = locationurl
            except:
                url = locationurl
        
    if url != '': 
        itemlist.append(item.clone(url = url))

    return itemlist



def search(item, texto):
    logger.info("texto: %s" % texto)
    itemlist = []

    try:
        data = httptools.downloadpage(host + '?s=' + texto.replace(" ", "+")).data
        if '<div class="dt_mainmeta">' in data: data = data.split('<div class="dt_mainmeta">')[0]

        matches = re.compile('<div class="result-item"><article>(.*?)</article>', re.DOTALL).findall(data)
        for data_show in matches:
            thumb = scrapertools.find_single_match(data_show, ' src="([^"]+)')
            url, title = scrapertools.find_single_match(data_show, '<div class="title"><a href="([^"]+)">([^<]+)')
            year = scrapertools.find_single_match(data_show, '<span class="year">(\d{4})</span>')
            if not year: year = '-'
            plot = scrapertools.find_single_match(data_show, '<p>(.*?)</p>').strip()
            
            itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, 
                                        contentType='tvshow', contentSerieName=title, 
                                        infoLabels={'year': year, 'plot': scrapertools.htmlclean(plot)} ))

        tmdb.set_infoLabels(itemlist)
        return itemlist

    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
