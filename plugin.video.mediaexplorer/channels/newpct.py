# -*- coding: utf-8 -*-
from core.libs import *

HOST = settings.get_setting('host', __file__, getvalue=True)

LNG = Languages({
    Languages.es: ['Español Castellano', 'Castellano', 'Spanish', 'Espa', 'Español'],
    Languages.la: ['Español Latino'],
    Languages.sub_en: ['Ingles Subtitulado'],
    Languages.vos: ['V.O. Subt. Castellano']
})

QLT = Qualities({
    Qualities.hd_full: ['bluray 1080p', 'bluray microhd', 'bdremux', 'hdtv 1080p ac3 5.1', 'microhd'],
    Qualities.uhd:['4kultrahd', '4k', '4kuhdrip', '4kuhdremux', '4k uhdmicro'],
    Qualities.m3d:['bluray 3d 1080p'],
    Qualities.rip: ['blurayrip ac3 5.1', 'blurayrip', 'dvdrip', 'rip', 'dvdrip ac3 5.1'],
    Qualities.sd: ['hdtv'],
    Qualities.scr: ['bluray-screeener', 'ts-screener', 'dvd-screener', 'hdtv-screener', 'camrip'],
    Qualities.hd: ['hdtv 720p ac3 5.1', 'hdtv 720p']
})


def mainlist(item):
    logger.trace()
    itemlist = list()


    #itemlist.append(item.clone(type='label', label=HOST))

    new_item = item.clone(
        type='label',
        label="Películas",
        category='movie',
        banner='banner/movie.png',
        icon='icon/movie.png',
        poster='poster/movie.png'
    )
    itemlist.append(new_item)
    itemlist.extend(menupeliculas(new_item))

    new_item = item.clone(
        type='label',
        label="Series",
        category='tvshow',
        banner='banner/tvshow.png',
        icon='icon/tvshow.png',
        poster='poster/tvshow.png',
    )
    itemlist.append(new_item)
    itemlist.extend(menuseries(new_item))

    itemlist.append(item.clone(
        action="config",
        label="Configuración",
        folder=False,
        category='all',
        type='setting'
    ))

    return itemlist


