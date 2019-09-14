# -*- coding: utf-8 -*-

import re
import urlparse
from channels import renumbertools
from core import httptools
from core import scrapertools
from core import tmdb
from core.item import Item
from platformcode import logger
from channels import autoplay

IDIOMAS = {'VOSE': 'VOSE'}
list_language = IDIOMAS.values()
list_servers = ['directo']
list_quality = ['default']


HOST = "https://animeflv.ru/"


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()
    itemlist.append(Item(channel=item.channel, action="novedades_episodios", title="Últimos episodios",
                         url=HOST, thumbnail="https://i.imgur.com/w941jbR.png"))

    itemlist.append(Item(channel=item.channel, action="novedades_anime", title="Últimos animes",
                         url=HOST, thumbnail="https://i.imgur.com/hMu5RR7.png"))

    itemlist.append(Item(channel=item.channel, action="listado", title="Animes",
                         url=HOST + "animes/nombre/lista", thumbnail='https://i.imgur.com/50lMcjW.png'))

    itemlist.append(Item(channel=item.channel, action="search_section",
                         title="Géneros", url=HOST + "animes",
                         extra="genre", thumbnail='https://i.imgur.com/Xj49Wa7.png'))

    itemlist.append(Item(channel=item.channel, action="search", title="Buscar...",
                         thumbnail='https://i.imgur.com/4jH5gpT.png'))


    itemlist = renumbertools.show_option(item.channel, itemlist)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def clean_title(title):
    year_pattern = r'\([\d -]+?\)'
    year_pattern += '|(\d{4})$'
    year_pattern += '|(TV)$'
    return re.sub(year_pattern, '', title).strip()


def search(item, texto):
    logger.info()
    itemlist = []
    item.url = urlparse.urljoin(HOST, "search_suggest")
    texto = texto.replace(" ", "+")
    post = "value=%s" % texto

    try:
        dict_data = httptools.downloadpage(item.url, post=post).json
        for e in dict_data:
            title = clean_title(scrapertools.htmlclean(e["name"]))
            url = e["url"]
            plot = e["description"]
            thumbnail = e["thumb"]
            new_item = item.clone(action="episodios", title=title, url=url, plot=plot, thumbnail=thumbnail)
            if "Pelicula" in e["genre"]:
                new_item.contentType = "movie"
                new_item.contentTitle = title
            else:
                new_item.contentSerieName = title
                new_item.context = renumbertools.context(item)
            itemlist.append(new_item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
    
    tmdb.set_infoLabels(itemlist, seekTmdb=True)

    return itemlist


def search_section(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)
    patron = 'id="%s_filter"[^>]+><div class="inner">(.*?)</div></div>' % item.extra
    data = scrapertools.find_single_match(data, patron)
    matches = re.compile('<a href="([^"]+)"[^>]+>(.*?)</a>', re.DOTALL).findall(data)
    for url, title in matches:
        url = "%s/nombre/lista" % url
        itemlist.append(Item(channel=item.channel, action="listado", title=title, url=url,
                             context=renumbertools.context(item)))
    return itemlist


def newest(categoria):
    itemlist = []
    if categoria == 'anime':
        itemlist = novedades_episodios(Item(url=HOST))
    return itemlist


def novedades_episodios(item):
    logger.info()
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)
    data = scrapertools.find_single_match(data, '<ul class="ListEpisodios[^>]+>(.*?)</ul>')
    matches = re.compile('href="([^"]+)"[^>]+>.+?<img src="([^"]+)".+?"Capi">(.*?)</span>'
                         '<strong class="Title">(.*?)</strong>', re.DOTALL).findall(data)
    itemlist = []
    for url, thumbnail, str_episode, show in matches:
        try:
            episode = int(str_episode.replace("Ep. ", ""))
        except ValueError:
            season = 1
            episode = 1
        else:
            season, episode = renumbertools.numbered_for_tratk(item.channel, item.contentSerieName, 1, episode)
        show = clean_title(show)
        title = "%s: %sx%s" % (show, season, str(episode).zfill(2))
        url = urlparse.urljoin(HOST, url)
        thumbnail = urlparse.urljoin(HOST, thumbnail)
        new_item = Item(channel=item.channel, action="findvideos", title=title, url=url, contentSerieName=show, thumbnail=thumbnail,
                        contentTitle=title)
        itemlist.append(new_item)
    
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    
    return itemlist


def novedades_anime(item):
    logger.info()
    itemlist = []
    
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)
    data = scrapertools.find_single_match(data, '<ul class="ListAnimes[^>]+>(.*?)</ul>')
    
    matches = re.compile('<img src="([^"]+)".+?<a href="([^"]+)">(.*?)</a>', re.DOTALL).findall(data)
    
    for thumbnail, url, title in matches:
        url = urlparse.urljoin(HOST, url)
        thumbnail = urlparse.urljoin(HOST, thumbnail)
        title = clean_title(title)
        
        new_item = Item(channel=item.channel, action="episodios", title=title, url=url, thumbnail=thumbnail,
                        contentTitle=title)
        new_item.contentSerieName = title
        new_item.context = renumbertools.context(item)
        
        itemlist.append(new_item)
    
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    
    return itemlist


