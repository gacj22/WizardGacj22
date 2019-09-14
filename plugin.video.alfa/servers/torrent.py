# -*- coding: utf-8 -*-

import time
import threading
import os
import traceback
import re
import urllib
import sys

try:
    import xbmc
    import xbmcgui
    import xbmcaddon
except:
    pass

from core import filetools
from core import httptools
from core import scrapertools
from platformcode import logger
from platformcode import config
from platformcode import platformtools

trackers = [
        "udp://tracker.openbittorrent.com:80/announce",
        "http://tracker.torrentbay.to:6969/announce",
        "http://tracker.pow7.com/announce",
        "udp://tracker.ccc.de:80/announce",
        "udp://open.demonii.com:1337",

        "http://9.rarbg.com:2710/announce",
        "http://bt.careland.com.cn:6969/announce",
        "http://explodie.org:6969/announce",
        "http://mgtracker.org:2710/announce",
        "http://tracker.best-torrents.net:6969/announce",
        "http://tracker.tfile.me/announce",
        "http://tracker1.wasabii.com.tw:6969/announce",
        "udp://9.rarbg.com:2710/announce",
        "udp://9.rarbg.me:2710/announce",
        "udp://coppersurfer.tk:6969/announce",

        "http://www.spanishtracker.com:2710/announce",
        "http://www.todotorrents.com:2710/announce",
           ]


# Returns an array of possible video url's from the page_url
def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("server=torrent, la url es la buena")
    
    if page_url.startswith("magnet:"):
        video_urls = [["magnet: [torrent]", page_url]]
    else:
        video_urls = [[".torrent [torrent]", page_url]]

    return video_urls


class XBMCPlayer(xbmc.Player):

    def __init__(self, *args):
        pass

xbmc_player = XBMCPlayer()


def caching_torrents(url, referer=None, post=None, torrents_path=None, timeout=10, lookup=False, data_torrent=False, headers={}):
    if torrents_path != None:
        logger.info("path = " + torrents_path)
    else:
        logger.info()
    if referer and post:
        logger.info('REFERER: ' + referer)

    torrent_file = ''
    if referer:
        headers.update({'Content-Type': 'application/x-www-form-urlencoded', 'Referer': referer})   #Necesario para el Post del .Torrent
    
    """
    Descarga en el path recibido el .torrent de la url recibida, y pasa el decode
    Devuelve el path real del .torrent, o el path vacío si la operación no ha tenido éxito
    """
    
    videolibrary_path = config.get_videolibrary_path()                  #Calculamos el path absoluto a partir de la Videoteca
    if torrents_path == None:
        if not videolibrary_path:
            torrents_path = ''
            if data_torrent:
                return (torrents_path, torrent_file)
            return torrents_path                                        #Si hay un error, devolvemos el "path" vacío
        torrents_path = filetools.join(videolibrary_path, 'temp_torrents_Alfa', 'cliente_torrent_Alfa.torrent')    #path de descarga temporal
    if '.torrent' not in torrents_path:
        torrents_path += '.torrent'                                     #path para dejar el .torrent
    #torrents_path_encode = filetools.encode(torrents_path)              #encode utf-8 del path
    torrents_path_encode = torrents_path
    
    #if url.endswith(".rar") or url.startswith("magnet:"):               #No es un archivo .torrent
    if url.endswith(".rar"):                                            #No es un archivo .torrent
        logger.error('No es un archivo Torrent: ' + url)
        torrents_path = ''
        if data_torrent:
            return (torrents_path, torrent_file)
        return torrents_path                                            #Si hay un error, devolvemos el "path" vacío
    
    try:
        #Descargamos el .torrent
        if url.startswith("magnet:"):
            torrent_file = magnet2torrent(url, headers=headers)         #Convierte el Magnet en un archivo Torrent
            if not torrent_file:
                logger.error('No es un archivo Magnet: ' + url)
                torrents_path = ''
                if data_torrent:
                    return (torrents_path, torrent_file)
                return torrents_path                                    #Si hay un error, devolvemos el "path" vacío
        else:
            if post:                                                    #Descarga con POST
                response = httptools.downloadpage(url, headers=headers, post=post, follow_redirects=False, timeout=timeout)
            else:                                                       #Descarga sin post
                response = httptools.downloadpage(url, headers=headers, timeout=timeout)
            if not response.sucess:
                logger.error('Archivo .torrent no encontrado: ' + url)
                torrents_path = ''
                if data_torrent:
                    return (torrents_path, torrent_file)
                return torrents_path                                    #Si hay un error, devolvemos el "path" vacío
            torrent_file = response.data

        #Si es un archivo .ZIP tratamos de extraer el contenido
        if torrent_file.startswith("PK"):
            logger.info('Es un archivo .ZIP: ' + url)
            
            torrents_path_zip = filetools.join(videolibrary_path, 'temp_torrents_zip')  #Carpeta de trabajo
            torrents_path_zip = filetools.encode(torrents_path_zip)
            torrents_path_zip_file = filetools.join(torrents_path_zip, 'temp_torrents_zip.zip')     #Nombre del .zip
            
            import time
            filetools.rmdirtree(torrents_path_zip)                      #Borramos la carpeta temporal
            time.sleep(1)                                               #Hay que esperar, porque si no da error
            filetools.mkdir(torrents_path_zip)                          #La creamos de nuevo
            
            if filetools.write(torrents_path_zip_file, torrent_file):   #Salvamos el .zip
                torrent_file = ''                                       #Borramos el contenido en memoria
                try:                                                    #Extraemos el .zip
                    from core import ziptools
                    unzipper = ziptools.ziptools()
                    unzipper.extract(torrents_path_zip_file, torrents_path_zip)
                except:
                    import xbmc
                    xbmc.executebuiltin('XBMC.Extract("%s", "%s")' % (torrents_path_zip_file, torrents_path_zip))
                    time.sleep(1)
                
                for root, folders, files in filetools.walk(torrents_path_zip):      #Recorremos la carpeta para leer el .torrent
                    for file in files:
                        if file.endswith(".torrent"):
                            input_file = filetools.join(root, file)                 #nombre del .torrent
                            torrent_file = filetools.read(input_file)               #leemos el .torrent

            filetools.rmdirtree(torrents_path_zip)                                  #Borramos la carpeta temporal

        #Si no es un archivo .torrent (RAR, HTML,..., vacío) damos error
        if not scrapertools.find_single_match(torrent_file, '^d\d+:.*?\d+:'):
            logger.error('No es un archivo Torrent: ' + url)
            torrents_path = ''
            if data_torrent:
                return (torrents_path, torrent_file)
            return torrents_path                                            #Si hay un error, devolvemos el "path" vacío
        
        #Salvamos el .torrent
        if not lookup:
            if not filetools.write(torrents_path_encode, torrent_file):
                logger.error('ERROR: Archivo .torrent no escrito: ' + torrents_path_encode)
                torrents_path = ''                                          #Si hay un error, devolvemos el "path" vacío
                torrent_file = ''                                           #... y el buffer del .torrent
                if data_torrent:
                    return (torrents_path, torrent_file)
                return torrents_path
    except:
        torrents_path = ''                                                  #Si hay un error, devolvemos el "path" vacío
        torrent_file = ''                                                   #... y el buffer del .torrent
        logger.error('Error en el proceso de descarga del .torrent: ' + url + ' / ' + torrents_path_encode)
        logger.error(traceback.format_exc())
    
    #logger.debug(torrents_path)
    if data_torrent:
        return (torrents_path, torrent_file)
    return torrents_path
    

