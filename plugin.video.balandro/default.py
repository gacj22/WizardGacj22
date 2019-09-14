# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Balandro - Main
# ------------------------------------------------------------

import os, sys, urllib2

from platformcode import config, logger, platformtools
from core.item import Item

from platformcode.config import WebErrorException


logger.info('Starting with %s' % sys.argv[1])

# Obtener parámetros de lo que hay que ejecutar
# ---------------------------------------------
if sys.argv[2]:
    item = Item().fromurl(sys.argv[2])
else:
    item = Item(channel='mainmenu', action='mainlist')

logger.debug(item)


# Establecer si channel es un canal web o un módulo
# -------------------------------------------------
tipo_channel = ''

if item.channel == '' or item.action == '':
    logger.info('Empty channel/action, nothing to do')

else:
    # channel puede ser un canal web o un módulo
    path = os.path.join(config.get_runtime_path(), 'channels', item.channel + ".py")
    if os.path.exists(path):
        tipo_channel = 'channels.'
    else:
        path = os.path.join(config.get_runtime_path(), 'modules', item.channel + ".py")
        if os.path.exists(path):
            tipo_channel = 'modules.'
        else:
            logger.error('Channel/Module not found, nothing to do')
            logger.debug(item)


# Ejecutar según los parámetros recibidos
# ---------------------------------------
if tipo_channel != '':
    try:
        canal = __import__(tipo_channel + item.channel, fromlist=[''])

        # findvideos se considera reproducible y debe acabar haciendo play (o play_fake en su defecto)
        if item.action == 'findvideos':
            if hasattr(canal, item.action):
                itemlist = canal.findvideos(item)
            else:
                itemlist = servertools.find_video_items(item)

            platformtools.play_from_itemlist(itemlist, item)

        else:
            # search pide el texto a buscar antes de llamar a la rutina del canal (pasar item.buscando para no mostrar diálogo)
            if item.action == 'search':
                if item.buscando != '':
                    tecleado = item.buscando
                else:
                    last_search = config.get_last_search(item.search_type)
                    tecleado = platformtools.dialog_input(last_search, 'Texto a buscar')
                    
                if tecleado is not None and tecleado != '':
                    itemlist = canal.search(item, tecleado)
                    if item.buscando == '': config.set_last_search(item.search_type, tecleado)
                else:
                    itemlist = []

            # cualquier otra acción se ejecuta en el canal, y se renderiza si devuelve una lista de items
            else:
                if hasattr(canal, item.action):
                    func = getattr(canal, item.action)
                    itemlist = func(item)
                else:
                    logger.info('Action not found in channel')
                    itemlist = [] if item.folder else False  # Si item.folder kodi espera un listado
            
            if type(itemlist) == list:
                logger.info('renderizar itemlist')
                platformtools.render_items(itemlist, item)

            # ~ elif itemlist == None: # Si kodi espera un listado (desactivado pq igualmente sale ERROR: GetDirectory en el log)
                # ~ logger.info('sin renderizar')
                # ~ platformtools.render_no_items()

            elif itemlist == True:
                logger.info('El canal ha ejecutado correctamente una acción que no devuelve ningún listado.')

            elif itemlist == False:
                logger.info('El canal ha ejecutado una acción que no devuelve ningún listado.')

    except urllib2.URLError, e:
        import traceback
        logger.error(traceback.format_exc())

        # Grab inner and third party errors
        if hasattr(e, 'reason'):
            logger.error("Razon del error, codigo: %s | Razon: %s" % (str(e.reason[0]), str(e.reason[1])))
            texto = "No se puede conectar con el servidor"  # "No se puede conectar con el sitio web"
            platformtools.dialog_ok(config.__addon_name, texto)

        # Grab server response errors
        elif hasattr(e, 'code'):
            logger.error("Codigo de error HTTP : %d" % e.code)
            platformtools.dialog_ok(config.__addon_name, "El sitio web no funciona correctamente (error http %d)" % e.code)

    except WebErrorException, e:
        import traceback
        logger.error(traceback.format_exc())
        
        # Ofrecer buscar en otros canales o en el mismo canal, si está activado en la configuración
        if item.contentType in ['movie', 'tvshow', 'season', 'episode'] and config.get_setting('tracking_weberror_dialog', default=True):
            if item.action == 'findvideos': platformtools.play_fake()

            item_search = platformtools.dialogo_busquedas_por_fallo_web(item)
            if item_search is not None:
                platformtools.itemlist_update(item_search)
                
        else:
            platformtools.dialog_ok('Error en el canal ' + item.channel, 
                                    'La web de la que depende parece no estar disponible, puede volver a intentarlo, si el problema persiste verifique mediante un navegador la web: %s' % (e) )

    except:
        import traceback
        logger.error(traceback.format_exc())
        platformtools.dialog_ok(
            "Error inesperado en el canal " + item.channel,
            "Puede deberse a un fallo de conexión, la web del canal ha cambiado su estructura, o un error interno del addon. Para saber más detalles, consulta el log.")


logger.info('Ending with %s' % sys.argv[1])
