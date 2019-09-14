# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Configuracion
# ------------------------------------------------------------

from channelselector import get_thumb
from core import filetools
from core import servertools
from core.item import Item
from platformcode import config, logger
from platformcode import platformtools

CHANNELNAME = "setting"


def mainlist(item):
    logger.info()

    itemlist = list()
    itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60535), action="settings", folder=False,
                         thumbnail=get_thumb("setting_0.png")))

    itemlist.append(Item(channel=CHANNELNAME, title="", action="", folder=False, thumbnail=get_thumb("setting_0.png")))

    itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60536) + ":", text_bold=True, action="", folder=False,
                         thumbnail=get_thumb("setting_0.png")))
    itemlist.append(Item(channel=CHANNELNAME, title="     " + config.get_localized_string(60537), action="menu_channels", folder=True,
                         thumbnail=get_thumb("channels.png")))
    itemlist.append(Item(channel=CHANNELNAME, title="     " + config.get_localized_string(60538), action="menu_servers", folder=True,
                         thumbnail=get_thumb("channels.png")))
    itemlist.append(Item(channel="news", title="     " + config.get_localized_string(60539), action="menu_opciones",
                         folder=True, thumbnail=get_thumb("news.png")))
    itemlist.append(Item(channel="search", title="     " + config.get_localized_string(60540), action="opciones", folder=True,
                         thumbnail=get_thumb("search.png")))
    itemlist.append(Item(channel=CHANNELNAME, title="     " + config.get_localized_string(60541), action="channel_config",
                         config="downloads", folder=True, thumbnail=get_thumb("downloads.png")))

    if config.get_videolibrary_support():
        itemlist.append(Item(channel="videolibrary", title="     " + config.get_localized_string(60542), action="channel_config",
                             folder=True, thumbnail=get_thumb("videolibrary.png")))

    if config.is_xbmc():
        itemlist.append(Item(channel=CHANNELNAME, title="     " + config.get_localized_string(70253), action="setting_torrent",
                             folder=True, thumbnail=get_thumb("channels_torrent.png")))

    itemlist.append(Item(channel=CHANNELNAME, action="", title="", folder=False, thumbnail=get_thumb("setting_0.png")))
    itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60544), action="submenu_tools", folder=True,
                         thumbnail=get_thumb("setting_0.png")))

    return itemlist


def menu_channels(item):
    logger.info()
    itemlist = list()

    itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60545), action="conf_tools", folder=False,
                         extra="channels_onoff", thumbnail=get_thumb("setting_0.png")))

    itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60546) + ":", action="", folder=False,
                         text_bold = True, thumbnail=get_thumb("setting_0.png")))

    # Inicio - Canales configurables
    import channelselector
    from core import channeltools
    channel_list = channelselector.filterchannels("all")
    for channel in channel_list:
        if not channel.channel:
            continue
        channel_parameters = channeltools.get_channel_parameters(channel.channel)
        if channel_parameters["has_settings"]:
            itemlist.append(Item(channel=CHANNELNAME, title=".    " + config.get_localized_string(60547) % channel.title,
                                 action="channel_config", config=channel.channel, folder=False,
                                 thumbnail=channel.thumbnail))
    # Fin - Canales configurables
    itemlist.append(Item(channel=CHANNELNAME, action="", title="", folder=False, thumbnail=get_thumb("setting_0.png")))
    itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60548) + ":", action="", folder=False,
                         text_bold=True, thumbnail=get_thumb("channels.png")))
    itemlist.append(Item(channel=CHANNELNAME, title=".    " + config.get_localized_string(60549), action="conf_tools",
                         folder=True, extra="lib_check_datajson", thumbnail=get_thumb("channels.png")))
    return itemlist


def channel_config(item):
    return platformtools.show_channel_settings(channelpath=filetools.join(config.get_runtime_path(), "channels",
                                                                          item.config))


def setting_torrent(item):
    logger.info()

    LIBTORRENT_PATH = config.get_setting("libtorrent_path", server="torrent", default="")
    LIBTORRENT_ERROR = config.get_setting("libtorrent_error", server="torrent", default="")
    default = config.get_setting("torrent_client", server="torrent", default=0)
    BUFFER = config.get_setting("mct_buffer", server="torrent", default="50")
    DOWNLOAD_PATH = config.get_setting("mct_download_path", server="torrent", default=config.get_setting("downloadpath"))
    BACKGROUND = config.get_setting("mct_background_download", server="torrent", default=True)
    RAR = config.get_setting("mct_rar_unpack", server="torrent", default=True)
    DOWNLOAD_LIMIT = config.get_setting("mct_download_limit", server="torrent", default="")
    BUFFER_BT = config.get_setting("bt_buffer", server="torrent", default="50")
    DOWNLOAD_PATH_BT = config.get_setting("bt_download_path", server="torrent", default=config.get_setting("downloadpath"))
    MAGNET2TORRENT = config.get_setting("magnet2torrent", server="torrent", default=False)

    torrent_options = [config.get_localized_string(30006), config.get_localized_string(70254), config.get_localized_string(70255)]
    torrent_options.extend(platformtools.torrent_client_installed())
    

    list_controls = [
        {
            "id": "libtorrent_path",
            "type": "text",
            "label": "Libtorrent path",
            "default": LIBTORRENT_PATH,
            "enabled": True,
            "visible": False
        },
        {
            "id": "libtorrent_error",
            "type": "text",
            "label": "libtorrent error",
            "default": LIBTORRENT_ERROR,
            "enabled": True,
            "visible": False
        },
        {
            "id": "list_torrent",
            "type": "list",
            "label": config.get_localized_string(70256),
            "default": default,
            "enabled": True,
            "visible": True,
            "lvalues": torrent_options
        },
        {
            "id": "mct_buffer",
            "type": "text",
            "label": "MCT - Tamaño del Buffer a descargar antes de la reproducción",
            "default": BUFFER,
            "enabled": True,
            "visible": "eq(-1,%s)" % torrent_options[2]
        },
        {
            "id": "mct_download_path",
            "type": "text",
            "label": "MCT - Ruta de la carpeta de descarga",
            "default": DOWNLOAD_PATH,
            "enabled": True,
            "visible": "eq(-2,%s)" % torrent_options[2]
        },
        {
            "id": "bt_buffer",
            "type": "text",
            "label": "BT - Tamaño del Buffer a descargar antes de la reproducción",
            "default": BUFFER_BT,
            "enabled": True,
            "visible": "eq(-3,%s)" % torrent_options[1]
        },
        {
            "id": "bt_download_path",
            "type": "text",
            "label": "BT - Ruta de la carpeta de descarga",
            "default": DOWNLOAD_PATH_BT,
            "enabled": True,
            "visible": "eq(-4,%s)" % torrent_options[1]
        },
        {
            "id": "mct_download_limit",
            "type": "text",
            "label": "Límite (en Kb's) de la velocidad de descarga en segundo plano (NO afecta a RAR)",
            "default": DOWNLOAD_LIMIT,
            "enabled": True,
            "visible": "eq(-5,%s) | eq(-5,%s)" % (torrent_options[1], torrent_options[2])
        },
        {
            "id": "mct_rar_unpack",
            "type": "bool",
            "label": "¿Quiere que se descompriman los archivos RAR y ZIP para su reproducción?",
            "default": RAR,
            "enabled": True,
            "visible": True
        },
        {
            "id": "mct_background_download",
            "type": "bool",
            "label": "¿Se procesa la descompresión de RARs en segundo plano?",
            "default": BACKGROUND,
            "enabled": True,
            "visible": True
        },
        {
            "id": "magnet2torrent",
            "type": "bool",
            "label": "¿Quiere convertir los Magnets a Torrents para ver tamaños y almacenarlos?",
            "default": MAGNET2TORRENT,
            "enabled": True,
            "visible": True
        }
    ]

    platformtools.show_channel_settings(list_controls=list_controls, callback='save_setting_torrent', item=item,
                                        caption=config.get_localized_string(70257), custom_button={'visible': False})


