# -*- coding: utf-8 -*-

import re, urlparse

from platformcode import config, logger
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


HOST = 'http://seriesdanko.to/'
IDIOMAS = {'es': 'Esp', 'la': 'Lat', 'vos': 'VOSE', 'vo': 'VO', 'ca': 'Cat'}


def configurar_proxies(item):
    from core import proxytools
    return proxytools.configurar_proxies_canal(item.channel, HOST)

def do_downloadpage(url, post=None):
    # ~ url = url.replace('seriesdanko.to', 'seriesdanko.net') # por si viene de enlaces guardados
    # ~ data = httptools.downloadpage(url, post=post).data
    data = httptools.downloadpage_proxy('seriesdanko', url, post=post).data
    return data


def mainlist(item):
    return mainlist_series(item)

def mainlist_series(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title='Nuevos capítulos', action='novedades' ))

    itemlist.append(item.clone( title='Listado alfabético', action='listado_alfabetico' ))

    itemlist.append(item.clone( title = 'Buscar serie ...', action = 'search', search_type = 'tvshow' ))

    plot = 'Es posible que para poder utilizar este canal necesites configurar algún proxy, ya que no es accesible desde algunos países/operadoras.'
    plot += '[CR]Si desde un navegador web no te funciona el sitio seriesdanko.to necesitarás un proxy.'
    itemlist.append(item.clone( title = 'Configurar proxies a usar ...', action = 'configurar_proxies', folder=False, plot=plot, text_color='red' ))

    return itemlist


def extraer_de_titulo(txt):
    # ~ Una aldea francesa 1x04 Español Disponible
    # ~ The City & The City Completa Español Disponible
    # ~ The Gymkhana Files 1x03 1x04 1x05 1x06 Vose
    # ~ Legacies 1x05 Español y Vose Disponible
    # ~ Control de fronteras: España 5x01 y 5x02 Español Disponible
    # ~ Hero Mask (2018) Temporada 1 Vose Disponible
    # ~ Dinastias (Dynasties) 1x03 Español Disponible
    def separa(txt):
        aux = txt.split('~sep~')
        show = aux[0].strip()
        langs = aux[-1].strip()
        return show, langs

    txt = scrapertools.decodeHtmlentities(txt)
    txt = txt.replace('Disponible','').replace('Ya', '').strip()
    season = ''
    episode = ''

    s_e = re.findall('(\d+)x(\d+)', txt)
    if s_e:
        season, episode = s_e[-1]
        txt = re.sub('(\d+)x(\d+)', '~sep~', txt)
        show, langs = separa(txt)

    else:
        tempo = re.findall('temporada (\d+)', txt, re.IGNORECASE)
        if tempo:
            season = tempo[0]
            txt = re.sub('temporada (\d+)', '~sep~', txt, flags=re.IGNORECASE)
            show, langs = separa(txt)

        else:
            tempo = re.findall(' completa ', txt, re.IGNORECASE)
            if tempo:
                txt = re.sub(' completa ', '~sep~', txt, flags=re.IGNORECASE)
                show, langs = separa(txt)

            else:
                show = txt
                langs = ''

    showalt = scrapertools.find_single_match(show, '\((.*)\)$') # si acaba en (...) puede ser el título traducido ej: Cast (Eng)
    if showalt != '':
        show = show.replace('(%s)' % showalt, '').strip()
        if showalt.isdigit(): showalt = '' # si sólo hay dígitos no es un título alternativo

    return show, season, episode, langs, showalt

def novedades(item):
    logger.info()
    itemlist = []

    if item.page == '': item.page = 0
    perpage = 10

    data = do_downloadpage(HOST)
    # ~ logger.debug(data)
    
    matches = re.findall("<div class='post-header'>(.*?)</span>", data, re.DOTALL)

    for serie_data in matches[item.page * perpage:]:
        # ~ logger.debug(serie_data)
        title = scrapertools.find_single_match(serie_data, "title='([^']+)'")
        if title == '': title = scrapertools.find_single_match(serie_data, 'title="([^"]+)"')

        url = scrapertools.find_single_match(serie_data, 'href="([^"]+)"')
        if url == '': url = scrapertools.find_single_match(serie_data, "href='([^']+)'")

        img = scrapertools.find_single_match(serie_data, "src='([^']+)'")

        show, season, episode, langs, showalt = extraer_de_titulo(title)
        if show == '': continue
        
        if episode != '':
            titulo = '%s - %sx%s [%s]' % (show, season, episode, langs)
            numserie = scrapertools.find_single_match(url, 'serie=(.+)')
            url_capitulo = urlparse.urljoin(HOST, 'capitulo.php?serie=%s&temp=%s&cap=%s' % (numserie, season, episode))
            
            # Menú contextual: ofrecer acceso a temporada / serie
            context = []
            context.append({ 'title': '[COLOR pink]Listar temporada %s[/COLOR]' % season, 
                             'action': 'episodios', 'url': urlparse.urljoin(HOST, url), 'context': '', 'folder': True, 'link_mode': 'update' })
            context.append({ 'title': '[COLOR pink]Listar temporadas[/COLOR]',
                             'action': 'temporadas', 'url': urlparse.urljoin(HOST, url), 'context': '', 'folder': True, 'link_mode': 'update' })
            
            itemlist.append(item.clone( action='findvideos', url=url_capitulo, title=titulo, thumbnail=img, context=context, 
                                        contentType = 'episode', contentSerieName = show, contentSeason=season, contentEpisodeNumber=episode, contentTitleAlt=showalt ))

        elif season != '':
            # Menú contextual: ofrecer acceso a serie
            context = []
            context.append({ 'title': '[COLOR pink]Listar temporadas[/COLOR]',
                             'action': 'temporadas', 'url': urlparse.urljoin(HOST, url), 'context': '', 'folder': True, 'link_mode': 'update' })
            
            titulo = '%s - Temporada %s [%s]' % (show, season, langs)
            itemlist.append(item.clone( action='episodios', url=urlparse.urljoin(HOST, url), title=titulo, thumbnail=img, context=context,
                                        contentType = 'season', contentSerieName = show, contentSeason=season, contentTitleAlt=showalt ))

        else:
            itemlist.append(item.clone( action='temporadas', url=urlparse.urljoin(HOST, url), title=show, thumbnail=img,
                                        languages=langs,
                                        contentType = 'tvshow', contentSerieName = show, contentTitleAlt=showalt ))

        if len(itemlist) >= perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if len(matches) > (item.page + 1) * perpage:
        itemlist.append(item.clone( title="Siguiente >>", page=item.page + 1 ))

    return itemlist



