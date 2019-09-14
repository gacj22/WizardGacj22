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

channel = "mejortorrent1"
#host = config.get_setting('domain_name', channel)
host = "https://mejortorrent1.net/"
domain = "mejortorrent1.net"

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
    thumb_series_az = get_thumb("channels_tvshow_az.png")
    thumb_docus = get_thumb("channels_documentary.png")
    thumb_buscar = get_thumb("search.png")
    thumb_separador = get_thumb("next.png")
    thumb_settings = get_thumb("setting_0.png")
    
    autoplay.init(item.channel, list_servers, list_quality)

    #itemlist.append(Item(channel=item.channel, title="Novedades", action="listado_busqueda", extra="novedades", tipo=False,
    #                     url= host + "ultimos-torrents/", thumbnail=thumb_buscar))
                         
    itemlist.append(Item(channel=item.channel, title="Peliculas", action="submenu", extra="peliculas",
                         url= host, thumbnail=thumb_pelis))
    
    itemlist.append(Item(channel=item.channel, title="Series", action="submenu", extra="series",
                         url= host, thumbnail=thumb_series))
    
    itemlist.append(Item(channel=item.channel, title="Documentales", action="submenu", extra="documentales",
                         url= host, thumbnail=thumb_docus))
    
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", thumbnail=thumb_buscar, tipo=False))
    
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

    thumb_pelis = get_thumb("channels_movie.png")
    thumb_pelis_hd = get_thumb("channels_movie_hd.png")
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_series_hd = get_thumb("channels_tvshow_hd.png")
    thumb_series_az = get_thumb("channels_tvshow_az.png")
    thumb_docus = get_thumb("channels_documentary.png")
    thumb_buscar = get_thumb("search.png")
    thumb_settings = get_thumb("setting_0.png")

    if item.extra == "peliculas":
        itemlist.append(Item(channel=item.channel, title="Peliculas", action="listado", extra="peliculas", tipo=False,
                             url= host + "peliculas/", thumbnail=thumb_pelis))
        itemlist.append(Item(channel=item.channel, title="Películas Listado Alfabético", action="alfabeto",
                             url= host + "listado?cat=peliculas&letra=", extra="peliculas", thumbnail=thumb_pelis))
        itemlist.append(Item(channel=item.channel, title="Peliculas HD", action="listado", extra="peliculas", tipo=False,
                             url= host + "peliculas-hd/", thumbnail=thumb_pelis_hd))
        itemlist.append(Item(channel=item.channel, title="Películas HD Listado Alfabético", action="alfabeto",
                             url= host + "listado?cat=peliculas hd&letra=", extra="peliculas", thumbnail=thumb_pelis))
    
    elif item.extra == "series":
        itemlist.append(Item(channel=item.channel, title="Series", action="listado", extra="series", tipo=False,
                             url= host + "series/", thumbnail=thumb_series))
        itemlist.append(Item(channel=item.channel, title="Series Listado Alfabético", action="alfabeto", extra="series",
                             url= host + "listado?cat=series&letra=", thumbnail=thumb_series_az))
        itemlist.append(Item(channel=item.channel, title="Series HD", action="listado", extra="series", tipo=False,
                             url= host + "series-hd/", thumbnail=thumb_series_hd))
        itemlist.append(Item(channel=item.channel, title="Series HD Listado Alfabético", action="alfabeto", extra="series",
                             url= host + "listado?cat=series hd&letra=", thumbnail=thumb_series_az))
                         
    elif item.extra == "documentales":                     
        itemlist.append(Item(channel=item.channel, title="Documentales", action="listado", extra="documentales", tipo=False,
                             url= host + "documentales/", thumbnail=thumb_docus))
        itemlist.append(Item(channel=item.channel, title="Documentales Listado Alfabético", action="alfabeto", extra="documentales", url= host + "listado?cat=documentales&letra=", thumbnail=thumb_docus))
        itemlist.append(Item(channel=item.channel, title="Varios", action="listado", extra="varios", tipo=False,
                             url= host + "variados/", thumbnail=thumb_docus))
        itemlist.append(Item(channel=item.channel, title="Varios Listado Alfabético", action="alfabeto", extra="varios", url= host + "listado?cat=variados&letra=", thumbnail=thumb_docus))

    return itemlist
    
    
def alfabeto(item):
    logger.info()
    itemlist = []

    for letra in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']:
        itemlist.append(Item(channel=item.channel, action="listado", title=letra, extra=item.extra, tipo=True, url=item.url + letra.lower()))

    return itemlist

