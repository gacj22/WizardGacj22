# encoding=utf8
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import xbmc
import os
import sys
import urlparse
from sqlite3 import dbapi2 as database

args = urlparse.parse_qs(sys.argv[1][1:])
cache_location = os.path.join(xbmc.translatePath("special://database"), 'noise_db.db')
dbcon = database.connect(cache_location)
dbcur = dbcon.cursor()

lang_is = 0; # 0: English, 1: Spanish

if 'Spanish' in xbmc.getLanguage():
    lang_is = 1

LANG = {
	'Album added to My Albums successfully': 'Album añadido a Mis Albums correctamente',
	'Hey!' : 'Oye!',
	'This album is already in My Albums' : 'Este album ya está guardado en Mis Álbumes',
    'Deleted' : 'Borrado',
    'The album has been deleted from My Albums' : 'Se ha borrado el album de Mis Álbumes'
}

def str_by_lang(str_in):
    if lang_is == 0:
        return str_in
    else:
        if str_in in LANG:
            return LANG[str_in]
        else:
            return str_in

dbcur.execute("CREATE TABLE IF NOT EXISTS my_albums (album_type TEXT, id TEXT, title TEXT, image TEXT, UNIQUE(album_type, id));")

if args['mode'][0] == 'save':
	dbcur.execute("SELECT * FROM my_albums WHERE album_type = '" + args['album_type'][0] + "' AND id = '" + args['id'][0] + "'")
	match = dbcur.fetchone()
	if match == None:
		if 'image' in args:
			image = args['image'][0]
			msg_image = args['image'][0]
		else:
			image = '';
			msg_image = 'special://home/addons/plugin.video.noise/icon.png'
		dbcur.execute('INSERT INTO my_albums VALUES ("' + args['album_type'][0] + '","' + args['id'][0] + '","' + args['title'][0].replace('"', '[*DQ*]') + '","' + image + '")')
		dbcon.commit()
		xbmc.executebuiltin('XBMC.Notification(%s, %s, %s, %s)' % (args['title'][0], str_by_lang('Album added to My Albums successfully'), 4000, msg_image))
	else:
		xbmc.executebuiltin('XBMC.Notification(%s, %s, %s, %s)' % (str_by_lang('Hey!'), str_by_lang('This album is already in My Albums'), 4000, 'special://home/addons/plugin.video.noise/icon.png'))

if args['mode'][0] == 'delete':
	dbcur.execute("DELETE FROM my_albums WHERE album_type = '" + args['album_type'][0] + "' AND id = '" + args['id'][0] + "'")
	dbcon.commit()
	xbmc.executebuiltin("Container.Refresh")
	xbmc.executebuiltin('XBMC.Notification(%s, %s, %s, %s)' % (str_by_lang('Deleted'), str_by_lang('The album has been deleted from My Albums'), 4000, 'special://home/addons/plugin.video.noise/icon.png'))