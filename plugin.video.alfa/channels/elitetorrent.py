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

host = 'http://www.elitetorrent.io'
channel = "elitetorrent"

categoria = channel.capitalize()
__modo_grafico__ = config.get_setting('modo_grafico', channel)
timeout = config.get_setting('timeout_downloadpage', channel)


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
    
    itemlist.append(Item(channel=item.channel, action="submenu", title="Series", url=host, extra="series", thumbnail=thumb_series))
    
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar", url=host, thumbnail=thumb_buscar, filter_lang=True))

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
    
    data = ''
    try:
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)
    except:
        pass
        
    if not data:
        logger.error("ERROR 01: SUBMENU: La Web no responde o ha cambiado de URL: " + item.url)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
        return itemlist                                                         #Algo no funciona, pintamos lo que tenemos
    
    patron = '<div class="cab_menu"\s*>.*?<\/div>'                                 #Menú principal
    data1 = scrapertools.find_single_match(data, patron)
    patron = '<div id="menu_langen"\s*>.*?<\/div>'                                 #Menú de idiomas
    data1 += scrapertools.find_single_match(data, patron)
    
    patron = '<a href="(.*?)".*?title="(.*?)"'                                  #Encontrar todos los apartados
    matches = re.compile(patron, re.DOTALL).findall(data1)
    if not matches:
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            for clone_inter, autoridad in item.intervencion:
                thumb_intervenido = get_thumb(autoridad)
                itemlist.append(item.clone(action='', title="[COLOR yellow]" + clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial + '. Reportar el problema en el foro', thumbnail=thumb_intervenido))
            return itemlist                                                     #Salimos
        
        logger.error("ERROR 02: SUBMENU: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data1)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: SUBMENU: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
        return itemlist                                     #si no hay más datos, algo no funciona, pintamos lo que tenemos
    
    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = re.sub('\r\n', '', scrapedtitle).decode('utf8').strip()
        scrapedtitle = scrapedtitle.replace(" torrent", "").replace(" Torrent", "").replace("Series y ", "").title()
        
        if "castellano" in scrapedtitle.lower():            #Evita la entrada de peliculas castellano del menú de idiomas
            continue
        
        if item.extra == "series":                          #Tratamos Series
            if not "/serie" in scrapedurl:
                continue
        else:                                               #Tratamos Películas
            if "/serie" in scrapedurl:
                continue
        
        if 'subtitulado' in scrapedtitle.lower() or 'latino' in scrapedtitle.lower() or 'original' in scrapedtitle.lower():
            item.filter_lang = False
        
        itemlist.append(item.clone(action="listado", title=scrapedtitle, url=scrapedurl))
            
    if item.extra == "series":                              #Añadimos Series VOSE que está fuera del menú principal
        itemlist.append(item.clone(action="listado", title="Series VOSE", url=host + "/series-vose/", filter_lang=False))
    
    return itemlist
    

def listado(item):
    logger.info()
    itemlist = []

    inicio = time.time()                                    # Controlaremos que el proceso no exceda de un tiempo razonable
    fin = inicio + 5                                        # Después de este tiempo pintamos (segundos)
    timeout_search = timeout                                # Timeout para descargas
    if item.extra == 'search':
        timeout_search = timeout * 2                        # Timeout un poco más largo para las búsquedas
        if timeout_search < 5:
            timeout_search = 5                              # Timeout un poco más largo para las búsquedas
    
    # Descarga la página
    data = ''
    try:
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url, timeout=timeout_search).data)
    except:
        pass
        
    if not data:                                            #Si la web está caída salimos sin dar error
        logger.error("ERROR 01: LISTADO: La Web no responde o ha cambiado de URL: " + item.url + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: LISTADO:.  La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
        return itemlist                                     #si no hay más datos, algo no funciona, pintamos lo que tenemos
    
    patron = '<div id="principal">.*?<\/nav><\/div><\/div>'
    data = scrapertools.find_single_match(data, patron)
    
    patron = '<li>\s*<div\s*class="[^"]+">\s*<a href="([^"]+)"\s*'              #url
    patron += 'title="([^"]+)"\s*(?:alt="[^"]+")?\s*>\s*'                       #título
    patron += '<img (?:class="[^"]+")?\s*src="([^"]+)"\s*border="[^"]+"\s*'     #thumb
    patron += 'title="([^"]+)".*?'                                              #categoría, idioma
    patron += '<span class="[^"]+" style="[^"]+"\s*><i>(.*?)<\/i><\/span.*?'    #calidad
    patron += '="dig1">(.*?)<.*?'                                               #tamaño
    patron += '="dig2">(.*?)<\/span><\/div>'                                    #tipo tamaño

    matches = re.compile(patron, re.DOTALL).findall(data)
    if not matches and not '<title>503 Backend fetch failed</title>' in data and not 'No se han encontrado resultados' in data:                                                                           #error
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            item, itemlist = generictools.post_tmdb_listado(item, itemlist)     #Llamamos al método para el pintado del error
            return itemlist                                                     #Salimos
        
        logger.error("ERROR 02: LISTADO: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: LISTADO: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
        return itemlist                                     #si no hay más datos, algo no funciona, pintamos lo que tenemos
    
    #logger.debug("PATRON: " + patron)
    #logger.debug(matches)
    #logger.debug(data)

    for scrapedurl, scrapedtitle, scrapedthumbnail, scrapedcategory, scrapedcalidad, scrapedsize, scrapedsizet in matches:
        item_local = item.clone()                           #Creamos copia de Item para trabajar
        
        title = re.sub('\r\n', '', scrapedtitle).decode('utf8').strip()
        title = title.replace(" torrent", "").replace(" Torrent", "").replace("Series y ", "")
        item_local.url = urlparse.urljoin(host, scrapedurl)
        item_local.thumbnail = urlparse.urljoin(host, scrapedthumbnail)
        
        if "---" in scrapedcalidad:                         #limpiamos calidades
            scrapedcalidad = ''
        if "microhd" in title.lower():
            item_local.quality = "microHD"
        if not "/series-vose/" in item.url and not item_local.quality:
            item_local.quality = scrapedcalidad
        if scrapertools.find_single_match(item_local.quality, r'\d+\.\d+'):
            item_local.quality = ''
        if not item_local.quality and ("DVDRip" in title or "HDRip" in title or "BR-LINE" in title or "HDTS-SCREENER" in title or "BDRip" in title or "BR-Screener" in title or "DVDScreener" in title or "TS-Screener" in title):
            item_local.quality = scrapertools.find_single_match(title, r'\((.*?)\)')
            item_local.quality = item_local.quality.replace("Latino", "")
        if not scrapedsizet:
            scrapedsize = ''
        else:
            item_local.quality += ' [%s %s]' % (scrapedsize.replace(".", ","), scrapedsizet)
        
        item_local.language = []                            #Verificamos el idioma por si encontramos algo
        if "latino" in scrapedcategory.lower() or "latino" in item.url or "latino" in title.lower():
            item_local.language += ["LAT"]
        if "ingles" in scrapedcategory.lower() or "ingles" in item.url or "vose" in scrapedurl or "vose" in item.url:
            if "VOSE" in scrapedcategory.lower() or "sub" in title.lower() or "vose" in scrapedurl or "vose" in item.url:
                item_local.language += ["VOS"]
            else:
                item_local.language += ["VO"]
        if "dual" in scrapedcategory.lower() or "dual" in title.lower():
            item_local.language[0:0] = ["DUAL"]
            
        if item_local.language == []:
                item_local.language = ['CAST']              #Por defecto
        
        #Limpiamos el título de la basura innecesaria
        title = title.replace("Dual", "").replace("dual", "").replace("Subtitulada", "").replace("subtitulada", "").replace("Subt", "").replace("subt", "").replace("Sub", "").replace("sub", "").replace("(Proper)", "").replace("(proper)", "").replace("Proper", "").replace("proper", "").replace("#", "").replace("(Latino)", "").replace("Latino", "")
        title = title.replace("- HDRip", "").replace("(HDRip)", "").replace("- Hdrip", "").replace("(microHD)", "").replace("(DVDRip)", "").replace("(HDRip)", "").replace("(BR-LINE)", "").replace("(HDTS-SCREENER)", "").replace("(BDRip)", "").replace("(BR-Screener)", "").replace("(DVDScreener)", "").replace("TS-Screener", "").replace(" TS", "").replace(" Ts", "").replace("temporada", "").replace("Temporada", "").replace("capitulo", "").replace("Capitulo", "")
        
        title = re.sub(r'(?:\d+)?x.?\s?\d+', '', title)
        title = re.sub(r'\??\s?\d*?\&.*', '', title).title().strip()
        
        item_local.from_title = title                       #Guardamos esta etiqueta para posible desambiguación de título
        
        if item_local.extra == "peliculas":                 #preparamos Item para películas
            if "/serie" in scrapedurl or "/serie" in item.url:
                continue
        if not "/serie" in scrapedurl and not "/serie" in item.url:
            item_local.contentType = "movie"
            item_local.contentTitle = title
            item_local.extra = "peliculas"
        
        if item_local.extra == "series":                    #preparamos Item para series
            if not "/serie" in scrapedurl and not "/serie" in item.url:
                continue
        if "/serie" in scrapedurl or "/serie" in item.url:
            item_local.contentType = "episode"
            item_local.extra = "series"
            epi_mult = scrapertools.find_single_match(item_local.url, r'cap.*?-\d+-al-(\d+)')
            item_local.contentSeason = scrapertools.find_single_match(item_local.url, r'temporada-(\d+)')
            item_local.contentEpisodeNumber = scrapertools.find_single_match(item_local.url, r'cap.*?-(\d+)')
            if not item_local.contentSeason:
                item_local.contentSeason = scrapertools.find_single_match(item_local.url, r'-(\d+)[x|X]\d+')
            if not item_local.contentEpisodeNumber:
                item_local.contentEpisodeNumber = scrapertools.find_single_match(item_local.url, r'-\d+[x|X](\d+)')
            if not item_local.contentSeason or item_local.contentSeason < 1:
                item_local.contentSeason = 0
            if item_local.contentEpisodeNumber < 1:
                item_local.contentEpisodeNumber = 1
            
            item_local.contentSerieName = title
            if epi_mult:
                title = "%sx%s al %s -" % (item_local.contentSeason, str(item_local.contentEpisodeNumber).zfill(2), str(epi_mult).zfill(2))                         #Creamos un título con el rango de episodios
            else:
                title = '%sx%s ' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber).zfill(2))
        
        item_local.action = "findvideos"
        item_local.title = title.strip()
        item_local.infoLabels['year'] = "-"
        
        #Pasamos a TMDB cada Item, para evitar el efecto memoria de tmdb
        #if item.category:       #Si este campo no existe es que viene de la primera pasada de una búsqueda global, pasamos
        #    tmdb.set_infoLabels(item_local, True)
        
        #Ahora se filtra por idioma, si procede, y se pinta lo que vale
        if config.get_setting('filter_languages', channel) > 0 and item.filter_lang:     #Si hay idioma seleccionado, se filtra
            itemlist = filtertools.get_link(itemlist, item_local, list_language)
        else:
            itemlist.append(item_local.clone())                     #Si no, pintar pantalla
   
    #if not item.category:       #Si este campo no existe es que viene de la primera pasada de una búsqueda global
    #    return itemlist         #Retornamos sin pasar por la fase de maquillaje para ahorra tiempo

    #Pasamos a TMDB la lista completa Itemlist
    tmdb.set_infoLabels(itemlist, True)
    
    #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
    item, itemlist = generictools.post_tmdb_listado(item, itemlist)
    
    # Extrae el paginador
    patron = '<div class="paginacion">.*?<span class="pagina pag_actual".*?'
    patron += "<a href='([^']+)'.*?"                                            #url siguiente página
    patron += 'class="pagina">(\d+)<'                                           #próxima página
    matches = scrapertools.find_single_match(data, patron)
    
    patron = 'class="pagina pag_sig">Siguiente.*?'
    patron += "<a href='.*?\/page\/(\d+)\/"                                     #total de páginas
    last_page = scrapertools.find_single_match(data, patron)
    if not last_page:
        patron = '<div class="paginacion">.*?'
        patron += 'class="pagina">(\d+)<\/a><\/div><\/nav><\/div><\/div>'       #total de páginas
        last_page = scrapertools.find_single_match(data, patron)

    if matches:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        if last_page:
            title = '[COLOR gold]Página siguiente >>[/COLOR] %s de %s' % (int(matches[1]) - 1, last_page)
        else:
            title = '[COLOR gold]Página siguiente >>[/COLOR] %s' % (int(matches[1]) - 1)
        
        itemlist.append(Item(channel=item.channel, action="listado", title=title, url=scrapedurl, extra=item.extra, filter_lang=item.filter_lang))

    return itemlist

    