def listado(item):
    logger.info()
    itemlist = []
    url_next_page =''                                       # Control de paginación
    cnt_tot = 30                                            # Poner el num. máximo de items por página
    
    if item.totalItems:
        del item.totalItems
    item.category = item.channel.capitalize()
    
    try:
        data = ''
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url, timeout=timeout).data)
        data = re.sub('\r\n', '', data).decode('utf8').encode('utf8')
        data = js2py_conversion(data, item.url)
        data = data.replace("'", '"')
    except:
        logger.error("ERROR 01: LISTADO: La Web no responde o ha cambiado de URL: " + item.url + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: LISTADO:.  La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
    if not data:                                #Si la web está caída salimos sin dar error
        logger.error("ERROR 01: LISTADO: La Web no responde o ha cambiado de URL: " + item.url + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: LISTADO:.  La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
    
    # En este canal las url's y los títulos tienen diferente formato dependiendo del contenido
    if (item.extra == "peliculas" or item.extra == "varios") and item.tipo:             #Desde Lista Alfabética
        patron = '<a href="([^"]+)">([^<]+)?<\/a>'
        patron_enlace = '\/\/.*?\/(.*?)\/$'
        patron_title = '<a href="[^"]+">([^<]+)<\/a>(\s*<b>([^>]+)<\/b>)?'
        item.action = "findvideos"
        item.contentType = "movie"
        pag = False                                                                     #No hay paginación
    elif (item.extra == "peliculas" or item.extra == "varios") and not item.tipo:       #Desde Menú principal
        patron = '<a href="([^"]+)"[^>]+>?<img src="([^"]+)"[^<]+<\/a>'
        patron_enlace = '\/\/.*?\/(8.*?)\/$'
        patron_title = '<a href="[^"]+">([^<]+)<\/a>(\s*<b>([^>]+)<\/b>)?'
        item.action = "findvideos"
        item.contentType = "movie"
        pag = True                                                                      #Sí hay paginación
        cnt_tot = 20                                    # Poner el num. máximo de items por página.  Parece que hay 18
        item.next_page = 'b'
    elif item.extra == "series" and item.tipo:
        patron = '<a href="([^"]+)">([^<]+)?<\/a>'
        patron_enlace = '\/\/.*?\/(.*?)-[temporada]?\d+[-|x]'
        patron_title = '<a href="[^"]+">([^<]+)<\/a>(\s*<b>([^>]+)<\/b>)?'
        patron_title_ep = '\/\/.*?\/(.*?)-(\d{1,2})x(\d{1,2})(?:-al-\d{1,2}x\d{1,2})?-?(\d+p)?\/$'
        patron_title_se = '\/\/.*?\/(.*?)temporada-?(?:\d+p-)?(\d{1,2})?-?(.*?)?\/$'
        item.action = "episodios"
        item.contentType = "season"
        pag = False
        cnt_tot = 10                                    # Se reduce el numero de items por página porque es un proceso pesado
    elif item.extra == "series" and not item.tipo:
        patron = '<a href="([^"]+)"[^>]+>?<img src="([^"]+)"[^<]+<\/a>'
        patron_enlace = '\/\/.*?\/(.*?)-[temporada]?\d+[-|x]'
        patron_title = '<a href="[^"]+">([^<]+)<\/a>(\s*<b>([^>]+)<\/b>)?'
        patron_title_ep = '\/\/.*?\/(.*?)-(\d{1,2})x(\d{1,2})(?:-al-\d{1,2}x\d{1,2})?-?(\d+p)?\/$'
        patron_title_se = '\/\/.*?\/(.*?)temporada-?(?:\d+p-)?(\d{1,2})?-?(.*?)?\/$'
        item.action = "episodios"
        item.contentType = "season"
        pag = True
        cnt_tot = 10                                    # Se reduce el numero de items por página porque es un proceso pesado
    elif item.extra == "documentales" and item.tipo:
        patron = '<a href="([^"]+)">([^<]+)?<\/a>'
        patron_enlace = '\/\/.*?\/(.*?)-[temporada]?\d+[-|x]'
        patron_title = '<a href="[^"]+">([^<]+)<\/a>(\s*<b>([^>]+)<\/b>)?'
        patron_title_ep = '\/\/.*?\/(.*?)-(\d{1,2})x(\d{1,2})(?:-al-\d{1,2}x\d{1,2})?-?(\d+p)?\/$'
        patron_title_se = '\/\/.*?\/(.*?)temporada-?(?:\d+p-)?(\d{1,2})?-?(.*?)?\/$'
        item.action = "episodios"
        item.contentType = "tvshow"
        pag = False
    else:
        patron = '<a href="([^"]+)"[^>]+>?<img src="([^"]+)"[^<]+<\/a>'
        patron_enlace = '\/\/.*?\/(.*?)-[temporada]?\d+[-|x]'
        patron_title = '<a href="[^"]+">([^<]+)<\/a>(\s*<b>([^>]+)<\/b>)?'
        patron_title_ep = '\/\/.*?\/(.*?)-(\d{1,2})x(\d{1,2})(?:-al-\d{1,2}x\d{1,2})?-?(\d+p)?\/$'
        patron_title_se = '\/\/.*?\/(.*?)temporada-?(?:\d+p-)?(\d{1,2})?-?(.*?)?\/$'
        item.action = "episodios"
        item.contentType = "tvshow"
        pag = True
        item.next_page = 'b'

    # Preparamos la paginación.  Las páginas alfabéticas no tienen paginación.  
    # El resto sí, pero con un número variable de links
    if not item.cnt_pag:
        cnt_pag = 0
    else:
        cnt_pag = item.cnt_pag
        del item.cnt_pag
    if not item.cnt_pag_num:
        cnt_pag_num = 0         # Número de página actual
    else:
        cnt_pag_num = item.cnt_pag_num
        del item.cnt_pag_num

    matches = re.compile(patron, re.DOTALL).findall(data)
    matches_cnt = len(matches)
    if not matches and not 'Se han encontrado<b>0</b> resultados.' in data:     #error
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            item, itemlist = generictools.post_tmdb_listado(item, itemlist)     #Llamamos al método para el pintado del error
            return itemlist                                                     #Salimos
            
        logger.error("ERROR 02: LISTADO: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: LISTADO: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
        return itemlist                             #si no hay más datos, algo no funciona, pintamos lo que tenemos

    #Capturamos el num. de la última página para informala a pié de página.  Opción para páginas sin paginación
    if pag == False:
        item.last_page = (len(matches) / cnt_tot) + 1
    
    if not item.last_page and pag:                  #Capturamos el num. de la última página para informala a pié de página
        item.last_page = -1
        #patron_next_page = "<a href='([^']+)' class='paginar'> Siguiente >> <\/a>"
        if "/documentales" in item.url:
            patron_next_page = '<a href="([^"]+\/)\d+\/" class="paginar" >\d+<\/a'
        else:
            patron_next_page = '<a class="paginar" href="([^"]+\/)\d+\/">&\w+;<\/a>&\w+;<\/div>'
        url_next_page = urlparse.urljoin(item.url, scrapertools.find_single_match(data, patron_next_page) + str(cnt_pag_num + 2))
        #url_last_page = re.sub(r"\d+$", "9999", url_next_page)
        #data_last = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(url_last_page).data)
        #data_last = js2py_conversion(data_last, url_last_page)
        #if "/documentales" in item.url:
            #patron_last_page = '<a href="[^"]+\/(\d+)\/" class="paginar" >\d+<\/a>&nbsp;<\/div>'
        patron_last_page = '<a class="paginar" href="[^"]+\/(\d+)\/">&\w+;<\/a>&\w+;<\/div>'
        #patron_last_page = '<span class="nopaginar">(\d+)<\/span>'
        try:
            #item.last_page = int(scrapertools.find_single_match(data, patron_last_page)) * (len(matches) / cnt_tot)
            item.last_page = int(scrapertools.find_single_match(data, patron_last_page))
        except:
            item.last_page = 0

    if matches_cnt > cnt_tot and item.extra == "documentales" and pag:
        item.next_page = ''
    if item.next_page != 'b':
        if matches_cnt > cnt_pag + cnt_tot:
            url_next_page = item.url
        matches = matches[cnt_pag:cnt_pag+cnt_tot]
        next_page = ''
        if matches_cnt <= cnt_pag + (cnt_tot * 2):
            if pag:
                next_page = 'b'
        modo = 'continue'
    else:
        matches = matches[cnt_pag:cnt_pag+cnt_tot]
        next_page = 'a'
        #patron_next_page = "<a href='([^']+)' class='paginar'> Siguiente >> <\/a>"
        if "/documentales" in item.url:
            patron_next_page = '<a href="([^"]+\/)\d+\/" class="paginar" >\d+<\/a'
        else:
            patron_next_page = '<a class="paginar" href="([^"]+\/)\d+\/">&\w+;<\/a>&\w+;<\/div>'
        matches_next_page = re.compile(patron_next_page, re.DOTALL).findall(data)
        modo = 'continue'
        if len(matches_next_page) > 0:
            url_next_page = urlparse.urljoin(item.url, matches_next_page[0] + str(cnt_pag_num + 2))
            modo = 'next'
    if item.next_page:
        del item.next_page

    #logger.debug(data)
    #logger.debug("PATRON1: " + patron + " / ")
    #logger.debug(matches)

    # Primera pasada
    # En la primera pasada se obtiene una información básica del título a partir de la url
    # Para Series se obtienen la temporada y el episodio  
    # Se limpian algunas etiquetas del item inical.
    for scrapedurl, scrapedthumbnail in matches:
        item_local = item.clone()
        item_local.tipo = True
        del item_local.tipo
        if item_local.totalItems:
            del item_local.totalItems
        if item_local.modo:
            del item_local.modo
        if item_local.next_page:
            del item_local.next_page
        item_local.pag = True
        del item_local.pag
        if item_local.text_color:
            del item_local.text_color
        item_local.last_page = 0
        del item_local.last_page
        if item_local.cnt_pag_num:
            del item_local.cnt_pag_num
            
        item_local.title = ''
        item_local.context = "['buscar_trailer']"

        item_local.title = scrapertools.find_single_match(scrapedurl, patron_enlace)
        item_local.title = item_local.title.replace("-", " ").capitalize()
        item_local.url = scrapedurl
        item_local.thumbnail = scrapedthumbnail
        if "http" not in item_local.thumbnail:
            item_local.thumbnail = ''
        item_local.infoLabels['year'] = '-'         # Al no saber el año, le ponemos "-" y TmDB lo calcula automáticamente
        
        # Para que el menú contextual muestre conrrectamente las opciones de añadir a Videoteca
        if item_local.extra == "series":
            if scrapertools.find_single_match(scrapedurl, patron_title_ep):
                item_local.contentType = "episode"
            else:
                item_local.contentType = "season"
            
        # Poner nombre real de serie.  Busca nº de temporada y capítulo
        if item_local.extra == "series":
            if item_local.contentType == "episode":
                real_title, item_local.contentSeason, episodio, item_local.quality = scrapertools.find_single_match(scrapedurl, patron_title_ep)
                
                #Hay que buscar la raiz de la temporada
                data_epi = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item_local.url, timeout=timeout).data)
                data_epi = js2py_conversion(data_epi, item_local.url)
                url = scrapertools.find_single_match(data_epi, '<tr><td>.*<a href="([^"]+)" style="text-decoration:none;"><h1 style=')
                if not url:
                    url = scrapertools.find_single_match(data_epi, '<td><a href="(secciones.php\?sec\=descargas&ap=[^"]+)"')
                if not url:
                    url = scrapertools.find_single_match(data_epi, '<link rel="canonical" href="([^"]+)"')
                #Probamos si es una temporada completa, aunque no tenga raiz
                if not url and scrapertools.find_single_match(data_epi, "(<form (?:style='[^']+'\s)?name='episodios' action='[^']+' method='post'>.*?)<\/form>"):
                    url = item_local.url                    #Salvamos la url original
                if not url:                                 #No encuentro la Temporada.  Lo dejo como capítulo suelto
                    item_local.action = "findvideos"
                    item_local.contentEpisodeNumber = episodio
                    if not item_local.contentEpisodeNumber:
                        item_local.contentEpisodeNumber = 1
                    logger.debug(item_local)
                    logger.debug(data_epi)
                else:                                       #Busco la temporada.  Salvo url de episodio por si acaso
                    #item_local.url_ori = item_local.url
                    item_local.url = url
                    item_local.contentType = "season"
            else:
                try:
                    real_title, item_local.contentSeason, item_local.quality = scrapertools.find_single_match(scrapedurl, patron_title_se)
                except:
                    real_title = ''
                    item_local.action = "findvideos"
                    item_local.contentType = "episode"
                    item_local.contentSeason = 1
                    item_local.contentEpisodeNumber = 1
                    item_local.quality = ''

            item_local.contentSerieName = real_title.replace("-", " ").capitalize()
            if not item_local.contentSeason:
                item_local.contentSeason = 1
        elif item.extra == "documentales":
            item_local.contentSerieName = item_local.title
            item_local.contentSeason = 1
        else:
            item_local.contentTitle = item_local.title
                
        if item_local.contentType == "episode": 
            item_local.title = '%sx%s -' % (item_local.contentSeason, str(item_local.contentEpisodeNumber).zfill(2))
        
        itemlist.append(item_local.clone())
        
        #logger.debug(item_local)

    # Segunda pasada
    # En esta pasada se localizan títulos válidos y las calidades.  Varían los formas dependiendo desde donde se llama
    # Si la llamada es desde Alfabéticos faltarán muchas calidades
    matches = re.compile(patron_title, re.DOTALL).findall(data)
    matches = matches[cnt_pag:cnt_pag+cnt_tot]
    if modo == 'next':
        cnt_pag = 0
    else:
        cnt_pag += cnt_tot
    cnt_pag_num += 1
    
    #logger.debug("PATRON2: " + patron_title)
    #logger.debug(matches)
    cnt = 0
    for scrapedtitle_alt, notused, scrapedinfo in matches:
        item_local = itemlist[cnt]  #Vinculamos item_local con la entrada de la lista itemlist (más fácil de leer)
        
        # Limpiamos títulos, Sacamos datos de calidad, audio y lenguaje
        scrapedtitle = re.sub('\r\n', '', scrapedtitle_alt).decode('utf8').encode('utf8').strip()
        title = scrapedtitle
        title = title.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ü", "u").replace("ï¿½", "ñ").replace("Ã±", "ñ").replace("&#215;", "x")

        title_subs = []
        
        #Determinamos y marcamos idiomas distintos del castellano
        item_local.language = []
        if "[subs" in title.lower() or "[vos" in title.lower()  or "v.o.s" in title.lower():
            item_local.language += ["VOS"]
        title = title.replace(" [Subs. integrados]", "").replace(" [subs. Integrados]", "").replace(" [VOSE", "").replace(" [VOS", "").replace(" (V.O.S.E)", "")
        if "latino" in title.lower() or "argentina" in title.lower():
            item_local.language += ["LAT"]
            title = title.replace(" Latino", "").replace(" latino", "").replace(" Argentina", "").replace(" argentina", "")
        title = title.replace("Castellano", "").replace("castellano", "").replace("inglés", "").replace("ingles", "").replace("Inglés", "").replace("Ingles", "")
        
        if "audio" in title.lower():                                    #Reservamos info de audio para después de TMDB
            title_subs += ['[%s]' % scrapertools.find_single_match(title, r'(\[[a|A]udio.*?\])')]
            title = re.sub(r'\[[a|A]udio.*?\]', '', title)
        if "[dual" in title.lower():
            item_local.language[0:0] = ["DUAL"]
            title = title = re.sub(r'\[D|dual.*?\]', '', title)
        if scrapertools.find_single_match(title, r'-\s[m|M].*?serie'):
            title = re.sub(r'-\s[m|M].*?serie', '', title)
            title_subs += ["Miniserie"]
            
        if item_local.language == []:
            item_local.language = ['CAST']                              #Por defecto
        
        if title.endswith('.'):
            title = title[:-1]
            
        if not title:
            title = "SIN TÍTULO"
        title = scrapertools.remove_htmltags(title)
            
        info = scrapedinfo.decode('utf8').encode('utf8')
        info = info.replace("(", "").replace(")", "").replace(" ", "")

        # Ahora preparamos el título y la calidad tanto para series como para documentales y películas 
        # scrapedinfo tiene la calidad, pero solo en llamadas desde peliculas sin alfabeto
        if item_local.extra == "series" or item_local.extra == "documentales":
            if item_local.quality:
                title = re.sub(r'[\[|\(]\d+.*?[\)|\]]', '', title)      # Quitar la calidad del título
            info = ""
            if not item_local.contentSerieName:
                item_local.contentSerieName = title.strip()
                if not item_local.contentSerieName:
                    item_local.contentSerieName = "SIN TITULO"
            if item_local.infoLabels['title']:
                del item_local.infoLabels['title']
            if item_local.contentType == "episode":
                title = re.sub(r'\d+x\d+(?: al \d+)?', '', title)

        if info != "" and not item_local.quality:
            item_local.quality = info
        if not scrapertools.find_single_match(title, '[\[|\(](.*?)[\)|\]]') in item_local.quality:
            if item_local.quality:
                item_local.quality += ' '
            item_local.quality = scrapertools.find_single_match(title, '[\[|\(](.*?)[\)|\]]')
            if scrapertools.find_single_match(title, '[\[|\(].*?[\)|\]]\s?[\[|\(](.*?)[\)|\]]') and not scrapertools.find_single_match(title, '[\[|\(].*?[\)|\]]\s?[\[|\(](.*?)[\)|\]]') in item_local.quality:
                item_local.quality += ' %s' % scrapertools.find_single_match(title, '[\[|\(].*?[\)|\]]\s?[\[|\(](.*?)[\)|\]]')
        title = re.sub(r'[\[|\(].*?[\)|\]]\s?[\[|\(].*?[\)|\]]', '', title)
        title = re.sub(r'[\[|\(].*?[\)|\]]', '', title)
        if "(hdrip" in title.lower() or "(br" in title.lower() or "(vhsrip" in title.lower() or "(dvdrip" in title.lower() or "(fullb" in title.lower() or "(blu" in title.lower() or "(4k" in title.lower() or "(hevc" in title.lower() or "(imax" in title.lower() or "extendida" in title.lower() or "[720p]" in title.lower()  or "[1080p]" in title.lower():
            title = re.sub(r'[\[|\(].*?[\)|\]]', '', title)
        if not item_local.quality:
            if "fullbluray" in title.lower():
                item_local.quality = "FullBluRay"
                title = title.replace("FullBluRay", "").replace("fullbluray", "")
            if "4k" in title.lower() or "hdr" in title.lower():
                item_local.quality = "4K"
                title = title.replace("4k-hdr", "").replace("4K-HDR", "").replace("hdr", "").replace("HDR", "").replace("4k", "").replace("4K", "")
        title = title.replace("(", "").replace(")", "").replace("[", "").replace("]", "").strip()
        if item_local.contentType == "movie":
            item_local.title = title
            item_local.contentTitle = title
        elif item_local.contentType != "episode":
            item_local.title = title
            item_local.title = item_local.contentSerieName
            title = item_local.contentSerieName
        item_local.from_title = title                       #Guardamos esta etiqueta para posible desambiguación de título

        if "saga" in item_local.contentTitle.lower() or "saga" in item_local.contentSerieName.lower():
            item_local.contentTitle = item_local.contentTitle.replace("Saga ", "").replace("Saga", "")
            item_local.contentSerieName = item_local.contentSerieName.replace("Saga ", "").replace("Saga", "")
            title_subs += ["Saga"]
        if "colecc" in item_local.contentTitle.lower() or "colecc" in item_local.contentSerieName.lower():
            item_local.contentTitle = item_local.contentTitle.replace("Coleccion ", "").replace("Coleccion", "")
            item_local.contentSerieName = item_local.contentSerieName.replace("Coleccion ", "").replace("Coleccion", "")
            title_subs += ["Coleccion"]
            
        #Guarda la variable temporal que almacena la info adicional del título a ser restaurada después de TMDB
        item_local.title_subs = title_subs
        
        #Salvamos y borramos el número de temporadas porque TMDB a veces hace tonterias.  Lo pasamos como serie completa
        if item_local.contentSeason and (item_local.contentType == "season" or item_local.contentType == "tvshow"):
            item_local.contentSeason_save = item_local.contentSeason
            del item_local.infoLabels['season']


        #logger.debug(item_local)
        
        cnt += 1
        if cnt == len(itemlist):
            break
    
    #Llamamos a TMDB para que complete InfoLabels desde itemlist.  Mejor desde itemlist porque envía las queries en paralelo
    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    
    #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
    item, itemlist = generictools.post_tmdb_listado(item, itemlist)

    if len(itemlist) == 0:
        itemlist.append(Item(channel=item.channel, action="mainlist", title="No se ha podido cargar el listado"))
    else:
        if url_next_page:
            title_foot = str(cnt_pag_num)
            if item.last_page > 0:
                title_foot += ' de %s' % str(item.last_page)
            itemlist.append(
                Item(channel=item.channel, action="listado", title="[COLOR gold][B]Pagina siguiente >> [/B][/COLOR]" + title_foot, url=url_next_page, next_page=next_page, cnt_pag=cnt_pag, pag=pag, modo=modo, extra=item.extra, tipo=item.tipo, last_page=item.last_page, cnt_pag_num=cnt_pag_num))
                
    #logger.debug(url_next_page + " / " + next_page + " / " + str(matches_cnt) + " / " + str(cnt_pag)  + " / " + str(pag)  + " / " + modo + " / " + item.extra + " / " + str(item.tipo))

    return itemlist
    

def listado_busqueda(item):
    logger.info()
    itemlist = []
    url_next_page =''           # Controlde paginación
    cnt_tot = 39                # Poner el num. máximo de items por página.  Dejamos que la web lo controle
    cnt_title = 0               # Contador de líneas insertadas en Itemlist
    cnt_pag = 0                 # Contador de líneas leídas de Matches
    cnt_next = 0                # Contador de páginas leidas antes de pintar la pantalla
    total_pag = 10              # Líneas por página de la web
    curr_page_num = 1           # Página actual
    category = ""               # Guarda la categoria que viene desde una busqueda global
    matches = []
    inicio = time.time()                                    # Controlaremos que el proceso no exceda de un tiempo razonable
    fin = inicio + 5                                        # Después de este tiempo pintamos (segundos)
    timeout_search = timeout                                # Timeout para descargas
    if item.extra == 'search':
        timeout_search = timeout * 2                        # Timeout un poco más largo para las búsquedas
        if timeout_search < 5:
            timeout_search = 5                              # Timeout un poco más largo para las búsquedas
    
    if item.url_next_page:
        url_next_page = item.url_next_page
    else:
        url_next_page = item.url

    #Máximo num. de líneas permitidas por TMDB. Máx de 5 páginas por Itemlist para no degradar el rendimiento
    while cnt_title <= cnt_tot and fin > time.time():
        
        status = False          # Calidad de los datos leídos
        data = ''
        try:
            data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(url_next_page, post=item.post, timeout=timeout_search).data)
            data = re.sub('\r\n', '', data).decode('utf8').encode('utf8')
            data = js2py_conversion(data, url_next_page, post=item.post)
            data = data.replace("'", '"')
        except:
            logger.error("ERROR 01: LISTADO_BUSQUEDA: La Web no responde o ha cambiado de URL: " + item.url + item.post + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: LISTADO_BUSQUEDA:.  La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
            if len(itemlist) > 1:
                #Pasamos a TMDB la lista completa Itemlist
                tmdb.set_infoLabels(itemlist, __modo_grafico__)
                #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
                item, itemlist = generictools.post_tmdb_listado(item, itemlist)
            return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
        if not data:        #Si la web está caída salimos sin dar error
            logger.error("ERROR 01: LISTADO_BUSQUEDA: La Web no responde o ha cambiado de URL: " + item.url + item.post + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: LISTADO_BUSQUEDA:.  La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
            if len(itemlist) > 1:
                #Pasamos a TMDB la lista completa Itemlist
                tmdb.set_infoLabels(itemlist, __modo_grafico__)
                #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
                item, itemlist = generictools.post_tmdb_listado(item, itemlist)
            return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

        cnt_next += 1
        patron = '<a href="([^"]+)" style="[^>]+>([^<]+)<\/a>'                      #url y título
        patron += '<span style="[^"]+">\(([^>]+)?\)<\/a><\/td>'                     #calidad
        patron += '<td align="[^"]+" width="[^"]+">([^>]+)<\/td><\/tr>'             #tipo de contenido
        matches_alt = scrapertools.find_multiple_matches(data, patron)

        i = 0
        if len(matches_alt) > 0:
            status = True
            for scrapedurl, scrapedtitle, scrapedquality, scrapedtype in matches_alt:
                if scrapedtype in ['Juegos', 'Capitulos', 'Musica']:                #limpiamos de contenidos no deseados
                    i += 1
                    continue
                if not lookup_idiomas_paginacion(item, scrapedurl, scrapedtitle, scrapedquality, list_language):
                    i += 1
                    continue
                matches.append(matches_alt[i])                                      #acumulamos los títulos
                i += 1
        cnt_title = len(matches)                                                    #número de títulos a pintar
        
        if not matches_alt and not 'Se han encontrado<b>0</b> resultado(s).' in data and not "Introduce alguna palabra para buscar con al menos 3 letras" in data and status is False and not matches:                #error
            item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
            if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
                item, itemlist = generictools.post_tmdb_listado(item, itemlist)     #Llamamos al método para el pintado del error
                return itemlist                                                     #Salimos
            
            logger.error("ERROR 02: LISTADO_BUSQUEDA: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: LISTADO_BUSQUEDA: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
            if len(itemlist) > 1:
                #Pasamos a TMDB la lista completa Itemlist
                tmdb.set_infoLabels(itemlist, __modo_grafico__)
                #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
                item, itemlist = generictools.post_tmdb_listado(item, itemlist)
            return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
        
        #Capturamos el num. de la última página para informala a pié de página
        try:
            last_page = int(scrapertools.find_single_match(data, 'Se han encontrado<b>(\d+)<\/b> resultado\(s\).'))
            last_page = (last_page / total_pag) + 1
        except:
            last_page = 0
            pass

        curr_page_num = int(scrapertools.find_single_match(url_next_page, '\/page\/(\d+)\/$'))
        if (curr_page_num + 1) <= last_page:                                        #Tenemos la pantalla llena?
            url_next_page = re.sub(r'\/page\/\d+\/$', '/page/%s/' % str(curr_page_num + 1), url_next_page)  #actualizamos el num. pag.
        else:
            url_next_page = ''                      #si no hay más página, limpiamos para salir
            cnt_title = 99
          
        if cnt_title >= cnt_tot * 0.75:             #Si el num. de títulos supera el límite, salimos del loop
            cnt_title = 99

    #logger.debug("MATCHES: ")
    #logger.debug(matches)
    #logger.debug(data)
    
    for scrapedurl, scrapedtitle_alt, scrapedquality, scrapedtype in matches:
        # Creamos "item_local" y lo limpiamos un poco de algunos restos de item
        item_local = item.clone()
        if item_local.category:
            category = item.category
            item_local.category = item_local.channel.capitalize()
        item_local.tipo = True
        del item_local.tipo
        if item_local.totalItems:
            del item_local.totalItems
        if item_local.text_color:
            del item_local.text_color
        if item_local.cnt_pag_num:
            del item_local.cnt_pag_num
        item_local.url = scrapedurl
        item_local.contentThumbnail = ''
        item_local.thumbnail = ''
        item_local.title = ''
        item_local.context = "['buscar_trailer']"
        item_local.infoLabels['year'] = '-'  # Al no saber el año, le ponemos "-" y TmDB lo calcula automáticamente
        
        # Limpiamos títulos, Sacamos datos de calidad, audio y lenguaje
        scrapedtitle = re.sub('\r\n', '', scrapedtitle_alt).decode('utf8').encode('utf8').strip()
        title = scrapedtitle
        title = title.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ü", "u").replace("ï¿½", "ñ").replace("Ã±", "ñ")

        title_subs = []
        
        #Determinamos y marcamos idiomas distintos del castellano
        item_local.language = []
        if "[subs" in title.lower() or "[vos" in title.lower()  or "v.o.s" in title.lower() or "vo" in title.lower():
            item_local.language += ["VOS"]
        title = title.replace(" [Subs. integrados]", "").replace(" [subs. Integrados]", "").replace(" [VOSE", "").replace(" [VOS", "").replace(" (V.O.S.E)", "").replace(" VO", "")
        if "latino" in title.lower() or "argentina" in title.lower():
            item_local.language += ["LAT"]
            title = title.replace(" Latino", "").replace(" latino", "").replace(" Argentina", "").replace(" argentina", "")
        title = title.replace("Castellano", "").replace("castellano", "").replace("inglés", "").replace("ingles", "").replace("Inglés", "").replace("Ingles", "")
        
        if "audio" in title.lower():                                    #Reservamos info de audio para después de TMDB
            title_subs += ['[%s]' % scrapertools.find_single_match(title, r'(\[[a|A]udio.*?\])')]
            title = re.sub(r'\[[a|A]udio.*?\]', '', title)
        if "[dual" in title.lower():
            item_local.language[0:0] = ["DUAL"]
            title = title = re.sub(r'\[D|dual.*?\]', '', title)
        if scrapertools.find_single_match(title, r'-\s[m|M].*?serie'):
            title = re.sub(r'-\s[m|M].*?serie', '', title)
            title_subs += ["Miniserie"]
            
        if item_local.language == []:
            item_local.language = ['CAST']                              #Por defecto
        
        if title.endswith('.'):
            title = title[:-1]
        
        if not title:
            title = "SIN TÍTULO"
        title = scrapertools.remove_htmltags(title)

        # Ahora preparamos el título y la calidad tanto para series como para documentales y películas
        #if item.extra == "novedades" and ("Series" in scrapedtype or "Documentales" in scrapedtype):
        if item.extra == "novedades":
            item_local.quality = scrapertools.find_single_match(scrapedtitle, '.*?\[(.*?)\]')
        else:
            item_local.quality = scrapertools.remove_htmltags(scrapedquality).decode('utf8').encode('utf8')
        item_local.quality = item_local.quality.replace("(", "").replace(")", "").replace("[", "").replace("]", "").replace("Documental", "").replace("documental", "")
        
        #Preparamos la información básica para TMDB
        if "Series" in scrapedtype or "Documentales" in scrapedtype:
            item_local.action = "episodios"
            if "Series" in scrapedtype:
                item_local.extra = "series"
            else:
                item_local.extra = "documentales"
            item_local.contentType = "season"
            
            title = re.sub(r'\[\d+.*?\]', '', title)                # Quitar la calidad del título
            item_local.contentSerieName = scrapertools.find_single_match(title, '(.*?) Temporada\s?(?:\d+)?\s?').strip()
            if not item_local.contentSerieName:
                item_local.contentSerieName = title.strip()
            if item_local.infoLabels['title']:
                del item_local.infoLabels['title']
            title = item_local.contentSerieName
            item_local.title = title
            if not item_local.contentSerieName:
                item_local.contentSerieName = "SIN TITULO"
            item_local.contentSeason = scrapertools.find_single_match(scrapedurl, 'temporada-?(?:\d+p-)?(\d{1,2})[-|\/]')
            if not item_local.contentSeason:
                item_local.contentSeason = 1
                title = title.replace('Temporada', '').replace('temporada', '')
        
        if not scrapertools.find_single_match(title, '[\[|\(](.*?)[\)|\]]') in item_local.quality:
            if item_local.quality:
                item_local.quality += ' '
            item_local.quality += scrapertools.find_single_match(title, '[\[|\(](.*?)[\)|\]]')
            if scrapertools.find_single_match(title, '[\[|\(].*?[\)|\]]\s?[\[|\(](.*?)[\)|\]]') and not scrapertools.find_single_match(title, '[\[|\(].*?[\)|\]]\s?[\[|\(](.*?)[\)|\]]') in item_local.quality:
                item_local.quality += ' %s' % scrapertools.find_single_match(title, '[\[|\(].*?[\)|\]]\s?[\[|\(](.*?)[\)|\]]')
        title = re.sub(r'[\[|\(].*?[\)|\]]\s?[\[|\(].*?[\)|\]]', '', title)
        title = re.sub(r'[\[|\(].*?[\)|\]]', '', title)
        if "(hdrip" in title.lower() or "(br" in title.lower() or "(vhsrip" in title.lower() or "(dvdrip" in title.lower() or "(fullb" in title.lower() or "(blu" in title.lower() or "(4k" in title.lower() or "(hevc" in title.lower() or "(imax" in title.lower() or "extendida" in title.lower() or "[720p]" in title.lower()  or "[1080p]" in title.lower():
            title = re.sub(r'\(.*?\)?\(.*?\)', '', title)
            title = re.sub(r'[\[|\(].*?[\)|\]]', '', title)
        if not item_local.quality:
            if "fullbluray" in title.lower():
                item_local.quality = "FullBluRay"
                title = title.replace("FullBluRay", "").replace("fullbluray", "")
            if "4k" in title.lower() or "hdr" in title.lower():
                item_local.quality = "4K"
                title = title.replace("4k-hdr", "").replace("4K-HDR", "").replace("hdr", "").replace("HDR", "").replace("4k", "").replace("4K", "")
        title = title.replace("(", "").replace(")", "").replace("[", "").replace("]", "").strip()
        item_local.title = title
        item_local.from_title = title                       #Guardamos esta etiqueta para posible desambiguación de título
        
        if "Peliculas" in scrapedtype or "Variados" in scrapedtype:
            item_local.action = "findvideos"
            item_local.extra = "peliculas"
            item_local.contentType = "movie"
            item_local.contentTitle = title
            if "Variados" in scrapedtype:
                item_local.extra = "varios"
        
        if "saga" in item_local.contentTitle.lower() or "saga" in item_local.contentSerieName.lower():
            item_local.contentTitle = item_local.contentTitle.replace("Saga ", "").replace("Saga", "")
            item_local.contentSerieName = item_local.contentSerieName.replace("Saga ", "").replace("Saga", "")
            title_subs += ["Saga"]
        if "colecc" in item_local.contentTitle.lower() or "colecc" in item_local.contentSerieName.lower():
            item_local.contentTitle = item_local.contentTitle.replace("Coleccion ", "").replace("Coleccion", "")
            item_local.contentSerieName = item_local.contentSerieName.replace("Coleccion ", "").replace("Coleccion", "")
            title_subs += ["Coleccion"]

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
        
    #if not category:            #Si este campo no existe es que viene de la primera pasada de una búsqueda global
    #    return itemlist         #Retornamos sin pasar por la fase de maquillaje para ahorra tiempo

    #Llamamos a TMDB para que complete InfoLabels desde itemlist.  Mejor desde itemlist porque envía las queries en paralelo
    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    
    #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
    item, itemlist = generictools.post_tmdb_listado(item, itemlist)
         
    if url_next_page:
        title_foot = str(curr_page_num)
        if last_page > 0:
            title_foot += ' de %s' % str(last_page)
        itemlist.append(
            Item(channel=item.channel, action="listado_busqueda", title="[COLOR gold][B]Pagina siguiente >> [/B][/COLOR]" + title_foot, url=url_next_page, extra=item.extra))

    return itemlist

    
def findvideos(item):
    logger.info()
    itemlist = []
    itemlist_t = []                                                 #Itemlist total de enlaces
    itemlist_f = []                                                 #Itemlist de enlaces filtrados
    if not item.language:
        item.language = ['CAST']                                    #Castellano por defecto
    matches = []

    #logger.debug(item)

    data = ''
    torrent_data = ''
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Referer': item.url}    #Necesario para el Post del .Torrent

    #Llamamos al método para crear el título general del vídeo, con toda la información obtenida de TMDB
    item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)
    
    #Si es un lookup para cargar las urls de emergencia en la Videoteca...
    if item.videolibray_emergency_urls:
        item.emergency_urls = []
        item.emergency_urls.append([])                              #Reservamos el espacio para los .torrents locales
    
    #Bajamos los datos de la página de todo menos de Documentales y Varios
    try:
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url, timeout=timeout).data)
        data = js2py_conversion(data, item.url)
        data = data.replace('"', "'")
    except:
        pass    
    if not item.post:
        patron = "<form (?:.*?)?"
        patron += "name='episodios'.+action='([^']+)' method='post'>.*?"
        patron += "<input\s*type='[^']+'\s*name='([^']+)'\s*value='([^']+)'>\s*<input\s*type='[^']+'\s*value='([^']+)'\s*name='([^']+)'>(?:\s*<input\s*type='[^']+'\s*value='([^']+)'\s*name='([^']+)'\s*id='([^']+)'>)?"

        if not data:
            logger.error("ERROR 01: FINDVIDEOS: La Web no responde o la URL es erronea: " + item.url + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: FINDVIDEOS:.  La Web no responde o la URL es erronea. Si la Web está activa, reportar el error con el log', folder=False))
            if item.emergency_urls and not item.videolibray_emergency_urls:         #Hay urls de emergencia?
                matches = item.emergency_urls[1]                                    #Restauramos matches
                item.armagedon = True                                               #Marcamos la situación como catastrófica 
            else:
                if item.videolibray_emergency_urls:         #Si es llamado desde creación de Videoteca...
                    return item                                                     #Devolvemos el Item de la llamada
                else:
                    return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

        if not item.armagedon:                                                      #Si es un proceso normal, seguimos
            matches = re.compile(patron, re.DOTALL).findall(data)
        if not matches:
            item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
            if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
                item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)  #Llamamos al método para el pintado del error
            else:
                logger.error("ERROR 02: FINDVIDEOS: El archivo Torrent no existe o ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
                itemlist.append(item.clone(action='', title=item.category + ': ERROR 02: FINDVIDEOS: El archivo Torrent no existe o ha cambiado la estructura de la Web.  Verificar en la Web y reportar el error con el log', folder=False))
                
            if item.emergency_urls and not item.videolibray_emergency_urls:         #Hay urls de emergencia?
                matches = item.emergency_urls[1]                                    #Restauramos matches
                item.armagedon = True                                               #Marcamos la situación como catastrófica 
            else:
                if item.videolibray_emergency_urls:                                 #Si es llamado desde creación de Videoteca...
                    return item                                                     #Devolvemos el Item de la llamada
                else:
                    return itemlist                                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
        
        #logger.debug("PATRON: " + patron)
        #logger.debug(matches)
        #logger.debug(data)

        #Si es un lookup para cargar las urls de emergencia en la Videoteca...
        if item.videolibray_emergency_urls:
            item.emergency_urls.append(matches)                                 #Salvamnos matches...
        
        for scrapedurl, name1, value1, value2, name2, value3, name3, id3 in matches: #Hacemos el FOR aunque solo habrá un item
            url = scrapedurl

            # Localiza el .torrent en el siguiente link con Post
            post = '%s=%s&%s=%s' % (name1, value1, name2, value2)
            #post = '%s=%s&%s=%s&%s=%s' % (name1, value1, name2, value2, name3, value3)
            if not item.armagedon:
                try:
                    torrent_data = httptools.downloadpage(url, post=post, headers=headers, follow_redirects=False)
                except:                                                         #error
                    pass
                    
    else:
        #Viene de SERIES y DOCUMENTALES. Generamos una copia de Item para trabajar sobre ella
        try:                     #Localiza el .torrent en el siguiente link con Post.  Viene de Documentales y Varios
            url = item.url_post
            del item.url_post
            post = item.post
            torrent_data = httptools.downloadpage(url, post=post, headers=headers, follow_redirects=False)
        except:
            pass

    if not torrent_data and not ('location' in torrent_data.headers or 'zip' in torrent_data.headers):
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)  #Llamamos al método para el pintado del error
        elif not item.armagedon:
            logger.error("ERROR 02: FINDVIDEOS: El archivo Torrent no existe o ha cambiado la estructura de la Web " + " / URL: " + url + " / POST: " + post + " / DATA: " + str(torrent_data.headers))
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: FINDVIDEOS: El archivo Torrent no existe o ha cambiado la estructura de la Web.  Verificar en la Web y reportar el error con el log', folder=False))
            
        if item.emergency_urls and not item.videolibray_emergency_urls:         #Hay urls de emergencia?
            item.url = item.emergency_urls[0][0]                                #Restauramos la url del .torrent
            item.armagedon = True                                               #Marcamos la situación como catastrófica 
        else:
            if item.videolibray_emergency_urls:                                 #Si es llamado desde creación de Videoteca...
                return item                                                     #Devolvemos el Item de la llamada
            else:
                return itemlist                             #si no hay más datos, algo no funciona, pintamos lo que tenemos
    
    #Si el torrent viene en un .zip en vez de desde una url, lo preparamos todo para el play
    referer_zip = None
    post_zip = None
    if 'location' not in torrent_data.headers and 'zip' in torrent_data.headers['content-type'] and not item.armagedon:
        item.referer = item.url
        referer_zip = item.referer
        item.url = url
        item.post = post
        post_zip = item.post
    
    #Generamos una copia de Item para trabajar sobre ella
    item_local = item.clone()
    
    #Capturamos la url del .torrent desde el Header
    if not item.armagedon:
        item_local.url = torrent_data.headers['location'] if 'location' in torrent_data.headers else item.url
        item_local.url = item_local.url.replace(" ", "%20")                     #Quitamos espacios
        if item.emergency_urls:
            item_local.torrent_alt = item.emergency_urls[0][0]                  #Guardamos la url del .Torrent ALTERNATIVA
    
    #Si es un lookup para cargar las urls de emergencia en la Videoteca...
    if item.videolibray_emergency_urls:
        if 'location' in torrent_data.headers or config.get_setting("emergency_urls_torrents", item_local.channel):
            item.emergency_urls[0].append(item_local.url)                       #Salvamnos la url...
        elif not config.get_setting("emergency_urls_torrents", item_local.channel):
            item.emergency_urls[0].append(item_local.referer)                   #Salvamnos el referer...
        return item                                                             #... y nos vamos
        
    # Poner la calidad, si es necesario
    if not item_local.quality:
        item_local.quality = ''
        if scrapertools.find_single_match(data, '<b>Formato:<\/b>&\w+;\s?([^<]+)<br>'):
            item_local.quality = scrapertools.find_single_match(data, '<b>Formato:<\/b>&\w+;\s?([^<]+)<br>')
        elif "hdtv" in item_local.url.lower() or "720p" in item_local.url.lower() or "1080p" in item_local.url.lower() or "4k" in item_local.url.lower():
            item_local.quality = scrapertools.find_single_match(item_local.url, '.*?_([H|7|1|4].*?)\.torrent')
        item_local.quality = item_local.quality.replace("_", " ")
    if item.armagedon:                                                          #Si es catastrófico, lo marcamos
        item_local.quality = '[/COLOR][COLOR hotpink][E] [COLOR limegreen]%s' % item_local.quality
    
    # Extrae el tamaño del vídeo
    if scrapertools.find_single_match(data, '<b>Tama.*?:<\/b>&\w+;\s?([^<]+B)<?'):
        size = scrapertools.find_single_match(data, '<b>Tama.*?:<\/b>&\w+;\s?([^<]+B)<?')
    else:
        size  = scrapertools.find_single_match(item_local.url, '(\d{1,3},\d{1,2}?\w+)\.torrent')
    size = size.replace('GB', 'G·B').replace('Gb', 'G·b').replace('MB', 'M·B')\
                        .replace('Mb', 'M·b').replace('.', ',')
    if not item.armagedon:
        size = generictools.get_torrent_size(item_local.url, referer_zip, post_zip) #Buscamos el tamaño en el .torrent
    if size:
        item_local.title = re.sub('\s\[\d+,?\d*?\s\w[b|B]\]', '', item_local.title) #Quitamos size de título, si lo traía
        item_local.quality = re.sub('\s\[\d+,?\d*?\s\w[b|B]\]', '', item_local.quality) #Quitamos size de calidad, si lo traía
        item_local.torrent_info = '%s' % size                                               #Agregamos size
        if not item.unify:
            item_local.torrent_info = '[%s]' % item_local.torrent_info.strip().strip(',')
 
    # Si tiene un archivo RAR, busca la contraseña
    if 'RAR-' in item_local.torrent_info and not item_local.password:
        if not item_local.password:
            item_local = generictools.find_rar_password(item_local)
        if item_local.password:
            item.password = item_local.password
            itemlist.append(item.clone(action="", title="[COLOR magenta][B] Contraseña: [/B][/COLOR]'" 
                    + item_local.password + "'", folder=False))
    
    #Ahora pintamos el link del Torrent, si lo hay
    if item_local.url:		# Hay Torrent ?
        item_local.title = '[[COLOR yellow]?[/COLOR]] [COLOR yellow][Torrent][/COLOR] ' \
                        + '[COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR] %s' % \
                        (item_local.quality, str(item_local.language),  \
                        item_local.torrent_info)                                        #Preparamos título de Torrent
        
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

    #logger.debug("title=[" + item.title + "], torrent=[ " + item_local.url + " ], url=[ " + url + " ], post=[" + item.post + "], thumbnail=[ " + item.thumbnail + " ]" + " size: " + size)
    
    #logger.debug(item_local)

    if len(itemlist_f) > 0:                                                         #Si hay entradas filtradas...
        itemlist.extend(itemlist_f)                                                 #Pintamos pantalla filtrada
    else:                                                                       
        if config.get_setting('filter_languages', channel) > 0 and len(itemlist_t) > 0: #Si no hay entradas filtradas ...
            thumb_separador = get_thumb("next.png")                                 #... pintamos todo con aviso
            itemlist.append(Item(channel=item.channel, url=host, title="[COLOR red][B]NO hay elementos con el idioma seleccionado[/B][/COLOR]", thumbnail=thumb_separador, folder=False))
        itemlist.extend(itemlist_t)                                     #Pintar pantalla con todo si no hay filtrado

    # Requerido para AutoPlay
    autoplay.start(itemlist, item)                                                  #Lanzamos Autoplay
    
    return itemlist
 

