# -*- coding: utf-8 -*-
from core.libs import *
import random


def start():
    logger.trace()
    ret = True
    settings.check_directories()

    if not settings.get_setting('installation_id'):
        settings.set_setting('installation_id', "%032x" % (random.getrandbits(128)))

    if not settings.get_setting('first_run'):
        ret = platformtools.show_first_run()

    return ret


def run(item):
    logger.trace()
    itemlist = list()

    # Desactivar modo report si han pasado 600 segundos
    if settings.get_setting('debug') > 3 and time.time() > settings.get_setting('debug_time_Report')[0] + 600:
        settings.set_setting('debug', settings.get_setting('debug_time_Report')[1])
        logger.init_logger()

    # Contraseña para canales adultos
    if item.adult and item.action == 'mainlist' and settings.get_setting('adult_pin'):
        pin = platformtools.dialog_input('', 'Introduzca la contraseña para mostrar el canal', True)
        if not pin == settings.get_setting('adult_password'):
            platformtools.dialog_ok('MediaExplorer', 'La contraseña no es correcta')
            return

    # Dialogo introducir texto
    if item.query is True:
        from core import finder
        logger.debug('Abriendo dialogo')
        default = ""

        if settings.get_setting("last_search", finder.__file__):
            searches = settings.get_setting('saved_searches', finder.__file__) or []
            if searches:
                default = searches[0].get('query', '')

        item.query = platformtools.dialog_input(default)
        logger.debug('Texto obtenido: %s' % item.query)

        if not item.query:
            return

        if settings.get_setting("last_search", finder.__file__) and item.channel !='finder':
            finder.save_search(item.query, item.category)

    # Label sin accion
    if not (item.context_action or item.action):
        logger.info('El item no tiene accion, se omite')
        return

    # Importar canal
    if item.context_channel or item.channel:
        channel = moduletools.get_channel_module(item.context_channel or item.channel)
    else:
        channel = None

    # Acciones en el canal
    if hasattr(channel, item.context_action or item.action):
        try:
            logger.info('Ejecutando funcion en canal: %s' % item.context_channel or item.channel)
            itemlist = getattr(channel, item.context_action or item.action)(item)
            if settings.get_setting('debug') == 5: settings.set_setting('debug', 0)
        except Exception:
            logger.error()

            if settings.get_setting('debug') == 0:
                if platformtools.dialog_yesno(
                        'MediaExplorer',
                        'Se ha producido un error en el canal %s\n' % moduletools.get_module_name(channel.__file__),
                        '¿Quieres generar un reporte de este error?'):

                    settings.set_setting('debug', 5)
                    settings.set_setting('debug_time_Report', [time.time(), 0])

                    if os.path.isfile(os.path.join(sysinfo.data_path, 'report.log')):
                        os.remove(os.path.join(sysinfo.data_path, 'report.log'))

                    logger.init_logger('report.log')
                    run(item)

                    return None

            if settings.get_setting('debug') > 3:
                settings.set_setting('debug', settings.get_setting('debug_time_Report')[1])
                report()
                return None


    # Acciones genericas (en el launcher)
    else:
        if not item.action == 'play':
            logger.info('Ejecutando funcion en launcher')
            itemlist = getattr(sys.modules[__name__], item.context_action or item.action)(item)
            if itemlist is None:
                return


    # Representar resultado:
    
    # Si tenemos un listado de servidores ...
    # no venimos del item '..click aqui para mostrar todos' ...
    # no venimos de ejecutar el autoplay ...
    # y esta activa la funcion autoplay (en la configuracion o en el menu contextual) ...
    # ...entonces intentar reproducir un video.
    if item.content_type == 'servers' and \
            isinstance(itemlist, list) and \
            not item.nofilter and \
            not item.autoplay and \
            ((settings.get_setting('autoplay') and
            item.context_autoplay in ['', True]) or
             (item.context_autoplay)):

        if servertools.autoplay(itemlist, item) or item.context_autoplay:
            return

    # Funcion 'Play' reproduce un vídeo
    if item.action == 'play' and not item.context_action:

        # El canal tenia función play y ha devuelto algun resultado
        if itemlist:
            # El resultado es un item (se reproduce)
            if type(itemlist) == Item:
                platformtools.play(itemlist)

            # El resultado es un list con objetos Video(), se añaden las video_urls
            else:
                platformtools.play(item.clone(video_urls=itemlist))

        # El canal no tiene función play o esta no devuelve resultado alguna, se reproduce el item
        else:
            platformtools.play(item)

    # Resto de funciones cargan un listado.
    elif isinstance(itemlist, list):
        # Listado de temporadas:
        if item.content_type == 'seasons' and itemlist and len(itemlist) == 1 and itemlist[0].season == 1 and \
                settings.get_setting("hide_unique_season" , "platformcode/viewtools"):
                    run(itemlist[0])
                    return

        # Listado de servidores
        elif item.content_type == 'servers':
            filtered_itemlist = itemlist[:]

            # Filtrar servidores por idioma, calidad y tipo
            if not item.nofilter:
                # idiomas
                if settings.get_setting('lang_filter_server'):
                    disabled_langs = settings.get_setting('disabled_langs') or []
                    for i in range(len(filtered_itemlist)-1,-1,-1) :
                        x = filtered_itemlist[i]
                        if x.type == 'server':
                            if not x.lang or not x.lang.name:
                                if 'unk' in disabled_langs:
                                    del (filtered_itemlist[i])

                            elif x.lang.name in disabled_langs:
                                del (filtered_itemlist[i])


                # Calidades
                if settings.get_setting('quality_filter_server'):
                    disabled_qualities = settings.get_setting('disabled_qualities') or []
                    for i in range(len(filtered_itemlist)-1,-1,-1) :
                        x = filtered_itemlist[i]
                        if x.type == 'server':
                            if not x.quality or not x.quality.name:
                                if 'unk' in disabled_qualities:
                                    del (filtered_itemlist[i])

                            elif x.quality.name in disabled_qualities:
                                del (filtered_itemlist[i])


                # Por tipo de servidor (stream, download, torrent)
                hide = settings.get_setting('hide_servers_type', servertools.__file__)
                if hide:
                    hide = [lambda x: x.stream,
                            lambda x: x.server!="torrent",
                            lambda x: x.stream and x.server!="torrent"][hide -1]
                    filtered_itemlist = filter(hide, filtered_itemlist)

                # Opcion No Filtrar
                if filtered_itemlist != itemlist:
                    filtered_itemlist.insert(0, item.clone(
                        label='Hay %s servidores ocultos, click aqui para mostrar todos' % (
                            len(itemlist) - len(filtered_itemlist)
                        ),
                        nofilter=True,
                        type='highlight'
                    ))

            # Agrupar y ordenar por tipo de servidor (stream, download, torrent)
            sort = settings.get_setting('group_servers_type', servertools.__file__)
            if sort:
                if item.quality: del item.quality
                items_type_server=[[], [], [], []] # Comunes, streaming, download, torrent
                for i in filtered_itemlist:
                    if i.type != 'server':
                        items_type_server[0].append(i)

                    elif i.stream and i.server !='torrent':
                        if not items_type_server[1]:
                            items_type_server[1].append(item.clone(label="Ver en:", type='label'))
                        items_type_server[1].append(i.clone(group=True))

                    elif not i.stream:
                        if not items_type_server[2]:
                            items_type_server[2].append(item.clone(label="Descargar de:", type='label'))
                        items_type_server[2].append(i.clone(group=True))

                    elif i.stream and i.server =='torrent':
                        if not items_type_server[3]:
                            items_type_server[3].append(item.clone(label="Torrents:", type='label'))
                        items_type_server[3].append(i.clone(group=True))


                sort = [123, 231, 312, 213, 132, 321][sort -1]
                filtered_itemlist = items_type_server[0]
                filtered_itemlist.extend(servertools.sort_servers(items_type_server[sort / 100]))
                filtered_itemlist.extend(servertools.sort_servers(items_type_server[(sort % 100) / 10]))
                filtered_itemlist.extend(servertools.sort_servers(items_type_server[(sort % 100) % 10]))

            itemlist = filtered_itemlist


        # Filtro de canales por categoria
        if item.action == 'mainlist' and item.category != "all":
            filtered_itemlist = filter(
                lambda x: x.category in [item.category, 'all'],
                itemlist)
            itemlist = filtered_itemlist

        platformtools.render_items(itemlist, item)