def findvideos(item):
    logger.info()
    itemlist = []
    itemlist_t = []                                                             #Itemlist total de enlaces
    itemlist_f = []                                                             #Itemlist de enlaces filtrados
    if not item.language:
        item.language = ['CAST']                                                #Castellano por defecto

    #Bajamos los datos de la página
    data = ''
    try:
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url, timeout=timeout).data)
    except:
        pass
        
    if not data:
        logger.error("ERROR 01: FINDVIDEOS: La Web no responde o la URL es erronea: " + item.url + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: FINDVIDEOS:.  La Web no responde o la URL es erronea. Si la Web está activa, reportar el error con el log', folder=False))
        if item.emergency_urls and not item.videolibray_emergency_urls:         #Hay urls de emergencia?
            link_torrent = item.emergency_urls[0][0]                            #Guardamos la url del .Torrent
            link_magnet = item.emergency_urls[1][0]                             #Guardamos la url del .Magnet
            item.armagedon = True                                               #Marcamos la situación como catastrófica 
        else:
            if item.videolibray_emergency_urls:                                 #Si es llamado desde creación de Videoteca...
                return item                                                     #Devolvemos el Item de la llamada
            else:
                return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
    #data = unicode(data, "utf-8", errors="replace")

    patron_t = '<div class="enlace_descarga".*?<a href="(.*?\.torrent)"'
    patron_m = '<div class="enlace_descarga".*?<a href="(magnet:?.*?)"'
    if not item.armagedon:                                                      #Si es un proceso normal, seguimos
        link_torrent = scrapertools.find_single_match(data, patron_t)
        link_torrent = urlparse.urljoin(item.url, link_torrent)
        link_torrent = link_torrent.replace(" ", "%20")                         #sustituimos espacios por %20, por si acaso
        #logger.info("link Torrent: " + link_torrent)
        
        link_magnet = scrapertools.find_single_match(data, patron_m)
        link_magnet = urlparse.urljoin(item.url, link_magnet)
        #logger.info("link Magnet: " + link_magnet)
    
    #Si es un lookup para cargar las urls de emergencia en la Videoteca...
    if (link_torrent or link_magnet) and item.videolibray_emergency_urls:
        item.emergency_urls = []
        item.emergency_urls.append([link_torrent])                              #Salvamos el enlace de .torrent
        item.emergency_urls.append([link_magnet])                               #Salvamos el enlace de .magnet
        return item                                                             #... y nos vamos
    
    #Añadimos el tamaño para todos
    size = scrapertools.find_single_match(item.quality, '\s\[(\d+,?\d*?\s\w\s*[b|B]s*)\]')
    if size:
        item.title = re.sub('\s\[\d+,?\d*?\s\w\s*[b|B]s*\]', '', item.title)    #Quitamos size de título, si lo traía
        item.quality = re.sub('\s\[\d+,?\d*?\s\w\s*[b|B]s*\]', '', item.quality)    #Quitamos size de calidad, si lo traía
    
    if not link_torrent and not link_magnet:                                    #error
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)  #Llamamos al método para el pintado del error
        else:
            logger.error("ERROR 02: FINDVIDEOS: El archivo Torrent no existe o ha cambiado la estructura de la Web " + " / PATRON: " + patron_t + " / " + patron_m + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: FINDVIDEOS: El archivo Torrent no existe o ha cambiado la estructura de la Web.  Verificar en la Web y reportar el error con el log', folder=False))
        if item.emergency_urls and not item.videolibray_emergency_urls:         #Hay urls de emergencia?
            link_torrent = item.emergency_urls[0][0]                            #Guardamos la url del .Torrent
            link_magnet = item.emergency_urls[1][0]                             #Guardamos la url del .Magnet
            item.armagedon = True                                               #Marcamos la situación como catastrófica 
        else:
            if item.videolibray_emergency_urls:                                 #Si es llamado desde creación de Videoteca...
                return item                                                     #Devolvemos el Item de la llamada
            else:
                return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

    #Llamamos al método para crear el título general del vídeo, con toda la información obtenida de TMDB
    item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)
    
    if not size and not item.armagedon:
        size = generictools.get_torrent_size(link_torrent)                      #Buscamos el tamaño en el .torrent
    if size:
        size = size.replace('GB', 'G·B').replace('Gb', 'G·b').replace('MB', 'M·B')\
                        .replace('Mb', 'M·b').replace('.', ',')

    #Ahora pintamos el link del Torrent, si lo hay
    if link_torrent:		                                                    # Hay Torrent ?
        #Generamos una copia de Item para trabajar sobre ella
        item_local = item.clone()

        item_local.torrent_info = "[Torrent] "
        item_local.torrent_info += '%s' % size                                   #Agregamos size
        if not item.unify:
            item_local.torrent_info = '[%s]' % item_local.torrent_info.strip().strip(',')
        if item.armagedon:                                                      #Si es catastrófico, lo marcamos
            item_local.quality = '[/COLOR][COLOR hotpink][E] [COLOR limegreen]%s' % item_local.quality
        item_local.url = link_torrent
        if item_local.url and item.emergency_urls and not item.armagedon:
            item_local.torrent_alt = item.emergency_urls[0][0]                  #Guardamos la url del .Torrent ALTERNATIVA
        
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
                
        item_local.alive = "??"                                                 #Calidad del link sin verificar
        item_local.action = "play"                                              #Visualizar vídeo
        item_local.server = "torrent"                                           #Seridor Torrent
        
        itemlist_t.append(item_local.clone())                                   #Pintar pantalla, si no se filtran idiomas
        
        # Requerido para FilterTools
        if config.get_setting('filter_languages', channel) > 0:                 #Si hay idioma seleccionado, se filtra
            itemlist_f = filtertools.get_link(itemlist_f, item_local, list_language)  #Pintar pantalla, si no está vacío
            
        if len(itemlist_f) > 0:                                                 #Si hay entradas filtradas...
            itemlist.extend(itemlist_f)                                         #Pintamos pantalla filtrada
        else:                                                                       
            if config.get_setting('filter_languages', channel) > 0 and len(itemlist_t) > 0: #Si no hay entradas filtradas ...
                thumb_separador = get_thumb("next.png")                             #... pintamos todo con aviso
                itemlist.append(Item(channel=item.channel, url=host, title="[COLOR red][B]NO hay elementos con el idioma seleccionado[/B][/COLOR]", thumbnail=thumb_separador, folder=False))
            itemlist.extend(itemlist_t)                                         #Pintar pantalla con todo si no hay filtrado
    
    #Ahora pintamos el link del Magnet, si lo hay
    itemlist_t = []                                                             #Itemlist total de enlaces
    itemlist_f = []                                                             #Itemlist de enlaces filtrados
    if link_magnet:		                                                        # Hay Magnet ?
        #Generamos una copia de Item para trabajar sobre ella
        item_local = item.clone()
        
        item_local.torrent_info = "[Magnet] "
        item_local.torrent_info += '%s' % size                                  #Agregamos size
        if not item.unify:
            item_local.torrent_info = '[%s]' % item_local.torrent_info.strip().strip(',')
        if item.armagedon:                                                      #Si es catastrófico, lo marcamos
            item_local.quality = '[/COLOR][COLOR hotpink][E] [COLOR limegreen]%s' % item_local.quality
        item_local.url = link_magnet
        
        item_local.title = '[[COLOR yellow]?[/COLOR]] [COLOR yellow][Torrent][/COLOR] ' \
                        + '[COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR] %s' % \
                        (item_local.quality, str(item_local.language),  \
                        item_local.torrent_info)                                #Preparamos título de Magnet
                        
        item_local.title = re.sub(r'\s\[COLOR \w+\]\[\[?\]?\]\[\/COLOR\]', '', item_local.title)    #Quitamos etiquetas vacías
        item_local.title = re.sub(r'\s\[COLOR \w+\]\[\/COLOR\]', '', item_local.title)          #Quitamos colores vacíos
        item_local.alive = "??"                                                 #Calidad del link sin verificar
        item_local.action = "play"                                              #Visualizar vídeo
        item_local.server = "torrent"                                           #Seridor Torrent
        
        itemlist_t.append(item_local.clone())                                   #Pintar pantalla, si no se filtran idiomas
        
        # Requerido para FilterTools
        if config.get_setting('filter_languages', channel) > 0:                 #Si hay idioma seleccionado, se filtra
            itemlist_f = filtertools.get_link(itemlist_f, item_local, list_language)  #Pintar pantalla, si no está vacío
            
        if len(itemlist_f) > 0:                                                 #Si hay entradas filtradas...
            itemlist.extend(itemlist_f)                                         #Pintamos pantalla filtrada
        else:                                                                       
            if config.get_setting('filter_languages', channel) > 0 and len(itemlist_t) > 0: #Si no hay entradas filtradas ...
                thumb_separador = get_thumb("next.png")                             #... pintamos todo con aviso
                itemlist.append(Item(channel=item.channel, url=host, title="[COLOR red][B]NO hay elementos con el idioma seleccionado[/B][/COLOR]", thumbnail=thumb_separador, folder=False))
            itemlist.extend(itemlist_t)                                         #Pintar pantalla con todo si no hay filtrado
    
    #logger.debug("TORRENT: " + link_torrent + "MAGNET: " + link_magnet + " / title gen/torr: " + item.title + " / " + item_local.title + " / calidad: " + item_local.quality + " / tamaño: " + size + " / content: " + item_local.contentTitle + " / " + item_local.contentSerieName)
    #logger.debug(item_local)

    # Requerido para AutoPlay
    autoplay.start(itemlist, item)                                              #Lanzamos Autoplay
    
    return itemlist


def actualizar_titulos(item):
    logger.info()
    
    item = generictools.update_title(item) #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels

    #Volvemos a la siguiente acción en el canal
    return item
    

def search(item, texto):
    logger.info("search:" + texto)
    # texto = texto.replace(" ", "+")

    try:
        item.url = host + "?s=%s&x=0&y=0" % texto
        itemlist = listado(item)
        
        return itemlist

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
 
 
def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host + '/estrenos-/'
            item.extra = "peliculas"
            item.category_new= 'newest'

            itemlist = listado(item)
            if "Página siguiente >>" in itemlist[-1].title:
                itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
