# -*- coding: utf-8 -*-

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, jsontools, tmdb

host = 'http://tv-vip.com/'

perpage = 20

default_headers = {}
default_headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0'
default_headers['Referer'] = host



def configurar_proxies(item):
    from core import proxytools
    return proxytools.configurar_proxies_canal(item.channel, host)


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Películas', action = 'mainlist_pelis' ))
    itemlist.append(item.clone( title = 'Series', action = 'mainlist_series' ))
    
    return itemlist


def mainlist_pelis(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Películas novedades', action = 'list_all', url = host + 'json/playlist/000-novedades/index.json', 
                                thumbnail = host + 'json/playlist/000-novedades/background.jpg', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Películas destacadas', action = 'list_all', url = host + 'json/playlist/lo-mas-visto/index.json', 
                                thumbnail = host + 'json/playlist/lo-mas-visto/background.jpg', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Películas más vistas', action = 'list_all', url = host + 'json/playlist/peliculas-mas-vistas/index.json', 
                                thumbnail = host + 'json/playlist/peliculas-mas-vistas/background.jpg', search_type = 'movie' ))

    # Descartado menú Últimas pq solamente salen 9 películas (los 31 restantes son episodios o pelis sin nombre)
    # ~ itemlist.append(item.clone( title = 'Últimas películas', action = 'list_all', url = host + 'json/playlist/ultimas-peliculas/index.json', 
                                # ~ thumbnail = host + 'json/playlist/ultimas-peliculas/background.jpg', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Películas por categorías', action = 'list_subcategorias', url = host + 'json/playlist/peliculas/index.json', 
                                thumbnail = host + 'json/playlist/peliculas/background.jpg', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Películas en 3D', action = 'list_all', url = host + 'json/playlist/3D/index.json', 
                                thumbnail = host + 'json/playlist/3D/background.jpg', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Películas en V.O.', action = 'list_all', url = host + 'json/playlist/version-original/index.json', 
                                thumbnail = host + 'json/playlist/version-original/background.jpg', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Documentales', action = 'list_all', url = host + 'json/playlist/documentales/index.json', 
                                thumbnail = host + 'json/playlist/documentales/background.jpg', search_type = 'movie' ))

    itemlist.append(item.clone( title = 'Buscar película ...', action = 'search', search_type = 'movie' ))


    plot = 'Para poder utilizar este canal es posible que necesites configurar algún proxy si no te funcionan los vídeos.'
    itemlist.append(item.clone( title = 'Configurar proxies a usar ...', action = 'configurar_proxies', folder=False, plot=plot, text_color='red' ))

    return itemlist


