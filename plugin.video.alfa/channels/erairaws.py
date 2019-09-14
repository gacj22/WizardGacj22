# -*- coding: utf-8 -*-
# -*- Channel AnimeSpace -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib, urlparse

from core import httptools
from core import scrapertools
from core import servertools
from channelselector import get_thumb
from core import tmdb
from core.item import Item
from platformcode import logger, config
from channels import autoplay
from channels import filtertools
from channels import renumbertools

host = "https://www.erai-raws.info"


IDIOMAS = {'fr':'Francés', 'de':'Alemán',  'it': 'Italiano',
           'us': 'Inglés', 'br': 'Portugués', 'es': 'Español'
           }


list_language = IDIOMAS.values()

list_quality = ['1080p', '720p', '480p']
list_servers = ['directo', 'torrent']

p_main = ' según Idioma de Subs seleccionado'


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Nuevos Episodios",
                         plot= 'Nuevos episodios' + p_main,
                         action="new_episodes",
                         thumbnail='https://i.imgur.com/IexJg5R.png',
                         url=host + '/posts/'))

    itemlist.append(Item(channel=item.channel, title="Batch",
                        plot='Ultimas Temporadas o Packs de Episodios' + p_main,
                        action="new_episodes", not_post=True,
                        thumbnail='https://i.imgur.com/CzAGve1.png',
                        url=host + '/batch/'))

    itemlist.append(Item(channel=item.channel, title="Películas",
                         plot='Ultimas Películas, Especiales, Ovas..etc' + p_main,
                         action="new_episodes",
                         thumbnail='https://i.imgur.com/aYBo36W.png',
                         url=host + '/movies/',
                         ar_post='buscar=&from=&pinput=0&tipo%5B%5D=2&orden=0'))

    itemlist.append(Item(channel=item.channel, title="A-Z",
                         action="alpha",
                         thumbnail='https://i.imgur.com/vIRCKQq.png',
                         url=host + '/anime-list/',
                         ar_post='buscar=&from=&pinput=0&tipo%5B%5D=2&orden=0'))

    itemlist.append(Item(channel=item.channel, title="Buscar...",
                               action="search",
                               url=host + '/anime-list/',
                               thumbnail='https://i.imgur.com/ZVMl3NP.png'))

    autoplay.show_option(item.channel, itemlist)
    #itemlist = renumbertools.show_option(item.channel, itemlist)

    return itemlist


def get_source(url, post=None, host=host, get_url=False):
    logger.info()
    if not host in url:
        i = url.split('/')
        host = '%s/%s/%s' % (i[0], i[1], i[2])
    page = httptools.downloadpage(url, post=post, ignore_response_code=True)
    if page.code > 399:
        import base64
        headers = {'Referer': url}
        u = url.split(host)[1]
        u = base64.b64encode(u.encode('utf-8'))
        h = base64.b64encode(host.encode('utf-8'))
        url = 'https://ddgu.ddos-guard.net/ddgu/'
        post = urllib.urlencode({'u': u, 'h': h, 'p': ''})
        page = httptools.downloadpage(url, post=post, ignore_response_code=True, headers=headers)

    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", page.data)
    if get_url:
        url = page.url
        return data, url
    return data

def get_info(data, quality=False):
    logger.info()
    txt_info = "[COLOR gold]"
    if quality:
        txt_info = "[COLOR grey]"
    #list_data = []

    if quality:
        patron = '>(\d+p)x</a>'
    else:
        patron = 'flag-icon-(\w+)"'

    list_info = re.compile(patron, re.DOTALL).findall(data)

    for txt in list_info:
        if quality:
            txt_info += '[%s]' % txt
        else:
            txt_info += '[%s]' % IDIOMAS.get(txt, txt)
        #list_data.append(IDIOMAS.get(txt, txt))
    txt_info += '[/COLOR]'
    return list_info, txt_info

def folder_list(item):
    itemlist = []
    infoLabels = ''

    data, item.url = get_source(item.url, get_url=True)
    patron = '<li data-name="([^"]+)".*?href="([^"]+)".*?' #title, url
    patron += 'text-right">(.*?)</span>' #size

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedtitle, scrapedurl, info_s in matches:
        if len(scrapedtitle) < 10:
            continue
        title = re.sub('^\[.*?\]|\.\w{3}$', '', scrapedtitle)
        zanga = scrapertools.find_single_match(title, ' - (\d+.*)$')
        
        if zanga:
            title = 'Ep %s' % zanga
        
        

        if scrapedurl.startswith('?dir='):
            action = 'folder_list'
            folder = True

        
        else:
            action = 'play'
            folder = False
            title += '[%s]' % info_s
            if not item.d_host:
                item.d_host = re.sub('\?dir=.*', '', item.url)
            d_host = item.d_host.replace('?dir=', '')

            infoLabels = item.infoLabels
            if item.inforaws:
                infoLabels = item.inforaws
            infoLabels['season'] = 1
            infoLabels['episode'] = scrapertools.find_single_match(zanga, '(\d+)')
        if not item.d_host:
            d_host = item.url+'/'
        url = d_host+scrapedurl
        itemlist.append(Item(channel=item.channel, title=title,
                            url=url, action=action, folder=folder,
                            language = item.language,d_host=d_host,
                            contentSerieName=item.nom_serie,
                            inforaws=item.infoLabels,
                            infoLabels=infoLabels, server='directo'))




    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    return itemlist

