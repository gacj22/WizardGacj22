# -*- coding: utf-8 -*-
import hashlib
from io import BytesIO

from core import ziptools
from core.libs import *

updates_file = os.path.join(sysinfo.data_path, 'updates.json')
MAX_ATTEMTS = 3


def mainlist(item):
    logger.trace()
    itemlist = list()

    itemlist.append(Item(
        label='Version actual: %s' % sysinfo.main_version,
        type='label',
        fanart=item.fanart,
        icon='icon/mediaexplorer.png'
    ))

    itemlist.append(item.clone(
        action='check',
        label='Buscar e instalar actualizaciones ahora' if settings.get_setting(
            'update_auto') else 'Buscar actualizaciones ahora',
        description='Busca si hay actualizaciones disponibles',
        type='highlight'
    ))

    try:
        updates = get_updates()
        if updates['main']:
            for x, u in enumerate(updates['main']):
                itemlist.append(item.clone(
                    action='update',
                    label='Actualizar a la versión %s %s' % (u['version'], ['', ' (beta)'][u['beta']]),
                    description='Fecha: %s\nVersión: %s\nCambios: %s' % (
                        u['date'],
                        u['version'],
                        u['changes']
                    ),
                    date=u['date'],
                    version=u['version'],
                    url=u['url'],
                    mode='main',
                    type='highlight' if x == 0 else 'item'
                ))

        itemlist.append(item.clone(
            action='reinstall',
            label='Reinstalar la versión actual',
            description='Reinstala la version actual del MediaExplorer para solucionar problemas en caso de '
                        'actualizaciones fallidas',
            type='item'
        ))

        if count('channels'):
            itemlist.append(item.clone(
                action='list_to_update',
                mode='channels',
                label='Actualizaciones de canales (%s)' % count('channels'),
                description='Actualiza los canales',
                type='highlight'
            ))
        if count('servers'):
            itemlist.append(item.clone(
                action='list_to_update',
                mode='servers',
                label='Actualizaciones de servidores (%s)' % count('servers'),
                description='Actualiza los servidores',
                type='highlight'
            ))
    except Exception:
        pass
    return itemlist


def list_to_update(item):
    logger.trace()
    itemlist = list()

    updates = get_updates()['modules']

    for upd in updates[item.mode].values():
        if upd['compatible'] or not settings.get_setting('update_hide_incompatible'):
            new_item = item.clone(
                label=upd['name'] + (' [No compatible]' if not upd['compatible'] else ''),
                type='update',
                id=upd['id'],
                name=upd['name'],
                date=upd['date'],
                version=upd['version'],
                compatible=upd['compatible'],
                min_version=upd['min_version'],
                url=upd['url'],
                description='Fecha: %s\nVersión: %s\nCambios: %s\n' % (upd['date'], upd['version'], upd['changes']),
                action='update',
                icon="icon/%s.png" % upd['id'],
                poster="poster/%s.png" % upd['id'],
                thumb=upd.get('thumb', "thumb/%s.png" % upd['id']),
                mode=item.mode
            )
            itemlist.append(new_item)

    if itemlist:
        itemlist.insert(0, item.clone(
            label='Actualizar todos los %s' % ('canales' if item.mode == 'channels' else 'servidores'),
            action='update_all',
            type='highlight',
            description='Actualiza todos los %s' % ('canales' if item.mode == 'channels' else 'servidores')
        ))

    return itemlist


def update_all(item):
    logger.trace()

    if item.mode == 'channels' or item.mode == 'servers':
        dialog = platformtools.dialog_progress_bg('Actualizaciones', 'Actualizando...')
        c = 0
        updates = get_updates()['modules']
        for k, v in updates[item.mode].items():
            text = "Actualizando canal %s" if item.mode == 'channels' else "Actualizando servidor %s"
            dialog.update(c * 100 / len(updates[item.mode]), 'MediaExplorer: Actualizaciones', text % v['name'])
            c += 1
            update(Item(
                id=v['id'],
                mode=item.mode,
                all=True,
                name=v['name'],
                url=v['url'],
                version=v['version'],
                min_version=v['min_version'],
                compatible=moduletools.is_compatible(v['min_version'])
            ))
        dialog.close()


