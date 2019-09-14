# -*- coding: utf-8 -*-

import re
import sys
import urllib
import urlparse
import time

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import tmdb
from lib import generictools
from channels import filtertools
from channels import autoplay


#IDIOMAS = {'CAST': 'Castellano', 'LAT': 'Latino', 'VO': 'Version Original'}
IDIOMAS = {'Castellano': 'CAST', 'Latino': 'LAT', 'Version Original': 'VO'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['torrent']

host = 'https://www.divxtotal3.net/'
domain = 'www.divxtotal3.net'
channel = 'divxtotal'
categoria = channel.capitalize()
color1, color2, color3 = ['0xFF58D3F7', '0xFF2E64FE', '0xFF0404B4']
__modo_grafico__ = config.get_setting('modo_grafico', channel)
modo_ultima_temp = config.get_setting('seleccionar_ult_temporadda_activa', channel)        #Actualización sólo últ. Temporada?
timeout = config.get_setting('timeout_downloadpage', channel)

headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3', 'Accept-Encoding': 'gzip, deflate, br', 'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36', 'Referer': 'https://www.divxtotal3.net/peliculas-15/'}


def mainlist(item):
    logger.info()
    itemlist = []
    
    thumb_cartelera = get_thumb("now_playing.png")
    thumb_pelis_hd = get_thumb("channels_movie_hd.png")
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_buscar = get_thumb("search.png")
    thumb_separador = get_thumb("next.png")
    thumb_settings = get_thumb("setting_0.png")
    
    autoplay.init(item.channel, list_servers, list_quality)

    item.url_plus = "peliculas-15/"
    itemlist.append(Item(channel=item.channel, title="Películas", action="categorias", url=host + item.url_plus, url_plus=item.url_plus, thumbnail=thumb_cartelera, extra="Películas"))
    item.url_plus = "peliculas-hd-3/"
    itemlist.append(Item(channel=item.channel, title="Películas HD", action="categorias", url=host + item.url_plus, url_plus=item.url_plus, thumbnail=thumb_pelis_hd, extra="Películas HD"))
    item.url_plus = "peliculas-dvdr/"
    itemlist.append(Item(channel=item.channel, title="Películas DVDR", action="categorias", url=host + item.url_plus, url_plus=item.url_plus, thumbnail=thumb_pelis_hd, extra="Películas DVDR"))

    itemlist.append(Item(channel=item.channel, url=host, title="", folder=False, thumbnail=thumb_separador))
    
    itemlist.append(Item(channel=item.channel, url=host, title="Series", action="submenu", thumbnail=thumb_series, extra="series"))

    itemlist.append(Item(channel=item.channel, url=host, title="", folder=False, thumbnail=thumb_separador))
    
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + "?s=%s", thumbnail=thumb_buscar, extra="search"))

    itemlist.append(Item(channel=item.channel, url=host, title="[COLOR yellow]Configuración:[/COLOR]", folder=False, thumbnail=thumb_separador))
    
    itemlist.append(Item(channel=item.channel, action="configuracion", title="Configurar canal", thumbnail=thumb_settings))
    
    autoplay.show_option(item.channel, itemlist)            #Activamos Autoplay

    return itemlist
    
    
def configuracion(item):
    from platformcode import platformtools
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return

    
def submenu(item):
    logger.info()
    itemlist = []
    
    thumb_series = get_thumb("channels_tvshow.png")

    if item.extra == "series":
        data = ''
        try:
            data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url, timeout=timeout, headers=headers).data)
            data = js2py_conversion(data, item.url)
            data = unicode(data, "utf-8", errors="replace").encode("utf-8")
        except:
            pass

        patron = '<ul class="nav navbar-nav">.*?<li><a href="[^"]+\/(series[^\/]+\/)">Series<\/a><\/li>'
        item.url_plus = scrapertools.find_single_match(data, patron)
        if not item.url_plus: item.url_plus = 'series-16/'
        itemlist.append(item.clone(title="Series completas", action="listado", url=item.url + item.url_plus, url_plus=item.url_plus, thumbnail=thumb_series, extra="series"))
        itemlist.append(item.clone(title="Alfabético A-Z", action="alfabeto", url=item.url + item.url_plus + "?s=letra-%s", url_plus=item.url_plus, thumbnail=thumb_series, extra="series"))

    return itemlist
    

