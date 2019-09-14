# -*- coding: utf-8 -*-

import urlparse, re

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

servers = {'ul': 'uploaded', 'ok': 'okru', 'hqq': 'netu', 'waaw': 'netu',
          'drive': 'gvideo', 'mp4': 'gvideo', 'api': 'gvideo'}
IDIOMAS = {'Latino': 'LAT', 'Español': 'CAST', 'SUB': 'VOSE', 'Subtitulado': 'VOSE', 'Inglés':'VO' }
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['directo', 'rapidvideo', 'streamango', 'okru', 'vidoza', 'openload', 'powvideo']


CHANNEL_HOST = "http://www.cinetux.to/"

# Configuracion del canal
__modo_grafico__ = config.get_setting('modo_grafico', 'cinetux')
__perfil__ = config.get_setting('perfil', 'cinetux')

# Fijar perfil de color            
perfil = [['0xFFFFE6CC', '0xFFFFCE9C', '0xFF994D00'],
          ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E'],
          ['0xFF58D3F7', '0xFF2E9AFE', '0xFF2E64FE']]
color1, color2, color3 = perfil[__perfil__]

viewmode_options = {0: 'movie_with_plot', 1: 'movie', 2: 'list'}
viewmode = viewmode_options[config.get_setting('viewmode', 'cinetux')]


def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []
    item.viewmode = viewmode
    data = httptools.downloadpage(CHANNEL_HOST + "pelicula").data
    total = scrapertools.find_single_match(data, "Películas</h1><span>(.*?)</span>")
    titulo = "Peliculas (%s)" %total
    #titulo peliculas
    itemlist.append(Item(channel=item.channel, title=titulo, text_color=color2, action="",
                         text_bold=True, plot=item.plot, thumbnail=item.thumbnail, folder=False))
    
    itemlist.append(Item(channel=item.channel, action="peliculas", title="      Novedades",
                         url=CHANNEL_HOST + "pelicula", thumbnail=get_thumb('newest', auto=True),
                         text_color=color1, plot=item.plot))
    
    itemlist.append(Item(channel=item.channel, action="destacadas", title="      Destacadas",
                         url=CHANNEL_HOST + "mas-vistos/", thumbnail=get_thumb('hot', auto=True),
                         text_color=color1, plot=item.plot))
    
    itemlist.append(Item(channel=item.channel, action="idioma", title="      Por idioma",
                         text_color=color1, thumbnail=get_thumb('language', auto=True),
                         plot=item.plot))
    
    itemlist.append(Item(channel=item.channel, action="generos", title="      Por géneros",
                         url=CHANNEL_HOST, thumbnail=get_thumb('genres', auto=True),
                         text_color=color1, plot=item.plot))
    #titulo documentales
    itemlist.append(Item(channel=item.channel, title="Documentales", text_bold=True, folder=False, 
                         text_color=color2, plot=item.plot, action="", thumbnail=item.thumbnail))
    
    itemlist.append(Item(channel=item.channel, action="peliculas", title="      Novedades",
                         url=CHANNEL_HOST + "genero/documental/", text_color=color1,
                         thumbnail=get_thumb('newest', auto=True), plot=item.plot))
    
    itemlist.append(Item(channel=item.channel, action="peliculas", title="      Por orden alfabético",
                         url=CHANNEL_HOST + "genero/documental/?orderby=title&order=asc&gdsr_order=asc",
                         text_color=color1, plot=item.plot, thumbnail=get_thumb('alphabet', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title="", action="", folder=False,
                         plot=item.plot, thumbnail=item.thumbnail))
    
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar...", text_color=color3,
                         thumbnail=get_thumb('search', auto=True), plot=item.plot))
    
    itemlist.append(Item(channel=item.channel, action="configuracion", title="Configurar canal...",
                         text_color="gold", folder=False, plot=item.plot,
                         thumbnail=get_thumb("setting_0.png")))
    
    autoplay.show_option(item.channel, itemlist)
    
    return itemlist


def configuracion(item):
    from platformcode import platformtools
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


