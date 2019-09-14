# -*- coding: utf-8 -*-
import inspect
import traceback
import logging.config
from logging.handlers import RotatingFileHandler
import logging
from core.libs import *
import threading

logger_object = None
level = 0


class ExtendedLogger(logging.Logger):
    def findCaller(self):
        try:
            filename = inspect.getmodule(inspect.currentframe().f_back.f_back.f_back.f_back).__name__
        except:
            filename = inspect.getmodule(inspect.currentframe().f_back.f_back.f_back).__name__
        func = inspect.currentframe().f_back.f_back.f_back.f_back.f_code.co_name
        line = inspect.currentframe().f_back.f_back.f_back.f_back.f_lineno
        rv = (filename, line, func)

        return rv


class Formatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        return datetime.datetime.fromtimestamp(record.created).strftime(datefmt)[:-3]


class Handler(RotatingFileHandler):
    def __init__(self, *args, **kwargs):
        RotatingFileHandler.__init__(self, *args, **kwargs)
        self.last_record = None
        self.count_repeat = 0
        self.thread_messages = {}
        self.thread_lock = Lock()
        self.lock = None
        self.main_thread = threading.current_thread()

    def end_thread(self):
        ident = threading.current_thread().ident
        if ident in self.thread_messages.keys():
            with self.thread_lock:
                for record in self.thread_messages[ident]:
                    self.do_emit(record)

            del self.thread_messages[ident]

    def emit(self, record):
        ident = threading.current_thread().ident
        if ident != self.main_thread.ident and 0:  # TODO: desactivado para la version mediaserver, pendiente de mirar
            if ident not in self.thread_messages:
                self.thread_messages[ident] = []

            self.thread_messages[ident].append(record)
        else:
            with self.thread_lock:
                self.do_emit(record)

    def do_emit(self, record):
        if self.last_record and \
                record.msg == self.last_record.msg and \
                record.lineno == self.last_record.lineno and \
                record.pathname == self.last_record.pathname:

            self.count_repeat += 1
        else:
            if self.count_repeat:
                self.last_record.msg = 'Last line repeats %s times' % self.count_repeat
                RotatingFileHandler.emit(self, self.last_record)
                self.count_repeat = 0

            self.last_record = record
            RotatingFileHandler.emit(self, record)


def init_logger(fname=None, lev=None):
    global logger_object
    global level

    platform_logger = settings.get_setting('platform_log', platformsettings.__file__)
    level = lev or settings.get_setting("debug")

    # Logger propio de plataforma (kodi) se formatea el mensaje y se pasa al modulo de platformlogger
    if platform_logger and not fname and level < 4:
        from platformcode import platformlogger
        logger_object = platformlogger.logger_object

    # Si no está configurado el logger de la plataforma o estamos en nivel 4 (modo reporte)
    # se guarda en mediaexplorer.log, report.log o el que pasemos en fname
    else:
        filename = fname or ('report.log' if level > 3 else 'mediaexplorer.log')
        filetools.makedirs(sysinfo.data_path)

        logging.setLoggerClass(ExtendedLogger)
        handler = Handler(
            os.path.join(sysinfo.data_path, filename),
            mode='a',
            maxBytes=5 * 1024 * 1024,
            backupCount=10,
            encoding=None,
            delay=0
        )

        handler.setFormatter(
            Formatter(
                '%(asctime)12s %(levelname)-5s %(filename)-30s %(funcName)-20s %(lineno)-4s | %(message)s',
                '%H:%M:%S.%f'
            )
        )

        logger_object = logging.getLogger('mediaexplorer')
        logger_object.setLevel(logging.DEBUG)
        logger_object.handlers = [handler]
        logger_object.end_thread = handler.end_thread


def trace():
    """
    Función trace: Imprime una linea para cada función en la que se entra:
        - Nivel 1-2 (Errores, Básico): Imprime una linea al entrar en cada función
        - Nievel 3 (Detallado): Imprime una linea al entrar en cada función mas las variables pasadas
    """
    # TODO: no estoy seguro de si es lo que quieres, pero segun la descripcion deberia ser if 0 < leve < 3
    if 1 < level < 3:  # (Errores, Basico)
        logger_object.info('Enter to function')

    elif level > 2:  # (Detallado)
        var_list = inspect.currentframe().f_back.f_locals

        logger_object.info('Enter to function with %s arguments:' % len(var_list))
        if var_list:
            for line in format_message(var_list):
                logger_object.info(line)


def info(message=""):
    """
    Función info: Imprime un mensaje si el nivel es 3 (Detallado)
    Para mostrar información detallada:
        - Conenido de páginas web
        - Contenido de archivos leidos
        - etc
    :param message:
    """
    if level > 2:
        for line in format_message(message):
            logger_object.info(line)


def debug(message=""):
    """
    Función debug: Imprime un mensaje si el nivel es 2 o superior (Básico, Detallado)
    Para mostrar información de depuración:
        - Valores de variables
        - Resultados de funciónes
        - etc
    :param message:
    """
    if level > 0:
        for line in format_message(message):
            logger_object.debug(line)


def error(message=""):
    """
    Función error: Imprime un mensaje si el nivel es superior a 0 (Errores, Basico, Detallado)
        - Si se pasa el parametro message, este se imprime en primer lugar
        - Se imprimen las variables locales en el momento de producirse el error
        - Se imprime el mensaje de traceback
    :param message:
    """
    if level > 0:
        var_list = inspect.trace()[-1][0].f_locals
        logger_object.error('Error while execute function')

        if message:
            logger_object.error('Message:')
            for line in format_message(message):
                logger_object.error(line)

        if var_list:
            logger_object.error('Vars:')
            for line in format_message(var_list):
                logger_object.error(line)

        logger_object.error('Description:')
        for l in traceback.format_exc().splitlines():
            logger_object.error('%s' % l)


def format_message(data):
    """
    Formatea el mensaje para mostrarlo en el log:
        - Se muestran los dict, list y tuple en varias lineas una para cada valor
        - Se ocultan las contraseñas siempre que el nombre de la varible que la contiene contengan las palabras
            'password' o 'clientKey'
        - Representa los demas objetos mediante repr()
    :param data:
    :return:
    """
    result = []

    if type(data) == list:
        result.append('[')
        for v in data:
            separator = ('', ',')[data.index(v) + 1 < len(data)]
            res = format_message(v)
            result.extend(['\t%s' % line for line in res[0:-1]])
            result.append('\t%s' % res[-1] + separator)
        result.append(']')

        return result

    elif type(data) == tuple:
        result.append('(')
        for v in data:
            separator = ('', ',')[data.index(v) + 1 < len(data)]
            res = format_message(v)
            result.extend(['\t%s' % line for line in res[0:-1]])
            result.append('\t%s' % res[-1] + separator)
        result.append(')')

        return result

    elif type(data) == dict:
        result.append('{')

        for k, v in data.items():
            separator = ('', ',')[data.keys().index(k) + 1 < len(data.keys())]
            if ('password' in str(k) or 'clientKey' in str(k)) and v:
                v = '*' * len(v)
            res = format_message(v)
            result.append('\t%s: %s' % (k, res[0]))
            if len(res) > 1:
                result.extend(['\t%s' % y for y in res[1:-1]])
                result.append('\t%s' % res[-1] + separator)
        result.append('}')

        return result

    else:
        return [str(data)]
