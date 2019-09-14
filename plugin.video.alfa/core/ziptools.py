# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Zip Tools
# --------------------------------------------------------------------------------

import os
import zipfile

from platformcode import config, logger
from core import filetools


class ziptools:
    def extract(self, file, dir, folder_to_extract="", overwrite_question=False, backup=False):
        logger.info("file=%s" % file)
        logger.info("dir=%s" % dir)

        if not dir.endswith(':') and not filetools.exists(dir):
            filetools.mkdir(dir)

        zf = zipfile.ZipFile(file)
        if not folder_to_extract:
            self._createstructure(file, dir)
        num_files = len(zf.namelist())

        for nameo in zf.namelist():
            name = nameo.replace(':', '_').replace('<', '_').replace('>', '_').replace('|', '_').replace('"', '_').replace('?', '_').replace('*', '_')
            logger.info("name=%s" % nameo)
            if not name.endswith('/'):
                logger.info("no es un directorio")
                try:
                    (path, filename) = filetools.split(filetools.join(dir, name))
                    logger.info("path=%s" % path)
                    logger.info("name=%s" % name)
                    if folder_to_extract:
                        if path != filetools.join(dir, folder_to_extract):
                            break
                    else:
                        filetools.mkdir(path)
                except:
                    pass
                if folder_to_extract:
                    outfilename = filetools.join(dir, filename)

                else:
                    outfilename = filetools.join(dir, name)
                logger.info("outfilename=%s" % outfilename)
                try:
                    if filetools.exists(outfilename) and overwrite_question:
                        from platformcode import platformtools
                        dyesno = platformtools.dialog_yesno("El archivo ya existe",
                                                            "El archivo %s a descomprimir ya existe" \
                                                            ", ¿desea sobrescribirlo?" \
                                                            % filetools.basename(outfilename))
                        if not dyesno:
                            break
                        if backup:
                            import time
                            hora_folder = "Copia seguridad [%s]" % time.strftime("%d-%m_%H-%M", time.localtime())
                            backup = filetools.join(config.get_data_path(), 'backups', hora_folder, folder_to_extract)
                            if not filetools.exists(backup):
                                filetools.mkdir(backup)
                            filetools.copy(outfilename, filetools.join(backup, filetools.basename(outfilename)))

                    outfile = filetools.file_open(outfilename, 'wb')
                    outfile.write(zf.read(nameo))
                except:
                    import traceback
                    logger.error(traceback.format_exc())
                    logger.error("Error en fichero " + nameo)

    def _createstructure(self, file, dir):
        self._makedirs(self._listdirs(file), dir)

    def create_necessary_paths(filename):
        try:
            (path, name) = filetools.split(filename)
            filetools.mkdir(path)
        except:
            pass

    def _makedirs(self, directories, basedir):
        for dir in directories:
            curdir = filetools.join(basedir, dir)
            if not filetools.exists(curdir):
                filetools.mkdir(curdir)

    def _listdirs(self, file):
        zf = zipfile.ZipFile(file)
        dirs = []
        for name in zf.namelist():
            if name.endswith('/'):
                dirs.append(name)

        dirs.sort()
        return dirs
