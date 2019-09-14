# -*- coding: utf-8 -*-
from core.libs import *
import inspect


def get_servers_from_id(itemlist, fnc=None, sort=True):
    """
    Busca en un listado de items el servidor para cada uno, cuando la url no es valida
    basandose en el server id pasado por el canal
    :param itemlist: listado de servidores
    :param fnc: funcion encargada de devolver el label para cada item una vez asignado el servidor (obsoleto)
    :param sort: Ordena los servidores segun los favoritos
    :return: itemlist
    """
    logger.trace()
    list_servers = list()
    try:
        referer = inspect.currentframe().f_back.f_back.f_locals.get('item', Item()).url
    except Exception:
        referer = None

    # Obterner los servidores si es necesario
    if len(filter(lambda i: i.type == 'server', itemlist)):
        list_servers = moduletools.get_servers()

    # Recorremos el itemlist
    for item in itemlist:
        # Saltamos todos los que no sean servers
        if not item.type == 'server':
            continue

        # Recorremos los servers
        for server in list_servers:
            # Comprobamos el id y asignamos los datos en caso de coincidencia
            if item.server == server['id'] or item.server in server.get('ids', []):
                item.servername = server['name']
                item.serverimage = server.get('serverimage', 'thumb/%s.png' % server['id'])
                item.server = server['id']
                if server.get('settings'):
                    item.context = [{
                        'label': 'Configurar servidor %s' % server['name'],
                        'action': 'config_channel',
                        'channel': 'settings',
                        'path': server['path']
                    }]
                break

        # Asignamos el label (obsoleto)
        if fnc:
            item.label = fnc(item)

        item.referer = referer

        # Si no se ha encontrado se marca como desconocido
        if not item.servername:
            logger.debug('Servidor no disponible para: \'%s\'' % item.server)
            item.servername = 'Desconocido'
            item.server = 'directo'
            item.serverimage = 'thumb/server_unknow.png'


    # Filtrar si es necesario
    new_itemlist = filter_servers(itemlist)

    # Ordenar segun favoriteslist si es necesario
    if sort:
        itemlist = sort_servers(new_itemlist)

    return itemlist


def get_servers_itemlist(itemlist, fnc=None, sort=True):
    """
    Busca en un listado de items el servidor de cada uno y lo asigna
    :param itemlist: listado de servidores
    :param fnc: funcion encargada de devolver el label para cada item una vez asignado el servidor (obsoleto)
    :param sort: Ordena los servidores segun los favoritos
    :return: itemlist
    """
    logger.trace()
    new_itemlist = list()
    try:
        referer = inspect.currentframe().f_back.f_back.f_locals.get('item', Item()).url
    except Exception:
        referer = None

    num_servers = len(filter(lambda i: i.type == 'server', itemlist))

    # Recorre los servidores
    for server_path in moduletools.get_paths_servers():
        if num_servers > 0:
            server = jsontools.load_file(server_path)
            # Recorre los patrones
            for pattern in server.get("find_videos", {}).get("patterns", []):
                logger.info(pattern["pattern"])
                # Recorre los resultados
                for match in re.compile(pattern["pattern"], re.DOTALL | re.M).finditer(
                        "\n".join([item.url for item in itemlist if not item.server])):
                    url = pattern["url"]
                    for x in range(len(match.groups())):
                        url = url.replace("\\%s" % (x + 1), match.groups()[x])

                    for item in itemlist:
                        if match.group() in item.url:
                            num_servers -= 1
                            item.serverimage = server.get('serverimage', 'thumb/%s.png' % server['id'])
                            item.server = server['id']
                            item.servername = server['name']
                            item.url = url
                            if server.get('settings'):
                                item.context = [{
                                    'label': 'Configurar servidor %s' % server['name'],
                                    'action': 'config_channel',
                                    'channel': 'settings',
                                    'path': server_path
                                }]


    for item in itemlist:
        # Otros items que puedan haber no se tocan
        if not item.type == 'server':
            continue

        # Asignamos el label (obsoleto)
        if fnc:
            item.label = fnc(item)

        item.referer = referer

        # Si no se ha encontrado se marca como desconocido
        if not item.server:
            logger.debug('Servidor no disponible para: \'%s\'' % item.url)
            item.servername = 'Desconocido'
            item.server = 'directo'
            item.serverimage = 'thumb/server_unknow.png'


    # Filtrar si es necesario
    itemlist = filter_servers(itemlist)

    # Ordenar segun favoriteslist si es necesario
    if sort:
        itemlist = sort_servers(itemlist)

    return itemlist


def normalize_url(item):
    """
    Normaliza la url segun el patron del .json
    :param item: item a normalizar
    :return: item
    """
    logger.trace()
    path = os.path.join(sysinfo.data_path, 'modules', 'user_servers', item.server + '.json')
    if not os.path.isfile(path):
        path = os.path.join(sysinfo.runtime_path, 'servers', item.server + '.json')

    server = moduletools.get_module_parameters(path)
    for pattern in server.get("find_videos", {}).get("patterns", []):
        for match in re.compile(pattern["pattern"], re.DOTALL).finditer(item.url):
            url = pattern["url"]
            for x in range(len(match.groups())):
                url = url.replace("\\%s" % (x + 1), match.groups()[x])

            item.url = url
            break

    return item


def resolve_video_urls(item):
    """
    Resuelve la url del servidor en una reproducible
    :param item:
    :return:
    """
    logger.trace()

    if item.server == 'directo':
        return [Video(url=item.url, server='Directo')]

    if item.server == 'local':
        return [Video(url=item.url, server='Local')]

    # Importamos el servidor
    server = moduletools.get_server_module(item.server)

    # Obtenemos los debriders disponibles para el servidor
    debriders = filter(lambda x: item.server in x['servers'], moduletools.get_debriders())

    # Obtenemos los parametros del servidor
    server_parameters = moduletools.get_module_parameters(server.__file__)

    # Mostramos el dialogo
    dialog = platformtools.dialog_progress("MediaExplorer", "Conectando con %s" % server_parameters["name"])

    # Buscamos la url en el servidor
    try:
        result = server.get_video_url(item)
    except Exception:
        result = ResolveError(6)
        logger.error()

    # Si el resultado es un str es que se ha producido un error o el video no existe, ponemos el str en el itemlist
    if isinstance(result, Exception):
        itemlist = '[%s] %s' % (server_parameters['name'], result)

    # Si el resultado es un list es que tenemos enlaces, los pasamos al itemlist
    else:
        itemlist = result

    # Si no tenemos enlaces o aún teniendolos la configuración marca que busquemos en los debriders, buscamos
    if not type(itemlist) == list or not itemlist or not settings.get_setting('resolve_stop', __file__):
        for debrider in debriders:
            # Importamos el debrider
            mod = moduletools.get_debrider_module(debrider['id'])
            dialog.update((debriders.index(debrider) + 1) * 100 / (len(debriders) + 1),
                          "Conectando con %s" % debrider["name"])

            # Probamos con el debrider
            try:
                result = mod.get_video_url(item)
            except Exception, e:
                result = e
                logger.error()

            # Si teniamos un error en el itemlist y aqui obtenemos otro, lo añadimos a una nueva linea
            if type(itemlist) == str:
                if isinstance(result, Exception):
                    itemlist += '\n[%s] %s' % (debrider['name'], result)

                # Si teniamos un error en el itemlist pero aquí tenemos enlaces, borramos el error y ponemos los enlaces
                else:
                    itemlist = result

            # Si ya teniamos enlaces y aqui obtenemos mas enlaces, los añadimos
            else:
                if type(result) == list:
                    itemlist.extend(mod.get_video_url(item))

            # Si tenemos enlaces y la configuración marca que no sigamos buscando, paramos
            if type(itemlist) == list and itemlist and settings.get_setting('resolve_stop'):
                break

        dialog.update(100, "Terminado")

        dialog.close()

    # Ordenamos el itemlist
    def __res2int(i):
        res = re.sub("(\d+)[kK]", '\\g<1>000', i.res)
        res = re.sub("Original", '10000', res) # La resolucion original, sea cual sea, siempre sera mayor q el resto
        try:
            return int(re.findall("(\d+)", res)[0])
        except Exception:
            return 0

    if type(itemlist) == list:
        itemlist = sorted(itemlist, key=__res2int, reverse=True)

    # Si no tenemos error, pero tampoco tenemos enlaces, añadimos un error generico
    if not itemlist:
        itemlist = ResolveError(6)
        logger.debug('No se ha encontrado ningúna url válida para: %s' % item.url)

    return itemlist


