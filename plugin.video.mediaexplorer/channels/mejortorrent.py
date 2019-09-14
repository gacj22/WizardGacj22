# -*- coding: utf-8 -*-
from core.libs import *
import unicodedata

QLT = Qualities({
    Qualities.rip: ['dvdrip', 'rhdtv', 'hdrip'],
    Qualities.hd_full: ['1080p', 'fullbluray'],
    Qualities.uhd: ['4k hdr', '4k'],
    Qualities.hd: ['hdtv', '720p'],
    Qualities.scr: ['dvdscr', 'br screener', 'dvdscreener'],
    Qualities.sd: ['sd'],
    Qualities.m3d: ['3d']
})

HOST = 'https://www.mejortorrentt.org/'

def mainlist(item):
    logger.trace()
    itemlist = list()

    # SubMenu Peliculas
    new_item = item.clone(
        type='label',
        label="Películas",
        category='movie',
        thumb='thumb/movie.png',
        icon='icon/movie.png',
        poster='poster/movie.png'
    )
    itemlist.append(new_item)
    itemlist.extend(menupeliculas(new_item))

    #SubMenu Series
    new_item = item.clone(
        type='label',
        label="Series",
        category='tvshow',
        thumb='thumb/tvshow.png',
        icon='icon/tvshow.png',
        poster='poster/tvshow.png',
    )
    itemlist.append(new_item)
    itemlist.extend(menuseries(new_item))

    '''itemlist.append(item.clone(
        action="config",
        label="Configuración",
        folder=False,
        category='all',
        type='setting'
    ))'''

    return itemlist


'''def config(item):
    platformtools.show_settings(item=item)'''


def menupeliculas(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        label="Novedades SD",
        action="newest_movies",
        content_type='movies',
        type="item",
        group=True,
        url=HOST + '/torrents-de-peliculas.html'
    ))

    itemlist.append(item.clone(
        label="Novedades HD",
        action="newest_movies",
        content_type='movies',
        type="item",
        group=True,
        url=HOST + '/torrents-de-peliculas-hd-alta-definicion.html'
    ))

    itemlist.append(item.clone(
        action="generos",
        label="Géneros",
        type="item",
        group=True,
        url=HOST + '/torrents-de-peliculas.html'
    ))

    itemlist.append(item.clone(
        action="abc",
        label="Películas por orden alfabético",
        url=HOST,
        type="item",
        group=True,
    ))

    itemlist.append(item.clone(
        action="search",
        label="Buscar",
        query=True,
        type='search',
        group=True,
        content_type='movies'
    ))

    return itemlist


def menuseries(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        label="Nuevos episodios SD",
        action="newest_episodes",
        content_type='episodes',
        type="item",
        group=True,
        url=HOST + '/torrents-de-series.html',
        quality='sd'
    ))

    itemlist.append(item.clone(
        label="Nuevos episodios HD",
        action="newest_episodes",
        content_type='episodes',
        type="item",
        group=True,
        url=HOST + '/torrents-de-series-hd-alta-definicion.html'
    ))

    itemlist.append(item.clone(
        action="abc",
        label="Series por orden alfabético",
        url=HOST,
        type="item",
        group=True,
    ))

    itemlist.append(item.clone(
        action="search",
        label="Buscar",
        query=True,
        type='search',
        group=True,
        content_type='tvshows'
    ))

    return itemlist


def generos(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, "<select name='valor2'(.*?)</select>")

    for genero in scrapertools.find_multiple_matches(data,'<option[ selected]?>([^<]+)</option>'):
        itemlist.append(item.clone(
            label=genero,
            campo='genero',
            valor=genero,
            type='item',
            content_type='movies',
            action='listado_unico_peliculas',
            url=HOST + '/peliculas-buscador.html'
        ))

    return itemlist


