# -*- coding: utf-8 -*-

import re
import sys
import urllib
import urlparse
import datetime
import time
import ast
import random
import traceback

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import channeltools
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

channel_py = 'newpct1'

#Código para permitir usar un único canal para todas las webs clones de NewPct1
#Cargamos en .json del canal para ver las listas de valores en settings
clone_list = channeltools.get_channel_json(channel_py)

for settings in clone_list['settings']:                                         #Se recorren todos los settings
    if settings['id'] == "clonenewpct1_channels_list":                          #Encontramos en setting
        clone_list = settings['default']                                        #Carga lista de clones
        break
clone_list = ast.literal_eval(clone_list)                                       #la convierte en array
clone_list_check = clone_list[:]                                                #la salvamos para otros usos
host_index = 0
host_index = config.get_setting('clonenewpct1_channel_default', channel_py)     #Clone por defecto
host_index_check = host_index                                                   #lo salvamos para otros usos

clone_list_random = []                                                          #Iniciamos la lista aleatoria de clones

if host_index == 0:                                                             #Si el clones es "Aleatorio"...
    i = 0
    j = 1                                                                   #... marcamos el último de los clones "buenos"
    for active_clone, channel_clone, host_clone, contentType_clone, info_clone in clone_list:
        if i <= j and active_clone == "1":
            clone_list_random += [clone_list[i]]                            #... añadimos el clone activo "bueno" a la lista
        i += 1
    if clone_list_random:                                                       #Si hay clones en la lista aleatoria...
        clone_list = [random.choice(clone_list_random)]                         #Seleccionamos un clone aleatorio
        #logger.debug(clone_list)
    host_index = 1                              #mutamos el num. de clone para que se procese en el siguiente loop
        
if host_index > 0 or not clone_list_random:     #Si el Clone por defecto no es Aleatorio, o hay ya un aleatorio sleccionado...
    i = 1
    for active_clone, channel_clone, host_clone, contentType_clone, info_clone in clone_list:
        if i == host_index:
            channel_clone_name = channel_clone                                  #Nombre del Canal elegido
            host = host_clone                                                   #URL del Canal elegido
            if active_clone == "1":                                             #Comprueba que el clone esté activo
                break
            channel_clone_name = "*** DOWN ***"                                 #es un fallo masivo ???
            for active_clone, channel_clone, host_clone, contentType_clone, info_clone in clone_list:
                if active_clone == "1":                                         #Comprueba que el clone esté activo
                    channel_clone_name = channel_clone                          #Nombre del Canal elegido
                    host = host_clone                                           #URL del Canal elegido
                    break
        i += 1
    
item = Item()
if item.channel != channel_py:
    item.channel = channel_py

#Carga de opciones del canal        
__modo_grafico__ = config.get_setting('modo_grafico', channel_py)               #TMDB?
modo_ultima_temp = config.get_setting('seleccionar_ult_temporadda_activa', channel_py)  #Actualización sólo últ. Temporada?
timeout = config.get_setting('clonenewpct1_timeout_downloadpage', channel_py)   #Timeout downloadpage
timeout = timeout * 1.4                                                         # Incremento temporal del 40%
if timeout == 0: timeout = None
if httptools.channel_proxy_list(host):                                          #Si usa un proxy, ...
    timeout = timeout * 2                                                       #Duplicamos en timeout

fecha_rango = config.get_setting('clonenewpct1_rango_fechas_novedades', channel_py) #Rango fechas para Novedades
if fecha_rango == 0: fecha_rango = 'Hoy'
elif fecha_rango == 1: fecha_rango = 'Ayer'
elif fecha_rango == 2: fecha_rango = 'Semana'
elif fecha_rango == 3: fecha_rango = 'Mes'
elif fecha_rango == 4: fecha_rango = 'Siempre'
episodio_serie = config.get_setting('clonenewpct1_serie_episodio_novedades', channel_py)    #Episodio o serie para Novedades

#Temporal, sólo para actualizar newpct1_data.json con otro valor por defecto
#channel_banned = config.get_setting('clonenewpct1_excluir1_enlaces_veronline', channel_py)  #1eer Canal baneado
#if channel_banned == 9:
#    config.set_setting('clonenewpct1_excluir1_enlaces_veronline', 22, channel_py)      #se pone el nuevo valor por defecto


def mainlist(item):
    logger.info()
    
    itemlist = []
    
    item, host_alt = verify_host(item, host, force=False)                       # Actualizamos la url del host

    thumb_pelis = get_thumb("channels_movie.png")
    thumb_pelis_hd = get_thumb("channels_movie_hd.png")
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_series_hd = get_thumb("channels_tvshow_hd.png")
    thumb_series_az = get_thumb("channels_tvshow_az.png")
    thumb_docus = get_thumb("channels_documentary.png")
    thumb_buscar = get_thumb("search.png")
    thumb_separador = get_thumb("next.png")
    thumb_settings = get_thumb("setting_0.png")
    
    if channel_clone_name == "*** DOWN ***":                                    # Ningún clones activo !!!
        itemlist.append(item.clone(action='', title="[COLOR yellow]Ningún canal NewPct1 activo[/COLOR]"))    
        return itemlist                                     # si no hay más datos, algo no funciona, pintamos lo que tenemos y salimos

    autoplay.init(item.channel, list_servers, list_quality)
        
    itemlist.append(Item(channel=item.channel, action="submenu_novedades", title="Novedades", 
                    url=item.channel_host + "ultimas-descargas/", extra="novedades", 
                    thumbnail=thumb_pelis, category=item.category, channel_host=item.channel_host))
    
    itemlist.append(Item(channel=item.channel, action="submenu", title="Películas", 
                    url=item.channel_host, extra="peliculas", thumbnail=thumb_pelis, 
                    category=item.category, channel_host=item.channel_host))

    itemlist.append(Item(channel=item.channel, action="submenu", title="Series", 
                    url=item.channel_host, extra="series", thumbnail=thumb_series, 
                    category=item.category, channel_host=item.channel_host))
                         
    itemlist.append(Item(channel=item.channel, action="submenu", title="Documentales", 
                    url=item.channel_host, extra="varios", thumbnail=thumb_docus, 
                    category=item.category, channel_host=item.channel_host))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar", 
                    url=item.channel_host + "buscar", thumbnail=thumb_buscar, 
                    category=item.category, channel_host=item.channel_host))
    
    clone_act = 'Clone: '
    if config.get_setting('clonenewpct1_channel_default', channel_py) == 0:
        clone_act = 'Aleatorio: '
    itemlist.append(Item(channel=item.channel, url=item.channel_host, 
                    title="[COLOR yellow]Configuración:[/COLOR] (" + clone_act + 
                    item.category + ")", folder=False, thumbnail=thumb_separador, 
                    category=item.category, channel_host=item.channel_host))
    
    itemlist.append(Item(channel=item.channel, action="settingCanal", 
                    title="Configurar canal", thumbnail=thumb_settings, category=item.category, 
                    channel_host=item.channel_host))
    
    autoplay.show_option(item.channel, itemlist)                                #Activamos Autoplay
       
    item.category = '%s / %s' % (channel_py.title(), item.category.title())     #Newpct1: nombre de clone en pantalla Mainlist
        
    return itemlist

    
def settingCanal(item):
    from platformcode import platformtools
    platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return 
    

def submenu(item):
    logger.info()
    
    itemlist = []
    item.extra2 = ''
    
    item, host_alt = verify_host(item, host)                                    # Actualizamos la url del host
    
    data = ''
    try:
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url, timeout=timeout).data)
    except:
        logger.error(traceback.format_exc())
        
    patron = '<li><a\s*class="[^"]+"\s*href="[^"]+"><i\s*class="[^"]+".*?><\/i>.*?'
    patron += 'Inicio.*?<\/a><\/li>(.+)<\/ul>\s*<\/nav>'
    if not scrapertools.find_single_match(data, patron):
        patron = '<div class="links-content">\s*<div class="one_fourth">\s*<h3>'
        patron += 'Categorias<\/h3>\s*<ul class="content-links">(.*?)<\/ul>\s*<\/div>'
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
        
        try:
            logger.error("ERROR 01: SUBMENU: La Web no responde o ha cambiado de URL: " 
                    + item.url + " / DATA: " + data)
        except:
            logger.error("ERROR 01: SUBMENU: La Web no responde o ha cambiado de URL: " 
                    + item.url + " / DATA: (probablemente bloqueada por antivirus)")
        #Si no hay datos consistentes, llamamos al método de fail_over para que encuentre un canal que esté activo y pueda gestionar el submenú
        item, data = generictools.fail_over_newpct1(item, patron, timeout=timeout)
    
    if not data:    #Si no ha logrado encontrar nada, salimos
        itemlist.append(item.clone(action='', title="[COLOR yellow]" + item.category 
                    + '[/COLOR]: Ningún canal NewPct1 activo'))    
        itemlist.append(item.clone(action='', title=item.category + 
                    ': ERROR 01: SUBMENU: La Web no responde o ha cambiado de URL. ' 
                    + 'Si la Web está activa, reportar el error con el log'))
        return itemlist                                 #si no hay más datos, algo no funciona, pintamos lo que tenemos
    elif item.channel_alt:                                                      #Si ha habido fail-over, lo comento
        itemlist.append(item.clone(action='', title="[COLOR yellow]" + 
                    item.category + '[/COLOR] [ALT ] en uso'))
        itemlist.append(item.clone(action='', title="[COLOR yellow]" + 
                    item.channel_alt.capitalize() + '[/COLOR] inaccesible'))
        
        if item.url_alt: del item.url_alt
        del item.channel_alt

    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
    data = data.replace("'", '"').replace('/series"', '/series/"')              #Compatibilidad con mispelisy.series.com
    if "pelisyseries.com" in item.channel_host and item.extra == "varios":      #compatibilidad con mispelisy.series.com
        data_menu = '<li><a href="' + item.channel_host + 'varios/" title="Documentales">Documentales</a></li>'
    else:
        data_menu = scrapertools.find_single_match(data, patron)                #Seleccionamos el trozo que nos interesa
    if not data_menu:
        try:
            logger.error("ERROR 02: SUBMENU: Ha cambiado la estructura de la Web " 
                    + " / PATRON: " + patron + " / DATA: " + data)
        except:
            logger.error("ERROR 02: SUBMENU: Ha cambiado la estructura de la Web " 
                    + " / PATRON: " + patron + " / DATA: (probablemente bloqueada por antivirus)")
        itemlist.append(item.clone(action='', title=item.category + 
                    ': ERROR 02: SUBMENU: Ha cambiado la estructura de la Web.  ' 
                    + ' Reportar el error con el log'))
        return itemlist                                 #si no hay más datos, algo no funciona, pintamos lo que tenemos

    patron = '<li><a\s*(?:style="[^"]+"\s*)?href="([^"]+)"\s*.itle="[^"]+"\s*>'
    patron += '(?:<i\s*class="[^"]+">\s*<\/i>)?([^>]+)<\/a><\/li>'
    matches = re.compile(patron, re.DOTALL).findall(data_menu)

    if not matches:
        logger.error("ERROR 02: SUBMENU: Ha cambiado la estructura de la Web " + 
                    " / PATRON: " + patron + " / DATA: " + data_menu)
        itemlist.append(item.clone(action='', title=item.category + 
                    ': ERROR 02: SUBMENU: Ha cambiado la estructura de la Web.  ' 
                    + 'Reportar el error con el log'))
        return itemlist                                 #si no hay más datos, algo no funciona, pintamos lo que tenemos

    matches_hd = []
    if item.extra == "peliculas":
        patron = '<h3\s*(?:style="[^"]+")?>(?:<strong>)?Peliculas(?:<\/strong>)? en HD '
        patron += '<a href="[^"]+"\s*class="[^"]+"\s*title="[^"]+">(?:ver .*?)?<\/a>'
        patron += '<span(?: style="[^"]+")?>(.*?)(?:<\/span>)?<\/h3>'
        data_hd = scrapertools.find_single_match(data, patron)                  #Seleccionamos el trozo que nos interesa
        if data_hd:
            patron = '<a href="([^"]+)"\s*.itle="[^"]+"\s*>([^<]+)<\/a>'
            matches_hd = re.compile(patron, re.DOTALL).findall(data_hd)
            #logger.debug(matches_hd)
    
    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle.strip()

        #Preguntamos por las entradas que no corresponden al "extra"
        if item.extra in scrapedtitle.lower() or (item.extra == "peliculas" and \
                    ("cine" in scrapedurl or "anime" in scrapedurl)) or \
                    (item.extra == "varios" and ("documentales" in scrapedurl \
                    or "varios" in scrapedurl)):
            
            #Si tiene filtro de idiomas, marcamos estas páginas como no filtrables
            if "castellano" in title.lower() or "latino" in title.lower() or \
                    "subtituladas" in title.lower() or "vo" in title.lower() or \
                    "v.o" in title.lower() or "- es" in title.lower():
                item.extra2 = "categorias"
            else:
                item.extra2 = ""
            
            url = scrapedurl                                                    #Arreglo para Desacargas2020
            if scrapedurl == item.url:
                url = scrapedurl + item.extra + '/'
            
            itemlist.append(item.clone(action="listado", title=title, url=url))
            
            if matches_hd and 'HD' in title:
                for scrapedurlcat, scrapedtitlecat in matches_hd:           #Pintamos las categorías de peliculas en HD
                    if '4k' in scrapedtitlecat.lower():                     #... ignoramos 4K, no funcionan las categorías
                        continue
                    itemlist.append(item.clone(action="listado", title="   - Calidad: " 
                            + scrapedtitlecat, url=scrapedurlcat))
            
            itemlist.append(item.clone(action="alfabeto", title=title + " [A-Z]", url=url))
            
    if item.extra == "varios" and len(itemlist) == 0:
        itemlist.append(item.clone(action="listado", title="Varios", url=item.channel_host 
                    + "varios/"))
        itemlist.append(item.clone(action="alfabeto", title="Varios" + " [A-Z]", 
                    url=item.channel_host + "varios/"))
    
    if item.extra == "peliculas":
        itemlist.append(item.clone(action="listado", title="Películas 4K", 
                    url=item.channel_host + "peliculas-hd/4kultrahd/"))
        itemlist.append(item.clone(action="alfabeto", title="Películas 4K" + 
                    " [A-Z]", url=item.channel_host + "peliculas-hd/4kultrahd/"))

    return itemlist


def submenu_novedades(item):
    logger.info()
    
    itemlist = []
    itemlist_alt = []
    item.extra2 = ''
    thumb_buscar = get_thumb("search.png")
    
    #item, host_alt = verify_host(item, host, force=True, category='descargas2020')  # Actualizamos el clone, preferible descargas2020
    item, host_alt = verify_host(item, host, force=True)                        # Actualizamos el clone
    
    data = ''
    timeout_search=timeout * 2                                                  #Más tiempo para Novedades, que es una búsqueda
    thumb_settings = get_thumb("setting_0.png")
    
    if channel_clone_name == "*** DOWN ***":                                    #Ningún clones activo !!!
        itemlist.append(item.clone(action='', title="[COLOR yellow]Ningún canal NewPct1 activo[/COLOR]"))    
        return itemlist                             #si no hay más datos, algo no funciona, pintamos lo que tenemos y salimos
    
    try:
        data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url, timeout=timeout_search).data)
    except:
        logger.error(traceback.format_exc())
        
    patron = '<div class="content">.*?<ul class="noticias'
    #Verificamos si se ha cargado una página, y si además tiene la estructura correcta
    if not data or not scrapertools.find_single_match(data, patron):
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            for clone_inter, autoridad in item.intervencion:
                thumb_intervenido = get_thumb(autoridad)
                itemlist.append(item.clone(action='', title="[COLOR yellow]" 
                        + clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial + 
                        '. Reportar el problema en el foro', thumbnail=thumb_intervenido))
            return itemlist                                                     #Salimos
        
        logger.error("ERROR 01: SUBMENU: La Web no responde o ha cambiado de URL: " + item.url + data)
        #Si no hay datos consistentes, llamamos al método de fail_over para que encuentre un canal que esté activo y pueda gestionar el submenú
        item, data = generictools.fail_over_newpct1(item, patron, timeout=timeout)
    
    if not data:                                                                #Si no ha logrado encontrar nada, salimos
        itemlist.append(item.clone(action='', title="[COLOR yellow]" + item.category + 
                    '[/COLOR]: Ningún canal NewPct1 activo'))    
        itemlist.append(item.clone(action='', title=item.category + 
                    ': ERROR 01: SUBMENU: La Web no responde o ha cambiado de URL. ' 
                    + ' Si la Web está activa, reportar el error con el log'))
        return itemlist                                     #si no hay más datos, algo no funciona, pintamos lo que tenemos
    elif item.channel_alt:                                                      #Si ha habido fail-over, lo comento
        itemlist.append(item.clone(action='', title="[COLOR yellow]" + item.category 
                    + '[/COLOR] [ALT ] en uso'))
        itemlist.append(item.clone(action='', title="[COLOR yellow]" + item.channel_alt.capitalize() 
                    + '[/COLOR] inaccesible'))
        
        if item.url_alt: del item.url_alt
        del item.channel_alt
        
    data = scrapertools.find_single_match(data, patron)                         #Seleccionamos el trozo que nos interesa
    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
    data = data.replace("'", '"').replace('/series"', '/series/"')              #Compatibilidad con mispelisy.series.com
    
    patron = '<option value="([^"]+)".*?>(.*?)<\/option>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    
    if not matches:
        item.action = "listado_busqueda"
        return listado_busqueda(item)
    
    itemlist.append(item.clone(action='', title="[COLOR yellow]Ver lo Último de:[/COLOR]"))
    for value, title in matches:
        if not value.isdigit():
            if title not in "Mes": 
                item.post = "date=%s" % value
                itemlist.append(item.clone(action="listado_busqueda", title=title, 
                        url=item.url, post=item.post))
    
    itemlist.append(
        Item(channel=item.channel, action="search", title="Buscar", url=item.channel_host 
                        + "buscar", thumbnail=thumb_buscar, category=item.category, 
                        channel_host=item.channel_host))
    
    itemlist.append(item.clone(action='', title="[COLOR yellow]Lo Último en la " 
                        + "Categoría de [B]%s[/B][/COLOR]" % fecha_rango))
    for value, title in matches:
        if value.isdigit():
            if title not in "Juegos, Software, Musica, Deportes":
                
                #tratamos de poner al principio las categorías más relevantes
                if value == '1027': title = "01" + title                        #Pelis HD
                elif value == '757': title = "02" + title                       #Pelis Castellano
                elif value == '1527': title = "03" + title                      #Pelis Latino
                elif value == '1469': title = "04" + title                      #Series HD
                elif value == '767': title = "05" + title                       #Series
                else: title = "99" + title                                      #Resto

                item.post = "categoryIDR=%s&date=%s" % (value, fecha_rango)
                itemlist_alt.append(item.clone(action="listado_busqueda", title=title, 
                        url=item.url, post=item.post))
    
    itemlist_alt = sorted(itemlist_alt, key=lambda it: it.title)                #clasificamos
    for item_local in itemlist_alt:
        item_local.title = re.sub(r'^\d{2}', '', item_local.title)              #Borramos la secuencia
        
        #Si tiene filtro de idiomas, marcamos estas páginas como no filtrables
        if "castellano" in item_local.title.lower() or "latino" in item_local.title.lower() \
                    or "subtituladas" in item_local.title.lower() or "vo" in \
                    item_local.title.lower() or "v.o" in item_local.title.lower() \
                    or "- es" in item_local.title.lower():
            item_local.extra2 = "categorias"
        else:
            item_local.extra2 = ""
        
        itemlist.append(item_local.clone())
        
    itemlist.append(
        Item(channel=item.channel, action="", title="[COLOR yellow]Configuración de " 
                    + "Novedades:[/COLOR]", url="", thumbnail=thumb_settings, 
                    category=item.category, channel_host=item.channel_host))
    itemlist.append(
        Item(channel=item.channel, action="settingCanal", 
                    title="Periodos y formatos de series en Novedades", url="", 
                    thumbnail=thumb_settings, category=item.category, 
                    channel_host=item.channel_host))

    return itemlist
    
    
