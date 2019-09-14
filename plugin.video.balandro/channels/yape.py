# -*- coding: utf-8 -*-

import re, urllib

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, tmdb

host = 'https://www.yape.nu/'
host_catalogue = host + 'catalogue'

IDIOMAS = {'la':'Lat', 'es':'Esp', 'en_es':'VOSE', 'en':'VO'}

# Versión de Dilo para películas

# Filtros para generos, idiomas, calidades y ordenes. Ejecutar manualmente rutina extraer_datos_web si hay cambios
# --------------------------------------------------
web_generos = [['accion', 'Acci\xc3\xb3n'], ['animacion', 'Animaci\xc3\xb3n'], ['aventura', 'Aventura'], ['belico', 'B\xc3\xa9lico'], ['biografico', 'Biogr\xc3\xa1fico'], ['ciencia-ficcion', 'Ciencia Ficci\xc3\xb3n'], ['cine-negro', 'Cine negro'], ['comedia', 'Comedia'], ['crimen', 'Crimen'], ['documental', 'Documental'], ['drama', 'Drama'], ['familia', 'Familia'], ['fantasia', 'Fantas\xc3\xada'], ['gore', 'Gore'], ['historico', 'Hist\xc3\xb3rico'], ['intriga', 'Intriga'], ['kids', 'Kids'], ['misterio', 'Misterio'], ['musical', 'Musical'], ['romance', 'Romance'], ['slasher', 'Slasher'], ['terror', 'Terror'], ['thriller', 'Thriller'], ['western', 'Western'], ['zombis', 'Zombis']]

web_idiomas = [['es', 'Espa\xc3\xb1ol'], ['la', 'Latino'], ['en', 'Ingles'], ['en_es', 'Subtitulado']]

web_calidades = [['c1', 'Cam'], ['c2', 'TS Screener HQ'], ['c3', 'TS Screnner'], ['c4', 'DVD Screnner'], ['c5', 'DVD Rip'], ['c6', 'BR Screnner'], ['c7', 'HD Rip'], ['c8', 'HD 720'], ['c9', 'HD 1080p']]

web_ordenes = [['mosts-today', 'Popular Hoy'], ['mosts-week', 'Popular esta semana'], ['latest', 'Nuevo'], ['time_update', 'Actualizadas']]

web_paises = [['AR', 'Argentina'], ['AU', 'Australia'], ['AT', 'Austria'], ['BE', 'B\xc3\xa9lgica'], ['BO', 'Bolivia'], ['BR', 'Brasil'], ['BG', 'Bulgaria'], ['CA', 'Canad\xc3\xa1'], ['CL', 'Chile'], ['CN', 'China'], ['CO', 'Colombia'], ['CR', 'Costa Rica'], ['HR', 'Croacia'], ['CU', 'Cuba'], ['CZ', 'Rep\xc3\xbablica Checa'], ['DK', 'Dinamarca'], ['EC', 'Ecuador'], ['SV', 'El Salvador'], ['FI', 'Finlandia'], ['FR', 'Francia'], ['DE', 'Alemania'], ['GR', 'Grecia'], ['GT', 'Guatemala'], ['HN', 'Honduras'], ['HK', 'Hong Kong'], ['HU', 'Hungr\xc3\xada'], ['IS', 'Islandia'], ['IN', 'India'], ['IE', 'Irlanda'], ['IL', 'Israel'], ['IT', 'Italia'], ['JP', 'Jap\xc3\xb3n'], ['LT', 'Lituania'], ['MY', 'Malasia'], ['MX', 'M\xc3\xa9xico'], ['NL', 'Pa\xc3\xadses Bajos'], ['NZ', 'Nueva Zelanda'], ['NO', 'Noruega'], ['PA', 'Panam\xc3\xa1'], ['PY', 'Paraguay'], ['PE', 'Per\xc3\xba'], ['PL', 'Polonia'], ['PT', 'Portugal'], ['PR', 'Puerto Rico'], ['RO', 'Rumania'], ['RU', 'Rusia'], ['RS', 'Serbia'], ['SG', 'Singapur'], ['ES', 'Espa\xc3\xb1a'], ['SE', 'Suecia'], ['CH', 'Suiza'], ['TH', 'Tailandia'], ['TR', 'Turqu\xc3\xada'], ['UA', 'Ucrania'], ['GB', 'Reino Unido'], ['US', 'Estados Unidos'], ['UY', 'Uruguay'], ['VE', 'Venezuela'] ]


