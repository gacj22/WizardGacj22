# -*- coding: utf-8 -*-

__all__ = ['Languages', 'Qualities', 'Item', 'Video', 'Language', 'Quality']

import base64
import copy
import inspect

from core.libs import *


class Language:
    def __init__(self, name, label, short):
        self.name = name
        self.label = label
        self.short = short

    def __str__(self):
        from platformcode import viewtools
        if settings.get_setting('short_labels', viewtools.__file__):
            return self.short
        else:
            return self.label


class Quality:
    def __init__(self, name, label, short, level):
        self.name = name
        self.label = label
        self.short = short
        self.level = level

    def __str__(self):
        from platformcode import viewtools
        if settings.get_setting('short_labels', viewtools.__file__):
            return self.short
        else:
            return self.label


class Languages(object):
    es = Language(name='es', label='Español', short='ES')
    en = Language(name='en', label='Inglés', short='EN')
    la = Language(name='la', label='Latino', short='LAT')
    sub_es = Language(name='sub_es', label='Español Subtitulado', short='ES-SUB')
    sub_en = Language(name='sub_en', label='Inglés Subtitulado', short='EN-SUB')
    sub_la = Language(name='sub_la', label='Latino Subtitulado', short='LA-SUB')
    vo = Language(name='vo', label='Version Original', short='VO')
    vos = Language(name='vos', label='Version Original Subtitulada', short='VOS')
    unk = Language(name='unk', label='Desconocido', short='DES')

    def __init__(self, values=None):
        self.values = {}
        if values:
            for name, codes in values.items():
                for c in codes:
                    if c not in self.values:
                        self.values[c] = name
                    else:
                        if type(self.values[c]) != list:
                            self.values[c] = [self.values[c]]
                        self.values[c].append(name)

    def get(self, item):
        if not item:
            return None

        if item in self.values:
            return self.values[item]

        logger.debug('Idioma desconocido: \'%s\'' % item)
        return self.unk

    @staticmethod
    def from_name(item):
        values = Languages().all
        if type(item) == list:
            result = []
            for i in item:
                for v in values:
                    if v.name == i:
                        result.append(v)
            return result
        else:
            for v in values:
                if v.name == item:
                    return v

    @property
    def all(self):
        return [l for l in self.__class__.__dict__.values() if isinstance(l, Language)]


class Qualities(object):
    uhd = Quality(name='uhd', label='Ultra HD', short='4K', level=80)
    m3d = Quality(name='m3d', label='3D', short='3D', level=70)
    hd_full = Quality(name='hd_full', label='Full HD 1080p', short='FULLHD', level=60)
    hd = Quality(name='hd', label='HD 720p', short='HD', level=50)
    sd = Quality(name='sd', label='SD', short='SD', level=40)
    rip = Quality(name='rip', label='Rip', short='RIP', level=30)
    scr = Quality(name='scr', label='Screener', short='SC', level=20)
    unk = Quality(name='unk', label='Desconocida', short='DES', level=10)

    def __init__(self, values=None):
        self.values = {}
        if values:
            for name, codes in values.items():
                for c in codes:
                    if c not in self.values:
                        self.values[c] = name
                    else:
                        if type(self.values[c]) != list:
                            self.values[c] = [self.values[c]]
                        self.values[c].append(name)

    def get(self, item):
        if not item:
            return None

        if item in self.values:
            return self.values[item]

        logger.debug('Calidad desconocida: \'%s\'' % item)
        return self.unk

    @staticmethod
    def from_name(item):
        values = Qualities().all
        if type(item) == list:
            result = []
            for i in item:
                for v in values:
                    if v.name == i:
                        result.append(v)
            return result
        else:
            for v in values:
                if v.name == item:
                    return v

    @property
    def all(self):
        return [l for l in self.__class__.__dict__.values() if isinstance(l, Quality)]


