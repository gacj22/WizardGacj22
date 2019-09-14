# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Acceso a directorios con samba
# ------------------------------------------------------------
import os
import sys

from core import config
from core import logger

try:
    import xbmc
    librerias = xbmc.translatePath(os.path.join(config.get_runtime_path(), 'lib', 'sambatools'))
except ImportError:
    xbmc = None
    librerias = os.path.join(config.get_runtime_path(), 'lib', 'sambatools')

if librerias not in sys.path:
    sys.path.append(librerias)


def parse_url(url):
    logger.info("[lib.samba.py] url=" + url)

    # Algunas trampas para facilitar el parseo de la url
    url = url.strip()
    if not url.endswith("/"):
        url += "/"

    import re
    patron = 'smb\:\/\/([^\:]+)\:([^\@]+)@([^\/]+)\/([^\/]+)\/(.*\/)?'
    matches = re.compile(patron, re.DOTALL).findall(url)

    if len(matches) > 0:
        logger.info("url con login y password")
        server_name = matches[0][2]
        share_name = matches[0][3]
        path = matches[0][4]
        user = matches[0][0]
        password = matches[0][1]
    else:
        logger.info("url sin login y password")
        patron = 'smb\:\/\/([^\/]+)\/([^\/]+)/(.*/)?'
        matches = re.compile(patron, re.DOTALL).findall(url)

        if len(matches) > 0:
            server_name = matches[0][0]
            share_name = matches[0][1]
            path = matches[0][2]
            user = ""
            password = ""
        else:
            server_name = ""
            share_name = ""
            path = ""
            user = ""
            password = ""

    if path == "":
        path = "/"

    # logger.info("[lib.samba.py] server_name=" + server_name + ", share_name=" + share_name + ", path=" + path + ",
    # user=" + user + ", password=" + password)

    if type(server_name) == unicode:
        server_name = server_name.encode("utf8")
    if type(user) == unicode:
        user = user.encode("utf8")
    if type(password) == unicode:
        password = password.encode("utf8")
    if type(share_name) == unicode:
        share_name = share_name.encode("utf8")

    return server_name, share_name, path, user, password


def connect(server_name, user, password, domain='', use_ntlm_v2=True):
    logger.info("[lib.samba.py] connect")

    from smb.SMBConnection import SMBConnection
    import socket

    from smb import smb_structs
    smb_structs.SUPPORT_SMB2 = False

    if user == 'quest' or user == 'anonnimo' or user == 'invitado' or user == 'anonimo' or user == '' or user is None:
        user = 'quest'
        password = ''

    logger.info("[lib.samba.py] Averigua IP...")
    server_ip = socket.gethostbyname(server_name)
    logger.info("[lib.samba.py] server_ip=" + server_ip)

    logger.info("[lib.samba.py] Crea smb...")
    try:
        remote = SMBConnection(user, password, domain, server_name, use_ntlm_v2=use_ntlm_v2)
        conn = remote.connect(server_ip, 139)
    except:
        remote = SMBConnection(user, password, domain, server_ip, use_ntlm_v2=use_ntlm_v2)
        conn = remote.connect(server_ip, 139)

    logger.info("[lib.samba.py] Conexión realizada con éxito")

    return remote


def get_files(url):
    logger.info("[lib.samba.py] get_files")

    server_name, share_name, path, user, password = parse_url(url)
    remote = connect(server_name, user, password)

    files = []
    for f in remote.listPath(share_name, path):
        name = f.filename
        if name == '.' or name == '..':
            continue
        if f.isDirectory:
            continue
        files.append(name)

    remote.close()

    return files


def get_directories(url):
    logger.info("[lib.samba.py] get_directories")

    server_name, share_name, path, user, password = parse_url(url)
    remote = connect(server_name, user, password)

    directories = []
    for f in remote.listPath(share_name, path):
        name = f.filename
        if name == '.' or name == '..':
            continue
        if not f.isDirectory:
            continue
        directories.append(name)

    remote.close()

    return directories


def get_files_and_directories(url):
    logger.info("[lib.samba.py] get_files_and_directories")

    server_name, share_name, path, user, password = parse_url(url)
    remote = connect(server_name, user, password)

    files = []
    directories = []
    for f in remote.listPath(share_name, path):
        name = f.filename
        if name == '.' or name == '..':
            continue
        if f.isDirectory:
            directories.append(name)
        else:
            files.append(name)

    remote.close()

    return files, directories


def get_attributes(file_or_folder, url):
    logger.info("[lib.samba.py] get_attributes" + file_or_folder)

    if file_exists(file_or_folder, url) or folder_exists(file_or_folder, url):
        server_name, share_name, path, user, password = parse_url(url)
        remote = connect(server_name, user, password)
        attributes = remote.getAttributes(share_name, path + file_or_folder)
        remote.close()
        return attributes
    else:
        return None


