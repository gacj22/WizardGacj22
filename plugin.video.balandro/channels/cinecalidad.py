# -*- coding: utf-8 -*-

import re, urlparse

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, tmdb


def host_by_lang(lang=''):
    if lang == '': # si no se especifica idioma, obtenerlo de las preferencias de idioma del usuario
        pref_esp = config.get_setting('preferencia_idioma_esp', default='1')
        pref_lat = config.get_setting('preferencia_idioma_lat', default='2')
        lang = 'Esp' if pref_esp != 0 and pref_esp <= pref_lat else 'Lat'
        
    if lang == 'Lat': return 'https://www.cinecalidad.is/'
    if lang == 'Esp': return 'https://www.cinecalidad.is/espana/'
    if lang == 'Por': return 'https://www.cinemaqualidade.is/'
    return 'https://www.cinecalidad.is/'


def mainlist(item):
    return mainlist_pelis(item)

def mainlist_pelis(item):
    logger.info()
    itemlist = []
    
    itemlist.append(item.clone( title='Castellano', action='mainlist_pelis_lang', idioma='Esp' ))
    itemlist.append(item.clone( title='Latino', action='mainlist_pelis_lang', idioma='Lat' ))
    # ~ itemlist.append(item.clone( title='Portugués', action='mainlist_pelis_lang', idioma='Por' ))

    return itemlist


def mainlist_pelis_lang(item):
    logger.info()
    itemlist = []
    
    host = host_by_lang(item.idioma)
    itemlist.append(item.clone( title='Lista de películas', action='peliculas', url=host ))
    itemlist.append(item.clone( title='Destacadas', action='peliculas', url=host+'genero-peliculas/destacada/' ))
    itemlist.append(item.clone( title='Por Género', action='generos' ))
    itemlist.append(item.clone( title='Por Año', action='anyos' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    return itemlist

def generos(item):
    logger.info()
    itemlist = []

    # ~ item.url = host_by_lang(item.idioma)+'genero-peliculas/'
    item.url = host_by_lang(item.idioma)

    data = httptools.downloadpage(item.url).data
    # ~ patron = '<li id="menu-item-.*?" class="menu-item menu-item-type-taxonomy menu-item-object-category ' \
             # ~ 'menu-item-.*?"><a href="([^"]+)">([^<]+)<\/a></li>'
    patron = ' class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-[^"]*"><a href=([^>]+)>([^<]+)<\/a></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        url = urlparse.urljoin(item.url, scrapedurl)
        itemlist.append(item.clone( title=scrapedtitle, action='peliculas', url=url ))

    return sorted(itemlist, key=lambda it: it.title)


def anyos(item):
    logger.info()
    itemlist = []

    item.url = host_by_lang(item.idioma)+'peliculas-por-ano/'

    data = httptools.downloadpage(item.url).data
    # ~ patron = '<a href="([^"]+)">([^<]+)</a><br'
    patron = '<a href=([^>]+)>([^<]+)</a><br'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        url = urlparse.urljoin(item.url, scrapedurl)
        itemlist.append(item.clone( title=scrapedtitle, action='peliculas', url=url ))

    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    # ~ patron = '<div class="home_post_cont[^"]*">\s*<a href="([^"]+)">'
    # ~ patron += '<img width="[^"]*" height="[^"]*" src="([^"]+)" class="[^"]*" alt="[^"]*" title="([^"]+)"'
    # ~ patron += '.*?&lt;p&gt;(.*?)&lt;/p&gt;&lt;'
    patron = '<div class="home_post_cont[^"]*">\s*<a href=([^>]+)>'
    patron += '<img width=\d* height=\d* src=([^ ]+) class="[^"]*" alt="[^"]*" title="([^"]+)"'
    patron += '.*?&lt;p&gt;(.*?)&lt;/p&gt;&lt;'
    matches = re.compile(patron, re.DOTALL).findall(data)
    
    for url, thumb, title, plot in matches:
        title = re.sub('&lt;!--.*?--&gt;', '', title)
        m = re.match(r"^(.*?)\((\d+)\)$", title)
        if m: 
            title = m.group(1).strip()
            year = m.group(2)
        else:
            year = '-'

        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb,
                                    languages=item.idioma,
                                    contentType='movie', contentTitle=title, infoLabels={'year': year, 'plot': plot} ))

    tmdb.set_infoLabels(itemlist)

    # ~ next_page_link = scrapertools.find_single_match(data, "<link rel='next' href='([^']+)' />")
    next_page_link = scrapertools.find_single_match(data, "<link rel=next href=([^>]+)")
    if next_page_link:
        itemlist.append(item.clone( title='>> Página siguiente', url=next_page_link, action='peliculas' ))

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
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)

    dec_value = scrapertools.find_single_match(data, 'String\.fromCharCode\(parseInt\(str\[i\]\)-(\d+)\)')

    # Enlaces Online
    server_url = {'YourUpload': 'http://www.yourupload.com/embed/%s',
                  'Openload': 'https://openload.co/embed/%s',
                  'Streamango': 'https://streamango.com/embed/%s',
                  'RapidVideo': 'https://www.rapidvideo.com/e/%s',
                  'Fembed': 'https://www.fembed.com/v/%s',
                  'OkRu': 'http://ok.ru/videoembed/%s',
                  'YourUpload': 'http://www.yourupload.com/embed/%s',
                  'Verystream': 'https://verystream.com/e/%s',
                  'Gounlimited': 'https://gounlimited.to/embed-%s.html',
                  'Netu': 'https://netu.tv/watch_video.php?v=%s',
                  'Vidcloud': 'https://vidcloud.co/embed/%s',
                  'Vidoza': 'https://vidoza.net/embed-%s.html',
                  'Clipwatching': 'https://clipwatching.com/embed-%s.html',
                  'Mega': 'https://mega.nz/embed#!%s'}

    # ~ patron = ' target="_blank" class="link onlinelink" service="Online([^"]+)" data="([^"]+)'
    patron = ' target=_blank class="link onlinelink" service=Online([^ ]+) data="([^"]+)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for srv, encoded in matches:
        if srv in server_url:
            url = server_url[srv] % dec(encoded, dec_value)
            servidor = srv.lower()
            if servidor == 'netu': servidor = 'netutv'
            
            itemlist.append(Item(channel = item.channel, action = 'play', server = servidor,
                                 title = '', url = url,
                                 language = item.languages
                           ))

    # Enlaces Torrent
    patron = ' href="([^"]+)" target=_blank class=link rel=nofollow service=BitTorrent'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url in matches:
        itemlist.append(Item(channel = item.channel, action = 'play', server = 'torrent',
                             title = '', url = host_by_lang('Lat')+url[1:],
                             language = 'VOSE'
                       ))

    return itemlist

def play(item):
    logger.info()
    itemlist = []

    url = item.url
    if '/protect/v.php' in item.url:
        data = httptools.downloadpage(item.url).data
        # ~ logger.debug(data)
        url_torrent = scrapertools.find_single_match(data, 'value="(magnet.*?)"')
        if url_torrent != '': url = url_torrent

    itemlist.append(item.clone(url = url))
    
    return itemlist



def search(item, texto):
    logger.info()
    try:
        item.url = host_by_lang(item.idioma) + '?s=' + texto.replace(" ", "+")
        item.idioma = 'Esp' if '/espana/' in item.url else 'Lat' # Desde búsqueda global no hay idioma fijado
        return peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