def save_setting_torrent(item, dict_data_saved):
    if dict_data_saved and "list_torrent" in dict_data_saved:
        config.set_setting("torrent_client", dict_data_saved["list_torrent"], server="torrent")
    if dict_data_saved and "mct_buffer" in dict_data_saved:
        config.set_setting("mct_buffer", dict_data_saved["mct_buffer"], server="torrent")
    if dict_data_saved and "mct_download_path" in dict_data_saved:
        config.set_setting("mct_download_path", dict_data_saved["mct_download_path"], server="torrent")
    if dict_data_saved and "mct_background_download" in dict_data_saved:
        config.set_setting("mct_background_download", dict_data_saved["mct_background_download"], server="torrent")
    if dict_data_saved and "mct_rar_unpack" in dict_data_saved:
        config.set_setting("mct_rar_unpack", dict_data_saved["mct_rar_unpack"], server="torrent")
    if dict_data_saved and "mct_download_limit" in dict_data_saved:
        config.set_setting("mct_download_limit", dict_data_saved["mct_download_limit"], server="torrent")
    if dict_data_saved and "bt_buffer" in dict_data_saved:
        config.set_setting("bt_buffer", dict_data_saved["bt_buffer"], server="torrent")
    if dict_data_saved and "bt_download_path" in dict_data_saved:
        config.set_setting("bt_download_path", dict_data_saved["bt_download_path"], server="torrent")
    if dict_data_saved and "magnet2torrent" in dict_data_saved:
        config.set_setting("magnet2torrent", dict_data_saved["magnet2torrent"], server="torrent")

def menu_servers(item):
    logger.info()
    itemlist = list()

    itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60550), action="servers_blacklist", folder=False,
                         thumbnail=get_thumb("setting_0.png")))

    itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60551),
                         action="servers_favorites", folder=False, thumbnail=get_thumb("setting_0.png")))

    itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60552),
                         action="", folder=False, text_bold = True, thumbnail=get_thumb("setting_0.png")))

    # Inicio - Servidores configurables

    server_list = servertools.get_debriders_list().keys()
    for server in server_list:
        server_parameters = servertools.get_server_parameters(server)
        if server_parameters["has_settings"]:
            itemlist.append(
                Item(channel=CHANNELNAME, title = ".    " + config.get_localized_string(60553) % server_parameters["name"],
                     action="server_config", config=server, folder=False, thumbnail=""))

    itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60554),
                         action="", folder=False, text_bold = True, thumbnail=get_thumb("setting_0.png")))

    server_list = servertools.get_servers_list().keys()

    for server in sorted(server_list):
        server_parameters = servertools.get_server_parameters(server)
        logger.info(server_parameters)
        if server_parameters["has_settings"] and filter(lambda x: x["id"] not in ["black_list", "white_list"],
                                                        server_parameters["settings"]):
            itemlist.append(
                Item(channel=CHANNELNAME, title=".    " + config.get_localized_string(60553) % server_parameters["name"],
                     action="server_config", config=server, folder=False, thumbnail=""))

    # Fin - Servidores configurables

    return itemlist


def server_config(item):
    return platformtools.show_channel_settings(channelpath=filetools.join(config.get_runtime_path(), "servers",
                                                                          item.config))


def servers_blacklist(item):
    server_list = servertools.get_servers_list()
    dict_values = {}

    list_controls = [{"id": "filter_servers",
                      "type": "bool",
                      "label": "@30068",
                      "default": False,
                      "enabled": True,
                      "visible": True}]
    dict_values['filter_servers'] = config.get_setting('filter_servers')
    if dict_values['filter_servers'] == None:
        dict_values['filter_servers'] = False
    for i, server in enumerate(sorted(server_list.keys())):
        server_parameters = server_list[server]
        controls, defaults = servertools.get_server_controls_settings(server)
        dict_values[server] = config.get_setting("black_list", server=server)

        control = {"id": server,
                   "type": "bool",
                   "label": '    %s' % server_parameters["name"],
                   "default": defaults.get("black_list", False),
                   "enabled": "eq(-%s,True)" % (i + 1),
                   "visible": True}
        list_controls.append(control)

    return platformtools.show_channel_settings(list_controls=list_controls, dict_values=dict_values,
                                               caption=config.get_localized_string(60550), callback="cb_servers_blacklist")


def cb_servers_blacklist(item, dict_values):
    f = False
    progreso = platformtools.dialog_progress(config.get_localized_string(60557), config.get_localized_string(60558))
    n = len(dict_values)
    i = 1
    for k, v in dict_values.items():
        if k == 'filter_servers':
            config.set_setting('filter_servers', v)
        else:
            config.set_setting("black_list", v, server=k)
            if v:  # Si el servidor esta en la lista negra no puede estar en la de favoritos
                config.set_setting("favorites_servers_list", 100, server=k)
                f = True
                progreso.update((i * 100) / n, config.get_localized_string(60559) % k)
        i += 1

    if not f:  # Si no hay ningun servidor en la lista, desactivarla
        config.set_setting('filter_servers', False)

    progreso.close()


