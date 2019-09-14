# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools, tmdb

host = 'https://www.salynpm.com'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append( Item(channel=item.channel, title="Películas" , action="lista", url=host + "/search/label/Pel%C3%ADcula?&max-results=24"))
    # itemlist.append( Item(channel=item.channel, title="Mas vistos" , action="lista", url=host + "/?display=tube&filtre=views"))
    # itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="lista", url=host + "/?display=tube&filtre=rate"))

    itemlist.append( Item(channel=item.channel, title="Géneros" , action="generos", url=host + "/p/categorias.html"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search?q=%s" % texto
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def generos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    data = scrapertools.find_single_match(data, 'Películas</div>(.*?)</div>')
    patron = '<a href="([^"]+)".*?</i>(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        title = scrapedtitle
        scrapedthumbnail =  ""
        itemlist.append( Item(channel=item.channel, action="lista", title=title, url=scrapedurl,
                              thumbnail=scrapedthumbnail , plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron  = '<a class=\'card__image(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for match in matches:
        url = scrapertools.find_single_match(match,'href=\'([^\']+)\' title=')
        scrapedtitle = scrapertools.find_single_match(match,'title=\'([^\']+)\'')
        thumbnail = scrapertools.find_single_match(match,'src=\'([^\']+)\'')
        quality = scrapertools.find_single_match(match,'p\'>(.*?)</span>')
        title = scrapedtitle
        if quality:
            title = scrapedtitle + " [COLOR red]" + quality + "[/COLOR]"
        scrapedyear = "-"
        plot = ""
        itemlist.append( Item(channel=item.channel, action="findvideos", title=title, url=url,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle = scrapedtitle,
                              quality=quality, infoLabels={'year':scrapedyear}))

    tmdb.set_infoLabels(itemlist, True)

    next_page = scrapertools.find_single_match(data, '<a class=\'older-link flex align-items-center\' href=\'([^\']+)\'')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append( Item(channel=item.channel, action="lista", title="Página Siguiente >>", text_color="blue", 
                              url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    idiomas = scrapertools.find_single_match(data,'<b>Audio:</b>(.*?)<')
    subtitulada = scrapertools.find_single_match(data,'<b>Subtitulada:</b>(.*?)<')
    audios = []
    if "Latino" in idiomas: audios.append('LAT')
    if "Inglés" in idiomas: audios.append('ENG')
    if "Japones" in idiomas: audios.append('JAP')
    if "Si" in subtitulada: audios.append('SUB')

    numero = scrapertools.find_multiple_matches(data,'data-tab="tab\d+">(.*?)</li>')
    numero = len(numero)
    if not numero:
        numero = 1
    n = 1
    patron = '<video class="js-player".*?<source src="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url in matches:
        url= url.replace("amp;", "")
        if not config.get_setting('unify'):
            title = '%s (%s)' % (item.quality, " / ".join(audios))
        else:
            title = ""
        if n <= numero:
            itemlist.append(item.clone(action="play", title = "%s " + title, language=audios, url=url ))
            n += 1
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


