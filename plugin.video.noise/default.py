# encoding=utf8
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import xbmcgui
import xbmcplugin
import xbmc
import urllib
import urllib2
import urlparse
import requests
import json
import xbmcaddon
import youtube_resolver
import base64
import os
import re
import unicodedata
import settings
from difflib import SequenceMatcher
from sqlite3 import dbapi2 as database
from datetime import datetime, timedelta

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
my_addon = xbmcaddon.Addon()
PATH = my_addon.getAddonInfo('path')
RESOURCES = PATH+'/resources/icons/'
REMOTE_URL = 'http://hirayasoftware.com/noise_brain/'

cache_location = settings.get_db_dir()
dbcon = database.connect(cache_location)
dbcur = dbcon.cursor()

lang_is = 0; # 0: English, 1: Spanish

if 'Spanish' in xbmc.getLanguage():
    lang_is = 1

LANG = {
    'Search' : 'Buscar',
    'Artist' : 'Artista',
    'Label' : 'Sello',
    'Filter' : 'Filtrar',
    'Add to MY ALBUMS' : 'Añadir a MIS ÁLBUMES',
    'Add new Tracklist' : 'Añadir nueva Tracklist',
    'Tracklist created successfully' : 'Tracklist creada correctamente',
    'Hey!' : 'Oye!',
    'This tracklist is already in My Tracklists' : 'Ya existe una Tracklist con ese nombre',
    'Add to Tracklist' : 'Añadir a la Tracklist',
    'Delete from the Tracklist' : 'Borrar de la Tracklist',
    '[B]Search Album[/B]\n\nYou can find any music album or single by typing the album name or any track title.': '[B]Buscar Album[/B]\n\nEncuentra cualquier Album o Single buscando por el título del album o por el título de una canción.',
    'Search by Artist' : 'Buscar por Artista',
    '[B]Search by Artist[/B]\n\nType and find any group or artist and browse for their released albums.' : '[B]Buscar por Artista[/B]\n\nEncuentra cualquier Grupo o Artista y explora los álbumes de toda su discografía.',
    'Search by Label' : 'Buscar por Sello',
    '[B]Search by Label[/B]\n\nType and find any label and browse for all their released albums.' : '[B]Buscar por Sello[/B]\n\nEncuentra cualquier sello y explora todos sus álbumes.',
    'Browse Styles' : 'Explorar Estilos',
    '[B]Browse by Styles[/B]\n\nBrowse for any album by style.' : '[B]Explorar Estilos[/B]\n\nEncuentra cualquier album por estilo.',
    'People Listening' : 'Lo más escuchado',
    '[B]People Listening[/B]\n\nBrowse albums which people are listening to right now.' : '[B]Lo más escuchado[/B]\n\nDescubre qué álbumes son los más escuchados.',
    'New Albums' : 'Nuevos Álbumes',
    '[B]New Albums[/B]\n\nBrowse for newly added and released albums.' : '[B]Nuevos Álbumes[/B]\n\nExplora los nuevos álbumes, clasificados por estilo.',
    'My Albums' : 'Mis Álbumes',
    '[B]My Albums[/B]\n\nListen to your saved albums here.\n\nTo save your favorite albums, hit right click on the album that you want to save.' : '[B]Mis Álbumes[/B]\n\nEscucha aquí los álbumes que has guardado.\n\nPara guardar tus álbumes preferidos, haz click en el botón derecho sobre el álbum que quieres guardar.',
    'My Tracklists' : 'Mis Tracklists',
    '[B]My Tracklists[/B]\n\nCreate new Tracklists here and save any track you like to these lists.\n\nListen to your favorite songs from your saved tracklists.' : '[B]Mis Tracklists[/B]\n\nCrea nuevas Tracklists y guarda cualquier canción que te guste en ellas.\n\nEscucha tus canciones favoritas desde tus tracklists.',
    '[B]Extra[/B]\n\nDiscover other features here.\n\nListen to live concerts, unreleased music, electronic sessions and more!' : '[B]Extra[/B]\n\nEncuentra muchas mas cosas aquí.\n\nEscucha conciertos, música inédita, sesiones de música electrónica y mucho más!',
    'Next Page' : 'Siguiente Página',
    'Add to MY ALBUMS' : 'Añadir a MIS ÁLBUMES',
    'Filter by year' : 'Filtrar por año',
    'Delete from MY ALBUMS' : 'Borrar de MIS ÁLBUMES',
    '[B]Add New Tracklist[/B]' : '[B]Añadir Nueva Tracklist[/B]',
    "[B]Add New Tracklist[/B]\nCreate a new Tracklist to start adding tracks to it." : "[B]Añadir Nueva Tracklist[/B]\nCrea una nueva Tracklist para añadir canciones.",
    'Delete this Tracklist' : 'Borrar esta Tracklist',
    "Browse for the best albums in\n[B]" : "Explora los mejores álbumes de\n[B]",
    "Browse for the latest albums in\n[B]" : "Explora los últimos álbumes de\n[B]",
    "Browse for all the albums in:\n[B]" : "Explora todo los álbumes de:\n[B]",
    'Search New' : 'Buscar nuevo',
    'Remove search term' : 'Eliminar esta búsqueda',
    "Search again for [B]\"" : "Buscar otra vez [B]\"",
    'Choose a directory to save the Album' : 'Elige un directorio para guardar el Album',
    'Choose a directory to save the Tracklist' : 'Elige un directorio para guardar la Tracklist',
    'Choose a directory to save the Track' : 'Elige un directorio para guardar la canción',
    'Album Downloaded' : 'Album Descargado',
    'Tracklist Downloaded' : 'Tracklist Descargada',
    'Track Downloaded' : 'Canción Descargada',
    'Download Tracklist' : 'Descargar Tracklist',
    'Download Album' : 'Descargar Album',
    'Download this Track' : 'Descargar esta Canción',
    'Please wait' : 'Espera',
    'The previous download is still in progress...': 'Todavía hay una descarga en proceso...',
    'Database': 'Base de datos'
}

LANG_info = {
    'Label:' : 'Sello:',
    'Format:' : 'Formato:',
    'Country:' : 'País:',
    'Genre:' : 'Género:',
    'Style:' : 'Estilo:',
    'Releases' : 'Publicaciones',
    'Albums' : 'Álbumes',
    'Compilations' : 'Compilaciones',
    'Miscellaneous' : 'Varios',
    'Appearances' : 'Aparece en',
    'Credits' : 'Créditos',
    'Featuring & Presenting' : 'Presentando',
    'Production' : 'Producción',
    'Technical' : 'Como Técnico',
    'Unofficial' : 'No Oficial',
    'Vocals' : 'Vocales',
    'Instruments & Performance' : 'Instrumentos & Actuación',
    'Writing & Arrangement' : 'Escritura & Composición',
    'Acting, Literary & Spoken' : 'Participación, Literatura & Narración',
    'Conducting & Leading' : 'Guiando & Liderando'
}

LANG_plot = {
    'Releases' : 'Publicaciones',
    'Albums' : 'Álbumes',
    'Compilations' : 'Compilaciones',
    'Miscellaneous' : 'Varios',
    'Appearances' : 'Aparece en',
    'Credits' : 'Créditos',
    'Featuring & Presenting' : 'Presentando',
    'Production' : 'Producción',
    'Technical' : 'Como Técnico',
    'Unofficial' : 'No Oficial',
    'Vocals' : 'Vocales',
    'Instruments & Performance' : 'Instrumentos & Actuación',
    'Writing & Arrangement' : 'Escritura & Composición',
    'Acting, Literary & Spoken' : 'Participación, Literatura & Narración',
    'Conducting & Leading' : 'Guiando & Liderando',
    'Management' : 'Dirección'
}

def get_iam_downloading():
    if os.path.isfile(PATH+'/resources/IAM_DOWNLOADING.info') == True:
        f = open(PATH+'/resources/IAM_DOWNLOADING.info', "r")
        iam_downloading = f.read()
        f.close()
    else:
        iam_downloading = '0'
        set_iam_downloading('0')
    return iam_downloading

def set_iam_downloading(n):
    f = open(PATH+'/resources/IAM_DOWNLOADING.info', "w")
    f.write(n)
    f.close()

def strip_accents(text):

    try:
        text = unicode(text.encode("utf-8"), 'utf-8')
    except NameError:
        pass

    text = unicodedata.normalize('NFD', text)\
           .encode('ascii', 'ignore')\
           .decode("utf-8")

    return str(text)

def only_legal_chars(string_in):

    string_out = strip_accents(string_in)
    string_out = re.sub(r'[\\/:"*?<>|]+', "", string_out)
    string_out = "".join(i for i in string_out if ord(i)<128)
    string_out = ' '.join(string_out.split())
    return string_out

def str_by_lang(str_in):
    if lang_is == 0:
        return str_in
    else:
        if str_in in LANG:
            return LANG[str_in]
        else:
            return str_in

