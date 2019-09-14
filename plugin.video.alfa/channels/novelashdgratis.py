# -*- coding: utf-8 -*-
# -*- Channel Novelas HD Gratis -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from channels import filtertools
from channels import autoplay

host = 'http://www.novelasgratishd.co'

IDIOMAS = {'la':'Latino'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['powvideo',
                'netu',
                'playedto',
                'allmyvideos',
                'gamovideo',
                'openload',
                'dailymotion',
                'streamplay',
                'streaminto',
                'youtube',
                'vidoza',
                'flashx']

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = list()

    itemlist.append(item.clone(title="En Emision", action="list_all", url=host, type='emision'))
    itemlist.append(item.clone(title="Ultimas Agregadas", action="list_all", url=host, type='ultimas'))
    itemlist.append(item.clone(title="Todas", action="list_all", url=host, type='todas'))
    itemlist.append(item.clone(title="Alfabetico", action="alpha", url=host, type='alfabetico'))

    if autoplay.context:
        autoplay.show_option(item.channel, itemlist)

    return itemlist


def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def list_all(item):
    logger.info()
    itemlist =[]
    data = get_source(item.url)
    no_thumbs= ['emision', 'todas']

    if item.type not in no_thumbs:
        patron = '<div class=picture><a href=(.*?) title=(.*?)><img src=(.*?) width='
    else:
        if item.type == 'emision':
            data = scrapertools.find_single_match(data, 'class=dt>Telenovelas que se Transmiten<\/div>.*?</ul>')
        if item.type == 'todas':
            data = scrapertools.find_single_match(data, 'class=dt>Lista de Novelas<\/div>.*?</ul>')
        patron = '<li><a href=(.*?) title=(.*?)>.*?</a></li>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    if item.type in no_thumbs:
        for scrapedurl, scrapedtitle in matches:
            url = host+scrapedurl
            contentSerieName = scrapedtitle
            title = contentSerieName
            new_item = Item(channel=item.channel, title=title, url= url, action='episodes',
                            contentSerieName= contentSerieName)
            itemlist.append(new_item)
    else:
        for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
            url = host + '/'+scrapedurl
            contentSerieName = scrapedtitle
            title = contentSerieName
            thumbnail = scrapedthumbnail
            new_item = Item(channel=item.channel, title=title, url=url, action='episodes', thumbnail=thumbnail,
                            contentSerieName=contentSerieName)
            itemlist.append(new_item)

    return itemlist


def alpha(item):
    logger.info()
    itemlist= []

    data = get_source(item.url)
    patron = '<li class=menu-gen><a href=(.*?)>(.*?)</a> </li>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(item.clone(title=scrapedtitle, url=host+scrapedurl, action='list_all'))

    return itemlist


def episodes(item):
    logger.info()
    itemlist=[]

    data=get_source(item.url)
    patron='<li class=lc><a href=(.*?) title=.*?class=lcc>(.*?)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle
        url = host+scrapedurl
        new_item = Item(channel=item.channel, title=title, url=url, action='findvideos')
        itemlist.append(new_item)

    return itemlist [::-1]

def findvideos(item):
    logger.info()

    servers = {'powvideo':'http://powvideo.net/embed-',
               'netu':'http://netu.tv/watch_video.php?v=',
               'played':'http://played.to/embed-',
               'allmy':'http://allmyvideos.net/embed-',
               'gamo':'http://gamovideo.com/embed-',
               'openload':'https://openload.co/embed/',
               'daily':'http://www.dailymotion.com/embed/video/',
               'play':'http://streamplay.to/embed-',
               'streamin':'http://streamin.to/embed-',
               'youtube':'https://www.youtube.com/embed/',
               'vidoza':'https://vidoza.net/embed-',
               'flashx':'https://www.flashx.tv/embed-'}


    itemlist = []
    data = get_source(item.url)
    patron = 'id=tab\d+><script>(.*?)\((.*?)\)<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for server, id in matches:
        if server in servers:
            url= '%s%s'%(servers[server], id)
            itemlist.append(item.clone(url=url, title='%s', action='play', language=IDIOMAS['la']))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)


    return itemlist


