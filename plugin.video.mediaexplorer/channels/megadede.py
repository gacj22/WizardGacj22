# -*- coding: utf-8 -*-
from core.libs import *

LNG = Languages({
    Languages.sub_es: ['SUBspanish', 'SUBothers'],
    Languages.es: ['spanish'],
    Languages.sub_en: ['SUBenglish'],
    Languages.en: ['english'],
    Languages.la: ['latino'],
})

QLT = Qualities({
    Qualities.hd_full: ['Hd 1080'],
    Qualities.hd: ['Hd 720', 'Hd Micro'],
    Qualities.rip: ['Hd Rip', 'Dvd Rip', 'Rip'],
    Qualities.scr: ['Ts Screener', 'Tc Screener', 'Dvd Screener'],
})


def mainlist(item):
    logger.trace()
    itemlist = []

    if not login():
        itemlist.append(item.clone(
            action="config",
            label="Configuración",
            folder=False,
            type='setting'
        ))
    else:
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
        label='Novedades',
        action='movies',
        url='https://www.megadede.com/pelis',
        content_type='movies',
        type="item",
        group=True
    ))

    itemlist.append(item.clone(
        label='Mas vistas',
        action='movies',
        url='https://www.megadede.com/pelis/top',
        content_type='movies',
        type="item",
        group=True
    ))

    itemlist.append(item.clone(
        label='Todas',
        action='movies',
        url='https://www.megadede.com/pelis/all',
        content_type='movies',
        type="item",
        group=True
    ))

    itemlist.append(item.clone(
        label='Buscar',
        action='movie_search',
        content_type='movies',
        query=True,
        group=True,
        type='search'
    ))
    return itemlist


def menuseries(item):
    logger.trace()

    itemlist = list()

    itemlist.append(item.clone(
        label='Novedades',
        action='tvshows',
        url='https://www.megadede.com/series',
        type="item",
        group=True,
        content_type='tvshows'
    ))

    itemlist.append(item.clone(
        label='Mas vistas',
        action='tvshows',
        url='https://www.megadede.com/series/top',
        type="item",
        group=True,
        content_type='tvshows'
    ))

    itemlist.append(item.clone(
        label='Todas',
        action='tvshows',
        url='https://www.megadede.com/series/all',
        type="item",
        group=True,
        content_type='tvshows'
    ))

    itemlist.append(item.clone(
        label='Buscar',
        action='tv_search',
        content_type='tvshows',
        query=True,
        group=True,
        type='search'
    ))
    return itemlist


def movies(item):
    logger.trace()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = 'data-id="(?P<id>[^"]+)".*?<a href="(?P<url>[^"]+)" data-toggle.*?title="(?P<title>[^"]+)".*?' \
             'src="(?P<thumb>[^"]+)".*?class="year">(?P<year>[\d]+).*?' \
             '</i>(?P<rating>[^<]+)</div>'

    for result in re.compile(patron, re.DOTALL).finditer(data):
        itemlist.append(item.clone(
            action='findvideos',
            label=result.group('title'),
            url='https://www.megadede.com/aportes/4/%s' % result.group('id'),  # result.group('url'),
            poster=result.group('thumb'),
            rating=result.group('rating'),
            title=result.group('title'),
            year=result.group('year'),
            plusdedeid=result.group('id'),
            type='movie',
            content_type='servers'
        ))

    return itemlist


def tvshows(item):
    logger.trace()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '<a href="(?P<url>[^"]+)" data-toggle.*?title="\d+x\d+ (?P<title>[^"]+)".*?' \
             'src="(?P<thumb>[^"]+)".*?class="year">(?P<year>[\d]+).*?' \
             '</i>(?P<rating>[^<]+).*?data-id="(?P<id>[^"]+)"'

    if item.category == 'episode':
        # Novedades Episodios
        patron = '<a href="(?P<url>[^"]+)" data-toggle.*?title="(?P<season>[\d]+)x(?P<episode>[\d]+) (?P<title>[^"]+)".*?' \
                 'src="(?P<thumb>[^"]+)".*?class="year">(?P<year>[\d]+).*?' \
                 '</i>(?P<rating>[^<]+).*?data-id="(?P<id>[^"]+)"'

    for result in re.compile(patron, re.DOTALL).finditer(data):
        new_item = item.clone(
            action='seasons',
            label=result.group('title'),
            url=result.group('url'),
            poster=result.group('thumb'),
            rating=result.group('rating'),
            title=result.group('title'),
            year=result.group('year'),
            plusdedeid=result.group('id'),
            type='tvshow',
            content_type='seasons'
        )

        if item.category == 'episode':
            new_item.episode = int(result.group('episode'))
            new_item.season = int(result.group('season'))
            new_item.tvshowtitle = result.group('title').strip()
            new_item.action = 'episodes_newest'
            new_item.type = "episode"
            new_item.content_type = 'servers'

        itemlist.append(new_item)

    return itemlist


