# -*- coding: utf-8 -*-
# -*- Channel Cuevana 3 -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib
from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb, jsontools
from core.item import Item
from platformcode import config, logger
from channels import autoplay
from channels import filtertools


host = 'http://www.cuevana3.com/'

IDIOMAS = {'Latino': 'LAT', 'Español': 'CAST', 'Subtitulado':'VOSE'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['fastplay', 'rapidvideo', 'streamplay', 'flashx', 'streamito', 'streamango', 'vidoza']


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="Todas", action="list_all", url=host+'peliculas',
                         thumbnail=get_thumb('all', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Estrenos", action="list_all", url=host+'estrenos',
                         thumbnail=get_thumb('premieres', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Mas vistas", action="list_all", url=host+'peliculas-mas-vistas',
                         thumbnail=get_thumb('more watched', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Mas votadas", action="list_all", url=host+'peliculas-mas-valoradas',
                         thumbnail=get_thumb('more voted', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Generos", action="section", section='genre',
                         thumbnail=get_thumb('genres', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Castellano", action="list_all", url= host+'peliculas-espanol',
                         thumbnail=get_thumb('audio', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title="Latino", action="list_all", url=host + 'peliculas-latino',
                         thumbnail=get_thumb('audio', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title="VOSE", action="list_all", url=host + 'peliculas-subtituladas',
                         thumbnail=get_thumb('audio', auto=True)))
    
    # itemlist.append(Item(channel=item.channel, title="Alfabetico", action="section", section='alpha',
    #                     thumbnail=get_thumb('alphabet', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host+'?s=',
                         thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def list_all(item):
    logger.info()
    itemlist = []

    try:
        # if item.section == 'alpha':
        #   patron = '<span class="Num">\d+.*?<a href="([^"]+)" class.*?'
        #   patron += 'src="([^"]+)" class.*?<strong>([^<]+)</strong>.*?<td>(\d{4})</td>'
        # else:
        patron = '<article class="TPost C post-\d+.*?<a href="([^"]+)">.*?'
        patron +='"Year">(\d{4})<.*?data-src="([^"]+)".*?"Title">([^"]+)</h2>'
        data = get_source(item.url)
        matches = re.compile(patron, re.DOTALL).findall(data)

        for scrapedurl, year, scrapedthumbnail, scrapedtitle in matches:

            url = scrapedurl
            if "|" in scrapedtitle:
                scrapedtitle= scrapedtitle.split("|")
                contentTitle = scrapedtitle[0].strip()
            else:
                contentTitle = scrapedtitle

            contentTitle = re.sub('\(.*?\)','', contentTitle)

            title = '%s [%s]'%(contentTitle, year)
            #thumbnail = 'https:'+scrapedthumbnail
            itemlist.append(Item(channel=item.channel, action='findvideos',
                                       title=title,
                                       url=url,
                                       thumbnail=scrapedthumbnail,
                                       contentTitle=contentTitle,
                                       infoLabels={'year':year}
                                       ))
        tmdb.set_infoLabels_itemlist(itemlist, True)

        #  Paginación

        url_next_page = scrapertools.find_single_match(data,'<a href="([^"]+)" class="next page-numbers">')
        if url_next_page:
            itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=url_next_page, action='list_all',
                                 section=item.section))
    except:
        pass
    return itemlist

def section(item):
    logger.info()
    itemlist = []

    data = get_source(host)
    action = 'list_all'

    if item.section == 'genre':
        data = scrapertools.find_single_match(data, '>Géneros</a>.*?</ul>')
    elif item.section == 'alpha':
        data = scrapertools.find_single_match(data, '<ul class="AZList"><li>.*?</ul>')
    patron = '<a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for data_one, data_two in matches:

        url = data_one
        title = data_two
        if title != 'Ver más':
            new_item = Item(channel=item.channel, title= title, url=url, action=action, section=item.section)
            itemlist.append(new_item)

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    patron = 'TPlayerNv="Opt(\w\d+)".*?img src="(.*?)<span>\d+ - (.*?) - ([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for option, url_data, language, quality in matches:
        if 'domain' in url_data:
            url = scrapertools.find_single_match(url_data, 'domain=([^"]+)"')
        elif '1' in option:
            url = scrapertools.find_single_match(data, 'id="Opt%s">.*?file=([^"]+)"' % option)
        else:
            url = scrapertools.find_single_match(data, 'id="Opt%s">.*?h=([^"]+)"' % option)

        
        if url != '' and 'youtube' not in url:
                itemlist.append(item.clone(channel=item.channel, title='%s', url=url, language=IDIOMAS[language],
                                     quality=quality, action='play'))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % '%s [%s] [%s]'%(i.server.capitalize(),
                                                                                              i.language, i.quality))
    
    try:
        itemlist.append(trailer)
    except:
        pass

    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

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
        return list_all(item)
    else:
        return []


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'infantiles':
            item.url = host+'/category/animacion'
        elif categoria == 'terror':
            item.url = host+'/category/terror'
        elif categoria == 'documentales':
            item.url = host+'/category/documental'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

def play(item):
    if not item.url.startswith('http'):
        url_list = []
        res = ''
        ext = 'mp4'
        post = urllib.urlencode({'link': item.url})
        new_data = httptools.downloadpage("https://api.cuevana3.com/stream/plugins/gkpluginsphp.php", post=post).data

        if new_data and not "error" in new_data:
            matches = re.compile('"link":"([^"]+)"', re.DOTALL).findall(new_data)
            itags = {'18': '360p', '22': '720p', '34': '360p', '35': '480p', '37': '1080p', '43': '360p', '59': '480p'}
            for link in matches:
                item.url = link.replace('\\', '').strip()

                #tratar con multilinks/multicalidad de gvideo
                tag = scrapertools.find_single_match(link,'&itag=(\d+)&')
                ext = scrapertools.find_single_match(link,'&mime=.*?/(\w+)&')
                if tag:
                    res = itags[tag]
                    url_list.append([".%s (%s)" % (ext,res), item.url])
            if len(matches) > 1 and url_list:
                item.password = url_list
        else:
            url = 'https://api.cuevana3.com/rr/gotogd.php?h=%s' % item.url
            link = httptools.downloadpage(url).url
            shost = 'https://' + link.split("/")[2]
            vid = scrapertools.find_single_match(link, "\?id=(\w+)")
            if vid:
                item.url = shost+ '/hls/' + vid + '/' + vid + '.playlist.m3u8'
            else:
                item.url = ''

    return [item]

