# -*- coding: utf-8 -*-

import re
import urlparse

from channels import renumbertools
from core import httptools
from core import jsontools
from core import servertools
from core import scrapertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channels import autoplay
from channels import filtertools


IDIOMAS = {'LAT': 'LAT','SUB': 'VOSE'}
list_language = IDIOMAS.values()
list_servers = ['directo', 'rapidvideo', 'streamango', 'yourupload', 'mailru', 'netutv', 'okru']
list_quality = ['default']


HOST = "https://animeflv.net/"

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()
    itemlist.append(Item(channel=item.channel, action="novedades_episodios", title="Últimos episodios",
                         url=HOST, thumbnail="https://i.imgur.com/w941jbR.png"))
    
    itemlist.append(Item(channel=item.channel, action="novedades_anime", title="Últimos animes",
                         url=HOST, thumbnail="https://i.imgur.com/hMu5RR7.png"))
    
    itemlist.append(Item(channel=item.channel, action="listado", title="Animes",
                         url=HOST + "browse?order=title", thumbnail='https://i.imgur.com/50lMcjW.png'))
    
    itemlist.append(Item(channel=item.channel, action="search_section", title="    Género",
                         url=HOST + "browse", thumbnail='https://i.imgur.com/Xj49Wa7.png',
                         extra="genre"))
    
    itemlist.append(Item(channel=item.channel, action="search_section", title="    Tipo",
                         url=HOST + "browse", thumbnail='https://i.imgur.com/0O5U8Y0.png',
                         extra="type"))
    
    itemlist.append(Item(channel=item.channel, action="search_section", title="    Año",
                         url=HOST + "browse", thumbnail='https://i.imgur.com/XzPIQBj.png',
                         extra="year"))
    
    itemlist.append(Item(channel=item.channel, action="search_section", title="    Estado",
                         url=HOST + "browse", thumbnail='https://i.imgur.com/7LKKjSN.png',
                         extra="status"))
    
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar...",
                         thumbnail='https://i.imgur.com/4jH5gpT.png'))
    
    itemlist = renumbertools.show_option(item.channel, itemlist)

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def get_source(url, patron=None):

    data = httptools.downloadpage(url).data
    data = re.sub(r"\n|\r|\t|\s{2}|-\s", "", data)
    
    if patron:
        data = scrapertools.find_single_match(data, patron)

    return data

def search(item, texto):
    logger.info()
    itemlist = []
    
    item.url = urlparse.urljoin(HOST, "api/animes/search")
    
    texto = texto.replace(" ", "+")
    post = "value=%s" % texto
    
    try:
        dict_data = httptools.downloadpage(item.url, post=post).json
        for e in dict_data:
            if e["id"] != e["last_id"]:
                _id = e["last_id"]
            else:
                _id = e["id"]
            url = "%sanime/%s/%s" % (HOST, _id, e["slug"])
            title = e["title"]
            #if "&#039;" in title:
            #    title = title.replace("&#039;","")
            #if "&deg;" in title:
            #    title = title.replace("&deg;","")
            thumbnail = "%suploads/animes/covers/%s.jpg" % (HOST, e["id"])
            new_item = item.clone(action="episodios", title=title, url=url, thumbnail=thumbnail)
            if e["type"] != "movie":
                new_item.contentSerieName = title
                new_item.context = renumbertools.context(item)
            else:
                new_item.contentType = "movie"
                new_item.contentTitle = title
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

    patron = 'id="%s_select"[^>]+>(.*?)</select>' % item.extra
    data = get_source(item.url, patron=patron)
    
    matches = re.compile('<option value="([^"]+)">(.*?)</option>', re.DOTALL).findall(data)
    
    for _id, title in matches:
        url = "%s?%s=%s&order=title" % (item.url, item.extra, _id)
        
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
    itemlist = []

    patr = '<h2>Últimos episodios</h2>.+?<ul class="ListEpisodios[^>]+>(.*?)</ul>'
    data = get_source(item.url, patron=patr)
    
    patron = '<a href="([^"]+)"[^>]+>.+?<img src="([^"]+)".+?"Capi">(.*?)</span>'
    patron += '<strong class="Title">(.*?)</strong>'
    
    matches = re.compile(patron, re.DOTALL).findall(data)
    
    for url, thumbnail, str_episode, show in matches:
        try:
            episode = int(str_episode.replace("Episodio ", ""))
        except ValueError:
            season = 1
            episode = 1
        else:
            season, episode = renumbertools.numbered_for_tratk(item.channel, item.contentSerieName, 1, episode)

        title = "%s: %sx%s" % (show, season, str(episode).zfill(2))
        url = urlparse.urljoin(HOST, url)
        thumbnail = urlparse.urljoin(HOST, thumbnail)

        new_item = Item(channel=item.channel, action="findvideos", title=title, url=url,
                        contentSerieName=show, thumbnail=thumbnail)

        itemlist.append(new_item)
    
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    
    return itemlist