def info(item):
    logger.trace()
    platformtools.media_info(item)


def set_no_viewed(item):
    logger.trace()
    from core import bbdd
    bbdd.media_viewed_del(item)
    platformtools.itemlist_refresh()


def report():
    logger.init_logger()
    try:
        path = os.path.join(sysinfo.data_path, 'report.log')
        report = open(path, 'r').read()
    except:
        platformtools.dialog_ok(
            'MediaExplorer : Error',
            'Se ha producido un error al generar el reporte.')
    else:
        line = ['']
        for l in path.split(os.sep):
            if len(line[-1]) + len(l) < 54:
                line[-1] += l + os.sep
            else:
                line.append(l + os.sep)

        str_path = '\n'.join(line)[:-1]

        try:
            from core import anonfile
            url = None
            response_id = anonfile.upload(path)
            if response_id:
                url = 'https://anonfile.com/%s' % response_id

            if url:
                logger.debug("Report subido a %s" % url)
                img = 'http://www.codigos-qr.com/qr/php/qr_img.php?d=%s&s=6&e=m' % url
                msg = 'El reporte se ha generado con éxito.\nPuedes encontrar una copia local en:\n'
                msg += str_path
                msg += "\n\nTambien se ha subido a '%s'\nPuedes abrirlo escaneando el codigo QR o " \
                       "compartir esta URL en el foro para que podamos ayudarte." % url
                platformtools.dialog_img_yesno(img, 'MediaExplorer : Reporte generado', msg, False)

            else:
                raise()

        except:
            platformtools.dialog_ok(
                'MediaExplorer : Reporte generado',
                'El reporte se ha generado con éxito. Puedes encontrarlo en:',
                path)


