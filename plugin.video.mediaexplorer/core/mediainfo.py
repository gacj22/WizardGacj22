# -*- coding: utf-8 -*-
import hashlib

from core import bbdd
from core.libs import *

MAX_CONCURRENT_THREADS = 40
TEMP_DATA_CACHE = {}
lock = Lock()


def get_movie_info(item, extended=True, ask=False):
    """
    Busca la información de una película
    :param item: item sobre el que hay que buscar
    :param extended: Indica si se tiene que obtener la información detallada (más lento)
    :param ask: Indica si se ha de preguntar en caso de obtener varios resultados posibles
    """
    logger.trace()

    # Nos aseguramos que el item sea una película
    assert item.type == 'movie'

    # Cargamos el scraper con la configuración para peliculas
    mi = MediaInfo(MediaInfo.movie_services[settings.get_setting('movie_scrapper', "platformcode/viewtools")])

    # Si no hay que preguntar o si la búsqueda ha devuelto un resultado búscamos los datos
    if not ask or mi.search(item, ask):
        data = mi.get_media_info(item, extended)
        item.__dict__.update(data)


def get_tvshow_info(item, extended=True, ask=False):
    """
        Busca la información de una serie
        :param item: item sobre el que hay que buscar
        :param extended: Indica si se tiene que obtener la información detallada (más lento)
        :param ask: Indica si se ha de preguntar en caso de obtener varios resultados posibles
        """
    logger.trace()

    # Nos aseguramos que el item sea una serie
    assert item.type == 'tvshow'

    # Cargamos el scraper con la configuración para series
    mi = MediaInfo(MediaInfo.tvshow_services[settings.get_setting('tvshow_scrapper', "platformcode/viewtools")])

    # Si no hay que preguntar o si la búsqueda ha devuelto un resultado búscamos los datos
    if not ask or mi.search(item, ask):
        data = mi.get_media_info(item, extended)
        item.__dict__.update(data)


def get_episode_info(item, extended=True, ask=False):
    """
            Busca la información de un episodio
            :param item: item sobre el que hay que buscar
            :param extended: Indica si se tiene que obtener la información detallada (más lento)
            :param ask: Indica si se ha de preguntar en caso de obtener varios resultados posibles
            """
    logger.trace()

    # Nos aseguramos que el item sea un episodio
    assert item.type == 'episode'

    # Cargamos el scraper con la configuración para series
    mi = MediaInfo(MediaInfo.tvshow_services[settings.get_setting('tvshow_scrapper', "platformcode/viewtools")])

    # Si no hay que preguntar o si la búsqueda ha devuelto un resultado búscamos los datos
    if not ask or mi.search(item, ask):
        data = mi.get_media_info(item, extended)
        item.__dict__.update(data)


def get_season_info(item, extended=True, ask=False):
    """
    Busca la información de una temporada
    :param item: item sobre el que hay que buscar
    :param extended: Indica si se tiene que obtener la información detallada (más lento)
    :param ask: Indica si se ha de preguntar en caso de obtener varios resultados posibles
    """
    logger.trace()

    # Nos aseguramos que el item sea una temporada
    assert item.type == 'season'

    # Cargamos el scraper con la configuración para series
    mi = MediaInfo(MediaInfo.tvshow_services[settings.get_setting('tvshow_scrapper', "platformcode/viewtools")])

    # Si no hay que preguntar o si la búsqueda ha devuelto un resultado búscamos los datos
    if not ask or mi.search(item, ask):
        data = mi.get_media_info(item, extended)
        item.__dict__.update(data)


def get_itemlist_info(itemlist, extended=False, ask=False):
    logger.trace()
    global TEMP_DATA_CACHE
    threads = []

    s_items = [i for i in itemlist if i.type in ('movie', 'tvshow', 'season', 'episode')]
    max_size_list_info = settings.get_setting("max_size_list_info", "platformcode/viewtools", True)
    s_items = s_items[:int(max_size_list_info)] if max_size_list_info and max_size_list_info != 'Sin límites' else s_items

    if s_items:
        for item in s_items:
            if item.type == 'movie':
                t = Thread(target=get_movie_info, args=[item, extended, ask])
            if item.type == 'tvshow':
                t = Thread(target=get_tvshow_info, args=[item, extended, ask])
            if item.type == 'season':
                t = Thread(target=get_season_info, args=[item, extended, ask])
            if item.type == 'episode':
                t = Thread(target=get_episode_info, args=[item, extended, ask])

            t.setDaemon(True)
            t.start()
            threads.append(t)
            yield len(filter(lambda x: not x.isAlive(), threads)), len(s_items)

            # Para no colapsar el sistema los buscamos en grupos de maximo MAX_CONCURRENT_THREADS
            while len(filter(lambda x: x.isAlive(), threads)) > MAX_CONCURRENT_THREADS:
                yield len(filter(lambda x: not x.isAlive(), threads)), len(s_items)
                time.sleep(0.1)

        while filter(lambda x: x.isAlive(), threads):
            yield len(filter(lambda x: not x.isAlive(), threads)), len(s_items)
            time.sleep(0.1)
        if len(s_items):
            yield len(filter(lambda x: not x.isAlive(), threads)), len(s_items)

        # Guardamos la cache en la BBDD
        #logger.debug(TEMP_DATA_CACHE)
        bbdd.scraper_cache_insert(TEMP_DATA_CACHE)

        # Fix para mediaserver, hay que tener cuidado con las variables globales ya que en mediaserver no se resetean a
        # cada peticion, y en este caso la funcion scraper_cache_insert hace un base64 encode que se queda guardado en
        # la variable global modificando los datos y haciendo que falle, por eso la reseteo aqui de meomento, pero los
        # mejor seria modificar la funcion para que el encode no afecte a la variable global haciendo una copia del
        # diccionario antes de tocar los dadtos.
        TEMP_DATA_CACHE = {}


