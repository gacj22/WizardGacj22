# -*- coding: utf-8 -*-
from core.libs import *


def config(item):
    return platformtools.show_settings(item=item)


def mainlist(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        action='movies',
        type='item',
        label='Películas',
        content_type='movies',
        poster='poster/movie.png',
        thumb='thumb/movie.png',
        icon='icon/movie.png',
        description='Contiene las peliculas guardadas en tu biblioteca',
        path=filetools.join(
            settings.get_setting('library_path', __file__),
            settings.get_setting('library_movies_folder', __file__)
        )
    ))

    itemlist.append(item.clone(
        action='tvshows',
        type='item',
        label='Series',
        label_extra={'sublabel': ' (%s)', 'value': get_new_items()},
        content_type='tvshows',
        poster='poster/tvshow.png',
        thumb='thumb/tvshow.png',
        icon='icon/tvshow.png',
        description='Contiene las series guardadas en tu biblioteca',
        path=filetools.join(
            settings.get_setting('library_path', __file__),
            settings.get_setting('library_tvshows_folder', __file__)
        )
    ))

    itemlist.append(item.clone(
        action='check_updates',
        label='Buscar nuevos episodios ahora',
        group=True,
        type='item'
    ))

    itemlist.append(item.clone(
        action='videos',
        type='item',
        label='Vídeos',
        content_type='videos',
        poster='poster/video.png',
        thumb='thumb/video.png',
        icon='icon/video.png',
        description='Contiene los vídeos guardados en tu biblioteca',
        path=filetools.join(
            settings.get_setting('library_path', __file__),
            settings.get_setting('library_videos_folder', __file__)
        )
    ))

    # Integrar Biblioteca con Kodi
    if sysinfo.platform_name == 'kodi':
        from platformcode import library_tools
        library_path = settings.get_setting('library_path', __file__)
        movies_path = filetools.join(library_path, settings.get_setting('library_movies_folder', __file__))
        tvshows_path = filetools.join(library_path, settings.get_setting('library_tvshows_folder', __file__))
        sources = library_tools.get_video_sources()
        if not (filetools.exists(movies_path) and filetools.exists(tvshows_path) and
                movies_path in sources and tvshows_path in sources):
            itemlist.append(item.clone(label='', action=''))
            itemlist.append(item.clone(
                action='integrate',
                label='Integrar Biblioteca con kodi',
                type='highlight'
            ))

    return itemlist


def integrate(item):
    logger.trace()
    from platformcode import library_tools
    if library_tools.integrate():
        platformtools.dialog_notification("MediaExplorer",
                                          "Biblioteca de kodi configurada correctamente. Reiniciar Kodi ahora.",
                                          t=7000)


def videos(item):
    logger.trace()
    itemlist = list()

    if not filetools.isdir(item.path):
        return itemlist

    context = [{'label': 'Quitar de la biblioteca', 'action': 'delete', 'channel': 'library'}]

    for video in filetools.listdir(item.path):
        video_info = jsontools.load_json(
            filetools.file_open(filetools.join(item.path, video, 'info.json'), 'rb').read()
        )

        itemlist.append(Item(
            action='findvideos',
            channel='library',
            path=filetools.join(item.path, video),
            context=context,
            content_type='servers',
            **video_info
        ))

    return itemlist


def movies(item):
    logger.trace()
    itemlist = []

    if not filetools.isdir(item.path):
        return itemlist

    context = [{'label': 'Quitar de la biblioteca', 'action': 'delete'}]

    for movie in filetools.listdir(item.path):
        movie_info = jsontools.load_json(
            filetools.file_open(filetools.join(item.path, movie, 'info.json'), 'rb').read()
        )

        itemlist.append(Item(
            action='findvideos',
            channel='library',
            path=filetools.join(item.path, movie),
            context=context,
            content_type='servers',
            **movie_info

        ))

    return itemlist