def abc(item):
    logger.trace()
    itemlist = list()

    for letra in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        new_item = item.clone(
            label=letra,
            type='item'
        )

        if item.category == 'movie':
            new_item.campo = 'letra'
            new_item.valor = letra
            new_item.content_type='movies'
            new_item.action = 'listado_unico_peliculas'
            new_item.url = HOST + '/peliculas-buscador.html'
        else:
            new_item.content_type = 'tvshows'
            new_item.action = 'listado_unico_series'
            new_item.url = HOST + '/series-letra-%s.html' % letra.lower()


        itemlist.append(new_item)

    return itemlist


def search(item):
    logger.trace()

    item.url = HOST + '/secciones.php?sec=buscador&valor=%s' % item.query.replace(' ','+')
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    data = scrapertools.find_single_match(data, "Se han encontrado <b>(.*?)<td id='main_td_right'>")
    #data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")

    patron = "<a href='([^']+)[^>]+>(.*?)</a>(.*?)</td></tr>"

    listado = []
    for url, title, quality in scrapertools.find_multiple_matches(data, patron):
        if item.category == 'movie' and 'Película' in quality:
            # Simplificar quality
            quality = scrapertools.find_single_match(re.sub(r'<.*?>|Película|Serie|-', '', quality), '\w+').lower()
            if '3d' in quality:
                quality = '3d'
            elif '1080p' in quality:
                quality = '1080p'
            elif '720p' in quality:
                quality = '720p'

            title = re.sub(r'<.*?>','', title)
            title += '#|#' + quality
            listado.append((url, title))

        if item.category == 'tvshow' and 'Serie' in quality:
            title = re.sub(r'<.*?>', '', title)
            listado.append((url, title))

    if item.category == 'movie':
        return filtrar_peliculas(item, listado)
    else:
        return filtrar_series(item, listado)


def listado_unico_series(item):
    logger.trace()

    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, "<big>Mostrando <b>(.*?)<td id='main_td_right'>")
    #data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    return filtrar_series(item,scrapertools.find_multiple_matches(data,"<td>\s?<a href='([^']+)'.*?>\s?([^<]+)</a>"))


def filtrar_series(item, series):
    logger.trace()
    itemlist = list()
    listado = {}
    for url, title in series:
        try:
            title = title.split('-')
            tvshowtitle = re.sub(r'\s?\.?\s?$', '', re.sub(r'[\(|\[].*[\)|\]]', '', title[0]))
            temporada = re.sub(r'\s?\.?\s?$', '', re.sub(r'[\(|\[].*[\)|\]]', '', title[1]))
            if 'miniserie' in temporada.lower():
                temporada = 1
            else:
                temporada = int(scrapertools.find_single_match(temporada,'(\d+)'))
        except:
            continue

        listado_temporadas = listado.get(tvshowtitle, {})
        listado_urls = listado_temporadas.get(temporada, [])
        listado_urls.append(HOST + url)
        listado_temporadas[temporada] = listado_urls
        listado[tvshowtitle] = listado_temporadas

    if item.ini:
        ini = item.ini
        del item.ini
    else:
        ini = 0

    for k in sorted(listado.keys())[ini:ini + 40]:
        itemlist.append(item.clone(
            tvshowtitle=k,
            title = k,
            temporadas=listado[k],
            type='tvshow',
            content_type='seasons',
            action='seasons'
        ))

    # paginacion
    if ini + 40 < len(listado):
        itemlist.append(item.clone(
            ini=ini + 40,
            type='next'))

    return itemlist


def listado_unico_peliculas(item):
    logger.trace()

    post = {
        'submit': 'Buscar',
        'campo': item.campo,
        'valor2': item.valor,
        'valor3': item.valor}

    data = httptools.downloadpage(item.url, post=post).data
    data = scrapertools.find_single_match(data, "<br>Se han encontrado <b>(.*?)<td id='main_td_right'>")
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    return filtrar_peliculas(item, scrapertools.find_multiple_matches(data, "<td><a href='([^']+)'.*?>\s?([^<]+)</a>"))


def normalizar(s):
    """
    Devuelve la cadena s en minusculas y sin marcas diacríticas como tildes, dieresis, etc...
    :param s: str o unicode a normalizar
    :return: cadena sin marcas diacriticas
    """
    #import unicodedata
    s = s.lower()
    if isinstance(s, str):
        s = s.decode('utf-8')

    return ''.join((c for c in unicodedata.normalize('NFD',unicode(s)) if unicodedata.category(c) != 'Mn'))


