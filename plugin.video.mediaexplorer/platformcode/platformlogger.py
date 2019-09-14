# -*- coding: utf-8 -*-
import inspect
import threading

import xbmc


# Clase para usar el logger de kodi y mostrar los mensajes de otros threads de forma agrupada
class Logger(object):
    def __init__(self):
        self.thread_messages = {}
        self.main_thread = threading.current_thread()
        self.handlers = [self]
        self.thread_lock = threading.Lock()

    def trace(self, message):
        self.log(message, xbmc.LOGNOTICE)

    def debug(self, message):
        self.log(message, xbmc.LOGDEBUG)

    def error(self, message):
        self.log(message, xbmc.LOGERROR)

    def info(self, message):
        self.log(message, xbmc.LOGNOTICE)

    def log(self, message, level):
        rv = self.find_caller()
        msg = 'MediaExplorer.%-38s %-20s %-4s | %s'

        if level == xbmc.LOGDEBUG:
            level = xbmc.LOGNOTICE
            msg = '[DEBUG] MediaExplorer.%-30s %-20s %-4s | %s'

        data = (msg %(rv[0], rv[2], rv[1], message), level)

        ident = threading.current_thread().ident
        if ident != self.main_thread.ident:
            if ident not in self.thread_messages:
                self.thread_messages[ident] = []

            self.thread_messages[ident].append(data)
        else:
            with self.thread_lock:
                xbmc.log(data[0], data[1])

    def end_thread(self):
        ident = threading.current_thread().ident
        if ident in self.thread_messages.keys():
            with self.thread_lock:
                for data in self.thread_messages[ident]:
                    xbmc.log(data[0], data[1])

            del self.thread_messages[ident]

    @staticmethod
    def find_caller():
        try:
            filename = inspect.getmodule(inspect.currentframe().f_back.f_back.f_back.f_back).__name__
        except:
            filename = inspect.getmodule(inspect.currentframe().f_back.f_back.f_back).__name__
        func = inspect.currentframe().f_back.f_back.f_back.f_back.f_code.co_name
        line = inspect.currentframe().f_back.f_back.f_back.f_back.f_lineno
        rv = (filename, line, func)
        return rv


logger_object = Logger()