def tvshows(item):
    logger.trace()
    itemlist = list()

    if not filetools.isdir(item.path):
        return itemlist

    context = [{'label': 'Quitar de la biblioteca', 'action': 'delete'}]

    for tvshow in filetools.listdir(item.path):
        tvshow_info = jsontools.load_json(
            filetools.file_open(
                filetools.join(item.path, tvshow, 'tvshow.json'), 'rb').read()
        )

        itemlist.append(Item(
            action='seasons',
            label_extra={'sublabel': ' (%s)', 'value': get_new_items(tvshow_info['code'])},
            content_type='seasons',
            channel='library',
            path=filetools.join(item.path, tvshow),
            context=context,
            **tvshow_info
        ))

    return itemlist


def seasons(item):
    logger.trace()
    itemlist = list()

    remove_new_items(item.code)

    season_list = set([f for f in filetools.listdir(item.path) if
                       filetools.isdir(filetools.join(item.path, f))])

    for season in sorted(season_list):
        season_info = jsontools.load_json(
            filetools.file_open(filetools.join(item.path, season, 'info.json'), 'rb').read()
        )

        itemlist.append(Item(
            action='episodes',
            channel='library',
            content_type='episodes',
            path=filetools.join(item.path, season),
            **season_info
        ))

    return itemlist


def episodes(item):
    logger.trace()
    itemlist = list()

    episode_list = [f for f in filetools.listdir(item.path) if
                    filetools.isdir(filetools.join(item.path, f))]

    for episode in sorted(episode_list, key=int):
        episode_info = jsontools.load_json(
            filetools.file_open(filetools.join(item.path, episode, 'info.json'), 'rb').read()
        )

        itemlist.append(item.clone(
            action='findvideos',
            channel='library',
            content_type='servers',
            path=filetools.join(item.path, episode),
            **episode_info
        ))

    return itemlist


def findvideos(item):
    logger.trace()
    itemlist = list()

    movie_info = jsontools.load_json(
        filetools.file_open(filetools.join(item.path, 'info.json'), 'rb').read()
    )
    item.__dict__.update(movie_info)
    dialog = platformtools.dialog_progress_bg('Buscando servidores...')

    sources = filter(
        lambda x: x.endswith('.json') and not x == 'info.json',
        filetools.listdir(item.path)
    )

    for source in sources:
        i = Item().fromjson(
            filetools.file_open(filetools.join(item.path, source), 'rb').read()
        )

        i.__dict__.update(movie_info)

        if i.channel == 'downloads':
            if type(i.url) == list:
                # Archivo en biblioteca
                url = filetools.join(settings.get_setting('library_path', __file__), 'downloads', *i.url)
            else:
                # Archivo en otra ruta
                url = i.url

            itemlist.insert(0, i.clone(
                channel='',
                type='server',
                server='local',
                servername='Local',
                label_extra={"sublabel": " (%s)", "color": "color2", "value": filetools.basename(url)},
                url=url
            ))
        elif i.action == 'play':
            channel = moduletools.get_channel_module(i.channel)
            channelname = moduletools.get_module_name(channel.__file__)

            itemlist.append(i.clone(label=channelname))
        else:
            channel = moduletools.get_channel_module(i.channel)

            channelname = moduletools.get_module_name(channel.__file__)

            dialog.update(
                (sources.index(source) + 1) * 100 / len(sources),
                'Buscando servidores...',
                '[%s/%s] - %s' % (sources.index(source) + 1, len(sources), channelname)
            )

            results = filter(lambda x: x.type == 'server', getattr(channel, i.action)(i))

            itemlist.extend(results)

    dialog.close()

    return itemlist


