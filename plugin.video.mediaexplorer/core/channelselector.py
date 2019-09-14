# -*- coding: utf-8 -*-
from core.libs import *


def mainlist(item):
    logger.trace()
    itemlist = list()
    item.fanart = "fanart/mediaexplorer.jpg"

    itemlist.append(item.clone(
        label='Canales',
        name='Canales',
        action='channels',
        category='all',
        thumb='thumb/channel.png',
        icon='icon/channel.png',
        poster='poster/channel.png',
        content_type='channels',
        description='Acceso a todos los canales con contenido multimedia, '
                    'todos tus sitios webs favoritos ahora al alcance de tu mediacenter.'
                    '\n\nSoporte en: http://bit.ly/MediaExplorer-Foro'
    ))

    itemlist.append(item.clone(
        label='Categorias',
        name='Categorias',
        action='categories',
        thumb='thumb/category.png',
        icon='icon/category.png',
        poster='poster/category.png',
        content_type='icons',
        description='Acceso a los canales filtrados por categorias para encontrar más facilmente lo que estés buscando.'
                    '\n\nSoporte en: http://bit.ly/MediaExplorer-Foro'
    ))

    itemlist.append(item.clone(
        label='Novedades',
        name='Novedades',
        action='mainlist',
        channel='newest',
        thumb='thumb/newest.png',
        icon='icon/newest.png',
        poster='poster/newest.png',
        content_type='icons',
        description='Acceso directo al contenido nuevo de los diferentes canales.'
                    '\n\nSoporte en: http://bit.ly/MediaExplorer-Foro'
    ))

    itemlist.append(item.clone(
        label='Buscador',
        name='Buscador',
        channel='finder',
        action='mainlist',
        thumb='thumb/search.png',
        icon='icon/search.png',
        poster='poster/search.png',
        content_type='items',
        description='Busca en todos los canales el contenido que quieras encontrar, si existe seguro que aparece.'
                    '\n\nSoporte en: http://bit.ly/MediaExplorer-Foro'
    ))

    itemlist.append(item.clone(
        label='Listas',
        name='Listas',
        channel='lists',
        action='mainlist',
        thumb='thumb/lists.png',
        icon='icon/lists.png',
        poster='poster/lists.png',
        content_type='items',
        description='Crea una lista con tus contenidos preferidos y compartela con tus familiares y amigos.'
                    '\n\nSoporte en: http://bit.ly/MediaExplorer-Foro'
    ))

    itemlist.append(item.clone(
        label='Favoritos',
        name='favoritos',
        channel='bookmarks',
        action='mainlist',
        thumb='thumb/bookmark.png',
        icon='icon/bookmark.png',
        poster='poster/bookmark.png',
        content_type='items',
        description='Organiza tus favoritos para acceder mas rapido a aquellos los lugares que sueles'
                    ' ir con mas frecuencia, ya sea un canal, sección, película, serie o cualquier lugar.'
                    '\n\nSoporte en: http://bit.ly/MediaExplorer-Foro'
    ))

    import library
    itemlist.append(item.clone(
        label='Biblioteca',
        label_extra={'sublabel': ' (%s)', 'value': library.get_new_items()},
        name='Biblioteca',
        channel='library',
        action='mainlist',
        thumb='thumb/library.png',
        icon='icon/library.png',
        poster='poster/library.png',
        content_type='items',
        description='Guarda la colección de peliculas y series que quieres tener a mano para poder verlas cuando '
                    'quieres, puedes añadir tantas fuentes como quieras para cada una.'
                    '\n\nSoporte en: http://bit.ly/MediaExplorer-Foro'
    ))

    itemlist.append(item.clone(
        label='Descargas',
        name='Descargas',
        channel='downloads',
        action='mainlist',
        thumb='thumb/download.png',
        icon='icon/download.png',
        poster='poster/download.png',
        content_type='items',
        description='Gestor de descargas para poder guardar tus peliculas y series favoritas y'
                    ' poder verlas cuando quieras incluso sin conexión.'
                    '\n\nSoporte en: http://bit.ly/MediaExplorer-Foro'
    ))

    from core import updates
    aux = updates.count()
    aux = "(%s)" % aux if aux > 0 else ""
    itemlist.append(item.clone(
        label='Actualizaciones %s' % aux,
        name='Actualizaciones',
        channel='updates',
        action='mainlist',
        thumb='thumb/update.png',
        icon='icon/update.png',
        poster='poster/update.png',
        content_type='items',
        description='Manten MediaExplorer actualizado, las webs cambian continuamente y es necesario ir actualizando'
                    ' los distintos canales para que siempre funcionen correctamente.'
                    '\n\nSoporte en: http://bit.ly/MediaExplorer-Foro'
    ))

    itemlist.append(item.clone(
        label='Ajustes',
        name='Ajustes',
        channel='settings',
        action='mainlist',
        thumb='thumb/setting.png',
        icon='icon/setting.png',
        poster='poster/setting.png',
        content_type='items',
        description='Todos los ajustes de MediaExplorer están en este lugar, accede aqui para gestionar cuentas de '
                    'usuario, activar o deasctivar canales, ajustes visuales y de todo tipo.'
                    '\n\nSoporte en: http://bit.ly/MediaExplorer-Foro'
    ))

    return itemlist


