# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import logger

host = "https://jkanime.net"

def mainlist(item):
    logger.info()
    itemlist = list()
    itemlist.append(Item(channel=item.channel, action="ultimas_series", title="Últimas Series", url=host))
    itemlist.append(Item(channel=item.channel, action="ultimos_episodios", title="Últimos Episodios", url=host))
    itemlist.append(Item(channel=item.channel, action="p_tipo", title="Listado Alfabetico", url=host, extra="Animes por letra"))
    itemlist.append(Item(channel=item.channel, action="p_tipo", title="Listado por Genero", url=host, extra="Animes por Genero"))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar"))
    return itemlist


def ultimas_series(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, 'Últimos Animes agregados</h3></div>.*?</div><!-- .content-box -->')
    patron  = '<a title="([^"]+).*?'
    patron += 'href="([^"]+)".*?'
    patron += 'src="([^"]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedtitle, scrapedurl, scrapedthumbnail in matches:
        itemlist.append(
            Item(channel=item.channel, action="episodios", title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail,
                 show=scrapedtitle))
    tmdb.set_infoLabels(itemlist)
    return itemlist


def search(item, texto):
    logger.info()
    if item.url == "":
        item.url = host + "/buscar/%s/"
    texto = texto.replace(" ", "+")
    item.url = item.url % texto
    try:
        return series(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def ultimos_episodios(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    #data = scrapertools.find_single_match(data, '<ul class="latestul">(.*?)</ul>')
    patron = '<a class="odd" title="([^"]+).*?'
    patron += 'href="([^"]+)".*?'
    patron += 'img src="([^"]+)".*?'
    patron += 'Episodio.*?(\d+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedtitle, scrapedurl, scrapedthumbnail, scrapedepisode in matches:
        title = scrapedtitle + " - Episodio " + scrapedepisode
        itemlist.append(
            Item(channel=item.channel, action="findvideos", title=title, url=scrapedurl, thumbnail=scrapedthumbnail,
                 show=scrapedtitle))
    tmdb.set_infoLabels(itemlist)
    return itemlist


def p_tipo(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, '<h3>%s(.*?)</ul>' %item.extra)
    patron  = 'href="([^"]+)".*?'
    patron += 'title.*?>([^<]+)</a>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle in matches:
        if "Por Genero" not in scrapedtitle:
            itemlist.append(
                Item(channel=item.channel, action="series", title=scrapedtitle, url=host + scrapedurl,
                     viewmode="movie_with_plot"))
    return itemlist


def series(item):
    logger.info()
    # Descarga la pagina
    data = httptools.downloadpage(item.url).data
    # Extrae las entradas
    patron  = '<a title="([^"]+)" href="([^"]+)" rel="nofollow">.*?'
    patron += 'src="([^"]+)".*?'
    patron += 'eps-num">([^<]+)</span>.*?'
    patron += '<p>([^\<]+)</p>'
    matches = scrapertools.find_multiple_matches(data, patron)
    itemlist = []
    for scrapedtitle, scrapedurl, scrapedthumbnail, scrapedepisode, scrapedplot in matches:
        title = scrapedtitle + " (" + scrapedepisode + ")"
        scrapedthumbnail = scrapedthumbnail.replace("thumbnail", "image")
        plot = scrapertools.htmlclean(scrapedplot)
        itemlist.append(Item(channel=item.channel, action="episodios", title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail, fanart=scrapedthumbnail,
                 plot=scrapedplot, show=scrapedtitle))
    tmdb.set_infoLabels(itemlist)
    try:
        siguiente = scrapertools.find_single_match(data, '<a class="text nav-next" href="([^"]+)"')
        scrapedurl = siguiente
        scrapedtitle = ">> Pagina Siguiente"
        scrapedthumbnail = ""
        scrapedplot = ""
        if len(itemlist)>0:
            itemlist.append(
                Item(channel=item.channel, action="series", title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail,
                     plot=scrapedplot, folder=True, viewmode="movie_with_plot"))
    except:
        pass
    return itemlist


def get_pages_and_episodes(data):
    results = scrapertools.find_multiple_matches(data, 'href="#pag([0-9]+)".*?>[0-9]+ - ([0-9]+)')
    if results:
        return int(results[-1][0]), int(results[-1][1])
    return 1, 0


def episodios(item):
    logger.info()
    itemlist = []
    # Descarga la pagina
    data = httptools.downloadpage(item.url).data
    scrapedplot = scrapertools.find_single_match(data, '<meta name="description" content="([^"]+)"/>')
    scrapedthumbnail = scrapertools.find_single_match(data, '<div class="separedescrip">.*?src="([^"]+)"')
    idserie = scrapertools.find_single_match(data, "ajax/pagination_episodes/(\d+)/")
    logger.info("idserie=" + idserie)
    if " Eps" in item.extra and "Desc" not in item.extra:
        caps_x = item.extra
        caps_x = caps_x.replace(" Eps", "")
        capitulos = int(caps_x)
        paginas = capitulos / 10 + (capitulos % 10 > 0)
    else:
        paginas, capitulos = get_pages_and_episodes(data)
    for num_pag in range(1, paginas + 1):
        numero_pagina = str(num_pag)
        headers = {"Referer": item.url}
        data2 = httptools.downloadpage(host + "/ajax/pagination_episodes/%s/%s/" % (idserie, numero_pagina),
                                        headers=headers).data
        patron = '"number"\:"(\d+)","title"\:"([^"]+)"'
        matches = scrapertools.find_multiple_matches(data2, patron)
        for numero, scrapedtitle in matches:
            title = scrapedtitle.strip()
            url = item.url + numero
            plot = scrapedplot
            itemlist.append(item.clone(action="findvideos", title=title, url=url, plot=plot))
    if len(itemlist) == 0:
        try:
            itemlist.append(Item(channel=item.channel, action="findvideos", title="Serie por estrenar", url="",
                                 thumbnail=scrapedthumbnail, fanart=scrapedthumbnail, plot=scrapedplot,
                                 server="directo", folder=False))
        except:
            pass
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    aux_url = []
    data = httptools.downloadpage(item.url).data
    list_videos = scrapertools.find_multiple_matches(data, '<iframe class="player_conte" src="([^"]+)"')
    list_down = scrapertools.find_multiple_matches(data, "blank\" href='(.*?)'>Descargar")
    index = 1
    for e in list_videos:
        if e.startswith(host + "/jk") or "um.php" in e:
            headers = {"Referer": item.url}
            data = httptools.downloadpage(e, headers=headers).data
            url = scrapertools.find_single_match(data, '<embed class="player_conte".*?&file=([^\"]+)\"')
            if "um.php?" in e:
                url = decode_url(data)
            
            if not url:
                url = scrapertools.find_single_match(data, 'source src="([^\"]+)\"')

            if not url:
                url = scrapertools.find_single_match(data, '<iframe class="player_conte" src="([^\"]+)\"')

            if "jkanime" in url:
                url = httptools.downloadpage(url, follow_redirects=False, only_headers=True).headers.get("location", "")

            if url:
                itemlist.append(item.clone(title="Enlace encontrado en server #" + str(index) + " (%s)", url=url, action="play"))
                index += 1
        else:
            aux_url.append(item.clone(title="Enlace encontrado (%s)", url=e, action="play"))
    
    for d in list_down:
        aux_url.append(item.clone(title="Enlace encontrado (%s)", url=d, action="play"))
    itemlist.extend(aux_url)
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    for videoitem in itemlist:
        videoitem.contentTitle = item.contentTitle
        videoitem.channel = item.channel
        videoitem.thumbnail = item.thumbnail
    return itemlist

def btoa(s):
    import base64
    return base64.b64encode(s.to_string().value)
    
def decode_url(data):
    import js2py
    import re
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    js = scrapertools.find_single_match(data, '<script>(l.*?)</script>')
    
    part = js.split("+ll")
    part0 = part[1].split("String['fromCharCode'")[0]
    part1 = part[1].replace(part0, "")
    part1 = re.sub(r'(l.*?)\(\(\[', 'window.btoa(([', part1)
    logger.info("zebiiiii-%s" % part1)
    context = js2py.EvalJs({ "btoa": btoa });
    url = "htt%s" % context.eval(part1)
    logger.info(url)
    return url