def magnet2torrent(magnet, headers={}):
    logger.info()
    
    torrent_file = ''
    info = ''
    post = ''
    LIBTORRENT_PATH = config.get_setting("libtorrent_path", server="torrent", default="")
    LIBTORRENT_MAGNET_PATH = filetools.join(config.get_setting("downloadpath"), 'magnet')
    MAGNET2TORRENT = config.get_setting("magnet2torrent", server="torrent", default=False)
    btih = scrapertools.find_single_match(magnet, 'urn:btih:([\w\d]+)\&').upper()

    if magnet.startswith('magnet') and MAGNET2TORRENT:

        # Tratamos de convertir el magnet on-line (opción más rápida, pero no se puede convertir más de un magnet a la vez)
        url_list = [
                    ('https://itorrents.org/torrent/', 6, '', '.torrent')
                   ]                                                            # Lista de servicios on-line testeados
        for url, timeout, id, sufix in url_list:
            if id:
                post = '%s=%s' % (id, magnet)
            else:
                url = '%s%s%s' % (url, btih, sufix)
            response = httptools.downloadpage(url, timeout=timeout, headers=headers, post=post)
            if not response.sucess:
                continue
            if not scrapertools.find_single_match(response.data, '^d\d+:.*?\d+:') and not response.data.startswith("PK"):
                continue
            torrent_file = response.data
            break

        #Usamos Libtorrent para la conversión del magnet como alternativa (es lento)
        if not torrent_file:
            lt, e, e1, e2 = import_libtorrent(LIBTORRENT_PATH)                  # Importamos Libtorrent
            if lt:
                ses = lt.session()                                              # Si se ha importado bien, activamos Libtorrent
                ses.add_dht_router("router.bittorrent.com",6881)
                ses.add_dht_router("router.utorrent.com",6881)
                ses.add_dht_router("dht.transmissionbt.com",6881)
                if ses:
                    filetools.mkdir(LIBTORRENT_MAGNET_PATH)                     # Creamos la carpeta temporal
                    params = {
                              'save_path': LIBTORRENT_MAGNET_PATH,
                              'trackers': trackers,
                              'storage_mode': lt.storage_mode_t.storage_mode_allocate
                             }                                                  # Creamos los parámetros de la sesión
                    
                    h = lt.add_magnet_uri(ses, magnet, params)                  # Abrimos la sesión
                    i = 0
                    while not h.has_metadata() and not xbmc.abortRequested:     # Esperamos mientras Libtorrent abre la sesión
                        h.force_dht_announce()
                        time.sleep(1)
                        i += 1
                        logger.error(i)
                        if i > 5:
                            LIBTORRENT_PATH = ''                                # No puede convertir el magnet
                            break
                    
                    if LIBTORRENT_PATH:
                        info = h.get_torrent_info()                             # Obtiene la información del .torrent
                        torrent_file = lt.bencode(lt.create_torrent(info).generate())   # Obtiene los datos del .torrent
                    ses.remove_torrent(h)                                       # Desactiva Libtorrent
                    filetools.rmdirtree(LIBTORRENT_MAGNET_PATH)                 # Elimina la carpeta temporal
    
    return torrent_file    


def verify_url_torrent(url, timeout=5):
    """
    Verifica si el archivo .torrent al que apunta la url está disponible, descargándolo en un area temporal
    Entrada:    url
    Salida:     True o False dependiendo del resultado de la operación
    """

    if not url or url == 'javascript:;':                                            #Si la url viene vacía...
        return False                                                                #... volvemos con error
    torrents_path = caching_torrents(url, timeout=timeout, lookup=True)             #Descargamos el .torrent
    if torrents_path:                                                               #Si ha tenido éxito...
        return True
    else:
        return False