def info_by_lang(str_in):
    if lang_is == 0:
        return str_in
    else:
        str_out = str_in.replace('Label:', LANG_info['Label:'])
        str_out = str_out.replace('Format:', LANG_info['Format:'])
        str_out = str_out.replace('Country:', LANG_info['Country:'])
        str_out = str_out.replace('Genre:', LANG_info['Genre:'])
        str_out = str_out.replace('Style:', LANG_info['Style:'])
        return str_out

def plot_by_lang(str_in):
    if lang_is == 0:
        str_out = str_in.replace('Publicaciones recientes', 'Recently released')
        return str_out
    else:
        str_out = str_in.replace('Releases', LANG_plot['Releases'])
        str_out = str_out.replace('Albums', LANG_plot['Albums'])
        str_out = str_out.replace('Compilations', LANG_plot['Compilations'])
        str_out = str_out.replace('Miscellaneous', LANG_plot['Miscellaneous'])
        str_out = str_out.replace('Appearances', LANG_plot['Appearances'])
        str_out = str_out.replace('Credits', LANG_plot['Credits'])
        str_out = str_out.replace('Featuring & Presenting', LANG_plot['Featuring & Presenting'])
        str_out = str_out.replace('Production', LANG_plot['Production'])
        str_out = str_out.replace('Technical', LANG_plot['Technical'])
        str_out = str_out.replace('Unofficial', LANG_plot['Unofficial'])
        str_out = str_out.replace('Vocals', LANG_plot['Vocals'])
        str_out = str_out.replace('Instruments & Performance', LANG_plot['Instruments & Performance'])
        str_out = str_out.replace('Writing & Arrangement', LANG_plot['Writing & Arrangement'])
        str_out = str_out.replace('Acting, Literary & Spoken', LANG_plot['Acting, Literary & Spoken'])
        str_out = str_out.replace('Conducting & Leading', LANG_plot['Conducting & Leading'])
        str_out = str_out.replace('Management', LANG_plot['Management'])
        return str_out

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

def getusersearch(search_type):
    kb = xbmc.Keyboard('default', 'heading')
    kb.setDefault('')
    kb.setHeading(str_by_lang('Search') + ' ' + str_by_lang(search_type.capitalize()) + ':')
    kb.setHiddenInput(False)
    kb.doModal()
    if (kb.isConfirmed()):
        search_term  = kb.getText()
        return(search_term)
    else:
        return ''

def filterstylebyyear(style_name, style_url, sort):
    kb = xbmc.Keyboard('default', 'heading')
    kb.setDefault('')
    kb.setHeading(str_by_lang('Filter') + ' ' + style_name + ' ' + str_by_lang('by year') + ':')
    kb.setHiddenInput(False)
    kb.doModal()
    if (kb.isConfirmed()):
        year  = kb.getText()
        showalbumsstyle(style_url, '1', year, sort)
    else:
        return ''


def showalbumsstyle(search_url, page, year, sort):
    if sort == 'score':
        rq = cached_url(REMOTE_URL + 'albums_style.php?q=' + search_url + '&p=' + page + '&y=' + year.replace(' ', '') + '&s=' + sort, 1)
    else:
        rq = cached_url_m(REMOTE_URL + 'albums_style.php?q=' + search_url + '&p=' + page + '&y=' + year.replace(' ', '') + '&s=' + sort, 10)
    albums_list = json.loads(rq)
    for this_album in albums_list:

        if this_album['page'] == '':

            if this_album['fanart'] == '':
                this_album['fanart'] = RESOURCES + 'album.png'
            if this_album['thumbnail'] == '':
                this_album['thumbnail'] = RESOURCES + 'album.png'

            url = build_url({'mode': 'folder', 'search_type': 'album', 'url': this_album['url'], 'album_type': 'release', 'image': this_album['thumbnail']})

            commands = []
            scriptToRun = "special://home/addons/plugin.video.noise/resources/myAlbums.py"
            argsToSend = '?' + urllib.urlencode({'mode':'save', 'type':'album', 'album_type':'release', 'id':this_album['url'], 'image':this_album['thumbnail'], 'title':this_album['title']})
            commands.append(( str_by_lang('Add to MY ALBUMS'), 'XBMC.RunScript(' + scriptToRun + ', ' + argsToSend + ')' ))

            cmd = 'XBMC.RunPlugin({})'.format(build_url({'mode': 'download', 'type':'album', 'album_type': 'release', 'id':this_album['url'], 'image':this_album['thumbnail'], 'title': base64.b64encode(this_album['title'])}))
            commands.append(( str_by_lang('Download Album'), cmd ))

            li = xbmcgui.ListItem(this_album['title'], iconImage=this_album['thumbnail'])
            li.setInfo(type="Video", infoLabels={ "plot": '[B]' + this_album['title'] + '[/B]'})
            li.setArt({'fanart': this_album['fanart'], 'thumb': this_album['thumbnail']})
            li.addContextMenuItems(commands)
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
        elif this_album['page'] == '-1':
            if sort != 'date_added':
                url = build_url({'mode': 'filter_by_year', 'url': this_album['url'], 'search_url': search_url, 'sort': sort})
                li = xbmcgui.ListItem('[I]' + str_by_lang('Filter by year') + '[/I]', iconImage=RESOURCES+'filter.png')
                li.setInfo(type="Video", infoLabels={ "plot" : '[B]' + str_by_lang('Filter by year') + '[/B]'})
                li.setArt({'fanart': RESOURCES + 'styles.jpg', 'thumb': RESOURCES+'filter.png'})
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
        else:
            url = build_url({'mode': 'folder', 'search_type': 'style', 'search_url': this_album['url'], 'page': this_album['page'], 'year': year, 'sort': sort})
            li = xbmcgui.ListItem('[I]' + str_by_lang('Next Page') + '[/I]', iconImage=RESOURCES+'next.png')
            li.setInfo(type="Video", infoLabels={"plot": "[B]" + str_by_lang('Next Page') + " (" + str(int(this_album['page'])) + ")[/B]"})
            if sort == 'score':
                li.setArt({'fanart': RESOURCES + 'styles.jpg', 'thumb': RESOURCES+'next.png'})
            else:
                li.setArt({'fanart': RESOURCES + 'new_albums.jpg', 'thumb': RESOURCES+'next.png'})
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)


def addnewtracklist():
    kb = xbmc.Keyboard('default', 'heading')
    kb.setDefault('')
    kb.setHeading(str_by_lang('Add new Tracklist'))
    kb.setHiddenInput(False)
    kb.doModal()
    if (kb.isConfirmed()):
        term = kb.getText()
        dbcur.execute("CREATE TABLE IF NOT EXISTS my_tracklists (name TEXT, UNIQUE(name));")
        dbcon.commit()
        dbcur.execute("SELECT * FROM my_tracklists WHERE name = '" + term + "'")
        match = dbcur.fetchone()
        if match == None:
            dbcur.execute('INSERT INTO my_tracklists VALUES("' + term.replace('"', '[*DQ*]') + '")')
            dbcon.commit()
            xbmc.executebuiltin("Container.Refresh")
            xbmc.executebuiltin('XBMC.Notification(%s, %s, %s, %s)' % (term, str_by_lang('Tracklist created successfully')  , 4000, 'special://home/addons/plugin.video.noise/icon.png'))
        else:
            xbmc.executebuiltin('XBMC.Notification(%s, %s, %s, %s)' % (str_by_lang('Hey!'), str_by_lang('This tracklist is already in My Tracklists')  , 4000, 'special://home/addons/plugin.video.noise/icon.png'))
    else:
        return_list

def get_resolved_video(id_video):
    if id_video == '':
        return '';
    else:
        data_videos = youtube_resolver.resolve(id_video)
        for data_video in data_videos:
            if data_video['sort'][0] != 1080:
                return data_video['url']

def time_to_seconds(time_in):
    a = time_in.split(':')

    if len(a) > 1:
        if len(a) == 2:
            return (int(a[0])*60) + int(a[1])
        else:
            return (int(a[0])*60*60) + (int(a[1])*60) + int(a[2])

    else:
        return ''

def clean_this_shit(str_in):
    str_out = str_in
    str_out = str_out.replace('(', ' ')
    str_out = str_out.replace(')', ' ')
    str_out = str_out.replace('&amp;', '&')

    str_out = ' '.join(str_out.split())

    return str_out

