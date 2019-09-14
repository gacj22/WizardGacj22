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
from core import jsontools
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

host = 'https://pelismag.net'
channel = "pelismagnet"
api = host + '/api'
api_serie = host + "/seapi"
api_temp = host + "/sapi"


categoria = channel.capitalize()
__modo_grafico__ = config.get_setting('modo_grafico', channel)
timeout = config.get_setting('timeout_downloadpage', channel)


def mainlist(item):
    logger.info()
    itemlist = []
    
    thumb_pelis = get_thumb("channels_movie.png")
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_buscar = get_thumb("search.png")
    thumb_separador = get_thumb("next.png")
    thumb_settings = get_thumb("setting_0.png")

    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(Item(channel=item.channel, title="Películas", action="submenu", url=api, thumbnail=thumb_pelis, extra="peliculas"))
    itemlist.append(Item(channel=item.channel, title="Buscar en Películas >>", action="search", url=api + "?keywords=%s&page=0", thumbnail=thumb_buscar, extra="peliculas"))
    
    itemlist.append(Item(channel=item.channel, title="Series", action="submenu", url=api_serie, thumbnail=thumb_series, extra="series"))
    itemlist.append(Item(channel=item.channel, title="Buscar en Series >>", action="search", url=api_serie + "?keywords=%s&page=0", thumbnail=thumb_buscar, extra="series"))
    
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
    
    thumb_cartelera = get_thumb("now_playing.png")
    thumb_pelis_az = get_thumb("channels_movie_az.png")
    thumb_pelis = get_thumb("channels_movie.png")
    thumb_pelis_hd = get_thumb("channels_movie_hd.png")
    thumb_pelis_vos = get_thumb("channels_vos.png")
    thumb_popular = get_thumb("popular.png")
    thumb_generos = get_thumb("genres.png")
    thumb_spanish = get_thumb("channels_spanish.png")
    thumb_latino = get_thumb("channels_latino.png")
    thumb_torrent = get_thumb("channels_torrent.png")
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_series_az = get_thumb("channels_tvshow_az.png")
    thumb_buscar = get_thumb("search.png")
    
    
    if item.extra != "series":
        itemlist.append(item.clone(action="listado", title="Peliculas", url=api + "?sort_by=''&page=0", thumbnail=thumb_pelis))
        itemlist.append(item.clone(action="listado", title="     Estrenos", url=api + "?sort_by=date_added&page=0", thumbnail=thumb_cartelera))
        itemlist.append(item.clone(action="listado", title="     + Populares", url=api + "?page=0", thumbnail=thumb_popular))
        itemlist.append(item.clone(action="listado", title="     + Valoradas", url=api + "?sort_by=rating&page=0", thumbnail=thumb_popular))
        itemlist.append(item.clone(action="alfabeto", title="     Ordenado Alfabético", url=api, thumbnail=thumb_pelis_az))
        itemlist.append(item.clone(action="categorias", title="     Ordenado por Género", url=api, thumbnail=thumb_generos))
    
    else:
        itemlist.append(item.clone(action="listado", title="Series", url=api_serie + "?sort_by=''&page=0", thumbnail=thumb_series))
        itemlist.append(item.clone(action="listado", title="     Recientes", url=api_serie + "?sort_by=date_added&page=0", thumbnail=thumb_series))
        itemlist.append(item.clone(action="listado", title="     + Populares", url=api_serie + "?page=0", thumbnail=thumb_popular))
        itemlist.append(item.clone(action="listado", title="     + Valoradas", url=api_serie + "?sort_by=rating&page=0", thumbnail=thumb_popular))
        itemlist.append(item.clone(action="alfabeto", title="     Ordenado Alfabético", url=api_serie, thumbnail=thumb_series_az))
        itemlist.append(item.clone(action="categorias", title="     Ordenado por Género", url=api_serie, thumbnail=thumb_generos))
    
    return itemlist
    