def categorias(item):
    logger.info()
    
    itemlist = []
    
    if item.extra3:
        extra3 = item.extra3
        del item.extra3
    else:
        extra3 = False
    
    data = ''
    try:
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url, timeout=timeout, headers=headers).data)
        data = js2py_conversion(data, item.url)
        data = unicode(data, "utf-8", errors="replace").encode("utf-8")
    except:
        pass
        
    patron = '<li><a class="alist" href="([^"]+)">(.*?)<\/a><\/li>'
    #Verificamos si se ha cargado una página, y si además tiene la estructura correcta
    if not data or not scrapertools.find_single_match(data, patron):
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            for clone_inter, autoridad in item.intervencion:
                thumb_intervenido = get_thumb(autoridad)
                itemlist.append(item.clone(action='', title="[COLOR yellow]" + clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial + '. Reportar el problema en el foro', thumbnail=thumb_intervenido))
            return itemlist                                                     #Salimos
        
        logger.error("ERROR 01: SUBMENU: La Web no responde o ha cambiado de URL: " + item.url + data)
        #Si no hay datos consistentes, llamamos al método de fail_over para que encuentre un canal que esté activo y pueda gestionar el submenú
    
    if not data:    #Si no ha logrado encontrar nada, salimos
        itemlist.append(item.clone(action='', title=item.category + ': ERROR 01: SUBMENU: La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
        return itemlist                                 #si no hay más datos, algo no funciona, pintamos lo que tenemos

    matches = re.compile(patron, re.DOTALL).findall(data)

    if not matches:
        logger.error("ERROR 02: SUBMENU: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.category + ': ERROR 02: SUBMENU: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
        return itemlist                                 #si no hay más datos, algo no funciona, pintamos lo que tenemos

    #logger.debug(item.url_plus)
    #logger.debug(matches)
    
    #Insertamos las cabeceras para todas las peliculas de la Aalidad, por Año, Alfabético, por Género, y Otras Calidades
    if not extra3:
        itemlist.append(item.clone(title="Todas las " + item.extra.upper(), action="listado"))
        itemlist.append(item.clone(title="Alfabético A-Z", action="alfabeto", url=item.url + "?s=letra-%s"))
        #itemlist.append(item.clone(title="Géneros", url=item.url))
    
    for scrapedurl, scrapedtitle in matches:
        if item.url_plus not in scrapedurl:
            continue
        if "Todas" in scrapedtitle:
            continue
        
        title = scrapedtitle.strip()

        #Preguntamos por las entradas que corresponden al "extra"
        if extra3 == 'now':
            if scrapedtitle.lower() in ['ac3 51', 'bluray rip', 'series', 'serie', 'subtitulada', 'vose', 'bdrip', 'dvdscreener', 'brscreener r6', 'brscreener', 'webscreener', 'dvd', 'hdrip', 'screener', 'screeer', 'webrip', 'brrip', 'dvb', 'dvdrip', 'dvdsc', 'dvdsc - r6', 'hdts', 'hdtv', 'kvcd', 'line', 'ppv', 'telesync', 'ts hq', 'ts hq proper', '480p', '720p', 'ac3', 'bluray', 'camrip', 'ddc', 'hdtv - screener', 'tc screener', 'ts screener', 'ts screener alto', 'ts screener medio', 'vhs screener']:
                itemlist.append(item.clone(action="listado", title=title, url=scrapedurl, extra2="categorias"))
        
        elif scrapedtitle.lower() in ['ac3 51', 'bluray rip', 'series', 'serie', 'subtitulada', 'vose', 'bdrip', 'dvdscreener', 'brscreener r6', 'brscreener', 'webscreener', 'dvd', 'hdrip', 'screener', 'screeer', 'webrip', 'brrip', 'dvb', 'dvdrip', 'dvdsc', 'dvdsc - r6', 'hdts', 'hdtv', 'kvcd', 'line', 'ppv', 'telesync', 'ts hq', 'ts hq proper', '480p', '720p', 'ac3', 'bluray', 'camrip', 'ddc', 'hdtv - screener', 'tc screener', 'ts screener', 'ts screener alto', 'ts screener medio', 'vhs screener']:
            extra3 = 'next'
            
        else:
            itemlist.append(item.clone(action="listado", title="    " + title.capitalize(), url=scrapedurl, extra2="categorias"))
            
    if extra3 == 'next':
        itemlist.append(item.clone(action="categorias", title="Otras Calidades", url=item.url + '-0-0-fx-1-1-.fx', extra2="categorias", extra3='now'))

    return itemlist
    
    
def alfabeto(item):
    logger.info()
    itemlist = []
    
    itemlist.append(item.clone(action="listado", title="0-9", url=item.url % "0"))

    for letra in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']:
        itemlist.append(item.clone(action="listado", title=letra, url=item.url % letra.lower()))

    return itemlist

    
def listado(item):
    logger.info()
    itemlist = []
    item.category = categoria

    #logger.debug(item)
    
    curr_page = 1                                                               # Página inicial
    last_page = 99999                                                           # Última página inicial
    if item.curr_page:
        curr_page = int(item.curr_page)                                         # Si viene de una pasada anterior, lo usamos
        del item.curr_page                                                      # ... y lo borramos
    if item.last_page:
        last_page = int(item.last_page)                                         # Si viene de una pasada anterior, lo usamos
        del item.last_page                                                      # ... y lo borramos
    
    cnt_tot = 40                                                                # Poner el num. máximo de items por página
    cnt_title = 0                                                               # Contador de líneas insertadas en Itemlist
    inicio = time.time()                                    # Controlaremos que el proceso no exceda de un tiempo razonable
    fin = inicio + 5                                                               # Después de este tiempo pintamos (segundos)
    timeout_search = timeout                                                    # Timeout para descargas
    if item.extra == 'search':
        timeout_search = timeout * 2                                            # Timeout un poco más largo para las búsquedas
        if timeout_search < 5:
            timeout_search = 5                                                  # Timeout un poco más largo para las búsquedas

    #Sistema de paginado para evitar páginas vacías o semi-vacías en casos de búsquedas con series con muchos episodios
    title_lista = []                            # Guarda la lista de series que ya están en Itemlist, para no duplicar lineas
    if item.title_lista:                                    # Si viene de una pasada anterior, la lista ya estará guardada
        title_lista.extend(item.title_lista)                                    # Se usa la lista de páginas anteriores en Item
        del item.title_lista                                                    # ... limpiamos
        
    if not item.extra2:                                                         # Si viene de Catálogo o de Alfabeto
        item.extra2 = ''
    
    next_page_url = item.url
    #Máximo num. de líneas permitidas por TMDB. Máx de 10 segundos por Itemlist para no degradar el rendimiento
    while cnt_title <= cnt_tot * 0.45 and curr_page <= last_page and fin > time.time():
    
        # Descarga la página
        data = ''
        try:
            data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)|&nbsp;", "", httptools.downloadpage(next_page_url, timeout=timeout_search, headers=headers).data)
            data = js2py_conversion(data, next_page_url)
            data = unicode(data, "utf-8", errors="replace").encode("utf-8")
        except:
            pass
        
        curr_page += 1                                                          #Apunto ya a la página siguiente
        if not data and not item.extra2:                                        #Si la web está caída salimos sin dar error
            logger.error("ERROR 01: LISTADO: La Web no responde o ha cambiado de URL: " + item.url + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: LISTADO:.  La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
            break                                       #si no hay más datos, algo no funciona, pintamos lo que tenemos

        #Patrón para todo, menos para Series completas, incluido búsquedas en cualquier caso
        patron = '<tr><td(?: class="[^"]+")?><a href="([^"]+)".?title="([^"]+)".*?<\/a><\/td><td(?: class="[^"]+")?>(?:<a href="[^"]+">)?(.*?)(?:<\/a>)?<\/td><td(?: class="[^"]+")?>.*?<\/td><td(?: class="[^"]+")?>(.*?)<\/td><\/tr>'
        
        #Si son series completas, ponemos un patrón especializado
        if item.extra == 'series':
            patron = '<div class="[^"]+"><p class="[^"]+"><a href="([^"]+)".?title="([^"]+)"><img src="([^"]+)".*?<a href=\'[^\']+\'.?title="([^"]+)".*?<\/p><\/div>'
            
        matches = re.compile(patron, re.DOTALL).findall(data)
        if not matches and not '<p>Lo sentimos, pero que esta buscando algo que no esta aqui. </p>' in data and not item.extra2 and not '<h2>Sin resultados</h2>' in data:                                          #error
            item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
            if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
                item, itemlist = generictools.post_tmdb_episodios(item, itemlist)   #Llamamos al método para el pintado del error
                return itemlist                                                     #Salimos
            
            #logger.error("ERROR 02: LISTADO: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
            logger.error("ERROR 02: LISTADO: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + str(matches))
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + \
                        ': ERROR 02: LISTADO: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
            break                                       #si no hay más datos, algo no funciona, pintamos lo que tenemos
        
        #logger.debug("PATRON: " + patron)
        #logger.debug(matches)
        #logger.debug(data)
        
        #Buscamos la próxima y la última página
        patron_next = "<ul class=\"pagination\">.*?\(current\).*?href='([^']+)'>(\d+)<\/a><\/li>"
        #patron_last = "<ul class=\"pagination\">.*?\(current\).*?href='[^']+'>\d+<\/a><\/li>.*?href='[^']+\/(\d+)\/(?:\?s=[^']+)?'><span aria-hidden='[^']+'>&\w+;<\/span><\/a><\/li><\/ul><\/nav><\/div><\/div><\/div>"
        patron_last = "<ul class=\"pagination\">.*?\(current\).*?href='[^']+'>\d+<\/a><\/li>.*?href='[^']+\/(\d+)\/(?:\?[^']+)?'>(?:\d+)?(?:<span aria-hidden='[^']+'>&\w+;<\/span>)?<\/a><\/li><\/ul><\/nav><\/div><\/div><\/div>"

        try:
            next_page_url, next_page = scrapertools.find_single_match(data, patron_next)
            next_page = int(next_page)
        except:                                                                         #Si no lo encuentra, lo ponemos a 1
            #logger.error('ERROR 03: LISTADO: Al obtener la paginación: ' + patron_next + ' / ' + patron_last + ' / ' + scrapertools.find_single_match(data, "<ul class=\"pagination\">.*?<\/span><\/a><\/li><\/ul><\/nav><\/div><\/div><\/div>"))
            next_page = 1
        #logger.debug('curr_page: ' + str(curr_page) + ' / next_page: ' + str(next_page) + ' / last_page: ' + str(last_page))
        
        if last_page == 99999:                                                          #Si es el valor inicial, buscamos
            try:
                last_page = int(scrapertools.find_single_match(data, patron_last))      #lo cargamos como entero
            except:                                                                     #Si no lo encuentra, lo ponemos a 1
                #logger.error('ERROR 03: LISTADO: Al obtener la paginación: ' + patron_next + ' / ' + patron_last + ' / ' + scrapertools.find_single_match(data, "<ul class=\"pagination\">.*?<\/span><\/a><\/li><\/ul><\/nav><\/div><\/div><\/div>"))
                last_page = next_page
            #logger.debug('curr_page: ' + str(curr_page) + ' / next_page: ' + str(next_page) + ' / last_page: ' + str(last_page))
        
        #Empezamos el procesado de matches
        for scrapedurl, scrapedtitle, cat_ppal, size in matches:
            if "/programas" in scrapedurl or "/otros" in scrapedurl:
                continue
            
            title = scrapedtitle
            url = scrapedurl
            title = title.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ü", "u").replace("ï¿½", "ñ").replace("Ã±", "ñ").replace("&atilde;", "a").replace("&etilde;", "e").replace("&itilde;", "i").replace("&otilde;", "o").replace("&utilde;", "u").replace("&ntilde;", "ñ").replace("&#8217;", "'")
            extra = item.extra

            #Si es una búsqueda, convierte los episodios en Series completas, aptas para la Videoteca
            if extra == 'search' and '/series' in scrapedurl and not "Temp" in title and not "emporada" in title:
                if scrapedurl in title_lista:                               #Si ya hemos procesado la serie, pasamos de los episodios adicionales
                    continue

                # Descarga la página del episodio, buscando el enlace a la serie completa
                data_serie = ''
                try:
                    data_serie = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)|&nbsp;", "", httptools.downloadpage(scrapedurl, timeout=timeout, headers=headers).data)
                    data_serie = js2py_conversion(data_serie, scrapedurl)
                    data_serie = unicode(data_serie, "utf-8", errors="replace").encode("utf-8")
                except:
                    pass
                
                if not data_serie:                                              #Si la web está caída salimos sin dar error. Pintamos el episodio
                    logger.error("ERROR 01: LISTADO: La Web no responde o ha cambiado de URL: " + scrapedurl + " / SERIE: " + scrapedurl)
                else:
                    patron_serie = '<div id="where_i_am">.*?<a href="[^"]+">.*?<\/a>.*?<a href="([^"]+)">'
                    url = scrapertools.find_single_match(data_serie, patron_serie)      #buscamos la url de la serie completa
                    if url:
                        url = host + url
                        extra = 'series'                                                #es una serie completa    
                        title_lista += [scrapedurl]                                     #la añadimos a la lista de series completas procesadas    
                        title = scrapedurl                                              #salvamos el título de la serie completa
                    else:
                        url = scrapedurl                                                #No se encuentra la Serie, se trata como Episodio suelto

            #cnt_title += 1
            item_local = item.clone()                                                   #Creamos copia de Item para trabajar
            if item_local.tipo:                                                         #... y limpiamos
                del item_local.tipo
            if item_local.totalItems:
                del item_local.totalItems
            if item_local.post_num:
                del item_local.post_num
            if item_local.category:
                del item_local.category
            if item_local.intervencion:
                del item_local.intervencion
            if item_local.viewmode:
                del item_local.viewmode
            item_local.extra2 = True
            del item_local.extra2
            item_local.text_bold = True
            del item_local.text_bold
            item_local.text_color = True
            del item_local.text_color
            if item_local.url_plus:
                del item_local.url_plus
                
            title_subs = []                                                         #creamos una lista para guardar info importante
            item_local.language = []                                                #creamos lista para los idiomas
            item_local.quality = ''                                                 #iniciamos calidad   
            quality_alt = ''
            if 'series' in cat_ppal or extra == 'series':                                            
                item_local.thumbnail = cat_ppal                                     #si son series, contiene el thumb
            else:
                quality_alt = scrapedurl.lower().strip()                            #si no son series, contiene la calidad
                item_local.thumbnail = ''                                           #guardamos el thumb
            item_local.extra = extra                                                #guardamos el extra procesado    
            item_local.url = url                                                    #guardamos la url final
            item_local.context = "['buscar_trailer']"
            
            item_local.contentType = "movie"                                        #por defecto, son películas
            item_local.action = "findvideos"
            
            #Analizamos los formatos de la películas
            if '/peliculas/' in scrapedurl or item_local.extra == 'Películas':
                item_local.quality = 'HDRip '
            elif '/peliculas-hd' in scrapedurl or item_local.extra == 'Películas HD':
                item_local.quality = 'HD '
            elif '/peliculas-dvdr' in scrapedurl or item_local.extra == 'Películas DVDR':
                item_local.quality = 'DVDR '
            elif 'subtituladas' in cat_ppal or item_local.extra == 'VOSE' or 'vose' in title.lower():
                item_local.language += ['VOSE']
            elif 'Version Original' in cat_ppal or item_local.extra == 'VO' or 'vo' in title.lower():
                item_local.language += ['VO']

            #Analizamos los formatos de series, temporadas y episodios
            elif '/series' in scrapedurl or item_local.extra == 'series':
                item_local.contentType = "tvshow"
                item_local.action = "episodios"
                item_local.season_colapse = True                                    #Muestra las series agrupadas por temporadas
            elif item_local.extra == 'episodios':
                item_local.contentType = "episode"
                item_local.extra = "episodios"
                if "Temp" in title or "emporada" in title:
                    try:
                        item_local.contentSeason = int(scrapertools.find_single_match(title, '[t|T]emp.*?(\d+)'))
                    except:
                        item_local.contentSeason = 1
                    title = re.sub(r'[t|T]emp.*?\d+', '', title)
                    title_subs += ["Temporada"]
                    item_local.contentType = "season"
                    item_local.extra = "season"

            if item_local.contentType == "movie":                                   #para las peliculas ponemos el mismo extra
                item_local.extra = "peliculas"
                
            #Detectamos idiomas
            if "latino" in scrapedurl.lower() or "latino" in title.lower():
                item_local.language += ['LAT']
            elif "vose" in scrapedurl.lower() or "vos" in scrapedurl.lower() or "vose" in title.lower() or "vos" in title.lower():
                item_local.language += ['VOSE']
            
            if item_local.language == []:
                item_local.language = ['CAST']

            #Detectamos el año
            patron = '(\d{4})\s*?(?:\)|\])?$'
            item_local.infoLabels["year"] = '-'
            year = ''
            year = scrapertools.find_single_match(title, patron)
            if year:
                title_alt = re.sub(patron, "", title)
                title_alt = title_alt.strip()
                if title_alt:
                    title = title_alt
                try:
                    year = int(year)
                    if year >= 1970 and year <= 2040:
                        item_local.infoLabels["year"] = year
                except:
                    pass
            
            #Detectamos info importante a guardar para después de TMDB
            if scrapertools.find_single_match(title, '[m|M].*?serie'):
                title = re.sub(r'[m|M]iniserie', '', title)
                title_subs += ["Miniserie"]
            if scrapertools.find_single_match(title, '[s|S]aga'):
                title = re.sub(r'[s|S]aga', '', title)
                title_subs += ["Saga"]
            if scrapertools.find_single_match(title, '[c|C]olecc'):
                title = re.sub(r'[c|C]olecc...', '', title)
                title_subs += ["Colección"]
            
            #Empezamos a limpiar el título en varias pasadas
            patron = '\s?-?\s?(line)?\s?-\s?$'
            regex = re.compile(patron, re.I)
            title = regex.sub("", title)
            title = re.sub(r'\(\d{4}\s*?\)', '', title)
            title = re.sub(r'\[\d{4}\s*?\]', '', title)
            title = re.sub(r'[s|S]erie', '', title)
            title = re.sub(r'- $', '', title)
            title = re.sub(r'\d+[M|m|G|g][B|b]', '', title)
            title = re.sub(r'\[.*?\]', '', title)

            #Limpiamos el título de la basura innecesaria
            title = title.replace("Dual", "").replace("dual", "").replace("Subtitulada", "").replace("subtitulada", "").replace("Subt", "").replace("subt", "").replace("Sub", "").replace("sub", "").replace("(Proper)", "").replace("(proper)", "").replace("Proper", "").replace("proper", "").replace("#", "").replace("(Latino)", "").replace("Latino", "").replace("LATINO", "").replace("Spanish", "").replace("Trailer", "").replace("Audio", "")
            title = title.replace("HDTV-Screener", "").replace("DVDSCR", "").replace("TS ALTA", "").replace("- HDRip", "").replace("(HDRip)", "").replace("- Hdrip", "").replace("(microHD)", "").replace("(DVDRip)", "").replace("HDRip", "").replace("(BR-LINE)", "").replace("(HDTS-SCREENER)", "").replace("(BDRip)", "").replace("(BR-Screener)", "").replace("(DVDScreener)", "").replace("TS-Screener", "").replace(" TS", "").replace(" Ts", "").replace(" 480p", "").replace(" 480P", "").replace(" 720p", "").replace(" 720P", "").replace(" 1080p", "").replace(" 1080P", "").replace("DVDRip", "").replace(" Dvd", "").replace(" DVD", "").replace(" V.O", "").replace(" Unrated", "").replace(" UNRATED", "").replace(" unrated", "").replace("screener", "").replace("TS-SCREENER", "").replace("TSScreener", "").replace("HQ", "").replace("AC3 5.1", "").replace("Telesync", "").replace("Line Dubbed", "").replace("line Dubbed", "").replace("LineDuB", "").replace("Line", "").replace("XviD", "").replace("xvid", "").replace("XVID", "").replace("Mic Dubbed", "").replace("HD", "").replace("V2", "").replace("CAM", "").replace("VHS.SCR", "").replace("Dvd5", "").replace("DVD5", "").replace("Iso", "").replace("ISO", "").replace("Reparado", "").replace("reparado", "").replace("DVD9", "").replace("Dvd9", "")

            #Obtenemos temporada y episodio si se trata de Episodios
            if item_local.contentType == "episode":
                patron = '(\d+)[x|X](\d+)'
                try:
                    item_local.contentSeason, item_local.contentEpisodeNumber = scrapertools.find_single_match(title, patron)
                except:
                    item_local.contentSeason = 1
                    item_local.contentEpisodeNumber = 0
                
                #Si son eisodios múltiples, lo extraemos
                patron1 = '\d+[x|X]\d+.?(?:y|Y|al|Al)?.?\d+[x|X](\d+)'
                epi_rango = scrapertools.find_single_match(title, patron1)
                if epi_rango:
                    item_local.infoLabels['episodio_titulo'] = 'al %s' % epi_rango
                    title = re.sub(patron1, '', title)
                else:
                    title = re.sub(patron, '', title)
                
            #Terminamos de limpiar el título
            title = re.sub(r'\??\s?\d*?\&.*', '', title)
            title = re.sub(r'[\(|\[]\s+[\)|\]]', '', title)
            title = title.replace('()', '').replace('[]', '').strip().lower().title()
            item_local.from_title = title.strip().lower().title()           #Guardamos esta etiqueta para posible desambiguación de título

            #Salvamos el título según el tipo de contenido
            if item_local.contentType == "movie":
                item_local.contentTitle = title
            else:
                item_local.contentSerieName = title.strip().lower().title()
                
            if item_local.contentType == "episode":
                item_local.title = '%sx%s ' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber).zfill(2))
                item_local.extra3 = 'completa'
            else:
                item_local.title = title.strip().lower().title()
                      
            if scrapertools.find_single_match(size, '\d+.\d+\s?[g|G|m|M][b|B]'):
                size = size.replace('b', ' B').replace('B', ' B').replace('b', 'B').replace('g', 'G').replace('m', 'M').replace('.', ',')
                item_local.quality += '[%s]' % size
                
            #Guarda la variable temporal que almacena la info adicional del título a ser restaurada después de TMDB
            item_local.title_subs = title_subs
                
            #Salvamos y borramos el número de temporadas porque TMDB a veces hace tonterias.  Lo pasamos como serie completa
            if item_local.contentSeason and (item_local.contentType == "season" or item_local.contentType == "tvshow"):
                item_local.contentSeason_save = item_local.contentSeason
                del item_local.infoLabels['season']

            #Ahora se filtra por idioma, si procede, y se pinta lo que vale
            if config.get_setting('filter_languages', channel) > 0:     #Si hay idioma seleccionado, se filtra
                itemlist = filtertools.get_link(itemlist, item_local, list_language)
            else:
                itemlist.append(item_local.clone())                     #Si no, pintar pantalla
            
            cnt_title = len(itemlist)                                   #Contador de líneas añadidas
            
            #logger.debug(item_local)

    #Pasamos a TMDB la lista completa Itemlist
    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    
    #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
    item, itemlist = generictools.post_tmdb_listado(item, itemlist)

    # Si es necesario añadir paginacion
    if curr_page <= last_page:
        if last_page:
            title = '%s de %s' % (curr_page-1, last_page)
        else:
            title = '%s' % curr_page-1

        itemlist.append(Item(channel=item.channel, action="listado", title=">> Página siguiente " + title, title_lista=title_lista, url=next_page_url, extra=item.extra, extra2=item.extra2, last_page=str(last_page), curr_page=str(curr_page)))

    return itemlist

    
def findvideos(item):
    logger.info()
    itemlist = []
    itemlist_t = []                                                                 #Itemlist total de enlaces
    itemlist_f = []                                                                 #Itemlist de enlaces filtrados
    if not item.language:
        item.language = ['CAST']                                                    #Castellano por defecto
    matches = []
    item.category = categoria

    #logger.debug(item)

    #Bajamos los datos de la página
    data = ''
    patron = '<a onclick="eventDownloadTorrent\(.*?\)".?class="linktorrent" href="([^"]+)"'
    if item.contentType == 'movie':                                                 #Es una peli
        try:
            data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url, timeout=timeout, headers=headers).data)
            data = js2py_conversion(data, item.url)
            data = unicode(data, "utf-8", errors="replace").encode("utf-8")
        except:
            pass
            
        if not data:
            logger.error("ERROR 01: FINDVIDEOS: La Web no responde o la URL es erronea: " + item.url)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: FINDVIDEOS:.  La Web no responde o la URL es erronea. Si la Web está activa, reportar el error con el log', folder=False))
            if item.emergency_urls and not item.videolibray_emergency_urls:         #Hay urls de emergencia?
                matches = item.emergency_urls[0]                                    #Restauramos matches
                item.armagedon = True                                               #Marcamos la situación como catastrófica 
            else:
                if item.videolibray_emergency_urls:                                 #Si es llamado desde creación de Videoteca...
                    return item                                                     #Devolvemos el Item de la llamada
                else:
                    return itemlist                                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

        if not item.armagedon:                                                      #Si es un proceso normal, seguimos
            matches = re.compile(patron, re.DOTALL).findall(data)
        if not matches:                                                             #error
            item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
            if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
                item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)  #Llamamos al método para el pintado del error
            else:
                logger.error("ERROR 02: FINDVIDEOS: No hay enlaces o ha cambiado la estructura de la Web " + " / PATRON: " + patron + data)
                itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: FINDVIDEOS: No hay enlaces o ha cambiado la estructura de la Web.  Verificar en la Web esto último y reportar el error con el log', folder=False))
            if item.emergency_urls and not item.videolibray_emergency_urls:         #Hay urls de emergencia?
                matches = item.emergency_urls[0]                                    #Restauramos matches
                item.armagedon = True                                               #Marcamos la situación como catastrófica 
            else:
                if item.videolibray_emergency_urls:                                 #Si es llamado desde creación de Videoteca...
                    return item                                                     #Devolvemos el Item de la llamada
                else:
                    return itemlist                                     #si no hay más datos, algo no funciona, pintamos lo que tenemos

    else:                                                                           #Es un episodio
        matches = [item.url]
    
    #logger.debug("PATRON: " + patron)
    #logger.debug(matches)
    #logger.debug(data)
    
    #Si es un lookup para cargar las urls de emergencia en la Videoteca...
    if item.videolibray_emergency_urls:
        item.emergency_urls = [] 
        item.emergency_urls.append(matches)                                         #Salvamnos matches...
        return item                                                                 #... y nos vamos
    
    #Llamamos al método para crear el título general del vídeo, con toda la información obtenida de TMDB
    if not item.videolibray_emergency_urls:
        item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)

    #Ahora tratamos los enlaces .torrent
    for scrapedurl in matches:                                          #leemos los torrents con la diferentes calidades
        #Generamos una copia de Item para trabajar sobre ella
        item_local = item.clone()

        #Buscamos si ya tiene tamaño, si no, los buscamos en el archivo .torrent
        size = scrapertools.find_single_match(item_local.quality, '\s\[(\d+,?\d*?\s\w\s?[b|B])\]')
        if not item.armagedon:
            size = generictools.get_torrent_size(scrapedurl)                                #Buscamos el tamaño en el .torrent
        if size:
            item_local.title = re.sub(r'\s\[\d+,?\d*?\s\w[b|B]\]', '', item_local.title)    #Quitamos size de título, si lo traía
            size = size.replace('GB', 'G·B').replace('Gb', 'G·b').replace('MB', 'M·B')\
                        .replace('Mb', 'M·b').replace('.', ',')
        item_local.quality = re.sub(r'\s\[\d+,?\d*?\s\w\s?[b|B]\]', '', item_local.quality) #Quitamos size de calidad, si lo traía
        item_local.torrent_info = '%s' % size                                               #Agregamos size
        if not item.unify:
            item_local.torrent_info = '[%s]' % item_local.torrent_info.strip().strip(',')
        
        #Ahora pintamos el link del Torrent
        item_local.url = scrapedurl
        if host not in item_local.url and host.replace('https', 'http') not in item_local.url and not item.armagedon:
            item_local.url = host + item_local.url
        if item_local.url and not item.armagedon and item.emergency_urls:
            item_local.torrent_alt = item.emergency_urls[0][0]                      #Guardamos la url del .Torrent ALTERNATIVA
        if item.armagedon:                                                          #Si es catastrófico, lo marcamos
            item_local.quality = '[/COLOR][COLOR hotpink][E] [COLOR limegreen]%s' % item_local.quality
        item_local.title = '[[COLOR yellow]?[/COLOR]] [COLOR yellow][Torrent][/COLOR] ' \
                        + '[COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR] %s' % \
                        (item_local.quality, str(item_local.language),  \
                        item_local.torrent_info)                                    #Preparamos título de Torrent
        
        #Preparamos título y calidad, quitamos etiquetas vacías
        item_local.title = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', item_local.title)    
        item_local.title = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', item_local.title)
        item_local.title = item_local.title.replace("--", "").replace("[]", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()
        item_local.quality = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', item_local.quality)
        item_local.quality = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', item_local.quality)
        item_local.quality = item_local.quality.replace("--", "").replace("[]", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()
        
        item_local.alive = "??"                                                     #Calidad del link sin verificar
        item_local.action = "play"                                                  #Visualizar vídeo
        item_local.server = "torrent"                                               #Seridor Torrent
        
        itemlist_t.append(item_local.clone())                                       #Pintar pantalla, si no se filtran idiomas
        
        # Requerido para FilterTools
        if config.get_setting('filter_languages', channel) > 0:                     #Si hay idioma seleccionado, se filtra
            itemlist_f = filtertools.get_link(itemlist_f, item_local, list_language)  #Pintar pantalla, si no está vacío

        #logger.debug("TORRENT: " + scrapedurl + " / title gen/torr: " + item.title + " / " + item_local.title + " / calidad: " + item_local.quality + " / content: " + item_local.contentTitle + " / " + item_local.contentSerieName)
        #logger.debug(item_local)

    if len(itemlist_f) > 0:                                                     #Si hay entradas filtradas...
        itemlist.extend(itemlist_f)                                             #Pintamos pantalla filtrada
    else:                                                                       
        if config.get_setting('filter_languages', channel) > 0 and len(itemlist_t) > 0: #Si no hay entradas filtradas ...
            thumb_separador = get_thumb("next.png")                             #... pintamos todo con aviso
            itemlist.append(Item(channel=item.channel, url=host, title="[COLOR red][B]NO hay elementos con el idioma seleccionado[/B][/COLOR]", thumbnail=thumb_separador, folder=False))
        itemlist.extend(itemlist_t)                                             #Pintar pantalla con todo si no hay filtrado
    
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)                                              #Lanzamos Autoplay
    
    return itemlist

    
def episodios(item):
    logger.info()
    itemlist = []
    item.category = categoria
    
    #logger.debug(item)

    if item.from_title:
        item.title = item.from_title
    
    #Limpiamos num. Temporada y Episodio que ha podido quedar por Novedades
    season_display = 0
    if item.contentSeason:
        if item.season_colapse:                                                             #Si viene del menú de Temporadas...
            season_display = item.contentSeason                                             #... salvamos el num de sesión a pintar
            item.from_num_season_colapse = season_display
            del item.season_colapse
            item.contentType = "tvshow"
            if item.from_title_season_colapse:
                item.title = item.from_title_season_colapse
                del item.from_title_season_colapse
                if item.infoLabels['title']:
                    del item.infoLabels['title']
        del item.infoLabels['season']
    if item.contentEpisodeNumber:
        del item.infoLabels['episode']
    if season_display == 0 and item.from_num_season_colapse:
        season_display = item.from_num_season_colapse

    # Obtener la información actualizada de la Serie.  TMDB es imprescindible para Videoteca
    #if not item.infoLabels['tmdb_id']:
    try:
        tmdb.set_infoLabels(item, True)                                                     #TMDB de cada Temp
    except:
        pass
        
    modo_ultima_temp_alt = modo_ultima_temp
    if item.ow_force == "1":                                                                #Si hay un traspaso de canal o url, se actualiza todo 
        modo_ultima_temp_alt = False
    
    max_temp = 1
    if item.infoLabels['number_of_seasons']:
        max_temp = item.infoLabels['number_of_seasons']
    y = []
    if modo_ultima_temp_alt and item.library_playcounts:                                    #Averiguar cuantas temporadas hay en Videoteca
        patron = 'season (\d+)'
        matches = re.compile(patron, re.DOTALL).findall(str(item.library_playcounts))
        for x in matches:
            y += [int(x)]
        max_temp = max(y)

    # Descarga la página
    data = ''                                                                               #Inserto en num de página en la url
    try:
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)|&nbsp;", "", httptools.downloadpage(item.url, timeout=timeout, headers=headers).data)
        data = js2py_conversion(data, item.url)
        data = unicode(data, "utf-8", errors="replace").encode("utf-8")
    except:                                                                                 #Algún error de proceso, salimos
        pass
        
    if not data:
        logger.error("ERROR 01: EPISODIOS: La Web no responde o la URL es erronea" + item.url)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: EPISODIOS:.  La Web no responde o la URL es erronea. Si la Web está activa, reportar el error con el log'))
        return itemlist

    #Usamos el mismo patrón que en listado
    patron = '<tr><td><img src="[^"]+".*?title="Idioma Capitulo" \/>(.*?)<a onclick="[^"]+".?href="[^"]+".?title="[^"]*">(.*?)<\/a><\/td><td><a href="([^"]+)".?title="[^"]*".?onclick="[^"]+".?<img src="([^"]+)".*?<\/a><\/td><td>.*?<\/td><\/tr>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    if not matches:                                                             #error
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            item, itemlist = generictools.post_tmdb_episodios(item, itemlist)   #Llamamos al método para el pintado del error
            return itemlist                                                     #Salimos
        
        logger.error("ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

    #logger.debug("PATRON: " + patron)
    #logger.debug(matches)
    #logger.debug(data)
    
    season = max_temp
    #Comprobamos si realmente sabemos el num. máximo de temporadas
    if item.library_playcounts or (item.infoLabels['number_of_seasons'] and item.tmdb_stat):
        num_temporadas_flag = True
    else:
        num_temporadas_flag = False

    # Recorremos todos los episodios generando un Item local por cada uno en Itemlist
    for language, scrapedtitle, scrapedurl, scrapedthumbnail in matches:
        item_local = item.clone()
        item_local.action = "findvideos"
        item_local.contentType = "episode"
        item_local.extra = "episodios"
        if item_local.library_playcounts:
            del item_local.library_playcounts
        if item_local.library_urls:
            del item_local.library_urls
        if item_local.path:
            del item_local.path
        if item_local.update_last:
            del item_local.update_last
        if item_local.update_next:
            del item_local.update_next
        if item_local.channel_host:
            del item_local.channel_host
        if item_local.active:
            del item_local.active
        if item_local.contentTitle:
            del item_local.infoLabels['title']
        if item_local.season_colapse:
            del item_local.season_colapse
        
        item_local.title = ''
        item_local.context = "['buscar_trailer']"
        item_local.url = scrapedurl
        title = scrapedtitle
        item_local.language = []
        
        lang = language.strip()
        if not lang:
            item_local.language += ['CAST']
        elif 'vo' in lang.lower() or 'v.o' in lang.lower() or 'vo' in title.lower() or 'v.o' in title.lower():
            item_local.language += ['VO']
        elif 'vose' in lang.lower() or 'v.o.s.e' in lang.lower() or 'vose' in title.lower() or 'v.o.s.e' in title.lower():
            item_local.language += ['VOSE']
        elif 'latino' in lang.lower() or 'latino' in title.lower():
            item_local.language += ['LAT']

        try:
            item_local.contentEpisodeNumber = 0
            if 'miniserie' in title.lower():
                item_local.contentSeason = 1
                title = title.replace('miniserie', '').replace('MiniSerie', '')
            elif 'completa' in title.lower():
                patron = '[t|T].*?(\d+) [c|C]ompleta'
                if scrapertools.find_single_match(title, patron):
                    item_local.contentSeason = int(scrapertools.find_single_match(title, patron))
            if not item_local.contentSeason:
                #Extraemos los episodios
                patron = '(\d{1,2})[x|X](\d{1,2})'
                item_local.contentSeason, item_local.contentEpisodeNumber = scrapertools.find_single_match(title, patron)
                item_local.contentSeason = int(item_local.contentSeason)
                item_local.contentEpisodeNumber = int(item_local.contentEpisodeNumber)
        except:
            logger.error('ERROR al extraer Temporada/Episodio: ' + title)
            item_local.contentSeason = 1
            item_local.contentEpisodeNumber = 0
        
        #Si son eisodios múltiples, lo extraemos
        patron1 = '\d+[x|X]\d{1,2}.?(?:y|Y|al|Al)?(?:\d+[x|X]\d{1,2})?.?(?:y|Y|al|Al)?.?\d+[x|X](\d{1,2})'
        epi_rango = scrapertools.find_single_match(title, patron1)
        if epi_rango:
            item_local.infoLabels['episodio_titulo'] = 'al %s' % epi_rango
            item_local.title = '%sx%s al %s -' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber).zfill(2), str(epi_rango).zfill(2))
        else:
            item_local.title = '%sx%s -' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber).zfill(2))

        if modo_ultima_temp_alt and item.library_playcounts:                    #Si solo se actualiza la última temporada de Videoteca
            if item_local.contentSeason < max_temp:
                break                                                           #Sale del bucle actual del FOR

        if season_display > 0:
            if item_local.contentSeason > season_display:
                continue
            elif item_local.contentSeason < season_display:
                break
        
        itemlist.append(item_local.clone())
        
        #logger.debug(item_local)
            
    if len(itemlist) > 1:
        itemlist = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))       #clasificamos
        
    if item.season_colapse and not item.add_videolibrary:                       #Si viene de listado, mostramos solo Temporadas
        item, itemlist = generictools.post_tmdb_seasons(item, itemlist)

    if not item.season_colapse:                                                 #Si no es pantalla de Temporadas, pintamos todo
        # Pasada por TMDB y clasificación de lista por temporada y episodio
        tmdb.set_infoLabels(itemlist, True)

        #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
        item, itemlist = generictools.post_tmdb_episodios(item, itemlist)
    
    #logger.debug(item)

    return itemlist
    
    
