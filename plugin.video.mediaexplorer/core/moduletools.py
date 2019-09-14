# -*- coding: utf-8 -*-
from core.libs import *


def get_controls(mod=None):
    if mod:
        module_path = '%s.json' % os.path.splitext(mod)[0]
    else:
        module_path = os.path.join(sysinfo.runtime_path, 'core', 'ajustes.json')

    if os.path.isfile(module_path):
        try:
            return jsontools.load_file(module_path).get('settings', [])
        except Exception:
            logger.error()
            return []
    else:
        return []


def is_compatible(reqs):
    from distutils.version import LooseVersion

    if reqs.get('python') and LooseVersion(reqs['python']) > LooseVersion(sysinfo.py_version):
        return False

    if reqs.get('main') and LooseVersion(reqs['main']) > LooseVersion(sysinfo.main_version):
        return False

    return True


def get_module_name(mod):
    logger.trace()
    module_path = '%s.json' % os.path.splitext(mod)[0]
    if os.path.isfile(module_path):
        try:
            return jsontools.load_file(module_path)['name']
        except Exception:
            return os.path.splitext(os.path.basename(mod))[0]
    else:
        return os.path.splitext(os.path.basename(mod))[0]


def get_module_parameters(mod):
    logger.trace()
    module_path = '%s.json' % os.path.splitext(mod)[0]
    if os.path.isfile(module_path):
        try:
            return jsontools.load_file(module_path)
        except Exception:
            logger.error()
            return []
    return {}


def get_channels():
    itemlist = []

    modulenames = []
    if os.path.isdir(os.path.join(sysinfo.data_path, 'modules', 'user_channels')):
        for f in os.listdir(os.path.join(sysinfo.data_path, 'modules', 'user_channels')):
            f = os.path.join(sysinfo.data_path, 'modules', 'user_channels', f)
            if not f.endswith('.json'):
                continue

            data = jsontools.load_file(f)
            if data and data['active']:
                data['path'] = f
                itemlist.append(data)
                modulenames.append(data['id'])
            else:
                continue

    for f in os.listdir(os.path.join(sysinfo.runtime_path, 'channels')):
        f = os.path.join(sysinfo.runtime_path, 'channels', f)
        if not f.endswith('.json'):
            continue

        data = jsontools.load_file(f)
        if data and data['active'] and not data['id'] in modulenames:
            data['path'] = f
            itemlist.append(data)
        else:
            continue

    return sorted(itemlist, key=lambda x: x['name'])


def get_paths_servers():
    pathslist = list()
    filesnames = list()

    for d in [os.path.join(sysinfo.data_path, 'modules', 'user_servers'),
              os.path.join(sysinfo.runtime_path, 'servers')]:
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith('.json') and  f not in filesnames:
                    filesnames.append(f)
                    pathslist.append(os.path.join(d,f))

    return pathslist


def get_servers():
    itemlist = []

    for f in get_paths_servers():
        data = jsontools.load_file(f)
        if data:
            data['path'] = f
            itemlist.append(data)
        else:
            continue

    return sorted(itemlist, key=lambda x: x['name'])


def get_debriders():
    itemlist = []
    for f in os.listdir(os.path.join(sysinfo.runtime_path, 'debriders')):
        f = os.path.join(sysinfo.runtime_path, 'debriders', f)
        if not f.endswith('.json'):
            continue

        data = jsontools.load_file(f)
        if data:
            data['path'] = f
            itemlist.append(data)
        else:
            continue

    return sorted(itemlist, key=lambda x: x['name'])


def serverinfo(server):
    logger.trace()
    try:
        f = os.path.join(sysinfo.runtime_path, 'servers', '%s.json' % server)
        data = jsontools.load_file(f)
        return platformtools.dialog_ok(
            'Información del servidor %s' % data['name'],
            'Version: %s' % data['version'],
            'Fecha: %s' % data['changes'][0]['date'],
            'Cambios: %s' % data['changes'][0]['description']
        )
    except Exception:
        logger.error()


def channelinfo(channel):
    logger.trace()
    try:
        f = os.path.join(sysinfo.runtime_path, 'channels', '%s.json' % channel)
        data = jsontools.load_file(f)
        return platformtools.dialog_ok(
            'Información del canal %s' % data['name'],
            'Version: %s' % data['version'],
            'Fecha: %s' % data['changes'][0]['date'],
            'Cambios: %s' % data['changes'][0]['description']
        )
    except Exception:
        logger.error()


def get_channel_module(channel):
    logger.trace()

    if os.path.isfile(os.path.join(sysinfo.runtime_path, 'core', channel + '.py')):
        if 'core.' + channel in sys.modules:
            reload(sys.modules['core.' + channel])
        return __import__('core.%s' % channel, None, None, ['core.%s' % channel])

    elif os.path.isfile(os.path.join(sysinfo.data_path, 'modules', 'user_channels', channel + '.py')):
        if 'user_channels.' + channel in sys.modules:
            reload(sys.modules['user_channels.' + channel])
        return __import__('user_channels.%s' % channel, None, None, ['user_channels.%s' % channel])

    elif os.path.isfile(os.path.join(sysinfo.runtime_path, 'channels', channel + '.py')):
        if 'channels.' + channel in sys.modules:
            reload(sys.modules['channels.' + channel])
        return __import__('channels.%s' % channel, None, None, ['channels.%s' % channel])


def get_server_module(server):
    logger.trace()

    if os.path.isfile(os.path.join(sysinfo.data_path, 'modules', 'user_servers', server + '.py')):
        if 'user_servers.' + server in sys.modules:
            reload(sys.modules['user_servers.' + server])
        return __import__('user_servers.%s' % server, None, None, ['user_servers.%s' % server])

    elif os.path.isfile(os.path.join(sysinfo.runtime_path, 'servers', server + '.py')):
        if 'servers.' + server in sys.modules:
            reload(sys.modules['servers.' + server])
        return __import__('servers.%s' % server, None, None, ['servers.%s' % server])


def get_debrider_module(debrider):
    logger.trace()

    if os.path.isfile(os.path.join(sysinfo.runtime_path, 'servers', debrider + '.py')):
        if 'debriders.' + debrider in sys.modules:
            reload(sys.modules['debriders.' + debrider])
        return __import__('debriders.%s' % debrider, None, None, ['debriders.%s' % debrider])