def sort_servers(servers_list, priority=5):
    """
    Ordena los servidores por tres criterios:
        1. Los items que no sean servers los primeros.
        2. Los servers que esten marcados como 'stream' antes que los que no.
        3. Por ultimo se ordenan segun el parametro priority.

    :param servers_list: itemlist con servidores
    :priority:
                0 _ No ordenar
                1_ Servidores y calidades
                2_ Calidades y servidores
                3_ Solo servidores
                4_ Solo calidades
                5_(Por defecto) Segun el valor guardado en la configuracion
    :return: itemlist ordenado
    """
    logger.trace()
    order_list = [settings.get_setting('priority_%s' % x, __file__) for x in range(10)]

    if priority > 4:
        priority = settings.get_setting('sort_servers', __file__)

    lambda_priority = [
        # No ordenar
        lambda y: (bool(y.server),
                   not y.stream,
                   0
                ),
        # Servidores y calidades
        lambda y: (bool(y.server),
                   not y.stream,
                   order_list.index(y.server) if y.server in order_list else 100,
                   1000 - y.quality.level if y.quality else 1000
                ),
        # Calidades y servidores
        lambda y: (bool(y.server),
                   not y.stream,
                   1000 - y.quality.level if y.quality else 1000,
                   order_list.index(y.server) if y.server in order_list else 100
                ),
        # Solo servidores
        lambda y: (bool(y.server),
                   not y.stream,
                   order_list.index(y.server) if y.server in order_list else 100
                ),
        # Solo calidades
        lambda y: (bool(y.server),
                   not y.stream,
                   1000 - y.quality.level if y.quality else 1000
                )
    ]

    servers_list = sorted(
        servers_list,
        key= lambda_priority[priority]
    )

    return servers_list


def filter_servers(servers_list):
    """
    Filtra los servidores quitando los que estén desactivados o deshabilitados en la configuración y ocultando
    si es necesario los servidores Desconocidos
    :param servers_list: itemlist con servidores
    :return: itemlist filtrado
    """

    active = dict([(s['id'], s['active']) for s in moduletools.get_servers()])

    if settings.get_setting('hide_servers_unknown', __file__):
        # Ocultar Desconocidos
        servers_list = filter(
            lambda x: x.servername != 'Desconocido' and active.get(x.server, True) and
                not settings.get_setting("disabled",
                                         os.path.join(sysinfo.runtime_path, 'servers', '%s.json' % x.server)),
            servers_list)

    else:
        servers_list = filter(
            lambda x: active.get(x.server, True) and
                      not settings.get_setting("disabled",
                                               os.path.join(sysinfo.runtime_path, 'servers', '%s.json' % x.server)),
            servers_list)

    return servers_list