def seasons(item):
    logger.trace()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    patron = '<a href="#" class="season-link[^"]+" data-season="(?P<season>[^"]+)">' \
             '(?P<title>[^<]+)<span class="fa fa-angle-right">'

    for result in re.compile(patron, re.DOTALL).finditer(data):
        itemlist.append(item.clone(
            action='episodes',
            label=result.group('title').strip(),
            season=int(result.group('season')),
            type='season',
            content_type='episodes'
        ))

    return itemlist


def episodes(item):
    logger.trace()
    itemlist = []

    data = httptools.downloadpage(item.url).data

    data = scrapertools.find_single_match(data, '<ul.*?data-season="%s" >(.*?)</ul>' % item.season)

    patron = 'data\-href="(?P<url>[^"]+)">.*?<span class="num">(?P<episode>\d+)</span>' \
             '(?P<title>[^<]+).*?"date">\s+(?P<date>[^\s]+)\s+</div>.*?<i class="fa fa-wifi" aria-hidden="true">' \
             '</i>\s+(?P<stream>\d+)</div>.*?<i class="fa fa-download" aria-hidden="true"></i>\s+(?P<down>\d+)</div>'

    for result in re.compile(patron, re.DOTALL).finditer(data):
        if result.group('stream') != '0' or result.group('down') != '0':
            itemlist.append(item.clone(
                action='findvideos',
                episode=int(result.group('episode')),
                title=result.group('title').strip(),
                tvshowtitle=item.title,
                aired=result.group('date'),
                url=result.group('url'),
                type='episode',
                content_type='servers'
            ))

    return itemlist


def episodes_newest(item):
    logger.trace()

    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, '<ul.*?data-season="%s" >(.*?)</ul>' % item.season)

    patron = 'data\-href="(?P<url>[^"]+)">.*?<span class="num">(?P<episode>\d+)</span>' \
             '(?P<title>[^<]+).*?"date">\s+(?P<date>[^\s]+)\s+</div>'

    for result in re.compile(patron, re.DOTALL).finditer(data):
        if int(result.group('episode')) != item.episode:
            continue

        new_item = item.clone(
            title=result.group('title').strip(),
            aired=result.group('date'),
            url=result.group('url'),
        )
        return findvideos(new_item)

    return []


def login():
    logger.trace()

    data = httptools.downloadpage('https://www.megadede.com/login').data
    captcha = scrapertools.find_single_match(data, '<img src="([^"]+)" alt="captcha">')
    _token = scrapertools.find_single_match(data, '<input name="_token" type="hidden" value="([^"]+)">')
    username = scrapertools.find_single_match(data, '<span class="username">([^<]+)<i')

    if username and username == settings.get_setting('user', __file__):
        return True
    elif username:
        httptools.downloadpage('https://www.megadede.com/logout')
        data = httptools.downloadpage('https://www.megadede.com/login').data
        captcha = scrapertools.find_single_match(data, '<img src="([^"]+)" alt="captcha">')
        _token = scrapertools.find_single_match(data, '<input name="_token" type="hidden" value="([^"]+)">')

    post = {'email': settings.get_setting('user', __file__),
            'password': settings.get_setting('password', __file__),
            '_token': _token
            }
    if captcha:
        value = platformtools.show_captcha(captcha)
        post['captcha'] = value

    data = httptools.downloadpage('https://www.megadede.com/login', post=post).data

    post = {'setting_4': 1,
            '_token': _token
            }

    if not '"redirect":"https:\\/\\/www.megadede.com"' in data:
        platformtools.dialog_notification('Megadede', 'Login incorrecto')
        return False
    else:
        return True


