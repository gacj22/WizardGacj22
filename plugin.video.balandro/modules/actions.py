# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Balandro - Ejecución de acciones concretas que no devuelven ningún listado
# ------------------------------------------------------------

from platformcode import config, logger, platformtools
from core.item import Item


# Abrir ventana de Configuración
def open_settings(item):
    logger.info()

    config.__settings__.openSettings()


# Comprobar nuevos episodios en cualquiera de las series en seguimiento
def comprobar_nuevos_episodios(item):
    logger.info()

    # TODO aviso de espera...
    
    from core import trackingtools
    trackingtools.check_and_scrap_new_episodes()
 

# Comprobar actualizaciones (llamada desde una opción de la Configuración)
def check_addon_updates(item):
    logger.info()

    # TODO aviso de espera...
    
    from platformcode import updater
    updater.check_addon_updates(verbose=True)


# Borrar caché de TMDB (llamada desde una opción de la Configuración)
def drop_db_cache(item):
    logger.info()

    if platformtools.dialog_yesno('Borrar caché Tmdb', '¿ Eliminar todos los registros del caché de Tmdb ?'): 
        from core import tmdb
        if tmdb.drop_bd():
            platformtools.dialog_notification(config.__addon_name, 'Borrado caché Tmdb', time=2000, sound=False)


# Limpiar caché de TMDB (llamada desde una opción de la Configuración)
def clean_db_cache(item):
    logger.info()

    import sqlite3, time
    from core import filetools
    
    fecha_caducidad = time.time() - (31 * 24 * 60 * 60) # al cabo de 31 días

    fname = filetools.join(config.get_data_path(), "tmdb.sqlite")
    conn = sqlite3.connect(fname)
    c = conn.cursor()
    
    c.execute('SELECT COUNT() FROM tmdb_cache')
    numregs = c.fetchone()[0]
    
    c.execute('SELECT COUNT() FROM tmdb_cache WHERE added < ?', (fecha_caducidad,))
    numregs_expired = c.fetchone()[0]
    
    txt = 'El caché de Tmdb ocupa [COLOR gold]%s[/COLOR]' % config.format_bytes(filetools.getsize(fname))
    txt += ' y contiene [COLOR gold]%s[/COLOR] registros.' % numregs
    txt += ' ¿ Borrar los [COLOR blue]%s[/COLOR] registros que tienen más de un mes de antiguedad ?' % numregs_expired
    if platformtools.dialog_yesno('Limpiar caché Tmdb', txt): 
        c.execute('DELETE FROM tmdb_cache WHERE added < ?', (fecha_caducidad,))
        conn.commit()
        conn.execute('VACUUM')
        platformtools.dialog_notification(config.__addon_name, 'Limpiado caché Tmdb', time=2000, sound=False)

    conn.close()



# Mostrar diálogo de información de un item haciendo una nueva llamada a Tmdb para recuperar más datos
def more_info(item):
    logger.info()

    # Si se llega aquí mediante el menú contextual, hay que recuperar los parámetros action y channel
    if item.from_action: item.__dict__['action'] = item.__dict__.pop('from_action')
    if item.from_channel: item.__dict__['channel'] = item.__dict__.pop('from_channel')

    import xbmcgui
    from core import tmdb
    
    tmdb.set_infoLabels_item(item)

    xlistitem = xbmcgui.ListItem()
    platformtools.set_infolabels(xlistitem, item, True)

    ret = xbmcgui.Dialog().info(xlistitem)


