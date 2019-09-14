# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Balandro - Menú principal
# ------------------------------------------------------------

from platformcode import config, logger, platformtools
from core.item import Item

from core import channeltools


# MAIN
# ====

def mainlist(item):
    logger.info()
    item.category = config.__addon_name
    
    itemlist = []
    
    itemlist.append(item.clone( action='channels', extra='movies', title='Películas', thumbnail=config.get_thumb('movie') ))

    itemlist.append(item.clone( action='channels', extra='tvshows', title='Series', thumbnail=config.get_thumb('tvshow') ))

    itemlist.append(item.clone( action='channels', extra='documentaries', title='Documentales', thumbnail=config.get_thumb('documentary') ))

    itemlist.append(Item( channel='generos', action='mainlist', title='Géneros', thumbnail=config.get_thumb('genres') ))

    itemlist.append(Item( channel='search', action='mainlist', title='Buscar', thumbnail=config.get_thumb('search') ))

    itemlist.append(Item( channel='tracking', action='mainlist', title='Enlaces guardados  (videoteca)', thumbnail=config.get_thumb('videolibrary') ))

    itemlist.append(Item( channel='downloads', action='mainlist', title='Descargas', thumbnail=config.get_thumb('downloads') ))

    itemlist.append(Item( channel='actions', action='open_settings', title='Configuración / Ayuda (Balandro v%s)' % config.get_addon_version(), 
                          folder=False, thumbnail=config.get_thumb('settings') ))

    if config.get_setting('channels_link_main', default=False):
        itemlist.append(item.clone( action='channels', extra='all', title='Canales', thumbnail=config.get_thumb('stack') ))

    # Developers:
    import os
    if os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'test.py')):
        itemlist.append(Item( channel='test', action='mainlist', title='Tests Canales y Servidores', thumbnail=config.get_thumb('dev') ))
    if os.path.exists(os.path.join(config.get_runtime_path(), 'modules', 'developer.py')):
        itemlist.append(Item( channel='developer', action='mainlist', title='Gestión de géneros', thumbnail=config.get_thumb('dev') ))

    return itemlist


def channels(item):
    logger.info()
    itemlist = []
    
    if item.extra == 'movies':
        item.category = 'Canales con Películas'
        accion = 'mainlist_pelis'
        filtros = {'categories': 'movie'}

    elif item.extra == 'tvshows':
        item.category = 'Canales con Series'
        accion = 'mainlist_series'
        filtros = {'categories': 'tvshow'}

    elif item.extra == 'documentaries':
        item.category = 'Canales con Documentales'
        accion = 'mainlist'
        filtros = {'categories': 'documentary'}

    else:
        item.category = 'Todos los Canales'
        accion = 'mainlist'
        filtros = {}

    channels_list_status = config.get_setting('channels_list_status', default=0) # 0:Todos, 1:preferidos+activos, 2:preferidos
    if channels_list_status > 0:
        filtros['status'] = 0 if channels_list_status == 1 else 1
    color_preferidos = config.get_setting('channels_list_prefe_color')

    ch_list = channeltools.get_channels_list(filtros=filtros)
    for ch in ch_list:
        context = []
        if ch['status'] != -1:
            context.append({'title': 'Marcar como Desactivado', 'channel': item.channel, 'action': 'marcar_canal', 'estado': -1})
        if ch['status'] != 0:
            context.append({'title': 'Marcar como Activo', 'channel': item.channel, 'action': 'marcar_canal', 'estado': 0})
        if ch['status'] != 1:
            context.append({'title': 'Marcar como Preferido', 'channel': item.channel, 'action': 'marcar_canal', 'estado': 1})

        color = color_preferidos if ch['status'] == 1 else 'white' if ch['status'] == 0 else 'gray'

        plot = ''
        if item.extra == 'all': plot += '[' + ', '.join([config.get_localized_category(ct) for ct in ch['categories']]) + '][CR]'
        plot += '[' + ', '.join([idioma_canal(lg) for lg in ch['language']]) + ']'
        if ch['notes'] != '': plot += '[CR][CR]' + ch['notes']
        
        titulo = ch['name']
        if ch['status'] == -1: titulo += ' (desactivado)'
        
        itemlist.append(Item( channel=ch['id'], action=accion, title=titulo, context=context, text_color=color, plot = plot,
                              thumbnail=ch['thumbnail'], category=ch['name'] ))

    if item.extra == 'movies':
        itemlist.append(Item( channel='search', action='search', search_type='movie', title='Buscar Película ...', thumbnail=config.get_thumb('search') ))
    elif item.extra == 'tvshows':
        itemlist.append(Item( channel='search', action='search', search_type='tvshow', title='Buscar Serie ...', thumbnail=config.get_thumb('search') ))
    elif item.extra == 'documentaries':
        itemlist.append(Item( channel='search', action='search', search_type='documentary', title='Buscar Documental ...', thumbnail=config.get_thumb('search') ))

    return itemlist


def idioma_canal(lang):
    idiomas = { 'cast':'Castellano', 'lat':'Latino', 'eng':'Inglés', 'por':'Portugués', 'vo':'VO', 'vose':'VOSE', 'vos':'VOS', 'cat':'Català' }
    return idiomas[lang] if lang in idiomas else lang


def marcar_canal(item):
    logger.info()

    config.set_setting('status', item.estado, item.from_channel)

    platformtools.itemlist_refresh()
    return True


# ~ def marcar_servidor(item):
    # ~ logger.info()

    # ~ config.set_setting('status', item.estado, server=item.server)

    # ~ platformtools.itemlist_refresh()
    # ~ return True
