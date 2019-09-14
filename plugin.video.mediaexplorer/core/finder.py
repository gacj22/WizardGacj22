# -*- coding: utf-8 -*-
from core.libs import *
from core import mediainfo
from difflib import SequenceMatcher

category = {
    'movie': 'Películas',
    'tvshow': 'Series',
    'adult': 'Adultos',
    #'anime': 'Anime',
    #'child': 'Infantil'
}

content_type_dict = {
    "video": "default",
    "movie": "movies",
    "tvshow": "tvshows",
    "season": "seasons",
    "episode": "episodes"
}


def mainlist(item):
    logger.trace()
    itemlist = list()
    item.content_type = 'default'

    itemlist.append(item.clone(
        type='label',
        label="Búsquedas por título:"
    ))

    for c_id, name in sorted(category.items()):
        if c_id == 'adult' and not settings.get_setting('adult_mode'):
            continue
        itemlist.append(item.clone(
            action='search',
            label='Buscar por título en ' + name,
            search_categories={c_id:True},
            group=True,
            query=True,
            content_type=content_type_dict.get(c_id, "default"),
            description='Busca solo en %s' % name,
            type='search'
        ))

    itemlist.append(item.clone(
        action='search',
        label='Buscar por título en todas las categorias',
        group=True,
        query=True,
        description='Busca en todas las categorias',
        type='search'
    ))

    itemlist.append(item.clone(
        type='label',
        label="Otras búsquedas:"
    ))

    searches = settings.get_setting('saved_searches', __file__) or []
    if searches:
        itemlist.append(item.clone(
            action='load_saved_searches',
            label='Búsquedas previas',
            group=True,
            description='Repetir búsquedas realizadas anteriormente',
            type='search'
        ))

    itemlist.append(item.clone(
        action='list_genders',
        label='Buscar películas por género',
        group=True,
        category='movie',
        description='Buscar películas por género',
        type='search'
    ))

    itemlist.append(item.clone(
        action='mainlist',
        channel='rankings',
        label='Rankings Filmaffinity',
        group=True,
        category='movie',
        description='Buscar películas en los rankings de Filmaffinity',
        type='search'
    ))

    itemlist.append(item.clone(type='label',label=""))
    itemlist.append(item.clone(
        action='settings_menu',
        label='Ajustes buscador',
        description='Ajustes del buscador, activar/desactivar canales, borrar busquedas guardadas, etc...',
        type='setting'
    ))


    return itemlist


def settings_menu(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        type='label',
        action='',
        label="Canales incluidos en la búsqueda:"
    ))

    for c_id, name in sorted(category.items()):
        if c_id == 'adult' and not settings.get_setting('adult_mode'):
            continue

        itemlist.append(item.clone(
            action='channels',
            label=name,
            category=c_id,
            group=True,
            description='Elige los canales en los que quieres que se realice la búsqueda',
            type='item'
        ))

    itemlist.append(item.clone(
        action='clear_history',
        label='Borrar historial',
        description='Borra el historial de búsquedas realizadas',
        type='setting'
    ))

    itemlist.append(item.clone(
        action='config',
        label='Otros ajustes',
        description='Resto de ajustes del buscador',
        type='setting'
    ))
    return itemlist


def clear_history(item):
    logger.trace()
    settings.set_setting('saved_searches', [], __file__)
    platformtools.dialog_ok('Buscador', '¡Historial borrado con éxito!')


def config(item):
    return platformtools.show_settings()


def channels(item):
    logger.trace()
    controls = []

    channel_list = moduletools.get_channels()
    channel_list = filter(lambda c: c.get('search') and c['search'].get(item.category), channel_list)

    if not channel_list:
        platformtools.dialog_ok('Buscador', '¡No hay canales en los que buscar!')
        return

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


