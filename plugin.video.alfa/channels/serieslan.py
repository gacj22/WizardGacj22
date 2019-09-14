# -*- coding: utf-8 -*-

import re

from channels import renumbertools
from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channels import filtertools
from channels import autoplay
from lib import gktools

IDIOMAS = {'latino': 'Latino'}
list_language = IDIOMAS.values()
list_servers = ['openload'
                ]
list_quality = ['default']


host = "https://serieslan.com"


def mainlist(item):
    logger.info()
    thumb_series = get_thumb("channels_tvshow.png")
    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(
        Item(channel=item.channel, action="lista", title="Series", contentSerieName="Series", url=host, thumbnail=thumb_series, page=0))
    itemlist.append(
        Item(channel=item.channel, action="lista", title="Live Action", contentSerieName="Live Action", url=host+"/liveaction", thumbnail=thumb_series, page=0))
    #TODO buscar solucion para reproducion peliculas (findvideos+js2py)
    #itemlist.append(
    #    Item(channel=item.channel, action="peliculas", title="Películas", contentSerieName="Películas", url=host+"/peliculas", thumbnail=thumb_series, page=0))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar",
                         thumbnail=thumb_series))
    itemlist = renumbertools.show_option(item.channel, itemlist)
    autoplay.show_option(item.channel, itemlist)
    return itemlist

def search(item, texto):
    logger.info()
    #texto = texto.replace(" ", "+")
    item.url = host +"/buscar.php"
    item.texto = texto
    if texto != '':
        return sub_search(item)
    else:
        return []

def sub_search(item):
    logger.info()
    itemlist = []
    post = "k=" + item.texto
    results = httptools.downloadpage(item.url, post=post).json
    if not results:
        return itemlist
    for result in results:
        scrapedthumbnail = host + "/tb/" + result[0] + ".jpg"
        scrapedtitle = result[1]
        scrapedurl = host + "/" + result[2]

        context = renumbertools.context(item)
        context2 = autoplay.context
        context.extend(context2)
        try:
            scrapedyear = result[3]
        except:
            scrapedyear = ''
        filtro_tmdb = {"first_air_date": scrapedyear}.items()
        itemlist.append(item.clone(action = "episodios",
                                   title = scrapedtitle,
                                   thumbnail = scrapedthumbnail,
                                   url = scrapedurl,
                                   context=context,
                                   contentSerieName = scrapedtitle,
                                   infoLabels={'filtro':filtro_tmdb}
                        ))
    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    return itemlist

def lista(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<a href="([^"]+)" '
    if item.contentSerieName == "Series":
        patron += 'class="link">.+?<img src="([^"]+)".*?'
    else:
        patron += 'class="link-la">.+?<img src="([^"]+)".*?'
    patron += 'title="([^"]+)">'
    if item.url==host or item.url==host+"/liveaction":
        a=1
    else:
        num=(item.url).split('-')
        a=int(num[1])
    matches = scrapertools.find_multiple_matches(data, patron)

    # Paginacion
    num_items_x_pagina = 30
    min = item.page * num_items_x_pagina
    min=min-item.page
    max = min + num_items_x_pagina - 1
    b=0
    for link, img, name in matches[min:max]:
        b=b+1
        if " y " in name:
            title=name.replace(" y "," & ")
        else:
            title = name
        url = host + link
        scrapedthumbnail = host + img
        context = renumbertools.context(item)
        context2 = autoplay.context
        context.extend(context2)
        
        itemlist.append(item.clone(title=title, url=url, action="episodios", thumbnail=scrapedthumbnail, show=title,contentSerieName=title,
                                   context=context))
    if b<29:
        a=a+1
        url=host+"/pag-"+str(a)
        if b>10:
            itemlist.append(
                Item(channel=item.channel, contentSerieName=item.contentSerieName, title="[COLOR cyan]Página Siguiente >>[/COLOR]", url=url, action="lista", page=0))
    else:    
        itemlist.append(
             Item(channel=item.channel, contentSerieName=item.contentSerieName, title="[COLOR cyan]Página Siguiente >>[/COLOR]", url=item.url, action="lista", page=item.page + 1))

    tmdb.set_infoLabels(itemlist)
    return itemlist

def peliculas(item):
    logger.info()

    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<div class="pel play" dt="(.+?)" .+?><img src="(.+?)" .+? title="(.*?)"><span class=".+?">(.+?)<\/span><a href="(.+?)" class.+?>'
    matches = scrapertools.find_multiple_matches(data, patron)
    # Paginacion
    num_items_x_pagina = 30
    min = item.page * num_items_x_pagina
    min=min-item.page
    max = min + num_items_x_pagina - 1
    b=0
    for scrapedplot,scrapedthumbnail, scrapedtitle, scrapedyear, scrapedurl in matches[min:max]:
        b=b+1
        url = host + scrapedurl
        thumbnail = host +scrapedthumbnail
        #context = renumbertools.context(item)
        context = autoplay.context
        #context.extend(context2)
        title = "%s [COLOR darkgrey](%s)[/COLOR]" % (scrapedtitle, scrapedyear)
        
        itemlist.append(item.clone(title=title, url=url, action="findvideos", thumbnail=thumbnail, plot=scrapedplot,
                                   contentTitle=scrapedtitle, context=context, infoLabels={'year': scrapedyear}))
    if b<29:
        pass
    else:    
        itemlist.append(
             Item(channel=item.channel, contentTitle=item.contentTitle, title="[COLOR cyan]Página Siguiente >>[/COLOR]", url=item.url, action="peliculas", page=item.page + 1))

    tmdb.set_infoLabels(itemlist)
    return itemlist

