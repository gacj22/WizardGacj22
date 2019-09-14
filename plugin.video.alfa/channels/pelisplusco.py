# -*- coding: utf-8 -*-
# -*- Channel PelisPlus.co -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import urllib
from platformcode import logger
from platformcode import config
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from channels import filtertools, autoplay
from core import tmdb



IDIOMAS = {'latino':'Lat', 'castellano':'Cast', 'subtitulado':'VOSE'}
list_language = IDIOMAS.values()
list_quality = ['360p', '480p', '720p', '1080p']
list_servers = ['mailru', 'openload',  'streamango', 'estream']


host = 'http://pelisplus.co'
CHANNEL_HEADERS = [
                  ["Host", host.replace("http://","")],
                  ["X-Requested-With", "XMLHttpRequest"]
                  ]


def mainlist(item):
    logger.info()

    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(item.clone(title="Peliculas",
                               action="movie_menu",
                               ))

    itemlist.append(item.clone(title="Series",
                               action="series_menu",
                               ))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def movie_menu(item):

    logger.info()

    itemlist = []

    itemlist.append(item.clone(title="Estrenos",
                               action="list_all",
                               url = host+'/estrenos/',
                               type = 'normal'
                               ))

    itemlist.append(item.clone(title="Generos",
                               action="seccion",
                               url=host,
                               seccion='generos'
                               ))

    itemlist.append(item.clone(title="Por Año",
                               action="seccion",
                               url=host,
                               seccion='anios'
                               ))

    itemlist.append(item.clone(title="Buscar",
                               action="search",
                               url=host + "/suggest/?query=",
                               type="m",
                               seccion='buscar'
                               ))

    return itemlist


def search(item, texto):
    logger.info()
    if not item.type:
        item.type = "m"
        item.url = host + "/suggest/?query="
    item.url = item.url + texto
    if texto != '':
        return sub_search(item)
    else:
        return []


def sub_search(item):
    logger.info()
    itemlist =[]
    headers = {'Referer':host, 'X-Requested-With': 'XMLHttpRequest'}
    dict_data = httptools.downloadpage(item.url, headers=headers).json
    list =dict_data["data"] [item.type]

    if item.type == "m":
        action = "findvideos"
    else:
        action = "seasons"
    for dict in list:
        itemlist.append(item.clone(channel = item.channel,
                             action = action,
                             contentTitle = dict["title"],
                             show = dict["title"],
                             infoLabels={"year":dict["release_year"]},
                             thumbnail = "http://static.pelisfox.tv/static/movie/" + dict["cover"],
                             title = dict["title"] + " (" + dict["release_year"] + ")",
                             url = host + dict["slug"]
                             ))
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    return itemlist

    

def series_menu(item):

    logger.info()

    itemlist =[]

    itemlist.append(item.clone(title="Todas",
                               action="list_all",
                               url=host + '/series/',
                               type='serie'
                               ))

    itemlist.append(item.clone(title="Buscar",
                               action="search",
                               url=host + "/suggest/?query=",
                               type="s",
                               seccion='buscar'
                               ))

    return itemlist


def get_source(url, referer=None):
    logger.info()
    if referer is None:
        data = httptools.downloadpage(url).data
    else:
        data = httptools.downloadpage(url, headers={'Referer':referer, 'x-requested-with': 'XMLHttpRequest'}).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def list_all (item):
    logger.info ()
    itemlist = []
    if item.type in ['serie','recents']:
        contentType = 'serie'
        action = 'seasons'
    else:
        contentType = 'pelicula'
        action = 'findvideos'
    if 'pagination' in item.url:
        post = {'page':item.page, 'type':item.type,'slug':item.slug,'id':item.id}
        post = urllib.urlencode(post)
        data =httptools.downloadpage(item.url, post=post, headers=CHANNEL_HEADERS).data
        data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
        patron = '<a href="([^"]+)">.*?<figure><img.*?src="([^"]+)".*?'
        patron +='<span class="year text-center">(\d{4})</span>.*?<p>([^<]+)</p>'
    else:
        data = get_source(item.url)
        patron = '<div class="item-pelicula pull-left"><a href="([^"]+)">.*?data-src="([^"]+)".*?'
        patron += '<span class="year text-center">([^<]+)</span>.*?<p>([^<]+)</p>'

    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedyear, scrapedtitle in matches:
        url = host+scrapedurl
        thumbnail = scrapedthumbnail
        contentTitle=scrapedtitle
        title = contentTitle
        year = scrapedyear
        new_item=item.clone(action=action,
                            title=title,
                            url=url,
                            thumbnail=thumbnail,
                            plot="",
                            fanart="",
                            infoLabels ={'year':year}
                            )
        if contentType =='serie':
            new_item.contentSerieName=title
        else:
            new_item.contentTitle = title
        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb =True)
 #Paginacion

    next_page_valid = scrapertools.find_single_match(data, '<div class="butmore" site=(?:""|"series") page="(\d+)" '
                                                           'id="(.*?)" type="([^"]+)" limit="\d+">')
    if item.type != 'normal' and (len(itemlist)>19 or next_page_valid):
        type = item.type
        if item.type == 'serie':
            type = 'recents'
        if next_page_valid:
            page = str(int(next_page_valid[0])+1)
            if item.type != 'recents':
                id = next_page_valid[1]
                type = next_page_valid[2]
            else:
                id =''
        else:
            if not item.page:
                item.page = "1"
            page = str(int(item.page)+1)
            id = item.id

        if type =='recents':
            type_pagination = '/series/pagination/'
        else:
            type_pagination = '/pagination/'

        url = host+type_pagination

        itemlist.append(item.clone(action = "list_all",
                                   title = 'Siguiente >>>',
                                   page=page,
                                   url = url,
                                   id = id,
                                   type = type
                                   ))
    return itemlist