class Label:
    def __init__(self, value):
        self.value = value


# Base class
class MediaInfo(object):
    movie_services = ['TMDb']
    tvshow_services = ['TMDb'] # , 'TVDb']

    def __new__(cls, service):
        """
        incializamos la subclase segun el scraper solicitado
        """
        if service:
            return object.__new__(type(cls.__name__, (getattr(sys.modules[__name__], service), MediaInfo), {}))
        else:
            return object.__new__(type(cls.__name__, (MediaInfo,), {}))

    def __init__(self, *args, **kwargs):
        """
        Inicializamos los parametros
        :param args:
        :param kwargs:
        """
        self.raw_results = []
        self.raw_result = {"search": {}, "movie": {}, "tvshow": {}, "season": {}, "episode": {}}
        self.running_threads = []
        self.item = None

    @property
    def results(self):
        """
        Devuelve la cantidad de resultados
        :return:
        """
        return len(self.raw_results)

    def set_result(self, index):
        """
        Fija cual del los resultados vamos a usar
        :param index:
        :return:
        """
        self.raw_result["search"] = self.raw_results[index]
        self.raw_result["movie"] = {}
        self.raw_result["tvshow"] = {}
        self.raw_result["season"] = {}
        self.raw_result["episode"] = {}

    def search(self, item, ask=True):
        """
        Realiza una busqueda en el servicio configurado
            - Si no hay resultados devuelve False
            - Si hay resultados:
                - Si solo hay uno devuelve True y fija el unico resultado como activo
                - Si hay mas de uno:
                    - Si ask = True deja elejir que resultado fijar
                    - Si ask = False fija el primer resultado como activo
        :param item: Item sobre el que buscar información
        :param ask: Especifica si se debe o no preguntar en caso de encotrar varios resultados
        :return: True/False si hay o no resultados
        """
        self.item = item
        self._search()

        if self.results > 1:
            if ask:
                itemlist = []

                for x in range(self.results):
                    self.set_result(x)
                    data = self.get_media_info(item, False)
                    itemlist.append(Item(type=item.type, **data))

                index = platformtools.show_info(itemlist, title='Elige la película correcta')

                if index is None:
                    return False

                self.set_result(index)
            else:
                return True

        if self.results == 0:
            return False

        return True

    def get_media_info(self, item, extended=True):
        """
        Busca la información (en caso de no haber llamado la funcion search() anterirormente) y devuelve la información
        encotrada para ese item.
        :param item: Item sobre el que buscar información
        :param extended: Si extended es True busca información extendida (mas lento si son muchos items) puede variar
                         el funcionamiento segun el serivcio escogido
        :return: Diccionario con los datos obtenidos
        """
        self.item = item

        if not self.raw_result["search"]:
            self._search()
            if not self.results:
                return {}

        if item.type == "movie":
            return self.get_movie_info(extended)

        elif item.type == "tvshow":
            return self.get_tvshow_info(extended)

        elif item.type == "season":
            return self.get_season_info(extended)

        elif item.type == "episode":
            return self.get_episode_info(extended)

    def _create_data(self):
        """
        Crea el diccionario con los datos segun los resultados.
        :return:
        """
        data = {}
        for prop in dir(self):
            val = getattr(self, prop)
            if isinstance(val, Label):
                try:
                    ressult = val.value(self)
                    if ressult:
                        data[prop] = ressult
                except Exception:
                    continue

        return data

    def _threaded_request_api(self, url, post=None, key=None, dest=None, t=False):
        """
        Ejecuta la API de forma asincorónica
        :param url: Url
        :param post: Datos POST
        :param key: Nombre de la clave donde guardar los datos
        :param dest: Dicionario donde guardar los datos
        :param t:
        :return:
        """
        if not t:
            self.running_threads.append(url)
            Thread(target=self._threaded_request_api, args=[url, post, key, dest, True]).start()
            return

        data = self._request_api(url, post)

        if key:
            if key in self.raw_result[dest]:
                self.raw_result[dest][key].update(data)
            else:
                self.raw_result[dest][key] = data
        else:
            self.raw_result[dest] = data

        self.running_threads.remove(url)

    def _search(self):
        raise NotImplementedError()

    def get_movie_info(self, extended=True):
        raise NotImplementedError()

    def get_tvshow_info(self, extended=True):
        raise NotImplementedError()

    def get_episode_info(self, extended=True):
        raise NotImplementedError()

    def get_season_info(self, extended=True):
        raise NotImplementedError()

    def _request_api(self, url, post):
        raise NotImplementedError()


