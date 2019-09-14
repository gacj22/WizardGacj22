# -*- coding: utf-8 -*-

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools


HOST = "https://www.area-documental.com/"


def mainlist(item):
    logger.info()
    itemlist = []
    
    itemlist.append(item.clone( title='Documentales destacados', action='list_all', url=HOST+'resultados.php?buscar=&genero=' ))

    itemlist.append(item.clone( title='Documentales recientes', action='list_all', url=HOST+'resultados-reciente.php?buscar=&genero=' ))
    itemlist.append(item.clone( title='Documentales más vistos', action='list_all', url=HOST+'resultados-visto.php?buscar=&genero=' ))

    itemlist.append(item.clone( title='Documentales por año', action='list_all', url=HOST+'resultados-anio.php?buscar=&genero=' ))
    itemlist.append(item.clone( title='Documentales por título', action='list_all', url=HOST+'resultados-titulo.php?buscar=&genero=' ))

    itemlist.append(item.clone( title='Documentales en 3D', action='list_all', url=HOST+'3D.php' ))

    itemlist.append(item.clone( title='Series completas', action='list_all', url=HOST+'series.php' ))

    itemlist.append(item.clone( title='Por categorías', action='generos' ))

    itemlist.append(item.clone( title = 'Buscar documental ...', action = 'search', search_type = 'documentary' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(HOST).data

    patron = '<a href="(resultados[^"]+)" class="dropdown-toggle" data-toggle="dropdown">([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url, title in matches:
        
        patron = '<li><a href="%s">TODO</a></li>(.*?)</ul>' % url.replace('?', '\?')
        bloque = scrapertools.find_single_match(data, patron)
        subitems = scrapertools.find_multiple_matches(bloque, '<li><a href="[^"]+">([^<]+)')

        itemlist.append(item.clone( action='subgeneros', title=title.strip(), url=HOST + url, subitems=subitems, plot=', '.join(subitems) ))

    return itemlist

def subgeneros(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( action='list_all', title='Todo ' + item.title, url=item.url ))

    for subgenero in item.subitems:
        itemlist.append(item.clone( action='list_all', title=subgenero, url=HOST+'resultados.php?genero=&buscar='+subgenero.replace(' ', '+') ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '<a class="hvr-shutter-out-horizontal" href="([^"]+)"><img (?:data-|)src="([^"]+)" alt="([^"]+)"'
    patron += '.*?&nbsp;&nbsp;&nbsp;(\d+| ).*?<div class="comments-space">(.*?)</div>'
    matches = scrapertools.find_multiple_matches(data, patron)

    for url, thumb, title, year, plot in matches:
        
        if 'player.php' not in url:
            titulo = '%s [COLOR gray](%s)[/COLOR]' % (title, year)
            itemlist.append(item.clone( action='list_all', url=url, title=titulo, thumbnail=HOST+thumb,
                                        plot=scrapertools.htmlclean(plot).strip() ))

        else:
            itemlist.append(item.clone( action='findvideos', url=HOST+url, title=title, thumbnail=HOST+thumb,
                                        infoLabels={"year": year, "plot": scrapertools.htmlclean(plot).strip()},
                                        contentType='movie', contentTitle=title, contentExtra='documentary' ))

    next_page_link = scrapertools.find_single_match(data, '<li><a class="last">\d+</a></li>\s*<li>\s*<a href="([^"]+)')
    if next_page_link != '':
        if next_page_link.startswith('?'): 
            if 'series.php' in item.url: next_page_link = HOST + 'series.php' + next_page_link
            else: next_page_link = HOST + 'index.php' + next_page_link
        else: next_page_link = HOST + next_page_link[1:]
        next_page_link = next_page_link.replace('&amp;', '&')
        itemlist.append(item.clone( title='>> Página siguiente', action='list_all', url = next_page_link ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    try:
        sub_url, sub_lang = scrapertools.find_single_match(data, 'file:\s*"/(webvtt/[^"]+)",\s*label: "([^"]*)"')
        sub_url = HOST + sub_url
        sub_url += '|Referer=' + item.url
    except:
        sub_url = ''; sub_lang = ''
    
    matches = scrapertools.find_multiple_matches(data, 'file:\s*"([^"]+)",\s*label: "([^"]*)"')
    for url, lbl in matches:
        if '.mp4' not in url: continue
        # ~ url += '|Referer=' + item.url # !?
        lang = 'VOSE' if 'Espa' in sub_lang else 'Esp' # !?
        
        itemlist.append(Item( channel = item.channel, action = 'play', server='directo', 
                              title = 'Directo', url = url, language = lang, quality = lbl, subtitle = sub_url
                       ))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = HOST + 'resultados.php?genero=&buscar=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
