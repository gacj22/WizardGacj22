# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Distributed under the terms of GNU General Public License v3 (GPLv3)
# http://www.gnu.org/licenses/gpl-3.0.html
# ------------------------------------------------------------
# Parámetros de configuración (kodi)
# ------------------------------------------------------------

import os

import xbmc
import xbmcaddon

PLATFORM_NAME = "kodi"
OLD_PLATFORM = False
PLUGIN_NAME = "deportesalacarta"

__settings__ = xbmcaddon.Addon(id="plugin.video." + PLUGIN_NAME)
__language__ = __settings__.getLocalizedString


def get_platform():
    return PLATFORM_NAME


def get_system_platform():
    """ fonction: pour recuperer la platform que xbmc tourne """
    import xbmc
    platform = "unknown"
    if xbmc.getCondVisibility("system.platform.linux"):
        platform = "linux"
    elif xbmc.getCondVisibility("system.platform.xbox"):
        platform = "xbox"
    elif xbmc.getCondVisibility("system.platform.windows"):
        platform = "windows"
    elif xbmc.getCondVisibility("system.platform.osx"):
        platform = "osx"
    return platform


def open_settings():
    __settings__.openSettings()


def get_setting(name, channel=""):
    """
    Retorna el valor de configuracion del parametro solicitado.

    Devuelve el valor del parametro 'name' en la configuracion global o en la configuracion propia del canal 'channel'.

    Si se especifica el nombre del canal busca en la ruta \addon_data\plugin.video.pelisalacarta\settings_channels el
    archivo channel_data.json y lee el valor del parametro 'name'. Si el archivo channel_data.json no existe busca en la
     carpeta channels el archivo channel.xml y crea un archivo channel_data.json antes de retornar el valor solicitado.
    Si el parametro 'name' no existe en channel_data.json lo busca en la configuracion global y si ahi tampoco existe
    devuelve un str vacio.

    Parametros:
    name -- nombre del parametro
    channel [opcional] -- nombre del canal

    Retorna:
    value -- El valor del parametro 'name'

    """
    # xbmc.log("config.get_setting name="+name+", channel="+channel+", OLD_PLATFORM="+str(OLD_PLATFORM))

    # Specific channel setting
    if channel:

        # Old platforms read settings from settings-oldplatform.xml, all but the "include_in_global_search", "include_in_newest..."
        if OLD_PLATFORM and ("user" in name or "password" in name):
            # xbmc.log("config.get_setting reading channel setting from main xml '"+channel+"_"+name+"'")
            value = __settings__.getSetting(channel+"_"+name)
            # xbmc.log("config.get_setting -> '"+value+"'")
            return value

        # New platforms read settings from each channel
        else:
            # xbmc.log("config.get_setting reading channel setting '"+name+"' from channel xml")
            from core import channeltools
            value = channeltools.get_channel_setting(name, channel)
            # xbmc.log("config.get_setting -> '"+repr(value)+"'")

            if value is not None:
                return value
            else:
                return ""

    # Global setting
    else:
        # xbmc.log("config.get_setting reading main setting '"+name+"'")
        value = __settings__.getSetting(channel+name)
        if value.startswith("special://"):
            value = xbmc.translatePath(value)
        # xbmc.log("config.get_setting -> '"+value+"'")
        return value


def set_setting(name,value, channel=""):
    """
    Fija el valor de configuracion del parametro indicado.

    Establece 'value' como el valor del parametro 'name' en la configuracion global o en la configuracion propia del
    canal 'channel'.
    Devuelve el valor cambiado o None si la asignacion no se ha podido completar.

    Si se especifica el nombre del canal busca en la ruta \addon_data\plugin.video.pelisalacarta\settings_channels el
    archivo channel_data.json y establece el parametro 'name' al valor indicado por 'value'. Si el archivo
    channel_data.json no existe busca en la carpeta channels el archivo channel.xml y crea un archivo channel_data.json
    antes de modificar el parametro 'name'.
    Si el parametro 'name' no existe lo añade, con su valor, al archivo correspondiente.


    Parametros:
    name -- nombre del parametro
    value -- valor del parametro
    channel [opcional] -- nombre del canal

    Retorna:
    'value' en caso de que se haya podido fijar el valor y None en caso contrario

    """
    if channel:
        from core import channeltools
        return channeltools.set_channel_setting(name, value, channel)
    else:
        try:
            __settings__.setSetting(name, value)
        except:
            # xbmc.log("[config.py] ERROR al fijar el parametro global {0}= {1}".format(name, value))
            return None

        return value


def get_localized_string(code):
    dev = __language__(code)

    try:
        dev = dev.encode("utf-8")
    except:
        pass

    return dev


