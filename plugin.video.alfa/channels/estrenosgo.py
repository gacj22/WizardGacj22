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
from platformcode import config, logger, platformtools
from core import tmdb
from lib import generictools
from channels import filtertools
from channels import autoplay


#IDIOMAS = {'CAST': 'Castellano', 'LAT': 'Latino', 'VO': 'Version Original'}
IDIOMAS = {'Castellano': 'CAST', 'Latino': 'LAT', 'Version Original': 'VO'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['torrent']

host = 'http://estrenoske.net/'
host_alt = 'http://estrenosby.net/' # 'http://estrenosli.org/'
channel = "estrenosgo"

color1, color2, color3 = ['0xFF58D3F7', '0xFF2E64FE', '0xFF0404B4']
__modo_grafico__ = config.get_setting('modo_grafico', channel)
modo_ultima_temp = config.get_setting('seleccionar_ult_temporadda_activa', channel) #Actualización sólo últ. Temporada?
timeout = config.get_setting('timeout_downloadpage', channel)


def mainlist(item):
    logger.info()
    itemlist = []
    item.url = host
    
    thumb_cartelera = get_thumb("now_playing.png")
    thumb_pelis = get_thumb("channels_movie.png")
    thumb_pelis_hd = get_thumb("channels_movie_hd.png")
    thumb_pelis_VO = get_thumb("channels_vos.png")
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_series_hd = get_thumb("channels_tvshow_hd.png")
    thumb_series_VOD = get_thumb("videolibrary_tvshow.png")
    thumb_buscar = get_thumb("search.png")
    thumb_separador = get_thumb("next.png")
    thumb_cabecera = get_thumb("nofolder.png")
    thumb_settings = get_thumb("setting_0.png")
    
    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, url=host, title="PELÍCULAS: ", folder=False, thumbnail=thumb_pelis))
    itemlist.append(Item(channel=item.channel, title="  - Cartelera", action="categorias", url=item.url + "descarga-0-58126", thumbnail=thumb_cartelera, extra="cartelera", filter_lang=True))
    itemlist.append(Item(channel=item.channel, title="  - DVD-RIP", action="categorias", url=item.url + "descarga-0-581210", thumbnail=thumb_pelis, extra="DVD-RIP", filter_lang=True))
    itemlist.append(Item(channel=item.channel, title="  - HD-RIP", action="categorias", url=item.url + "descarga-0-58128", thumbnail=thumb_pelis_hd, extra="HD-RIP", filter_lang=True))
    itemlist.append(Item(channel=item.channel, title="  - Subtituladas", action="categorias", url=item.url + "descarga-0-58127", thumbnail=thumb_pelis_VO, extra="VOSE", filter_lang=False))
    itemlist.append(Item(channel=item.channel, title="  - Versión Original", action="categorias", url=item.url + "descarga-0-5812255", thumbnail=thumb_pelis_VO, extra="VO", filter_lang=False))
    
    itemlist.append(Item(channel=item.channel, url=host, title="Series", action="submenu", thumbnail=thumb_series, extra="series"))
    
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + "descarga-0-0-0-0-fx-1-%s-sch-titulo-", thumbnail=thumb_buscar, extra="search"))

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
    item.filter_lang = True
    
    thumb_cartelera = get_thumb("now_playing.png")
    thumb_pelis = get_thumb("channels_movie.png")
    thumb_pelis_hd = get_thumb("channels_movie_hd.png")
    thumb_pelis_VO = get_thumb("channels_vos.png")
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_series_hd = get_thumb("channels_tvshow_hd.png")
    thumb_series_VOD = get_thumb("videolibrary_tvshow.png")
    thumb_buscar = get_thumb("search.png")
    thumb_separador = get_thumb("next.png")
    thumb_cabecera = get_thumb("nofolder.png")

    if item.extra == "series":

        itemlist.append(item.clone(title="Series completas", action="listado", url=item.url + "descarga-0-58122-0-0-fx-1-1-.fx", thumbnail=thumb_series_VOD, extra="series"))
        itemlist.append(item.clone(title="Nuevos episodios", action="listado", url=item.url + "descarga-0-58122-0-0-fx-1-1-.fx", thumbnail=thumb_series, extra="episodios"))
        itemlist.append(item.clone(title="      - Año", action="year", url=item.url + "descarga-0-58122-0-%s-fx-1-1-.fx", thumbnail=thumb_series, extra="episodios"))
        itemlist.append(item.clone(title="      - Alfabético A-Z", action="alfabeto", url=item.url + "descarga-0-58122-0-0-%s-1-1-.fx", thumbnail=thumb_series, extra="episodios"))

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
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url + '-0-0-fx-1-1-.fx', timeout=timeout).data)
    except:
        pass
        
    patron = '<div class="subitem"><a href="([^"]+)" class="[^"]+">(.*?)<\/a><\/div>'
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
        return itemlist                                     #si no hay más datos, algo no funciona, pintamos lo que tenemos

    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
    matches = re.compile(patron, re.DOTALL).findall(data)

    if not matches:
        logger.error("ERROR 02: SUBMENU: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.category + ': ERROR 02: SUBMENU: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
        return itemlist                                     #si no hay más datos, algo no funciona, pintamos lo que tenemos

    #logger.debug(matches)
    
    #Insertamos las cabeceras para todas las peliculas de la Aalidad, por Año, Alfabético, por Género, y Otras Calidades
    if not extra3:
        itemlist.append(item.clone(title="Todas las Películas de " + item.extra.upper(), action="listado", url=item.url + '-0-0-fx-1-1-.fx'))
        itemlist.append(item.clone(title="Año", action="year", url=item.url + '-0-%s-fx-1-1-.fx'))
        itemlist.append(item.clone(title="Alfabético A-Z", action="alfabeto", url=item.url + '-0-0-%s-1-1-.fx'))
        itemlist.append(item.clone(title="Géneros", url=item.url + '-0-0-fx-1-1-.fx'))
    
    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle.strip()

        #Preguntamos por las entradas que corresponden al "extra"
        if extra3 == 'now':
            if scrapedtitle.lower() in ['ac3 51', 'bluray rip', 'series', 'serie', 'subtitulada', 'vose', 'bdrip', 'dvdscreener', 'brscreener r6', 'brscreener', 'webscreener', 'dvd', 'hdrip', 'screener', 'screeer', 'webrip', 'brrip', 'dvb', 'dvdrip', 'dvdsc', 'dvdsc - r6', 'hdts', 'hdtv', 'kvcd', 'line', 'ppv', 'telesync', 'ts hq', 'ts hq proper', '480p', '720p', 'ac3', 'bluray', 'camrip', 'ddc', 'hdtv - screener', 'tc screener', 'ts screener', 'ts screener alto', 'ts screener medio', 'vhs screener']:
                itemlist.append(item.clone(action="listado", title=title, url=scrapedurl, extra2="categorias"))
        
        elif scrapedtitle.lower() in ['ac3 51', 'bluray rip', 'series', 'serie', 'subtitulada', 'vose', 'bdrip', 'dvdscreener', 'brscreener r6', 'brscreener', 'webscreener', 'dvd', 'hdrip', 'screener', 'screeer', 'webrip', 'brrip', 'dvb', 'dvdrip', 'dvdsc', 'dvdsc - r6', 'hdts', 'hdtv', 'kvcd', 'line', 'ppv', 'telesync', 'ts hq', 'ts hq proper', '480p', '720p', 'ac3', 'bluray', 'camrip', 'ddc', 'hdtv - screener', 'tc screener', 'ts screener', 'ts screener alto', 'ts screener medio', 'vhs screener']:
            extra3 = 'next'
            
        else:
            itemlist.append(item.clone(action="listado", title="    " + title.title(), url=scrapedurl, extra2="categorias"))
            
    if extra3 == 'next':
        itemlist.append(item.clone(action="categorias", title="Otras Calidades", url=item.url + '-0-0-fx-1-1-.fx', extra2="categorias", extra3='now'))

    return itemlist
    
    
def alfabeto(item):
    logger.info()
    itemlist = []
    
    itemlist.append(item.clone(action="listado", title="0-9", url=item.url % "_"))

    for letra in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']:
        itemlist.append(item.clone(action="listado", title=letra, url=item.url % letra))

    return itemlist

    
def listado(item):
    logger.info()
    itemlist = []

    #logger.debug(item)
    
    curr_page = 1                                                               # Página inicial
    last_page = 99999                                                           # Última página inicial
    if item.curr_page:
        curr_page = int(item.curr_page)                                         # Si viene de una pasada anterior, lo usamos
        del item.curr_page                                                      # ... y lo borramos
    if item.last_page:
        last_page = int(item.last_page)                                         # Si viene de una pasada anterior, lo usamos
        del item.last_page                                                      # ... y lo borramos
    item.url = item.url.replace('-1-.fx', '-%s-.fx')
    
    cnt_tot = 40                                                                # Poner el num. máximo de items por página
    cnt_title = 0                                                               # Contador de líneas insertadas en Itemlist
    inicio = time.time()                                    # Controlaremos que el proceso no exceda de un tiempo razonable
    fin = inicio + 5                                                            # Después de este tiempo pintamos (segundos)
    timeout_search = timeout                                                    # Timeout para descargas
    if item.extra == 'search':
        timeout_search = timeout * 2                                            # Timeout un poco más largo para las búsquedas
        if timeout_search < 5:
            timeout_search = 5                                                  # Timeout un poco más largo para las búsquedas

    #Sistema de paginado para evitar páginas vacías o semi-vacías en casos de búsquedas con series con muchos episodios
    title_lista = []                            # Guarda la lista de series que ya están en Itemlist, para no duplicar lineas
    if item.title_lista:                        # Si viene de una pasada anterior, la lista ya estará guardada
        title_lista.extend(item.title_lista)    # Se usa la lista de páginas anteriores en Item
        del item.title_lista                                                    # ... limpiamos
        
    if not item.extra2:                                                         # Si viene de Catálogo o de Alfabeto
        item.extra2 = ''
    
    #Máximo num. de líneas permitidas por TMDB. Máx de 10 segundos por Itemlist para no degradar el rendimiento
    while cnt_title <= cnt_tot * 0.45 and curr_page <= last_page and fin > time.time():
    
        # Descarga la página
        data = ''
        url = item.url % curr_page                                              #Inserto en num de página en la url
        try:
            data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)|&nbsp;", "", httptools.downloadpage(url, timeout=timeout_search).data)
            data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
        except:
            pass
        
        curr_page += 1                                                          #Apunto ya a la página siguiente
        if not data:                                                            #Si la web está caída salimos sin dar error
            logger.error("ERROR 01: LISTADO: La Web no responde o ha cambiado de URL: " + url + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: LISTADO:.  La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
            if len(itemlist) > 1:
                #Pasamos a TMDB la lista completa Itemlist
                tmdb.set_infoLabels(itemlist, __modo_grafico__)
                #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
                item, itemlist = generictools.post_tmdb_listado(item, itemlist)
            return itemlist                                 #si no hay más datos, algo no funciona, pintamos lo que tenemos

        #Patrón para todo menos para Series completas
        patron = '<div class="MiniFicha"><a href="([^"]+)" title="([^"]+)">'
        patron += '<img src="([^"]+).*?'
        patron += '<div class="MiniF_TitleSpecial">[^>]+>([^<]+).*?'
        patron += '<b>Categoria:\s*<\/b>([^&]+)&raquo;\s*([^<]+).*?'
        patron += '<div class="OpcionesDescargasMini">(.*?)<\/div>'
        
        #Si son series completas, ponemos un patrón especializado, de categorías, y luego llamamos a un método especializado
        if item.extra == 'series':
            patron = '<div class="subitem"><a href="([^"]+)" class="[^"]+">(.*?)<\/a><\/div>'
            
        matches = re.compile(patron, re.DOTALL).findall(data)
        if not matches and not 'En Total 0 Paginas y un total de 0 de Fichas' in data:               #error
            item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
            if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
                item, itemlist = generictools.post_tmdb_episodios(item, itemlist)   #Llamamos al método para el pintado del error
                return itemlist                                                     #Salimos
            
            logger.error("ERROR 02: LISTADO: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: LISTADO: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
            if len(itemlist) > 1:
                #Pasamos a TMDB la lista completa Itemlist
                tmdb.set_infoLabels(itemlist, __modo_grafico__)
                #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
                item, itemlist = generictools.post_tmdb_listado(item, itemlist)
            return itemlist                                 #si no hay más datos, algo no funciona, pintamos lo que tenemos
        
        #logger.debug("PATRON: " + patron)
        #logger.debug(matches)
        #logger.debug(data)
        
        #Buscamos la última página, pero solo en la primera pasada, porque en búsquedan deja de funcionar a partir de la seguna página
        if last_page == 99999:                                                      #Si es el valor inicial, buscamos
            patron = '<div class="sPages">.*?'
            patron += '<a href="[^"]+">Siguiente'
            patron += ' &raquo;<\/a><br> En Total (\d+) Pagina?'                    #Esta es la parte que vale
            try:
                last_page = int(scrapertools.find_single_match(data, patron))       #lo cargamos como entero
            except:
                last_page = 1                                                       #Si no lo encuentra, lo ponemos a 1

        if item.extra == 'series':                              #Si son series completas, vamos a un listado especializado
            item.matches = matches                              #salvamos todas las matches, no hay paginación
            return listado_series(item)                         #llamamos a un método especializado
        
        #Empezamos el procesado de matches
        for scrapedurl, scrapedenlace, scrapedthumbnail, scrapedtitle, cat_ppal, cat_sec, opciones in matches:
            if "musica" in cat_ppal or "juegos" in cat_ppal or "juegos" in cat_ppal or "software" in cat_ppal:
                continue

            url = scrapedurl
            title = scrapedtitle
            title = title.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ü", "u").replace("ï¿½", "ñ").replace("Ã±", "ñ").replace("&atilde;", "a").replace("&etilde;", "e").replace("&itilde;", "i").replace("&otilde;", "o").replace("&utilde;", "u").replace("&ntilde;", "ñ")
            extra = item.extra

            #Si es una búsqueda, convierte los episodios en Series completas, aptas para la Videoteca
            if extra == 'search' and 'series' in cat_ppal and not "Temp" in title and not "emporada" in title:
                if cat_sec in title_lista:                                      #Si ya hemos procesado la serie, pasamos de los episodios adicionales
                    continue

                # Descarga la página del episodio, buscando el enlace a la serie completa
                data_serie = ''
                try:
                    data_serie = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)|&nbsp;", "", httptools.downloadpage(scrapedurl, timeout=timeout).data)
                    data_serie = unicode(data_serie, "iso-8859-1", errors="replace").encode("utf-8")
                except:
                    pass
                
                if not data_serie:                      #Si la web está caída salimos sin dar error. Pintamos el episodio
                    logger.error("ERROR 01: LISTADO: La Web no responde o ha cambiado de URL: " + scrapedurl + " / SERIE: " + cat_sec)
                else:
                    patron_serie = '<div id="where_i_am">.*?<a href="[^"]+">.*?<\/a>.*?<a href="([^"]+)">'
                    url = scrapertools.find_single_match(data_serie, patron_serie)      #buscamos la url de la serie completa
                    if url:
                        if host not in url and host_alt not in url:
                            url = host + url
                        extra = 'series'                        #es una serie completa    
                        title_lista += [cat_sec]                #la añadimos a la lista de series completas procesadas    
                        title = cat_sec                         #salvamos el título de la serie completa
                    else:
                        url = scrapedurl                        #No se encuentra la Serie, se trata como Episodio suelto

            elif "Archivo Torrent" not in scrapedenlace and "Video Online" not in scrapedenlace:    #Si no tiene enlaces pasamos
                continue

            #cnt_title += 1
            item_local = item.clone()                           #Creamos copia de Item para trabajar
            if item_local.tipo:                                 #... y limpiamos
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
            item_local.filter_lang = True
            del item_local.filter_lang
                
            title_subs = []                                         #creamos una lista para guardar info importante
            item_local.language = []                                #creamos lista para los idiomas
            item_local.quality = ''                                 #iniciamos calidad   
            quality_alt = ''
            if 'series' not in cat_ppal:                            #si no son series, contiene la calidad
                quality_alt = cat_sec.lower().strip()
            item_local.extra = extra                                #guardamos el extra procesado    
            item_local.url = url                                    #guardamos la url final
            if host not in scrapedthumbnail and host_alt not in scrapedthumbnail:
                item_local.thumbnail = host[:-1] + scrapedthumbnail #guardamos el thumb
            else:
                item_local.thumbnail = scrapedthumbnail             #guardamos el thumb sin Host
            item_local.context = "['buscar_trailer']"
            
            item_local.contentType = "movie"                        #por defecto, son películas
            item_local.action = "findvideos"
            
            #Analizamos los formatos de la películas
            if ('cartelera' in cat_ppal or item.extra == "cartelera") and not item.extra2:
                item_local.quality = cat_sec.lower().capitalize()
            if 'peliculas-dvdrip' in cat_ppal or item_local.extra == 'DVD-RIP':
                item_local.quality = 'DVD-RIP'
            elif 'HDRIP' in cat_ppal or item_local.extra == 'HD-RIP':
                item_local.quality = 'HD-RIP'
            elif 'subtituladas' in cat_ppal or item_local.extra == 'VOSE':
                item_local.language += ['VOSE']
            elif 'Version Original' in cat_ppal or item_local.extra == 'VO':
                item_local.language += ['VO']

            #Analizamos los formatos de series, temporadas y episodios
            elif item_local.extra == 'series':
                item_local.contentType = "tvshow"
                item_local.action = "episodios"
                item_local.season_colapse = True                        #Muestra las series agrupadas por temporadas
            elif 'series' in cat_ppal or item_local.extra == 'episodios':
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

            if item_local.contentType == "movie":                       #para las peliculas ponemos el mismo extra
                item_local.extra = "peliculas"
                
            #Detectamos idiomas
            if "Latino" in cat_sec or "latino" in cat_sec or "Latino" in title or "latino" in title or "LATINO" in title:
                item_local.language += ['LAT']
            elif "VOSE" in cat_sec or "VOS" in cat_sec or "VOSE" in title or "VOS" in title:
                item_local.language += ['VOSE']
            
            if item_local.language == []:
                item_local.language = ['CAST']
                
            #Procesamos calidades
            if not item_local.quality:
                if quality_alt in ['dvdscreener', 'brscreener r6', 'brscreener', 'webscreener', 'dvd', 'hdrip', 'screener', 'screeer', 'webrip', 'brrip', 'dvb', 'dvdrip', 'dvdsc', 'dvdsc - r6', 'hdts', 'hdtv', 'kvcd', 'line', 'ppv', 'telesync', 'ts hq', 'ts hq proper', '480p', '720p', 'ac3', 'bluray', 'camrip', 'ddc', 'hdtv - screener', 'tc screener', 'ts screener', 'ts screener alto', 'ts screener medio', 'vhs screener']:
                    item_local.quality = quality_alt.capitalize()

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
            title = re.sub(r'- $', '', title)
            title = re.sub(r'\d+[M|m|G|g][B|b]', '', title)

            #Limpiamos el título de la basura innecesaria
            title = title.replace("Dual", "").replace("dual", "").replace("Subtitulada", "").replace("subtitulada", "").replace("Subt", "").replace("subt", "").replace("Sub", "").replace("sub", "").replace("(Proper)", "").replace("(proper)", "").replace("Proper", "").replace("proper", "").replace("#", "").replace("(Latino)", "").replace("Latino", "").replace("LATINO", "").replace("Spanish", "").replace("Esp", "").replace("Trailer", "").replace("Audio", "")
            title = title.replace("HDTV-Screener", "").replace("DVDSCR", "").replace("TS ALTA", "").replace("- HDRip", "").replace("(HDRip)", "").replace("- Hdrip", "").replace("(microHD)", "").replace("(DVDRip)", "").replace("HDRip", "").replace("(BR-LINE)", "").replace("(HDTS-SCREENER)", "").replace("(BDRip)", "").replace("(BR-Screener)", "").replace("(DVDScreener)", "").replace("TS-Screener", "").replace(" TS", "").replace(" Ts", "").replace(" 480p", "").replace(" 480P", "").replace(" 720p", "").replace(" 720P", "").replace(" 1080p", "").replace(" 1080P", "").replace("DVDRip", "").replace(" Dvd", "").replace(" DVD", "").replace(" V.O", "").replace(" Unrated", "").replace(" UNRATED", "").replace(" unrated", "").replace("screener", "").replace("TS-SCREENER", "").replace("TSScreener", "").replace("HQ", "").replace("AC3 5.1", "").replace("Telesync", "").replace("Line Dubbed", "").replace("line Dubbed", "").replace("LineDuB", "").replace("Line", "").replace("XviD", "").replace("xvid", "").replace("XVID", "").replace("Mic Dubbed", "").replace("HD", "").replace("V2", "").replace("CAM", "").replace("VHS.SCR", "")

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
                
            #Guarda la variable temporal que almacena la info adicional del título a ser restaurada después de TMDB
            item_local.title_subs = title_subs
            
            #Salvamos y borramos el número de temporadas porque TMDB a veces hace tonterias.  Lo pasamos como serie completa
            if item_local.contentSeason and (item_local.contentType == "season" or item_local.contentType == "tvshow"):
                item_local.contentSeason_save = item_local.contentSeason
                del item_local.infoLabels['season']

            #Ahora se filtra por idioma, si procede, y se pinta lo que vale
            if config.get_setting('filter_languages', channel) > 0 and item.filter_lang:     #Si hay idioma seleccionado, se filtra
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

        itemlist.append(Item(channel=item.channel, action="listado", title=">> Página siguiente " + title, title_lista=title_lista, url=item.url, extra=item.extra, extra2=item.extra2, last_page=str(last_page), curr_page=str(curr_page), filter_lang=item.filter_lang))

    return itemlist

    
def listado_series(item):
    logger.info()
    itemlist = []
    matches = []
    matches_current = 0
    pag = 30
    
    #logger.debug(item)
    
    #Control de paginación
    matches = item.matches                                      #Restauramos la matches de la primera pasada
    del item.matches
    matches_tot = len(matches)                                  #La web no pagina las Series, lo tenemos que controlar
    if item.matches_current:                                    #Llevamos los contadores de cuánto hemos pintado y cuánto queda
        matches_current = item.matches_current
    if matches_tot >= matches_current + pag:
        item.matches_current = matches_current + pag            #Establecemos el bloque a pintar en este pasada
    else:
        item.matches_current = matches_tot

    #logger.debug(matches[matches_current:item.matches_current])
    
    #procesamos una página
    for scrapedurl, scrapedtitle in matches[matches_current:item.matches_current]:
        item_local = item.clone()                                           #Creamos copia de Item para trabajar
        
        if scrapertools.find_single_match(scrapedtitle, '\d+[x|X]\d+'):     #Si es episodio suelto, pasamos
            continue
        
        if item_local.tipo:
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
        if item_local.matches_current:
            del item_local.matches_current
        item_local.extra2 = True
        del item_local.extra2
        item_local.text_bold = True
        del item_local.text_bold
        item_local.text_color = True
        del item_local.text_color
            
        #Iniciamos variables
        title_subs = []
        item_local.language = []
        item_local.quality = ''
        title = scrapedtitle

        #Empezamos a construir el Item de salida
        item_local.url = scrapedurl
        item_local.context = "['buscar_trailer']"
        item_local.contentType = "tvshow"
        item_local.action = "episodios"
        item_local.season_colapse = True                                    #Muestra las series agrupadas por temporadas
        
        #Tratamos idiomas, aunque hay poco...
        if "Latino" in title or "latino" in title:
            item_local.language += ['LAT']
        elif "VOSE" in title or "VOS" in title:
            item_local.language += ['VOSE']
        
        if item_local.language == []:
            item_local.language = ['CAST']
            
        #Establecemos el título
        item_local.contentSerieName = title.strip().lower().title() 
        item_local.title = title.strip().lower().title() 
        item_local.from_title = title.strip().lower().title() 

        #Ahora se filtra por idioma, si procede, y se pinta lo que vale
        if config.get_setting('filter_languages', channel) > 0:     #Si hay idioma seleccionado, se filtra
            itemlist = filtertools.get_link(itemlist, item_local, list_language)
        else:
            itemlist.append(item_local.clone())                     #Si no, pintar pantalla

        #logger.debug(item_local)
   
    #if not item.category:          #Si este campo no existe es que viene de la primera pasada de una búsqueda global
    #    return itemlist            #Retornamos sin pasar por la fase de maquillaje para ahorra tiempo

    #Pasamos a TMDB la lista completa Itemlist
    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    
    #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
    item, itemlist = generictools.post_tmdb_listado(item, itemlist)
    
    #Control de siguiente página
    if matches_tot > item.matches_current:
        pag_tot = matches_tot / pag
        pag_cur = item.matches_current / pag
        
        itemlist.append(Item(channel=item.channel, action="listado_series", title=">> Página siguiente (" + str(pag_cur) + " de " + str(pag_tot) + ")", url=item.url, text_color=color3, text_bold=True, extra=item.extra, matches_current=item.matches_current, matches=matches))

    return itemlist
    
    
def findvideos(item):
    logger.info()
    itemlist = []
    itemlist_t = []                                     #Itemlist total de enlaces
    itemlist_f = []                                     #Itemlist de enlaces filtrados
    if not item.language:
        item.language = ['CAST']                        #Castellano por defecto

    item.url = item.url.replace(host_alt, host)         #Cambio de dominio (videoteca)
    
    #logger.debug(item)
    
    IDIOMAS = {"banderita1": "CAST", "banderita2": "VOSE", "banderita3": "LAT"}

    #Bajamos los datos de la página
    data_torrent = ''
    data_directo = ''
    try:
        url = item.url.replace('/descargar-', '/descargar-torrent-').replace('.fx', '-aportes.fx')
        data_torrent = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(url, timeout=timeout).data)
        url = item.url.replace('/descargar-', '/ver-online-').replace('.fx', '-aportes.fx')
        data_directo = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(url, timeout=timeout).data)
    except:
        pass
        
    if not data_torrent and not data_directo:
        logger.error("ERROR 01: FINDVIDEOS: La Web no responde o la URL es erronea: " + item.url)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: FINDVIDEOS:.  La Web no responde o la URL es erronea. Si la Web está activa, reportar el error con el log', folder=False))

    patron = '<div class="content"><a href="([^"]+).*?'
    patron += '(?:<div class="content_medium">(.*?)<\/div>.*?)?'
    patron += '<div class="content_mini"><span class="([^"]+)'
    matches_torrent = re.compile(patron, re.DOTALL).findall(data_torrent)
    matches_directo = re.compile(patron, re.DOTALL).findall(data_directo)
    if not matches_torrent and not matches_directo and scrapertools.find_single_match(data_directo, '<div id="where_i_am".*?<a href="[^"]+">Ver Online<\/a>.*?href="([^"]+)">') != url:                                     #error
        
        if item.emergency_urls and not item.videolibray_emergency_urls:         #Hay urls de emergencia?
            matches_torrent = item.emergency_urls[1]                            #Guardamos los matches de los .Torrents
            try:
                matches_directo = item.emergency_urls[3]                        #Guardamos los matches de Directos, si los hay
            except:
                pass
            item.armagedon = True                                               #Marcamos la situación como catastrófica
        else:
            if len(itemlist) == 0:
                logger.error("ERROR 02: FINDVIDEOS: No hay enlaces o ha cambiado la estructura de la Web " + " / PATRON: " + patron)
                itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: FINDVIDEOS: No hay enlaces o ha cambiado la estructura de la Web.  Verificar en la Web esto último y reportar el error con el log', folder=False))
                if data_torrent:
                    logger.error(data_torrent)
                if data_directo:
                    logger.error(data_directo)
            if item.videolibray_emergency_urls:
                return item
            else:
                return itemlist                                     #si no hay más datos, algo no funciona, pintamos lo que tenemos
    
    #logger.debug("PATRON: " + patron)
    #logger.debug(matches_torrent)
    #logger.debug(matches_directo)
    #logger.debug(data_torrent)
    #logger.debug(data_directo)
    
    if item.videolibray_emergency_urls:
        item.emergency_urls = []                                            #Iniciamos emergency_urls
        item.emergency_urls.append([])                                      #Reservamos el espacio para los .torrents locales
        item.emergency_urls.append(matches_torrent)                         #Guardamos los matches_torrent iniciales
        item.emergency_urls.append([])                                      #Reservamos el espacio para los matches_torrent finales
        item.emergency_urls.append(matches_directo)                         #Guardamos los matches_directo iniciales
        item.emergency_urls.append([])                                      #Reservamos el espacio para los matches_directo finales
    
    #Llamamos al método para crear el título general del vídeo, con toda la información obtenida de TMDB
    if not item.videolibray_emergency_urls:
        item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)
    
    #Si es un Episodio suelto, tratamos de poner un enlace a la Serie completa
    if item.extra3 == 'completa':
        del item.extra3
        item_local = item.clone()
        
        #Salvamos lo imprescindible y reiniciamos InfoLabels
        tmdb_id = item.infoLabels['tmdb_id']
        item_local.infoLabels = {}
        item_local.unify = True
        del item_local.unify
        
        #Restauramos lo básico
        item.infoLabels['tmdb_id'] = tmdb_id
        item_local.contentSerieName = item_local.from_title
        item_local.title = item_local.from_title
        item_local.quality = ''
        item.infoLabels['year'] = '-'
        item_local.contentType = 'tvshow'
        item_local.extra = 'series'
        item_local.action = 'episodios'
        item_local.season_colapse = True                                                #Muestra las series agrupadas por temporadas
        
        #Buscamos la url de la serie y verificamos que existe
        patron_serie = '<div class="linkMoreMovies"><div class="linkMore"><a href="([^"]+)">'
        item_local.url = scrapertools.find_single_match(data_torrent, patron_serie)     #buscamos la url de la serie completa
        if not item_local.url:
            item_local.url = scrapertools.find_single_match(data_directo, patron_serie) #buscamos la url de la serie completa
        if item_local.url:
            item_local.url = item_local.url.replace('descargar-torrent', 'descarga').replace('-0-0-0-0-fx-', '-0-0-fx-')
            try:
                tmdb.set_infoLabels(item_local, True)                                   #TMDB de la serie completa
            except:
                pass
            
            #Solo si hay url de Serie lo pintamos
            itemlist.append(item_local.clone(title="** [COLOR yelow]Ver la Serie COMPLETA[/COLOR] **"))

    #Ahora tratamos los enlaces .torrent
    itemlist_alt = []                                                               #Usamos una lista intermedia para poder ordenar los episodios
    if matches_torrent:
        for scrapedurl, scrapedquality, scrapedlang in matches_torrent:     #leemos los torrents con la diferentes calidades
            #Generamos una copia de Item para trabajar sobre ella
            item_local = item.clone()
            
            item_local.url = scrapedurl                                             #Guardamos la url intermedia
            
            item_local.quality = ''
            if scrapedquality and not '--' in scrapedquality:                       #Salvamos la calidad, si la hay
                item_local.quality = scrapedquality.lower().capitalize()
            
            if not item_local.quality:
                item_local.quality = item.quality
            elif scrapertools.find_single_match(item.quality, '(\[\d+:\d+ h\])'):   #Salvamos la duración
                item_local.quality += ' [/COLOR][COLOR white]%s' % scrapertools.find_single_match(item.quality, '(\[\d+:\d+ h\])')                                                                    #Copiamos duración

            if scrapedlang in IDIOMAS:                                              #Salvamos el idioma, si lo hay
                item_local.language = ["%s" % IDIOMAS[scrapedlang]]
            
            #Leemos la página definitiva para el enlace al .torrent
            data = ''
            if not item.armagedon:
                try:
                    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item_local.url, timeout=timeout).data)
                except:
                    pass
                    
                patron = '<div class="linksDescarga"><span class="titulo">Descargar Torrent: <\/span><br><a href="([^"]+)" class="TTlink">&raquo;\s?(.*?)\s?&laquo;<\/a>'
                matches = re.compile(patron, re.DOTALL).findall(data)
            else:
                matches = item.emergency_urls[2][0]                         #Guardamos los matches de Directos, si los hay
                del item.emergency_urls[2][0]                                       #Una vez tratado lo limpiamos
                data = 'xyz123'                                                     #iniciamos data para que no dé problemas
            
            if item.videolibray_emergency_urls:                                     #Si esyamos añadiendo a Videoteca...
                item.emergency_urls[2].append(matches)                              #Salvamos este matches
            
            if not data or not matches:
                logger.error("ERROR 02: FINDVIDEOS: El archivo Torrent no existe o ha cambiado la estructura de la Web " + " / PATRON: " + patron  + " / URL: " + item_local.url  + " / DATA: " + data)
                continue                                    #si no hay más datos, algo no funciona, pasamos a Ver Online
            
            #logger.debug(patron)
            #logger.debug(matches)
            #logger.debug(data)

            for scrapedtorrent_alt, scrapedtitle in matches:
                if host not in scrapedtorrent_alt and host_alt not in scrapedtorrent_alt:
                    scrapedtorrent = host + scrapedtorrent_alt
                else:
                    scrapedtorrent = scrapedtorrent_alt
                    
                if item.videolibray_emergency_urls:
                    item.emergency_urls[0].append(scrapedtorrent)
                else:
                    item_local = item_local.clone()
                    quality = item_local.quality
                    qualityscraped = ''
                    if not item_local.contentEpisodeNumber and item_local.contentType == 'episode':
                        item_local.contentEpisodeNumber = 0
                    
                    #Si son episodios múltiples, los listamos con sus títulos
                    if len(matches) > 1 or len(itemlist_alt) > 1:
                        if item_local.contentType == 'episode' or item_local.contentType == 'season':
                            if scrapertools.find_single_match(scrapedtitle, '(\d+[x|X]\d+(?:-\d{1,2})?)'):
                                qualityscraped = '%s' % scrapertools.find_single_match(scrapedtitle, '(\d+[x|X]\d+(?:-\d{1,2})?)')
                            if scrapertools.find_single_match(scrapedtitle, '\d+[x|X](\d+)'):
                                item_local.contentEpisodeNumber = int(scrapertools.find_single_match(scrapedtitle, '\d+[x|X](\d+)'))
                            elif scrapertools.find_single_match(scrapedtitle, '[c|C]ap.*?(\d+)'):
                                item_local.contentEpisodeNumber = int(scrapertools.find_single_match(scrapedtitle, '[c|C]ap.*?(\d+)'))
                            elif scrapertools.find_single_match(scrapedtorrent, '[s|S]\d{1,2}[e|E](\d{1,2})'):
                                item_local.contentEpisodeNumber = int(scrapertools.find_single_match(scrapedtorrent, '[s|S]\d{1,2}[e|E](\d{1,2})'))
                            if not qualityscraped:
                                qualityscraped = '%sx%s' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber).zfill(2))
                        else:
                            qualityscraped = '%s' % scrapedtitle
                    
                    #Si todavía no sabemos el num de Episodio, lo buscamos
                    if not item_local.contentEpisodeNumber and item_local.contentType == 'episode':
                        try:
                            if scrapertools.find_single_match(scrapedtitle, '(\d+)[x|X](\d+)'):
                                item_local.contentSeason, item_local.contentEpisodeNumber = scrapertools.find_single_match(scrapedtitle, '(\d+)[x|X](\d+)')
                                qualityscraped = '%sx%s' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber).zfill(2))
                        except:
                            pass
                    
                    #Buscamos calidades
                    if scrapertools.find_single_match(scrapedtitle, '(\d+p)'):
                        qualityscraped += ' ' + scrapertools.find_single_match(scrapedtitle, '(\d+p)')
                    if qualityscraped:
                        quality = '[%s] %s' % (qualityscraped, item_local.quality)

                    #Ahora pintamos el link del Torrent
                    item_local.url = scrapedtorrent
                    if item.emergency_urls and not item.videolibray_emergency_urls:
                        item_local.torrent_alt = item.emergency_urls[0][0]      #Guardamos la url del .Torrent ALTERNATIVA
                        if item.armagedon:
                            item_local.url = item.emergency_urls[0][0]          #... ponemos la emergencia como primaria
                        del item.emergency_urls[0][0]                           #Una vez tratado lo limpiamos
                    
                    size = ''
                    if not item.armagedon:
                        size = generictools.get_torrent_size(item_local.url)    #Buscamos el tamaño en el .torrent
                    if size:
                        item_local.torrent_info += '%s' % size                  #Agregamos size
                        if not item.unify:
                            item_local.torrent_info = '[%s]' % item_local.torrent_info.strip().strip(',')
                    if item.armagedon:                                          #Si es catastrófico, lo marcamos
                        quality = '[/COLOR][COLOR hotpink][E] [COLOR limegreen]%s' % quality
                    item_local.title = '[[COLOR yellow]?[/COLOR]] [COLOR yellow][Torrent][/COLOR] ' \
                        + '[COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR] %s' % \
                        (quality, str(item_local.language),  item_local.torrent_info)   #Preparamos título de Torrent
                        
                    #Preparamos título y calidad, quitamos etiquetas vacías
                    item_local.title = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', item_local.title)    
                    item_local.title = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', item_local.title)
                    item_local.title = item_local.title.replace("--", "").replace("[]", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()
                    quality = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', quality)
                    quality = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', quality)
                    quality = quality.replace("--", "").replace("[]", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()
                    
                    item_local.alive = "??"                                                 #Calidad del link sin verificar
                    item_local.action = "play"                                              #Visualizar vídeo
                    item_local.server = "torrent"                                           #Seridor Torrent

                    itemlist_t.append(item_local.clone(quality=quality))                    #Pintar pantalla, si no se filtran idiomas
            
                    # Requerido para FilterTools
                    if config.get_setting('filter_languages', channel) > 0:                 #Si hay idioma seleccionado, se filtra
                        item_local.quality = quality                                        #Calidad
                        itemlist_f = filtertools.get_link(itemlist_f, item_local, list_language)  #Pintar pantalla, si no está vacío

                    #logger.debug("TORRENT: " + scrapedtorrent + " / title gen/torr: " + item.title + " / " + item_local.title + " / calidad: " + item_local.quality + " / tamaño: " + scrapedsize + " / content: " + item_local.contentTitle + " / " + item_local.contentSerieName)
                    #logger.debug(item_local)
    
    if not item.videolibray_emergency_urls:
        if len(itemlist_f) > 0:                                                             #Si hay entradas filtradas...
            itemlist_alt.extend(itemlist_f)                                                 #Pintamos pantalla filtrada
        else:                                                                       
            if config.get_setting('filter_languages', channel) > 0 and len(itemlist_t) > 0: #Si no hay entradas filtradas ...
                thumb_separador = get_thumb("next.png")                             #... pintamos todo con aviso
                itemlist.append(Item(channel=item.channel, url=host, title="[COLOR red][B]NO hay elementos con el idioma seleccionado[/B][/COLOR]", thumbnail=thumb_separador, folder=False))
            itemlist_alt.extend(itemlist_t)                                                 #Pintar pantalla con todo si no hay filtrado
        
        #Si son múltiples episodios, ordenamos
        if len(itemlist_alt) > 1 and (item.contentType == 'episode' or item.contentType == 'season'):
            itemlist_alt = sorted(itemlist_alt, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))     #clasificamos
            tmdb.set_infoLabels(itemlist_alt, True)                                         #TMDB de la lista de episodios
        itemlist.extend(itemlist_alt)

    #Ahora tratamos los servidores directo
    itemlist_alt = []
    itemlist_t = []                                                                         #Itemlist total de enlaces
    itemlist_f = []                                                                         #Itemlist de enlaces filtrados
    if matches_directo:
        for scrapedurl, scrapedquality, scrapedlang in matches_directo:                     #leemos los torrents con la diferentes calidades
            #Generamos una copia de Item para trabajar sobre ella
            item_local = item.clone()
            
            item_local.url = scrapedurl                                                     #Guardamos la url intermedia
            
            item_local.quality = ''
            if scrapedquality:
                item_local.quality = scrapedquality
            
            if not item_local.quality:
                item_local.quality = item.quality
            elif scrapertools.find_single_match(item.quality, '(\[\d+:\d+ h\])'):           #Salvamos la duración
                item_local.quality += ' [/COLOR][COLOR white]%s' % scrapertools.find_single_match(item.quality, '(\[\d+:\d+ h\])') #Copiamos duración

            if scrapedlang in IDIOMAS:
                item_local.language = ["%s" % IDIOMAS[scrapedlang]]                         #Salvamos el idioma, si lo hay
            
            #Leemos la página con el enlace al Servidor
            data = ''
            if not item.armagedon:
                try:
                    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item_local.url, timeout=timeout).data)
                except:
                    pass
                    
                patron = '<div class="linksDescarga"><span class="titulo">Video Online:\s?([^<]+)?<\/span><br><br><a href="([^"]+)'
                matches = re.compile(patron, re.DOTALL).findall(data)
            else:
                matches = item.emergency_urls[4][0]                                 #Guardamos los matches de Directos, si los hay
                del item.emergency_urls[4][0]                                       #Una vez tratado lo limpiamos
                data = 'xyz123'                                                     #iniciamos data para que no dé problemas
            
            if item.videolibray_emergency_urls:                                     #Si esyamos añadiendo a Videoteca...
                item.emergency_urls[4].append(matches)                              #Salvamos este matches
           
            if not data or not matches:
                logger.error("ERROR 02: FINDVIDEOS: El enlace no existe o ha cambiado la estructura de la Web " + " / PATRON: " + patron  + " / DATA: " + data)
                itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: FINDVIDEOS: El enlace no existe o ha cambiado la estructura de la Web.  Verificar en la Web y reportar el error con el log', folder=False))
                continue                                                #si no hay más datos, algo no funciona, salimos
            
            #logger.debug(patron)
            #logger.debug(matches)
            #logger.debug(data)

            for scrapedtitle, scrapedenlace in matches:
                if not item.videolibray_emergency_urls:
                    item_local = item_local.clone()
                    
                    enlace = ''
                    devuelve = ''
                    mostrar_server = ''
                    capitulo = ''
                    
                    servidor = scrapedtitle.strip()
                    servidor = servidor.replace("streamin", "streaminto")
                    if not servidor or "Capituo" in servidor or "Capitulo" in servidor or scrapertools.find_single_match(servidor, '(\d+[x|X]\d+)'):
                        capitulo = scrapertools.find_single_match(servidor, '(\d+[x|X]\d+)')
                        servidor = scrapertools.find_single_match(scrapedenlace, ':\/\/(.*?)\.')
                    quality = item_local.quality
                    
                    qualityscraped = ''
                    if not item_local.contentEpisodeNumber and item_local.contentType == 'episode':
                        item_local.contentEpisodeNumber = 0
                    
                    #Si son episodios múltiples, los listamos con sus títulos
                    if (len(matches) > 1 or len(itemlist_alt) > 1) and not servidor in scrapedtitle:
                        if not capitulo and (item_local.contentType == 'episode' or item_local.contentType == 'season'):
                            if scrapertools.find_single_match(scrapedtitle, '(\d+[x|X]\d+(?:-\d{1,2})?)'):
                                qualityscraped = '%s' % scrapertools.find_single_match(scrapedtitle, '(\d+[x|X]\d+(?:-\d{1,2})?)')
                            if scrapertools.find_single_match(scrapedtitle, '\d+[x|X](\d+)'):
                                item_local.contentEpisodeNumber = int(scrapertools.find_single_match(scrapedtitle, '\d+[x|X](\d+)'))
                            elif scrapertools.find_single_match(scrapedtitle, '[c|C]ap.*?(\d+)'):
                                item_local.contentEpisodeNumber = int(scrapertools.find_single_match(scrapedtitle, '[c|C]ap.*?(\d+)'))
                            elif scrapertools.find_single_match(scrapedtorrent, '[s|S]\d{1,2}[e|E](\d{1,2})'):
                                item_local.contentEpisodeNumber = int(scrapertools.find_single_match(scrapedtorrent, '[s|S]\d{1,2}[e|E](\d{1,2})'))
                            if not qualityscraped:
                                qualityscraped = '%sx%s' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber).zfill(2))
                        elif capitulo:
                            if scrapertools.find_single_match(capitulo, '\d+[x|X](\d+)'):
                                item_local.contentEpisodeNumber = int(scrapertools.find_single_match(scrapedtitle, '\d+[x|X](\d+)'))
                            qualityscraped = '%s' % capitulo
                        else:
                            qualityscraped = '%s' % scrapedtitle
                    
                    #Si todavía no sabemos el num de Episodio, lo buscamos
                    if not item_local.contentEpisodeNumber and item_local.contentType == 'episode':
                        try:
                            if scrapertools.find_single_match(scrapedtitle, '(\d+)[x|X](\d+)'):
                                item_local.contentSeason, item_local.contentEpisodeNumber = scrapertools.find_single_match(scrapedtitle, '(\d+)[x|X](\d+)')
                                qualityscraped = '%sx%s' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber).zfill(2))
                        except:
                            pass
                    
                    #Buscamos calidades
                    if scrapertools.find_single_match(scrapedenlace, '(\d+p)'):
                        qualityscraped += ' ' + scrapertools.find_single_match(scrapedenlace, '(\d+p)')
                    if qualityscraped:
                        quality = '[%s] %s' % (qualityscraped, item_local.quality)
                    
                    if scrapertools.find_single_match(item.url, '(\d+x\d+.*?\d+x\d+)') and not capitulo and not qualityscraped:
                        quality = '[%s] %s' % (scrapertools.find_single_match(scrapedenlace, '(\d+x\d+)'), quality)
                    elif capitulo and not qualityscraped:
                        quality = '[%s] %s' % (capitulo, quality)
                    if item.armagedon:                                              #Si es catastrófico, lo marcamos
                        quality = '[/COLOR][COLOR hotpink][E] [COLOR limegreen]%s' % quality

                    #Verificamos el si el enlace del servidor está activo
                    mostrar_server = True
                    if config.get_setting("hidepremium"):                           #Si no se aceptan servidore premium, se ignoran
                        mostrar_server = servertools.is_server_enabled(servidor)
                    
                    try:                                                                            #Obtenemos el enlace
                        if mostrar_server:
                            devuelve = servertools.findvideosbyserver(scrapedenlace, servidor)      #existe el link ?
                            if devuelve:
                                enlace = devuelve[0][1]                                             #Se guarda el link
                        if not enlace:
                            continue
                            
                        item_local.alive = servertools.check_video_link(enlace, servidor, timeout=timeout)      #activo el link ?
                        #Si el link no está activo se ignora
                        if "??" in item_local.alive:                                                            #dudoso
                            item_local.title = '[COLOR yellow][?][/COLOR] [COLOR yellow][%s][/COLOR] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (servidor.capitalize(), quality, str(item_local.language))
                        elif "no" in item_local.alive.lower():                  #No está activo.  Lo preparo, pero no lo pinto
                            item_local.title = '[COLOR red][%s][/COLOR] [COLOR yellow][%s][/COLOR] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (item_local.alive, servidor.capitalize(), quality, str(item_local.language))
                            logger.debug(item_local.alive + ": ALIVE / "  + servidor + " / " + enlace)
                            raise
                        else:                                                                               #Sí está activo
                            item_local.title = '[COLOR yellow][%s][/COLOR] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (servidor.capitalize(), quality, str(item_local.language))

                        #Ahora pintamos el link Directo
                        item_local.url = enlace
                        
                        #Preparamos título y calidad, quitamos etiquetas vacías
                        item_local.title = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', item_local.title)    
                        item_local.title = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', item_local.title)
                        item_local.title = item_local.title.replace("--", "").replace("[]", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()
                        quality = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', quality)
                        quality = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', quality)
                        quality = quality.replace("--", "").replace("[]", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()

                        item_local.action = "play"                                      #Visualizar vídeo
                        item_local.server = servidor                                    #Servidor Directo
                        
                        itemlist_t.append(item_local.clone(quality=quality))            #Pintar pantalla, si no se filtran idiomas
            
                        # Requerido para FilterTools
                        if config.get_setting('filter_languages', channel) > 0:         #Si hay idioma seleccionado, se filtra
                            item_local.quality = quality                                #Calidad
                            itemlist_f = filtertools.get_link(itemlist_f, item_local, list_language)  #Pintar pantalla, si no está vacío
                    except:
                        logger.error('ERROR al procesar enlaces DIRECTOS: ' + servidor + ' / ' + scrapedenlace)

                    #logger.debug("DIRECTO: " + scrapedenlace + " / title gen/torr: " + item.title + " / " + item_local.title + " / calidad: " + item_local.quality + " / tamaño: " + scrapedsize + " / content: " + item_local.contentTitle + " / " + item_local.contentSerieName)
                    #logger.debug(item_local)
    
    if item.videolibray_emergency_urls:                                                 #Si estamos cargados emergency_urls, no vamos
        return item
    
    if len(itemlist_f) > 0:                                                             #Si hay entradas filtradas...
        itemlist_alt.extend(itemlist_f)                                                 #Pintamos pantalla filtrada
    else:                                                                       
        if config.get_setting('filter_languages', channel) > 0 and len(itemlist_t) > 0: #Si no hay entradas filtradas ...
            thumb_separador = get_thumb("next.png")                             #... pintamos todo con aviso
            itemlist.append(Item(channel=item.channel, url=host, title="[COLOR red][B]NO hay elementos con el idioma seleccionado[/B][/COLOR]", thumbnail=thumb_separador, folder=False))
        itemlist_alt.extend(itemlist_t)                                                 #Pintar pantalla con todo si no hay filtrado
    
    #Si son múltiples episodios, ordenamos
    if len(itemlist_alt) > 1 and (item.contentType == 'episode' or item.contentType == 'season'):
        itemlist_alt = sorted(itemlist_alt, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))     #clasificamos
        tmdb.set_infoLabels(itemlist_alt, True)                                         #TMDB de la lista de episodios
    itemlist.extend(itemlist_alt)
    
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)                                                      #Lanzamos Autoplay

    return itemlist

    