def novedades_anime(item):
    logger.info()
    itemlist = []
    
    patr = '<ul class="ListAnimes[^>]+>(.*?)</ul>'
    data = get_source(item.url, patron=patr)
    

    patron = 'href="([^"]+)".+?<img src="([^"]+)".+?'
    patron += '<span class=.+?>(.*?)</span>.+?<h3.+?>(.*?)</h3>.+?'
    patron += '(?:</p><p>(.*?)</p>.+?)?</article></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    
    for url, thumbnail, _type, title, plot in matches:
        url = urlparse.urljoin(HOST, url)
        thumbnail = urlparse.urljoin(HOST, thumbnail)
        
        new_item = Item(channel=item.channel, action="episodios", title=title, url=url, thumbnail=thumbnail,
                        plot=plot)
        
        if _type != "Película":
            new_item.contentSerieName = title
            new_item.context = renumbertools.context(item)
        
        else:
            new_item.contentType = "movie"
            new_item.contentTitle = title
        
        itemlist.append(new_item)
    
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    
    return itemlist


def listado(item):
    logger.info()
    itemlist = []
    
    data = get_source(item.url)

    url_pagination = scrapertools.find_single_match(data, '<li class="active">.*?</li><li><a href="([^"]+)">')
    
    data = scrapertools.find_multiple_matches(data, '<ul class="ListAnimes[^>]+>(.*?)</ul>')
    data = "".join(data)
    
    matches = re.compile('<a href="([^"]+)">.+?<img src="([^"]+)".+?<span class=.+?>(.*?)</span>.+?<h3.*?>(.*?)</h3>'
                         '.*?</p><p>(.*?)</p>', re.DOTALL).findall(data)
    
    for url, thumbnail, _type, title, plot in matches:
        url = urlparse.urljoin(HOST, url)
        thumbnail = urlparse.urljoin(HOST, thumbnail)
        
        new_item = Item(channel=item.channel, action="episodios", title=title, url=url, thumbnail=thumbnail,
                        plot=plot)
        
        if _type == "Anime":
            new_item.contentSerieName = title
            new_item.context = renumbertools.context(item)
        
        else:
            new_item.contentType = "movie"
            new_item.contentTitle = title
        
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
    
    data = get_source(item.url)
    
    info = scrapertools.find_single_match(data, "anime_info = \[(.*?)\];")
    info = eval(info)
    
    episodes = eval(scrapertools.find_single_match(data, "var episodes = (.*?);"))
    
    infoLabels = item.infoLabels

    for episode in episodes:
        url = '%s/ver/%s/%s-%s' % (HOST, episode[1], info[2], episode[0])
        season = 1
        season, episodeRenumber = renumbertools.numbered_for_tratk(item.channel, item.contentSerieName, season, int(episode[0]))

        infoLabels['season'] = season
        infoLabels['episode'] = episodeRenumber
        
        title = '%sx%s Episodio %s' % (season, str(episodeRenumber).zfill(2), episodeRenumber)
        
        itemlist.append(item.clone(title=title, url=url, action='findvideos', 
                                    contentSerieName=item.contentSerieName, infoLabels=infoLabels))
    
    itemlist = itemlist[::-1]
    
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel, title="Añadir esta serie a la videoteca", url=item.url,
                             action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))
    
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    
    return itemlist


def findvideos(item):
    logger.info()
    
    from core import jsontools
    itemlist = []
    
    data = get_source(item.url)

    videos = scrapertools.find_single_match(data, 'var videos = (.*?);')
    
    videos_json = jsontools.load(videos)
    
    for video_lang in videos_json.items():
        language = IDIOMAS.get(video_lang[0], video_lang[0])
        matches = scrapertools.find_multiple_matches(str(video_lang[1]), "code': '(.*?)'")
        
        lang = " [COLOR=grey](%s)[/COLOR]" % language
        for source in matches:
            url = source
            if 'redirector' in source:
                new_data = httptools.downloadpage(source).data
                url = scrapertools.find_single_match(new_data, 'window.location.href = "([^"]+)"')
            elif 'animeflv.net/embed' in source:
                source = source.replace('embed', 'check')
                new_data = httptools.downloadpage(source).data
                json_data = jsontools.load(new_data)
                try:
                    url = json_data['file']
                except:
                    continue
            #Parche por error tipografico en web(RV)
            elif 'e/http' in source:
                url = url.split('/e/')[1]

            itemlist.append(Item(channel=item.channel, url=url, title='%s'+lang, 
                                action='play', infoLabels=item.infoLabels, language=language))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist
