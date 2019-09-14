# -*- coding: utf-8 -*-
from core.libs import *


def mainlist(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        label='Configuración general',
        type='item1',
        action='config',
        folder=False,
        description='Ajustes generales'
    ))

    itemlist.append(item.clone(
        label='Configuración especifica para %s' % sysinfo.platform_name,
        type='item1',
        action='platform_config',
        folder=False,
        description='Ajustes especificos para %s' % sysinfo.platform_name
    ))

    itemlist.append(item.clone(
        label='Configuración de aspecto',
        type='item1',
        action='visual_config',
        folder=False,
        description='Todos los ajustes sobre la apariencia de MediaExplorer los encontrarás aquí'
    ))

    itemlist.append(item.clone(
        label='Configuración de canales',
        type='item1',
        action='menuchannels',
        folder=True,
        description='Ajustes de canales: Activar/Desactivar canales, Configurar cuentas de usuario, etc...',
    ))

    itemlist.append(item.clone(
        label='Configuración de servidores',
        type='item1',
        action='menuservers',
        folder=True,
        description='Ajustes de servidores: Activar/Desactivar servidores, Seleccionar los servidores favoritos, '
                    'Cuentas premium, etc...',
    ))

    itemlist.append(item.clone(
        label='Configuración de Anti Captcha',
        type='item1',
        action='config',
        channel='anticaptcha',
        description='Ajustes para el servicio anti captcha, necesario para algunas webs, requiere registro en '
                    'https://anti-captcha.com el servicio es de pago',
    ))

    itemlist.append(item.clone(label='', action=''))
    itemlist.append(item.clone(label='Ajustes por secciones:', type='label', action=''))

    itemlist.append(item.clone(
        label='Configuración de la Biblioteca',
        type='item',
        channel='library',
        action='config',
        folder=False,
        group=True,
        description='Todos los ajustes sobre la Biblioteca los encontrarás aquí'
    ))

    itemlist.append(item.clone(
        label='Configuración del Buscador',
        type='item',
        channel='finder',
        action='settings_menu',
        group=True,
        description='Todos los ajustes sobre el Buscador los encontrarás aquí'
    ))

    itemlist.append(item.clone(
        label='Configuración de Novedades',
        type='item',
        channel='newest',
        action='config_menu',
        folder=True,
        group=True,
        description='Todos los ajustes sobre la sección \'Novedades\' los encontrarás aquí'
    ))

    itemlist.append(item.clone(
        label='Configuración de Descargas',
        type='item',
        channel='downloads',
        action='config',
        folder=False,
        group=True,
        description='Todos los ajustes sobre la sección \'Descargas\' los encontrarás aquí'
    ))

    itemlist.append(item.clone(label='', action=''))
    itemlist.append(item.clone(label='Herramientas:', type='label', action=''))

    itemlist.append(item.clone(
        label='Copias de seguridad',
        type='item',
        action='mainlist',
        channel='backup',
        group=True,
        description='Permite hacer una copia de seguridad de los ajustes y restaurarlos',
    ))

    itemlist.append(item.clone(
        label='Publicar archivos de configuración',
        type='item',
        action='publicar_config',
        folder=False,
        group=True,
        description='Compartir sus ajustes sin desvelar sus contraseñas.'
    ))

    itemlist.append(item.clone(
        label='Gestor de librerias',
        type='item',
        action='mainlist',
        channel='libraries',
        folder=True,
        group=True,
        description='Ayuda a instalar las librerias externas'
    ))

    return itemlist


def platform_config(item):
    from platformcode import platformsettings
    platformsettings.config()


def config(item):
    platformtools.show_settings(callback='save_config')


def save_config(item, values):
    if sysinfo.platform_name == 'mediaserver' and 'adult_mode' in values:
        from platformcode import mediaserver
        if values['adult_mode'] == 1:
            values['adult_mode'] = 0
            mediaserver.set_adult_client()
        else:
            mediaserver.set_adult_client(False)

    old_debug_mode = get_setting('debug')
    old_update_channel = get_setting('update_channel')
    set_settings(values)

    if get_setting('debug') != old_debug_mode:
        if get_setting('debug') == 4:
            # Activar modo report
            platformtools.dialog_ok('MediaExplorer', 'Activado el modo Reporte.',
                                    'Este modo permanecerá activo hasta que se desactive manualmente, se produzca un error o pasen 10 minutos.')
            set_setting('debug_time_Report', [time.time(), old_debug_mode])

            if os.path.isfile(os.path.join(sysinfo.data_path, 'report.log')):
                os.remove(os.path.join(sysinfo.data_path, 'report.log'))

            logger.init_logger()

        elif old_debug_mode == 4:
            # Desactivar modo report
            from core import launcher
            launcher.report()

    if get_setting('update_channel') != old_update_channel:
        platformtools.itemlist_refresh()


