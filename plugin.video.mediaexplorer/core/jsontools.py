# -*- coding: utf-8 -*-
from core.libs import *
import json


def load_file(path):
    data = load_json(open(path, 'rb').read())
    return data


def dump_file(data, path):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    open(path, 'wb').write(dump_json(data))


def load_json(*args, **kwargs):
    if "object_hook" not in kwargs:
        kwargs["object_hook"] = to_utf8

    try:
        value = json.loads(*args, **kwargs)
    except Exception:
        logger.error()
        value = {}

    return value


def dump_json(*args, **kwargs):
    if not kwargs:
        kwargs = {
            'indent': 4,
            'skipkeys': True,
            'sort_keys': True,
            'ensure_ascii': False
        }

    try:
        value = json.dumps(*args, **kwargs)
    except Exception:
        logger.error()
        value = ''

    return value


def to_utf8(dct):
    if isinstance(dct, dict):
        return dict((to_utf8(key), to_utf8(value)) for key, value in dct.iteritems())

    elif isinstance(dct, list):
        return [to_utf8(element) for element in dct]

    elif isinstance(dct, unicode):
        return dct.encode('utf-8')

    else:
        return dct
