# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# filetools
# Gestion de archivos con discriminación xbmcvfs/samba/local
# ------------------------------------------------------------

import os
import traceback
import sys

from core import scrapertools
from platformcode import platformtools, logger

xbmc_vfs = True                                                 # False para desactivar XbmcVFS, True para activar
if xbmc_vfs:
    try:
        import xbmcvfs
        reload(sys)                                             ### Workoround.  Revisar en la migración a Python 3
        sys.setdefaultencoding('utf-8')                         # xbmcvfs degrada el valor de defaultencoding.  Se reestablece
        xbmc_vfs = True
    except:
        xbmc_vfs = False

samba = None
if not xbmc_vfs:
    try:
        from lib.sambatools import libsmb as samba
    except:
        samba = None
        # Python 2.4 No compatible con modulo samba, hay que revisar

# Windows es "mbcs" linux, osx, android es "utf8"
if os.name == "nt":
    fs_encoding = ""
else:
    fs_encoding = "utf8"



def validate_path(path):
    """
    Elimina cáracteres no permitidos
    @param path: cadena a validar
    @type path: str
    @rtype: str
    @return: devuelve la cadena sin los caracteres no permitidos
    """
    chars = ":*?<>|"
    if scrapertools.find_single_match(path, '(^\w+:\/\/)'):
        protocolo = scrapertools.find_single_match(path, '(^\w+:\/\/)')
        import re
        parts = re.split(r'^\w+:\/\/(.+?)/(.+)', path)[1:3]
        return protocolo + parts[0] + "/" + ''.join([c for c in parts[1] if c not in chars])

    else:
        if path.find(":\\") == 1:
            unidad = path[0:3]
            path = path[2:]
        else:
            unidad = ""

        return unidad + ''.join([c for c in path if c not in chars])


def encode(path, _samba=False):
    """
    Codifica una ruta según el sistema operativo que estemos utilizando.
    El argumento path tiene que estar codificado en utf-8
    @type path unicode o str con codificación utf-8
    @param path parámetro a codificar
    @type _samba bool
    @para _samba si la ruta es samba o no
    @rtype: str
    @return ruta codificada en juego de caracteres del sistema o utf-8 si samba
    """
    if not type(path) == unicode:
        path = unicode(path, "utf-8", "ignore")

    if scrapertools.find_single_match(path, '(^\w+:\/\/)') or _samba:
        path = path.encode("utf-8", "ignore")
    else:
        if fs_encoding:
            path = path.encode(fs_encoding, "ignore")

    return path


def decode(path):
    """
    Convierte una cadena de texto al juego de caracteres utf-8
    eliminando los caracteres que no estén permitidos en utf-8
    @type: str, unicode, list de str o unicode
    @param path: puede ser una ruta o un list() con varias rutas
    @rtype: str
    @return: ruta codificado en UTF-8
    """
    if type(path) == list:
        for x in range(len(path)):
            if not type(path[x]) == unicode:
                path[x] = path[x].decode(fs_encoding, "ignore")
            path[x] = path[x].encode("utf-8", "ignore")
    else:
        if not type(path) == unicode:
            path = path.decode(fs_encoding, "ignore")
        path = path.encode("utf-8", "ignore")
    return path


def read(path, linea_inicio=0, total_lineas=None, whence=0, silent=False, vfs=True):
    """
    Lee el contenido de un archivo y devuelve los datos
    @param path: ruta del fichero
    @type path: str
    @param linea_inicio: primera linea a leer del fichero
    @type linea_inicio: int positivo
    @param total_lineas: numero maximo de lineas a leer. Si es None o superior al total de lineas se leera el
        fichero hasta el final.
    @type total_lineas: int positivo
    @rtype: str
    @return: datos que contiene el fichero
    """
    path = encode(path)
    try:
        if type(linea_inicio) != int:
            try:
                linea_inicio = int(linea_inicio)
            except:
                logger.error('Read: ERROR de linea_inicio: %s' % str(linea_inicio))
                linea_inicio = 0
        if total_lineas != None and type(total_lineas) != int:
            try:
                total_lineas = int(total_lineas)
            except:
                logger.error('Read: ERROR de total_lineas: %s' % str(total_lineas))
                total_lineas = None
        if xbmc_vfs and vfs:
            if not exists(path): return False
            f = xbmcvfs.File(path, "rb")
            if linea_inicio > 0:
                if type(whence) != int:
                    try:
                        whence = int(whence)
                    except:
                        return False
                f.seek(linea_inicio, whence)
                logger.debug('POSICIÓN de comienzo de lectura, tell(): %s' % f.seek(0, 1))
            if total_lineas == None:
                total_lineas = 0
            data = f.read(total_lineas)
            return "".join(data)
        elif path.lower().startswith("smb://"):
            f = samba.smb_open(path, "rb")
        else:
            f = open(path, "rb")

        data = []
        for x, line in enumerate(f):
            if x < linea_inicio: continue
            if len(data) == total_lineas: break
            data.append(line)
        f.close()
    except:
        if not silent:
            logger.error("ERROR al leer el archivo: %s" % path)
            logger.error(traceback.format_exc())
        return False

    else:
        return "".join(data)