def episodios(item):
    logger.info()
    itemlist = []
    
    #logger.debug(item)
    
    item.url = item.url.replace(host_alt, host)                                             #Cambio de dominio (videoteca)
    
    curr_page = 1                                                                           # Página inicial
    last_page = 99999                                                                       # Última página inicial
    if item.curr_page:
        curr_page = int(item.curr_page)                                                     # Si viene de una pasada anterior, lo usamos
        del item.curr_page                                                                  # ... y lo borramos
    if item.last_page:
        last_page = int(item.last_page)                                                     # Si viene de una pasada anterior, lo usamos
        del item.last_page                                                                  # ... y lo borramos
    url_item = item.url.replace('1-.fx', '%s-.fx').replace('-1.fx', '-%s.fx')
    if item.from_title:
        item.title = item.from_title
    
    #Limpiamos num. Temporada y Episodio que ha podido quedar por Novedades
    season_display = 0
    if item.contentSeason:
        if item.season_colapse:                                                             #Si viene del menú de Temporadas...
            season_display = item.contentSeason                                     #... salvamos el num de sesión a pintar
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
        tmdb.set_infoLabels(item, True)                             #TMDB de cada Temp
    except:
        pass
        
    modo_ultima_temp_alt = modo_ultima_temp
    if item.ow_force == "1":                                        #Si hay un traspaso de canal o url, se actualiza todo 
        modo_ultima_temp_alt = False
    
    max_temp = 1
    if item.infoLabels['number_of_seasons']:
        max_temp = item.infoLabels['number_of_seasons']
    y = []
    if modo_ultima_temp_alt and item.library_playcounts:            #Averiguar cuantas temporadas hay en Videoteca
        patron = 'season (\d+)'
        matches = re.compile(patron, re.DOTALL).findall(str(item.library_playcounts))
        for x in matches:
            y += [int(x)]
        max_temp = max(y)

    while curr_page <= last_page:
    
        # Descarga la página
        data = ''
        url = url_item % curr_page                                                  #Inserto en num de página en la url
        try:
            data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)|&nbsp;", "", httptools.downloadpage(url, timeout=timeout).data)
            data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
        except:                                                                     #Algún error de proceso, salimos
            pass
            
        if not data:
            logger.error("ERROR 01: EPISODIOS: La Web no responde o la URL es erronea" + item.url)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: EPISODIOS:.  La Web no responde o la URL es erronea. Si la Web está activa, reportar el error con el log'))
            break                                                                   #Pintamos lo que tenemos
        
        curr_page += 1                                                              #Apunto ya a la página siguiente

        #Usamos el mismo patrón que en listado
        patron = '<div class="MiniFicha"><a href="([^"]+)" title="([^"]+)">'
        patron += '<img src="([^"]+).*?'
        patron += '<div class="MiniF_TitleSpecial">[^>]+>([^<]+).*?'
        patron += '<b>Categoria:\s*<\/b>([^&]+)&raquo;\s*([^<]+).*?'
        patron += '<div class="OpcionesDescargasMini">(.*?)<\/div>'
        matches = re.compile(patron, re.DOTALL).findall(data)
        if not matches:                                                             #error
            item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
            if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
                item, itemlist = generictools.post_tmdb_episodios(item, itemlist)   #Llamamos al método para el pintado del error
                return itemlist                                                     #Salimos
            
            logger.error("ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
            break                                           #si no hay más datos, algo no funciona, pintamos lo que tenemos

        #logger.debug("PATRON: " + patron)
        #logger.debug(matches)
        #logger.debug(data)
        
        #Buscamos la última página, pero solo en la primera pasada, porque en búsquedan deja de funcionar a partir de la seguna página
        if last_page == 99999:                                                      #Si es el valor inicial, buscamos
            patron = '<div class="sPages">.*?'
            patron += '<a href="[^"]+">Siguiente'
            patron += ' &raquo;<\/a><br> En Total (\d+) Pagina?'                    #Esta es la parte que vale
            try:
                last_page = int(scrapertools.find_single_match(data, patron))       #lo cargamos como entero
            except:
                last_page = 1                                                       #Si no lo encuentra, lo ponemos a 1
                
        season = max_temp
        #Comprobamos si realmente sabemos el num. máximo de temporadas
        if item.library_playcounts or (item.infoLabels['number_of_seasons'] and item.tmdb_stat):
            num_temporadas_flag = True
        else:
            num_temporadas_flag = False

        # Recorremos todos los episodios generando un Item local por cada uno en Itemlist
        for scrapedurl, scrapedenlace, scrapedthumbnail, scrapedtitle, cat_ppal, cat_sec, opciones in matches:
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
            
            if 'VO' in title or 'V.O' in title:
                item_local.language = ['VO']
                title = title.replace('VO', '').replace('V.O', '')

            try:
                item_local.contentEpisodeNumber = 0
                if 'miniserie' in title.lower():
                    item_local.contentSeason = 1
                    title = title.replace('miniserie', '').replace('MiniSerie', '')
                elif 'completa' in title.lower():
                    patron = '[t|T]emporada (\d+) [c|C]ompleta'
                    item_local.contentSeason = int(scrapertools.find_single_match(title, patron))
                if not item_local.contentSeason:
                    #Extraemos los episodios
                    patron = '(\d{1,2})[x|X](\d{1,2})'
                    item_local.contentSeason, item_local.contentEpisodeNumber = scrapertools.find_single_match(title, patron)
                    item_local.contentSeason = int(item_local.contentSeason)
                    item_local.contentEpisodeNumber = int(item_local.contentEpisodeNumber)
            except:
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

            if modo_ultima_temp_alt and item.library_playcounts:    #Si solo se actualiza la última temporada de Videoteca
                if item_local.contentSeason < max_temp:
                    curr_page = 999999                              #Sale del bucle de leer páginas
                    break                                           #Sale del bucle actual del WHILE de episodios por página

            if season_display > 0:
                if item_local.contentSeason > season_display:
                    continue
                elif item_local.contentSeason < season_display:
                    break
            
            itemlist.append(item_local.clone())
            
            #logger.debug(item_local)
            
    if len(itemlist) > 1:
        itemlist = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))       #clasificamos
        
    if item.season_colapse and not item.add_videolibrary:               #Si viene de listado, mostramos solo Temporadas
        item, itemlist = generictools.post_tmdb_seasons(item, itemlist)

    if not item.season_colapse:                                         #Si no es pantalla de Temporadas, pintamos todo
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

    
def year(item):
    logger.info()
    
    texto = platformtools.dialog_numeric(0, heading='Año a buscar')
    
    item.url = item.url % texto

    if texto != '' and texto != None:
        return listado(item)
 
 
def search(item, texto):
    logger.info()
    #texto = texto.replace(" ", "+")
    
    try:
        if item.extra == "search":
            item.url = item.url + texto + "-sch.fx"
        else:
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
            item.url = host + 'descarga-0-58128-0-0-fx-1-1-.fx'
            item.extra = "HD-RIP"
            item.channel = "estrenosgo"
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
