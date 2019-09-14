# -*- coding: utf-8 -*-
from core.libs import *
import sqlite3
import base64

FILE_DB = os.path.join(sysinfo.data_path, 'mediaexplorer.db')


def create():
    if not os.path.exists(FILE_DB):
        conn = sqlite3.connect(FILE_DB)
        cursor = conn.cursor()
        # Añadir a partir de aqui la estructura de la BBDD

        # Crear tabla SCRAPER_CACHE
        cursor.execute('''CREATE TABLE SCRAPER_CACHE
                    (ID CHAR(32) PRIMARY KEY NOT NULL,
                    DATA TEXT,
                    LIMIT_TIME FLOAT)''')

        # Crear tabla MEDIA_VIEWED
        cursor.execute('''CREATE TABLE MEDIA_VIEWED
                        (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                        IMDB_ID CHAR(12), 
                        TMDB_ID CHAR(12),
                        TVDB_ID CHAR(12),
                        SEASON_EPISODE CHAR(12))        
                        ''')

        # Crear tabal PROPIEDADES
        cursor.execute('''CREATE TABLE PROPIEDADES
                        (VERSION INTEGER) 
                        ''')
        cursor.execute('''INSERT INTO PROPIEDADES (VERSION) VALUES (5)''')

        conn.close()


def connect_DB(text_factory = bytes):
    def _connect_DB(func):
        def _connect(*args, **kwargs):
            retval = None
            conn = sqlite3.connect(FILE_DB)
            cursor = conn.cursor()

            try:
                conn.text_factory = text_factory
                retval = func(cursor, *args, **kwargs)
                conn.commit()
            except:
                conn.rollback()
                logger.error()

            finally:
                conn.close()

            return retval

        _connect.__name__ = func.__name__
        _connect.__doc__ = func.__doc__

        return _connect

    return _connect_DB


@connect_DB()
def scraper_cache_insert_old(cursor, cache):
    logger.trace()
    if cache:
        for k,v in cache.items():
            total_results = re.findall('"total_results":(\d+)', v['data'])
            if total_results and int(total_results[0]) > 1:
                cache[k]['data'] = jsontools.dump_json({'total_results': 1, 'total_pages': 1, 'page': 1,
                                                'results': [jsontools.load_json(v['data'])['results'][0]]})

        values = [(k,v['limit_time'], str(base64.b64encode(jsontools.dump_json(v['data'])))) for k, v in cache.items()]
        sql = "INSERT OR IGNORE INTO SCRAPER_CACHE (ID,LIMIT_TIME, DATA) VALUES (?, ?, ?)"
        cursor.executemany(sql, values)


@connect_DB()
def scraper_cache_insert(cursor, cache):
    logger.trace()
    # MAX_RESULTADOS = Maximo numero de resultados a almacenar en la BBDD por cada busqueda.
    # Si una busqueda devuelve mas de un resultado solo almacenaremos en la BBDD MAX_RESULTADOS.
    MAX_RESULTADOS = 5
    if cache:
        for k in cache.keys():
            if not cache[k].has_key('limit_time'):
                del cache[k]
                continue

            results = jsontools.load_json(cache[k]['data']).get('results', [])
            if not results:
                del cache[k]

            elif len(results) > MAX_RESULTADOS:
                cache[k]['data'] = jsontools.dump_json(
                    {'total_results': MAX_RESULTADOS,
                     'total_pages': 1,
                     'page': 1,
                     'results': results[:MAX_RESULTADOS]})

        values = [(k, v.pop('limit_time'), str(base64.b64encode(jsontools.dump_json(v))))for k, v in cache.items()]
        sql = "INSERT OR IGNORE INTO SCRAPER_CACHE (ID,LIMIT_TIME, DATA) VALUES (?, ?, ?)"
        cursor.executemany(sql, values)


@connect_DB()
def scraper_cache_get(cursor, cache_id, item_type):
    # Busca cache_id en la tabla y devuelve su valor o None
    logger.trace()
    cursor.execute("SELECT DATA FROM SCRAPER_CACHE WHERE ID = ?", [cache_id])
    res = cursor.fetchone()

    if res:
        return jsontools.load_json(base64.b64decode(res[0]))


