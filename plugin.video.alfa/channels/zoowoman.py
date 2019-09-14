# -*- coding: utf-8 -*-

import re
from channelselector import get_thumb
from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger


IDIOMAS = {'VOSE': 'VOSE',
           'VOSI': 'VOS',
           'Español latino': 'Lat',
           'Iberian spanish': 'Cast'
        }
list_language = IDIOMAS.values()
list_quality = ['720p', '480p']
list_servers = ['mega', 'archiveorg', 'wetube', 'peertube']


__channel__='zoowoman'

host = "https://zoowoman.website/wp/"

try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
    full_title = config.get_setting('full_title_view', __channel__)
except:
    __modo_grafico__ = True
    full_title = False


def mainlist(item):
    logger.info()
    
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []
    itemlist.append(Item(channel = item.channel, title = "Novedades", action = "peliculas", url = host+"movies/", thumbnail = get_thumb("newest", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Más Vistas", action = "peliculas", url = host+'tendencias/', thumbnail = get_thumb("more watched", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Mejor Valoradas", action = "peliculas", url = host+'calificaciones/', thumbnail = get_thumb("more voted", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Ranking IMDb", action = "ranking", url = host+'raking-imdb/', thumbnail = get_thumb("recomended", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Por género", action = "generos_years", url = host, minfo = "Géneros", thumbnail = get_thumb("genres", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Por año", action = "generos_years", url = host, minfo = "year", thumbnail = get_thumb("year", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Buscar", action = "search", url = host + "?s=", thumbnail = get_thumb("search", auto = True)))
    autoplay.show_option(item.channel, itemlist)
    return itemlist

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas','latino']:
            item.url = host
        elif categoria == 'infantiles':
            item.url = host + 'genre/animacion/'
        elif categoria == 'terror':
            item.url = host + 'genre/terror/'
        itemlist = peliculas(item)
        if "Pagina" in itemlist[-1].title:
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    if texto != '':
        return peliculas(item)
    else:
        return []


def generos_years(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data

    patron = '(?s)%s</h2>(.*?)</ul></nav>' %item.minfo
    bloque = scrapertools.find_single_match(data, patron)
    patron  = 'href="([^"]+)'
    patron += '">([^<]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for url, titulo in matches:
        itemlist.append(Item(channel = item.channel,
                             action = "peliculas",
                             title = titulo,
                             url = url
                             ))
    return itemlist

def ranking(item):
    logger.info()
    itemlist = []
    pos = 0
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}", "", data)
    try:
        data = data.split("Ranking IMDb 50</h1>")[1]
    except:
        pass
    patron = '<img src="([^"]+)".*?<div class="rating">(.*?)</div>' #rating, url
    patron+= '<div class="title"><a href="([^"]+)">(.*?)</a>' #title, thumb
    matches = scrapertools.find_multiple_matches(data, patron)
    
    for thumbnail, punt, url, title in matches:
        title = title.replace(" VOSI", "")
        pos += + 1
        pre = "[COLOR=yellow][B]%s[/COLOR] %s [/B]" % (pos, punt)
        mtitle = pre + title
        if '&#8211;' in title:
            title0 = title.split(" &#8211; ")
            title = title0[0]
            toriginal = title0[1]

        elif ' / ' in title:
            title0 = title.split(" / ")
            title = title0[0]
            toriginal = title0[1]
        if full_title == False:
            mtitle = pre + title

        itemlist.append(Item(channel = item.channel,
                                   action = "findvideos",
                                   title = mtitle,
                                   contentTitle= title,
                                   url = url,
                                   infoLabels={'year': '-'},
                                   thumbnail = thumbnail
                                   ))
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    return itemlist



def peliculas(item):
    logger.info()
    itemlist = []
    p_act = ""
    data = httptools.downloadpage(item.url).data

    patron = '<div class="poster"><a href="([^"]+)"><img src="([^"]+)" ' #url, thumb
    if "/movies/" in item.url:
        patron += 'alt="([^"]+)".*?<span>(\d{4})</span>.*?' #title, year
        patron += '<div class="texto">(.*?)<div class="degradado">' #plot+info

    elif "/?s=" in item.url:
        patron = 'thumbnail animation-2"><a href="([^"]+)"><img src="([^"]+)" '
        patron += 'alt="([^"]+)".*?class="year">(\d{4})</span>.*?' #title, year
        patron += '<p>(.*?)</p>' #info
    else:
        patron += 'alt="([^"]+)".*?icon-st.*?"></span> (.*?)</div>.*?' #title, info(punt)
        patron += '<span>(\d{4})</span>' #year
    matches = scrapertools.find_multiple_matches(data, patron)
    for url, thumbnail, title, year, info in matches:
        tlang = ''
        punt = ''
        title = title.replace(" VOSI", "")
        
        info = re.sub(r"\n|\r|\t|\s{2}", "", info)
        
        vers = scrapertools.find_single_match(info, '(Vers[^"]+)')
        if vers:
            info = info.replace(vers, "")
        plot = info
        if len(info) == 4 and info != "":
            a = info
            b = year
            year = a
            info = b
            punt = " (%s)" % info
            plot = ""
        elif 'http' in info:
            info = info.split('http')[0]
            if '&#160;' in info:
                info = info.split('&#160;')[0]
        
        mtitle = title
        plot = info
        if '&#8211;' in title:
            title0 = title.split(" &#8211; ")
            title = title0[0]
            toriginal = title0[1]

        elif ' / ' in title:
            title0 = title.split(" / ")
            title = title0[0]
            toriginal = title0[1]
        if full_title == False:
            mtitle = title
        mtitle += " (" + year + ")"+tlang+punt

        itemlist.append(Item(channel = item.channel,
                                   action = "findvideos",
                                   title = mtitle,
                                   contentTitle= title,
                                   url = url,
                                   contentPlot = plot,
                                   infoLabels={'year': year},
                                   thumbnail = thumbnail
                                   ))
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    try:
        p_act, p_tot = scrapertools.find_single_match(data, 'pagination"><span>Página (\d+) de (\d+)</span>')
    except:
        pass
    if p_act != "":
        p_next = int(p_act) + 1
        pagina = "[COLOR=blue]Ir a la Página %s de %s >>[/COLOR]" % (p_next, p_tot)
        if "/?s=" in item.url:
            url_pagina = item.url.replace("/wp/" , "/wp/page/%s/" % p_next)
            if "/page/" in item.url:
                url_pagina = item.url.replace("/page/%s/" % p_act, "/page/%s/" % p_next)
        else:
            url_pagina = item.url+"/page/%s/" % p_next
            if "/page/" in item.url:
                url_pagina = item.url.replace("/page/%s/" % p_act, "/page/%s/" % p_next)
        if int(p_act) < int(p_tot):
            itemlist.append(Item(channel=item.channel, action="peliculas", title=pagina, url=url_pagina))
    return itemlist


def findvideos(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if not item.contentPlot:
        item.contentPlot = scrapertools.find_single_match(data, 'wp-content"><p>(.*?)\/')

    patron = 'download" href="([^"]+)".*?</td><td><img.*?> (.*?)</td>' #url, server
    patron+= '<td>(.*?)</td><td>(.*?)</td><td>(.*?)</td>' #cal, lang, tipo
    #patron+= '<td>(.*?)</td><td><a href.*?>(.*?)' #fecha, uploader
    
    matches = scrapertools.find_multiple_matches(data, patron)
    for surl, sserver, scal, slang, stype in matches:
        sname = sserver.split(".")[0]
        lang = IDIOMAS[slang]
        scal = scal.replace("HD", "720")
        stitle = " [COLOR=green][%sp][/COLOR] [COLOR=yellow](%s)[/COLOR]" % (scal, lang)
        
        if 'torrent' in stype.lower():
            sname = 'torrent'
            server = 'torrent'

        elif sname == "mega":
            server=sname
        #si hay mas excepciones, usar dict
        elif sname == "ok":
            server='okru'
            sname == "okru"
        else:
            server="directo"

        titulo = "Ver en: %s" % sname.capitalize()

        if host in surl:
            new_data = httptools.downloadpage(surl).data
            surl = scrapertools.find_single_match(new_data, '<a href="([^"]+)"')
        if "/formats=" in surl:
            surl = surl.split("/formats=")[0].replace("/compress/", "/details/")
            server = "archiveorg"
        itemlist.append(
                 item.clone(channel = item.channel,
                 action = "play",
                 title = titulo+stitle,
                 url = surl,
                 server = server,
                 language= lang,
                 quality= scal+'p',
                 infoLabels = item.infoLabels
                 ))
    #se produce cuando aún no han subido enlaces y solo hay embed(provisional)
    if not matches:
        lang = ""
        stitle = ""
        #en los embed no siempre sale el idioma, y si sale puede ser el mismo para varios videos
        mlang = scrapertools.find_multiple_matches(data, '<strong>(.*?)</strong>')
        patron = '<iframe src="([^"]+)"' #server
        matches = scrapertools.find_multiple_matches(data, patron)
        for i, surl in enumerate(matches):
            if mlang:
                try:
                    slang = mlang[i]
                except:
                    slang = mlang[0]
                if "original" in slang.lower():
                    if "castellano" in slang.lower():
                        lang = "VOSE"
                    elif "ingl" in slang.lower():
                        lang = "VOS"
                    else: lang = "VOSE"
                elif "castellano" in slang.lower():
                    lang = "Cast"
                else:
                    lang = "Lat"
            if lang:
                stitle = " [COLOR=yellow](%s)[/COLOR]" % lang
            itemlist.append(
                 item.clone(channel = item.channel,
                 action = "play",
                 title = "%s" + stitle,
                 url = surl,
                 language= lang,
                 infoLabels = item.infoLabels
                 ))

        itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if itemlist and item.contentChannel != "videolibrary":
        itemlist.append(item.clone(channel="trailertools", title="Buscar Tráiler", action="buscartrailer", context="",
                                   text_color="magenta"))
        # Opción "Añadir esta película a la biblioteca de KODI"
        if config.get_videolibrary_support():
            itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="green",
                                 action="add_pelicula_to_library", url=item.url, thumbnail = item.thumbnail,
                                 contentTitle = item.contentTitle
                                 ))
    return itemlist