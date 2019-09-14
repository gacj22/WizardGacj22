# -*- coding: utf-8 -*-
import BaseHTTPServer
from SocketServer import ThreadingMixIn
import traceback
from threading import Thread
from core import logger


class Server(ThreadingMixIn, BaseHTTPServer.HTTPServer):
    daemon_threads = True
    timeout = 1

    def __init__(self, address, handler, client):
        BaseHTTPServer.HTTPServer.__init__(self, address, handler)
        self.client = client
        self.running = True

    def stop(self):
        self.running = False

    def serve(self):
        while self.running:
            try:
                self.handle_request()
            except Exception:
                print traceback.format_exc()

    def run(self):
        t = Thread(target=self.serve, name='HTTP Server')
        t.daemon = True
        t.start()

    def handle_error(self, request, client_address):
        if "socket.py" not in traceback.format_exc():
            logger.debug(traceback.format_exc())
