# -*- coding: utf-8 -*-

import re
import sys
import urllib
import urlparse
import time
import traceback

from channelselector import get_thumb
from core import httptools, proxytools
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

channel = "mejortorrent"

host = 'http://www.mejortorrentt.org/'
host_sufix = '.org'
#host = config.get_setting('domain_name', channel)

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
    #                     url= host + "secciones.php?sec=ultimos_torrents", thumbnail=thumb_buscar))
    itemlist.append(Item(channel=item.channel, title="Peliculas", action="listado", extra="peliculas", tipo=False,
                         url= host + "torrents-de-peliculas.html", thumbnail=thumb_pelis))
    itemlist.append(Item(channel=item.channel, title="Peliculas HD", action="listado", extra="peliculas", tipo=False,
                         url= host + "torrents-de-peliculas-hd-alta-definicion.html",
                         thumbnail=thumb_pelis_hd))
    itemlist.append(Item(channel=item.channel, title="Películas Listado Alfabetico", action="alfabeto",
                         url= host + "peliculas-buscador.html" +
                         "?campo=letra&valor=&valor2=Acci%C3%B3n&valor3=XXX&valor4=3&submit=Buscar", extra="peliculas", 
                         thumbnail=thumb_pelis))
    itemlist.append(Item(channel=item.channel, title="Series", action="listado", extra="series", tipo=False,
                         url= host + "torrents-de-series.html", thumbnail=thumb_series))
    itemlist.append(Item(channel=item.channel, title="Series Listado Alfabetico", action="alfabeto", extra="series",
                         url= host + "torrents-de-series.html", thumbnail=thumb_series_az))
    itemlist.append(Item(channel=item.channel, title="Series HD", action="listado", extra="series", tipo=False,
                         url= host + "torrents-de-series-hd-alta-definicion.html",
                         thumbnail=thumb_series_hd))
    itemlist.append(Item(channel=item.channel, title="Series HD Listado Alfabetico", action="alfabeto", extra="series-hd",
                         url= host + "torrents-de-series-hd-alta-definicion.html", thumbnail=thumb_series_az))
    itemlist.append(Item(channel=item.channel, title="Documentales", action="listado", extra="documentales", tipo=False,
                         url= host + "torrents-de-documentales.html", thumbnail=thumb_docus))
    itemlist.append(Item(channel=item.channel, title="Documentales Listado Alfabetico", action="alfabeto", extra="documentales", url= host + "torrents-de-documentales.html", thumbnail=thumb_docus))
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


def alfabeto(item):
    logger.info()
    itemlist = []

    if item.extra == "series-hd":
        itemlist.append(Item(channel=item.channel, action="listado", title="Todas",  extra="series", tipo=True, 
                             url= host + "secciones.php?sec=descargas&ap=series_hd&func=mostrar&letra=."))
        for letra in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']:
            itemlist.append(Item(channel=item.channel, action="listado", title=letra, extra="series", tipo=True,
                             url= host + "secciones.php?sec=descargas&ap=series_hd&func=mostrar&letra=" + letra))

    elif item.extra == "series" or item.extra == "documentales":
        itemlist.append(Item(channel=item.channel, action="listado", title="Todas", extra=item.extra, tipo=True, url= host + "/" + item.extra + "-letra-..html"))
        for letra in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']:
            itemlist.append(Item(channel=item.channel, action="listado", title=letra, extra=item.extra, tipo=True, url= host + "/" + item.extra + "-letra-" + letra.lower() + ".html"))

    elif item.extra == "peliculas":
        itemlist.append(Item(channel=item.channel, action="listado", title="Todas", extra=item.extra, tipo=True, url=item.url.replace('XXX', '.'), headers={'Referer': 'http://www.mejortorrentt.org/torrents-de-peliculas.html'}))
        for letra in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']:
            itemlist.append(Item(channel=item.channel, action="listado", title=letra, extra=item.extra, tipo=True, url=item.url.replace('XXX', letra), headers={'Referer': 'http://www.mejortorrentt.org/torrents-de-peliculas.html'}))

    return itemlist