def movie_search(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url or 'https://www.megadede.com/search/%s' % item.query).data

    patron = 'data-id="(?P<id>[^"]+)".*?<a href="(?P<url>[^"]+)" data-toggle.*?title="(?P<title>[^"]+)".*?' \
             'src="(?P<thumb>[^"]+)".*?class="year">(?P<year>[\d]+).*?' \
             '</i>(?P<rating>[^<]+).*?<div class="media-sub">(?P<type>[^<]+)</div>'

    for result in re.compile(patron, re.DOTALL).finditer(data):
        if not result.group('type') == 'película':
            continue

        itemlist.append(item.clone(
            action='findvideos',
            label=result.group('title'),
            url='https://www.megadede.com/aportes/4/%s' % result.group('id'),  # result.group('url'),
            poster=result.group('thumb'),
            rating=result.group('rating'),
            title=result.group('title'),
            year=result.group('year'),
            plusdedeid=result.group('id'),
            type='movie',
            content_type='servers'
        ))

    return itemlist


def tv_search(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url or 'https://www.megadede.com/search/%s' % item.query).data

    patron = '<a href="(?P<url>[^"]+)" data-toggle.*?title="(?P<title>[^"]+)".*?' \
             'src="(?P<thumb>[^"]+)".*?class="year">(?P<year>[\d]+).*?' \
             '</i>(?P<rating>[^<]+).*?<div class="media-sub">(?P<type>[^<]+)</div>.*?data-id="(?P<id>[^"]+)"'

    for result in re.compile(patron, re.DOTALL).finditer(data):
        if not result.group('type') == 'serie':
            continue

        itemlist.append(item.clone(
            action='seasons',
            label=result.group('title'),
            url=result.group('url'),
            poster=result.group('thumb'),
            rating=result.group('rating'),
            title=result.group('title'),
            year=result.group('year'),
            plusdedeid=result.group('id'),
            type='tvshow',
            content_type='seasons'
        ))

    return itemlist


def findvideos(item):
    logger.trace()
    itemlist = []

    data = httptools.downloadpage(urlparse.urljoin('https://www.megadede.com/', item.url)).data

    patron = 'data-v.*?href="(?P<url>[^"]+)".*?src=".*?/(?P<server>[^./]+).png.*?' \
             'class="language">(?P<langblock>.*?)</div>.*?' \
             'fa-video-camera"></span>\s+(?P<quality>[^<\n]+)\n*\s+</div>.*?' \
             'fa-headphones"></span>\s+(?P<audio>[^<\n]+)\n*\s+</div>[\s]+' \
             '(<div class="size">[\s+]+<span class="fa fa-download"></span>\n*\s+' \
             '(?P<size>[^<\n]+)\n*\s+</div>)?'

    for result in re.compile(patron, re.DOTALL).finditer(data):
        lang = [''.join(l) for l in scrapertools.find_multiple_matches(
            result.group('langblock'),
            '(?:<span class="sub">([^<]+)?</span>\s+)?<img src="[^"]+/([^.]+).png"/>')][-1]

        size = None
        if result.group('size'):
            size = float(scrapertools.find_single_match(result.group('size'),'([\d,]+)').replace(',','.'))
            if 'GB' in result.group('size'):
                size = size * 1024 * 1024
            elif 'MB' in result.group('size'):
                size = size * 1024
            elif 'KB' in result.group('size'):
                size = size
            else:
                size = None


        itemlist.append(item.clone(
            action='play',
            url=result.group('url'),
            server=result.group('server'),
            quality=QLT.get(result.group('quality')),
            lang=LNG.get(lang),
            stream=not result.group('size'),
            size=size,
            type='server',
        ))

    itemlist = servertools.get_servers_from_id(itemlist)

    return itemlist


def play(item):
    logger.trace()

    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(
        data,
        '<a href="([^"]+)" target="_blank"><button class="btn btn-primary">visitar enlace</button></a>'
    )
    url = httptools.downloadpage(urlparse.urljoin(item.url, url), follow_redirects=False).headers['location']
    item.url = url
    servertools.normalize_url(item)

    return item


def config(item):
    v = platformtools.show_settings()
    platformtools.itemlist_refresh()
    return v
