# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Updater (kodi)
# --------------------------------------------------------------------------------

import os
import time
import threading
import traceback

from platformcode import config, logger, platformtools

from core import httptools
from core import jsontools
from core import downloadtools
from core import ziptools
from core import filetools


def check_addon_init():
    logger.info()
    
    # Subtarea de monitor.  Se activa cada X horas para comprobar si hay FIXES al addon
    def check_addon_monitor():
        logger.info()
        
        # Obtiene el íntervalo entre actualizaciones y si se quieren mensajes
        try:
            timer = int(config.get_setting('addon_update_timer'))       # Intervalo entre actualizaciones, en Ajustes de Alfa
            if timer <= 0:
                return                                                  # 0.  No se quieren actualizaciones
            verbose = config.get_setting('addon_update_message')
        except:
            timer = 12                                                  # Por defecto cada 12 horas
            verbose = False                                             # Por defecto, sin mensajes
        timer = timer * 3600                                            # Lo pasamos a segundos

        if config.get_platform(True)['num_version'] >= 14:              # Si es Kodi, lanzamos el monitor
            import xbmc
            monitor = xbmc.Monitor()
        else:                                                           # Lanzamos solo una actualización y salimos
            check_addon_updates(verbose)                                # Lanza la actualización
            return
            
        while not monitor.abortRequested():                             # Loop infinito hasta cancelar Kodi

            check_addon_updates(verbose)                                # Lanza la actualización
            
            if monitor.waitForAbort(timer):                             # Espera el tiempo programado o hasta que cancele Kodi
                break                                                   # Cancelación de Kodi, salimos
                
        return
                
    # Lanzamos en Servicio de actualización de FIXES
    try:
        threading.Thread(target=check_addon_monitor).start()            # Creamos un Thread independiente, hasta el fin de Kodi
        time.sleep(5)                                                   # Dejamos terminar la primera verificación...
    except:                                                             # Si hay problemas de threading, se llama una sola vez
        try:
            timer = int(config.get_setting('addon_update_timer'))       # Intervalo entre actualizaciones, en Ajustes de Alfa
            if timer <= 0:
                return                                                  # 0.  No se quieren actualizaciones
            verbose = config.get_setting('addon_update_message')
        except:
            verbose = False                                             # Por defecto, sin mensajes
            pass
        check_addon_updates(verbose)                                    # Lanza la actualización, en Ajustes de Alfa
        time.sleep(5)                                                   # Dejamos terminar la primera verificación...
              
    return
    

def check_addon_updates(verbose=False):
    logger.info()

    ADDON_UPDATES_JSON = 'https://extra.alfa-addon.com/addon_updates/updates.json'
    ADDON_UPDATES_ZIP = 'https://extra.alfa-addon.com/addon_updates/updates.zip'

    try:
        last_fix_json = os.path.join(config.get_runtime_path(), 'last_fix.json')   # información de la versión fixeada del usuario
        # Se guarda en get_runtime_path en lugar de get_data_path para que se elimine al cambiar de versión

        # Descargar json con las posibles actualizaciones
        # -----------------------------------------------
        data = httptools.downloadpage(ADDON_UPDATES_JSON, timeout=5).data
        if data == '': 
            logger.info('No se encuentran actualizaciones del addon')
            if verbose:
                platformtools.dialog_notification('Alfa ya está actualizado', 'No hay ninguna actualización urgente')
            return False

        data = jsontools.load(data)
        if 'addon_version' not in data or 'fix_version' not in data: 
            logger.info('No hay actualizaciones del addon')
            if verbose:
                platformtools.dialog_notification('Alfa ya está actualizado', 'No hay ninguna actualización urgente')
            return False

        # Comprobar versión que tiene instalada el usuario con versión de la actualización
        # --------------------------------------------------------------------------------
        current_version = config.get_addon_version(with_fix=False)
        if current_version != data['addon_version']:
            logger.info('No hay actualizaciones para la versión %s del addon' % current_version)
            if verbose:
                platformtools.dialog_notification('Alfa ya está actualizado', 'No hay ninguna actualización urgente')
            return False

        if os.path.exists(last_fix_json):
            try:
                lastfix =  {} 
                lastfix = jsontools.load(filetools.read(last_fix_json))
                if lastfix['addon_version'] == data['addon_version'] and lastfix['fix_version'] == data['fix_version']:
                    logger.info('Ya está actualizado con los últimos cambios. Versión %s.fix%d' % (data['addon_version'], data['fix_version']))
                    if verbose:
                        platformtools.dialog_notification('Alfa ya está actualizado', 'Versión %s.fix%d' % (data['addon_version'], data['fix_version']))
                    return False
            except:
                if lastfix:
                    logger.error('last_fix.json: ERROR en: ' + str(lastfix))
                else:
                    logger.error('last_fix.json: ERROR desconocido')
                lastfix =  {}

        # Descargar zip con las actualizaciones
        # -------------------------------------
        localfilename = os.path.join(config.get_data_path(), 'temp_updates.zip')
        if os.path.exists(localfilename): os.remove(localfilename)

        downloadtools.downloadfile(ADDON_UPDATES_ZIP, localfilename, silent=True)
        
        # Descomprimir zip dentro del addon
        # ---------------------------------
        try:
            unzipper = ziptools.ziptools()
            unzipper.extract(localfilename, config.get_runtime_path())
        except:
            import xbmc
            xbmc.executebuiltin('XBMC.Extract("%s", "%s")' % (localfilename, config.get_runtime_path()))
            time.sleep(1)
        
        # Borrar el zip descargado
        # ------------------------
        os.remove(localfilename)
        
        # Guardar información de la versión fixeada
        # -----------------------------------------
        if 'files' in data: data.pop('files', None)
        filetools.write(last_fix_json, jsontools.dump(data))
        
        logger.info('Addon actualizado correctamente a %s.fix%d' % (data['addon_version'], data['fix_version']))
        if verbose:
            platformtools.dialog_notification('Alfa actualizado a', 'Versión %s.fix%d' % (data['addon_version'], data['fix_version']))
        return True

    except:
        logger.error('Error al comprobar actualizaciones del addon!')
        logger.error(traceback.format_exc())
        if verbose:
            platformtools.dialog_notification('Alfa actualizaciones', 'Error al comprobar actualizaciones')
        return False