# Mostrar diálogo con los trailers encontrados para un item
def search_trailers(item):
    logger.info()

    from core.tmdb import Tmdb
    import xbmcgui, xbmc
    
    tipo = 'movie' if item.contentType == 'movie' else 'tv'
    nombre = item.contentTitle if item.contentType == 'movie' else item.contentSerieName
    if item.infoLabels['tmdb_id']:
        tmdb_search = Tmdb(id_Tmdb=item.infoLabels['tmdb_id'], tipo=tipo, idioma_busqueda='es')
    else:
        anyo = item.infoLabels['year'] if item.infoLabels['year'] else '-'
        tmdb_search = Tmdb(texto_buscado=nombre, tipo=tipo, year=anyo, idioma_busqueda='es')

    opciones = []
    resultados = tmdb_search.get_videos()
    for res in resultados:
        # ~ logger.debug(res)
        it = xbmcgui.ListItem(res['name'], '[%sp] (%s)' % (res['size'], res['language']))
        if item.thumbnail: it.setArt({ 'thumb': item.thumbnail })
        opciones.append(it)
    
    if len(resultados) == 0:
        platformtools.dialog_ok(nombre, 'No se encuentra ningún tráiler en TMDB')
    else:
        while not xbmc.Monitor().abortRequested(): # (while True)
            ret = xbmcgui.Dialog().select('Tráilers para %s' % nombre, opciones, useDetails=True)
            if ret == -1: break

            platformtools.dialog_notification(resultados[ret]['name'], 'Cargando tráiler ...', time=3000, sound=False)
            from core import servertools
            if 'youtube' in resultados[ret]['url']:
                video_urls, puedes, motivo = servertools.resolve_video_urls_for_playing('youtube', resultados[ret]['url'])
            else:
                video_urls = [] #TODO si no es youtube ...
                logger.debug(resultados[ret])
            if len(video_urls) > 0:
                # ~ logger.debug(video_urls)
                xbmc.Player().play(video_urls[-1][1]) # el último es el de más calidad
                xbmc.sleep(1000)
                while not xbmc.Monitor().abortRequested() and xbmc.Player().isPlaying():
                    xbmc.sleep(1000)
            else:
                platformtools.dialog_notification(resultados[ret]['name'], 'No se puede reproducir el tráiler', time=3000, sound=False)

            if len(resultados) == 1: break # si sólo hay un vídeo no volver al diálogo de tráilers



# Diálogos para mostrar info de Ayuda
# -----------------------------------

def show_help_settings(item):
    logger.info()

    txt = '*) Las opciones para los [COLOR gold]listados de canales[/COLOR] se usan si marcas canales como preferidos o desactivados.'
    txt += ' Esto lo puedes hacer desde el menú contextual en los listados de canales.'

    txt += '[CR][CR]'
    txt += '*) En "Búsquedas" el parámetro "[COLOR gold]Resultados previsualizados por canal[/COLOR]" sirve para limitar el número de coincidencias que se muestran en la pantalla de búsqueda global.'
    txt += ' Es para que no salga un listado demasiado largo ya que algunos canales son más sensibles que otros y pueden devolver bastantes resultados.'
    txt += ' Pero de todas maneras se puede acceder al listado de todos los resultados de cada canal concreto.'

    txt += '[CR][CR]'
    txt += '*) En "Reproducción" se puede activar Autoplay para no tener que seleccionar un servidor para reproducir.'
    txt += ' Si hay algún canal para el que quieras desactivar el autoplay puedes ponerlo en "Canales sin autoplay".'

    txt += '[CR][CR]'
    txt += '*) En "Reproducción" los parámetros para ordenar/filtrar los enlaces [COLOR gold]por idioma[/COLOR] permiten indicar nuestras preferencias de idiomas.'
    txt += ' Entre Español, Latino y Versión Original elije el orden que prefieres, o descarta alguno de ellos si no te interesa.'

    txt += '[CR][CR]'
    txt += '*) En "Reproducción" los parámetros para ordenar los enlaces [COLOR gold]por calidad[/COLOR] permiten mostrar antes los de más calidad en lugar de mostrarlos según el orden que tienen en la web.'
    txt += ' Algunos canales tienen valores fiables de calidad pero otros no, depende de cada web.'

    txt += '[CR][CR]'
    txt += '*) En "Reproducción" los parámetros para ordenar/filtrar los enlaces [COLOR gold]por servidores[/COLOR] permiten hacer algunos ajustes en función de los servers.'
    txt += ' Si no quieres que te salgan enlaces de ciertos servidores, escríbelos en "descartados" (ej: torrent,mega).'
    txt += ' Y si quieres priorizar algunos servidores escríbelos en "preferentes" (ej: torrent,openload), o al revés en "última opción" (ej: directo,flashx).'
    txt += ' Para modificar estas opciones necesitas saber qué servidores te funcionan mejor y peor, en caso de duda no hace falta que las modifiques.'

    txt += '[CR][CR]'
    txt += '*) Una opción puede provocar una demora en los tiempos de respuesta es en "Otros/TMDB" si se activa "[COLOR gold]buscar información extendida[/COLOR]".'
    txt += ' Esto provoca que los listados de películas y series de todos los canales tarden más en mostrarse ya que se hace una segunda llamada a TMDB para intentar recuperar más datos.'

    txt += '[CR][CR]'
    txt += '*) En "Otros/TMDB" se pueden desactivar las "[COLOR gold]llamadas a TMDB en los listados[/COLOR]".'
    txt += ' Esto provoca que los listados de películas y series de todos los canales tarden menos en mostrarse pero en la mayoría de casos no tendrán información como la sinopsi y las carátulas serán de baja calidad.'
    txt += ' Puede ser útil desactivarlo temporalmente en casos dónde alguna película/serie no se identifica correctamente en tmdb y se quieran ver los datos originales de la web.'

    platformtools.dialog_textviewer('Notas sobre algunos parámetros de configuración', txt)