def actualizar_titulos(item):
    logger.info()
    
    item = generictools.update_title(item) #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels
    
    #Volvemos a la siguiente acción en el canal
    return item

    
def js2py_conversion(data, url, post=None, follow_redirects=True):
    logger.info()
    import js2py
    import base64
    
    if not 'Javascript is required' in data:
        return data
        
    patron = ',\s*S="([^"]+)"'
    data_new = scrapertools.find_single_match(data, patron)
    if not data_new:
        patron = ",\s*S='([^']+)'"
        data_new = scrapertools.find_single_match(data, patron)
    if not data_new:
        logger.error('js2py_conversion: NO data_new')
        return data
        
    try:
        for x in range(10):                                          # Da hasta 10 pasadas o hasta que de error
            data_end = base64.b64decode(data_new).decode('utf-8')
            data_new = data_end
    except:
        js2py_code = data_new
    else:
        logger.error('js2py_conversion: base64 data_new NO Funciona: ' + str(data_new))
        return data
    if not js2py_code:
        logger.error('js2py_conversion: NO js2py_code BASE64')
        return data
        
    js2py_code = js2py_code.replace('document', 'window').replace(" location.reload();", "")
    js2py.disable_pyimport()
    context = js2py.EvalJs({'atob': atob})
    new_cookie = context.eval(js2py_code)
    
    logger.info('new_cookie: ' + new_cookie)

    dict_cookie = {'domain': domain,
                }

    if ';' in new_cookie:
        new_cookie = new_cookie.split(';')[0].strip()
        namec, valuec = new_cookie.split('=')
        dict_cookie['name'] = namec.strip()
        dict_cookie['value'] = valuec.strip()
    zanga = httptools.set_cookies(dict_cookie)

    data_new = ''
    data_new = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(url, \
                timeout=timeout, headers=headers, post=post, follow_redirects=follow_redirects).data)
    data_new = re.sub('\r\n', '', data_new).decode('utf8').encode('utf8')
    if data_new:
        data = data_new
    
    return data
    
    
def atob(s):
    import base64
    return base64.b64decode(s.to_string().value)
    

def search(item, texto):
    logger.info()
    #texto = texto.replace(" ", "+")
    
    try:
        item.url = item.url % texto

        if texto != '':
            return listado(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []
 
 
def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    
    try:
        if categoria == 'peliculas':
            item.url = host + "peliculas-dvdr/"
            item.extra = "Películas DVDR"
            item.channel = channel
            item.category_new= 'newest'

            itemlist = listado(item)
            if ">> Página siguiente" in itemlist[-1].title:
                itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