def add_to_library(item, silent=False):
    from core import mediainfo
    logger.trace()

    new_items = 0

    library_path = settings.get_setting('library_path', __file__)
    item = item.clone()
    if item.context_action:
        del item.context_action
    if item.context_channel:
        del item.context_channel

    if item.type == 'video':
        if not silent:
            dialog = platformtools.dialog_progress('Biblioteca', 'Añadiendo Vídeo')

        # Nombres de las rutas
        folder_name = filetools.validate_path(
            filetools.join(
                settings.get_setting('library_videos_folder', __file__),
                '%s [%s]' % (item.title or item.label, item.channel)
            )
        )
        path_strm = filetools.validate_path(
            filetools.join(library_path, folder_name, '%s.strm' % (item.title or item.label)))
        path_json = filetools.join(library_path, folder_name, 'info.json')
        path_media = filetools.join(library_path, folder_name, '%s.json' % item.channel)

        # Creamos los directorios (si no existen)
        filetools.makedirs(filetools.join(library_path, folder_name))

        if not filetools.exists(path_strm):
            new_items += 1

        # Guardamos los archivos
        filetools.file_open(path_strm, 'wb').write(
            'plugin://plugin.video.mediaexplorer?%s' % Item(
                action='findvideos',
                channel='library',
                path=folder_name,
                type='video',
                strm=True
            ).tourl()
        )
        filetools.file_open(path_media, 'wb').write(item.tojson())
        filetools.file_open(path_json, 'wb').write(Item(
            fanart=item.fanart,
            poster=item.poster,
            thumb=item.thumb,
            icon=item.icon,
            mediatype=item.mediatype,
            title=item.title,
            type=item.type,
            adult=item.adult,
            plot=item.plot
        ).tojson())
        if not silent:
            dialog.close()
            platformtools.dialog_ok(
                'Biblioteca',
                'Se ha añadido la película \'%s\' a la biblioteca' % (item.title or item.label)
            )

    if item.type == 'movie':
        if not silent:
            dialog = platformtools.dialog_progress('Biblioteca', 'Añadiendo Pelicula')
            dialog.update(0, 'Obteniendo información de la película...')

        # Obtenemos la info
        data = Item(title=item.title, year=item.year, type='movie')
        mediainfo.get_movie_info(data, ask=True)

        # Si no hay datos salimos
        if not data.code:
            return
            # TODO: ¿Introducirla manualmente?

        # Nombres de las rutas
        folder_name = filetools.validate_path(
            filetools.join(
                settings.get_setting('library_movies_folder', __file__),
                '%s [%s]' % (data.title, data.code)
            )
        )
        path_strm = filetools.validate_path(filetools.join(library_path, folder_name, '%s.strm' % data.title))
        path_json = filetools.join(library_path, folder_name, 'info.json')
        path_nfo = filetools.validate_path(filetools.join(library_path, folder_name, '%s.nfo' % data.title))
        path_media = filetools.join(library_path, folder_name, '%s.json' % item.channel)

        # Creamos los directorios (si no existen)
        filetools.makedirs(filetools.join(library_path, folder_name))

        if not filetools.exists(path_strm):
            new_items += 1

        # Guardamos los archivos
        filetools.file_open(path_strm, 'wb').write(
            'plugin://plugin.video.mediaexplorer?%s' % Item(
                action='findvideos',
                channel='library',
                path=folder_name,
                type='movie',
                strm=True
            ).tourl()
        )
        filetools.file_open(path_nfo, 'wb').write('https://www.themoviedb.org/movie/%s' % data.tmdb_id)
        filetools.file_open(path_media, 'wb').write(item.tojson())
        filetools.file_open(path_json, 'wb').write(data.tojson())

        if not silent:
            dialog.close()
            platformtools.dialog_ok('Biblioteca', 'Se ha añadido la película \'%s\' a la biblioteca' % data.title)
        if sysinfo.platform_name == 'kodi':
            from platformcode import library_tools
            library_tools.update(settings.get_setting('library_path', __file__))

    if item.type == 'tvshow':
        if not silent:
            dialog = platformtools.dialog_progress('Biblioteca', 'Añadiendo Serie')
            dialog.update(0, 'Obteniendo información de la serie...')

        # Obtenemos la info de la serie
        data = Item(title=item.title, year=item.year, type='tvshow')
        mediainfo.get_tvshow_info(data, ask=True)

        # Si no hay datos salimos
        if not data.code:
            return
            # TODO: ¿Introducirla manualmente?

        # Nombres de las rutas para la serie
        folder_name = filetools.validate_path(
            filetools.join(
                settings.get_setting('library_tvshows_folder', __file__),
                '%s [%s]' % (data.title, data.code)
            )
        )
        path_json = filetools.join(library_path, folder_name, 'tvshow.json')
        path_sources = filetools.join(library_path, folder_name, 'sources.json')
        path_nfo = filetools.join(library_path, folder_name, 'tvshow.nfo')

        # Creamos los directorios (si no existen)
        filetools.makedirs(filetools.join(library_path, folder_name))

        # Guardamos los archivos de la serie
        filetools.file_open(path_nfo, 'wb').write('https://www.themoviedb.org/tv/%s' % data.tmdb_id)
        filetools.file_open(path_json, 'wb').write(data.tojson())

        if filetools.exists(path_sources):
            sources = jsontools.load_json(filetools.file_open(path_sources).read())
        else:
            sources = []

        sources = filter(lambda src: not src['channel'] == item.channel, sources)
        sources.append(item.__dict__)

        filetools.file_open(path_sources, 'wb').write(jsontools.dump_json(sources))

        if not silent:
            dialog.update(0, 'Obteniendo temporadas...')

        # Obtenemos las temporadas
        channelmodule = moduletools.get_channel_module(item.channel)
        season_list = filter(lambda y: y.type == 'season', getattr(channelmodule, item.action)(item))

        datalist = [data.clone(type='season', season=s.season) for s in season_list]

        datalist = filter(
            lambda z: not filetools.isfile(filetools.join(library_path, folder_name, '%d' % z.season, 'info.json')),
            datalist
        )
        if datalist:
            for ready, total in mediainfo.get_itemlist_info(datalist):
                if not silent:
                    dialog.update(ready * 100 / total, 'Obteniendo información de temporadas...',
                                  '%s de %s' % (ready, total))

        datalist = dict([(x.season, x) for x in datalist])

        for x in range(len(season_list)):
            season = season_list[x]

            # Nombres de las rutas para el episodio
            season_name = filetools.join(folder_name, '%d' % season.season)
            path_json = filetools.join(library_path, season_name, 'info.json')

            filetools.makedirs(filetools.join(library_path, season_name))

            if not filetools.isfile(path_json):
                season_data = datalist.get(season.season)
                filetools.file_open(path_json, 'wb').write(season_data.tojson())

        if not silent:
            dialog.update(0, 'Obteniendo episodios...')

        episode_list = list()

        for season in season_list:
            # Obtenemos los episodios
            episode_list.extend(filter(lambda w: w.type == 'episode', getattr(channelmodule, season.action)(season)))
            if not silent:
                dialog.update((season_list.index(season) + 1) * 100 / len(season_list), 'Obteniendo episodios...')

        datalist = [
            data.clone(
                type='episode',
                episode=e.episode,
                season=e.season,
                tvshowtitle=data.title
            )
            for e in episode_list
        ]

        datalist = filter(
            lambda v: not filetools.isfile(
                filetools.join(library_path, folder_name, '%d' % v.season, '%d' % v.episode, 'info.json')
            ),
            datalist
        )

        if datalist:
            for ready, total in mediainfo.get_itemlist_info(datalist):
                if not silent:
                    dialog.update(
                        ready * 100 / total,
                        'Obteniendo información de episodios...',
                        '%s de %s' % (ready, total)
                    )

        datalist = dict([('%dx%02d' % (x.season, x.episode), x) for x in datalist])

        for x in range(len(episode_list)):
            episode = episode_list[x]

            # Nombres de las rutas para el episodio
            episode_name = filetools.join(folder_name, '%d' % episode.season, '%d' % episode.episode)
            path_strm = filetools.join(library_path, episode_name, '%dx%02d.strm' % (episode.season, episode.episode))
            path_json = filetools.join(library_path, episode_name, 'info.json')
            path_media = filetools.join(library_path, episode_name, '%s.json' % item.channel)

            if not filetools.exists(path_strm):
                new_items += 1

            if not filetools.isfile(path_json):
                episode_data = datalist.get('%dx%02d' % (episode.season, episode.episode))

                # Creamos los directios (si no existen)
                filetools.makedirs(filetools.join(library_path, episode_name))
                if not silent:
                    dialog.update(
                        (episode_list.index(episode) + 1) * 100 / len(episode_list),
                        'Añadiendo episodio \'%dx%02d: %s\'...' % (
                            episode_data.season,
                            episode_data.episode,
                            episode_data.title
                        )
                    )

                # Guardamos los archivos del episodio
                filetools.file_open(path_strm, 'wb').write(
                    'plugin://plugin.video.mediaexplorer?%s' % Item(
                        action='findvideos',
                        channel='library',
                        path=episode_name,
                        type='episode',
                        strm=True
                    ).tourl()
                )
                filetools.file_open(path_nfo, 'wb').write('https://www.themoviedb.org/tv/%s' % episode_data.tmdb_id)
                filetools.file_open(path_json, 'wb').write(episode_data.tojson())
                filetools.file_open(path_media, 'wb').write(episode.tojson())

            else:
                episode_data = Item().fromjson(filetools.file_open(path_json, 'rb').read())
                if not silent:
                    dialog.update(
                        (episode_list.index(episode) + 1) * 100 / len(episode_list),
                        'Añadiendo episodio \'%dx%02d: %s\'...' % (
                            episode_data.season,
                            episode_data.episode,
                            episode_data.title
                        )
                    )
                filetools.file_open(path_media, 'wb').write(episode.tojson())

        if not silent:
            dialog.close()
            platformtools.dialog_ok('Biblioteca', 'Se ha añadido la serie \'%s\' a la biblioteca' % data.title)
        if sysinfo.platform_name == 'kodi':
            from platformcode import library_tools
            library_tools.update(settings.get_setting('library_path', __file__))

    if item.type == 'episode':
        if not silent:
            dialog = platformtools.dialog_progress('Biblioteca', 'Añadiendo episodio')
            dialog.update(0, 'Obteneiendo información de la serie...')

        # Obtenemos la info de la serie
        data = Item(title=item.tvshowtitle, year=item.year, type='tvshow')
        mediainfo.get_tvshow_info(data, ask=True)

        # Si no hay datos salimos
        if not data.code:
            return
            # TODO: ¿Introducirla manualmente?

        # Nombres de las rutas para la serie
        folder_name = filetools.validate_path(
            filetools.join(
                settings.get_setting('library_tvshows_folder', __file__),
                '%s [%s]' % (data.title, data.code)
            )
        )
        path_json = filetools.join(library_path, folder_name, 'tvshow.json')
        path_sources = filetools.join(library_path, folder_name, 'sources.json')
        path_nfo = filetools.join(library_path, folder_name, 'tvshow.nfo')

        # Creamos los directorios (si no existen)
        filetools.makedirs(filetools.join(library_path, folder_name))

        # Guardamos los archivos de la serie
        filetools.file_open(path_nfo, 'wb').write('https://www.themoviedb.org/tv/%s' % data.tmdb_id)
        filetools.file_open(path_json, 'wb').write(data.tojson())

        if filetools.exists(path_sources):
            sources = jsontools.load_json(filetools.file_open(path_sources).read())
        else:
            sources = []

        sources = filter(lambda src: not src['channel'] == item.channel, sources)
        sources.append(item.__dict__)

        filetools.file_open(path_sources, 'wb').write(jsontools.dump_json(sources))

        season = data.clone(type='season', season=item.season)
        mediainfo.get_season_info(season)

        # Nombres de las rutas para la temporada
        season_name = filetools.join(folder_name, '%d' % season.season)
        path_json = filetools.join(library_path, season_name, 'info.json')

        filetools.makedirs(filetools.join(library_path, season_name))

        if not filetools.isfile(path_json):
            filetools.file_open(path_json, 'wb').write(season.tojson())

        episode = data.clone(type='episode', episode=item.episode, season=item.season, tvshowtitle=data.title)
        mediainfo.get_episode_info(episode)

        # Nombres de las rutas para el episodio
        episode_name = filetools.join(folder_name, '%d' % episode.season, '%d' % episode.episode)
        path_strm = filetools.join(library_path, episode_name,
                                   '%dx%02d.strm' % (episode.season, episode.episode))
        path_json = filetools.join(library_path, episode_name, 'info.json')
        path_media = filetools.join(library_path, episode_name, '%s.json' % item.channel)

        if not filetools.exists(path_strm):
            new_items += 1

        if not filetools.isfile(path_json):

            # Creamos los directios (si no existen)
            filetools.makedirs(filetools.join(library_path, episode_name))

            # Guardamos los archivos del episodio
            filetools.file_open(path_strm, 'wb').write(
                'plugin://plugin.video.mediaexplorer?%s' % Item(
                    action='findvideos',
                    channel='library',
                    path=episode_name,
                    type='episode',
                    strm=True
                ).tourl()
            )
            filetools.file_open(path_nfo, 'wb').write(
                'https://www.themoviedb.org/tvshow/%s' % episode.tmdb_id)
            filetools.file_open(path_json, 'wb').write(episode.tojson())
            filetools.file_open(path_media, 'wb').write(item.tojson())

        else:
            filetools.file_open(path_media, 'wb').write(item.tojson())

        if not silent:
            dialog.close()
            platformtools.dialog_ok('Biblioteca', 'Se ha añadido el episodo \'%s\' a la biblioteca' % item.title)
        if sysinfo.platform_name == 'kodi':
            from platformcode import library_tools
            library_tools.update(settings.get_setting('library_path', __file__))

    return new_items


