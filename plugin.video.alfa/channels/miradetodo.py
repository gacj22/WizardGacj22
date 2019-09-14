# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

tgenero = {"Comedia": "https://s7.postimg.cc/ne9g9zgwb/comedia.png",
           "Suspense": "https://s13.postimg.cc/wmw6vl1cn/suspenso.png",
           "Drama": "https://s16.postimg.cc/94sia332d/drama.png",
           "Acción": "https://s3.postimg.cc/y6o9puflv/accion.png",
           "Aventura": "https://s10.postimg.cc/6su40czih/aventura.png",
           "Romance": "https://s15.postimg.cc/fb5j8cl63/romance.png",
           "Animación": "https://s13.postimg.cc/5on877l87/animacion.png",
           "Ciencia ficción": "https://s9.postimg.cc/diu70s7j3/cienciaficcion.png",
           "Terror": "https://s7.postimg.cc/yi0gij3gb/terror.png",
           "Documental": "https://s16.postimg.cc/7xjj4bmol/documental.png",
           "Música": "https://s29.postimg.cc/bbxmdh9c7/musical.png",
           "Western": "https://s23.postimg.cc/lzyfbjzhn/western.png",
           "Fantasía": "https://s13.postimg.cc/65ylohgvb/fantasia.png",
           "Guerra": "https://s4.postimg.cc/n1h2jp2jh/guerra.png",
           "Misterio": "https://s1.postimg.cc/w7fdgf2vj/misterio.png",
           "Crimen": "https://s4.postimg.cc/6z27zhirx/crimen.png",
           "Historia": "https://s15.postimg.cc/fmc050h1n/historia.png",
           "película de la televisión": "https://s9.postimg.cc/t8xb14fb3/delatv.png",
           "Action & Adventure": "https://s4.postimg.cc/neu65orz1/action_adventure.png",
           "Sci-Fi & Fantasy": "https://s23.postimg.cc/ys5if2oez/scifi_fantasy.png",
           "Suspenso": "https://s13.postimg.cc/wmw6vl1cn/suspenso.png",
           "Familia": "https://s7.postimg.cc/6s7vdhqrf/familiar.png",
           "Foreign": "https://s29.postimg.cc/jdc2m158n/extranjera.png",
           "Cartelera MDT": "https://s1.postimg.cc/6yle12szj/cartelera.png",
           "Romanticas": "https://s21.postimg.cc/xfsj7ua0n/romantica.png"
           }

tcalidad = {"FULL HD": "https://s18.postimg.cc/qszt3n6tl/fullhd.png",
            "HD": "https://s27.postimg.cc/m2dhhkrur/image.png",
            "SD": "https://s29.postimg.cc/l66t2pfqf/image.png"
            }
host = 'http://miradetodo.net/'


def mainlist(item):
    logger.info()

    itemlist = []

    itemlist.append(item.clone(title="Peliculas",
                               action="menu_peliculas",
                               thumbnail=get_thumb('movies', auto=True),
                               fanart='https://s8.postimg.cc/6wqwy2c2t/peliculas.png'
                               ))

    itemlist.append(item.clone(title="Series",
                               action="menu_series",
                               thumbnail=get_thumb('tvshows', auto=True),
                               fanart='https://s27.postimg.cc/iahczwgrn/series.png',
                               ))

    itemlist.append(item.clone(title="Buscar", action="search",
                               thumbnail=get_thumb('search', auto=True),
                               fanart='https://s30.postimg.cc/pei7txpa9/buscar.png',
                               url=host + '?s='
                               ))

    return itemlist


def menu_peliculas(item):
    logger.info()

    itemlist = []

    itemlist.append(item.clone(title="Todas",
                               action="lista",
                               thumbnail=get_thumb('all', auto=True),
                               fanart='https://s18.postimg.cc/fwvaeo6qh/todas.png',
                               url=host + 'page/1/?s'
                               ))

    itemlist.append(item.clone(title="Generos",
                               action="seccion",
                               url=host + 'page/1/?s',
                               thumbnail=get_thumb('genres', auto=True),
                               fanart='https://s3.postimg.cc/5s9jg2wtf/generos.png',
                               seccion='generos-pelicula'
                               ))

    itemlist.append(item.clone(title="Por Año",
                               action="seccion",
                               url=host + 'page/1/?s',
                               thumbnail=get_thumb('year', auto=True),
                               fanart='https://s8.postimg.cc/7eoedwfg5/pora_o.png',
                               seccion='fecha-estreno'
                               ))

    itemlist.append(item.clone(title="Calidad",
                               action="seccion",
                               url=host + 'page/1/?s',
                               thumbnail=get_thumb('quality', auto=True),
                               fanart='https://s13.postimg.cc/6nzv8nlkn/calidad.png',
                               seccion='calidad'
                               ))

    return itemlist


