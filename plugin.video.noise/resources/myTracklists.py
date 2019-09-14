# encoding=utf8
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import xbmc
import os
import sys
import urlparse
import base64
from sqlite3 import dbapi2 as database
from datetime import datetime, timedelta

args = urlparse.parse_qs(sys.argv[1][1:])
cache_location = os.path.join(xbmc.translatePath("special://database"), 'noise_db.db')
dbcon = database.connect(cache_location)
dbcur = dbcon.cursor()

lang_is = 0; # 0: English, 1: Spanish

if 'Spanish' in xbmc.getLanguage():
    lang_is = 1

LANG = {
	'Track added to ' : 'Canción añadida en ',
	' successfully' : ' correctamente',
	'Hey!' : 'Oye!',
	'This Track is already in ' : 'Esta canción ya se encuentra en ',
	'Deleted' : 'Borrada',
	'The Track has been deleted from the Tracklist' : 'Se ha borrado la canción del Tracklist',
	'The Tracklist has been deleted' : 'Se ha borrado la Tracklist'
}

def str_by_lang(str_in):
    if lang_is == 0:
        return str_in
    else:
        if str_in in LANG:
            return LANG[str_in]
        else:
            return str_in

dbcur.execute("CREATE TABLE IF NOT EXISTS my_tracklist (tracklist TEXT,	artist TEXT, title TEXT, image TEXT, duration INT, plot TEXT, added INT, UNIQUE(tracklist, artist, title, image));")

if args['mode'][0] == 'save':

	if 'image' in args:
		image = args['image'][0]
		msg_image = args['image'][0]
	else:
		image = '';
		msg_image = 'special://home/addons/plugin.video.noise/icon.png'

	dbcur.execute('SELECT * FROM my_tracklist WHERE tracklist = "' + args['tracklist'][0].replace('"', '[*DQ*]') + '" AND artist = "' + args['artist'][0].replace('"', '[*DQ*]') + '" AND title = "' + args['title'][0].replace('"', '[*DQ*]') + '" AND image = "' + image + '"')
	match = dbcur.fetchone()
	if match == None:
		dbcur.execute('INSERT INTO my_tracklist VALUES ("' + args['tracklist'][0].replace('"', '[*DQ*]') + '", "' + args['artist'][0].replace('"', '[*DQ*]') + '", "' + args['title'][0].replace('"', '[*DQ*]') + '", "' + image + '", ' + args['duration'][0] + ', "' + base64.b64encode(args['plot'][0]) + '", ' + datetime.now().strftime("%Y%m%d%H%M%S") + ')')
		dbcon.commit()
		xbmc.executebuiltin('XBMC.Notification(%s, %s, %s, %s)' % (args['artist'][0] + ' - ' + args['title'][0], str_by_lang('Track added to ') + args['tracklist'][0] + str_by_lang(' successfully'), 4000, msg_image))
	else:
		xbmc.executebuiltin('XBMC.Notification(%s, %s, %s, %s)' % (str_by_lang('Hey!'), str_by_lang('This Track is already in ') + args['tracklist'][0], 4000, 'special://home/addons/plugin.video.noise/icon.png'))

if args['mode'][0] == 'delete':
	dbcur.execute('DELETE FROM my_tracklist WHERE tracklist = "' + args['tracklist'][0].replace('"', '[*DQ*]') + '" AND artist = "' + args['artist'][0].replace('"', '[*DQ*]') + '" AND title = "' + args['title'][0].replace('"', '[*DQ*]') + '" AND image = "' + args['image'][0] + '"')
	dbcon.commit()
	xbmc.executebuiltin("Container.Refresh")
	xbmc.executebuiltin('XBMC.Notification(%s, %s, %s, %s)' % (str_by_lang('Deleted'), str_by_lang('The Track has been deleted from the Tracklist'), 4000, 'special://home/addons/plugin.video.noise/icon.png'))

if args['mode'][0] == 'delete_list':
	dbcur.execute('DELETE FROM my_tracklist WHERE tracklist = "' + args['tracklist'][0].replace('"', '[*DQ*]') + '"')
	dbcur.execute('DELETE FROM my_tracklists WHERE name = "' + args['tracklist'][0].replace('"', '[*DQ*]') + '"')
	dbcon.commit()
	xbmc.executebuiltin("Container.Refresh")
	xbmc.executebuiltin('XBMC.Notification(%s, %s, %s, %s)' % (str_by_lang('Deleted'), str_by_lang('The Tracklist has been deleted'), 4000, 'special://home/addons/plugin.video.noise/icon.png'))