# Reproductor Cliente Torrent propio (libtorrent)
def bt_client(mediaurl, xlistitem, rar_files, subtitle=None, password=None, item=None):
    logger.info()
    
    # Importamos el cliente
    from btserver import Client

    played = False
    debug = False

    save_path_videos = filetools.join(config.get_setting("bt_download_path", server="torrent", 
               default=config.get_setting("downloadpath")), 'BT-torrents')
    if not save_path_videos:
        save_path_videos = filetools.join(config.get_data_path(), 'BT-torrents')
        
    UNRAR = config.get_setting("unrar_path", server="torrent", default="")
    BACKGROUND = config.get_setting("mct_background_download", server="torrent", default=True)
    RAR = config.get_setting("mct_rar_unpack", server="torrent", default=True)
    try:
        BUFFER = int(config.get_setting("bt_buffer", server="torrent", default="50"))
    except:
        BUFFER = 50
    DOWNLOAD_LIMIT = config.get_setting("mct_download_limit", server="torrent", default="")
    if DOWNLOAD_LIMIT:
        try:
            DOWNLOAD_LIMIT = int(DOWNLOAD_LIMIT)
        except:
            DOWNLOAD_LIMIT = 0
    else:
        DOWNLOAD_LIMIT = 0
    UPLOAD_LIMIT = 100
    
    torr_client = 'BT'
    rar_file = ''
    rar_names = []
    rar = False
    rar_res = False
    bkg_user = False
    video_names = []
    video_file = ''
    video_path = ''
    videourl = ''
    msg_header = 'Alfa %s Cliente Torrent' % torr_client
    extensions_list = ['.aaf', '.3gp', '.asf', '.avi', '.flv', '.mpeg',
                       '.m1v', '.m2v', '.m4v', '.mkv', '.mov', '.mpg',
                       '.mpe', '.mp4', '.ogg', '.rar', '.wmv', '.zip']
    
    for entry in rar_files:
        for file, path in entry.items():
            if file == 'path' and '.rar' in str(path):
                for file_r in path:
                    rar_names += [file_r]
                    rar = True
                    if RAR and BACKGROUND:
                        bkg_user = True
            elif file == 'path' and not '.rar' in str(path):
                for file_r in path:
                    if os.path.splitext(file_r)[1] in extensions_list:
                        video_names += [file_r]
            elif file == '__name':
                video_path = path
                video_file = path
    if rar: rar_file = '%s/%s' % (video_path, rar_names[0])
    erase_file_path = filetools.join(save_path_videos, video_path)
    video_path = erase_file_path
    if video_names: video_file = video_names[0]
    if not video_file and mediaurl.startswith('magnet'):
        video_file = urllib.unquote_plus(scrapertools.find_single_match(mediaurl, '(?:\&|&amp;)dn=([^\&]+)\&'))
        erase_file_path = filetools.join(save_path_videos, video_file)
    
    if rar and RAR and not UNRAR:
        if not platformtools.dialog_yesno(msg_header, 'Se ha detectado un archivo .RAR en la descarga', \
                    'No tiene instalado el extractor UnRAR', '¿Desea descargarlo en cualquier caso?'):
            return

    # Iniciamos el cliente:
    c = Client(url=mediaurl, is_playing_fnc=xbmc_player.isPlaying, wait_time=None, auto_shutdown=False, timeout=10,
               temp_path=save_path_videos, print_status=debug, auto_delete=False)
    
    activo = True
    finalizado = False
    dp_cerrado = True

    # Mostramos el progreso
    if rar and RAR and BACKGROUND:                                                  # Si se descarga un RAR...
        progreso = platformtools.dialog_progress_bg(msg_header)
        platformtools.dialog_notification("Descarga de RAR en curso", "Puedes realizar otras tareas en Kodi mientrastanto. " + \
                "Te informaremos...", time=10000)
    else:
        progreso = platformtools.dialog_progress('Alfa %s Cliente Torrent' % torr_client, '')
    dp_cerrado = False

    # Mientras el progreso no sea cancelado ni el cliente cerrado
    try:
        while not c.closed and not xbmc.abortRequested:
            # Obtenemos el estado del torrent
            s = c.status
            if debug:
                # Montamos las tres lineas con la info del torrent
                txt = '%.2f%% de %.1fMB %s | %.1f kB/s' % \
                      (s.progress_file, s.file_size, s.str_state, s._download_rate)
                txt2 = 'S: %d(%d) P: %d(%d) | DHT:%s (%d) | Trakers: %d | Pi: %d(%d)' % \
                       (s.num_seeds, s.num_complete, s.num_peers, s.num_incomplete, s.dht_state, s.dht_nodes,
                        s.trackers, s.pieces_sum, s.pieces_len)
                txt3 = 'Origen Peers TRK: %d DHT: %d PEX: %d LSD %d ' % \
                       (s.trk_peers, s.dht_peers, s.pex_peers, s.lsd_peers)
            else:
                txt = '%.2f%% de %.1fMB %s | %.1f kB/s' % \
                      (s.progress_file, s.file_size, s.str_state, s._download_rate)
                txt2 = 'S: %d(%d) P: %d(%d) | DHT:%s (%d) | Trakers: %d | Pi: %d(%d)' % \
                       (s.num_seeds, s.num_complete, s.num_peers, s.num_incomplete, s.dht_state, s.dht_nodes,
                        s.trackers, s.pieces_sum, s.pieces_len)
                txt3 = video_file

            if rar and RAR and BACKGROUND or bkg_user:
                progreso.update(s.buffer, txt, txt2)
            else:
                progreso.update(s.buffer, txt, txt2, txt3)
            time.sleep(1)

            if (not bkg_user and progreso.iscanceled()) and (not (rar and RAR and BACKGROUND) and progreso.iscanceled()):
                
                if not dp_cerrado:
                    progreso.close()
                    dp_cerrado = True
                if 'Finalizado' in s.str_state or 'Seeding' in s.str_state:
                    """
                    if not rar and platformtools.dialog_yesno(msg_header, config.get_localized_string(70198)):
                        played = False
                        dp_cerrado = False
                        progreso = platformtools.dialog_progress(msg_header, '')
                        progreso.update(s.buffer, txt, txt2, txt3)
                    else:
                    """
                    dp_cerrado = False
                    progreso = platformtools.dialog_progress(msg_header, '')
                    break

                else:
                    if platformtools.dialog_yesno(msg_header, "¿Borramos los archivo descargados? (incompletos)",  
                                    "Selecciona NO para seguir descargando en segundo plano"):
                        dp_cerrado = False
                        progreso = platformtools.dialog_progress(msg_header, '')
                        break

                    else:
                        bkg_user = True
                        if not dp_cerrado: progreso.close()
                        dp_cerrado = False
                        progreso = platformtools.dialog_progress_bg(msg_header)
                        progreso.update(s.buffer, txt, txt2)
                        if not c.closed:
                            c.set_speed_limits(DOWNLOAD_LIMIT, UPLOAD_LIMIT)        # Bajamos la velocidad en background

            # Si el buffer se ha llenado y la reproduccion no ha sido iniciada, se inicia
            if ((s.pieces_sum >= BUFFER  or 'Finalizado' in s.str_state or 'Seeding' in s.str_state) and not rar and not bkg_user) or \
                        (s.pieces_sum >= s.pieces_len - 3 and s.pieces_len > 0 and ('Finalizado' in s.str_state or 'Seeding' \
                        in s.str_state) and (rar or bkg_user)) and not played:
                
                if rar and RAR and UNRAR:
                    c.stop()
                    activo = False
                    finalizado = True
                    bkg_user = False
                    dp_cerrado = False
                    video_file, rar_res, video_path, erase_file_path = extract_files(rar_file, \
                                    save_path_videos, password, progreso, item, torr_client)  # ... extraemos el vídeo del RAR
                    if rar_res and not xbmc.abortRequested:
                        time.sleep(1)
                    else:
                        break
                elif (rar and not UNRAR) or (rar and not RAR):
                    break
                elif bkg_user:
                    finalizado = True
                    break
                
                # Cerramos el progreso
                if not dp_cerrado:
                    progreso.close()
                    dp_cerrado = True

                # Reproducimos el vídeo extraido, si no hay nada en reproducción
                if not c.closed:
                    c.set_speed_limits(DOWNLOAD_LIMIT, UPLOAD_LIMIT)        # Bajamos la velocidad en background
                bkg_auto = True
                while xbmc_player.isPlaying() and not xbmc.abortRequested:
                    time.sleep(3)      
                
                # Obtenemos el playlist del torrent
                #videourl = c.get_play_list()
                if not rar_res:                                             # Es un Magnet ?
                    video_file = filetools.join(save_path_videos, s.file_name)
                    if erase_file_path == save_path_videos:
                        erase_file_path = video_file
                    videourl = video_file
                else:
                    videourl = filetools.join(video_path, video_file)

                # Iniciamos el reproductor
                playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
                playlist.clear()
                playlist.add(videourl, xlistitem)
                # xbmc_player = xbmc_player
                log("##### videourl: %s" % videourl)
                xbmc_player.play(playlist)

                # Marcamos como reproducido para que no se vuelva a iniciar
                played = True
                
                mark_auto_as_watched(item)
                
                # Y esperamos a que el reproductor se cierre
                bkg_auto = True
                dp_cerrado = True
                while xbmc_player.isPlaying() and not xbmc.abortRequested:
                    time.sleep(1)
                    
                    if xbmc.getCondVisibility('Player.Playing'):
                        if not dp_cerrado:
                            dp_cerrado = True
                            progreso.close()
                    
                    if xbmc.getCondVisibility('Player.Paused') and not rar_res:
                        if not c.closed: s = c.status
                        txt = '%.2f%% de %.1fMB %s | %.1f kB/s' % \
                              (s.progress_file, s.file_size, s.str_state, s._download_rate)
                        txt2 = 'S: %d(%d) P: %d(%d) | DHT:%s (%d) | Trakers: %d | Pi: %d(%d)' % \
                               (s.num_seeds, s.num_complete, s.num_peers, s.num_incomplete, s.dht_state, s.dht_nodes,
                                s.trackers, s.pieces_sum, s.pieces_len)
                        txt3 = video_file[:99]
                        if dp_cerrado:
                            dp_cerrado = False
                            progreso = xbmcgui.DialogProgressBG()
                            progreso.create(msg_header)
                        progreso.update(s.buffer, msg_header, '[CR][CR]' + txt + '[CR]' + txt2)
                
                if not dp_cerrado:
                    dp_cerrado = True
                    progreso.close()
                
                # Miramos si se ha completado la descarga para borrar o no los archivos
                if activo:
                    s = c.status
                if s.pieces_sum == s.pieces_len:
                    finalizado = True
                    break

                if platformtools.dialog_yesno(msg_header, "¿Borramos los archivo descargados? (incompletos)",  
                                    "Selecciona NO para seguir descargando en segundo plano"):
                    progreso = platformtools.dialog_progress(msg_header, '')
                    dp_cerrado = False
                    break
                else:
                    bkg_user = True
                    played = False
                    if not dp_cerrado: progreso.close()
                    progreso = platformtools.dialog_progress_bg(msg_header)
                    progreso.update(s.buffer, txt, txt2)
                    dp_cerrado = False
                    continue
                
                # Cuando este cerrado,  Volvemos a mostrar el dialogo
                if not (rar and bkg_user):
                    progreso = platformtools.dialog_progress(msg_header, '')
                    progreso.update(s.buffer, txt, txt2, txt3)
                    dp_cerrado = False
                    
                break
    except:
        logger.error(traceback.format_exc(1))
        return
    
    if not dp_cerrado:
        if rar or bkg_user:
            progreso.update(100, config.get_localized_string(70200), " ")
        else:
            progreso.update(100, config.get_localized_string(70200), " ", " ")

    # Detenemos el cliente
    if activo and not c.closed:
        c.stop()
        activo = False

    # Cerramos el progreso
    if not dp_cerrado:
        progreso.close()
        dp_cerrado = True
    
    # Y borramos los archivos de descarga restantes
    time.sleep(1)
    if filetools.exists(erase_file_path) and not bkg_user:
        if finalizado and not platformtools.dialog_yesno(msg_header, '¿Borrarmos los archivos descargados? (completos)'):
            return
        log("##### erase_file_path: %s" % erase_file_path)
        for x in range(10):
            if filetools.isdir(erase_file_path):
                if erase_file_path != save_path_videos:
                    filetools.rmdirtree(erase_file_path)
                else:
                    break
            else:
                filetools.remove(erase_file_path)
            time.sleep(5)
            if not filetools.exists(erase_file_path):
                break


