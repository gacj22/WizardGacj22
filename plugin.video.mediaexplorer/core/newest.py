# -*- coding: utf-8 -*-
from core.libs import *
from core import mediainfo

category = {
    'movie': 'Peliculas',
    'tvshow': 'Series',
    'adult': 'Adultos',
    'episode': 'Episodios',
    'anime': 'Anime',
    'child': 'Infantil'
}


def mainlist(item):
    logger.trace()
    itemlist = list()
    item.type = 'item'

    itemlist.append(item.clone(
        action='search',
        label='Películas',
        category='movie',
        description='Todas las novedades en películas',
        content_type='movies',
        icon='icon/movie.png',
        poster='poster/movie.png',
        thumb='thumb/movie.png'
    ))

    itemlist.append(item.clone(
        action='search',
        label='Series',
        category='tvshow',
        description='Todas las novedades en series',
        content_type='tvshows',
        icon='icon/tvshow.png',
        poster='poster/tvshow.png',
        thumb='thumb/tvshow.png'
    ))

    itemlist.append(item.clone(
        action='search',
        label='Episodios',
        category='episode',
        description='Los últimos episodios actualizados',
        content_type='episodes',
        icon='icon/episode.png',
        poster='poster/episode.png',
        thumb='thumb/episode.png'
    ))

    '''
    itemlist.append(item.clone(
        action='search',
        label='Anime',
        category='anime',
        description='Todas las novedades en anime',
        content_type='movies',
        icon='icon/anime.png',
        poster='poster/anime.png',
        thumb='thumb/anime.png'
    ))
    
    itemlist.append(item.clone(
        action='search',
        label='Infantiles',
        category='child',
        description='Todas las novedades en infantiles',
        icon='icon/child.png',
        content_type='movies',
        poster='poster/child.png',
        thumb='thumb/child.png'
    ))'''

    itemlist.append(item.clone(
        action='config_menu',
        label='Configuración de novedades',
        description='Configuración para la seccion novedades',
        type='setting',
        content_type='items'
    ))

    return itemlist


def config_menu(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        type='label',
        action='',
        label="Canales incluidos en Novedades:"
    ))

    itemlist.append(item.clone(
        action='channels',
        label='Canales para peliculas',
        category='movie',
        group=True,
        description='Elige los canales en los que quieres que se realice la búsqueda',
        type='item'
    ))

    itemlist.append(item.clone(
        action='channels',
        label='Canales para series',
        category='tvshow',
        group=True,
        description='Elige los canales en los que quieres que se realice la búsqueda',
        type='item'
    ))

    itemlist.append(item.clone(
        action='channels',
        label='Canales para episodios',
        category='episode',
        group=True,
        description='Elige los canales en los que quieres que se realice la búsqueda',
        type='item'
    ))

    '''
    itemlist.append(item.clone(
        action='channels',
        label='Canales para anime',
        category='anime',
        group=True,
        description='Elige los canales en los que quieres que se realice la búsqueda',
        type='item'
    ))
    
    itemlist.append(item.clone(
        action='channels',
        label='Canales para infantil',
        category='child',
        group=True,
        description='Elige los canales en los que quieres que se realice la búsqueda',
        type='item'
    ))'''

    itemlist.append(item.clone(
        action='config',
        label='Otros ajustes',
        description='Resto de ajustes del canal novedades',
        type='setting'
    ))

    return itemlist


def config(item):
    logger.trace()
    return platformtools.show_settings()


def channels(item):
    logger.trace()

    channel_list = moduletools.get_channels()
    channel_list = filter(lambda c: c.get('newest') and c['newest'].get(item.category), channel_list)

    controls = []

    values = settings.get_setting('disabled_channels', __file__) or {}
    values = values.get(item.category, [])

    for channel in sorted(channel_list, key=lambda x: x['name']):
        control = {
            'id': channel['id'],
            'type': "bool",
            'label': channel['name'],
            'value': channel['id'] not in values,
            'default': True,
            'enabled': not settings.get_setting("disabled", channel['path'])
        }

        controls.append(control)

    return platformtools.show_settings(controls=controls, title=item.label, callback="save_settings", item=item)


