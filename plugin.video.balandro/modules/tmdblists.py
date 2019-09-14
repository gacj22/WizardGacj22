# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Balandro - Listados de peliculas de TMDB
# ------------------------------------------------------------

from platformcode import config, logger, platformtools
from core.item import Item
from core import tmdb


def mainlist(item):
    logger.info()
    itemlist = []

    item.category = 'TMDB'
    
    itemlist.append(item.clone( action='personas', search_type='cast', title='Buscar por Personas (Interpretación) ...',
                                plot = 'Escribir el nombre de un actor o una actriz para listar todas las películas y series en las que ha intervenido.' ))

    itemlist.append(item.clone( action='personas', search_type='crew', title='Buscar por Personas (Dirección) ...',
                                plot = 'Escribir el nombre de una persona para listar todas las películas y series que ha dirigido.' ))

    itemlist.append(item.clone( action='listado_personas', search_type='person', extra = 'popular', title='Personas más Populares' ))

    itemlist.append(item.clone( action='listado', search_type='movie', extra = 'popular', title='Películas más Populares' ))
    itemlist.append(item.clone( action='listado', search_type='movie', extra = 'top_rated', title='Películas Mejor Valoradas' ))
    itemlist.append(item.clone( action='listado', search_type='movie', extra = 'now_playing', title='Películas en Cartelera' ))
    # ~ itemlist.append(item.clone( action='listado', search_type='movie', url = 'movie/upcoming', title='Próximas Películas' ))
    itemlist.append(item.clone( action='generos', search_type='movie', title='Películas por Géneros' ))

    itemlist.append(item.clone( action='listado', search_type='tvshow', extra = 'popular', title='Series más Populares' ))
    itemlist.append(item.clone( action='listado', search_type='tvshow', extra = 'top_rated', title='Series Mejor Valoradas' ))
    itemlist.append(item.clone( action='listado', search_type='tvshow', extra = 'on_the_air', title='Series emitiéndose actualmente' ))
    # ~ itemlist.append(item.clone( action='listado', search_type='tvshow', url = 'tv/airing_today', title='Series que se emiten Hoy' ))
    itemlist.append(item.clone( action='generos', search_type='tvshow', title='Series por Géneros' ))

    itemlist.append(item.clone( action='show_help', title='Información / Ayuda', folder=False, thumbnail=config.get_thumb('help') ))

    return itemlist


def show_help(item):
    txt = 'En este apartado se pueden hacer consultas a la web [B]The Movie Database[/B] (TMDb), un proyecto comunitario que ofrece información de películas, series y personas.'

    txt += '[CR]'
    txt += '[CR]Se puede buscar la filmografía de una persona y ver las películas/series en dónde ha participado.'
    txt += ' Y también se pueden ver distintas listas de películas, series y personas según varios conceptos (más populares, más valoradas, por géneros, etc).'

    txt += '[CR]'
    txt += '[CR]Al seleccionar una película/serie se iniciará su búsqueda en los diferentes canales del addon y se mostrarán los resultados encontrados.'
    txt += ' Hay que tener en cuenta que habrá películas/series que no tendrán enlaces en ninguno de los canales.'

    txt += '[CR]'
    txt += '[CR]Si al buscar por persona se obtiene una sola coincidencia, se listan directamente sus películas y series (Ej: Stanley Kubrick).'
    txt += ' Si puede haber varios resultados se muestra una lista de personas para seleccionar la que corresponda (Ej: Kubrick).'

    platformtools.dialog_textviewer('Información / Ayuda', txt)
    return True


def texto_busqueda(txt):
    if ':' in txt: return txt.split(':')[1].strip()
    return txt

def lista(item, elementos):
    itemlist = []
    if not item.page: item.page = 1

    for elemento in elementos:
        # ~ logger.debug(elemento)
        titulo = elemento['title'] if 'title' in elemento else elemento['name']

        if 'title' in elemento:
            itemlist.append(item.clone( channel='search', action = 'search', buscando = texto_busqueda(titulo), from_channel = item.channel, 
                                        title = titulo, search_type = 'movie', 
                                        contentType = 'movie', contentTitle = titulo, infoLabels = {'tmdb_id': elemento['id']} ))
        else:
            itemlist.append(item.clone( channel='search', action = 'search', buscando = texto_busqueda(titulo), from_channel = item.channel, 
                                        title = titulo, search_type = 'tvshow', 
                                        contentType = 'tvshow', contentSerieName = titulo, infoLabels = {'tmdb_id': elemento['id']} ))

    tmdb.set_infoLabels(itemlist)
    
    if len(itemlist) > 0:
        itemlist.append(item.clone( title='Página siguiente >>', page = item.page + 1 ))

    return itemlist


def listado(item):
    logger.info()

    tipo = 'movie' if item.search_type == 'movie' else 'tv'
    elementos = tmdb.get_list(tipo, item.extra, item.page)
    
    return lista(item, elementos)
    

def descubre(item):
    logger.info()

    tipo = 'movie' if item.search_type == 'movie' else 'tv'
    elementos = tmdb.get_discover(tipo, item.extra, item.page)

    return lista(item, elementos)


