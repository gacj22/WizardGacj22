# -*- coding: utf-8 -*-
from core.libs import *
from sambatools import libsmb as samba

# Windows es "mbcs" linux, osx, android es "utf8"
if os.name == "nt":
    fs_encoding = ""
else:
    fs_encoding = "utf8"


def validate_path(path):
    """
    Elimina cáracteres no permitidos
    :param path: str
    :return: str
    """
    chars = ":*?<>|"
    if path.lower().startswith("smb://"):
        parts = re.split(r'smb://(.+?)/(.+)', path)[1:3]
        return "smb://" + parts[0] + "/" + ''.join([c for c in parts[1] if c not in chars])

    else:
        if path.find(":\\") == 1:
            unidad = path[0:3]
            path = path[2:]
        else:
            unidad = ""

        path = unidad + ''.join([c for c in path if c not in chars])

        if sysinfo.os.startswith('win') and  len(path) > 240:
            # Limite en NTFS longitud maxima
            # ver: https://docs.microsoft.com/es-es/windows/desktop/FileIO/naming-a-file#maximum-path-length-limitation
            parts = path.split(os.sep)
            name, extension = parts[-1].split('.')
            path = os.sep.join(parts[:-1])

            if len(path) + len(extension) < 220:
                name = name[:240 - len(path) - len(extension)] + '.' + extension
                path = os.sep.join([path, name])

        return path


def encode(path, _samba=False):
    """
    Codifica una ruta según el sistema operativo que estemos utilizando.
    El argumento path tiene que estar codificado en utf-8
    :param path: str
    :param _samba: bool
    :return: str
    """
    if not type(path) == unicode:
        path = unicode(path, "utf-8", "ignore")

    if path.lower().startswith("smb://") or _samba:
        path = path.encode("utf-8", "ignore")
    else:
        if fs_encoding:
            path = path.encode(fs_encoding, "ignore")

    return path