def show_help_tips(item):
    logger.info()

    txt = '*) Es importante usar el [B][COLOR gold]menú contextual[/COLOR][/B] para acceder a acciones que se pueden realizar sobre los elementos de los listados.'
    txt += ' Si dispones de un teclado puedes acceder a él pulsando la tecla C, en dispositivos táctiles manteniendo pulsado un elemento, y en mandos de tv-box manteniendo pulsado el botón de selección.'
    txt += ' Si usas un mando de TV es recomendable configurar una de sus teclas con "ContextMenu".'

    txt += '[CR][CR]'
    txt += '*) En los listados de canales puedes usar el menú contextual para marcarlos como Desactivado/Activo/Preferido.'
    txt += ' De esta manera podrás tener tus [COLOR gold]canales preferidos[/COLOR] al inicio y quitar o mover al final los que no te interesen.'
    txt += ' Los canales desactivados son accesibles pero no forman parte de las búsquedas.'

    txt += '[CR][CR]'
    txt += '*) Si en algún canal encuentras una película/serie que te interesa pero fallan sus enlaces, accede al menú contextual y selecciona'
    txt += ' "[COLOR gold]buscar en otros canales[/COLOR]" para ver si está disponible en algún otro canal.'

    txt += '[CR][CR]'
    txt += '*) Desde cualquier pantalla desplázate hacia el lateral izquierdo para desplegar algunas [COLOR gold]opciones standard de Kodi[/COLOR].'
    txt += ' Allí tienes siempre un acceso directo a la Configuración del addon y también puedes cambiar el tipo de vista que se aplica a los listados.'
    txt += ' Entre Lista, Cartel, Mays., Muro de información, Lista amplia, Muro, Fanart, escoge como prefieres ver la información.'

    txt += '[CR][CR]'
    txt += '*) Algunos canales de series tienen un listado de [COLOR gold]últimos episodios[/COLOR]. En función de las características de las webs, los enlaces llevan'
    txt += ' a ver el capítulo o a listar las temporadas de la serie. Cuando es posible, desde el enlace se ve el episodio y desde el menú contextual'
    txt += ' se puede acceder a la temporada concreta o la lista de temporadas (como por ejemplo en seriespapaya y pepecine).'

    txt += '[CR][CR]'
    txt += '*) Para seguir series es recomendable usar la función de [COLOR gold]enlaces guardados[/COLOR]. Busca la serie que te interese en cualquiera de los canales y desde el menú contextual guárdala.'
    txt += ' Luego ves a "Enlaces guardados" dónde podrás gestionar lo necesario para la serie. Pues empezar con "Buscar en otros canales" y desde el listado de resultados con el menú'
    txt += ' contextual también los puedes guardar y se añadirán a los enlaces que ya tenías. De esta manera tendrás alternativas en diferentes enlaces por si algún día falla alguno o desaparece.'

    platformtools.dialog_textviewer('Truquillos y consejos varios', txt)


