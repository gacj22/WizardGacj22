# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# filetools
# ------------------------------------------------------------
# Gestion de archivos con discriminación samba/local

import locale
import os
import sys
from socket import gaierror

from core import config
from core import logger
from core import scrapertools
from platformcode import platformtools

try:
    from lib.sambatools import libsmb as samba

except ImportError:
    try:
        import xbmc

        librerias = xbmc.translatePath(os.path.join(config.get_runtime_path(), 'lib'))
    except ImportError:
        xbmc = None
        librerias = os.path.join(config.get_runtime_path(), 'lib')

    sys.path.append(librerias)
    from sambatools import libsmb as samba


def text2filename(text):
    # Eliminamos o sustituimos los caracteres no validos

    filename = text.strip().lower()

    dict_char = {'á': 'a', 'à': 'a', 'ä': 'a', 'â': 'a',
                 'é': 'e', 'è': 'e', 'ë': 'e', 'ê': 'e',
                 'í': 'i', 'ì': 'i', 'ï': 'i', 'î': 'i',
                 'ó': 'o', 'ò': 'o', 'ö': 'o', 'ô': 'o',
                 'ú': 'u', 'ù': 'u', 'ü': 'u', 'û': 'u'}  # , 'ç':'c', 'ñ':'n'}
    for i, j in dict_char.iteritems():
        filename = filename.replace(i, j)

    filename = filter(lambda c: c in "abcçdefghijklmnñopqrstuvwxyz1234567890-_()[]'. ", filename)

    return filename


def remove_chars(path):
    """
    Elimina cáracteres no permitidos
    @param path: cadena a validar
    @type path: str
    @rtype: str
    @return: devuelve la cadena sin los caracteres no permitidos
    """
    chars = ":*?<>|"
    if path.lower().startswith("smb://"):
        import re
        parts = re.split(r'smb://(.+?)/(.+)', path)[1:3]
        return "smb://" + parts[0] + "/" + ''.join([c for c in parts[1] if c not in chars])

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

    if path.lower().startswith("smb://") or _samba:
        path = path.encode("utf-8", "ignore")
    else:
        _ENCODING = sys.getfilesystemencoding() or locale.getdefaultlocale()[1] or 'utf-8'
        path = path.encode(_ENCODING, "ignore")

    return remove_chars(path)


def decode(path):
    """
    Convierte una cadena de texto al juego de caracteres utf-8
    eliminando los caracteres que no estén permitidos en utf-8
    @type: str, unicode, list de str o unicode
    @param path: puede ser una ruta o un list() con varias rutas
    @rtype: str
    @return: ruta codificado en UTF-8
    """
    _ENCODING = sys.getfilesystemencoding() or locale.getdefaultlocale()[1] or 'utf-8'

    if type(path) == list:
        for x in range(len(path)):
            if not type(path[x]) == unicode:
                path[x] = path[x].decode(_ENCODING, "ignore")
            path[x] = path[x].encode("utf-8", "ignore")
    else:
        if not type(path) == unicode:
            path = path.decode(_ENCODING, "ignore")
        path = path.encode("utf-8", "ignore")
    return path


def read(path, linea_inicio=0, total_lineas=None):
    """
    Lee el contenido de un archivo y devuelve los datos
    @param path: ruta del fichero
    @type path: str
    @param linea_inicio: primera linea a leer del fichero
    @type linea_inicio: int positivo
    @param total_lineas: numero maximo de lineas a leer. Si es None, 0 o superior al total de lineas se leera el
        fichero hasta el final.
    @type total_lineas: int positivo
    @rtype: str
    @return: datos que contiene el fichero
    """
    path = encode(path)
    data = ""
    n_line = 0
    line_count = 0
    if total_lineas <= 0:
        total_lineas = None

    if path.lower().startswith("smb://"):
        from sambatools.smb.smb_structs import OperationFailure

        try:
            f = samba.get_file_handle_for_reading(os.path.basename(path), os.path.dirname(path))
            for line in f:
                if n_line >= linea_inicio:
                    data += line
                    line_count += 1
                n_line += 1
                if total_lineas is not None and line_count == int(total_lineas):
                    break
            f.close()

        except OperationFailure:
            logger.info("deportesalacarta.core.filetools read: ERROR al leer el archivo: {0}".format(path))

    else:
        try:
            f = open(path, "rb")
            for line in f:
                if n_line >= linea_inicio:
                    data += line
                    line_count += 1
                n_line += 1
                if total_lineas is not None and line_count == int(total_lineas):
                    break
            f.close()

        except EnvironmentError:
            logger.info("deportesalacarta.core.filetools read: ERROR al leer el archivo: %s" % path)

    return data