def langs_filter(item):
    logger.trace()

    controls = []

    disabled_langs = settings.get_setting('disabled_langs') or []

    controls.append({
        'id': 'lang_filter_server',
        'label': 'Filtrar idiomas en el listado de servidores:',
        'type': 'bool',
        'value': settings.get_setting('lang_filter_server') or False
    })

    '''controls.append({
        'id': 'lang_filter_media',
        'label': 'Filtrar idiomas en el listado de contenido:',
        'type': 'bool',
        'value': settings.get_setting('lang_filter_media') or False
    })'''

    controls.append({
        'label': 'Idiomas que desea ocultar:',
        'type': 'label',
    })

    for lang in sorted(Languages().all, key=lambda obj: obj.label):
        controls.append({
            'id': lang.name,
            'label': lang.label,
            'type': 'bool',
            'value': lang.name in disabled_langs,
            'enabled': 'eq(-%s,true)|eq(-%s,true)' % (len(controls), len(controls) - 1)
        })

    return platformtools.show_settings(controls=controls,
                                       title=item.label,
                                       callback="langs_save"
                                       )


def langs_save(item, values):
    logger.trace()
    settings.set_setting('lang_filter_server', values.pop('lang_filter_server'))
    # settings.set_setting('lang_filter_media', values.pop('lang_filter_media'))
    settings.set_setting('disabled_langs', [k for k, v in values.items() if v is True])


def qualities_filter(item):
    logger.trace()

    controls = []

    disabled_qualities = settings.get_setting('disabled_qualities') or []
    controls.append({
        'id': 'quality_filter_server',
        'label': 'Filtrar calidades en el listado de servidores:',
        'type': 'bool',
        'value': settings.get_setting('quality_filter_server') or False
    })

    '''controls.append({
        'id': 'quality_filter_media',
        'label': 'Filtrar calidades en el listado de contenido:',
        'type': 'bool',
        'value': settings.get_setting('quality_filter_media') or False
    })'''

    controls.append({
        'label': 'Calidades que desea ocultar:',
        'type': 'label',
    })

    for quality in sorted(Qualities().all, key=lambda obj: obj.level):
        controls.append({
            'id': quality.name,
            'label': quality.label,
            'type': 'bool',
            'value': quality.name in disabled_qualities,
            'enabled': 'eq(-%s,true)|eq(-%s,true)' % (len(controls), len(controls) - 1)
        })

    return platformtools.show_settings(controls=controls,
                                       title=item.label,
                                       callback="qualities_save"
                                       )


def qualities_save(item, values):
    logger.trace()
    settings.set_setting('quality_filter_server', values.pop('quality_filter_server'))
    # settings.set_setting('quality_filter_media', values.pop('quality_filter_media'))
    settings.set_setting('disabled_qualities', [k for k, v in values.items() if v is True])


def visual_config(item):
    from platformcode import viewtools
    return platformtools.show_settings(mod=viewtools.__file__, title=item.label)


def menuchannels(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        label='Activar o desactivar canales',
        action='active_channels',
        folder=False,
        description='Desactiva los canales que no quieras que se muestren en MediaExplorer'
    ))

    itemlist.append(item.clone(
        label='Configurar proxies para los canales',
        action='config_proxies',
        folder=False,
        description='Configurar proxies para los canales'
    ))

    itemlist.append(item.clone(label='', action=''))
    itemlist.append(item.clone(label='Ajustes propios de cada canal:', type='label', action=''))

    channel_list = moduletools.get_channels()

    for channel in channel_list:
        if not channel.get('settings'):
            continue

        controls = filter(lambda s: not s['id'].startswith('include_in_'), channel['settings'])

        if not controls:
            continue

        itemlist.append(item.clone(
            label=channel['name'],
            type='item',
            action='config_channel',
            path=channel['path'],
            folder=False,
            thumb='',
            group=True,
            description='Configuracíón indiviual para el canal %s' % channel['name']
        ))

    return itemlist


