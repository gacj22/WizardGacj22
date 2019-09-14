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
	'Deleted' : 'Borrada',
    'Term removed from Search history' : 'Se ha borrado la búsqueda'
}

def str_by_lang(str_in):
    if lang_is == 0:
        return str_in
    else:
        if str_in in LANG:
            return LANG[str_in]
        else:
            return str_in

if args['mode'][0] == 'delete':
	dbcur.execute('DELETE FROM search WHERE search_type = "' + args['search_type'][0].lower() + '" AND query = "' + args['query'][0].replace('"', '[*DQ*]') + '"')
	dbcon.commit()
	xbmc.executebuiltin("Container.Refresh")
	xbmc.executebuiltin('XBMC.Notification(%s, %s, %s, %s)' % (str_by_lang('Deleted'), str_by_lang('Term removed from Search history'), 4000, 'special://home/addons/plugin.video.noise/icon.png'))