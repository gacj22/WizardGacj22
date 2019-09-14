# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Distributed under the terms of GNU General Public License v3 (GPLv3)
# http://www.gnu.org/licenses/gpl-3.0.html
# ------------------------------------------------------------
# ------------------------------------------------------------

import glob
import os
import traceback
import urlparse

from core import channeltools
from core import config
from core import filetools
from core import logger
from core.item import Item

DEBUG = config.get_setting("debug")


def getmainlist(preferred_thumb=""):
    logger.info("channelselector.getmainlist")
    itemlist = list()

    # Añade los canales que forman el menú principal

    itemlist.append(Item(title=config.get_localized_string(30118),
                         channel="channelselector", 
                         action="filterchannels",
                         thumbnail=get_thumb(preferred_thumb,"thumb_canales.png"),
                         viewmode="movie"))

    itemlist.append(Item(title="MatchCenter",
                         channel="matchcenter", 
                         action="start",
                         thumbnail=filetools.join(config.get_runtime_path(),"resources","images","matchcenter","matchcenter.png"),
                         viewmode="movie"))

    itemlist.append(Item(title=config.get_localized_string(30102),
                         channel="favoritos", 
                         action="mainlist",
                         thumbnail=get_thumb(preferred_thumb,"thumb_favoritos.png"),
                         viewmode="movie"))

    itemlist.append(Item(title=config.get_localized_string(30101), 
                         channel="descargas",
                         action="mainlist",
                         thumbnail=get_thumb(preferred_thumb,"thumb_descargas.png"),
                         viewmode="movie"))

    itemlist.append(Item(title=config.get_localized_string(30100),
                         channel="configuracion", 
                         action="mainlist",
                         thumbnail=get_thumb(preferred_thumb,"thumb_configuracion.png"),
                         viewmode="list"))

    return itemlist


def get_thumb(preferred_thumb,thumb_name):
    return urlparse.urljoin(get_thumbnail_path(preferred_thumb),thumb_name)


def filterchannels(category,preferred_thumb=""):
    logger.info("channelselector.filterchannels")

    channelslist =[]

    # Lee la lista de canales
    channel_path = os.path.join( config.get_runtime_path() , "channels" , '*.xml' )
    logger.info("channelselector.filterchannels channel_path="+channel_path)

    channel_files = glob.glob(channel_path)
    logger.info("channelselector.filterchannels channel_files encontrados "+str(len(channel_files)))

    for index, channel in enumerate(channel_files):
        logger.info("channelselector.filterchannels channel="+channel)
        if channel.endswith(".xml"):
            try:
                channel_parameters = channeltools.get_channel_parameters(channel[:-4])
                logger.info("channelselector.filterchannels channel_parameters="+repr(channel_parameters))

                # Si prefiere el bannermenu y el canal lo tiene, cambia ahora de idea
                if preferred_thumb=="bannermenu" and "bannermenu" in channel_parameters:
                    channel_parameters["thumbnail"] = channel_parameters["bannermenu"]

                # Se salta el canal si no está activo
                if not channel_parameters["active"] == "true":
                    continue

                import xbmc
                if xbmc.Player().isPlayingAudio():
                    xbmc.executebuiltin('xbmc.PlayMedia(Stop)')

                # Si ha llegado hasta aquí, lo añade
                channelslist.append(Item(title=channel_parameters["title"], channel=channel_parameters["channel"], action="mainlist", thumbnail=channel_parameters["thumbnail"] , fanart=channel_parameters["fanart"], category=", ".join(channel_parameters["categories"])[:-2], language=channel_parameters["language"], viewmode="list" ))
            
            except:
                logger.info("Se ha producido un error al leer los datos del canal " + channel)
                import traceback
                logger.info(traceback.format_exc())
           
    channelslist.sort(key=lambda item: item.title.lower().strip())

    return channelslist

def get_thumbnail_path(preferred_thumb=""):

    WEB_PATH = ""
    
    if preferred_thumb=="":
        thumbnail_type = config.get_setting("thumbnail_type")
        if thumbnail_type=="":
            thumbnail_type="2"

        if thumbnail_type=="0":
            WEB_PATH = "http://media.tvalacarta.info/pelisalacarta/posters/"
        elif thumbnail_type=="1":
            WEB_PATH = "http://media.tvalacarta.info/pelisalacarta/banners/"
        elif thumbnail_type=="2":
            WEB_PATH = "http://media.tvalacarta.info/pelisalacarta/squares/"
    else:
        WEB_PATH = "http://media.tvalacarta.info/pelisalacarta/"+preferred_thumb+"/"

    return WEB_PATH
