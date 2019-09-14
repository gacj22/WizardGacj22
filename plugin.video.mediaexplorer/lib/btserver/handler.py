# -*- coding: utf-8 -*-
import os
import re
import time
import urllib
import urlparse
from BaseHTTPServer import BaseHTTPRequestHandler


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    range_re = re.compile(r'bytes=(\d+)-')

    def __init__(self, request, client_address, server):
        self.client = server.client
        self.offset = 0
        self.file = None
        BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    def log_message(self, frm, *args):
        pass

    def get_range(self):
        if self.headers.get('Range'):
            m = self.range_re.match(self.headers['Range'])
            if m:
                try:
                    self.offset = int(m.group(1))
                    return
                except Exception:
                    pass
        self.offset = 0

    def do_GET(self):
        if self.do_HEAD():
            cursor = self.file.create_cursor(self.offset)
            while True:
                buf = cursor.read(1024 * 8)
                if not buf:
                    break
                try:
                    self.wfile.write(buf)
                except Exception:
                    break
            cursor.close()

    def send_pls(self, files):
        playlist = [
            '[playlist]',
            '',
        ]
        for x, f in enumerate(files):
            playlist.append('File%d=http://127.0.0.1:%d/%s' % (
                x + 1,
                self.client.port,
                urllib.quote(f.path)
            ))
            playlist.append('Title%d=%s' % (
                x + 1,
                f.path
            ))

        playlist.append('NumberOfEntries=%d' % len(files))
        playlist.append('Version=0')

        data = '\n'.join(playlist)
        self.send_response(200, 'OK')
        self.send_header("Content-Length", str(len(data)))
        self.finish_header()
        self.wfile.write(data)

    def do_HEAD(self):
        url = urllib.unquote(urlparse.urlparse(self.path).path)

        while not self.client.has_meta:
            time.sleep(1)

        # Playlist
        if url == "/playlist.pls":
            self.send_pls(self.client.files)
            return False

        self.file = self.client.set_file(url[1:])
        if not self.file:
            return False
        self.send_resp_header()
        return True

    def _file_info(self):
        size = self.file.size
        ext = os.path.splitext(self.file.path)[1]
        mime = self.client.video_exts.get(ext)
        if not mime:
            mime = 'application/octet-stream'
        return size, mime

    def send_resp_header(self):
        size, cont_type = self._file_info()
        self.get_range()
        if self.offset:
            self.send_response(206, 'Partial Content')
        else:
            self.send_response(200, 'OK')

        self.send_header('Content-Type', cont_type)
        self.send_header('transferMode.dlna.org', 'Streaming')
        self.send_header('contentFeatures.dlna.org',
                         'DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000')
        self.send_header('Accept-Ranges', 'bytes')

        if self.offset:
            self.send_header('Content-Range', 'bytes %d-%d/%d' % (self.offset, size - 1, size))
            self.send_header('Content-Length', size - self.offset)
        else:
            self.send_header('Content-Length', size)
        self.finish_header()

    def finish_header(self):
        self.send_header('Connection', 'close')
        self.end_headers()