def write(path, data):
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
    if path.lower().startswith("smb://"):
        from sambatools.smb.smb_structs import OperationFailure
        try:
            samba.store_file(os.path.basename(path), data, os.path.dirname(path))
        except OperationFailure:
            logger.info("deportesalacarta.core.filetools write: Error al guardar el archivo: {0}".format(path))
            return False
        else:
            return True

    else:
        try:
            f = open(path, "wb")
            f.write(data)
            f.close()

        # except EnvironmentError:
        except Exception, ex:
            logger.info("filetools.write: Error al guardar el archivo: ")
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logger.info(message)
            # logger.info("deportesalacarta.core.filetools write: Error al guardar el archivo: {0}".format(path))
            return False
        else:
            return True


def open_for_reading(path):
    """
    Abre un archivo para leerlo
    @param path: ruta
    @type path: str
    @rtype: str
    @return: datos del fichero
    """
    path = encode(path)
    if path.lower().startswith("smb://"):
        return samba.get_file_handle_for_reading(os.path.basename(path), os.path.dirname(path))
    else:
        return open(path, "rb")


def rename(path, new_name):
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
    if path.lower().startswith("smb://"):
        new_name = encode(new_name, True)
        try:
            samba.rename(os.path.basename(path), new_name, os.path.dirname(path))
        except:
            import traceback
            logger.info(
                "deportesalacarta.core.filetools mkdir: Error al renombrar el archivo o carpeta" + traceback.format_exc())
            platformtools.dialog_notification("Error al renombrar", path)
            return False
    else:
        new_name = encode(new_name, False)
        try:
            os.rename(path, os.path.join(os.path.dirname(path), new_name))
        except OSError:
            import traceback
            logger.info(
                "deportesalacarta.core.filetools mkdir: Error al renombrar el archivo o carpeta" + traceback.format_exc())
            platformtools.dialog_notification("Error al renombrar", path)
            return False

    return True


def exists(path):
    """
    Comprueba si existe una carpeta o fichero
    @param path: ruta
    @type path: str
    @rtype: bool
    @return: Retorna True si la ruta existe, tanto si es una carpeta como un archivo
    """
    path = encode(path)
    if path.lower().startswith("smb://"):
        try:
            return samba.file_exists(os.path.basename(path), os.path.dirname(path)) or \
                   samba.folder_exists(os.path.basename(path), os.path.dirname(path))
        except gaierror:
            logger.info("deportesalacarta.core.filetools exists: No es posible conectar con la ruta")
            platformtools.dialog_notification("No es posible conectar con la ruta", path)
            return True
    else:
        return os.path.exists(path)


def isfile(path):
    """
    Comprueba si la ruta es un fichero
    @param path: ruta
    @type path: str
    @rtype: bool
    @return: Retorna True si la ruta existe y es un archivo
    """
    path = encode(path)
    if path.lower().startswith("smb://"):
        return samba.file_exists(os.path.basename(path), os.path.dirname(path))
    else:
        return os.path.isfile(path)


def isdir(path):
    """
    Comprueba si la ruta es un directorio
    @param path: ruta
    @type path: str
    @rtype: bool
    @return: Retorna True si la ruta existe y es un directorio
    """
    path = encode(path)
    if path.lower().startswith("smb://"):
        if path.endswith("/"):
            path = path[:-1]

        return samba.folder_exists(os.path.basename(path), os.path.dirname(path))
    else:
        return os.path.isdir(path)


def getsize(path):
    """
    Obtiene el tamaño de un archivo
    @param path: ruta del fichero
    @type path: str
    @rtype: str
    @return: tamaño del fichero
    """
    path = encode(path)
    if path.lower().startswith("smb://"):
        return samba.get_attributes(os.path.basename(path), os.path.dirname(path)).file_size
    else:
        return os.path.getsize(path)


def remove(path):
    """
    Elimina un archivo
    @param path: ruta del fichero a eliminar
    @type path: str
    @rtype: bool
    @return: devuelve False en caso de error
    """
    path = encode(path)
    if path.lower().startswith("smb://"):
        try:
            samba.delete_files(os.path.basename(path), os.path.dirname(path))
        except:
            import traceback
            logger.info("deportesalacarta.core.filetools mkdir: Error al eliminar el archivo " + traceback.format_exc())
            platformtools.dialog_notification("Error al eliminar el archivo", path)
            return False
    else:
        try:
            os.remove(path)
        except OSError:
            import traceback
            logger.info("deportesalacarta.core.filetools mkdir: Error al eliminar el archivo " + traceback.format_exc())
            platformtools.dialog_notification("Error al eliminar el archivo", path)
            return False

    return True


def rmdirtree(path):
    """
    Elimina un directorio y su contenido
    @param path: ruta a eliminar
    @type path: str
    @rtype: bool
    @return: devuelve False en caso de error
    """

    path = encode(path)
    if path.lower().startswith("smb://"):
        try:
            for raiz, subcarpetas, ficheros in walk(path, topdown=False):
                samba.delete_files(ficheros, raiz)
                for s in subcarpetas:
                    samba.delete_directory(s, raiz)
        except:
            pass
    else:
        import shutil
        shutil.rmtree(path, ignore_errors=True)

    if exists(path):  # No se ha eliminado
        return False

    return True