def listado(item):
    logger.info()
    itemlist = []
    url_next_page =''       # Control de paginación
    cnt_tot = 30            # Poner el num. máximo de items por página
    
    if item.category:
        del item.category
    if item.totalItems:
        del item.totalItems
    
    try:
        data = ''
        # La url de Películas por orden Alfabético tiene un formato distinto
        if item.extra == "peliculas" and item.tipo:
            headers={}
            if item.headers: headers=item.headers
            url = item.url.split("?")
            data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(url[0], post=url[1], headers=headers).data)
        else:
            data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)
    except:
            logger.error(traceback.format_exc())
            logger.error("ERROR 01: LISTADO: La Web no responde o ha cambiado de URL: " + item.url + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: LISTADO:.  La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
            return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
    if not data:        #Si la web está caída salimos sin dar error
            logger.error("ERROR 01: LISTADO: La Web no responde o ha cambiado de URL: " + item.url + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: LISTADO:.  La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
            return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
    
    # En este canal las url's y los títulos tienen diferente formato dependiendo del contenido
    if item.extra == "peliculas" and item.tipo:     #Desde Lista Alfabética
        patron = "<a href='((?:[^']+)?/peli-descargar-torrent[^']+)'()"
        patron_enlace = "/peli-descargar-torrent-\d+-(.*?)\.html"
        patron_title = "<a href='(?:[^']+)?/peli-descargar-torrent[^']+'[^>]+>([^>]+)</a>(\s*<b>([^>]+)</b>)?"
        item.action = "findvideos"
        item.contentType = "movie"
        pag = False                                 #No hay paginación
    elif item.extra == "peliculas" and not item.tipo:       #Desde Menú principal
        patron = '<a href="((?:[^"]+)?/peli-descargar-torrent[^"]+)">?'
        patron += '<img src="([^"]+)"[^<]+</a>'
        patron_enlace = "/peli-descargar-torrent-\d+-(.*?)\.html"
        patron_title = '<a href="(?:[^"]+)?/peli-descargar-torrent[^"]+">([^<]+)</a>(\s*<b>([^>]+)</b>)?'
        item.action = "findvideos"
        item.contentType = "movie"
        pag = True                                  #Sí hay paginación
        cnt_tot = 15            # Poner el num. máximo de items por página.  Parece que hay 50
    elif item.extra == "series" and item.tipo:
        patron = "<a href='((?:[^']+)?/serie-descargar-torrent[^']+)'>()"
        patron_enlace = "\/serie-descargar-torrent*.-\d+-?\d+-(.*?)\.html"
        patron_title = "<a href='(?:[^']+)?\/serie-descargar-torrent[^']+'>([^<]+)<\/a>(\s*<b>([^>]+)<\/b>)?"
        patron_title_ep = "\/serie-descargar-torrent*.-\d+-?\d+-(.*?)-\d+x\d+.*?\.html"
        patron_title_se = "\/serie-descargar-torrent*.-\d+-?\d+-(.*?)-\d+-Temp.*?\.html"
        item.action = "episodios"
        item.contentType = "season"
        pag = False
    elif item.extra == "series" and not item.tipo:
        patron = '<a href="((?:[^"]+)?\/serie-[^a_z]{0,10}descargar-torrent[^"]+)">?'
        patron += '<img src="([^"]+)"[^<]+</a>'
        patron_enlace = "\/serie-[^a_z]{0,10}descargar-torrent*.-\d+-?\d+-(.*?)\.html"
        patron_title = '<a href="(?:[^"]+)?/serie-[^a_z]{0,10}descargar-torrent[^"]+">([^<]+)</a>(\s*<b>([^>]+)</b>)?'
        patron_title_ep = "\/serie-[^a_z]{0,10}descargar-torrent*.-\d+-?\d+-(.*?)-\d+x\d+.*?\.html"
        patron_title_se = "\/serie-[^a_z]{0,10}descargar-torrent*.-\d+-?\d+-(.*?)-\d+-Temp.*?\.html"
        item.action = "episodios"
        item.contentType = "season"
        pag = True
        cnt_tot = 10        # Se reduce el numero de items por página porque es un proceso pesado
    elif item.extra == "documentales" and item.tipo:
        patron = "<a href='((?:[^']+)?/doc-descargar-torrent[^']+)'>()"
        patron_enlace = "\/doc-descargar-torrent*.-\d+-?\d+-(.*?)\.html"
        patron_title = "<a href='(?:[^']+)?\/doc-descargar-torrent[^']+'>([^<]+)<\/a>(\s*<b>([^>]+)<\/b>)?"
        patron_title_ep = "\/doc-descargar-torrent*.-\d+-?\d+-(.*?)-\d+x\d+.*?\.html"
        patron_title_se = "\/doc-descargar-torrent*.-\d+-?\d+-(.*?)-\d+-Temp.*?\.html"
        item.action = "episodios"
        item.contentType = "movie"
        pag = False
    else:
        patron = '<a href="((?:[^"]+)?/doc-descargar-torrent[^"]+)">?'
        patron += '<img src="([^"]+)"[^<]+</a>'
        patron_enlace = "/doc-descargar-torrent-\d+-\d+-(.*?)\.html"
        patron_title = '<a href="(?:[^"]+)?/doc-descargar-torrent[^"]+">([^<]+)</a>(\s*<b>([^>]+)</b>)?'
        patron_title_ep = "\/doc-descargar-torrent*.-\d+-?\d+-(.*?)-\d+x\d+.*?\.html"
        patron_title_se = "\/doc-descargar-torrent*.-\d+-?\d+-(.*?)-\d+-Temp.*?\.html"
        item.action = "episodios"
        item.contentType = "movie"
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
    if not matches and not 'Se han encontrado <b>0</b> resultados.' in data:    #error
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            item, itemlist = generictools.post_tmdb_listado(item, itemlist)     #Llamamos al método para el pintado del error
            return itemlist                                                     #Salimos
        
        logger.error("ERROR 02: LISTADO: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: LISTADO: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

    #Capturamos el num. de la última página para informala a pié de página.  Opción para páginas sin paginación
    if pag == False:
        item.last_page = (len(matches) / cnt_tot) + 1
    
    if not item.last_page and pag:    #Capturamos el num. de la última página para informala a pié de página
        item.last_page = -1
        patron_next_page = "<a href='([^']+)' class='paginar'> Siguiente >> <\/a>"
        url_next_page = urlparse.urljoin(item.url, scrapertools.find_single_match(data, patron_next_page))
        url_last_page = re.sub(r"\d+$", "9999", url_next_page)
        data_last = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(url_last_page).data)
        patron_last_page = "<span class='nopaginar'>(\d+)<\/span>"
        try:
            if item.extra == "documentales":
                item.last_page = int(scrapertools.find_single_match(data_last, patron_last_page))
            else:
                item.last_page = int(scrapertools.find_single_match(data_last, patron_last_page)) * (len(matches) / cnt_tot)
        except:
            item.last_page = 1

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
        patron_next_page = "<a href='([^']+)' class='paginar'> Siguiente >> <\/a>"
        matches_next_page = re.compile(patron_next_page, re.DOTALL).findall(data)
        modo = 'continue'
        if len(matches_next_page) > 0:
            url_next_page = urlparse.urljoin(item.url, matches_next_page[0])
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
        if item_local.last_page:
            del item_local.last_page
        if item_local.cnt_pag_num:
            del item_local.cnt_pag_num
        if item_local.headers:
            del item_local.headers
            
        item_local.title = ''
        item_local.context = "['buscar_trailer']"

        item_local.title = scrapertools.find_single_match(scrapedurl, patron_enlace)
        item_local.title = item_local.title.replace("-", " ")
        item_local.url = verificar_url(urlparse.urljoin(item_local.url, scrapedurl)).replace(' ', '%20')
        item_local.thumbnail = verificar_url(urlparse.urljoin(host, scrapedthumbnail)).replace(' ', '%20')
        item_local.contentThumbnail = item_local.thumbnail
        item_local.infoLabels['year'] = '-'  # Al no saber el año, le ponemos "-" y TmDB lo calcula automáticamente
        
        # Para que el menú contextual muestre conrrectamente las opciones de añadir a Videoteca
        if item_local.extra == "series":
            if "/serie-episodio" in item_local.url:
                item_local.contentType = "episode"
            else:
                item_local.contentType = "season"
            
        # Poner nombre real de serie.  Busca nº de temporada y capítulo
        if item_local.extra == "series" or item.extra == "documentales":
            if item_local.contentType == "episode":
                real_title = scrapertools.find_single_match(scrapedurl, patron_title_ep)
                real_title = real_title.replace("-", " ")
                item_local.contentSeason = scrapertools.find_single_match(scrapedurl, '.*?-(\d{1,2})x\d{1,2}.*?\.html')
                
                #Hay que buscar la raiz de la temporada
                data_epi = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item_local.url).data)
                url = scrapertools.find_single_match(data_epi, r"<a href='.*?(\/serie-descargar-torrents.*?\.html)'")
                if not url:
                    url = scrapertools.find_single_match(data_epi, r"<td><a href='(secciones.php\?sec\=descargas&ap=[^']+)'")
                if not url:     #No encuentro la Temporada.  Lo dejo como capítulo suelto
                    logger.debug(item_local)
                    logger.debug(data_epi)
                    item_local.action = "findvideos"
                    item_local.contentEpisodeNumber = scrapertools.find_single_match(scrapedurl, '.*?-\d{1,2}x(\d{1,2}).*?\.html')
                    if not item_local.contentEpisodeNumber:
                        item_local.contentEpisodeNumber = 1
                else:           #Busco la temporada.  Salvo url de episodio por si acaso
                    #item_local.url_ori = item_local.url
                    item_local.url = urlparse.urljoin(host, url)
                    item_local.contentType = "season"
            else:
                real_title = scrapertools.find_single_match(scrapedurl, patron_title_se)
                real_title = real_title.replace("-", " ")
                item_local.contentSeason = scrapertools.find_single_match(scrapedurl, '.*?-(\d{1,2})-Temp.*?\.html')

            item_local.contentSerieName = real_title
            if not item_local.contentSeason:
                item_local.contentSeason = 1
        else:
            item_local.contentTitle = item_local.title
                
        if item_local.contentType == "episode": 
            item_local.title = '%sx%s ' % (item_local.contentSeason, item_local.contentEpisodeNumber)
        
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
    for scrapedtitle, notused, scrapedinfo in matches:
        item_local = itemlist[cnt]  #Vinculamos item_local con la entrada de la lista itemlist (más fácil de leer)
        
        # Limpiamos títulos, Sacamos datos de calidad, audio y lenguaje
        #scrapedtitle = re.sub('\r\n', '', scrapedtitle).decode('iso-8859-1').encode('utf8').strip()
        title = scrapedtitle
        title = title.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ü", "u").replace("ï¿½", "ñ").replace("Ã±", "ñ")

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
        
        if "3d" in title.lower():        #Reservamos info para después de TMDB
            item_local.quality += " 3D"
            title = title.replace(" [3d]", "").replace(" 3d", "").replace(" [3D]", "").replace(" 3D", "")
        #if "temp" in title.lower():        #Reservamos info de Temporada para después de TMDB
        #    title_subs += ["Temporada"]
        if "audio" in title.lower():        #Reservamos info de audio para después de TMDB
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
            
        #info = scrapedinfo.decode('iso-8859-1').encode('utf8')
        info = scrapedinfo
        info = info.replace("(", "").replace(")", "").replace(" ", "")

        # Ahora preparamos el título y la calidad tanto para series como para documentales y películas 
        # scrapedinfo tiene la calidad, pero solo en llamadas desde peliculas sin alfabeto
        if item_local.extra == "series" or item_local.extra == "documentales":
            item_local.quality = scrapertools.find_single_match(scrapedtitle, '.*?[\[|\(](\d+.*?)[\)|\]]')
            if item_local.quality:
                title = re.sub(r'[\[|\(]\d+.*?[\)|\]]', '', title)    # Quitar la calidad del título
            info = ""
            item_local.contentSerieName = scrapertools.find_single_match(title, '(.*?) - \d.*?').strip()
            if not item_local.contentSerieName:
                item_local.contentSerieName = title.strip()
            if item_local.infoLabels['title']:
                del item_local.infoLabels['title']
            if not item_local.contentSerieName:
                item_local.contentSerieName = "SIN TITULO"
        
        if info != "" and not item_local.quality:
            item_local.quality = info
        if "(hdrip" in title.lower() or "(br" in title.lower() or "(vhsrip" in title.lower() or "(dvdrip" in title.lower() or "(fullb" in title.lower() or "(blu" in title.lower() or "(4k" in title.lower() or "4k" in title.lower() or "(hevc" in title.lower() or "(imax" in title.lower() or "extendida" in title.lower() or "[720p]" in title.lower()  or "[1080p]" in title.lower():
            if not item_local.quality:
                item_local.quality = scrapertools.find_single_match(title, r'\(.*?\)?\(.*?\)')
                if not item_local.quality:
                    item_local.quality = scrapertools.find_single_match(title, r'[\[|\(](.*?)[\)|\]]')
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
        if item_local.extra == "peliculas": 
            item_local.title = title
            item_local.contentTitle = title
        elif item_local.contentType != "episode":
            item_local.title = title
            item_local.title = '%s ' % item_local.contentSerieName

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
    url_next_page =''   # Controlde paginación
    cnt_tot = 30        # Poner el num. máximo de items por página
    pag = False         # No hay paginación en la web
    category = ""       # Guarda la categoria que viene desde una busqueda global

    try:
        data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url, post=item.post).data)
    except:
        logger.error("ERROR 01: LISTADO_BUSQUEDA: La Web no responde o ha cambiado de URL: " + item.url + item.post + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: LISTADO_BUSQUEDA:.  La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
    if not data:        #Si la web está caída salimos sin dar error
        logger.error("ERROR 01: LISTADO_BUSQUEDA: La Web no responde o ha cambiado de URL: " + item.url + item.post + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: LISTADO_BUSQUEDA:.  La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

    # busca series y Novedades
    patron = "<a href='((?:[^']+)?\/serie-descargar-torrent[^']+)'[^>]+>(.*?)<\/a>"
    patron += ".*?<span style='color:\w+;'>([^']+)<\/span>"
    patron_enlace = "\/serie-descargar-torrents-\d+-\d+-(.*?)\.html"
    matches = scrapertools.find_multiple_matches(data, patron)
    
    # busca pelis y Novedades
    patron = "<a href='((?:[^']+)?\/peli-descargar-torrent[^']+)'[^>]+>(.*?)<\/a>"
    patron += ".*?<span style='color:\w+;'>([^']+)<\/a>"
    matches += re.compile(patron, re.DOTALL).findall(data)      #Busquedas
    patron = "<a href='((?:[^']+)?\/peli-descargar-torrent[^']+)'[^>]+>(.*?)<\/a>"
    patron += ".*?<span style='color:\w+;'>([^']+)<\/span>"
    patron_enlace = "\/peli-descargar-torrent-\d+(.*?)\.html"
    matches += re.compile(patron, re.DOTALL).findall(data)      #Novedades
    
    # busca docu
    patron = "<a href='((?:[^']+)?\/doc-descargar-torrent[^']+)' .*?"
    patron += "<font Color='\w+'>(.*?)<\/a>.*?"
    patron += "<td align='right' width='20%'>(.*?)<\/td>"
    patron_enlace = "\/doc-descargar-torrent-\d+-\d+-(.*?)\.html"
    matches += re.compile(patron, re.DOTALL).findall(data)
    matches_cnt = len(matches)
    
    if not matches and not 'Se han encontrado <b>0</b> resultados.' and not "href='/juego-descargar-torrent" in data:  #error
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            item, itemlist = generictools.post_tmdb_listado(item, itemlist)     #Llamamos al método para el pintado del error
            return itemlist                                                     #Salimos
        
        logger.error("ERROR 02: LISTADO_BUSQUEDA: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: LISTADO_BUSQUEDA: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

    #logger.debug("MATCHES: ")
    #logger.debug(matches)
    
    # Preparamos la paginación.  Con un número variable de links, sin límite
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
    
    #Capturamos el num. de la última página para informala a pié de página
    last_page = (len(matches) / cnt_tot) + 1

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
        patron_next_page = "<a href='([^']+)' class='paginar'> Siguiente >> <\/a>"
        matches_next_page = re.compile(patron_next_page, re.DOTALL).findall(data)
        modo = 'continue'
        if len(matches_next_page) > 0:
            url_next_page = urlparse.urljoin(item.url, matches_next_page[0])
            modo = 'next'
    if item.next_page:
        del item.next_page
        
    if matches_cnt >= cnt_tot:
        cnt_pag += cnt_tot
    else:
        cnt_pag += matches_cnt
    cnt_pag_num += 1

    for scrapedurl, scrapedtitle, scrapedinfo in matches:
        # Creamos "item_local" y lo limpiamos un poco de algunos restos de item
        item_local = item.clone()
        if item_local.category:
            category = item.category
            del item_local.category
        item_local.tipo = True
        del item_local.tipo
        if item_local.totalItems:
            del item_local.totalItems
        if item_local.text_color:
            del item_local.text_color
        if item_local.cnt_pag_num:
            del item_local.cnt_pag_num
        item_local.contentThumbnail = ''
        item_local.thumbnail = ''
        item_local.title = ''
        item_local.context = "['buscar_trailer']"
        item_local.infoLabels['year'] = '-'  # Al no saber el año, le ponemos "-" y TmDB lo calcula automáticamente
        
        # Limpiamos títulos, Sacamos datos de calidad, audio y lenguaje
        #scrapedtitle = re.sub('\r\n', '', scrapedtitle).decode('iso-8859-1').encode('utf8').strip()
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
        
        if "3d" in title or "3D" in title:        #Reservamos info para después de TMDB
            item_local.quality += " 3D"
            title = title.replace(" [3d]", "").replace(" 3d", "").replace(" [3D]", "").replace(" 3D", "")
        #if "temp" in title.lower():        #Reservamos info de Temporada para después de TMDB
        #    title_subs += ["Temporada"]
        if "audio" in title.lower():        #Reservamos info de audio para después de TMDB
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
        if item.extra == "novedades" and ("/serie-" in scrapedurl or "/doc-" in scrapedurl):
            item_local.quality = scrapertools.find_single_match(scrapedtitle, r'.*?\[(.*?)\]')
        else:
            item_local.quality = scrapertools.remove_htmltags(scrapedinfo).decode('iso-8859-1').encode('utf8')
        item_local.quality = item_local.quality.replace("(", "").replace(")", "").replace("[", "").replace("]", "").replace("Documental", "").replace("documental", "")
        
        item_local.url = verificar_url(urlparse.urljoin(item.url, scrapedurl)).replace(' ', '%20')
        
        #Preparamos la información básica para TMDB
        if "/serie-" in scrapedurl or "/doc-" in scrapedurl:
            item_local.action = "episodios"
            if "/serie-" in scrapedurl:
                item_local.extra = "series"
                item_local.contentType = "season"
            else:
                item_local.extra = "documentales"
                item_local.contentType = "movie"

            title = re.sub(r'\[\d+.*?\]', '', title)    # Quitar la calidad del título
            item_local.contentSerieName = scrapertools.find_single_match(title, '(.*?) - \d.*?').strip()
            if not item_local.contentSerieName:
                item_local.contentSerieName = title.strip()
            if item_local.infoLabels['title']:
                del item_local.infoLabels['title']
            title = item_local.contentSerieName
            item_local.title = title
            if not item_local.contentSerieName:
                item_local.contentSerieName = "SIN TITULO"
            item_local.contentSeason = scrapertools.find_single_match(scrapedurl, '.*?-(\d{1,2})-Temp.*?\.html')
            if not item_local.contentSeason:
                item_local.contentSeason = 1
        
        if "(hdrip" in title.lower() or "(br" in title.lower() or "(vhsrip" in title.lower() or "(dvdrip" in title.lower() or "(fullb" in title.lower() or "(blu" in title.lower() or "(4k" in title.lower() or "4k" in title.lower() or "(hevc" in title.lower() or "(imax" in title.lower() or "extendida" in title.lower() or "[720p]" in title.lower()  or "[1080p]" in title.lower():
            if not item_local.quality:
                item_local.quality = scrapertools.find_single_match(title, r'\(.*?\)?\(.*?\)')
                if not item_local.quality:
                    item_local.quality = scrapertools.find_single_match(title, r'[\[|\(](.*?)[\)|\]]')
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
        
        if "/peli-" in scrapedurl:
            item_local.action = "findvideos"
            item_local.extra = "peliculas"
            item_local.contentType = "movie"
            item_local.contentTitle = title
        
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
        
        #cnt_title = len(itemlist)                                   #Contador de líneas añadidas
        
        #logger.debug(item_local)
        
    #if not category:            #Si este campo no existe es que viene de la primera pasada de una búsqueda global
    #    return itemlist         #Retornamos sin pasar por la fase de maquillaje para ahorra tiempo

    #Llamamos a TMDB para que complete InfoLabels desde itemlist.  Mejor desde itemlist porque envía las queries en paralelo
    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    
    #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
    item, itemlist = generictools.post_tmdb_listado(item, itemlist)
         
    if url_next_page:
        title_foot = str(cnt_pag_num)
        if last_page > 0:
            title_foot += ' de %s' % str(last_page)
        itemlist.append(
            Item(channel=item.channel, action="listado_busqueda", title="[COLOR gold][B]Pagina siguiente >> [/B][/COLOR]" + title_foot, url=url_next_page, next_page=next_page, cnt_pag=cnt_pag, pag=pag, modo=modo, extra=item.extra, cnt_pag_num=cnt_pag_num))
                
    #logger.debug(url_next_page + " / " + next_page + " / " + str(matches_cnt) + " / " + str(cnt_pag)  + " / " + str(pag)  + " / " + modo + " / " + item.extra ))
    
    return itemlist

    
def findvideos(item):
    logger.info()
    itemlist = []
    itemlist_t = []                                     #Itemlist total de enlaces
    itemlist_f = []                                     #Itemlist de enlaces filtrados
    if not item.language:
        item.language = ['CAST']                        #Castellano por defecto
    matches = []

    #Si es un lookup para cargar las urls de emergencia en la Videoteca...
    if item.videolibray_emergency_urls:
        item.emergency_urls = []
        item.emergency_urls.append([])                  #Reservamos el espacio para los .torrents locales
    
    #Bajamos los datos de la página
    data = ''
    try:
        if item.post:   #Puede traer datos para una llamada "post".  De momento usado para documentales, podrían ser series
            headers = {}
            if item.headers:
                headers = item.headers
            data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url, post=item.post, headers=headers).data)
            data = data.replace('"', "'")
            if 'documentales' in item.post:
                patron = "(>\s*Pincha.*?<a\s*href='.*?'\s*onclick='post\('[^']+',\s*\{\s*table:\s*'[^']+',\s*name:\s*'[^']+'}\))"
            else:
                patron = ">\s*Pincha.*?<a href='([^\']+\.torrent)'"
        else:
            data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)
            patron = "<a href='((?:[^']+)?secciones.php\?sec\=descargas&ap=contar&tabla=[^']+)'"
    except:
        pass
        
    if not data:    
        logger.error("ERROR 01: FINDVIDEOS: La Web no responde o la URL es erronea: " + item.url + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: FINDVIDEOS:.  La Web no responde o la URL es erronea. Si la Web está activa, reportar el error con el log', folder=False))
        
        if item.emergency_urls and not item.videolibray_emergency_urls:         #Hay urls de emergencia?
            matches = item.emergency_urls[1]                                    #Restauramos matches
            item.armagedon = True                                               #Marcamos la situación como catastrófica 
        else:
            if item.videolibray_emergency_urls:                                 #Si es llamado desde creación de Videoteca...
                return item                                                     #Devolvemos el Item de la llamada
            else:
                return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
    
    if not item.armagedon:                                                      #Si es un proceso normal, seguimos
        matches = re.compile(patron, re.DOTALL).findall(data)
    if not matches:
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)  #Llamamos al método para el pintado del error
        elif not item.armagedon:
            logger.error("ERROR 02: FINDVIDEOS: El archivo Torrent no existe o ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.category + ': ERROR 02: FINDVIDEOS: El archivo Torrent no existe o ha cambiado la estructura de la Web.  Verificar en la Web y reportar el error con el log, folder=False'))
        
        if item.emergency_urls and not item.videolibray_emergency_urls:         #Hay urls de emergencia?
            matches = item.emergency_urls[1]                                    #Restauramos matches
            item.armagedon = True                                               #Marcamos la situación como catastrófica 
        else:
            if item.videolibray_emergency_urls:                                 #Si es llamado desde creación de Videoteca...
                return item                                                     #Devolvemos el Item de la llamada
            else:
                return itemlist                                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
        
    #logger.debug(data)
    #logger.debug("PATRON: " + patron)
    #logger.debug(matches)
    
    #Si es un lookup para cargar las urls de emergencia en la Videoteca...
    if item.videolibray_emergency_urls:
        item.emergency_urls.append(matches)                                 #Salvamnos matches...

    #Llamamos al método para crear el título general del vídeo, con toda la información obtenida de TMDB
    item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)
    
    for scrapedurl in matches:
        #Generamos una copia de Item para trabajar sobre ella
        item_local = item.clone()
        url = verificar_url(urlparse.urljoin(item.url, scrapedurl))
        #patron_torrent = ">\s*Pincha.*?<a href='([^\']+\.torrent)'"
        patron_torrent = ">\s*Pincha.*?<a\s*href='.*?'\s*onclick=.post\('([^']+)',\s*\{\s*table:\s*'([^']+)',\s*name:\s*'([^']+)'}\)"
        
        # Localiza el .torrent en el siguiente link
        if not item.post and not item.armagedon:                    # Si no es llamada con Post, hay que bajar un nivel más
            try:
                torrent_data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(url).data)
            except:                                                                     #error
                pass
                
            if not torrent_data or not scrapertools.find_single_match(torrent_data, patron_torrent):
                logger.error("ERROR 02: FINDVIDEOS: El archivo Torrent no existe o ha cambiado la estructura de la Web " + " / URL: " + url + " / DATA: " + torrent_data)
                itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: FINDVIDEOS: El archivo Torrent no existe o ha cambiado la estructura de la Web.  Verificar en la Web y reportar el error con el log, folder=False'))
                if item.emergency_urls and not item.videolibray_emergency_urls:         #Hay urls de emergencia?
                    if len(item.emergency_urls[0]):
                        item_local.url = item.emergency_urls[0][0]                      #Restauramos la primera url
                    item.armagedon = True                           #Marcamos la situación como catastrófica 
                else:
                    if item.videolibray_emergency_urls:             #Si es llamado desde creación de Videoteca...
                        return item                                                     #Devolvemos el Item de la llamada
                    else:
                        return itemlist                     #si no hay más datos, algo no funciona, pintamos lo que tenemos
            
            if not item.armagedon:
                url1, url2, url3 = scrapertools.find_single_match(torrent_data, patron_torrent)
                item_local.url = urlparse.urljoin(host, url1)
                item_local.url = '%s/%s/%s' % (item_local.url, url2, url3)
                item_local.url = verificar_url(item_local.url)

        
        elif not item.armagedon:
            item_local.url = url                            # Ya teníamos el link desde el primer nivel (documentales)
            if 'documentales' in item.post:                 # Si es un documental, se trata como una película
                url1, url2, url3 = scrapertools.find_single_match(scrapedurl, patron_torrent)
                item_local.url = urlparse.urljoin(host, url1)
                item_local.url = '%s/%s/%s' % (item_local.url, url2, url3)
                item_local.url = verificar_url(item_local.url)
        item_local.url = item_local.url.replace(" ", "%20")
        
        if item.armagedon and item.emergency_urls and not item.videolibray_emergency_urls:
            if len(item.emergency_urls[0]):
                item_local.url = item.emergency_urls[0][0]                              #Guardamos la primera url del .Torrent
                if len(item.emergency_urls[0]) > 1:
                    del item.emergency_urls[0][0]
        if not item.armagedon and item.emergency_urls and not item.videolibray_emergency_urls:
            if len(item.emergency_urls[0]):
                item_local.torrent_alt = item.emergency_urls[0][0]      #Guardamos la primera url del .Torrent ALTERNATIVA
        
        if item.videolibray_emergency_urls:
            item.emergency_urls[0].verificar_url(append(item_local.url))                #Salvamnos la url...

        # Poner la calidad, si es necesario
        if not item_local.quality:
            if "hdtv" in item_local.url.lower() or "720p" in item_local.url.lower() or "1080p" in item_local.url.lower() or "4k" in item_local.url.lower():
                item_local.quality = scrapertools.find_single_match(item_local.url, '.*?_([H|7|1|4].*?)\.torrent')
                item_local.quality = item_local.quality.replace("_", " ")
        if item.armagedon:                                                              #Si es catastrófico, lo marcamos
            item_local.quality = '[/COLOR][COLOR hotpink][E] [COLOR limegreen]%s' % item_local.quality
        
        # Extrae la dimensión del vídeo
        item_local.torrent_info = ''
        size  = scrapertools.find_single_match(item_local.url, '(\d{1,3},\d{1,2}?\w+)\.torrent')
        size = size.replace('GB', 'G·B').replace('Gb', 'G·b').replace('MB', 'M·B')\
                        .replace('Mb', 'M·b').replace('.', ',')
        if not size and not item.armagedon:
            size = generictools.get_torrent_size(item_local.url)                        #Buscamos el tamaño en el .torrent
        if size:
            item_local.title = re.sub('\s\[\d+,?\d*?\s\w[b|B]\]', '', item_local.title) #Quitamos size de título, si lo traía
            item_local.quality = re.sub('\s\[\d+,?\d*?\s\w[b|B]\]', '', item_local.quality) #Quitamos size de calidad, si lo traía
            item_local.torrent_info = '%s' % size                                               #Agregamos size
            if not item.unify:
                item_local.torrent_info = '[%s]' % item_local.torrent_info.strip().strip(',')
     
        #Ahora pintamos el link del Torrent, si lo hay
        if item_local.url:		                                                        # Hay Torrent ?
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
            
            item_local.alive = "??"                                                 #Calidad del link sin verificar
            item_local.action = "play"                                              #Visualizar vídeo
            item_local.server = "torrent"                                           #Seridor Torrent
        
            itemlist_t.append(item_local.clone())                                   #Pintar pantalla, si no se filtran idiomas
        
            # Requerido para FilterTools
            if config.get_setting('filter_languages', channel) > 0:                 #Si hay idioma seleccionado, se filtra
                itemlist_f = filtertools.get_link(itemlist_f, item_local, list_language)  #Pintar pantalla, si no está vacío

        #logger.debug("title=[" + item.title + "], torrent=[ " + item_local.url + " ], url=[ " + url + " ], post=[" + item.post + "], thumbnail=[ " + item.thumbnail + " ]" + " size: " + size)

    if item.videolibray_emergency_urls:
        return item
    
    if len(itemlist_f) > 0:                                                         #Si hay entradas filtradas...
        itemlist.extend(itemlist_f)                                                 #Pintamos pantalla filtrada
    else:                                                                       
        if config.get_setting('filter_languages', channel) > 0 and len(itemlist_t) > 0: #Si no hay entradas filtradas ...
            thumb_separador = get_thumb("next.png")                                 #... pintamos todo con aviso
            itemlist.append(Item(channel=item.channel, url=host, title="[COLOR red][B]NO hay elementos con el idioma seleccionado[/B][/COLOR]", thumbnail=thumb_separador, folder=False))
        itemlist.extend(itemlist_t)                                                 #Pintar pantalla con todo si no hay filtrado

    # Requerido para AutoPlay
    autoplay.start(itemlist, item)                                                  #Lanzamos Autoplay
    
    return itemlist
 