def filtrar_peliculas(item, peliculas):
    logger.trace()
    itemlist = list()
    listado = dict()
    i = -1

    for url, title in peliculas:
        try:
            title, quality = title.split('#|#')
        except:
            quality = ''

        title = re.sub(r'\s?\.?\s?$', '', title)
        key = normalizar(title)
        if key in listado:
            orden, title_old, listado_urls, listado_calidades = listado[key]
        else:
            i += 1
            orden, title_old, listado_urls, listado_calidades = (i, '', [], [])

        listado_urls.append(HOST + url)
        listado_calidades.append(quality)
        listado[key] = (orden, title, listado_urls, listado_calidades)

    ini = item.ini if item.ini else 0

    for orden, title, listado_urls, listado_calidades in sorted(listado.values(), key=lambda x: x[0])[ini:ini + 40]:
        quality = list()
        for q in listado_calidades:
            if QLT.get(q) not in quality:
                quality.append(QLT.get(q))

        itemlist.append(item.clone(
            title=title,
            url=listado_urls,
            type='movie',
            content_type='servers',
            action='findvideos',
            quality= quality if quality else None
        ))

    # paginacion
    if ini + 40 < len(listado):
        itemlist.append(item.clone(
            ini=ini + 40,
            type='next'))

    return itemlist


def newest_movies(item):
    logger.trace()
    itemlist = list()
    auxdict = dict()
    i=0

    if not item.url:
        item.url = HOST + "torrents-de-peliculas-hd-alta-definicion.html"

    data = httptools.downloadpage(item.url).data
    #data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    # Extraemos bloque_noticia
    patron = "<table class='main_table_center_content'>(.*?)<span class='nopaginar'>"

    for noticia in scrapertools.find_multiple_matches(data,patron):
        # Obtenemos las urls y los posters incluidos en cada noticia
        patron = '<a href="([^"]+)"><img src="([^"]+)'
        for url, poster in scrapertools.find_multiple_matches(noticia, patron):
            # Con ayuda de la url obtenemos el titulo y la calidad de cada pelicula
            patron = '%s">([^<]+)</a>\s*<b>([^<]+)</b>' % url

            title, quality = scrapertools.find_single_match(noticia, patron)
            quality = quality.replace('(', '').replace(')', '').strip()
            title = re.sub(r'\s?\.?\s?$', '', re.sub('[\(|\[]%s[\)|\]]' % quality, '', title))

            # Simplificar quality
            quality = quality.replace('-', ' ').lower()
            if scrapertools.find_single_match(quality + ' ', ' 3d '):
                quality = '3d'
            elif scrapertools.find_single_match(quality + ' ', ' 1080p? '):
                quality = '1080p'
            elif scrapertools.find_single_match(quality + ' ', ' 720p? '):
                quality = '720p'

            new_item= item.clone(
                title=title,
                label=title,
                url= [HOST + url],
                type="movie",
                content_type="servers",
                poster= HOST + poster.replace(' ', '%20'),
                action="findvideos",
                quality=[QLT.get(quality)]
                )

            key = normalizar(title)
            if not key in auxdict:
                auxdict[key] = (i, new_item.clone())
                i += 1

            else:
                orden, it = auxdict[key]
                q_aux = it.quality[:]
                u_aux = it.url[:]
                u_aux.append(HOST + url)

                if QLT.get(quality) not in it.quality:
                    q_aux.append(QLT.get(quality))



                auxdict[key] = (orden, it.clone(
                    url=u_aux,
                    quality=sorted(q_aux, key=lambda q: q.level, reverse=True)
                ))

    for orden, it in sorted(auxdict.values(), key=lambda x: x[0]):
        itemlist.append(it.clone())

    # Paginador
    if len(itemlist) > 40:
        if not item.page:
            itemlist = itemlist[:len(itemlist) / 2]
            next_url = ""
            itemlist.append(item.clone(
                type='next',
                page=True
            ))
        else:
            itemlist = itemlist[len(itemlist) / 2:]
            next_url = scrapertools.find_single_match(data, "</span> <a href='(.*?)'")

    else:
        next_url = scrapertools.find_single_match(data, "</span> <a href='(.*?)'")

    if next_url and itemlist:
        next_url = HOST + next_url
        itemlist.append(item.clone(
            url=next_url,
            type='next',
            page=False
        ))

    return itemlist