def servers_favorites(item):
    server_list = servertools.get_servers_list()
    dict_values = {}

    list_controls = [{'id': 'favorites_servers',
                      'type': "bool",
                      'label': config.get_localized_string(60577),
                      'default': False,
                      'enabled': True,
                      'visible': True}]
    dict_values['favorites_servers'] = config.get_setting('favorites_servers')
    if dict_values['favorites_servers'] == None:
        dict_values['favorites_servers'] = False

    server_names = ['Ninguno']

    for server in sorted(server_list.keys()):
        if config.get_setting("black_list", server=server):
            continue

        server_names.append(server_list[server]['name'])

        orden = config.get_setting("favorites_servers_list", server=server)

        if orden > 0:
            dict_values[orden] = len(server_names) - 1

    for x in range(1, 6):
        control = {'id': x,
                   'type': "list",
                   'label': config.get_localized_string(60597) % x,
                   'lvalues': server_names,
                   'default': 0,
                   'enabled': "eq(-%s,True)" % x,
                   'visible': True}
        list_controls.append(control)

    return platformtools.show_channel_settings(list_controls=list_controls, dict_values=dict_values, item=server_names,
                                               caption=config.get_localized_string(60551), callback="cb_servers_favorites")


def cb_servers_favorites(server_names, dict_values):
    dict_name = {}
    progreso = platformtools.dialog_progress(config.get_localized_string(60557), config.get_localized_string(60558))

    for i, v in dict_values.items():
        if i == "favorites_servers":
            config.set_setting("favorites_servers", v)
        elif int(v) > 0:
            dict_name[server_names[v]] = int(i)

    servers_list = servertools.get_servers_list().items()
    n = len(servers_list)
    i = 1
    for server, server_parameters in servers_list:
        if server_parameters['name'] in dict_name.keys():
            config.set_setting("favorites_servers_list", dict_name[server_parameters['name']], server=server)
        else:
            config.set_setting("favorites_servers_list", 0, server=server)
        progreso.update((i * 100) / n, config.get_localized_string(60559) % server_parameters['name'])
        i += 1

    if not dict_name:  # Si no hay ningun servidor en lalista desactivarla
        config.set_setting("favorites_servers", False)

    progreso.close()


def settings(item):
    config.open_settings()


def submenu_tools(item):
    logger.info()
    itemlist = list()

    # Herramientas personalizadas
    import os
    channel_custom = os.path.join(config.get_runtime_path(), 'channels', 'custom.py')
    if not filetools.exists(channel_custom):
        user_custom = os.path.join(config.get_data_path(), 'custom.py')
        if filetools.exists(user_custom):
            filetools.copy(user_custom, channel_custom, silent=True)
    if filetools.exists(channel_custom):
        itemlist.append(Item(channel='custom', action='mainlist', title='Custom Channel'))


    itemlist.append(Item(channel=CHANNELNAME, action="check_quickfixes", folder=False,
                         title="Comprobar actualizaciones urgentes (Actual: Alfa %s)" %config.get_addon_version(), plot="Versión actual: %s" % config.get_addon_version() ))
    itemlist.append(Item(channel=CHANNELNAME, action="update_quasar", folder=False,
                         title="Actualizar addon externo Quasar"))
    itemlist.append(Item(channel=CHANNELNAME, action="", title="", folder=False,
                         thumbnail=get_thumb("setting_0.png")))

    itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60564) + ":", action="", folder=False,
                         text_bold=True, thumbnail=get_thumb("channels.png")))
    itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60565), action="conf_tools",
                         folder=True, extra="lib_check_datajson", thumbnail=get_thumb("channels.png")))

    if config.get_videolibrary_support():
        itemlist.append(Item(channel=CHANNELNAME, action="", title="", folder=False,
                             thumbnail=get_thumb("setting_0.png")))
        itemlist.append(Item(channel=CHANNELNAME, title=config.get_localized_string(60566) + ":", action="", folder=False,
                             text_bold=True, thumbnail=get_thumb("videolibrary.png")))
        itemlist.append(Item(channel=CHANNELNAME, action="overwrite_tools", folder=False,
                             thumbnail=get_thumb("videolibrary.png"),
                             title="- " + config.get_localized_string(60567)))
        itemlist.append(Item(channel="videolibrary", action="update_videolibrary", folder=False,
                             thumbnail=get_thumb("videolibrary.png"),
                             title="- " + config.get_localized_string(60568)))

    return itemlist


def check_quickfixes(item):
    logger.info()
    
    from platformcode import updater
    return updater.check_addon_updates(verbose=True)


def update_quasar(item):
    logger.info()
    
    from platformcode import custom_code, platformtools
    stat = False
    stat = custom_code.update_external_addon("quasar")
    if stat:
        platformtools.dialog_notification("Actualización Quasar", "Realizada con éxito")
    else:
        platformtools.dialog_notification("Actualización Quasar", "Ha fallado. Consulte el log")
    
    