def channels(item=Item(category='all')):
    from distutils.version import LooseVersion
    logger.trace()
    itemlist = list()

    channel_list = moduletools.get_channels()

    for channel in channel_list:
        try:
            # Descartamos canales desactivados
            if settings.get_setting('disabled', channel['path']):
                logger.debug('Canal %s omitido: Canal desactivado' % channel['name'])
                continue

            # Filtramos canales por categorias
            if item.category != 'all' and item.category not in channel['categories']:
                logger.debug('Canal %s omitido: Categoria no coincide' % channel['name'])
                continue

            # Descartamos canales que necesiten una version del plugin superior a la actual
            if channel['min_version']["main"] and LooseVersion(str(sysinfo.main_version)) < LooseVersion(
                    channel['min_version']["main"]):
                logger.debug('Canal %s omitido: Versión MediaExplorer mínima %s' % (
                    channel['name'], channel['min_version']["main"]))
                continue

            # Descartamos canales que necesiten una version de python superior a la actual
            if channel['min_version']["python"] and LooseVersion(sysinfo.py_version) < LooseVersion(
                    channel['min_version']["python"]):
                logger.debug(
                    'Canal %s omitido: Versión Python mínima %s' % (channel['name'], channel['min_version']["python"]))
                continue

            itemlist.append(Item(
                label=channel['name'],
                name=channel['name'],
                channel=channel['id'],
                action='mainlist',
                category=item.category,
                type='channel',
                content_type='items',
                adult=channel['adult'],
                fanart=channel.get('fanart', 'fanart/%s.jpg' % channel['id']),
                poster=channel.get('poster', 'poster/%s.png' % channel['id']),
                icon=channel.get('icon', 'icon/%s.png' % channel['id']),
                thumb=channel.get('thumb', 'thumb/%s.png' % channel['id'])
            ))
        except Exception:
            logger.error()

    return itemlist


def categories(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        label='Películas',
        action='channels',
        category='movie',
        poster='poster/movie.png',
        icon='icon/movie.png',
        thumb='thumb/movie.png',
        content_type='channels'
    ))

    itemlist.append(item.clone(
        label='Series',
        action='channels',
        category='tvshow',
        poster='poster/tvshow.png',
        icon='icon/tvshow.png',
        thumb='thumb/tvshow.png',
        content_type='channels'
    ))

    '''itemlist.append(item.clone(
        label='Anime',
        action='channels',
        category='anime',
        poster='poster/anime.png',
        icon='icon/anime.png',
        thumb='thumb/anime.png',
        content_type='channels'
    ))

    itemlist.append(item.clone(
        label='Infantil',
        action='channels',
        category='child',
        poster='poster/child.png',
        icon='icon/child.png',
        thumb='thumb/child.png',
        content_type='channels'
    ))'''

    itemlist.append(item.clone(
        label='Adulto',
        action='channels',
        category='adult',
        poster='poster/adult.png',
        icon='icon/adult.png',
        thumb='thumb/adult.png',
        content_type='channels',
        adult=True
    ))

    return itemlist


def channel_info(item):
    logger.trace()

    f = os.path.join(sysinfo.runtime_path, 'channels', item.channel + ".json")
    new_item = Item().fromjson(path=f)

    new_item.type = item.type
    new_item.poster = item.poster if item.poster.startswith('http') else \
        os.path.join(sysinfo.runtime_path, 'resources', 'images', *item.poster.split('/'))

    d_categories = dict((i.category, i.label) for i in categories(item))
    new_item.categories = [d_categories[i] for i in new_item.categories]

    d_categories['movie_gender'] = "Géneros"
    new_item.search = [d_categories[i] for i in new_item.search]

    d_categories['episode'] = "Episodios"
    new_item.newest = [d_categories[i] for i in new_item.newest]

    new_item.min_version = ["%s: %s" % (k.capitalize(), v) for k, v in new_item.min_version.items() if v]
    new_item.changes = ["%10s   %s" % (i['date'], i['description']) for i in new_item.changes]

    platformtools.show_info(new_item, new_item.name)
