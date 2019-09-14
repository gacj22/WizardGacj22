# -*- coding: utf-8 -*-
import xbmc
from core.libs import *
logger.init_logger('services.log', 2)

if __name__ == '__main__':
    # Desactivar el modo de adultos si es necesario
    if settings.get_setting('adult_mode') == 1:
        logger.debug('Desactivando modo adultos')
        settings.set_setting('adult_mode', 0)

    # Mantenimiento BBDD
    bbdd.scraper_cache_clear()

    settings.set_setting('update_service', 'stop')
    settings.set_setting('library_service', 'stop')

    monitor = xbmc.Monitor()
    while not monitor.abortRequested():
        if settings.get_setting('update_service') == 'stop':
            logger.debug('Iniciando servicio de actualizaciones')
            xbmc.executebuiltin('RunScript(plugin.video.mediaexplorer, update_service.py)')
            settings.set_setting('update_service', 'start')

        if settings.get_setting('library_service') == 'stop':
            logger.debug('Iniciando servicio de biblioteca')
            xbmc.executebuiltin('RunScript(plugin.video.mediaexplorer, library_service.py)')
            settings.set_setting('library_service', 'start')

        if monitor.waitForAbort(10):
            break