def give_most_similar_videos(track_info, yt_html_res):

    parts = yt_html_res.split('data-context-item-id="')
    parts.pop(0);

    r = 0
    options = []
    best_duration = -1
    best_duration_pos = -1
    best_url = ''
    looper = 0
    final = []

    n = 0
    r = 0
    best_ratio = 0.0000

    track_name = track_info['artist'] + ' - ' + track_info['name']
    track_name = clean_this_shit(track_name.lower())
    track_name = re.sub('[^\w ]', '', track_name)
    track_name = clean_this_shit(track_name.lower())

    for part in parts:

        a = part.split('"')
        id_video = a[0]

        b = part.split('<span class="video-time" aria-hidden="true">')
        c = b[1].split('<')
        duration = c[0]

        d = part.split('<h3')
        e = d[1].split('</a>')
        cleanr = re.compile('<.*?>')
        title = re.sub(cleanr, '', '<h3' + e[0])
        title = clean_this_shit(title)
        title = re.sub('[^\w ]+', '', title.lower())
        title = clean_this_shit(title)

        ratio = SequenceMatcher(None, track_name, title.lower().replace('-', '')).ratio()

        if ratio > 0.7:
            options.append({'pos': r, 'ratio': ratio, 'yt_title': title, 'yt_id': id_video, 'duration': time_to_seconds(duration)})
        else:

            dg_words = track_name.split(' ')
            yt_words = title.split(' ')

            found_len = 0.0000
            if len(dg_words) > len(yt_words):
                total_len = 0.0000 + len(dg_words)
                for word in yt_words:
                    if word in dg_words:
                        found_len = found_len + 1
            else:
                total_len = 0.0000 + len(yt_words)
                for word in dg_words:
                    if word in yt_words:
                        found_len = found_len + 1

            percent = found_len/total_len

            if percent > 0.7:
                options.append({'pos': r, 'ratio': percent, 'yt_title': title, 'yt_id': id_video, 'duration': time_to_seconds(duration)})

        r = r + 1

    options = sorted(options, key = lambda i: i['ratio'],reverse=True)

    if r == 0:
        final.append({'id': '', 'url': ''})
        return final
    else:
        if track_info['time'] != '':
            track_info_time = float(track_info['time'])
            for opt in options:

                duration = float(opt['duration'])

                if looper == 0:
                    best_duration = duration
                    best_duration_pos = looper
                else:
                    if duration > track_info_time:
                        diff = duration - track_info_time
                    else:
                        diff = track_info_time - duration

                    if diff < best_duration:
                        best_duration = diff
                        best_duration_pos = looper

                looper = looper + 1

                if looper == 5:

                    if best_duration_pos != 0:
                        if abs(options[best_duration_pos]['duration'] - options[0]['duration']) <= 90:
                            best_duration_pos = 0

                    final.append({'id': options[best_duration_pos]['yt_id'], 'url': get_resolved_video(options[best_duration_pos]['yt_id'])})
                    return final

            if looper < 5:
                if best_duration_pos != 0:
                    if abs(options[best_duration_pos]['duration'] - options[0]['duration']) <= 90:
                        best_duration_pos = 0

                final.append({'id': options[best_duration_pos]['yt_id'], 'url': get_resolved_video(options[best_duration_pos]['yt_id'])})
                return final

        else:
            final.append({'id': options[0]['yt_id'], 'url': get_resolved_video(options[0]['yt_id'])})
            return final

def cached_url(url, expire_days):

    dbcur.execute("CREATE TABLE IF NOT EXISTS url_cache (url TEXT, content TEXT, expire INT, UNIQUE(url));")
    dbcon.commit()
    dbcur.execute("SELECT content FROM url_cache WHERE url = '" + url + "' AND expire > " + datetime.now().strftime("%Y%m%d%H%M%S"))
    match = dbcur.fetchone()
    if match == None:
        rq = requests.get(url).content
        expiration = datetime.now() + timedelta(expire_days)
        expire = expiration.strftime("%Y%m%d%H%M%S")
        dbcur.execute("DELETE FROM url_cache WHERE url = '" + url + "'")
        dbcur.execute("INSERT INTO url_cache VALUES ('" + url + "','" + base64.b64encode(rq) + "'," + expire + ")")
        dbcon.commit()
    else:
        rq = base64.b64decode(match[0])

    return rq

def cached_url_m(url, expire_minutes):

    dbcur.execute("CREATE TABLE IF NOT EXISTS url_cache (url TEXT, content TEXT, expire INT, UNIQUE(url));")
    dbcon.commit()
    dbcur.execute("SELECT content FROM url_cache WHERE url = '" + url + "' AND expire > " + datetime.now().strftime("%Y%m%d%H%M%S"))
    match = dbcur.fetchone()
    if match == None:
        rq = requests.get(url).content
        expiration = datetime.now() + timedelta(minutes=expire_minutes)
        expire = expiration.strftime("%Y%m%d%H%M%S")
        dbcur.execute("DELETE FROM url_cache WHERE url = '" + url + "'")
        dbcur.execute("INSERT INTO url_cache VALUES ('" + url + "','" + base64.b64encode(rq) + "'," + expire + ")")
        dbcon.commit()
    else:
        rq = base64.b64decode(match[0])

    return rq

def create_track_item(track, image, url_video, is_from_tracklist, id_video):

    if url_video != '':

        if track['time'] == '':
            video_url_parts = url_video.split('&dur=')
            v2 = video_url_parts[1].split('&')
            duration = v2[0]
        else:
            duration = track['time']

        commands = []
        scriptToRun = "special://home/addons/plugin.video.noise/resources/myTracklists.py"
        dbcur.execute("CREATE TABLE IF NOT EXISTS my_tracklists (name TEXT, UNIQUE(name));")
        dbcon.commit()

        if is_from_tracklist == 0:
            dbcur.execute("SELECT * FROM my_tracklists")
            matches = dbcur.fetchall()
            for match in matches:
                commands.append((str_by_lang('Add to Tracklist') + ': ' + match[0], 'XBMC.RunScript(' + scriptToRun + ', ' + '?' + urllib.urlencode({'mode' : 'save', 'artist' : track['artist'], 'title' : track['name'], 'image' : image, 'plot' : track['info'], 'duration' : duration, 'tracklist': match[0]}) + ')'))
        else:
            commands.append((str_by_lang('Delete from the Tracklist') + ': ' + track['tracklist'], 'XBMC.RunScript(' + scriptToRun + ', ' + '?' + urllib.urlencode({'mode' : 'delete', 'artist' : track['artist'], 'title' : track['name'], 'image' : image, 'tracklist': track['tracklist']}) + ')'))

        cmd = 'XBMC.RunPlugin({})'.format(build_url({'mode': 'download', 'type':'track', 'artist':track['artist'], 'name':track['name'], 'id_video':id_video, 'image': image}))
        commands.append(( str_by_lang('Download this Track'), cmd ))

        li = xbmcgui.ListItem('[B]' + track['artist'] + ' - ' + track['name'] + '[/B]', iconImage=image)
        li.setInfo(type="Video", infoLabels={ "plot": info_by_lang(track['info']), "Title" : '[B]' + track['artist'] + ' - ' + track['name'] + '[/B]', "Duration" : duration})
        li.setArt({ 'poster': image, 'fanart': image })
        li.addContextMenuItems(commands)
        li.setProperty("IsPlayable","true")
    else:
        li = xbmcgui.ListItem('[I][COLOR silver]' + track['artist'] + ' - ' + track['name'] + '[/COLOR][/I]', iconImage=image)
        li.setArt({ 'poster': image, 'fanart': image })
        li.setProperty("IsPlayable","false")
    
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url_video, listitem=li, isFolder=False)

def get_url_from_id_video(id_video):
    return get_resolved_video(id_video)