def store_file(_file, data, url):
    logger.info("[lib.samba.py] write_file")

    server_name, share_name, path, user, password = parse_url(url)
    remote = connect(server_name, user, password)

    logger.info("Crea fichero temporal")
    try:
        import xbmc
        localfilename = xbmc.translatePath("special://temp")
    except ImportError:
        xbmc = None
        localfilename = config.get_data_path()
    logger.info("localfilename="+localfilename)

    localfilename = os.path.join(localfilename, "bookmark.tmp")
    bookmarkfile = open(localfilename, "wb")
    bookmarkfile.write(data)
    bookmarkfile.flush()
    bookmarkfile.close()

    # Copia el bookmark al directorio Samba
    logger.info("Crea el fichero remoto")
    bookmarkfile = open(localfilename, "rb")
    remote.storeFile(share_name, path + _file, bookmarkfile)
    bookmarkfile.close()

    # Borra el fichero temporal
    logger.info("Borra el fichero local")
    os.remove(localfilename)

    remote.close()


def create_directory(folder, url):
    logger.info("[lib.samba.py] create_directory " + folder)

    server_name, share_name, path, user, password = parse_url(url)
    remote = connect(server_name, user, password)
    remote.createDirectory(share_name, path + folder)
    remote.close()


def get_file_handle_for_reading(_file, url):
    logger.info("[lib.samba.py] get_file_handle_for_reading")

    server_name, share_name, path, user, password = parse_url(url)
    remote = connect(server_name, user, password)

    # Crea un fichero temporal con el bookmark
    logger.info("[lib.samba.py] Crea fichero temporal")
    try:
        import xbmc
        localfilename = xbmc.translatePath("special://temp")
    except ImportError:
        xbmc = None
        localfilename = config.get_data_path()
    logger.info("[lib.samba.py] localfilename=" + localfilename)

    localfilename = os.path.join(localfilename, "bookmark.tmp")

    # Lo abre
    bookmarkfile = open(localfilename, "wb")

    # Lo copia de la URL
    try:
        remote.retrieveFile(share_name, path + _file, bookmarkfile)
    finally:
        bookmarkfile.close()

    remote.close()

    return open(localfilename)


def file_exists(_file, url):
    logger.info("[lib.samba.py] file_exists " + _file)

    server_name, share_name, path, user, password = parse_url(url)
    remote = connect(server_name, user, password)

    files = []
    for f in remote.listPath(share_name, path):
        name = f.filename
        if name == '.' or name == '..':
            continue
        if f.isDirectory:
            continue
        files.append(name)

    remote.close()

    try:
        logger.info(str(files.index(_file)))
        return True
    except:
        return False


def folder_exists(folder, url):
    logger.info("[lib.samba.py] folder_exists " + folder)

    server_name, share_name, path, user, password = parse_url(url)
    remote = connect(server_name, user, password)

    directory = []
    for f in remote.listPath(share_name, path):
        name = f.filename
        if name == '.' or name == '..':
            continue
        if not f.isDirectory:
            continue
        directory.append(name)

    remote.close()

    try:
        logger.info(str(directory.index(folder)))
        return True
    except:
        return False


def delete_files(_file, url):
    if type(_file) is list:
        server_name, share_name, path, user, password = parse_url(url)
        remote = connect(server_name, user, password)
        for f in _file:
            logger.info("[lib.samba.py] delete_files " + f)
            remote.deleteFiles(share_name, path + f)
        remote.close()
    else:
        logger.info("[lib.samba.py] delete_files " + _file)
        if file_exists(_file, url):
            server_name, share_name, path, user, password = parse_url(url)
            remote = connect(server_name, user, password)
            remote.deleteFiles(share_name, path + _file)
            remote.close()


def delete_directory(folder, url):
    logger.info("[lib.samba.py] create_directory " + folder)

    if folder_exists(folder, url):
        server_name, share_name, path, user, password = parse_url(url)
        remote = connect(server_name, user, password)
        remote.deleteDirectory(share_name, path + folder)

        remote.close()


def rename(old_name, new_name, url):
    logger.info("[lib.samba.py] rename %s to %s" %(old_name, new_name))

    if folder_exists(old_name, url) or file_exists(old_name, url):
        server_name, share_name, path, user, password = parse_url(url)
        remote = connect(server_name, user, password)
        remote.rename(share_name, path + old_name, path + new_name)

    remote.close()


def usingsamba(path):
    return path.upper().startswith("SMB://")
