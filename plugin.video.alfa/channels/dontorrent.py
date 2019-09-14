# -*- coding: utf-8 -*-

import re
import urlparse
import time
import traceback

from channelselector import get_thumb
from core import httptools
from core import scrapertools
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

host = 'https://dontorrent.com/'
channel = 'dontorrent'
categoria = channel.capitalize()
__modo_grafico__ = config.get_setting('modo_grafico', channel)
modo_ultima_temp = config.get_setting('seleccionar_ult_temporadda_activa', channel)        #Actualización sólo últ. Temporada?
timeout = config.get_setting('timeout_downloadpage', channel)
season_colapse = config.get_setting('season_colapse', channel)                  # Season colapse?
filter_languages = config.get_setting('filter_languages', channel)              # Filtrado de idiomas?


def mainlist(item):
    logger.info()
    itemlist = []
    
    thumb_cartelera = get_thumb("now_playing.png")
    thumb_pelis = get_thumb("channels_movie.png")
    thumb_pelis_hd = get_thumb("channels_movie_hd.png")
    thumb_pelis_VO = get_thumb("channels_vos.png")
    
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_series_hd = get_thumb("channels_tvshow_hd.png")
    thumb_series_VOD = get_thumb("videolibrary_tvshow.png")
    
    thumb_documentales = get_thumb("channels_documentary.png")
    thumb_alfabeto = get_thumb("channels_movie_az.png")
    thumb_genero = get_thumb("genres.png")
    thumb_buscar = get_thumb("search.png")
    thumb_separador = get_thumb("next.png")
    thumb_settings = get_thumb("setting_0.png")
    
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(Item(channel=item.channel, title="Novedades", action="novedades_menu", 
                url=host + "ultimos", thumbnail=thumb_cartelera, extra2="novedades"))
    itemlist.append(Item(channel=item.channel, title="Películas", action="submenu", 
                url=host, thumbnail=thumb_pelis, extra="peliculas"))
    itemlist.append(Item(channel=item.channel, title="Series", action="submenu", 
                url=host, thumbnail=thumb_series, extra="series"))
    itemlist.append(Item(channel=item.channel, title="Documentales", action="submenu", 
                url=host, thumbnail=thumb_documentales, extra="documentales"))
    
    
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search",
                url=host, thumbnail=thumb_buscar, extra="search"))

    itemlist.append(Item(channel=item.channel, url=host, title="[COLOR yellow]Configuración:[/COLOR]", 
                folder=False, thumbnail=thumb_separador))
    
    itemlist.append(Item(channel=item.channel, action="configuracion", title="Configurar canal", 
                thumbnail=thumb_settings))
    
    autoplay.show_option(item.channel, itemlist)                                #Activamos Autoplay

    return itemlist
    
    
def configuracion(item):
    from platformcode import platformtools
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return


def submenu(item):
    logger.info()
    itemlist = []
    
    thumb_alfabeto = get_thumb("channels_movie_az.png")
    thumb_genero = get_thumb("genres.png")
    thumb_anno = get_thumb("update.png")

    data = ''
    response = httptools.downloadpage(item.url, timeout=timeout, ignore_response_code=True)
    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", response.data).replace("'", '"')
    data = unicode(data, "utf-8", errors="replace").encode("utf-8")
        
    patron = '<span\s*class="list-group-item\s*top">Torrents<\/span>(.*?)<\/span><\/div>'
    #Verificamos si se ha cargado una página, y si además tiene la estructura correcta
    if not data or not scrapertools.find_single_match(data, patron):
        
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            for clone_inter, autoridad in item.intervencion:
                thumb_intervenido = get_thumb(autoridad)
                itemlist.append(item.clone(action='', title="[COLOR yellow]" + 
                        clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial + 
                        '. Reportar el problema en el foro', thumbnail=thumb_intervenido))
            return itemlist                                                     #Salimos
        
        logger.error("ERROR 01: SUBMENU: La Web no responde o ha cambiado de URL: " 
                        + item.url + data)
    
    if not data:                                                                #Si no ha logrado encontrar nada, salimos
        itemlist.append(item.clone(action='', title=item.category + 
                        ': ERROR 01: SUBMENU: La Web no responde o ha cambiado de URL. ' + 
                        'Si la Web está activa, reportar el error con el log'))
        return itemlist                                             #si no hay más datos, algo no funciona, pintamos lo que tenemos

    # Seleccionamos el bloque y buscamos los apartados
    data = scrapertools.find_single_match(data, patron)
    patron = '<a\s*href="([^"]+)"\s*class="list-group-item list-group-item-action">(.*?)<span'
    matches = re.compile(patron, re.DOTALL).findall(data)

    if not matches:
        logger.error("ERROR 02: SUBMENU: Ha cambiado la estructura de la Web " + 
                        " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.category + 
                        ': ERROR 02: SUBMENU: Ha cambiado la estructura de la Web.  '
                        + 'Reportar el error con el log'))
        return itemlist                                             #si no hay más datos, algo no funciona, pintamos lo que tenemos

    #logger.debug(patron)
    #logger.debug(matches)
    #logger.debug(data)
    
    # En películas las categorías se llaman con Post
    post_alfabeto = 'campo=letra&valor3=%s&valor=&valor2=&pagina=1'
    post_anno = 'campo=anyo&valor=%s&valor2=&valor3=&valor4=&pagina=1'
    post_genero = 'campo=genero&valor3=&valor=&valor2=%s&pagina=1'
    
    for scrapedurl, scrapedtitle in matches:
        if item.extra not in scrapedurl:                                        # Seleccionamos las categorias del apartado
            continue
        
        url = urlparse.urljoin(host, scrapedurl)
        itemlist.append(item.clone(action="listado", title=scrapedtitle.strip(), url=url+'/page/1', extra2='submenu'))
        if item.extra != 'peliculas':                                           # Para todo, menos películas
            itemlist.append(item.clone(action="alfabeto", title=scrapedtitle.strip() 
                    + " [A-Z]", url=url + "/letra-%s/page/1", thumbnail=thumb_alfabeto))
        
        elif scrapedtitle.strip() == 'Pel&iacute;culas':                        # Categorías sólo de películas
            itemlist.append(item.clone(action="alfabeto", title="         " 
                    + "- Por [A-Z]", url=url + "/buscar", post=post_alfabeto, thumbnail=thumb_alfabeto))
            itemlist.append(item.clone(action="genero", title="         " 
                    + "- Por Género", url=url, post=post_genero, thumbnail=thumb_genero))
            itemlist.append(item.clone(action="anno", title="         " 
                    + "- Buscar por Año", url=url + "/buscar", post=post_anno, thumbnail=thumb_anno))

    return itemlist
    
    