def decode(path):
    """
    Convierte una cadena de texto al juego de caracteres utf-8
    eliminando los caracteres que no estén permitidos en utf-8
    :param path: str
    :return: str
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


def read(path, start=0, count=None):
    """
    Lee el contenido de un archivo y devuelve los datos
    :param path: str
    :param start: int
    :param count: int
    :return:
    """
    path = encode(path)

    try:
        if path.lower().startswith("smb://"):
            f = samba.smb_open(path, "rb")
        else:
            f = open(path, "rb")

        data = []
        for x, line in enumerate(f):
            if x < start:
                continue
            if len(data) == count:
                break
            data.append(line)
        f.close()
    except Exception:
        logger.error()
        return None

    else:
        return "".join(data)


def write(path, data):
    """
    Guarda los datos en un archivo
    :param path: str
    :param data: str
    :return: bool
    """
    path = encode(path)

    try:
        if path.lower().startswith("smb://"):
            f = samba.smb_open(path, "wb")
        else:
            f = open(path, "wb")

        f.write(data)
        f.close()
    except Exception:
        logger.error()
        return False
    else:
        return True


def file_open(path, mode="r"):
    """
    Abre un archivo
    :param path: str
    :param mode: str
    :return: object
    """
    path = encode(path)

    try:
        if path.lower().startswith("smb://"):
            return samba.smb_open(path, mode)
        else:
            return open(path, mode)
    except Exception:
        logger.error()
        platformtools.dialog_notification("Error al abrir", path)
        return None


def rename(path, new_name):
    """
    Renombra un archivo o carpeta
    :param path: str
    :param new_name: str
    :return: bool
    """
    path = encode(path)

    try:
        if path.lower().startswith("smb://"):
            new_name = encode(new_name, True)
            samba.rename(path, join(dirname(path), new_name))
        else:
            new_name = encode(new_name, False)
            os.rename(path, os.path.join(os.path.dirname(path), new_name))
    except Exception:
        logger.error()
        platformtools.dialog_notification("Error al renombrar", path)
        return False
    else:
        return True


def move(path, dest):
    """
    Mueve un archivo
    :param path: str
    :param dest: str
    :return: bool
    """
    try:
        # samba/samba
        if path.lower().startswith("smb://") and dest.lower().startswith("smb://"):
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
            return copy(path, dest) is True and remove(path) is True
    except Exception:
        logger.error("ERROR al mover el archivo: %s" % path)
        return False
    else:
        return True


def copy(path, dest, silent=False):
    """
    Copia un archivo
    :param path: str
    :param dest: str
    :param silent: bool
    :return: bool
    """
    try:
        fo = file_open(path, "rb")
        fd = file_open(dest, "wb")

        if fo and fd:
            if not silent:
                dialog = platformtools.dialog_progress("Copiando archivo", "")
            size = getsize(path)
            sucess = 0
            while True:
                if not silent:
                    dialog.update(sucess * 100 / size, basename(path))
                buf = fo.read(1024 * 1024)
                if not buf:
                    break
                if not silent and dialog.iscanceled():
                    dialog.close()
                    return False
                fd.write(buf)
                sucess += len(buf)
            if not silent:
                dialog.close()
    except Exception:
        logger.error()
        return False
    else:
        return True


def exists(path):
    """
    Comprueba si existe una carpeta o fichero
    :param path: str
    :return: bool
    """
    path = encode(path)

    try:
        if path.lower().startswith("smb://"):
            return samba.exists(path)
        else:
            return os.path.exists(path)
    except Exception:
        logger.error()
        return False


def isfile(path):
    """
    Comprueba si la ruta es un fichero
    :param path: str
    :return: bool
    """
    path = encode(path)

    try:
        if path.lower().startswith("smb://"):
            return samba.isfile(path)
        else:
            return os.path.isfile(path)
    except Exception:
        logger.error()
        return False


def isdir(path):
    """
    Comprueba si la ruta es un directorio
    :param path: str
    :return: bool
    """
    path = encode(path)

    try:
        if path.lower().startswith("smb://"):
            return samba.isdir(path)
        else:
            return os.path.isdir(path)
    except Exception:
        logger.error()
        return False


def getsize(path):
    """
    Obtiene el tamaño de un archivo
    :param path: str
    :return: int
    """
    path = encode(path)

    try:
        if path.lower().startswith("smb://"):
            return long(samba.get_attributes(path).file_size)
        else:
            return os.path.getsize(path)
    except Exception:
        logger.error()
        return 0L


def remove(path):
    """
    Elimina un archivo
    :param path: str
    :return: bool
    """
    path = encode(path)

    try:
        if path.lower().startswith("smb://"):
            samba.remove(path)
        else:
            os.remove(path)
    except Exception:
        logger.error()
        platformtools.dialog_notification("Error al eliminar el archivo", path)
        return False
    else:
        return True


def rmdirtree(path):
    """
    Elimina un directorio y su contenido
    :param path: str
    :return: bool
    """
    path = encode(path)

    try:
        if path.lower().startswith("smb://"):
            for raiz, subcarpetas, ficheros in samba.walk(path, topdown=False):
                for f in ficheros:
                    samba.remove(join(decode(raiz), decode(f)))
                for s in subcarpetas:
                    samba.rmdir(join(decode(raiz), decode(s)))
            samba.rmdir(path)
        else:
            import shutil
            shutil.rmtree(path, ignore_errors=True)
    except Exception:
        logger.error()
        platformtools.dialog_notification("Error al eliminar el directorio", path)
        return False
    else:
        return not exists(path)


def rmdir(path):
    """
    Elimina un directorio
    :param path: str
    :return: bool
    """
    path = encode(path)

    try:
        if path.lower().startswith("smb://"):
            samba.rmdir(path)
        else:
            os.rmdir(path)
    except Exception:
        logger.error()
        platformtools.dialog_notification("Error al eliminar el directorio", path)
        return False
    else:
        return True


def makedirs(path):
    """
    Crea un directorio y subdirectorios si no existen
    :param path: str
    :return: bool
    """
    path = encode(path)

    try:
        if path.lower().startswith("smb://"):
            if not samba.exists(path):
                samba.makedirs(path)
        else:
            if not os.path.exists(path):
                os.makedirs(path)
    except Exception:
        logger.error()
        platformtools.dialog_notification("Error al crear el directorio", path)
        return False
    else:
        return True


def mkdir(path):
    """
    Crea un directorio
    :param path: str
    :return: bool
    """
    path = encode(path)

    try:
        if path.lower().startswith("smb://"):
            samba.mkdir(path)
        else:
            os.mkdir(path)
    except Exception:
        logger.error()
        platformtools.dialog_notification("Error al crear el directorio", path)
        return False
    else:
        return True


def walk(top, topdown=True, onerror=None):
    """
    Lista un directorio de manera recursiva
    :param top: str
    :param topdown: bool
    :param onerror: bool
    :return: iterator
    """
    top = encode(top)
    if top.lower().startswith("smb://"):
        for a, b, c in samba.walk(top, topdown, onerror):
            # list(b) es para que haga una copia del listado de directorios
            # si no da error cuando tiene que entrar recursivamente en directorios con caracteres especiales
            yield decode(a), decode(list(b)), decode(c)
    else:
        for a, b, c in os.walk(top, topdown, onerror):
            # list(b) es para que haga una copia del listado de directorios
            # si no da error cuando tiene que entrar recursivamente en directorios con caracteres especiales
            yield decode(a), decode(list(b)), decode(c)


def listdir(path):
    """
    Lista un directorio
    :param path: str
    :return: list
    """

    path = encode(path)

    try:
        if path.lower().startswith("smb://"):
            return decode(samba.listdir(path))
        else:
            return decode(os.listdir(path))
    except Exception:
        logger.error()
        return False


def join(*paths):
    """
    Junta varios directorios
    :param paths: tuple
    :return: str
    """
    list_path = []
    if paths[0].startswith("/"):
        list_path.append("")

    for path in paths:
        if path:
            list_path += path.replace("\\", "/").strip("/").split("/")

    if list_path[0].lower() == "smb:":
        return "/".join(list_path)
    else:
        return os.sep.join(list_path)


def split(path):
    """
    Devuelve una tupla formada por el directorio y el nombre del fichero de una ruta
    :param path: str
    :return: tuple
    """
    if path.lower().startswith("smb://"):
        if '/' not in path[6:]:
            path = path.replace("smb://", "smb:///", 1)
        return path.rsplit('/', 1)
    else:
        return os.path.split(path)


def basename(path):
    """
    Devuelve el nombre del fichero de una ruta
    :param path: str
    :return: str
    """
    return split(path)[1]


def dirname(path):
    """
    Devuelve el directorio de una ruta
    :param path: str
    :return: str
    """
    return split(path)[0]


def is_relative(path):
    """
    Comprueba si una ruta es relativa
    :param path: str
    :return: bool
    """
    return "://" not in path and not path.startswith("/") and ":\\" not in path


def normalize_dir(path):
    """
    Corrige los directorios que no acaban con '/'
    :param path: str
    :return: path
    """
    list_path = list(split(path))
    if list_path[-1] != '':
        list_path.append('')

    if list_path[0].lower() == "smb:":
        return "/".join(list_path)
    else:
        return os.path.join(*list_path)
