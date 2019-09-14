# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Balandro - Buscador global
# ------------------------------------------------------------

import time
from threading import Thread

from platformcode import config, logger, platformtools
from core.item import Item

from core import channeltools



def mainlist(item):
    logger.info()
    itemlist = []

    item.category = 'Buscar'
    
    itemlist.append(item.clone( channel='tmdblists', action='mainlist', title='Listas y búsquedas en TMDB', thumbnail=config.get_thumb('bookshelf'),
                                plot = 'Buscar personas y ver listas de películas y series de la base de datos de The Movie Database' ))

    itemlist.append(item.clone( action='search', search_type='movie', title='Buscar Película ...', thumbnail=config.get_thumb('movie'),
                                plot = 'Escribir el nombre de una película para buscarla en los canales de películas' ))

    itemlist.append(item.clone( action='search', search_type='tvshow', title='Buscar Serie ...', thumbnail=config.get_thumb('tvshow'),
                                plot = 'Escribir el nombre de una serie para buscarla en los canales de series' ))

    itemlist.append(item.clone( action='search', search_type='documentary', title='Buscar Documental ...', thumbnail=config.get_thumb('documentary'),
                                plot = 'Escribir el nombre de un documental para buscarlo en los canales de documentales' ))

    itemlist.append(item.clone( action='search', search_type='all', title='Buscar Película y/o Serie ...',
                                plot = 'Buscar indistintamente películas o series en todos los canales del addon' ))

    # ~ itemlist.append(item.clone( action='show_help', title='Información sobre búsquedas', folder=False, thumbnail=config.get_thumb('help') ))

    return itemlist


def show_help(item):
    txt = 'Desde la configuración del addon se puede definir el número de resultados que se previsualizan para cada canal.'
    txt += ' Si por ejemplo el canal devuelve 15 resultados y se previsualizan 2, entrar en el enlace de la búsqueda para verlos todos.'
    txt += '[CR]'
    txt += '[CR]Según cada web/canal su buscador puede permitir diferenciar por películas/series o no, y también es variable la sensibilidad de la búsqueda (si busca sólo en el título o también en la sinopsi, el tratamiento si hay varias palabras, si devuelve muchos o pocos resultados, etc)'
    txt += '[CR]'
    txt += '[CR]Desde cualquier película/serie mostrada en el addon, acceder al menú contextual para buscar esa misma película/serie en los demás canales.'
    txt += '[CR]'
    txt += '[CR]Desde cualquier película/serie guardada en enlaces, si al acceder se produce un error en la web, se ofrece un diálogo para volver a buscar esa misma película/serie en los demás canales o en el mismo canal (por si han cambiado las urls de la web y el enlace ya no funciona).'

    platformtools.dialog_textviewer('Información sobre búsquedas', txt)
    return True



def search(item, tecleado):
    logger.info()

    item.category = 'Buscar ' + tecleado
    if item.search_type == '': item.search_type = 'all'

    itemlist = do_search(item, tecleado)

    return itemlist


def do_search_channel(item, tecleado, ch):
    canal = __import__('channels.' + item.channel, fromlist=[''])
    if hasattr(canal, 'search'):
        ch['itemlist_search'] = canal.search(item, tecleado)
    else:
        logger.error('Search not found in channel %s. Implementar search o quitar searchable!' % item.channel)


