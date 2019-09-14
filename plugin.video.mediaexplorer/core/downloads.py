# -*- coding: utf-8 -*-
from core.downloader import Downloader
from core.libs import *


def mainlist(item):
    logger.trace()
    itemlist = []

    downloads = settings.get_setting('downloads', __file__) or []

    # Lista de archivos
    for d in downloads:
        i = Item().fromjson(d['item'])

        if i.type == 'tvshow':
            progress = [e.get('download_progress', 0) for e in d['episodes']]
            status = [e.get('download_status', 0) for e in d['episodes']]
            if 3 in status:
                status = 3
            elif 2 in status:
                status = 2
            elif 1 in status and 0 in status:
                status = 2
            elif 1 in status:
                status = 1
            elif 0 in status:
                status = 0
            itemlist.append(item.clone(
                label=i.title,
                action='episodes',
                download_id=d['id'],
                download_channel=i.channel,
                download_progress=sum(progress) / len(progress),
                download_status=status,
                plot='',
                type='download'
            ))
        elif i.type == 'movie':
            itemlist.append(item.clone(
                title=i.title,
                action='menu',
                download_id=d['id'],
                download_channel=i.channel,
                download_progress=i.download_progress or 0,
                download_status=i.download_status or 0,
                plot='',
                type='download'
            ))
        elif i.type == 'video':
            itemlist.append(item.clone(
                title=i.title or i.label,
                action='menu',
                download_id=d['id'],
                download_channel=i.channel,
                download_progress=i.download_progress or 0,
                download_status=i.download_status or 0,
                plot='',
                type='download',
                server=True
            ))

    status = [i.download_status for i in itemlist]

    # Si hay alguno completado
    if 1 in status:
        itemlist.insert(0, item.clone(
            action='clean_ready',
            label='Eliminar descargas completadas',
            plot='Elimina las descargas completadas y las que tienen un error, no elimina los archivos descargados',
            type='highlight',
        ))

    # Si hay alguno con error
    if 3 in status:
        itemlist.insert(0, item.clone(
            action='restart_error',
            label='Reiniciar descargas con error',
            plot='Restaura las descargas con error, para poder volver a intentar descargar después',
            type='highlight',
        ))

    # Si hay alguno pendiente
    if 2 in status or 0 in status:
        itemlist.insert(0, item.clone(
            action='download_all',
            label='Descargar todo',
            plot='Inicia todas las descargas en el orden del listado',
            type='highlight',
        ))

    if len(itemlist):
        itemlist.insert(0, item.clone(
            action='clean_all',
            label='Eliminar todo',
            plot='Elimina todas las descargas tanto completadas como pendientes, no elimina los archivos descargados',
            type='highlight',
        ))

    if settings.get_setting("browse", __file__):
        itemlist.insert(0, item.clone(
            action='browser',
            label='Ver archivos descargados',
            url=settings.get_setting('download_path', __file__),
            type='highlight',
            plot='Desde aquí puedes ver y reproducir los archivos descargados'
        ))

    itemlist.insert(0, item.clone(
        action='config',
        label='Configuración descargas...',
        type='setting'
    ))

    return itemlist


def episodes(item):
    logger.trace()
    itemlist = []

    downloads = settings.get_setting('downloads', __file__)
    d = filter(lambda x: x['id'] == item.download_id, downloads)[0]

    for episode in d['episodes']:
        e = Item().fromjson(episode)
        itemlist.append(item.clone(
            label=e.title,
            season=e.season,
            episode=e.episode,
            download_progress=e.download_progress or 0,
            download_status=e.download_status or 0,
            download_index=d['episodes'].index(episode),
            action='menu',
            type='download_episode'
        ))

    return itemlist


def menu(item):
    logger.trace()

    options = [
        {
            'label': 'Descargar',
            'action': download,
            'visible': lambda x: x.download_status == 0
        },
        {
            'label': 'Descargar desde...',
            'action': lambda x: download(x, select=True),
            'visible': lambda x: x.download_status == 0 and not x.server
        },
        {
            'label': 'Continuar descarga',
            'action': lambda x: download(x, resume=True),
            'visible': lambda x: x.download_status == 2
        },
        {
            'label': 'Eliminar datos descargados',
            'action': remove_data,
            'visible': lambda x: x.download_status in (1, 2, 3)
        },
        {
            'label': 'Integrar en la biblioteca',
            'action': to_library,
            'visible': lambda x: x.download_status == 1
        },
        {
            'label': 'Reiniciar descarga',
            'action': lambda x: (update_status(
                {
                    'download_status': 0,
                    'download_progress': 0,
                    'download_url': ''
                },
                x.download_id,
                x.download_index), remove_data(x)
            ),
            'visible': lambda x: x.download_status in (1, 2, 3)
        },
        {
            'label': 'Eliminar de la lista',
            'action': delete,
            'visible': lambda x: True
        }

    ]

    options = filter(lambda x: x['visible'](item), options)
    index = platformtools.dialog_select('Descargas', [o['label'] for o in options])

    if index > -1:
        options[index]['action'](item)
        platformtools.itemlist_refresh()


