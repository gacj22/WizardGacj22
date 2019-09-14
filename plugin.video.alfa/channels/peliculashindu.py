# -*- coding: utf-8 -*-

import re
import urlparse

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger

host = "http://www.peliculashindu.com/"


def mainlist(item):
    logger.info()

    itemlist = list()

    #itemlist.append(
    #    Item(channel=item.channel, action="lista", title="Top Películas", url=urlparse.urljoin(host, "top")))
    itemlist.append(Item(channel=item.channel, action="lista", title="Novedades", url=host+'novedades/'))
    itemlist.append(Item(channel=item.channel, action="explorar", title="Género", url=urlparse.urljoin(host, "genero")))
    #itemlist.append(Item(channel=item.channel, action="explorar", title="Listado Alfabético",
    #                     url=urlparse.urljoin(host, "alfabetico")))
    itemlist.append(Item(channel=item.channel, action="explorar", title="Listado por Año", url=urlparse.urljoin(host, "genero")))
    #itemlist.append(Item(channel=item.channel, action="lista", title="Otras Películas (No Bollywood)",
    #                     url=urlparse.urljoin(host, "estrenos")))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=urlparse.urljoin(host, "buscar/")))
    return itemlist


def explorar(item):
    logger.info()
    itemlist = list()
    urltitle = item.title
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    if 'Género' in urltitle:
        patron = "var accion = '<div .+?>(.+?)<\/div>'"
    # if 'Listado Alfabético' in urltitle:
    #    patron = '<\/li><\/ul>.+?<h3>Pel.+?tico<\/h3>(.+?)<\/h3>'
    if 'Año' in urltitle:
        patron = "var anho = '<div .+?>(.+?)<\/div>'"
    data_explorar = scrapertools.find_single_match(data, patron)
    patron_explorar = '<li class=".+?"><a class=".+?" href="(.+?)">(.+?)<\/a><\/li>'
    matches = scrapertools.find_multiple_matches(data_explorar, patron_explorar)
    for scrapedurl, scrapedtitle in matches:
        if 'Ficcion' in scrapedtitle:
            scrapedtitle = 'Ciencia Ficción'

        itemlist.append(item.clone(action='lista', title=scrapedtitle, url=scrapedurl))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "-")
    item.url = item.url + texto
    # logger.info("item="+item.url)
    if texto != '':
        return lista(item)


def lista(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)  # Eliminamos tabuladores, dobles espacios saltos de linea, etc...
    # data_mov= scrapertools.find_single_match(data,'<div class="lista-anime">(.+?)<section class="paginacion">')
    patron =  "<figure class='figure-peliculas'>" #generico
    patron += " <a href='(.+?)' .+?>.+?" #scrapedurl
    patron += "<img .+? src=(.+?) alt.+?> " #scrapedthumbnail
    patron += "<p>(.+?)<\/p>.+?" #scrapedplot
    patron += "<p class='.+?anho'>(.+?)" #scrapedyear
    patron += "<\/p>.+?<h2>(.+?)<\/h2>" #scrapedtitle
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedplot, scrapedyear, scrapedtitle in matches:
        if '"' in scrapedthumbnail:
            scrapedthumbnail=scrapedthumbnail.replace('"','')
        itemlist.append(item.clone(title=scrapedtitle+' ['+scrapedyear+']', url=scrapedurl, plot=scrapedplot, 
                                   thumbnail=scrapedthumbnail, action="play", contentTitle=scrapedtitle))
    # Paginacion
    patron_pag = '<a href="([^"]+)" aria-label="Next"> Siguiente'
    paginasig = scrapertools.find_single_match(data, patron_pag)
    next_page_url = paginasig

    if paginasig != "":
        item.url = next_page_url
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR cyan]Página Siguiente >>[/COLOR]", url=next_page_url,
                             thumbnail='https://s32.postimg.cc/4zppxf5j9/siguiente.png'))
    return itemlist

def play(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<\/div> <\/div> <a href="(.+?)" class="a-play-cartelera"'
    scrapedurl = scrapertools.find_single_match(data, patron)
    data2 = httptools.downloadpage(host+scrapedurl).data
    url = scrapertools.find_single_match(data2, '<a link="([^"]+)"')
    item.url = url
    item.server = servertools.get_server_from_url(url)
    #for scrapedurl in match:
    itemlist.append(item.clone())

    return itemlist
# #def findvideos(item):
#     logger.info()

#     itemlist = []

#     data = httptools.downloadpage(item.url).data
#     data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
#     itemlist.extend(servertools.find_video_items(data=data))
#     patron_show = '<strong>Ver Pel.+?a([^<]+) online<\/strong>'
#     show = scrapertools.find_single_match(data, patron_show)
#     for videoitem in itemlist:
#         videoitem.channel = item.channel
#     if config.get_videolibrary_support() and len(itemlist) > 0 and item.contentChannel!='videolibrary':
#         itemlist.append(
#             Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
#                  action="add_pelicula_to_library", extra="findvideos", contentTitle=show))

#     return itemlist