def mark_auto_as_watched(item):
    
    time_limit = time.time() + 150                                      #Marcamos el timepo máx. de buffering
    while not platformtools.is_playing() and time.time() < time_limit:                #Esperamos mientra buffera    
        time.sleep(5)                                                   #Repetimos cada intervalo
        #logger.debug(str(time_limit))
    if item.subtitle:
        time.sleep(5)
        xbmc_player.setSubtitles(item.subtitle)
        #subt = xbmcgui.ListItem(path=item.url, thumbnailImage=item.thumbnail)
        #subt.setSubtitles([item.subtitle])

    if item.strm_path and platformtools.is_playing():                                 #Sólo si es de Videoteca
        from platformcode import xbmc_videolibrary
        xbmc_videolibrary.mark_auto_as_watched(item)                    #Marcamos como visto al terminar
        #logger.debug("Llamado el marcado")


def wait_for_download(rar_files, torr_client):
    logger.info()

    from subprocess import Popen, PIPE, STDOUT
    
    # Analizamos los archivos dentro del .torrent
    rar = False
    rar_names = []
    rar_names_abs = []
    folder = ''
    for entry in rar_files:
        for file, path in entry.items():
            if file == 'path' and '.rar' in str(path):
                for file_r in path:
                    rar_names += [file_r]
                    rar = True
            elif file == '__name':
                folder = path
    
    if not folder:                                                              # Si no se detecta el folder...
        return ('', '', '')                                                     # ... no podemos hacer nada
        
    if not rar_names:
        return ('', '', folder)
    rar_file = '%s/%s' % (folder, rar_names[0])
    log("##### rar_file: %s" % rar_file)
    if len(rar_names) > 1:
        log("##### rar_names: %s" % str(rar_names))
        
    # Localizamos el path de descarga del .torrent
    save_path_videos = ''
    __settings__ = xbmcaddon.Addon(id="plugin.video.%s" % torr_client)          # Apunta settings del cliente torrent
    if torr_client == 'torrenter':
        save_path_videos = str(xbmc.translatePath(__settings__.getSetting('storage')))
        if not save_path_videos:
            save_path_videos = str(filetools.join(xbmc.translatePath("special://home/"), \
                                   "cache", "xbmcup", "plugin.video.torrenter", "Torrenter"))
    else:
        save_path_videos = str(xbmc.translatePath(__settings__.getSetting('download_path')))
        if __settings__.getSetting('download_storage') == '1':                  # Descarga en memoria?
            return ('', '', folder)                                             # volvemos
    if not save_path_videos:                                                    # No hay path de descarga?
        return ('', '', folder)                                                 # Volvemos
    log("##### save_path_videos: %s" % save_path_videos)

    # Esperamos mientras el .torrent se descarga.  Verificamos si el .RAR está descargado al completo
    platformtools.dialog_notification("Automatizando la extracción", "Acepta descargar el archivo RAR y te iremos guiando...", time=10000)
    
    # Plan A: usar el monitor del cliente torrent para ver el status de la descarga
    loop = 3600                                                                 # Loop de 10 horas hasta crear archivo
    wait_time = 10
    time.sleep(wait_time)
    fast = False
    for x in range(loop):
        if xbmc.abortRequested:
            return ('', '', folder)
        torr_data, deamon_url, index = get_tclient_data(folder, torr_client)
        if not torr_data or not deamon_url:
            break
        if torr_client in ['quasar'] and not torr_data['label'].startswith('0.00%') and not fast:
            platformtools.dialog_notification("Descarga en curso", "Puedes realizar otras tareas en Kodi mientrastanto. " + \
                    "Te informaremos...", time=10000)
            fast = True
        if not torr_data['label'].startswith('100.00%'):
            log("##### Descargado: %s, ID: %s" % (scrapertools.find_single_match(torr_data['label'], '(^.*?\%)'), index))
            time.sleep(wait_time)
            continue
        
        log("##### Torrent FINALIZADO: %s" % str(folder))
        return (rar_file, save_path_videos, folder)
    
    # Plan B: monitorizar con UnRAR si los archivos se han desacargado por completo
    unrar_path = config.get_setting("unrar_path", server="torrent", default="")
    if not unrar_path:                                                          # Si Unrar no está instalado...
        return ('', '', folder)                                                 # ... no podemos hacer nada
        
    cmd = []
    for rar_name in rar_names:                                                  # Preparamos por si es un archivo multiparte
        cmd.append(['%s' % unrar_path, 'l', '%s' % filetools.join(save_path_videos, folder, rar_name)])
    
    creationflags = ''
    if xbmc.getCondVisibility("system.platform.Windows"):
        creationflags = 0x08000000
    loop = 30                                                                   # Loop inicial de 5 minutos hasta crear archivo
    wait_time = 10
    loop_change = 0
    loop_error = 6
    part_name = ''
    y = 0
    returncode = ''
    fast = False
    while rar and not xbmc.abortRequested:
        for x in range(loop):                                                   # Loop corto (5 min.) o largo (10 h.)
            if xbmc.abortRequested:
                return ('', '', folder)
            if not rar or loop_change > 0:
                loop = loop_change                                              # Paso de loop corto a largo
                loop_change = 0
                break
            try:
                responses = []
                for z, command in enumerate(cmd):                               # Se prueba por cada parte
                    if xbmc.getCondVisibility("system.platform.Windows"):
                        data_rar = Popen(command, bufsize=0, stdout=PIPE, stdin=PIPE, \
                                     stderr=STDOUT, creationflags=creationflags)
                    else:
                        data_rar = Popen(command, bufsize=0, stdout=PIPE, stdin=PIPE, \
                                     stderr=STDOUT)
                    out_, error_ = data_rar.communicate()
                    responses.append([z, str(data_rar.returncode), out_, error_])   # Se guarda la respuesta de cada parte
            except:
                logger.error(traceback.format_exc(1))                           # Error de incompatibilidad de UnRAR
                rar = False
                break
            else:
                dl_files = 0
                for z, returncode, out__, error__ in responses:                 # Analizamos las respuestas
                    if returncode == '0':                                       # Ya se ha descargado... parte ...
                        dl_files += 1
                        part_name = scrapertools.find_single_match(str(out__), '(\.part\d+.rar)')
                        log("##### Torrent descargando: %s, %s" % (part_name, str(returncode)))
                        if dl_files == len(cmd):                                # ... o todo
                            fast = True
                            rar = False
                            break                                                   # ... o sólo una parte
                    elif returncode == '10':                                    # archivo no existe
                        if loop != 30:                                          # Si el archivo es borrado durante el proceso ...
                            rar = False
                        break                                                   #... abortamos
                    elif returncode == '6':                                     # En proceso de descarga
                        y += 1
                        #if loop == 30 and y == len(responses):                  # Si es la primera vez en proceso ...
                        if loop == 30 and y == 1:                               # Si es la primera vez en proceso ...
                            if torr_client in ['quasar']:
                                platformtools.dialog_notification("Descarga en curso", "Puedes realizar otras tareas en Kodi mientrastanto. " + \
                                        "Te informaremos...", time=10000)
                            loop_change = 3600                                  # ... pasamos a un loop de 10 horas
                        elif loop <= 6:                                         # Recuerado el error desconocido
                            loop_change = 3600                                  # ... pasamos a un loop de 10 horas
                            loop_error = 6                                      # Restauramos loop_error por si acaso
                        break
                    elif returncode == '1':                                     # Ha alcanzado el fin de archivo ??? pasamos
                        part_name = scrapertools.find_single_match(str(out__), '(\.part\d+.rar)')
                        log("##### Torrent descargando: %s, %s" % (part_name, str(returncode)))
                    else:                                                       # No entendemos el error
                        loop_change = loop_error                                # ... pasamos a un loop de 1 minutos para reintentar
                        loop_error += -1
                        break                                                   #... abortamos
                
                if str(returncode) in ['0', '6', '10']:
                    log("##### Torrent descargando: %s" % str(returncode))
                else:
                    log("##### Torrent descargando: %s, %s" % (str(out__), str(returncode)))
                if not rar or fast:
                    fast = False
                    break
                time.sleep(wait_time)                                           # Esperamos un poco y volvemos a empezar
        else:
            rar = False
            break

    if str(returncode) == '0':
        log("##### Torrent FINALIZADO: %s" % str(returncode))
    else:
        rar_file = ''
        logger.error('##### Torrent NO DESCARGADO: %s, %s' % (str(out__), str(returncode)))
    
    return (rar_file, save_path_videos, folder)
    
    