def alfabeto(item):
    logger.info()
    itemlist = []
    
    item, host_alt = verify_host(item, host)                                    # Actualizamos la url del host
    
    try:
        data = ''
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url, timeout=timeout).data)
        data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
    except:
        logger.error(traceback.format_exc())

    patron = '<ul class="alfabeto">(.*?)</ul>'
    if not data or not scrapertools.find_single_match(data, patron):
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            for clone_inter, autoridad in item.intervencion:
                thumb_intervenido = get_thumb(autoridad)
                itemlist.append(item.clone(action='', title="[COLOR yellow]" + 
                        clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial 
                        + '. Reportar el problema en el foro', thumbnail=thumb_intervenido))
            return itemlist                                                     #Salimos
        
        logger.error("ERROR 01: ALFABETO: La Web no responde o ha cambiado de URL: " + item.url + data)
        #Si no hay datos consistentes, llamamos al método de fail_over para que encuentre un canal que esté activo y pueda gestionar el submenú
        item, data = generictools.fail_over_newpct1(item, patron, timeout=timeout)
    
    if not data:    #Si no ha logrado encontrar nada, salimos
        itemlist.append(item.clone(action='', title="[COLOR yellow]" + item.category + 
                        '[/COLOR]: Ningún canal NewPct1 activo'))    
        itemlist.append(item.clone(action='', title=item.category + 
                        ': ERROR 01: ALFABETO: La Web no responde o ha cambiado de URL. ' 
                        + 'Si la Web está activa, reportar el error con el log'))
        return itemlist                                 #si no hay más datos, algo no funciona, pintamos lo que tenemos
    elif item.channel_alt:                                                      #Si ha habido fail-over, lo comento
        itemlist.append(item.clone(action='', title="[COLOR yellow]" + 
                        item.category + '[/COLOR] [ALT ] en uso'))
        itemlist.append(item.clone(action='', title="[COLOR yellow]" + 
                        item.channel_alt.capitalize() + '[/COLOR] inaccesible'))
        
        if item.url_alt: del item.url_alt
        del item.channel_alt
    
    data = scrapertools.find_single_match(data, patron)

    patron = '<a href="([^"]+)"[^>]*>([^>]*)</a>'

    matches = re.compile(patron, re.DOTALL).findall(data)
    if not matches:
        logger.error("ERROR 02: ALFABETO: Ha cambiado la estructura de la Web " + 
                        " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.category + 
                        ': ERROR 02: ALFABETO: Ha cambiado la estructura de la Web.  ' 
                        + 'Reportar el error con el log'))
        return itemlist                                 #si no hay más datos, algo no funciona, pintamos lo que tenemos

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle.upper()

        itemlist.append(item.clone(action="listado", title=title, url=scrapedurl))

    return itemlist


def listado(item):
    logger.info()
    itemlist = []
    
    item, host_alt = verify_host(item, host)                                    # Actualizamos la url del host
    
    clase = "pelilist"                                                          # etiqueta para localizar zona de listado de contenidos
    url_next_page =''                                                           # Control de paginación
    cnt_tot = 30                                                                # Poner el num. máximo de items por página

    if item.totalItems:
        del item.totalItems

    data = ''
    try:
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url, timeout=timeout).data)
    except:
        logger.error(traceback.format_exc())
    
    patron = '<ul class="' + clase + '">(.*?)</ul>'                             #seleccionamos el bloque que nos interesa
    if not data or (not scrapertools.find_single_match(data, patron) and not '<h3><strong>( 0 ) Resultados encontrados </strong>' in data):
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            item, itemlist = generictools.post_tmdb_listado(item, itemlist)     #Llamamos al método para el pintado del error
            return itemlist                                                     #Salimos
            
        logger.error("ERROR 01: LISTADO: La Web no responde o ha cambiado de URL: " 
                    + item.url + " / DATA: " + data)
        #Si no hay datos consistentes, llamamos al método de fail_over para que encuentre un canal que esté activo y pueda gestionar el submenú
        item, data = generictools.fail_over_newpct1(item, patron, timeout=timeout)
    
    if not data:    #Si no ha logrado encontrar nada, salimos
        itemlist.append(item.clone(action='', title="[COLOR yellow]" + 
                    item.channel.capitalize() + '[/COLOR]: Ningún canal NewPct1 activo'))    
        itemlist.append(item.clone(action='', title=item.category + 
                    ': ERROR 01: LISTADO: La Web no responde o ha cambiado de URL. ' 
                    + 'Si la Web está activa, reportar el error con el log'))
        return itemlist                                     #si no hay más datos, algo no funciona, pintamos lo que tenemos

    #Establecemos los valores básicos en función del tipo de contenido
    if item.extra == "peliculas":
        item.action = "findvideos"
        item.contentType = "movie"
        pag = True                                                              #Sí hay paginación
    elif item.extra == "series" and not "/miniseries" in item.url:
        item.action = "episodios"
        item.contentType = "tvshow"
        item.season_colapse = True
        pag = True
    elif item.extra == "varios" or "/miniseries" in item.url:
        item.action = "findvideos"
        item.contentType = "movie"
        pag = True
    
    #Selecciona el tramo de la página con el listado de contenidos
    patron = '<ul class="' + clase + '">(.*?)</ul>'
    if data:
        fichas = scrapertools.find_single_match(data, patron)
        if not fichas and not '<h3><strong>( 0 ) Resultados encontrados </strong>' in data:         #error
            logger.error("ERROR 02: LISTADO: Ha cambiado la estructura de la Web " 
                    + " / PATRON: " + patron + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.category + 
                    ': ERROR 02: LISTADO: Ha cambiado la estructura de la Web.  ' 
                    + 'Reportar el error con el log'))
            return itemlist                                 #si no hay más datos, algo no funciona, pintamos lo que tenemos
        elif '<h3><strong>( 0 ) Resultados encontrados </strong>' in data:      #no hay vídeos
            return itemlist
    else:
        return itemlist
    page_extra = clase

    #Scrapea los datos de cada vídeo.  Título alternativo se mantiene, aunque no se usa de momento
    patron = '<a href="([^"]+)"\s*'                                             # la url
    patron += 'title="([^"]+)"[^>]*>\s*'                                        # el titulo
    patron += '<img.*?src="([^"]+)"[^>]*>\s*'                                   # el thumbnail
    patron += '<h2.*?>(.*?)?<\/h2>\s*'                                          # titulo alternativo.  Se trunca en títulos largos
    patron += '<span>([^<].*?)?<'                                               # la calidad
    matches = re.compile(patron, re.DOTALL).findall(fichas)
    if not matches:                                                             #error
        logger.error("ERROR 02: LISTADO: Ha cambiado la estructura de la Web " 
                    + " / PATRON: " + patron + " / DATA: " + fichas)
        itemlist.append(item.clone(action='', title=item.category + 
                    ': ERROR 02: LISTADO: Ha cambiado la estructura de la Web.  ' 
                    + 'Reportar el error con el log'))
        return itemlist                                     #si no hay más datos, algo no funciona, pintamos lo que tenemos
    
    #logger.debug("MATCHES: " + str(len(matches)))
    #logger.debug(matches)
    #logger.debug("patron: " + patron + " / fichas: " + fichas)

    # Identifico la página actual y el total de páginas para el pie de página
    patron_last_page  = '<a href="[^"]+\/(\d+)">Last<\/a><\/li>'
    if item.total_pag:
        total_pag = item.total_pag
    else:
        total_pag  = scrapertools.find_single_match(data, patron_last_page)

    if not item.post_num:
        post_num = 1
    else:
        post_num = int(item.post_num) + 1
    if not total_pag:
        total_pag = 1
    #Calcula las páginas del canal por cada página de la web
    if not item.total_pag:
        total_pag = int(total_pag) * int((float(len(matches))/float(cnt_tot)) + 0.999999)
    
    # Preparamos la paginación.
    if not item.cnt_pag:
        cnt_pag = 0
    else:
        cnt_pag = item.cnt_pag
        del item.cnt_pag
    
    matches_cnt = len(matches)
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
        patron_next_page  = '<a href="([^"]+)">Next<\/a>'
        matches_next_page = re.compile(patron_next_page, re.DOTALL).findall(data)
        modo = 'continue'
        if len(matches_next_page) > 0:
            url_next_page = urlparse.urljoin(item.url, matches_next_page[0])
            modo = 'next'
    
    # Avanzamos el contador de líneas en una página
    if item.next_page:
        del item.next_page
    if modo == 'next':
        cnt_pag = 0
    else:
        cnt_pag += cnt_tot

    #Tratamos todos los contenidos, creardo una variable local de Item
    for scrapedurl, scrapedtitle, scrapedthumbnail, scrapedtitle_alt, calidad in matches:
        item_local = item.clone()
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
        if item_local.total_pag:
            del item_local.total_pag

        item_local.title = ''
        item_local.context = "['buscar_trailer']"
        
        # Limpiamos títulos, Sacamos datos de calidad, audio y lenguaje
        title = re.sub('\r\n', '', scrapedtitle).decode('iso-8859-1').encode('utf8').strip()
        #title = re.sub('\r\n', '', scrapedtitle).decode('utf-8').encode('utf-8').strip()
        title_alt = re.sub('\r\n', '', scrapedtitle_alt).decode('iso-8859-1').encode('utf8').strip()
        #title_alt = re.sub('\r\n', '', scrapedtitle_alt).decode('utf-8').encode('utf-8').strip()
        title = title.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o")\
                    .replace("ú", "u").replace("ü", "u").replace("ï¿½", "ñ")\
                    .replace("Ã±", "ñ").replace(".", " ")
        title_alt = title_alt.replace("á", "a").replace("é", "e").replace("í", "i")\
                    .replace("ó", "o").replace("ú", "u").replace("ü", "u")\
                    .replace("ï¿½", "ñ").replace("Ã±", "ñ")
        
        item_local.quality = calidad
        title_subs = []
        
        #Determinamos y marcamos idiomas distintos del castellano
        item_local.language = []
        if "[vos" in title.lower() or "v.o.s" in title.lower() or "vo" in title.lower() \
                    or "subs" in title.lower() or ".com/pelicula/" in scrapedurl  or \
                    ".com/series-vo" in scrapedurl or "-vo/" in scrapedurl or "vos" in \
                    calidad.lower() or "vose" in calidad.lower() or "v.o.s" in calidad.lower() \
                    or "sub" in calidad.lower() or ".com/peliculas-vo" in item.url:
            item_local.language += ["VOS"]
        title = title.replace(" [Subs. integrados]", "").replace(" [subs. Integrados]", "")\
                    .replace(" [VOSE", "").replace(" [VOS", "").replace(" (V.O.S.E)", "")\
                    .replace(" VO", "").replace("Subtitulos", "")
        if "latino" in title.lower() or "argentina" in title.lower() or "-latino/" in \
                    scrapedurl or "latino" in calidad.lower() or "argentina" in calidad.lower():
            item_local.language += ["LAT"]
        
        #Guardamos info de 3D en calidad y limpiamos
        if "3d" in title.lower():
            if not "3d" in item_local.quality.lower():
                item_local.quality = item_local.quality + " 3D"
            calidad3D = scrapertools.find_single_match(title, r'\s(3[d|D]\s\w+)')
            if calidad3D:
                item_local.quality = item_local.quality.replace("3D", calidad3D)
            title = re.sub(r'\s3[d|D]\s\w+', '', title)
            title = re.sub(r'\s3[d|D]', '', title)
            title_alt = re.sub(r'\s3[d|D]\s\w+', '', title_alt)
            title_alt = re.sub(r'\s3[d|D]', '', title_alt)
            if "imax" in title.lower():
                item_local.quality = item_local.quality + " IMAX"
                title = title.replace(" IMAX", "").replace(" imax", "")
                title_alt = title_alt.replace(" IMAX", "").replace(" imax", "")
        if "2d" in title.lower():
            title = title.replace("(2D)", "").replace("(2d)", "").replace("2D", "").replace("2d", "")
            title_subs += ["[2D]"]
        
        if ("temp" in title.lower() or "cap" in title.lower()) and item_local.contentType != "movie":
            #Eliminamos Temporada de Series, solo nos interesa la serie completa
            title = re.sub(r'-?\s*[t|T]emp\w+ \d+ Comp\w+\d+[x|X]\d+', ' Completa', title)
            title = re.sub(r'-?\s*[t|T]emp\w+.?\d+.?[c|C]ap\w+.?\d+.?(?:al|Al|y).?\d+', '', title)
            title = re.sub(r'-?\s*[t|T]emp\w+ \d+x\d+', '', title)
            title = re.sub(r'-?\s*[t|T]emp\w+ \d+', '', title)
            title = re.sub(r'-?\s*[t|T]emp\w+.*?\d+', '', title)
            title = re.sub(r'\s*[t|T]emp.*?\d+[x|X]\d+', '', title)
            title = re.sub(r'\s*[t|T]emp.*?\d+', '', title)
            title = re.sub(r'\s*[c|C]ap.*?\d+ al \d+', '', title)
            title = re.sub(r'\s*[c|C]ap.*?\d+', '', title)
        if "audio" in title.lower():                                #Reservamos info de audio para después de TMDB
            title_subs += ['[%s]' % scrapertools.find_single_match(title, r'(\[[a|A]udio.*?\])')]
            title = re.sub(r'\[[a|A]udio.*?\]', '', title)
        if "[dual" in title.lower() or "multileng" in title.lower() or "multileng" \
                    in item_local.quality.lower() or (("espa" in title.lower() or \
                    "spani" in title.lower()) and "VOS" in item_local.language):
            item_local.language[0:0] = ["DUAL"]
            title = re.sub(r'\[[D|d]ual.*?\]', '', title)
            title = re.sub(r'\[[M|m]ultileng.*?\]', '', title)
            item_local.quality = re.sub(r'\[[M|m]ultileng.*?\]', '', item_local.quality)
        if "duolog" in title.lower():
            title_subs += ["[Saga]"]
            title = title.replace(" Duologia", "").replace(" duologia", "")\
                    .replace(" Duolog", "").replace(" duolog", "")
        if "trilog" in title.lower():
            title_subs += ["[Saga]"]
            title = title.replace(" Trilogia", "").replace(" trilogia", "")\
                    .replace(" Trilog", "").replace(" trilog", "")
        if "extendida" in title.lower() or "v.e." in title.lower()or "v e " in title.lower():
            title_subs += ["[V. Extendida]"]
            title = title.replace("Version Extendida", "").replace("(Version Extendida)", "")\
                    .replace("V. Extendida", "").replace("VExtendida", "")\
                    .replace("V Extendida", "").replace("V.Extendida", "")\
                    .replace("V  Extendida", "").replace("V.E.", "").replace("V E ", "")
        if "saga" in title.lower():
            title = title.replace(" Saga Completa", "").replace(" saga sompleta", "")\
                    .replace(" Saga", "").replace(" saga", "")
            title_subs += ["[Saga]"]
        if "colecc" in title.lower() or "completa" in title.lower():
            title = title.replace(" Coleccion", "").replace(" coleccion", "")\
                    .replace(" Colecci", "").replace(" colecci", "").replace(" Completa", "")\
                    .replace(" completa", "").replace(" COMPLETA", "")
        if scrapertools.find_single_match(title, r'(- [m|M].*?serie ?\w+)'):
            title = re.sub(r'- [m|M].*?serie ?\w+', '', title)
            title_subs += ["[Miniserie]"]

        if not item_local.language:
            item_local.language = ["CAST"]
        
        #Limpiamos restos en título
        title = title.replace("Castellano", "").replace("castellano", "").replace("inglés", "")\
                    .replace("ingles", "").replace("Inglés", "").replace("Ingles", "")\
                    .replace("Ingl", "").replace("Engl", "").replace("Calidad", "")\
                    .replace("de la Serie", "").replace("Spanish", "")
        title_alt = title_alt.replace("Castellano", "").replace("castellano", "")\
                    .replace("inglés", "").replace("ingles", "").replace("Inglés", "")\
                    .replace("Ingles", "").replace("Ingl", "").replace("Engl", "")\
                    .replace("Calidad", "").replace("de la Serie", "").replace("Spanish", "")
        
        #Limpiamos cabeceras y colas del título
        title = re.sub(r'Descargar\s\w+\-\w+', '', title)
        title = re.sub(r'\(COMPLE.*?\)', '', title)
        
        title = title.replace("Ver online Serie", "").replace("Ver online ", "")\
                    .replace("Descarga Serie HD ", "").replace("Descargar Serie HD ", "")\
                    .replace("Descarga Serie ", "").replace("Descargar Serie ", "")\
                    .replace("Ver en linea ", "").replace("Ver en linea", "")\
                    .replace("en Full HD", "").replace("en hd ", "").replace("en HD ", "")\
                    .replace("MicroHD", "").replace("HD ", "").replace("(Proper)", "")\
                    .replace("HDTV", "").replace("RatDVD", "").replace("DVDRiP", "")\
                    .replace("DVDRIP", "").replace("DVDRip", "").replace("DVDR", "")\
                    .replace("DVD9", "").replace("DVD", "").replace("DVBRIP", "")\
                    .replace("DVB", "").replace("LINE", "").replace("calidad", " ")\
                    .replace("- ES ", "").replace("ES ", "").replace("COMPLETA", "")\
                    .replace("Serie Animada", " ").replace("(", "-").replace(")", "-")\
                    .replace(".", " ").strip()
        
        title = title.replace("Descargar torrent ", "").replace("Descarga Gratis", "")\
                    .replace("Descarga gratis", "").replace("Descargar Gratis", "")\
                    .replace("Descargar gratis", "").replace("en gratis", "")\
                    .replace("gratis gratis", "").replace("Gratisgratis", "")\
                    .replace("Descargar Estreno ", "").replace("Descargar Estrenos ", "")\
                    .replace("Pelicula en latino ", "").replace("Descargar Pelicula ", "")\
                    .replace("Descargar pelicula ", "").replace("Descargar Peliculas ", "")\
                    .replace("Descargar peliculas ", "").replace("Descargar Todas ", "")\
                    .replace("Descargar Otras ", "").replace("Descargar ", "").replace("Descarga ", "")\
                    .replace("Descargar ", "").replace("Decargar ", "").replace("Bajar ", "")\
                    .replace("HDRIP ", "").replace("HDRiP ", "").replace("HDRip ", "")\
                    .replace("RIP ", "").replace("Rip", "").replace("RiP", "")\
                    .replace("XviD", "").replace("AC3 5.1", "").replace("AC3", "")\
                    .replace("1080p ", "").replace("720p ", "").replace("DVD-Screener ", "")\
                    .replace("TS-Screener ", "").replace("Screener ", "").replace("BdRemux ", "")\
                    .replace("BR ", "").replace("4K UHDrip", "").replace("BDremux", "")\
                    .replace("FULL UHD4K", "").replace("4KULTRA", "").replace("FULLBluRay", "")\
                    .replace("FullBluRay", "").replace("en BluRay", "").replace("BluRay en", "")\
                    .replace("Bluray en", "").replace("BluRay", "").replace("Bonus Disc", "")\
                    .replace("de Cine ", "").replace("TeleCine ", "").replace("latino", "")\
                    .replace("Latino", "").replace("argentina", "").replace("Argentina", "")\
                    .replace("++Sub", "").replace("+-+Sub", "").replace("Directors Cut", "").strip()
        
        title = re.sub(r'\(\d{4}\)$', '', title)
        if re.sub(r'\d{4}$', '', title).strip():
            title = re.sub(r'\d{4}$', '', title)
        if item_local.contentType != "movie":
            title = re.sub(r'\d+x\d+', '', title)
            title = re.sub(r'x\d+', '', title).strip()
        
        if title.endswith("torrent gratis"): title = title[:-15]
        if title.endswith("gratis"): title = title[:-7]
        if title.endswith("torrent"): title = title[:-8]
        if title.endswith("en HD"): title = title[:-6]
        if title.endswith(" -"): title = title[:-2]
        if "en espa" in title: title = title[:-11]
        
        item_local.quality = item_local.quality.replace("gratis ", "")
        if "HDR" in title:
            title = title.replace(" HDR", "")
            if not "HDR" in item_local.quality:
                item_local.quality += " HDR"
        
        title = title.strip()
        title_alt = title_alt.strip()
        item_local.quality = item_local.quality.strip()

        if not title:                               #Usamos solo el title_alt en caso de que no exista el título original
            title = title_alt
            if not title:
                title = "SIN TITULO"
        
        #Limpieza final del título y guardado en las variables según su tipo de contenido
        title = scrapertools.remove_htmltags(title)
        item_local.title = title
        item_local.from_title = title               #Guardamos esta etiqueta para posible desambiguación de título
        if item_local.contentType == "movie":
            item_local.contentTitle = title
        else:
            item_local.contentSerieName = title
        
        #Guardamos el resto de variables del vídeo
        item_local.url = scrapedurl
        if not item_local.url.startswith("http"):                               #Si le falta el http.: lo ponemos
            item_local.url = scrapertools.find_single_match(item_local.channel_host, '(\w+:)//') + item_local.url
        item_local.thumbnail = scrapedthumbnail
        if not item_local.thumbnail.startswith("http"):                         #Si le falta el http.: lo ponemos
            item_local.thumbnail = scrapertools.find_single_match(item_local.channel_host, \
                    '(\w+:)//') + item_local.thumbnail
        item_local.contentThumbnail = item_local.thumbnail

        #Guardamos el año que puede venir en la url, por si luego no hay resultados desde TMDB
        year = ''
        if item_local.contentType == "movie": 
            year = scrapertools.find_single_match(scrapedurl, r'(\d{4})')
        if year >= "1900" and year <= "2040" and year != "2020":
            item_local.infoLabels['year'] = year
            #title_subs += [year]
        else:
            item_local.infoLabels['year'] = '-'
        
        #Guarda la variable temporal que almacena la info adicional del título a ser restaurada después de TMDB
        item_local.title_subs = title_subs
        
        #Ahora se filtra por idioma, si procede, y se pinta lo que vale.  Excluye categorías en otros idiomas.
        #if config.get_setting('filter_languages', channel_py) > 0 and item.extra2 != 'categorias':
        #    itemlist = filtertools.get_link(itemlist, item_local, list_language)
        #else:
        itemlist.append(item_local.clone())                                     #Si no, pintar pantalla
        
        #logger.debug(item_local)

    #Pasamos a TMDB la lista completa Itemlist
    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    
    #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
    item, itemlist = generictools.post_tmdb_listado(item, itemlist)

    if len(itemlist) == 0:
        itemlist.append(Item(channel=item.channel, action="mainlist", 
                    title="No se ha podido cargar el listado"))
    else:
        if url_next_page:
            itemlist.append(Item(channel=item.channel, action="listado", 
                    title="[COLOR gold][B]Pagina siguiente >> [/B][/COLOR]" + 
                    str(post_num) + " de " + str(total_pag), url=url_next_page, 
                    next_page=next_page, cnt_pag=cnt_pag, post_num=post_num, 
                    total_pag=total_pag, pag=pag, modo=modo, extra=item.extra))
                
    #logger.debug(url_next_page + " / " + next_page + " / " + str(matches_cnt) + 
    #                " / " + str(cnt_pag)+ " / " + str(total_pag)  + " / " + str(pag)  
    #                + " / " + modo + " / " + item.extra)
    
    return itemlist

