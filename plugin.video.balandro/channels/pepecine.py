# -*- coding: utf-8 -*-

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, servertools, jsontools, tmdb

# ~ host = 'https://pepecine.me'
host = 'https://verencasa.com'

ruta_pelis  = '/browse?type=movie'
ruta_series = '/browse?type=series'


# ~ def configurar_proxies(item):
    # ~ from core import proxytools
    # ~ return proxytools.configurar_proxies_canal(item.channel, host)

def do_downloadpage(url, post=None):
    url = url.replace('pepecine.me', 'verencasa.com') # por si viene de enlaces guardados
    url = url.replace('pepecine.tv', 'verencasa.com') # por si viene de enlaces guardados
    data = httptools.downloadpage(url, post=post).data
    # ~ data = httptools.downloadpage_proxy('pepecine', url, post=post).data
    return data


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series' ))

    itemlist.append(item.clone( title = 'Buscar ...', action = 'search', search_type = 'all' ))

    # ~ plot = 'Es posible que para poder utilizar este canal necesites configurar algún proxy, ya que no es accesible desde algunos países/operadoras.'
    # ~ plot += '[CR]Si desde un navegador web no te funciona el sitio %s necesitarás un proxy.' % host
    # ~ itemlist.append(item.clone( title = 'Configurar proxies a usar ...', action = 'configurar_proxies', folder=False, plot=plot, text_color='red' ))

    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Últimas películas', action = 'list_latest', url = host + '/last/estrenos-peliculas-online.php', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Las más populares', action = 'list_all', url = host + ruta_pelis, orden = 'popularity:desc', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Las más valoradas', action = 'list_all', url = host + ruta_pelis, orden = 'user_score:desc', search_type = 'movie' ))
    itemlist.append(item.clone( title = 'Las más recientes', action = 'list_all', url = host + ruta_pelis, orden = 'date_added:desc', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Películas por género', action = 'generos', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Listas de películas', action = 'listas', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))

    # ~ plot = 'Es posible que para poder utilizar este canal necesites configurar algún proxy, ya que no es accesible desde algunos países/operadoras.'
    # ~ plot += '[CR]Si desde un navegador web no te funciona el sitio %s necesitarás un proxy.' % host
    # ~ itemlist.append(item.clone( title = 'Configurar proxies a usar ...', action = 'configurar_proxies', folder=False, plot=plot, text_color='red' ))

    return itemlist


def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'list_latest', url = host + '/last/estrenos-episodios-online.php', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Las más populares', action = 'list_all', url = host + ruta_series, orden = 'popularity:desc', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Las más valoradas', action = 'list_all', url = host + ruta_series, orden = 'user_score:desc', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Las más recientes', action = 'list_all', url = host + ruta_series, orden = 'date_added:desc', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Series por género', action = 'generos', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Listas de series', action = 'listas', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    # ~ plot = 'Es posible que para poder utilizar este canal necesites configurar algún proxy, ya que no es accesible desde algunos países/operadoras.'
    # ~ plot += '[CR]Si desde un navegador web no te funciona el sitio %s necesitarás un proxy.' % host
    # ~ itemlist.append(item.clone( title = 'Configurar proxies a usar ...', action = 'configurar_proxies', folder=False, plot=plot, text_color='red' ))

    return itemlist