def anime_list(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    if item.letra:
        pat = 'id="%s"(.*?)</div><h4' % item.letra
        if item.letra == 'Z':
            pat = 'id="Z"(.*?)</div></div>'
            
        data = scrapertools.find_single_match(data, pat)

    patron = 'button button5.*?href="([^"]+)".*?>([^<]+)<'#url, title
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        if not item.busq in scrapedtitle:
            continue
        url = item.url+scrapedurl
        itemlist.append(item.clone(title=scrapedtitle,
                        contentSerieName=scrapedtitle,
                        url=url,
                        action='episodios'))
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    return itemlist

def generos(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)
    patron = '(?s)<a class="block.*?href="([^"]+)">.*?'
    patron += '>(\d+).*?<img .*? src="([^"]+)".*?<p .*?>(.*?)</p>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, num, thumb, title in matches:
        titles = '%s [COLOR darkgrey](%s animes)[/COLOR]' % (title.strip(), num)
        thumb = urlparse.urljoin(host, thumb)
        itemlist.append(
            Item(channel=item.channel, action="list_all", title=titles,
                 url=url, thumbnail=thumb, plot=title))
    return itemlist

def search(item, texto):
    logger.info()
    matches = scrapertools.find_multiple_matches(texto, '([a-zA-Z]+)')

    for a in matches:
        texto = texto.replace(a, a.capitalize())

    item.busq = texto
    try:
        if texto != '':
            return anime_list(item)
        else:
            return []
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

def new_episodes(item):
    logger.info()
    itemlist = []
    language = 'VOS'
    sub_filter = config.get_setting('filter_subs', channel='erairaws')
    sub_choosen = list_language[sub_filter]

    data = get_source(item.url)
    
    patron = '<article.*?href=".*?>(.*?) - (\d+|.*?)</a>.*?' #title, ep_n
    patron += '_blank" href="(https://srv[^"]+)".*?Subtitles(.*?)<' #ddl, subs,
    patron += '/td>(.*?)</tbody>(.*?)</article>' #quality,torrents
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedtitle, epi, ddl, scrapedsub, scrapedquality, storrent in matches:
        urls = []
        urls_q = []
        urls.append(ddl)

        title = scrapedtitle
        scrapedtitle = re.sub('\((.*?)\)$', '', scrapedtitle)

        list_quality, quality = get_info(scrapedquality, quality=True)
        list_langs, langs = get_info(scrapedsub)

        for q in list_quality:
            patron = '<i>\[%sx\]</i>.*?<a href="([^"]+)"' % q
            torrent = scrapertools.find_single_match(storrent, patron)
            
            t_dom = urlparse.urlparse(torrent)[1]
            d_dom = urlparse.urlparse(ddl)[1]
            
            ddl_direct = torrent.replace(t_dom, d_dom)
            ddl_direct = re.sub('/Torrent|\.torrent$', '', ddl_direct)

            if not ddl_direct.endswith('.mkv'):
                ddl_direct = ddl_direct.replace('/%5BErai', '/?dir=%5BErai')

            urls.append(torrent)
            urls_q.append(ddl_direct)
            urls_q.append(torrent)

        if not sub_choosen in langs:
            continue
        if sub_filter == 5:
            language = 'VOSE'
        
        #TODO compatibilidad con unify..etc
        if 'Episodios' in item.title:
            title += ': 1x%s' % epi
        else:
            title += ': %s' % epi
        
        if not config.get_setting('unify'):
            title += ' %s[COLOR burlywood][Sub-%s][/COLOR]' % (quality, sub_choosen)
        

        itemlist.append(Item(channel=item.channel, title=title, url=urls, quality=list_quality,
                             action='findvideos', contentSerieName=scrapedtitle, language=language,
                             urls_q=urls_q))
    
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    #itemlist = filtertools.get_links(itemlist, item, list_language)
    
    return itemlist

def episodios(item):
    logger.info()
    itemlist = []
    language = 'VOS'
    sub_filter = config.get_setting('filter_subs', channel='erairaws')
    sub_choosen = list_language[sub_filter]
    infoLabels = item.infoLabels

    data = get_source(item.url)
    
    #TODO fix para primer item, y diferenciar tipo contenido
    patron = '<i class="fa fa-circle.*?href=".*?>(.*?) - (\d+|.*?)</a>.*?' #title, ep_n
    patron += '_blank" href="(https://srv[^"]+)".*?Subtitles(.*?)<' #ddl, subs,
    patron += '/td>(.*?)</tbody>(.*?)</article>' #quality,torrents
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedtitle, epi, ddl, scrapedsub, scrapedquality, storrent in matches:
        urls = []
        urls_q = []
        urls.append(ddl)

        title = scrapedtitle
        scrapedtitle = re.sub('\((.*?)\)$', '', scrapedtitle)

        list_quality, quality = get_info(scrapedquality, quality=True)
        list_langs, langs = get_info(scrapedsub)

        for q in list_quality:
            patron = '<i>\[%sx\]</i>.*?<a href="([^"]+)"' % q
            torrent = scrapertools.find_single_match(storrent, patron)
            
            t_dom = urlparse.urlparse(torrent)[1]
            d_dom = urlparse.urlparse(ddl)[1]
            
            ddl_direct = torrent.replace(t_dom, d_dom)
            ddl_direct = re.sub('/Torrent|\.torrent$', '', ddl_direct)
            if not ddl_direct.endswith('.mkv'):
                ddl_direct = ddl_direct.replace('/%5BErai', '/?dir=%5BErai')

            urls.append(torrent)
            urls_q.append(ddl_direct)
            urls_q.append(torrent)
            

        if not sub_choosen in langs:
            continue
        
        if sub_filter == 5:
            language = 'VOSE'
        #TODO compatibilidad con "auto-click", unify..etc
        if len(matches) == 1:
            title += ': %s %s(Sub-%s)' % (epi, quality, sub_choosen)
            item = item.clone(title=title, url=urls, quality=list_quality, urls_q=urls_q,
                        action='findvideos', contentSerieName=scrapedtitle, language=language)
            return findvideos(item)

        else:
            title = '1x%s %s[COLOR burlywood][Sub-%s][/COLOR]' % (epi, quality, sub_choosen)
            infoLabels['season'] = 1
            infoLabels['episode'] = scrapertools.find_single_match(epi, '(\d+)')
        

        itemlist.append(Item(channel=item.channel, title=title, url=urls, quality=list_quality,
                             action='findvideos', contentSerieName=scrapedtitle, language=language,
                             urls_q=urls_q, infoLabels=infoLabels))
    
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    #itemlist = filtertools.get_links(itemlist, item, list_language)
    itemlist.reverse()
    if matches and not itemlist:
        zanga = '[COLOR tomato]No hay enlaces con subtitulos en %s[/COLOR]' % str(list_language)
        from platformcode import platformtools
        return platformtools.dialog_ok('Information', zanga)

        #itemlist.append(item.clone(title=zanga, url='', action=''))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    url_list = item.urls_q

    logger.error(url_list[0])
    try:
        test = httptools.downloadpage(url_list[0], only_headers=True).url
    except:
        try:
            domain = urlparse.urlparse(url_list[0])[1]
            url_t = 'https://'+domain
            get_source(url_t)
            test = httptools.downloadpage(url_list[0], only_headers=True).url
        except:
            test = 'error'

    if 'error.' in test:
        url_list = item.url
    


    for url in url_list:
        if not url:
            continue
        server = 'torrent'
        action = 'play'

        title = server.capitalize()
        quality = scrapertools.find_single_match(url, '(\d+)p%')
        
        new_item = Item(channel=item.channel, title=title,
                                url=url, action=action,
                                language = item.language, plot=item.plot,
                                server=server, thumbnail=item.thumbnail)
        
        if not url.endswith('.torrent') and not url.startswith('mag'):
            
            if not url.endswith('.mkv'):
                new_item.server = ''
                new_item.action = 'folder_list'
                new_item.title = 'Directo [Folder]'
                new_item.nom_serie = item.contentSerieName

                #return folder_list(item)
            else:
                new_item.server = 'directo'
                new_item.title = new_item.server.capitalize()
                new_item.infoLabels=item.infoLabels

        else:
            new_item.infoLabels=item.infoLabels

        if quality:
            quality += 'p'
            new_item.quality = quality
            new_item.title += ' [%s]' % quality
        
        itemlist.append(new_item)

    itemlist.sort(key=lambda x:x.server)
    return itemlist

def play(item):
    if item.server == 'directo':
        item.url = httptools.get_url_headers(item.url, forced=True)

    return [item]

def alpha(item):
    itemlist = []
    w = '#ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    for i in w:
        itemlist.append(item.clone(title=i,
                        letra=i,
                        action='anime_list'))

    return itemlist