def alfabeto(item):
    logger.info()
    itemlist = []

    for letra in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 
                        'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 
                        'Z', '.']:
        if item.extra != 'peliculas':
            itemlist.append(item.clone(action="listado", title=letra.replace('.', 'TODAS'), 
                        url=item.url % letra.lower(), extra2='alfabeto'))
        else:
            itemlist.append(item.clone(action="listado", title=letra.replace('.', 'TODAS'), 
                        post=item.post % letra, extra2='alfabeto'))

    return itemlist
    

def anno(item):
    logger.info()
    from platformcode import platformtools
    
    itemlist = []

    year = platformtools.dialog_numeric(0, "Introduzca el Año de búsqueda", default="")
    item.post = item.post % year
    item.extra2 = 'anno'

    return listado(item)

    
def genero(item):
    logger.info()
    itemlist = []

    data = ''
    response = httptools.downloadpage(item.url, timeout=timeout, ignore_response_code=True)
    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", response.data).replace("'", '"')
    data = unicode(data, "utf-8", errors="replace").encode("utf-8")
        
    patron = '<select\s*name="valor2"\s*id="valor2"\s*'
    patron += 'class="[^"]+">(.*?)<\/select>'
    #Verificamos si se ha cargado una página, y si además tiene la estructura correcta
    if not data or not scrapertools.find_single_match(data, patron):
        
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            for clone_inter, autoridad in item.intervencion:
                thumb_intervenido = get_thumb(autoridad)
                itemlist.append(item.clone(action='', title="[COLOR yellow]" + 
                        clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial + 
                        '. Reportar el problema en el foro', thumbnail=thumb_intervenido))
            return itemlist                                                     #Salimos
        
        logger.error("ERROR 01: SUBMENU: La Web no responde o ha cambiado de URL: " 
                        + item.url + data)
    
    if not data:                                                                #Si no ha logrado encontrar nada, salimos
        itemlist.append(item.clone(action='', title=item.category + 
                        ': ERROR 01: SUBMENU: La Web no responde o ha cambiado de URL. ' + 
                        'Si la Web está activa, reportar el error con el log'))
        return itemlist                                             #si no hay más datos, algo no funciona, pintamos lo que tenemos

    data = scrapertools.find_single_match(data, patron)
    patron = '<option[^>]*>(.*?)<\/option>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    if not matches:
        logger.error("ERROR 02: SUBMENU: Ha cambiado la estructura de la Web " + 
                        " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.category + 
                        ': ERROR 02: SUBMENU: Ha cambiado la estructura de la Web.  '
                        + 'Reportar el error con el log'))
        return itemlist                                             #si no hay más datos, algo no funciona, pintamos lo que tenemos

    #logger.debug(patron)
    #logger.debug(matches)
    #logger.debug(data)
    
    for gen in matches:
        itemlist.append(item.clone(action="listado", title=gen, url=item.url + "/buscar", 
                        extra2='genero', post=item.post % gen))

    return itemlist
    
    
def novedades_menu(item):
    logger.info()
    itemlist = []

    for novedad in ['Peliculas', 'Series', 'Documentales']:
        itemlist.append(item.clone(action="novedades", title=novedad, extra=novedad.lower()))

    return itemlist
    

def novedades(item):
    logger.info()
    itemlist = []
    matches_fin = []

    data = ''
    response = httptools.downloadpage(item.url, timeout=timeout, ignore_response_code=True)
    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", response.data).replace("'", '"')
    data = unicode(data, "utf-8", errors="replace").encode("utf-8").replace("'", '"')
        
    patron = '<span\s*class="text-muted">(?:\d{4})?[^<]+<\/span>\s*<a\s*href="([^"]+)"'
    patron += '\s*class="text-primary">([^<]+)<\/a>(?:\s*<span\s*class="text-muted">\((.*?)\)<\/span>)?'
    #Verificamos si se ha cargado una página, y si además tiene la estructura correcta
    if not data or not scrapertools.find_single_match(data, patron):
        
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            for clone_inter, autoridad in item.intervencion:
                thumb_intervenido = get_thumb(autoridad)
                itemlist.append(item.clone(action='', title="[COLOR yellow]" + 
                        clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial + 
                        '. Reportar el problema en el foro', thumbnail=thumb_intervenido))
            return itemlist                                                     #Salimos
        
        logger.error("ERROR 01: SUBMENU: La Web no responde o ha cambiado de URL: " 
                        + item.url + data)
    
    if not data:                                                                #Si no ha logrado encontrar nada, salimos
        itemlist.append(item.clone(action='', title=item.category + 
                        ': ERROR 01: SUBMENU: La Web no responde o ha cambiado de URL. ' + 
                        'Si la Web está activa, reportar el error con el log'))
        return itemlist                                             #si no hay más datos, algo no funciona, pintamos lo que tenemos

    matches = re.compile(patron, re.DOTALL).findall(data)

    if not matches:
        logger.error("ERROR 02: SUBMENU: Ha cambiado la estructura de la Web " + 
                        " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.category + 
                        ': ERROR 02: SUBMENU: Ha cambiado la estructura de la Web.  '
                        + 'Reportar el error con el log'))
        return itemlist                                             #si no hay más datos, algo no funciona, pintamos lo que tenemos

    #logger.debug(patron)
    #logger.debug(matches)
    #logger.debug(data)
    
    extra = item.extra                                                          # Ajuste de categorías a la url
    if extra == 'peliculas':
        extra = 'pelicula'
    elif extra == 'series':
        extra = 'serie'
    elif extra == 'documentales':
        extra = 'documental'
    
    for scrapedurl, scrapedtitle, scrapedquality in matches:
        if extra not in scrapedurl:
            continue
        matches_fin.append((scrapedurl, scrapedtitle, scrapedquality))          # Guardamos las urls de la categoría

    item.matches = matches_fin
    return listado(item)


