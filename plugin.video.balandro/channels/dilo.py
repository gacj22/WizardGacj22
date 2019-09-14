# -*- coding: utf-8 -*-

import re, urllib

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, tmdb, jsontools

host = 'https://www.dilo.nu/'
host_catalogue = host + 'catalogue'

IDIOMAS = {'la':'Lat', 'es':'Esp', 'en_es':'VOSE', 'en':'VO'}

# Versión de Yape para series


def mainlist(item):
    return mainlist_series(item)

def mainlist_series(item):
    logger.info()
    itemlist = []
    
    itemlist.append(item.clone( title = 'Series más populares', action = 'list_all', url = host_catalogue ))
    itemlist.append(item.clone( title = 'Series de la semana', action = 'list_all', url = host_catalogue+'?sort=mosts-week' ))
    itemlist.append(item.clone( title = 'Últimas actualizadas', action = 'list_all', url = host_catalogue+'?sort=latest' ))

    itemlist.append(item.clone( title = 'Series en emisión', action = 'list_all', url = host_catalogue+'?status=0' ))
    itemlist.append(item.clone( title = 'Series finalizadas', action = 'list_all', url = host_catalogue+'?status=1' ))

    itemlist.append(item.clone( title = 'Por género', action = 'generos' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anyos' ))
    itemlist.append(item.clone( title = 'Por país', action = 'paises' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(host_catalogue).data

    patron = '<input type="checkbox" class="[^"]+" id="[^"]+" value="([^"]+)" name="genre\[\]">'
    patron += '<label class="custom-control-label" for="[^"]+">([^<]+)</label>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for valor, titulo in matches:
        itemlist.append(item.clone( title=titulo.strip(), url=host_catalogue+'?genre[]='+valor, action='list_all' ))

    return sorted(itemlist, key=lambda it: it.title)

def anyos(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1970, -1):
        itemlist.append(item.clone( title=str(x), url=host_catalogue+'?year[]='+str(x), action='list_all' ))
        
    return itemlist

def paises(item):
    logger.info()
    itemlist = []

    web_paises = [['AR', 'Argentina'], ['AU', 'Australia'], ['AT', 'Austria'], ['BE', 'B\xc3\xa9lgica'], ['BO', 'Bolivia'], ['BR', 'Brasil'], ['BG', 'Bulgaria'], ['CA', 'Canad\xc3\xa1'], ['CL', 'Chile'], ['CN', 'China'], ['CO', 'Colombia'], ['CR', 'Costa Rica'], ['HR', 'Croacia'], ['CU', 'Cuba'], ['CZ', 'Rep\xc3\xbablica Checa'], ['DK', 'Dinamarca'], ['EC', 'Ecuador'], ['SV', 'El Salvador'], ['FI', 'Finlandia'], ['FR', 'Francia'], ['DE', 'Alemania'], ['GR', 'Grecia'], ['GT', 'Guatemala'], ['HN', 'Honduras'], ['HK', 'Hong Kong'], ['HU', 'Hungr\xc3\xada'], ['IS', 'Islandia'], ['IN', 'India'], ['IE', 'Irlanda'], ['IL', 'Israel'], ['IT', 'Italia'], ['JP', 'Jap\xc3\xb3n'], ['LT', 'Lituania'], ['MY', 'Malasia'], ['MX', 'M\xc3\xa9xico'], ['NL', 'Pa\xc3\xadses Bajos'], ['NZ', 'Nueva Zelanda'], ['NO', 'Noruega'], ['PA', 'Panam\xc3\xa1'], ['PY', 'Paraguay'], ['PE', 'Per\xc3\xba'], ['PL', 'Polonia'], ['PT', 'Portugal'], ['PR', 'Puerto Rico'], ['RO', 'Rumania'], ['RU', 'Rusia'], ['RS', 'Serbia'], ['SG', 'Singapur'], ['ES', 'Espa\xc3\xb1a'], ['SE', 'Suecia'], ['CH', 'Suiza'], ['TH', 'Tailandia'], ['TR', 'Turqu\xc3\xada'], ['UA', 'Ucrania'], ['GB', 'Reino Unido'], ['US', 'Estados Unidos'], ['UY', 'Uruguay'], ['VE', 'Venezuela'] ]
    for x in sorted(web_paises, key=lambda x: x[1]):
        itemlist.append(item.clone( title=x[1], url=host_catalogue+'?country[]='+x[0], action='list_all' ))
        
    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)
    
    matches = re.compile('<div class="col-lg-2 col-md-3 col-6 mb-3"><a(.*?)</a></div>', re.DOTALL).findall(data)
    for article in matches:
        url = scrapertools.find_single_match(article, ' href="([^"]+)"')
        thumb = scrapertools.find_single_match(article, ' src="([^"]+)"')
        title = scrapertools.find_single_match(article, '<div class="text-white[^"]*">([^<]+)</div>').strip()
        year = scrapertools.find_single_match(article, '<div class="txt-gray-200 txt-size-\d+">(\d+)</div>')
        
        itemlist.append(item.clone( action='temporadas', url=url, title=title, thumbnail=thumb, 
                                    contentType='tvshow', contentSerieName=title, infoLabels={'year': year} ))

    tmdb.set_infoLabels(itemlist)

    next_page_link = scrapertools.find_single_match(data, '<li class="page-item"><a href="([^"]+)" aria-label="(?:Netx|Next)"')
    if next_page_link:
        itemlist.append(item.clone( title='>> Página siguiente', url=host_catalogue + next_page_link, action='list_all' ))

    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)
    
    item_id = scrapertools.find_single_match(data, 'data-json=\'\{"item_id": "([^"]+)')
    url = 'https://www.dilo.nu/api/web/seasons.php'
    post = 'item_id=%s' % item_id
    data = jsontools.load(httptools.downloadpage(url, post=post).data)
    for tempo in data:
        itemlist.append(item.clone( action='episodios', title='Temporada %s' % tempo['number'], item_id = item_id, 
                                    contentType='season', contentSeason=tempo['number'] ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


# Si una misma url devuelve los episodios de todas las temporadas, definir rutina tracking_all_episodes para acelerar el scrap en trackingtools.
# ~ def tracking_all_episodes(item):
    # ~ return episodios(item)


def episodios(item):
    logger.info()
    itemlist = []

    if not item.item_id:
        data = httptools.downloadpage(item.url).data
        # ~ logger.debug(data)
        item.item_id = scrapertools.find_single_match(data, 'data-json=\'\{"item_id": "([^"]+)')

    url = 'https://www.dilo.nu/api/web/episodes.php'
    post = 'item_id=%s&season_number=%s' % (item.item_id, item.contentSeason)
    data = jsontools.load(httptools.downloadpage(url, post=post).data)
    for epi in data:
        titulo = '%sx%s %s' % (epi['season_number'], epi['number'], epi['name'])
        plot = epi['description']
        langs = re.findall('languajes/([^.]+).png', epi['audio'])
        if langs: titulo += ' [COLOR pink][%s][/COLOR]' % ','.join([IDIOMAS.get(lang, lang) for lang in langs])

        itemlist.append(item.clone( action='findvideos', url=host+epi['permalink']+'/', title=titulo, plot=plot,
                                    contentType='episode', contentSeason=epi['season_number'], contentEpisodeNumber=epi['number'] ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)
    
    patron = '<a href="#" class="[^"]*" data-link="([^"]+)".*?/languajes/([^.]+).png'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, language in matches:
        if '/download?' in url: continue # descartar descargas directas !?

        server = scrapertools.find_single_match(url, '/servers/([^.]+)')
        # ~ logger.debug('%s %s %s' % (url, language, server))

        itemlist.append(Item( channel = item.channel, action = 'play', server = server,
                              title = '', url = url,
                              language = IDIOMAS.get(language, language)
                       ))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    # ~ logger.debug(data)
    
    url = scrapertools.find_single_match(data, 'iframe class="" src="([^"]+)')
    if host in url:
        url = httptools.downloadpage(url, follow_redirects=False, only_headers=True).headers.get('location', '')

    if url != '': 
        itemlist.append(item.clone(url = url))
    
    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + 'search?s=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