def newest_episodes(item):
    logger.trace()
    itemlist = list()

    if not item.url:
        item.url = HOST + "torrents-de-series-hd-alta-definicion.html"

    data = httptools.downloadpage(item.url).data
    #data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    # Extraemos bloque_noticia
    patron = "<table class='main_table_center_content'>(.*?)<span class='nopaginar'>"
    for noticia in scrapertools.find_multiple_matches(data, patron):
        # Obtenemos las urls y los posters incluidos en cada noticia
        patron = '<a href="([^"]+)"><img src="([^"]+)'
        for url, poster in scrapertools.find_multiple_matches(noticia, patron):
            # Con ayuda de la url obtenemos el titulo_temporada y el capitulo
            patron = '%s">([^<]+)</a>\s*(?:<b>)+([^<]+)</b>' % url
            title_season, episode = scrapertools.find_single_match(noticia, patron)
            tvshowtitle, season = scrapertools.find_single_match(title_season, "(?i)(.*?) - ([0-9,M]+)")
            quality = scrapertools.find_single_match(title_season, "\[([^\]]+)")

            # Simplificar quality
            quality = quality.replace('-', ' ').lower()
            if scrapertools.find_single_match(quality + ' ', ' 3d '):
                quality = '3d'
            elif scrapertools.find_single_match(quality + ' ', ' 1080p? '):
                quality = '1080p'
            elif scrapertools.find_single_match(quality + ' ', ' 720p? '):
                quality = '720p'

            # si es miniserie
            season = int(season.lower().replace('m', '1'))

            new_item = item.clone(
                tvshowtitle=tvshowtitle.strip(),
                label=tvshowtitle.strip(),
                url=HOST + url,
                action="findvideos",
                thumb=HOST + poster.replace(' ', '%20'),
                season=season,
                type='episode',
                content_type='servers',
                quality = QLT.get(quality) if quality else item.quality
            )

            num_episode = scrapertools.find_multiple_matches(episode, "(\d+)")
            num_episode = [int(n) for n in num_episode]
            new_item.episode = num_episode[0]

            if len(num_episode) > 1:
                if 'al' in episode and len(num_episode) == 2:
                    multi_episodes = range(num_episode[0], num_episode[1] + 1)
                else:
                    multi_episodes = num_episode

                if 'serie-episodio-descargar-torrent' in url or 'serie-descargar-torrents' in url:
                    new_item.multi_episodes = multi_episodes


            if 'serie-descargar-torrents' in url:
                new_item.content_type = 'episodes'
                new_item.action='filter_episodes' # Esto obtiene solo los episodios indicados

            itemlist.append(new_item)

    # Paginador
    if len(itemlist) > 40:
        if not item.page:
            itemlist = itemlist[:len(itemlist) / 2]
            next_url = ""
            itemlist.append(item.clone(
                type='next',
                page=True
            ))
        else:
            itemlist = itemlist[len(itemlist) / 2:]
            next_url = scrapertools.find_single_match(data, "</span> <a href='(.*?)'")

    else:
        next_url = scrapertools.find_single_match(data, "</span> <a href='(.*?)'")

    if next_url and itemlist:
        next_url = HOST + next_url
        itemlist.append(item.clone(
            url=next_url,
            type='next',
            page=False
        ))

    return itemlist


def filter_episodes(item):
    itemlist= list()

    if item.multi_episodes:
        multi_episodes = item.multi_episodes
        item.multi_episodes=[]

        for new_item in episodes(item):
            if new_item.multi_episodes:
                # Verdadero multi_episodes
                if set(multi_episodes).intersection(set(new_item.multi_episodes)):
                    itemlist.append(new_item)
            elif new_item.episode in multi_episodes:
                itemlist.append(new_item)
    else:
        for new_item in episodes(item):
            if new_item.episode == item.episode:
                itemlist = findvideos(new_item)
                break

    return itemlist