def generos(item):
    logger.info()
    itemlist=[]

    if item.search_type not in ['movie', 'tvshow']: item.search_type = 'movie'
    url = host + (ruta_pelis if item.search_type == 'movie' else ruta_series)

    generos = ['Accion', 'Animacion', 'Aventura', 'Belica', 'CienciaFiccion', 'Comedia', 'Crimen', 'Documental', 'Drama', 'Familia', 'Fantasia', 'Guerra', 'Historia', 'Kids', 'Misterio', 'Musica', 'News', 'PeliculaDeTV', 'Reality', 'Romance', 'Soap', 'Suspense', 'Talk', 'Terror', 'Thriller', 'Western']

    for genero in generos:
        itemlist.append(item.clone( action = 'list_all', title = genero, url = url, genero = genero ))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        if item.search_type not in ['movie', 'tvshow', 'all']: item.search_type = 'all'
        item.url = host + '/secure/search/' + texto.replace(" ", "+")
        return sub_search(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def sub_search(item):
    logger.info()
    itemlist = []

    # ~ data = do_downloadpage(item.url.replace('/secure/search/', '/search?'))

    url = item.url + '?type=&limit=30'

    data = do_downloadpage(url)
    dict_data = jsontools.load(data)
    
    if 'results' not in dict_data: return itemlist
    
    for element in dict_data['results']:
        # ~ logger.debug(element)
        if 'is_series' not in element or 'name' not in element: continue
        
        if element['is_series'] and item.search_type == 'movie': continue
        if not element['is_series'] and item.search_type == 'tvshow': continue
        
        new_item = item.clone( title = element['name'], thumbnail = element['poster'],
                               infoLabels = {'year':element['year'], 'plot': element['description']})

        # ~ new_item.url = host + '/titles/' + str(element['id'])
        new_item.url = host + '/secure/titles/' + str(element['id']) + '?titleId=' + str(element['id'])

        if not element['is_series']:
            new_item.action = 'findvideos'
            new_item.contentType = 'movie'
            new_item.contentTitle = element['name']
        else:
            new_item.action = 'temporadas'
            new_item.contentType = 'tvshow'
            new_item.contentSerieName = element['name']
        
        new_item.fmt_sufijo = '' if item.search_type != 'all' else new_item.contentType
    
        itemlist.append(new_item)

    tmdb.set_infoLabels(itemlist)

    return itemlist



def list_all(item):
    logger.info()
    itemlist=[]

    # ~ data = do_downloadpage(item.url)

    if not item.page: item.page = '1'
    if not item.orden: item.orden = 'popularity:desc'

    tipo = 'movie' if item.search_type == 'movie' else 'series'

    url = host + '/secure/titles?type=%s&order=%s&onlyStreamable=true&page=%s' % (tipo, item.orden, item.page)
    if item.genero: url += '&genre=' + item.genero

    data = do_downloadpage(url)
    dict_data = jsontools.load(data)

    if 'pagination' not in dict_data: return itemlist

    for element in dict_data['pagination']['data']:
        new_item = item.clone( title = element['name'], thumbnail = element['poster'],
                               infoLabels = {'year':element['year'], 'plot': element['description']})

        # ~ new_item.url = host + '/titles/' + str(element['id'])
        new_item.url = host + '/secure/titles/' + str(element['id']) + '?titleId=' + str(element['id'])

        if not element['is_series']:
            new_item.action = 'findvideos'
            new_item.contentType = 'movie'
            new_item.contentTitle = element['name']
        else:
            new_item.action = 'temporadas'
            new_item.contentType = 'tvshow'
            new_item.contentSerieName = element['name']

        itemlist.append(new_item)

    tmdb.set_infoLabels(itemlist)

    if dict_data['pagination']['next_page_url']:
        itemlist.append(item.clone( title = 'Página siguiente >>', page = dict_data['pagination']['next_page_url'].replace('/?page=', ''), action='list_all' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist=[]

    # Si viene de list_latest, limpiar season, episode
    if item.contentEpisodeNumber: item.__dict__['infoLabels'].pop('episode')
    if item.contentSeason: item.__dict__['infoLabels'].pop('season')

    data = do_downloadpage(item.url)
    dict_data = jsontools.load(data)

    if 'title' not in dict_data: return itemlist

    for element in dict_data['title']['seasons']:
        itemlist.append(item.clone( action='episodios', title='Temporada ' + str(element['number']), 
                                    contentType = 'season', contentSeason = element['number'] ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def episodios(item):
    logger.info()
    itemlist=[]

    url = item.url+'&seasonNumber='+str(item.contentSeason)
    
    data = do_downloadpage(url)
    dict_data = jsontools.load(data)

    if 'title' not in dict_data: return itemlist

    for element in dict_data['title']['season']['episodes']:
        
        titulo = '%sx%s %s' % (element['season_number'], element['episode_number'], element['name'])
        
        itemlist.append(item.clone( action='findvideos', title = titulo, url = url + '&episodeNumber=' + str(element['episode_number']),
                                    contentType = 'episode', contentSeason = element['season_number'], contentEpisodeNumber = element['episode_number'] ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


# Asignar un numérico según las calidades del canal, para poder ordenar por este valor
def puntuar_calidad(txt):
    if txt == None: txt = '?'
    orden = ['?', 'Cam', 'Ts-Scr', 'Tc-Scr', 'Rip', 'DVD Rip', 'SD', 'Hd Micro', 'Hd Rip', 'Hd-Tv', 'HD Real', 'Hd 720', 'Hd 1080']
    if txt not in orden: return 0
    else: return orden.index(txt) + 1

def _extraer_idioma(lang):
    if 'Castellano' in lang: return 'Esp'
    if 'Latino' in lang: return 'Lat'
    if 'Subtitulado' in lang: return 'VOSE'
    return 'VO'

def findvideos(item):
    logger.info()
    itemlist=[]
    
    data = do_downloadpage(item.url)
    # ~ logger.debug(data)
    dict_data = jsontools.load(data)

    if 'title' not in dict_data: return itemlist
    
    elementos = []
    if 'episodeNumber=' in item.url and 'season' in dict_data['title'] and 'episodes' in dict_data['title']['season']:
        for epi in dict_data['title']['season']['episodes']:
            if epi['season_number'] == item.contentSeason and epi['episode_number'] == item.contentEpisodeNumber and 'videos' in epi:
                elementos = epi['videos']
                break
    if len(elementos) == 0:
        elementos = dict_data['title']['videos']
    
    for element in elementos:
        if '/z' in element['name']: continue # descartar descargas directas
        if 'youtube.com/' in element['url']: continue # descartar tráilers
        # ~ logger.debug(element)
        
        url = element['url']
        if url.startswith('https://goo.gl/'): # acortador de google
            url = httptools.downloadpage(url, follow_redirects=False, only_headers=True).headers.get('location', '')
            if not url: continue
        
        #TODO? Mostrar info de positive_votes, negative_votes, reports
        
        itemlist.append(Item(channel = item.channel, action = 'play',
                             title = item.title, url = url,
                             language = _extraer_idioma(element['name']), 
                             quality = element['quality'], quality_num = puntuar_calidad(element['quality'])
                       ))
        
    itemlist = servertools.get_servers_itemlist(itemlist)
    
    return itemlist


def list_latest(item):
    logger.info()
    itemlist = []

    if not item.desde: item.desde = 0
    perpage = 20
    if item.search_type == 'tvshow': color = config.get_setting('context_tracking_color', default='blue')

    data = do_downloadpage(item.url).decode('iso-8859-1').encode('utf8')
    # ~ logger.debug(data)

    import re
    matches = re.compile("<div class='online'><table><tr>(.*?)</tr></table></div>", re.DOTALL).findall(data)
    num_matches = len(matches)

    # Como len(matches)=300, se controla una paginación interna y se muestran en bloques de 20 (perpage)
    # Se descartan enlaces repetidos en la misma paginación pq algunas pelis se duplican por el idioma/calidad pero apuntan a la misma url

    for n, elemento in enumerate(matches[item.desde:]):

        url = scrapertools.find_single_match(elemento, ' href=([^ ]+)')
        thumb = scrapertools.find_single_match(elemento, ' src=([^ ]+)')
        title = scrapertools.find_single_match(elemento, ' alt="([^"]+)')
        language = scrapertools.find_single_match(elemento, '<div class="s7">([^<]+)')

        if '-z' in language: continue # descartar descargas directas
        # ~ lang = _extraer_idioma(language) # No se muestran los idiomas pq sólo se indican los modificados y normalmente hay más, por lo que puede llevar a engaño.
        
        if item.search_type == 'movie':
            vid = scrapertools.find_single_match(url, '/([^/]+)$')
            url = host + '/secure/titles/' + vid + '?titleId=' + vid

            if url in [it.url for it in itemlist]: continue # descartar repetidos

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, 
                                        contentType='movie', contentTitle=title, infoLabels={'year': '-'} ))

        else:
            vid, season, episode = scrapertools.find_single_match(url, '/(\d+)/season/(\d+)/episode/(\d+)$')

            url_serie = host + '/secure/titles/' + vid + '?titleId=' + vid
            url_tempo = url_serie + '&seasonNumber=' + season
            url = url_tempo + '&episodeNumber=' + episode

            if url in [it.url for it in itemlist]: continue # descartar repetidos
            
            show = title.replace(' %sx%s' % (season, episode), '').strip()

            # Menú contextual: ofrecer acceso a temporada / serie
            contextual = []
            contextual.append({ 'title': '[COLOR pink]Listar temporada %s[/COLOR]' % season, 
                                      'action': 'episodios', 'url': url_tempo, 'context': '', 'folder': True, 'link_mode': 'update' })
            contextual.append({ 'title': '[COLOR pink]Listar temporadas[/COLOR]',
                                      'action': 'temporadas', 'url': url_serie, 'context': '', 'folder': True, 'link_mode': 'update' })

            itemlist.append(item.clone( action='findvideos', url=url, title=title, thumbnail=thumb, context=contextual, 
                                        contentType='episode', contentSerieName=show, contentSeason=season, contentEpisodeNumber=episode ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    # Paginación 
    if item.desde + n + 1 < num_matches:
        itemlist.append(item.clone( title='>> Página siguiente', desde=item.desde + n + 1, action='list_latest' ))

    return itemlist



def listas(item):
    logger.info()
    itemlist = []
    
    if item.search_type == 'movie':
        seleccion = [
            ['226606', 'Cine Familiar'], 
            ['226608', 'Recomendadas'], 
            ['226605', 'Recomendaciones'], 
            ['226596', 'En Cines'], 
            ['226704', 'Documentales'], 
            ['226607', 'Universo Marvel'], 
            ['226613', 'Animación'], 
            ['226612', 'Terror'], 
        ]
    else:
        seleccion = [
            ['226601', 'En emisión'], 
            ['226604', 'Nuevas Series y Temporadas'], 
            ['226609', 'Recomendadas'], 
            ['226611', 'Renovadas'], 
            ['226607', 'Universo Marvel'], 
            ['226613', 'Animación'], 
            ['226612', 'Terror'], 
        ]
        
    for numero, nombre in seleccion:
        itemlist.append(item.clone( title = nombre, action = 'list_list', 
                                    url = host + '/secure/lists/' + numero + '.php?sortBy=pivot.order&sortDir=asc' ))

    return itemlist


def list_list(item):
    logger.info()
    itemlist = []

    if not item.desde: item.desde = 0
    perpage = 20

    data = do_downloadpage(item.url)
    dict_data = jsontools.load(data)

    if 'items' not in dict_data: return itemlist

    for n, element in enumerate(dict_data['items']['data'][item.desde:]):
        if item.search_type == 'movie' and element['is_series']: continue
        if item.search_type == 'tvshow' and not element['is_series']: continue
        
        new_item = item.clone( title = element['name'], thumbnail = element['poster'],
                               infoLabels = {'year':element['year'], 'plot': element['description']})

        # ~ new_item.url = host + '/titles/' + str(element['id'])
        new_item.url = host + '/secure/titles/' + str(element['id']) + '?titleId=' + str(element['id'])

        if not element['is_series']:
            new_item.action = 'findvideos'
            new_item.contentType = 'movie'
            new_item.contentTitle = element['name']
        else:
            new_item.action = 'temporadas'
            new_item.contentType = 'tvshow'
            new_item.contentSerieName = element['name']

        itemlist.append(new_item)

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)

    # Paginación 
    if item.desde + n + 1 < len(dict_data['items']['data']):
        itemlist.append(item.clone( title='>> Página siguiente', desde=item.desde + n + 1, action='list_list' ))

    return itemlist