def seccion(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)
    page = "1"
    if item.seccion == 'generos':
        patron = '<li><a href="([^"]+)"><i class="ion-cube"></i>([^<]+)<'
        type = 'genre'
        pat = 'genero/'
    elif item.seccion == 'anios':
        patron = '<li><a href="(\/peliculas.*?)">(\d{4})<\/a>'
        type = 'year'
        pat = 'peliculas-'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle
        url = host+scrapedurl
        slug = scrapertools.find_single_match(scrapedurl, "%s(.*?)/" %pat)
        itemlist.append(
            Item(action="list_all",
                 channel=item.channel,
                 contentTitle=item.title,
                 page = "1",
                 slug = slug,
                 title=title,
                 type = type,
                 url=url
                 ))
        # Paginacion

        if itemlist != []:
            next_page = scrapertools.find_single_match(data, '<li><a class= item href=(.*?)&limit=.*?>Siguiente <')
            next_page_url = host + next_page
            import inspect
            if next_page != '':
                itemlist.append(item.clone(action="seccion",
                                           title='Siguiente >>>',
                                           url=next_page_url,
                                           thumbnail='https://s16.postimg.cc/9okdu7hhx/siguiente.png'
                                           ))

    return itemlist


def seasons(item):
    logger.info()
    itemlist =[]

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    patron ='<i class=ion-chevron-down arrow><\/i>(.*?)<\/div>'
    matches = matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels=item.infoLabels

    for title in matches:
        season = title.replace('Temporada ','')
        infoLabels['season'] = season
        title = 'Temporada %s' % season.lstrip('0')
        itemlist.append(Item(
                             channel=item.channel,
                             title=title,
                             url=item.url,
                             action='season_episodes',
                             contentSerieName= item.contentSerieName,
                             contentSeasonNumber = season,
                             infoLabels=infoLabels
                             ))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    itemlist = itemlist[::-1]
    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'episodios':
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += season_episodes(tempitem)

    return itemlist

def season_episodes(item):
    logger.info()
    itemlist = []

    full_data = httptools.downloadpage(item.url+'/').data
    full_data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", full_data)

    season = str(item.infoLabels['season'])
    if int(season) <= 9:
        season = '0'+season
    data = scrapertools.find_single_match(full_data, '</i>Temporada %s</div>(.*?)(?:down arrow|cuadre_comments)' % season)
    patron = '<a href="([^"]+)" title=".*?i-play"><\/i> (.*?)<\/a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    infoLabels = item.infoLabels
    for url, episode in matches:
        episodenumber = re.sub('C.* ','',episode)
        infoLabels['episode'] = episodenumber
        title = '%sx%s - %s' % (infoLabels['season'], episodenumber, episode)
        itemlist.append(Item(channel=item.channel,
                        title= title,
                        url = host+url,
                        action = 'findvideos',
                        infoLabels=infoLabels,
                        contentEpisodeNumber=episode
                        ))
        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)


    return itemlist[::-1]

def get_links_by_language(item, data):
    logger.info()
    video_list = []

    language = scrapertools.find_single_match(data, 'ul id="level\d_([^"]+)"\s*class=')
    patron = 'data-source="([^"]+)"data-quality="([^"]+)"data-srt="([^"]+)?"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    if language in IDIOMAS:
        language = IDIOMAS[language]

    for url, quality, sub in matches:
        if 'http' not in url:

            new_url = 'https://onevideo.tv/api/player?key=90503e3de26d45e455b55e9dc54f015b3d1d4150&link' \
                      '=%s&srt=%s' % (url, sub)
            data = httptools.downloadpage(new_url).data
            data = re.sub(r'\\', "", data)
            video_list.extend(servertools.find_video_items(data=data))

            for video_url in video_list:
                video_url.channel = item.channel
                video_url.action = 'play'
                video_url.title = item.title + '(%s) (%s)' % ('', video_url.server)
                if video_url.language == '':
                    video_url.language = language
                video_url.subtitle = sub
                video_url.contentTitle = item.contentTitle

        else:
            video_list.append(item.clone(title='%s [%s] [%s]',
                                         url=url,
                                         action='play',
                                         quality=quality,
                                         language=language,
                                         subtitle=sub
                                         ))

    return video_list

def findvideos(item):
    logger.info()
    itemlist = []
    video_list = []
    if item.contentType == 'movie':
        new_url = new_url = item.url.replace('/pelicula/', '/player/%s/' % item.contentType)
    else:
        base_url = scrapertools.find_single_match(item.url, '(.*?)/temporada')
        new_url = base_url.replace('/serie/', '/player/serie/')
        new_url += '|%s|%s/'  % (item.contentSeason, item.contentEpisodeNumber)
    data = get_source(new_url, referer=item.url)
    patron_language ='(<ul id="level\d_.*?"*class=.*?ul>)'
    matches = re.compile(patron_language, re.DOTALL).findall(data)

    for language in matches:
        video_list.extend(get_links_by_language(item, language))
    video_list = servertools.get_servers_itemlist(video_list, lambda i: i.title % (i.server.capitalize(), i.language,
                                                                                   i.quality) )
    # Requerido para FilterTools

    video_list = filtertools.get_links(video_list, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(video_list, item)

    if item.contentType != 'episode':
        if config.get_videolibrary_support() and len(video_list) > 0 and item.extra != 'findvideos':
            video_list.append(
                Item(channel=item.channel,
                     title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                     url=item.url,
                     action="add_pelicula_to_library",
                     extra="findvideos",
                     contentTitle=item.contentTitle
                     ))


    return video_list