def seasons(item):
    logger.trace()
    itemlist = list()

    for s in  sorted(item.temporadas.keys()):
        itemlist.append(item.clone(
            action="episodes",
            season=s,
            type='season',
            url= item.temporadas[s],
            content_type='episodes'
        ))

    return itemlist


def episodes(item):
    logger.trace()
    itemlist = list()
    listado = {}

    if not isinstance(item.url, list):
        item.url = [item.url]

    for url in item.url:
        data = httptools.downloadpage(url).data
        #data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
        data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

        patron = "<a href='(/serie-episodio-descargar-torrent[^']+)'>([^<]+)"
        for url, episode in scrapertools.find_multiple_matches(data, patron):
            num_episode = scrapertools.find_multiple_matches(episode, "\d+[x|X](\d+)")

            if len(num_episode) == 1:
                n = int(num_episode[0])
                listado_urls = listado.get(n, [])
                listado_urls.append(HOST + url)
                listado[n] = listado_urls

            else:
                if 'al' in episode and len(num_episode) == 2:
                    multi_episodes = range(int(num_episode[0]), int(num_episode[1]) + 1)
                else:
                    multi_episodes = [int(n) for n in num_episode]
                    multi_episodes.sort()

                for n in multi_episodes:
                    listado_urls = listado.get(n, [])
                    listado_urls.append(HOST + url)
                    listado[n] = listado_urls

    if listado:
        if item.ini:
            ini = item.ini
            del item.ini
        else:
            ini = 0

        for k in sorted(listado.keys())[ini:ini + 40]:
            itemlist.append(item.clone(
                url=listado[k],
                episode=k,
                action="findvideos",
                type='episode',
                content_type='servers'
            ))

        # paginacion
        if ini + 40 < len(listado):
            itemlist.append(item.clone(
                ini=ini + 40,
                type='next'))


    return itemlist


def findvideos(item):
    logger.trace()
    itemlist = list()

    if not isinstance(item.url, list):
        item.url = [item.url]

    for url in item.url:
        data = httptools.downloadpage(url).data
        #data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")

        data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|<br>", "", data)
        patron = "<img border=.*?src='([^']+).*?<b>Formato:?</b>:?\s*([^<]+).*?<b>Torrent.*?href='([^']+)"
        poster, quality, url = scrapertools.find_single_match(data,patron)

        # Simplificar quality
        quality = quality.replace('-', ' ').lower()
        if scrapertools.find_single_match(quality + ' ', ' 3d '):
            quality = '3d'
        elif scrapertools.find_single_match(quality + ' ', ' 1080p? '):
            quality = '1080p'
        elif scrapertools.find_single_match(quality + ' ', ' 720p? '):
            quality = '720p'
        else:
            quality = re.sub(chr(194), " ", quality)
            quality = re.sub(chr(160), " ", quality).strip()

        table_name = scrapertools.find_single_match(httptools.downloadpage(HOST + "/" + url).data, "Pincha <a href='.*?table:\s*'([^']+)',\s*name:\s*'([^']+)")
        if table_name:
            new_item = item.clone(
                action="play",
                url='%s/uploads/torrents/%s/%s' % (HOST, table_name[0], table_name[1]),
                quality=QLT.get(quality),
                poster=item.poster if item.poster.startswith(HOST) else poster.replace(' ', '%20'),
                type='server',
                server='torrent'
            )

            size = scrapertools.find_single_match(data, 'Tamaño:</b>(.*?)<').replace(',', '.')
            if size:
                n = float(scrapertools.find_single_match(size, '(\d[.\d]*)')) * 1024
                new_item.size = n * 1024 if 'gb' in size.lower() else n

            #logger.debug(new_item.url)
            itemlist.append(new_item)

    return servertools.get_servers_from_id(itemlist)

