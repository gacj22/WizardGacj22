# -*- coding: utf-8 -*-

import re
import string
import urllib
import urlparse

from channels import filtertools
from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from channels import autoplay
from core.item import Item
from platformcode import config, logger

HOST = "https://www.seriespapaya.net/"

IDIOMAS = {'es': 'Español', 'lat': 'Latino', 'in': 'Inglés', 'ca': 'Catalán', 'sub': 'VOSE', 'Español Latino':'Latino',
           'Español Castellano':'Español', 'Sub Español':'VOSE'}
list_idiomas = IDIOMAS.values()
list_quality = ['360p', '480p', '720p HD', '1080p HD', 'default']
list_servers = ['powvideo', 'streamplay', 'filebebo', 'flashx', 'gamovideo', 'nowvideo', 'openload', 'streamango',
                'streamcloud', 'vidzi', 'clipwatching', ]
thumb_videolibrary = get_thumb("videolibrary_tvshow.png")

def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_latino = get_thumb("channels_latino.png")
    thumb_spanish = get_thumb("channels_spanish.png")
    thumb_vos = get_thumb("channels_vos.png")
    thumb_hot = get_thumb("news.png")
    thumb_recientes = get_thumb("on_the_air.png")
    thumb_vistas = get_thumb("channels_all.png")
    thumb_series_az = get_thumb("channels_tvshow_az.png")
    thumb_buscar = get_thumb("search.png")
    itemlist = []
    itemlist.append(
        Item(title="Capitulos de Estreno:", channel=item.channel, folder=False, thumbnail=thumb_hot))
    
    itemlist.append(
        Item(action="showmore", title="    Latino",
             url=HOST+"estreno-serie-espanol-latino/",
             channel=item.channel, thumbnail=thumb_latino,
             extra_lang="Latino", page=0))

    itemlist.append(
        Item(action="showmore", title="    Castellano", 
             url=HOST+"estreno-serie-castellano/", channel=item.channel,
             thumbnail=thumb_spanish, extra_lang="Español", page=0))
    
    itemlist.append(
        Item(action="showmore", title="    Subtitulado",
             url=HOST+"estreno-serie-sub-espanol/", channel=item.channel, 
             thumbnail=thumb_vos, extra_lang="VOSE", page=0))
    
    itemlist.append(
        Item(action="novedades", title="Capitulos Recientes", channel=item.channel, thumbnail=thumb_recientes, extra="recientes"))
    itemlist.append(
        Item(action="novedades", title="Series Nuevas", channel=item.channel, thumbnail=thumb_series, extra="nuevas"))
    itemlist.append(
        Item(action="novedades", title="Las Más Vistas", channel=item.channel, thumbnail=thumb_vistas, url= HOST + "/lista-series-populares/"))
    itemlist.append(
        Item(action="listado_alfabetico", title="Listado Alfabetico", channel=item.channel, thumbnail=thumb_series_az))

    itemlist.append(Item(action="search", title="Buscar", channel=item.channel, thumbnail=thumb_buscar))
    
    itemlist = filtertools.show_option(itemlist, item.channel, list_idiomas, list_quality)
    
    autoplay.show_option(item.channel, itemlist)
    
    return itemlist


def listado_alfabetico(item):
    logger.info()
    itemlist = [item.clone(action="series_por_letra", title="0-9")]
    
    for letra in string.ascii_uppercase:
        itemlist.append(item.clone(action="series_por_letra", title=letra))
    
    return itemlist


def series_por_letra(item):
    logger.info("letra: %s" % item.title)
    item.letter = item.title.lower()
    item.extra = 0
    
    return series_por_letra_y_grupo(item)


def series_por_letra_y_grupo(item):
    logger.info("letra: %s - grupo: %s" % (item.letter, item.extra))
    itemlist = []
    url = urlparse.urljoin(HOST, "autoload_process.php")
    post_request = {
        "group_no": item.extra,
        "letra": item.letter.lower()
    }

    data = httptools.downloadpage(url, post=urllib.urlencode(post_request)).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    
    patron = r'<div class=list_imagen><img src=(.*?) \/>.*?'
    patron += '<div class=list_titulo><a href=(.*?) style=.*?inherit;>(.*?)'
    patron +=r'<.*?justify>(.*?)<.*?Año:<\/b>.*?(\d{4})<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for img, url, name, plot, year in matches:
        title = re.sub(r'\s*\((.*?)\)$', '', name)
        new_item= Item(
            channel = item.channel,
            action="seasons",
            title=name,
            contentSerieName=title,
            url=urlparse.urljoin(HOST, url),
            thumbnail=urlparse.urljoin(HOST, img),
            context=filtertools.context(item, list_idiomas, list_quality),
            plot = plot,
            infoLabels={'year':year}
        )
        
        itemlist.append(new_item)
    if len(matches) == 8:
        itemlist.append(item.clone(title="Siguiente >>", action="series_por_letra_y_grupo", extra=item.extra + 1))
    
    return itemlist