def listado(item):
    logger.info()
    
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)
    
    url_pagination = scrapertools.find_single_match(data, '<li class="current">.*?</li>[\s]<li><a href="([^"]+)">')
    
    data = scrapertools.find_single_match(data, '</div><div class="full">(.*?)<div class="pagination')
    
    matches = re.compile('<img.+?src="([^"]+)".+?<a href="([^"]+)">(.*?)</a>.+?'
                         '<div class="full item_info genres_info">(.*?)</div>.+?class="full">(.*?)</p>',
                         re.DOTALL).findall(data)
    itemlist = []
    for thumbnail, url, title, genres, plot in matches:
        title = clean_title(title)
        url = urlparse.urljoin(HOST, url)
        thumbnail = urlparse.urljoin(HOST, thumbnail)
        new_item = Item(channel=item.channel, action="episodios", title=title, url=url, thumbnail=thumbnail,
                        contentTitle=title, plot=plot, )
        if "Pelicula Anime" in genres:
            new_item.contentType = "movie"
            new_item.contentTitle = title
        else:
            new_item.contentSerieName = title
            new_item.context = renumbertools.context(item)
        itemlist.append(new_item)
    if url_pagination:
        url = urlparse.urljoin(HOST, url_pagination)
        title = ">> Pagina Siguiente"
        itemlist.append(Item(channel=item.channel, action="listado", title=title, url=url))
    
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    infoLabels = item.infoLabels
    
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)
    
    if item.plot == "":
        item.plot = scrapertools.find_single_match(data, 'Description[^>]+><p>(.*?)</p>')
    
    data = scrapertools.find_single_match(data, '<div class="Sect Episodes full">(.*?)</div>')
    matches = re.compile('<a href="([^"]+)"[^>]+>(.+?)</a', re.DOTALL).findall(data)
    
    for url, title in matches:
        title = title.strip()
        url = urlparse.urljoin(item.url, url)
        thumbnail = item.thumbnail
        try:
            episode = int(scrapertools.find_single_match(title, "Episodio (\d+)"))
        except ValueError:
            season = 1
            episode = 1
        else:
            season, episode = renumbertools.numbered_for_tratk(item.channel, item.contentSerieName, 1, episode)
        
        infoLabels['season'] = season
        infoLabels['episode'] = episode

        title = "%s: %sx%s" % (item.title, season, str(episode).zfill(2))
        
        itemlist.append(item.clone(action="findvideos", title=title, url=url, thumbnail=thumbnail,
                                   contentTitle=title, fanart=thumbnail, contentType="episode",
                                   infoLabels=infoLabels, contentSerieName=item.contentSerieName,))
    itemlist.reverse()
    
    tmdb.set_infoLabels(itemlist, seekTmdb=True)

    return itemlist

def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, 'Server</span>(.*?)choose_quality')
    matches = scrapertools.find_multiple_matches(bloque, '<option value="([^"]+)"')
    headers = {"Referer" : item.url}

    for url in matches:
        xserver = scrapertools.find_single_match(url, 's=([a-zA-Z0-9]+)')
        source = HOST + "get_video_info_v2?s=%s" % xserver
        #TODO reactivar despues de resolver problema Hydrax
        if xserver == 'hserver':
            continue
        link = get_link(source, url)
        if link:
            itemlist.append(Item(channel=item.channel, action="play", url=link, 
                            title=xserver.capitalize(),plot=item.plot, thumbnail=item.thumbnail,
                            contentTitle=item.title, language='VOSE', server="directo"))
    #~itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    return itemlist

def get_link(url, referer):
    logger.info()
    itemlist = []
    
    headers={"Referer" : referer}
    _id = scrapertools.find_single_match(referer, 'ver/([^/]+)/')
    post = "embed_id=%s" % _id

    
    dict_data = httptools.downloadpage(url, post=post,  headers=headers).json
    frame_src = scrapertools.find_single_match(dict_data["value"], 'iframe src="([^"]+)"')
    
    try:
        new_data = httptools.downloadpage(frame_src, headers=headers).data
    except:
        logger.error('Problema con headers???')
        return ''
   
    #TODO descurbir como reproducir esta lista en kodi
    '''if 'hydrax.net' in new_data:
        slug = scrapertools.find_single_match(new_data, '"slug","value":"([^"]+)"')
        post = "slug=%s&dataType=mp4" % slug
        ua = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Mobile Safari/537.36"
        
        data = httptools.downloadpage("https://multi.hydrax.net/guest", post=post, headers={"User-Agent": ua}).data

        url = scrapertools.find_single_match(data, '"link":"([^"]+)"')
        url += '|User-Agent=%s' % ua
        
        return url'''

    url = scrapertools.find_single_match(new_data, '(?:"file":|var urlVideo = )"([^"]+)"')

    url = url.replace("\\","")
    url += "|User-Agent=%s" % httptools.get_user_agent()
        
    return url