def download_track_item(track, url_video, folder, n, times):

    if url_video != '':
        try:

            if os.path.isdir(PATH+'/temp') == False:
                os.mkdir(PATH+'/temp')

            if n != 0:
                if n < 10:
                    track_n = '0' + str(n) + ' '
                else:
                    track_n = str(n) + ' '
            else:
                track_n = ''

            if times == 2:
                final_file = folder + '/' + track_n + only_legal_chars(track['artist'] + ' - ' + track['name']) + '_2nd_time.mp3'
                final_temp_file = PATH + '/temp/' + track_n + only_legal_chars(track['artist'] + ' - ' + track['name']) + '_2nd_time.mp3'
            else:
                final_file = folder + '/' + track_n + only_legal_chars(track['artist'] + ' - ' + track['name']) + '.mp3'
                final_temp_file = PATH + '/temp/' + track_n + only_legal_chars(track['artist'] + ' - ' + track['name']) + '.mp3'

            hs = {
                'pragma':'no-cache',
                'origin':'https://y2mate.com',
                'accept-language':'es-ES,es;q=0.9',
                'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36',
                'content-type':'application/x-www-form-urlencoded; charset=UTF-8',
                'accept':'*/*',
                'cache-control':'no-cache',
                'authority':'mate06.y2mate.com',
                'referer':'https://y2mate.com/es/youtube-to-mp3/' + url_video
            }

            ds = urllib.urlencode({'url':'https://www.youtube.com/watch?v=' + url_video, 'ajax':'1'})
            
            request = urllib2.Request("https://mate06.y2mate.com/es/mp3/ajax/", data=ds, headers=hs)
            
            data = urllib2.urlopen(request).read()

            if 'Sorry' in data:
                
                hs2 = {
                    'Accept':'*/*',
                    'Referer':'https://mp3converter.to/',
                    'Origin':'https://mp3converter.to',
                    'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36'
                }

                request2 = urllib2.Request('https://api-1.yxwz.xyz/sconverter.php?url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3D' + url_video, headers=hs2)
                datos = urllib2.urlopen(request2).read()

                request3 = urllib2.Request('https://api-1.yxwz.xyz/api/?ftype=mp3&quality=320&url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3D' + url_video + '&vid=' + url_video + datos + '&web=insertlink', headers=hs2)
                datos3 = urllib2.urlopen(request3).read()

                data2 = json.loads(datos3)

                request4 = urllib2.Request('https:' + data2['result'])

                f = open(final_temp_file, "wb")
                f.write(urllib2.urlopen(request4).read())
                f.close()
                            
            else:
                split_data = data.split('_id: \'')
                split_data2 = split_data[1].split('\'')

                xbmc.sleep(500)

                for x in range(0, 10):

                    hs5 = {
                        'pragma':'no-cache',
                        'origin':'https://y2mate.com',
                        'accept-language':'es-ES,es;q=0.9',
                        'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36',
                        'content-type':'application/x-www-form-urlencoded; charset=UTF-8',
                        'accept':'*/*',
                        'cache-control':'no-cache',
                        'authority':'mate08.y2mate.com',
                        'referer':'https://y2mate.com/es/youtube-to-mp3/' + url_video
                    }

                    ds5 = urllib.urlencode({'type':'youtube','_id':split_data2[0],'v_id':url_video,'mp3_type':'320'})

                    request5 = urllib2.Request('https://mate08.y2mate.com/mp3Convert/', data=ds5, headers=hs5)
                    datos5 = urllib2.urlopen(request5).read()

                    json_data = json.loads(datos5)

                    a = json_data['result'].split('<a href="')
                    b = a[1].split('"')
                    if b[0] != '':

                        request6 = urllib2.Request(b[0])
                        
                        f = open(final_temp_file, "wb")
                        f.write(urllib2.urlopen(request6).read())
                        f.close()

                        break
                    else:
                        xbmc.sleep(500)

            xbmc.sleep(500)

            if times == 1:
                if os.path.isfile(final_temp_file) == True:
                    download_track_item(track, url_video, folder, n, 2)
                else:
                    download_track_item(track, url_video, folder, n, 1)
            else:
                if os.path.isfile(final_temp_file) == True:
                    size1 = os.path.getsize(PATH + '/temp/' + track_n + only_legal_chars(track['artist'] + ' - ' + track['name']) + '.mp3')
                    size2 = os.path.getsize(PATH + '/temp/' + track_n + only_legal_chars(track['artist'] + ' - ' + track['name']) + '_2nd_time.mp3')
                    if size1 != size2:
                        os.remove(PATH + '/temp/' + track_n + only_legal_chars(track['artist'] + ' - ' + track['name']) + '.mp3')
                        os.remove(PATH + '/temp/' + track_n + only_legal_chars(track['artist'] + ' - ' + track['name']) + '_2nd_time.mp3')
                        download_track_item(track, url_video, folder, n, 1)
                    else:
                        os.remove(PATH + '/temp/' + track_n + only_legal_chars(track['artist'] + ' - ' + track['name']) + '_2nd_time.mp3')

                        fr = open(PATH + '/temp/' + track_n + only_legal_chars(track['artist'] + ' - ' + track['name']) + '.mp3', 'rb')
                        load_file = fr.read()
                        fr.close()

                        fw = open(folder + '/' + track_n + only_legal_chars(track['artist'] + ' - ' + track['name']) + '.mp3', "wb")
                        fw.write(load_file)
                        fw.close()
                        
                        os.remove(PATH + '/temp/' + track_n + only_legal_chars(track['artist'] + ' - ' + track['name']) + '.mp3')
                else:
                    download_track_item(track, url_video, folder, n, 2)

        except IndexError:

            if os.path.isfile(PATH + '/temp/' + track_n + only_legal_chars(track['artist'] + ' - ' + track['name']) + '.mp3') == True:
                os.remove(PATH + '/temp/' + track_n + only_legal_chars(track['artist'] + ' - ' + track['name']) + '.mp3')
            if os.path.isfile(PATH + '/temp/' + track_n + only_legal_chars(track['artist'] + ' - ' + track['name']) + '_2nd_time.mp3') == True:
                os.remove(PATH + '/temp/' + track_n + only_legal_chars(track['artist'] + ' - ' + track['name']) + '_2nd_time.mp3')
            xbmc.sleep(1)
            download_track_item(track, url_video, folder, n, 1)

def download_cached_track(track, folder, n):

    yt_title = track['artist'] + ' ' + track['name']
    db_title = yt_title.replace('"', '[*DQ*]')

    url_video = ''

    try:

        dbcur.execute('CREATE TABLE IF NOT EXISTS track_id_cache (name TEXT, id_video TEXT, expire INT, UNIQUE(name));')
        dbcon.commit()
        dbcur.execute('SELECT id_video FROM track_id_cache WHERE name = "' + db_title + '" AND expire > ' + datetime.now().strftime("%Y%m%d%H%M%S"))
        match = dbcur.fetchone()
        if match == None:
            res = urllib2.urlopen("http://www.youtube.com/results?" + urllib.urlencode({"search_query" : yt_title.lower()})).read()
            id_and_url = give_most_similar_videos(track, res)

            if id_and_url[0]['id'] != '':
                expiration = datetime.now() + timedelta(hours=5)
            else:
                expiration = datetime.now() + timedelta(hours=5)

            dbcur.execute('DELETE FROM track_id_cache WHERE name = "' + db_title + '"')
            dbcur.execute('INSERT INTO track_id_cache VALUES ("' + db_title + '","' + id_and_url[0]['id'] + '",' + expiration.strftime("%Y%m%d%H%M%S") + ')')
            
            expiration = datetime.now() + timedelta(hours=5)

            dbcur.execute('CREATE TABLE IF NOT EXISTS track_video_cache (id_video TEXT, res_url TEXT, expire INT, UNIQUE(id_video));')
            dbcur.execute('DELETE FROM track_video_cache WHERE id_video = "' + id_and_url[0]['id'] + '"')
            dbcur.execute('INSERT INTO track_video_cache VALUES ("' + id_and_url[0]['id'] + '","' + id_and_url[0]['url'] + '",' + expiration.strftime("%Y%m%d%H%M%S") + ')')
            dbcon.commit()

            download_track_item(track, id_and_url[0]['id'], folder, n, 1)

        else:
            
            most_similar = match[0]

            dbcur.execute('CREATE TABLE IF NOT EXISTS track_video_cache (id_video TEXT, res_url TEXT, expire INT, UNIQUE(id_video));')
            dbcon.commit()
            dbcur.execute('SELECT res_url, id_video, expire FROM track_video_cache WHERE id_video = "' + most_similar + '" AND expire > ' + datetime.now().strftime("%Y%m%d%H%M%S"))
            match = dbcur.fetchone()
            if match == None:
                url_video = get_url_from_id_video(most_similar)

                expiration = datetime.now() + timedelta(hours=5)

                dbcur.execute('DELETE FROM track_video_cache WHERE id_video = "' + most_similar + '"')
                dbcur.execute('INSERT INTO track_video_cache VALUES ("' + most_similar + '","' + url_video + '",' + expiration.strftime("%Y%m%d%H%M%S") + ')')
                dbcon.commit()
            else:
                url_video = match[0]

            download_track_item(track, most_similar, folder, n, 1)

    except IndexError:

        download_track_item(track, '', folder, n, 1)