def novedades(item):
    logger.info()
    itemlist = []
    if item.extra == "recientes":
        data = httptools.downloadpage(HOST).data
        data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
        patron0 = '<h2>Capitulos Recientes</h2>(.*?)<div class=clearfix></div>'
        patron = ' src=(.*?) />.*?href=(.*?)>(.*?)</a><br />(.*?):'
        match = scrapertools.find_single_match(data, patron0)
        
        matches = re.compile(patron, re.DOTALL).findall(match)
        for img, url, title, info in matches:
            if "(" in title and ")" not in title:
                title = title.split(" (")[0]
            ses, ep = scrapertools.find_single_match(info, '(\d+), Episodio (\d+)')
            ftitle =  title + " %sx%s" % (ses, ep)
            title = re.sub(r'\s*\((.*?)\)$', '', title)
            itemlist.append(item.clone(action="findvideos", title=ftitle, url=urlparse.urljoin(HOST, url),
                                      thumbnail=urlparse.urljoin(HOST, img), contentSerieName=title))
    
    elif item.extra == "nuevas":
        data = httptools.downloadpage(HOST).data
        data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
        patron0 = '<h2>Series Nuevas</h2>(.*?)<div class=clearfix></div>'
        patron = '<a title=(.*?) alt.*?href=(.*?)>.*?src=(.*?) />'
        match = scrapertools.find_single_match(data, patron0)
        matches = re.compile(patron, re.DOTALL).findall(match)

        for title, url, img in matches:
            url = url.strip()
            stitle = re.sub(r'\s*\((.*?)\)$', '', title)
            itemlist.append(item.clone(action="seasons", title=title, url=urlparse.urljoin(HOST, url),
                                       thumbnail=urlparse.urljoin(HOST, img), contentSerieName=stitle))
    else:
        data = httptools.downloadpage(item.url).data
        data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
        patron0 = '<h2>Lista De Series - Mas Vistas</h2>(.*?)Vistas de la Semana</h3>'
        match = scrapertools.find_single_match(data, patron0)
        patron = 'class=esimagen>.*? src=(.*?) />.*?href=(.*?) .*?>(.*?)</a>'
        matches = re.compile(patron, re.DOTALL).findall(match)
        for img, url, title in matches:
            stitle = re.sub(r'\s*\((.*?)\)', '', title)
            itemlist.append(item.clone(action="seasons", title=title, url=urlparse.urljoin(HOST, url),
                                       thumbnail=urlparse.urljoin(HOST, img), contentSerieName=stitle))
    
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    
    return itemlist


def showmore(item):
    logger.info()
    language = item.extra_lang
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    patron = r"location.href='(.*?)'.*?background-image: url\('(.*?)'\).*?"
    patron += r"<strong>(\d+)<\/strong>x<strong>(\d+)<\/strong>.*?margin-top: 3px;>(.*?)<\/div>"
    matches = re.compile(patron, re.DOTALL).findall(data)
    itemlist = []
    for url, img , ses, ep, title in matches[item.page:item.page + 30]:
        ftitle =  title + " %sx%s" % (ses, ep)
        title = re.sub(r'\s*\((.*?)\)$', '', title)
        itemlist.append(item.clone(action="findvideos", title=ftitle, url=urlparse.urljoin(HOST, url), 
                        thumbnail=urlparse.urljoin(HOST, img), language=language, contentSerieName=title))
    
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    
    if item.page + 30 < len(matches):
        itemlist.append(item.clone(page=item.page + 30,
                                   title="Siguiente >>"))
    return itemlist


def newest(categoria):
    logger.info("categoria: %s" % categoria)
    if categoria != 'series':
        return []
    return novedades(Item())

def seasons(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '>&rarr; Temporada (\d+) '

    matches = re.compile(patron, re.DOTALL).findall(data)

    if len(matches) == 1:
        return episodesxseasons(item)
    elif len(matches) < 1:
        itemlist.append(item.clone(title = '[COLOR=grey]No hay episodios disponibles para esta serie[/COLOR]', action='', url=''))
        return itemlist
    infoLabels = item.infoLabels
    for scrapedseason in matches:
        contentSeasonNumber = scrapedseason
        title = 'Temporada %s' % scrapedseason
        infoLabels['season'] = contentSeasonNumber

        itemlist.append(Item(channel=item.channel, action='episodesxseasons', url=item.url, title=title,
                             contentSeasonNumber=contentSeasonNumber, infoLabels=infoLabels, extra1=item.title))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName,
                 extra2='library', thumbnail=thumb_videolibrary))

    return itemlist

def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseasons(tempitem)

    return itemlist