class Video(object):
    def __init__(self, **kwargs):
        kwargs.setdefault('server',
                          moduletools.get_module_name(inspect.getmodule(inspect.currentframe().f_back).__file__))
        self.__dict__.update(kwargs)

    def __str__(self):
        return repr(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)

    def __getattr__(self, name):
        if name.startswith("__"):
            return super(Video, self).__getattribute__(name)

        elif name == 'type':
            return self._get_type()

        elif name == 'mpd':
            return False

        else:
            return ''

    def __deepcopy__(self, memo):
        new = Video(**self.__dict__)
        return new

    def _get_type(self):
        if self.url.startswith('rtmp'):
            return 'rtmp'
        else:
            return os.path.splitext(self.url.split('?')[0].split('|')[0])[1]


class Item(object):
    defaults = {'folder': True, 'content_type': 'items', 'type': 'default',
                'stream': True, "watched": False, "context": list(), 'size': 0, 'category': 'all'}
    valid_contents = [
        "items",
        "channels",
        "icons",
        "servers",
        "videos",
        "movies",
        "tvshows",
        "seasons",
        "episodes",
        "default"
    ]
    valid_types = [
        "video",
        "movie",
        "tvshow",
        "season",
        "episode",
        "setting",
        "search",
        "item",
        "item1",
        "item2",
        "warning",
        "info",
        "user",
        "channel",
        "next",
        "label",
        "server",
        "default",
        "highlight",
        'update',
        'download',
        'download_episode'
    ]

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __contains__(self, item):
        return item in self.__dict__

    def __setattr__(self, key, value):
        if key == 'type' and value in ('movie', 'tvshow', 'video', 'season', 'episode'):
            object.__setattr__(self, 'mediatype', value)

        if key == 'type' and value not in self.valid_types:
            raise Exception('El tipo de ítem no es válido: \'%s\'' % value)

        if key == 'content_type' and value not in self.valid_contents:
            raise Exception('El tipo de contenido no es válido: \'%s\'' % value)

        # Quality & Language to dict conversion
        if key in ('lang', 'quality') and value:
            is_list = True
            if type(value) != list:
                is_list = False
                value = [value]
            aux = []
            for a in value:
                if isinstance(a, (Language, Quality)):
                    aux.append(a.name)
                elif isinstance(a, str):
                    aux.append(a)
            if is_list:
                value = aux
            else:
                value = aux.pop()

        object.__setattr__(self, key, value)

    def __getattribute__(self, item):
        # dict to Quality & Language conversion
        if item == 'lang':
            return Languages.from_name(object.__getattribute__(self, item))
        elif item == 'quality':
            return Qualities.from_name(object.__getattribute__(self, item))
        else:
            return object.__getattribute__(self, item)

    def __getattr__(self, item):
        if item.startswith("__"):
            return object.__getattribute__(self, item)

        else:
            return self.defaults.get(item, '')

    def __str__(self):
        return '{%s}' % (', '.join(['\'%s\': %s' % (k, repr(self.__dict__[k])) for k in sorted(self.__dict__.keys())]))

    def tourl(self):
        vlaue = repr(self.__dict__)
        return urllib.quote(base64.b64encode(vlaue))

    def fromurl(self, url):
        str_item = base64.b64decode(urllib.unquote(url))
        self.__dict__.update(eval(str_item))
        return self

    def tojson(self, path=""):
        if path:
            open(path, "wb").write(jsontools.dump_json(self.__dict__))
        else:
            return jsontools.dump_json(self.__dict__)

    def fromjson(self, json_item=None, path=""):
        if path:
            json_item = open(path, "rb").read()

        if type(json_item) == str:
            item = jsontools.load_json(json_item)
        else:
            item = json_item
        self.__dict__.update(item)
        return self

    def clone(self, **kwargs):
        newitem = copy.deepcopy(self)
        if 'group' in newitem.__dict__:
            newitem.__dict__.pop('group')
        if 'label' in newitem.__dict__:
            newitem.__dict__.pop('label')
        if 'label_extra' in newitem.__dict__:
            newitem.__dict__.pop('label_extra')
        if 'context_action' in newitem.__dict__:
            newitem.__dict__.pop('context_action')
        if 'context_channel' in newitem.__dict__:
            newitem.__dict__.pop('context_channel')
        for k, v in kwargs.items():
            setattr(newitem, k, v)
        return newitem
