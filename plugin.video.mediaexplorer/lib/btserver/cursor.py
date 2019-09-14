# -*- coding: utf-8 -*-
import time
from threading import Lock, Event, Thread


class Cursor(object):
    def __init__(self, fileobj, pos=0):
        self.fileobj = fileobj
        self.buffer_size = self.fileobj.client.buffer_size
        self.current_pos = 0
        self.closed = False
        self.buffer = {}
        self.fileobj.cursors.append(self)
        self.seek(pos)
        self.current_piece, self.current_offset = self.fileobj.map_piece(self.current_pos)
        self.piece_arrival = Event()
        self.monitor = Thread(target=self.fill_buffer).start()

    def fill_buffer(self):
        while not self.closed:
            self.buffer = dict(filter(lambda y: y[0] >= self.current_piece, self.buffer.items()))
            p = 1000
            for i in range(self.current_piece, min(self.current_piece + self.buffer_size, self.fileobj.last_piece) + 1):
                if i not in self.buffer:
                    self.buffer[i] = None
                    self.fileobj.client.th.set_piece_deadline(i, p)
                    p += 1000

            for x in self.buffer:
                if self.buffer[x] is None and self.have_piece(x):
                    self.buffer[x] = False
                    self.fileobj.client.th.read_piece(x)
            time.sleep(0.5)

    def have_piece(self, pc_no):
        return self.fileobj.client.th.have_piece(pc_no)

    def wait_piece(self, pc_no):
        if not self.have_piece(pc_no):
            self.fileobj.client.th.set_piece_deadline(pc_no, 1000)
            while not self.have_piece(pc_no):
                time.sleep(0.5)

        self.fileobj.client.th.read_piece(pc_no)

        while not self.buffer.get(pc_no):
            time.sleep(0.5)

    def get_piece(self, n):
        if not self.buffer.get(n):
            print 'Esperando Pieza %s' % n
            self.wait_piece(n)
            print 'Enviando Pieza %s' % n
        return self.buffer[n]

    def close(self):
        self.closed = True
        self.fileobj.cursors.remove(self)

    def read(self, size=0):
        data = ""
        size = min(size, self.fileobj.size - self.current_pos) or self.fileobj.size - self.current_pos

        if size:
            # Obtenemos la pieza y el offset
            self.current_piece, self.current_offset = self.fileobj.map_piece(self.current_pos)

            # Obtenemos los datos
            data = self.get_piece(self.current_piece)[self.current_offset: self.current_offset + size]

            if len(data) < size:
                remains = size - len(data)
                self.current_piece += 1
                self.current_offset = 0
                while remains and self.have_piece(self.current_piece):
                    sz = min(remains, self.fileobj.piece_size)
                    data += self.get_piece(self.current_piece)[:sz]
                    remains -= sz
                    if remains:
                        self.current_piece += 1

        self.current_pos += len(data)
        return data

    def add_to_buffer(self, pc_no, data):
        print 'LLegada %s' % pc_no
        if pc_no in self.buffer:
            self.buffer[pc_no] = data
            self.piece_arrival.set()

    def seek(self, n):
        if n > self.fileobj.size:
            n = self.fileobj.size
        elif n < 0:
            raise ValueError('Seeking negative')
        self.current_pos = n

    def tell(self):
        return self.current_pos

    @property
    def buffer_status(self):
        filled = 0
        empty = 0
        for v in self.buffer.values():
            if v is not None:
                filled += 1
            else:
                empty += 1

        return filled * 100.0 / (filled + empty)

    def __repr__(self):
        return 'Cursor %s #%d | Posicion: %s | Pieza: %s:%s | Buffer: %.2f%% (%s)' % (
            hash(self),
            self.fileobj.cursors.index(self),
            self.current_pos,
            self.current_piece,
            self.current_offset,
            self.buffer_status,
            [(0, 1)[bool(self.fileobj.client.th.have_piece(a))] for a in self.buffer]
        )