def autoplay(itemlist, item):
    """
    Funcion que intenta reproducir un video del itemlist automaticamente despues de filtrar y ordenar el listado.
        1. Se eliminan los enlaces de servidores 'Desconocidos' (no suelen funcionar) y los del tipo 'download'
        2. Se eliminan todos los enlaces que no correspondan al "Idioma preferido de reproducción" fijado en Ajustes.
        3. Se eliminan los enlaces cuya calidad este incluida en 'disabled_qualities'
        4. Se ordena el listado resultante segun el criterio 'Ordenar enlaces' dentro de la "Configuración general de servidores"

    :param itemlist: Listado de items devuelto por la funcion 'findvideos'
    :param item: Elemento del menu que invoco a 'findvideo'
    :return: True en el caso de que se haya podido reproducir en video. False en caso contrario.
    """
    logger.trace()
    autoplay_list = itemlist

    # Informa que AutoPlay esta activo
    dialog = platformtools.dialog_progress_bg('AutoPlay', 'Iniciando...')

    # Filtrar solo streaming (excepto server='directo') y del idioma predeterminado
    lang_autoplay = sorted(Languages().all, key=lambda obj: obj.label)[settings.get_setting('autoplay_lang_fav')]
    try:
        autoplay_list = filter(
            lambda x: x.type == 'server' and
                      x.stream and x.server != 'directo' and
                      x.lang.name == lang_autoplay.name,
            autoplay_list
        )
    except:
        lang_autoplay = Languages.from_name('unk')

    # Filtrado por calidades
    if settings.get_setting('quality_filter_server'):
        disabled_qualities = settings.get_setting('disabled_qualities') or []
        autoplay_list = filter(
            lambda x: x.quality.name not in disabled_qualities,
            autoplay_list
        )

    if not autoplay_list:
        # No hay enlaces que satisfagan todos los filtros
        dialog.update(100, 'AutoPlay', 'No hay enlaces que cumplan todos los filtros')
        time.sleep(2)
        dialog.close()
        return False

    # Ordenar segun la prioridad seleccionada
    autoplay_list = servertools.sort_servers(autoplay_list, settings.get_setting('sort_servers', __file__))


    # Si se esta reproduciendo algo detiene la reproduccion
    if platformtools.is_playing():
        platformtools.stop_video()

    # Recorrer la lista intentando encontrar uno funcional
    max_intentos = int(settings.get_setting('autoplay_max_intentos', getvalue=True))
    max_intentos_servers = {}

    for autoplay_elem in autoplay_list:
        if not platformtools.is_playing():
            if autoplay_elem.server not in max_intentos_servers:
                max_intentos_servers[autoplay_elem.server] = max_intentos

            # Si se han alcanzado el numero maximo de intentos de este servidor saltamos al siguiente
            if max_intentos_servers[autoplay_elem.server] == 0:
                continue

            dialog.update((autoplay_list.index(autoplay_elem) + 1) * 100 / (len(autoplay_list) + 1),
                          'AutoPlay',
                          "%s [%s] %s" % (
                              autoplay_elem.servername,
                              lang_autoplay.label,
                              ("(%s)" % autoplay_elem.quality.label) if isinstance(autoplay_elem.quality, Language) else ''
                          ))

            # Intenta reproducir los enlaces
            from core import launcher
            launcher.run(autoplay_elem.clone(autoplay=True))

            if platformtools.is_playing():
                dialog.close()
                return True
            else:
                max_intentos_servers[autoplay_elem.server] -= 1

                # Si se han alcanzado el numero maximo de intentos de este servidor
                # preguntar si queremos seguir probando o lo ignoramos
                if max_intentos_servers[autoplay_elem.server] == 0:
                    text = "Parece que los enlaces de %s no estan funcionando." % autoplay_elem.servername
                    if not platformtools.dialog_yesno("AutoPlay", text,
                                                      "¿Desea ignorar todos los enlaces de este servidor?"):
                        max_intentos_servers[autoplay_elem.server] = max_intentos

    dialog.update(100, 'No ha sido posible reproducir ningún enlace automáticamente')
    time.sleep(2)
    dialog.close()
    return False


def config(item):
    return platformtools.show_settings()