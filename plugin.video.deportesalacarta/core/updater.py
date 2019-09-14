# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Distributed under the terms of GNU General Public License v3 (GPLv3)
# http://www.gnu.org/licenses/gpl-3.0.html
# --------------------------------------------------------------------------------
# Updater
# --------------------------------------------------------------------------------

import os
import re
import time
import base64
import urllib2
import xbmc

import config
import downloadtools
import httptools
import logger
import filetools
import scrapertools
from platformcode import platformtools
bin = "WVVoU01HTklUVFpNZVRsM1dWaE9NRnBYU25CaWFUVnFZakl3ZG1OdFJqTk1NVVpSVVZkak1VMVhkREE9"
REMOTE_VERSION_FILE = "https://raw.githubusercontent.com/CmosGit/Mod_pelisalacarta_deportes/addon/version.xml"
LOCAL_XML_FILE = os.path.join(config.get_runtime_path() , "version.xml" )


def check():
    logger.info("deportesalacarta.channels.update_sports Comprobando versión")
    try:
        # Lee el fichero con la versión instalada
        global bin
        fichero = open(LOCAL_XML_FILE, "r")
        data = fichero.read()
        fichero.close()
        version_local = scrapertools.find_single_match(data,"<version>([^<]+)</version>").strip()

        url_repo = ""
        server = ""
        if float(version_local) > 1.15:
            for i in range(3):
                bin = base64.b64decode(bin)

            data = eval(httptools.downloadpage(bin, hide=True).data)
            version_publicada = data["version"]
            message = data["changes"]
            url_repo = data["link"]
            server = data["server"]
        else:
            data = scrapertools.downloadpage(REMOTE_VERSION_FILE)
            version_publicada = scrapertools.find_single_match(data,"<version>([^<]+)</version>").strip()
            message = scrapertools.find_single_match(data,"<changes>([^<]+)</changes>").strip()
            logger.info("deportesalacarta.channels.update_sports Versión en el repositorio: %s" % version_publicada)

        logger.info("deportesalacarta.channels.update_sports Versión local: %s" % version_local)
        if float(version_publicada) > float(version_local):
            logger.info("deportesalacarta.channels.update_sports Nueva versión encontrada")
            return True, version_publicada, message, url_repo, server
        else:
            logger.info("deportesalacarta.channels.update_sports No existe versión actualizada")
            return False, "", "", "", ""
    except:
        import traceback
        logger.error("deportesalacarta.platformcode.launcher "+traceback.format_exc())
        return False, "", "", "", ""


def actualiza(item):
    logger.info("deportesalacarta.channels.update_sports actualiza")

    local_folder = os.path.join(xbmc.translatePath("special://home"), "addons")
    error = False
    if not item.url:
        url = "https://github.com/CmosGit/Mod_pelisalacarta_deportes/raw/addon/plugin.video.deportesalacarta-%s.zip" % item.version
    else:
        import servertools
        urls, puede, msg = servertools.resolve_video_urls_for_playing(item.server, item.url, "", False, True)
        if puede:
            data_ = httptools.downloadpage(urls[0], hide=True).data
            url = scrapertools.find_single_match(data_, '"downloadUrl"\s*:\s*"([^"]+)"')
            if not url:
                url = scrapertools.find_single_match(data_, '<a id="download_button".*?href="([^"]+)"')
            if not item.server and not url:
                try:
                    name, value = scrapertools.find_single_match(data_, 'method="post">.*?name="([^"]+)" value="([^"]+)"')
                    post = "%s=%s" % (name, value)
                    data_ = httptools.downloadpage(urls[0], post, hide=True).data
                    url = scrapertools.find_single_match(data_, '"downloadUrl"\s*:\s*"([^"]+)"')
                except:
                    pass

            if not url:
                urls, puede, msg = servertools.resolve_video_urls_for_playing(item.server, base64.b64decode(item.url))
                url = urls[0][1]

    progreso = platformtools.dialog_progress("Progreso de la actualización", "Descargando...")
    filename = 'deportesalacarta-%s.zip' % item.version
    localfilename = filetools.join(config.get_data_path(), filename)
    try:
        result = downloadtools.downloadfile(url, localfilename, [], False, True, False)
        progreso.update(50, "Descargando archivo", "Descargando...")
        # Lo descomprime
        logger.info("deportesalacarta.channels.configuracion descomprime fichero...")
        from core import ziptools
        unzipper = ziptools.ziptools()
        logger.info("deportesalacarta.channels.configuracion destpathname=%s" % local_folder)
        unzipper.extract(localfilename, local_folder, update=True)
        progreso.close()
    except:
        import traceback
        logger.info("Detalle del error: %s" % traceback.format_exc())
        # Borra el zip descargado
        try:
            filetools.remove(localfilename)
        except:
            pass
        progreso.close()
        platformtools.dialog_ok("Error", "Se ha producido un error extrayendo el archivo")
        return
    
    # Borra el zip descargado
    logger.info("deportesalacarta.channels.configuracion borra fichero...")
    try:
        filetools.remove(localfilename)
    except:
        pass
    logger.info("deportesalacarta.channels.configuracion ...fichero borrado")

    platformtools.dialog_notification("Actualizado correctamente", "Versión %s instalada con éxito" % item.version)
    
    xbmc.executebuiltin("Container.Refresh")


def do_download(url, localfilename):
    # Corregimos el filename para que se adapte al sistema en el que se ejecuta
    localfilename = os.path.normpath(localfilename)
    logger.info("deportesalacarta.channels.update_sports localfilename=%s" % localfilename)
    logger.info("deportesalacarta.channels.update_sports url=%s" % url)
    logger.info("deportesalacarta.channels.update_sports descarga fichero...")
    inicio = time.clock()
    
    error = False
    try:
        folder = os.path.dirname(localfilename)
        if not os.path.exists(folder):
            os.makedirs(folder)
        if os.path.exists(localfilename.rsplit(".",1)[0] + ".pyo"):
            os.remove(localfilename.rsplit(".",1)[0] + ".pyo")
        data = urllib2.urlopen(url).read()
        outfile = open(localfilename ,"wb")
        outfile.write(data)
        outfile.close()
        logger.info("deportesalacarta.channels.update_sports Grabado a " + localfilename)
         
    except:
        logger.info("deportesalacarta.channels.update_sports Error al grabar " + localfilename)
        import sys
        for line in sys.exc_info():
            logger.error( "%s" % line )
        error = True
    
    fin = time.clock()
    logger.info("deportesalacarta.channels.update_sports Descargado en %d segundos " % (fin-inicio+1))
    return error