def write(path, data, silent=False, vfs=True):
    """
    Guarda los datos en un archivo
    @param path: ruta del archivo a guardar
    @type path: str
    @param data: datos a guardar
    @type data: str
    @rtype: bool
    @return: devuelve True si se ha escrito correctamente o False si ha dado un error
    """
    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            f = xbmcvfs.File(path, "wb")
        elif path.lower().startswith("smb://"):
            f = samba.smb_open(path, "wb")
        else:
            f = open(path, "wb")

        f.write(data)
        f.close()
    except:
        logger.error("ERROR al guardar el archivo: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
        return False
    else:
        return True


def file_open(path, mode="r", silent=False, vfs=True):
    """
    Abre un archivo
    @param path: ruta
    @type path: str
    @rtype: str
    @return: objeto file
    """
    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            if 'r' in mode and '+' in mode:
                mode = mode.replace('r', 'w').replace('+', '')
                logger.debug('Open MODE cambiado a: %s' % mode)
            if 'a' in mode:
                mode = mode.replace('a', 'w').replace('+', '')
                logger.debug('Open MODE cambiado a: %s' % mode)
            return xbmcvfs.File(path, mode)
        elif path.lower().startswith("smb://"):
            return samba.smb_open(path, mode)
        else:
            return open(path, mode)
    except:
        logger.error("ERROR al abrir el archivo: %s, %s" % (path, mode))
        if not silent:
            logger.error(traceback.format_exc())
            platformtools.dialog_notification("Error al abrir", path)
        return False


def file_stat(path, silent=False, vfs=True):
    """
    Stat de un archivo
    @param path: ruta
    @type path: str
    @rtype: str
    @return: objeto file
    """
    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            if not exists(path): return False
            return xbmcvfs.Stat(path)
        raise
    except:
        logger.error("File_Stat no soportado: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
        return False


def rename(path, new_name, silent=False, strict=False, vfs=True):
    """
    Renombra un archivo o carpeta
    @param path: ruta del fichero o carpeta a renombrar
    @type path: str
    @param new_name: nuevo nombre
    @type new_name: str
    @rtype: bool
    @return: devuelve False en caso de error
    """
    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            path_end = path
            if path_end.endswith('/') or path_end.endswith('\\'):
                path_end = path_end[:-1]
            dest = encode(join(dirname(path_end), new_name))
            result = xbmcvfs.rename(path, dest)
            if not result and not strict:
                logger.error("ERROR al RENOMBRAR el archivo: %s.  Copiando y borrando" % path)
                if not silent:
                    dialogo = platformtools.dialog_progress("Copiando archivo", "")
                result = xbmcvfs.copy(path, dest)
                if not result:
                    return False
                xbmcvfs.delete(path)
            return bool(result)
        elif path.lower().startswith("smb://"):
            new_name = encode(new_name, True)
            samba.rename(path, join(dirname(path), new_name))
        else:
            new_name = encode(new_name, False)
            os.rename(path, os.path.join(os.path.dirname(path), new_name))
    except:
        logger.error("ERROR al renombrar el archivo: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
            platformtools.dialog_notification("Error al renombrar", path)
        return False
    else:
        return True


def move(path, dest, silent=False, strict=False, vfs=True):
    """
    Mueve un archivo
    @param path: ruta del fichero a mover
    @type path: str
    @param dest: ruta donde mover
    @type dest: str
    @rtype: bool
    @return: devuelve False en caso de error
    """
    try:
        if xbmc_vfs and vfs:
            if not exists(path): return False
            path = encode(path)
            dest = encode(dest)
            result = xbmcvfs.rename(path, dest)
            if not result and not strict:
                logger.error("ERROR al MOVER el archivo: %s.  Copiando y borrando" % path)
                if not silent:
                    dialogo = platformtools.dialog_progress("Copiando archivo", "")
                result = xbmcvfs.copy(path, dest)
                if not result:
                    return False
                xbmcvfs.delete(path)
            return bool(result)
        # samba/samba
        elif path.lower().startswith("smb://") and dest.lower().startswith("smb://"):
            dest = encode(dest, True)
            path = encode(path, True)
            samba.rename(path, dest)

        # local/local
        elif not path.lower().startswith("smb://") and not dest.lower().startswith("smb://"):
            dest = encode(dest)
            path = encode(path)
            os.rename(path, dest)
        # mixto En este caso se copia el archivo y luego se elimina el de origen
        else:
            if not silent:
                dialogo = platformtools.dialog_progress("Copiando archivo", "")
            return copy(path, dest) == True and remove(path) == True
    except:
        logger.error("ERROR al mover el archivo: %s a %s" % (path, dest))
        if not silent:
            logger.error(traceback.format_exc())
        return False
    else:
        return True


def copy(path, dest, silent=False, vfs=True):
    """
    Copia un archivo
    @param path: ruta del fichero a copiar
    @type path: str
    @param dest: ruta donde copiar
    @type dest: str
    @param silent: se muestra o no el cuadro de dialogo
    @type silent: bool
    @rtype: bool
    @return: devuelve False en caso de error
    """
    try:
        if xbmc_vfs and vfs:
            path = encode(path)
            dest = encode(dest)
            if not silent:
                dialogo = platformtools.dialog_progress("Copiando archivo", "")
            return bool(xbmcvfs.copy(path, dest))
        
        fo = file_open(path, "rb")
        fd = file_open(dest, "wb")
        if fo and fd:
            if not silent:
                dialogo = platformtools.dialog_progress("Copiando archivo", "")
            size = getsize(path)
            copiado = 0
            while True:
                if not silent:
                    dialogo.update(copiado * 100 / size, basename(path))
                buf = fo.read(1024 * 1024)
                if not buf:
                    break
                if not silent and dialogo.iscanceled():
                    dialogo.close()
                    return False
                fd.write(buf)
                copiado += len(buf)
            if not silent:
                dialogo.close()
    except:
        logger.error("ERROR al copiar el archivo: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
        return False
    else:
        return True


def exists(path, silent=False, vfs=True):
    """
    Comprueba si existe una carpeta o fichero
    @param path: ruta
    @type path: str
    @rtype: bool
    @return: Retorna True si la ruta existe, tanto si es una carpeta como un archivo
    """
    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            result = bool(xbmcvfs.exists(path))
            if not result and not path.endswith('/') and not path.endswith('\\'):
                result = bool(xbmcvfs.exists(join(path, ' ').rstrip()))
            return result    
        elif path.lower().startswith("smb://"):
            return samba.exists(path)
        else:
            return os.path.exists(path)
    except:
        logger.error("ERROR al comprobar la ruta: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
        return False


def isfile(path, silent=False, vfs=True):
    """
    Comprueba si la ruta es un fichero
    @param path: ruta
    @type path: str
    @rtype: bool
    @return: Retorna True si la ruta existe y es un archivo
    """
    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            if not scrapertools.find_single_match(path, '(^\w+:\/\/)'):
                return os.path.isfile(path)
            if path.endswith('/') or path.endswith('\\'):
                path = path[:-1]
            dirs, files = xbmcvfs.listdir(dirname(path))
            base_name = basename(path)
            for file in files:
                if base_name == file:
                    return True
            return False
        elif path.lower().startswith("smb://"):
            return samba.isfile(path)
        else:
            return os.path.isfile(path)
    except:
        logger.error("ERROR al comprobar el archivo: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
        return False


def isdir(path, silent=False, vfs=True):
    """
    Comprueba si la ruta es un directorio
    @param path: ruta
    @type path: str
    @rtype: bool
    @return: Retorna True si la ruta existe y es un directorio
    """
    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            if not scrapertools.find_single_match(path, '(^\w+:\/\/)'):
                return os.path.isdir(path)
            if path.endswith('/') or path.endswith('\\'):
                path = path[:-1]
            dirs, files = xbmcvfs.listdir(dirname(path))
            base_name = basename(path)
            for dir in dirs:
                if base_name == dir:
                    return True
            return False
        elif path.lower().startswith("smb://"):
            return samba.isdir(path)
        else:
            return os.path.isdir(path)
    except:
        logger.error("ERROR al comprobar el directorio: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
        return False


def getsize(path, silent=False, vfs=True):
    """
    Obtiene el tamaño de un archivo
    @param path: ruta del fichero
    @type path: str
    @rtype: str
    @return: tamaño del fichero
    """
    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            if not exists(path): return 0L
            f = xbmcvfs.File(path)
            s = f.size()
            f.close()
            return s
        elif path.lower().startswith("smb://"):
            return long(samba.get_attributes(path).file_size)
        else:
            return os.path.getsize(path)
    except:
        logger.error("ERROR al obtener el tamaño: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
        return 0L


def remove(path, silent=False, vfs=True):
    """
    Elimina un archivo
    @param path: ruta del fichero a eliminar
    @type path: str
    @rtype: bool
    @return: devuelve False en caso de error
    """
    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            return bool(xbmcvfs.delete(path))
        elif path.lower().startswith("smb://"):
            samba.remove(path)
        else:
            os.remove(path)
    except:
        logger.error("ERROR al eliminar el archivo: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
            platformtools.dialog_notification("Error al eliminar el archivo", path)
        return False
    else:
        return True


def rmdirtree(path, silent=False, vfs=True):
    """
    Elimina un directorio y su contenido
    @param path: ruta a eliminar
    @type path: str
    @rtype: bool
    @return: devuelve False en caso de error
    """
    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            if not exists(path): return True
            if not path.endswith('/') and not path.endswith('\\'):
                path = join(path, ' ').rstrip()
            for raiz, subcarpetas, ficheros in walk(path, topdown=False):
                for f in ficheros:
                    xbmcvfs.delete(join(raiz, f))
                for s in subcarpetas:
                    xbmcvfs.rmdir(join(raiz, s))
            xbmcvfs.rmdir(path)
        elif path.lower().startswith("smb://"):
            for raiz, subcarpetas, ficheros in samba.walk(path, topdown=False):
                for f in ficheros:
                    samba.remove(join(decode(raiz), decode(f)))
                for s in subcarpetas:
                    samba.rmdir(join(decode(raiz), decode(s)))
            samba.rmdir(path)
        else:
            import shutil
            shutil.rmtree(path, ignore_errors=True)
    except:
        logger.error("ERROR al eliminar el directorio: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
            platformtools.dialog_notification("Error al eliminar el directorio", path)
        return False
    else:
        return not exists(path)


def rmdir(path, silent=False, vfs=True):
    """
    Elimina un directorio
    @param path: ruta a eliminar
    @type path: str
    @rtype: bool
    @return: devuelve False en caso de error
    """
    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            if not path.endswith('/') and not path.endswith('\\'):
                path = join(path, ' ').rstrip()
            return bool(xbmcvfs.rmdir(path))
        elif path.lower().startswith("smb://"):
            samba.rmdir(path)
        else:
            os.rmdir(path)
    except:
        logger.error("ERROR al eliminar el directorio: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
            platformtools.dialog_notification("Error al eliminar el directorio", path)
        return False
    else:
        return True


def mkdir(path, silent=False, vfs=True):
    """
    Crea un directorio
    @param path: ruta a crear
    @type path: str
    @rtype: bool
    @return: devuelve False en caso de error
    """
    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            if not path.endswith('/') and not path.endswith('\\'):
                path = join(path, ' ').rstrip()
            result = bool(xbmcvfs.mkdirs(path))
            if not result:
                import time
                time.sleep(0.1)
                result = exists(path)
            return result
        elif path.lower().startswith("smb://"):
            samba.mkdir(path)
        else:
            os.mkdir(path)
    except:
        logger.error("ERROR al crear el directorio: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
            platformtools.dialog_notification("Error al crear el directorio", path)
        return False
    else:
        return True


def walk(top, topdown=True, onerror=None, vfs=True):
    """
    Lista un directorio de manera recursiva
    @param top: Directorio a listar, debe ser un str "UTF-8"
    @type top: str
    @param topdown: se escanea de arriba a abajo
    @type topdown: bool
    @param onerror: muestra error para continuar con el listado si tiene algo seteado sino levanta una excepción
    @type onerror: bool
    ***El parametro followlinks que por defecto es True, no se usa aqui, ya que en samba no discrimina los links
    """
    top = encode(top)
    if xbmc_vfs and vfs:
        for a, b, c in walk_vfs(top, topdown, onerror):
            # list(b) es para que haga una copia del listado de directorios
            # si no da error cuando tiene que entrar recursivamente en directorios con caracteres especiales
            yield a, list(b), c
    elif top.lower().startswith("smb://"):
        for a, b, c in samba.walk(top, topdown, onerror):
            # list(b) es para que haga una copia del listado de directorios
            # si no da error cuando tiene que entrar recursivamente en directorios con caracteres especiales
            yield decode(a), decode(list(b)), decode(c)
    else:
        for a, b, c in os.walk(top, topdown, onerror):
            # list(b) es para que haga una copia del listado de directorios
            # si no da error cuando tiene que entrar recursivamente en directorios con caracteres especiales
            yield decode(a), decode(list(b)), decode(c)


def walk_vfs(top, topdown=True, onerror=None):
    """
    Lista un directorio de manera recursiva
    Como xmbcvfs no tiene esta función, se copia la lógica de libsmb(samba) para realizar la previa al Walk
    """
    top = encode(top)
    dirs, nondirs = xbmcvfs.listdir(top)

    if topdown:
        yield top, dirs, nondirs

    for name in dirs:
        new_path = "/".join(top.split("/") + [unicode(name, "utf8")])
        for x in walk_vfs(new_path, topdown, onerror):
            yield x
    if not topdown:
        yield top, dirs, nondirs


def listdir(path, silent=False, vfs=True):
    """
    Lista un directorio
    @param path: Directorio a listar, debe ser un str "UTF-8"
    @type path: str
    @rtype: str
    @return: contenido de un directorio
    """

    path = encode(path)
    try:
        if xbmc_vfs and vfs:
            dirs, files = xbmcvfs.listdir(path)
            return dirs + files
        elif path.lower().startswith("smb://"):
            return decode(samba.listdir(path))
        else:
            return decode(os.listdir(path))
    except:
        logger.error("ERROR al leer el directorio: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
        return False


def join(*paths):
    """
    Junta varios directorios
    Corrige las barras "/" o "\" segun el sistema operativo y si es o no smaba
    @rytpe: str
    @return: la ruta concatenada
    """
    list_path = []
    if paths[0].startswith("/"):
        list_path.append("")

    for path in paths:
        if path:
            if xbmc_vfs and scrapertools.find_single_match(paths[0], '(^\w+:\/\/)'):
                path = encode(path, True)
            elif xbmc_vfs:
                path = encode(path)
            list_path += path.replace("\\", "/").strip("/").split("/")

    if scrapertools.find_single_match(paths[0], '(^\w+:\/\/)'):
        return str("/".join(list_path))
    else:
        return str(os.sep.join(list_path))


def split(path, vfs=True):
    """
    Devuelve una tupla formada por el directorio y el nombre del fichero de una ruta
    @param path: ruta
    @type path: str
    @return: (dirname, basename)
    @rtype: tuple
    """
    if scrapertools.find_single_match(path, '(^\w+:\/\/)'):
        protocol = scrapertools.find_single_match(path, '(^\w+:\/\/)')
        if '/' not in path[6:]:
            path = path.replace(protocol, protocol + "/", 1)
        return path.rsplit('/', 1)
    else:
        return os.path.split(path)


def basename(path, vfs=True):
    """
    Devuelve el nombre del fichero de una ruta
    @param path: ruta
    @type path: str
    @return: fichero de la ruta
    @rtype: str
    """
    return split(path)[1]


def dirname(path, vfs=True):
    """
    Devuelve el directorio de una ruta
    @param path: ruta
    @type path: str
    @return: directorio de la ruta
    @rtype: str
    """
    return split(path)[0]


def is_relative(path):
    return "://" not in path and not path.startswith("/") and ":\\" not in path


def remove_tags(title):
    """
    devuelve el titulo sin tags como color
    @type title: str
    @param title: title
    @rtype: str
    @return: cadena sin tags
    """
    logger.info()

    title_without_tags = scrapertools.find_single_match(title, '\[color .+?\](.+)\[\/color\]')

    if title_without_tags:
        return title_without_tags
    else:
        return title
        
    
def remove_smb_credential(path):
    """
    devuelve el path sin contraseña/usuario para paths de SMB
    @param path: ruta
    @type path: str
    @return: cadena sin credenciales
    @rtype: str
    """
    logger.info()
    
    if not scrapertools.find_single_match(path, '(^\w+:\/\/)'):
        return path
    
    protocol = scrapertools.find_single_match(path, '(^\w+:\/\/)')
    path_without_credentials = scrapertools.find_single_match(path, '^\w+:\/\/(?:[^;\n]+;)?(?:[^:@\n]+[:|@])?(?:[^@\n]+@)?(.*?$)')

    if path_without_credentials:
        return (protocol + path_without_credentials)
    else:
        return path