def remove(item):
    logger.trace()
    filetools.remove(item.url)
    platformtools.itemlist_refresh()


def remove_data(item):
    logger.trace()

    downloads = settings.get_setting('downloads', __file__)
    index = downloads.index(filter(lambda x: x['id'] == item.download_id, downloads)[0])

    if type(item.download_index) == int:
        path = downloads[index]['episodes'][item.download_index]['download_path']
        filename = downloads[index]['episodes'][item.download_index]['download_filename']
        if filetools.isfile(filetools.join(path, filename)):
            filetools.remove(filetools.join(path, filename))
        if filetools.isfile(filetools.join(path, filename) + '.tmp'):
            filetools.remove(filetools.join(path, filename) + '.tmp')
    else:
        path = downloads[index]['item']['download_path']
        filename = downloads[index]['item']['download_filename']
        if filetools.isfile(filetools.join(path, filename)):
            filetools.remove(filetools.join(path, filename))
        if filetools.isfile(filetools.join(path, filename) + '.tmp'):
            filetools.remove(filetools.join(path, filename) + '.tmp')


def delete(item):
    logger.trace()
    downloads = settings.get_setting('downloads', __file__)
    downloads = filter(lambda x: not x['id'] == item.download_id, downloads)
    settings.set_setting('downloads', downloads, __file__)


def update_status(status, download_id, episode=None):
    logger.trace()

    downloads = settings.get_setting('downloads', __file__)
    index = downloads.index(filter(lambda x: x['id'] == download_id, downloads)[0])

    if type(episode) == int:
        downloads[index]['episodes'][episode].update(status)
    else:
        downloads[index]['item'].update(status)

    settings.set_setting('downloads', downloads, __file__)


def download(item, select=False, resume=False):
    logger.trace()
    result = dict()

    downloads = settings.get_setting('downloads', __file__)
    d = filter(lambda x: x['id'] == item.download_id, downloads)[0]

    channel = moduletools.get_channel_module(d['item']['channel'])

    channelname = moduletools.get_module_name(channel.__file__)

    dialog = platformtools.dialog_progress('Descargas', 'Obteniendo servidores en %s...' % channelname)

    # Episodios
    if type(item.download_index) == int:
        episode = Item().fromjson(d['episodes'][item.download_index])

        servers = filter(lambda x: x.type == 'server', getattr(channel, episode.action)(episode))

        path = '%s [%s]' % (episode.tvshowtitle or
                            d['item']['title'] or
                            d['item']['label'], episode.channel
                            )

        filename = '%dx%02d %s' % (
            episode.season,
            episode.episode,
            episode.title or episode.tvshowtitle
        )

    elif d['item']['type'] == 'video':
        video = Item().fromjson(d['item'])
        servers = [video]

        path = None
        filename = '%s [%s]' % (
            video.title or video.label,
            video.channel
        )

    else:
        video = Item().fromjson(d['item'])
        servers = filter(lambda x: x.type == 'server', getattr(channel, video.action)(video))

        path = None
        filename = '%s [%s]' % (
            video.title or video.label,
            video.channel
        )

    if not servers:
        result = {'download_status': 3}
        dialog.update(100, '¡No se han encontrado servidores!')

        time.sleep(1)
        dialog.close()
        if dialog.iscanceled():
            return {'download_status': 2}
    else:
        dialog.update(100, 'Encontrados %s servidores' % len(servers))

        time.sleep(1)

        if dialog.iscanceled():
            return {'download_status': 2}

        dialog.close()

        if select:
            from platformcode import viewtools
            s = platformtools.dialog_select(
                'Selecciona el servidor',
                [
                    viewtools.set_label_format(s) for s in servers
                ]
            )

            if s == -1:
                return

            server = servers[s]

            result = download_server(server, path, filename, resume)
            result['download_url'] = server.url

        else:
            if d['item'].get('download_url') and resume:

                server = [s for s in servers if s.url == d['item']['download_url']]

                if server:
                    result = download_server(server[0], path, filename, resume)
                    result['download_url'] = server[0].url

                else:
                    resume = False

            if not d['item'].get('download_url') or not resume:
                for server in servers:
                    result = download_server(server, path, filename, resume)
                    result['download_url'] = server.url

                    if result['download_status'] in [1, 2]:
                        break

    update_status(result, item.download_id, item.download_index)
    if result['download_status'] == 1:  # completado
        if settings.get_setting('library_add', __file__):
            to_library(item)

    return result


