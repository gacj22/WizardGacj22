# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from core import tmdb
from core import jsontools

host = 'https://www.tnaflix.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/new/?d=all&period=all"))
    itemlist.append( Item(channel=item.channel, title="Popular" , action="peliculas", url=host + "/popular/?d=all&period=all"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorado" , action="peliculas", url=host + "/toprated/?d=all&period=month"))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="catalogo", url=host + "/channels/all/top-rated/1/all"))
    itemlist.append( Item(channel=item.channel, title="PornStars" , action="categorias", url=host + "/pornstars"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search.php?what=%s&tab=" % texto
    try:
        return peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def catalogo(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<div class="vidcountSp">(\d+)</div>.*?<a class="categoryTitle channelTitle" href="([^"]+)" title="([^"]+)">.*?data-original="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for cantidad,scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        title = scrapedtitle + " (" + cantidad + ")"
        scrapedplot = ""
        itemlist.append( Item(channel=item.channel, action="peliculas", title=title , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    next_page_url = scrapertools.find_single_match(data,'<a class="llNav" href="([^"]+)">')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="catalogo" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    if item.title=="PornStars" :
        data = scrapertools.find_single_match(data,'</i> Hall Of Fame Pornstars</h1>(.*?)</section>')
    patron  = '<a class="thumb" href="([^"]+)">.*?<img src="([^"]+)".*?<div class="vidcountSp">(.*?)</div>.*?<a class="categoryTitle".*?>([^"]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,cantidad,scrapedtitle in matches:
        scrapedplot = ""
        if item.title=="Categorias" :
            scrapedthumbnail = "http:" + scrapedthumbnail
            scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        if item.title=="PornStars" :
            scrapedurl = urlparse.urljoin(item.url,scrapedurl) + "?section=videos"
        scrapedtitle = scrapedtitle + " (" + cantidad + ")"
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    next_page_url = scrapertools.find_single_match(data,'<a class="llNav" href="([^"]+)">')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="categorias" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<a class=\'thumb no_ajax\' href=\'(.*?)\'.*?'
    patron += 'data-original=\'(.*?)\' alt="([^"]+)"><div class=\'videoDuration\'>([^<]+)</div>(.*?)<div class=\'watchedInfo'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,duracion,quality in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        title = "[COLOR yellow]" + duracion + "[/COLOR] " + scrapedtitle
        if quality:
            quality= scrapertools.find_single_match(quality, '>(\d+p)<')
            title = "[COLOR yellow]" + duracion + "[/COLOR] " + "[COLOR red]" + quality +  "[/COLOR] " + scrapedtitle
        contentTitle = title
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append(Item(channel=item.channel, action="play" , title=title , url=url, thumbnail=thumbnail,
                             fanart=thumbnail, plot=plot, contentTitle = contentTitle))
    next_page_url = scrapertools.find_single_match(data,'<a class="llNav" href="([^"]+)">')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append(item.clone(action="peliculas", title="Página Siguiente >>", text_color="blue", url=next_page_url) )
    return itemlist


def ref(url):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(url).data
    VID = scrapertools.find_single_match(data,'id="VID" type="hidden" value="([^"]+)"')
    vkey = scrapertools.find_single_match(data,'id="vkey" type="hidden" value="([^"]+)"')
    thumb = scrapertools.find_single_match(data,'id="thumb" type="hidden" value="([^"]+)"')
    nkey= scrapertools.find_single_match(data,'id="nkey" type="hidden" value="([^"]+)"')
    url = "https://cdn-fck.tnaflix.com/tnaflix/%s.fid?key=%s&VID=%s&nomp4=1&catID=0&rollover=1&startThumb=%s" % (vkey, nkey, VID, thumb)
    url += "&embed=0&utm_source=0&multiview=0&premium=1&country=0user=0&vip=1&cd=0&ref=0&alpha"
    return url


def play(item):
    logger.info()
    itemlist = []
    url= ref(item.url)
    headers = {'Referer': item.url}
    data = httptools.downloadpage(url, headers=headers).data
    patron = '<res>(.*?)</res>.*?'
    patron += '<videoLink><([^<]+)></videoLink>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for title, url in matches:
        url= url.replace("![CDATA[", "http:").replace("]]", "")
        itemlist.append(["%s %s [directo]" % (title, url), url])
    itemlist.reverse()
    return itemlist