class TMDb(MediaInfo):
    base_url = "http://api.themoviedb.org/3"
    api_key = "a79d70765e78bc6b322fb6f81bb6659d"
    image_path = "http://image.tmdb.org/t/p/original"
    trailer_path = "https://www.youtube.com/watch?v="
    tvshow_status = {
        "Returning Series": "Returning Series",
        "Production": "Production",
        "Planed": "Planed",
        "Cancelled": "Cancelled",
        "Ended": "Ended"
    }

    """
    Funciones @Label cada funcion es un parametro que se guardara en el item (title, plot, etc...)
    La función debe devolver el valor para cada parametro dependiendo del tipo de item (movie, tvshow, etc)
    Si una función falla o no devuelve nada ese parametro se omitira manteniendo el valor que tuviera el item
    """
    @Label
    def title(self):
        if self.item.type == 'movie':
            dct = self.raw_result['movie']
            return dct['title'].strip()

        elif self.item.type == 'tvshow':
            dct = self.raw_result['tvshow']
            return dct['name'].strip()

        elif self.item.type == 'season':
            dct = self.raw_result['season']
            return dct['name'].strip()

        elif self.item.type == 'episode':
            dct = self.raw_result['episode']
            return dct['name'].strip()

    @Label
    def originaltitle(self):
        if self.item.type == 'movie':
            dct = self.raw_result['movie']
            return dct['original_title']
        elif self.item.type == 'tvshow':
            dct = self.raw_result['tvshow']
            return dct['original_name']

    @Label
    def tvshowtitle(self):
        if self.item.type in ('tvshow', 'season', 'episode'):
            dct = self.raw_result['tvshow']
            return dct['name'].strip()

    @Label
    def language(self):
        if self.item.type == 'movie':
            dct = self.raw_result['movie']
        else:
            dct = self.raw_result['tvshow']
        return dct['original_language']

    @Label
    def plot(self):
        if self.item.type == 'movie':
            dct = self.raw_result['movie']
        elif self.item.type == 'tvshow':
            dct = self.raw_result['tvshow']
        elif self.item.type == 'season':
            dct = self.raw_result['season']
            if not dct.get('overview'):
                dct = self.raw_result['tvshow']
        else:
            dct = self.raw_result['episode']
            if not dct.get('overview'):
                dct = self.raw_result['tvshow']

        value = dct['overview']
        # Debug añade el titulo asignado por el canal para comprobar que coincida con el resultado
        # value = '%s (%s)\n\n' % (self.item.title, self.item.year) + value
        return value

    @Label
    def poster(self):
        if self.item.type == 'movie':
            dct = self.raw_result['movie']
        elif self.item.type == 'tvshow':
            dct = self.raw_result['tvshow']
        elif self.item.type == 'season':
            dct = self.raw_result['season']
            if not dct.get('poster_path'):
                dct = self.raw_result['tvshow']
        else:
            dct = self.raw_result['episode']
            if not dct.get('poster_path'):
                dct = self.raw_result['tvshow']
        if dct['poster_path']:
            return self.image_path + dct.get('poster_path', '')

    @Label
    def fanart(self):
        if self.item.type == 'movie':
            dct = self.raw_result['movie']
        elif self.item.type == 'tvshow':
            dct = self.raw_result['tvshow']
        elif self.item.type == 'season':
            dct = self.raw_result['season']
            if not dct.get('backdrop_path'):
                dct = self.raw_result['tvshow']
        else:
            dct = self.raw_result['episode']
            if not dct.get('backdrop_path'):
                dct = self.raw_result['tvshow']
        if dct.get('backdrop_path'):
            return self.image_path + dct.get('backdrop_path', '')

    @Label
    def thumb(self):
        if self.item.type == 'episode':
            dct = self.raw_result['episode']
            if dct.get('still_path'):
                return self.image_path + dct.get('still_path', '')
            dct = self.raw_result['tvshow']
            return self.image_path + dct.get('poster_path', '')

    @Label
    def code(self):
        if self.item.type == 'movie':
            dct = self.raw_result['movie']
            return dct['imdb_id']
        elif self.item.type in ('tvshow', 'season', 'episode'):
            dct = self.raw_result['tvshow']
            return dct["external_ids"]['imdb_id']

    @Label
    def tmdb_id(self):
        if self.item.type == 'movie':
            dct = self.raw_result['movie']
        else:
            dct = self.raw_result['tvshow']
        return dct['id']

    @Label
    def tagline(self):
        if self.item.type == 'movie':
            dct = self.raw_result['movie']
        else:
            dct = self.raw_result['tvshow']
        return dct['tagline']

    @Label
    def duration(self):
        if self.item.type == 'movie':
            dct = self.raw_result['movie']
        else:
            dct = self.raw_result['tvshow']
        return dct.get('runtime', 0) * 60

    @Label
    def genre(self):
        if self.item.type == 'movie':
            dct = self.raw_result['movie']
        else:
            dct = self.raw_result['tvshow']
        return ", ".join([v["name"] for v in dct.get("genres", [])])

    @Label
    def year(self):
        if self.item.type == 'movie':
            dct = self.raw_result['movie']
            return int(dct.get("release_date")[:4])
        elif self.item.type == 'tvshow':
            dct = self.raw_result['tvshow']
            return int(dct.get("first_air_date")[:4])
        elif self.item.type == 'season':
            dct = self.raw_result['season']
            return int(dct.get("air_date")[:4])
        elif self.item.type == 'episode':
            dct = self.raw_result['espisode']
            return int(dct.get("air_date")[:4])

    @Label
    def aired(self):
        if self.item.type == 'movie':
            dct = self.raw_result['movie']
            return "%s/%s/%s" % tuple(reversed(dct["release_date"].split("-")))
        elif self.item.type == 'tvshow':
            dct = self.raw_result['tvshow']
            return "%s/%s/%s" % tuple(reversed(dct["first_air_date"].split("-")))
        elif self.item.type == 'season':
            dct = self.raw_result['season']
            return "%s/%s/%s" % tuple(reversed(dct["air_date"].split("-")))
        elif self.item.type == 'episode':
            dct = self.raw_result['episode']
            return "%s/%s/%s" % tuple(reversed(dct["air_date"].split("-")))

    @Label
    def studio(self):
        if self.item.type == 'movie':
            dct = self.raw_result['movie']
        else:
            dct = self.raw_result['tvshow']
        return ", ".join([v["name"] for v in dct.get("production_companies", [])])

    @Label
    def country(self):
        if self.item.type == 'movie':
            dct = self.raw_result['movie']
        else:
            dct = self.raw_result['tvshow']
        return ", ".join([v["name"] for v in dct.get("production_countries", [])])

    @Label
    def mpaa(self):
        raise NotImplementedError()

    @Label
    def rating(self):
        if self.item.type == 'movie':
            dct = self.raw_result['movie']
        elif self.item.type in ('tvshow', 'season'):
            dct = self.raw_result['tvshow']
        else:
            dct = self.raw_result['episode']
        return dct["vote_average"]

    @Label
    def votes(self):
        if self.item.type == 'movie':
            dct = self.raw_result['movie']
        elif self.item.type in ('tvshow', 'season'):
            dct = self.raw_result['tvshow']
        else:
            dct = self.raw_result['episode']
        return dct["vote_count"]

    @Label
    def director(self):
        if self.item.type == 'movie':
            dct = self.raw_result['movie']
        else:
            dct = self.raw_result['tvshow']
        return ", ".join([v["name"] for v in dct.get("credits").get("crew") if v["job"] == "Director"])

    @Label
    def writer(self):
        if self.item.type == 'movie':
            dct = self.raw_result['movie']
        else:
            dct = self.raw_result['tvshow']
        return ", ".join([v["name"] for v in dct.get("credits").get("crew") if v["job"] in ["Writer", "Screenplay"]])

    @Label
    def castandrole(self):
        if self.item.type == 'movie':
            dct = self.raw_result['movie']
        elif self.item.type == 'tvshow':
            dct = self.raw_result['tvshow']
        elif self.item.type == 'season':
            dct = self.raw_result['season']
        else:
            dct = self.raw_result['episode']
        return [[v["name"], v["character"]] for v in dct.get("credits").get("cast")]

    @Label
    def trailer(self):
        if self.item.type == 'movie':
            dct = self.raw_result['movie']
        elif self.item.type == 'tvshow':
            dct = self.raw_result['tvshow']
        elif self.item.type == 'season':
            dct = self.raw_result['season']
        else:
            dct = self.raw_result['episode']
        url = self.trailer_path + sorted(
            filter(lambda v: v["type"] == "Trailer" and v["site"] == "YouTube",
                   dct.get("videos").get("results")), key=lambda v: v["size"], reverse=True)[0]["key"]

        return '%s?%s' % (sys.argv[0], Item(
            url=url,
            server='youtube',
            action='play',
            type='video',
            title='Trailer'
        ).tourl())

    @Label
    def seasons(self):
        if self.item.type == 'tvshow':
            dct = self.raw_result['tvshow']
            return dct["number_of_seasons"]
        elif self.item.type == 'season':
            return 1

    @Label
    def episodes(self):
        if self.item.type == 'tvshow':
            dct = self.raw_result['tvshow']
            return dct["number_of_episodes"]
        elif self.item.type == 'season':
            dct = self.raw_result['season']
            return len(dct['episodes'])

    @Label
    def season(self):
        if self.item.type == 'season':
            dct = self.raw_result['season']
        elif self.item.type == 'episode':
            dct = self.raw_result['episode']
        else:
            dct = {}
        return dct["season_number"]

    @Label
    def episode(self):
        if self.item.type == 'episode':
            dct = self.raw_result['episode']
            return dct["episode_number"]

    @Label
    def status(self):
        if self.item.type == 'tvshow':
            dct = self.raw_result['tvshow']
            return self.tvshow_status[dct.get("status", '')]


    def _search(self):
        """
        Función encargada de buscar usando el titulo, año, etc...
        Si encuentra resultados fija el primero
        :return:
        """
        if self.item.tmdb_id:
            self.raw_results = [{"id": self.item.tmdb_id}]
            self.set_result(0)
            return

        # Selecciona la url en función del typo de contenido
        if self.item.type == "movie":
            url = self._get_url(
                action="search/movie",
                params={
                    "query": self.item.title,
                    "year": self.item.year
                }
            )

        elif self.item.type == "tvshow":
            url = self._get_url(
                action="search/tv",
                params={
                    "query": self.item.title,
                    "first_air_date_year": self.item.year
                }
            )

        else:
            url = self._get_url(
                action="search/tv",
                params={"query": self.item.tvshowtitle}
            )

        response = self._request_api(url)

        self.limit_ressults(response)

        if response.get('results'):
            self.raw_results = response["results"]
            self.set_result(0)
        else:
            self.raw_results = {}

    def limit_ressults(self, response):
        # Si solo hay un resultado lo damos por bueno
        if response.get('results') is None or len(response['results']) == 1:
            return response

        # Si alguno de los resultados tiene el mismo titulo exacto que el buscado ya sea para titulo o titulo original
        # eliminamos el resto
        filtered = filter(
            lambda x: x.get('title', '').replace(x.get('original_title', ''), '').strip('() ') == self.item.title or
                      x.get('name', '').replace(x.get('original_name', ''), '').strip('() ') == self.item.title or
                      x.get('title', '') == self.item.title or
                      x.get('name', '') == self.item.title or
                      x.get('original_title', '') == self.item.title or
                      x.get('original_name', '') == self.item.title,
            response['results']
        )
        if filtered:
            response['results'] = filtered

        else:
            # Hacemos una búsqueda sobre los titulos obtenidos para determinar cual es el que mas se parece y los ordenamos
            from difflib import SequenceMatcher
            response['results'] = sorted(
                response['results'],
                reverse=True,
                key=lambda x: max(
                    SequenceMatcher(None, x.get('name', x.get('title', '')), self.item.title).ratio(),
                    SequenceMatcher(None, x.get('original_name', x.get('original_title', '')), self.item.title).ratio()
                )
            )

        # Si hay mas de un resultado eliminamos los que no coincidan con el año, siempre y cuando nos quede almenos uno
        if len(response['results']) > 1 and self.item.year:
            filtered = filter(
                lambda x: x.get('release_date', x.get('first_air_date', '')).startswith(str(self.item.year)),
                response['results']
            )
            if filtered:
                response['results'] = filtered

        return response


    def get_episode_info(self, extended=True):
        # Nos aseguramos que se haya hecho la búsqueda previamente para obtener el ID de la serie
        assert self.results
        self.get_tvshow_info(extended)

        if not self.raw_result['episode']:
            if extended:
                url = self._get_url(
                    action="tv/%s/season/%s/episode/%s" % (
                        self.raw_result["search"]["id"],
                        self.item.season,
                        self.item.episode
                    ),
                    params={"append_to_response": "videos,credits,external_ids"}
                )
                self.raw_result['episode'] = self._request_api(url)
            else:
                url = self._get_url(
                    action="tv/%s/season/%s" % (self.raw_result["search"]["id"], self.item.season),
                    params={"append_to_response": "videos,credits,external_ids"}
                )
                self.raw_result['season'] = self._request_api(url)
                try:
                    self.raw_result['episode'] = filter(
                        lambda x: x['episode_number'] == self.item.episode,
                        self.raw_result['season']['episodes']
                    )[-1]
                except Exception:
                    url = self._get_url(
                        action="tv/%s/season/%s/episode/%s" % (
                            self.raw_result["search"]["id"],
                            self.item.season,
                            self.item.episode
                        ),
                        params={"append_to_response": "videos,credits,external_ids"}
                    )
                    self.raw_result['episode'] = self._request_api(url)

        # Esperamos a que no haya peticiones pendientes
        while self.running_threads:
            time.sleep(0.1)

        return self._create_data()

    def get_season_info(self, extended=True):
        # Nos aseguramos que se haya hecho la búsqueda previamente para obtener el ID de la serie
        assert self.results
        self.get_tvshow_info(True)

        # Obtenemos los datos de la temporada
        if not self.raw_result['season']:
            if extended:
                url = self._get_url(
                    action="tv/%s/season/%s" % (self.raw_result["search"]["id"], self.item.season),
                    params={"append_to_response": "videos,credits,external_ids"}
                )
                self._threaded_request_api(url, dest="season")
            else:
                try:
                    self.raw_result['season'] = filter(
                        lambda x: x['season_number'] == self.item.season,
                        self.raw_result['tvshow']['seasons']
                    )[-1]
                except Exception:
                    url = self._get_url(
                        action="tv/%s/season/%s" % (self.raw_result["search"]["id"], self.item.season),
                        params={"append_to_response": "videos,credits,external_ids"}
                    )
                    self._threaded_request_api(url, dest="season")

        # Esperamos a que no haya peticiones pendientes
        while self.running_threads:
            time.sleep(0.1)

        return self._create_data()

    def get_movie_info(self, extended=True):
        # Nos aseguramos que se haya hecho la búsqueda previamente para obtener el ID de la película
        assert self.results
        if len(self.raw_result['search']) == 1:
            # No hemos realizado búsqueda, solo tenemos el ID porque lo hemos heredado
            # Ponemos extended porque no podemos obtener nada de la búsqueda
            extended = True

        # Si no tenemos los datos extendidos de la película y los queremos, lánzamos la peticón para obtenerlos
        if not self.raw_result["movie"]:
            if extended:
                url = self._get_url(
                    action="movie/%s" % self.raw_result["search"]["id"],
                    params={"append_to_response": "videos,credits"}
                )
                self._threaded_request_api(url, dest="movie")
            else:
                self.raw_result["movie"] = self.raw_result["search"]

        # Esperamos a que no haya peticiones pendientes
        while self.running_threads:
            time.sleep(0.1)

        return self._create_data()

    def get_tvshow_info(self, extended=True):
        # Nos aseguramos que se haya hecho la búsqueda previamente para obtener el ID de la serie
        assert self.results
        if len(self.raw_result['search']) == 1:
            # No hemos realizado búsqueda, solo tenemos el ID porque lo hemos heredado
            # Ponemos extended porque no podemos obtener nada de la búsqueda
            extended = True

        # Si no tenemos los datos extendidos de la serie y los queremos, lánzamos la peticón para obtenerlos
        if not self.raw_result["tvshow"]:
            if extended:
                url = self._get_url(
                    action="tv/%s" % self.raw_result["search"]["id"],
                    params={"append_to_response": "videos,credits,external_ids"}
                )
                self._threaded_request_api(url, dest="tvshow")
            else:
                self.raw_result["tvshow"] = self.raw_result["search"]

        # Esperamos a que no haya peticiones pendientes
        while self.running_threads:
            time.sleep(0.1)

        return self._create_data()

    def _get_url(self, action, params=None):
        if params is None:
            params = dict()

        params["api_key"] = self.api_key
        # params["include_adult"] = True
        params["language"] = "es"

        return "/".join([self.base_url, action]) + "?" + urllib.urlencode(params)

    def _request_api(self, url, post=None):
        cache_id = hashlib.md5(url + str(post)).hexdigest()

        cached = False
        with lock:
            if cache_id not in TEMP_DATA_CACHE:
                TEMP_DATA_CACHE[cache_id] = {'data': None, 'limit_time': time.time()}
            else:
                cached = True

        if cached:
            try:
                while TEMP_DATA_CACHE[cache_id]['data'] is None:
                    time.sleep(0.1)
            except:
                cached = False
            else:
                #logger.debug('Cacheada')
                return jsontools.load_json(TEMP_DATA_CACHE[cache_id]['data'])

        if not cached:
            data = bbdd.scraper_cache_get(cache_id, self.item.type)
            if data:
                TEMP_DATA_CACHE[cache_id] = data
                #logger.debug('BBDD')
                return jsontools.load_json(TEMP_DATA_CACHE[cache_id]['data'])

            req = httptools.downloadpage(url, cookies=False)
            if req.sucess:
                TEMP_DATA_CACHE[cache_id]['data'] = req.data
                TEMP_DATA_CACHE[cache_id]['limit_time'] = time.time() + (3600*24*7 if self.item.type in ('movie', 'tvshow') else 3600*24)
                #logger.debug('Encontrada: %s' % url)
                return jsontools.load_json(req.data)

            else:
                if cache_id in TEMP_DATA_CACHE:
                    del TEMP_DATA_CACHE[cache_id]
                if req.code == 429:
                    if req.headers.get('Retry-After'):
                        time.sleep(int(req.headers.get('Retry-After')))
                    return self._request_api(url)
                else:
                    #logger.debug('No encontrada: %s' % url)
                    return {'results': None}


