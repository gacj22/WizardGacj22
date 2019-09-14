# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Balandro - Updater (actualizaciones del addon)
# --------------------------------------------------------------------------------

import os, time, traceback

from platformcode import config, logger, platformtools
from core import httptools, jsontools, filetools, downloadtools


def check_addon_updates(verbose=False):
    logger.info()

    ADDON_UPDATES_JSON = 'https://balandro.tk/addon_updates/updates.json'
    ADDON_UPDATES_ZIP  = 'https://balandro.tk/addon_updates/updates.zip'

    try:
        last_fix_json = os.path.join(config.get_runtime_path(), 'last_fix.json')   # información de la versión fixeada del usuario
        # Se guarda en get_runtime_path en lugar de get_data_path para que se elimine al cambiar de versión

        # Descargar json con las posibles actualizaciones
        # -----------------------------------------------
        data = httptools.downloadpage(ADDON_UPDATES_JSON, timeout=2).data
        if data == '': 
            logger.info('No se encuentran actualizaciones del addon')
            if verbose:
                platformtools.dialog_notification('Balandro ya está actualizado', 'No hay ninguna actualización pendiente')
            return False

        data = jsontools.load(data)
        if 'addon_version' not in data or 'fix_version' not in data: 
            logger.info('No hay actualizaciones del addon')
            if verbose:
                platformtools.dialog_notification('Balandro ya está actualizado', 'No hay ninguna actualización pendiente')
            return False

        # Comprobar versión que tiene instalada el usuario con versión de la actualización
        # --------------------------------------------------------------------------------
        current_version = config.get_addon_version(with_fix=False)
        if current_version != data['addon_version']:
            logger.info('No hay actualizaciones para la versión %s del addon' % current_version)
            if verbose:
                platformtools.dialog_notification('Balandro ya está actualizado', 'No hay ninguna actualización pendiente')
            return False

        if os.path.exists(last_fix_json):
            lastfix = jsontools.load(filetools.read(last_fix_json))
            if lastfix['addon_version'] == data['addon_version'] and lastfix['fix_version'] == data['fix_version']:
                logger.info('Ya está actualizado con los últimos cambios. Versión %s.fix%d' % (data['addon_version'], data['fix_version']))
                if verbose:
                    platformtools.dialog_notification('Balandro ya está actualizado', 'Versión %s.fix%d' % (data['addon_version'], data['fix_version']))
                return False

        # Descargar zip con las actualizaciones
        # -------------------------------------
        localfilename = os.path.join(config.get_data_path(), 'temp_updates.zip')
        if os.path.exists(localfilename): os.remove(localfilename)

        down_stats = downloadtools.do_download(ADDON_UPDATES_ZIP, config.get_data_path(), 'temp_updates.zip', silent=True, resume=False)
        if down_stats['downloadStatus'] != 2: # 2:completed
            logger.info('No se puede descargar la actualización')
            if verbose:
                platformtools.dialog_notification('Actualización fallida', 'No se puede descargar la actualización')
            return False
        
        # Descomprimir zip dentro del addon
        # ---------------------------------
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
            platformtools.dialog_notification('Balandro actualizado a', 'Versión %s.fix%d' % (data['addon_version'], data['fix_version']))
        return True

    except:
        logger.error('Error al comprobar actualizaciones del addon!')
        logger.error(traceback.format_exc())
        if verbose:
            platformtools.dialog_notification('Balandro actualizaciones', 'Error al comprobar actualizaciones')
        return False
