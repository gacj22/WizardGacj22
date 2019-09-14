# -*- coding: utf-8 -*-
import xbmc

from core.libs import *


def run_rpc(payload):
    logger.trace()
    try:
        data = jsontools.load_json(xbmc.executeJSONRPC(jsontools.dump_json(payload)))
    except Exception:
        logger.error()
        return ["error"]

    return data


def update(path=''):
    logger.trace()

    payload = {
        "jsonrpc": "2.0",
        "method": "VideoLibrary.Scan",
        "id": 1,
        "directory": path
    }

    while xbmc.getCondVisibility('Library.IsScanningVideo()'):
        xbmc.sleep(500)

    run_rpc(payload)


def clean(mostrar_dialogo=False):
    """
    limpia la libreria de elementos que no existen
    @param mostrar_dialogo: muestra el cuadro de progreso mientras se limpia la biblioteca
    @type mostrar_dialogo: bool
    """
    logger.info()
    payload = {"jsonrpc": "2.0", "method": "VideoLibrary.Clean", "id": 1,
               "params": {"showdialogs": mostrar_dialogo}}
    data = run_rpc(payload)

    if data.get('result', False) == 'OK':
        return True

    return False


def search_path_db(path):
    path = filetools.normalize_dir(path)

    sql = 'SELECT strPath FROM path WHERE strPath LIKE "%s"' % path
    nun_records, records = execute_sql_kodi(sql)
    if nun_records >= 1:
        logger.debug(records[0][0])
        return records[0][0]
    return None


def add_path_db(path, **kwargs):
    logger.trace()

    # Buscamos el idPath
    if not kwargs.get('idPath'):
        nun_records, records = execute_sql_kodi('SELECT MAX(idPath) FROM path')
        if nun_records == 1:
            kwargs['idPath'] = records[0][0] + 1
        else:
            kwargs['idPath'] = 0

    # Buscamos el idParentPath
    sql = 'SELECT idPath, strPath FROM path where strPath LIKE "%s"' % filetools.normalize_dir(filetools.dirname(path))
    nun_records, records = execute_sql_kodi(sql)
    if nun_records == 1:
        kwargs['idParentPath'] = records[0][0]

    else:
        sql = 'INSERT INTO path (idPath, strPath,  scanRecursive, useFolderNames, noUpdate, exclude) VALUES ' \
              '(%s, "%s", 0, 0, 0, 0)' % (kwargs['idPath'], filetools.normalize_dir(filetools.dirname(path)))
        execute_sql_kodi(sql)
        kwargs['idParentPath'] = kwargs['idPath']
        kwargs['idPath'] += 1

    kwargs['strPath'] = filetools.normalize_dir(path)
    sql = 'INSERT INTO path (%s) VALUES (%s)' % (
        ', '.join(kwargs.keys()),
        ', '.join(['"%s"' % v for v in kwargs.values()])
    )
    execute_sql_kodi(sql)


def execute_sql_kodi(sql):
    """
    Ejecuta la consulta sql contra la base de datos de kodi
    @param sql: Consulta sql valida
    @type sql: str
    @return: Numero de registros modificados o devueltos por la consulta
    @rtype nun_records: int
    @return: lista con el resultado de la consulta
    @rtype records: list of tuples
    """
    logger.trace()

    nun_records = 0
    records = None
    conn = None

    file_db = filter(
        lambda x: x.startswith('MyVideos'),
        os.listdir(xbmc.translatePath("special://userdata/Database"))
    )[0]

    file_db = os.path.join(xbmc.translatePath("special://userdata/Database"), file_db)

    try:
        import sqlite3
        conn = sqlite3.connect(file_db)
        cursor = conn.cursor()

        logger.info("Ejecutando sql: %s" % sql)
        cursor.execute(sql)
        conn.commit()

        records = cursor.fetchall()
        if sql.lower().startswith("select"):
            nun_records = len(records)
            if nun_records == 1 and records[0][0] is None:
                nun_records = 0
                records = []
        else:
            nun_records = conn.total_changes

        conn.close()
        logger.info("Consulta ejecutada. Registros: %s" % nun_records)

    except Exception:
        logger.error()
        if conn:
            conn.close()

    return nun_records, records