def episodios(item):
    logger.info()
    itemlist = []

    # Obtener la información actualizada de la Serie.  TMDB es imprescindible para Videoteca
    #if not item.infoLabels['tmdb_id']:
    try:
        tmdb.set_infoLabels(item, True)                                             #TMDB de cada Temp
    except:
        pass

    # Carga la página
    data_ini = ''

    try:
        data_ini = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url, timeout=timeout).data)
        data_ini = js2py_conversion(data_ini, item.url)
        data_ini = data_ini.replace('"', "'")
    except:                                                                     #Algún error de proceso, salimos
        logger.error(traceback.format_exc())
        pass
        
    if not data_ini:
        logger.error("ERROR 01: EPISODIOS: La Web no responde o la URL es erronea" + item.url)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: EPISODIOS:.  La Web no responde o la URL es erronea. Si la Web está activa, reportar el error con el log'))
        return itemlist
    
    # Selecciona en tramo que nos interesa
    data = scrapertools.find_single_match(data_ini, "(<form (?:style='[^']+'\s)?name='episodios' action='[^']+' method='post'>.*?)<\/form>")
    
    # Prepara el patrón de búsqueda
    patron = "<form (?:style='[^']+'\s)?name='episodios' action='([^']+)'"
    url = scrapertools.find_single_match(data, patron)                          #Salvamos la url de descarga
    # Para SERIES: ESTA DESCARGARÍA EL TORRENT EN VEZ DEL ENLACE. Se copia MANULAMENTE la url.php de DOCUMENTALES
    #url = url.replace('descargar_tv.php', 'post_dd.php')
    patron = "<form (?:style='[^']+'\s)?name='episodios' action='[^']+'.*?<input type='hidden' value='([^']+)' name='([^']+)'>"
    value2 = ''                                                                 #Patrón general para Documentales (1)
    name2 = ''
    if scrapertools.find_single_match(data, patron):
        value2, name2 = scrapertools.find_single_match(data, patron)            #extraemos valores para el Post
    
    patron = "<td bgcolor='[^>]+><a href='([^']+)'>([^<]+)<\/a><\/td><td[^>]+><div[^>]+>[^<]+?<\/div><\/td>.*?<input type='\w+'\s?name='([^']+)'\s?value='([^']+)'>\s?<\/td><\/tr>"              #Patrón para series con Post
    if not scrapertools.find_single_match(data, patron):
        patron = "<form name='episodios' action='([^']+)'(.*?)<input type='\w+' name='([^']+)' value='([^']+)'>"
        if not scrapertools.find_single_match(data, patron):                    #Patrón para documentales (2)
            #Si no han funcionado los anteriores, usamos el tradicional para series sin Post
            patron = "<td bgcolor='[^>]+><a href='([^']+)'>([^<]+)<\/a><\/td><td[^>]+><div([^>]+)>([^<]+)?<\/div><\/td>"
    
    matches = re.compile(patron, re.DOTALL).findall(data)
    if not matches:                                                             #error
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            item, itemlist = generictools.post_tmdb_episodios(item, itemlist)   #Llamamos al método para el pintado del error
            return itemlist                                                     #Salimos
        
        logger.error("ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA_INI: " + data_ini + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
        return itemlist                                 #si no hay más datos, algo no funciona, pintamos lo que tenemos

    #logger.debug("PATRON: " + patron)
    #logger.debug(matches)
    #logger.debug(data)

    # Recorremos todos los episodios generando un Item local por cada uno en Itemlist
    for scrapedurl, title, name1, value1 in matches:
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
        
        item_local.title = ''
        item_local.context = "['buscar_trailer']"
        item_local.url = scrapedurl
        
        if name1 and value1:                                                #llamada con post
            item_local.url = item.url                                       #Dejamos la url de la Temporada como Refer
            item_local.url_post = url                                       #Ponemos la url de Descarga (retocado)
            item_local.post = '%s=%s' % (name1, value1)                     #Ponemos la primera pareja de valores
            if not name2 and not value2 and item.extra != "series":         #Si no hay segunda pareja...
                item_local.post = '%s=0&id_post=%s' % (name1, value1)       #... adaptamos el formato final
        if name2 and value2:                                                #Si hay segunda pareja, la añadimos
            if item_local.post:
                item_local.post += '&'
            item_local.post += '%s=%s' % (name2, value2)

        scrapedtemp = ''
        scrapedepi = ''
        if scrapertools.find_single_match(scrapedurl, "\/.*?-(\d{1,2})x(\d{1,2})[-|\/]"):
            scrapedtemp, scrapedepi = scrapertools.find_single_match(scrapedurl, "\/.*?-(\d{1,2})x(\d{1,2})[-|\/]")
        scrapedepi2 = scrapertools.find_single_match(scrapedurl, "\/.*?-\d{1,2}x\d{1,2}-al-\d{1,2}x(\d{1,2})[-|\/]")
        try:
            item_local.contentSeason = int(scrapedtemp)
        except:
            item_local.contentSeason = 1
        try:
            item_local.contentEpisodeNumber = int(scrapedepi)
        except:
            item_local.contentEpisodeNumber = 1
        try:
            scrapedepi2 = int(scrapedepi2)
        except:
            scrapedepi2 = ''
            
        if scrapedepi2:
            item_local.title = '%sx%s al %s -' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber).zfill(2), str(scrapedepi2).zfill(2))
            #item_local.infoLabels['episodio_titulo'] = 'al %s' % scrapedepi2
        else:
            item_local.title = '%sx%s -' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber).zfill(2))
            
        # Buscamos si tiene contraseña y la guardamos:
        passw = scrapertools.find_single_match(title, "(?:CONTRASE|contrase|Contrase)[^:]+:\s*(.*?)$")
        if passw:
            item_local.password = passw

        itemlist.append(item_local.clone())
        
    if len(itemlist) > 1:
        itemlist = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))     #clasificamos

    # Pasada por TMDB y clasificación de lista por temporada y episodio
    tmdb.set_infoLabels(itemlist, True)

    #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
    item, itemlist = generictools.post_tmdb_episodios(item, itemlist)

    return itemlist
    
    
