#   script.limpiarkodi
#   Copyright (C) 2016  Teco
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.



import xbmc, xbmcaddon, xbmcgui, xbmcplugin, os, sys, xbmcvfs, glob
import shutil
import urllib2,urllib
import re
import os


thumbnailPath = xbmc.translatePath('special://thumbnails');
cachePath = os.path.join(xbmc.translatePath('special://home'), 'cache')
tempPath = xbmc.translatePath('special://home/temp')
torrentsdir = xbmc.translatePath(os.path.join('special://cache'))
tempPath = xbmc.translatePath('special://kodi/temp')
addonPath = os.path.join(os.path.join(xbmc.translatePath('special://home'), 'addons'),'script.limpiarkodi')

mediaPath = os.path.join(addonPath, 'media')
databasePath = xbmc.translatePath('special://database')
THUMBS    =  xbmc.translatePath(os.path.join('special://home/userdata/Thumbnails',''))

addon_id = 'script.limpiarkodi'
fanart = xbmc.translatePath(os.path.join('special://home/addons/' + addon_id , 'fanart.jpg'))
iconpath = xbmc.translatePath(os.path.join('special://home/addons/' + addon_id, 'icon.png'))
class cacheEntry:
    def __init__(self, namei, pathi):
        self.name = namei
        self.path = pathi

def setupCacheEntries():
    entries = 19 #make sure this refelcts the amount of entries you have
    dialogName = [" YouTube", " UrlResolve", " Simple Cacher", " Simple Downloader", " Metadatautils", " Streamlink", " Tvalacarta", " Resolveurl", " Alfa Downloads", " Metahandler", " Youtube.dl", " Extendedinfo", " TheMovieDB", " Extendedinfo/YouTube", " Autocompletion/Google", " Autocompletion/Bing", " Universalscrapers", " Torrents Alfa", " Clouddrive Common"]
    pathName = ["special://profile/addon_data/plugin.video.youtube/kodion", "special://profile/addon_data/script.module.urlresolve/cache",
                    "special://profile/addon_data/script.module.simplecache", "special://profile/addon_data/script.module.simple.downloader",
                    "special://profile/addon_data/script.module.metadatautils/animatedgifs", "special://profile/addon_data/script.module.streamlink/base","special://profile/addon_data/plugin.video.tvalacarta/downloads", "special://profile/addon_data/script.module.resolveurl/cache", "special://profile/addon_data/plugin.video.alfa/downloads", "special://profile/addon_data/script.module.metahandler/meta_cache", "special://profile/addon_data/script.module.youtube.dl/tmp", "special://profile/addon_data/script.extendedinfo/images", "special://profile/addon_data/script.extendedinfo/TheMovieDB", "special://profile/addon_data/script.extendedinfo/YouTube", "special://profile/addon_data/plugin.program.autocompletion/Google", "special://profile/addon_data/plugin.program.autocompletion/Bing", "special://profile/addon_data/script.module.universalscrapers", "special://profile/addon_data/plugin.video.alfa/videolibrary/temp_torrents_Alfa", "special://profile/addon_data/script.module.clouddrive.common",]
                    
    cacheEntries = []
    
    for x in range(entries):
        cacheEntries.append(cacheEntry(dialogName[x],pathName[x]))
    
    return cacheEntries