def menu_series(item):
    logger.info()

    itemlist = []

    itemlist.append(item.clone(title="Todas",
                               action="lista", thumbnail=get_thumb('all', auto=True),
                               fanart='https://s18.postimg.cc/fwvaeo6qh/todas.png',
                               url=host + 'series/page/1/',
                               ))

    itemlist.append(item.clone(title="Generos",
                               action="seccion",
                               url=host + 'series/page/1/',
                               thumbnail=get_thumb('genres', auto=True),
                               fanart='https://s3.postimg.cc/5s9jg2wtf/generos.png',
                               seccion='generos-serie'
                               ))

    itemlist.append(item.clone(title="Por Año",
                               action="seccion",
                               url=host + 'series/page/1/',
                               thumbnail=get_thumb('year', auto=True),
                               fanart='https://s8.postimg.cc/7eoedwfg5/pora_o.png',
                               seccion='series-lanzamiento'
                               ))

    return itemlist


def lista(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    patron = 'class=item>.*?<a href=(.*?)><div class=image>.*?<img src=(.*?) alt=(.*?) \(\d{4}.*?ttx>(.*?)'
    patron += '<div class=degradado>.*?fixyear><h2>.*?<\/h2>.*?<span class=year>(.*?)<\/span><\/div>(.*?)<\/div>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedplot, scrapedyear, scrapedquality in matches:
        url = scrapedurl
        action = 'findvideos'
        thumbnail = scrapedthumbnail
        plot = scrapedplot
        contentSerieName = ''
        contentTitle = scrapedtitle
        title = contentTitle
        if scrapedquality != '':
            quality = scrapertools.find_single_match(scrapedquality, 'calidad2>(.*?)<')
            title = contentTitle + ' (%s)' % quality
        year = scrapedyear

        if 'series' in item.url or 'series' in url:
            action = 'temporadas'
            contentSerieName = contentTitle
            contentTitle = ''
            quality = ''

        itemlist.append(Item(channel=item.channel,
                             action=action,
                             title=title,
                             url=url,
                             thumbnail=thumbnail,
                             plot=plot,
                             contentTitle=contentTitle,
                             contentSerieName=contentSerieName,
                             quality=quality,
                             infoLabels={'year': year}
                             ))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    # Paginacion

    if itemlist != []:
        actual_page_url = item.url
        next_page = scrapertools.find_single_match(data,
                                                   'alignleft><a href=(.*?) ><\/a><\/div><div class=nav-next alignright>')
        if next_page != '':
            itemlist.append(Item(channel=item.channel,
                                 action="lista",
                                 title='Siguiente >>>',
                                 url=next_page,
                                 thumbnail='https://s16.postimg.cc/9okdu7hhx/siguiente.png'
                                 ))
    return itemlist


def seccion(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)
    if item.seccion == 'generos-pelicula':
        patron = '<li class=cat-item cat-item-.*?><a href=(.*?) >(.*?<\/a> <span>.*?)<\/span><\/li>'
    elif item.seccion == 'generos-serie':
        patron = '<li class=cat-item cat-item-.*?><a href=(.*?\/series-genero\/.*?) >(.*?<\/a> <span>.*?)<\/span><\/li>'
    elif item.seccion in ['fecha-estreno', 'series-lanzamiento']:
        patron = '<li><a href=http:\/\/miradetodo\.io\/fecha-estreno(.*?)>(.*?)<\/a>'
    elif item.seccion == 'calidad':
        patron = '<li><a href=http:\/\/miradetodo\.io\/calidad(.*?)>(.*?)<\/a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        thumbnail = ''
        if 'generos' in item.seccion:
            cantidad = re.sub(r'.*?<\/a> <span>', '', scrapedtitle)
            title = re.sub(r'<\/a> <span>|\d|\.', '', scrapedtitle)
            url = scrapedurl
            title = scrapertools.decodeHtmlentities(title)
            if title in tgenero:
                thumbnail = tgenero[title]
            title = title + ' (%s)' % cantidad
        elif item.seccion in ['series-lanzamiento', 'fecha-estreno', 'calidad']:
            title = scrapedtitle
            url = 'http://miradetodo.io/%s%s' % (item.seccion, scrapedurl)
            if item.seccion == 'calidad' and title in tcalidad:
                thumbnail = tcalidad[title]

        itemlist.append(item.clone(action='lista',
                                   title=title,
                                   url=url,
                                   thumbnail=thumbnail
                                   ))
    return itemlist


def temporadas(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    patron = '<span class=title>.*?- Temporada (.*?)<\/span>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for temporada in matches:
        title = 'Temporada %s' % temporada
        contentSeasonNumber = temporada
        item.infoLabels['season'] = contentSeasonNumber
        itemlist.append(item.clone(action='episodiosxtemp',
                                   title=title,
                                   contentSeasonNumber=contentSeasonNumber
                                   ))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel,
                             title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                             url=item.url,
                             action="add_serie_to_library",
                             extra="episodios",
                             contentSerieName=item.contentSerieName,
                             contentSeasonNumber=contentSeasonNumber
                             ))

    return itemlist


