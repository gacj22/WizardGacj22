# -*- coding: utf-8 -*-
import platform
import shutil
from io import BytesIO

from core import ziptools
from core.libs import *


def mainlist(item):
    logger.trace()
    itemlist = []

    remote_libs = get_libs()

    itemlist.append(Item(label='Python: %s' % sys.version, type='highlight'))
    itemlist.append(Item(label='Librerias disponibles:', type='label'))

    libsitemlist = []

    for lib in remote_libs:
        try:
            local_data = get_local_data(lib['path'])
            remote_version = lib.get('version')

            if local_data:
                if lib.get('version') != local_data.get('version'):
                    installed = False
                    _str = "Nueva versión disponible"
                    installed_version = local_data.get('version')
                else:
                    installed = True
                    _str = "Versión instalada: %s" % local_data.get('version', 'No disponible')
                    installed_version = local_data.get('version')
            else:
                installed = False
                _str = "No instalada"
                installed_version = None

            libsitemlist.append(item.clone(
                label=lib['name'],
                action='install' if not installed else 'uninstall',
                url=lib['url'],
                path=lib['path'],
                installed_version=installed_version,
                remote_version=remote_version,
                label_extra={
                    "sublabel": " [%s]",
                    "color": ("red", 'blue')[bool(local_data)],
                    "value": _str
                },
                folder=False,
                group=True
            ))

        except Exception:
            continue

    if not libsitemlist:
        itemlist.append(Item(
            label='¡No hay librerias disponibles para este sistema!',
            type='highlight',
            group=True
        ))
    else:
        itemlist.extend(libsitemlist)
    return itemlist


def get_libs():
    post = {
        'version': sys.version,
        'machine': platform.machine(),
        'platform': sys.platform
    }

    req = call_api('libraries', post)
    if req.sucess:
        try:
            return jsontools.load_json(req.data)['libs']
        except Exception:
            return []
    else:
        return []


def get_local_data(path):
    info_path = os.path.join(sysinfo.data_path, 'modules', 'lib', path, 'libinfo.json')
    dir_path = os.path.join(sysinfo.data_path, 'modules', 'lib', path)

    if not os.path.isdir(dir_path) or not os.path.isfile(info_path):
        return False

    try:
        libinfo = jsontools.load_json(open(info_path, 'rb').read())
    except Exception:
        libinfo = {}

    return libinfo


def uninstall(item):
    logger.trace()

    name = 'Kodi' if sysinfo.platform_name == 'kodi' else 'MediaExplorer'
    dir_path = os.path.join(sysinfo.data_path, 'modules', 'lib', item.path)

    if not platformtools.dialog_yesno(
            'MediaExplorer',
            'Se va a eliminar la libreria %s %s' % (item.label, item.installed_version),
            '¿Deseas continuar?'
    ):
        return

    try:
        if os.path.isdir(dir_path):
            shutil.rmtree(dir_path)
        elif os.path.isfile(dir_path):
            os.remove(dir_path)
    except Exception:
        platformtools.dialog_ok(
            'MediaExplorer: Librarias',
            'No se ha podido desinstalar la libreria \'%s\'' % item.label,
            'Probablemente porque este actualmente en uso',
            'Prueba de reiniciar %s y vuelve a intentarlo' % name
        )

    platformtools.itemlist_refresh()


def install(item):
    logger.trace()

    name = 'Kodi' if sysinfo.platform_name == 'kodi' else 'MediaExplorer'

    if not platformtools.dialog_yesno(
            'MediaExplorer',
            'Se va a descargar e instalar la libreria %s %s' % (item.label, item.remote_version),
            '¿Deseas continuar?',
            yeslabel='Si (recomendado)'
    ):
        return

    dialog = platformtools.dialog_progress('MediaExplorer', 'Descargando: %s' % os.path.basename(item.url))
    resp = httptools.downloadpage(item.url)

    if resp.sucess:
        try:
            dialog.update(80, 'Instalando: %s' % item.label)
            fileobj = BytesIO()
            fileobj.write(resp.data)
            ziptools.extract(fileobj, os.path.join(sysinfo.data_path, 'modules', 'lib'), True, True)
            dialog.close()
        except Exception:
            dialog.close()
            platformtools.dialog_ok(
                'MediaExplorer: Librarias',
                'No se ha podido instalar la libreria \'%s\'' % item.label,
                'Si el fallo persiste prueba de reiniciar %s' % name
            )

    else:
        dialog.close()
        platformtools.dialog_ok(
            'MediaExplorer: Librarias',
            'No se ha podido descargar la libreria \'%s\'' % item.label,
            'Comprueba la red y vuelve a intentarlo'
        )

    platformtools.itemlist_refresh()


def autointall():
    for lib in get_libs():
        install(Item(
            label=lib['name'],
            url=lib['url'],
            remote_version=lib.get('version')
        ))