def get_library_path():
    if get_system_platform() == "xbox":
        default = xbmc.translatePath(os.path.join(get_runtime_path(), "matchcenter"))
    else:
        default = xbmc.translatePath("special://profile/addon_data/plugin.video." +
                                     PLUGIN_NAME + "/matchcenter")

    return default


def get_temp_file(filename):
    return xbmc.translatePath(os.path.join("special://temp/", filename))


def get_runtime_path():
    return xbmc.translatePath(__settings__.getAddonInfo('Path'))


def get_data_path():
    dev = xbmc.translatePath(__settings__.getAddonInfo('Profile'))

    # Parche para XBMC4XBOX
    if not os.path.exists(dev):
        os.makedirs(dev)

    return dev


def get_cookie_data():
    import os
    ficherocookies = os.path.join(get_data_path(), 'cookies.dat')

    cookiedatafile = open(ficherocookies, 'r')
    cookiedata = cookiedatafile.read()
    cookiedatafile.close()

    return cookiedata

# Test if all the required directories are created
def verify_directories_created():
    import logger

    from core import filetools

    # Force download path if empty
    download_path = get_setting("downloadpath")
    if download_path == "":
        if is_xbmc():
            download_path = "special://profile/addon_data/plugin.video." + PLUGIN_NAME + "/downloads"
        else:
            download_path = filetools.join(get_data_path(), "downloads")

        set_setting("downloadpath", download_path)

    # Force download list path if empty
    download_list_path = get_setting("downloadlistpath")
    if download_list_path == "":
        if is_xbmc():
            download_list_path = "special://profile/addon_data/plugin.video." + PLUGIN_NAME + "/downloads/list"
        else:
            download_list_path = filetools.join(get_data_path(), "downloads", "list")

        set_setting("downloadlistpath", download_list_path)

    # Force bookmark path if empty
    bookmark_path = get_setting("bookmarkpath")
    if bookmark_path == "":
        if is_xbmc():
            bookmark_path = "special://profile/addon_data/plugin.video." + PLUGIN_NAME + "/downloads/list"
        else:
            bookmark_path = filetools.join(get_data_path(), "bookmarks")

        set_setting("bookmarkpath", bookmark_path)

    # Create data_path if not exists
    if not os.path.exists(get_data_path()):
        logger.debug("Creating data_path " + get_data_path())

        filetools.mkdir(get_data_path())

    if is_xbmc():
        # xbmc.log("Es una plataforma XBMC")
        if download_path.startswith("special://"):
            # Translate from special and create download_path if not exists
            download_path = xbmc.translatePath(download_path)
            texto = "(from special)"
        else:
            texto = ""

        # TODO si tiene smb se debería poder dejar que cree? filetools permite crear carpetas para SMB
        if not download_path.lower().startswith("smb") and not filetools.exists(download_path):
            logger.debug("Creating download_path" + texto + ": " + download_path)
            filetools.mkdir(download_path)

        if download_list_path.startswith("special://"):
            # Create download_list_path if not exists
            download_list_path = xbmc.translatePath(download_list_path)
            texto = "(from special)"
        else:
            texto = ""

        # TODO si tiene smb se debería poder dejar que cree? filetools permite crear carpetas para SMB
        if not download_list_path.lower().startswith("smb") and not filetools.exists(download_list_path):
            logger.debug("Creating download_list_path" + texto + ": " + download_list_path)
            filetools.mkdir(download_list_path)

        if bookmark_path.startswith("special://"):
            # Create bookmark_path if not exists
            bookmark_path = xbmc.translatePath(bookmark_path)
            texto = "(from special)"
        else:
            texto = ""

        # TODO si tiene smb se debería poder dejar que cree? filetools permite crear carpetas para SMB
        if not bookmark_path.lower().startswith("smb") and not filetools.exists(bookmark_path):
            logger.debug("Creating bookmark_path" + texto + ": " + bookmark_path)
            filetools.mkdir(bookmark_path)

    # Create settings_path is not exists
    settings_path = filetools.join(get_data_path(), "settings_channels")
    if not filetools.exists(settings_path):
        logger.debug("Creating settings_path " + settings_path)
        filetools.mkdir(settings_path)

    # Checks that a directory "xbmc" is not present on platformcode
    old_xbmc_directory = os.path.join(get_runtime_path(), "platformcode", "xbmc")
    if os.path.exists(old_xbmc_directory):
        logger.debug("Removing old platformcode.xbmc directory")
        filetools.rmdirtree(old_xbmc_directory)

    # Create library is not exists
    matchcenter_path = get_library_path()
    if not filetools.exists(matchcenter_path):
        logger.debug("Creating matchcenter path: " + matchcenter_path)
        filetools.mkdir(matchcenter_path)


def is_xbmc():
    return True