def listado(item):                                                              # Listado principal y de búsquedas
    logger.info()
    itemlist = []
    item.category = categoria
    thumb_pelis = get_thumb("channels_movie.png")
    thumb_series = get_thumb("channels_tvshow.png")

    #logger.debug(item)
    
    curr_page = 1                                                               # Página inicial
    last_page = 99999                                                           # Última página inicial
    if item.curr_page:
        curr_page = int(item.curr_page)                                         # Si viene de una pasada anterior, lo usamos
        del item.curr_page                                                      # ... y lo borramos
    if item.last_page:
        last_page = int(item.last_page)                                         # Si viene de una pasada anterior, lo usamos
        del item.last_page                                                      # ... y lo borramos
    
    cnt_tot = 30                                                                # Poner el num. máximo de items por página
    cnt_title = 0                                                               # Contador de líneas insertadas en Itemlist
    inicio = time.time()                                    # Controlaremos que el proceso no exceda de un tiempo razonable
    fin = inicio + 5                                                            # Después de este tiempo pintamos (segundos)
    timeout_search = timeout * 2                                                # Timeout para descargas
    if item.extra == 'search' and item.extra2 == 'episodios':                   # Si viene de episodio que quitan los límites
        cnt_tot = 999
        fin = inicio + 30
        

    #Sistema de paginado para evitar páginas vacías o semi-vacías en casos de búsquedas con series con muchos episodios
    title_lista = []                            # Guarda la lista de series que ya están en Itemlist, para no duplicar lineas
    if item.title_lista:                                    # Si viene de una pasada anterior, la lista ya estará guardada
        title_lista.extend(item.title_lista)                                    # Se usa la lista de páginas anteriores en Item
        del item.title_lista                                                    # ... limpiamos
    matches = []
        
    if not item.extra2:                                                         # Si viene de Catálogo o de Alfabeto
        item.extra2 = ''
        
    post = ''
    if item.post:                                                               # Rescatamos el Post, si lo hay
        post = item.post
    
    next_page_url = item.url
    #Máximo num. de líneas permitidas por TMDB. Máx de 5 segundos por Itemlist para no degradar el rendimiento
    while (cnt_title < cnt_tot and curr_page <= last_page and fin > time.time()) or item.matches:
    
        # Descarga la página
        data = ''
        cnt_match = 0                                                           # Contador de líneas procesadas de matches
        if not item.matches:                                                    # si no viene de una pasada anterior, descargamos
            response = httptools.downloadpage(next_page_url, timeout=timeout_search, ignore_response_code=True, post=post)
            data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", response.data).replace("'", '"')
            data = unicode(data, "utf-8", errors="replace").encode("utf-8")
            
            curr_page += 1                                                      #Apunto ya a la página siguiente
            if not data:                                                        #Si la web está caída salimos sin dar error
                logger.error("ERROR 01: LISTADO: La Web no responde o ha cambiado de URL: " 
                            + item.url + " / DATA: " + data)
                itemlist.append(item.clone(action='', title=item.channel.capitalize() + 
                            ': ERROR 01: LISTADO:.  La Web no responde o ha cambiado de URL. ' 
                            + 'Si la Web está activa, reportar el error con el log'))
                if len(itemlist) > 1:                                           # Si hay algo que pintar lo pintamos
                    last_page = 0
                    break
                return itemlist                                                 # Si no hay nada más, salimos directamente

        #Patrón para búsquedas, pelis y series
        if item.extra == 'search':                                              # Búsquedas...
            patron = '<p><span><a\s*href="([^"]+)"\s*class="[^"]+">(?:<span\s*class="[^"]+">)?'
            patron += '(.*?)(?:\((.*?)\))?(?:<\/a>|<\/span>)<\/span><span\s*class=[^>]+>'
            patron += '(?:Pel.*?|Serie.*?|Document.*?)<\/span><\/p>'
            #patron += '<\/span><span\s*class=[^>]+>(.*?)<\/span><\/p>'
        elif item.extra == 'peliculas' and (item.extra2 == 'alfabeto' or item.extra2 == 'genero' or item.extra2 == 'anno'):
            patron = '<a\s*class="position-relative"\s*href="([^"]+)"[^>]+><p\s*class=[^>]+>'
            patron += '([^<]+)<\/p><[^>]+><p>.*?<\/p><\/div>"><img\s*style=[^>]+>\s*'
            patron += '<span\s*class=[^>]+>([^<]+)<\/span><\/a>'
        elif (item.extra == 'series' or item.extra == 'documentales') and item.extra2 == 'alfabeto':    # Series o documentales alfabeto
            patron = '<p><a href="([^"]+)">([^<]+)<\/a>()<\/p>'
        elif (item.extra == 'series' or item.extra == 'documentales') and item.extra2 == 'novedades':   # Series, Docs desde Novedades
            patron = '(?:Temporada.*|Miniserie.*): (\d+[x|X]\d+)'
        else:                                                                   # Películas o Series o Documentales menú
            patron = 'a\s*href="([^"]+)">([^<]+)<\/a>(?:\s*<b>\(([^\)]+)\)\s*<\/b>)?'

        if not item.matches:                                                    # De pasada anterior o desde Novedades?
            matches = re.compile(patron, re.DOTALL).findall(data)
        else:
            matches = item.matches
            del item.matches

        if not matches and item.extra != 'search':                              #error
            item = generictools.web_intervenida(item, data)                     #Verificamos que no haya sido clausurada
            if item.intervencion:                                               #Sí ha sido clausurada judicialmente
                item, itemlist = generictools.post_tmdb_episodios(item, itemlist)   #Llamamos al método para el pintado del error
                return itemlist                                                 #Salimos
            
            if ((item.extra == 'series' or item.extra == 'documentales') and \
                            item.extra2 == 'alfabeto' and curr_page > 1) or \
                            (last_page == 999 and curr_page > 1):               # No sabemos cuál es la última página
                last_page = 0
                break
            
            logger.error("ERROR 02: LISTADO: Ha cambiado la estructura de la Web " 
                        + " / PATRON: " + patron + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + 
                        ': ERROR 02: LISTADO: Ha cambiado la estructura de la Web.  ' 
                        + 'Reportar el error con el log'))
            break                                       #si no hay más datos, algo no funciona, pintamos lo que tenemos
        
        if not matches and item.extra == 'search':                              #búsqueda vacía
            if len(itemlist) > 0:                                               # Si hay algo que pintar lo pintamos
                last_page = 0
                break
            return itemlist                                                     #Salimos
        
        #logger.debug("PATRON: " + patron)
        #logger.debug(matches)
        #logger.debug(data)

        #Buscamos la próxima página
        if item.extra2 != 'novedades':
            if item.extra == 'peliculas' and item.extra2 == 'alfabeto' or item.extra2 == 'anno' \
                            or item.extra2 == 'genero':                         # Películas con Alfabeto y similares
                post = re.sub(r'pagina=(\d+)', 'pagina=%s' % str(curr_page), post)
            else:                                                               # Resto
                next_page_url = re.sub(r'page\/(\d+)', 'page/%s' % str(curr_page), item.url)
            #logger.debug('curr_page: ' + str(curr_page) + ' / last_page: ' + str(last_page))
        
        #Buscamos la última página
        if last_page == 99999:                                                  #Si es el valor inicial, buscamos
            if item.extra == 'peliculas' and item.extra2 == 'alfabeto' or item.extra2 == 'anno' \
                            or item.extra2 == 'genero':                         # Películas con Alfabeto y similares
                patron_last = '<option value="(\d+)"[^<]+<\/option><\/select>'
                try:
                    last_page = int(scrapertools.find_single_match(data, patron_last))
                except:                                                         #Si no lo encuentra, lo ponemos a 999
                    last_page = 999
            elif item.extra2 == 'novedades':                                    # Novedades, no hay última página
                last_page = 0
            else:                                                               # Resto, se descarga la página 9999 para ver la última real
                patron_last = '<li\s*class="page-item active"\s*aria-current="page">'
                patron_last += '<a\s*class="page-link" href="#">(\d+)<\/a><\/li>'
                last_page_url = re.sub(r'page\/(\d+)', 'page/9999', item.url)
                try:
                    response = httptools.downloadpage(last_page_url, timeout=timeout_search, ignore_response_code=True, post=post)
                    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", response.data).replace("'", '"')
                    data = unicode(data, "utf-8", errors="replace").encode("utf-8")
                    last_page = int(scrapertools.find_single_match(data, patron_last))
                except:                                                         #Si no lo encuentra, lo ponemos a 999
                    last_page = 999
            #logger.debug('curr_page: ' + str(curr_page) + ' / last_page: ' + str(last_page))
        
        #Empezamos el procesado de matches
        for scrapedurl, scrapedtitle, scrapedquality in matches:
            cnt_match += 1
            title = scrapertools.remove_htmltags(scrapedtitle).rstrip('.')      # Removemos Tags del título
            url = scrapedurl
            if '/aviso-legal' in url:                                           # Ignoramos estas entradas
                continue

            title_subs = []                                                     #creamos una lista para guardar info importante
            
            title = title.replace("á", "a").replace("é", "e").replace("í", "i")\
                        .replace("ó", "o").replace("ú", "u").replace("ü", "u")\
                        .replace("ï¿½", "ñ").replace("Ã±", "ñ").replace("&atilde;", "a")\
                        .replace("&etilde;", "e").replace("&itilde;", "i")\
                        .replace("&otilde;", "o").replace("&utilde;", "u")\
                        .replace("&ntilde;", "ñ").replace("&#8217;", "'")\
                        .replace("&amp;", "&")

            # Salvo que venga la llamada desde Episodios, se filtran las entradas para evitar duplicados de Temporadas
            url_list = url
            if '/serie' in url and not (item.extra == 'search' and item.extra2 == 'episodios'):
                if scrapertools.find_single_match(url_list, '-torrents-\d+-\d+-'):
                    url_list = re.sub('-torrents-\d+-\d+-', '-torrents-', url)
                else:
                    url_list = re.sub('\/\d+\/\d+\/', '/', url)
                url_list = re.sub('-(\d+)-Temporada(?:.$)?', '-X-Temporada', url_list)
            if url_list in title_lista:                                         #Si ya hemos procesado el título, lo ignoramos
                continue
            else:
                title_lista += [url_list]                                       #la añadimos a la lista de títulos
            
            cnt_title += 1                                                      # Incrementamos el contador de entradas válidas
            item_local = item.clone()                                           #Creamos copia de Item para trabajar
            if item_local.tipo:                                                 #... y limpiamos
                del item_local.tipo
            if item_local.totalItems:
                del item_local.totalItems
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
            
            # Después de un Search se restablecen las categorías
            if item_local.extra == 'search':
                if '/pelicula' in url:
                    item_local.extra = 'peliculas'                              # Película búsqueda
                elif '/serie' in url:
                    item_local.extra = 'series'                                 # Serie búsqueda
                else:
                    item_local.extra = 'documentales'                           # Documental búsqueda
                
            # Procesamos idiomas
            item_local.language = []                                            #creamos lista para los idiomas
            if '[Subs. integrados]' in title or '(Sub Forzados)' in title:
                title = title.replace('[Subs. integrados]', '')
                title = title.replace('(Sub Forzados)', '')
                item_local.language = ['VOS']                                   # añadimos VOS
            if '[Dual' in title:
                title = re.sub(r'(?i)\[dual.*?\]', '', title)
                item_local.language += ['DUAL']                                 # añadimos DUAL
            if not item_local.language:
                item_local.language = ['CAST']                                  # [CAST] por defecto
                
            # Procesamos Calidad
            item_local.quality = scrapertools.remove_htmltags(scrapedquality)   # iniciamos calidad
            if item_local.extra == 'series' or item_local.extra == 'documentales':
                if '[720p]' in title:
                    title = title.replace('[720p]', '')
                    item_local.quality = 'HDTV-720p'
                elif '[1080p]' in title:
                    title = title.replace('[1080p]', '')
                    item_local.quality = '1080p'
                else:
                    item_local.quality = 'HDTV'
            if '4k' in title.lower() and not '4k' in item_local.quality.lower():
                item_local.quality += ', 4K'
            if '3d' in title.lower() and not '3d' in item_local.quality.lower():
                item_local.quality += ', 3D'
                
            item_local.thumbnail = ''                                           #iniciamos thumbnail

            item_local.url = urlparse.urljoin(host, url)                        #guardamos la url final
            item_local.context = "['buscar_trailer']"                           #... y el contexto

            # Guardamos los formatos para películas
            if item_local.extra == 'peliculas':
                item_local.contentType = "movie"
                item_local.action = "findvideos"

            # Guardamos los formatos para series y documentales
            elif item_local.extra == 'series' or item_local.extra == 'documentales':
                item_local.contentType = "tvshow"
                item_local.action = "episodios"
                item_local.season_colapse = season_colapse                      #Muestra las series agrupadas por temporadas?

            #Limpiamos el título de la basura innecesaria
            if (item.extra == 'series' or item.extra == 'documentales') and item.extra2 == 'novedades': # Series, Docs desde Novedades
                title_subs += [scrapertools.find_single_match(title, patron)]   # Salvamos info de episodio
            if item_local.contentType == "tvshow":
                title = scrapertools.find_single_match(title, '(^.*?)\s*(?:$|\(|\[|-)')

            title = re.sub(r'(?i)TV|Online|(4k-hdr)|(fullbluray)|4k| - 4k|(3d)', '', title).strip()
            item_local.quality = re.sub(r'(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', 
                        '', item_local.quality).strip()

            #Analizamos el año.  Si no está claro ponemos '-'
            item_local.infoLabels["year"] = '-'
            
            #Terminamos de limpiar el título
            title = re.sub(r'[\(|\[]\s+[\)|\]]', '', title)
            title = title.replace('()', '').replace('[]', '').replace('[4K]', '').replace('(4K)', '').strip().lower().title()
            item_local.from_title = title.strip().lower().title()           #Guardamos esta etiqueta para posible desambiguación de título

            #Salvamos el título según el tipo de contenido
            if item_local.contentType == "movie":
                item_local.contentTitle = title
            else:
                item_local.contentSerieName = title.strip().lower().title()

            item_local.title = title.strip().lower().title()
                
            #Guarda la variable temporal que almacena la info adicional del título a ser restaurada después de TMDB
            item_local.title_subs = title_subs
                
            #Salvamos y borramos el número de temporadas porque TMDB a veces hace tonterias.  Lo pasamos como serie completa
            if item_local.contentSeason and (item_local.contentType == "season" \
                        or item_local.contentType == "tvshow"):
                item_local.contentSeason_save = item_local.contentSeason
                del item_local.infoLabels['season']

            #Ahora se filtra por idioma, si procede, y se pinta lo que vale
            if filter_languages > 0:                                            #Si hay idioma seleccionado, se filtra
                itemlist = filtertools.get_link(itemlist, item_local, list_language)
            else:
                itemlist.append(item_local.clone())                             #Si no, pintar pantalla
            
            cnt_title = len(itemlist)                                           # Recalculamos los items después del filtrado
            if cnt_title >= cnt_tot and (len(matches) - cnt_match) + cnt_title > cnt_tot * 1.3:     #Contador de líneas añadidas
                break
            
            #logger.debug(item_local)
    
        matches = matches[cnt_match:]                                           # Salvamos la entradas no procesadas
    
    #Pasamos a TMDB la lista completa Itemlist
    tmdb.set_infoLabels(itemlist, __modo_grafico__, idioma_busqueda='es,en')
    
    #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
    item, itemlist = generictools.post_tmdb_listado(item, itemlist)

    # Si es necesario añadir paginacion
    if curr_page <= last_page or len(matches) > 0:
        if last_page:
            title = '%s de %s' % (curr_page-1, last_page)
        else:
            title = '%s' % curr_page-1

        itemlist.append(Item(channel=item.channel, action="listado", title=">> Página siguiente " 
                        + title, title_lista=title_lista, url=next_page_url, extra=item.extra, 
                        extra2=item.extra2, last_page=str(last_page), curr_page=str(curr_page), 
                        matches=matches, post=post))

    return itemlist

    
def findvideos(item):
    logger.info()
    itemlist = []
    itemlist_t = []                                                             #Itemlist total de enlaces
    itemlist_f = []                                                             #Itemlist de enlaces filtrados
    
    #logger.debug(item)

    #Bajamos los datos de las páginas
    if item.contentType == 'movie':
        patron = '(?:<p><b\s*class="bold">Clave:\s*<\/b><a\s*data-toggle="popover"'
        patron += '\s*title="Contraseña\s*del\s* Torrent.*?data-clave="([^"]+)">.*?)?'
        patron += '<a\s*class="text-white[^"]+"\s*style="font-size[^"]+"\s*href="([^"]+)"'
        patron += '\s*download>Descargar<\/a>()'
    else:
        patron = '<tr><td style=[^>]+>([^<]+)<\/td><td><a\s*class="text-white[^"]+"'
        patron += '\s*style="font-size[^"]+"\s*href="([^"]+)"\s*download>Descargar<\/a>'
        patron += '(?:<\/td><td\s*style=[^<]+<\/td><td\s*style=[^>]+><a\s*data-toggle='
        patron += '"popover"\s*title="Contraseña del Torrent.*?data-clave="([^"]+)">)?'
    
    data = ''
    response = httptools.downloadpage(item.url, timeout=timeout, ignore_response_code=True)
    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", response.data).replace("'", '"')
    data = unicode(data, "utf-8", errors="replace").encode("utf-8")
        
    if not data:
        logger.error("ERROR 01: FINDVIDEOS: La Web no responde o la URL es erronea: " + item.url)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + 
                        ': ERROR 01: FINDVIDEOS:.  La Web no responde o la URL es erronea. ' 
                        + 'Si la Web está activa, reportar el error con el log', folder=False))
        if item.emergency_urls and not item.videolibray_emergency_urls:         #Hay urls de emergencia?
            matches = item.emergency_urls[1]                                    #Restauramos matches de vídeos
            item.armagedon = True                                               #Marcamos la situación como catastrófica 
        else:
            if item.videolibray_emergency_urls:                                 #Si es llamado desde creación de Videoteca...
                return item                                                     #Devolvemos el Item de la llamada
            else:
                return itemlist                                     #si no hay más datos, algo no funciona, pintamos lo que tenemos

    if not item.armagedon:
        matches = re.compile(patron, re.DOTALL).findall(data)
    
    if not matches:                                                             #error
        if "Sorry, we haven't matched torrents for this" in data:               # No hay torrents
            return itemlist
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)  #Llamamos al método para el pintado del error
        else:
            logger.error("ERROR 02: FINDVIDEOS: No hay enlaces o ha cambiado la estructura de la Web " 
                        + " / PATRON: " + patron + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() 
                        + ': ERROR 02: FINDVIDEOS: No hay enlaces o ha cambiado la ' 
                        + 'estructura de la Web.  Verificar en la Web esto último y ' 
                        + 'reportar el error con el log', folder=False))
            if item.emergency_urls and not item.videolibray_emergency_urls:     #Hay urls de emergencia?
                matches = item.emergency_urls[1]                                #Restauramos matches de vídeos
                item.armagedon = True                                           #Marcamos la situación como catastrófica 
            else:
                if item.videolibray_emergency_urls:                             #Si es llamado desde creación de Videoteca...
                    return item                                                 #Devolvemos el Item de la llamada
                else:
                    return itemlist                                 #si no hay más datos, algo no funciona, pintamos lo que tenemos

    #logger.debug("PATRON: " + patron)
    #logger.debug(matches)
    #logger.debug(data)
    
    #Si es un lookup para cargar las urls de emergencia en la Videoteca...
    if item.videolibray_emergency_urls:
        item.emergency_urls = []                                                #Iniciamos emergency_urls
        item.emergency_urls.append([])                                          #Reservamos el espacio para los .torrents locales
        item.emergency_urls.append(matches)                                     #Salvamnos matches de los vídeos...  

    #Llamamos al método para crear el título general del vídeo, con toda la información obtenida de TMDB
    if not item.videolibray_emergency_urls:
        item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)

    #Ahora tratamos los enlaces .torrent con las diferentes calidades
    for scrapedtitle, scrapedurl, scrapedpassword in matches:
        # Si es una Serie o Documental, buscamos el episodio deseado
        if item.contentType == 'episode':
            patron_temp = '^(\d+)[x|X](\d+)\s*'
            patron_epi = '^(\d+)'
            if scrapertools.find_single_match(scrapedtitle, patron_temp):       # Formato estándar AAxBB
                temp, epi = scrapertools.find_single_match(scrapedtitle, patron_temp)
            elif scrapertools.find_single_match(scrapedtitle, patron_epi):      # Formato sólo de episodio, Temporada 1
                epi = scrapertools.find_single_match(scrapedtitle, patron_epi)
                temp = 1
            try:
                if item.contentSeason != int(temp) or item.contentEpisodeNumber != int(epi):    # Si no es el episodio buscado, pasamos
                    continue
            except:                                                             # Hay error?
                if item.extra == 'series':                                      # Si es Serie ignoramos la entrada
                    continue
        
        #Generamos una copia de Item para trabajar sobre ella
        item_local = item.clone()

        item_local.url = urlparse.urljoin(host, scrapedurl)

        # Restauramos urls de emergencia si es necesario
        local_torr = ''
        if item.emergency_urls and not item.videolibray_emergency_urls:
            item_local.torrent_alt = item.emergency_urls[0][0]                  #Guardamos la url del .Torrent ALTERNATIVA
            if item.armagedon:
                item_local.url = item.emergency_urls[0][0]                      #Restauramos la url
                if item_local.url.startswith("\\") or item_local.url.startswith("/"):
                    from core import filetools
                    if item.contentType == 'movie':
                        FOLDER = config.get_setting("folder_movies")
                    else:
                        FOLDER = config.get_setting("folder_tvshows")
                    local_torr = filetools.join(config.get_videolibrary_path(), FOLDER, item_local.url)
            if len(item.emergency_urls[0]) > 1:
                del item.emergency_urls[0][0]
        
        #Buscamos tamaño en el archivo .torrent
        if item_local.torrent_info:
            size = item_local.torrent_info
        else:
            size = ''
        if not size and not item.videolibray_emergency_urls:
            if not item.armagedon:
                size = generictools.get_torrent_size(item_local.url, local_torr=local_torr) #Buscamos el tamaño en el .torrent desde la web
        if size:
            size = size.replace('GB', 'G·B').replace('Gb', 'G·b').replace('MB', 'M·B')\
                        .replace('Mb', 'M·b').replace('.', ',')
            item_local.torrent_info = '%s, ' % size                             #Agregamos size
        if item_local.torrent_info:
            item_local.torrent_info = item_local.torrent_info.strip().strip(',')
            item.torrent_info = item_local.torrent_info
            if not item.unify:
                item_local.torrent_info = '[%s]' % item_local.torrent_info
   
        # Guadamos la password del RAR
        password = scrapedpassword
        if item.contentType == 'movie':
            password = scrapedtitle
        # Si tiene contraseña, la guardamos y la pintamos
        if password or item.password:
            if not item.password: item.password = password
            item_local.password = item.password
            itemlist.append(item.clone(action="", title="[COLOR magenta][B] Contraseña: [/B][/COLOR]'" 
                        + item_local.password + "'", folder=False))
        
        # Guardamos urls de emergencia si se viene desde un Lookup de creación de Videoteca
        if item.videolibray_emergency_urls:
            item.emergency_urls[0].append(item_local.url)                       #guardamos la url y nos vamos
            continue

        #Ahora pintamos el link del Torrent
        item_local.title = '[[COLOR yellow]?[/COLOR]] [COLOR yellow][Torrent][/COLOR] ' \
                        + '[COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR] %s' % \
                        (item_local.quality, str(item_local.language), \
                        item_local.torrent_info)
        
        #Preparamos título y calidad, quitando etiquetas vacías
        item_local.title = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', item_local.title)    
        item_local.title = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', item_local.title)
        item_local.title = item_local.title.replace("--", "").replace("[]", "")\
                        .replace("()", "").replace("(/)", "").replace("[/]", "")\
                        .replace("|", "").strip()
        item_local.quality = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', item_local.quality)
        item_local.quality = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', item_local.quality)
        item_local.quality = item_local.quality.replace("--", "").replace("[]", "")\
                        .replace("()", "").replace("(/)", "").replace("[/]", "")\
                        .replace("|", "").strip()
        
        item_local.alive = "??"                                                 #Calidad del link sin verificar
        item_local.action = "play"                                              #Visualizar vídeo
        item_local.server = "torrent"                                           #Seridor Torrent
        
        itemlist_t.append(item_local.clone())                                   #Pintar pantalla, si no se filtran idiomas
        
        # Requerido para FilterTools
        if config.get_setting('filter_languages', channel) > 0:                 #Si hay idioma seleccionado, se filtra
            itemlist_f = filtertools.get_link(itemlist_f, item_local, list_language)  #Pintar pantalla, si no está vacío

        #logger.debug("TORRENT: " + scrapedurl + " / title gen/torr: " + item.title + " / " + item_local.title + " / calidad: " + item_local.quality + " / content: " + item_local.contentTitle + " / " + item_local.contentSerieName)
        #logger.debug(item_local)

    #Si es un lookup para cargar las urls de emergencia en la Videoteca...
    if item.videolibray_emergency_urls:
        return item                                                             #... nos vamos
    
    if len(itemlist_f) > 0:                                                     #Si hay entradas filtradas...
        itemlist.extend(itemlist_f)                                             #Pintamos pantalla filtrada
    else:                                                                       
        if config.get_setting('filter_languages', channel) > 0 and len(itemlist_t) > 0: #Si no hay entradas filtradas ...
            thumb_separador = get_thumb("next.png")                             #... pintamos todo con aviso
            itemlist.append(Item(channel=item.channel, url=host, 
                        title="[COLOR red][B]NO hay elementos con el idioma seleccionado[/B][/COLOR]", 
                        thumbnail=thumb_separador, folder=False))
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
        if item.season_colapse:                                                 #Si viene del menú de Temporadas...
            season_display = item.contentSeason                                 #... salvamos el num de sesión a pintar
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
    try:
        tmdb.set_infoLabels(item, True, idioma_busqueda='es,en')
    except:
        pass
        
    modo_ultima_temp_alt = modo_ultima_temp
    if item.ow_force == "1":                                                    #Si hay una migración de canal o url, se actualiza todo 
        modo_ultima_temp_alt = False
    
    # Vemos la última temporada de TMDB y del .nfo
    max_temp = 1
    max_nfo = 0
    if item.infoLabels['number_of_seasons']:
        max_temp = item.infoLabels['number_of_seasons']
    y = []
    if modo_ultima_temp_alt and item.library_playcounts:                        #Averiguar cuantas temporadas hay en Videoteca
        patron = 'season (\d+)'
        matches = re.compile(patron, re.DOTALL).findall(str(item.library_playcounts))
        for x in matches:
            y += [int(x)]
        max_nfo = max(y)

    # Obtenemos todas las Temporada de la Serie desde Search
    list_temps = []
    list_temp = []
    patron_quality = '(?:Temporada|Miniserie)(?:-(.*?)(?:\.|$)|()\.|()$)'
    list_temps.append(item.url)
    
    # Si no hay TMDB o es sólo una temporada, listamos lo que tenemos
    if season_display == 0 and item.infoLabels['tmdb_id']:
        # Si hay varias temporadas, buscamos todas las ocurrencias y las filtraos por TMDB y calidad
        item_search = item.clone()
        item_search.extra = 'search'
        item_search.extra2 = 'episodios'
        title = scrapertools.find_single_match(item_search.contentSerieName, '(^.*?)\s*(?:$|\(|\[)')    # Limpiamos un poco el título
        item_search.title = title
        item_search.url = host + 'buscar/' + title.lower().replace(" ", "%20") + '/page/1'
        item_search.infoLabels = {}                                             # Limpiamos infoLabels
        itemlist = listado(item_search)                                         # Llamamos a 'Listado' para que procese la búsqueda

        for item_found in itemlist:                                             # Procesamos el Itemlist de respuesta
            if item_found.url in str(list_temps):                               # Si ya está la url, pasamos a la siguiente
                continue
            if not item_found.infoLabels['tmdb_id']:                            # tiene TMDB?
                continue
            if item_found.infoLabels['tmdb_id'] != item.infoLabels['tmdb_id']:  # Es el mismo TMDB?
                continue
            if item.language and item_found.language:                           # Es el mismo Idioma?
                if item.language != item_found.language:
                    continue
            if item.quality and item_found.quality:                             # Es la misma Calidad?, si la hay...
                if item.quality != item_found.quality:
                    continue
            elif scrapertools.find_single_match(item.url, patron_quality) != \
                        scrapertools.find_single_match(item_found.url, patron_quality):     # Coincide la calidad? (alternativo)
                continue
            list_temps.append(item_found.url)                                   # Si hay ocurrencia, guardamos la url
        
        if len(list_temps) > 1:
            list_temps = sorted(list_temps)                                     # Clasificamos las urls
            item.url = list_temps[-1]                                           # Guardamos la url de la última Temporada en .NFO

        if max_temp >= max_nfo and item.library_playcounts and modo_ultima_temp_alt:    # Si viene de videoteca, solo tratamos lo nuevo
            for url in list_temps:
                if scrapertools.find_single_match(url, '-(\d+)-Temporada'):     # Está la Temporada en la url?
                    try:                                                        # Miramos si la Temporada está procesada
                        if int(scrapertools.find_single_match(url, '-(\d+)-Temporada')) >= max_nfo:
                            list_temp.append(url)                               # No está procesada, la añadimos
                    except:
                        list_temp.append(url)
                else:                                                           # Si no está la Temporada en la url, se añade la url
                    list_temp.append(url)                                       # Por seguridad, la añadimos
        else:
            list_temp = list_temps[:]

    if not list_temp:
        list_temp = list_temps[:]                                               # Lista final de Temporadas a procesar

    # Descarga las páginas
    itemlist = []
    for url in list_temp:                                                       # Recorre todas las temporadas encontradas
        data = ''
        response = httptools.downloadpage(url, timeout=timeout, ignore_response_code=True)
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", response.data).replace("'", '"')
        data = unicode(data, "utf-8", errors="replace").encode("utf-8")

        if not data:
            logger.error("ERROR 01: EPISODIOS: La Web no responde o la URL es erronea" + item.url)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + 
                            ': ERROR 01: EPISODIOS:.  La Web no responde o la URL es erronea. ' 
                            + 'Si la Web está activa, reportar el error con el log'))
            return itemlist

        patron = '<tr><td style=[^>]+>([^<]+)<\/td><td><a\s*class="text-white[^"]+"'
        patron += '\s*style="font-size[^"]+"\s*href="([^"]+)"\s*download>Descargar<\/a>'
        patron += '(?:<\/td><td\s*style=[^<]+<\/td><td\s*style=[^>]+><a\s*data-toggle='
        patron += '"popover"\s*title="Contraseña del Torrent.*?data-clave="([^"]+)">)?'
        matches = re.compile(patron, re.DOTALL).findall(data)

        #logger.debug("PATRON: " + patron)
        #logger.debug(matches)
        #logger.debug(data)

        # Recorremos todos los episodios generando un Item local por cada uno en Itemlist
        for episode_num, epi_url, scrapedpassword in matches:
            item_local = item.clone()
            item_local.action = "findvideos"
            item_local.contentType = "episode"
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

            item_local.url = url                                                # Usamos las url de la temporada, no hay de episodio
            item_local.title = ''
            item_local.context = "['buscar_trailer']"
            title = episode_num
            if not item_local.infoLabels['poster_path']:
                item_local.thumbnail = item_local.infoLabels['thumbnail']
            
            # Extraemos números de temporada y episodio
            epi_rango = False
            alt_epi = 0
            try:
                if scrapertools.find_single_match(title, '^(\d+)[x|X](\d+)\s*(?:al|Al|AL|aL)\s*\d+[x|X](\d+)'):
                    item_local.contentSeason, item_local.contentEpisodeNumber, alt_epi = \
                            scrapertools.find_single_match(title, '^(\d+)[x|X](\d+)\s*(?:al|Al|AL|aL)\s*\d+[x|X](\d+)')
                    epi_rango = True
                elif scrapertools.find_single_match(title, '^(\d+)[x|X](\d+)\s*(?:al|Al|AL|aL)\s*(\d+)'):
                    item_local.contentSeason, item_local.contentEpisodeNumber, alt_epi = \
                            scrapertools.find_single_match(title, '^(\d+)[x|X](\d+)\s*(?:al|Al|AL|aL)\s*(\d+)')
                    epi_rango = True
                elif scrapertools.find_single_match(title, '^(\d+)[x|X](\d+)\s*-\s*(\d+)'):
                    item_local.contentSeason, item_local.contentEpisodeNumber, alt_epi = \
                            scrapertools.find_single_match(title, '^(\d+)[x|X](\d+)\s*-\s*(\d+)')
                    epi_rango = True
                elif scrapertools.find_single_match(title, '^(\d+)[x|X](\d+)'):
                    item_local.contentSeason, item_local.contentEpisodeNumber = \
                            scrapertools.find_single_match(title, '^(\d+)[x|X](\d+)')
                elif scrapertools.find_single_match(title, '^(\d+)'):
                    item_local.contentSeason = 1
                    item_local.contentEpisodeNumber = scrapertools.find_single_match(title, '^(\d+)')
                else:
                    raise
                item_local.contentSeason = int(item_local.contentSeason)
                item_local.contentEpisodeNumber = int(item_local.contentEpisodeNumber)
                alt_epi = int(alt_epi)
            except:
                logger.error('ERROR al extraer Temporada/Episodio: ' + title)
                item_local.contentSeason = 1
                item_local.contentEpisodeNumber = 0
                if item.extra == 'documentales':
                    item_local.contentEpisodeNumber = 1

            if epi_rango:                                                       #Si son episodios múltiples, lo guardamos
                item_local.infoLabels['episodio_titulo'] = 'al %s' % str(alt_epi).zfill(2)
                item_local.title = '%sx%s al %s' % (str(item_local.contentSeason), 
                        str(item_local.contentEpisodeNumber).zfill(2), str(alt_epi).zfill(2))
            else:
                item_local.title = '%sx%s - ' % (str(item_local.contentSeason), 
                        str(item_local.contentEpisodeNumber).zfill(2))
            
            if season_display > 0:                                              # Son de la temporada estos episodios?
                if item_local.contentSeason > season_display:
                    break
                elif item_local.contentSeason < season_display:
                    continue
            
            itemlist.append(item_local.clone())

            #logger.debug(item_local)
            
    if len(itemlist) > 1:
        itemlist = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))       #clasificamos
        
    if item.season_colapse and not item.add_videolibrary:                       #Si viene de listado, mostramos solo Temporadas
        item, itemlist = generictools.post_tmdb_seasons(item, itemlist, url='episode')

    if not item.season_colapse:                                                 #Si no es pantalla de Temporadas, pintamos todo
        # Pasada por TMDB y clasificación de lista por temporada y episodio
        tmdb.set_infoLabels(itemlist, True, idioma_busqueda='es,en')

        #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
        item, itemlist = generictools.post_tmdb_episodios(item, itemlist)
    
    #logger.debug(item)

    return itemlist
    
    
def actualizar_titulos(item):
    logger.info()
    
    #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels
    item = generictools.update_title(item)
    
    #Volvemos a la siguiente acción en el canal
    return item

    
def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "%20")
    
    try:
        item.url = host + 'buscar/' + texto + '/page/1'
        item.extra = 'search'

        if texto != '':
            return listado(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        logger.error(traceback.format_exc())
        return []
 
 
def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()

    item.title = "newest"
    item.category_new = "newest"
    item.channel = channel
    
    try:
        if categoria == 'peliculas':
            item.url = host + "ultimos"
            item.extra = "peliculas"
            item.extra2 = "novedades"
            item.action = "novedades"
            itemlist = novedades(item)
                
        elif categoria == 'series':
            item.url = host + "ultimos"
            item.extra = "series"
            item.extra2 = "novedades"
            item.action = "novedades"
            itemlist = novedades(item)

        if ">> Página siguiente" in itemlist[-1].title or "Pagina siguiente >>" in itemlist[-1].title:
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