def episodios(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)

    patron = '<li><div class=numerando>(\d+).*?x.*?(\d+)<\/div>.*?<a href=(.*?)> (.*?)<\/a>.*?<\/i>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedtemp, scrapedep, scrapedurl, scrapedtitle in matches:
        temporada = scrapedtemp
        title = temporada + 'x%s %s' % (scrapedep, scrapedtitle)
        url = scrapedurl
        contentEpisodeNumber = scrapedep
        item.infoLabels['episode'] = contentEpisodeNumber
        itemlist.append(item.clone(action='findvideos',
                                   title=title,
                                   url=url,
                                   contentEpisodeNumber=contentEpisodeNumber,
                                   ))
    return itemlist


def episodiosxtemp(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    temporada = item.contentSeasonNumber
    patron = '<li><div class=numerando>%s.*?x.*?(\d+)<\/div>.*?<a href=(.*?)> (.*?)<\/a>.*?<\/i>' % temporada
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedep, scrapedurl, scrapedtitle in matches:
        title = temporada + 'x%s %s' % (scrapedep, scrapedtitle)
        url = scrapedurl
        contentEpisodeNumber = scrapedep
        item.infoLabels['episode'] = contentEpisodeNumber
        itemlist.append(item.clone(action='findvideos',
                                   title=title,
                                   url=url,
                                   contentEpisodeNumber=contentEpisodeNumber,
                                   ))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def findvideos(item):
    logger.info()
    url_list = []
    itemlist = []
    duplicados = []
    data = get_source(item.url)
    src = data
    patron = 'id=(?:div|player)(\d+)>.*?data-lazy-src=(.*?) scrolling'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for option, videoitem in matches:
        sub = ''
        lang = scrapertools.find_single_match(src,
                                              '<a href=#(?:div|player)%s.*?>.*?(.*?)<\/a>' % option)
        if 'audio ' in lang.lower():
            lang=lang.lower().replace('audio ','')
            lang=lang.capitalize()

        data = get_source(videoitem)
        video_urls = scrapertools.find_multiple_matches(data, '<li><a href=(.*?)><span')
        for video in video_urls:
            video_data = get_source(video)
            if sub == '' and 'sub' in lang:
                sub_file = scrapertools.find_single_match(video, '&sub=([^+]+)')
                sub = 'http://miradetodo.io/stream/subt/%s' % sub_file
                                
            if 'openload' in video or 'your' in video:
                new_url= scrapertools.find_single_match(video_data,'<li><a href=(.*?srt)><span')
                data_final = get_source(new_url)
            else:
                data_final=video_data
            
            url = scrapertools.find_single_match(data_final,'iframe src=(.*?) scrolling')
            if url == '':
                url = scrapertools.find_single_match(data_final, "'file':'(.*?)'")
            
            
            quality = item.quality
            server = servertools.get_server_from_url(url)
            title = item.contentTitle + ' [%s] [%s]' % (server, lang)
            if item.quality != '':
                title = item.contentTitle + ' [%s] [%s] [%s]' % (server, quality, lang)

            if url!='':
                itemlist.append(item.clone(title=title, url=url, action='play', language=lang, subtitle=sub))
    itemlist = servertools.get_servers_itemlist(itemlist)
    if item.infoLabels['mediatype'] == 'movie':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(Item(channel=item.channel,
                                 title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                                 url=item.url,
                                 action="add_pelicula_to_library",
                                 extra="findvideos",
                                 contentTitle=item.contentTitle
                                 ))

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    try:
        if texto != '':
            return lista(item)
        else:
            return []
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas','latino']:
            item.url = host + 'page/1/?s'

        elif categoria == 'infantiles':
            item.url = host + 'category/animacion/'

        itemlist = lista(item)
        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data