def listado_busqueda(item):
    logger.info()
    
    #logger.debug(item)

    item, host_alt = verify_host(item, host)                            # Actualizamos la url del host
    item.category_new = item.category
    
    if channel_clone_name == "*** DOWN ***":                            #Ningún clones activo !!!
        itemlist.append(item.clone(action='', title="[COLOR yellow]Ningún canal NewPct1 activo[/COLOR]"))    
        return itemlist                             #si no hay más datos, algo no funciona, pintamos lo que tenemos y salimos
    
    itemlist = []
    cnt_tot = 40                                    # Poner el num. máximo de items por página.  Dejamos que la web lo controle
    cnt_title = 0                                                       # Contador de líneas insertadas en Itemlist
    cnt_pag = 0                                                         # Contador de líneas leídas de Matches
    timeout_search = timeout * 2                                        # Timeout un poco más largo para las búsquedas
    if timeout_search < 5:
        timeout_search = 5                                              # Timeout un poco más largo para las búsquedas
    data = ''

    if item.cnt_pag:
        cnt_pag = item.cnt_pag                                          # Se guarda en la lista de páginas anteriores en Item
        del item.cnt_pag
    if item.totalItems:
        del item.totalItems
    if item.text_bold:
        del item.text_bold
    if item.text_color:
        del item.text_color

    #Sistema de paginado para evitar páginas vacías o semi-vacías en casos de búsquedas con series con muchos episodios
    title_lista = []                    # Guarda la lista de series que ya están en Itemlist, para no duplicar lineas
    if item.title_lista:                                        # Si viene de una pasada anterior, la lista ya estará guardada
        title_lista = item.title_lista                                  # Se usa la lista de páginas anteriores en Item
    title_lista_alt = []
    for url in title_lista:
        title_lista_alt += [url]                                        #hacemos una copia no vinculada de title_lista
    matches = []
    cnt_next = 0
    total_pag = 1
    post_num = 1
    inicio = time.time()                                    # Controlaremos que el proceso no exceda de un tiempo razonable
    fin = inicio + 5                                                            # Después de este tiempo pintamos (segundos)
    
    #Máximo num. de líneas permitidas por TMDB. Máx de 5 páginas por Itemlist para no degradar el rendimiento
    while cnt_title <= cnt_tot and cnt_next < 10 and fin > time.time():

        data = ''
        try:
            data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url, 
                    post=item.post, timeout=timeout_search).data)
            #data = unicode(data, "utf-8", errors="replace").encode("utf-8")
        except:
            logger.error(traceback.format_exc())
        
        cnt_next += 1
        #seleccionamos el bloque que nos interesa
        pattern2 = None
        if item.extra == "novedades":
            pattern = '<div class="content">.*?<ul class="noticias(.*?)<\/div><!-- end .content -->'
            if not scrapertools.find_single_match(data, pattern) and not \
                            '<h3><strong>( 0 ) Resultados encontrados </strong>' in data:
                pattern = '<div class="content">.*?<ul class="noticias(.*?)<\/li><\/ul><\/form><\/div>'
                if not scrapertools.find_single_match(data, pattern) and not \
                            '<h3><strong>( 0 ) Resultados encontrados </strong>' in data:
                    pattern = 'patron|'
                    pattern += '<div class="content">.*?<ul class="noticias(.*?)<\/div><!-- end .content -->|'
                    pattern += '<div class="content">.*?<ul class="noticias(.*?)<\/li><\/ul><\/form><\/div>'
        elif scrapertools.find_single_match(data, '"torrentName":'):
            pattern = '"torrentName":\s*"([^"]+)",\s*"calidad":\s*(?:"([^"]+)"|null),.*?'
            pattern += '"torrentSize":\s*"([^"]+)",\s*"imagen":\s*"([^"]+)","guid":"([^"]+)"'
        else:
            pattern = '<ul class="%s">(.*?)</ul>' % item.pattern
        if not data or (not scrapertools.find_single_match(data, pattern) and not \
                    '<h3><strong>( 0 ) Resultados encontrados </strong>' in data):
            item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
            if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
                item, itemlist = generictools.post_tmdb_listado(item, itemlist)     #Llamamos al método para el pintado del error
                return itemlist                                                     #Salimos
            
            logger.error("ERROR 01: LISTADO_BUSQUEDA: La Web no responde o ha cambiado de URL: " 
                    + item.url + ' / POST: ' + item.post + " / DATA: " + data)
            #Si no hay datos consistentes, llamamos al método de fail_over para que encuentre un canal que esté activo y pueda gestionar el submenú
            item, data = generictools.fail_over_newpct1(item, pattern, timeout=timeout_search)
        
        if not data:                                                                #Si no ha logrado encontrar nada, salimos
            itemlist.append(item.clone(action='', title="[COLOR yellow]" + item.channel.capitalize() 
                    + '[/COLOR]: Ningún canal NewPct1 activo'))    
            itemlist.append(item.clone(action='', title=item.category + 
                    ': ERROR 01: LISTADO_BUSQUEDA:.  La Web no responde o ha cambiado de URL. ' 
                    + 'Si la Web está activa, reportar el error con el log'))
            if len(itemlist) > 2:
                #Pasamos a TMDB la lista completa Itemlist
                tmdb.set_infoLabels(itemlist, __modo_grafico__)
                #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
                item, itemlist = generictools.post_tmdb_listado(item, itemlist)
            return itemlist                                 #si no hay más datos, algo no funciona, pintamos lo que tenemos
        elif item.channel_alt:                              #Si ha habido fail-over, lo comento
            host_alt = host_alt.replace(item.channel_alt, item.channel)

        #Obtiene la dirección de la próxima página, si la hay
        try:
            post_actual = item.post     #Guardamos el post actual por si hay overflow de Itemlist y hay que hechar marcha atrás
            # Probamos para descargas2020 y pctnew
            if scrapertools.find_single_match(data, '"total":\d+,"all":(\d+),'):
                total_pag = int(scrapertools.find_single_match(data, '"total":\d+,"all":(\d+),'))
                post = int(scrapertools.find_single_match(item.post, '\&pg=(\d+)')) + 1
                page_size = int(scrapertools.find_single_match(data, '"total":\d+,"all":\d+,"items":(\d+),'))
                if post > total_pag or page_size < 30:
                    post = False
                    cnt_next = 99                           #No hay más páginas.  Salir del bucle después de procesar ésta
            #Probamos si es Novedades o Planetatorrent, sino, el resto
            elif scrapertools.find_single_match(data, '<ul class="pagination">.*?' + 
                    '<a\s*href="([^"]+pg[\/|=])(\d+)">Next<\/a>.*?<a\s*href="[^"]' + 
                    '+pg[\/|=](\d+)">Last<\/a>'):
                get, post, total_pag = scrapertools.find_single_match(data, \
                    '<ul class="pagination">.*?<a\s*href="([^"]+pg[\/|=])(\d+)">Next' + '<\/a>.*?<a\s*href="[^"]+pg[\/|=](\d+)">Last<\/a>')
            else:
                get, post, total_pag = scrapertools.find_single_match(data, \
                    '<ul class="pagination">.*?<a\s*href="([^"]+)"(?:\s*onClick=' + '".*?\(\'([^"]+)\'\);">Next<\/a>.*?onClick=".*?\(\'([^"]+)\'\)' + 
                    ';">Last<\/a>)')
        except:
            post = False
            cnt_next = 99                                   #No hay más páginas.  Salir del bucle después de procesar ésta
            logger.error(traceback.format_exc())

        if post:                                            #puntero a la siguiente página.  Cada página de la web tiene 30 entradas
            if "pg" in item.post:
                item.post = re.sub(r"pg=(\d+)", "pg=%s" % post, item.post)
            else:
                item.post += "&pg=%s" % post
            post_num = int(post)-1                                              #Guardo página actual

        # Preparamos un patron que pretence recoger todos los datos significativos del video
        #seleccionamos el bloque que nos interesa
        if item.extra == "novedades":
            pattern = '<div class="content">.*?<ul class="noticias(.*?)<\/li><\/ul><\/form><\/div>'
            if not scrapertools.find_single_match(data, pattern):
                pattern = '<div class="content">.*?<ul class="noticias(.*?)<\/div><!-- end .content -->'  
        else:
            pattern = '<ul class="%s">(.*?)</ul>' % item.pattern
        data_alt = data
        if not scrapertools.find_single_match(data, '"torrentName":'):
            data = scrapertools.find_single_match(data, pattern)
        if item.extra == "novedades":
            pattern = '<a href="(?P<scrapedurl>[^"]+)"\s?'                      #url
            pattern += 'title="(?P<scrapedtitle>[^"]+)"[^>]*>'                  #título
            pattern += '<img[^>]*src="(?P<scrapedthumbnail>[^"]+)"?.*?'         #thumb
            pattern += '<\/h2>\s*<\/a>\s*<span.*?">(?P<calidad>.*?)?'           #calidad
            pattern += '<(?P<year>.*?)?'                                        #año
            pattern += '>Tama.*?\s(?P<size>\d+[.|\s].*?[GB|MB])?\s?<\/strong>'  #tamaño (significativo para peliculas)
        elif scrapertools.find_single_match(data, '"torrentName":'):
            pattern = '"torrentName":\s*"([^"]+)",\s*"calidad":\s*(?:"([^"]+)"|null),.*?'
            pattern += '"torrentSize":\s*"([^"]+)",\s*"imagen":\s*"([^"]+)","guid":"([^"]+)"()'
        else:
            pattern = '<li[^>]*>\s*<a href="(?P<scrapedurl>[^"]+)"\s*'          #url
            pattern += 'title="(?P<scrapedtitle>[^"]+)">\s*'                    #título
            pattern += '<img.*?src="(?P<scrapedthumbnail>[^"]+)?".*?'           #thumb
            pattern += '<h2.*?(?P<calidad>\[.*?)?<\/h2.*?'                      #calidad
            pattern += '<span.*?>\d+-\d+-(?P<year>\d{4})?<\/span>*.?'           #año
            pattern += '<span.*?>(?P<size>\d+[\.|\s].*?[GB|MB])?<\/span>'       #tamaño (significativo para peliculas)
        
        matches_alt = re.compile(pattern, re.DOTALL).findall(data)
        if not matches_alt and not '<h3><strong>( 0 ) Resultados encontrados </strong>' \
                    in data_alt and not '<ul class="noticias-series"></ul></form></div>' + \
                    '<!-- end .page-box -->' in data_alt:                       #error
            logger.error("ERROR 02: LISTADO_BUSQUEDA: Ha cambiado la estructura de la Web " + 
                    " / PATRON: " + pattern + " / DATA: " + data_alt)
            itemlist.append(item.clone(action='', title=item.category + 
                    ': ERROR 02: LISTADO_BUSQUEDA: Ha cambiado la estructura de la Web.  ' 
                    + 'Reportar el error con el log'))
            if len(itemlist) > 1:
                #Pasamos a TMDB la lista completa Itemlist
                tmdb.set_infoLabels(itemlist, __modo_grafico__)
                #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
                item, itemlist = generictools.post_tmdb_listado(item, itemlist)
            return itemlist                                 #si no hay más datos, algo no funciona, pintamos lo que tenemos
        
        #Ahora se hace una simulación para saber cuantas líneas podemos albergar en este Itemlist.
        #Se controlará cuantas páginas web se tienen que leer para rellenar la lista, sin pasarse
        
        title_lista_alt_for = []                #usamos está lista de urls para el FOR, luego la integramos en la del WHILE
        for _scrapedurl, _scrapedtitle, _scrapedthumbnail, _calidad, _year, _size in matches_alt:
            
            scrapedurl = _scrapedurl
            scrapedtitle = _scrapedtitle
            scrapedthumbnail = _scrapedthumbnail
            calidad = _calidad
            year = _year
            size = _size
            
            if scrapertools.find_single_match(data, '"torrentName":'):
                scrapedtitle = scrapertools.find_single_match(_scrapedurl, '^(.*?)\s*(?:-(?:\s*[T|t]emp)|\[|$)')
                calidad = _scrapedtitle
                size = _scrapedthumbnail
                scrapedthumbnail = _calidad.replace('\\', '')
                scrapedthumbnail = urlparse.urljoin(host_alt, scrapedthumbnail)
                scrapedurl = _year.replace('\\', '')
                scrapedurl = urlparse.urljoin(host_alt, scrapedurl)
                year = _size
                
            #Realiza un control de las series que se añaden, ya que el buscador devuelve episodios y no las series completas
            #Se analiza si la url de la serie ya se ha listado antes.  Si es así, esa entrada se ignora
            #Cuando llega al num. máximo de entradas por página, la pinta y guarda los contadores y la lista de series
            scrapedurl_alt = scrapedurl
            if "pelisyseries.com" in host_alt:                                      #Excepción para mispelisyseries.com.
                scrapedurl_alt = re.sub(r'\/[c|C]ap.*?-\d+-al-\d+', '', scrapedurl_alt) #Scrapeo el capítulo para hacerlo serie
                scrapedurl_alt = re.sub(r'\/[c|C]ap.*?-\d+', '', scrapedurl_alt)    #Scrapeo el capítulo para hacerlo serie
                scrapedurl_alt = re.sub(r'\/[c|C]ap.*?-', '', scrapedurl_alt)       #Scrapeo el capítulo para hacerlo serie
                scrapedurl_alt = re.sub(r'\/\d{5,7}', '', scrapedurl_alt)           #Scrapeo el capítulo para hacerlo serie
                if scrapedurl_alt in title_lista_alt:                       # si ya se ha tratado, pasamos al siguiente item
                    continue                                                # solo guardamos la url para series y docus

            if scrapedurl_alt in title_lista_alt or scrapedurl_alt in title_lista_alt_for or scrapedthumbnail in title_lista_alt or scrapedthumbnail in title_lista_alt_for:                        # si ya se ha tratado, pasamos al siguiente item
                continue                                                    # solo guardamos la url para series y docus

            if ".com/serie" in scrapedurl or "/serie" in scrapedurl or "-serie" \
                    in scrapedurl or "varios/" in scrapedurl:
                title_lista_alt_for += [scrapedurl_alt]
                title_lista_alt_for += [scrapedthumbnail]

            if "juego/" in scrapedurl:                                          # no mostramos lo que no sean videos
                continue
            
            #Verificamos si el idioma está dentro del filtro, si no pasamos
            if not lookup_idiomas_paginacion(item, scrapedurl, scrapedtitle, calidad, list_language):
                continue
            cnt_title += 1                                                      # Sería una línea real más para Itemlist
            
            #Control de página
            if cnt_title >= cnt_tot*0.65:           #si se acerca al máximo num. de lineas por pagina, tratamos lo que tenemos
                cnt_next = 99                       #Casi completo, no sobrepasar con la siguiente página
                if cnt_title > cnt_tot or item.extra == 'novedades':
                    if item.extra != 'novedades': cnt_title = 99                #Sobrepasado el máximo.  Ignoro página actual
                    item.post = post_actual         #Restauro puntero "next" a la página actual, para releearla en otra pasada
                    post_num -= 1                   #Restauro puntero a la página actual en el pie de página
                    break

        if cnt_title <= cnt_tot:
            matches.extend(matches_alt)             #Acumulamos las entradas a tratar. Si nos hemos pasado ignoro última página
            title_lista_alt.extend(title_lista_alt_for)
    
    #logger.debug("PATRON: " + pattern)
    #logger.debug(matches)
    #logger.debug(title_lista_alt)
    #logger.debug(data)

    cnt_title = 0
    for _scrapedurl, _scrapedtitle, _scrapedthumbnail, _calidad, _scrapedyear, _scrapedsize in matches:
        cnt_pag += 1
        
        scrapedurl = _scrapedurl
        scrapedtitle = _scrapedtitle
        scrapedthumbnail = _scrapedthumbnail
        calidad = _calidad
        year = _scrapedyear
        size = _scrapedsize
        
        if scrapertools.find_single_match(data, '"torrentName":'):
            scrapedtitle = scrapertools.find_single_match(_scrapedurl, '^(.*?)\s*(?:-(?:\s*[T|t]emp)|\[|$)')
            calidad = _scrapedtitle
            size = _scrapedthumbnail
            scrapedthumbnail = _calidad.replace('\\', '')
            scrapedthumbnail = urlparse.urljoin(host_alt, scrapedthumbnail)
            scrapedurl = _scrapedyear.replace('\\', '')
            scrapedurl = urlparse.urljoin(host_alt, scrapedurl)
            year = _scrapedsize
        
        #Realiza un control de las series que se añaden, ya que el buscador devuelve episodios y no las series completas
        #Se analiza si la url de la serie ya se ha listado antes.  Si es así, esa entrada se ignora
        #El control de página ya se ha realizado más arriba
        if "pelisyseries.com" in host_alt:                              #Excepción para mispelisyseries.com.
                scrapedurl_alt = scrapedurl
                scrapedurl_alt = re.sub(r'\/[c|C]ap.*?-\d+-al-\d+', '', scrapedurl_alt) #Scrapeo el capítulo para hacerlo serie
                scrapedurl_alt = re.sub(r'\/[c|C]ap.*?-\d+', '', scrapedurl_alt)    #Scrapeo el capítulo para hacerlo serie
                scrapedurl_alt = re.sub(r'\/[c|C]ap.*?-', '', scrapedurl_alt)       #Scrapeo el capítulo para hacerlo serie
                scrapedurl_alt = re.sub(r'\/\d{5,7}', '', scrapedurl_alt)           #Scrapeo el capítulo para hacerlo serie
                if scrapedurl_alt in title_lista:                       # si ya se ha tratado, pasamos al siguiente item
                    continue                                            # solo guardamos la url para series y docus

        if scrapedurl in title_lista or scrapedthumbnail in title_lista:    # si ya se ha tratado, pasamos al siguiente item
            continue                                                        # solo guardamos la url para series y docus

        if ".com/serie" in scrapedurl or "/serie" in scrapedurl or "-serie" in \
                    scrapedurl or "varios/" in scrapedurl:
            if "pelisyseries.com" in host_alt:
                title_lista += [scrapedurl_alt]
            else:
                title_lista += [scrapedurl]
                title_lista += [scrapedthumbnail]
                
        if ("juego/" in scrapedurl or "xbox" in scrapedurl.lower()) and not "/serie" \
                    in scrapedurl or "xbox" in scrapedtitle.lower() or "windows" in \
                    scrapedtitle.lower() or "windows" in calidad.lower() or "nintendo" \
                    in scrapedtitle.lower() or "xbox" in calidad.lower() or "epub" in \
                    calidad.lower() or "pdf" in calidad.lower() or "pcdvd" in calidad.lower() \
                    or "crack" in calidad.lower():                              # no mostramos lo que no sean videos
            continue
        #cnt_title += 1                                                         # Sería una línea real más para Itemlist
        
        #Creamos una copia de Item para cada contenido
        item_local = item.clone()
        if item_local.category_new:
            del item_local.category_new
        if item_local.tipo:
            del item_local.tipo
        if item_local.totalItems:
            del item_local.totalItems
        if item_local.post:
            del item_local.post
        if item_local.pattern:
            del item_local.pattern
        if item_local.title_lista:
            del item_local.title_lista
        item_local.adult = True
        del item_local.adult
        item_local.folder = True
        del item_local.folder
        if item_local.intervencion:
            del item_local.intervencion
        item_local.title = ''
        item_local.context = "['buscar_trailer']"
        item_local.contentType = ""
        url = scrapedurl
        
        title_subs = []
        
        #Si son episodios sueltos de Series que vienen de Novedades, se busca la url de la Serie
        if item.extra == "novedades" and "/serie" in url and episodio_serie == 1:
            item_local.url = url
            item_local.extra2 = 'serie_episodios'                   #Creamos acción temporal excluyente para otros clones
            if item_local.category == 'Mispelisyseries':            #Esta web no gestiona bien el cambio de episodio a Serie
                pattern = 'class="btn-torrent">.*?window.location.href = "([^"]+)";'        #Patron para .torrent
                #Como no hay datos consistentes, llamamos al método de fail_over para que encuentre un canal que esté activo y pueda gestionar el cambio de episodio por serie
                item_local, data_serie = generictools.fail_over_newpct1(item_local, pattern, timeout=timeout_search)
            else:
                try:
                    data_serie = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage\
                        (item_local.url, timeout=timeout).data)
                except:
                    logger.error(traceback.format_exc())

                pattern = '<div\s*class="content.*?">.*?<h1.*?>.*?<a\s*href="([^"]+)"'      #Patron para Serie completa
                if not data_serie or (not scrapertools.find_single_match(data_serie, pattern) \
                        and not '<h3><strong>( 0 ) Resultados encontrados </strong>' in data \
                        and not '<ul class="noticias-series"></ul></form></div><!-- end .page-box -->' \
                        in data):
                    logger.error("ERROR 01: LISTADO_BUSQUEDA: La Web no responde o ha cambiado de URL: " 
                        + item_local.url + " / DATA: " + data_serie)
                    #Si no hay datos consistentes, llamamos al método de fail_over para que encuentre un canal que esté activo y pueda gestionar el cambio de episodio por serie
                    item_local, data_serie = generictools.fail_over_newpct1(item_local, \
                        pattern, timeout=timeout)
            
            if not data_serie:                                                  #Si no ha logrado encontrar nada, salimos
                title_subs += ["ERR"]
            
            elif item_local.channel_alt:                                        #Si ha habido fail-over, lo comento
                url = url.replace(item_local.channel_alt, item_local.category.lower())
                title_subs += ["ALT"]

            try:
                pattern = '<div\s*class="content.*?">.*?<h1.*?>.*?<a\s*href="([^"]+)"'      #Patron para Serie completa
                item_local.url = scrapertools.find_single_match(data_serie, pattern)
                #Son series VO mal formadas?
                if (item.post and '775' in item.post and 'vo/' not in item_local.url) or 'vo/' in url:      
                    item_local.url = item_local.url.replace('/series/', '/series-vo/')
                    
                #Son series HD formada como series estándar?
                #if (scrapertools.find_single_match(item_local.quality, '\d{3, 4}p')) and '/series/' in item_local.url:
                if 'hd/' in url:
                    item_local.url = item_local.url.replace('/series/', '/series-hd/')
                    
                #item_local.url = re.sub(r'\/\d+$', '/', item_local.url)        #Quitamos el ID de la serie por compatib.
                if item_local.url:
                    title_subs += ["Episodio %sx%s" % (scrapertools.find_single_match(url, \
                                '\/temp.*?-(\d+)-?\/cap.*?-(\d+(?:-al-\d+)?)-?\/'))]
                    url = item_local.url
            except:
                logger.error(traceback.format_exc())
                
            #logger.debug(item_local.url)
            
        if item.extra == "novedades" and "/serie" in url:
            if not item_local.url or episodio_serie == 0:
                item_local.url = url
                if scrapertools.find_single_match(url, '\/temp.*?-(\d+)-?\/cap.*?-(\d+(?:-al-\d+)?)-?\/'):
                    title_subs += ["Episodio %sx%s" % (scrapertools.find_single_match(url, \
                                '\/temp.*?-(\d+)-?\/cap.*?-(\d+(?:-al-\d+)?)-?\/'))]
                else:
                    title_subs += ["Episodio 1x01"]

        #Establecemos los valores básicos en función del tipo de contenido
        if (".com/serie" in url or "/serie" in url or "-serie" in url) and not \
                        "/miniseries" in url and (not "/capitulo" in url or \
                        "pelisyseries.com" in item_local.channel_host):         #Series
            item_local.action = "episodios"
            item_local.contentType = "tvshow"
            item_local.season_colapse = True
            item_local.extra = "series"
        elif "varios/" in url or "/miniseries" in url:                          #Documentales y varios
            item_local.action = "findvideos"
            item_local.contentType = "movie"
            item_local.extra = "varios"
        elif "/capitulo" in url:                                                #Documentales y varios
            item_local.action = "findvideos"
            item_local.contentType = "episode"
            item_local.extra = "series"
        else:                                                                   #Películas
            item_local.action = "findvideos"
            item_local.contentType = "movie"
            item_local.extra = "peliculas"
        
        # Limpiamos títulos, Sacamos datos de calidad, audio y lenguaje
        title = re.sub('\r\n', '', scrapedtitle).decode('iso-8859-1').encode('utf8').strip()
        #title = re.sub('\r\n', '', scrapedtitle).decode('utf-8').encode('utf-8').strip()
        title = title.replace("á", "a").replace("é", "e").replace("í", "i")\
                    .replace("ó", "o").replace("ú", "u").replace("ü", "u")\
                    .replace("ï¿½", "ñ").replace("Ã±", "ñ")
        
        item_local.quality = scrapertools.htmlclean(calidad)

        #Determinamos y marcamos idiomas distintos del castellano
        item_local.language = []
        if "[vos" in title.lower()  or "v.o.s" in title.lower() or "vo" in title.lower() \
                    or "subs" in title.lower() or ".com/pelicula/" in url  or \
                    ".com/series-vo" in url or "-vo/" in url or "vos" in calidad.lower() \
                    or "vose" in calidad.lower() or "v.o.s" in calidad.lower() or \
                    "sub" in calidad.lower() or ".com/peliculas-vo" in item.url:
            item_local.language += ["VOS"]
        title = title.replace(" [Subs. integrados]", "").replace(" [subs. Integrados]", "")\
                    .replace(" [VOSE", "").replace(" [VOS", "").replace(" (V.O.S.E)", "")\
                    .replace(" VO", "").replace("Subtitulos", "")
        if "latino" in title.lower() or "argentina" in title.lower() or "-latino/" \
                    in url or "latino" in calidad.lower() or "argentina" in calidad.lower():
            item_local.language += ["LAT"]
        
        #Guardamos info de 3D en calidad y limpiamos
        if "3d" in title.lower():
            if not "3d" in item_local.quality.lower():
                item_local.quality = "3D " + item_local.quality
            calidad3D = scrapertools.find_single_match(title, r'\s(3[d|D]\s\w+)')
            if calidad3D:
                item_local.quality = item_local.quality.replace("3D", calidad3D)
            title = re.sub(r'\s3[d|D]\s\w+', '', title)
            title = re.sub(r'\s3[d|D]', '', title)
            if "imax" in title.lower():
                item_local.quality = item_local.quality + " IMAX"
                title = title.replace(" IMAX", "").replace(" imax", "")
        if "2d" in title.lower():
            title = title.replace("(2D)", "").replace("(2d)", "").replace("2D", "").replace("2d", "")
            title_subs += ["[2D]"]
        
        #Extraemos info adicional del título y la guardamos para después de TMDB
        if ("temp" in title.lower() or "cap" in title.lower()) and item_local.contentType != "movie":
            #Eliminamos Temporada de Series, solo nos interesa la serie completa
            title = re.sub(r'-?\s*[t|T]emp\w+ \d+ Comp\w+\d+[x|X]\d+', ' Completa', title)
            title = re.sub(r'-?\s*[t|T]emp\w+.?\d+.?[c|C]ap\w+.?\d+.?(?:al|Al|y).?\d+', '', title)
            title = re.sub(r'-?\s*[t|T]emp\w+ \d+x\d+', '', title)
            title = re.sub(r'-?\s*[t|T]emp\w+ \d+', '', title)
            title = re.sub(r'-?\s*[t|T]emp\w+.*?\d+', '', title)
            title = re.sub(r'\s*[t|T]emp.*?\d+[x|X]\d+', '', title)
            title = re.sub(r'\s*[t|T]emp.*?\d+', '', title)
            title = re.sub(r'\s*[c|C]ap.*?\d+ al \d+', '', title)
            title = re.sub(r'\s*[c|C]ap.*?\d+', '', title)
        if "audio" in title.lower():                                    #Reservamos info de audio para después de TMDB
            title_subs += ['[%s]' % scrapertools.find_single_match(title, r'(\[[a|A]udio.*?\])')]
            title = re.sub(r'\[[a|A]udio.*?\]', '', title)
        if "[dual" in title.lower() or "multileng" in title.lower() or "multileng" \
                    in item_local.quality.lower() or (("espa" in title.lower() or \
                    "spani" in title.lower()) and "VOS" in item_local.language):
            item_local.language[0:0] = ["DUAL"]
            title = re.sub(r'\[[D|d]ual.*?\]', '', title)
            title = re.sub(r'\[[M|m]ultileng.*?\]', '', title)
            item_local.quality = re.sub(r'\[[M|m]ultileng.*?\]', '', item_local.quality)
        if "duolog" in title.lower():
            title_subs += ["[Saga]"]
            title = title.replace(" Duologia", "").replace(" duologia", "")\
                    .replace(" Duolog", "").replace(" duolog", "")
        if "trilog" in title.lower():
            title_subs += ["[Saga]"]
            title = title.replace(" Trilogia", "").replace(" trilogia", "")\
                    .replace(" Trilog", "").replace(" trilog", "")
        if "extendida" in title.lower() or "v.e." in title.lower()or "v e " in title.lower():
            title_subs += ["[V. Extendida]"]
            title = title.replace("Version Extendida", "").replace("(Version Extendida)", "")\
                    .replace("V. Extendida", "").replace("VExtendida", "")\
                    .replace("V Extendida", "").replace("V.Extendida", "")\
                    .replace("V  Extendida", "").replace("V.E.", "").replace("V E ", "")
        if "saga" in title.lower():
            title = title.replace(" Saga Completa", "").replace(" saga completa", "")\
                    .replace(" Saga", "").replace(" saga", "")
            title_subs += ["[Saga]"]
        if "colecc" in title.lower() or "completa" in title.lower():
            title = title.replace(" Coleccion", "").replace(" coleccion", "")\
                    .replace(" Colecci", "").replace(" colecci", "").replace(" Completa", "")\
                    .replace(" completa", "").replace(" COMPLETA", "")
            title_subs += ["[Saga]"]
        if scrapertools.find_single_match(title, r'(- [m|M].*?serie ?\w+)'):
            title = re.sub(r'- [m|M].*?serie ?\w+', '', title)
            title_subs += ["[Miniserie]"]

        if not item_local.language:
            item_local.language = ["CAST"]
        
        #Limpiamos restos en título
        title = title.replace("Castellano", "").replace("castellano", "").replace("inglés", "")\
                    .replace("ingles", "").replace("Inglés", "").replace("Ingles", "")\
                    .replace("Ingl", "").replace("Engl", "").replace("Calidad", "")\
                    .replace("de la Serie", "").replace("Spanish", "")
        
        #Limpiamos cabeceras y colas del título
        title = re.sub(r'Descargar\s\w+\-\w+', '', title)
        title = re.sub(r'\(COMPLE.*?\)', '', title)
        
        title = title.replace("Ver online Serie", "").replace("Ver online ", "")\
                    .replace("Descarga Serie HD ", "").replace("Descargar Serie HD ", "")\
                    .replace("Descarga Serie ", "").replace("Descargar Serie ", "")\
                    .replace("Ver en linea ", "").replace("Ver en linea", "")\
                    .replace("en Full HD", "").replace("en hd ", "").replace("en HD ", "")\
                    .replace("MicroHD", "").replace("HD ", "").replace("(Proper)", "")\
                    .replace("HDTV", "").replace("RatDVD", "").replace("DVDRiP", "")\
                    .replace("DVDRIP", "").replace("DVDRip", "").replace("DVDR", "")\
                    .replace("DVD9", "").replace("DVD", "").replace("DVBRIP", "")\
                    .replace("DVB", "").replace("LINE", "").replace("calidad", " ")\
                    .replace("- ES ", "").replace("ES ", "").replace("COMPLETA", "")\
                    .replace("Serie Animada", " ").replace("(", "-").replace(")", "-")\
                    .replace(".", " ").strip()
        
        title = title.replace("Descargar torrent ", "").replace("Descarga Gratis", "")\
        .replace("Descarga gratis", "").replace("Descargar Gratis", "").replace("Descargar gratis", "")\
        .replace("en gratis", "").replace("gratis gratis", "").replace("Gratisgratis", "")\
        .replace("Descargar Estreno ", "").replace("Descargar Estrenos ", "")\
        .replace("Pelicula en latino ", "").replace("Descargar Pelicula ", "")\
        .replace("Descargar pelicula ", "").replace("Descargar Peliculas ", "")\
        .replace("Descargar peliculas ", "").replace("Descargar Todas ", "")\
        .replace("Descargar Otras ", "").replace("Descargar ", "").replace("Descarga ", "")\
        .replace("Descargar ", "").replace("Decargar ", "").replace("Bajar ", "")\
        .replace("HDRIP ", "").replace("HDRiP ", "").replace("HDRip ", "")\
        .replace("RIP ", "").replace("Rip", "").replace("RiP", "").replace("XviD", "")\
        .replace("AC3 5.1", "").replace("AC3", "").replace("1080p ", "").replace("720p ", "")\
        .replace("DVD-Screener ", "").replace("TS-Screener ", "").replace("Screener ", "")\
        .replace("BdRemux ", "").replace("BR ", "").replace("4K UHDrip", "")\
        .replace("BDremux", "").replace("FULL UHD4K", "").replace("4KULTRA", "")\
        .replace("FULLBluRay", "").replace("FullBluRay", "").replace("en BluRay", "")\
        .replace("BluRay en", "").replace("Bluray en", "").replace("BluRay", "")\
        .replace("Bonus Disc", "").replace("de Cine ", "").replace("TeleCine ", "")\
        .replace("latino", "").replace("Latino", "").replace("argentina", "")\
        .replace("Argentina", "").replace("++Sub", "").replace("+-+Sub", "")\
        .replace("Directors Cut", "").strip()
        
        title = re.sub(r'\(\d{4}\)$', '', title)
        if re.sub(r'\d{4}$', '', title).strip():
            title = re.sub(r'\d{4}$', '', title)
        if item_local.contentType != "movie":
            title = re.sub(r'\d+x\d+', '', title)
            title = re.sub(r'x\d+', '', title).strip()
        
        if "pelisyseries.com" in host_alt and item_local.contentType == "tvshow":
            titulo = ''
            title = title.lower()
            title = re.sub(r'\d+[x|X]\d+', '', title)
            while len(title) > 0:
                palabra = scrapertools.find_single_match(title, r'(^[A-Za-z0-9_.-?ñ]+)')
                if not palabra:
                    break
                title = title.replace(palabra, '')
                title = re.sub(r'^\s+\??', '', title)
                title = re.sub(r'^-\s?', '', title)
                titulo += palabra + " "
                palabra = ""
            title = titulo.title()
        
        if title.endswith("torrent gratis"): title = title[:-15]
        if title.endswith("gratis"): title = title[:-7]
        if title.endswith("torrent"): title = title[:-8]
        if title.endswith("en HD"): title = title[:-6]
        if title.endswith(" -"): title = title[:-2]
        if "en espa" in title: title = title[:-11]
        #title = re.sub(r'^\s', '', title)
        title = title.replace("a?o", 'año').replace("a?O", 'año').replace("A?o", 'Año')\
                    .replace("A?O", 'Año').strip()

        #Preparamos calidad
        item_local.quality = item_local.quality.replace("[ ", "").replace(" ]", "")     #Preparamos calidad para Series
        item_local.quality = re.sub(r'\[\d{4}\]', '', item_local.quality)               #Quitar año, si lo tiene
        item_local.quality = re.sub(r'\[Cap.*?\]', '', item_local.quality)              #Quitar episodios, si lo tiene
        item_local.quality = re.sub(r'\[Docu.*?\]', '', item_local.quality)             #Quitar tipo contenidos, si lo tiene
        #Mirar si es DUAL
        if "VOS" in item_local.language and "DUAL" not in item_local.language and \
                    ("[sp" in item_local.quality.lower() or "espa" in item_local.quality.lower() \
                    or "cast" in item_local.quality.lower() or "spani" in item_local.quality.lower()):
            item_local.language[0:0] = ["DUAL"]    
        if ("[es-" in item_local.quality.lower() or (("cast" in item_local.quality.lower() \
                    or "espa" in item_local.quality.lower() or "spani" in \
                    item_local.quality.lower()) and ("eng" in item_local.quality.lower() \
                    or "ing" in item_local.quality.lower()))) and "DUAL" not in \
                    item_local.language:                                                #Mirar si es DUAL
            item_local.language[0:0] = ["DUAL"]                                         #Salvar DUAL en idioma
            item_local.quality = re.sub(r'\[[es|ES]-\w+]', '', item_local.quality)      #borrar DUAL
        item_local.quality = re.sub(r'[\s|-][c|C]aste.+', '', item_local.quality)       #Borrar después de Castellano
        item_local.quality = re.sub(r'[\s|-][e|E]spa.+', '', item_local.quality)        #Borrar después de Español
        item_local.quality = re.sub(r'[\s|-|\[][s|S]pani.+', '', item_local.quality)    #Borrar después de Spanish
        item_local.quality = re.sub(r'[\s|-][i|I|e|E]ngl.+', '', item_local.quality)    #Borrar después de Inglés-English
        item_local.quality = item_local.quality.replace("[", "").replace("]", " ")\
                    .replace("ALTA DEFINICION", "HDTV").replace(" Cap", "")
        #Borrar palabras innecesarias restantes
        item_local.quality = item_local.quality.replace("Espaol", "").replace("Español", "")\
                    .replace("Espa", "").replace("Castellano ", "").replace("Castellano", "")\
                    .replace("Spanish", "").replace("English", "").replace("Ingles", "")\
                    .replace("Latino", "").replace("+Subs", "").replace("-Subs", "")\
                    .replace("Subs", "").replace("VOSE", "").replace("VOS", "").strip()
        
        #Limpieza final del título y guardado en las variables según su tipo de contenido
        item_local.title = title
        item_local.from_title = title                       #Guardamos esta etiqueta para posible desambiguación de título
        if item_local.contentType == "movie":
            item_local.contentTitle = title
            size = size.replace(".", ",")
            item_local.quality = '%s [%s]' % (item_local.quality, size)
        else:
            item_local.contentSerieName = title
        
        #Guardamos el resto de variables del vídeo
        item_local.url = url
        if not item_local.url.startswith("http"):                               #Si le falta el http.: lo ponemos
            item_local.url = scrapertools.find_single_match(item_local.channel_host, 
                    '(\w+:)//') + item_local.url
        item_local.thumbnail = scrapedthumbnail
        if not item_local.thumbnail.startswith("http"):                         #Si le falta el http.: lo ponemos
            item_local.thumbnail = scrapertools.find_single_match(item_local.channel_host, 
                    '(\w+:)//') + item_local.thumbnail
        item_local.contentThumbnail = item_local.thumbnail

        #Guardamos el año que puede venir en la url, por si luego no hay resultados desde TMDB
        try:
            year = int(scrapedyear)
        except:
            year = ""
        year = str(year)
        if year >= "1900" and year <= "2040" and year != "2020":
            item_local.infoLabels['year'] = year
            #title_subs += [year]
        else:
            item_local.infoLabels['year'] = '-'
        
        #Guarda la variable temporal que almacena la info adicional del título a ser restaurada después de TMDB
        item_local.title_subs = title_subs

        # Codigo para rescatar lo que se pueda en pelisy.series.com de Series para la Videoteca.  la URL apunta al capítulo y no a la Serie.  Nombre de Serie frecuentemente en blanco. Se obtiene de Thumb, así como el id de la serie
        if ("/serie" in item_local.url or "-serie" in item_local.url) and \
                    "pelisyseries.com" in item_local.channel_host:
            #Extraer la calidad de la serie basados en la info de la url
            if "seriehd" in item_local.url:
                calidad_mps = "series-hd/"
            elif "serievo" in item_local.url or "serie-vo" in item_local.url:
                calidad_mps = "series-vo/"
            else:
                calidad_mps = "series/"
                
            if "no_image" in scrapedthumbnail:
                real_title_mps = item_local.title
            else:
                real_title_mps = re.sub(r'.*?\/\d+_', '', scrapedthumbnail)
                real_title_mps = re.sub(r'\.\w+.*?', '', real_title_mps)
            
            #Extraer el ID de la serie desde Thumbs (4 dígitos).  Si no hay, nulo
            if "/0_" not in scrapedthumbnail and not "no_image" in scrapedthumbnail:
                serieid = scrapertools.find_single_match(scrapedthumbnail, r'\/\w\/(?P<serieid>\d+)')
                if len(serieid) > 5:
                    serieid = ""
            else:
                serieid = ""

            #detectar si la url creada de tvshow es válida o hay que volver atras 
            url_id = host_alt + calidad_mps + real_title_mps + "/" + serieid    #A veces necesita el serieid...
            url_tvshow = host_alt + calidad_mps + real_title_mps + "/"          #... otras no.  A probar...
            
            #Leemos la página, a ver  si es una página de episodios
            data_serie = data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage\
                        (url_id, timeout=timeout, ignore_response_code=True).data)
            data_serie = unicode(data_serie, "iso-8859-1", errors="replace").encode("utf-8")
            data_serie = data_serie.replace("chapters", "buscar-list")
            
            pattern = '<ul class="%s">(.*?)</ul>' % "buscar-list"       #Patrón de lista de episodios
            if not scrapertools.find_single_match(data_serie, pattern) and serieid:     #no es válida la página, 
                                                                                        #intentarlo con la otra url
                data_serie = data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage\
                        (url_tvshow, timeout=timeout, ignore_response_code=True).data)
                data_serie = unicode(data_serie, "iso-8859-1", errors="replace").encode("utf-8")
                data_serie = data_serie.replace("chapters", "buscar-list")
                
                if not scrapertools.find_single_match(data_serie, pattern):     #No ha habido suerte ...
                    item_local.contentType = "movie"                            #tratarlo el capítulo como película
                    item_local.extra = "peliculas"
                else:
                    item_local.url = url_tvshow                                 #Cambiamos url de episodio por el de serie
            else:
                item_local.url = url_id                                         #Cambiamos url de episodio por el de serie

            #logger.debug("url: " + item_local.url + " / title o/n: " + item_local.title 
            #            + " / " + real_title_mps + " / calidad_mps : " + calidad_mps 
            #            + " / contentType : " + item_local.contentType)
            
            item_local.title = real_title_mps.replace('-', ' ').title().strip() #Esperemos que el nuevo título esté bien
            item_local.contentSerieName = item_local.title
        
        #Ahora se filtra por idioma, si procede, y se pinta lo que vale.  Excluye categorías en otros idiomas.
        if config.get_setting('filter_languages', channel_py) > 0 and item.extra2 != 'categorias':
            itemlist = filtertools.get_link(itemlist, item_local, list_language)
        else:
            itemlist.append(item_local.clone())                                 #Si no, pintar pantalla
            
        cnt_title = len(itemlist)                                               #Contador de líneas añadidas
        
        #logger.debug(item_local)
        
    #if not item.category_new:              #Si este campo no existe es que viene de la primera pasada de una búsqueda global
    #    return itemlist                    #Retornamos sin pasar por la fase de maquillaje para ahorra tiempo

    #Pasamos a TMDB la lista completa Itemlist
    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    
    #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
    item, itemlist = generictools.post_tmdb_listado(item, itemlist)

    if post:
        itemlist.append(item.clone(channel=item.channel, action="listado_busqueda", 
                    title="[COLOR gold][B]Pagina siguiente >> [/B][/COLOR]" + 
                    str(post_num) + " de " + str(total_pag), thumbnail=get_thumb("next.png"), 
                    title_lista=title_lista, cnt_pag=cnt_pag, language=''))
                                   
    #logger.debug("Titulos: " + str(len(itemlist)) + " Matches: " + str(len(matches)) + 
    #                " Post: " + str(item.post) + " / " + str(post_actual) + " / " 
    #                + str(total_pag))

    return itemlist