def rmdir(path):
    """
    Elimina un directorio
    @param path: ruta a eliminar
    @type path: str
    @rtype: bool
    @return: devuelve False en caso de error
    """
    path = encode(path)

    if path.lower().startswith("smb://"):
        try:
            samba.delete_directory(os.path.basename(path), os.path.dirname(path))
        except:
            import traceback
            logger.info("deportesalacarta.core.filetools mkdir: Error al eliminar el directorio " + traceback.format_exc())
            platformtools.dialog_notification("Error al eliminar el directorio", path)
            return False
    else:
        try:
            os.rmdir(path)
        except OSError:
            import traceback
            logger.info("deportesalacarta.core.filetools mkdir: Error al eliminar el directorio " + traceback.format_exc())
            platformtools.dialog_notification("Error al eliminar el directorio", path)
            return False

    return True


def mkdir(path):
    """
    Crea un directorio
    @param path: ruta a crear
    @type path: str
    @rtype: bool
    @return: devuelve False en caso de error
    """
    logger.info("deportesalacarta.core.filetools mkdir " + path)

    path = encode(path)
    if path.lower().startswith("smb://"):
        try:
            samba.create_directory(os.path.basename(path), os.path.dirname(path))
        except gaierror:
            import traceback
            logger.info("deportesalacarta.core.filetools mkdir: Error al crear la ruta " + traceback.format_exc())
            platformtools.dialog_notification("Error al crear la ruta", path)
            return False
    else:
        try:
            # path = normalize(path, respect)
            os.mkdir(path)
        except OSError:
            import traceback
            logger.info("deportesalacarta.core.filetools mkdir: Error al crear la ruta " + traceback.format_exc())
            platformtools.dialog_notification("Error al crear la ruta", path)
            return False

    return True


# def normalize(s, respect=True):
#     """
#     Convierte a unicode las tildes de una cadena o las elimina.
#     @param s: cadena a convertir
#     @type s: str
#     @param respect: valor que especifica el tipo de formulario, si conversa los caracteres originales
#     @bool respect: bool
#     @rtype: str
#     @return: devuelve la conversión
#     """
#     if respect:
#         form = "NFC"
#     else:
#         form = "NFD"
#
#     import unicodedata
#     if not isinstance(s, unicode):
#         s = s.decode("UTF-8")
#     return ''.join((c for c in unicodedata.normalize(form, s) if unicodedata.category(c) != 'Mn'))


def join(*paths):
    """
    Junta varios directorios
    @rytpe: str
    @return: la ruta concatenada
    """
    if paths[0].lower().startswith("smb://"):
        return paths[0].strip("/") + "/" + "/".join(paths[1:])
    else:
        import os
        return os.path.join(*paths)


def walk(top, topdown=True, onerror=None):
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
    if top.lower().startswith("smb://"):
        try:
            names = listdir(top)
        except Exception, _err:
            if onerror is not None:
                onerror(_err)
            return

        dirs, nondirs = [], []
        for name in names:
            if isdir(join(top, name)):
                dirs.append(name)
            else:
                nondirs.append(name)
        if topdown:
            yield top, dirs, nondirs

        for name in dirs:
            new_path = join(top, name)
            for x in walk(new_path, topdown, onerror):
                yield x
        if not topdown:
            yield top, dirs, nondirs

    else:
        for a, b, c in os.walk(top, topdown, onerror):
            # list(b) es para que haga una copia del listado de directorios
            # si no da error cuando tiene que entrar recursivamente en directorios con caracteres especiales
            yield decode(a), decode(list(b)), decode(c)


def listdir(path):
    """
    Lista un directorio
    @param path: Directorio a listar, debe ser un str "UTF-8"
    @type path: str
    @rtype: str
    @return: contenido de un directorio
    """

    path = encode(path)
    if path.lower().startswith("smb://"):
        files, directories = samba.get_files_and_directories(path)
        files_directories = files + directories
        return decode(files_directories)
    else:
        return decode(os.listdir(path))


def split(path):
    """
    Devuelve una tupla formada por el directorio y el nombre del fichero de una ruta
    @param path: ruta
    @type path: str
    @return: (dirname, basename)
    @rtype: tuple
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
    @param path: ruta
    @type path: str
    @return: fichero de la ruta
    @rtype: str
    """
    return split(path)[1]


def dirname(path):
    """
    Devuelve el directorio de una ruta
    @param path: ruta
    @type path: str
    @return: directorio de la ruta
    @rtype: str
    """
    return split(path)[0]


def remove_tags(title):
    """
    devuelve el titulo sin tags como color
    @type title: str
    @param title: title
    @rtype: str
    @return: cadena sin tags
    """
    logger.info("deportesalacarta.core.filetools remove_tags")

    title_without_tags = scrapertools.find_single_match(title, '\[color .+?\](.+)\[\/color\]')

    if title_without_tags:
        return title_without_tags
    else:
        return title