def download_server(item, path=None, filename=None, resume=False):
    logger.trace()
    result = dict()

    dialog = platformtools.dialog_progress('Descargas', 'Probando con: %s' % (item.servername or item.server))
    channel = moduletools.get_channel_module(item.channel)

    channelname = moduletools.get_module_name(channel.__file__)

    if hasattr(channel, "play"):
        dialog.update(
            50,
            "Probando con: %s" % (item.servername or item.server or channelname),
            "Conectando con %s..." % channelname
        )

        try:
            response = getattr(channel, "play")(item)
        except Exception:
            logger.error()
            dialog.close()
            return {'download_status': 3}

        if type(response) == Item:
            item = response

        elif type(response) == list:
            item.video_urls = response
            if not item.servername:
                item.servername = channelname

        else:
            dialog.close()
            return {'download_status': 3}

    dialog.close()

    if not item.video_urls:
        item.video_urls = servertools.resolve_video_urls(item)

    if type(item.video_urls) == str:
        logger.debug('El vídeo no esta disponible, respuesta del servidor: %s' % item.video_urls)
        return {'download_status': 3}

    elif not item.video_urls:
        logger.debug('No hay video_urls')
        return {'download_status': 3}

    else:
        for video_url in item.video_urls:
            result = download_url(video_url.url, item, path, filename, resume)

            if result["download_status"] in (1, 2):
                break

            # Error en la descarga, continuamos con la siguiente opcion
            if result["download_status"] == 3:
                continue

        return result


def download_url(url, item, path=None, filename=None, resume=False):
    logger.trace()

    if url.lower().endswith(".m3u8") or url.lower().startswith("rtmp") or item.server == 'torrent':
        logger.debug('Servidor o tipo de medio no soportado')
        return {"status": 3}

    download_path = settings.get_setting('download_path', __file__)

    if path:
        path = filetools.join(download_path, path)
    else:
        path = download_path

    if not filetools.isdir(path):
        filetools.makedirs(path)

    d = Downloader(
        url=url,
        path=filetools.validate_path(path),
        filename=filetools.validate_path(filename),
        resume=resume,
        max_connections=1 + settings.get_setting("max_connections", __file__),
        block_size=2 ** (17 + settings.get_setting("block_size", __file__)),
        part_size=2 ** (20 + settings.get_setting("part_size", __file__)),
        max_buffer=2 * settings.get_setting("max_buffer", __file__)
    )

    d.start_dialog("Descargas [%s]" % item.servername or item.server)

    result = {
        'download_size': d.size[0],
        'download_progress': d.progress,
        'download_filename': d.filename,
        'download_path': path
    }

    if d.state == d.states.error:
        logger.debug("Error al intentar descargar %s" % url)
        result['download_status'] = 3

    elif d.state == d.states.stopped:
        logger.debug("Descarga detenida")
        result['download_status'] = 2

    elif d.state == d.states.completed:
        logger.debug("Descargado correctamente")
        result['download_status'] = 1

    return result


def config(item):
    ret = platformtools.show_settings()
    platformtools.itemlist_refresh()
    return ret


def browser(item):
    logger.trace()
    itemlist = []

    for f in filetools.listdir(item.url):
        if filetools.isdir(filetools.join(item.url, f)):
            itemlist.append(item.clone(
                label=f,
                url=filetools.join(item.url, f),
                plot='',
                folder=True,
                type='item',
                icon='icon/folder.png'
            ))
        else:
            if f.endswith('.tmp'):
                continue
            itemlist.append(item.clone(
                title=f.split('[')[0].strip(),
                action='play',
                url=filetools.join(item.url, f),
                plot='',
                folder=False,
                type='item',
                server='local',
                icon='icon/video.png',
                poster='poster/video.png',
                thumb='thumb/video.png',
                description='',
                mediatype='video'
            ))

    return itemlist


def clean_all(item):
    logger.trace()
    settings.set_setting('downloads', [], __file__)
    platformtools.itemlist_refresh()


def clean_ready(item):
    logger.trace()
    downloads = settings.get_setting('downloads', __file__)
    downloads = filter(lambda x: x['item'].get('download_status', 0) != 1, downloads)
    settings.set_setting('downloads', downloads, __file__)
    platformtools.itemlist_refresh()