def findvideos(item):
    logger.info()
    from core import videolibrarytools
    itemlist = []
    itemlist_t = []                                                             #Itemlist total de enlaces
    itemlist_f = []                                                             #Itemlist de enlaces filtrados
    if not item.language:
        item.language = ['CAST']                                                #Castellano por defecto

    #logger.debug(item)
    
    item, host_alt = verify_host(item, host)                                    # Actualizamos la url del host

    # Cualquiera de las tres opciones son válidas
    # item.url = item.url.replace(".com/",".com/ver-online/")
    # item.url = item.url.replace(".com/",".com/descarga-directa/")
    item.url = item.url.replace("/descarga-torrent/descargar", "/descargar")
    torrent_tag = item.channel_host + 'descargar-torrent/'
    
    #Función para limitar la verificación de enlaces de Servidores para Ver online y Descargas
    #Inicializamos las variables por si hay un error en medio del proceso
    channel_exclude = []
    ver_enlaces = []
    ver_enlaces_veronline = -1                                      #Ver todos los enlaces Ver Online
    verificar_enlaces_veronline = -1                                #Verificar todos los enlaces Ver Online
    verificar_enlaces_veronline_validos = True                      #"¿Contar sólo enlaces 'verificados' en Ver Online?"
    excluir_enlaces_veronline = []                                  #Lista vacía de servidores excluidos en Ver Online
    ver_enlaces_descargas = 0                                       #Ver todos los enlaces Descargar
    verificar_enlaces_descargas = -1                                #Verificar todos los enlaces Descargar
    verificar_enlaces_descargas_validos = True                      #"¿Contar sólo enlaces 'verificados' en Descargar?"
    excluir_enlaces_descargas = []                                  #Lista vacía de servidores excluidos en Descargar
    
    if not item.videolibray_emergency_urls:                         #Si es un proceso nomal...
        try:
            #Leemos las opciones de permitir Servidores para Ver Online y Descargas
            #Cargamos en .json del canal para ver las listas de valores en  settings
            channel_exclude = channeltools.get_channel_json(item.channel)
            for settings in channel_exclude['settings']:                        #Se recorren todos los settings
                if settings['id'] == "clonenewpct1_excluir1_enlaces_veronline": #lista de enlaces a excluir
                    max_excl = int(settings['max_excl'])                        #Máximo número de servidores excluidos
                    channel_exclude = settings['lvalues']                       #Cargamos la lista de servidores
                if settings['id'] == "clonenewpct1_ver_enlaces_descargas":      #Número de enlances a ver o verificar
                    ver_enlaces = settings['lvalues']                           #Cargamos la lista de num. de enlaces
        
            #Primer loop para enlaces de Ver Online.  
            #Carga la variable de ver
            ver_enlaces_veronline = int(config.get_setting("clonenewpct1_ver_enlaces_veronline", item.channel))
            if ver_enlaces_veronline == 1:                                  #a "Todos" le damos valor -1.  Para "No" dejamos 0
                ver_enlaces_veronline = -1
            if ver_enlaces_veronline > 1:                                   #para los demás valores, tomamos los de la lista
                ver_enlaces_veronline = int(ver_enlaces[ver_enlaces_veronline])
        
            #Carga la variable de verificar
            verificar_enlaces_veronline = int(config.get_setting("clonenewpct1_verificar_enlaces_veronline", item.channel))
            if verificar_enlaces_veronline == 1:                            #a "Todos" le damos valor -1.  Para "No" dejamos 0
                verificar_enlaces_veronline = -1
            if verificar_enlaces_veronline > 1:                             #para los demás valores, tomamos los de la lista
                verificar_enlaces_veronline = int(ver_enlaces[verificar_enlaces_veronline])

            #Carga la variable de contar sólo los servidores verificados
            verificar_enlaces_veronline_validos = int(config.get_setting\
                    ("clonenewpct1_verificar_enlaces_veronline_validos", item.channel))

            #Carga la variable de lista de servidores excluidos
            x = 1
            for x in range(1, max_excl+1):                                  #recorremos todas las opciones de canales exluidos
                valor = str(config.get_setting("clonenewpct1_excluir%s_enlaces_veronline" % x, item.channel))
                valor = int(valor)
                if valor > 0:                                               #Evitamos "No"
                    excluir_enlaces_veronline += [channel_exclude[valor]]   #Añadimos el nombre de servidor excluido a la lista
                x += 1

            #Segundo loop para enlaces de Descargar.  
            #Carga la variable de ver
            ver_enlaces_descargas = int(config.get_setting("clonenewpct1_ver_enlaces_descargas", item.channel))
            if ver_enlaces_descargas == 1:                                  #a "Todos" le damos valor -1.  Para "No" dejamos 0
                ver_enlaces_descargas = -1
            if ver_enlaces_descargas > 1:                                   #para los demás valores, tomamos los de la lista
                ver_enlaces_descargas = int(ver_enlaces[ver_enlaces_descargas])
        
            #Carga la variable de verificar
            verificar_enlaces_descargas = int(config.get_setting\
                    ("clonenewpct1_verificar_enlaces_descargas", item.channel))
            if verificar_enlaces_descargas == 1:                            #a "Todos" le damos valor -1.  Para "No" dejamos 0
                verificar_enlaces_descargas = -1
            if verificar_enlaces_descargas > 1:                             #para los demás valores, tomamos los de la lista
                verificar_enlaces_descargas = int(ver_enlaces[verificar_enlaces_descargas])

            #Carga la variable de contar sólo los servidores verificados
            verificar_enlaces_descargas_validos = int(config.get_setting\
                    ("clonenewpct1_verificar_enlaces_descargas_validos", item.channel))

            #Carga la variable de lista de servidores excluidos
            x = 1
            for x in range(1, max_excl+1):                                  #recorremos todas las opciones de canales exluidos
                valor = str(config.get_setting("clonenewpct1_excluir%s_enlaces_descargas" % x, item.channel))
                valor = int(valor)
                if valor > 0:                                               #Evitamos "No"
                    excluir_enlaces_descargas += [channel_exclude[valor]]   #Añadimos el nombre de servidor excluido a la lista
                x += 1

        except Exception, ex:                                   #En caso de error, lo mostramos y reseteamos todas las variables
            logger.error("Error en la lectura de parámentros del .json del canal: " 
                    + item.channel + " \n%s" % ex)
            #Mostrar los errores
            logger.error(ver_enlaces_veronline)
            logger.error(verificar_enlaces_veronline)
            logger.error(verificar_enlaces_veronline_validos)
            logger.error(excluir_enlaces_veronline)
            logger.error(ver_enlaces_descargas)
            logger.error(verificar_enlaces_descargas)
            logger.error(verificar_enlaces_descargas_validos)
            logger.error(excluir_enlaces_descargas)
            
            #Resetear las variables a sus valores por defecto
            ver_enlaces_veronline = -1                          #Ver todos los enlaces Ver Online
            verificar_enlaces_veronline = -1                    #Verificar todos los enlaces Ver Online
            verificar_enlaces_veronline_validos = True          #"¿Contar sólo enlaces 'verificados' en Ver Online?"
            excluir_enlaces_veronline = []                      #Lista vacía de servidores excluidos en Ver Online
            ver_enlaces_descargas = 0                           #Ver todos los enlaces Descargar
            verificar_enlaces_descargas = -1                    #Verificar todos los enlaces Descargar
            verificar_enlaces_descargas_validos = True          #"¿Contar sólo enlaces 'verificados' en Descargar?"
            excluir_enlaces_descargas = []                      #Lista vacía de servidores excluidos en Descargar

    # Descarga la página
    data = ''
    data_servidores = ''
    enlaces_ver = ''
    try:
        url_servidores = item.url
        category_servidores = item.category
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url, timeout=timeout).data)
        data = data.replace("$!", "#!").replace("'", "\"").replace("Ã±", "ñ").replace("//pictures", "/pictures")
        data_servidores = data                                  #salvamos data para verificar servidores, si es necesario
        data_servidores_stat = False
    except:                                                     #La web no responde.  Probemos las urls de emergencia
        logger.error(traceback.format_exc())
    
    patron = 'class="btn-torrent">.*?window.location.href = (?:parseURL\()?"(.*?)"\)?;'     #Patron para .torrent
    patron_mult = 'torrent:check:status|' + patron + '|<a href="([^"]+)"\s?title='
    patron_mult += '"[^"]+"\s?class="btn-torrent"'
    if not scrapertools.find_single_match(data, patron):
        patron_alt = '<\s*script\s*type="text\/javascript"\s*>\s*var\s*[lt\s*=\s*"[^"]*"'   #Patron .torrent
        patron_alt += '(?:,\s*idlt\s*=\s*"[^"]*")?,\s*nalt\s*=\s*"([^"]+)"'                 #descargas2020
        if scrapertools.find_single_match(data, patron_alt):
            patron = patron_alt
        else:
            patron_alt = '<a\s*href="javascript:;"\s*onclick="if\s*\(!window.__cfRLUnblockHandlers\)'
            patron_alt += '\s*return\s*false;\s*post\([^\{]+{name:\s*"([^"]+).torrent"}\);"'    #Patron .torrent Pctnew
            if scrapertools.find_single_match(data, patron_alt):
                patron = patron_alt
            else:
                patron_alt = '<a href="([^"]+)"\s?title="[^"]+"\s?class="btn-torrent"'      #Patron .torrent (planetatorrent)
                if scrapertools.find_single_match(data, patron_alt):
                    patron = patron_alt
    
    torrent_link = scrapertools.find_single_match(data, patron)
    if 'planetatorrent' in item.url or 'mispelisyseries' in item.url:           # Cambio en clones porque redirigen mal
        torrent_tag = torrent_tag.replace('/descargar-torrent/', '/download/')
        torrent_link = torrent_link.replace('/descargar-torrent/', '/download/')
        torrent_link = torrent_link + '.torrent'
        torrent_link = torrent_link.replace('/.torrent', '.torrent')
    url_torr = urlparse.urljoin(torrent_tag, torrent_link)
    if not url_torr.startswith("http"):                                         #Si le falta el http.: lo ponemos
        url_torr = scrapertools.find_single_match(item.channel_host, '(\w+:)//') + url_torr

    #Verificamos si se ha cargado una página, y si además tiene la estructura correcta
    local_torr = ''
    size = ''
    size = generictools.get_torrent_size(url_torr, timeout=timeout)             #Buscamos si hay .torrent y el tamaño
    if not data or not scrapertools.find_single_match(data, patron) or not size:    # Si no hay datos o url, error
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)  #Llamamos al método para el pintado del error
        else:
            logger.error("ERROR 01: FINDVIDEOS: La Web no responde o la URL es erronea: " + 
                item.url + " / PATRON: " + patron + " / DATA: " + data)

        if item.emergency_urls and not item.videolibray_emergency_urls:         #Hay urls de emergencia?
            itemlist.append(item.clone(action='', title=item.category + 
                ': ERROR 01: FINDVIDEOS:.  La Web no responde o la URL es erronea. ' 
                + 'Si la Web está activa, reportar el error con el log', folder=False))
            item.url = item.emergency_urls[0][0]                                #Restauramos la url del .Torrent
            if item.url.startswith("\\") or item.url.startswith("/"):
                from core import filetools
                if item.contentType == 'movie':
                    FOLDER = config.get_setting("folder_movies")
                else:
                    FOLDER = config.get_setting("folder_tvshows")
                local_torr = filetools.join(config.get_videolibrary_path(), FOLDER, item.url)
            try:
                enlaces_ver = item.emergency_urls[1]            #Restauramos los datos iniciales de los Servidores Directos
            except:
                logger.error(traceback.format_exc())
            item.armagedon = True                                               #Marcamos la situación como catastrófica 
            data = 'xyz123'                                                     #Para que no haga más preguntas
        else:
            #Si no hay datos consistentes, llamamos al método de fail_over para que 
            #encuentre un canal que esté activo y pueda gestionar el vídeo
            item, data = generictools.fail_over_newpct1(item, patron_mult, timeout=timeout)

    if not data:                                            #Si no ha logrado encontrar nada, verificamos si hay servidores
        cnt_servidores = 0
        item.category = category_servidores                                     #restauramos valores originales
        item.url = url_servidores
        
        # Sistema de scrapeo de servidores creado por Torrentlocula, compatible con otros clones de Newpct1
        patron = '<div class=\"box1\"[^<]+<img src=\"([^<]+)?" style[^<]+><\/div'
        patron += '[^<]+<div class="box2">([^<]+)?<\/div[^<]+<div class="box3">([^<]+)?'
        patron += '<\/div[^<]+<div class="box4">([^<]+)?<\/div[^<]+<div class="box5">'
        patron += '<a href=(.*?)? rel.*?<\/div[^<]+<div class="box6">([^<]+)?<'
        enlaces_ver = re.compile(patron, re.DOTALL).findall(data_servidores)
        enlaces_descargar = enlaces_ver
        
        for logo, servidor, idioma, calidad, enlace, title in enlaces_ver:  #buscamos enlaces de servidores de ver-online
            if ver_enlaces_veronline == 0:                                  #Si no se quiere Ver Online, se sale del bloque
                break
            if "ver" in title.lower():
                cnt_servidores += 1

        if cnt_servidores == 0:
            item, data_servidores = generictools.fail_over_newpct1(item, patron, timeout=timeout)    #intentamos recuperar servidores
            
            #Miramos si ha servidores
            if not data_servidores:                                         #Si no ha logrado encontrar nada nos vamos
                itemlist.append(item.clone(action='', title="[COLOR yellow]" + 
                        item.channel.capitalize() + '[/COLOR]: Ningún canal NewPct1 activo', 
                        folder=False))    
                itemlist.append(item.clone(action='', title=item.category + 
                        ': ERROR 01: FINDVIDEOS:.  La Web no responde o la URL es erronea. ' 
                        + 'Si la Web está activa, reportar el error con el log', 
                        folder=False))
                if item.videolibray_emergency_urls:
                    return item
                else:
                    return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos
        
        data = data_servidores                                                  #restauramos los datos
        data_servidores_stat = True                                             #Marcamos como que los hemos usado

    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
    data = data.replace("$!", "#!").replace("'", "\"").replace("Ã±", "ñ").replace("//pictures", "/pictures")

    # patrón para la url torrent
    patron = 'class="btn-torrent">.*?window.location.href = (?:parseURL\()?"(.*?)"\)?;' #Patron para .torrent
    if not scrapertools.find_single_match(data, patron):
        patron = '<\s*script\s*type="text\/javascript"\s*>\s*var\s*dl\s*=\s*"([^"]+)"'  #Patron .torrent descargas2020
        if not scrapertools.find_single_match(data, patron):
            patron = '<\s*script\s*type="text\/javascript"\s*>\s*var\s*[lt\s*=\s*"[^"]*"'   #Patron .torrent
            patron += '(?:,\s*idlt\s*=\s*"[^"]*")?,\s*nalt\s*=\s*"([^"]+)"'                 #descargas2020
        if not scrapertools.find_single_match(data, patron):
            patron = '<a href="([^"]+)"\s?title="[^"]+"\s?class="btn-torrent"'  #Patron para .torrent (planetatorrent)
    url_torr = urlparse.urljoin(torrent_tag, scrapertools.find_single_match(data, patron))
    if not url_torr.startswith("http"):                                         #Si le falta el http.: lo ponemos
        url_torr = scrapertools.find_single_match(item.channel_host, '(\w+:)//') + url_torr

    #buscamos el tamaño del .torrent
    if not size:
        size = scrapertools.find_single_match(data, '<div class="entry-left".*?><a href=' + \
                    '".*?span class=.*?>Size:<\/strong>?\s(\d+?\.?\d*?\s\w[b|B])<\/span>')
    if not size:                                                                #Para planetatorrent
        size = scrapertools.find_single_match(data, '<div class="fichas-box"><div class=' + \
                    '"entry-right"><div style="[^"]+"><span class="[^"]+"><strong>' + \
                    'Size:<\/strong>?\s(\d+?\.?\d*?\s\w[b|B])<\/span>')
    size = size.replace(".", ",")                                               #sustituimos . por , porque Unify lo borra
    if not size:
        size = scrapertools.find_single_match(item.quality, '\s?\[(\d+.?\d*?\s?\w\s?[b|B])\]')
    if not size and not item.armagedon and not item.videolibray_emergency_urls and url_torr:
        size = generictools.get_torrent_size(url_torr, local_torr=local_torr)   #Buscamos el tamaño en el .torrent
    if size:
        size = size.replace('GB', 'G·B').replace('Gb', 'G·b').replace('MB', 'M·B')\
                        .replace('Mb', 'M·b').replace('.', ',')
    item.quality = re.sub(r'\s\[\d+,?\d*?\s\w\s?[b|B]\]', '', item.quality)     #Quitamos size de calidad, si lo traía
    
    # Si tiene contraseña, la guardamos
    patron_pass = '<input\s*type="text"\s*id="txt_password"\s*name="[^"]+"\s*onClick="[^"]+"\s*value="([^"]+)"'
    if scrapertools.find_single_match(data, patron_pass):
        item.password = scrapertools.find_single_match(data, patron_pass)
    
    item.torrent_info = '%s' % size                                             #Agregamos size
    if not item.unify:
        item.torrent_info = '[%s]' % item.torrent_info.strip().strip(',')
    
    #Llamamos al método para crear el título general del vídeo, con toda la información obtenida de TMDB
    if not item.videolibray_emergency_urls:
        item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)

    #Generamos una copia de Item para trabajar sobre ella
    item_local = item.clone()

    # Verificamos la url torrent o usamos la de emergencia
    if not item.armagedon:
        item_local.url = url_torr
        if item_local.url == 'javascript:;': 
            item_local.url = ''                                                 #evitamos url vacías
        item_local.url = item_local.url.replace(" ", "%20")                     #sustituimos espacios por %20, por si acaso
    
        if item_local.url and item.emergency_urls:                              #la url no está verificada
            item_local.torrent_alt = item.emergency_urls[0][0]                  #Guardamos la url del .Torrent ALTERNATIVA
        
    if not item_local.url:                                                      #error en url?
        logger.error("ERROR 02: FINDVIDEOS: El archivo Torrent no existe o ha " + 
                    "cambiado la estructura de la Web " + " / PATRON: " + patron + 
                    " / DATA: " + data)
        if item.emergency_urls:                                                 #Hay urls de emergencia?
            item_local.url = item.emergency_urls[0][0]                          #Restauramos la url del .Torrent
            item.armagedon = True                                               #Marcamos la situación como catastrófica 
            itemlist.append(item.clone(action='', title=item.category + 
                    ': [COLOR hotpink]Usando enlaces de emergencia[/COLOR]', folder=False))
    
    #logger.debug("Patron: " + patron + " url: " + item_local.url)
    #logger.debug(data)
    
    #Si es un lookup para cargar las urls de emergencia en la Videoteca...
    if item.videolibray_emergency_urls:
        if item.channel_host: del item.channel_host
        item.emergency_urls = []
        item.emergency_urls.append([item_local.url])                            #Guardamos el enlace del .torrent
    #... si no, ejecutamos el proceso normal
    else:
        #Ahora pintamos el link del Torrent, si lo hay
        if item_local.url:		                                                # Hay Torrent ?
            quality = item_local.quality
            if item.armagedon:                                                  #Si es catastrófico, lo marcamos
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
            item_local.quality = quality.replace("--", "").replace("[]", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()
            
            item_local.alive = "??"                                             #Calidad del link sin verificar
            item_local.action = "play"                                          #Visualizar vídeo
            item_local.server = "torrent"                                       #Servidor
            
            itemlist_t.append(item_local.clone())                               #Pintar pantalla, si no se filtran idiomas
            
            # Requerido para FilterTools
            if config.get_setting('filter_languages', channel_py) > 0:          #Si hay idioma seleccionado, se filtra
                itemlist_f = filtertools.get_link(itemlist_f, item_local, list_language)  #Pintar pantalla, si no está vacío
        
            logger.debug("TORRENT: " + item_local.url + " / title gen/torr: " + 
                    item.title + " / " + item_local.title + " / calidad: " + 
                    item_local.quality + " / tamaño: " + size + " / content: " + 
                    item_local.contentTitle + " / " + item_local.contentSerieName)
            #logger.debug(item_local)

        if len(itemlist_f) > 0:                                                 #Si hay entradas filtradas...
            itemlist.extend(itemlist_f)                                         #Pintamos pantalla filtrada
        else:                                                                       
            if config.get_setting('filter_languages', channel_py) > 0 and len(itemlist_t) > 0: #Si no hay entradas filtradas ...
                thumb_separador = get_thumb("next.png")                         #... pintamos todo con aviso
                itemlist.append(Item(channel=item.channel, url=item.channel_host, 
                    title="[COLOR red][B]NO hay elementos con el idioma seleccionado[/B][/COLOR]", 
                    thumbnail=thumb_separador, folder=False))
            itemlist.extend(itemlist_t)                                         #Pintar pantalla con todo si no hay filtrado
        

    itemlist_t = []                                                             #Itemlist total de enlaces
    itemlist_f = []                                                             #Itemlist de enlaces filtrados
    # VER vídeos, descargar vídeos un link,  o múltiples links
    data = scrapertools.find_single_match(data, '<div id="tab1" class="tab_content"(.*?<\/ul>(?:<div.*?>)?<\/div><\/div><\/div>)')      #Seleccionar el bloque para evitar duplicados
    
    host_dom = item.channel_host.replace("https://", "").replace("http://", "").replace("www.", "")
    data = data.replace("http://tumejorserie.com/descargar/url_encript.php?link=", "(")
    data = re.sub(r'javascript:;" onClick="popup\("(?:http:)?\/\/(?:www.)?' + host_dom + 
                    '\w{1,9}\/library\/include\/ajax\/get_modallinks.php\?links=', "", data)

    # Nuevo sistema de scrapeo de servidores creado por Torrentlocula, compatible con otros clones de Newpct1
    patron = '<div class=\"box1\"[^<]+<img src=\"([^<]+)?" style[^<]+><\/div[^<]'
    patron += '+<div class="box2">([^<]+)?<\/div[^<]+<div class="box3">([^<]+)?'
    patron += '<\/div[^<]+<div class="box4">([^<]+)?<\/div[^<]+<div class="box5">'
    patron += '<a href=(.*?)? rel.*?<\/div[^<]+<div class="box6">([^<]+)?<'

    if not item.armagedon:                                                      #Si es un proceso normal, seguimos
        enlaces_ver = re.compile(patron, re.DOTALL).findall(data)
    
    if not enlaces_ver:                                                         #Si no hay enlaces, hay urls de emergencia?
        try:
            enlaces_ver = item.emergency_urls[1]            #Guardamos los datos iniciales de los Servidores Directos
            item.armagedon = True                                               #Activamos el modo catástrofe
        except:
            logger.error(traceback.format_exc())
        
    enlaces_descargar = enlaces_ver
    #logger.debug(enlaces_ver)
    
    #Si es un lookup para cargar las urls de emergencia en la Videoteca, lo hacemos y nos vamos si más
    if item.videolibray_emergency_urls:
        emergency_urls_directos = []
        i = 0
        for logo, servidor, idioma, calidad, enlace, title in enlaces_ver:
            if "ver" in title.lower():
                emergency_urls_directos.append(enlaces_ver[i])
            i += 1
        item.emergency_urls.append(emergency_urls_directos)
        return item
    
    #Recorre todos los links de VER, si está permitido
    cnt_enl_ver = 1
    cnt_enl_verif = 1
    for logo, servidor, idioma, calidad, enlace, title in enlaces_ver:
        if ver_enlaces_veronline == 0:                                  #Si no se quiere Ver Online, se sale del bloque
            break
        
        if "ver" in title.lower():
            item_local = item.clone()
            servidor = servidor.replace("streamin", "streaminto")

            if servidor.capitalize() in excluir_enlaces_veronline:      #Servidor excluido, pasamos al siguiente
                continue
            mostrar_server = True
            if config.get_setting("hidepremium"):                       #Si no se aceptan servidore premium, se ignoran
                mostrar_server = servertools.is_server_enabled(servidor)
                
            #logger.debug("VER: url: " + enlace + " / title: " + title + 
            #        " / servidor: " + servidor + " / idioma: " + idioma)
            
            #Si el servidor es válido, se comprueban si los links están activos
            if mostrar_server:
                try:
                    if cnt_enl_ver <= ver_enlaces_veronline or ver_enlaces_veronline == -1:
                        devuelve = servertools.findvideosbyserver(enlace, servidor) #existe el link ?
                        if verificar_enlaces_veronline == 0:
                            cnt_enl_ver += 1
                    else:
                        break                           #Si se ha agotado el contador de verificación, se sale de Ver Online
                    
                    if devuelve:                                                #Hay link
                        enlace = devuelve[0][1]                                 #Se guarda el link
                        item_local.alive = "??"                                 #Se asume poe defecto que es link es dudoso
                        if verificar_enlaces_veronline != 0:                    #Se quiere verificar si el link está activo?
                            if cnt_enl_verif <= verificar_enlaces_veronline or \
                                        verificar_enlaces_veronline == -1: #contador?
                                #Llama a la subfunción de check_list_links(itemlist) para cada link de servidor
                                item_local.alive = servertools.check_video_link(enlace, servidor, timeout=timeout)       #activo el link ?
                                if verificar_enlaces_veronline_validos: #Los links tienen que ser válidos para contarlos?
                                    if item_local.alive == "Ok":        #Sí
                                        cnt_enl_verif += 1                      #Movemos los contadores
                                        cnt_enl_ver += 1                        #Movemos los contadores
                                else:                                   #Si no es necesario que sean links válidos, sumamos
                                    cnt_enl_verif += 1                          #Movemos los contadores
                                    cnt_enl_ver += 1                            #Movemos los contadores
                            else:
                                break                   #Si se ha agotado el contador de verificación, se sale de Ver Online

                        if item.armagedon:                              #Si es catastrófico, lo marcamos
                            item_local.quality = '[/COLOR][COLOR hotpink][E] [COLOR limegreen]%s' \
                                    % item_local.quality
                        #Si el link no está activo se ignora
                        if "??" in item_local.alive:                            #dudoso
                            item_local.title = '[COLOR yellow][?][/COLOR] [COLOR yellow]' + \
                                    '[%s][/COLOR] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' \
                                    % (servidor.capitalize(), item_local.quality, \
                                    str(item_local.language))
                        elif "no" in item_local.alive.lower():                  #No está activo.  Lo preparo, pero no lo pinto
                            item_local.title = '[COLOR red][%s][/COLOR] [COLOR yellow]' % item_local.alive + \
                                    '[%s][/COLOR] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' \
                                    % (servidor.capitalize(), item_local.quality, str(item_local.language))
                            logger.debug(item_local.alive + ": ALIVE / " + title + 
                                    " / " + servidor + " / " + enlace)
                            raise
                        else:                                           #Sí está activo
                            item_local.title = '[COLOR yellow][%s][/COLOR] [COLOR limegreen]' % \
                                    servidor.capitalize() + '[%s][/COLOR] [COLOR red]%s[/COLOR]' % \
                                    (item_local.quality, str(item_local.language))

                        #Preparamos el resto de variables de Item para ver los vídeos en directo    
                        item_local.action = "play"
                        item_local.server = servidor
                        item_local.url = enlace
                        
                        #Preparamos título y calidad, quitamos etiquetas vacías
                        item_local.title = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', \
                                '', item_local.title)    
                        item_local.title = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', \
                                '', item_local.title)
                        item_local.title = item_local.title.replace("--", "")\
                                .replace("[]", "").replace("()", "").replace("(/)", "")\
                                .replace("[/]", "").strip()
                        item_local.quality = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]'\
                                , '', item_local.quality)
                        item_local.quality = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', \
                                '', item_local.quality)
                        item_local.quality = item_local.quality.replace("--", "")\
                                .replace("[]", "").replace("()", "").replace("(/)", "")\
                                .replace("[/]", "").strip()
                        
                        itemlist_t.append(item_local.clone())                   #Pintar pantalla, si no se filtran idiomas
                        
                        # Requerido para FilterTools
                        if config.get_setting('filter_languages', channel_py) > 0: #Si hay idioma seleccionado, se filtra
                            itemlist_f = filtertools.get_link(itemlist_f, item_local, \
                                list_language)                                  #Pintar pantalla, si no está vacío

                except:
                    logger.error('ERROR al procesar enlaces VER DIRECTOS: ' + 
                                servidor + ' / ' + enlace)
                    #logger.error(traceback.format_exc())

    if len(itemlist_f) > 0:                                                     #Si hay entradas filtradas...
        itemlist.extend(itemlist_f)                                             #Pintamos pantalla filtrada
    else:                                                                       
        if config.get_setting('filter_languages', channel_py) > 0 and len(itemlist_t) > 0: #Si no hay entradas filtradas ...
            thumb_separador = get_thumb("next.png")                             #... pintamos todo con aviso
            itemlist.append(Item(channel=item.channel, url=item.channel_host, title=\
                        "[COLOR red][B]NO hay elementos con el idioma seleccionado[/B][/COLOR]", 
                        thumbnail=thumb_separador, folder=False))
        itemlist.extend(itemlist_t)                                             #Pintar pantalla con todo si no hay filtrado
    
    itemlist_t = []                                                             #Itemlist total de enlaces
    itemlist_f = []                                                             #Itemlist de enlaces filtrados
    #Ahora vemos los enlaces de DESCARGAR
    if len(enlaces_descargar) > 0 and ver_enlaces_descargas != 0:
        
        #Pintamos un pseudo-título de Descargas
        if not item.unify:                                                      #Si Titulos Inteligentes NO seleccionados:
            itemlist.append(item_local.clone(title="[COLOR gold]**- Enlaces Descargar: -**[/COLOR]", 
                        action="", folder=False))
        else:
            itemlist.append(item_local.clone(title="[COLOR gold] Enlaces Descargar: [/COLOR]", 
                        action="", folder=False))

    #Recorre todos los links de DESCARGAR
    cnt_enl_ver = 1
    cnt_enl_verif = 1
    for logo, servidor, idioma, calidad, enlace, title in enlaces_descargar:
        if ver_enlaces_descargas == 0:
            break

        if "Ver" not in title:
            item_local = item.clone()
            servidor = servidor.replace("uploaded", "uploadedto")
            partes = enlace.split(" ")                                      #Partimos el enlace en cada link de las partes
            title = "Descarga"                      #Usamos la palabra reservada de Unify para que no formatee el título

            if servidor.capitalize() in excluir_enlaces_descargas:          #Servidor excluido, pasamos al siguiente
                continue
            
            #logger.debug("DESCARGAR: url: " + enlace + " / title: " + title + 
            #                " / servidor: " + servidor + " / idioma: " + idioma)
            
            #Recorremos cada una de las partes.  Vemos si el primer link está activo.  Si no lo está ignoramos todo el enlace
            p = 1
            for enlace in partes:
                if not item.unify:                                          #Si titles Inteligentes NO seleccionados:
                    parte_title = "[COLOR yellow][%s][/COLOR] %s (%s/%s) [COLOR limegreen]" % \
                            (servidor.capitalize(), title, p, len(partes)) + \
                            "[%s][/COLOR] [COLOR red]%s[/COLOR]" % (item_local.quality, \
                            str(item_local.language))
                else:
                    title = title.replace('Descarga', 'Descarg.')
                    item_local.quality = '[/COLOR][COLOR white] %s (%s/%s) [/COLOR][COLOR limegreen][%s] ' \
                            % (title, p, len(partes), item.quality)
                    parte_title = "[COLOR yellow][%s]%s[/COLOR] [COLOR red][%s][/COLOR]" % \
                            (servidor.capitalize(), item_local.quality, str(item_local.language))
                p += 1
                mostrar_server = True
                if config.get_setting("hidepremium"):                       #Si no se aceptan servidore premium, se ignoran
                    mostrar_server = servertools.is_server_enabled(servidor)

                #Si el servidor es válido, se comprueban si los links están activos
                if mostrar_server:
                    try:
                        if cnt_enl_ver <= ver_enlaces_descargas or ver_enlaces_descargas == -1:
                            devuelve = servertools.findvideosbyserver(enlace, servidor)     #activo el link ?
                            if verificar_enlaces_descargas == 0:
                                cnt_enl_ver += 1
                        else:
                            ver_enlaces_descargas = 0                       #FORZAR SALIR de DESCARGAS
                            break                           #Si se ha agotado el contador de verificación, se sale de "Enlace"

                        if devuelve:
                            enlace = devuelve[0][1]
                            
                            #Verifica si está activo el primer link.  Si no lo está se ignora el enlace-servidor entero
                            if p <= 2:
                                item_local.alive = "??"                         #Se asume poe defecto que es link es dudoso
                                if verificar_enlaces_descargas != 0:            #Se quiere verificar si el link está activo?
                                    if cnt_enl_verif <= verificar_enlaces_descargas or \
                                                verificar_enlaces_descargas == -1:  #contador?
                                        #Llama a la subfunción de check_list_links(itemlist) para primer link de servidor
                                        item_local.alive = servertools.check_video_link\
                                                (enlace, servidor, timeout=timeout)     #activo el link ?
                                        if verificar_enlaces_descargas_validos: #Los links tienen que ser válidos para contarlos?
                                            if item_local.alive == "Ok":        #Sí
                                                cnt_enl_verif += 1              #Movemos los contadores
                                                cnt_enl_ver += 1                #Movemos los contadores
                                        else:                           #Si no es necesario que sean links válidos, sumamos
                                            cnt_enl_verif += 1                  #Movemos los contadores
                                            cnt_enl_ver += 1                    #Movemos los contadores
                                    else:
                                        ver_enlaces_descargas = 0               #FORZAR SALIR de DESCARGAS
                                        break               #Si se ha agotado el contador de verificación, se sale de "Enlace"
                                
                                if "??" in item_local.alive:                    #dudoso
                                    if not item.unify:                          #Si titles Inteligentes NO seleccionados:
                                        parte_title = '[COLOR yellow][?][/COLOR] %s' % \
                                                (parte_title)
                                    else:
                                        parte_title = '[COLOR yellow]%s[/COLOR]-%s' % \
                                                (item_local.alive, parte_title)
                                elif "no" in item_local.alive.lower():          #No está activo.  Lo preparo, pero no lo pinto
                                    if not item.unify:                          #Si titles Inteligentes NO seleccionados:
                                        parte_title = '[COLOR red][%s][/COLOR] %s' % \
                                            (item_local.alive, parte_title)
                                    else:
                                        parte_title = '[COLOR red]%s[/COLOR]-%s' % \
                                            (item_local.alive, parte_title)
                                    logger.debug(item_local.alive + ": ALIVE / " 
                                            + title + " / " + servidor + " / " + enlace)
                                    raise

                            #Preparamos el resto de variables de Item para descargar los vídeos
                            item_local.action = "play"
                            item_local.server = servidor
                            item_local.url = enlace
                            item_local.title = parte_title.strip()
                            
                            #Preparamos título y calidad, quitamos etiquetas vacías
                            item_local.title = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', \
                                    '', item_local.title)    
                            item_local.title = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', \
                                    '', item_local.title)
                            item_local.title = item_local.title.replace("--", "")\
                                    .replace("[]", "").replace("()", "").replace("(/)", "")\
                                    .replace("[/]", "").strip()
                            item_local.quality = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', \
                                    '', item_local.quality)
                            item_local.quality = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', \
                                    '', item_local.quality)
                            item_local.quality = item_local.quality.replace("--", "")\
                                    .replace("[]", "").replace("()", "").replace("(/)", "")\
                                    .replace("[/]", "").strip()
                            
                            itemlist_t.append(item_local.clone())               #Pintar pantalla, si no se filtran idiomas
                        
                            # Requerido para FilterTools
                            if config.get_setting('filter_languages', channel_py) > 0: #Si hay idioma seleccionado, se filtra
                                itemlist_f = filtertools.get_link(itemlist_f, \
                                    item_local, list_language)                  #Pintar pantalla, si no está vacío

                    except:
                        logger.error('ERROR al procesar enlaces DESCARGAR DIRECTOS: ' 
                                    + servidor + ' / ' + enlace)
                        #logger.error(traceback.format_exc())
                        break
                    
    if len(itemlist_f) > 0:                                                     #Si hay entradas filtradas...
        itemlist.extend(itemlist_f)                                             #Pintamos pantalla filtrada
    else:                                                                       
        if config.get_setting('filter_languages', channel_py) > 0 and len(itemlist_t) > 0: #Si no hay entradas filtradas ...
            thumb_separador = get_thumb("next.png")                             #... pintamos todo con aviso
            itemlist.append(Item(channel=item.channel, url=item.channel_host, title=\
                    "[COLOR red][B]NO hay elementos con el idioma seleccionado[/B][/COLOR]", 
                    thumbnail=thumb_separador, folder=False))
        itemlist.extend(itemlist_t)                                             #Pintar pantalla con todo si no hay filtrado
    
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)                                              #Lanzamos Autoplay

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    
    #logger.debug(item)
    
    json_category = item.category.lower()
    item, host_alt = verify_host(item, host)                                    # Actualizamos la url del host
    if not json_category:
        json_category = item.category.lower()

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
    #if not item.infoLabels['tmdb_id']:
    try:
        tmdb.set_infoLabels(item, True)                                 #TMDB de cada Temp
    except:
        pass
        
    modo_ultima_temp_alt = modo_ultima_temp
    if item.ow_force == "1":                                            #Si hay un traspaso de canal o url, se actualiza todo 
        modo_ultima_temp_alt = False
    
    max_temp = 1
    max_temp_seen = False
    if item.infoLabels['number_of_seasons']:
        max_temp = item.infoLabels['number_of_seasons']
    else:
        modo_ultima_temp_alt = False                                    #No sabemos cuantas temporadas hay
    y = []
    if modo_ultima_temp_alt and item.library_playcounts:                #Averiguar cuantas temporadas hay en Videoteca
        patron = 'season (\d+)'
        matches = re.compile(patron, re.DOTALL).findall(str(item.library_playcounts))
        for x in matches:
            y += [int(x)]
        max_temp = max(y)

    # Si es actualización de la videoteca, no viene en el .nfo el "language" de la serie.  Hay que obtenerlo desde un episodio.json
    if item.library_playcounts:
        try:
            from core import filetools, jsontools
            for key, value in item.library_playcounts.items():
                if scrapertools.find_single_match(key, '\d+x\d+'):
                    break
            if not item.path and item.infoLabels['IMDBNumber']:
                item.path = filetools.join(' ', '%s [%s]' % (item.title, item.infoLabels['IMDBNumber'])).strip()
            epi_json_path = filetools.join(config.get_videolibrary_path(), config.get_setting("folder_tvshows"))
            if epi_json_path in item.path:
                epi_json_path = filetools.join(item.path, '%s [%s].json' % (key, json_category))
            else:
                epi_json_path = filetools.join(epi_json_path, item.path, '%s [%s].json' % (key, json_category))
            epi_json = jsontools.load(filetools.read(epi_json_path))
            if 'language' in epi_json:
                item.language = epi_json['language']
            else:
                item.language = ['CAST']
        except:
            item.language = ['CAST']
            logger.error(traceback.format_exc(1))
    
    data = ''
    data_alt = ''
    """
    try:
        if "pelisyseries.com" in item.url:
            patron = '<ul\s*class="%s">(.*?)<\/ul>' % "chapters"                # item.pattern
        else:
            patron = '<ul\s*class="%s">(.*?)<\/ul>' % "buscar-list"             # item.pattern
        
        data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(item.url, timeout=timeout).data)
        if data: data_alt = scrapertools.find_single_match(data, patron)
    except:                                                                     #Algún error de proceso
        logger.error(traceback.format_exc())

    if "pelisyseries.com" in item.url:
        pattern = '<li[^>]*><div class.*?src="(?P<thumb>[^"]+)?".*?<a class.*?'
        pattern += 'href="(?P<url>[^"]+).*?<h3[^>]+>(?P<info>.*?)?<\/h3>.*?<\/li>'
    else:
        pattern = '<li[^>]*>\s*<a href="(?P<url>[^"]+)"\s*title="[^>]+>\s*<img.*?src="(?P<thumb>[^"]+)?"'
        pattern += '.*?<h2[^>]+>(?P<info>.*?)?<\/h2>'
            
    #Verificamos si se ha cargado una página, y si además tiene la estructura correcta
    if not data_alt or not scrapertools.find_single_match(data_alt, pattern):
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            item, itemlist = generictools.post_tmdb_episodios(item, itemlist)   #Llamamos al método para el pintado del error
            return itemlist                                                     #Salimos
        
        #Si a la url de la serie que se ha quitado el código final, en algunos canales puede dar error
        if not scrapertools.find_single_match(item.url, '\/(\d{4,20})\/*$'):
            patron_series = "var\s*parametros\s*=\s*\{(?:'rating'\s*\:[^']+)?(?:'ratingc'\s*\:[^']+)?"
            patron_series += "(?:'n_votos'\s*\:[^']+)?(?:'id'\s*\:[^,]+,)?'cate'\s*\:\s*'([^']+)'"
            url_serie_nocode = scrapertools.find_single_match(data, patron_series)
            url_serie_nocode = '%s/%s' % (item.url, url_serie_nocode)
            if url_serie_nocode:
                data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage\
                            (url_serie_nocode, timeout=timeout, ignore_response_code=True).data)
                if data: data_alt = scrapertools.find_single_match(data, patron)
        
        if not data_alt or not scrapertools.find_single_match(data_alt, pattern):
            logger.error("ERROR 01: EPISODIOS: La Web no responde o la URL es erronea: " + item.url)
            logger.error(pattern + data)

            #Si no hay datos consistentes, llamamos al método de fail_over para que encuentre un canal que esté activo y pueda gestionar el vídeo
            item, data = generictools.fail_over_newpct1(item, patron, pattern, timeout=timeout)

    if not data:                                                    #No se ha encontrado ningún canal activo para este vídeo
        itemlist.append(item.clone(action='', title="[COLOR yellow]" + item.channel.capitalize() 
                    + '[/COLOR]: Ningún canal NewPct1 activo'))    
        itemlist.append(item.clone(action='', title=item.category + 
                    ': ERROR 01: EPISODIOS:.  La Web no responde o la URL es erronea. ' 
                    + 'Si la Web está activa, reportar el error con el log'))
        return itemlist

    #Busca y pre-carga todas las páginas de episodios que componen las serie, para obtener la url de cada página
    pattern = '<ul class="%s">(.*?)</ul>' % "pagination"  # item.pattern
    pagination = scrapertools.find_single_match(data, pattern)
    if pagination:
        if "/pg/" in item.url:
            act_page = int(scrapertools.find_single_match(item.url, r'\/pg\/(\d+)'))    #Num página actual
        else:
            act_page = 1
        pattern = '<li><a href="([^"]+)">Last<\/a>'                             #Busca última página
        full_url = scrapertools.find_single_match(pagination, pattern)
        url, last_page = scrapertools.find_single_match(full_url, r'(.*?\/pg\/)(\d+)')
        last_page = int(last_page)
        list_pages = [item.url]
        for x in range(act_page + 1, last_page + 1):            #carga cada página para obtener la url de la siguiente
            #LAS SIGUIENTES 3 LINEAS ANULADAS: no es necesario leer la pagína siguiente. Se supone que está activa
            #response = httptools.downloadpage('%s%s'% (url,x))
            #if response.sucess:
            #    list_pages.append("%s%s" % (url, x))           #Guarda la url de la siguiente página en una lista
            list_pages.append("%s%s" % (url, x))                #Guarda la url de la siguiente página en una lista
    else:
        list_pages = [item.url]
    """

    max_page = 100                                                              # Límite de páginas a visitar
    if item.library_playcounts: 
        max_page = max_page / 5                                                 # Si es una actualización, recortamos
    page = 1
    if scrapertools.find_single_match(item.url, '\/(\d{4,20})\/*$'):            # Tiene número de serie?
        list_pages = ['%s/pg/%s' % (item.url, page)]
    else:
        list_pages = ['%s//pg/%s' % (item.url, page)]                           # ... si no hay que poner 2 //
    list_episodes = []
    
    season = max_temp
    first = True
    #Comprobamos si realmente sabemos el num. máximo de temporadas
    if item.library_playcounts or (item.infoLabels['number_of_seasons'] and item.tmdb_stat):
        num_temporadas_flag = True
    else:
        num_temporadas_flag = False

    while list_pages and page < max_page:                                       #Recorre la lista de páginas, con límite
        try:
            if not data:
                data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage(list_pages[0], timeout=timeout).data)
            data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
            data = data.replace("chapters", "buscar-list")                      #Compatibilidad con mispelisy.series.com
        except:
            if len(itemlist) == 0:                                              # Si ya hay datos, puede ser la última página
                logger.error("ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web " 
                        + " / PATRON: " + pattern + " / " + str(list_pages) + " / DATA: " + str(data))
                itemlist.append(item.clone(action='', title=item.category + 
                        ': ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web.  ' 
                        + 'Reportar el error con el log', contentSeason=0, contentEpisodeNumber=1))
                logger.error(traceback.format_exc())
            break                                           #si no hay más datos, algo no funciona, pintamos lo que tenemos

        if "pelisyseries.com" in item.url:
            pattern = '<li[^>]*><div class.*?src="(?P<thumb>[^"]+)?".*?<a class.*?'
            pattern += 'href="(?P<url>[^"]+).*?<h3[^>]+>(?P<info>.*?)?<\/h3>.*?<\/li>'
        else:
            pattern = '<li[^>]*>\s*<a href="(?P<url>[^"]+)"\s*title="[^>]+>\s*<img.*?src="(?P<thumb>[^"]+)?"'
            pattern += '.*?<h2[^>]+>(?P<info>.*?)?<\/h2>'
        
        #Verificamos si se ha cargado una página, y si además tiene la estructura correcta
        if not data or not scrapertools.find_single_match(data, pattern) or '>( 0 ) Capitulos encontrados <' in data:
            if len(itemlist) > 0 or '>( 0 ) Capitulos encontrados <' in data:       # Si ya hay datos, puede ser la última página
                break
            item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
            if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
                item, itemlist = generictools.post_tmdb_episodios(item, itemlist)   #Llamamos al método para el pintado del error
                return itemlist                                                     #Salimos
            
            #Si a la url de la serie que se ha quitado el código final, en algunos canales puede dar error
            if not scrapertools.find_single_match(item.url, '\/(\d{4,20})\/*$'):
                patron_series = "var\s*parametros\s*=\s*\{(?:'rating'\s*\:[^']+)?(?:'ratingc'\s*\:[^']+)?"
                patron_series += "(?:'n_votos'\s*\:[^']+)?(?:'id'\s*\:[^,]+,)?'cate'\s*\:\s*'([^']+)'"
                url_serie_nocode = scrapertools.find_single_match(data, patron_series)
                if url_serie_nocode:
                    url_serie_nocode = '%s/%s/pg/1' % (item.url, url_serie_nocode)
                    data = re.sub(r"\n|\r|\t|\s{2,}", "", httptools.downloadpage\
                                (url_serie_nocode, timeout=timeout, ignore_response_code=True).data)
                else:
                    data = ''

            if not data or not scrapertools.find_single_match(data, pattern):
                logger.error("ERROR 01: EPISODIOS: La Web no responde o la URL es erronea: " + item.url)
                logger.error(pattern + data)

                #Si no hay datos consistentes, llamamos al método de fail_over para que encuentre un canal que esté activo y pueda gestionar el vídeo
                item, data = generictools.fail_over_newpct1(item, pattern, timeout=timeout)

        if not data:                                                    #No se ha encontrado ningún canal activo para este vídeo
            itemlist.append(item.clone(action='', title="[COLOR yellow]" + item.channel.capitalize() 
                        + '[/COLOR]: Ningún canal NewPct1 activo'))    
            itemlist.append(item.clone(action='', title=item.category + 
                        ': ERROR 01: EPISODIOS:.  La Web no responde o la URL es erronea. ' 
                        + 'Si la Web está activa, reportar el error con el log'))
            return itemlist
        
        matches = re.compile(pattern, re.DOTALL).findall(data)
        if not matches or '>( 0 ) Capitulos encontrados <' in data:             #error
            if len(itemlist) == 0:                                              # Si ya hay datos, puede ser la última página
                logger.error("ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web " 
                        + " / PATRON: " + pattern + " / DATA: " + data)
                itemlist.append(item.clone(action='', title=item.category + 
                        ': ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web.  ' 
                        + 'Reportar el error con el log', contentSeason=0, contentEpisodeNumber=1))
            break                                           #si no hay más datos, algo no funciona, pintamos lo que tenemos
        
        page += 1                                                               # Apuntamos a la página siguiente
        if scrapertools.find_single_match(item.url, '\/(\d{4,20})\/*$'):        # Tiene número de serie?
            list_pages = ['%s/pg/%s' % (item.url, page)]
        else:
            list_pages = ['%s//pg/%s' % (item.url, page)]                       # ... si no hay que poner 2 //

        #logger.debug("patron: " + pattern)
        #logger.debug(matches)
        
        #Empezamos a generar cada episodio
        for scrapedurl, scrapedthumb, info in matches:
            url = scrapedurl
            thumb = scrapedthumb
            if "pelisyseries.com" in item.url:                                  #En esta web están en diferente orden
                interm = url
                url = thumb
                thumb = interm
            
            item_local = item.clone()                                           #Creamos copia local de Item por episodio
            item_local.url = url
            if not item_local.url.startswith("http"):                           #Si le falta el http.: lo ponemos
                item_local.url = scrapertools.find_single_match(item_local.channel_host, \
                        '(\w+:)//') + item_local.url
            item_local.thumbnail = thumb
            if not item_local.thumbnail.startswith("http"):                     #Si le falta el http.: lo ponemos
                item_local.thumbnail = scrapertools.find_single_match(item_local.channel_host, \
                        '(\w+:)//') + item_local.thumbnail
            item_local.contentThumbnail = item_local.thumbnail
            estado = True                                                       #Buena calidad de datos por defecto

            if "<span" in info:                                                 # new style
                pattern = "[^>]+>.*?Temporada\s*(?:<span[^>]+>\[\s?)?(?P<season>\d+)?.*?"
                pattern += "Capitulo(?:s)?\s*(?:<span[^>]+>\[\s?)?(?P<episode>\d+)?(?:.*?(?P"
                pattern += "<episode2>\d+)?)<.*?<span[^>]+>(?P<lang>.*?)?<\/span>\s*Calidad"
                pattern += "\s*<span[^>]+>[\[]\s*(?P<quality>.*?)?\s*[\]]<\/span>"
                if not scrapertools.find_single_match(info, pattern):
                    if "especial" in info.lower():                              # Capitulos Especiales
                        pattern = ".*?[^>]+>.*?Temporada.*?\[.*?(?P<season>\d+).*?\].*?"
                        pattern += "Capitulo.*?\[\s*(?P<episode>\d+).*?\]?(?:.*?"
                        pattern += "(?P<episode2>\d+)?)<.+?<span[^>]+>(?P<lang>.*?)?"
                        pattern += "<\/span>\s*Calidad\s*<span[^>]+>[\[]\s*(?P<quality>.*?)"
                        pattern += "?\s*[\]]<\/span>"
                    elif "miniserie" in info.lower() or "completa" in info.lower():     # Series o miniseries completa
                        logger.debug("patron episodioNEW - MINISERIE: " + info)
                        info = '><strong>%sTemporada %s Capitulo 01_99</strong> - ' % \
                                (item_local.contentSerieName, season) + \
                                '<span >Español Castellano</span> Calidad <span >[%s]</span>' \
                                % item_local.quality
                
                if not scrapertools.find_single_match(info, pattern):           #en caso de error de formato, creo uno básico
                    logger.debug("patron episodioNEW: " + pattern)
                    logger.debug(info)
                    logger.debug(item_local.url)
                    info = '><strong>%sTemporada %s Capitulo 0</strong> - <span >' % \
                                (item_local.contentSerieName, season) + \
                                'Español Castellano</span> Calidad <span >[%s]</span>' \
                                % item_local.quality

            else:   # old style.  Se intenta buscar un patrón que encaje con los diversos formatos antiguos.  Si no, se crea
                pattern = '\[(?P<quality>.*?)\]\[Cap.(?P<season>\d).*?(?P<episode>\d{2})'
                pattern += '(?:_(?P<season2>\d+)(?P<episode2>\d{2}))?\].*?(?P<lang>.*)?'    #Patrón básico por defecto

                if scrapertools.find_single_match(info, '\[\d{3}\]'):
                    info = re.sub(r'\[(\d{3}\])', r'[Cap.\1', info)
                elif scrapertools.find_single_match(info, 'Temp.*?(?P<season>\d+).*?[c|C]ap.*?\.(?P<episode>\d+)?.*?(?:(?P<episode2>\d+))\]?\[(?P<lang>\w+)?(?P<quality>\w+)\]?'):
                    pattern = 'Temp.*?(?P<season>\d+).*?[c|C]ap.*?\.(?P<episode>\d+)?.*?(?:(?P<episode2>\d+))\]?\[(?P<lang>\w+)?(?P<quality>\w+)\]?'
                elif scrapertools.find_single_match(info, 'Temp.*?(?P<season>\d+).*?\[(?P<quality>.*?)\].*?(?P<episode>\d{2})?(?:.*?(?P<episode2>\d{2}))?.*?(?P<lang>\[\w+.*)\[.*?\]?'):
                    pattern = 'Temp.*?(?P<season>\d+).*?\[(?P<quality>.*?)\].*?(?P<episode>\d{2})?(?:.*?(?P<episode2>\d{2}))?.*?(?P<lang>\[\w+.*)\[.*?\]?'
                elif scrapertools.find_single_match(info, 'Temp.*?(?P<season>\d+).*?\[(?P<quality>.*?)\].*?Cap\w?\.\s\d?(?P<episode>\d{2})(?:.*?(?P<episode2>\d{2}))?.*?\[(?P<lang>\w+)\]?'):
                    pattern = 'Temp.*?(?P<season>\d+).*?\[(?P<quality>.*?)\].*?Cap\w?\.\s\d?(?P<episode>\d{2})(?:.*?(?P<episode2>\d{2}))?.*?\[(?P<lang>\w+)\]?'
                elif scrapertools.find_single_match(info, '\[Cap.\d{2}_\d{2}\]'):
                    info = re.sub(r'\[Cap.(\d{2})_(\d{2})\]', r'[Cap.1\1_1\2]', info)
                elif scrapertools.find_single_match(info, '\[Cap.([A-Za-z]+)\]'):
                    info = re.sub(r'\[Cap.([A-Za-z]+)\]', '[Cap.100]', info)
                elif "completa" in info.lower():
                    info = info.replace("COMPLETA", "Caps. 01_99")
                    pattern = 'Temp.*?(?P<season>\d+).*?Cap\w?\.\s\d?(?P<episode>\d{2})(?:.*?(?P<episode2>\d{2}))?.*?\[(?P<quality>.*?)\].*?\[(?P<lang>\w+)\]?'
                    if not scrapertools.find_single_match(info, pattern):       #en caso de error de formato, creo uno básico
                        logger.debug(info)
                        info = '%s - Temp.%s [Caps. 01_99][%s][Spanish]' % \
                                (item_local.contentSerieName, season, item_local.quality)
                if scrapertools.find_single_match(info, '\[Cap.\d{2,3}'):
                    pattern = "\[(?P<quality>.*?)\].*?\[Cap.(?P<season>\d).*?(?P<episode>\d{2})(?:_(?P<season2>\d+)(?P<episode2>\d{2}))?.*?\].*?(?:\[(?P<lang>.*?)\])?"
                elif scrapertools.find_single_match(info, 'Cap.\d{2,3}'):
                    pattern = ".*?Temp.*?\s(?P<quality>.*?)\s.*?Cap.(?P<season>\d).*?(?P<episode>\d{2})(?:_(?P<season2>\d+)(?P<episode2>\d{2}))?.*?\s(?P<lang>.*)?"
                elif scrapertools.find_single_match(info, '(?P<quality>.*?)?(?P<season>\d)[x|X|\.](?P<episode>\d{2})\s?(?:_(?P<season2>\d+)(?P<episode2>\d{2}))?.*?(?P<lang>.*)?'):
                    pattern = "(?P<quality>.*?)?(?P<season>\d)[x|X|\.](?P<episode>\d{2})\s?(?:_(?P<season2>\d+)(?P<episode2>\d{2}))?.*?(?P<lang>.*)?"
                    estado = False                                              #Mala calidad de datos
                if not scrapertools.find_single_match(info, pattern):           #en caso de error de formato, creo uno básico
                    logger.debug("patron episodioOLD: " + pattern)
                    logger.debug(info)
                    logger.debug(item_local.url)
                    info = '%s - Temp.%s [%s][Cap.%s00][Spanish]' % (item_local.contentSerieName, \
                            season, item_local.quality, season)
                    estado = False                                              #Mala calidad de datos
            
            r = re.compile(pattern)
            match = [m.groupdict() for m in r.finditer(info)][0]
            if not match:                                                       #error
                logger.error("ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web " 
                            + " / PATRON: " + pattern + " / DATA: " + info)
                itemlist.append(item.clone(action='', title=item.category + 
                            ': ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web.  ' 
                            + 'Reportar el error con el log'))
                break                                   #si no hay más datos, algo no funciona, pintamos lo que tenemos

            #Si no se encuentran valores, se pone lo básico
            if match['season'] is None or match['season'] == "0" or \
                            not match['season']: match['season'] = season
            if match['episode'] is None: match['episode'] = "0"
            try:
                match['season'] = int(match['season'])
                season_alt = match['season']
                match['episode'] = int(match['episode'])
                if match['season'] > max_temp:
                    logger.error("ERROR 07: EPISODIOS: Error en número de Temporada o Episodio: " 
                            + " / TEMPORADA/EPISODIO: " + str(match['season']) + " / " + 
                            str(match['episode']) + " / NUM_TEMPORADA: " + str(max_temp) 
                            + " / " + str(season) + " / MATCHES: " + str(matches))
                    match['season'] = scrapertools.find_single_match(item_local.url, '\/[t|T]emp\w+-*(\d+)\/')
                    num_temporadas_flag = False
                    if not match['season']:
                        match['season'] = season_alt
                    else:
                        match['season'] = int(match['season'])
            except:
                logger.error("ERROR 07: EPISODIOS: Error en número de Temporada o Episodio: " 
                            + " / TEMPORADA/EPISODIO: " + str(match['season']) + " / " 
                            + str(match['episode']) + " / NUM_TEMPORADA: " + str(max_temp) 
                            + " / " + str(season) + " / MATCHES: " + str(matches))
                logger.error(traceback.format_exc())

            if num_temporadas_flag and match['season'] != season and match['season'] > max_temp + 1:
                #Si el num de temporada está fuera de control, se trata pone en num. de temporada actual
                logger.error("ERROR 07: EPISODIOS: Num. de Temporada fuera de rango " + 
                            " / TEMPORADA: " + str(match['season']) + " / " + str(match['episode']) 
                            + " / NUM_TEMPORADA: " + str(max_temp) + " / " + str(season) + 
                            " / PATRON: " + pattern + " / MATCHES: " + str(matches))
                match['season'] = season
                item_local.contentSeason = season
            else:
                item_local.contentSeason = match['season']
                season = match['season']
                if match['episode'] > 0:
                    num_temporadas_flag = True
                if season > max_temp:
                    max_temp = season
                    
            if match['quality'] and estado == True:
                item_local.quality = match['quality']                           #Si hay quality se coge, si no, la de la serie
                item_local.quality = item_local.quality.replace("ALTA DEFINICION", "HDTV")
            
            if match['lang'] and (estado == False or "especia" in str(match['lang']).lower()):
                match['lang'] = match['lang'].replace("- ", "").replace("[", "").replace("]", "")
                item_local.infoLabels['episodio_titulo'] = match['lang']
                item_local.infoLabels['title'] = item_local.infoLabels['episodio_titulo']
            elif match['lang']:
                if 'espa' in match['lang'].lower(): item_local.language = ['CAST']
                if 'lati' in match['lang'].lower(): item_local.language = ['LAT']
                if 'dual' in match['lang'].lower(): item_local.language = ['DUAL']
                if 'vers' in match['lang'].lower() or 'orig' in match['lang'].lower() \
                        or 'subt' in match['lang'].lower() or 'ingl' in match['lang'].lower() \
                        or 'engl' in match['lang'].lower(): item_local.language = ['VOS']

            if match['episode'] == 0: match['episode'] = 1                      #Evitar errores en Videoteca
            item_local.contentEpisodeNumber = match['episode']

            if match["episode2"]:                                               #Hay episodio dos? es una entrada múltiple?
                item_local.title = "%sx%s al %s -" % (str(match["season"]), \
                        str(match["episode"]).zfill(2), str(match["episode2"])\
                        .zfill(2))                                              #Creamos un título con el rango de episodios
            else:                                                               #Si es un solo episodio, se formatea ya
                item_local.title = "%sx%s -" % (match["season"], str(match["episode"]).zfill(2))

            if first:                                                           #Si es el primer episodio, comprobamos que ...
                first = False
                if item_local.contentSeason < max_temp:                         #... la temporada sea la última ...
                    modo_ultima_temp_alt = False                        #... si no, por seguridad leeremos toda la serie
            
            if modo_ultima_temp_alt and item.library_playcounts:    #Si solo se actualiza la última temporada de Videoteca
                if item_local.contentSeason < max_temp and modo_ultima_temp_alt and max_temp_seen > 1:
                    list_pages = []                                             #Sale del bucle de leer páginas
                    break                                           #Sale del bucle actual del FOR de episodios por página
                elif item_local.contentSeason < max_temp:                       #Si está desordenada ...
                    modo_ultima_temp_alt = False                                #... por seguridad leeremos toda la serie
                #if ('%sx%s' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber).zfill(2))) in item.library_playcounts:
                #    continue
              
            if season_display > 0:
                if item_local.contentSeason > season_display or (not modo_ultima_temp_alt \
                            and item_local.contentSeason != season_display):
                    continue
                elif item_local.contentSeason < season_display and max_temp_seen > 1:
                    list_pages = []                                             #Sale del bucle de leer páginas
                    break
                elif item_local.contentSeason < season_display:                 #Si no ha encontrado epis de la temp, sigue
                    continue
            
            if item_local.active:
                del item_local.active
            if item_local.contentTitle:
                del item_local.infoLabels['title']
            if item_local.season_colapse:
                del item_local.season_colapse
            item_local.context = "['buscar_trailer']"
            item_local.action = "findvideos"
            item_local.contentType = "episode"
            item_local.extra = "episodios"
            max_temp_seen += 1

            # Si mezcla episodios de diferentes calidades e idiomas, intentamos filtrarlos para igualar a los de de la Serie
            if not item_local.quality: item_local.quality = item.quality
            if not item_local.language: item_local.language = item.language
            for lang in item_local.language:
                if lang in str(item.language):
                    break
            else:
                lang = ''
            if item_local.quality == item.quality and lang and item_local.title not in str(list_episodes):
                list_episodes += [item_local.title]
                
                itemlist.append(item_local.clone())
            
            #logger.debug(item_local)
            
        data = ''

    if len(itemlist) > 1:
        itemlist = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))     #clasificamos
        
    if item.season_colapse and not item.add_videolibrary:                   #Si viene de listado, mostramos solo Temporadas
        item, itemlist = generictools.post_tmdb_seasons(item, itemlist)

    if not item.season_colapse:                                             #Si no es pantalla de Temporadas, pintamos todo
        # Pasada por TMDB y clasificación de lista por temporada y episodio
        tmdb.set_infoLabels(itemlist, True)

        #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
        item, itemlist = generictools.post_tmdb_episodios(item, itemlist)
    
    #logger.debug(item)

    return itemlist
    
    