def conf_tools(item):
    logger.info()

    # Activar o desactivar canales
    if item.extra == "channels_onoff":
        if config.get_platform(True)['num_version'] >= 17.0: # A partir de Kodi 16 se puede usar multiselect, y de 17 con preselect
            return channels_onoff(item)
        
        import channelselector
        from core import channeltools

        channel_list = channelselector.filterchannels("allchannelstatus")

        excluded_channels = ['url',
                             'search',
                             'videolibrary',
                             'setting',
                             'news',
                             # 'help',
                             'downloads']

        list_controls = []
        try:
            list_controls.append({'id': "all_channels",
                                  'type': "list",
                                  'label': config.get_localized_string(60594),
                                  'default': 0,
                                  'enabled': True,
                                  'visible': True,
                                  'lvalues': ['',
                                              config.get_localized_string(60591),
                                              config.get_localized_string(60592),
                                              config.get_localized_string(60593)]})

            for channel in channel_list:
                # Si el canal esta en la lista de exclusiones lo saltamos
                if channel.channel not in excluded_channels:

                    channel_parameters = channeltools.get_channel_parameters(channel.channel)

                    status_control = ""
                    status = config.get_setting("enabled", channel.channel)
                    # si status no existe es que NO HAY valor en _data.json
                    if status is None:
                        status = channel_parameters["active"]
                        logger.debug("%s | Status (XML): %s" % (channel.channel, status))
                        if not status:
                            status_control = config.get_localized_string(60595)
                    else:
                        logger.debug("%s  | Status: %s" % (channel.channel, status))

                    control = {'id': channel.channel,
                               'type': "bool",
                               'label': channel_parameters["title"] + status_control,
                               'default': status,
                               'enabled': True,
                               'visible': True}
                    list_controls.append(control)

                else:
                    continue

        except:
            import traceback
            logger.error("Error: %s" % traceback.format_exc())
        else:
            return platformtools.show_channel_settings(list_controls=list_controls,
                                                       item=item.clone(channel_list=channel_list),
                                                       caption=config.get_localized_string(60596),
                                                       callback="channel_status",
                                                       custom_button={"visible": False})

    # Comprobacion de archivos channel_data.json
    elif item.extra == "lib_check_datajson":
        itemlist = []
        import channelselector
        from core import channeltools
        channel_list = channelselector.filterchannels("allchannelstatus")

        # Tener una lista de exclusion no tiene mucho sentido por que se comprueba si channel.json tiene "settings",
        # pero por si acaso se deja
        excluded_channels = ['url',
                             'setting',
                             'help']

        try:
            import os
            from core import jsontools
            for channel in channel_list:

                list_status = None
                default_settings = None

                # Se comprueba si el canal esta en la lista de exclusiones
                if channel.channel not in excluded_channels:
                    # Se comprueba que tenga "settings", sino se salta
                    list_controls, dict_settings = channeltools.get_channel_controls_settings(channel.channel)

                    if not list_controls:
                        itemlist.append(Item(channel=CHANNELNAME,
                                             title=channel.title + config.get_localized_string(60569),
                                             action="", folder=False,
                                             thumbnail=channel.thumbnail))
                        continue
                        # logger.info(channel.channel + " SALTADO!")

                    # Se cargan los ajustes del archivo json del canal
                    file_settings = os.path.join(config.get_data_path(), "settings_channels",
                                                 channel.channel + "_data.json")
                    dict_settings = {}
                    dict_file = {}
                    if filetools.exists(file_settings):
                        # logger.info(channel.channel + " Tiene archivo _data.json")
                        channeljson_exists = True
                        # Obtenemos configuracion guardada de ../settings/channel_data.json
                        try:
                            dict_file = jsontools.load(open(file_settings, "rb").read())
                            if isinstance(dict_file, dict) and 'settings' in dict_file:
                                dict_settings = dict_file['settings']
                        except EnvironmentError:
                            logger.error("ERROR al leer el archivo: %s" % file_settings)
                    else:
                        # logger.info(channel.channel + " No tiene archivo _data.json")
                        channeljson_exists = False

                    if channeljson_exists:
                        try:
                            datajson_size = filetools.getsize(file_settings)
                        except:
                            import traceback
                            logger.error(channel.title + config.get_localized_string(60570) % traceback.format_exc())
                    else:
                        datajson_size = None

                    # Si el _data.json esta vacio o no existe...
                    if (len(dict_settings) and datajson_size) == 0 or not channeljson_exists:
                        # Obtenemos controles del archivo ../channels/channel.json
                        needsfix = True
                        try:
                            # Se cargan los ajustes por defecto
                            list_controls, default_settings = channeltools.get_channel_controls_settings(
                                channel.channel)
                            # logger.info(channel.title + " | Default: %s" % default_settings)
                        except:
                            import traceback
                            logger.error(channel.title + config.get_localized_string(60570) % traceback.format_exc())
                            # default_settings = {}

                        # Si _data.json necesita ser reparado o no existe...
                        if needsfix or not channeljson_exists:
                            if default_settings is not None:
                                # Creamos el channel_data.json
                                default_settings.update(dict_settings)
                                dict_settings = default_settings
                                dict_file['settings'] = dict_settings
                                # Creamos el archivo ../settings/channel_data.json
                                json_data = jsontools.dump(dict_file)
                                try:
                                    open(file_settings, "wb").write(json_data)
                                    # logger.info(channel.channel + " - Archivo _data.json GUARDADO!")
                                    # El channel_data.json se ha creado/modificado
                                    list_status = config.get_localized_string(60560)
                                except EnvironmentError:
                                    logger.error("ERROR al salvar el archivo: %s" % file_settings)
                            else:
                                if default_settings is None:
                                    list_status = config.get_localized_string(60571)

                    else:
                        # logger.info(channel.channel + " - NO necesita correccion!")
                        needsfix = False

                    # Si se ha establecido el estado del canal se añade a la lista
                    if needsfix is not None:
                        if needsfix:
                            if not channeljson_exists:
                                list_status = config.get_localized_string(60588)
                                list_colour = "red"
                            else:
                                list_status = config.get_localized_string(60589)
                                list_colour = "green"
                        else:
                            # Si "needsfix" es "false" y "datjson_size" es None habra
                            # ocurrido algun error
                            if datajson_size is None:
                                list_status = config.get_localized_string(60590)
                                list_colour = "red"
                            else:
                                list_status = config.get_localized_string(60589)
                                list_colour = "green"

                    if list_status is not None:
                        itemlist.append(Item(channel=CHANNELNAME,
                                             title=channel.title + list_status,
                                             action="", folder=False,
                                             thumbnail=channel.thumbnail,
                                             text_color=list_colour))
                    else:
                        logger.error("Algo va mal con el canal %s" % channel.channel)

                # Si el canal esta en la lista de exclusiones lo saltamos
                else:
                    continue
        except:
            import traceback
            logger.error("Error: %s" % traceback.format_exc())

        return itemlist


