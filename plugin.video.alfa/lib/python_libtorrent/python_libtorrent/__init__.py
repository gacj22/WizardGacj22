#-*- coding: utf-8 -*-
'''
    python-libtorrent for Kodi (script.module.libtorrent)
    Copyright (C) 2015-2016 DiMartino, srg70, RussakHH, aisman

    Permission is hereby granted, free of charge, to any person obtaining
    a copy of this software and associated documentation files (the
    "Software"), to deal in the Software without restriction, including
    without limitation the rights to use, copy, modify, merge, publish,
    distribute, sublicense, and/or sell copies of the Software, and to
    permit persons to whom the Software is furnished to do so, subject to
    the following conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
    LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
    OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
    WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

from functions import *
import xbmc, xbmcaddon
import sys
import os
import traceback                                                                ### Alfa

#__settings__ = xbmcaddon.Addon(id='script.module.libtorrent')                  ### Alfa
#__version__ = __settings__.getAddonInfo('version')                             ### Alfa
#__plugin__ = __settings__.getAddonInfo('name') + " v." + __version__           ### Alfa
#__settings__ = xbmcaddon.Addon(id='plugin.video.alfa')                         ### Alfa
__version__ = '1.1.17'                                                          ### Alfa
__plugin__ = "python-libtorrent v.1.1.7"                                        ### Alfa
#__language__ = __settings__.getLocalizedString                                 ### Alfa
__root__ = os.path.dirname(os.path.dirname(__file__))

libtorrent=None
platform = get_platform()
#set_dirname=__settings__.getSetting('dirname')                                 ### Alfa
#set_dirname=os.path.join(__settings__.getAddonInfo('Path'),'lib', 'python_libtorrent')  ### Alfa
set_dirname=__root__                                                            ### Alfa
if getSettingAsBool('custom_dirname') and set_dirname:
    log('set_dirname:' +str(set_dirname))
    dirname=set_dirname
else:
    #dirname = os.path.join(xbmc.translatePath('special://temp'), 'xbmcup', 'script.module.libtorrent',
    #                       'python_libtorrent')
    dirname=set_dirname                                                         ### Alfa

log('dirname: ' +str(dirname))

versions = ['0.16.19', '1.0.6', '1.0.7', '1.0.8', '1.0.9', '1.0.11', '1.1.0', '1.1.1', '1.1.6', '1.1.7', '1.2.1']       ### Alfa
default_path = versions[-1]
#set_version = int(__settings__.getSetting('set_version'))                      ### Alfa
set_version = 0                                                                 ### Alfa
if getSettingAsBool('custom_version'):
    log('set_version:' +str(set_version)+' '+versions[set_version])
    platform['version'] = versions[set_version]
else:
    platform['version'] = default_path

sizefile_path = os.path.join(__root__, platform['system'], platform['version'])
if not os.path.exists(sizefile_path):
    log('set_version: no sizefile at %s back to default %s' % (sizefile_path, default_path))
    platform['version'] = default_path
    sizefile_path = os.path.join(__root__, platform['system'], platform['version'])
    if not os.path.exists(sizefile_path):
        log('set_version: no default at %s searching for any version' % sizefile_path)
        try:
            versions = sorted(os.listdir(os.path.join(__root__, platform['system'])))
        except:
            versions = []
        for ver in versions:
            if not os.path.isdir(os.path.join(__root__, platform['system'], ver)):
                versions.remove(ver)

        if len(versions)>0:
            platform['version'] = versions[-1]
            log('set_version: chose %s out of %s' % (platform['version'], str(versions)))
        else:
            e = 'die because the folder is empty'
            log(e)
            raise Exception(e)
dest_path = os.path.join(dirname, platform['system'], platform['version'])
sys.path.insert(0, dest_path)

lm=LibraryManager(dest_path, platform)
if not lm.check_exist():
    ok=lm.download()
    xbmc.sleep(2000)


#if __settings__.getSetting('plugin_name')!=__plugin__:                         ### Alfa
#    __settings__.setSetting('plugin_name', __plugin__)                         ### Alfa
#    lm.update()                                                                ### Alfa

log('platform: ' + str(platform))
if platform['system'] not in ['windows', 'windows_x64']:                        ### Alfa
    log('os: '+str(os.uname()))
    log_text = 'ucs4' if sys.maxunicode > 65536 else 'ucs2'
    log_text += ' x64' if sys.maxint > 2147483647 else ' x86'
    log(log_text)

try:
    fp = ''
    pathname = ''
    description = ''
    libtorrent = ''
    from platformcode import config
    if platform['system'] in ['linux_x86', 'windows', 'windows_x64', 'linux_armv6', 'linux_armv7',
                              'linux_x86_64', 'linux_mipsel_ucs2', 'linux_mipsel_ucs4',
                              'linux_aarch64_ucs2', 'linux_aarch64_ucs4']:      ### Alfa
        import libtorrent
    
    elif platform['system'] in ['darwin', 'ios_arm']:
        import imp
        path_list = [dest_path]
        log('path_list = ' + str(path_list))
        fp, pathname, description = imp.find_module('libtorrent', path_list)
        log('fp = ' + str(fp))
        log('pathname = ' + str(pathname))
        log('description = ' + str(description))
        try:
            libtorrent = imp.load_module('libtorrent', fp, pathname, description)
        finally:
            if fp: fp.close()
    
    elif platform['system'] in ['android_armv7', 'android_x86']:
        import imp
        from ctypes import CDLL
        try:
            dest_path=lm.android_workaround(os.path.join(xbmc.translatePath('special://xbmc/'), 'files').replace('/cache/apk/assets', ''))
            dll_path=os.path.join(dest_path, 'liblibtorrent.so')
            log('CDLL path = ' + dll_path)
            liblibtorrent=CDLL(dll_path)
            log('CDLL = ' + str(liblibtorrent))
            path_list = [dest_path]
            log('path_list = ' + str(path_list))
            fp, pathname, description = imp.find_module('libtorrent', path_list)
            #if fp: fp.close()
            #from core import filetools
            #fp = filetools.file_open(pathname, 'rb')                                # Alfa: Usa XbmcVFS
            #fp = open(pathname, 'rt')
            log('fp = ' + str(fp))
            log('pathname = ' + str(pathname))
            log('description = ' + str(description))
            try:
                libtorrent = imp.load_module('libtorrent', fp, pathname, description)
            finally:
                if fp: fp.close()
        except Exception, e:
            e = unicode(str(e), "utf8", errors="replace").encode("utf8")
            config.set_setting("libtorrent_path", "", server="torrent")         ### Alfa
            config.set_setting("libtorrent_error", str(e), server="torrent")    ### Alfa
            log(traceback.format_exc(1))
            log('fp = ' + str(fp))
            log('pathname = ' + str(pathname))
            log('description = ' + str(description))
            log('Error importing libtorrent from "' + dest_path + '". Exception: ' + str(e))
            if fp: fp.close()

            # If no permission in dest_path we need to go deeper on root!
            try:                                                                ### Alfa START
                sys_path = '/data/app/'
                fp = ''
                pathname = sys_path
                dest_path = sys_path
                description = ''
                libtorrent = ''
                LIBTORRENT_MSG = config.get_setting("libtorrent_msg", server="torrent", default='')
                if not LIBTORRENT_MSG:
                    dialog = xbmcgui.Dialog()
                    dialog.notification('ALFA: Instalando Cliente Torrent interno', \
                                'Puede solicitarle permisos de Superusuario', time=15000)
                    log('### ALFA: Notificación enviada: Instalando Cliente Torrent interno')
                    config.set_setting("libtorrent_msg", 'OK', server="torrent")
                
                from core import scrapertools
                kodi_app = xbmc.translatePath('special://xbmc')
                kodi_app = scrapertools.find_single_match(kodi_app, '\/\w+\/\w+\/.*?\/(.*?)\/')
                kodi_dir = '%s-1' % kodi_app
                dir_list = ''
                try:
                    dir_list = os.listdir(sys_path).split()
                except:
                    import subprocess
                    command = ['su', '-c', 'ls', sys_path]
                    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    output_cmd, error_cmd = p.communicate()
                    log('Comando ROOT: %s' % str(command))
                    dir_list = output_cmd.split()
                
                if not dir_list:
                    raise
                
                for file in dir_list:
                    if kodi_app in file:
                        kodi_dir = file
                        break

                bits = sys.maxsize > 2 ** 32 and "64" or ""
                dest_path = os.path.join(sys_path, kodi_dir, 'lib', platform['arch'] + bits)
                dest_path=lm.android_workaround(new_dest_path=dest_path)
                dll_path=os.path.join(dest_path, 'liblibtorrent.so')
                log('NEW CDLL path = ' + dll_path)
                liblibtorrent=CDLL(dll_path)
                log('CDLL = ' + str(liblibtorrent))
                path_list = [dest_path]
                log('path_list = ' + str(path_list))
                fp, pathname, description = imp.find_module('libtorrent', path_list)
                try:
                    libtorrent = imp.load_module('libtorrent', fp, pathname, description)
                finally:
                    if fp: fp.close()
                
            except Exception, e:
                log('ERROR Comando ROOT: %s, %s' % (str(command), str(dest_path)))
                e = unicode(str(e), "utf8", errors="replace").encode("utf8")
                log(traceback.format_exc(1))                                    ### Alfa
                log('fp = ' + str(fp))
                log('pathname = ' + str(pathname))
                log('description = ' + str(description))
                log('Error importing libtorrent from "' + dest_path + '". Exception: ' + str(e))
                if fp: fp.close()

    if libtorrent:
        config.set_setting("libtorrent_path", dest_path, server="torrent")      ### Alfa
        config.set_setting("libtorrent_error", "", server="torrent")            ### Alfa
        log('Imported libtorrent v' + libtorrent.version + ' from "' + dest_path + '"')

except Exception, e:
    e = unicode(str(e), "utf8", errors="replace").encode("utf8")
    config.set_setting("libtorrent_path", "", server="torrent")                 ### Alfa
    config.set_setting("libtorrent_error", str(e), server="torrent")            ### Alfa
    log('Error importing libtorrent from "' + dest_path + '". Exception: ' + str(e))
    if fp: fp.close()


def get_libtorrent():
    return libtorrent