def episodios(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    # obtener el numero total de episodios
    total_episode = 0

    patron_caps = '<li><span><strong>Capitulo <\/strong>(\d+).*? -<\/span>(.+?)<\/li><\/a><a href="(.*?)">'
    matches = scrapertools.find_multiple_matches(data, patron_caps)
    patron_info = '<img src="([^"]+)">.+?</span>(.*?)</p>.*?<h2>Reseña:</h2><p>(.*?)</p>'
    scrapedthumbnail, show, scrapedplot = scrapertools.find_single_match(data, patron_info)
    scrapedthumbnail = host + scrapedthumbnail
    
    for cap, name, link in matches:

        title = ""
        pat = "/"
        if "Mike, Lu & Og"==item.title:
            pat="&/"
        if "KND" in item.title:
            pat="-"
        # varios episodios en un enlace
        if len(name.split(pat)) > 1:
            i = 0
            for pos in name.split(pat):
                i = i + 1
                total_episode += 1
                season, episode = renumbertools.numbered_for_tratk(item.channel, item.contentSerieName, 1, total_episode)
                if len(name.split(pat)) == i:
                    title += "%sx%s " % (season, str(episode).zfill(2))
                else:
                    title += "%sx%s_" % (season, str(episode).zfill(2))
        else:
            total_episode += 1
            season, episode = renumbertools.numbered_for_tratk(item.channel,item.contentSerieName, 1, total_episode)

            title += "%sx%s " % (season, str(episode).zfill(2))

        url = host + "/" + link
        
        if "disponible" in link:
            title += "No Disponible aún"
        else:
            title += name
            itemlist.append(
                item.clone(action="findvideos", title=title, url=url, plot=scrapedplot))

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel, title="[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]", url=item.url,
                             action="add_serie_to_library", extra="episodios", show=show))

    return itemlist

def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    _sa = scrapertools.find_single_match(data, 'var _sa = (true|false);')
    _sl = scrapertools.find_single_match(data, 'var _sl = ([^;]+);')
    sl = eval(_sl)
    buttons = scrapertools.find_multiple_matches(data, '<button.*?class="selop" sl="([^"]+)">')
    if not buttons:
        buttons = [0,1,2]
    for id in buttons:
        title = '%s'
        new_url = golink(int(id), _sa, sl)
        data_new = httptools.downloadpage(new_url).data
        matches = scrapertools.find_multiple_matches(data_new, 'javascript">(.*?)</script>')
        js = ""
        for part in matches:
            js += part
        #logger.info("test before:" + js)

        try: 
            matches = scrapertools.find_multiple_matches(data_new, '" id="(.*?)" val="(.*?)"')
            for zanga, val in matches:
                js = js.replace('var %s = document.getElementById("%s");' % (zanga, zanga), "")
                js = js.replace('%s.getAttribute("val")' % zanga, '"%s"' % val)
            #logger.info("test1 after:" +js)
        except:
            pass
        
        #v1
        js = re.sub('(document\[.*?)=', 'prem=', js)
        
        #Parcheando a lo bruto v2
        video = scrapertools.find_single_match(js, "sources: \[\{src:(.*?), type")
        js = re.sub(' videojs\((.*?)\);', video+";", js)
        
        import js2py
        js2py.disable_pyimport()
        context = js2py.EvalJs({'atob': atob})
        
        try:
            result = context.eval(js)
        except:
            logger.error("Js2Py no puede desofuscar el codigo, ¿cambió?")
            continue

        url = scrapertools.find_single_match(result, 'src="(.*?)"')
        #v2
        if not url:
            url = result.strip()
        
        itemlist.append(Item(channel=item.channel, title=title, url=url, action='play', language='latino',
                         infoLabels=item.infoLabels))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist

def golink (num, sa, sl):
    import urllib
    b = [3, 10, 5, 22, 31]
    #d = ''
    #for i in range(len(b)):
    #    d += sl[2][b[i]+num:b[i]+num+1]

    SVR = "https://viteca.stream" if sa == 'true' else "http://serieslan.com"
    TT = "/" + urllib.quote_plus(sl[3].replace("/", "><")) if num == 0 else ""
    url_end = link(num,sl)
    #return SVR + "/el/" + sl[0] + "/" + sl[1] + "/" + str(num) + "/" + sl[2] + d + TT
    return SVR + "/el/" + sl[0] + "/" + sl[1] + "/" + str(num) + "/" + sl[2] + url_end + TT

def link(ida,sl):
    a=ida
    b=[3,10,5,22,31]
    c=1
    d=""
    e=sl[2]
    for i in range(len(b)):
      d=d+substr(e,b[i]+a,c)
    return d

def substr(st,a,b):
    return st[a:a+b]
'''
def x92(data1, data2):
    data3 = []
    data4 = 0
    data5 = ""
    data6 = ""
    for i in range(len(256)):
      data3[i] = i
    for i in range(len(256)):
      data4 = (data4 + data3[i] + ord(data1[i])) % 256
      data5 = data3[i]
      data3[i] = data3[data4]
      data3[data4] = data5
    i = 0
    data4 = 0
    for j in range(len(data2)):
        i = (i + 1) % 256
        data4 = (data4 + data3[i]) % 256
        data5 = data3[i]
        data3[i] = data3[data4]
        data3[data4] = data5
        data6 =1#+= str(unichr(data2[ord(str(j)) ^ data3[(data3[i] + data3[data4]) % 256]))
    return data6

def _ieshlgagkP(umZFJ):
    return umZFJ
def _RyHChsfwdd(ZBKux):
    return ZBKux
def _eladjkKtjf(czuwk):
    return czuwk
def _slSekoKrHb():
    return ''
def _VySdeBApGO():
    return 'Z'

def _nEgqhkiRub():
    return 28

def _lTjZxWGNnE():
    return 57
'''
def atob(s):
    import base64
    return base64.b64decode(s.to_string().value)