def save_settings(item, values):
    logger.trace()
    disabled_channels = settings.get_setting('disabled_channels', __file__) or {}
    disabled_channels[item.category] = [k for k, v in values.items() if v is False]
    settings.set_setting('disabled_channels', disabled_channels, __file__)


def search(item):
    logger.trace()
    itemlist = list()
    newest_items = list()
    threads = list()
    results = list()
    bloquea = RLock()

    multithread = settings.get_setting('multithread', __file__)
    disabled_channels = settings.get_setting('disabled_channels', __file__) or {}
    disabled_channels = disabled_channels.get(item.category, [])

    # Obtenemos el listado de canales incluidos en las Novedades para esta categoria
    # y no esten desactivados en ajustes/canales
    channel_list = moduletools.get_channels()
    channel_list = filter(lambda c: c.get('newest') and
                            c['newest'].get(item.category) and
                            c['id'] not in disabled_channels and
                            not settings.get_setting("disabled", c['path']),
                            channel_list)


    # Recorresmos los canales
    for channel in channel_list:
        # Añadimos el item de búsqueda
        newest_items.append(Item(
            channel=channel['id'],
            channelname=channel['name'],
            poster='poster/%s.png' % channel['id'],
            icon='icon/%s.png' % channel['id'],
            thumb='thumb/%s.png' % channel['id'],
            adult=item.category == 'adult',
            category=item.category,
            use_proxy=settings.get_setting("use_proxy", channel['path']),
            **channel['newest'][item.category]
        ))

    # Si no hay items de búsqueda mostramos el aviso
    if not newest_items:
        platformtools.dialog_ok('Novedades', '¡No hay canales en los que buscar!')
        return

    # Abrimos el progreso
    dialog = platformtools.dialog_progress('Novedades', 'Iniciando búsqueda en %s canales' % len(newest_items))

    # Lanzamos las busquedas
    for newest_item in newest_items:
        # Modo multithread
        if multithread:
            # Lanzamos la búsqueda
            t = Thread(target=channel_search,
                       args=[newest_item, results, bloquea],
                       name='%s [%s]' % (newest_item.channelname, category[newest_item.category])
                       )
            t.setDaemon(True)
            t.start()
            threads.append(t)

            # Actualizamos el progreso
            dialog.update(0, "Iniciada busqueda en %s [%s]..." % (
                newest_item.channelname,
                category[newest_item.category]
            ))
        # Modo normal
        else:
            # Lanzamos la búsqueda
            channel_search(newest_item, results, bloquea)

            # Actualizamos el progreso
            dialog.update(0, "Buscando en %s [%s]..." % (
                newest_item.channelname,
                category[newest_item.category]
            ))

    # Si estamos en modo multithread, esperamos a que terminen
    if multithread:
        running = [t for t in threads if t.isAlive()]

        while running:
            percent = (len(threads) - len(running)) * 100 / len(threads)
            completed = len(threads) - len(running)

            if len(running) > 5:
                dialog.update(percent, "Busqueda terminada en %d de %d canales..." % (completed, len(threads)))
            else:
                dialog.update(percent, "Buscando en %s" % (", ".join([t.getName() for t in running])))

            if dialog.iscanceled():
                break

            time.sleep(0.5)
            running = [t for t in threads if t.isAlive()]

    dialog.close()

    # Mostramos los resultados
    for result in results:
        if result['result']:
            itemlist.extend(result['result'])


    # Agrupar y ordenar resultados
    itemlist = group_and_sort(itemlist)

    return itemlist


def channel_search(item, results, bloquea):
    logger.trace()

    try:
        if item.use_proxy: bloquea.acquire()
        mod = moduletools.get_channel_module(item.channel)
        result = getattr(mod, item.action)(item)

    except Exception:
        result = []
        logger.error()

    finally:
        if item.use_proxy:
            bloquea.release()

    # Limitar el numero de resultados devueltos por cada canal
    max = settings.get_setting("max_result", __file__)
    if max:
        result = result[:int(max) * 10]

    results.append({'item': item, 'result': result})