def config_channel(item):
    return platformtools.show_settings(mod=item.path,
                                       title=item.label)


def config_proxies(item):
    logger.trace()

    controls = [
        {
            "id": "proxy_aut",
            "label": "proxy",
            "default": "",
            "value": get_setting("proxy_aut") or "",
            "type": "text",
            "visible": False
        },
        {
            "default": 0,
            "id": "proxy_tipo",
            "type": "list",
            "label": "Selección de proxy:",
            "value": get_setting("proxy_tipo"),
            "lvalues": ["Manual", "Automatica"]
        },
        {
            "default": "198.27.67.35:3128",
            "id": "proxy_man",
            "label": "    - Proxy http/https (IP:Puerto):",
            "value": get_setting("proxy_man") or "198.27.67.35:3128",
            "type": "text",
            "visible": "eq(-1,0)"
        },
        {
            "default": 0,
            "id": "proxy_aut_list",
            "type": "list",
            "label": "    - Listado web de proxies:",
            "value": get_setting("proxy_aut_list"),
            "lvalues": ["proxyscrape.com", "spys.me", 'proxy-list.download'],
            "mode": "label",
            "visible": "eq(-2,1)"
        },
        {
            "default": False,
            "id": "proxy_aut_search_now",
            "label": "    - Proxy actual: %s. Buscar nuevo proxy ahora:" % (get_setting("proxy_aut") or ""),
            "type": "bool",
            "value": False,
            "visible": "eq(-3,1) + !eq(-4,'')"
        }
    ]

    return platformtools.show_settings(controls=controls, title=item.label,
                                       callback='config_proxies_cb')


def config_proxies_cb(item, values):
    logger.trace()
    # Validar proxy_man
    mascara = scrapertools.find_single_match(values['proxy_man'], '^(\d+)\.(\d+)\.(\d+)\.(\d+):(\d+)$')
    if len(mascara) != 5 or int(mascara[0]) > 255 or int(mascara[1]) > 255 or int(mascara[2]) > 255 or int(
            mascara[3]) > 255 or int(mascara[4]) > 65535:
        values['proxy_man'] = get_setting('proxy_man') or "198.27.67.35:3128"

    proxy_aut_search_now = values.pop('proxy_aut_search_now', False) and values["proxy_tipo"] == 1
    set_settings(values)

    # Buscar nuevo proxy automatico ahora?
    if proxy_aut_search_now:
        httptools.search_proxies()


def menuservers(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        label='Configuración general de servidores',
        action='config',
        channel='servertools',
        folder=False,
        description='Ajustes generales de los servidores'
    ))

    itemlist.append(item.clone(
        label='Activar o desactivar servidores',
        action='active_servers',
        folder=False,
        description='Desactiva los servidores que no quieras que se muestren en MediaExplorer'
    ))

    itemlist.append(item.clone(
        label='Servidores preferidos',
        action='priority_servers',
        folder=False,
        description='Selecciona los servidores preferidos, estos se mostraran al principio del listado'
    ))

    itemlist.append(item.clone(
        label='Filtrar servidores por idiomas',
        action='langs_filter',
        folder=False,
        description='Selecciona que idiomas que no deseas que se muestren en los resultados'
    ))

    itemlist.append(item.clone(
        label='Filtrar servidores por calidades',
        action='qualities_filter',
        folder=False,
        description='Selecciona que calidades que no deseas que se muestren en los resultados'
    ))

    itemlist.append(item.clone(label='', action=''))
    itemlist.append(item.clone(label='Ajustes propios de debriders:', type='label', action=''))

    debriders = moduletools.get_debriders()

    for debrider in debriders:
        if not debrider.get('settings'):
            continue

        itemlist.append(item.clone(
            label=debrider['name'],
            type='item',
            action='config_channel',
            path=debrider['path'],
            folder=False,
            thumb='',
            group=True,
            description='Configuracíón indiviual para el servidor %s' % debrider['name']
        ))

    itemlist.append(item.clone(label='', action=''))
    itemlist.append(item.clone(label='Ajustes propios de cada servidor:', type='label', action=''))

    server_list = moduletools.get_servers()

    for server in server_list:
        if not server.get('settings'):
            continue

        controls = filter(lambda s: not s['id'].startswith('include_in_'), server['settings'])

        if not controls:
            continue

        itemlist.append(item.clone(
            label=server['name'],
            type='item',
            action='config_channel',
            path=server['path'],
            folder=False,
            thumb='',
            group=True,
            description='Configuracíón indiviual para el servidor %s' % server['name']
        ))

    return itemlist