def episodios(item):
    logger.info()
    itemlist = []
    
    # Obtener la información actualizada de la Serie.  TMDB es imprescindible para Videoteca
    #if not item.infoLabels['tmdb_id']:
    try:
        tmdb.set_infoLabels(item, True)                                                 #TMDB de cada Temp
    except:
        pass

    # Carga la página
    try:
        data_alt = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url).data)
    except:                                                                             #Algún error de proceso, salimos
        logger.error("ERROR 01: EPISODIOS: La Web no responde o la URL es erronea" + item.url)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: EPISODIOS:.  La Web no responde o la URL es erronea. Si la Web está activa, reportar el error con el log'))
        return itemlist
    
    #Datos para crear el Post.  Usado para documentales
    total_capis = scrapertools.find_single_match(data_alt, "<input type='hidden' name='total_capis' value='(\d+)'>")
    tabla = scrapertools.find_single_match(data_alt, "<input type='hidden' name='tabla' value='([^']+)'>")
    titulo_post = scrapertools.find_single_match(data_alt, "<input type='hidden' name='titulo' value='([^']+)'>")
    
    # Selecciona en tramo que nos interesa
    data = scrapertools.find_single_match(data_alt,
                                  "(<form name='episodios' action='(?:[^']+)?secciones.php\?sec=descargas\&ap=contar_varios' method='post'>.*?)</form>")
    
    # Prepara el patrón de búsqueda de: URL, título, fechas y dos valores mas sin uso
    if '/serie' in item.url:
        patron = ".*?<td bgcolor[^>]+><a href='(.*?)'>?([^>]+)<\/a><\/td>.*?"
    else:
        patron = "<form\s*name='episodios'\s*action='([^']+)'\s*method='post'>.*?<td\s*bgcolor='[^>]+>(.*?)<\/td>.*?"
    patron += "<td[^<]+<div[^>]+>Fecha: ([^<]+)<\/div><\/td>.*?<td[^<]+"
    patron += "<input\s*type='checkbox'\s*name='([^']+)'\s*value='([^']+)'"

    matches = re.compile(patron, re.DOTALL).findall(data)
    if not matches:                             #error
        item = generictools.web_intervenida(item, data_alt)                     #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            item, itemlist = generictools.post_tmdb_episodios(item, itemlist)   #Llamamos al método para el pintado del error
            return itemlist                                                     #Salimos
        
        logger.error("ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data_alt)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

    #logger.debug("PATRON: " + patron)
    #logger.debug(matches)
    #logger.debug(data)

    # Recorremos todos los episodios generando un Item local por cada uno en Itemlist
    for scrapedurl, scrapedtitle, year, name, value in matches:
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

        item_local.url = verificar_url(urlparse.urljoin(host, scrapedurl))
        
        #scrapedtitle = re.sub('\r\n', '', scrapedtitle).decode('iso-8859-1').encode('utf8').strip()
        if scrapedtitle.endswith('.'):
            scrapedtitle = scrapedtitle[:-1]
        if not scrapedtitle:
            scrapedtitle = "SIN TITULO"

        if '/serie' in item.url:
            scrapedtitle = re.sub(r'[a|A]l \d+[x|X]', 'al ', scrapedtitle)  #Quitamos Temporada del segundo rango
            title = scrapedtitle.lower()
            epi = title.split("x")
            if len(epi) > 1:
                temporada = re.sub("\D", "", epi[0])
                if temporada:
                    item_local.contentSeason = temporada
                else:
                    item_local.contentSeason = 1
                capitulo = re.search("\d+", epi[1])
                if capitulo:
                    item_local.contentEpisodeNumber = capitulo.group()
                else:
                    item_local.contentEpisodeNumber = 1
        
        else:                                                               #Se prepara el Post para documentales
            item_local.contentSeason = 1
            item_local.contentEpisodeNumber = 1
            item_local.url = verificar_url(urlparse.urljoin(host, "secciones.php?sec=descargas&ap=contar_varios"))
            item_local.post = urllib.urlencode({name: value, "total_capis": total_capis, "tabla": tabla, "titulo": titulo_post})
            item_local.headers = {'Referer': item.url}
        
        if year:
            item_local.infoLabels['year'] = scrapertools.find_single_match(year, r'(\d{4})')
        
        item_local.title = scrapedtitle
        
        itemlist.append(item_local.clone())
        
    if len(itemlist) > 1:
        itemlist = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))     #clasificamos

    # Pasada por TMDB y clasificación de lista por temporada y episodio
    tmdb.set_infoLabels(itemlist, True)

    #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
    item, itemlist = generictools.post_tmdb_episodios(item, itemlist)

    return itemlist
    
    