def generos(item):
    logger.info()
    itemlist = []

    tipo = 'movie' if item.search_type == 'movie' else 'tv'
    elementos = tmdb.get_genres(tipo)
    # ~ logger.debug(elementos)

    for codigo, titulo in elementos[tipo].items():

        itemlist.append(item.clone( title=titulo, action='descubre', extra = codigo ))

    return sorted(itemlist, key=lambda it: it.title)



def personas(item):
    logger.info()
    itemlist = []
    
    if not item.person_id:
        # Diálogo para introducir el texto de la persona buscada
        # ------------------------------------------------------
        last_search = config.get_setting('search_last_person', default='')
        tecleado = platformtools.dialog_input(last_search, 'Nombre de la persona a buscar')
        if tecleado is None or tecleado == '':
            return itemlist
        config.set_setting('search_last_person', tecleado)
        
        # Diálogo para escoger entre la lista posible de gente
        # ----------------------------------------------------
        elementos = tmdb.get_person(tecleado)
        
        if len(elementos) == 0:
            platformtools.dialog_notification('Persona no encontrada', 'Sin resultados para [COLOR gold]%s[/COLOR]' % tecleado)
            return itemlist

        elif len(elementos) == 1:
            item.person_id = elementos[0]['id']
            item.category = elementos[0]['name']
        
        else:
            opciones = []; opciones_ids = [];
            for elemento in elementos:
                # ~ logger.debug(elemento)
                info = ''
                for detalle in elemento['known_for']:
                    if info != '': info += ', '
                    if 'title' in detalle:
                        info += '%s (%s)' % (detalle['title'], detalle['release_date'][:4])
                    else:
                        info += '%s (TV %s)' % (detalle['name'], detalle['first_air_date'][:4])
                    
                thumb = ''
                if elemento['profile_path']:
                    thumb = 'https://image.tmdb.org/t/p/w235_and_h235_face%s' % elemento['profile_path']
                
                opciones.append(platformtools.listitem_to_select(elemento['name'], info, thumb))
                opciones_ids.append(elemento['id'])

            ret = platformtools.dialog_select('Selecciona la persona que buscas', opciones, useDetails=True)
            if ret == -1: 
                return itemlist # pedido cancel

            item.person_id = opciones_ids[ret]
            item.category = opciones[ret].getLabel()
    
    # Listar pelis y series de la persona
    # -----------------------------------
    if not item.page: item.page = 1

    elementos = tmdb.get_person_credits(item.person_id, item.search_type)
    
    if item.search_type == 'crew': # filtrar solamente dirección
        elementos = filter(lambda it: 'job' in it and it['job'] == 'Director', elementos)

    perpage = 20
    num_elementos = len(elementos)
    desde = (item.page - 1) * perpage
    # ~ logger.info('Hay %d pelis/series para %s' % (num_elementos, item.category))
    
    for elemento in elementos[desde:]:
        titulo = elemento['title'] if 'title' in elemento else elemento['name']
        sufijo = ''
        if 'name' in elemento: sufijo += '[COLOR hotpink](TV)[/COLOR] '
        # ~ if 'job' in elemento: sufijo += '[COLOR gray][I]%s[/I][/COLOR]' % elemento['job']
        if 'character' in elemento: sufijo += '[LIGHT][COLOR gray][I]%s[/I][/COLOR][/LIGHT]' % elemento['character']

        if 'title' in elemento:
            itemlist.append(item.clone( channel='search', action = 'search', buscando = texto_busqueda(titulo), from_channel = item.channel, 
                                        title = titulo, fmt_sufijo=sufijo, search_type = 'movie', 
                                        contentType = 'movie', contentTitle = titulo, infoLabels = {'tmdb_id': elemento['id']} ))
        else:
            itemlist.append(item.clone( channel='search', action = 'search', buscando = texto_busqueda(titulo), from_channel = item.channel, 
                                        title = titulo, fmt_sufijo=sufijo, search_type = 'tvshow', 
                                        contentType = 'tvshow', contentSerieName = titulo, infoLabels = {'tmdb_id': elemento['id']} ))

        if len(itemlist) >= perpage: break

    tmdb.set_infoLabels(itemlist)
    
    if desde + perpage < num_elementos:
        itemlist.append(item.clone( title='Página siguiente >>', page = item.page + 1 ))

    return itemlist


def listado_personas(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 1

    elementos = tmdb.get_list('person', item.extra, item.page)

    for elemento in elementos:
        info = ''
        for detalle in elemento['known_for']:
            if info != '': info += ', '
            if 'title' in detalle:
                info += '%s (%s)' % (detalle['title'], detalle['release_date'][:4])
            else:
                info += '%s (TV %s)' % (detalle['name'], detalle['first_air_date'][:4])
            
        thumb = ''
        if elemento['profile_path']:
            thumb = 'https://image.tmdb.org/t/p/w235_and_h235_face%s' % elemento['profile_path']

        itemlist.append(item.clone( action = 'personas', person_id = elemento['id'], search_type = 'cast', page = 1, 
                                    title = elemento['name'], thumbnail = thumb, plot = info, category = elemento['name'] ))
        
    if len(itemlist) > 0:
        itemlist.append(item.clone( title='Página siguiente >>', page = item.page + 1 ))

    return itemlist