def channels_onoff(item):
    import channelselector, xbmcgui
    from core import channeltools

    # Cargar lista de opciones
    # ------------------------
    lista = []; ids = []
    channels_list = channelselector.filterchannels('allchannelstatus')
    for channel in channels_list:
        channel_parameters = channeltools.get_channel_parameters(channel.channel)
        lbl = '%s' % channel_parameters['language']
        # ~ lbl += ' %s' % [config.get_localized_category(categ) for categ in channel_parameters['categories']]
        lbl += ' %s' % ', '.join(config.get_localized_category(categ) for categ in channel_parameters['categories'])

        it = xbmcgui.ListItem(channel.title, lbl)
        it.setArt({ 'thumb': channel.thumbnail, 'fanart': channel.fanart })
        lista.append(it)
        ids.append(channel.channel)

    # Diálogo para pre-seleccionar
    # ----------------------------
    preselecciones = [config.get_localized_string(70517), config.get_localized_string(70518), config.get_localized_string(70519)]
    ret = platformtools.dialog_select(config.get_localized_string(60545), preselecciones)
    if ret == -1: return False # pedido cancel
    if ret == 2: preselect = []
    elif ret == 1: preselect = range(len(ids))
    else:
        preselect = []
        for i, canal in enumerate(ids):
            channel_status = config.get_setting('enabled', canal)
            if channel_status is None: channel_status = True
            if channel_status:
                preselect.append(i)

    # Diálogo para seleccionar
    # ------------------------
    ret = xbmcgui.Dialog().multiselect(config.get_localized_string(60545), lista, preselect=preselect, useDetails=True)
    if ret == None: return False # pedido cancel
    seleccionados = [ids[i] for i in ret]

    # Guardar cambios en canales activados
    # ------------------------------------
    for canal in ids:
        channel_status = config.get_setting('enabled', canal)
        if channel_status is None: channel_status = True

        if channel_status and canal not in seleccionados:
            config.set_setting('enabled', False, canal)
        elif not channel_status and canal in seleccionados:
            config.set_setting('enabled', True, canal)

    return False


def channel_status(item, dict_values):
    try:
        for k in dict_values:

            if k == "all_channels":
                logger.info("Todos los canales | Estado seleccionado: %s" % dict_values[k])
                if dict_values[k] != 0:
                    excluded_channels = ['url', 'search',
                                         'videolibrary', 'setting',
                                         'news',
                                         'help',
                                         'downloads']

                    for channel in item.channel_list:
                        if channel.channel not in excluded_channels:
                            from core import channeltools
                            channel_parameters = channeltools.get_channel_parameters(channel.channel)
                            new_status_all = None
                            new_status_all_default = channel_parameters["active"]

                            # Opcion Activar todos
                            if dict_values[k] == 1:
                                new_status_all = True

                            # Opcion Desactivar todos
                            if dict_values[k] == 2:
                                new_status_all = False

                            # Opcion Recuperar estado por defecto
                            if dict_values[k] == 3:
                                # Si tiene "enabled" en el _data.json es porque el estado no es el del channel.json
                                if config.get_setting("enabled", channel.channel):
                                    new_status_all = new_status_all_default

                                # Si el canal no tiene "enabled" en el _data.json no se guarda, se pasa al siguiente
                                else:
                                    continue

                            # Se guarda el estado del canal
                            if new_status_all is not None:
                                config.set_setting("enabled", new_status_all, channel.channel)
                    break
                else:
                    continue

            else:
                logger.info("Canal: %s | Estado: %s" % (k, dict_values[k]))
                config.set_setting("enabled", dict_values[k], k)
                logger.info("el valor esta como %s " % config.get_setting("enabled", k))

        platformtools.itemlist_update(Item(channel=CHANNELNAME, action="mainlist"))

    except:
        import traceback
        logger.error("Detalle del error: %s" % traceback.format_exc())
        platformtools.dialog_notification(config.get_localized_string(60579), config.get_localized_string(60580))


def overwrite_tools(item):
    import videolibrary_service
    from core import videolibrarytools

    seleccion = platformtools.dialog_yesno(config.get_localized_string(60581),
                                           config.get_localized_string(60582),
                                           config.get_localized_string(60583))
    if seleccion == 1:
        # tvshows
        heading = config.get_localized_string(60584)
        p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(60585), heading)
        p_dialog.update(0, '')

        show_list = []
        for path, folders, files in filetools.walk(videolibrarytools.TVSHOWS_PATH):
            show_list.extend([filetools.join(path, f) for f in files if f == "tvshow.nfo"])

        if show_list:
            t = float(100) / len(show_list)

        for i, tvshow_file in enumerate(show_list):
            head_nfo, serie = videolibrarytools.read_nfo(tvshow_file)
            path = filetools.dirname(tvshow_file)

            if not serie.active:
                # si la serie no esta activa descartar
                continue

            # Eliminamos la carpeta con la serie ...
            filetools.rmdirtree(path)

            # ... y la volvemos a añadir
            videolibrary_service.update(path, p_dialog, i, t, serie, 3)
        p_dialog.close()

        # movies
        heading = config.get_localized_string(60586)
        p_dialog2 = platformtools.dialog_progress_bg(config.get_localized_string(60585), heading)
        p_dialog2.update(0, '')

        movies_list = []
        for path, folders, files in filetools.walk(videolibrarytools.MOVIES_PATH):
            movies_list.extend([filetools.join(path, f) for f in files if f.endswith(".json")])

        logger.debug("movies_list %s" % movies_list)

        if movies_list:
            t = float(100) / len(movies_list)

        for i, movie_json in enumerate(movies_list):
            try:
                from core import jsontools
                path = filetools.dirname(movie_json)
                movie = Item().fromjson(filetools.read(movie_json))

                # Eliminamos la carpeta con la pelicula ...
                filetools.rmdirtree(path)

                import math
                heading = config.get_localized_string(60587)

                p_dialog2.update(int(math.ceil((i + 1) * t)), heading, "%s: %s" % (movie.contentTitle,
                                                                                   movie.channel.capitalize()))
                # ... y la volvemos a añadir
                videolibrarytools.save_movie(movie)
            except Exception, ex:
                logger.error("Error al crear de nuevo la película")
                template = "An exception of type %s occured. Arguments:\n%r"
                message = template % (type(ex).__name__, ex.args)
                logger.error(message)

        p_dialog2.close()

        