def update(item, silent=False):
    logger.trace()

    if item.mode == 'main':
        error = 0
        response = httptools.downloadpage(item.url)

        if response.sucess:
            fileobj = BytesIO()
            fileobj.write(response.data)
            try:
                if sysinfo.platform_name == 'kodi':
                    if ziptools.extract(fileobj, os.path.dirname(sysinfo.runtime_path), True, silent):
                        settings.set_setting('update_service', 'restart')
                        if os.path.isfile(updates_file):
                            os.remove(updates_file)
                else:
                    if ziptools.extract(fileobj, sysinfo.runtime_path, True, silent):
                        if os.path.isfile(updates_file):
                            os.remove(updates_file)
                        platformtools.itemlist_refresh()
                        os._exit(10)
            except:
                logger.error()
                error = 1
        else:
            logger.error('Datos no descargados correctamente')
            error = 1
        if error:
            text = 'No se ha podido actualizar MediaExplorer'
            platformtools.dialog_notification('MediaExplorer: Actualizaciones', text)

        platformtools.itemlist_refresh()

    elif item.mode == 'channels' or item.mode == 'servers':
        updates = get_updates()
        m_updates = updates['modules']
        error = 0
        if not item.compatible:
            if not item.all:
                platformtools.dialog_ok(
                    'MediaExplorer: Actualizaciones',
                    'El %s %s no es compatible, se requiere:' % (
                        ('canal', 'servidor')[item.mode == 'server'],
                        item.name
                    ),
                    'MediaExplorer: %s (actual %s)' % (
                        item.min_version.get('main'),
                        sysinfo.main_version
                    ),
                    'Python: %s (actual %s)' % (
                        item.min_version.get('python'),
                        sysinfo.py_version
                    )
                )
            return
        if m_updates[item.mode][item.id].get('attemts', 0) > MAX_ATTEMTS and item.all:
            return

        zip_data = call_api(
            item.url,
            {
                "beta": ['false', 'true'][settings.get_setting('update_channel')],
                'version': sysinfo.main_version
            }).data

        if zip_data:
            try:
                fileobj = BytesIO()
                fileobj.write(zip_data)
                ziptools.extract(fileobj, os.path.join(sysinfo.runtime_path, item.mode), True, silent)
            except Exception:
                logger.error()
                error = 1
        else:
            logger.error('Datos no descargados correctamente')
            error = 1

        if not error:
            del updates['modules'][item.mode][item.id]
        else:
            m_updates[item.mode][item.id]['attemts'] = m_updates[item.mode][item.id].get('attemts', 0) + 1

        set_updates(updates)

        if not item.all and not error:
            text = 'Canal %s actualizado correctamente' if item.mode == 'channels' else \
                'Servidor %s actualizado correctamente'
            platformtools.dialog_ok('MediaExplorer: Actualizaciones', text % item.name)
        elif not item.all and error:
            text = 'Canal %s No se ha podido actualizar correctamente' if item.mode == 'channels' else \
                'Servidor %s no se ha podido actualizar correctamente'
            text += '\n Contacte con el foro para buscar una solución'
            platformtools.dialog_ok('MediaExplorer: Actualizaciones', text % item.name)
        elif item.all and error and m_updates[item.mode][item.id].get('attemts', 0) == MAX_ATTEMTS:
            text = 'Canal %s No se ha podido actualizar correctamente' if item.mode == 'channels' else \
                'Servidor %s no se ha podido actualizar correctamente'
            text += ' Intente una actualización manual'
            platformtools.dialog_notification('MediaExplorer: Actualizaciones', text % item.name)

        if not updates['modules'][item.mode]:
            platformtools.itemlist_update(Item(channel='updates', action='mainlist'))
        else:
            platformtools.itemlist_refresh()


def check(item):
    logger.trace()
    if not check_updates():
        platformtools.dialog_notification("Buscar actualizaciones", "No hay nuevas actualizaciones")
    platformtools.itemlist_refresh()


def reinstall(item):
    logger.trace()
    if platformtools.dialog_yesno('MediaExplorer',
                                  'Se va a instalar la version %s, ¿Deseas continuar?' % sysinfo.main_version):
        update(item.clone(
            action='update',
            date='',
            version=sysinfo.main_version,
            url='http://mediaexplorer.tk/download?platform=%s&version=%s' % (
                sysinfo.platform_name,
                sysinfo.main_version
            ),
            mode='main'
        ))


def last_check_updates():
    logger.trace()
    updates = get_updates()
    return updates['last_check_updates']


