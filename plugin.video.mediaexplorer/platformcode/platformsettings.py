# -*- coding: utf-8 -*-
from core.libs import *
import xbmc
import xbmcaddon


def get_platform():
    """
        Devuelve la información la version de xbmc o kodi sobre el que se ejecuta el plugin

        @rtype: dict
        @return: Retorna un diccionario con las siguientes claves:
            'num_version': (float) numero de version en formato XX.X
            'name_version': (str) nombre clave de cada version
            'video_db': (str) nombre del archivo que contiene la base de datos de videos
            'plaform': (str) "kodi" o "xbmc" segun corresponda.
         """

    ret = {}
    codename = {"10": "dharma", "11": "eden", "12": "frodo",
                "13": "gotham", "14": "helix", "15": "isengard",
                "16": "jarvis", "17": "krypton", "18": "leia"}
    code_db = {'10': 'MyVideos37.db', '11': 'MyVideos60.db', '12': 'MyVideos75.db',
               '13': 'MyVideos78.db', '14': 'MyVideos90.db', '15': 'MyVideos93.db',
               '16': 'MyVideos99.db', '17': 'MyVideos107.db', '18': 'MyVideos116.db'}

    num_version = xbmc.getInfoLabel('System.BuildVersion')
    num_version = re.match("\d+\.\d+", num_version).group(0)
    ret['name_version'] = codename.get(num_version.split('.')[0], num_version)
    ret['video_db'] = code_db.get(num_version.split('.')[0], "")
    ret['num_version'] = float(num_version)
    ret['platform'] = "kodi"

    return ret


def config():
    platformtools.show_settings()


def get_kodi_version():
    xml_path = os.path.join(runtime_path, 'addon.xml')
    xml = open(xml_path, 'rb').read()
    return re.compile('name="MediaExplorer".*?version="([^"]+)"', re.DOTALL).findall(xml)[0]


# Main
data_path = xbmc.translatePath(xbmcaddon.Addon(id="plugin.video.mediaexplorer").getAddonInfo('Profile'))
runtime_path = xbmc.translatePath(xbmcaddon.Addon(id="plugin.video.mediaexplorer").getAddonInfo('Path'))
temp_path = xbmc.translatePath("special://temp/")
bookmarks_path = xbmc.translatePath("special://profile/favourites.xml")
info_platform = get_platform()
platform_name = info_platform['platform']
platform_version = info_platform['num_version']
main_version = get_kodi_version()