def do_search(item, tecleado):
    itemlist = []
    # De item se usa .search_type y .from_channel
    
    multithread = config.get_setting('search_multithread', default=True)
    threads = []
    search_limit_by_channel = config.get_setting('search_limit_by_channel', default=2)
    
    progreso = platformtools.dialog_progress('Buscando '+tecleado, '...')

    # Seleccionar los canales dónde se puede buscar
    # ---------------------------------------------
    filtros = { 'searchable': True, 'status': 0 } # status para descartar desactivados por el usuario, solamente se busca en activos y preferidos
    if item.search_type != 'all': filtros['search_types'] = item.search_type

    ch_list = channeltools.get_channels_list(filtros=filtros)
    if item.from_channel != '': # descartar from_channel (búsqueda en otros canales)
        ch_list = [ch for ch in ch_list if ch['id'] != item.from_channel]
    if item.search_type == 'all': # descartar documentary cuando 'all'
        ch_list = [ch for ch in ch_list if 'documentary' not in ch['categories']]
    num_canales = float(len(ch_list)) # float para calcular porcentaje
    
    # Hacer la búsqueda en cada canal
    # -------------------------------
    for i, ch in enumerate(ch_list):
        perc = int(i / num_canales * 100)
        progreso.update(perc, 'Buscando '+tecleado, 'Procesando canal '+ch['name'])

        c_item = Item( channel=ch['id'], action='search', search_type=item.search_type, title='Buscar en '+ch['name'], thumbnail=ch['thumbnail'] )

        if multithread:
            t = Thread(target=do_search_channel, args=[c_item, tecleado, ch], name=ch['name'])
            t.setDaemon(True)
            t.start()
            threads.append(t)
        else:
            do_search_channel(c_item, tecleado, ch)

        if progreso.iscanceled(): break

    if multithread: # bucle de espera hasta que acabe o se cancele
        pendent = [a for a in threads if a.isAlive()]
        while len(pendent) > 0:
            hechos = num_canales - len(pendent)
            perc = int(hechos / num_canales * 100)
            mensaje = ', '.join([a.getName() for a in pendent])

            progreso.update(perc, 'Finalizado en %d de %d canales. Quedan %d :' % (hechos, num_canales, len(pendent)), mensaje)

            if progreso.iscanceled(): break

            time.sleep(0.5)
            pendent = [a for a in threads if a.isAlive()]


    # Mostrar resultados de las búsquedas
    # -----------------------------------
    if item.from_channel != '': 
        # Búsqueda exacta en otros/todos canales de una peli/serie : mostrar sólo las coincidencias exactas
        tecleado_lower = tecleado.lower()
        for ch in ch_list:
            if 'itemlist_search' in ch and len(ch['itemlist_search']) > 0:
                for it in ch['itemlist_search']:
                    if it.contentType not in ['movie','tvshow']: continue # paginaciones
                    if it.infoLabels['tmdb_id'] and item.infoLabels['tmdb_id']:
                        if it.infoLabels['tmdb_id'] != item.infoLabels['tmdb_id']: continue
                    else:
                        if it.contentType == 'movie' and it.contentTitle.lower() != tecleado_lower: continue
                        if it.contentType == 'tvshow' and it.contentSerieName.lower() != tecleado_lower: continue
                    it.title += ' [COLOR gold][%s][/COLOR]' % ch['name']
                    itemlist.append(it)

    else:
        # Búsqueda parecida en todos los canales : link para acceder a todas las coincidencias y previsualización de n enlaces por canal
        # Mover al final los canales que no tienen resultados
        # ~ for ch in ch_list:
        for ch in sorted(ch_list, key=lambda ch: True if 'itemlist_search' not in ch or len(ch['itemlist_search']) == 0 else False):
            if 'itemlist_search' in ch:
                if len(ch['itemlist_search']) == 0:
                    titulo = 'Sin resultados en '+ch['name']
                    color = 'red'
                else:
                    titulo = '%d resultados en %s ...' % (len(ch['itemlist_search']), ch['name'])
                    color = 'gold'
            else:
                color = 'gray'
                if progreso.iscanceled():
                    titulo = 'Cancelado antes de buscar en '+ch['name']
                else:
                    titulo = 'No se puede buscar en '+ch['name']
            
            titulo = '[B][COLOR %s]%s[/COLOR][/B]' % (color, titulo)
            itemlist.append(Item( channel=ch['id'], action='search', buscando=tecleado, title=titulo, thumbnail=ch['thumbnail'], search_type=item.search_type ))
            if 'itemlist_search' in ch:
                for j, it in enumerate(ch['itemlist_search']):
                    if it.contentType not in ['movie','tvshow']: continue # paginaciones
                    if j < search_limit_by_channel:
                        itemlist.append(it)
                    else:
                        break

    progreso.close()
    
    return itemlist