def load_cached_track(track, image, is_from_tracklist):

    yt_title = track['artist'] + ' ' + track['name']
    db_title = yt_title.replace('"', '[*DQ*]')

    url_video = ''

    try:

        dbcur.execute('CREATE TABLE IF NOT EXISTS track_id_cache (name TEXT, id_video TEXT, expire INT, UNIQUE(name));')
        dbcon.commit()
        dbcur.execute('SELECT id_video FROM track_id_cache WHERE name = "' + db_title + '" AND expire > ' + datetime.now().strftime("%Y%m%d%H%M%S"))
        match = dbcur.fetchone()
        if match == None:
            res = urllib2.urlopen("http://www.youtube.com/results?" + urllib.urlencode({"search_query" : yt_title.lower()})).read()
            id_and_url = give_most_similar_videos(track, res)

            if id_and_url[0]['id'] != '':
                expiration = datetime.now() + timedelta(hours=5)
            else:
                expiration = datetime.now() + timedelta(hours=5)

            dbcur.execute('DELETE FROM track_id_cache WHERE name = "' + db_title + '"')
            dbcur.execute('INSERT INTO track_id_cache VALUES ("' + db_title + '","' + id_and_url[0]['id'] + '",' + expiration.strftime("%Y%m%d%H%M%S") + ')')
            
            expiration = datetime.now() + timedelta(hours=5)

            dbcur.execute('CREATE TABLE IF NOT EXISTS track_video_cache (id_video TEXT, res_url TEXT, expire INT, UNIQUE(id_video));')
            dbcur.execute('DELETE FROM track_video_cache WHERE id_video = "' + id_and_url[0]['id'] + '"')
            dbcur.execute('INSERT INTO track_video_cache VALUES ("' + id_and_url[0]['id'] + '","' + id_and_url[0]['url'] + '",' + expiration.strftime("%Y%m%d%H%M%S") + ')')
            dbcon.commit()

            create_track_item(track, image, id_and_url[0]['url'], is_from_tracklist, id_and_url[0]['id'])

        else:
            
            most_similar = match[0]

            dbcur.execute('CREATE TABLE IF NOT EXISTS track_video_cache (id_video TEXT, res_url TEXT, expire INT, UNIQUE(id_video));')
            dbcon.commit()
            dbcur.execute('SELECT res_url, id_video, expire FROM track_video_cache WHERE id_video = "' + most_similar + '" AND expire > ' + datetime.now().strftime("%Y%m%d%H%M%S"))
            match = dbcur.fetchone()
            if match == None:
                url_video = get_url_from_id_video(most_similar)

                expiration = datetime.now() + timedelta(hours=5)

                dbcur.execute('DELETE FROM track_video_cache WHERE id_video = "' + most_similar + '"')
                dbcur.execute('INSERT INTO track_video_cache VALUES ("' + most_similar + '","' + url_video + '",' + expiration.strftime("%Y%m%d%H%M%S") + ')')
                dbcon.commit()
            else:
                url_video = match[0]

            create_track_item(track, image, url_video, is_from_tracklist, most_similar)

    except IndexError:

        create_track_item(track, image, url_video, is_from_tracklist, '')

mode = args.get('mode', None)