def get_tclient_data(folder, torr_client):
    import json
    
    # Monitoriza el estado de descarga del torrent en Quasar y Elementum
    local_host = {"quasar": "http://localhost:65251/torrents/", "elementum": "http://localhost:65220/torrents/"}
    torr = ''
    torr_id = ''
    x = 0
    y = ''
    
    try:
        data = httptools.downloadpage(local_host[torr_client], timeout=5, alfa_s=True).data
        if not data:
            return '', local_host[torr_client], 0

        data = json.loads(data)
        data = data['items']
        for x, torr in enumerate(data):
            if not folder in torr['label']:
                continue
            if "elementum" in torr_client:
                torr_id = scrapertools.find_single_match(str(torr), 'torrents\/pause\/(.*?)\)')
            break
        else:
            return '', local_host[torr_client], 0
    except:
        log(traceback.format_exc(1))
        return '', local_host[torr_client], 0
    
    if torr_id:
        y = torr_id
    else:
        y = x
    return torr, local_host[torr_client], y


def extract_files(rar_file, save_path_videos, password, dp, item=None, torr_client=None):
    logger.info()
    
    #reload(sys)
    #sys.setdefaultencoding('utf-8')
    sys.path.insert(0, config.get_setting("unrar_path", server="torrent", default="")\
                    .replace('/unrar', '').replace('\\unrar,exe', ''))
    
    import rarfile

    # Verificamos si hay path para UnRAR
    rarfile.UNRAR_TOOL = config.get_setting("unrar_path", server="torrent", default="")
    if not rarfile.UNRAR_TOOL:
        if xbmc.getCondVisibility("system.platform.Android"):
            rarfile.UNRAR_TOOL = xbmc.executebuiltin("StartAndroidActivity(com.rarlab.rar)")
        return rar_file, False, '', ''
    log("##### unrar_path: %s" % rarfile.UNRAR_TOOL)
    rarfile.DEFAULT_CHARSET = 'utf-8'
    
    # Preparamos un path alternativo más corto para no sobrepasar la longitud máxima
    video_path = ''
    if item:
        if item.contentType == 'movie':
            video_path = '%s-%s' % (item.contentTitle, item.infoLabels['tmdb_id'])
        else:
            video_path = '%s-%sx%s-%s' % (item.contentSerieName, item.contentSeason, \
                            item.contentEpisodeNumber, item.infoLabels['tmdb_id'])
    
    # Renombramos el path dejado en la descarga a uno más corto
    rename_status = False
    org_rar_file = rar_file
    org_save_path_videos = save_path_videos
    if video_path and '/' in rar_file:
        log("##### rar_file: %s" % rar_file)
        rename_status, rar_file = rename_rar_dir(org_rar_file, org_save_path_videos, video_path, torr_client)

    # Calculamos el path para del RAR
    if "/" in rar_file:
        folders = rar_file.split("/")
        erase_file_path = filetools.join(save_path_videos, folders[0])
        file_path = save_path_videos
        for f in folders:
            file_path = filetools.join(file_path, f)
    else:
        file_path = save_path_videos
        erase_file_path = save_path_videos

    # Calculamos el path para la extracción
    if "/" in rar_file:
        folders = rar_file.split("/")
        for f in folders:
            if not '.rar' in f:
                save_path_videos = filetools.join(save_path_videos, f)
    save_path_videos = filetools.join(save_path_videos, 'Extracted')
    if not filetools.exists(save_path_videos): filetools.mkdir(save_path_videos)
    log("##### save_path_videos: %s" % save_path_videos)

    # Permite hasta 5 pasadas de extracción de .RARs anidados
    platformtools.dialog_notification("Empezando extracción...", rar_file, time=5000)
    for x in range(5):
        try:
            archive = rarfile.RarFile(file_path.decode("utf8"))
        except:
            log("##### ERROR en Archivo rar: %s" % rar_file)
            log("##### ERROR en Carpeta del rar: %s" % file_path)
            log(traceback.format_exc())
            platformtools.dialog_notification("Error al abrir el RAR", "Comprueba el log para más detalles")
            return rar_file, False, '', ''

        # Analizamos si es necesaria una contraseña, que debería estar en item.password
        if archive.needs_password():
            if not password:
                pass_path = filetools.split(file_path)[0]
                password = last_password_search(pass_path)
            if not password :
                password = platformtools.dialog_input(heading="Introduce la contraseña (Mira en %s)" % pass_path)
                if not password:
                    return rar_file, False, '', ''
            archive.setpassword(password)
            log("##### Password rar: %s" % password)

        # Miramos el contenido del RAR a extraer
        files = archive.infolist()
        info = []
        for idx, i in enumerate(files):
            if i.file_size == 0:
                files.pop(idx)
                continue
            filename = i.filename
            if "/" in filename:
                filename = filename.rsplit("/", 1)[1]

            info.append("%s - %.2f MB" % (filename, i.file_size / 1048576.0))
        if info:
            info.append("Extraer todo sin reproducir")
        else:
            platformtools.dialog_notification("El RAR está vacío", "O no contiene archivos válidos")
            return rar_file, False, '', erase_file_path

        # Seleccionamos extraer TODOS los archivos del RAR
        #selection = xbmcgui.Dialog().select("Selecciona el fichero a extraer y reproducir", info)
        selection = len(info) - 1
        if selection < 0:
            return rar_file, False, '', erase_file_path
        else:
            try:
                log("##### RAR Extract INI #####")
                if selection == len(info) - 1:
                    log("##### rar_file 1: %s" % file_path)
                    log("##### save_path_videos 1: %s" % save_path_videos)
                    dp.update(99, "Extrayendo archivos...", "Espera unos minutos....")
                    archive.extractall(save_path_videos)
                else:
                    log("##### rar_file 2: %s" % file_path)
                    log("##### save_path_videos 2: %s" % save_path_videos)
                    dp.update(99, "Espera unos minutos....", "Extrayendo archivo... %s" % info[selection])
                    archive.extract(files[selection], save_path_videos)
                log("##### RAR Extract END #####")
            except (rarfile.RarWrongPassword, rarfile.RarCRCError):
                platformtools.dialog_notification("Error al extraer", "Contraseña incorrecta")
                log(traceback.format_exc(1))
                return rar_file, False, '', erase_file_path
            except rarfile.BadRarFile:
                platformtools.dialog_notification("Error al extraer", "Archivo rar con errores")
                log(traceback.format_exc(1))
                return rar_file, False, '', erase_file_path
            except:
                platformtools.dialog_notification("Error al extraer", "Comprueba el log para más detalles")
                log(traceback.format_exc(1))
                return rar_file, False, '', erase_file_path

            extensions_list = ['.aaf', '.3gp', '.asf', '.avi', '.flv', '.mpeg',
                               '.m1v', '.m2v', '.m4v', '.mkv', '.mov', '.mpg',
                               '.mpe', '.mp4', '.ogg', '.wmv']
            
            # Localizamos el path donde se ha dejado la extracción
            folder = True
            file_result = filetools.listdir(save_path_videos)
            while folder:
                for file_r in file_result:
                    if filetools.isdir(filetools.join(save_path_videos, file_r)):
                        file_result_alt = filetools.listdir(filetools.join(save_path_videos, file_r))
                        if file_result_alt:
                            file_result = file_result_alt
                            save_path_videos = filetools.join(save_path_videos, file_r)
                        else:
                            folder = False
                        break
                else:
                    folder = False

            # Si hay RARs anidados, ajustamos los paths para la siguiente pasada
            if '.rar' in str(file_result):
                for file_r in file_result:
                    if '.rar' in file_r:
                        rar_file = file_r
                        file_path = str(filetools.join(save_path_videos, rar_file))
                        save_path_videos = filetools.join(save_path_videos, 'Extracted')
                        if not filetools.exists(save_path_videos): filetools.mkdir(save_path_videos)
                        platformtools.dialog_notification("Siguiente extracción...", rar_file, time=5000)
            
            # Si ya se ha extraido todo, preparamos el retorno            
            else:
                video_list = []
                for file_r in file_result:
                    if os.path.splitext(file_r)[1] in extensions_list:
                        video_list += [file_r]
                if len(video_list) == 0:
                    platformtools.dialog_notification("El rar está vacío", "O no contiene archivos válidos")
                    return rar_file, False, '', erase_file_path
                else:
                    log("##### Archivo extraído: %s" % video_list[0])
                    platformtools.dialog_notification("Archivo extraído...", video_list[0], time=10000)
                    return str(video_list[0]), True, save_path_videos, erase_file_path


def rename_rar_dir(rar_file, save_path_videos, video_path, torr_client):
    logger.info()

    rename_status = False
    folders = rar_file.split("/")
    if filetools.exists(filetools.join(save_path_videos, folders[0])):
        src = filetools.join(save_path_videos, folders[0]).decode("utf8")
        dst = filetools.join(save_path_videos, video_path).decode("utf8")
        dst_file = video_path.decode("utf8")
        
        # Se para la actividad para que libere los archivos descargados
        if torr_client in ['quasar', 'elementum']:
            torr_data, deamon_url, index = get_tclient_data(folders[0], torr_client)
            log("##### Client URL: %s" % '%spause/%s' % (deamon_url, index))
            if torr_data and deamon_url:
                data = httptools.downloadpage('%spause/%s' % (deamon_url, index), timeout=5, alfa_s=True).data
            
        for x in range(10):
            if xbmc.abortRequested:
                return rename_status, rar_file
            xbmc.sleep(1000)
            try:
                if filetools.exists(src):
                    filetools.rename(src, dst_file)
                else:
                    break
            except:
                log("##### Rename ERROR: SRC: %s" % src)
                log(traceback.format_exc(1))
            else:
                if filetools.exists(dst):
                    log("##### Renamed: SRC: %s" % src)
                    log("##### TO: DST: %s" % dst)
                    rar_file = video_path + '/' + folders[1]
                    rename_status = True
                    break
                    
    return rename_status, rar_file


def last_password_search(pass_path):
    logger.info()

    # Busca en el Path de extracción si hay algún archivo que contenga la URL donde pueda estar la CONTRASEÑA
    password = ''
    patron_url = '(http.*\:\/\/(?:www.)?\w+\.\w+\/.*?[\n|\r|$])'
    patron_pass = '<input\s*type="text"\s*id="txt_password"\s*name="[^"]+"\s*onClick="[^"]+"\s*value="([^"]+)"'
    
    try:
        pass_path_list = filetools.listdir(pass_path)
        for file in pass_path_list:
            if 'contrase' in file.lower() and '.rar' not in file:
                file_pass = filetools.read(filetools.join(pass_path, file))
                url = scrapertools.find_single_match(file_pass, patron_url)
                if url:
                    data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(url).data)
                    password = scrapertools.find_single_match(data, patron_pass)
            if password:
                break
    except:
        log(traceback.format_exc(1))
    
    log("##### Contraseña extraída: %s" % password)
    return password


def import_libtorrent(LIBTORRENT_PATH):
    logger.info(LIBTORRENT_PATH)

    try:
        sys.path.insert(0, LIBTORRENT_PATH)
        e = ''
        e1 = ''
        e2 = ''
        fp = ''
        pathname = ''
        description = ''
        lt = ''
        if LIBTORRENT_PATH:
            try:
                if not xbmc.getCondVisibility("system.platform.android"):
                    import libtorrent as lt
                    pathname = LIBTORRENT_PATH
                else:
                    import imp
                    from ctypes import CDLL
                    dll_path = os.path.join(LIBTORRENT_PATH, 'liblibtorrent.so')
                    liblibtorrent = CDLL(dll_path)
                    
                    path_list = [LIBTORRENT_PATH, xbmc.translatePath('special://xbmc')]
                    fp, pathname, description = imp.find_module('libtorrent', path_list)
                    
                    # Esta parte no funciona en Android.  Por algún motivo da el error "dlopen failed: library "liblibtorrent.so" not found"
                    # Hay que encontrar un hack para rodear el problema.  Lo siguiente ha sido probado sin éxito:
                    #if fp: fp.close()
                    #fp = filetools.file_open(filetools.join(LIBTORRENT_PATH, 'libtorrent.so'), mode='rb')  # Usa XbmcVFS
                    #fp = open(os.path.join(LIBTORRENT_PATH, 'libtorrent.so'), 'rb')
                    
                    try:
                        lt = imp.load_module('libtorrent', fp, pathname, description)
                    finally:
                        if fp: fp.close()
                
            except Exception, e1:
                logger.error(traceback.format_exc(1))
                log('fp = ' + str(fp))
                log('pathname = ' + str(pathname))
                log('description = ' + str(description))
                if fp: fp.close()
                from lib.python_libtorrent.python_libtorrent import get_libtorrent
                lt = get_libtorrent()

    except Exception, e2:
        try:
            logger.error(traceback.format_exc())
            if fp: fp.close()
            e = e1 or e2
            ok = platformtools.dialog_ok('ERROR en el cliente MCT Libtorrent', \
                        'Módulo no encontrado o imcompatible con el dispositivo.', \
                        'Reporte el fallo adjuntando un "log".', str(e))
        except:
            pass
    
    return lt, e, e1, e2


def log(texto):
    try:
        xbmc.log(texto, xbmc.LOGNOTICE)
    except:
        pass
    