def search(item, texto):
    logger.info()
    item.url = CHANNEL_HOST + "?s="
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    try:
        return peliculas(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
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
        if categoria == 'peliculas':
            item.url = CHANNEL_HOST
            item.action = "peliculas"

        elif categoria == 'documentales':
            item.url = CHANNEL_HOST + "genero/documental/"
            item.action = "peliculas"

        elif categoria == 'infantiles':
            item.url = CHANNEL_HOST + "genero/animacion/"
            item.action = "peliculas"

        elif categoria == 'terror':
            item.url = CHANNEL_HOST + "genero/terror/"
            item.action = "peliculas"

        elif categoria == 'castellano':
            item.url = CHANNEL_HOST + "idioma/espanol/"
            item.action = "peliculas"

        elif categoria == 'latino':
            item.url = CHANNEL_HOST + "idioma/latino/"
            item.action = "peliculas"

        itemlist = peliculas(item)
        if itemlist[-1].action == "peliculas":
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    item.text_color = color2
    data = httptools.downloadpage(item.url).data
    patron = '(?s)class="(?:result-item|item movies)">.*?<img src="([^"]+)'
    patron += '.*?alt="([^"]+)"'
    patron += '(.*?)'
    patron += 'href="([^"]+)"'
    patron += '.*?(?:<span>|<span class="year">)(.+?)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedthumbnail, scrapedtitle, quality, scrapedurl, scrapedyear in matches:
        quality = scrapertools.find_single_match(quality, '.*?quality">([^<]+)')
        try:
            contentTitle = scrapedtitle
            year = scrapertools.find_single_match(scrapedyear,'\d{4}')
            if "/" in contentTitle:
                contentTitle = contentTitle.split(" /", 1)[0]
            scrapedtitle = "%s (%s)" % (contentTitle, year)
        except:
            contentTitle = scrapedtitle
        if quality:
            scrapedtitle += "  [%s]" % quality
        new_item = item.clone(action="findvideos", title=scrapedtitle, contentTitle=contentTitle,
                              url=scrapedurl, thumbnail=scrapedthumbnail,
                              contentType="movie", quality=quality)
        if year:
            new_item.infoLabels['year'] = int(year)
        itemlist.append(new_item)

    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    # Extrae el paginador
    next_page_link = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)')
    if next_page_link:
        itemlist.append(item.clone(action="peliculas", title=">> Página siguiente", url=next_page_link,
                                   text_color=color3))
    return itemlist


def destacadas(item):
    logger.info()
    itemlist = []
    item.text_color = color2
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, 'peliculas_destacadas.*?class="letter_home"')
    patron = '(?s)href="([^"]+)".*?'
    patron += 'alt="([^"]+)".*?'
    patron += 'src="([^"]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        #scrapedurl = CHANNEL_HOST + scrapedurl
        url = urlparse.urljoin(CHANNEL_HOST, scrapedurl)
        itemlist.append(item.clone(action="findvideos", title=scrapedtitle, contentTitle=scrapedtitle,
                              url=url, thumbnail=scrapedthumbnail,
                              contentType="movie"
                              ))
    next_page_link = scrapertools.find_single_match(data, '<a href="([^"]+)"\s+><span [^>]+>&raquo;</span>')
    if next_page_link:
        itemlist.append(
            item.clone(action="destacadas", title=">> Página siguiente", url=next_page_link, text_color=color3))
    return itemlist


def generos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, '(?s)dos_columnas">(.*?)</ul>')
    patron = '<li><a.*?href="([^"]+)">(.*?)</li>'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedtitle in matches:
        #scrapedurl = CHANNEL_HOST + scrapedurl
        url = urlparse.urljoin(CHANNEL_HOST, scrapedurl)
        scrapedtitle = scrapertools.htmlclean(scrapedtitle).strip()
        scrapedtitle = unicode(scrapedtitle, "utf8").capitalize().encode("utf8")
        if scrapedtitle == "Erotico" and config.get_setting("adult_mode") == 0:
            continue
        itemlist.append(item.clone(action="peliculas", title=scrapedtitle, url=url))
    return itemlist


def idioma(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="peliculas", title="Español", url= CHANNEL_HOST + "idioma/espanol/"))
    itemlist.append(item.clone(action="peliculas", title="Latino", url= CHANNEL_HOST + "idioma/latino/"))
    itemlist.append(item.clone(action="peliculas", title="VOSE", url= CHANNEL_HOST + "idioma/subtitulado/"))
    return itemlist


