# coding=utf-8
import xbmc

from core import updates
from core.libs import *

if __name__ == '__main__':
    logger.init_logger('update_service.log', 3)
    logger.debug('Servicio de actializaciones iniciado')

    update_interval = settings.get_setting('update_interval')
    logger.debug(
        'Intervalo de comprobación: %s' % ["Nunca", "Al iniciar", "Cada 12 horas", "Una vez al dia"][update_interval]
    )

    if update_interval == 1 and updates.check_updates(True):
        platformtools.dialog_notification("MediaExplorer", "Actualizaciones disponibles", sound=False)

    monitor = xbmc.Monitor()
    while not monitor.abortRequested():
        if not platformtools.is_playing():
            update_interval = settings.get_setting('update_interval')
            last_check_updates = updates.last_check_updates()

            if ((update_interval == 2 and time.time() - last_check_updates > 3600 * 12) or
                (update_interval == 3 and time.time() - last_check_updates > 3600 * 24)) and \
                    updates.check_updates(True):
                platformtools.dialog_notification("MediaExplorer", "Actualizaciones disponibles", sound=False)

        if monitor.waitForAbort(3600):
            break

        # Detenemos el servicio si se solicita un reinicio del mismo
        if settings.get_setting('update_service') == 'restart':
            logger.debug('Reiniciando servicio de actualizaciones')
            settings.set_setting('update_service', 'stop')
            break

    logger.debug('Servicio de actializaciones detenido')