def show_help_use(item):
    logger.info()

    txt = '[COLOR gold]Nivel 1, casual[/COLOR][CR]'
    txt += 'Accede a Pelis (o Series) desde el menú principal, entra en alguno de los canales y navega por sus diferentes opciones hasta encontrar una película que te interese.'
    txt += ' Al entrar en la película se mostrará un diálogo con diferentes opciones de vídeos encontrados.'
    txt += ' Prueba con el primero y si el enlace es válido empezará a reproducirse. Sino, prueba con alguno de los otros enlaces disponibles.'
    txt += ' Si ninguno funcionara, desde el enlace de la película accede al menú contextual y selecciona "Buscar en otros canales".'

    txt += '[CR][CR][COLOR gold]Nivel 2, directo[/COLOR][CR]'
    txt += 'Si quieres ver una peli/serie concreta, accede a "Buscar" desde el menú principal y escribe el título en el buscador.'
    txt += ' Te saldrá una lista con las coincidencias en todos los canales disponibles.'

    txt += '[CR][CR][COLOR gold]Nivel 3, planificador[/COLOR][CR]'
    txt += 'Navega por los diferentes canales y ves apuntando las pelis/series que te puedan interesar.'
    txt += ' Para ello accede al menú contextual desde cualquier peli/serie y selecciona "Guardar enlace".'
    txt += ' Cuando quieras ver una peli, accede a "Enlaces guardados" desde el menú principal dónde estará todo lo apuntado.'

    txt += '[CR][CR][COLOR gold]Nivel 4, asegurador[/COLOR][CR]'
    txt += 'Descarga algunas películas para tener listas para ver sin depender de la saturación de la red/servidores en momentos puntuales.'
    txt += ' Desde cualquier peli/episodio, tanto en los canales como en los enlaces guardados, accede al menú contextual y "Descargar vídeo".'
    txt += ' Selecciona alguno de los enlaces igual que cuando se quiere reproducir y empezará la descarga.'
    txt += ' Para ver lo descargado, accede a "Descargas" desde el menú principal.'

    txt += '[CR][CR][COLOR gold]Nivel 5, coleccionista[/COLOR][CR]'
    txt += 'Desde "Enlaces guardados" accede a "Gestionar listas", dónde puedes crear diferentes listas para organizarte las películas y series que te interesen.'
    txt += ' Por ejemplo puedes tener listas para distintos usuarios o de diferentes temáticas, o para guardar lo que ya hayas visto, o para pasar tus recomendaciones a algún amigo, etc.'

    platformtools.dialog_textviewer('Ejemplos de uso de Balandro', txt)


def show_help_faq(item):
    logger.info()

    txt = '[COLOR gold]¿ De dónde viene Balandro ?[/COLOR][CR]'
    txt += 'Balandro es un addon derivado de Pelisalacarta y Alfa, simplificado a nivel interno de código y a nivel de uso por parte del usuario.'
    txt += ' Puede ser útil en dispositivos poco potentes como las Raspberry Pi u otros TvBox y para usuarios que no se quieran complicar mucho.'
    txt += ' Al ser un addon de tipo navegador, tiene el nombre de un velero ya que el balandro era una embarcación ligera y maniobrable, muy apreciada por los piratas.'

    txt += '[CR][CR][COLOR gold]¿ Qué características tiene Balandro ?[/COLOR][CR]'
    txt += 'Principalmente permite acceder a los contenidos de webs con vídeos de películas y series para reproducirlos y/o guardarlos, y'
    txt += ' dispone de una videoteca propia dónde poder apuntar todas las pelis y series que interesen al usuario.'
    txt += ' Se pueden configurar múltiples opciones, por ejemplo la preferencia de idioma, la reproducción automática, los colores para los listados, los servidores preferidos, etc.'

    txt += '[CR][CR][COLOR gold]¿ Cómo funciona el Autoplay ?[/COLOR][CR]'
    txt += 'Se puede activar la función de reproducción automática desde la configuración del addon.'
    txt += ' Si se activa, al ver una película o episodio se intenta reproducir el primero de los enlaces que funcione, sin mostrarse el diálogo de selección de servidor.'
    txt += ' Los enlaces se intentan secuencialmente en el mismo orden que se vería en el diálogo, por lo que es importante haber establecido las preferencias de idioma y servidores.'

    txt += '[CR][CR][COLOR gold]¿ En qué orden se muestran los enlaces de servidores ?[/COLOR][CR]'
    txt += 'El orden inicial es por la fecha de los enlaces, para tener al principio los últimos actualizados ya que es más probable que sigan vigentes, aunque en los canales que no lo informan es según el orden que devuelve la web.'
    txt += ' Desde la configuración se puede activar el ordenar por calidades, pero su utilidad va a depender de lo que muestre cada canal y la fiabilidad que tenga.'
    txt += ' A partir de aquí, si hay preferencias de servidores en la configuración, se cambia el orden para mostrar al principio los servidores preferentes y al final los de última opción.'
    txt += ' Y finalmente se agrupan en función de las preferencias de idiomas del usuario.'

    txt += '[CR][CR][COLOR gold]¿ Funcionan los enlaces Torrent ?[/COLOR][CR]'
    txt += 'El addon está preparado para tratarlos usando un gestor de torrents externo, tipo Quasar, Elementum, etc.'
    txt += ' De momento hay pocos canales que tengan torrents, pero se puede probar su uso en el canal cinecalidad o en los clones de newpct1.'

    platformtools.dialog_textviewer('FAQ - Preguntas y respuestas', txt)


