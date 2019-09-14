# -*- coding: utf-8 -*-
from core.libs import *
import threading
import mimetypes


class Downloader:
    @property
    def state(self):
        return self._state

    @property
    def connections(self):
        return len(
            [c for c in self._download_info["parts"] if
             c["status"] in [self.states.downloading, self.states.connecting]]
        ), self._max_connections

    @property
    def downloaded(self):
        return self.__change_units__(sum([c["current"] - c["start"] for c in self._download_info["parts"]]))

    @property
    def average_speed(self):
        return self.__change_units__(self._average_speed)

    @property
    def speed(self):
        return self.__change_units__(self._speed)

    @property
    def remaining_time(self):
        if self.speed[0] and self._file_size:
            t = (self.size[0] - self.downloaded[0]) / self.speed[0]
        else:
            t = 0

        return time.strftime("%H:%M:%S", time.gmtime(t))

    @property
    def download_url(self):
        return self.url

    @property
    def size(self):
        return self.__change_units__(self._file_size)

    @property
    def progress(self):
        if self._file_size:
            return float(self.downloaded[0]) * 100 / float(self._file_size)
        elif self._state == self.states.completed:
            return 100
        else:
            return 0

    @property
    def filename(self):
        return self._filename

    @property
    def fullpath(self):
        return os.path.abspath(filetools.join(self._path, self._filename))

    # Funciones
    def start_dialog(self, title="Descargando..."):
        dialog = platformtools.dialog_progress(title, "Iniciando descarga...")
        self.start()
        while self.state == self.states.downloading and not dialog.iscanceled():
            time.sleep(0.1)
            line1 = "%s" % self.filename
            line2 = "%.2f%% - %.2f %s de %.2f %s a %.2f %s/s (%d/%d)" % (
                self.progress,
                self.downloaded[1],
                self.downloaded[2],
                self.size[1],
                self.size[2],
                self.speed[1],
                self.speed[2],
                self.connections[0],
                self.connections[1]
            )
            line3 = "Tiempo restante: %s" % self.remaining_time

            dialog.update(int(self.progress), line1, line2, line3)

        if self.state == self.states.downloading:
            self.stop()

        dialog.close()

    def start(self):
        if self._state == self.states.error:
            return

        conns = []

        for x in range(self._max_connections):
            try:
                conns.append(self.__open_connection__("0", ""))
            except Exception:
                self._max_connections = x
                self._threads = [Thread(
                    target=self.__start_part__,
                    name="Downloader %s/%s" % (x + 1, self._max_connections)
                ) for x in range(self._max_connections)]
                break

        del conns

        self._start_time = time.time() - 1
        self._state = self.states.downloading
        self._speed_thread.start()
        self._save_thread.start()

        for t in self._threads:
            t.start()

    def stop(self, erase=False):
        if self._state == self.states.downloading:
            # Detenemos la descarga
            self._state = self.states.stopped
            for t in self._threads:
                if t.isAlive():
                    t.join()

            if self._save_thread.isAlive():
                self._save_thread.join()

            if self._seekable:
                # Guardamos la info al final del archivo
                self.file.seek(0, 2)
                offset = self.file.tell()
                self.file.write(str(self._download_info))
                self.file.write("%0.16d" % offset)

        self.file.close()

        if erase:
            os.remove(filetools.join(self._path, self._filename + '.tmp'))

    def __speed_metter__(self):
        self._speed = 0
        self._average_speed = 0

        downloaded = self._start_downloaded
        downloaded2 = self._start_downloaded
        t = time.time()
        t2 = time.time()
        time.sleep(1)

        while self.state == self.states.downloading:
            self._average_speed = (self.downloaded[0] - self._start_downloaded) / (time.time() - self._start_time)
            # self._speed = (self.downloaded[0] - self._start_downloaded) / (time.time() - self._start_time)
            self._speed = (self.downloaded[0] - downloaded) / (time.time() - t)

            if time.time() - t > 5:
                t = t2
                downloaded = downloaded2
                t2 = time.time()
                downloaded2 = self.downloaded[0]

            time.sleep(0.5)

    # Funciones internas
    def __init__(self, url, path, filename=None, headers=None, resume=True, max_connections=10, block_size=2 ** 17,
                 part_size=2 ** 24, max_buffer=10):

        # Parametros
        self._resume = resume
        self._path = path
        self._filename = filename
        self._max_connections = max_connections
        self._block_size = block_size
        self._part_size = part_size
        self._max_buffer = max_buffer
        self.url = url

        self.tmp_path = sysinfo.temp_path

        self.states = type('states', (), {
            "stopped": 0,
            "connecting": 1,
            "downloading": 2,
            "completed": 3,
            "error": 4,
            "saving": 5
        })

        self._state = self.states.stopped
        self._download_lock = Lock()
        self._headers = httptools.default_headers
        self._speed = 0
        self._start_time = None
        self._buffer = {}
        self._seekable = True

        self._threads = [
            Thread(
                target=self.__start_part__,
                name="Downloader %s/%s" % (x + 1, self._max_connections)
            )
            for x in range(self._max_connections)
        ]

        self._speed_thread = Thread(target=self.__speed_metter__, name="Speed Meter")
        self._save_thread = Thread(target=self.__save_file__, name="File Writer")

        # Actualizamos los headers
        if headers:
            self._headers.update(dict(headers))

        # Obtenemos la info del servidor
        self.__get_download_headers__()

        self._file_size = int(self.response_headers.get("content-length", "0"))

        if not self.response_headers.get("accept-ranges") == "bytes" or self._file_size == 0:
            self._max_connections = 1
            self._part_size = 0
            self._resume = False

        # Obtenemos el nombre del archivo
        self.__get_download_filename__()

        # Abrimos en modo "a+" para que cree el archivo si no existe, luego en modo "r+b" para poder hacer seek()
        self.file = filetools.file_open(filetools.join(self._path, self._filename) + '.tmp', "a+")
        self.file = filetools.file_open(filetools.join(self._path, self._filename) + '.tmp', "r+b")

        if self._file_size >= 2 ** 31 or not self._file_size:
            try:
                self.file.seek(2 ** 31)
            except OverflowError:
                self._seekable = False
                logger.info("No se puede hacer seek() ni tell() en ficheros mayores de 2GB")

        self.__get_download_info__()

        logger.info("Descarga inicializada: Partes: %s | Ruta: %s | Archivo: %s | Tamaño: %s" % (
            len(self._download_info["parts"]),
            self._path,
            self._filename,
            self._download_info["size"]
        ))

    def __get_download_headers__(self):
        for x in range(3):
            try:
                conn = urllib2.urlopen(urllib2.Request(self.url, headers=self._headers), timeout=5)

            except Exception:
                self.response_headers = dict()
                self._state = self.states.error

            else:
                self.response_headers = conn.headers.dict
                self._state = self.states.stopped
                break

    def __get_download_filename__(self):
        # Obtenemos nombre de archivo y extension
        if "filename" in self.response_headers.get("content-disposition", "") \
                and "attachment" in self.response_headers.get("content-disposition", ""):

            cd_filename, cd_ext = os.path.splitext(urllib.unquote_plus(
                re.compile("attachment; filename ?= ?[\"|']?([^\"']+)[\"|']?").match(
                    self.response_headers.get("content-disposition")).group(1)))

        elif "filename" in self.response_headers.get("content-disposition", "") \
                and "inline" in self.response_headers.get("content-disposition", ""):

            cd_filename, cd_ext = os.path.splitext(urllib.unquote_plus(
                re.compile("inline; filename ?= ?[\"|']?([^\"']+)[\"|']?").match(
                    self.response_headers.get("content-disposition")).group(1)))

        else:
            cd_filename, cd_ext = "", ""

        url_filename, url_ext = os.path.splitext(urllib.unquote_plus(os.path.basename(urlparse.urlparse(self.url)[2])))

        if self.response_headers.get("content-type", "application/octet-stream") != "application/octet-stream":
            mime_ext = mimetypes.guess_extension(self.response_headers.get("content-type"))
        else:
            mime_ext = ""

        # Seleccionamos el nombre mas adecuado
        if cd_filename:
            self.remote_filename = cd_filename
            if not self._filename:
                self._filename = cd_filename

        elif url_filename:
            self.remote_filename = url_filename
            if not self._filename:
                self._filename = url_filename

        # Seleccionamos la extension mas adecuada
        if cd_ext:
            if cd_ext not in self._filename:
                self._filename += cd_ext
            if self.remote_filename:
                self.remote_filename += cd_ext
        elif mime_ext:
            if mime_ext not in self._filename:
                self._filename += mime_ext
            if self.remote_filename:
                self.remote_filename += mime_ext
        elif url_ext:
            if url_ext not in self._filename:
                self._filename += url_ext
            if self.remote_filename:
                self.remote_filename += url_ext

    @staticmethod
    def __change_units__(value):
        import math
        units = ["B", "KB", "MB", "GB"]
        if value <= 0:
            return 0, 0, units[0]
        else:
            return value, value / 1024.0 ** int(math.log(value, 1024)), units[int(math.log(value, 1024))]

    def __get_download_info__(self):
        # Continuamos con una descarga que contiene la info al final del archivo
        self._download_info = {}

        try:
            if not self._resume:
                raise Exception()

            self.file.seek(-16, 2)
            offset = int(self.file.read())
            self.file.seek(offset)
            data = self.file.read()[:-16]
            self._download_info = eval(data)
            if not self._download_info["size"] == self._file_size:
                raise Exception()
            self.file.seek(offset)
            self.file.truncate()

            if not self._seekable:
                for part in self._download_info["parts"]:
                    if part["start"] >= 2 ** 31 and part["status"] == self.states.completed:
                        part["status"] = self.states.stopped
                        part["current"] = part["start"]

            self._start_downloaded = sum([c["current"] - c["start"] for c in self._download_info["parts"]])
            self.pending_parts = set(
                [x for x, a in enumerate(self._download_info["parts"]) if not a["status"] == self.states.completed]
            )
            self.completed_parts = set(
                [x for x, a in enumerate(self._download_info["parts"]) if a["status"] == self.states.completed]
            )
            self.save_parts = set()
            self.download_parts = set()

        # La info no existe o no es correcta, comenzamos de 0
        except Exception:
            self._download_info["parts"] = []
            if self._file_size and self._part_size:
                for x in range(0, self._file_size, self._part_size):
                    end = x + self._part_size - 1
                    if end >= self._file_size:
                        end = self._file_size - 1
                    self._download_info["parts"].append(
                        {"start": x, "end": end, "current": x, "status": self.states.stopped}
                    )
            else:
                self._download_info["parts"].append(
                    {"start": 0, "end": self._file_size - 1, "current": 0, "status": self.states.stopped}
                )

            self._download_info["size"] = self._file_size
            self._start_downloaded = 0
            self.pending_parts = set([x for x in range(len(self._download_info["parts"]))])
            self.completed_parts = set()
            self.save_parts = set()
            self.download_parts = set()

            self.file.seek(0)
            self.file.truncate()

    def __open_connection__(self, start, end):
        headers = self._headers.copy()
        if not end:
            end = ""
        headers.update({"Range": "bytes=%s-%s" % (start, end)})
        conn = urllib2.urlopen(urllib2.Request(self.url, headers=headers), timeout=5)
        return conn

    def __check_consecutive__(self, d_id):
        return d_id == 0 or (len(self.completed_parts) >= d_id and sorted(self.completed_parts)[d_id - 1] == d_id - 1)

    def __save_file__(self):
        logger.info("Thread iniciado: %s" % threading.current_thread().name)

        while self._state == self.states.downloading:
            if not self.pending_parts and not self.download_parts and not self.save_parts:  # Descarga finalizada
                self._state = self.states.completed
                self.file.close()
                filetools.rename(
                    filetools.join(self._path, self._filename) + '.tmp',
                    filetools.join(self._path, self._filename)
                )
                continue

            elif not self.save_parts:
                continue

            save_id = min(self.save_parts)

            if not self._seekable \
                    and self._download_info["parts"][save_id]["start"] >= 2 ** 31 \
                    and not self.__check_consecutive__(save_id):
                continue

            if self._seekable or self._download_info["parts"][save_id]["start"] < 2 ** 31:
                self.file.seek(self._download_info["parts"][save_id]["start"])

            try:
                # file = open(os.path.join(self.tmp_path, self._filename + ".part%s" % save_id), "rb")
                # self.file.write(file.read())
                # file.close()
                # os.remove(os.path.join(self.tmp_path, self._filename + ".part%s" % save_id))
                for a in self._buffer.pop(save_id):
                    self.file.write(a)
                self.save_parts.remove(save_id)
                self.completed_parts.add(save_id)
                self._download_info["parts"][save_id]["status"] = self.states.completed
            except Exception:
                import traceback
                logger.error(traceback.format_exc())
                self._state = self.states.error

        if self.save_parts:
            for s in self.save_parts:
                self._download_info["parts"][s]["status"] = self.states.stopped
                self._download_info["parts"][s]["current"] = self._download_info["parts"][s]["start"]

        logger.info("Thread detenido: %s" % threading.current_thread().name)

    def __get_part_id__(self):
        self._download_lock.acquire()
        if len(self.pending_parts):
            d_id = min(self.pending_parts)
            self.pending_parts.remove(d_id)
            self.download_parts.add(d_id)
            self._download_lock.release()
            return d_id
        else:
            self._download_lock.release()
            return None

    def __set_part_connecting__(self, d_id):
        logger.info("ID: %s Estableciendo conexión" % d_id)
        self._download_info["parts"][d_id]["status"] = self.states.connecting

    def __set_part__error__(self, d_id):
        logger.info("ID: %s Error al descargar" % d_id)
        self._download_info["parts"][d_id]["status"] = self.states.error
        self.pending_parts.add(d_id)
        self.download_parts.remove(d_id)

    def __set_part__downloading__(self, d_id):
        logger.info("ID: %s Descargando datos..." % d_id)
        self._download_info["parts"][d_id]["status"] = self.states.downloading

    def __set_part_completed__(self, d_id):
        logger.info("ID: %s ¡Descarga finalizada!" % d_id)
        self._download_info["parts"][d_id]["status"] = self.states.saving
        self.download_parts.remove(d_id)
        self.save_parts.add(d_id)
        while self._state == self.states.downloading and len(self._buffer) > self._max_connections + self._max_buffer:
            time.sleep(0.1)

    def __set_part_stopped__(self, d_id):
        if self._download_info["parts"][d_id]["status"] == self.states.downloading:
            self._download_info["parts"][d_id]["status"] = self.states.stopped
            self.download_parts.remove(d_id)
            self.pending_parts.add(d_id)

    def __open_part_file__(self, d_id):
        open(os.path.join(self.tmp_path, self._filename + ".part%s" % d_id), "a+")
        f = open(os.path.join(self.tmp_path, self._filename + ".part%s" % d_id), "r+b")
        f.seek(self._download_info["parts"][d_id]["current"] - self._download_info["parts"][d_id]["start"])
        return f

    def __start_part__(self):
        logger.info("Thread Iniciado: %s" % threading.current_thread().name)

        while self._state == self.states.downloading:
            d_id = self.__get_part_id__()
            if d_id is None:
                break

            self.__set_part_connecting__(d_id)

            try:
                connection = self.__open_connection__(self._download_info["parts"][d_id]["current"],
                                                      self._download_info["parts"][d_id]["end"])
            except Exception:
                self.__set_part__error__(d_id)
                time.sleep(5)
                continue

            self.__set_part__downloading__(d_id)
            # file = self.__open_part_file__(id)

            if d_id not in self._buffer:
                self._buffer[d_id] = []
            speed = []

            while self._state == self.states.downloading:
                try:
                    start = time.time()
                    buff = connection.read(self._block_size)
                    speed.append(len(buff) / ((time.time() - start) or 0.001))
                except Exception:
                    logger.info("ID: %s Error al descargar los datos" % d_id)
                    self._download_info["parts"][d_id]["status"] = self.states.error
                    self.pending_parts.add(d_id)
                    self.download_parts.remove(d_id)
                    break
                else:
                    if len(buff) and \
                                    self._download_info["parts"][d_id]["current"] < \
                                    self._download_info["parts"][d_id]["end"]:

                        # file.write(buffer)
                        self._buffer[d_id].append(buff)
                        self._download_info["parts"][d_id]["current"] += len(buff)
                        if len(speed) > 10:
                            velocidad_minima = sum(speed) / len(speed) / 3
                            velocidad = speed[-1]
                            vm = self.__change_units__(velocidad_minima)
                            v = self.__change_units__(velocidad)

                            if velocidad_minima > speed[-1] \
                                    and velocidad_minima > speed[-2] \
                                    and self._download_info["parts"][d_id]["current"] < \
                                    self._download_info["parts"][d_id]["end"]:
                                logger.info("ID: %s ¡Reiniciando conexión! | "
                                            "Velocidad minima: %.2f %s/s | Velocidad: %.2f %s/s" % (
                                                d_id,
                                                vm[1],
                                                vm[2],
                                                v[1],
                                                v[2]
                                            ))
                                # file.close()
                                break
                    else:
                        self.__set_part_completed__(d_id)
                        # file.close()
                        break

            self.__set_part_stopped__(d_id)
        logger.info("Thread detenido: %s" % threading.current_thread().name)
