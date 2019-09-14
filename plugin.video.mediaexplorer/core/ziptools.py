# -*- coding: utf-8 -*-
import stat
import struct
import zipfile
import zlib

from core.libs import *


class _ZipEncrypter(zipfile._ZipDecrypter):
    def __call__(self, c):
        """Encrypt a single character."""
        _c = ord(c)
        k = self.key2 | 2
        _c = _c ^ (((k * (k ^ 1)) >> 8) & 255)
        _c = chr(_c)
        self._UpdateKeys(c)  # this is the only line that actually changed
        return _c


class ZipFile(zipfile.ZipFile):
    def write(self, filename, arcname=None, compress_type=None, pwd=None):
        """Put the bytes from filename into the archive under the name
        arcname."""
        if not self.fp:
            raise RuntimeError(
                "Attempt to write to ZIP archive that was already closed")

        st = os.stat(filename)
        isdir = stat.S_ISDIR(st.st_mode)
        mtime = time.localtime(st.st_mtime)
        date_time = mtime[0:6]
        # Create ZipInfo instance to store file information
        if arcname is None:
            arcname = filename
        arcname = os.path.normpath(os.path.splitdrive(arcname)[1])
        while arcname[0] in (os.sep, os.altsep):
            arcname = arcname[1:]
        if isdir:
            arcname += '/'
        zinfo = zipfile.ZipInfo(arcname, date_time)
        zinfo.external_attr = (st[0] & 0xFFFF) << 16L  # Unix attributes
        if isdir:
            zinfo.compress_type = zipfile.ZIP_STORED
        elif compress_type is None:
            zinfo.compress_type = self.compression
        else:
            zinfo.compress_type = compress_type

        zinfo.file_size = st.st_size
        zinfo.flag_bits = 0x00
        zinfo.header_offset = self.fp.tell()  # Start of header bytes

        self._writecheck(zinfo)
        self._didModify = True

        if isdir:
            zinfo.file_size = 0
            zinfo.compress_size = 0
            zinfo.CRC = 0
            zinfo.external_attr |= 0x10  # MS-DOS directory flag
            self.filelist.append(zinfo)
            self.NameToInfo[zinfo.filename] = zinfo
            self.fp.write(zinfo.FileHeader(False))
            return

        pwd = pwd or self.pwd
        if pwd:
            zinfo.flag_bits |= 0x8 | 0x1  # set stream and encrypted

        with open(filename, "rb") as fp:
            # Must overwrite CRC and sizes with correct data later
            zinfo.CRC = crc = 0
            zinfo.compress_size = compress_size = 0
            # Compressed size can be larger than uncompressed size
            zip64 = self._allowZip64 and zinfo.file_size * 1.05 > zipfile.ZIP64_LIMIT
            self.fp.write(zinfo.FileHeader(zip64))
            if zinfo.compress_type == zipfile.ZIP_DEFLATED:
                cmpr = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION,
                                        zlib.DEFLATED, -15)
            else:
                cmpr = None
            if pwd:
                ze = _ZipEncrypter(pwd)
                encrypt = lambda x: "".join(map(ze, x))
                zinfo._raw_time = (
                        zinfo.date_time[3] << 11
                        | zinfo.date_time[4] << 5
                        | (zinfo.date_time[5] // 2))
                check_byte = (zinfo._raw_time >> 8) & 0xff
                enryption_header = os.urandom(11) + chr(check_byte)
                self.fp.write(encrypt(enryption_header))
            else:
                encrypt = lambda x: x
            file_size = 0
            while 1:
                buf = fp.read(1024 * 8)
                if not buf:
                    break
                file_size = file_size + len(buf)
                crc = zipfile.crc32(buf, crc) & 0xffffffff
                if cmpr:
                    buf = cmpr.compress(buf)
                    compress_size = compress_size + len(buf)
                self.fp.write(encrypt(buf))
        if cmpr:
            buf = cmpr.flush()
            compress_size = compress_size + len(buf)
            self.fp.write(encrypt(buf))
            zinfo.compress_size = compress_size
        else:
            zinfo.compress_size = file_size
        zinfo.CRC = crc
        zinfo.file_size = file_size
        if not zip64 and self._allowZip64:
            if file_size > zipfile.ZIP64_LIMIT:
                raise RuntimeError(
                    'File size has increased during compressing')
            if compress_size > zipfile.ZIP64_LIMIT:
                raise RuntimeError(
                    'Compressed size larger than uncompressed size')
        if pwd:
            # Write CRC and file sizes after the file data
            zinfo.compress_size += 12
            fmt = '<LQQ' if zip64 else '<LLL'
            self.fp.write(struct.pack(
                fmt, zinfo.CRC, zinfo.compress_size, zinfo.file_size))
            self.fp.flush()
        else:
            # Seek backwards and write file header (which will now include
            # correct CRC and file sizes)
            position = self.fp.tell()  # Preserve current position in file
            self.fp.seek(zinfo.header_offset, 0)
            self.fp.write(zinfo.FileHeader(zip64))
            self.fp.seek(position, 0)
        self.filelist.append(zinfo)
        self.NameToInfo[zinfo.filename] = zinfo

    def writestr(self, zinfo_or_arcname, _bytes, compress_type=None, pwd=None):
        """Write a file into the archive.  The contents is the string
        'bytes'.  'zinfo_or_arcname' is either a ZipInfo instance or
        the name of the file in the archive."""
        if not isinstance(zinfo_or_arcname, zipfile.ZipInfo):
            zinfo = zipfile.ZipInfo(filename=zinfo_or_arcname,
                                    date_time=time.localtime(time.time())[:6])

            zinfo.compress_type = self.compression
            if zinfo.filename[-1] == '/':
                zinfo.external_attr = 0o40775 << 16  # drwxrwxr-x
                zinfo.external_attr |= 0x10  # MS-DOS directory flag
            else:
                zinfo.external_attr = 0o600 << 16  # ?rw-------
        else:
            zinfo = zinfo_or_arcname

        if not self.fp:
            raise RuntimeError(
                "Attempt to write to ZIP archive that was already closed")

        if compress_type is not None:
            zinfo.compress_type = compress_type

        zinfo.file_size = len(_bytes)  # Uncompressed size
        zinfo.header_offset = self.fp.tell()  # Start of header bytes
        self._writecheck(zinfo)
        self._didModify = True
        zinfo.CRC = zipfile.crc32(_bytes) & 0xffffffff  # CRC-32 checksum
        if zinfo.compress_type == zipfile.ZIP_DEFLATED:
            co = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION,
                                  zlib.DEFLATED, -15)
            _bytes = co.compress(_bytes) + co.flush()
            zinfo.compress_size = len(_bytes)  # Compressed size
        else:
            zinfo.compress_size = zinfo.file_size
        zip64 = zinfo.file_size > zipfile.ZIP64_LIMIT or zinfo.compress_size > zipfile.ZIP64_LIMIT
        if zip64 and not self._allowZip64:
            raise zipfile.LargeZipFile("Filesize would require ZIP64 extensions")

        pwd = pwd or self.pwd
        if pwd:
            zinfo.flag_bits |= 0x01
            zinfo.compress_size += 12  # 12 extra bytes for the header
            if zinfo.flag_bits & 0x8:
                zinfo._raw_time = (
                        zinfo.date_time[3] << 11
                        | zinfo.date_time[4] << 5
                        | (zinfo.date_time[5] // 2))
                check_byte = (zinfo._raw_time >> 8) & 0xff
            else:
                check_byte = (zinfo.CRC >> 24) & 0xff
            enryption_header = os.urandom(11) + chr(check_byte)
            ze = _ZipEncrypter(pwd)
            _bytes = "".join(map(ze, enryption_header + _bytes))

        self.fp.write(zinfo.FileHeader(zip64))
        self.fp.write(_bytes)
        if zinfo.flag_bits & 0x08:
            # Write CRC and file sizes after the file data
            fmt = '<LQQ' if zip64 else '<LLL'
            self.fp.write(struct.pack(fmt, zinfo.CRC, zinfo.compress_size,
                                      zinfo.file_size))
        self.fp.flush()
        self.filelist.append(zinfo)
        self.NameToInfo[zinfo.filename] = zinfo

    def open(self, name, mode="r", pwd=None):
        try:
            return zipfile.ZipFile.open(self, name, mode, pwd)
        except RuntimeError, e:
            if 'password required' in e.message:
                password = platformtools.dialog_input('', 'Introduzca la contraseña para el archivo', hidden=True)
            elif '' in e.message:
                password = platformtools.dialog_input(self.pwd, 'La contraseña no es correcta', hidden=True)
            else:
                raise
            if not password:
                raise
            else:
                self.setpassword(password)
                return self.open(name, mode, pwd)


def extract(fname, dest, overwrite=False, silent=False, password=None):
    logger.trace()
    import shutil
    created_dest = canceled = False
    zf = ZipFile(fname)
    if password:
        zf.setpassword(password)

    if not os.path.isdir(dest):
        os.makedirs(dest)
        created_dest = True

    if silent:
        # Descomprimimos en modo silencioso (mas rapido)
        zf.extractall(dest)
    else:
        # Descomprimimos mostrando el cuadro de progreso y permitiendo cancelar
        dialog = platformtools.dialog_progress('Extrayendo', '')
        uncompress_size = sum((f.file_size for f in zf.infolist()))
        extracted_size = num_files = count = 0

        # Crear destino temporal
        dest_tmp = dest + "_TMP"
        if not os.path.isdir(dest_tmp):
            os.makedirs(dest_tmp)

        for f in zf.infolist():
            extracted_size += f.file_size
            porcent = extracted_size * 100 / uncompress_size
            num_files += 1
            dialog.update(porcent,
                          "Descomprimiendo:",
                          ".../%s" % f.filename[-60:].split('/', 1)[1] if len(f.filename) > 60 else f.filename,
                          "Fichero %s de %s (%s%%)" % (num_files, len(zf.infolist()), porcent))

            if dialog.iscanceled():
                canceled = True
                break
            zf.extract(f, dest_tmp)

        if not canceled:
            list_remove = []
            # Mover desde la carpeta temporal a la carpeta destino
            for root, dirs, files in os.walk(dest_tmp):
                if overwrite and root == dest_tmp:
                    for d in dirs:
                        d = os.path.join(dest, d)
                        if os.path.isdir(d):
                            os.rename(d, d + "_bak")
                            list_remove.append(d + "_bak")

                    for f in files:
                        f = os.path.join(dest, f)
                        if os.path.isfile(f):
                            os.rename(f, f + '.bak')
                            list_remove.append(f + '.bak')

                for filename in files:
                    filepath_src = os.path.join(root, filename)
                    filepath_dest = filepath_src.replace(dest_tmp, dest, 1)
                    dirname_dest = os.path.dirname(filepath_dest)
                    if not os.path.isdir(dirname_dest):
                        os.makedirs(dirname_dest)
                    count += 1
                    porcent = count * 100 / num_files
                    dialog.update(porcent,
                                  "Moviendo:",
                                  ".../%s" % filepath_dest[-60:].split(os.sep, 1)[1] if len(
                                      filepath_dest) > 60 else filepath_dest,
                                  "Fichero %s de %s (%s%%)" % (count, num_files, porcent))
                    shutil.move(filepath_src, filepath_dest)

                for i in list_remove:
                    if os.path.isdir(i):
                        shutil.rmtree(i, ignore_errors=True)
                    elif os.path.isfile(i):
                        os.remove(i)

        elif created_dest:
            os.rmdir(dest)

        shutil.rmtree(dest_tmp, ignore_errors=True)
        dialog.close()

    zf.close()

    return not canceled


def create_zip(fname, filelist, overwrite=False, silent=False, password=None):
    if os.path.isfile(fname) and not overwrite:
        return
    elif os.path.isfile(fname):
        os.remove(fname)

    if not silent:
        dialog = platformtools.dialog_progress('Comprimiendo', fname)
    else:
        dialog = None

    zf = ZipFile(fname, 'w', zipfile.ZIP_DEFLATED)
    if password:
        zf.setpassword(password)
    for element in filelist:
        if not silent:
            dialog.update(filelist.index(element) * 100 / len(filelist), element[0])
        if os.path.isfile(element[1]):
            zf.write(element[1], element[0])
        elif os.path.isdir(element[1]):
            if not element[0].endswith(os.path.sep):
                element[0] += os.path.sep
            zf.writestr(zipfile.ZipInfo(element[0]), "")
        else:
            zf.writestr(element[0], element[1])
    if not silent:
        dialog.close()
    zf.close()