def delete(item):
    logger.trace()

    if platformtools.dialog_yesno(
            'Biblioteca',
            'Estas seguro que quieres eliminar de la biblioteca',
            '\'%s\'' % item.title
    ):
        filetools.rmdirtree(item.path)

    platformtools.itemlist_refresh()


def check_updates(item=None):
    logger.trace()

    new_items = {}

    path = filetools.join(
        settings.get_setting('library_path', __file__),
        settings.get_setting('library_tvshows_folder', __file__)
    )

    if not filetools.isdir(path):
        return

    dialog = platformtools.dialog_progress_bg('Actualizando biblioteca', '')

    tvshow_list = filetools.listdir(path)
    tvshow_list = filter(lambda t: filetools.isdir(filetools.join(path, t)), tvshow_list)

    for tvshow in tvshow_list:

        sources = jsontools.load_json(filetools.file_open(filetools.join(path, tvshow, 'sources.json')).read())
        data = jsontools.load_json(filetools.file_open(filetools.join(path, tvshow, 'tvshow.json')).read())
        dialog.update(tvshow_list.index(tvshow) * 100 / len(tvshow_list), 'Actualizando biblioteca', data['title'])
        new_items[data['code']] = 0

        for source in sources:
            item = Item(**source)
            logger.debug(item)
            item.__dict__.update(data)
            channel = moduletools.get_channel_module(item.channel)
            channelname = moduletools.get_module_name(channel.__file__)

            dialog.update(tvshow_list.index(tvshow) * 100 / len(tvshow_list), data['title'],
                          '[%d/%d]: %s' % (sources.index(source) + 1, len(sources), channelname))
            new_items[data['code']] += add_to_library(item, silent=True)


    add_new_items(new_items)

    dialog.close()
    if sysinfo.platform_name == 'kodi':
        from platformcode import library_tools
        library_tools.update(settings.get_setting('library_path', __file__))


def get_new_items(code=None):
    new_items = settings.get_setting('new_items', __file__) or {}
    if not code:
        return sum(new_items.values()) or False
    else:
        return new_items.get(code, 0) or False


def add_new_items(dct):
    new_items = settings.get_setting('new_items', __file__) or {}
    for code in dct:
        if code in new_items:
            new_items[code] += dct[code]
        else:
            new_items[code] = dct[code]
    settings.set_setting('new_items',new_items, __file__)


def remove_new_items(code):
    new_items = settings.get_setting('new_items', __file__) or {}

    if code in new_items:
        del new_items[code]

    settings.set_setting('new_items',new_items, __file__)