def lookup_idiomas_paginacion(item, url, title, calidad, list_language):
    logger.info()
    estado = True
    item.language = []
    itemlist = []
    
    if "[subs" in title.lower() or "[vos" in title.lower()  or "v.o.s" in title.lower() or "vo" in title.lower():
        item.language += ["VOS"]

    if "latino" in title.lower() or "argentina" in title.lower():
        item.language += ["LAT"]

    if item.language == []:
        item.language = ['CAST']                                #Por defecto

    #Ahora se filtra por idioma, si procede, y se pinta lo que vale.  Excluye categorías en otros idiomas.
    if config.get_setting('filter_languages', channel) > 0:
        itemlist = filtertools.get_link(itemlist, item, list_language)
        
        if len(itemlist) == 0:
            estado = False

    #Volvemos a la siguiente acción en el canal
    return estado

    
def actualizar_titulos(item):
    logger.info()
    
    item = generictools.update_title(item) #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels
    
    #Volvemos a la siguiente acción en el canal
    return item
    

def js2py_conversion(data, url, post=None, follow_redirects=True, headers={}):
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
    itemlist = []
    logger.info("search:" + texto)
    texto = texto.replace(" ", "+")

    item.url = host + "search/%s/page/1/" % (texto)
    
    try:
        itemlist = listado_busqueda(item)
        return itemlist

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
        

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host + "peliculas/"
            item.extra = "peliculas"
            item.channel = "mejortorrent1"
            item.category_new= 'newest'
            item.tipo = False
            itemlist = listado(item)
            if "Pagina siguiente >>" in itemlist[-1].title:
                itemlist.pop()

        if categoria == 'documentales':
            item.url = host + "documentales/"
            item.extra = "documentales"
            item.channel = "mejortorrent1"
            item.category_new= 'newest'
            item.tipo = False
            itemlist = listado(item)
            if "Pagina siguiente >>" in itemlist[-1].title:
                itemlist.pop()
    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