def group_and_sort(itemlist):
    logger.trace()
    dict_result = {}

    itemlist = filter(lambda it: it.type in ["video", "movie", "tvshow", "season", "episode"], itemlist)
    if not itemlist:
        return itemlist

    group = settings.get_setting("group_result", __file__)
    sort = settings.get_setting("sort_result", __file__) if itemlist[0].category != 'episode' else False
    if group == 0:
        # No Agrupar
        if sort:
            itemlist.sort(key=lambda x: x.title)

        return itemlist

    elif group == 1:
        # Agrupar por canales
        if sort:
            sorted_list = sorted(itemlist, key=lambda x: (x.channel, x.title))
        else:
            sorted_list = sorted(itemlist, key=lambda x: x.channel)

        itemlist = []
        list_channels = []
        for it in sorted_list:
            if it.channel not in list_channels:
                list_channels.append(it.channel)
                itemlist.append(Item(label="%s:" % it.channelname,
                                     type='label',
                                     action='',
                                     thumb=it.thumb,
                                     icon=it.icon))
            itemlist.append(it.clone(group=True))

        return itemlist


    elif group == 2:
        # Agupar por titulo
        for i in itemlist:
            titulo = unicode(i.title, "utf8").lower().encode("utf8")
            if i.category == 'episode':
                titulo = "%sx%s %s" %(i.season, i.episode, unicode(i.label or i.tvshowtitle, "utf8").lower().encode("utf8"))

            if titulo not in dict_result:
                dict_result[titulo] = [i]
            else:
                dict_result[titulo].append(i)


    elif group == 3:
        # Agrupar por IMDB
        dialog = platformtools.dialog_progress_bg('Obteniendo información de medios')
        for ready, total in mediainfo.get_itemlist_info(itemlist):
            dialog.update(ready * 100 / total, 'Obteniendo información de medios', '%s de %s' % (ready, total))
        dialog.close()

        for i in itemlist:
            #TODO Esta pensado para usar TMDB, en el caso de otros scraper habra q estudiarlo

            id = i.tmdb_id if i.tmdb_id else i.label
            if i.category == 'episode':
                # En el caso de los episodios i.tmdb_id deberia ser el codigo del episodio y no el de la serie,
                # pero como no es asi creamos un nuevo codigo con el id de la serie la temporada y el episodio.
                id = "%s_%sx%s" % (id, i.season, i.episode)

            if id not in dict_result:
                dict_result[id] = [i]
            else:
                dict_result[id].append(i)


    # Agrupar resultados
    itemlist = []
    list_aux = dict_result.values()
    if sort:
        list_aux.sort(key=lambda x: x[0].title or x[0].label)

    for v in list_aux:
        if len(v) > 1:
            new_item = Item(
                action='ungroup',
                channel='newest',
                content_type='default',
                label_extra={"sublabel": " [+%s]", "color": "yellow", "value": "%s" % len(v)},
                lang=list(set(l for p in v for l in p.lang)),
                list_of_items=[p.tourl() for p in v]
            )

            for atributo in ['label', 'category', 'adult', 'type', 'poster',
                             'year', 'plot', 'thumb', 'fanart', 'icon', 'title',
                             'season', 'episode']:
                for p1 in v:
                    valor = p1.__dict__.get(atributo)
                    if valor:
                        new_item.__dict__[atributo] = valor

            itemlist.append(new_item)

        else:
            itemlist.append(v[0])


    return itemlist


def ungroup(item):
    logger.trace()

    # Recuperar los subitems de la lista y ordenamos por canal (podrian haber varios subitems del mismo canal)
    subitems = [Item().fromurl(it) for it in item.list_of_items]
    subitems.sort(key=lambda x: x.channel)

    # Recorremos la lista añadiendo las etiquetas de los canales
    list_channels = []
    itemlist = []
    for it in subitems:
        if it.channel not in list_channels:
            list_channels.append(it.channel)
            itemlist.append(it.clone(label= "%s:" % it.channelname, type='label', action='', poster=''))

        itemlist.append(it.clone(group=True))

    return itemlist