def restart_error(item):
    logger.trace()
    downloads = settings.get_setting('downloads', __file__)

    for d in downloads:
        if d['item'].get('download_status') == 3:
            update_status({'download_status': 0, 'download_progress': 0, 'download_url': ''}, d['id'])
        if d['episodes']:
            for episode in d['episodes']:
                if episode.get('download_status') == 3:
                    update_status({'download_status': 0, 'download_progress': 0, 'download_url': ''}, d['id'],
                                  d['episodes'].index(episode))

    platformtools.itemlist_refresh()


def download_all(item):
    logger.trace()
    downloads = settings.get_setting('downloads', __file__)

    res = {}
    for down in downloads:
        i = Item().fromjson(down['item'])
        if i.download_status not in (1, 3):
            if not down['episodes']:
                i.download_id = down['id']
                res = download(i, resume=True)
                platformtools.itemlist_refresh()
            else:
                for episode in down['episodes']:
                    e = Item().fromjson(episode)
                    index = down['episodes'].index(episode)
                    if e.download_status not in (1, 3):
                        e.download_index = index
                        e.download_id = down['id']
                        res = download(e, resume=True)
                        platformtools.itemlist_refresh()

                    if res.get('download_status') in (2,):
                        break
        if res.get('download_status') in (2,):
            break


def add_to_downloads(item):
    logger.trace()

    if item.type == 'tvshow':
        save_download_tvshow(item)

    elif item.type in ('movie', 'video'):
        save_download_movie(item)


def save_download_movie(item):
    logger.trace()

    dialog = platformtools.dialog_progress('Descargas', 'Añadiendo película a descargas...')
    d_id = add_to_file(item)
    dialog.close()

    if not platformtools.dialog_yesno('Descargas', '¿Comenzar a descargar ahora?'):
        platformtools.dialog_ok('Descargas',
                                'La película \'%s\' se ha añadido a la lista de descargas' % (item.title or item.label))
    else:
        download(item.clone(download_id=d_id))


def save_download_tvshow(item):
    logger.trace()

    dialog = platformtools.dialog_progress('Descargas', 'Añadiendo serie a descargas...')
    channel = moduletools.get_channel_module(item.channel)

    dialog.update(50, "Obteniendo temporadas...")
    seasons = filter(lambda x: x.type == 'season', getattr(channel, item.action)(item))

    dialog.update(100, "Obteniendo episodios...")
    epi = []
    for season in seasons:
        epi.extend(filter(lambda x: x.type == 'episode', getattr(channel, season.action)(season)))

    d_id = add_to_file(item, epi)
    dialog.close()

    if not platformtools.dialog_yesno('Descargas', '¿Comenzar a descargar ahora?'):
        platformtools.dialog_ok('Descargas', 'La serie \'%s\' se ha añadido a la lista de descargas' % item.title)
    else:
        download(item.clone(download_id=d_id))


def add_to_file(item, epi=None):
    logger.trace()
    import random

    downloads = settings.get_setting('downloads', __file__) or []
    d_id = "%016x" % (random.getrandbits(64))
    item.download_status = 0
    downloads.append({
        'id': d_id,
        'time': time.time(),
        'item': item.__dict__,
        'episodes': [e.__dict__ for e in epi] if epi is not None else []
    })

    settings.set_setting('downloads', downloads, __file__)
    return d_id


def to_library(item):
    from core import library
    downloads = settings.get_setting('downloads', __file__)
    d = filter(lambda x: x['id'] == item.download_id, downloads)[0]

    if type(item.download_index) == int:
        path = d['episodes'][item.download_index]['download_path']
        filename = d['episodes'][item.download_index]['download_filename']
        media = Item().fromjson(d['episodes'][item.download_index])
    else:
        path = d['item']['download_path']
        filename = d['item']['download_filename']
        media = Item().fromjson(d['item'])

    filepath = filetools.join(path, filename)

    if settings.get_setting('library_move', __file__):
        if type(item.download_index) == int:
            filename = [filetools.basename(path)] + [filename]
        else:
            filename = [filename]
        new_path = filetools.join(
            settings.get_setting('library_path', library.__file__),
            'downloads',
            *filename
        )

        if not filetools.isdir(filetools.dirname(new_path)):
            filetools.makedirs(filetools.dirname(new_path))

        filetools.move(filepath, new_path)

        filepath = filename

    if media.lang:
        del media.lang
    if media.quality:
        del media.quality
    library.add_to_library(media.clone(
        action='play',
        url=filepath,
        channel='downloads',
    ), silent=True)