def show_help_tracking(item):
    logger.info()

    txt = '[COLOR gold]¿ Cómo se guardan las películas o series ?[/COLOR][CR]'
    txt += 'Desde cualquiera de los canales dónde se listen películas o series, accede al menú contextual y selecciona "Guardar peli/serie".'
    txt += ' En el caso de películas es casi instantáneo, y para series puede demorarse unos segundos si tiene muchas temporadas/episodios.'
    txt += ' Para ver y gestionar todo lo que tengas, accede a "Enlaces guardados" desde el menú principal del addon.'
    txt += ' También puedes guardar una temporada o episodios concretos.'

    txt += '[CR][CR][COLOR gold]¿ Qué pasa si una película/serie no está correctamente identificada ?[/COLOR][CR]'
    txt += 'Esto puede suceder cuando la peli/serie no está bien escrita en la web de la que procede o si hay varias películas con el mismo título.'
    txt += ' Si no se detecta te saldrá un diálogo para seleccionar entre varias opciones o para cambiar el texto de búsqueda.'
    txt += ' Desde las opciones de configuración puedes activar que se muestre siempre el diálogo de confirmación, para evitar que se detecte incorrectamente.'

    txt += '[CR][CR][COLOR gold]¿ Y si no se puede identificar la película/serie ?[/COLOR][CR]'
    txt += 'Es necesario poder identificar cualquier peli/serie en TMDB, sino no se puede guardar.'
    txt += ' Si no existe en http://themoviedb.org o tiene datos incompletos puedes completar allí la información ya que es un proyecto comunitario y agradecerán tu aportación.'

    txt += '[CR][CR][COLOR gold]¿ Se puede guardar la misma película/serie desde canales diferentes ?[/COLOR][CR]'
    txt += 'Sí, al guardar se apuntan en la base de datos interna los datos propios de la peli, serie, temporada o episodio, y también el enlace al canal de dónde se ha guardado.'
    txt += ' De esta manera puedes tener diferentes alternativas por si algún canal fallara o no tuviera enlaces válidos.'
    txt += ' Si tienes enlaces de varios canales, al reproducir podrás escoger en cual intentarlo.'

    txt += '[CR][CR][COLOR gold]¿ Se guardan las marcas de películas/episodios ya vistos ?[/COLOR][CR]'
    txt += 'Sí, Kodi gestiona automáticamente las marcas de visto/no visto.'
    txt += ' Estas marcas están en la base de datos de Kodi pero no en las propias de Balandro.'

    txt += '[CR][CR][COLOR gold]¿ Qué pasa si un enlace guardado deja de funcionar ?[/COLOR][CR]'
    txt += 'A veces las webs desaparecen o cambian de estructura y/o de enlaces y eso provoca que enlaces guardados dejen de ser válidos.'
    txt += ' Al acceder a un enlace que da error, se muestra un diálogo para escoger si se quiere "Buscar en otros canales" o "Volver a buscar en el mismo canal".'
    txt += ' Si la web ha dejado de funcionar deberás buscar en otros canales, pero si ha sufrido cambios puedes volver a buscar en ella.'

    txt += '[CR][CR][COLOR gold]¿ Se puede compartir una lista de enlaces guardados ?[/COLOR][CR]'
    txt += 'De momento puedes hacerlo manualmente. En la carpeta userdata del addon, dentro de "tracking_dbs" están los ficheros .sqlite de cada lista que tengas creada.'
    txt += ' Puedes copiar estos ficheros y copiarlos a otros dispositivos.'

    txt += '[CR][CR][COLOR gold]¿ Cómo invertir el orden de los episodios ?[/COLOR][CR]'
    txt += 'Por defecto los episodios dentro de una temporada se muestran en orden ascendente, del primero al último.'
    txt += ' Si prefieres que sea al revés, desde el menú contextual de una temporada selecciona "Invertir el orden de los episodios" y'
    txt += ' tu preferencia quedará guardada para esa temporada.'

    platformtools.dialog_textviewer('Funcionamiento de los enlaces guardados (videoteca)', txt)