@connect_DB()
def scraper_cache_clear(cursor):
    # Consultamos la version de la BBDD
    cursor.execute("CREATE TABLE IF NOT EXISTS PROPIEDADES (VERSION INTEGER)")
    cursor.execute("SELECT VERSION FROM PROPIEDADES")
    res = cursor.fetchone()

    if not res or int(res[0]) < 5:
        # Si la version de la BBDD es anterior a la 5 adaptarla
        cursor.execute("DROP TABLE SCRAPER_CACHE")
        cursor.execute('''CREATE TABLE SCRAPER_CACHE 
                        (ID CHAR(32) PRIMARY KEY NOT NULL,
                        DATA TEXT,
                        LIMIT_TIME FLOAT)''')
        cursor.execute('''INSERT INTO PROPIEDADES (VERSION) VALUES (5)''')
        logger.debug("La version de la BBDD ha sido actualizada")

    # Eliminar los registros caducados de la tabla SCRAPER_CACHE
    cursor.execute("DELETE FROM SCRAPER_CACHE WHERE LIMIT_TIME < %s" % time.time())

    # Limitar el numero de registros de la tabla SCRAPER_CACHE
    MAX_ROW = 5000
    cursor.execute("DELETE FROM SCRAPER_CACHE WHERE rowid NOT IN "
                   "(select rowid from scraper_cache order by rowid DESC LIMIT %s)" % MAX_ROW)


@connect_DB()
def media_viewed_set(cursor, item):
    logger.trace()
    res = None
    codes = get_codes(item)

    # Si no tenemos ningun identificador valido salimos sin marcar
    if not codes['values']:
        return

    where = "SEASON_EPISODE = '%s' AND (%s)" % (codes['season_episode'], " OR ".join(["%s = %s" % v for v in codes['values']]))
    sql = "SELECT ID, IMDB_ID, TMDB_ID, TVDB_ID, SEASON_EPISODE FROM MEDIA_VIEWED WHERE %s" % where
    cursor.execute(sql)
    res = cursor.fetchone()

    # Si no existe el registro añadirlo
    if not res:
        columns = ", ".join([v[0] for v in codes['values']])
        values = ", ".join([v[1] for v in codes['values']])

        sql = "INSERT INTO MEDIA_VIEWED (ID, %s, SEASON_EPISODE) VALUES (NULL, %s, '%s')" % \
              (columns, values, codes['season_episode'])
        cursor.execute(sql)

    # El registro existe, pero hay nuevos codigos. Actualizar con los codigos nuevos
    elif res[1] != codes['imdb'] or res[2] != codes['tmdb'] or res[3] != codes['tvdb']:
        set = ", ".join(["%s = %s" % v for v in codes['values']])
        sql = "UPDATE MEDIA_VIEWED SET %s WHERE ID = %s" % (set, res[0])
        cursor.execute(sql)

    if sysinfo.platform_name == 'kodi':
        from platformcode import library_tools
        library_tools.media_viewed_set(item, True)


@connect_DB()
def media_viewed_is_viewed(cursor, item):
    logger.trace()
    codes = get_codes(item)

    # Si no tenemos ningun identificador devolvemos False
    if not codes['values']:
        return False

    where = "SEASON_EPISODE = '%s' AND (%s)" % (codes['season_episode'], " OR ".join(["%s = %s" % v for v in codes['values']]))
    sql = "SELECT ID, IMDB_ID, TMDB_ID, TVDB_ID, SEASON_EPISODE FROM MEDIA_VIEWED WHERE %s" % where
    cursor.execute(sql)
    return cursor.fetchone() != None


@connect_DB()
def media_viewed_del(cursor, item):
    logger.trace()
    codes = get_codes(item)

    # Si no tenemos ningun identificador valido salimos sin marcar
    if not codes['values']:
        return

    where = "SEASON_EPISODE = '%s' AND (%s)" % (codes['season_episode'], " OR ".join(["%s = %s" % v for v in codes['values']]))
    sql = "DELETE FROM MEDIA_VIEWED WHERE %s" % where
    cursor.execute(sql)

    if sysinfo.platform_name == 'kodi':
        from platformcode import library_tools
        library_tools.media_viewed_set(item, False)


def get_codes(item):
    imdb = tmdb = tvdb = None
    values = []

    if item.code:  # code == imdb_id
        values.append(("IMDB_ID", "'%s'" % item.code))
        imdb = str(item.code)

    if item.tmdb_id:
        values.append(("TMDB_ID", "'%s'" % item.tmdb_id))
        tmdb = str(item.tmdb_id)

    if item.tvbd_id:
        values.append(("TVDB_ID", "'%s'" % item.tvbd_id))
        tvdb = str(item.tvbd_id)

    season_episode = "%dx%02d" % (item.season, item.episode) if isinstance(item.season, int) and \
                                                                isinstance(item.episode, int) else ""

    return {'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb, 'values': values, 'season_episode': season_episode}