def verificar_url(url):
    if '.com' in url or '.net' in url or '.org' in url or '.tv' in url:
        url = url.replace('.com', host_sufix).replace('.net', host_sufix).replace('.org', host_sufix).replace('.tv', host_sufix)
        url = url.replace('/nodo/torrent/', '/torrents/')
        url = url.replace('torrents/tmp/torrent.php?table=peliculas/&name=', 'torrents/peliculas/')
        url = url.replace('torrents/tmp/torrent.php?table=series/&name=', 'torrents/series/')
        url = url.replace('torrents/tmp/torrent.php?table=documentales/&name=', 'torrents/documentales/')
    return url


def actualizar_titulos(item):
    logger.info()
    itemlist = []
    
    from platformcode import launcher
    
    item = generictools.update_title(item) #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels
    
    #Volvemos a la siguiente acción en el canal
    return launcher.run(item)
    

def search(item, texto):
    itemlist = []
    logger.info("search:" + texto)
    texto = texto.replace(" ", "+")

    item.url = host + "secciones.php?sec=buscador&valor=%s" % (texto)
    
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
            item.url = host + "secciones.php?sec=ultimos_torrents"
            item.extra = "novedades"
            item.channel = "mejortorrent"
            item.tipo = False
            itemlist = listado_busqueda(item)
            if "Pagina siguiente >>" in itemlist[-1].title:
                itemlist.pop()

        if categoria == 'documentales':
            item.url = host + "torrents-de-documentales.html"
            item.extra = "documentales"
            item.channel = "mejortorrent"
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