def episodesxseasons(item):
    itemlist = []

    infoLabels = item.infoLabels
    data = httptools.downloadpage(item.url).data
    if item.contentSeasonNumber and item.extra2 != 'library':
        prevtitle = item.extra1
        data = scrapertools.find_single_match(data, r'<div style="cursor:pointer">&rarr; Temporada %s(.*?)</div>\n</div>\n'  % item.contentSeasonNumber)
    else:
        prevtitle = item.title
    patron = 'visco.*?href="(?P<url>[^"]+).+?nbsp; (?P<title>.*?)</a>.+?ucapaudio.?>(?P<langs>.*?)</div>'
    episodes = re.findall(patron, data, re.MULTILINE | re.DOTALL)
    for url, title, langs in episodes:
        s_e = scrapertools.get_season_and_episode(title)
        if item.contentSeasonNumber:
            infoLabels["season"] = item.contentSeasonNumber
        else:
            infoLabels["season"] = s_e.split("x")[0]
        infoLabels["episode"] = s_e.split("x")[1]
        languages = " ".join(
            ["[%s]" % IDIOMAS.get(lang, lang) for lang in re.findall('images/s-([^\.]+)', langs)])
        filter_lang = languages.replace("[", "").replace("]", "").split(" ")
        itemlist.append(item.clone(action="findvideos",
                                   infoLabels = infoLabels,
                                   language=filter_lang,
                                   title="%s %s %s" % (prevtitle, title, languages),
                                   url=urlparse.urljoin(HOST, url)
                                   ))
    itemlist = filtertools.get_links(itemlist, item, list_idiomas, list_quality)
    
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    
    # Opción "Añadir esta serie a la videoteca de KODI"
    if config.get_videolibrary_support() and len(itemlist) > 0 and not item.contentSeasonNumber:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName,
                 thumbnail=thumb_videolibrary))
    return itemlist


def search(item, texto):
    logger.info("texto: %s" % texto)
    itemlist = []
    infoLabels = ()
    data_dict = httptools.downloadpage(urlparse.urljoin(HOST, "/buscar.php?term=%s" % texto)).json
    try:
        tvshows = data_dict["myData"]
    except:
        return []
    for show in tvshows:
        title = re.sub('\s*\((.*?)\)$', '', show["titulo"])
        itemlist.append(item.clone(action="seasons",
                       context=filtertools.context(item, list_idiomas, list_quality),
                       contentSerieName=title,
                       thumbnail=urlparse.urljoin(HOST, show["img"]),
                       title=show["titulo"],
                       url=urlparse.urljoin(HOST, show["urla"])
                       ))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def findvideos(item):
    logger.info("url: %s" % item.url)
    data = httptools.downloadpage(item.url).data
    
    #parche para series agregadas a videoteca con bug
    casting = len(item.infoLabels.get('castandrole', ''))
    if casting > 100 and item.contentChannel == 'videolibrary':
        item.infoLabels['castandrole'] = []


    servers = {"Thevideo": "thevideome",
                "1fichier": "onefichier",
                "Uploaded": "uploadedto" }
    expr = 'mtos' + '.+?' + \
           '<div.+?images/(?P<lang>[^\.]+)' + '.+?' + \
           '<div[^>]+>\s+(?P<date>[^\s<]+)' + '.+?' + \
           '<div.+?img.+?>\s*(?P<server>.+?)</div>' + '.+?' + \
           '<div.+?href="(?P<url>[^"]+).+?images/(?P<type>[^\.]+)' + '.+?' + \
           '<div[^>]+>\s*(?P<quality>.*?)</div>' + '.+?' + \
           '<div.+?<a.+?>(?P<uploader>.*?)</a>'
    links = re.findall(expr, data, re.MULTILINE | re.DOTALL)
    itemlist = []
    try:
        filtro_enlaces = config.get_setting("filterlinks", item.channel)
    except:
        filtro_enlaces = 2
    typeListStr = ["Descargar", "Ver"]
    for lang, date, server, url, linkType, quality, uploader in links:
        linkTypeNum = 0 if linkType == "descargar" else 1
        if filtro_enlaces != 2 and filtro_enlaces != linkTypeNum:
            continue
        server = servers.get(server, server)
        itemlist.append(item.clone(
                action="play",
                title="{linkType} en {server} [{lang}] [{quality}] ({uploader}: {date})".format(
                    linkType=typeListStr[linkTypeNum],
                    lang=IDIOMAS.get(lang, lang),
                    date=date,
                    server=server.rstrip().capitalize(),
                    quality=quality,
                    uploader=uploader),
                server=server.rstrip().lower(),
                url=urlparse.urljoin(HOST, url),
                language=IDIOMAS.get(lang,lang),
                quality=quality
            )
        )

    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_idiomas, list_quality)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist


def play(item):
    logger.info("play: %s" % item.url)
    itemlist = []
    if not 'seriespapaya.' in item.url:
        itemlist.append(item.clone())
        itemlist = servertools.get_servers_itemlist(itemlist)

        return itemlist

    data = httptools.downloadpage(item.url).data
    
    if item.server not in ['openload', 'streamcherry', 'streamango']:
        item.server = ''
    item.url = scrapertools.find_single_match(data, "location.href='([^']+)'")
    itemlist.append(item.clone())
    itemlist = servertools.get_servers_itemlist(itemlist)

    return itemlist