def list_genders(item):
    logger.trace()
    itemlist = list()

    # TODO esta lista puede cambiarse, pero no interesa que sea demasiado larga
    generos = {"adventure": "Aventuras", "action":"Acción", "animation":"Animación", "comedy":"Comedia",
               "drama":"Drama", "fantasia":"Fantasía", "children":"Infantil", "intrigue":"Intriga", "musical":"Musical",
               "romantic":"Romántica", "science-fiction":"Ciencia Ficción", "terror":"Terror", "war":"Guerra",
               "western":"Western"}

    # Obtenemos el listado con los canales con busqueda por el genero seleccionado
    # y no esten desactivados en ajustes/canales ni en los ajustes del buscador
    disabled_channels = settings.get_setting('disabled_channels', __file__) or {}
    disabled_channels = disabled_channels.get('movie', [])
    channel_list = moduletools.get_channels()
    channel_list = filter(
        lambda c: c.get('search', {}).get('movie_gender', {})
                  and not settings.get_setting("disabled", c['path']) and
                  c['id'] not in disabled_channels, channel_list)
    if not channel_list:
        platformtools.dialog_ok('Buscador', '¡No hay canales en los que buscar!')
        return

    # Obtenemos solo los generos incluidos en los canales seleccionados
    s = set ()
    for c in channel_list:
        s.update(c.get('search', {}).get('movie_gender', {}).get('url').keys())
        if len(s) == len(generos): break

    for k, name in generos.items():
        if k in s:
            itemlist.append(item.clone(
                action='search_gender',
                search_categories=k,
                label=name,
                group=True,
                content_type='movies',
                type='search'
            ))

    itemlist.sort(key=lambda i: i.label)
    itemlist.insert(0, item.clone(
        label='Buscar películas por género:',
        type='label'
    ))

    return itemlist


def search_gender(item):
    logger.trace()
    search_items = []

    # Obtenemos el listado con los canales con busqueda por el genero seleccionado
    # y no esten desactivados en ajustes/canales ni en los ajustes del buscador
    disabled_channels = settings.get_setting('disabled_channels', __file__) or {}
    disabled_channels = disabled_channels.get('movie', [])
    channel_list = moduletools.get_channels()
    channel_list = filter(lambda c: c.get('search',{}).get('movie_gender',{}).get('url',{}).get(item.search_categories)
                                    and not settings.get_setting("disabled", c['path']) and
                                    c['id'] not in disabled_channels, channel_list)
    if not channel_list:
        platformtools.dialog_ok('Buscador', '¡No hay canales en los que buscar!')
        return

    # Recorremos los canales
    for channel in channel_list:
        search_channel = channel['search']['movie_gender']
        url = search_channel['url'][item.search_categories]
        del search_channel['url']

        # Añadimos el item de búsqueda
        search_items.append(item.clone(
            channel=channel['id'],
            channelname=channel['name'],
            action=search_channel.pop('action_gender'),
            url=url,
            ** search_channel
        ))

    return search_multichannel(item, search_items)


def search(item, categories=None):
    logger.trace()
    search_items = []

    # Si no hay nada introducido no hay nada que buscar, salimos
    if not item.query:
        return

    # Las categorias donde buscar puede especificarse como argumento de la funcion
    # o incluirlo en el atributo item.search_categories
    if not categories and isinstance(item.search_categories,dict):
        categories = item.search_categories

    # Guardamos la búsqueda
    save_search(item.query, categories)

    # Obtenemos los ajustes
    disabled_channels = settings.get_setting('disabled_channels', __file__) or {}

    # Obtenemos el listado con los canales con busqueda
    # y no esten desactivados en ajustes/canales
    channel_list = moduletools.get_channels()
    channel_list = filter(lambda c: c.get('search') and
                            not settings.get_setting("disabled", c['path']),
                            channel_list)

    # Si estamos buscando por categorias, dejamos solo las categorias que estan en True
    if categories:
        categories = [k for k, v in categories.items() if v]
        # Si no hay seleccionada ningun categoria no habra canales donde buscar
        if not categories:
            channel_list = []

    # Recorremos los canales
    for channel in channel_list:
        # Recorremos los servicios de búsqueda del canal para crear un item con cada uno
        search_channel = channel.get('search', {})
        for k, v in search_channel.items():
            # Saltamos los que no coincidan con la categoria
            if categories and not k in categories:
                continue
            # Saltamos los de adultos si no estan activados
            if channel['adult'] and not settings.get_setting('adult_mode'):
                continue
            # Saltamos los que estén desactivados
            if  channel['id'] in disabled_channels.get(k, []):
                continue
            # Saltamos los servicios de búsqueda no incluidos en category
            if k not in category:
                continue

            # Añadimos el item de búsqueda
            search_items.append(Item(
                channel=channel['id'],
                channelname=channel['name'],
                query=item.query,
                poster='poster/%s.png' % channel['id'],
                icon='icon/%s.png' % channel['id'],
                thumb='thumb/%s.png' % channel['id'],
                category=k,
                use_proxy=settings.get_setting("use_proxy", channel['path']),
                adult=k == 'adult',
                **v
            ))

    if search_items:
        return search_multichannel(item, search_items)
    else:
        # Si no hay items de búsqueda mostramos el aviso
        platformtools.dialog_ok('Buscador', '¡No hay canales en los que buscar!')
        return


