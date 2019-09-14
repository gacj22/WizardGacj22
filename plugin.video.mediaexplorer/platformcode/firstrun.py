# -*- coding: utf-8 -*-
import xbmc
import xbmcgui

from core.libs import *


class FirstRun(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        logger.trace()
        skin = 'Estuary' if xbmc.getSkinDir() == 'skin.estuary' else 'Default'
        self.mediapath = os.path.join(sysinfo.runtime_path, 'resources', 'skins', skin, 'media')
        self.restart = False
        self.step = 0

    def set_step(self):
        self.getControl(10007).setVisible(False)
        self.getControl(10008).setVisible(False)
        if self.step == 0:
            self.getControl(10004).setLabel('[B]¡Bienvenido a MediaExplorer![/B]')
            self.getControl(10005).setText('Con este addon podrá disfrutar de sus películas y series favoritas '
                                           'navegando de manera fácil, sencilla y segura desde su mediacenter.\n\n'
                                           'Busque entre las diferentes webs disponibles de '
                                           'manera simultánea.\n'
                                           'Añada accesos directos a las diferentes secciones o contenidos de '
                                           'MediaExplorer en los \'Favoritos\' de Kodi para tenerlos siempre'
                                           ' a mano.\n'
                                           'Visualice en pocos segundos las novedades añadidas en sus '
                                           'canales preferidos.\n'
                                           'Comparta un listado de enlaces recomendados con sus familiares y amigos.\n'
                                           'Y muchas mas funcionalidades que le invitamos a descubrir.\n\n'
                                           'Dediquemos un momento a configurar MediaExplorer antes de comenzar.\n\n'
                                           'Haga click en Empezar cuando esté preparado.')
            self.getControl(10006).setLabel('Empezar')
            self.setFocusId(10006)

        elif self.step == 1:
            self.getControl(10004).setLabel('[B]Aviso legal[/B]')
            msg = "1.- El material disponible a través de MediaExplorer, ha sido recolectado de sitios webs que son " \
                  "públicos (hdfull.tv, plusdede.com, seriesblanco.com, etc...), organizados como canales. " \
                  "Por lo que este material es considerado de libre distribución y su uso indebido no será nunca " \
                  "responsabilidad de los creadores o colaboradores de MediaExplorer.\n" \
                  "2.- Todos los vídeos que figuran en este addon son solo enlaces que han sido " \
                  "obtenidos de páginas como powvideo.net, openload.co, youtube.com, netu.tv, etc. " \
                  "Por lo tanto MediaExplorer solo se limita a facilitar la visibilidad de los vídeos a través de " \
                  "los enlaces de estos y otros servidores.\n" \
                  "3.- MediaExplorer, no aloja vídeos ni distribuye ningún tipo de archivo para streaming o descarga. " \
                  "El único material que proporciona son enlaces de webs de libre distribución. Por consiguiente " \
                  "solo los canales y servidores son plenamente responsables de los contenidos que publiquen.\n" \
                  "4.- Los canales y servidores podrían, en algún caso, publicar vídeos con contenido no apto." \
                  " MediaExplorer cuenta con un apartado exclusivo para adultos " \
                  "(por defecto deshabilitado), pero no puede garantizar que todo el material de este tipo se " \
                  "filtre correctamente. Usted es responsable de proteger a los menores de esta exposición.\n" \
                  "5.- Si este tipo de contenido esta prohibido en su país, solamente usted es responsable del uso" \
                  " de MediaExplorer.\n\n" \
                  "Si ha leído, comprendido y acepta estas condiciones pulse Aceptar.\n" \
                  "En caso contrario, pulse Cancelar"
            self.getControl(10005).setText(msg)
            self.getControl(10006).setLabel('Aceptar')
            self.getControl(10008).setLabel('Cancelar')
            self.getControl(10008).setVisible(True)
            self.setFocusId(10006)

        elif self.step == 2:
            self.getControl(10004).setLabel('[B]Normas de uso y distribución[/B]')
            self.getControl(10005).setText('MediaExplorer es un software [B]gratuito[/B] con licencia GPLv3.\n\n'
                                           'No obstante, no se permite su distribuición preinstalada en ningún tipo '
                                           'de dispositivo ni tampoco su inclusión total o parcial en cualquier '
                                           'paquete de software y/o hardware por el que el usuario final deba pagar '
                                           'su adquisición, uso o asistencia.\n\n'
                                           'Tampoco se permite ninguna modificación del codigo que tenga por objeto '
                                           'contravenir el significado del párrafo anterior o incluir imágenes, '
                                           'vídeos o sonidos sujetos a derechos de autor y que pudieran incumplir '
                                           'el [B]Aviso Legal antes aceptado.[/B]\n\n'
                                           'Si cree que alguna de estas normas no se está cumpliendo póngase en '
                                           'contacto con nosotros.'
                                           )
            self.getControl(10006).setLabel('Continuar')
            self.getControl(10008).setVisible(False)
            self.setFocusId(10006)

        elif self.step == 3:
            self.getControl(10004).setLabel('[B]Vamos a configurar la biblioteca[/B]')
            self.getControl(10005).setText('MediaExplorer dispone de una sección \'Biblioteca\', donde puede '
                                           'añadir enlaces a películas y series para verlas mas fácilmente '
                                           'cuando quiera.\n\n'
                                           'La biblioteca se puede integrar en Kodi, para acceder a su '
                                           'contenido desde la sección \'Peliculas\' y \'Series\' de Kodi\n\n'
                                           '¿Quiere integrar ahora la biblioteca de MediaExplorer en Kodi?'
                                           )
            self.getControl(10008).setLabel('No')
            self.getControl(10006).setVisible(False)
            self.getControl(10007).setVisible(True)
            self.getControl(10008).setVisible(True)
            self.setFocusId(10007)

        elif self.step == 4:
            self.getControl(10004).setLabel('[B]Librerías externas[/B]')
            self.getControl(10005).setText('Buscando librerias externas disponibles...')

            # Instalar librerias disponibles
            from core  import libraries
            libraries.autointall()

            opciones_disponibles = []
            opciones_no_disponibles = []
            if xbmc.getCondVisibility('System.HasAddon("plugin.video.xbmctorrent")'):
                opciones_disponibles.append('    Reproductor Torrent: XBMCtorrent')
            else:
                opciones_no_disponibles.append('    Reproductor Torrent: XBMCtorrent')

            if xbmc.getCondVisibility('System.HasAddon("plugin.video.pulsar")'):
                opciones_disponibles.append('    Reproductor Torrent: Pulsar')
            else:
                opciones_no_disponibles.append('    Reproductor Torrent: Pulsar')

            if xbmc.getCondVisibility('System.HasAddon("plugin.video.quasar")'):
                opciones_disponibles.append('    Reproductor Torrent: Quasar')
            else:
                opciones_no_disponibles.append('    Reproductor Torrent: Quasar')

            if xbmc.getCondVisibility('System.HasAddon("plugin.video.stream")'):
                opciones_disponibles.append('    Reproductor Torrent: Stream')
            else:
                opciones_no_disponibles.append('    Reproductor Torrent: Stream')

            if xbmc.getCondVisibility('System.HasAddon("plugin.video.torrenter")'):
                opciones_disponibles.append('    Reproductor Torrent: Torrenter')
            else:
                opciones_no_disponibles.append('    Reproductor Torrent: Torrenter')

            if xbmc.getCondVisibility('System.HasAddon("plugin.video.torrentin")'):
                opciones_disponibles.append('    Reproductor Torrent: Torrentin')
            else:
                opciones_no_disponibles.append('    Reproductor Torrent: Torrentin')

            if xbmc.getCondVisibility('System.HasAddon("plugin.video.elementum")'):
                opciones_disponibles.append('    Reproductor Torrent: Elementum')
            else:
                opciones_no_disponibles.append('    Reproductor Torrent: Elementum')

            try:
                import libtorrent
                opciones_disponibles.append('    Reproductor Torrent interno')
            except Exception:
                opciones_no_disponibles.append('    Reproductor Torrent interno')

            try:
                from megaserver import client
                opciones_disponibles.append('    Soporte para servidor Mega nativo')
            except Exception:
                opciones_no_disponibles.append('    Soporte para servidor Mega nativo')


            msg = 'MediaExplorer se distribuye preparado para funcionar. Pero puede interactuar ' \
                  'con otras librerías o añadidos externos para una mejor experiencia.\n\n'

            if opciones_disponibles:
                msg += 'Funciones disponibles:\n%s\n\n' % '\n'.join(opciones_disponibles)

            if opciones_no_disponibles:
                msg += 'Funciones no disponibles:\n%s\n' % '\n'.join(opciones_no_disponibles)

            self.getControl(10005).setText(msg)
            self.getControl(10006).setVisible(True)
            self.setFocusId(10006)
        elif self.step == 5:
            self.getControl(10004).setLabel('[B]¡Ya hemos terminado![/B]')
            self.getControl(10005).setText('MediaExplorer ya está listo para ser utilizado.\n\n'
                                           'Aunque le recomendamos que compruebe si hay novedades disponibles '
                                           'en el apartado \'Actualizaciones\'.\n\n'
                                           'También puede mejorar el funcionamiento de MediaExplorer entrando '
                                           'en las diferentes secciones de \'Ajustes\'.\n\n'
                                           '¡Esperamos que lo disfrute!'
                                           )
            self.getControl(10006).setLabel('Finalizar')
            self.getControl(10006).setVisible(True)
            self.getControl(10007).setVisible(False)
            self.getControl(10008).setVisible(False)
            self.setFocusId(10006)

        else:
            self.close()

    def start(self):
        logger.trace()
        settings.set_setting('first_run', True)
        self.doModal()
        if self.step == 1:
            settings.set_setting('first_run', False)
            return False
        if self.restart:
            platformtools.dialog_ok(
                'MediaExplorer',
                'Debe reiniciar kodi para que MediaExplorer funcione correctamente.')
            # TODO ¿quiere reiniciar ahora?
        return True

    def onInit(self):
        logger.trace()
        self.set_step()

    def onClick(self, cont_id):
        logger.trace()

        if cont_id == 10006:
            self.step += 1
            self.set_step()

        if cont_id == 10007:
            if self.step == 3:
                from platformcode import library_tools
                library_tools.integrate()
                self.restart = True
            self.step += 1
            self.set_step()

        if cont_id == 10008:
            if self.step == 1:
                self.close()
            else:
                self.step += 1
                self.set_step()

    def onAction(self, raw_action):
        c_id = self.getFocusId()
        action = raw_action.getId()

        # Accion 1: Flecha izquierda
        if action == 1:
            if c_id == 10007:
                self.setFocusId(10008)

        # Accion 1: Flecha derecha
        elif action == 2:
            if c_id == 10008:
                self.setFocusId(10007)
