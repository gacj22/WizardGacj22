# -*- coding: utf-8 -*-
import ziptools
from core import anonfile
from core.libs import *

backup_file = os.path.join(sysinfo.data_path, 'backup.zip')
base_dir = os.path.join(sysinfo.data_path, 'settings')


def mainlist(item):
    logger.trace()
    itemlist = []
    aux = []

    saved_backups = settings.get_setting('saved_backups', __file__) or {}

    itemlist.append(item.clone(
        label='Crear una nueva copia de seguridad',
        type='item1',
        action='new_backup',
        folder=False,
        description='Crea una copia de seguridad con la configuración actual.\nAtención esta copia podría contener nombres de usuarios y contaseñas personales.'
    ))

    itemlist.append(item.clone(
        label='Restaurar copia de seguridad',
        type='item1',
        action='restore_backup',
        folder=False,
        description='Restaura una copia de seguridad creada anteriormente introduciendo el ID manualmente'
    ))

    if saved_backups:
        itemlist.append(Item())
        itemlist.append(Item(label='Copias de seguridad guardadas:', type='item'))
        for _id, info in saved_backups.items():
            date = datetime.datetime.utcfromtimestamp(info['date']).strftime('%d/%m/%Y %H:%M:%S UTC')
            aux.append(item.clone(
                label='%s' % _id,
                label_extra={"sublabel": " [%s]", "color": "color1", "value": "%s" % date},
                backupid=_id,
                backupdate= date,
                poster=info['img'] or item.poster,
                type='item',
                action='restore_backup',
                folder=False,
                description='Restaura la copia de seguridad con ID %s:\n%s' % (_id,'\n'.join(info['include'])),
                group=True,
                context=[{'label': "Eliminar copia de seguridad", "context_action": 'delete_backup'}]
            ))

        itemlist.extend(sorted(aux, key=lambda x: x.backupdate, reverse=True))

    return itemlist


def new_backup(item):
    logger.trace()

    controls = [
        {
            'id': 'set_password',
            'label': 'Proteger la copia mediante contraseña:',
            'type': 'bool',
            'value': False,
            'default': False
        },
        {
            'id': 'password',
            'label': 'Contraseña:',
            'type': 'text',
            'hidden': True,
            'value': '',
            'default': '',
            'enabled': 'eq(-1,true)'
        },
        {
            'id': 'channels',
            'label': 'Guardar configuración de Canales:',
            'type': 'bool',
            'value': True,
            'default': True
        },
        {
            'id': 'servers',
            'label': 'Guardar configuración de Servidores:',
            'type': 'bool',
            'value': True,
            'default': True
        },
        {
            'id': 'core',
            'label': 'Guardar configuración General:',
            'type': 'bool',
            'value': True,
            'default': True
        },
        {
            'id': 'platformcode',
            'label': 'Guardar configuración de Aspecto y otras especificas de %s:' % sysinfo.platform_name,
            'type': 'bool',
            'value': True,
            'default': True
        }
    ]

    return platformtools.show_settings(controls=controls, title=item.label, callback="do_backup")