def priority_servers(item):
    logger.trace()

    server_list = moduletools.get_servers()
    namelist = ['Ninguno'] + [s['name'] for s in server_list]
    idlist = [None] + [s['id'] for s in server_list]

    controls = []

    for c in range(10):
        value = idlist.index(get_setting('priority_%s' % c, servertools.__file__))
        control = {'id': str(c),
                   'type': "list",
                   'label': 'Servidor #%s' % (c + 1),
                   'value': value,
                   'default': 0,
                   'enabled': (True, 'gt(-1,0)')[bool(c)],
                   'lvalues': namelist
                   }

        controls.append(control)

    return platformtools.show_settings(controls=controls,
                                       title=item.label,
                                       callback="priority_servers_save",
                                       item=idlist
                                       )


def priority_servers_save(item, values):
    logger.trace()
    progreso = platformtools.dialog_progress("Guardando configuración...", "Espere un momento por favor.")

    n = len(values)

    server_list = moduletools.get_servers()
    serverslist = [None] + [s['id'] for s in server_list]

    for i, v in values.items():
        progreso.update((int(i) * 100) / n, "Guardando configuración...")
        set_setting('priority_%s' % i, serverslist[v], servertools.__file__)

    progreso.close()


def active_servers(item):
    logger.trace()

    server_list = moduletools.get_servers()

    controls = []
    for server in server_list:
        control = {'id': server['path'],
                   'type': "bool",
                   'label': server['name'],
                   'value': not get_setting('disabled', server['path']),
                   'default': True
                   }

        controls.append(control)

    return platformtools.show_settings(controls=controls,
                                       title=item.label,
                                       callback="save_active_channels"
                                       )


def active_channels(item):
    logger.trace()

    channel_list = moduletools.get_channels()

    controls = []
    for channel in channel_list:
        control = {'id': channel['path'],
                   'type': "bool",
                   'label': channel['name'],
                   'value': not get_setting('disabled', channel['path']),
                   'default': True
                   }

        controls.append(control)

    return platformtools.show_settings(controls=controls,
                                       title=item.label,
                                       callback="save_active_channels"
                                       )


def save_active_channels(item, values):
    logger.trace()
    progreso = platformtools.dialog_progress("Guardando configuración...", "Espere un momento por favor.")
    n = len(values)
    for i, v in enumerate(values):
        progreso.update((i * 100) / n, "Guardando configuración...")
        set_setting("disabled", not values[v], v)

    progreso.close()


def publicar_config(item):
    logger.trace()
    controls = []
    n = 0

    # Archivos Logs
    for s in filetools.listdir(sysinfo.data_path):
        if s.endswith('.log'):
            controls.append({
                'id': filetools.join(sysinfo.data_path, s),
                'type': "bool",
                'label': ' ' * 5 + s,
                'value': False,
                'default': False
            })

    if controls:
        controls.insert(0, {"label": "Archivos de eventos:", "type": "label"})

    # Arcivos JSON
    for c in ['core', 'platformcode']:
        path = filetools.join(sysinfo.data_path, 'settings', c)
        if filetools.exists(path):
            lisdir = sorted(filetools.listdir(path))
            if lisdir:
                controls.append({"label": "Archivos de configuración %s:" % c.capitalize(), "type": "label"})
            for s in lisdir:
                if s.endswith('.json'):
                    controls.append({
                        'id': filetools.join(path, s),
                        'type': "bool",
                        'label': ' ' * 5 + s,
                        'value': False,
                        'default': False
                    })

    return platformtools.show_settings(controls=controls,
                                       title=item.label,
                                       callback='publicar_config_cb')