def clearCache():

    if os.path.exists(cachePath)==True:    
        for root, dirs, files in os.walk(cachePath):
            file_count = 0
            file_count += len(files)
            if file_count > 0:

                    for f in files:
                        try:
                            if (f == "kodi.log" or f == "kodi.old.log"): continue
                            os.unlink(os.path.join(root, f))
                        except:
                            pass
                    for d in dirs:
                        try:
                            shutil.rmtree(os.path.join(root, d))
                        except:
                            pass
                        
            else:
                pass
    if os.path.exists(tempPath)==True:    
        for root, dirs, files in os.walk(tempPath):
            file_count = 0
            file_count += len(files)
            if file_count > 0:

                    for f in files:
                        try:
                            if (f == "kodi.log" or f == "kodi.old.log"): continue
                            os.unlink(os.path.join(root, f))
                        except:
                            pass
                    for d in dirs:
                        try:
                            shutil.rmtree(os.path.join(root, d))
                        except:
                            pass
                        
            else:
                pass
    if xbmc.getCondVisibility('system.platform.ATV2'):
        atv2_cache_a = os.path.join('/private/var/mobile/Library/Caches/AppleTV/Video/', 'Other')
        
        for root, dirs, files in os.walk(atv2_cache_a):
            file_count = 0
            file_count += len(files)
        
            if file_count > 0:


                    for f in files:
                        os.unlink(os.path.join(root, f))
                    for d in dirs:
                        shutil.rmtree(os.path.join(root, d))
                        
            else:
                pass
        atv2_cache_b = os.path.join('/private/var/mobile/Library/Caches/AppleTV/Video/', 'LocalAndRental')
        
        for root, dirs, files in os.walk(atv2_cache_b):
            file_count = 0
            file_count += len(files)
        
            if file_count > 0:


                    for f in files:
                        os.unlink(os.path.join(root, f))
                    for d in dirs:
                        shutil.rmtree(os.path.join(root, d))
                        
            else:
                pass    
                
    cacheEntries = setupCacheEntries()
                                         
    for entry in cacheEntries:
        clear_cache_path = xbmc.translatePath(entry.path)
        if os.path.exists(clear_cache_path)==True:    
            for root, dirs, files in os.walk(clear_cache_path):
                file_count = 0
                file_count += len(files)
                if file_count > 0:


                        for f in files:
                            os.unlink(os.path.join(root, f))
                        for d in dirs:
                            shutil.rmtree(os.path.join(root, d))
                            
                else:
                    pass


    xbmc.executebuiltin('XBMC.Notification(%s, %s, %s, %s)' % ('Limpia tu Kodi' , 'Auto Limpieza Completada' , '3000', iconpath))   

def Cacherom():

    if os.path.exists(cachePath)==True:    
        for root, dirs, files in os.walk(cachePath):
            file_count = 0
            file_count += len(files)
            if file_count > 0:

                    for f in files:
                        try:
                            if (f == "kodi.log" or f == "kodi.old.log"): continue
                            os.unlink(os.path.join(root, f))
                        except:
                            pass
                    for d in dirs:
                        try:
                            shutil.rmtree(os.path.join(root, d))
                        except:
                            pass
                        
            else:
                pass
    if os.path.exists(tempPath)==True:    
        for root, dirs, files in os.walk(tempPath):
            file_count = 0
            file_count += len(files)
            if file_count > 0:

                    for f in files:
                        try:
                            if (f == "kodi.log" or f == "kodi.old.log"): continue
                            os.unlink(os.path.join(root, f))
                        except:
                            pass
                    for d in dirs:
                        try:
                            shutil.rmtree(os.path.join(root, d))
                        except:
                            pass
                        
            else:
                pass
    if xbmc.getCondVisibility('system.platform.ATV2'):
        atv2_cache_a = os.path.join('/private/var/mobile/Library/Caches/AppleTV/Video/', 'Other')
        
        for root, dirs, files in os.walk(atv2_cache_a):
            file_count = 0
            file_count += len(files)
        
            if file_count > 0:


                    for f in files:
                        os.unlink(os.path.join(root, f))
                    for d in dirs:
                        shutil.rmtree(os.path.join(root, d))
                        
            else:
                pass
        atv2_cache_b = os.path.join('/private/var/mobile/Library/Caches/AppleTV/Video/', 'LocalAndRental')
        
        for root, dirs, files in os.walk(atv2_cache_b):
            file_count = 0
            file_count += len(files)
        
            if file_count > 0:


                    for f in files:
                        os.unlink(os.path.join(root, f))
                    for d in dirs:
                        shutil.rmtree(os.path.join(root, d))
                        
            else:
                pass    
                
    cacheEntries = setupCacheEntries()

    for entry in cacheEntries:
        clear_cache_path = xbmc.translatePath(entry.path)
        if os.path.exists(clear_cache_path)==True:    
            for root, dirs, files in os.walk(clear_cache_path):
                file_count = 0
                file_count += len(files)
                if file_count > 0:


                        for f in files:
                            os.unlink(os.path.join(root, f))
                        for d in dirs:
                            shutil.rmtree(os.path.join(root, d))
                            
                else:
                    pass
                


    xbmc.executebuiltin('XBMC.Notification(%s, %s, %s, %s)' % ('Limpia tu Kodi' , 'Auto Limpieza Completada' , '3000', iconpath))    