def report_menu(item):
    logger.info('URL: ' + item.url)
    
    from channelselector import get_thumb
    
    thumb_debug = get_thumb("update.png")
    thumb_error = get_thumb("error.png")
    thumb_next = get_thumb("next.png")
    itemlist = []
    paso = 1

    # Crea un menú de opciones para permitir al usuario reportar un fallo de Alfa a través de un servidor "pastebin"
    # Para que el informe sea completo el usuario debe tener la opción de DEBUG=ON
    # Los servidores "pastbin" gratuitos tienen limitación de capacidad, por lo que el tamaño del log es importante
    # Al final de la operación de upload, se pasa al usuario la dirección de log en el servidor para que los reporte
    
    itemlist.append(Item(channel=item.channel, action="", title="[COLOR gold]SIGA los siguiente PASOS:[/COLOR]", 
                thumbnail=thumb_next, folder=False))
    #if not config.get_setting('debug'):
    itemlist.append(Item(channel=item.channel, action="activate_debug", extra=True, 
                    title="PASO %s: Active DEBUG aquí antes de generar el log" % 
                    str(paso), thumbnail=thumb_debug, folder=False))
    paso += 1
    itemlist.append(Item(channel="channelselector", action="getmainlist", 
                    title="PASO %s: Reproduzca el problema y vuelva al PASO %s" % 
                    (str(paso), str(paso+1)), thumbnail=thumb_debug, folder=False))
    paso += 1
    itemlist.append(Item(channel=item.channel, action="report_send", 
                    title="PASO %s: Genere el informe de FALLO desde aquí" % 
                    str(paso), thumbnail=thumb_error))
    paso += 1
    #if config.get_setting('debug'):
    itemlist.append(Item(channel=item.channel, action="activate_debug", extra=False, 
                    title="PASO %s: Desactive DEBUG aquí -opcional-" % str(paso), 
                    thumbnail=thumb_debug, folder=False))
    paso += 1
    
    if item.url:
        itemlist.append(Item(channel=item.channel, action="", title="", folder=False))
    
        itemlist.append(Item(channel=item.channel, action="", 
                    title="[COLOR limegreen]Ha terminado de generar el informe de fallo,[/COLOR]", 
                    thumbnail=thumb_next, folder=False))
        itemlist.append(Item(channel=item.channel, action="", 
                    title="[COLOR limegreen]Repórtelo en el Foro de Alfa: [/COLOR][COLOR yellow](pinche si Chrome)[/COLOR]", 
                    thumbnail=thumb_next, 
                    folder=False))        
        itemlist.append(Item(channel=item.channel, action="call_chrome", 
                    url='https://alfa-addon.com/foros/ayuda.12/', 
                    title="**- [COLOR yellow]https://alfa-addon.com/foros/ayuda.12/[/COLOR] -**", 
                    thumbnail=thumb_next, unify=False, folder=False))
    
        if item.one_use:
            action = ''
            url = ''
        else:
            action = 'call_chrome'
            url = item.url
        itemlist.append(Item(channel=item.channel, action=action, 
                    title="**- LOG: [COLOR gold]%s[/COLOR] -**" % item.url, url=url, 
                    thumbnail=thumb_next, unify=False, folder=False))
        
        if item.one_use:
            itemlist.append(Item(channel=item.channel, action="", 
                    title="[COLOR orange]NO ACCEDA al INFORME: se BORRARÁ[/COLOR]", 
                    thumbnail=thumb_next, folder=False))
            itemlist.append(Item(channel=item.channel, action="", 
                    title="[COLOR orange]ya que es de un solo uso[/COLOR]", 
                    thumbnail=thumb_next, folder=False))
    
    return itemlist
    
    
def activate_debug(item):
    logger.info(item.extra)
    from platformcode import platformtools
    
    # Activa/Desactiva la opción de DEBUB en settings.xml
    
    if isinstance(item.extra, str):
        return report_menu(item)
    if item.extra:
        config.set_setting('debug', True)
        platformtools.dialog_notification('Modo DEBUG', 'Activado')
    else:
        config.set_setting('debug', False)
        platformtools.dialog_notification('Modo DEBUG', 'Desactivado')
        
        