def publicar_config_cb(item, values):
    logger.trace()

    values = {k: v for k, v in values.items() if v == True}

    if not values:
        platformtools.dialog_ok('MediaExplorer', '¡No ha seleccionado ningun archivo!')
        return

    else:
        from core import anonfile
        import tempfile
        import ziptools
        filelist = list()
        error = None

        for path in values:
            if path.endswith('.json'):
                data = jsontools.load_file(path)
                for k in data.keys():
                    if 'password' in k:
                        data[k] = '*' * len(data[k])
                filelist.append([path.replace(sysinfo.data_path, ''), jsontools.dump_json(data)])

            else:
                filelist.append([path.replace(sysinfo.data_path, ''), path])

        try:
            backup_file = tempfile.NamedTemporaryFile().name
            ziptools.create_zip(backup_file, filelist, True)

        except:
            error = "Error al comprimir los archivos."

        else:
            try:
                fname = "configuracion_%s.zip" % datetime.datetime.utcnow().strftime('%Y%m%d%H%S')
                dialog = platformtools.dialog_progress('Subiendo archivo...', fname)
                msg = "Subiendo %s a Anonfile\nEsto puede tardar unos minutos. Por favor, espere." % fname
                dialog.update(75, msg)
                response_id = anonfile.upload(backup_file, fname)
                if dialog.iscanceled():
                    error = "Error al subir el archivo comprimido. Operación cancelada por el usuario"

                dialog.close()

            except:
                error = "Error al subir el archivo comprimido."

            else:
                if not error:
                    if response_id:
                        url = 'https://anonfile.com/%s' % response_id
                        logger.debug("Archivo subido a %s" % url)
                        img = 'http://www.codigos-qr.com/qr/php/qr_img.php?d=%s&s=6&e=m' % url
                        msg = 'El archivo comprimido se han subido a Anonfile.\nPuede abrirlo escaneando el codigo QR o ' \
                              'accediendo a %s' % url
                        platformtools.dialog_img_yesno(img, 'MediaExplorer: Configuración compartida', msg, False)

                    else:
                        error = "Error al subir el archivo comprimido."

        if error:
            logger.debug(error)
            platformtools.dialog_notification('MediaExplorer: Configuración compartida', error, 2)


#######################################################################################
def check_directories():
    logger.trace()
    if not os.path.exists(sysinfo.data_path):
        os.makedirs(sysinfo.data_path)

    if not os.path.exists(os.path.join(sysinfo.data_path, 'modules')):
        os.makedirs(os.path.join(sysinfo.data_path, 'modules'))

    if not os.path.exists(os.path.join(sysinfo.data_path, 'modules', 'user_channels')):
        os.makedirs(os.path.join(sysinfo.data_path, 'modules', 'user_channels'))
        open(os.path.join(sysinfo.data_path, 'modules', 'user_channels', '__init__.py'), 'wb')

    if not os.path.exists(os.path.join(sysinfo.data_path, 'modules', 'user_servers')):
        os.makedirs(os.path.join(sysinfo.data_path, 'modules', 'user_servers'))
        open(os.path.join(sysinfo.data_path, 'modules', 'user_servers', '__init__.py'), 'wb')


def set_setting(name, value, mod=__file__):
    if sysinfo.data_path in mod:
        if 'user_channels' in mod:
            settings_path = '%s.json' % os.path.splitext(
                mod.replace(
                    os.path.join(sysinfo.data_path, 'modules', 'user_channels'),
                    os.path.join(sysinfo.data_path, 'settings', 'channels'))
            )[0]

        if 'user_servers' in mod:
            settings_path = '%s.json' % os.path.splitext(
                mod.replace(
                    os.path.join(sysinfo.data_path, 'modules', 'user_servers'),
                    os.path.join(sysinfo.data_path, 'settings', 'servers'))
            )[0]
    else:
        if sysinfo.runtime_path not in mod and ('/' in mod or '\\' in mod):
            mod = os.path.join(sysinfo.runtime_path, mod.replace('/', '\\').replace('\\', os.path.sep))

        settings_path = '%s.json' % os.path.splitext(
            mod.replace(sysinfo.runtime_path, os.path.join(sysinfo.data_path, 'settings')))[0]

    data = {}

    if os.path.isfile(settings_path):
        try:
            data = jsontools.load_file(settings_path)
        except Exception:
            logger.error()

    data[name] = value
    jsontools.dump_file(data, settings_path)