def get_video_sources():
    logger.trace()
    from xml.dom import minidom

    sources_path = xbmc.translatePath("special://userdata/sources.xml")

    if not os.path.exists(sources_path):
        return []

    xmldoc = minidom.parse(sources_path)
    video = xmldoc.childNodes[0].getElementsByTagName("video")[0]
    paths = video.getElementsByTagName("path")
    return [p.firstChild.data for p in paths]


def add_video_source(path, name):
    logger.trace()
    from xml.dom import minidom

    name = unicode(name, 'utf8')

    sources_path = xbmc.translatePath("special://userdata/sources.xml")

    if os.path.exists(sources_path):
        xmldoc = minidom.parse(sources_path)
    else:
        # Crear documento
        xmldoc = minidom.Document()
        nodo_sources = xmldoc.createElement("sources")

        for t in ['programs', 'video', 'music', 'picture', 'files']:
            nodo_type = xmldoc.createElement(t)
            element_default = xmldoc.createElement("default")
            element_default.setAttribute("pathversion", "1")
            nodo_type.appendChild(element_default)
            nodo_sources.appendChild(nodo_type)
        xmldoc.appendChild(nodo_sources)

    # Buscamos el nodo video
    nodo_video = xmldoc.childNodes[0].getElementsByTagName("video")[0]

    # Buscamos el path dentro de los nodos_path incluidos en el nodo_video
    nodos_paths = nodo_video.getElementsByTagName("path")
    list_path = [p.firstChild.data for p in nodos_paths]
    logger.debug(list_path)
    if path in list_path:
        logger.debug("La ruta %s ya esta en sources.xml" % path)
        return
    logger.debug("La ruta %s NO esta en sources.xml" % path)

    # Si llegamos aqui es por q el path no esta en sources.xml, asi q lo incluimos
    nodo_source = xmldoc.createElement("source")

    # Nodo <name>
    nodo_name = xmldoc.createElement("name")
    nodo_name.appendChild(xmldoc.createTextNode(name))
    nodo_source.appendChild(nodo_name)

    # Nodo <path>
    nodo_path = xmldoc.createElement("path")
    nodo_path.setAttribute("pathversion", "1")
    nodo_path.appendChild(xmldoc.createTextNode(path))
    nodo_source.appendChild(nodo_path)

    # Nodo <allowsharing>
    nodo_allowsharing = xmldoc.createElement("allowsharing")
    nodo_allowsharing.appendChild(xmldoc.createTextNode('true'))
    nodo_source.appendChild(nodo_allowsharing)

    # Añadimos <source>  a <video>
    nodo_video.appendChild(nodo_source)

    # Guardamos los cambios
    filetools.write(sources_path,
                    '\n'.join([x for x in xmldoc.toprettyxml().encode("utf-8").splitlines() if x.strip()]))


def media_viewed_set(item, value):
    logger.trace()

    if item.type == 'movie':
        payload = {"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies",
                   "params": {"properties": ["uniqueid"], },
                   "id": 1}

        data = run_rpc(payload)
        for d in data.get('result', {}).get('movies', []):
            if d.get('uniqueid', {}).get('imdb', '') == item.code:
                payload_f = {"jsonrpc": "2.0", "method": "VideoLibrary.SetMovieDetails", "params": {
                    "movieid": d['movieid'], "playcount": int(value)}, "id": 1}
                run_rpc(payload_f)
                break

    if item.type == 'episode':
        payload = {"jsonrpc": "2.0", "method": "VideoLibrary.GetTvshows",
                   "params": {"properties": ["uniqueid"]},
                   "id": 1}

        data = run_rpc(payload)

        for tv in data.get('result', {}).get('tvshows', []):
            if tv.get('uniqueid', {}).get('tmdb', '') == item.tmdb_id:
                continue

            payload_episode = {"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes",
                               "params": {"properties": ["season", "episode"], },
                               "id": 1, "tvshowid": tv['tvshowid']}

            data = run_rpc(payload_episode)
            for ep in data.get('result', {}).get('episodes', []):
                if not ep['episode'] == item.episode or not ep['season'] == item.season:
                    continue

                payload_f = {"jsonrpc": "2.0", "method": "VideoLibrary.SetEpisodeDetails", "params": {
                    "episodeid": ep['episodeid'], "playcount": int(value)}, "id": 1}
                run_rpc(payload_f)
                break
            break