def lookup_idiomas_paginacion(item, url, title, calidad, list_language):
    logger.info()
    estado = True
    item.language = []
    itemlist = []
    
    if "[vos" in title.lower()  or "v.o.s" in title.lower() or "vo" in title.lower() \
                    or "subs" in title.lower() or ".com/pelicula/" in url  or \
                    ".com/series-vo" in url or "-vo/" in url or "vos" in calidad.lower() \
                    or "vose" in calidad.lower() or "v.o.s" in calidad.lower() or \
                    "sub" in calidad.lower() or ".com/peliculas-vo" in item.url:
        item.language += ["VOS"]
    
    if "latino" in title.lower() or "argentina" in title.lower() or "-latino/" \
                    in url or "latino" in calidad.lower() or "argentina" in calidad.lower():
        item.language += ["LAT"]

    if item.language == []:
        item.language = ['CAST']                                                #Por defecto
    
    #Ahora se filtra por idioma, si procede, y se pinta lo que vale.  Excluye categorías en otros idiomas.
    if config.get_setting('filter_languages', channel_py) > 0 and item.extra2 != 'categorias':
        itemlist = filtertools.get_link(itemlist, item, list_language)
        
        if len(itemlist) == 0:
            estado = False
    
    #Volvemos a la siguiente acción en el canal
    return estado

    