def menupeliculas(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        action="movies",
        label="Películas en Español",
        categoryIDR=757,
        type="item",
        group=True,
        content_type='movies'
    ))

    itemlist.append(item.clone(
        action="movies",
        label="Películas en Latino",
        categoryIDR=1527,
        type="item",
        group=True,
        content_type='movies'
    ))

    itemlist.append(item.clone(
        action="movies",
        label="Películas subtituladas",
        categoryIDR=778,
        type="item",
        group=True,
        content_type='movies'
    ))

    itemlist.append(item.clone(
        action="movies",
        label="Películas HD",
        categoryIDR=1027,
        type="item",
        group=True,
        content_type='movies'
    ))

    itemlist.append(item.clone(
        action="movies",
        label="Películas 3D",
        categoryIDR=1599,
        type="item",
        group=True,
        content_type='movies'
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
        action="newest_episodes",
        label="Nuevos episodios",
        url=HOST + '/ultimas-descargas/',
        categoryIDR=767,
        type="item",
        group=True,
        content_type='episodes'
    ))

    itemlist.append(item.clone(
        action="newest_episodes",
        label="Nuevos episodios VO",
        url=HOST + '/ultimas-descargas/',
        categoryIDR=775,
        type="item",
        group=True,
        content_type='episodes'
    ))

    itemlist.append(item.clone(
        action="newest_episodes",
        label="Nuevos episodios HD",
        url=HOST + '/ultimas-descargas/',
        categoryIDR=1469,
        type="item",
        group=True,
        content_type='episodes'
    ))

    itemlist.append(item.clone(
        action="tvshows",
        label="Series SD",
        url= HOST + '/series/',
        type="item",
        group=True,
        content_type='tvshows'
    ))

    itemlist.append(item.clone(
        action="tvshows",
        label="Series HD",
        url=HOST + '/series-hd/',
        type="item",
        group=True,
        content_type='tvshows'
    ))

    itemlist.append(item.clone(
        action="tvshows",
        label="Series subtituladas",
        url=HOST + '/series-vo/',
        type="item",
        group=True,
        content_type='tvshows'
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


def search(item):
    logger.trace()
    itemlist = list()
    list_next_pages= list()

    if item.pages:
        list_pages = item.pages
    elif item.content_type == 'movies':
        list_pages = [(757,1) , (1027,1)]
    else:
        list_pages = [(767, 1), (1469, 1)]

    for categoryIDR, pg in list_pages:
        url = HOST + '/index.php?page=buscar&q=%s&categoryIDR=%s&pg=%s' % (item.query, categoryIDR, pg)
        data = httptools.downloadpage(url).data
        data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
        data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

        buscarlist = scrapertools.find_single_match(data, '<ul class="buscar-list">.*?<ul class="pagination">')

        for url, ficha in scrapertools.find_multiple_matches(buscarlist, '<li[^>]*><a href="([^"]+)"(.*?)</li>'):
            if '<span class="votadas">' in ficha:
                patron = '<img src="([^"]+).*?<h2 style="padding:0;">(.*?)</h2> </a>' \
                         '<span class="votadas">.*?</span><span>([^<]+)</span><span>([^<]+)'
            else:
                patron = 'src="([^"]+).*?<h2[^>]+>(.*?)</h2>\s*</a><span[^>]*>([^<]+)</span><span[^>]*>([^<]+)</span>'

            poster, info_label, date, size = scrapertools.find_single_match(ficha, patron)
            info_label = re.sub(r'(<.*?>)', '', info_label)
            n = float(scrapertools.find_single_match(size, '(\d[.\d]*)')) * 1024

            temporada = scrapertools.find_single_match(info_label, 'Temporadas? \d+')
            if (item.content_type == 'movies' and temporada) or (item.content_type == 'tvshows' and not temporada):
                continue

            new_item = item.clone(
                url=url,
                poster=poster if poster.startswith('http') else ('https:' + poster),
                date=date,
                size=n * 1024 if 'gb' in size.lower() else n
                )

            if item.content_type== 'movies':
                new_item.year = scrapertools.find_single_match(info_label, '[(|\[](\d+)[)|\]]')
                info_label = re.split(r'\[',info_label,1)
                new_item.title = info_label[0].strip()
                new_item.type = 'movie'
                new_item.content_type = 'servers'
                new_item.action = 'findvideos'
            else:
                info_label = re.split(r'Temporadas \d+',info_label)
                new_item.title = info_label[0].strip()
                new_item.tvshowtitle = info_label[0].strip()
                new_item.type = 'tvshow'
                new_item.content_type = 'seasons'
                new_item.action = 'seasons'

            if not info_label[0].strip():
                continue
            elif len(info_label) == 2:
                info_label = ' ' + re.sub(r'\[|]', ' ', info_label[1]) + ' '
            else:
                info_label = str(info_label)

            # Idioma
            for k in sorted(LNG.values.keys(), key=lambda x: len(x), reverse=True):
                if ' %s ' % k.lower() in info_label.lower():
                    new_item.lang = [LNG.values.get(k)]
                    break

            # Calidad
            for k in sorted(QLT.values.keys(), key=lambda x: len(x), reverse=True):
                if ' %s ' % k.lower() in info_label.lower():
                    new_item.quality = QLT.values.get(k)
                    break

            itemlist.append(new_item)

        # Ordenar por fecha de publicacion
        itemlist.sort(key=lambda x: datetime.datetime.strptime(x.date, '%d-%m-%Y'))
        next_page = scrapertools.find_single_match(data, '<li><a href="javascript:;" onClick="_pgSUBMIT\(([^)]+)\);">Next</a></li>')

        if next_page:
            list_next_pages.append((categoryIDR, int(next_page.replace("'", ""))))

    if list_next_pages:
        itemlist.append(item.clone(
            pages=list_next_pages,
            type='next'))

    return itemlist


def movies(item):
    logger.trace()
    itemlist = list()

    if not item.url:
        item.url = HOST + '/ultimas-descargas/'

    data = httptools.downloadpage(item.url, post={'categoryIDR':item.categoryIDR, 'date':'Siempre'}).data
    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    patron = '<li><a href="([^"]+)" title="([^"]+)"[^>]*><img style="width:160px;height:230px;" src="([^"]+)".*?<span id="deco" style="[^"]+">([^<]+)<strong style="float:right;">Tamaño ([^<]+).*?Idioma : </span><strong style="display:inline-block;width:200px;color:red;border:solid 1px red;padding:1px 5px;">(.*?)</strong></div>'

    for url, title, poster, qlt, size, lang in scrapertools.find_multiple_matches(data, patron):
        n = float(scrapertools.find_single_match(size, '(\d[.\d]*)')) * 1024

        title = re.sub(r'^(descarg\w)', '', title, flags=re.I)
        if item.categoryIDR == 1599:
            title = re.sub(r'3D', '', title)

        if qlt.strip().lower() == 'fullbluray':
            # El contenido completo del BluRay no se puede reproducir
            continue

        itemlist.append(item.clone(
            title= title.strip(),
            url=url,
            poster=poster if poster.startswith('http') else ('https:' + poster),
            size=n * 1024 if 'gb' in size.lower() else n,
            quality=QLT.get(qlt.strip().lower()),
            lang=[LNG.get(lang)],
            type='movie',
            content_type='servers',
            action='findvideos'
        ))

    # paginacion
    next_page = scrapertools.find_single_match(data, '<li><a href="([^"]+)">Next</a></li>')
    if next_page:
        itemlist.append(item.clone(
            url=next_page,
            type='next'))

    return itemlist


def newest_episodes(item):
    logger.trace()
    itemlist = list()

    if not item.url:
        item.url = HOST + '/ultimas-descargas/'

    data = httptools.downloadpage(item.url, post={'categoryIDR': item.categoryIDR, 'date': 'Siempre'}).data
    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")

    if 'descargas2020' in item.url:
        data = scrapertools.find_single_match(data, '<ul class="noticias-series">(.*?)</ul>')
        patron = '<li><a href="(?P<url>[^"]+)" title="[^"]+"><img style="width:160px;height:230px;" ' \
                 'src="(?P<poster>[^"]+)".*?<h2 style="font-size:18px;">(?P<title>[^<]+)</h2>\s*</a>\s*' \
                 '<span id="deco" style="margin-bottom:10px;">(?P<qlt>[^<]+)<strong style="float:right;">' \
                 'Tamaño (?P<size>[^<]+).*?Idioma : </span>(?P<lang>.*?)</strong></div>'
    else:
        patron = '<li><a href="(?P<url>[^"]+)" title="(?P<title>[^"]+)"><img style="width:160px;height:230px;" ' \
                 'src="(?P<poster>[^"]+)".*?<span id="deco" style="margin-bottom:10px;">(?P<qlt>[^<]+)' \
                 '<strong style="float:right;">Tamaño (?P<size>[^<]+).*?Idioma : </span>(?P<lang>.*?)</strong></div>'


    for result in re.compile(patron, re.DOTALL).finditer(data):
        season_episode = scrapertools.find_single_match(result.group('title'), 'temp\w*\.?\s*(\d+).*?cap\w*\.?\s*(\d+ al \d+)',
                                                        flags=re.DOTALL | re.IGNORECASE)
        if not season_episode:
            season_episode = scrapertools.find_single_match(result.group('title'), 'temp\w*\.?\s*(\d+).*?cap\w*\.?\s*([^\s]+)',
                                                            flags=re.DOTALL | re.IGNORECASE)
        if not season_episode:
            season_episode = scrapertools.get_season_and_episode(result.group('title'))

        if season_episode:
            tvshowtitle = result.group('title').split('-')[0].strip()
            num_episode = [int(n) for n in scrapertools.find_multiple_matches(season_episode[1], "(\d+)")]
            n = float(scrapertools.find_single_match(result.group('size'), '(\d[.\d]*)')) * 1024
            poster = result.group('poster') if result.group('poster').startswith('http') else ('https:' + result.group('poster'))

            new_item = item.clone(
                tvshowtitle=tvshowtitle,
                label=tvshowtitle,
                url=result.group('url'),
                #poster=poster,
                thumb=poster,
                episode=num_episode[0],
                season=int(season_episode[0]),
                size=n * 1024 if 'gb' in result.group('size').lower() else n,
                quality=QLT.get(result.group('qlt').strip().lower()),
                lang=[LNG.get(re.sub(r'(<.*?>)','', result.group('lang')))],
                type='episode',
                content_type='servers',
                action='findvideos'
            )

            # Renumerar episodio si es necesario
            if new_item.episode > 99 and new_item.episode / 100 == new_item.season:
                new_item.episode -= (new_item.episode / 100) * 100

            # Multiepisodios
            if len(num_episode) > 1:
                new_item.multi_episode = list()
                if 'al' in season_episode[1] and len(num_episode) == 2:
                    multi_episodes = range(num_episode[0], num_episode[1] + 1)
                else:
                    multi_episodes = num_episode

                # Renumerar Multiepisodios si es necesario
                for n_episodio in multi_episodes:
                    if n_episodio > 99 and n_episodio / 100 == new_item.season:
                        new_item.multi_episodes.append(n_episodio - (n_episodio / 100) * 100)
                    else:
                        new_item.multi_episodes = multi_episodes
                        break

            itemlist.append(new_item)

        else:
            logger.debug("Temporada y episodio no encontrado: %s" % (result.group('title')))

    return itemlist


def tvshows(item):
    logger.trace()
    itemlist = list()

    if not item.url:
        item.url = HOST + '/series-hd/'

    if not item.subpage:
        item.subpage = 1

    data = httptools.downloadpage(item.url).data
    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    pelilist = scrapertools.find_single_match(data, '<ul class="pelilist">.*?<ul class="pagination">')
    for url, ficha in scrapertools.find_multiple_matches(pelilist, '<li>\s*<a href="([^"]+)"(.*?)</li>'):
        if url[:-1] == item.url:
            continue

        patron = '<img src="([^"]+).*?<h2 style="height:28px;">([^<]+)</h2>\s*<span>([^<]+)'
        for poster, title, qlt in scrapertools.find_multiple_matches(ficha, patron):
            itemlist.append(item.clone(
                action='seasons',
                label=title,
                tvshowtitle=title,
                title=title,
                url=url,
                poster=poster if poster.startswith('http') else ('https:' + poster),
                quality=QLT.get(qlt.lower()),
                type='tvshow',
                content_type='seasons'
            ))

    #paginacion
    ini = (item.subpage - 1) * 20
    fin = item.subpage * 20

    if fin < len(itemlist) - 1:
        itemlist = itemlist[ini:fin]
        itemlist.append(item.clone(
            subpage= item.subpage + 1,
            type='next'))
    else:
        next_page = scrapertools.find_single_match(data, '<li><a href="([^"]+)">Next</a></li>')
        if next_page:
            itemlist = itemlist[ini:fin]
            itemlist.append(item.clone(
                url=next_page,
                subpage= 1,
                type='next'))


    return itemlist


def read_episodes(item, pages):
    logger.trace()
    itemlist = list()


    def get_episodes(item, url_page, itemlist):
        data = httptools.downloadpage(url_page).data
        data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
        patron = '<div class="info">\s+<a href="([^"]+)" title="[^"]+"><h2 style="padding:0;">(.*?)</h2></a>\s+' \
                 '<span>[^<]+</span>\s+<span>([^<]+)</span>'

        for url, info_label, size in scrapertools.find_multiple_matches(data, patron):
            info_label = re.sub(r'(<.*?>)|\[|]',' ', info_label)
            # Metodo 1: info_label='Serie  The Walking Dead - Temporada 1 COMPLETA  Capitulos 1 al 6  -  Español Castellano  Calidad    BluRayRip AC3 5.1'
            season_episode = scrapertools.find_single_match(info_label, 'temp\w*\.?\s*(\d+).*?cap\w*\.?\s*(\d+ al \d+)', flags=re.DOTALL|re.IGNORECASE)

            if not season_episode:
                # Metodo 2: 'Padre De Familia - Temp.10  HDTV  Cap.1016_1018  Spanish '
                #           'Padre De Familia - Temporada 6  DVDRIP  Caps.604-605-606-607  Spanish '
                #           'Padre De Familia - Temporada 6  DVDRIP  Capit. 4'
                season_episode = scrapertools.find_single_match(info_label, 'temp\w*\.?\s*(\d+).*?cap\w*\.?\s*([^\s]+)', flags=re.DOTALL|re.IGNORECASE)

            if not season_episode:
                # Metodo 3: info_label= "Serie The Walking Dead  season 4 episode 2 - Español Castellano Calidad  HDTV'
                season_episode = scrapertools.get_season_and_episode(info_label)

            if season_episode:
                num_episode = [int(n) for n in scrapertools.find_multiple_matches(season_episode[1], "(\d+)")]
                n = float(scrapertools.find_single_match(size, '(\d[.\d]*)')) * 1024

                new_item = item.clone(
                    title=item.tvshowtitle,
                    url=url,
                    action="findvideos",
                    episode=num_episode[0],
                    season=int(season_episode[0]),
                    size=n * 1024 if 'gb' in size.lower() else n,
                    type='episode',
                    content_type='servers'
                )

                # Renumerar episodio si es necesario
                if new_item.episode > 99 and new_item.episode/100 == new_item.season:
                    new_item.episode -= (new_item.episode/100) * 100

                # Multiepisodios
                if len(num_episode) > 1:
                    new_item.multi_episode = list()
                    if 'al' in season_episode[1] and len(num_episode) == 2:
                        multi_episodes = range(num_episode[0], num_episode[1] + 1)
                    else:
                        multi_episodes = num_episode

                    # Renumerar Multiepisodios si es necesario
                    for n_episodio in multi_episodes:
                        if n_episodio > 99 and n_episodio/100 == new_item.season:
                            new_item.multi_episodes.append(n_episodio - (n_episodio/100) * 100)
                        else:
                            new_item.multi_episodes = multi_episodes
                            break

                # Idioma
                for k in sorted(LNG.values.keys(), key=lambda x: len(x), reverse=True):
                    if ' %s ' % k in info_label:
                        new_item.lang = LNG.values.get(k)
                        break

                # Calidad
                for k in sorted(QLT.values.keys(), key=lambda x: len(x), reverse=True):
                    if ' %s ' % k in info_label:
                        new_item.quality = QLT.values.get(k)
                        break

                itemlist.append(new_item)

            else:
                logger.debug("Temporada y episodio no encontrado: %s - %s" % (info_label, url_page))



    threads = list()

    for p in pages:
        t = Thread(target=get_episodes, args=[item, item.url + '/pg/%s' % p, itemlist])
        t.setDaemon(True)
        t.start()
        threads.append(t)

    while [t for t in threads if t.isAlive()]:
        time.sleep(0.5)

    return itemlist


def seasons(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    last = scrapertools.find_single_match(data, '<li><a href="%s/pg/(\d+)">Last</a></li>' % item.url)

    pages = (range(1,int(last)+1)) if last else [1]
    for t in sorted(set(e.season for e in read_episodes(item, pages))):
        itemlist.append(item.clone(
            pages=pages,
            season=t,
            action="episodes",
            type='season',
            content_type='episodes'
        ))

    return itemlist


def episodes(item):
    logger.trace()
    itemlist = list()

    if item.pages:
        itemlist = [e for e in read_episodes(item, item.pages) if e.season == item.season]

    return sorted(itemlist, key=lambda e: e.episode)


def findvideos(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = unicode(data, "iso-8859-1", errors="replace").encode("utf-8")
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    # Torrent
    new_item = item.clone(
        action="play",
        url=urlparse.urljoin(HOST, scrapertools.find_single_match(data, 'window.location.href\s+=\s+"([^"]+)";')),
        type='server',
        server='torrent'
    )
    try:
        new_item.lang = item.lang[0]
    except:
        pass
    itemlist.append(new_item)

    # Ver y descargar en 1 Link
    patron = """<div class="box2">([^<]+)</div><div class="box3">([^<]+)</div><div class="box4">([^<]+)</div>"""
    patron += """<div class="box5"><a href='([^']+)'[^>]+>([^<]+)</a></div><div class="box6">([^<]+)</div>"""
    for server, lang, quality, url, type, links in scrapertools.find_multiple_matches(data, patron):
        if '1 Link' in links:
            itemlist.append(item.clone(
                url=url,
                action='play',
                type='server',
                lang=LNG.get(lang),
                quality=QLT.get(quality.lower()),
                server=server,
                size=None,
                stream=False if 'DESCARGAR' in type else True
            ))

    return servertools.get_servers_from_id(itemlist)


def play(item):
    logger.trace()

    if item.server == 'powvideo':
        servertools.normalize_url(item)

    return item


def config(item):
    v = platformtools.show_settings(item=item)
    platformtools.itemlist_refresh()
    return v