def search_multichannel(item, search_items):
    logger.trace()
    itemlist = []
    results = []
    threads = []
    bloquea = RLock()

    # Abrimos el progreso
    dialog = platformtools.dialog_progress("Buscando '%s'..." % (item.query or item.label),
                                           'Iniciando búsqueda en %s canales' % len(search_items))

    multithread = settings.get_setting('multithread', __file__)

    # Lanzamos las busquedas
    for k in search_items:
        # Modo multithread
        if multithread:
            # Lanzamos la búsqueda
            t = Thread(target=channel_search,
                       args=[k, results, bloquea],
                       name= ('%s [%s]' % (k.channelname, category[k.category])) if k.query else k.channelname
                       )
            t.setDaemon(True)
            t.start()
            threads.append(t)

            # Actualizamos el progreso
            if k.query:
                dialog.update(0, "Iniciada busqueda de '%s' en %s [%s]..." % (
                    k.query,
                    k.channelname,
                    category[k.category]
                ))
            else:
                dialog.update(0, "Iniciada busqueda de '%s' en %s..." % (
                    k.label,
                    k.channelname
                ))


        # Modo normal
        else:
            # Lanzamos la búsqueda
            channel_search(k, results, bloquea)

            # Actualizamos el progreso
            if k.query:
                dialog.update(0, "Buscando '%s' en %s [%s]..." % (
                    k.query,
                    k.channelname,
                    category[k.category]
                ))
            else:
                dialog.update(0, "Buscando '%s' en %s..." % (
                    k.label,
                    k.channelname
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

    # Unimos los resultados devueltos por cada canal
    map(itemlist.extend, results)

    if itemlist:
        dialog.update(80, "Ordenando resultados...")
        itemlist = group_and_sort(item, itemlist)

    dialog.close()
    return itemlist


def channel_search(item, results, bloquea):
    logger.trace()

    try:
        if item.description: del item.description
        if item.search_categories: del item.search_categories
        if item.use_proxy: bloquea.acquire()
        mod = moduletools.get_channel_module(item.channel)
        result = getattr(mod, item.action)(item)

    except Exception:
        result = []
        logger.error()

    finally:
        if item.use_proxy:
            bloquea.release()

    # Filtramos y limitamos el numero de resultados devueltos
    result = filter(lambda it: it.type in content_type_dict, result)
    max = 1 if item.channel == 'rankings' else settings.get_setting("max_result", __file__)
    if max:
        result = result[:int(max) * 10]

    results.append(result)



def save_search(query, categories):
    logger.trace()

    if isinstance(categories, dict):
        categories = [k for k,v in categories.items() if v]
    elif isinstance(categories, str) and categories in category.keys():
        categories = [categories]
    else:
        categories = []

    # No guardamos las busquedas de la categoria Adultos
    if 'adult' in categories:
        return

    q = {"query": query, "categories": categories}

    searches = settings.get_setting('saved_searches', __file__) or []
    max_searches = 10 * (settings.get_setting('saved_searches_limit', __file__) + 1)

    if q in searches:
        searches.remove(q)
    searches.insert(0, q)
    settings.set_setting('saved_searches', searches[:max_searches], __file__)


def load_saved_searches(item):
    logger.trace()
    itemlist = []
    l_it = []

    searches = settings.get_setting('saved_searches', __file__) or []

    for q in searches:
        query = label = q.get('query')
        categories = q.get('categories')

        d_cat = {}
        l_cat = []
        if categories:
            if 'adult' in categories and not settings.get_setting('adult_mode'):
                categories.remove('adult')
                if not categories: continue

            for k in categories:
                l_cat.append(category[k])
                d_cat[k] = True

            label = "%s (%s)" %(query, ", ".join(l_cat))

        if label not in l_it:
            itemlist.append(item.clone(
                label=label,
                action='search',
                query=query,
                group=True,
                search_categories=d_cat,
                content_type='default' if len(d_cat.keys()) != 1 else content_type_dict.get(d_cat.keys()[0], "default"),
                description=''
            ))
            l_it.append(label)

    return itemlist


def group_and_sort(item, itemlist):
    logger.trace()
    dict_result = {}
    sorted_list = []

    if item.channel == "rankings":
        group_result = 3
        sort_result = True
    else:
        group_result = settings.get_setting("group_result", __file__)
        sort_result = settings.get_setting("sort_result", __file__)

    is_multi_category = len(set([x.category for x in itemlist])) > 1

    if group_result == 0:
        # Solo por categorias
        if sort_result:
            if item.query:
                sorted_list = sorted(itemlist, key=lambda x: (category[x.category],
                                                              1 - SequenceMatcher(None, x.title, x.query).ratio()))
            else:
                sorted_list = sorted(itemlist, key=lambda x: (category[x.category],x.title))
        else:
            sorted_list = sorted(itemlist, key=lambda x: category[x.category])


    elif group_result == 1 or itemlist[0].category == 'adult':
        # Por canales y por categorias
        if sort_result:
            if item.query:
                itemlist.sort(key=lambda x: (x.channel, category[x.category],
                                             1 - SequenceMatcher(None, x.title, x.query).ratio()))
            else:
                itemlist.sort(key=lambda x: (x.channel, category[x.category],x.title))
        else:
            itemlist.sort(key=lambda x: (x.channel, category[x.category]))

        list_channels = []
        list_category = []
        for it in itemlist:
            if it.channel not in list_channels:
                list_channels.append(it.channel)
                sorted_list.append(Item(label="%s:" % it.channelname,
                                     type='label',
                                     action='',
                                     thumb=it.thumb,
                                     icon=it.icon))
                list_category = []

            if is_multi_category and it.category not in list_category:
                list_category.append(it.category)
                sorted_list.append(Item(label="%s:" % category[it.category],
                                     type='label',
                                     action='',
                                     group=True,
                                     thumb=it.thumb,
                                     icon=it.icon))

            sorted_list.append(it.clone(group=True))

        return sorted_list

    elif group_result == 2:
        # Por categorias y por el titulo
        for i in itemlist:
            titulo = unicode(i.title, "utf8").lower().encode("utf8")

            if titulo not in dict_result:
                dict_result[titulo] = [i]
            else:
                dict_result[titulo].append(i)


    elif group_result == 3:
        # Por categorias y por el codigo IMDB
        dialog = platformtools.dialog_progress_bg('Obteniendo información de medios')
        for ready, total in mediainfo.get_itemlist_info(itemlist):
            dialog.update(ready * 100 / total, 'Obteniendo información de medios', '%s de %s' % (ready, total))
        dialog.close()

        for i in itemlist:
            #TODO Esta pensado para usar TMDB, en el caso de otros scraper habra q estudiarlo
            id = i.tmdb_id if i.tmdb_id else (i.label or i.title or i.tvshowtitle)
            if id not in dict_result:
                dict_result[id] = [i]
            else:
                dict_result[id].append(i)


    if group_result >= 2:
        # Agrupar resultados
        sorted_list = []
        list_aux = dict_result.values()

        if sort_result:
            if item.query:
                list_aux.sort(key=lambda x: (category[x[0].category],
                                             1 - SequenceMatcher(None, x[0].title, x[0].query).ratio()))
            else:
                list_aux.sort(key=lambda x: (category[x[0].category], x[0].title))
        else:
            list_aux.sort(key=lambda x: category[x[0].category])

        for v in list_aux:
            if len(v) > 1:
                new_item = Item(
                    action='ungroup',
                    channel='finder',
                    label_extra={"sublabel": " [+%s]", "color": "yellow", "value": "%s" % len(v)},
                    lang=dict((l.name, l) for p in v for l in p.lang).values(),
                    list_of_items=[p.tourl() for p in v]
                )

                for atributo in ['label', 'category', 'adult', 'type', 'poster',
                                 'year', 'plot', 'fanart', 'title',
                                 'season', 'episode', 'tmdb_id']: #, 'thumb', 'icon'
                    for p1 in v:
                        valor = p1.__dict__.get(atributo)
                        if valor:
                            new_item.__dict__[atributo] = valor

                new_item.content_type = content_type_dict.get(new_item.type, "default")
                sorted_list.append(new_item)

            else:
                sorted_list.append(v[0])


    # For group_result 0, 2 y 3
    if is_multi_category:
        itemlist = []
        list_category = []
        for it in sorted_list:
            if it.category not in list_category:
                list_category.append(it.category)
                itemlist.append(Item(label="%s:" % category[it.category],
                                     type='label',
                                     action='',
                                     thumb='thumb/search.png',
                                     icon='icon/search.png',
                                     poster='poster/search.png',))

            itemlist.append(it.clone(group=True))

    else:
        itemlist = sorted_list

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
            itemlist.append(it.clone(label= "%s:" % it.channelname, type='label', poster=''))

        if it.category == 'tvshow' and not it.title:
            it.title = it.tvshowtitle

        itemlist.append(it.clone(group=True))

    return itemlist