def show_help_tracking_update(item):
    logger.info()

    txt = '[COLOR gold]¿ Qué es el servicio de búsqueda de nuevos episodios ?[/COLOR][CR]'
    txt += 'El servicio es un proceso del addon que se ejecuta al iniciarse Kodi, y se encarga de comprobar cuando hay que buscar actualizaciones.'
    txt += ' En la configuración dentro de "Actualizaciones" puedes indicar cada cuanto tiempo deben hacerse las comprobaciones.'
    txt += ' Por defecto es dos veces al día, cada 12 horas, pero puedes cambiarlo.'
    txt += ' Si lo tienes desactivado, puedes ejecutar manualmente la misma búsqueda desde el menú contextual de "Series" dentro de los "Enlaces guardados".'

    txt += '[CR][CR][COLOR gold]¿ Cómo se activa la búsqueda de nuevos episodios para series ?[/COLOR][CR]'
    txt += 'Desde el listado de series dentro de "Enlaces guardados" accede a "Gestionar serie" desde el menú contextual.'
    txt += ' Al seleccionar "Programar búsqueda automática de nuevos episodios" podrás definir el seguimiento que quieres darle a la serie'
    txt += ' e indicar cada cuanto tiempo hay que hacer la comprobación de si hay nuevos episodios.'

    txt += '[CR][CR][COLOR gold]¿ Cómo se combina el servicio con las series ?[/COLOR][CR]'
    txt += 'Cada vez que se ejecuta el servicio (1, 2, 3 o 4 veces por día) se buscan las series que tienen activada la búsqueda automática.'
    txt += ' Por cada serie según su propia periodicidad se ejecuta o no la búsqueda.'
    txt += ' Esto permite por ejemplo tener series que sólo requieren una actualización por semana, y otras dónde conviene comprobar cada día.'

    txt += '[CR][CR][COLOR gold]¿ Por qué la búsqueda de nuevos episodios está desactivada por defecto ?[/COLOR][CR]'
    txt += 'Es preferible ser prudente con las actualizaciones para no saturar más las webs de dónde se obtiene la información.'
    txt += ' Por esta razón al guardar series por defecto no tienen activada la comprobación de nuevos episodios y hay que indicarlo explícitamente si se quiere.'
    txt += ' Si por ejemplo sigues una serie ya terminada seguramente no necesitarás buscar nuevos episodios, en cambio si sigues una serie de un show diario sí te interesará.'

    txt += '[CR][CR][COLOR gold]¿ Dónde se ven los nuevos episodios encontrados ?[/COLOR][CR]'
    txt += 'En "Enlaces guardados" estarán dentro de sus series respectivas, pero también se puede ver un listado de los últimos episodios añadidos'
    txt += ' por fecha de emisión o de actualización.'

    platformtools.dialog_textviewer('Búsqueda automática de nuevos episodios', txt)


def show_changelog(item):
    logger.info()
    
    import os

    with open(os.path.join(config.get_runtime_path(), 'changelog.txt'), 'r') as f: txt=f.read(); f.close()

    platformtools.dialog_textviewer('Historial de cambios', txt)
