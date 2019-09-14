# -*- coding: utf-8 -*-
import os
import time
import libtorrent as lt

from cursor import Cursor


class File(object):
    def __init__(self, f, base, fmap, piece_size, client):
        self.client = client
        self.path = f.path
        self.base = base
        self.index = f.index
        self.size = f.size

        self.piece_size = piece_size
        self._buffering = False

        self.full_path = os.path.join(base, f.path)
        self.first_piece = fmap.piece
        self.last_piece = self.first_piece + max((f.size - 1 + fmap.start), 0) // piece_size
        self.file_offset = fmap.start
        self.cursors = []
        self.buffer = {self.first_piece + x: False for x in range(self.client.buffer_size)}
        for x in range(self.last_piece - self.client.last_pieces_priorize, self.last_piece + 1):
            self.buffer[x] = False

    def create_cursor(self, offset=None):
        return Cursor(self, offset)

    def map_piece(self, ofs):
        return self.first_piece + (ofs + self.file_offset) // self.piece_size, (
                ofs + self.file_offset) % self.piece_size

    def add_to_buffer(self, piece, data):
        if self.buffering:
            if piece in self.buffer:
                self.buffer[piece] = True
        else:
            for cursor in self.cursors:
                cursor.add_to_buffer(piece, data)

    @property
    def buffering(self):
        if self._buffering:
            if not all(self.buffer.values()):
                return True
            else:
                self._buffering = False
                return False
        else:
            return False

    def wait_initial_buffer(self, wait=False):
        if not all(self.buffer.values()) and not self.buffering:
            self._buffering = True
            for x in self.buffer:
                self.client.th.set_piece_deadline(x, 1000, lt.deadline_flags.alert_when_available)

            if wait:
                while self.buffering:
                    time.sleep(0.5)

    @property
    def progress(self):
        try:
            return self.client.th.file_progress()[self.index] * 100.0 / self.size
        except IndexError:
            return 0

    @property
    def download_graphic(self):
        stat = []
        for x in range(self.first_piece, self.last_piece + 1):
            if self.client.th.have_piece(x):
                stat.append('|')
            else:
                stat.append('!')
        return ''.join(stat)

    def __str__(self):
        return 'File #%s | Pieces: %s[%s:%s] | Size: %s | Priority: %s | Downloaded: %.2f%% | Ready: %s%s' % (
            self.index,
            self.last_piece - self.first_piece + 1,
            self.first_piece,
            self.last_piece,
            self.size,
            self.client.th.file_priority(self.index),
            self.progress,
            all(self.buffer.values()) if not self.buffering else '...',
            ''.join(["\n\t%s" % c for c in self.cursors])
        )