def integrate():
    logger.trace()
    from core import library

    if not platformtools.dialog_yesno(
            'MediaExplorer',
            'Se va a proceder a configurar la biblioteca de Kodi',
            'Se añadiran las fuentes y se configurará el tipo de contenido',
            'Es necesario reiniciar Kodi al terminar',
            yeslabel='Continuar',
            nolabel='Cancelar'
    ):
        return False

    videos_path = filetools.join(
        settings.get_setting('library_path', library.__file__),
        settings.get_setting('library_videos_folder', library.__file__)
    )

    movies_path = filetools.join(
        settings.get_setting('library_path', library.__file__),
        settings.get_setting('library_movies_folder', library.__file__)
    )

    tvshows_path = filetools.join(
        settings.get_setting('library_path', library.__file__),
        settings.get_setting('library_tvshows_folder', library.__file__)
    )

    filetools.makedirs(videos_path)
    filetools.makedirs(movies_path)
    filetools.makedirs(tvshows_path)

    sources = get_video_sources()

    if videos_path not in sources:
        add_video_source(videos_path, 'MediaExplorer: Vídeos')

    if movies_path not in sources:
        add_video_source(movies_path, 'MediaExplorer: Películas')

    if tvshows_path not in sources:
        add_video_source(tvshows_path, 'MediaExplorer: Series')

    if not search_path_db(movies_path):
        if not xbmc.getCondVisibility('System.HasAddon(metadata.themoviedb.org)'):
            xbmc.executebuiltin('xbmc.installaddon(metadata.themoviedb.org)', True)

        if not xbmc.getCondVisibility('System.HasAddon(metadata.themoviedb.org)'):
            platformtools.dialog_ok('MediaExplorer', 'No se ha podido instalar')
            return False

        add_path_db(movies_path, **{
            'strContent': 'movies',
            'strScraper': 'metadata.themoviedb.org',
            'scanRecursive': 2147483647,
            'strSettings': "<settings><setting id='RatingS' value='TMDb' /><setting id='certprefix' value='Rated ' />"
                           "<setting id='fanart' value='true' /><setting id='keeporiginaltitle' value='false' />"
                           "<setting id='language' value='es' /><setting id='tmdbcertcountry' value='us' />"
                           "<setting id='trailer' value='true' /></settings>",
            'useFolderNames': 1,
            'noUpdate': 0,
            'exclude': 0,

        })

    if not search_path_db(tvshows_path):
        if not xbmc.getCondVisibility('System.HasAddon(metadata.tvshows.themoviedb.org)'):
            xbmc.executebuiltin('xbmc.installaddon(metadata.tvshows.themoviedb.org)', True)

        if not xbmc.getCondVisibility('System.HasAddon(metadata.tvshows.themoviedb.org)'):
            platformtools.dialog_ok('MediaExplorer', 'No se ha podido instalar')
            return False

        add_path_db(tvshows_path, **{
            'strContent': 'tvshows',
            'strScraper': 'metadata.tvshows.themoviedb.org',
            'scanRecursive': 0,
            'strSettings': "<settings><setting id='fanart' value='true' />"
                           "<setting id='keeporiginaltitle' value='false' />"
                           "<setting id='language' value='es' /></settings>",
            'useFolderNames': 0,
            'noUpdate': 0,
            'exclude': 0,
        })

    return True