def mainlist(item):
    return mainlist_pelis(item)

def mainlist_pelis(item):
    logger.info()
    itemlist = []
    
    # ~ ?sort=mosts-today (default), mosts-week, latest, time-update

    itemlist.append(item.clone( title = 'Películas más populares', action = 'list_all', url = host_catalogue ))
    itemlist.append(item.clone( title = 'Últimas películas agregadas', action = 'list_all', url = host_catalogue + '?sort=latest' ))

    itemlist.append(item.clone( title = 'Por idioma', action = 'idiomas' ))
    itemlist.append(item.clone( title = 'Por género', action = 'generos' ))
    itemlist.append(item.clone( title = 'Por calidad', action = 'calidades' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anyos' ))
    itemlist.append(item.clone( title = 'Por país', action = 'paises' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    # Recuperar filtros guardados del usuario
    # ---------------------------------------
    filtro = config.get_setting('filtro', item.channel, default='')
    if filtro != '':
        f_idi = scrapertools.find_multiple_matches(filtro, 'audio\[\]=([^&]+)')
        f_gen = scrapertools.find_multiple_matches(filtro, 'genre\[\]=([^&]+)')
        f_cal = scrapertools.find_multiple_matches(filtro, 'quality\[\]=([^&]+)')
        f_ord = scrapertools.find_single_match(filtro, 'sort=([^&]+)')
        plot = ''
        if len(f_idi) > 0: plot += 'Idiomas: [COLOR blue]%s[/COLOR][CR]' % ', '.join([x[1] for x in web_idiomas if x[0] in f_idi])
        if len(f_gen) > 0: plot += 'Géneros: [COLOR blue]%s[/COLOR][CR]' % ', '.join([x[1] for x in web_generos if x[0] in f_gen])
        if len(f_cal) > 0: plot += 'Calidades: [COLOR blue]%s[/COLOR][CR]' % ', '.join([x[1] for x in web_calidades if x[0] in f_cal])
        plot += 'Ordenadas por: [COLOR blue]%s[/COLOR][CR]' % f_ord
        
        itemlist.append(item.clone( title = 'Modificar filtro personalizado ...', action = 'modificar_filtro', plot=plot, folder=False ))
        itemlist.append(item.clone( title = 'Listar con filtro personalizado', action = 'filtrado', plot=plot ))
    else:
        itemlist.append(item.clone( title = 'Crear filtro personalizado ...', action = 'modificar_filtro', folder=False ))

    # ~ itemlist.append(item.clone( title = 'Developer testing', action = 'extraer_datos_web', folder=False )) # ejecutar manualmente si hace falta

    return itemlist


def idiomas(item):
    logger.info()
    itemlist = []
    
    for x in web_idiomas:
        itemlist.append(item.clone( title=x[1], url=host_catalogue+'?audio[]='+x[0], action='list_all' ))
        
    return itemlist

def generos(item):
    logger.info()
    itemlist = []

    for x in web_generos:
        itemlist.append(item.clone( title=x[1], url=host_catalogue+'?genre[]='+x[0], action='list_all' ))
        
    return itemlist

def calidades(item):
    logger.info()
    itemlist = []

    for x in web_calidades:
        itemlist.append(item.clone( title=x[1], url=host_catalogue+'?quality[]='+x[0], action='list_all' ))
        
    return itemlist

def anyos(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year - 1, 1984, -1):
        itemlist.append(item.clone( title=str(x), url=host_catalogue+'?year[]='+str(x), action='list_all' ))
        
    return itemlist

def paises(item):
    logger.info()
    itemlist = []

    for x in sorted(web_paises, key=lambda x: x[1]):
        itemlist.append(item.clone( title=x[1], url=host_catalogue+'?country[]='+x[0], action='list_all' ))
        
    return itemlist


def extraer_datos_web(item):
    logger.info()

    data = httptools.downloadpage(host_catalogue).data
    # ~ logger.debug(data)

    # Obtener distintos géneros, idiomas, calidades, órdenes
    # ------------------------------------------------------
    web_generos = []
    patron = '<input type="checkbox" class="[^"]+" id="[^"]+" value="([^"]+)" name="genre\[\]">'
    patron += '<label class="custom-control-label" for="[^"]+">([^<]+)</label>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for valor, titulo in matches:
        web_generos.append([valor, titulo.strip()])
    web_generos = sorted(web_generos, key=lambda x: x[0])
    logger.debug(web_generos)

    web_idiomas = []
    patron = '<input type="checkbox" id="[^"]+" name="audio\[\]" class="[^"]+" value="([^"]+)">'
    patron += '<label class="custom-control-label" for="[^"]+">([^<]+)</label>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for valor, titulo in matches:
        web_idiomas.append([valor, titulo.strip()])
    logger.debug(web_idiomas)

    web_calidades = []
    patron = '<input type="checkbox" id="[^"]+" name="quality\[\]" class="[^"]+" value="([^"]+)">'
    patron += '<label class="custom-control-label" for="[^"]+">([^<]+)</label>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for valor, titulo in matches:
        web_calidades.append([valor, titulo.strip()])
    logger.debug(web_calidades)

    web_ordenes = []
    matches = re.compile('<a class="dropdown-item" href="[^?]+\?sort=([^"]+)">([^<]+)</a>', re.DOTALL).findall(data)
    for valor, titulo in matches:
        web_ordenes.append([valor, titulo.strip()])
    logger.debug(web_ordenes)
    
    web_paises = []
    patron = '<input type="checkbox" class="[^"]+" id="[^"]+" name="country\[\]" value="([^"]+)">'
    patron += '<label class="custom-control-label" for="[^"]+">([^<]+)</label>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for valor, titulo in matches:
        web_paises.append([valor, titulo.strip()])
    logger.debug(web_paises)

    platformtools.dialog_notification('Yape', 'Comprobar nuevos valores en el log ...')
    return True


def modificar_filtro(item):

    # Recuperar filtros guardados del usuario
    # ---------------------------------------
    filtro = config.get_setting('filtro', item.channel, default='')
    f_idi = scrapertools.find_multiple_matches(filtro, 'audio\[\]=([^&]+)')
    f_gen = scrapertools.find_multiple_matches(filtro, 'genre\[\]=([^&]+)')
    f_cal = scrapertools.find_multiple_matches(filtro, 'quality\[\]=([^&]+)')
    f_ord = scrapertools.find_single_match(filtro, 'sort=([^&]+)')

    # Diálogos para escoger géneros, idiomas, calidades
    # -------------------------------------------------
    preselect = [i for i, x in enumerate(web_idiomas) if x[0] in f_idi]
    ret = platformtools.dialog_multiselect('Seleccionar idiomas a incluir', [x[1] for x in web_idiomas], preselect=preselect)
    if ret == None: return False
    selected_idi = [web_idiomas[i][0] for i in ret]

    preselect = [i for i, x in enumerate(web_generos) if x[0] in f_gen]
    ret = platformtools.dialog_multiselect('Seleccionar géneros a incluir', [x[1] for x in web_generos], preselect=preselect)
    if ret == None: return False
    selected_gen = [web_generos[i][0] for i in ret]

    preselect = [i for i, x in enumerate(web_calidades) if x[0] in f_cal]
    ret = platformtools.dialog_multiselect('Seleccionar calidades a incluir', [x[1] for x in web_calidades], preselect=preselect)
    if ret == None: return False
    selected_cal = [web_calidades[i][0] for i in ret]

    preselect = 2 #latest
    for i, x in enumerate(web_ordenes): 
        if x[0] == f_ord: preselect = i; break
    ret = platformtools.dialog_select('Seleccionar orden a aplicar', [x[1] for x in web_ordenes], preselect=preselect)
    if ret == -1: return False
    selected_ord = web_ordenes[ret][0]

    # Guardar filtro en la configuración del canal del usuario
    # --------------------------------------------------------
    filtro = '?'
    for valor in selected_idi: filtro += 'audio[]=%s&' % valor
    for valor in selected_gen: filtro += 'genre[]=%s&' % valor
    for valor in selected_cal: filtro += 'quality[]=%s&' % valor
    filtro += 'sort=%s' % selected_ord
    
    config.set_setting('filtro', filtro, item.channel)

    platformtools.itemlist_refresh()
    return True


def filtrado(item):
    logger.info()
    itemlist = []

    item.url = host_catalogue + config.get_setting('filtro', item.channel, default='')
    
    return list_all(item)


def list_all(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)
    
    matches = re.compile('<div class="col-lg-2 col-md-3 col-6 mb-3"><a(.*?)</a></div>', re.DOTALL).findall(data)
    for article in matches:
        url = scrapertools.find_single_match(article, ' href="([^"]+)"')
        thumb = scrapertools.find_single_match(article, ' src="([^"]+)"')
        title = scrapertools.find_single_match(article, '<div class="text-white[^"]*">([^<]+)</div>').strip()
        year = scrapertools.find_single_match(article, '<div class="txt-gray-200 txt-size-\d+">(\d+)</div>')
        quality = scrapertools.find_single_match(article, '<span class="[^"]*">([^<]+)</span>').strip()
        langs = scrapertools.find_multiple_matches(article, '/languajes/([^.]+).png')
        
        itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, 
                                    languages=', '.join([IDIOMAS.get(lg, lg) for lg in langs]), qualities=quality, 
                                    contentType='movie', contentTitle=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    next_page_link = scrapertools.find_single_match(data, '<li class="page-item"><a href="([^"]+)" aria-label="(?:Netx|Next)"')
    if next_page_link:
        itemlist.append(item.clone( title='>> Página siguiente', url=host_catalogue + next_page_link, action='list_all' ))

    return itemlist


# Asignar un numérico según las calidades del canal, para poder ordenar por este valor
def puntuar_calidad(txt):
    orden = ['TS Screnner', 'DVD Screnner', 'BR Screnner', 'HD Rip', 'HD 720', 'HD 1080p']
    if txt not in orden: return 0
    else: return orden.index(txt) + 1

def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)
    
    patron = '<a href="#" class="[^"]*" data-link="([^"]+)".*?/languajes/([^.]+).png.*?<span class="[^"]*">([^<]+)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, language, quality in matches:
        if '/download?' in url: continue # descartar descargas directas !?

        server = scrapertools.find_single_match(url, '/servers/([^.]+)')
        # ~ logger.debug('%s %s %s %s' % (url, language, quality, server))
        quality = quality.strip()

        itemlist.append(Item( channel = item.channel, action = 'play', server = server,
                              title = '', url = url,
                              language = IDIOMAS.get(language, language), quality = quality, quality_num = puntuar_calidad(quality)
                       ))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)
    
    url = scrapertools.find_single_match(data, 'iframe class="" src="([^"]+)')
    if host in url:
        url = httptools.downloadpage(url, follow_redirects=False, only_headers=True).headers.get('location', '')

    if url != '': 
        itemlist.append(item.clone(url = url))
    
    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + 'search?s=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
