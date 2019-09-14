# -*- coding: utf-8 -*-
import re
import urllib
from channelselector import get_thumb

from core.item import Item
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools, tmdb
from platformcode import config, logger
from channels import autoplay

host = "http://cuevana2espanol.com/"
list_quality = []
list_servers = ['rapidvideo', 'streamango', 'directo', 'yourupload', 'openload', 'dostream']

def load_data(url):
    data = httptools.downloadpage(url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    return data

def redirect_url(url, parameters=None, scr=False):

    try:
        url = url.replace("/irgo", "/go").replace('gotoolp', 'm3u8player')
        data = httptools.downloadpage(url, post=parameters, timeout=4.0)
    except:
        return

   
    if not data.data:
        return
    
    link = data.url
    data = data.data
    
    if scr:
        host = 'https://' + link.split("/")[2]
        vid = scrapertools.find_single_match(link, "\?id=(\w+)")
        if vid:
            link = host+ '/hls/' + vid + '/' + vid + '.playlist.m3u8'
    elif 'm3u8' in link:
        link = scrapertools.find_single_match(data, '"file": "([^"]+)"')
    return link

def mainlist(item):
    itemlist = []
    
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist.append(Item(channel = item.channel, title = "Novedades", action = "movies", 
        url = host + "ver-pelicula-online", thumbnail = get_thumb("newest", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Favoritas", action = "movies", 
        url = host + "calificaciones", thumbnail = get_thumb("favorites", auto = True) ))
    itemlist.append(Item(channel = item.channel, title = "Destacadas", action = "movies", 
        url = host + "tendencias", thumbnail = get_thumb("hot", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Ranking IMDB", action = "moviesIMDB", 
        url = host + "raking-imdb", thumbnail = get_thumb("hot", auto = True) ))
    itemlist.append(Item(channel = item.channel, title = "--- Busqueda ---", folder=False, text_bold=True))
    itemlist.append(Item(channel = item.channel, title = "Por Letra", action = "letters",
        url = host, thumbnail = get_thumb("alphabet", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Buscar...", action = "search", 
        url = host + "?s=", thumbnail = get_thumb("search", auto = True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def movies(item):
    itemlist = []
    infoLabels = ''
    data = load_data(item.url)
    pattern = 'class="poster"><img src="([^"]+)" alt="([^"]+)".*?'
    pattern += '</span> (.*?)</div>.*?'
    pattern += 'href="([^"]+)".*?'
    pattern += '<span>(\d+)</span>.*?'

    matches = scrapertools.find_multiple_matches(data, pattern)
    for img, title, ranking, link, age in matches:
        itemTitle = "%s [COLOR yellow](%s)[/COLOR] [COLOR blue](%s)[/COLOR]" % (title, ranking, age)
        itemlist.append(Item(channel = item.channel, title=itemTitle, contentTitle=title, thumbnail=img, 
            url=link, action="findvideos", language="LAT", infoLabels={'year':age}))

    next_page = scrapertools.find_single_match(data, 'href="([^"]+)" ><span class="icon-chevron-right">')
    if next_page:
        itemlist.append(Item(channel = item.channel, title="Siguiente Pagina", 
            url=next_page, action="movies"))

    tmdb.set_infoLabels(itemlist, True)

    return itemlist

def moviesIMDB(item):
    itemlist = []

    data = load_data(item.url)
    pattern = '"poster"><a href="([^"]+)"><img src="([^"]+)".*?'
    pattern += 'class="puesto">(\d+)</div>.*?'
    pattern += '"rating">(.*?)</div>.*?'
    pattern += '"title">.*?>(.*?)</a>'

    matches = scrapertools.find_multiple_matches(data, pattern)
    for link, img, rank, rating, title in matches:
        itemTitle = "[COLOR blue](#%s)[/COLOR] %s [COLOR yellow](%s)[/COLOR]" % (rank, title, rating)
        img = img.replace('-90x135', '')

        itemlist.append(Item(channel = item.channel, title=itemTitle, contentTitle=title, thumbnail=img, 
            url=link, action="findvideos", language="LAT", infoLabels={'year': '-'}))

    tmdb.set_infoLabels(itemlist, True)
    
    return itemlist

def byLetter(item):
    itemlist = []
    letter = item.extra

    pageForNonce = load_data(item.url)
    nonce = scrapertools.find_single_match(pageForNonce, '"nonce":"([^"]+)"')
    raw = httptools.downloadpage('http://cuevana2espanol.com/wp-json/dooplay/glossary/?term=%s&nonce=%s&type=all' % (letter, nonce)).data
    json = jsontools.load(raw)
    #logger.info(nonce)
    if 'error' not in json:
        for movie in json.items():
            data = movie[1]
            itemTitle = data['title']
            year = data.get('year', '-')
            if 'year' in data:
                itemTitle += " [COLOR blue](%s)[/COLOR]" % year
            if data['imdb']:
                itemTitle += " [COLOR yellow](%s)[/COLOR]" % data['imdb']

            itemlist.append(Item(channel = item.channel, title=itemTitle, contentTitle=data['title'], url=data['url'], 
                                 thumbnail=data['img'].replace('-90x135', ''), action="findvideos",
                                 language="LAT", infoLabels={'year': year}))

    tmdb.set_infoLabels(itemlist, True)

    return itemlist

def letters(item):
    itemlist = []
    letter = '#ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    for let in letter:
        itemlist.append(item.clone(title=let, extra=let.lower(), action="byLetter"))

    return itemlist

def searchMovies(item):
    itemlist = []

    data = load_data(item.url)
    pattern = 'class="image">.*?href="([^"]+)".*?'
    pattern += 'src="([^"]+)" alt="([^"]+)".*?'
    pattern += 'class="year">(\d+)</span>.*?'
    pattern += '<p>(.*?)</p>'

    matches = scrapertools.find_multiple_matches(data, pattern)
    for link, img, title, year, plot in matches:
        itemTitle = "%s [COLOR blue](%s)[/COLOR]" % (title, year)
        fullimg = img.replace('-150x150', '')
        itemlist.append(Item(channel = item.channel, title=itemTitle, contentTitle=title,
                             thumbnail=fullimg, url=link, plot=plot, action="findvideos",
                             language="LAT", infoLabels={'year': year}))

    next_page = scrapertools.find_single_match(data, 'href="([^"]+)" ><span class="icon-chevron-right">')
    if next_page:
        itemlist.append(Item(channel = item.channel, title="Siguiente Pagina", 
            url=next_page, action="searchMovies"))

    tmdb.set_infoLabels(itemlist, True)

    return itemlist

def search(item, text):
    text = text.lower().replace(' ', '+')
    item.url += text

    return searchMovies(item)

def RedirectLink(hash):
    hashdata = urllib.urlencode({r'url':hash})
    return redirect_url('https://player.cuevana2espanol.com/r.php', parameters=hashdata)

def GKPluginLink(hash):
    hashdata = urllib.urlencode({r'link':hash})
    try:
        json = httptools.downloadpage('https://player.cuevana2espanol.com/plugins/gkpluginsphp.php', post=hashdata).data
    except:
        return None
    #logger.info(jsontools.load(json))

    data = jsontools.load(json) if json else False
    if data:
        return data['link'] if 'link' in data else None
    else:
        return None

def OpenloadLink(hash):
    hashdata = urllib.urlencode({r'h':hash})
    json = httptools.downloadpage('https://cuevana2espanol.com/openload/api.php', post=hashdata).data
    data = jsontools.load(json) if json else False
    return data['url'] if data['status'] == 1 else None

def getContent(item, data):
    item.infoLabels["year"] = scrapertools.find_single_match(data, 'class="date">.*?(\d+)</span>')
    item.plot = scrapertools.find_single_match(data, 'class="wp-content"><p>(.*?)</p>')
    genres = ''
    for genre in scrapertools.find_multiple_matches(data, '/genero/.*?"tag">(.*?)</a>'):
        genres += genre + ', '

    item.infoLabels['genre'] = genres.strip(', ')

def findvideos(item):
    logger.info()
    itemlist = []

    data = load_data(item.url)
    getContent(item, data)
    """
    if item.extra:
        getContentShow(data, item)
    else:
        getContentMovie(data, item)
    """
    pattern = '<div id="option-(\d)".*?<iframe class="metaframe rptss" src="([^"]+)"'

    #itemlist.append(Item(channel = item.channel, title=item.url))
    for option, link in scrapertools.find_multiple_matches(data, pattern):
        #php.*?=(\w+)&
        #url=(.*?)&
        server = ""
        sname = scrapertools.find_single_match(data, 'href="#option-%s"><b class="icon-play_arrow"></b> Servidor (\w+)' % option)
        sname = sname.replace("Siempre", "SO")
        title = "[COLOR blue]Servidor "+sname+" [%s][/COLOR]"
        if 'player' in link:
            #~logger.info("CUEVANA LINK %s" % link)
            #fembed y rapidvideo
            if r'irgoto.php' in link:
                link = scrapertools.find_single_match(link, 'php\?url=(.*)').replace('%3A', ':').replace('%2F', '/')
                link = RedirectLink(link)
                if not link:
                    continue
                server = servertools.get_server_from_url(link)
                
            #vanlong
            elif r'irgotogd' in link:
                link = redirect_url('https:'+link, scr=True)
                server = "directo"

            #openloadpremium m3u8
            elif r'irgotoolp' in link:
                #deshabilitar por ahora
                continue
                link = redirect_url('https:'+link)
                server = "directo"
            
            #openloadpremium no les va en la web, se hace un fix aqui
            elif r'irgotogp' in link:
                link = scrapertools.find_single_match(data, r'irgotogd.php\?url=(\w+)')
                #link = redirect_url('https:'+link, "", True)
                link = GKPluginLink(link)
                server = "directo"
            elif r'gdv.php' in link:
                # google drive hace lento la busqueda de links, ademas no es tan buena opcion y es el primero que eliminan
                continue
            #amazon y vidcache, casi nunca van
            else:
                link = scrapertools.find_single_match(link, 'php.*?file=(\w+)')
                link = GKPluginLink(link)
                server = "directo"
            
        elif r'openload' in link:
            link = scrapertools.find_single_match(link, '\?h=(\w+)')
            link = OpenloadLink(link)
            server = "openload"
        elif 'youtube' in link:
            title = "[COLOR yellow]Ver Trailer (%s)[/COLOR]"
            server = "youtube"
        else: # En caso de que exista otra cosa no implementada, reportar si no aparece pelicula
            continue

        if not link:
            continue
        # GKplugin puede devolver multiples links con diferentes calidades, si se pudiera colocar una lista de opciones
        # personalizadas para Directo, se agradece, por ahora solo devuelve el primero que encuentre
        if type(link) is list:
            link = link[0]['link']
        #if r'chomikuj.pl' in link:
            # En algunas personas la opcion CH les da error 401
            #link += "|Referer=https://player4.cuevana2.com/plugins/gkpluginsphp.php" 
        itemlist.append(
            item.clone(title=title % server.capitalize(), server=server,
                       url=link, action='play'))

    #itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist):
                itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="yellow",
                                     action="add_pelicula_to_library", url=item.url, thumbnail = item.thumbnail,
                                     contentTitle = item.contentTitle
                                     ))
    return itemlist