def report_send(item, description='', fatal=False):
    import xbmc
    import xbmcaddon
    import random
    import urllib
    import urlparse
    import traceback
    import sys
    import platform
    import os
    import re

    try:
        requests_status = True
        import requests
    except:
        requests_status = False
        logger.error(traceback.format_exc())
    
    from core import jsontools, httptools, proxytools, scrapertools
    from platformcode import envtal
    
    # Esta función realiza la operación de upload del LOG.  El tamaño del archivo es de gran importacia porque
    # los servicios de "pastebin" gratuitos tienen limitaciones, a veces muy bajas.
    # Hay un ervicio, File.io, que permite subida directa de "achivos binarios" a través de la función "request"
    # Esto aumenta dráticamente la capacidad del envío del log, muy por encima de lo necesitado
    # Por ello es necesario contar con una lista de servicios "pastebin" que puedan realizar la operación de upload,
    # ya sea por capacidad disponible o por disponibilidad.
    # Para poder usar los servidores "pastebin" con un código común, se ha creado un diccionario con los servidores
    # y sus características.  En cada entrada se recogen las peculiaridades de cada servidor, tanto para formar
    # la petición consu POST como para la forma de recibir el código del upload en la respuesta (json, header, regex
    # en datos,...).
    # Al iniciar este método se aleatoriza la lista de servidores "pastebin" para evitar que todos los usuarios hagan 
    # uploads contra el mismo servidor y puedan ocasionar sobrecargas.
    # Se lee el arcivo de log y se compara su tamaño con la capacidad del servidor (parámetro 10 de cada entrada 
    # (empezando desde 0), expresado en MB, hasta que se encuentra uno capacitado.  Si el upload falla se sigue intentado
    # con los siguientes servidores que tengan la capacidad requerida.  
    # Si no se encuentra ningun servidor disponible se pide al usuario que lo intente más tarde, o que suba el log
    # directamente en el foro.  Si es un problema de tamaño, se le pide que reicinie Kodi y reporducza el fallo, para
    # que el LOG sea más pequeño.
    
    
    pastebin_list = {
    'hastebin': ('1', 'https://hastebin.com/', 'documents', 'random', '', '', 
                'data', 'json', 'key', '', '0.29', '10', True, 'raw/', '', ''), 
    'dpaste': ('1', 'http://dpaste.com/', 'api/v2/', 'random', 'content=', 
                '&syntax=text&title=%s&poster=alfa&expiry_days=7', 
                'headers', '', '', 'location', '0.23', '15', True, '', '.txt', ''),
    'ghostbin': ('1', 'https://ghostbin.com/', 'paste/new', 'random', 'lang=text&text=', 
                '&expire=2d&password=&title=%s', 
                'data', 'regex', '<title>(.*?)\s*-\s*Ghostbin<\/title>', '', 
                '0.49', '15', False, 'paste/', '', ''),
    'write.as': ('1', 'https://write.as/', 'api/posts', 'random', 'body=', '&title=%s', 
                'data', 'json', 'data', 'id', '0.018', '15', True, '', '', ''),
    'oneclickpaste': ('1', 'http://oneclickpaste.com/', 'index.php', 'random', 'paste_data=', 
                '&title=%s&format=text&paste_expire_date=1W&visibility=0&pass=&submit=Submit', 
                'data', 'regex', '<a class="btn btn-primary" href="[^"]+\/(\d+\/)">\s*View\s*Paste\s*<\/a>', 
                '', '0.060', '5', True, '', '', ''),
    'bpaste': ('1', 'https://bpaste.net/', '', 'random', 'code=', '&lexer=text&expiry=1week', 
                'data', 'regex', 'View\s*<a\s*href="[^*]+/(.*?)">raw<\/a>', '', 
                '0.79', '15', True, 'raw/', '', ''),
    'dumpz': ('0', 'http://dumpz.org/', 'api/dump', 'random', 'code=', '&lexer=text&comment=%s&password=', 
                'headers', '', '', 'location', '0.99', '15', False, '', '', ''),
    'file.io': ('1', 'https://file.io/', '', 'random', '', 'expires=1w', 
                'requests', 'json', 'key', '', '99.0', '30', False, '', '.log', ''), 
    'uploadfiles': ('1', 'https://up.uploadfiles.io/upload', '', 'random', '', '', 
                'requests', 'json', 'url', '', '99.0', '30', False, None, '', '') 
                 }
    pastebin_list_last = ['hastebin', 'ghostbin', 'file.io']            # Estos servicios los dejamos los últimos
    pastebin_one_use = ['file.io']                                      # Servidores de un solo uso y se borra
    pastebin_dir = []
    paste_file = {}
    paste_params = ()
    paste_post = ''
    status = False
    msg = 'Servicio no disponible.  Inténtelo más tarde'
    
    # Se verifica que el DEBUG=ON, si no está se rechaza y se pide al usuario que lo active y reproduzca el fallo
    if not config.get_setting('debug'):
        platformtools.dialog_notification('DEBUG debe estar ACTIVO', 'antes de generar el informe')
        return report_menu(item)
    
    # De cada al futuro se permitira al usuario que introduzca una breve descripción del fallo que se añadirá al LOG
    if description == 'OK':
        description = platformtools.dialog_input('', 'Introduzca una breve descripción del fallo')

    # Escribimos en el log algunas variables de Kodi y Alfa que nos ayudarán en el diagnóstico del fallo
    var = proxytools.logger_disp(debugging=True)
    environment = envtal.list_env()
    if not environment['log_path']:
        environment['log_path'] = str(filetools.join(xbmc.translatePath("special://logpath/"), 'kodi.log'))
        environment['log_size_bytes'] = str(filetools.getsize(environment['log_path']))
        environment['log_size'] = str(round(float(environment['log_size_bytes']) / (1024*1024), 3))
    
    # Se lee el archivo de LOG
    log_path = environment['log_path']
    if filetools.exists(log_path):
        log_size_bytes = int(environment['log_size_bytes'])             # Tamaño del archivivo en Bytes
        log_size = float(environment['log_size'])                       # Tamaño del archivivo en MB
        log_data = filetools.read(log_path)                             # Datos del archivo
        if not log_data:                                                # Algún error?
            platformtools.dialog_notification('No puede leer el log de Kodi', 'Comuniquelo directamente en el Foro de Alfa')
            return report_menu(item)
    else:                                                               # Log no existe o path erroneo?
        platformtools.dialog_notification('LOG de Kodi no encontrado', 'Comuniquelo directamente en el Foro de Alfa')
        return report_menu(item)

    # Si se ha introducido la descripción del fallo, se inserta la principio de los datos del LOG
    log_title = '***** DESCRIPCIÓN DEL FALLO *****'
    if description:
        log_data = '%s\n%s\n\n%s' %(log_title, description, log_data)
    
    # Se aleatorizan los nombre de los servidores "patebin"
    for label_a, value_a in pastebin_list.items():
        if label_a not in pastebin_list_last:
            pastebin_dir.append(label_a)
    random.shuffle(pastebin_dir)
    pastebin_dir.extend(pastebin_list_last)                             # Estos servicios los dejamos los últimos
    
    #pastebin_dir = ['file.io']                                          # Para pruebas de un servicio
        
    # Se recorre la lista de servidores "pastebin" hasta localizar uno activo, con capacidad y disponibilidad
    for paste_name in pastebin_dir:
        if pastebin_list[paste_name][0] != '1':                         # Si no esta activo el servidore, pasamos
            continue
        if pastebin_list[paste_name][6] == 'requests' and not requests_status:  # Si "requests" no esta activo, pasamos
            continue

        paste_host = pastebin_list[paste_name][1]                       # URL del servidor "pastebin"
        paste_sufix = pastebin_list[paste_name][2]                      # sufijo del API para el POST
        paste_title = ''
        if pastebin_list[paste_name][3] == 'random':
            paste_title = "LOG" + str(random.randrange(1, 999999999))   # Título del LOG
        paste_post1 = pastebin_list[paste_name][4]                      # Parte inicial del POST
        paste_post2 = pastebin_list[paste_name][5]                      # Parte secundaria del POST
        paste_type = pastebin_list[paste_name][6]                       # Tipo de downloadpage: DATA o HEADERS
        paste_resp = pastebin_list[paste_name][7]                       # Tipo de respuesta: JSON o datos con REGEX
        paste_resp_key = pastebin_list[paste_name][8]                   # Si es JSON, etiqueta `primaria con la CLAVE
        paste_url = pastebin_list[paste_name][9]                        # Etiqueta primaria para HEADER y sec. para JSON
        paste_file_size = float(pastebin_list[paste_name][10])          # Capacidad en MB del servidor
        if paste_file_size > 0:                                         # Si es 0, la capacidad es ilimitada
            if log_size > paste_file_size:                              # Verificación de capacidad y tamaño
                msg = 'Archivo de log demasiado grande.  Reinicie Kodi y reinténtelo'
                continue
        paste_timeout = int(pastebin_list[paste_name][11])              # Timeout para el servidor
        paste_random_headers = pastebin_list[paste_name][12]            # Utiliza RAMDOM headers para despistar el serv.?
        paste_host_return = pastebin_list[paste_name][13]               # Parte de url para componer la clave para usuario
        paste_host_return_tail = pastebin_list[paste_name][14]          # Sufijo de url para componer la clave para usuario
        paste_headers = {}
        if pastebin_list[paste_name][15]:                               # Headers requeridas por el servidor
            paste_headers.update(jsontools.load((pastebin_list[paste_name][15])))

        if paste_name in pastebin_one_use:
            pastebin_one_use_msg = '[COLOR red]NO ACCEDA al INFORME: se BORRARÁ[/COLOR]'
            item.one_use = True
        else:
            pastebin_one_use_msg = ''
        
        try:
            # Se crea el POST con las opciones del servidor "pastebin"
            # Se trata el formato de "requests"
            if paste_type == 'requests':
                paste_file = {'file': (paste_title+'.log', log_data)}
                if paste_post1:
                    paste_file.update(paste_post1)
                if paste_post2:
                    if '%s' in paste_post2:
                        paste_params = paste_post2 % (paste_title+'.log', log_size_bytes)
                    else:
                        paste_params = paste_post2
            
            #Se trata el formato de downloads
            else:
                #log_data = 'Test de Servidor para ver su viabilidad (áéíóúñ¿?)'
                if paste_name in ['hastebin']:                              # Hay algunos servicios que no necesitan "quote"
                    paste_post = log_data
                else:
                    paste_post = urllib.quote_plus(log_data)                # Se hace un "quote" de los datos del LOG
                if paste_post1:
                    paste_post = '%s%s' % (paste_post1, paste_post)
                if paste_post2:
                    if '%s' in paste_post2:
                        paste_post += paste_post2 % paste_title
                    else:
                        paste_post += paste_post2

            # Se hace la petición en downloadpage con HEADERS o DATA, con los parámetros del servidor
            if paste_type == 'headers':
                data = httptools.downloadpage(paste_host+paste_sufix, post=paste_post, 
                            timeout=paste_timeout, random_headers=paste_random_headers, 
                            headers=paste_headers).headers
            elif paste_type == 'data':
                data = httptools.downloadpage(paste_host+paste_sufix, post=paste_post, 
                            timeout=paste_timeout, random_headers=paste_random_headers, 
                            headers=paste_headers).data
            
            # Si la petición es con formato REQUESTS, se realiza aquí
            elif paste_type == 'requests':
                #data = requests.post(paste_host, params=paste_params, files=paste_file, 
                #            timeout=paste_timeout)
                data = httptools.downloadpage(paste_host, params=paste_params, file=log_data, 
                            file_name=paste_title+'.log', timeout=paste_timeout, 
                            random_headers=paste_random_headers, headers=paste_headers)
        except:
            msg = 'Inténtelo más tarde'
            logger.error('Fallo al guardar el informe. ' + msg)
            logger.error(traceback.format_exc())
            continue

        # Se analiza la respuesta del servidor y se localiza la clave del upload para formar la url a pasar al usuario
        if data:
            paste_host_resp = paste_host
            if paste_host_return == None:                               # Si devuelve la url completa, no se compone
                paste_host_resp = ''
                paste_host_return = ''
            
            # Respuestas a peticiones REQUESTS
            if paste_type == 'requests':                                # Respuesta de petición tipo "requests"?
                if paste_resp == 'json':                                                # Respuesta en formato JSON?
                    if paste_resp_key in data.data:
                        if not paste_url:
                            key = jsontools.load(data.data)[paste_resp_key]             # con una etiqueta
                        else:
                            key = jsontools.load(data.data)[paste_resp_key][paste_url]  # con dos etiquetas anidadas
                        item.url = "%s%s%s" % (paste_host_resp+paste_host_return, key, 
                                    paste_host_return_tail)
                    else:
                        logger.error('ERROR en formato de retorno de datos. data.data=' + 
                                    str(data.data))
                        continue
            
            # Respuestas a peticiones DOWNLOADPAGE
            elif paste_resp == 'json':                                  # Respuesta en formato JSON?
                if paste_resp_key in data:
                    if not paste_url:
                        key = jsontools.load(data)[paste_resp_key]      # con una etiqueta
                    else:
                        key = jsontools.load(data)[paste_resp_key][paste_url]   # con dos etiquetas anidadas
                    item.url = "%s%s%s" % (paste_host_resp+paste_host_return, key, 
                                    paste_host_return_tail)
                else:
                    logger.error('ERROR en formato de retorno de datos. data=' + str(data))
                    continue
            elif paste_resp == 'regex':                                 # Respuesta en DATOS, a buscar con un REGEX?
                key = scrapertools.find_single_match(data, paste_resp_key)
                if key:
                    item.url = "%s%s%s" % (paste_host_resp+paste_host_return, key, 
                                    paste_host_return_tail)
                else:
                    logger.error('ERROR en formato de retorno de datos. data=' + str(data))
                    continue
            elif paste_type == 'headers':                               # Respuesta en HEADERS, a buscar en "location"?
                if paste_url in data:
                    item.url = data[paste_url]                          # Etiqueta de retorno de la clave
                    item.url =  urlparse.urljoin(paste_host_resp + paste_host_return, 
                                    item.url + paste_host_return_tail)
                else:
                    logger.error('ERROR en formato de retorno de datos. response.headers=' + 
                                    str(data))
                    continue
            else:
                logger.error('ERROR en formato de retorno de datos. paste_type=' + 
                                    str(paste_type) + ' / DATA: ' + data)
                continue

            status = True                                               # Operación de upload terminada con éxito
            logger.info('Informe de Fallo en Alfa CREADO: ' + str(item.url))    #Se guarda la URL del informe a usuario
            if fatal:                                                   # De uso futuro, para logger.crash
                platformtools.dialog_ok('Informe de ERROR en Alfa CREADO', 'Repórtelo en el foro agregando ERROR FATAL y esta URL: ', '[COLOR gold]%s[/COLOR]' % item.url, pastebin_one_use_msg)
            else:                                                       # Se pasa la URL del informe a usuario
                platformtools.dialog_ok('Informe de Fallo en Alfa CREADO', 'Repórtelo en el foro agregando una descripcion del fallo y esta URL: ', '[COLOR gold]%s[/COLOR]' % item.url, pastebin_one_use_msg)

            break                                                       # Operación terminado, no seguimos buscando
    
    if not status and not fatal:                                        # Operación fracasada...
        platformtools.dialog_notification('Fallo al guardar el informe', msg)   #... se notifica la causa
        logger.error('Fallo al guardar el informe. ' + msg)
    
    # Se devuelve control con item.url actualizado, así aparecerá en el menú la URL del informe
    return report_menu(item)
    
    
def call_chrome(item):
    from lib import generictools

    resultado = generictools.call_chrome(item.url)
    
    return resultado