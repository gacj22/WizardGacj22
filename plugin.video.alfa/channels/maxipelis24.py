# -*- coding: utf-8 -*-

import re

from channels import autoplay
from channels import filtertools
from core import tmdb
from core import servertools
from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

host = "https://maxipelis24.org/"

IDIOMAS = {'Latino': 'Latino', 'Sub':'VOSE', 'Subtitulado': 'VOSE', 'Español': 'CAST', 'Castellano':'CAST'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['rapidvideo', 'vidoza', 'openload', 'streamango', 'okru']


def mainlist(item):
    logger.info()
    itemlist = []
    
    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, title="Estrenos",
                         action="movies", url=host+'Categoria/estrenos',
                         thumbnail=get_thumb('premieres', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title="Agregadas Recientemente",
                         action="movies", url=host, thumbnail=get_thumb('recents', auto=True)))
    
    itemlist.append(Item(channel=item.channel, action="category", title="Año de Estreno",
                         url=host, cat='year', thumbnail=get_thumb('year', auto=True)))
    
    itemlist.append(Item(channel=item.channel, action="category", title="Géneros",
                         url=host, cat='genre', thumbnail=get_thumb('genres', auto=True)))
    
    itemlist.append(Item(channel=item.channel, action="category", title="Calidad",
                         url=host, cat='quality', thumbnail=get_thumb("quality", auto=True)))
    
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search",
                         url=host + "?s=", thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "?s=" + texto
    if texto != '':
        return movies(item)


def category(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    if item.cat == 'genre':
        data = scrapertools.find_single_match(
            data, '<h3>Géneros <span class="icon-sort">.*?</ul>')
        patron = '<li class="cat-item cat-item.*?<a href="([^"]+)".*?>([^<]+)<'
    elif item.cat == 'year':
        data = scrapertools.find_single_match(
            data, '<h3>Año de estreno.*?</div>')
        patron = 'li><a href="([^"]+)".*?>([^<]+).*?<'
    elif item.cat == 'quality':
        data = scrapertools.find_single_match(data, '<h3>Calidad.*?</div>')
        patron = 'li><a href="([^"]+)".*?>([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        itemlist.append(Item(channel=item.channel, action='movies',
                             title=scrapedtitle, url=scrapedurl, type='cat'))
    return itemlist


def movies(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<div id="mt.*?href="([^"]+)".*?'
    patron += '<img src="([^"]+)" alt="([^"]+)".*?'
    patron += '<span class="ttx">([^<]+).*?'
    patron += 'class="year">([^<]+)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, img, scrapedtitle, resto, year in matches:
        scrapedtitle = re.sub(r' \((\d+)\)', '', scrapedtitle)
        plot = scrapertools.htmlclean(resto).strip()

        #title = ' %s [COLOR red][%s][/COLOR]' % (scrapedtitle, quality)
        title = '%s [COLOR darkgrey](%s)[/COLOR]' % (scrapedtitle, year)
        itemlist.append(Item(channel=item.channel,
                             title=title,
                             url=scrapedurl,
                             action="findvideos",
                             plot=plot,
                             thumbnail=img,
                             contentTitle=scrapedtitle,
                             contentType="movie",
                             #quality=quality,
                             infoLabels={'year': year}))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    # Paginacion
    c_page, next_page = scrapertools.find_single_match(
            data, "<a class='current'>(\d+)</a>.*?href='([^']+)'")
    #n_page = int(c_page) +1
    if next_page:
            itemlist.append(item.clone(url=next_page, title=" Siguiente »"))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<div id="div(\d+)"><div class="movieplay".*?(?:iframe.*?src|IFRAME SRC)="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for ot, link in matches:

        data1 = scrapertools.find_single_match(data, '<ul class="idTabs">.*?</ul></div>')

        patron = '<a href="#div%s.*?>([^<]+)' % ot
        matches1 = re.compile(patron, re.DOTALL).findall(data1)
        for info in matches1:
            
            
            try:
                lang, quality = scrapertools.find_single_match(info.strip(), '.*?([a-zA-ZÑñ]+)\s([a-zA-Z\0-9\-]+)\sOnline$')
            except:
                lang, quality = scrapertools.find_single_match(info.strip(), 'nline ([a-zA-ZÑñ]+)\s(.*?)$')
            if "VIP" in lang:
                continue
            idioma = lang

        '''if 'ok.ru' in link:
            patron = '<div id="div.*?<div class="movieplay".*?(?:iframe.*?src|IFRAME SRC)="([^"]+)"'
            matches = re.compile(patron, re.DOTALL).findall(data)
            for link in matches:
                if not link.startswith("https"):
                    url = "https:%s" % link
                    title = '%s'
                    new_item = Item(channel=item.channel, title=title, url=url,
                                    action='play', language=IDIOMAS[idioma], infoLabels=item.infoLabels)
                    itemlist.append(new_item)

        if '/hideload/?' in link:
            id_letter = scrapertools.find_single_match(link, '?(\w)d')
            id_type = '%sd' % id_letter
            ir_type = '%sr' % id_letter
            id = scrapertools.find_single_match(link, '%s=(.*)' % id_type)
            base_link = scrapertools.find_single_match(
                link, '(.*?)%s=' % id_type)
            ir = id[::-1]
            referer = base_link+'%s=%s&/' % (id_type, ir)
            video_data = httptools.downloadpage('%s%s=%s' % (base_link, ir_type, ir), headers={'Referer': referer},
                                                follow_redirects=False)
            url = video_data.headers['location']
            title = '%s'
        else:
            patron = '<div id="div.*?<div class="movieplay".*?(?:iframe.*?src|IFRAME SRC)="([^"]+)"'
            matches = re.compile(patron, re.DOTALL).findall(data)
            for link in matches:
                url = link
                title = '%s'''
        url = link
        try:
            title = ' [%s]' % quality
        except:
            title= ''
        new_item = Item(channel=item.channel, title='%s'+title, url=url,
                        action='play', language=IDIOMAS.get(idioma, idioma), infoLabels=item.infoLabels)
        itemlist.append(new_item)
    itemlist = servertools.get_servers_itemlist(
        itemlist, lambda i: i.title % '%s [%s]' % (i.server.capitalize(), i.language))
    #itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    if itemlist:
        if config.get_videolibrary_support():
            itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="green",
                                 action="add_pelicula_to_library", url=item.url, thumbnail=item.thumbnail,
                                 contentTitle=item.contentTitle
                                 ))
    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist
