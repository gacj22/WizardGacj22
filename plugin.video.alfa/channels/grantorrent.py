# -*- coding: utf-8 -*-

import re
import sys
import urllib
import urlparse
import time
import traceback

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

host = "https://grantorrent1.com/"
channel = "grantorrent"
domain = 'grantorrent1.com'
domain_files = 'files.grantorrent1.com'

dict_url_seasons = dict()
__modo_grafico__ = config.get_setting('modo_grafico', channel)
timeout = config.get_setting('timeout_downloadpage', channel)
if timeout > 0 and timeout <= 10: timeout = 15
modo_serie_temp = config.get_setting('seleccionar_serie_temporada', channel)
modo_ultima_temp = config.get_setting('seleccionar_ult_temporadda_activa', channel)


def mainlist(item):
    logger.info()

    itemlist = []
    
    thumb_pelis = get_thumb("channels_movie.png")
    thumb_pelis_hd = get_thumb("channels_movie_hd.png")
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_series_hd = get_thumb("channels_tvshow_hd.png")
    thumb_buscar = get_thumb("search.png")
    thumb_separador = get_thumb("next.png")
    thumb_settings = get_thumb("setting_0.png")
    
    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, action="submenu", title="Películas", url=host, extra="peliculas", thumbnail=thumb_pelis))

    #Buscar películas
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar en Películas >>", url=host, extra="peliculas", thumbnail=thumb_buscar))
    
    itemlist.append(Item(channel=item.channel, action="submenu", title="Series", url=host, extra="series", thumbnail=thumb_series))

    #Buscar series
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar en Series >>", url=host + "series/", extra="series", thumbnail=thumb_buscar))
        
    itemlist.append(Item(channel=item.channel, url=host, title="[COLOR yellow]Configuración:[/COLOR]", folder=False, thumbnail=thumb_separador))
    
    itemlist.append(Item(channel=item.channel, action="settingCanal", title="Configurar canal", thumbnail=thumb_settings))
    
    autoplay.show_option(item.channel, itemlist)            #Activamos Autoplay

    return itemlist

    
def settingCanal(item):
    from platformcode import platformtools
    return platformtools.show_channel_settings()


def submenu(item):
    logger.info()
    itemlist = []
    
    thumb_buscar = get_thumb("search.png")
    
    data = ''
    try:
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url, timeout=timeout).data)
        data = js2py_conversion(data, item.url)
        data = data.decode('utf8').encode('utf8')
    except:
        pass
        
    if not data:
        logger.error("ERROR 01: SUBMENU: La Web no responde o ha cambiado de URL: " + item.url)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
        return itemlist                                                     #Algo no funciona, pintamos lo que tenemos
    
    if item.extra == "peliculas":
        patron = '<li\s*class="navigation-top">\s*<a href="([^"]+)"\s*class="nav">([^<]+)<\/a><\/li>'
        matches = re.compile(patron, re.DOTALL).findall(data)
        if not matches:
            item = generictools.web_intervenida(item, data)                 #Verificamos que no haya sido clausurada
            if item.intervencion:                                           #Sí ha sido clausurada judicialmente
                for clone_inter, autoridad in item.intervencion:
                    thumb_intervenido = get_thumb(autoridad)
                    itemlist.append(item.clone(action='', title="[COLOR yellow]" + clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial + '. Reportar el problema en el foro', thumbnail=thumb_intervenido))
                return itemlist                                             #Salimos
        
        itemlist.append(item.clone(action="listado", title="Novedades", url=host))          #Menú principal películas
        
        itemlist.append(item.clone(action="generos", title="Películas **Géneros**", url=host))         #Lista de Géneros
    
        for scrapedurl, scrapedtitle in matches:
            title = scrapedtitle.strip()
        
            if not "películas" in scrapedtitle.lower():                     #Evita la entrada de ayudas y demás
                continue

            itemlist.append(item.clone(action="listado", title=title, url=scrapedurl))              #Menú películas

    else:                                                                   #Tratamos Series
        patron = '<li\s*class="navigation-top-dcha">\s*<a href="([^"]+)"\s*class="series">([^<]+)<\/a><\/li>'
        matches = re.compile(patron, re.DOTALL).findall(data)
        if not matches:
            item = generictools.web_intervenida(item, data)                 #Verificamos que no haya sido clausurada
            if item.intervencion:                                           #Sí ha sido clausurada judicialmente
                for clone_inter, autoridad in item.intervencion:
                    thumb_intervenido = get_thumb(autoridad)
                    itemlist.append(item.clone(action='', title="[COLOR yellow]" + clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial + '. Reportar el problema en el foro', thumbnail=thumb_intervenido))
                return itemlist                                             #Salimos

        for scrapedurl, scrapedtitle in matches:
            title = scrapedtitle.strip()

            itemlist.append(item.clone(action="listado", title=title, url=scrapedurl))              #Menú series
            
            itemlist.append(item.clone(action="generos", title="Series **Géneros**", url=host + "series/")) #Lista de Géneros

    return itemlist
    
    
def generos(item):
    logger.info()
    itemlist = []
    
    thumb_buscar = get_thumb("search.png")
    
    data = ''
    try:
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url, timeout=timeout).data)
        data = js2py_conversion(data, item.url)
    except:
        pass
        
    if not data:
        logger.error("ERROR 01: GÉNEROS: La Web no responde o ha cambiado de URL: " + item.url)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
        return itemlist                                                     #Algo no funciona, pintamos lo que tenemos
    
    item.extra2 = 'generos'
    patron = '<div class="titulo-sidebar">CATEGORÍAS<\/div><div class="contenedor-sidebar"><ul class="categorias-home">(.*?)<\/ul><\/div><\/aside>'     
    data = scrapertools.find_single_match(data, patron)
    patron = '\s*<a href="([^"]+)"><li class="categorias">(.*?)<\/li><\/a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    if not matches:
        item = generictools.web_intervenida(item, data)                 #Verificamos que no haya sido clausurada
        if item.intervencion:                                           #Sí ha sido clausurada judicialmente
            for clone_inter, autoridad in item.intervencion:
                thumb_intervenido = get_thumb(autoridad)
                itemlist.append(item.clone(action='', title="[COLOR yellow]" + clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial + '. Reportar el problema en el foro', thumbnail=thumb_intervenido))
            return itemlist                                             #Salimos

    for scrapedurl, scrapedtitle in matches:
        title = re.sub('\r\n', '', scrapedtitle).decode('utf8').encode('utf8').strip().capitalize()

        itemlist.append(item.clone(action="listado", title=title, url=scrapedurl))          #Listado de géneros

    return itemlist


def listado(item):
    logger.info()
    itemlist = []
    cnt_tot = 40                                                        # Poner el num. máximo de items por página
    cnt_title = 0                                                       # Contador de líneas insertadas en Itemlist
    result_mode = config.get_setting("result_mode", channel="search")   # Búsquedas globales: listado completo o no
    if not item.extra2:
        item.extra2 = ''
    
    #Sistema de paginado para evitar páginas vacías o semi-vacías en casos de búsquedas con series con muchos episodios
    title_lista = []                        # Guarda la lista de series que ya están en Itemlist, para no duplicar lineas
    if item.title_lista:                    # Si viene de una pasada anterior, la lista ya estará guardada
        title_lista = item.title_lista      # Se usa la lista de páginas anteriores en Item
    title_lista_alt = []                    # Creamos otra lista para esta pasada
    for url in title_lista:
        title_lista_alt += [url]            #hacemos una copia no vinculada de title_lista
    matches = []
    cnt_next = 0                            #num de página próxima
    cnt_top = 10                            #max. num de páginas web a leer antes de pintar
    total_pag = 1
    post_num = 1                            #num pagina actual
    inicio = time.time()                    # Controlaremos que el proceso no exceda de un tiempo razonable
    fin = inicio + 5                        # Después de este tiempo pintamos (segundos)
    timeout_search = timeout                # Timeout para descargas
    if item.action == 'search':
        timeout_search = int(timeout * 1.5) # Timeout un poco más largo para las búsquedas
        if timeout_search > 0 and timeout_search < 10:
            timeout_search = 10             # Timeout un poco más largo para las búsquedas
    
    #Máximo num. de líneas permitidas por TMDB (40). Máx de 5 páginas por Itemlist para no degradar el rendimiento.  
    #Si itemlist sigue vacío después de leer 5 páginas, se pueden llegar a leer hasta 10 páginas para encontrar algo

    while cnt_title <= cnt_tot and cnt_next < cnt_top and fin > time.time():
        # Descarga la página
        data = ''
        try:
            if not item.post:
                item.post = item.url
            video_section = ''
            data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.post, timeout=timeout_search).data)
            data = js2py_conversion(data, item.post, timeout=timeout_search)
            video_section = scrapertools.find_single_match(data, '<div class="contenedor-home">(?:\s*<div class="titulo-inicial">\s*Últi.*?Añadi...\s*<\/div>)?\s*<div class="contenedor-imagen">\s*(<div class="imagen-post">.*?<\/div><\/div>)<\/div>')
        except:
            pass
            
        cnt_next += 1
        if not data or 'Error 503 Backend fetch failed' in data:            #Si la web está caída salimos sin dar error
            logger.error("ERROR 01: LISTADO: La Web no responde o ha cambiado de URL: " + item.url + " / DATA: " + video_section)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: LISTADO:.  La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
            if len(itemlist) > 1:
                #Pasamos a TMDB la lista completa Itemlist
                tmdb.set_infoLabels(itemlist, __modo_grafico__)
                #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
                item, itemlist = generictools.post_tmdb_listado(item, itemlist)
            return itemlist                 #si no hay más datos, algo no funciona, pintamos lo que tenemos

        #Obtiene la dirección de la próxima página, si la hay
        try:
            patron = '<div class="nav-links">.*?<a class="next page.*?href="([^"]+)"'
            next_page = scrapertools.find_single_match(data, patron)                        #url próxima página        
            post = scrapertools.find_single_match(next_page, '\/page\/(\d+)\/')             #número próxima página
            if next_page:                                                                   #Hay próxima página?
                patron = '<div class="nav-links">.*?'
                patron += "href='.*?\/page\/\d+\/.*?'>(\d+)<\/a>\s?"
                patron += '<a class="next page-numbers"'
                total_pag = scrapertools.find_single_match(data, patron)                    #guarda el núm total de páginas
            
        except:
            post = False
            cnt_next = 99                           #No hay más páginas.  Salir del bucle después de procesar ésta

        if post:                                    #puntero a la siguiente página.  Cada página de la web tiene 30 entradas
            if "page/" in item.post:
                item.post = re.sub(r"page\/\d+\/", "page/%s/" % post, item.post)
            else:
                if "/categoria" in item.post:
                    item.post = re.sub(r"\/$", "/page/%s/" % post, item.post)
                elif "/series-2" in item.post:
                    item.post = re.sub(r"\/series-2\/", "/series-2/page/%s/" % post, item.post)
                elif "/series" in item.post:
                    item.post = re.sub(r"\/series\/", "/series/page/%s/" % post, item.post)
                else:
                    item.post = re.sub(r"\.net\/", ".net/page/%s/" % post, item.post)
                
            post_num = int(post) - 1      #Guardo página actual
        else:
            post = False
            cnt_next = 99       #No hay más páginas.  Salir del bucle después de procesar ésta

        # Preparamos un patron que pretende recoger todos los datos significativos del video
        patron = '<div class="imagen-post">\s*<a href="(?P<url>[^"]+)"><img.*?src="(?P<thumb>[^"]+)".*?'
        if "categoria" in item.url or item.media == "search":     #Patron distinto para páginas de Categorías o Búsquedas
            patron += 'class="attachment-(?P<quality>.*?)-(?P<lang>[^\s]+)\s.*?'
        else:
            patron += 'class="bloque-superior">\s*(?P<quality>.*?)\s*<div class="imagen-idioma">\s*<img src=".*?icono_(?P<lang>[^\.]+).*?'
        patron += '<div class="bloque-inferior">\s*(?P<title>.*?)\s*<\/div>\s*<div class="bloque-date">\s*(?P<date>.*?)\s*<\/div>\s*<\/div>'

        matches_alt = re.compile(patron, re.DOTALL).findall(video_section)
        if not matches_alt and not '<div class="titulo-load-core">0 resultados' in data:       #error
            item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
            if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
                item, itemlist = generictools.post_tmdb_listado(item, itemlist)     #Llamamos al método para el pintado del error
                return itemlist                                                     #Salimos
            
            if video_section: data = video_section
            logger.error("ERROR 02: LISTADO: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: LISTADO: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
            if len(itemlist) > 1:
                #Pasamos a TMDB la lista completa Itemlist
                tmdb.set_infoLabels(itemlist, __modo_grafico__)
                #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
                item, itemlist = generictools.post_tmdb_listado(item, itemlist)
            return itemlist                             #si no hay más datos, algo no funciona, pintamos lo que tenemos

        #Ahora se hace una simulación para saber cuantas líneas podemos albergar en este Itemlist.
        #Se controlará cuantas páginas web se tienen que leer para rellenar la lista, sin pasarse

        title_lista_alt_for = []         #usamos está lista de urls para el FOR, luego la integramos en la del WHILE
        for scrapedurl, scrapedthumb, quality, lang, scrapedtitle, date in matches_alt:
            #Realiza un control de las series que se añaden, ya que el buscador devuelve episodios y no las series completas
            #Se analiza si la url de la serie o pelicula ya se ha listado antes.  Si es así, esa entrada se ignora
            #Cuando llega al num. máximo de entradas por página, la pinta y guarda los contadores y la lista de series
            
            scrapedurl_alt = scrapedurl
            if modo_serie_temp == 1:        #si está en modo Serie agrupamos todos los episodios en una línea
                scrapedurl_alt = re.sub(r'-temporada.*?-\d+.*', '/', scrapedurl_alt)
                scrapedurl_alt = re.sub(r'-?\d+x\d+.*', '/', scrapedurl_alt)             #quita los datos de Temporada/episodio
            else:                           #si es modo Temporada, se agrupan a una línea por Temporada
                num_temp = scrapertools.find_single_match(scrapedurl_alt, '-?(\d+)x')    #captura num de Temporada
                scrapedurl_alt = re.sub(r'-?\d+x\d+.*', '-temporada-%s-completa' % num_temp, scrapedurl_alt) #epis. a Temporada

            if scrapedurl_alt in title_lista_alt or scrapedurl_alt in title_lista_alt_for:  # si ya se ha tratado, pasamos al siguiente item
                continue
            
            #Verificamos si el idioma está dentro del filtro, si no pasamos
            if not lookup_idiomas_paginacion(item, scrapedurl, scrapedtitle, lang, list_language):
                continue
            title_lista_alt_for += [scrapedurl_alt]
            cnt_title += 1                      # Sería una línea real más para Itemlist
            
            #Control de página
            if cnt_title > cnt_tot*0.65:        #si se acerca al máximo num. de lineas por pagina, tratamos lo que tenemos
                cnt_next = 99                   #Casi completo, no sobrepasar con la siguiente página
                if cnt_title > cnt_tot:
                    cnt_title = 99              #Sobrepasado el máximo.  Ignoro página actual
                    #Restauro puntero "next" a la página actual, para releearla en otra pasada, y salgo
                    item.post = re.sub(r"page\/\d+\/", "page/%s/" % post_num, item.post)
                    break

            if cnt_title > 0:        #Si se ha llegado a las 5 páginas tratadas, pintamos.  Si no continuamos un poco
                if cnt_next >= cnt_top*0.5:
                    cnt_next = 99

        if cnt_title <= cnt_tot:
            matches.extend(matches_alt)         #Acumulamos las entradas a tratar. Si nos hemos pasado ignoro última página
            title_lista_alt.extend(title_lista_alt_for)
    
        #logger.debug("BUCLE: " + item.post + " / post: " +  str(post) + " / post_num: " + str(post_num) + " / cnt_next: " + str(cnt_next) + " / " + str(title_lista_alt))
    
    #logger.debug("PATRON: " + patron)
    #logger.debug(matches)
    #logger.debug(video_section)     
    
    cnt_title = 0
    for scrapedurl, scrapedthumb, quality, lang, scrapedtitle, date in matches:
        
        #Realiza un control de las series que se añaden, ya que el buscador devuelve episodios y no las series completas
        #Se analiza si la url de la serie ya se ha listado antes.  Si es así, esa entrada se ignora
        #El control de página ya se ha realizado más arriba

        scrapedurl_alt = scrapedurl
        if modo_serie_temp == 1:                    #si está en modo Serie agrupamos todos los episodios en una línea
            scrapedurl_alt = re.sub(r'-temporada.*?-\d+.*', '/', scrapedurl_alt)
            scrapedurl_alt = re.sub(r'-?\d+x\d+.*', '/', scrapedurl_alt)             #quita los datos de Temporada/episodio
        else:                                       #si es modo Temporada, se agrupan a una línea por Temporada
            num_temp = scrapertools.find_single_match(scrapedurl_alt, '-?(\d+)x')    #captura num de Temporada
            scrapedurl_alt = re.sub(r'-?\d+x\d+.*', '-temporada-%s-completa' % num_temp, scrapedurl_alt) #epis. a Temporada

        if scrapedurl_alt in title_lista:           # si ya se ha tratado, pasamos al siguiente item
            continue                                # solo guardamos la url para series y docus
        title_lista += [scrapedurl_alt]
        #cnt_title += 1                              # Sería una línea real más para Itemlist

        item_local = item.clone()                   #Creamos copia de Item para trabajar y limpiamos campos innecesarios
        if item_local.media:                        #Viene de Búsquedas
            del item_local.media
        if item_local.title_lista:
            del item_local.title_lista
        item_local.post = True
        del item_local.post
        if item_local.category:
            del item_local.category
        item_local.context = "['buscar_trailer']"
        
        title = re.sub('\r\n', '', scrapedtitle).decode('utf8').encode('utf8').strip()      #Decode-encode utf8
        title = re.sub(r"\s{2}", " ", title)
        title = title.replace("&#8217;", "'").replace("\xc3\x97", "x")
        item_local.url = urlparse.urljoin(host, scrapedurl)

        if "categoria" in item.url:                 #En páginas de Categorias no viene ni la calidad ni el idioma
            if not item.extra2:
                item_local.quality = scrapertools.find_single_match(item.url, r'\/categoria\/(.*?)\/')
                if "4k" in item_local.quality.lower():
                    item_local.quality = "4K HDR"       #Maquillamos un poco la calidad
            else:
                item_local.quality = ''
            lang = ''                               #Ignoramos el idioma
        elif not "post" in quality:
            item_local.quality = quality            #Salvamos la calidad en el resto de páginas
        
        item_local.language = []                    #Verificamos el idioma por si encontramos algo
        if "latino" in lang.lower() or "latino" in item.url or "latino" in title.lower():
            item_local.language += ["LAT"]
        if "ingles" in lang.lower() or "ingles" in item.url or "vose" in scrapedurl or "vose" in item.url:
            if "VOSE" in lang.lower() or "sub" in title.lower() or "vose" in scrapedurl or "vose" in item.url:
                item_local.language += ["VOS"]
            else:
                item_local.language += ["VO"]
        if "dual" in lang.lower() or "dual" in title.lower():
            item_local.language[0:0] = ["DUAL"]
            
        if item_local.language == []:
            item_local.language = ['CAST']                  #Por defecto
                
        #Limpiamos el título de la basuna innecesaria
        title = title.replace("Dual", "").replace("dual", "").replace("Subtitulada", "").replace("subtitulada", "").replace("Subt", "").replace("subt", "").replace("Sub", "").replace("sub", "").replace("(Reparado)", "").replace("(Proper)", "").replace("(proper)", "").replace("Proper", "").replace("proper", "").replace("(Latino)", "").replace("Latino", "")
        title = title.replace("- HDRip", "").replace("(HDRip)", "").replace("- Hdrip", "").replace("(microHD)", "").replace("(DVDRip)", "").replace("(HDRip)", "").replace("(BR-LINE)", "").replace("(HDTS-SCREENER)", "").replace("(BDRip)", "").replace("(BR-Screener)", "").replace("(DVDScreener)", "").replace("TS-Screener", "").replace(" TS", "").replace(" Ts", "")
            
        if item_local.extra == "peliculas":                 #preparamos Item para películas
            if "/serie" in scrapedurl or "/serie" in item.url:
                continue
            item_local.contentType = "movie"
            item_local.action = "findvideos"
            title = scrapertools.htmlclean(title)           #Quitamos html restante
            item_local.contentTitle = title.strip()
        else:                                               #preparamos Item para series
            if not "/serie" in scrapedurl and not "/serie" in item.url:
                continue
            if modo_serie_temp == 1:                        #si está en modo Serie
                item_local.contentType = "tvshow"
                item_local.extra = "tvshow"
            else:                                           #si no, en modo temporada
                item_local.contentType = "season"
                item_local.extra = "season"
            item_local.action = "episodios"
            title = re.sub(r'[t|T]emp.*?\d+.*', '', title)  #Limpiamos temporadas completas, solo queremos la serie entera
            title = re.sub(r'\d?\d?&#.*', '', title)        #Limpiamos temporada y episodio
            title = re.sub(r'\d+[x|×]\d+.*', '', title)     #Limpiamos temporada y episodio
            title = scrapertools.htmlclean(title)           #Quitamos html restante
            item_local.contentSerieName = title.strip()

        item_local.title = title.strip()                    #Salvamos el título
        item_local.from_title = title.strip()               #Guardamos esta etiqueta para posible desambiguación de título
        item_local.infoLabels['year'] = "-"                 #Reseteamos el año para que TMDB nos lo de
        
        #Ahora se filtra por idioma, si procede, y se pinta lo que vale
        if config.get_setting('filter_languages', channel) > 0:     #Si hay idioma seleccionado, se filtra
            itemlist = filtertools.get_link(itemlist, item_local, list_language)
        else:
            itemlist.append(item_local.clone())                     #Si no, pintar pantalla
        
        cnt_title = len(itemlist)                                   #Contador de líneas añadidas

    #if not item.category and result_mode == 0:     #Si este campo no existe, viene de la primera pasada de una búsqueda global
    #    return itemlist                            #Retornamos sin pasar por la fase de maquillaje para ahorrar tiempo
    
    #Pasamos a TMDB la lista completa Itemlist
    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    
    #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
    item, itemlist = generictools.post_tmdb_listado(item, itemlist)

    #Gestionamos el paginador
    patron = '<div class="nav-links">.*?<a class="next page.*?href="([^"]+)"'
    next_page = scrapertools.find_single_match(data, patron)                        #url próxima página  
    #next_page_num = scrapertools.find_single_match(next_page, '\/page\/(\d+)\/')    #número próxima página
    if next_page:                                                                   #Hay próxima página?
        patron = '<div class="nav-links">.*?'
        patron += "href='.*?\/page\/\d+\/.*?'>(\d+)<\/a>\s?"
        patron += '<a class="next page-numbers"'
        last_page = scrapertools.find_single_match(data, patron)                    #cargamos la última página
        
        if last_page:                                                               #Sabemos la ultima página?
            title = '[COLOR gold]Página siguiente >>[/COLOR] %s de %s' % (post_num, last_page)
        else:
            title = '[COLOR gold]Página siguiente >>[/COLOR] %s' % post_num
        
        itemlist.append(item.clone(action="listado", title=title, url=next_page, thumbnail=get_thumb("next.png"), title_lista=title_lista, language=''))

    return itemlist

    
def findvideos(item):
    logger.info()
    itemlist = []
    itemlist_t = []                                     #Itemlist total de enlaces
    itemlist_f = []                                     #Itemlist de enlaces filtrados
    if not item.language:
        item.language = ['CAST']                        #Castellano por defecto

    #logger.debug(item)

    timeout_find = timeout
    follow_redirects=True
    if item.videolibray_emergency_urls:                 #Si se están cacheando enlaces aumentamos el timeout
        timeout_find = timeout * 2
    elif item.emergency_urls:                           #Si se llama desde la Videoteca con enlaces cacheados... 
        timeout_find = timeout / 2                      #reducimos el timeout antes de saltar a los enlaces cacheados
        #follow_redirects=False
    rar_search = True
        
    #Bajamos los datos de la página
    data = ''
    try:
        data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url, timeout=timeout_find, follow_redirects=follow_redirects).data)
        data = js2py_conversion(data, item.url, timeout=timeout_find, follow_redirects=follow_redirects)
    except:
        pass
        
    if not data:
        logger.error("ERROR 01: FINDVIDEOS: La Web no responde o la URL es erronea: " + item.url + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: FINDVIDEOS:.  La Web no responde o la URL es erronea. Si la Web está activa, reportar el error con el log', folder=False))
        if item.emergency_urls and not item.videolibray_emergency_urls:         #Hay urls de emergencia?
            matches = item.emergency_urls[1]                                    #Guardamos los matches de los .Torrent
            item.armagedon = True                                               #Marcamos la situación como catastrófica 
        else:
            if item.videolibray_emergency_urls:                                 #Si es llamado desde creación de Videoteca...
                return item                                                     #Devolvemos el Item de la llamada
            else:
                return itemlist                                                 #salimos
    
    data = unicode(data, "utf-8", errors="replace").encode("utf-8")
    data = scrapertools.find_single_match(data, 'div id="Tokyo" [^>]+>(.*?)</div>')     #Seleccionamos la zona de links
    
    patron = '\/icono_.*?png"\s*(?:title|alt)="(?P<lang>[^"]+)?"[^>]+><\/td><td>'
    patron += '(?P<temp_epi>.*?)?<?\/td>.*?<td>(?P<quality>.*?)?<\/td><td><a\s*'
    patron += 'class="link"\s*href="(?P<url>[^"]+)?"'
    if not item.armagedon:                                                      #Si es un proceso normal, seguimos
        matches = re.compile(patron, re.DOTALL).findall(data)
    if not matches:                                                             #error
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)  #Llamamos al método para el pintado del error
        else:
            logger.error("ERROR 02: FINDVIDEOS: El archivo Torrent no existe o ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: FINDVIDEOS: El archivo Torrent no existe o ha cambiado la estructura de la Web.  Verificar en la Web y reportar el error con el log', folder=False))
        if item.emergency_urls and not item.videolibray_emergency_urls:         #Hay urls de emergencia?
            matches = item.emergency_urls[1]                                    #Guardamos los matches de los .Torrent
            item.armagedon = True                                               #Marcamos la situación como catastrófica 
        else:
            if item.videolibray_emergency_urls:                                 #Si es llamado desde creación de Videoteca...
                return item                                                     #Devolvemos el Item de la llamada
            else:
                return itemlist                                                 #salimos
            
    #logger.debug("PATRON: " + patron)
    #logger.debug(matches)
    #logger.debug(data)

    #Llamamos al método para crear el título general del vídeo, con toda la información obtenida de TMDB
    item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)

    #Ahora recorremos todos los links por calidades
    if item.videolibray_emergency_urls:                                         #Viene de un lookup desde episodios para cachear enlaces
        emergency_torrents = []
        emergency_urls = []
    i = -1
    for lang, quality, size, scrapedurl in matches:
        i += 1
        temp_epi = ''
        if scrapertools.find_single_match(quality, '\([C|c]ontrase.*?<span\s*style="[^>]+>(.*?)<\/span>'):
            password = scrapertools.find_single_match(quality, '\([C|c]ontrase.*?<span\s*style="[^>]+>(.*?)<\/span>')
            quality = re.sub(r'\([C|c]ontrase.*?<span\s*style="[^>]+>(.*?)<\/span>', '', quality)
            quality += ' [Contraseña=%s]' % password
            if item.password:
                rar_search = False
        if scrapertools.find_single_match(size, '\([C|c]ontrase.*?<span\s*style="[^>]+>(.*?)<\/span>'):
            password = scrapertools.find_single_match(size, '\([C|c]ontrase.*?<span\s*style="[^>]+>(.*?)<\/span>')
            size = re.sub(r'\([C|c]ontrase.*?<span\s*style="[^>]+>(.*?)<\/span>', '', size)
            size += ' [Contraseña=%s]' % password
            if item.password:
                rar_search = False
        if item.contentType == "episode":       #En Series los campos están en otro orden.  No hay size, en su lugar sxe
            temp_epi = quality
            quality = size
            size = ''
            contentSeason = ''
            contentEpisodeNumber = ''
            try:                                #obtenemos la temporada y episodio de la página y la comparamos con Item
                if "temporada" in temp_epi.lower():
                    contentSeason = scrapertools.find_single_match(temp_epi, r'[t|T]emporada.*?(\d+)')
                    contentSeason = int(contentSeason)
                    contentEpisodeNumber = 1
                else:
                    if scrapertools.find_single_match(temp_epi, r'(\d+)&#.*?;(\d+)'):
                        contentSeason, contentEpisodeNumber = scrapertools.find_single_match(temp_epi, r'(\d+)&#.*?;(\d+)')
                    if not contentEpisodeNumber:
                        contentSeason = scrapertools.find_single_match(item.url, r'temporadas?-(\d+)')  #num de temporada
                        if not contentEpisodeNumber:
                            contentSeason = 1
                        contentEpisodeNumber = scrapertools.find_single_match(temp_epi, r'(\d+)-')
                        if not contentEpisodeNumber:
                            contentEpisodeNumber = 1
                    contentSeason = int(contentSeason)
                    contentEpisodeNumber = int(contentEpisodeNumber)
            except:
                logger.error("ERROR 03: FINDVIDEOS: Error en número de Episodio: " + temp_epi + " / " + str(contentSeason) + " / " + str(contentEpisodeNumber))
                continue                        
            if (contentSeason != item.contentSeason or contentEpisodeNumber != item.contentEpisodeNumber) and item.contentEpisodeNumber != 0:
                continue                        #si no son iguales, lo ignoramos

        #Si es un lookup desde episodios para cachear enlaces, lo salvamos en este momento
        if item.videolibray_emergency_urls:
            emergency_torrents.append(scrapedurl)
            emergency_urls.append(matches[i])
            continue
        
        #Generamos una copia de Item para trabajar sobre ella
        item_local = item.clone()
        
        #Verificamos el idioma por si encontramos algo
        if not item_local.language:
            if "latino" in lang.lower() or "latino" in scrapedurl:
                item_local.language += ["LAT"]
            if "ingles" in lang.lower() or "ingles" in scrapedurl or "vose" in scrapedurl or "vose" in scrapedurl:
                if "VOSE" in lang.lower() or "sub" in lang.lower() or "vose" in scrapedurl or "vose" in scrapedurl:
                    item_local.language += ["VOS"]
                else:
                    item_local.language += ["VO"]
            if "dual" in lang.lower() or "dual" in scrapedurl:
                item_local.language[0:0] = ["DUAL"]

        #Tratamos la calidad y tamaño de cada link
        item_local.torrent_info = ''
        if quality:
            item_local.quality = quality
        else:
            item_local.quality = item.quality
        if "temporada" in temp_epi.lower():
            item_local.torrent_info = '[Temporada], '
        #Añadimos la duración, que estará en item.quility
        if scrapertools.find_single_match(item.quality, '(\[\d+:\d+)') and not scrapertools.find_single_match(item_local.quality, '(\[\d+:\d+)'):
            item_local.quality = '%s [/COLOR][COLOR white][%s h]' % (item_local.quality, scrapertools.find_single_match(item.quality, '(\d+:\d+)'))
        
        # Comprobamos si es necesario renovar la cookie del domino de Torrents
        if config.get_setting("cookie_ren", channel=channel, default=True):
            data_tor = ''
            try:
                data_tor = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(scrapedurl, timeout=timeout).data)
                data_tor = js2py_conversion(data_tor, scrapedurl, domain_name=domain_files, timeout=timeout)
                config.set_setting("cookie_ren", False, channel=channel)            #Cookie renovada
            except:
                logger.error(traceback.format_exc())
        
        #if size and item_local.contentType != "episode":
        if not item.armagedon:
            size = generictools.get_torrent_size(scrapedurl)                        #Buscamos el tamaño en el .torrent y si es RAR
        if size:
            size = size.replace('GB', 'G·B').replace('Gb', 'G·b').replace('MB', 'M·B')\
                        .replace('Mb', 'M·b').replace('.', ',')
            item_local.torrent_info += '%s' % size                                       #Agregamos size
            if not item.unify:
                item_local.torrent_info = '[%s]' % item_local.torrent_info.strip().strip(',')
                
        # Si tiene un archivo RAR, busca la contraseña
        if ('RAR-' in item.torrent_info or 'RAR-' in item_local.torrent_info) and rar_search:
            rar_search = False
            if 'Contrase' in quality or 'Contrase' in size or 'Contrase' in temp_epi:
                item.password = scrapertools.find_single_match(quality, '\[Contrase.*?=(.*?)\]')
                if not item.password:
                    item.password = scrapertools.find_single_match(size, '\[Contrase.*?=(.*?)\]')
                    if not item.password:
                        item.password = scrapertools.find_single_match(temp_epi, '\[Contrase.*?=(.*?)\]')
                if item.password:
                    item_local.password = item.password
            if not item.password:
                item_local = generictools.find_rar_password(item_local)
            if item_local.password:
                item.password = item_local.password
                itemlist.append(item.clone(action="", title="[COLOR magenta][B] Contraseña: [/B][/COLOR]'" 
                        + item.password + "'", folder=False))

        if item_local.action == 'show_result':                                          #Viene de una búsqueda global
            channel_alt = item_local.channel.capitalize()
            if item_local.from_channel:
                channel_alt = item_local.from_channel.capitalize()
            item_local.quality = '[COLOR yellow][%s][/COLOR] %s' % (channel_alt, item_local.quality)

        #Salvamos la url del .torrent
        if scrapedurl:
            item_local.url = scrapedurl
            if item_local.emergency_urls and not item.armagedon:
                item_local = find_torrent_alt(item_local)                       #Si hay enlaces de emergencia los usamos como alternativos
            if item.armagedon:                                                  #Si es catastrófico, lo marcamos
                item_local.url = item.emergency_urls[0][i]
                item_local.quality = '[/COLOR][COLOR hotpink][E] [COLOR limegreen]%s' % item_local.quality
            item_local.title = '[COLOR yellow][?][/COLOR] [COLOR yellow][Torrent][/COLOR] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (item_local.quality, str(item_local.language))     #Preparamos título de Torrent
            item_local.title = '[[COLOR yellow]?[/COLOR]] [COLOR yellow][Torrent][/COLOR] ' \
                        + '[COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR] %s' % \
                        (item_local.quality, str(item_local.language),  \
                        item_local.torrent_info)                                #Preparamos título de Torrent

            #Preparamos título y calidad, quitamos etiquetas vacías
            item_local.title = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', item_local.title)    
            item_local.title = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', item_local.title)
            item_local.title = item_local.title.replace("--", "").replace("[]", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()
            item_local.quality = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', item_local.quality)
            item_local.quality = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', item_local.quality)
            item_local.quality = item_local.quality.replace("--", "").replace("[]", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()
            
            item_local.alive = "??"                                             #Calidad del link sin verificar
            item_local.action = "play"                                          #Visualizar vídeo
            item_local.server = "torrent"                                       #Seridor Torrent
        
            itemlist_t.append(item_local.clone())                               #Pintar pantalla, si no se filtran idiomas
        
            # Requerido para FilterTools
            if config.get_setting('filter_languages', channel) > 0:             #Si hay idioma seleccionado, se filtra
                itemlist_f = filtertools.get_link(itemlist_f, item_local, list_language)    #Pintar pantalla, si no está vacío
            
        #logger.debug("TORRENT: " + item_local.url + " / title gen/torr: " + item.title + " / " + item_local.title + " / calidad: " + item_local.quality)
        #logger.debug(item_local)

    if item.videolibray_emergency_urls:                                         #Viene de un lookup desde episodios para cachear enlaces
        if len(emergency_torrents) > 0:
            item.emergency_urls = []                                            #Le damos el formato estandar: lista de listas de tuplas
            item.emergency_urls.append(emergency_torrents)                      #Devolvemos las urls de .torrents cacheadas
            item.emergency_urls.append(emergency_urls)                          #Devolvemos los matches cacheados
        return item
    
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
    temp_actual_num = 0
    temp_actual = ''
    temp_previous = ''
    temp_next = ''
    item.extra = "episodios"
    
    #logger.debug(item)
    
    # Obtener la información actualizada de la Serie.  TMDB es imprescindible para Videoteca
    #if not item.infoLabels['tmdb_id']:
    try:
        tmdb.set_infoLabels(item, True)                                                 #TMDB de cada Temp
    except:
        pass

    data = ''
    try:
        data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url, timeout=timeout).data)    #Cargamos los datos de la página
        data = js2py_conversion(data, item.url, timeout=timeout)

        patron_actual = '<link rel="canonical" href="(.*?)"'                            #Patrón de url temporada actual
        patron_actual_num = 'temporadas?-(\d+)'                                         #Patrón de núm. de temporada actual
        patron_previous = '<a class="temp-anterior" href="(.*?)">'                      #Patrón de url temporada anterior
        patron_next = '<a class="temp-siguiente" href="(.*?)">'                         #Patrón de url temporada próxima
        temp_actual = scrapertools.find_single_match(data, patron_actual)               #url actual de la temporada
        item.url = temp_actual                              #Salvamos la temporada actual como primera para la Videoteca
        temp_next = scrapertools.find_single_match(data, patron_next)                   #url de temporada siguiente
        temp_previous = scrapertools.find_single_match(data, patron_previous)           #url de temporada anterior
        temp_advance = 'back'                                           #por defecto procesamos temporadas hacia atrás
        temp_actual_num = scrapertools.find_single_match(temp_actual, patron_actual_num)    #num de la temporada actual
        if not temp_actual_num:                                                         #Si el formato es extraño...
            temp_actual_num = 1                                                         #... ponemos 1 como valor
        temp_actual_num = int(temp_actual_num)
        contentSeason = temp_actual_num                                                 #Salvamos el núm de temporada actual
        temp_previous_num = scrapertools.find_single_match(temp_previous, patron_actual_num)    #num de la temporada previa
        temp_previous_num = int(temp_actual_num)
    except:                                                                             #Algún error de proceso, salimos
        logger.error("ERROR 01: EPISODIOS: La Web no responde o la URL es erronea: " + temp_actual + " (" + str (temp_actual_num) + ") / Previa: " + temp_previous + " / o Siguiente: " + temp_next + " / Avance: " + temp_advance + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: EPISODIOS:.  La Web no responde o la URL es erronea. Si la Web está activa, reportar el error con el log'))
        return itemlist

    max_temp = 1
    if item.library_playcounts:         #Averiguar cuantas temporadas hay en Videoteca
        patron = 'season (\d+)'
        matches = re.compile(patron, re.DOTALL).findall(str(item.library_playcounts))
        max_temp = int(max(matches))
    
    if not item.library_playcounts:     #no viene de Videoteca, se ponen valores de configuración o de la pasada anterior
        if not item.contentType:
            if modo_serie_temp == 0:
                item.contentType = "season"
            else:
                item.contentType = "tvshow"
                if item.contentSeason:
                    del item.infoLabels['season']

    elif max_temp < item.infoLabels["number_of_seasons"]:       #Si tenemos en .nfo menos temporadas, Temp.
        item.contentType = "season"

    elif max_temp >= item.infoLabels["number_of_seasons"]:      #Si tenemos en .nfo igaual o más temporadas, investigar
        cnt_s = 0
        for s in item.library_playcounts:                       #Ver cuántas Temporadas hay en Videoteca
            if "season" in s:
                cnt_s += 1

        if cnt_s > 1:                                           #hay más de 1 temporada en Videoteca, es Serie?
            if temp_actual_num > 1:                             #Temp. actual > 1, parece Temporada
                s = 1
                while s <= item.infoLabels["number_of_seasons"]:                #Buscamos la primera Temporada de Videoteca
                    if item.library_playcounts.has_key('season %d' % s):        #Buscamos si la Temporada 1 existe
                        if item.library_playcounts["season %d" % s] < temp_actual_num:    #Si menor que actual, es Temp.
                            item.contentType = "season"
                        else:
                            item.contentType = "tvshow"         #No es Temporada 1, pero es más baja que la actual.  Es Serie
                        break
                    s += 1
            else:                                               #Sí, es Serie
                item.contentType = "tvshow"

        else:                                                   #Solo hay una temporada en la Videoteca
            if temp_actual_num > 1:                             #es Temporada la actual?
                if item.contentSeason:
                    item.contentType = "season"                 #Si está informado el num de Temp. se creó como Temporada
                else:
                    item.contentType = "tvshow"                 #Si no, es Serie que no tiene Temp. 1
            else:                                               #Si es Temp. 1, se procesa según el valor de configuración    
                if modo_serie_temp == 0:                        #Es Temporada
                    item.contentType = "season"
                else:                                           #Es Serie
                    item.contentType = "tvshow"
    else:
        item.contentType = "list"

    if item.ow_force == '1':                                    #Si viene formazado la reconstrucción de la serie, lo hacemo
        item.contentType = "tvshow"
    if not modo_ultima_temp:                                    #Si se quiere actualiar toda la serie en vez de la última temporada...
        item.contentType = "tvshow"
    
    temp_lista = []
    temp_bucle = 0
    temp_next_alt = ''
    while temp_actual != '':                            #revisamos las temporadas hasta el final
        if not data:                                    #si no hay datos, descargamos. Si los hay de loop anterior, los usamos
            try:
                data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(temp_actual, timeout=timeout).data)
                data = js2py_conversion(data, temp_actual, timeout=timeout)
                
                #Controla que no haya un bucle en la cadena de links entre temporadas
                if scrapertools.find_single_match(temp_actual, patron_actual_num) in temp_lista:
                    temp_bucle += 1
                    if temp_bucle > 5:                  #Si ha pasado por aquí más de 5 veces es que algo anda mal
                        logger.error("ERROR 05: EPISODIOS: Los links entre temporadas están rotos y se está metiendo en un loop: " + temp_actual + " (" + str (temp_actual_num) + ") / Previa: " + temp_previous + " / o Siguiente: " + temp_next + " / Avance: " + temp_advance + " / Lista temps: " + str(temp_lista) + " / DATA: " + data)
                        itemlist.append(item.clone(action='', title=item.channel + ': ERROR 05: EPISODIOS.  Los links entre temporadas están rotos y se está metiendo en un loop.  Reportar error con log'))
                        data = ''
                        break                   #Algo no funciona con los links, pintamos lo que tenemos
                    if temp_advance == "back":     #Se salta una temporada hacia atrás
                        logger.error("ERROR 05: EPISODIOS: Temporada duplicada.  Link BACK erroneo: " + temp_actual + " (" + str (temp_actual_num) + ") / Previa: " + temp_previous + " / o Siguiente: " + temp_next + " / Avance: " + temp_advance + " / Lista temps: " + str(temp_lista) + " / Bucle: " + str(temp_bucle) + " / DATA: " + data)
                        temp_actual = scrapertools.find_single_match(data, patron_previous) #url de temporada anterior
                        data = ''
                        continue                #volvemos a leer página con la url de la anterior
                    if temp_advance == "forw":     #Se salta una temporada hacia adelante
                        logger.error("ERROR 05: EPISODIOS: Temporada duplicada.  Link FORW erroneo: " + temp_actual + " (" + str (temp_actual_num) + ") / Previa: " + temp_previous + " / o Siguiente: " + temp_next + " / Avance: " + temp_advance + " / Lista temps: " + str(temp_lista) + " / Bucle: " + str(temp_bucle) + " / DATA: " + data)
                        temp_actual = scrapertools.find_single_match(data, patron_next)     #url de temporada siguiente
                        data = ''
                        continue                #volvemos a leer página con la url de la siguiente
                
                #Comprobamos si se ha saltado una Temporada
                if temp_advance == "back":                          #Avanza marcha atrás?
                    temp_num_alt = int(scrapertools.find_single_match(temp_actual, patron_actual_num))  #nuevo num. Temp.
                    if temp_num_alt < temp_actual_num - 1:          #Hay un salto a la Temp. anterior, o más?
                        temp_next_alt = scrapertools.find_single_match(data, patron_next)   #url de temporada siguiente
                        temp_num_alt = int(scrapertools.find_single_match(temp_next_alt, patron_actual_num))
                        #Localizamos la Temp. siguiente y nos aseguramos que no está procesada
                        if temp_num_alt <= temp_actual_num - 1 and temp_num_alt not in temp_lista:
                            temp_actual_alt = temp_next_alt         #url actual de la temporada = url de la siguiente
                            temp_previous_alt = temp_actual         #url temporada anterior = url de la actual anterior
                            logger.error("ERROR 06: EPISODIOS: Se ha saltado una Temporda: Actual: " + temp_actual + " / Actual ALT: " + temp_actual_alt + " / Previa: " + temp_previous  + " / o Siguiente: " + temp_next + " / Avance: " + temp_advance + " / Bucle: " + str(temp_bucle))
                            temp_actual = temp_actual_alt           #url actual de la temporada = url de la siguiente
                            temp_bucle += 1
                            if temp_bucle > 5:                      #Evitamos loops infinitos
                                logger.error("ERROR 05: EPISODIOS: Los links entre temporadas están rotos y se está metiendo en un loop: " + temp_actual + " (" + str (temp_actual_num) + ") / Previa: " + temp_previous + " / o Siguiente: " + temp_next + " / Avance: " + temp_advance + " / Lista temps: " + str(temp_lista) + " / DATA: " + data)
                                data = ''
                                itemlist.append(item.clone(action='', title=item.channel + ': ERROR 05: EPISODIOS.  Los links entre temporadas están rotos y se está metiendo en un loop.  Reportar error con log'))
                                break                           #Algo no funciona con los links, pintamos lo que tenemos
                            data = ''
                            continue                            #volvemos a leer página con la url de la siguiente
                
                #Comprobamos si se ha saltado una Temporada
                if temp_advance == "forw":                          #Avanza marcha adelante?
                    temp_num_alt = int(scrapertools.find_single_match(temp_actual, patron_actual_num))  #nuevo num. Temp.
                    if temp_num_alt > temp_actual_num + 1:          #Hay un salto a la Temp. siguiente, o más?
                        temp_previous_alt = scrapertools.find_single_match(data, patron_previous)   #url de temporada anterior
                        temp_num_alt = int(scrapertools.find_single_match(temp_previous_alt, patron_actual_num))
                        #Localizamos la Temp. anterior y nos aseguramos que no está procesada
                        if temp_num_alt >= temp_actual_num + 1 and temp_num_alt not in temp_lista:
                            temp_actual_alt = temp_previous_alt     #url actual de la temporada = url de la anterior
                            temp_next_alt = temp_actual             #url temporada siguiente = url de la actual anterior
                            logger.error("ERROR 06: EPISODIOS: Se ha saltado una Temporda: Actual: " + temp_actual + " / Actual ALT: " + temp_actual_alt + " / Previa: " + temp_previous  + " / o Siguiente: " + temp_next + " / Avance: " + temp_advance + " / Bucle: " + str(temp_bucle))
                            temp_actual = temp_actual_alt           #url actual de la temporada = url de la siguiente
                            temp_bucle += 1
                            if temp_bucle > 5:                      #Evitamos loops infinitos
                                logger.error("ERROR 05: EPISODIOS: Los links entre temporadas están rotos y se está metiendo en un loop: " + temp_actual + " (" + str (temp_actual_num) + ") / Previa: " + temp_previous + " / o Siguiente: " + temp_next + " / Avance: " + temp_advance + " / Lista temps: " + str(temp_lista) + " / DATA: " + data)
                                data = ''
                                itemlist.append(item.clone(action='', title=item.channel + ': ERROR 05: EPISODIOS.  Los links entre temporadas están rotos y se está metiendo en un loop.  Reportar error con log'))
                                break                               #Algo no funciona con los links, pintamos lo que tenemos
                            data = ''
                            continue                                #volvemos a leer página con la url de la siguiente

                temp_actual_num = scrapertools.find_single_match(temp_actual, patron_actual_num)    #num de la temporada actual
                temp_actual_num = int(temp_actual_num)
                temp_previous = scrapertools.find_single_match(data, patron_previous)           #url de temporada anterior
                if temp_advance == 'forw':  #si estamos con temporadas previas, dejamos la url de la siguiente temporada inicial
                    temp_next = scrapertools.find_single_match(data, patron_next)               #url de temporada siguiente
                    temp_previous = ''                  #ya están procesadas las temporadas previas, no volvemos a hacerlo
            
            except:                                     #Error al leer o procesar la página actual? Salimos
                logger.error("ERROR 01: EPISODIOS:.  La Web no responde o la URL es erronea: " + temp_actual + " (" + str (temp_actual_num) + ") / Previa: " + temp_previous + " / o Siguiente: " + temp_next + " / Avance: " + temp_advance + " / DATA: " + data)
                itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: EPISODIOS:.  La Web no responde o la URL es erronea. Si la Web está activa, reportar el error con el log'))
                break                                   #si no hay más datos, algo no funciona, pintamos lo que tenemos
        
        if item.contentType == "season":
            temp_advance = ''                           #Es la últica temporada
            if temp_next and item.library_playcounts:   #Permitimos en actualización de Videoteca añadir nuevas temporadas
                temp_advance = 'forw'                   #Si hay nueva temporada, pasamos a esa como actual
            temp_previous = ''                          #lo limpiamos, por control
            item.url = temp_actual                      #Salvamos la temporada actual como primera para la Videoteca
            contentSeason = temp_actual_num             #Salvamos el núm de temporada
        elif temp_previous:                             #Para Series, vamos retrocediendo y procesando temporadas
            if temp_advance == 'back':
                if not modo_ultima_temp:                #Actualiza la Serie entera en la Videoteca?
                    item.url = temp_previous            #Salvamos la temporada previa como primera para la Videoteca
                contentSeason = temp_previous_num       #Salvamos en núm de temporada
            temp_advance = 'back'                       #hay temporadas anteriores, iremos marcha atrás procesándolas
        elif temp_next:
            if temp_advance == 'back':                  #Esta es la primera temporada disponible
                if not modo_ultima_temp:                #Actualiza la Serie entera en la Videoteca?
                    item.url = temp_actual              #Salvamos la temporada actual como primera para la Videoteca
                contentSeason = temp_actual_num         #Salvamos en núm de temporada
            else:
                if modo_ultima_temp and not item.library_playcounts:        #Actualiza la última Temporada en la Videoteca?
                    item.url = temp_next                #Salvamos la temporada siguiente como primera para la Videoteca
            temp_advance = 'forw'                       #No hay temporadas anteriores, pero sí posteriores.  Las procesamos
        else:
            temp_advance = ''                           #lo limpiamos, por control
        
        data = unicode(data, "utf-8", errors="replace").encode("utf-8")
        data = scrapertools.find_single_match(data, 'div id="Tokyo" [^>]+>(.*?)</div>')     #Seleccionamos la zona de links
        
        patron = '\/icono_.*?png"\s*(?:title|alt)="(?P<lang>[^"]+)?"[^>]+><\/td><td>'
        patron += '(?P<temp_epi>.*?)?<?\/td>.*?<td>(?P<quality>.*?)?<\/td><td><a\s*'
        patron += 'class="link"\s*href="(?P<url>[^"]+)?"'
        matches = re.compile(patron, re.DOTALL).findall(data)
        if not matches:                             #error
            item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
            if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
                item, itemlist = generictools.post_tmdb_episodios(item, itemlist)   #Llamamos al método para el pintado del error
                return itemlist                                                     #Salimos
            
            logger.error("ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
            break                                       #si no hay más datos, algo no funciona, pintamos lo que tenemos
        
        #logger.debug("PATRON: " + patron)
        #logger.debug(matches)
        #logger.debug(data)
        
        #Ahora recorremos todos los links por calidades
        for lang, temp_epi, quality, scrapedurl in matches:     #la URL apunta ya al .torrent. nos quedamos con la URL de temporada
            #Generamos una copia de Item para trabajar sobre ella y la rellenamos.  Borramos etiquetas innecesarias
            item_local = item.clone()
            if item_local.category:
                del item_local.category
            if item_local.infoLabels['title']:
                del item_local.infoLabels['title']
            item_local.context = "['buscar_trailer']"
            item_local.url = temp_actual                        #salvamos la URL de la temporada
            item_local.action = "findvideos"
            item_local.contentType = "episode"
            #item_local.contentSeason = temp_actual_num          #salvamos num de temporada
            item_local.title = re.sub(r'\[COLOR limegreen\]\[.*?\]\[\/COLOR\]', '', item_local.title)
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

            #Verificamos el idioma por si encontramos algo
            if not item_local.language:
                if "latino" in lang.lower() or "latino" in scrapedurl:
                    item_local.language += ["LAT"]
                if "ingles" in lang.lower() or "ingles" in scrapedurl or "vose" in scrapedurl or "vose" in scrapedurl:
                    if "VOSE" in lang.lower() or "sub" in lang.lower() or "vose" in scrapedurl or "vose" in scrapedurl:
                        item_local.language += ["VOS"]
                    else:
                        item_local.language += ["VO"]
                if "dual" in lang.lower() or "dual" in scrapedurl:
                    item_local.language[0:0] = ["DUAL"]
            
            try:
                if "temporada" in temp_epi.lower() or "completa" in temp_epi.lower():     #si es una temporada en vez de un episodio, lo aceptamos como episodio 1
                    item_local.contentSeason = scrapertools.find_single_match(temp_epi, r'[t|T]emporada.*?(\d+)')
                    if not item_local.contentSeason:
                        item_local.contentSeason = temp_actual_num
                    item_local.contentSeason = int(item_local.contentSeason)
                    item_local.contentEpisodeNumber = 1
                else:                                           #si es un episodio lo guardamos
                    if scrapertools.find_single_match(temp_epi, r'(\d+)&#.*?;(\d+)'):
                        item_local.contentSeason, item_local.contentEpisodeNumber = scrapertools.find_single_match(temp_epi, r'(\d+)&#.*?;(\d+)')
                    if not item_local.contentSeason:
                        item_local.contentSeason = temp_actual_num
                    item_local.contentSeason = int(item_local.contentSeason)
                    #item_local.contentEpisodeNumber = scrapertools.find_single_match(temp_epi, r'\d+&#.*?;(\d+)')
                    if not item_local.contentEpisodeNumber:
                        item_local.contentEpisodeNumber = scrapertools.find_single_match(temp_epi, r'(\d+)-')
                        if not item_local.contentEpisodeNumber:
                            item_local.contentEpisodeNumber = 0
                    item_local.contentEpisodeNumber = int(item_local.contentEpisodeNumber)
            except:
                logger.error("ERROR 07: EPISODIOS: Error en número de Temporada o Episodio: " + temp_epi)
                continue                                        #si da un error pasamos del episodio
                
            if item_local.contentSeason != temp_actual_num:     #A veces es diferente el num de Temp. de la URL y de
                temp_actual_num = item_local.contentSeason      #los episodios. Anatomia de Grey Temp. 14

            if "-" in temp_epi:                                 #episodios múltiples
                episode2 = scrapertools.find_single_match(temp_epi, r'-(\d+)')
                item_local.title = "%sx%s al %s -" % (item_local.contentSeason, str(item_local.contentEpisodeNumber).zfill(2), str(episode2).zfill(2))                        #Creamos un título con el rango de episodios
            elif "temporada" in temp_epi.lower() or "completa" in temp_epi.lower():       #Temporada completa
                episode2 = 99
                item_local.title = "%sx%s al %s -" % (item_local.contentSeason, str(item_local.contentEpisodeNumber).zfill(2), str(episode2).zfill(2))                        #Creamos un título con el rango ficticio de episodios
            elif item_local.contentEpisodeNumber == 0:          #episodio extraño
                item_local.title = '%sx%s - %s' % (item_local.contentSeason, str(item_local.contentEpisodeNumber).zfill(2), temp_epi)
            else:                                               #episodio normal
                item_local.title = '%sx%s -' % (item_local.contentSeason, str(item_local.contentEpisodeNumber).zfill(2))
            
            if len(itemlist) > 0 and item_local.contentSeason == itemlist[-1].contentSeason and item_local.contentEpisodeNumber == itemlist[-1].contentEpisodeNumber and item_local.title == itemlist[-1].title and itemlist[-1].contentEpisodeNumber != 0:                     #solo guardamos un episodio ...
                if itemlist[-1].quality:
                    itemlist[-1].quality += ", " + quality      #... pero acumulamos las calidades
                else:
                    itemlist[-1].quality = quality
                continue                                        #ignoramos el episodio duplicado
            else:
                item_local.quality = quality

            itemlist.append(item_local.clone())                 #guardamos el episodio

            #logger.debug("EPISODIOS: " + temp_actual + " (" + str (item_local.contentSeason) + "x" + str (item_local.contentEpisodeNumber) + ") / Previa: " + temp_previous + " / o Siguiente: " + temp_next + " / Avance: " + temp_advance + " / Lista Temps: " + str(temp_lista))
            #logger.debug(item_local)
        
        temp_lista += [temp_actual_num]
        if temp_advance == 'back':
            temp_actual = temp_previous                     #hay temporadas anteriores, iremos marcha atrás procesándolas
        elif temp_advance == 'forw':
            temp_actual = temp_next                         #hay temporadas posteriores.  Las procesamos
        else:
            temp_actual = ''                                #No hay más temporadas, salimos

        data = ''                                           #Limpiamos data para forzar la lectura en la próxima pasada
        
    item.contentSeason_save = contentSeason                 #Guardamos temporalemente este contador
    
    if len(itemlist) > 1:
        itemlist = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))     #clasificamos

    # Pasada por TMDB y clasificación de lista por temporada y episodio
    tmdb.set_infoLabels(itemlist, True)

    #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
    item, itemlist = generictools.post_tmdb_episodios(item, itemlist)
        
    return itemlist
    
    
def find_torrent_alt(item):
    logger.info()
    
    if not item.emergency_urls:
        return item
        
    i = 0    
    for lang, quality, size, scrapedurl in item.emergency_urls[1]:      #buscamos la url actual en la lista de matches cacheada
        if item.url == scrapedurl:                                      #si está ...
            item.torrent_alt = item.emergency_urls[0][i]                #... copiamos la url o la dirección de .torrent local
            break                                                       #... y nos vamos
        i += 1
    
    return item
    
    
def lookup_idiomas_paginacion(item, scrapedurl, title, lang, list_language):
    logger.info()
    estado = True
    item.language = []
    itemlist = []
    
    if "latino" in lang.lower() or "latino" in item.url or "latino" in title.lower():
        item_local.language += ["LAT"]
    if "ingles" in lang.lower() or "ingles" in item.url or "vose" in scrapedurl or "vose" in item.url:
        if "VOSE" in lang.lower() or "sub" in title.lower() or "vose" in scrapedurl or "vose" in item.url:
            item_local.language += ["VOS"]
        else:
            item_local.language += ["VO"]

    if item.language == []:
        item.language = ['CAST']                                #Por defecto
    
    #Ahora se filtra por idioma, si procede, y se pinta lo que vale.  Excluye categorías en otros idiomas.
    if config.get_setting('filter_languages', channel) > 0 and item.extra2 != 'categorias':
        itemlist = filtertools.get_link(itemlist, item, list_language)
        
        if len(itemlist) == 0:
            estado = False
    
    #Volvemos a la siguiente acción en el canal
    return estado


def actualizar_titulos(item):
    logger.info()
    
    item = generictools.update_title(item)  #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels
    
    #Volvemos a la siguiente acción en el canal
    return item
    
    
def js2py_conversion(data, url, post=None, domain_name=domain, headers={}, timeout=timeout, follow_redirects=True):
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
    new_cookie = context.eval(js2py_code)
    
    logger.info('new_cookie: ' + new_cookie)

    dict_cookie = {'domain': domain_name,
                }

    if ';' in new_cookie:
        new_cookie = new_cookie.split(';')[0].strip()
        namec, valuec = new_cookie.split('=')
        dict_cookie['name'] = namec.strip()
        dict_cookie['value'] = valuec.strip()
    zanga = httptools.set_cookies(dict_cookie)
    config.set_setting("cookie_ren", True, channel=channel)

    data_new = ''
    data_new = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(url, \
                timeout=timeout, headers=headers, post=post, follow_redirects=follow_redirects).data)
    #data_new = re.sub('\r\n', '', data_new).decode('utf8').encode('utf8')
    if data_new:
        data = data_new
    
    return data
    
    
def atob(s):
    import base64
    return base64.b64decode(s.to_string().value)
    

def search(item, texto):
    logger.info("texto:" + texto)
    texto = texto.replace(" ", "+")
    itemlist = []
    
    item.url = "%s?s=%s" % (item.url, texto)
    item.media = "search"                           #Marcar para "Listado": igual comportamiento que "Categorías"

    try:
        if "series/" in item.url:
            item.extra = "series"
            item.title = "Series"
        else:
            item.extra = "peliculas"
            item.title = "Películas"

        itemlist = listado(item)

        return itemlist

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("ERROR: %s: SEARCH" % line)
        return []

        
def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    
    try:
        if categoria == '4k':
            item.url = host + "categoria/4k/"
            item.extra = "peliculas"
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