def findvideos(item):
    import urllib
    logger.info()
    itemlist=[]
    qual_fix = ''
    data = httptools.downloadpage(item.url).data
    
    patron = "<a class='optn' href='([^']+)'.*?<img alt='([^']+)'.*?<img src='.*?>([^<]+)<.*?<img src='.*?>([^<]+)<"
    matches = scrapertools.find_multiple_matches(data, patron)
    for url, iserver, quality, language in matches:
        
        if not qual_fix:
            qual_fix += quality
        
        lang = IDIOMAS.get(language, language)
        
        if not config.get_setting('unify'):
            title = ' [%s][%s]' % (quality, lang)
        else:
            title = ''
        try:
            iserver = iserver.split('.')[0].rstrip()
            iserver = servers.get(iserver, iserver)
        except:
            pass

        server = iserver.lower().replace('gvideo', 'directo')
        
        iserver = iserver.capitalize() + title
        itemlist.append(Item(channel=item.channel, title=iserver, url=url,
                            action='play', quality=quality, text_color="",
                            language=lang, infoLabels=item.infoLabels, server=server))

    patron  = 'tooltipctx.*?data-type="([^"]+).*?'
    patron += 'data-post="(\d+)".*?'
    patron += 'data-nume="(\d+).*?'
    patron += '</noscript> (.*?)</.*?'
    patron += 'assets/img/(.*?)"/>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for tp, pt, nm, language, iserver in matches:
        language = language.strip()
        lang = IDIOMAS.get(language, language)

        post = {'action':'doo_player_ajax', 'post':pt, 'nume':nm, 'type':tp}
        post = urllib.urlencode(post)

        if item.quality == '':
            quality = 'SD'
            if qual_fix:
                quality = qual_fix
        else:
            quality = item.quality

        if not config.get_setting('unify'):
            title = ' [%s][%s]' % (quality, lang)
        else:
            title = ''
        try:
            iserver = iserver.split('.')[0].rstrip()
            iserver = servers.get(iserver, iserver)

        except:
            pass
        
        server = iserver.lower().replace('gvideo', 'directo')
        iserver = iserver.capitalize() + title

        itemlist.append(Item(channel=item.channel, title=iserver, url="", action='play',
                             infoLabels=item.infoLabels, language=lang, text_color = "", server=server,
                                 spost=post, quality=quality))
    #itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    itemlist.sort(key=lambda it: (it.language, it.title, it.quality))
    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)
    if itemlist:
        if item.contentChannel != "videolibrary":
            if config.get_videolibrary_support():
                itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="green",
                                     action="add_pelicula_to_library", url=item.url, thumbnail = item.thumbnail,
                                     contentTitle = item.contentTitle
                                     ))
    return itemlist


def get_url(url):
    logger.info()
    url = url.replace('\\/', '/')
    if "cinetux.me" in url:
        d1 = httptools.downloadpage(url).data
        url = scrapertools.find_single_match(d1, 'document.location.replace\("([^"]+)')
        if url == "":
            id = scrapertools.find_single_match(d1, '<img src="[^#]+#([^"]+)"')
            d1 = d1.replace("'",'"')
            url = scrapertools.find_single_match(d1, '<iframe.*?src="([^"]+)') + id
            if "drive" in url:
                url += "/preview"
            if "FFFFFF" in url:
                url = scrapertools.find_single_match(d1, 'class="cta" href="([^"]+)"')
    url = url.replace('&amp;f=frame', "")
    url = url.replace("povwideo","powvideo")
    return url


def play(item):
    if not item.spost:
        new_data = httptools.downloadpage(item.url).data
        url = scrapertools.find_single_match(new_data, 'id="link" href="([^"]+)"')
        item.url = get_url(url)
    else:
        post = item.spost
        new_data = httptools.downloadpage(CHANNEL_HOST+'wp-admin/admin-ajax.php',
                                           post=post, headers={'Referer':item.url}).data
        url = scrapertools.find_single_match(new_data, "src='([^']+)'")
        item.url = get_url(url)
    item.server = ""
    item = servertools.get_servers_itemlist([item])
    #item.thumbnail = item.contentThumbnail
    return item