def count(m_type=None):
    logger.trace()
    updates = get_updates()
    c = 0

    if m_type == 'main':
        return 1 if updates.get('main') else 0

    if settings.get_setting('update_hide_incompatible'):
        if m_type:
            for _id in updates['modules'].get(m_type, {}).keys():
                if updates['modules'][m_type][_id].get('compatible', True):
                    c += 1
        else:
            for m_type in updates['modules'].keys():
                for _id in updates['modules'].get(m_type, {}).keys():
                    if updates['modules'][m_type][_id].get('compatible', True):
                        c += 1
            c += 1 if updates.get('main') else 0

    else:
        if m_type:
            c = len(updates['modules'].get(m_type, {}))

        else:
            c = len(updates['modules']['channels']) + len(updates['modules']['servers']) + \
                (1 if updates.get('main') else 0)

    return c


def check_updates(silent=False):
    logger.trace()
    updates = {
        'modules': get_modules_updates(),
        'main': get_main_updates(),
        'last_check_updates': time.time()
    }

    set_updates(updates)
    c = count()

    if c > 0 and settings.get_setting('update_auto'):
        # Actualizar automaticamente el main
        if updates['main']:
            update(Item(mode='main', url=updates['main'][0]['url']), silent)
            new_version = updates['main'][0]['version']
            logger.debug('Actualizado main %s' % new_version)
            if silent:
                platformtools.dialog_notification('MediaExplorer', 'Actualizado a la versión %s' % new_version)
            updates = {
                'modules': get_modules_updates(),
                'main': get_main_updates(new_version),
                'last_check_updates': time.time()
            }
            set_updates(updates)

        # Actualizar automaticamente canales
        if updates['modules']['channels']:
            update_all(Item(mode='channels'))

        # Actualizar automaticamente servidores
        if updates['modules']['servers']:
            update_all(Item(mode='servers'))

        c = 0

    return c


def set_updates(updates):
    jsontools.dump_file(updates, updates_file)


def get_updates():
    empty_updates = {
        'modules': {'channels': {}, 'servers': {}},
        'main': [],
        'last_check_updates': 0
    }

    if os.path.isfile(updates_file):
        updates = jsontools.load_file(updates_file)
        if 'modules' in updates and 'main' in updates and 'last_check_updates' in updates:
            if 'servers' in updates['modules'] and 'channels' in updates['modules']:
                return updates

    return empty_updates


def get_main_updates(version=None):
    try:
        data = call_api(
            'updates/main',
            {
                "beta": ['false', 'true'][settings.get_setting('update_channel')],
                "platform": sysinfo.platform_name,
                "version": version if version is not None else sysinfo.main_version
            }
        ).data
        updates = jsontools.load_json(data)

    except Exception:
        logger.error()
        updates = []

    return updates


def get_modules_updates():
    data = {}
    d_url = ''
    try:
        data = jsontools.load_json(call_api(
            'updates/modules',
            {
                "beta": ['false', 'true'][settings.get_setting('update_channel')],
                'version': sysinfo.main_version
            }
        ).data)

    except Exception:
        logger.error()

    updates = get_updates()['modules']

    module_updates = {
        'servers': {},
        'channels': {}
    }

    for file_name, remote_data in data.items():
        m_type, m_path = file_name.split('/')
        if os.path.isfile(os.path.join(sysinfo.runtime_path, m_type, m_path.replace('zip', 'json'))):
            try:
                data = open(os.path.join(sysinfo.runtime_path, m_type, m_path.replace('zip', 'json')), 'rb').read()
                json_data = jsontools.load_json(data)
                hash_local = hashlib.sha1(data.replace('\r\n', '\n').replace('\r','\n')).hexdigest()
            except Exception:
                hash_local = ''
                json_data = {'version': 0}
        else:
            hash_local = ''
            json_data = {'version': 0}

        if hash_local != remote_data['hash'] and remote_data['version'] > json_data['version']:
            module_updates[m_type][remote_data['id']] = remote_data
            module_updates[m_type][remote_data['id']]['url'] = 'updates/modules/%s/%s' % (m_type, m_path)
            module_updates[m_type][remote_data['id']]['compatible'] = moduletools.is_compatible(
                remote_data.get('min_version', {})
            )
            module_updates[m_type][remote_data['id']]['min_version'] = remote_data.get('min_version', {})

            # La actualizacion ya está en el json
            if remote_data['id'] in updates[m_type] and \
                    updates[m_type][remote_data['id']]['hash'] == remote_data['hash']:
                module_updates[m_type][remote_data['id']]['attemts'] = updates[m_type][remote_data['id']].get('attemts')

    return module_updates