def do_backup(item, values):
    logger.trace()

    if os.path.isfile(backup_file):
        os.remove(backup_file)

    if values.pop('set_password'):
        password = values.pop('password')
        if not password:
            platformtools.dialog_ok('Copia de seguridad', 'Debes introducir una contraseña o desactivar la opcion')
            return
    else:
        password = None

    if not any(values.values()):
        platformtools.dialog_ok('Copia de seguridad', 'No has seleccionado ninguna opción, la copia ha sido cancelada')
        return

    if not password and not platformtools.dialog_yesno('Copia de seguridad',
            'Vas a realizar una copia de seguridad sin contraseña.\n'
            'Recomendamos siempre proteger las copias de seguridad mediante contraseña.\n'
            '¿Deseas continuar de todos modos?'):
        return

    filelist = []
    include = set()
    for root, folder, files in os.walk(base_dir):
        for fname in files:
            a = os.path.join(root, fname)
            if os.path.join(base_dir, 'channels') == os.path.dirname(a):
                if values['channels']:
                    include.add('  - Configuración de Canales')
                else:
                    continue
            if os.path.join(base_dir, 'servers') == os.path.dirname(a):
                if values['servers']:
                    include.add('  - Configuración de Servidores')
                else:
                    continue
            if os.path.join(base_dir, 'core') == os.path.dirname(a):
                if values['core']:
                    include.add('  - Configuración General')
                else:
                    continue
            if os.path.join(base_dir, 'platformcode') == os.path.dirname(a):
                if values['platformcode']:
                    include.add('  - Configuración de Aspecto y otras especificas de %s' % sysinfo.platform_name)
                else:
                    continue
            filelist.append([os.path.join(root.replace(base_dir, 'settings'), fname), a])

    # Añadimos la fecha del backup
    backup_info = {'date': time.time(), 'include': list(include), 'img': None}
    filelist.append(['backup_info.json', jsontools.dump_json(backup_info)])

    ziptools.create_zip(backup_file, filelist, True, password=password)

    dialog = platformtools.dialog_progress('Copia de seguridad', 'Subiendo a Anonfile...')
    response_id = anonfile.upload(backup_file)
    dialog.close()

    if not response_id:
        platformtools.dialog_ok('Copia de seguridad', 'Se ha producido un error al subir el archivo al servidor')
    else:
        url = 'https://anonfile.com/%s' % response_id
        logger.debug(url)
        img = 'http://www.codigos-qr.com/qr/php/qr_img.php?d=%s&s=6&e=m' % url
        backup_info['img'] = img

        # Añadimos el backup a la lista
        saved_backups = settings.get_setting('saved_backups', __file__) or {}
        saved_backups[response_id] = backup_info
        settings.set_setting('saved_backups', saved_backups, __file__)

        # Mostramos el mensaje
        msg = 'La copia se ha generado con éxito.\nEl ID es: %s\n' % response_id
        msg += 'Usa este ID para restaurar la configuración en cualquier dispositivo'
        msg += "\n\nTambien se ha subido a '%s'\nPuedes descargarlo escaneando el codigo QR" % url
        platformtools.dialog_img_yesno(img, 'MediaExplorer : Copia de seguridad completada', msg, False)


    platformtools.itemlist_refresh()


def delete_backup(item):
    logger.trace()

    saved_backups = settings.get_setting('saved_backups', __file__)
    del saved_backups[item.backupid]
    settings.set_setting('saved_backups', saved_backups, __file__)
    platformtools.itemlist_refresh()


def restore_backup(item):
    logger.trace()

    # Obtenemos el listado de backups antes de restaurar
    saved_backups = settings.get_setting('saved_backups', __file__) or {}

    if os.path.isfile(backup_file):
        os.remove(backup_file)

    if item.backupid:
        op = platformtools.dialog_select('Selecciona una opción', ['Restaurar copia', 'Eliminar copia'])
        if op == -1:
            return
        elif op == 1:
            del saved_backups[item.backupid]
            settings.set_setting('saved_backups', saved_backups, __file__)
            platformtools.itemlist_refresh()
            return
        else:
            code = item.backupid
    else:
        code = platformtools.dialog_input('', 'Introduce el ID de la copia que quieres restaurar')
        if not code:
            return

    dialog = platformtools.dialog_progress('Restaurando Copia de seguridad', 'Descargando archivo', 'ID: %s' % code)
    downloaded = anonfile.download(code, backup_file)
    dialog.update(30,  "Descomprimiendo...")

    if downloaded:
        try:
            ziptools.extract(backup_file, sysinfo.data_path, True, True)
            dialog.close()
        except Exception:
            logger.error()
            dialog.close()
            platformtools.dialog_ok('Copia de seguridad', 'Se ha producido un error al extraer el archivo')
            return
    else:
        dialog.close()
        platformtools.dialog_ok('Copia de seguridad', 'Se ha producido un error al descargar el archivo')
        return

    # Obtenemos la información del backup restaurado
    backup_info = jsontools.load_json(open(os.path.join(sysinfo.data_path, 'backup_info.json'), 'rb').read())

    # Añadimos el backup restaurado a la lista
    backup_info['img'] = 'http://www.codigos-qr.com/qr/php/qr_img.php?d=https://anonfile.com/%s&s=6&e=m' % code
    saved_backups[code] = backup_info

    # Añadimos los backups que habian en el zip si no estaban ya
    saved_backups.update(settings.get_setting('saved_backups', __file__))

    # Y los guardamos
    settings.set_setting('saved_backups', saved_backups, __file__)
    platformtools.dialog_ok('Copia de seguridad', 'Copia de seguridad restaurada con exito')

    if os.path.isfile(os.path.join(sysinfo.data_path, 'backup_info.json')):
        os.remove(os.path.join(sysinfo.data_path, 'backup_info.json'))

    platformtools.itemlist_refresh()