if mode is None:

    dbcur.execute('CREATE TABLE IF NOT EXISTS messages (id_message TEXT, UNIQUE(id_message))')
    dbcon.commit()
    messages = json.loads(requests.get(REMOTE_URL + 'messages.php?lang=' + str(lang_is)).content)
    
    if messages['id_message'] != '0':
        dbcur.execute('SELECT id_message FROM messages WHERE id_message = "' + str(messages['id_message']) + '"')
        match = dbcur.fetchone()
        if match == None:
            dbcur.execute('INSERT INTO messages VALUES ("' + str(messages['id_message']) + '")')
            dbcon.commit()
            xbmc.executebuiltin("ActivateWindow(10147)")
            controller = xbmcgui.Window(10147)
            xbmc.sleep(500)
            controller.getControl(1).setLabel(base64.b64decode(messages['label_message']))
            controller.getControl(5).setText(base64.b64decode(messages['text_message']))

    url = build_url({'mode': 'search', 'search_type': 'Album', 'search_page': '1'})
    li = xbmcgui.ListItem(str_by_lang('Search') + ' Album', iconImage = RESOURCES + 'album.png')
    li.setInfo(type="Video", infoLabels={"plot": str_by_lang('[B]Search Album[/B]\n\nYou can find any music album or single by typing the album name or any track title.')})
    li.setArt({'fanart': RESOURCES + 'album.jpg'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'search', 'search_type': 'Artist', 'search_page': '1'})
    li = xbmcgui.ListItem(str_by_lang('Search by Artist'), iconImage=RESOURCES+'artist.png')
    li.setInfo(type="Video", infoLabels={"plot": str_by_lang('[B]Search by Artist[/B]\n\nType and find any group or artist and browse for their released albums.')})
    li.setArt({'fanart': RESOURCES + 'artist.jpg'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'search', 'search_type': 'Label', 'search_page': '1'})
    li = xbmcgui.ListItem(str_by_lang('Search by Label'), iconImage=RESOURCES+'label.png')
    li.setInfo(type="Video", infoLabels={"plot": str_by_lang('[B]Search by Label[/B]\n\nType and find any label and browse for all their released albums.')})
    li.setArt({'fanart': RESOURCES + 'label.jpg'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'folder', 'search_type': 'styles', 'sort': 'score' })
    li = xbmcgui.ListItem(str_by_lang('Browse Styles'), iconImage=RESOURCES+'style.png')
    li.setInfo(type="Video", infoLabels={"plot": str_by_lang('[B]Browse by Styles[/B]\n\nBrowse for any album by style.')})
    li.setArt({'fanart': RESOURCES + 'styles.jpg'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'folder', 'search_type': 'styles', 'sort': 'date_added'})
    li = xbmcgui.ListItem(str_by_lang('New Albums'), iconImage=RESOURCES+'new.png')
    li.setInfo(type="Video", infoLabels={"plot": str_by_lang('[B]New Albums[/B]\n\nBrowse for newly added and released albums.')})
    li.setArt({'fanart': RESOURCES + 'new_albums.jpg'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'people', 'page':'1'})
    li = xbmcgui.ListItem(str_by_lang('People Listening'), iconImage=RESOURCES+'people.png')
    li.setInfo(type="Video", infoLabels={"plot": str_by_lang('[B]People Listening[/B]\n\nBrowse albums which people are listening to right now.')})
    li.setArt({'fanart': RESOURCES + 'people.jpg'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'folder', 'search_type': 'My Albums'})
    li = xbmcgui.ListItem(str_by_lang('My Albums'), iconImage=RESOURCES+'myalbums.png')
    li.setInfo(type="Video", infoLabels={"plot": str_by_lang('[B]My Albums[/B]\n\nListen to your saved albums here.\n\nTo save your favorite albums, hit right click on the album that you want to save.')})
    li.setArt({'fanart': RESOURCES + 'my_albums.jpg'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'folder', 'search_type': 'My Tracklists'})
    li = xbmcgui.ListItem(str_by_lang('My Tracklists'), iconImage=RESOURCES+'tracklist.png')
    li.setInfo(type="Video", infoLabels={"plot": str_by_lang('[B]My Tracklists[/B]\n\nCreate new Tracklists here and save any track you like to these lists.\n\nListen to your favorite songs from your saved tracklists.')})
    li.setArt({'fanart': RESOURCES + 'my_tracklists.jpg'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'extra', 'page':'1'})
    li = xbmcgui.ListItem('Extra', iconImage=RESOURCES+'extra.png')
    li.setInfo(type="Video", infoLabels={"plot": str_by_lang('[B]Extra[/B]\n\nDiscover other features here.\n\nListen to live concerts, unreleased music, electronic sessions and more!')})
    li.setArt({'fanart': RESOURCES + 'extra.jpg'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'extra':
    dbcur.execute("DELETE FROM url_cache WHERE url = '" + REMOTE_URL + "extra.php?page=" + args['page'][0] + "'")
    dbcon.commit()
    rq = cached_url(REMOTE_URL + 'extra.php?page=' + args['page'][0], 1)
    extra_items = json.loads(rq)
    for item in extra_items:

        if item['title'] != ' ':

            if item['image'] == '':
                item['image'] = RESOURCES + 'extra.png'
            if item['fanart'] == '':
                item['fanart'] = RESOURCES + 'extra.jpg'

            li = xbmcgui.ListItem('[B]' + item['title'] + '[/B]', iconImage=item['image'])
            li.setInfo(type="Video", infoLabels={ "plot": item['description'], "Title" : '[B]' + item['title'] + '[/B]'})
            li.setArt({ 'poster': item['image'], 'fanart': item['fanart'] })
            li.setProperty("IsPlayable","true")
            url_extra = 'plugin://plugin.video.youtube/' + item['link'] + '/'
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url_extra, listitem=li, isFolder=True)
        else:
            url = build_url({'mode': 'extra', 'page': str(int(args['page'][0]) + 1)})
            li = xbmcgui.ListItem('[I]' + str_by_lang('Next Page') + '[/I]', iconImage=RESOURCES+'next.png')
            li.setInfo(type="Video", infoLabels={"plot": "[B]" + str_by_lang('Next Page') + " (" + str(int(args['page'][0]) + 1) + ")[/B]"})
            li.setArt({'fanart': RESOURCES + 'extra.jpg', 'thumb': RESOURCES+'next.png'})
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'people':
    rq = cached_url_m(REMOTE_URL + 'people.php?page=' + args['page'][0], 10)
    people_items = json.loads(rq)
    if people_items != None:
        for item in people_items:
            if item['title'] != ' ':

                if item['image'] == ' ':
                    item['image'] = RESOURCES + 'album.png'

                url = build_url({'mode': 'folder', 'search_type': 'album', 'url': item['url'], 'album_type': item['album_type'], 'image': item['image']})

                commands = []
                scriptToRun = "special://home/addons/plugin.video.noise/resources/myAlbums.py"
                argsToSend = '?' + urllib.urlencode({'mode':'save', 'type':'album', 'album_type':item['album_type'], 'id':item['url'], 'image':item['image'], 'title':item['title']})
                commands.append(( str_by_lang('Add to MY ALBUMS'), 'XBMC.RunScript(' + scriptToRun + ', ' + argsToSend + ')' ))

                cmd = 'XBMC.RunPlugin({})'.format(build_url({'mode': 'download', 'type':'album', 'album_type': item['album_type'], 'id':item['url'], 'image':item['image'], 'title': base64.b64encode(item['title'])}))
                commands.append(( str_by_lang('Download Album'), cmd ))
                
                li = xbmcgui.ListItem(item['title'], iconImage=item['image'])
                li.setInfo(type="Video", infoLabels={"plot": "[B]" + item['title'] + "[/B]"})
                li.setArt({'fanart': item['image'], 'thumb': item['image']})
                li.addContextMenuItems(commands)
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

            else:
                url = build_url({'mode': 'people', 'page': str(int(args['page'][0]) + 1)})
                li = xbmcgui.ListItem('[I]' + str_by_lang('Next Page') + '[/I]', iconImage=RESOURCES+'people.png')
                li.setInfo(type="Video", infoLabels={"plot": "[B]" + str_by_lang('Next Page') + " (" + str(int(args['page'][0]) + 1) + ")[/B]"})
                li.setArt({'fanart': RESOURCES + 'people.jpg', 'thumb': RESOURCES+'next.png'})
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'add_tracklist':
    addnewtracklist()

elif mode[0] == 'filter_by_year':
    year = filterstylebyyear(args['url'][0].upper().replace('+',' '), args['search_url'][0], args['sort'][0])

elif mode[0] == 'download':

    if args['type'][0] == 'album':

        if get_iam_downloading() != '1':
            
            dialog = xbmcgui.Dialog().browse(0, str_by_lang('Choose a directory to save the Album'), "music")
            if dialog != '':

                set_iam_downloading('1')

                title = base64.b64decode(args['title'][0])

                path_for_album = dialog + only_legal_chars(title)

                if os.path.isdir(path_for_album) == False:
                    os.mkdir(path_for_album)

                split_image = args['image'][0].split('.')

                img_content = urllib2.urlopen(args['image'][0])
                file_name = path_for_album + '/' + only_legal_chars(title) + '.' + split_image[-1]
                text_file = open(file_name, "wb")
                text_file.write(img_content.read())
                text_file.close()

                rq = cached_url(REMOTE_URL + 'album.php?id=' + args['id'][0] + '&type=' + args['album_type'][0], 30)
                track_list = json.loads(rq)

                n = 1

                for track in track_list:
                    download_cached_track(track_list[track], path_for_album, n)
                    n = n + 1

                xbmc.executebuiltin('XBMC.Notification(%s, %s, %s, %s)' % (str_by_lang('Album Downloaded'), title, 4000, args['image'][0]))
                set_iam_downloading('0')

        else:
            xbmc.executebuiltin('XBMC.Notification(%s, %s, %s, %s)' % (str_by_lang('Please wait'), str_by_lang('The previous download is still in progress...'), 4000, 'special://home/addons/plugin.video.noise/icon.png'))

    if args['type'][0] == 'tracklist':

        if get_iam_downloading() != '1':

            dialog = xbmcgui.Dialog().browse(0, str_by_lang('Choose a directory to save the Tracklist'), "music")
            if dialog != '':

                set_iam_downloading('1')

                title = base64.b64decode(args['title'][0])

                path_for_album = dialog + only_legal_chars(title)

                if os.path.isdir(path_for_album) == False:
                    os.mkdir(path_for_album)

                dbcur.execute("CREATE TABLE IF NOT EXISTS my_tracklist (tracklist TEXT, artist TEXT, title TEXT, image TEXT, duration INT, plot TEXT, added INT, UNIQUE(tracklist, artist, title, image));")
                dbcur.execute('SELECT * FROM my_tracklist WHERE tracklist = "' + args['id'][0] + '" ORDER BY added ASC')
                matches = dbcur.fetchall()
                n = 1

                for match in matches:
                    download_cached_track({'artist':match[1], 'name':match[2], 'time':match[4], 'info':base64.b64decode(match[5]), 'tracklist': args['id'][0]}, path_for_album, n)
                    n = n + 1
                
                xbmc.executebuiltin('XBMC.Notification(%s, %s, %s, %s)' % (str_by_lang('Tracklist Downloaded'), title, 4000, 'special://home/addons/plugin.video.noise/icon.png'))
                set_iam_downloading('0')

        else:
            xbmc.executebuiltin('XBMC.Notification(%s, %s, %s, %s)' % (str_by_lang('Please wait'), str_by_lang('The previous download is still in progress...'), 4000, 'special://home/addons/plugin.video.noise/icon.png'))


    if args['type'][0] == 'track':
        
        if get_iam_downloading() != '1':

            dialog = xbmcgui.Dialog().browse(0, str_by_lang('Choose a directory to save the Track'), "music")
            if dialog != '':

                set_iam_downloading('1')
        
                path_for_album = dialog

                if os.path.isdir(path_for_album) == False:
                    os.mkdir(path_for_album)

                download_track_item({'artist': args['artist'][0], 'name': args['name'][0]}, args['id_video'][0], path_for_album, 0, 1)

                xbmc.executebuiltin('XBMC.Notification(%s, %s, %s, %s)' % (str_by_lang('Track Downloaded'), args['artist'][0] + ' - ' + args['name'][0], 4000, args['image'][0]))
                set_iam_downloading('0')
        else:
            xbmc.executebuiltin('XBMC.Notification(%s, %s, %s, %s)' % (str_by_lang('Please wait'), str_by_lang('The previous download is still in progress...'), 4000, 'special://home/addons/plugin.video.noise/icon.png'))

elif mode[0] == 'folder':

    search_type = args['search_type'][0]

    if search_type == 'My Albums':
        dbcur.execute("CREATE TABLE IF NOT EXISTS my_albums (album_type TEXT, id TEXT, title TEXT, image TEXT, UNIQUE(album_type, id));")
        dbcon.commit()
        dbcur.execute("SELECT * FROM my_albums")
        matches = dbcur.fetchall()
        for match in matches:

            if match[3] == '':
                image = RESOURCES + 'album.png'
            else:
                image = match[3]

            commands = []
            
            scriptToRun = "special://home/addons/plugin.video.noise/resources/myAlbums.py"
            argsToSend = "?mode=delete&type=album&album_type=" + match[0] + "&id=" + match[1]
            commands.append(( str_by_lang('Delete from MY ALBUMS'), 'XBMC.RunScript(' + scriptToRun + ', ' + argsToSend + ')' ))

            cmd = 'XBMC.RunPlugin({})'.format(build_url({'mode': 'download', 'type':'album', 'album_type': match[0], 'id':match[1], 'image':image, 'title': base64.b64encode(match[2].replace('[*DQ*]', '"'))}))
            commands.append(( str_by_lang('Download Album'), cmd ))

            url = build_url({'mode': 'folder', 'search_type': 'album', 'url': match[1], 'album_type': match[0], 'image': image})
            li = xbmcgui.ListItem(match[2].replace('[*DQ*]', '"'), iconImage=image)
            li.setInfo(type="Video", infoLabels={"plot": match[2].replace('[*DQ*]', '"')})
            li.setArt({'fanart': image, 'thumb': image})
            li.addContextMenuItems(commands)
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
        xbmcplugin.endOfDirectory(addon_handle)

    if search_type == 'My Tracklists':

        url = build_url({'mode': 'add_tracklist'})
        li = xbmcgui.ListItem(str_by_lang('[B]Add New Tracklist[/B]'), iconImage=RESOURCES + 'tracklist.png')
        li.setInfo(type="Video", infoLabels={"plot": str_by_lang("[B]Add New Tracklist[/B]\nCreate a new Tracklist to start adding tracks to it.")})
        li.setArt({'fanart': RESOURCES + 'my_tracklists.jpg', 'thumb': RESOURCES+'tracklist.png'})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

        dbcur.execute("CREATE TABLE IF NOT EXISTS my_tracklists (name TEXT, UNIQUE(name));")
        dbcon.commit()
        dbcur.execute("SELECT * FROM my_tracklists")
        matches = dbcur.fetchall()
        for match in matches:

            commands = []
            scriptToRun = "special://home/addons/plugin.video.noise/resources/myTracklists.py"
            argsToSend = '?' + urllib.urlencode({'mode':'delete_list', 'tracklist': match[0]})
            commands.append(( str_by_lang('Delete this Tracklist'), 'XBMC.RunScript(' + scriptToRun + ', ' + argsToSend + ')' ))

            cmd = 'XBMC.RunPlugin({})'.format(build_url({'mode': 'download', 'type':'tracklist', 'id':match[0], 'title': base64.b64encode(match[0].replace('[*DQ*]', '"'))}))
            commands.append(( str_by_lang('Download Tracklist'), cmd ))

            url = build_url({'mode': 'folder', 'search_type': 'tracklist', 'tracklist_name': match[0]})
            li = xbmcgui.ListItem(match[0].replace('[*DQ*]', '"'), iconImage=RESOURCES+'tracklist.png')
            li.setInfo(type="Video", infoLabels={"plot": match[0].replace('[*DQ*]', '"')})
            li.setArt({'fanart': RESOURCES + 'my_tracklists.jpg', 'thumb': RESOURCES+'tracklist.png'})
            li.addContextMenuItems(commands)
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
        xbmcplugin.endOfDirectory(addon_handle)

    if search_type == 'tracklist':
        dbcur.execute("CREATE TABLE IF NOT EXISTS my_tracklist (tracklist TEXT, artist TEXT, title TEXT, image TEXT, duration INT, plot TEXT, added INT, UNIQUE(tracklist, artist, title, image));")
        dbcur.execute('SELECT * FROM my_tracklist WHERE tracklist = "' + args['tracklist_name'][0].replace('"', '[*DQ*]') + '" ORDER BY added ASC')
        matches = dbcur.fetchall()
        for match in matches:
            load_cached_track({'artist':match[1], 'name':match[2], 'time':match[4], 'info':base64.b64decode(match[5]), 'tracklist': args['tracklist_name'][0]}, match[3], 1)
        xbmcplugin.endOfDirectory(addon_handle)

    if search_type == 'styles':

        if args['sort'][0] == 'score':
            rq = cached_url(REMOTE_URL + 'styles.php', 1)
        else:
            rq = cached_url_m(REMOTE_URL + 'styles.php', 30)
        styles_list = json.loads(rq)
        for this_style in styles_list:
            url = build_url({'mode': 'folder', 'search_type': 'style', 'search_url': this_style['url'], 'page': '1', 'year':' ', 'sort': args['sort'][0]})
            li = xbmcgui.ListItem(this_style['style'] + ' (' + this_style['total'] + ')', iconImage=RESOURCES+'style.png')
            if args['sort'][0] == 'score':
                li.setInfo(type="Video", infoLabels={"plot": str_by_lang("Browse for the best albums in\n[B]") + this_style['style'] + "[/B]"})
                li.setArt({'fanart': RESOURCES + 'styles.jpg', 'thumb': RESOURCES + 'style.png'})
            else:
                li.setInfo(type="Video", infoLabels={"plot": str_by_lang("Browse for the latest albums in\n[B]") + this_style['style'] + "[/B]"})
                li.setArt({'fanart': RESOURCES + 'new_albums.jpg', 'thumb': RESOURCES + 'new.png'})
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
        xbmcplugin.endOfDirectory(addon_handle)


    elif search_type == 'style':
        search_url = args['search_url'][0]
        page = args['page'][0]
        year = args['year'][0]
        sort = args['sort'][0]

        showalbumsstyle(search_url, page, year, sort)

    elif search_type == 'album':
        album_url = args['url'][0]
        album_type = args['album_type'][0]
        if 'image' in args:
            image = args['image'][0]
        else:
            image = ''

        rq = cached_url(REMOTE_URL + 'album.php?id=' + album_url + '&type=' + album_type, 30)
        track_list = json.loads(rq)

        for track in track_list:

            load_cached_track(track_list[track], image, 0)

        xbmcplugin.endOfDirectory(addon_handle)

    elif search_type == 'artist':
        rq = cached_url(REMOTE_URL + 'artist.php?id=' + args['url'][0],1)
        return_list = json.loads(rq)
        for this_item in return_list:

            if this_item['image'] == '':
                this_item['image'] = RESOURCES + 'artist.png'

            info_name = plot_by_lang(this_item['name']).replace(' > ', '').replace('[B]','').replace('[/B]','').strip()
            info_text = str_by_lang("Browse for all the albums in:\n[B]") + info_name + "[/B]"
            url = build_url({'mode': 'folder', 'search_type': 'albums_artist', 'filtro': this_item['filter'], 'page': 1})
            li = xbmcgui.ListItem(plot_by_lang(this_item['name']) + ' [I](' + this_item['total'] + ')[/I]', iconImage=this_item['image'])
            li.setInfo(type="Video", infoLabels={"plot": info_text})
            li.setArt({'fanart': this_item['image'], 'thumb': this_item['image']})
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
        xbmcplugin.endOfDirectory(addon_handle)

    elif search_type == 'albums_artist':
        rq = cached_url(REMOTE_URL + 'albums_artist.php?page=' + args['page'][0] + '&filter=' + args['filtro'][0], 1)
        albums_list = json.loads(rq)
        for this_album in albums_list:
            if this_album['m_r'] == '':
                url = build_url({'mode': 'folder', 'search_type': 'albums_artist', 'filtro': args['filtro'][0], 'page': this_album['page']})
                li = xbmcgui.ListItem('[I]' + str_by_lang('Next Page') + '[/I]', iconImage=RESOURCES+'next.png')
                li.setInfo(type="Video", infoLabels={"plot": "[B]" + str_by_lang('Next Page') + " (" + str(this_album['page']) + ")[/B]"})
                li.setArt({'fanart': this_album['fanart'], 'thumb': RESOURCES+'next.png'})
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
            else:

                url = build_url({'mode': 'folder', 'search_type': 'album', 'url': this_album['id'], 'album_type': this_album['m_r'], 'image': this_album['big_image']})

                if this_album['big_image'] == '':
                    this_album['big_image'] = RESOURCES + 'album.png'

                commands = []
                scriptToRun = "special://home/addons/plugin.video.noise/resources/myAlbums.py"
                argsToSend = '?' + urllib.urlencode({'mode':'save', 'type':'album', 'album_type':this_album['m_r'], 'id':this_album['id'], 'image':this_album['big_image'], 'title':this_album['artist'] + ' - ' + this_album['title']})
                commands.append(( str_by_lang('Add to MY ALBUMS'), 'XBMC.RunScript(' + scriptToRun + ', ' + argsToSend + ')' ))

                cmd = 'XBMC.RunPlugin({})'.format(build_url({'mode': 'download', 'type':'album', 'album_type': this_album['m_r'], 'id':this_album['id'], 'image':this_album['big_image'], 'title': base64.b64encode(this_album['artist'] + ' - ' + this_album['title'])}))
                commands.append(( str_by_lang('Download Album'), cmd ))
                
                li = xbmcgui.ListItem(this_album['artist'] + ' - ' + this_album['title'], iconImage=this_album['big_image'])
                li.setInfo(type="Video", infoLabels={"plot": "[B]" + this_album['artist'] + " - " + this_album['title'] + "[/B]"})
                li.setArt({'fanart': this_album['big_image'], 'thumb': this_album['big_image']})
                li.addContextMenuItems(commands)
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
        xbmcplugin.endOfDirectory(addon_handle)

    elif search_type == 'albums_label':
        rq = cached_url(REMOTE_URL + 'albums_label.php?page=' + args['page'][0] + '&id=' + args['url'][0], 1)
        albums_list = json.loads(rq)
        
        for this_album in albums_list:
            
            if this_album['m_r'] == '':
                url = build_url({'mode': 'folder', 'search_type': 'albums_label', 'url': this_album['id'], 'page': this_album['page']})
                li = xbmcgui.ListItem('[I]' + str_by_lang('Next Page') + '[/I]', iconImage=RESOURCES+'next.png')
                li.setInfo(type="Video", infoLabels={"plot": "[B]" + str_by_lang('Next Page') + " (" + str(this_album['page']) + ")[/B]"})
                li.setArt({'fanart': this_album['fanart'], 'thumb': RESOURCES+'next.png'})
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
            else:
                url = build_url({'mode': 'folder', 'search_type': 'album', 'url': this_album['id'], 'album_type': this_album['m_r'], 'image': this_album['big_image']})

                if this_album['big_image'] == '':
                    this_album['big_image'] = RESOURCES + 'album.png'

                commands = []
                scriptToRun = "special://home/addons/plugin.video.noise/resources/myAlbums.py"
                argsToSend = '?' + urllib.urlencode({'mode':'save', 'type':'album', 'album_type':this_album['m_r'], 'id':this_album['id'], 'image':this_album['big_image'], 'title':this_album['artist'] + ' - ' + this_album['title']})
                commands.append(( str_by_lang('Add to MY ALBUMS'), 'XBMC.RunScript(' + scriptToRun + ', ' + argsToSend + ')' ))

                cmd = 'XBMC.RunPlugin({})'.format(build_url({'mode': 'download', 'type':'album', 'album_type': this_album['m_r'], 'id':this_album['id'], 'image':this_album['big_image'], 'title': base64.b64encode(this_album['artist'] + ' - ' + this_album['title'])}))
                commands.append(( str_by_lang('Download Album'), cmd ))
                
                li = xbmcgui.ListItem(this_album['artist'] + ' - ' + this_album['title'], iconImage=this_album['big_image'])
                li.setInfo(type="Video", infoLabels={"plot": "[B]" + this_album['artist'] + ' - ' + this_album['title'] + "[/B]"})
                li.setArt({'fanart': this_album['big_image'], 'thumb': this_album['big_image']})
                li.addContextMenuItems(commands)
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
        xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'search':

    search_type = args['search_type'][0].lower()

    url = build_url({'mode': 'new_search', 'search_type': search_type, 'search_page': '1', 'search_query': ' '})
    li = xbmcgui.ListItem('[B]' + str_by_lang('Search New') + ' ' + str_by_lang(search_type.capitalize()) + '[/B]', iconImage=RESOURCES + search_type + '.png')
    li.setInfo(type="Video", infoLabels={"plot": '[B]' + str_by_lang('Search New') + ' ' + str_by_lang(search_type.capitalize()) + '[/B]'})
    li.setArt({'fanart': RESOURCES + search_type + '.jpg'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    dbcur.execute("CREATE TABLE IF NOT EXISTS search (query TEXT, search_type TEXT, expiration TEXT, UNIQUE(query, search_type));")
    dbcon.commit()
    dbcur.execute("SELECT * FROM search WHERE search_type = '" + search_type + "' ORDER BY expiration DESC LIMIT 50")
    matches = dbcur.fetchall()

    for match in matches:

        commands = []
        scriptToRun = "special://home/addons/plugin.video.noise/resources/mySearch.py"
        argsToSend = '?' + urllib.urlencode({'mode':'delete', 'search_type':search_type, 'query': match[0].replace('[*DQ*]', '"')})
        commands.append(( str_by_lang('Remove search term'), 'XBMC.RunScript(' + scriptToRun + ', ' + argsToSend + ')' ))

        url = build_url({'mode': 'new_search', 'search_type': search_type, 'search_page': '1', 'search_query': match[0].replace('[*DQ*]', '"')})
        li = xbmcgui.ListItem(match[0].replace('[*DQ*]', '"'), iconImage=RESOURCES + search_type + '.png')
        li.setInfo(type="Video", infoLabels={"plot": str_by_lang("Search again for [B]\"") + match[0].replace('[*DQ*]', '"') + "\"[/B]"})
        li.setArt({'fanart': RESOURCES + search_type +'.jpg'})
        li.addContextMenuItems(commands)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)


    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'new_search':

    search_page = args['search_page'][0]

    if not args['search_query']:
        search_query = ' '
    else:
        search_query = args['search_query'][0]

    if search_query != ' ':
        search_string = search_query
    else:
        if search_page == '1':
            search_string = getusersearch(args['search_type'][0].lower())
        else:
            search_string = args['search_query'][0]

    if search_string != '':

        rq = cached_url(REMOTE_URL + 'search_' + args['search_type'][0].lower() + '.php?query=' + search_string + '&page=' + search_page, 1)

        dbcur.execute("CREATE TABLE IF NOT EXISTS search (query TEXT, search_type TEXT, expiration TEXT, UNIQUE(query, search_type));")
        dbcon.commit()
        dbcur.execute('SELECT * FROM search WHERE search_type = "' + args['search_type'][0].lower() + '" AND query = "' + search_string.replace('"', '[*DQ*]') + '"')
        match = dbcur.fetchone()
        if match == None:
            dbcur.execute('INSERT INTO search VALUES("' + search_string.replace('"', '[*DQ*]') + '","' + args['search_type'][0].lower() + '","' + datetime.now().strftime("%Y%m%d%H%M%S") + '")')
            dbcon.commit()
            xbmc.executebuiltin("Container.Refresh")
        else:
            dbcur.execute('UPDATE search SET expiration = "' + datetime.now().strftime("%Y%m%d%H%M%S") + '" WHERE search_type = "' + args['search_type'][0].lower() + '" AND query = "' + search_string.replace('"', '[*DQ*]') + '"')
            dbcon.commit()
            xbmc.executebuiltin("Container.Refresh")

        return_list = json.loads(rq)

        for this_item in return_list:

            if args['search_type'][0] == 'album':
                if this_item['page'] == '':

                    if this_item['img'] == '':
                        this_item['img'] = RESOURCES + 'album.png'

                    commands = []
                    scriptToRun = "special://home/addons/plugin.video.noise/resources/myAlbums.py"
                    argsToSend = '?' + urllib.urlencode({'mode':'save', 'type':'album', 'album_type':'release', 'id':this_item['url'], 'image':this_item['img'], 'title':this_item['title']})
                    commands.append(( str_by_lang('Add to MY ALBUMS'), 'XBMC.RunScript(' + scriptToRun + ', ' + argsToSend + ')' ))

                    cmd = 'XBMC.RunPlugin({})'.format(build_url({'mode': 'download', 'type':'album', 'album_type': 'release', 'id':this_item['url'], 'image':this_item['img'], 'title': base64.b64encode(this_item['title'])}))
                    commands.append(( str_by_lang('Download Album'), cmd ))

                    url = build_url({'mode': 'folder', 'search_type': args['search_type'][0].lower(), 'url': this_item['url'], 'album_type': 'release', 'image': this_item['img']})
                    li = xbmcgui.ListItem(this_item['title'], iconImage=this_item['img'])
                    li.setInfo(type="Video", infoLabels={"plot": "[B]" + this_item['title'] + "[/B]"})
                    li.setArt({'fanart': this_item['img'], 'thumb': this_item['img']})
                    li.addContextMenuItems(commands)
                else:
                    url = build_url({'mode': 'new_search', 'search_type': args['search_type'][0].lower(), 'search_query': search_string, 'search_page': this_item['page']})
                    li = xbmcgui.ListItem('[I]' + str_by_lang('Next Page') + '[/I]', iconImage=RESOURCES+'next.png')
                    li.setInfo(type="Video", infoLabels={"plot": "[B]" + str_by_lang('Next Page') + " (" + str(this_item['page']) + ")[/B]"})
                    li.setArt({'fanart': RESOURCES + args['search_type'][0] + '.jpg', 'thumb': RESOURCES+'next.png'})
                    
            elif args['search_type'][0] == 'artist':
                if this_item['page'] == '':

                    if this_item['img'] == '':
                        this_item['img'] = RESOURCES + 'artist.png'

                    url = build_url({'mode': 'folder', 'search_type': args['search_type'][0].lower(), 'url': this_item['url']})
                    li = xbmcgui.ListItem(this_item['title'], iconImage=this_item['img'])
                    li.setInfo(type="Video", infoLabels={"plot": "[B]" + this_item['title'] + "[/B]"})
                    li.setArt({'fanart': this_item['img'], 'thumb': this_item['img']})
                else:
                    url = build_url({'mode': 'new_search', 'search_type': args['search_type'][0].lower(), 'search_query': search_string, 'search_page': this_item['page']})
                    li = xbmcgui.ListItem('[I]' + str_by_lang('Next Page') + '[/I]', iconImage=RESOURCES+'next.png')
                    li.setInfo(type="Video", infoLabels={"plot": "[B]" + str_by_lang('Next Page') + " (" + str(this_item['page']) + ")[/B]"})
                    li.setArt({'fanart': RESOURCES + args['search_type'][0] + '.jpg', 'thumb': RESOURCES+'next.png'})
                    
            elif args['search_type'][0] == 'label':
                if this_item['page'] == '':

                    if this_item['img'] == '':
                        this_item['img'] = RESOURCES + 'label.png'

                    url = build_url({'mode': 'folder', 'search_type': 'albums_label', 'url': this_item['url'], 'page': 1})
                    li = xbmcgui.ListItem(this_item['title'], iconImage=this_item['img'])
                    li.setInfo(type="Video", infoLabels={"plot": "[B]" + this_item['title'] + "[/B]"})
                    li.setArt({'fanart': this_item['img'], 'thumb': this_item['img']})
                else:
                    url = build_url({'mode': 'new_search', 'search_type': args['search_type'][0].lower(), 'search_query': search_string, 'search_page': this_item['page']})
                    li = xbmcgui.ListItem('[I]' + str_by_lang('Next Page') + '[/I]', iconImage=RESOURCES+'next.png')
                    li.setInfo(type="Video", infoLabels={"plot": "[B]" + str_by_lang('Next Page') + " (" + str(this_item['page']) + ")[/B]"})
                    li.setArt({'fanart': RESOURCES + args['search_type'][0] + '.jpg', 'thumb': RESOURCES+'next.png'})

            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
        xbmcplugin.endOfDirectory(addon_handle)