def categorias(item):
    logger.info()
    itemlist = []
    
    data = ''
    try:
        data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|<Br>|<BR>|<br>|<br/>|<br />|-\s", "", httptools.downloadpage(host + "/principal", timeout=timeout).data)
        data = unicode(data, "utf-8", errors="replace").encode("utf-8")
    except:
        pass
        
    patron = '<ul class="dropdown-menu.*?>(.*?)</ul>'
    #Verificamos si se ha cargado una página, y si además tiene la estructura correcta
    if not data or not scrapertools.find_single_match(data, patron):
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            for clone_inter, autoridad in item.intervencion:
                thumb_intervenido = get_thumb(autoridad)
                itemlist.append(item.clone(action='', title="[COLOR yellow]" + clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial + '. Reportar el problema en el foro', thumbnail=thumb_intervenido))
            return itemlist                                                     #Salimos
        
        logger.error("ERROR 01: SUBMENU: La Web no responde o ha cambiado de URL: " + item.url + data)
    if not data:    #Si no ha logrado encontrar nada, salimos
        itemlist.append(item.clone(action='', title=item.category + ': ERROR 01: SUBMENU: La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
        return itemlist                                 #si no hay más datos, algo no funciona, pintamos lo que tenemos

    data = scrapertools.find_single_match(data, patron)
    patron = '<li><a href="\/?genero\/([^"]+)">(.*?)<\/a><\/li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    if not matches:
        logger.error("ERROR 02: SUBMENU: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.category + ': ERROR 02: SUBMENU: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
        return itemlist                                 #si no hay más datos, algo no funciona, pintamos lo que tenemos

    #logger.debug(matches)

    for scrapedgenero, scrapedtitle in matches:
        itemlist.append(item.clone(action="listado", title=scrapedtitle.capitalize().strip(), url=item.url + "?genre=" + scrapedgenero + "&page=0"))

    return itemlist
    
    
def alfabeto(item):
    logger.info()
    itemlist = []

    for letra in ['[0-9]', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']:
        itemlist.append(item.clone(action="listado", title=letra, url=item.url + "?keywords=^" + letra + "&page=0"))

    return itemlist

    
def listado(item):
    logger.info()
    itemlist = []
    item.category = categoria

    #logger.debug(item)
    
    curr_page = 1                                                               # Página inicial
    last_page = 99999                                                           # Última página inicial
    last_title = 99999                                                          # Última línea inicial
    cnt_matches = 0                                                             # Contador de líneas insertadas en Itemlist
    if item.curr_page:
        curr_page = int(item.curr_page)                                         # Si viene de una pasada anterior, lo usamos
        del item.curr_page                                                      # ... y lo borramos
    if item.last_page:
        last_page = int(item.last_page)                                         # Si viene de una pasada anterior, lo usamos
        del item.last_page                                                      # ... y lo borramos
    if item.cnt_matches:
        cnt_matches = int(item.cnt_matches)                                     # Si viene de una pasada anterior, lo usamos
    item.cnt_matches = 0
    del item.cnt_matches                                                        # ... y lo borramos

    cnt_tot = 40                                                                # Poner el num. máximo de items por página
    cnt_pct = 0.625                                                             #% de la página a llenar
    cnt_title = 0                                                               # Contador de líneas insertadas en Itemlist
    inicio = time.time()                                    # Controlaremos que el proceso no exceda de un tiempo razonable
    fin = inicio + 10                                                           # Después de este tiempo pintamos (segundos)
    timeout_search = timeout                                                    # Timeout para descargas
    if item.extra == 'search':
        timeout_search = timeout * 2                                            # Timeout un poco más largo para las búsquedas
        if timeout_search < 5:
            timeout_search = 5                                                  # Timeout un poco más largo para las búsquedas
    item.tmdb_stat = True                                                       # Este canal no es ambiguo en los títulos

    #Sistema de paginado para evitar páginas vacías o semi-vacías en casos de búsquedas con series con muchos episodios
    title_lista = []                            # Guarda la lista de series que ya están en Itemlist, para no duplicar lineas
    if item.title_lista:                                    # Si viene de una pasada anterior, la lista ya estará guardada
        title_lista.extend(item.title_lista)                                    # Se usa la lista de páginas anteriores en Item
        del item.title_lista                                                    # ... limpiamos
        
    if not item.extra2:                                                         # Si viene de Catálogo o de Alfabeto
        item.extra2 = ''
    
    next_page_url = item.url
    #Máximo num. de líneas permitidas por TMDB. Máx de 10 segundos por Itemlist para no degradar el rendimiento
    while cnt_title < cnt_tot * cnt_pct and cnt_matches + 1 < last_title and fin > time.time():
    
        # Descarga la página
        data = ''
        try:
            data = httptools.downloadpage(next_page_url, timeout=timeout_search).data
            data = unicode(data, "utf-8", errors="replace").encode("utf-8")
            pos = data.find('[')
            if pos > 0: data = data[pos:]
        except:
            pass
        
        if not data:                                    #Si la web está caída salimos sin dar error
            logger.error("ERROR 01: LISTADO: La Web no responde o ha cambiado de URL: " + item.url + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: LISTADO:.  La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
            break                                       #si no hay más datos, algo no funciona, pintamos lo que tenemos
        
        matches = jsontools.load(data)                                              #cargamos lo datos como dict.
        if not matches and data[1] != ']':                                          #error
            item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
            if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
                item, itemlist = generictools.post_tmdb_episodios(item, itemlist)   #Llamamos al método para el pintado del error
                return itemlist                                                     #Salimos
            
            logger.error("ERROR 02: LISTADO: Ha cambiado la estructura de la Web " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: LISTADO: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
            return itemlist                             #si no hay más datos, algo no funciona, pintamos lo que tenemos
        
        last_title = len(matches)                                                   #Tamaño de total matches
        matches = matches[cnt_matches:]                                             #avanzamos hasta la página actual
        
        #logger.debug(matches)
        #logger.debug(data)

        if last_page == 99999:                                              #Si es el valor inicial, cargamos el num. de items
            last_page = int((last_title / (cnt_tot * cnt_pct)))
            curr_page = 1

        #Empezamos el procesado de matches
        for titulo in matches:
            cnt_title += 1                                                          #Sumamos 1 a los títulos tratados
            if cnt_title > cnt_tot * cnt_pct:
                cnt_title += last_title
                break
            cnt_matches += 1                                                        #Sumamos 1 a total títulos tratados

            title = titulo.get("nom", "")                                           #nombre del título
            title = title.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ü", "u").replace("ï¿½", "ñ").replace("Ã±", "ñ").replace("&atilde;", "a").replace("&etilde;", "e").replace("&itilde;", "i").replace("&otilde;", "o").replace("&utilde;", "u").replace("&ntilde;", "ñ").replace("&#8217;", "'")

            item_local = item.clone()                                               #Creamos copia de Item para trabajar
            if item_local.tipo:                                                     #... y limpiamos
                del item_local.tipo
            if item_local.totalItems:
                del item_local.totalItems
            if item_local.post_num:
                del item_local.post_num
            if item_local.intervencion:
                del item_local.intervencion
            if item_local.viewmode:
                del item_local.viewmode
            item_local.text_bold = True
            del item_local.text_bold
            item_local.text_color = True
            del item_local.text_color
            
            if titulo.get("posterurl", ""):
                item_local.thumbnail = "http://image.tmdb.org/t/p/w342%s" % titulo.get("posterurl", "")     #thumb
            if titulo.get("backurl", ""):
                item_local.fanart = "http://image.tmdb.org/t/p/w1280%s" % titulo.get("backurl", "")         #Fanart
            url = titulo.get("magnets", {})                                             #magnet de diversas calidades
            year = titulo.get("year", "")                                               #año
            if titulo.get("id", ""): 
                item_local.infoLabels["tmdb_id"] = titulo.get("id", "")                 #TMDB id
                
            title_subs = []                                                 #creamos una lista para guardar info importante
            item_local.language = []                                        #iniciamos Lenguaje
            item_local.quality = ''                                         #inicialmos la calidad
            item_local.context = "['buscar_trailer']"

            item_local.contentType = "movie"                                #por defecto, son películas
            item_local.action = "findvideos"

            #Analizamos los formatos de series
            if item_local.extra == 'series':
                item_local.contentType = "tvshow"
                item_local.action = "episodios"
                item_local.season_colapse = True                            #Muestra las series agrupadas por temporadas
                item_local.url = "%s?id=%s" % (api_temp, titulo.get("id", ""))  #Salvamos la url special para series

            #Revisamos para peliculas todos los magnets, extrayendo dirección y calidad
            if item_local.contentType == "movie":
                item_local.url = []                                         #iniciamos dict. de magnets
                for etiqueta, magnet in titulo.get("magnets", {}).iteritems():
                    if magnet.get("magnet"):                                #buscamos los magnets activos
                        url = magnet.get("magnet")                          #salvamos el magnet
                        quality =  magnet.get("quality", "")                #salvamos la calidad del magnet
                        item_local.url +=[(url, quality)]                   #guardamos todo como url para findvideos

                        item_local.quality += "%s, " % quality.strip()      #agregamos a la calidad del título
                item_local.quality = re.sub(r', $', '', item_local.quality)
                if not item_local.url:                                      #si no hay magnets, no seguimos
                    continue

            if item_local.language == []:
                item_local.language = ['CAST']

            #Detectamos info interesante a guardar para después de TMDB
            if scrapertools.find_single_match(title, '[m|M].*?serie'):
                title = re.sub(r'[m|M]iniserie', '', title)
                title_subs += ["Miniserie"]
            if scrapertools.find_single_match(title, '[s|S]aga'):
                title = re.sub(r'[s|S]aga', '', title)
                title_subs += ["Saga"]
            if scrapertools.find_single_match(title, '[c|C]olecc'):
                title = re.sub(r'[c|C]olecc...', '', title)
                title_subs += ["Colección"]
                
            if "duolog" in title.lower():
                title_subs += ["[Saga]"]
                title = title.replace(" Duologia", "").replace(" duologia", "").replace(" Duolog", "").replace(" duolog", "")
            if "trilog" in title.lower():
                title_subs += ["[Saga]"]
                title = title.replace(" Trilogia", "").replace(" trilogia", "").replace(" Trilog", "").replace(" trilog", "")
            if "extendida" in title.lower() or "v.e." in title.lower()or "v e " in title.lower():
                title_subs += ["[V. Extendida]"]
                title = title.replace("Version Extendida", "").replace("(Version Extendida)", "").replace("V. Extendida", "").replace("VExtendida", "").replace("V Extendida", "").replace("V.Extendida", "").replace("V  Extendida", "").replace("V.E.", "").replace("V E ", "").replace("V:Extendida", "")
            
            #Analizamos el año.  Si no está claro ponemos '-'
            try:
                yeat_int = int(year)
                if yeat_int >= 1950 and yeat_int <= 2040:
                    item_local.infoLabels["year"] = yeat_int
                else:
                    item_local.infoLabels["year"] = '-'
            except:
                item_local.infoLabels["year"] = '-'

            #Empezamos a limpiar el título en varias pasadas
            title = re.sub(r'[s|S]erie', '', title)
            title = re.sub(r'- $', '', title)

            #Limpiamos el título de la basura innecesaria
            title = re.sub(r'(?i)TV|Online|Spanish|Torrent|en Espa\xc3\xb1ol|Español|Latino|Subtitulado|Blurayrip|Bluray rip|\[.*?\]|R2 Pal|\xe3\x80\x90 Descargar Torrent \xe3\x80\x91|Completa|Temporada|Descargar|Torren', '', title)

            #Terminamos de limpiar el título
            title = re.sub(r'\??\s?\d*?\&.*', '', title)
            title = re.sub(r'[\(|\[]\s+[\)|\]]', '', title)
            title = title.replace('()', '').replace('[]', '').strip().lower().title()

            item_local.from_title = title.strip().lower().title()       #Guardamos esta etiqueta para posible desambiguación de título

            #Salvamos el título según el tipo de contenido
            if item_local.contentType == "movie":
                item_local.contentTitle = title.strip().lower().title()
            else:
                item_local.contentSerieName = title.strip().lower().title()

            item_local.title = title.strip().lower().title()
                
            #Guarda la variable temporal que almacena la info adicional del título a ser restaurada después de TMDB
            item_local.title_subs = title_subs

            #Ahora se filtra por idioma, si procede, y se pinta lo que vale
            if config.get_setting('filter_languages', channel) > 0:     #Si hay idioma seleccionado, se filtra
                itemlist = filtertools.get_link(itemlist, item_local, list_language)
            else:
                itemlist.append(item_local.clone())                     #Si no, pintar pantalla
            
            #logger.debug(item_local)

    #Pasamos a TMDB la lista completa Itemlist
    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    
    #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
    item, itemlist = generictools.post_tmdb_listado(item, itemlist)

    # Si es necesario añadir paginacion  
    if cnt_title >= cnt_tot * cnt_pct:

        title = '%s' % curr_page

        if cnt_matches + 1 >= last_title:                               #Si hemos pintado ya todo lo de esta página...
            cnt_matches = 0                                             #... la próxima pasada leeremos otra página
            next_page_url = re.sub(r'page=(\d+)', r'page=' + str(int(re.search('\d+', next_page_url).group()) + 1), next_page_url)
        
        itemlist.append(Item(channel=item.channel, action="listado", title=">> Página siguiente " + title, url=next_page_url, extra=item.extra, extra2=item.extra2, last_page=str(last_page), curr_page=str(curr_page + 1), cnt_matches=str(cnt_matches)))

    return itemlist

    
def findvideos(item):
    logger.info()
    itemlist = []
    itemlist_t = []                                                         #Itemlist total de enlaces
    itemlist_f = []                                                         #Itemlist de enlaces filtrados
    if not item.language:
        item.language = ['CAST']                                            #Castellano por defecto
    matches = []
    item.category = categoria

    item.extra2 = 'xyz'
    del item.extra2
    
    #logger.debug(item)

    matches = item.url
    if not matches:                                                         #error
        logger.error("ERROR 02: FINDVIDEOS: No hay enlaces o ha cambiado la estructura de la Web: " + str(item))
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: FINDVIDEOS: No hay enlaces o ha cambiado la estructura de la Web.  Verificar en la Web esto último y reportar el error con el log', folder=False))
        
        if item.emergency_urls and not item.videolibray_emergency_urls:     #Hay urls de emergencia?
            item.url = item.emergency_urls[0][0]                            #Guardamos la url del .Torrent
            matches = item.emergency_urls[1]                                #Restauramos matches
            item.armagedon = True                                           #Marcamos la situación como catastrófica 
        else:
            if item.videolibray_emergency_urls:                             #Si es llamado desde creación de Videoteca...
                return item                                                 #Devolvemos el Item de la llamada
            else:
                return itemlist                                     #si no hay más datos, algo no funciona, pintamos lo que tenemos
    
    #logger.debug(matches)
    
    #Si es un lookup para cargar las urls de emergencia en la Videoteca...
    if item.videolibray_emergency_urls:
        item.emergency_urls = []                                            #Iniciamos emergency_urls
        item.emergency_urls.append([])                                      #Reservamos el espacio para los .torrents locales
        item.emergency_urls.append(matches)                                 #Salvamnos matches...  
    
    #Llamamos al método para crear el título general del vídeo, con toda la información obtenida de TMDB
    if not item.videolibray_emergency_urls:
        item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)

    #Ahora tratamos los enlaces .torrent
    for scrapedurl, quality in matches:                                     #leemos los magnets con la diferentes calidades
        #Generamos una copia de Item para trabajar sobre ella
        item_local = item.clone()
            
        item_local.url = scrapedurl
        if item.videolibray_emergency_urls:
            item.emergency_urls[0].append(scrapedurl)                       #guardamos la url y pasamos a la siguiente
            continue
        if item.emergency_urls and not item.videolibray_emergency_urls:
            item_local.torrent_alt = item.emergency_urls[0][0]              #Guardamos la url del .Torrent ALTERNATIVA
            if item.armagedon:
                item_local.url = item.emergency_urls[0][0]                  #... ponemos la emergencia como primaria
            del item.emergency_urls[0][0]                                   #Una vez tratado lo limpiamos
        
        size = ''
        if not item.armagedon:
            size = generictools.get_torrent_size(item_local.url)            #Buscamos el tamaño en el .torrent
        if size:
            size = size.replace('GB', 'G·B').replace('Gb', 'G·b').replace('MB', 'M·B')\
                        .replace('Mb', 'M·b').replace('.', ',')
        item_local.torrent_info = '%s' % size                               #Agregamos size
        if not item.unify:
            item_local.torrent_info = '[%s]' % item_local.torrent_info.strip().strip(',')
        if item.armagedon:                                                  #Si es catastrófico, lo marcamos
            quality = '[/COLOR][COLOR hotpink][E] [COLOR limegreen]%s' % quality
            
        #Añadimos la calidad y copiamos la duración
        item_local.quality = quality
        if scrapertools.find_single_match(item.quality, '(\[\d+:\d+\ h])'):
            item_local.quality += ' [/COLOR][COLOR white]%s' % scrapertools.find_single_match(item.quality, '(\[\d+:\d+\ h])')
        
        #Ahora pintamos el link del Torrent
        item_local.title = '[[COLOR yellow]?[/COLOR]] [COLOR yellow][Torrent][/COLOR] ' \
                        + '[COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR] %s' % \
                        (item_local.quality, str(item_local.language),  \
                        item_local.torrent_info)                                #Preparamos título de Torrent
        
        #Preparamos título y calidad, quitamos etiquetas vacías
        item_local.title = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', item_local.title)    
        item_local.title = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', item_local.title)
        item_local.title = item_local.title.replace("--", "").replace("[]", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()
        item_local.quality = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', item_local.quality)
        item_local.quality = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', item_local.quality).strip()
        item_local.quality = item_local.quality.replace("--", "").replace("[]", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()

        item_local.alive = "??"                                                 #Calidad del link sin verificar
        item_local.action = "play"                                              #Visualizar vídeo
        item_local.server = "torrent"                                           #Servidor Torrent
        
        itemlist_t.append(item_local.clone())                                   #Pintar pantalla, si no se filtran idiomas
        
        # Requerido para FilterTools
        if config.get_setting('filter_languages', channel) > 0:                 #Si hay idioma seleccionado, se filtra
            itemlist_f = filtertools.get_link(itemlist_f, item_local, list_language)  #Pintar pantalla, si no está vacío

        #logger.debug("TORRENT: " + scrapedurl + " / title gen/torr: " + item.title + " / " + item_local.title + " / calidad: " + item_local.quality + " / content: " + item_local.contentTitle + " / " + item_local.contentSerieName)
        
        #logger.debug(item_local)

    if item.videolibray_emergency_urls:                                         #Si ya hemos guardado todas las urls...
        return item                                                             #... nos vamos
    
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
    item.extra2 = 'xyz'
    del item.extra2

    #Limpiamos num. Temporada y Episodio que ha podido quedar por Novedades
    season_display = 0
    if item.contentSeason:
        if item.season_colapse:                                                     #Si viene del menú de Temporadas...
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

    # Descarga la página
    data = ''                                                       #Inserto en num de página en la url
    try:
        data = httptools.downloadpage(item.url, timeout=timeout).data
        data = unicode(data, "utf-8", errors="replace").encode("utf-8")
    except:                                                         #Algún error de proceso, salimos
        pass
        
    if not data:
        logger.error("ERROR 01: EPISODIOS: La Web no responde o la URL es erronea" + item.url)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: EPISODIOS:.  La Web no responde o la URL es erronea. Si la Web está activa, reportar el error con el log'))
        return itemlist

    #Buscamos los episodios
    matches = jsontools.load(data)
    if not matches:                                                             #error
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            item, itemlist = generictools.post_tmdb_episodios(item, itemlist)   #Llamamos al método para el pintado del error
            return itemlist                                                     #Salimos
        
        logger.error("ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

    #logger.debug(matches)

    # Recorremos todos los episodios generando un Item local por cada uno en Itemlist
    for temporada in matches.get("temporadas", []):
        if season_display > 0 and temporada.get("numerotemporada", 0) != season_display:   #si no es nuestra temp., pasamos
            continue
        
        #Si hay más de una temporada, solo las enumeramos
        if len(matches.get("temporadas", [])) > 1 and item.season_colapse:
            item_local = item.clone()                                       #creo una copia de Item
            item_local.action = "findvideos"                                #y lo preparo para la reproducción
            item_local.contentType = "episode"
            item_local.extra = "episodios"
            
            item_local.contentSeason = temporada.get("numerotemporada", 1)  #Guardo el num. de temporada
            item_local.contentEpisodeNumber = 1                             #relleno el num. de episodio por compatibilidad
            itemlist.append(item_local.clone())                             #lo pinto
            continue                                                        #Paso a la siguiente temporada

        #Aquí tratamos todos los episodios de una temporada
        season = temporada.get("numerotemporada", 1)
        for episodio in temporada.get("capituls", []):
            
            item_local = item.clone()                                       #creo una copia de Item
            item_local.action = "findvideos"                                #y lo preparo para la reproducción
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
            if item_local.tmdb_stat:
                del item_local.tmdb_stat
            
            item_local.title = ''
            item_local.context = "['buscar_trailer']"
            title = episodio.get("nomcapitul", "")                              #título del episodio
            info_epi = episodio.get("infocapitul", "")                          #información adicional del episodio
            item_local.language = []
            item_local.url = []

            if episodio.get("links", {}).get("magnet"):                         #buscamos los magnets activos
                url = episodio.get("links", {}).get("magnet")                   #salvamos el magnet
                quality =  episodio.get("links", {}).get("calitat", "")         #salvamos la calidad del magnet
                item_local.url +=[(url, quality)]                               #guardamos todo como url para findvideos
                item_local.quality = quality.strip()                            #agregamos a la calidad del título
            
            if not item_local.language:
                item_local.language += ['CAST']                                 #Castellano por defecto
            
            #Buscamos la Temporada y el Episodio
            try:
                item_local.contentSeason = int(season)                          #Copiamos el num. de Temporada
            except:
                item_local.contentSeason = 1                                    #Si hay error, lo dejamos en 1
            try:
                item_local.contentEpisodeNumber = int(episodio.get("numerocapitul", 1))     #Copiamos el num. de Episodio
            except:
                item_local.contentEpisodeNumber = 1                             #Si hay error, lo dejamos en 1
            if 'miniserie' in title.lower():                                    #Si es una Miniserie, lo ajustamos
                if not item_local.contentSeason:
                    item_local.contentSeason = 1
                title = title.replace('miniserie', '').replace('MiniSerie', '')

            #Si son episodios múltiples, lo extraemos
            patron1 = '\d+[x|X]\d{1,2}.?(?:y|Y|al|Al)?.?(?:(?:\d+[x|X])?(\d{1,2}))?'
            epi_rango = scrapertools.find_single_match(info_epi, patron1)
            if epi_rango:
                item_local.infoLabels['episodio_titulo'] = 'al %s ' % epi_rango
                item_local.title = '%sx%s al %s -' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber).zfill(2), str(epi_rango).zfill(2))
            else:
                item_local.title = '%sx%s -' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber).zfill(2))
                item.infoLabels['episodio_titulo'] = '%s' % title
            
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

    
def search(item, texto):
    logger.info()
    itemlist = []
    texto = texto.replace(' ', '%20')
    
    try:
        item.url = item.url % texto

        if texto != '':
            itemlist = listado(item)
            return itemlist
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
        if categoria == 'torrent' or categoria == 'peliculas':
            item.category_new= 'newest'
            item.channel = channel
            item.category = channel.capitalize()
            item.extra = "peliculas"
            
            item.url = api + "?sort_by=date_added&page=0"
            itemlist = listado(item)
            if ">> Página siguiente" in itemlist[-1].title:
                itemlist.pop()
            
            if categoria == 'torrent':
                item.extra = "series"
                item.url = api_serie + "?sort_by=date_added&page=0"
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
