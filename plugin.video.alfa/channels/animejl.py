# -*- coding: utf-8 -*-
# -*- Channel AnimeJL -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import logger
from channelselector import get_thumb


host = 'https://www.animejl.net/'

def mainlist(item):
    logger.info()

    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Nuevos Episodios", action="new_episodes",
                         thumbnail=get_thumb('new_episodes', auto=True), url=host))

    itemlist.append(Item(channel=item.channel, title="Todas", action="list_all", thumbnail=get_thumb('all', auto=True),
                         url=host + 'animes'))

    itemlist.append(Item(channel=item.channel, title="Series", action="list_all",
                         thumbnail=get_thumb('tvshows', auto=True), url=host+'animes?type%5B%5D=1&order=default'))

    itemlist.append(Item(channel=item.channel, title="Películas", action="list_all",
                         thumbnail=get_thumb('movies',auto=True), url=host + 'animes?type%5B%5D=2&order=default'))

    itemlist.append(
        Item(channel=item.channel, title="Buscar", action="search", thumbnail=get_thumb('search', auto=True),
             url=host + 'animes?q='))

    return itemlist


def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}|"|\(|\)', "", data)
    return data


def new_episodes(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    data = scrapertools.find_single_match(data, "<h2>Últimos episodios</h2>.*?</ul>")
    patron = "<li><a href='(.*?)' class.*?<img src='(.*?)' alt='(.*?)'></span><span class='Capi'>(.*?)</span>"

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedepi in matches:
        url = host+scrapedurl
        thumbnail = host+scrapedthumbnail
        title = '%s %s' % (scrapedtitle, scrapedepi)
        itemlist.append(Item(channel=item.channel, action='findvideos',
                             title=title,
                             url=url,
                             thumbnail=thumbnail,
                             contentSerieName=scrapedtitle,
                             ))

    return itemlist

def list_all(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    patron = "<article class='Anime alt B'><a href='(.*?)'>.*?class=.*?<img src='(.*?)' alt='(.*?)'>"
    patron +="</figure><span class='Type .*?'>(.*?)</span>.*?star.*?<p>(.*?)</p>"

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle, type, plot in matches:
        url = host + scrapedurl
        thumbnail = host+scrapedthumbnail
        title = scrapedtitle
        type = type
        season = ''
        if 'season' in scrapedtitle.lower():
            season = scrapertools.find_single_match(scrapedtitle, 'season (\d+)')
            scrapedtitle = scrapertools.find_single_match(scrapedtitle, '(.*?) season')

        new_item = Item(channel=item.channel, action='episodios',
                        title=title,
                        url=url,
                        thumbnail=thumbnail,
                        contentSerieName=scrapedtitle,
                        plot=plot,
                        type=item.type,
                        infoLabels={}
                        )
        if type.lower() == 'anime':
            new_item.contentSerieName = scrapedtitle
            new_item.contentSeasonNumber = season
        else:
            new_item.contentTitle = scrapedtitle

        itemlist.append(new_item)

    # Paginacion
    next_page = scrapertools.find_single_match(data,
                                               "<li><a href='([^']+)'><span>&raquo;</span></a></li></ul>")
    if next_page != '':
        itemlist.append(Item(channel=item.channel,
                             action="list_all",
                             title=">> Página siguiente",
                             url=host+next_page,
                             thumbnail='https://s16.postimg.cc/9okdu7hhx/siguiente.png'
                             ))

    return itemlist

def episodios(item):
    logger.info()
    itemlist = []

    base_data = get_source(item.url)
    data = scrapertools.find_single_match(base_data, '<div class=Title>Lista de episodios</div>.*?</ul>')
    if data == '':
        data = scrapertools.find_single_match(base_data, '<div class=Title>Formatos disponibles</div>.*?</ul>')

    if 'listepisodes' in data.lower():
        patron = "<li><a href='(.*?)' class.*?>(.*?)<i class='fa-eye-slash'></i></a></li>"
    elif 'listcaps' in data.lower():
        patron = "<a href=(.*?)>.*?alt=(.*?)>"
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle.strip()
        n=0
        for char in title[::-1]:
            n += 1
            if char == ' ':
                break
        episode = title[-n:]
        episode = scrapertools.find_single_match(episode, r' (\d+)')

        url = host + scrapedurl
        itemlist.append(Item(channel=item.channel, title='Episodio %s' % episode, thumbnail=item.thumbnail, url=url,
                             action='findvideos'))
    if item.type.lower != 'anime' and len(itemlist)==1:
        return findvideos(itemlist[0])
    else:
        return itemlist[::-1]

def findvideos(item):
    logger.info()

    itemlist = []
    data = get_source(item.url)
    itemlist.extend(servertools.find_video_items(data=data))

    for videoitem in itemlist:
        videoitem.channel = item.channel
        videoitem.title = '[%s]' % videoitem.server.capitalize()

    return itemlist

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    try:
        if texto != '':
            return list_all(item)
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
        if categoria == 'anime':
            item.url = host
        itemlist = new_episodes(item)
        if itemlist[-1].title == '>> Página siguiente':
            itemlist.pop()
        return itemlist
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []
