# coding=utf-8
import xbmc

from core import library
from core.libs import *

if __name__ == '__main__':
    logger.init_logger('library_service.log', 3)
    logger.debug('Servicio de biblioteca iniciado')

    update_interval = settings.get_setting('library_update', library.__file__)
    last_check_updates = settings.get_setting('last_check_updates', library.__file__) or 0

    if update_interval == 1:
        library.check_updates()

    monitor = xbmc.Monitor()
    while not monitor.abortRequested():
        if update_interval == 2 and time.time() - last_check_updates > 86400:
            library.check_updates()

        if monitor.waitForAbort(3600):
            break

        # Detenemos el servicio si se solicita un reinicio del mismo
        if settings.get_setting('library_service') == 'restart':
            logger.debug('Reiniciando servicio de biblioteca')
            settings.set_setting('library_service', 'stop')
            break

    logger.debug('Servicio de biblioteca detenido')
