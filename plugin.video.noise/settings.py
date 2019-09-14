import xbmc, xbmcaddon, xbmcgui, xbmcplugin
import os

my_addon = xbmcaddon.Addon()
PATH = my_addon.getAddonInfo('path')

ADDON = xbmcaddon.Addon(id='plugin.video.noise')

def create_directory(dir_path, dir_name=None):
    
    if dir_name:
        dir_path = os.path.join(dir_path, dir_name)
    
    dir_path = dir_path.strip()
    
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    if os.path.isfile(os.path.join(xbmc.translatePath("special://database"), 'noise_db.db')):
        fr = open(os.path.join(xbmc.translatePath("special://database"), 'noise_db.db'), 'r')
        load_file = fr.read()
        fr.close()
        fw = open(os.path.join(dir_path, 'noise_db.db'), "w")
        fw.write(load_file)
        fw.close()
        os.remove(os.path.join(xbmc.translatePath("special://database"), 'noise_db.db'))
        f = open(PATH+'/resources/LAST_DB_PATH.info', "w")
        f.write(os.path.join(dir_path, 'noise_db.db'))
        f.close()
    else:
        if ADDON.getSetting('db_dir') != "":
            if os.path.isfile(os.path.join(ADDON.getSetting('db_dir') + 'noise_db', 'noise_db.db')) != True:
                if os.path.isfile(PATH+'/resources/LAST_DB_PATH.info'):
                    fr = open(PATH+'/resources/LAST_DB_PATH.info', 'r')
                    load_file = fr.read()
                    fr.close()

                    fr2 = open(load_file)
                    loaded_file = fr2.read()
                    fr2.close()

                    fw = open(os.path.join(dir_path, 'noise_db.db'), "w")
                    fw.write(loaded_file)
                    fw.close()

                    os.remove(load_file)

                    f = open(PATH+'/resources/LAST_DB_PATH.info', "w")
                    f.write(os.path.join(dir_path, 'noise_db.db'))
                    f.close()
    
    return os.path.join(dir_path, 'noise_db.db')

def get_db_dir():
    if ADDON.getSetting('db_dir') == "":
        return os.path.join(xbmc.translatePath("special://database"), 'noise_db.db')
    else:
        return create_directory(ADDON.getSetting('db_dir'), "noise_db")