def verify_host(item, host_call, force=True, category=''):
    clone_list_alt = []
    
    if force or host_index_check > 0:                                           # Si se quiere usar el mismo clone, en lo posible ...
        if not category:
            category = scrapertools.find_single_match(item.url, 'http.*\:\/\/(?:www.)?(\w+)\.\w+\/')
        if host_index_check > 0:
            category = channel_clone_name
        x = 0
        for active_clone, channel_clone, host_clone, contentType_clone, info_clone in clone_list_check:
            if category == channel_clone and active_clone == '1':               # Se coprueba que el clone esté activo
                clone_list_alt.append(clone_list_check[x])                      # y se salva como referencia
                break
            x += 1
        else:
            clone_list_alt = clone_list                                         # Si no se encuentra el clone, se usar el actual
    else:
        clone_list_alt = clone_list                                             # Se usa el clone actual
    
    # Renombramos el canal al nombre de clone elegido.  Actualizamos URL
    for active_clone, channel_clone, host_clone, contentType_clone, info_clone in clone_list_alt:
        host_call = host_clone                                                  # URL del clone actual
        item.channel_host = host_call
        item.url = re.sub(scrapertools.find_single_match(item.url, '(http.*\:\/\/(?:www.)?\w+\.\w+\/)'), host_call, item.url)
        item.category = channel_clone.capitalize()
        
        break                                                                   # Terminado
    
    return (item, host_call)


