# -*- coding: utf-8 -*-
import pickle
import random
from core.libs import *

import libtorrent as lt

from cache import Cache
from dispatcher import Dispatcher
from file import File
from handler import Handler
from monitor import Monitor
from resume_data import ResumeData
from server import Server


class Client(object):
    initial_trackers = [
        'udp://tracker.openbittorrent.com:80',
        'udp://tracker.istole.it:80',
        'udp://open.demonii.com:80',
        'udp://tracker.coppersurfer.tk:80',
        'udp://tracker.leechers-paradise.org:6969',
        'udp://exodus.desync.com:6969',
        'udp://tracker.publicbt.com:80'
    ]

    video_exts = {
        '.avi': 'video/x-msvideo', '.mp4': 'video/mp4', '.mkv': 'video/x-matroska',
        '.m4v': 'video/mp4', '.mov': 'video/quicktime', '.mpg': 'video/mpeg', '.ogv': 'video/ogg',
        '.ogg': 'video/ogg', '.webm': 'video/webm', '.ts': 'video/mp2t', '.3gp': 'video/3gpp'
    }

    def __init__(self, url=None, port=None, ip=None, auto_shutdown=True, wait_time=20, timeout=5, auto_delete=True,
                 temp_path=None, is_playing_fnc=None, print_status=False):

        # server
        self.port = port or random.randint(8000, 8099)
        self.ip = ip or "127.0.0.1"
        self.server = Server((self.ip, self.port), Handler, client=self)

        # Options
        self.temp_path = temp_path or os.path.join(os.path.dirname(__file__), "tmp")
        self.is_playing_fnc = is_playing_fnc
        self.timeout = timeout
        self.auto_delete = auto_delete
        self.wait_time = wait_time
        self.auto_shutdown = auto_shutdown
        self.buffer_size = 10
        self.last_pieces_priorize = 1
        self.state_file = "state"
        self.torrent_paramss = {'save_path': self.temp_path, 'storage_mode': lt.storage_mode_t.storage_mode_sparse}

        # State
        self.has_meta = False
        self.meta = None
        self.start_time = None
        self.last_connect = 0
        self.connected = False
        self.closed = False
        self.files = []
        self.th = None

        # Sesion
        self.cache = Cache(self.temp_path)
        self.ses = lt.session()
        self.ses.listen_on(0, 0)

        # Cargamos el archivo de estado (si esxiste)
        if os.path.exists(os.path.join(self.temp_path, self.state_file)):
            try:
                f = open(os.path.join(self.temp_path, self.state_file), "rb")
                state = pickle.load(f)
                self.ses.load_state(state)
                f.close()
            except Exception:
                pass

        self._start_services()

        # Monitor & Dispatcher
        self._monitor = Monitor(self)
        if print_status:
            self._monitor.add_listener(self.print_status)
        self._monitor.add_listener(self._check_meta)
        self._monitor.add_listener(self.save_state)
        self._monitor.add_listener(self.priorize_service)
        self._monitor.add_listener(self.announce_torrent)

        if self.auto_shutdown:
            self._monitor.add_listener(self._auto_shutdown)

        self._dispatcher = Dispatcher(self)
        self._dispatcher.add_listener(self._update_ready_pieces)

        # Iniciamos la URL
        if url:
            self.start_url(url)

    def wait_metadata(self):
        while not self.has_meta:
            time.sleep(1)

    def get_play_list(self):
        """
        Función encargada de generar el playlist
        """

        # Esperamos a lo metadatos
        self.wait_metadata()

        # Comprobamos que haya archivos de video
        if self.files:
            if len(self.files) > 1:
                return "http://" + self.ip + ":" + str(self.port) + "/playlist.pls"
            else:
                return "http://" + self.ip + ":" + str(self.port) + "/" + urllib.quote(self.files[0].path)

    def get_files(self):
        """
        Función encargada de genera el listado de archivos
        """

        # Esperamos a lo metadatos
        self.wait_metadata()

        files = []

        # Comprobamos que haya archivos de video
        if self.files:
            # Creamos el dict con los archivos
            for f in self.files:
                n = f.path
                u = "http://" + self.ip + ":" + str(self.port) + "/" + urllib.quote(n)
                s = f.size
                files.append({"name": n, "url": u, "size": s})

        return files

    def _find_files(self, files):
        """
        Función encargada de buscar los archivos reproducibles del torrent
        """
        # Obtenemos los archivos que la extension este en la lista
        videos = filter(lambda f: os.path.splitext(f.path)[1] in self.video_exts, files)

        if not videos:
            raise Exception('No video files in torrent')

        result = []
        for v in videos:
            v.index = files.index(v)
            result.append(File(v, self.temp_path, self.meta.map_file(v.index, 0, 1), self.meta.piece_length(), self))

        return result

    def set_file(self, f):
        """
        Función encargada de seleccionar el archivo que vamos a servir y por tanto precargar el buffer
        """
        if isinstance(f, str):
            for ff in self.files:
                if ff.path == f:
                    ff.wait_initial_buffer(True)
                    return ff
        else:
            f.wait_initial_buffer()

    @staticmethod
    def download_torrent(url):
        """
        Función encargada de descargar un archivo .torrent
        """
        data = httptools.downloadpage(url).data
        return data

    def start_url(self, uri):
        """
        Función encargada iniciar la descarga del torrent desde la url, permite:
          - Url apuntando a un .torrent
          - Url magnet
          - Archivo .torrent local
        """

        if self.th:
            raise Exception('Torrent is already started')

        if uri.startswith('http://') or uri.startswith('https://'):
            torrent_data = self.download_torrent(uri)
            info = lt.torrent_info(lt.bdecode(torrent_data))
            tp = {'ti': info}
            resume_data = self.cache.get_resume(info_hash=str(info.info_hash()))
            if resume_data:
                tp['resume_data'] = resume_data

        elif uri.startswith('magnet:'):
            tp = {'url': uri}
            resume_data = self.cache.get_resume(info_hash=Cache.hash_from_magnet(uri))
            if resume_data:
                tp['resume_data'] = resume_data

        elif os.path.isfile(uri):
            if os.access(uri, os.R_OK):
                info = lt.torrent_info(uri)
                tp = {'ti': info}
                resume_data = self.cache.get_resume(info_hash=str(info.info_hash()))
                if resume_data:
                    tp['resume_data'] = resume_data
            else:
                raise ValueError('Invalid torrent path %s' % uri)
        else:
            raise ValueError("Invalid torrent %s" % uri)

        tp.update(self.torrent_paramss)
        self.th = self.ses.add_torrent(tp)

        for tr in self.initial_trackers:
            self.th.add_tracker({'url': tr})

        self.th.set_sequential_download(True)
        self.th.force_reannounce()
        self.th.force_dht_announce()

        self._monitor.start()
        self._dispatcher.do_start(self.th, self.ses)
        self.server.run()

    def stop(self):
        """
        Función encargada de de detener el torrent y salir
        """
        self._dispatcher.stop()
        self._dispatcher.join()
        self._monitor.stop()
        self.server.stop()
        if self.ses:
            self.ses.pause()
            if self.th:
                ResumeData(self).save_resume_data()
            self.save_state()
        self._stop_services()
        self.ses.remove_torrent(self.th, self.auto_delete)
        del self.ses
        self.closed = True

    def _start_services(self):
        """
        Función encargada de iniciar los servicios de libtorrent: dht, lsd, upnp, natpnp
        """
        self.ses.add_dht_router("router.bittorrent.com", 6881)
        self.ses.add_dht_router("router.bitcomet.com", 554)
        self.ses.add_dht_router("router.utorrent.com", 6881)
        self.ses.start_dht()
        self.ses.start_lsd()
        self.ses.start_upnp()
        self.ses.start_natpmp()

    def _stop_services(self):
        """
        Función encargada de detener los servicios de libtorrent: dht, lsd, upnp, natpnp
        """
        self.ses.stop_natpmp()
        self.ses.stop_upnp()
        self.ses.stop_lsd()
        self.ses.stop_dht()

    @property
    def buffer_status(self):
        s = []
        if not self.files:
            return 0

        for x in self.files:
            if x.buffering:
                s.append(len([p for p in x.buffer if x.buffer[p]]) * 100 / len(x.buffer))

        if s:
            return sum(s) / len(s)
        else:
            return 100

    @property
    def active_file(self):
        for f in self.files:
            if f.cursors:
                return f

    @property
    def status(self):
        """
        Función encargada de devolver el estado del torrent
        """
        if self.th:
            s = self.th.status()
            st = dict([(a, getattr(s, a)) for a in dir(s) if not a.startswith('__')])
            # Download Rate
            st['download_rate'] = s.download_rate / 1000

            # Progreso del archivo
            if self.active_files:
                pieces = s.pieces[self.active_file.first_piece:self.active_file.last_piece]
                progress = float(sum(pieces)) / len(pieces)
            else:
                progress = 0

            st['progress_file'] = progress * 100

            # Tamaño del archivo
            if self.active_file:
                st['file_size'] = self.active_file.size / 1048576.0
            else:
                st['file_size'] = 0

            # Estado del buffer
            st['buffer'] = self.buffer_status

            # Tiempo restante para cerrar en caso de tener el timeout activo
            if self.auto_shutdown:
                if self.connected:
                    if self.timeout:
                        st['timeout'] = int(self.timeout - (time.time() - self.last_connect - 1))
                        if self.active_file and self.active_file.cursors:
                            st['timeout'] = self.timeout
                        if st['timeout'] < 0:
                            st['timeout'] = "Cerrando"
                    else:
                        st['timeout'] = "---"
                else:
                    if self.start_time and self.wait_time:
                        st['timeout'] = int(self.wait_time - (time.time() - self.start_time - 1))
                        if st['timeout'] < 0:
                            st['timeout'] = "Cerrando"
                    else:
                        st['timeout'] = "---"

            else:
                st['timeout'] = "Off"

            # Estado de la descarga
            STATE_STR = ['En cola', 'Comprobando', 'Descargando metadata', 'Descargando', 'Finalizado', 'Seeding',
                         'Allocating', 'Comprobando fastresume']
            st['str_state'] = STATE_STR[s.state]

            # Estado DHT
            if self.ses.dht_state() is not None:
                st['dht_state'] = "On"
                st['dht_nodes'] = self.ses.status().dht_nodes
            else:
                st['dht_state'] = "Off"
                st['dht_nodes'] = 0

            # Cantidad de Trackers
            st['trackers'] = len(self.th.trackers())

            # Origen de los peers
            st['dht_peers'] = 0
            st['trk_peers'] = 0
            st['pex_peers'] = 0
            st['lsd_peers'] = 0

            for peer in self.th.get_peer_info():
                if peer.source & 1:
                    st['dht_peers'] += 1
                if peer.source & 2:
                    st['trk_peers'] += 1
                if peer.source & 4:
                    st['pex_peers'] += 1
                if peer.source & 8:
                    st['lsd_peers'] += 1

            return type('', (), st)

    """
    Servicios:
      - Estas funciones se ejecutan de forma automatica cada x tiempo en otro Thread.
      - Estas funciones son ejecutadas mientras el torrent esta activo algunas pueden desactivarse 
        segun la configuracion como por ejemplo la escritura en el log
    """

    def _auto_shutdown(self, *args, **kwargs):
        """
        Servicio encargado de autoapagar el servidor
        """

        if self.active_file and self.active_file.cursors:
            self.last_connect = time.time()
            self.connected = True

        if self.is_playing_fnc and self.is_playing_fnc():
            self.last_connect = time.time()
            self.connected = True

        if self.auto_shutdown:
            # shudown por haber cerrado el reproductor
            if self.connected and self.is_playing_fnc and not self.is_playing_fnc():
                if time.time() - self.last_connect - 1 > self.timeout:
                    self.stop()

            # shutdown por no realizar ninguna conexion
            if (
                    not self.active_file or not self.active_file.cursors) and self.start_time and self.wait_time and not self.connected:
                if time.time() - self.start_time - 1 > self.wait_time:
                    self.stop()

            # shutdown tras la ultima conexion
            if (
                    not self.active_file or not self.active_file.cursors) and self.timeout and self.connected and not self.is_playing_fnc:
                if time.time() - self.last_connect - 1 > self.timeout:
                    self.stop()

    def announce_torrent(self):
        """
        Servicio encargado de anunciar el torrent
        """
        self.th.force_reannounce()
        self.th.force_dht_announce()

    def save_state(self):
        """
        Servicio encargado de guardar el estado
        """
        state = self.ses.save_state()
        f = open(os.path.join(self.temp_path, self.state_file), 'wb')
        pickle.dump(state, f)
        f.close()

    def _update_ready_pieces(self, alert_type, alert):
        """
        Servicio encargado de informar que hay una pieza disponible
        """
        if alert_type == 'read_piece_alert':
            for f in self.files:
                f.add_to_buffer(alert.piece, alert.buffer)

    def _check_meta(self):
        """
        Servicio encargado de comprobar si los metadatos se han descargado
        """
        if 3 <= self.status.state <= 5 and not self.has_meta:

            # Guardamos los metadatos
            self.meta = self.th.get_torrent_info()

            # Obtenemos la lista de archivos del meta
            fs = self.meta.files()
            if isinstance(fs, list):
                files = fs
            else:
                files = [fs.at(i) for i in xrange(fs.num_files())]

            # Guardamos la lista de archivos
            self.files = self._find_files(files)

            # Marcamos el primer archivo como activo
            self.set_file(self.files[0])

            # Damos por iniciada la descarga
            self.start_time = time.time()

            # Guardamos el .torrent en el cahce
            self.cache.file_complete(self.th.get_torrent_info())
            print self.th.get_torrent_info()
            self.has_meta = True

    def priorize_service(self):
        """
        Servicio encargado de priorizar el principio y final de archivo cuando no hay conexion
        """
        for f in self.files:
            if f.buffering:
                if self.th.file_priority(f.index) !=7:
                    self.th.file_priority(f.index, 7)

            elif f.cursors:
                if self.th.file_priority(f.index) !=7:
                    self.th.file_priority(f.index, 7)
            else:
                if self.th.file_priority(f.index) !=1:
                    self.th.file_priority(f.index, 1)

    @property
    def active_files(self):
        return [f for f in self.files if f.cursors]

    def print_status(self):
        """
        Servicio encargado de mostrar en el log el estado de la descarga
        """
        s = self.status
        logger.debug('%.2f%% de %.1fMB %s | %.1f kB/s | AutoClose: %s | S: %d(%d) P: %d(%d)) | '
                     'TRK: %d DHT: %d PEX: %d LSD %d | DHT:%s (%d) | Trakers: %d' % (
                         s.progress_file,
                         s.file_size,
                         s.str_state,
                         s.download_rate,
                         s.timeout,
                         s.num_seeds,
                         s.num_complete,
                         s.num_peers,
                         s.num_incomplete,
                         s.trk_peers,
                         s.dht_peers,
                         s.pex_peers,
                         s.lsd_peers,
                         s.dht_state,
                         s.dht_nodes,
                         s.trackers
                     ))
        for f in self.files:
            for l in str(f).splitlines():
                logger.debug(l)
        logger.debug('_____________________________________________________________________')