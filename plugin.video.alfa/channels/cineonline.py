# -*- coding: utf-8 -*-
#------------------------------------------------------------
import re, urllib, urlparse

from channels import autoplay
from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, jsontools, tmdb
from core import servertools
from channels import filtertools

host = 'https://www.cine-online.eu'

IDIOMAS = {'Español': 'ESP', 'Cast': 'ESP', 'Latino': 'LAT', 'Lat': 'LAT', 'Subtitulado': 'VOSE', 'Sub': 'VOSE'}
list_language = IDIOMAS.values()
list_servers = ['Streamango', 'Vidoza', 'Openload', 'Streamcherry', 'Netutv']
# list_quality = ['Brscreener', 'HD', 'TS']
list_quality = []
__channel__='cineonline'
__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', __channel__)
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', __channel__)
try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
except:
    __modo_grafico__ = True


def mainlist(item):
    logger.info()
    itemlist = []
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist.append(item.clone(title ="Películas", action ="mainlist_pelis"))
    itemlist.append(item.clone(title="Series" , action="lista", url= host + "/serie/"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    
    itemlist.append(item.clone(title="Configurar canal...", text_color="gold", action="configuracion", folder=False))
    autoplay.show_option(item.channel, itemlist)
    return itemlist

def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone(title="Novedades" , action="lista", url= host))
    itemlist.append(item.clone(title="Castellano" , action="lista", url= host + "/tag/castellano/"))
    itemlist.append(item.clone(title="Latino" , action="lista", url= host + "/tag/latino/"))
    itemlist.append(item.clone(title="Subtituladas" , action="lista", url= host + "/tag/subtitulado/"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url= host))
    itemlist.append(item.clone(title="Año" , action="categorias", url= host))

    itemlist.append(item.clone( title = 'Buscar', action = 'search', search_type = 'movie' ))

    return itemlist

def configuracion(item):
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/?s=%s" % texto
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if "Año" in item.title:
        data = scrapertools.find_single_match(data,'<h3>Año de estreno(.*?)</ul>')
        patron  = '<li><a href="([^"]+)">(\d+)</(\w)>'
    else:
        patron  = '<li class="cat-item cat-item-\d+"><a href="([^"]+)">([^"]+)</a> <span>(\d+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle, cantidad in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        title = scrapedtitle + " %s" % cantidad
        itemlist.append(item.clone(channel=item.channel, action="lista", title=title , url=scrapedurl ,
                              thumbnail=scrapedthumbnail , plot=scrapedplot) )
    return itemlist



    
    
def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<div id="mt-\d+".*?<a href="([^"]+)".*?'
    patron += '<img src="([^"]+)" alt="([^"]+)".*?'
    patron += '<span class="year">(\d+)</span>.*?'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedyear in matches:
        scrapedtitle = scrapedtitle.replace("Ver", "").replace("online", "")
        title = '%s (%s)' % (scrapedtitle, scrapedyear)
        url = scrapedurl
        new_item = Item(channel=item.channel,
                        title=title,
                        url=scrapedurl,
                        thumbnail=scrapedthumbnail,
                        infoLabels={'year':scrapedyear})

        if '/serie/' in url:
            new_item.action = 'temporadas'
            new_item.contentSerieName = scrapedtitle
        else:
            new_item.action = 'findvideos'
            new_item.contentTitle = scrapedtitle
        itemlist.append(new_item)
    tmdb.set_infoLabels(itemlist, True)
    next_page_url = scrapertools.find_single_match(data,'<a href="([^"]+)">Siguiente</a>')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append(item.clone(channel=item.channel , action="lista" , title="Next page >>" , 
                                   text_color="blue", url=next_page_url) )
    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<span class="se-t">(\d+)</span>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for numtempo in matches:
        itemlist.append(item.clone( action='episodesxseason', title='Temporada %s' % numtempo, url = item.url,
                                    contentType='season', contentSeason=numtempo ))
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))
    # return sorted(itemlist, key=lambda it: it.title)
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    templist = temporadas(item)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)
    return itemlist


def episodesxseason(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="numerando">%s x (\d+)</div>.*?' % item.contentSeason
    patron += '<a href="([^"]+)">([^"]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for episode, url, title in matches:
        titulo = '%sx%s %s' % (item.contentSeason, episode, title)
        itemlist.append(item.clone( action='findvideos', url=url, title=titulo,
                                    contentType='episode', contentEpisodeNumber=episode ))
    tmdb.set_infoLabels(itemlist)
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = 'id="plays-(\d+)">\s*([^<]+)</div'
    matches = scrapertools.find_multiple_matches(data, patron)
    for xnumber, xname in matches:
        if "/episodios/" in item.url:
            lang = scrapertools.find_single_match(data, '#player2%s">([^<]+)</a>' % xnumber)
        else:
            lang = scrapertools.find_single_match(data, '#div%s">([^<]+)<' % xnumber)
        if "lat" in lang.lower(): lang= "Lat"
        if 'cast' in lang.lower(): lang= "Cast"
        if 'sub' in lang.lower(): lang= "Sub"
        if lang in IDIOMAS:
            lang = IDIOMAS[lang]
        post= {"nombre":xname}
        url= httptools.downloadpage("https://www.cine-online.eu/ecrypt", post=urllib.urlencode(post)).data
        url = scrapertools.find_single_match(url,'<(?:IFRAME SRC|iframe src)="([^"]+)"')

        if not config.get_setting('unify'):
            title = ' (%s)' % (lang)
        else:
            title = ''
        if url != '':  
            itemlist.append(item.clone(action="play", title='%s'+title, url=url, language=lang ))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    # Requerido para Filtrar enlaces
    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra !='findvideos' and not "/episodios/" in item.url :
        itemlist.append(Item(channel=item.channel, action="add_pelicula_to_library", 
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                             extra="findvideos", contentTitle=item.contentTitle)) 
    return itemlist