def list_subcategorias(item):
    logger.info()
    itemlist = []

    data = jsontools.load(httptools.downloadpage(item.url, use_cache=True).data)
    # ~ logger.debug(data)

    for datos in data['sortedPlaylistChilds']:
        if datos['id'] in ['000-novedades', 'lo-mas-visto', 'peliculas-mas-vistas', 'ultimas-peliculas']: continue # ya mostrado en mainlist_pelis

        url = host + 'json/playlist/%s/index.json' % datos['id']

        if 'hasBackground' in datos and datos['hasBackground']: thumb = host + 'json/playlist/%s/background.jpg' % datos['id']
        elif 'hasPoster' in datos and datos['hasPoster']: thumb = host + 'json/playlist/%s/poster.jpg' % datos['id']
        else: thumb = host + 'json/playlist/%s/thumbnail.jpg' % datos['id']

        if datos['season'] or datos['seasonNumber'] or datos['numberOfSeasons']:
            itemlist.append(item.clone( action='temporadas', url=url, title=datos['name'].capitalize(), thumbnail=thumb,
                                        contentType='tvshow', contentSerieName=datos['name'].capitalize(), 
                                        infoLabels={'year': datos['year'], 'plot': datos['description']} ))
        else:
            itemlist.append(item.clone( title = datos['name'].capitalize(), action = 'list_all', url = url, 
                                        thumbnail = thumb, contentPlot = datos['description'] ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []
    
    if not item.page: item.page = 0
    
    campo = 'objectList' if '/search?q=' in item.url else 'sortedRepoChilds'

    data = jsontools.load(httptools.downloadpage(item.url, use_cache=True).data)
    data[campo] = filter(lambda x: 'height' in x and not x['isSeason'] and x['name'] != '', data[campo]) # limitar a películas
    num_matches = len(data[campo])

    if 'id' in data and data['id'] not in ['000-novedades', 'lo-mas-visto', 'peliculas-mas-vistas', 'ultimas-peliculas'] and \
       'sortedPlaylistChilds' in data and len(data['sortedPlaylistChilds']) > 0:

        itemlist.append(item.clone( title = 'Subcategorías (%d) de %s' % (len(data['sortedPlaylistChilds']), data['name']), 
                                    action = 'list_subcategorias', text_color='gold'  ))

    for datos in data[campo][item.page * perpage:]:
        # ~ logger.debug(datos)

        url = host + 'json/repo/%s/index.json' % datos['id']
        thumb = (host + 'json/repo/%s/poster.jpg' % datos['id']) if datos['hasPoster'] else ''
        
        quality = 'SD' if datos['height'] < 720 else '720p' if datos['height'] < 1080 else '1080p' if datos['height'] < 2160 else '4K'
        langs = []
        for lg in datos['languages']:
            if len(lg) > 2 and lg[2:] != 'und': langs.append(lg[2:].capitalize())

        itemlist.append(item.clone( action='findvideos', url=url, title=datos['name'], thumbnail=thumb,
                                    languages=', '.join(langs), qualities=quality, 
                                    referer=host+'film/'+datos['id']+'/',
                                    contentType='movie', contentTitle=datos['name'], infoLabels={'year': datos['year'], 'plot': datos['description']} ))

        if len(itemlist) >= perpage: break


    tmdb.set_infoLabels(itemlist)

    if num_matches > perpage: # subpaginación interna dentro de la página si hay demasiados items
        hasta = (item.page * perpage) + perpage
        if hasta < num_matches:
            itemlist.append(item.clone( title='>> Página siguiente', page=item.page + 1, action='list_all' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    headers = default_headers.copy()
    cookies = {}

    proxies = config.get_setting('proxies', item.channel, default='').replace(' ', '')
    if ';' in proxies: # Si los proxies estan separados por ; orden aleatorio
        proxies = proxies.replace(',', ';').split(';')
        import random
        random.shuffle(proxies)
    else:
        proxies = proxies.split(',')

    proxy_ok = False
    for n, proxy in enumerate(proxies):
        use_proxy = None if proxy == '' else {'http': proxy}

        # 1- /film/... (obtener cookies __cfduid y __cflb)
        resp = httptools.downloadpage(item.referer, headers=headers, only_headers=True, cookies=False, use_proxy=use_proxy, raise_weberror=False)
        if (type(resp.code) == int and (resp.code < 200 or resp.code > 399)) or not resp.sucess:
            logger.info('El proxy %s NO responde adecuadamente. %s' % (proxy, resp.code))
        else:
            proxy_ok = True
            logger.info('El proxy %s parece válido.' % proxy)
            if n > 0: # guardar el proxy que ha funcionado como primero de la lista si no lo está
                del proxies[n]
                new_proxies = proxy + ', ' + ', '.join(proxies)
                config.set_setting('proxies', new_proxies, item.channel)
            break
    if not proxy_ok: 
        platformtools.dialog_notification('Sin respuesta válida', 'Ninguno de los proxies ha funcionado.')
        return itemlist

    cks = httptools.get_cookies_from_headers(resp.headers)
    cookies.update(cks)

    # 2- /video2-prod/s/c (obtener cookie c)
    headers['Referer'] = item.referer
    headers['Cookie'] = '; '.join([ck_name + '=' + ck_value for ck_name, ck_value in cookies.items()])
    resp = httptools.downloadpage('http://tv-vip.com/video2-prod/s/c', headers=headers, cookies=False, use_proxy=use_proxy)
    cks = httptools.get_cookies_from_headers(resp.headers)
    cookies.update(cks)

    # 3- /json/repo/...
    headers['X-Requested-With'] = 'XMLHttpRequest'
    headers['Cookie'] = '; '.join([ck_name + '=' + ck_value for ck_name, ck_value in cookies.items()])
    try:
        data = jsontools.load(httptools.downloadpage(item.url, headers=headers, cookies=False, use_proxy=use_proxy).data)
    except:
        return itemlist
    if 'profiles' not in data:
        return itemlist

    # 4- /vendors/font-awesome/ (por cf_clearance !? required !?)
    url = 'http://tv-vip.com/vendors/font-awesome/fonts/fontawesome-webfont.woff2?v=4.7.0'
    headers['Referer'] = 'http://tv-vip.com/vendors/font-awesome/css/font-awesome.min.css'
    headers['Accept-Encoding'] = 'identity'
    del headers['X-Requested-With']
    resp = httptools.downloadpage(url, headers=headers, only_headers=True, cookies=False, use_proxy=use_proxy)


    for perfil, datos in data['profiles'].items():
        for servidor in datos['servers']:
            if servidor['id'] == 's2': continue # con s2 parece que siempre falla el vídeo

            itemlist.append(Item( channel = item.channel, action = 'play', server = 'directo', title = '', 
                                  videoUri = datos['videoUri'], videoServer = servidor['id'],
                                  referer = item.referer, cookies = headers['Cookie'], use_proxy = use_proxy, 
                                  language = '', quality = datos['videoResolution'], quality_num = datos['height'],
                                  other = datos['sizeHuman'] + ', ' + servidor['id']
                           ))

    # ~ return sorted(itemlist, key=lambda it: it.quality_num) # ordenar por calidad ascendente
    return itemlist


def play(item):
    logger.info()
    itemlist = []

    # 5- /video2-prod/s/uri?...
    headers = default_headers.copy()
    headers['Referer'] = item.referer
    headers['X-Requested-With'] = 'XMLHttpRequest'
    headers['Cookie'] = item.cookies

    url = 'http://tv-vip.com/video2-prod/s/uri?uri=/transcoder' + item.videoUri + '&s=' + item.videoServer
    data = jsontools.load(httptools.downloadpage(url, headers=headers, cookies=False, use_proxy=item.use_proxy).data)
    # ~ logger.debug(data)
    if 'a' not in data: return itemlist

    #if data['b'].endswith('.com') or data['b'].endswith('.tv'): # cuando resuelve a estos dominios falla el vídeo
    #    return itemlist
    #url2 = "http://" + item.videoServer + "." + data['b'] + "/e/transcoder" + item.videoUri + "?tt=" + str(data['a']['tt']) + "&mm=" + data['a']['mm'] + "&bb=" + data['a']['bb']

    url2 = "http://" + item.videoServer + ".tv-vip.info/e/transcoder" + item.videoUri + "?tt=" + str(data['a']['tt']) + "&mm=" + data['a']['mm'] + "&bb=" + data['a']['bb']

    url2 += '|User-Agent=%s' % headers['User-Agent']
    itemlist.append(item.clone(url = url2))

    return itemlist


def search(item, texto):
    logger.info("texto: %s" % texto)
    try:
        item.url = host + 'video-prod/s/search?q=' + texto.replace(" ", "+") + '&n=&p='
        if item.search_type == 'tvshow':
            return list_all_series(item)
        else:
            item.search_type = 'movie'
            return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []



def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Lista de series', thumbnail = host + 'json/playlist/series/background.jpg', 
                                action = 'list_all_series', url = host + 'json/playlist/series/index.json', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Series infantiles', thumbnail = host + 'json/playlist/series-infantiles/background.jpg', 
                                action = 'list_all_series', url = host + 'json/playlist/series-infantiles/index.json', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))


    plot = 'Para poder utilizar este canal es posible que necesites configurar algún proxy si no te funcionan los vídeos.'
    itemlist.append(item.clone( title = 'Configurar proxies a usar ...', action = 'configurar_proxies', folder=False, plot=plot, text_color='red' ))

    return itemlist


def list_all_series(item):
    logger.info()
    itemlist = []
    
    if not item.page: item.page = 0
    
    campo = 'objectList' if '/search?q=' in item.url else 'sortedPlaylistChilds'

    data = jsontools.load(httptools.downloadpage(item.url, use_cache=True).data)
    data[campo] = filter(lambda x: 'numberOfSeasons' in x and x['numberOfSeasons'] != '' and x['name'] != '', data[campo]) # limitar a series
    num_matches = len(data[campo])

    for datos in data[campo][item.page * perpage:]:

        url = host + 'json/playlist/%s/index.json' % datos['id']
        thumb = (host + 'json/playlist/%s/poster.jpg' % datos['id']) if datos['hasPoster'] else ''
        
        itemlist.append(item.clone( action='temporadas', url=url, title=datos['name'], thumbnail=thumb,
                                    contentType='tvshow', contentSerieName=datos['name'], 
                                    infoLabels={'year': datos['year'], 'plot': datos['description']} ))

        if len(itemlist) >= perpage: break


    tmdb.set_infoLabels(itemlist)

    if num_matches > perpage: # subpaginación interna dentro de la página si hay demasiados items
        hasta = (item.page * perpage) + perpage
        if hasta < num_matches:
            itemlist.append(item.clone( title='>> Página siguiente', page=item.page + 1, action='list_all_series' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = jsontools.load(httptools.downloadpage(item.url).data)
    
    # Si no hay info de temporadas y hay lista de episodios considerarlo temporada 1
    if len(data['sortedPlaylistChilds']) == 0 and 'sortedRepoChilds' in data and len(data['sortedRepoChilds']) > 0:
        itemlist.append(item.clone( action='episodios', title='Temporada 1',
                                    contentType = 'season', contentSeason = 1 ))
        tmdb.set_infoLabels(itemlist)
        return itemlist

    for datos in data['sortedPlaylistChilds']:

        url = host + 'json/playlist/%s/index.json' % datos['id']
        thumb = (host + 'json/playlist/%s/poster.jpg' % datos['id']) if datos['hasPoster'] else ''

        # ~ titulo = 'Extras' if datos['seasonNumber'] == '' else ('Temporada ' + datos['seasonNumber'])
        titulo = datos['name']
        try:
            season = int(datos['seasonNumber'])
        except:
            season = 0

        itemlist.append(item.clone( action='episodios', title=titulo, url=url, thumbnail=thumb,
                                    contentType = 'season', contentSeason = season ))

    tmdb.set_infoLabels(itemlist)

    # Corrección temporadas inexistentes. Ej: serie infantil Érase una vez...
    for it in itemlist:
        # ~ logger.debug(it)
        # Si es una temporada no prevista, apuntar su nombre por si se guarda en la videoteca
        if 'number_of_seasons' in it.infoLabels and it.contentSeason > it.infoLabels['number_of_seasons']:
            it.infoLabels['temporada_nombre'] = it.title

    # ~ return itemlist
    return sorted(itemlist, key=lambda it: it.contentSeason)


def episodios(item):
    logger.info()
    itemlist = []

    data = jsontools.load(httptools.downloadpage(item.url).data)

    if 'sortedRepoChilds' not in data: return itemlist

    for datos in data['sortedRepoChilds']:
        if 'episode' not in datos or not datos['episode'].isdigit(): continue

        url = host + 'json/repo/%s/index.json' % datos['id']
        thumb = (host + 'json/repo/%s/poster.jpg' % datos['id']) if datos['hasPoster'] else ''
        
        quality = 'SD' if datos['height'] < 720 else '720p' if datos['height'] < 1080 else '1080p' if datos['height'] < 2160 else '4K'
        langs = []
        for lg in datos['languages']:
            if len(lg) > 2: langs.append(lg[2:].capitalize())

        titulo = datos['name']
        if len(langs) > 0: titulo += ' [%s]' % (', '.join(langs))
        titulo += ' [%s]' % quality

        itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb,
                                    # ~ languages=', '.join(langs), qualities=quality, 
                                    referer=host+'film/'+datos['id']+'/',
                                    contentType = 'episode', contentEpisodeNumber = int(datos['episode']) ))

    tmdb.set_infoLabels(itemlist)

    return itemlist