class TVDb(MediaInfo):
    base_url = "https://api.thetvdb.com"
    api_key = "020944711115DCDD"
    username = "MediaExplorer"
    userkey = "6FBBB95E4A666758"
    image_path = "http://thetvdb.com/banners/"
    trailer_path = "https://www.youtube.com/watch?v="
    token = ""

    tvshow_status = {
        "Continuing": "Returning Series",
        "Production": "Production",
        "Planed": "Planed",
        "Cancelled": "Cancelled",
        "Ended": "Ended"
    }

    """
    Funciones @Label cada funcion es un parametro que se guardara en el item (title, plot, etc...)
    La función debe devolver el valor para cada parametro dependiendo del tipo de item (movie, tvshow, etc)
    Si una función falla o no devuelve nada ese parametro se omitira manteniendo el valor que tuviera el item
    """
    @Label
    def title(self):
        if self.item.type == 'tvshow':
            dct = self.raw_result['tvshow']
            return dct['seriesName'].strip()

        elif self.item.type == 'episode':
            dct = self.raw_result['episode']
            return dct['episodeName'].strip()

    @Label
    def originaltitle(self):
        raise NotImplementedError()

    @Label
    def tvshowtitle(self):
        dct = self.raw_result['tvshow']
        return dct['seriesName'].strip()

    @Label
    def language(self):
        raise NotImplementedError()

    @Label
    def plot(self):
        if self.item.type in ('tvshow', 'season'):
            dct = self.raw_result['tvshow']
        else:
            dct = self.raw_result['episode']
        value = dct['overview']
        # Debug añade el titulo asignado por el canal para comprobar que coincida con el resultado
        # value = '%s (%s)\n\n' % (self.item.title, self.item.year) + value
        return value

    @Label
    def poster(self):
        if self.item.type == 'tvshow':
            dct = self.raw_result['tvshow']
        elif self.item.type == 'season':
            dct = self.raw_result['season']
        else:
            dct = self.raw_result['episode']
        if dct.get("poster")[0]["fileName"]:
            return self.image_path + dct.get("poster")[0]["fileName"]

    @Label
    def fanart(self):
        dct = self.raw_result['tvshow']
        if dct.get("fanart")[0]["fileName"]:
            return self.image_path + dct.get("fanart")[0]["fileName"]

    @Label
    def thumb(self):
        if self.item.type == 'episode':
            dct = self.raw_result['episode']
            if dct.get('filename'):
                return self.image_path + dct.get('filename', '')

    @Label
    def banner(self):
        if self.item.type == 'tvshow':
            dct = self.raw_result['tvshow']
        elif self.item.type == 'season':
            dct = self.raw_result['season']
        else:
            dct = self.raw_result['episode']
        if dct.get('banner'):
            return self.image_path + dct.get('banner', '')

    @Label
    def code(self):
        dct = self.raw_result['tvshow']
        return dct["imdbId"]

    @Label
    def tvdb_id(self):
        dct = self.raw_result['tvshow']
        return dct['id']

    @Label
    def tagline(self):
        raise NotImplementedError()

    @Label
    def duration(self):
        dct = self.raw_result['tvshow']
        return int(dct.get('runtime', 0)) * 60

    @Label
    def genre(self):
        dct = self.raw_result['tvshow']
        return ", ".join(dct["genre"])

    @Label
    def year(self):
        if self.item.type == 'tvshow':
            dct = self.raw_result['tvshow']
        elif self.item.type == 'season':
            dct = self.raw_result.get('season').get('episodes')[0]
        else:
            dct = self.raw_result['episode']
        return int(dct.get("firstAired")[:4])

    @Label
    def aired(self):
        if self.item.type == 'tvshow':
            dct = self.raw_result['tvshow']
        elif self.item.type == 'season':
            dct = self.raw_result.get('season').get('episodes')[0]
        else:
            dct = self.raw_result['episode']
        return "%s/%s/%s" % tuple(reversed(dct["firstAired"].split("-")))

    @Label
    def studio(self):
        raise NotImplementedError()

    @Label
    def country(self):
        raise NotImplementedError()

    @Label
    def mpaa(self):
        dct = self.raw_result['tvshow']
        return dct["rating"]

    @Label
    def rating(self):
        if self.item.type in ('tvshow', 'season'):
            dct = self.raw_result['tvshow']
        else:
            dct = self.raw_result['episode']
        return dct["siteRating"]

    @Label
    def votes(self):
        if self.item.type in ('tvshow', 'season'):
            dct = self.raw_result['tvshow']
        else:
            dct = self.raw_result['episode']
        return dct["siteRatingCount"]

    @Label
    def director(self):
        if self.item.type in ('tvshow', 'season'):
            dct = self.raw_result['tvshow']
        else:
            dct = self.raw_result['episode']
        return ', '.join(dct["directors"])

    @Label
    def writer(self):
        if self.item.type in ('tvshow', 'season'):
            dct = self.raw_result['tvshow']
        else:
            dct = self.raw_result['episode']
        return ', '.join(dct["writers"])

    @Label
    def castandrole(self):
        dct = self.raw_result['tvshow']
        return [[v["name"], v["role"]] for v in dct.get("actors", [])]

    @Label
    def trailer(self):
        raise NotImplementedError()

    @Label
    def seasons(self):
        if self.item.type == 'tvshow':
            dct = self.raw_result['tvshow']
            return len(dct['summary']['airedSeasons'])
        elif self.item.type == 'season':
            return 1

    @Label
    def episodes(self):
        if self.item.type == 'tvshow':
            dct = self.raw_result['tvshow']
            return int(dct.get('summary').get('airedEpisodes'))

        elif self.item.type == 'season':
            dct = self.raw_result['season']
            return len(dct['episodes'])

    @Label
    def season(self):
        if self.item.type == 'season':
            return self.item.season

    @Label
    def episode(self):
        if self.item.type == 'episode':
            return self.item.episode

    @Label
    def status(self):
        dct = self.raw_result['tvshow']
        return self.tvshow_status[dct.get("status", '')]

    def _search(self):
        """
        Función encargada de buscar usando el titulo, año, etc...
        Si encuentra resultados fija el primero
        :return:
        """
        if self.item.tvdb_id:
            self.raw_results = [{"id": self.item.tvdb_id}]
            self.set_result(0)
            return

        if self.item.type == "tvshow":
            url = self._get_url(
                action="search/series",
                params={"name": self.item.title}
            )

        else:
            url = self._get_url(
                action="search/series",
                params={"name": self.item.tvshowtitle}
            )

        response = self._request_api(url)

        if response:
            self.raw_results = response
            self.set_result(0)

    def get_episode_info(self, extended=True):
        assert self.results

        if not self.raw_result['tvshow']:
            self.get_tvshow_info(extended)

        if not self.raw_result['season']:
            self.get_season_info(extended)

        episode_id = filter(
            lambda x: [x["airedEpisodeNumber"], x["airedSeason"]] == [self.item.episode, self.item.season],
            self.raw_result.get("season").get('episodes'))[0]["id"]

        url = self._get_url(action="episodes/%s" % episode_id)
        self.raw_result["episode"] = self._request_api(url)

        while self.running_threads:
            time.sleep(0.1)

        return self._create_data()

    def get_season_info(self, extended=True):
        assert self.results
        if not self.raw_result['tvshow']:
            self.get_tvshow_info(extended)

        url = self._get_url(action="series/%s/episodes/query" % self.raw_result["search"]["id"],
                            params={"airedSeason": self.item.season})
        self._threaded_request_api(url, dest="season", key='episodes')

        url = self._get_url(action="series/%s/images/query" % self.raw_result["search"]["id"],
                            params={"keyType": "season", 'subKey': self.item.season})
        self._threaded_request_api(url, dest="season", key="poster")

        while self.running_threads:
            time.sleep(0.1)

        return self._create_data()

    def get_tvshow_info(self, extended=True):
        assert self.results
        if len(self.raw_result['search']) == 1:
            # No hemos realizado búsqueda, solo tenemos el ID porque lo hemos heredado
            # Ponemos extended porque no podemos obtener nada de la búsqueda
            extended = True
        if extended:
            if not self.raw_result['tvshow']:
                url = self._get_url(action="series/%s" % self.raw_result["search"]["id"])
                self.raw_result["tvshow"] = self._request_api(url)

                url = self._get_url(action="series/%s/images/query" % self.raw_result["search"]["id"],
                                    params={"keyType": "fanart"})
                self._threaded_request_api(url, dest="tvshow", key="fanart")

                url = self._get_url(action="series/%s/images/query" % self.raw_result["search"]["id"],
                                    params={"keyType": "poster"})
                self._threaded_request_api(url, dest="tvshow", key="poster")

                url = self._get_url(action="series/%s/actors" % self.raw_result["search"]["id"])
                self._threaded_request_api(url, dest="tvshow", key="actors")
        else:
            self.raw_result["tvshow"] = self.raw_result["search"]

        while self.running_threads:
            time.sleep(0.1)

        return self._create_data()

    def get_movie_info(self, extended=True):
        raise NotImplementedError()

    def _autorize(self):
        url = self.base_url + "/login"
        post = '{"apikey":"%s","username":"%s","userkey":"%s"}' % (self.api_key, self.username, self.userkey)

        data = self._request_api(url, post)
        self.token = data["token"]
        settings.set_setting('token', self.token, __file__)

    def _get_url(self, action, params=None):
        if params is None:
            params = dict()

        return "/".join([self.base_url, action]) + "?" + urllib.urlencode(params)

    def _request_api(self, url, post=None):
        if not self.token and not url == self.base_url + "/login":
            self.token = settings.get_setting('token', __file__)
            if not self.token:
                self._autorize()

        headers = {"Accept-Language": "es", "Authorization": "Bearer %s" % self.token}

        if post:
            headers["Content-Type"] = "application/json"

        req = httptools.downloadpage(url, post=post, headers=headers)

        if not req.sucess:
            data = jsontools.load_json(req.data)
            if data.get("Error") == "Not authorized":
                self._autorize()
                data = self._request_api(url, post)
        else:
            data = jsontools.load_json(req.data)

        if "data" in data:
            return data["data"]
        else:
            return data