def listado_alfabetico(item):
    logger.info()
    itemlist = []

    for letra in '0ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        itemlist.append(item.clone( action='series_por_letra', title=letra, url=urlparse.urljoin(HOST, 'series.php?id=%s' % letra)))

    return itemlist

def series_por_letra(item):
    logger.info("letra = {0}".format(item.title))
    itemlist = []

    if item.page == '': item.page = 0
    perpage = 10

    data = do_downloadpage(item.url)

    matches = re.findall("<a href='([^']+)' title='Capitulos de: ([^']+)'><img class='ict' src='([^']*)", data)
    for url, title, img in matches[item.page * perpage:]:

        itemlist.append(item.clone( action='temporadas', url=urlparse.urljoin(HOST, url), title=title, 
                                    contentType = 'tvshow', contentSerieName = title, thumbnail=img ))

        if len(itemlist) >= perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if len(matches) > (item.page + 1) * perpage:
        itemlist.append(item.clone( title="Siguiente >>", page=item.page + 1 ))

    return itemlist



def temporadas(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    # Si viene de novedades, limpiar season, episode
    if item.contentEpisodeNumber: item.__dict__['infoLabels'].pop('episode')
    if item.contentSeason: item.__dict__['infoLabels'].pop('season')

    temporadas = re.findall('<div id="T(\d+)"', data)
    for tempo in temporadas:

        itemlist.append(item.clone( action='episodios', title='Temporada ' + tempo, 
                                    contentType = 'season', contentSeason = tempo ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


# Si una misma url devuelve los episodios de todas las temporadas, definir rutina tracking_all_episodes para acelerar el scrap en trackingtools.
def tracking_all_episodes(item):
    return episodios(item)


def episodios(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    patron = "<a href='([^']+)'>.*?(\d+)X(\d+) - (.*?)</a> (.*?)(?:<br>|</div)"
    episodes = re.findall(patron, data, re.MULTILINE | re.DOTALL)

    for url, season, episode, title, langs in episodes:

        if item.contentSeason and item.contentSeason != int(season):
            continue

        languages = ', '.join([IDIOMAS.get(lang, lang) for lang in re.findall('banderas/([^\.]+)', langs)])
        titulo = '%sx%s %s [%s]' % (season, episode, title, languages)

        itemlist.append(item.clone( action='findvideos', url=urlparse.urljoin(HOST, url), title=titulo, 
                                    contentType = 'episode', contentSeason = season, contentEpisodeNumber = episode ))

    tmdb.set_infoLabels(itemlist)

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = do_downloadpage(item.url)

    patron = "<tr><td class='tam12'><img src='/assets/img/banderas/([^\.]+).png' width='[^']*' height='[^']*' /></td>"
    patron += "<td class='tam12'>([^<]*)</td>"
    patron += "<td class='tam12'><img src='/assets/img/servidores/([^\.]+).jpg' width='[^']*' height='[^']*' style='[^']*' /></td>"
    patron += "<td><a class='capitulo2' href='([^']+)' rel='nofollow' alt=''>([^<]*)</a></td>"
    patron += "<td class='tam12'>([^<]*)</td></tr>"

    matches = re.findall(patron, data, re.MULTILINE | re.DOTALL)
    
    for lang, date, server, url, tipo, quality in matches:
        if tipo == 'Descargar': # descartar descargas directas ?
            continue

        itemlist.append(Item( channel = item.channel, action = 'play', server=server, 
                              title = '', url = urlparse.urljoin(HOST, url),
                              language = IDIOMAS.get(lang, lang), quality = quality, age = date
                       ))

    return itemlist


def play(item):
    logger.info("play url=%s" % item.url)

    data = do_downloadpage(item.url)

    url = scrapertools.find_single_match(data, '<a target="_blank" href="([^"]+)">')

    itemlist = servertools.find_video_items(data=url)

    return itemlist


def search(item, texto):
    logger.info("texto=%s" % texto)
    itemlist = []

    try:
        item.url = urlparse.urljoin(HOST, 'all.php')
        data = do_downloadpage(item.url)

        matches = re.findall("<a href='([^']+)' target='_blank'>([^<]+)</a>", data)
        for url, title in matches:
            if texto not in title.lower(): continue

            itemlist.append(item.clone( title=title, url=urlparse.urljoin(HOST, url), action='temporadas', 
                                        contentType='tvshow', contentSerieName=title ))

        tmdb.set_infoLabels(itemlist)

    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)

    return itemlist