def actualizar_titulos(item):
    logger.info()
    
    item = generictools.update_title(item) #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels

    #Volvemos a la siguiente acción en el canal
    return item
    

def search(item, texto):
    logger.info("search:" + texto)
    # texto = texto.replace(" ", "+")

    try:
        if '.org' in host:
            item.url = host + "get/result/"
            item.post = "categoryIDR=&categoryID=&idioma=&calidad=&ordenar=Fecha&inon=Descendente&s=%s&pg=1" % texto
        else:
            item.url = host + "buscar"
            item.post = "q=%s" % texto
        item.pattern = "buscar-list"
        itemlist = listado_busqueda(item)
        
        return itemlist

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        logger.error(traceback.format_exc())
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    
    item.title = "newest"
    item.category = "newest"
    item.channel = channel_py
    
    try:
        if categoria == 'peliculas':
            item.url = host + 'ultimas-descargas/'
            value = 757
            item.post = "categoryIDR=%s&date=%s" % (value, fecha_rango)
            item.extra = "novedades"
            item.action = "listado_busqueda"
            itemlist = listado_busqueda(item)
                
        elif categoria == 'series':
            item.url = host + 'ultimas-descargas/'
            value = 767
            item.post = "categoryIDR=%s&date=%s" % (value, fecha_rango)
            item.extra = "novedades"
            item.action = "listado_busqueda"
            itemlist = listado_busqueda(item)
                
        elif categoria == '4k':
            item.url = host + 'ultimas-descargas/'
            value = 1027
            item.post = "categoryIDR=%s&date=%s" % (value, fecha_rango)
            item.extra = "novedades"
            item.action = "listado_busqueda"
            itemlist = listado_busqueda(item)
                
        elif categoria == 'anime':
            item.url = host + 'anime/'
            item.extra = "peliculas"
            item.action = "listado"
            itemlist = listado(item)
                                 
        elif categoria == 'documentales':
            item.url = host + 'ultimas-descargas/'
            value = 780
            item.post = "categoryIDR=%s&date=%s" % (value, fecha_rango)
            item.extra = "novedades"
            item.action = "listado_busqueda"
            itemlist = listado_busqueda(item)
                
        elif categoria == 'latino':
            item.url = host + 'ultimas-descargas/'
            value = 1527
            item.post = "categoryIDR=%s&date=%s" % (value, fecha_rango)
            item.extra = "novedades"
            item.action = "listado_busqueda"
            itemlist = listado_busqueda(item)
            
        if ">> Página siguiente" in itemlist[-1].title or "Pagina siguiente >>" in itemlist[-1].title:
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        logger.error(traceback.format_exc())
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