def deleteThumbnails():

    if os.path.exists(thumbnailPath)==True:  
            dialog = xbmcgui.Dialog()
            if dialog.yesno("Borrar Imagenes", "Esta Opcion Borra las Imagenes", "Desea Eliminarlas?"):
                for root, dirs, files in os.walk(thumbnailPath):
                    file_count = 0
                    file_count += len(files)
                    if file_count > 0:                
                        for f in files:
                            try:
                                os.unlink(os.path.join(root, f))
                            except:
                                pass                


    if os.path.exists(THUMBS):
        try:    
            for root, dirs, files in os.walk(THUMBS):
                file_count = 0
                file_count += len(files)
                # Count files and give option to delete
                if file_count > 0:
                        for f in files:    os.unlink(os.path.join(root, f))
                        for d in dirs: shutil.rmtree(os.path.join(root, d))
        except:
            pass
            
    try:
        text13 = os.path.join(databasePath,"Textures13.db")
        os.unlink(text13)
    except:
        pass
    dialog.ok("[COLOR=red]Atencion[/COLOR]", "Debe Reiniciar Kodi Para Aplicar los Cambios")

def purgePackages():

    purgePath = xbmc.translatePath('special://home/addons/packages')
    dialog = xbmcgui.Dialog()
    for root, dirs, files in os.walk(purgePath):
            file_count = 0
            file_count += len(files)
    if dialog.yesno("Borrar contenido Package", "%d Packages Encontrados."%file_count, "Desea Eliminarlo?"):  
        for root, dirs, files in os.walk(purgePath):
            file_count = 0
            file_count += len(files)
            if file_count > 0:
                for f in files:
                    os.unlink(os.path.join(root, f))
                for d in dirs:
                    shutil.rmtree(os.path.join(root, d))
                dialog = xbmcgui.Dialog()
                dialog.ok("Limpia tu Kodi", "Borrar todo el contenido de Packages")
            else:
                dialog = xbmcgui.Dialog()
                dialog.ok("Limpia tu Kodi", "Eliminados Packages")

def purgeCacheRom():

    tempPath = xbmc.translatePath('special://home/addons/temp/')
    dialog = xbmcgui.Dialog()
    for root, dirs, files in os.walk(tempPath):
            file_count = 0
            file_count += len(files)
    if dialog.yesno("Borrar Temp de Kodi", "%d Archivos en Temp Encontrados."%file_count, "Desea Borrar Esto?"):  
        for root, dirs, files in os.walk(tempPath):
            file_count = 0
            file_count += len(files)
            if file_count > 0:
                for f in files:
                    os.unlink(os.path.join(root, f))
                for d in dirs:
                    shutil.rmtree(os.path.join(root, d))
                dialog = xbmcgui.Dialog()
                dialog.ok("Limpia tu Kodi", "Borrar todos los Archivos en Temp")
            else:
                dialog = xbmcgui.Dialog()
                dialog.ok("Limpia tu Kodi", "Eliminados Archivos en Temp")

def purgeTorrents():

    torrentsPath = xbmc.translatePath('special://home/cache/')
    dialog = xbmcgui.Dialog()
    for root, dirs, files in os.walk(torrentsPath):
            file_count = 0
            file_count += len(files)
    if dialog.yesno("Borrar contenido Torrent", "%d Torrents Encontrados."%file_count, "Desea Eliminarlo?"):  
        for root, dirs, files in os.walk(torrentsPath):
            file_count = 0
            file_count += len(files)
            if file_count > 0:
                for f in files:
                    os.unlink(os.path.join(root, f))
                for d in dirs:
                    shutil.rmtree(os.path.join(root, d))
                dialog = xbmcgui.Dialog()
                dialog.ok("Limpia tu Kodi", "Borrar todo el contenido de Torrents")
            else:
                dialog = xbmcgui.Dialog()
                dialog.ok("Limpia tu Kodi", "Eliminados Torrents")