def set_settings(values, mod=__file__):
    if sysinfo.data_path in mod:
        if 'user_channels' in mod:
            settings_path = '%s.json' % os.path.splitext(
                mod.replace(
                    os.path.join(sysinfo.data_path, 'modules', 'user_channels'),
                    os.path.join(sysinfo.data_path, 'settings', 'channels'))
            )[0]

        if 'user_servers' in mod:
            settings_path = '%s.json' % os.path.splitext(
                mod.replace(
                    os.path.join(sysinfo.data_path, 'modules', 'user_servers'),
                    os.path.join(sysinfo.data_path, 'settings', 'servers'))
            )[0]
    else:
        if sysinfo.runtime_path not in mod and ('/' in mod or '\\' in mod):
            mod = os.path.join(sysinfo.runtime_path, mod.replace('/', '\\').replace('\\', os.path.sep))

        settings_path = '%s.json' % os.path.splitext(
            mod.replace(sysinfo.runtime_path, os.path.join(sysinfo.data_path, 'settings')))[0]

    data = {}

    if os.path.isfile(settings_path):
        try:
            data = jsontools.load_file(settings_path)
        except Exception:
            logger.error()

    data.update(values)
    jsontools.dump_file(data, settings_path)


def pop_setting(name, mod=__file__, default=None):
    if sysinfo.data_path in mod:
        if 'user_channels' in mod:
            settings_path = '%s.json' % os.path.splitext(
                mod.replace(
                    os.path.join(sysinfo.data_path, 'modules', 'user_channels'),
                    os.path.join(sysinfo.data_path, 'settings', 'channels'))
            )[0]

        if 'user_servers' in mod:
            settings_path = '%s.json' % os.path.splitext(
                mod.replace(
                    os.path.join(sysinfo.data_path, 'modules', 'user_servers'),
                    os.path.join(sysinfo.data_path, 'settings', 'servers'))
            )[0]
    else:
        if sysinfo.runtime_path not in mod and ('/' in mod or '\\' in mod):
            mod = os.path.join(sysinfo.runtime_path, mod.replace('/', '\\').replace('\\', os.path.sep))

        settings_path = '%s.json' % os.path.splitext(
            mod.replace(sysinfo.runtime_path, os.path.join(sysinfo.data_path, 'settings')))[0]

    ret = default

    if os.path.isfile(settings_path):
        try:
            data = jsontools.load_file(settings_path)
            ret = data.pop(name, default)
            jsontools.dump_file(data, settings_path)
        except Exception:
            logger.error()

    return ret


def get_setting(name, mod=__file__, getvalue=False):
    if sysinfo.data_path in mod:
        if 'user_channels' in mod:
            settings_path = '%s.json' % os.path.splitext(
                mod.replace(
                    os.path.join(sysinfo.data_path, 'modules', 'user_channels'),
                    os.path.join(sysinfo.data_path, 'settings', 'channels'))
            )[0]

        if 'user_servers' in mod:
            settings_path = '%s.json' % os.path.splitext(
                mod.replace(
                    os.path.join(sysinfo.data_path, 'modules', 'user_servers'),
                    os.path.join(sysinfo.data_path, 'settings', 'servers'))
            )[0]
    else:
        if sysinfo.runtime_path not in mod and ('/' in mod or '\\' in mod):
            mod = os.path.join(sysinfo.runtime_path, mod.replace('/', '\\').replace('\\', os.path.sep))

        settings_path = '%s.json' % os.path.splitext(
            mod.replace(sysinfo.runtime_path, os.path.join(sysinfo.data_path, 'settings')))[0]

    def get_value(v, n, m, t):
        if not t:
            return v

        controls = moduletools.get_controls(m)
        for control in controls:
            if control.get('id') == n and control.get('type') == 'list':
                try:
                    return control.get('lvalues')[v]
                except Exception:
                    pass
        return v

    if os.path.isfile(settings_path):
        try:
            data = jsontools.load_file(settings_path)
            if name in data:
                if name == 'adult_mode' and sysinfo.platform_name == 'mediaserver' and data[name] == 0:
                    from platformcode import mediaserver
                    return get_value(mediaserver.get_adult_client(), name, mod, getvalue)
                return get_value(data[name], name, mod, getvalue)
        except Exception:
            logger.error()

    controls = moduletools.get_controls(mod)

    for control in controls:
        if control.get('id') == name:
            if type(control['default']) == str and re.match('^eval\((.*?)\)$', control['default']):
                return get_value(eval(re.match('^eval\((.*?)\)$', control['default']).group(1)), name, mod, getvalue)
            else:
                return get_value(control['default'], name, mod, getvalue)
