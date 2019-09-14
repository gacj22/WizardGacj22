# -*- coding: utf-8 -*-

import re, urllib

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger

__modo_grafico__ = config.get_setting('modo_grafico', "ver-pelis")
host = "http://ver-pelis.tv"
lang_title = {"latino": "[COLOR red][B] [LAT][/B][/COLOR]",
            "spanish": "[COLOR crimson][B] [ESP][/B][/COLOR]",
            "subtitulos": "[COLOR orangered][B] [VOS][/B][/COLOR]",
            "subtitulosp": "[COLOR indianred][B] [VOSE][/B][/COLOR]"}

def mainlist(item):
    logger.info()
    itemlist = []
    global i
    i = 0
    itemlist.append(
        item.clone(title="[COLOR oldlace]Películas[/COLOR]", action="scraper", url=host + "/ver/",
                   thumbnail="http://imgur.com/36xALWc.png", fanart="http://imgur.com/53dhEU4.jpg",
                   contentType="movie"))
    itemlist.append(item.clone(title="[COLOR oldlace]Latino[/COLOR]", action="scraper",
                               url=host + "/ver/latino/", thumbnail="http://imgur.com/36xALWc.png",
                               fanart="http://imgur.com/53dhEU4.jpg", contentType="movie"))
    itemlist.append(item.clone(title="[COLOR oldlace]Español[/COLOR]", action="scraper",
                               url=host + "/ver/espanol/", thumbnail="http://imgur.com/36xALWc.png",
                               fanart="http://imgur.com/53dhEU4.jpg", contentType="movie"))
    itemlist.append(item.clone(title="[COLOR oldlace]Subtituladas[/COLOR]", action="scraper",
                               url=host + "/ver/subtituladas/", thumbnail="http://imgur.com/36xALWc.png",
                               fanart="http://imgur.com/53dhEU4.jpg", contentType="movie"))
    itemlist.append(item.clone(title="[COLOR oldlace]Por Año[/COLOR]", action="categoria_anno",
                               url=host, thumbnail="http://imgur.com/36xALWc.png", extra="Por año",
                               fanart="http://imgur.com/53dhEU4.jpg", contentType="movie"))
    itemlist.append(item.clone(title="[COLOR oldlace]Por Género[/COLOR]", action="categoria_anno",
                               url=host, thumbnail="http://imgur.com/36xALWc.png", extra="Categorias",
                               fanart="http://imgur.com/53dhEU4.jpg", contentType="movie"))

    itemlist.append(itemlist[-1].clone(title="[COLOR orangered]Buscar[/COLOR]", action="search",
                                       thumbnail="http://imgur.com/ebWyuGe.png", fanart="http://imgur.com/53dhEU4.jpg",
                                       contentType="tvshow"))

    return itemlist


def categoria_anno(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, 'mobile_menu.*?(%s.*?)</ul>' % item.extra)
    patron = '(?is)<li.*?a href="([^"]+)'
    patron += '.*?title="[^"]+">([^<]+)'
    match = scrapertools.find_multiple_matches(bloque, patron)
    for url, titulo in match:
        itemlist.append(Item(
            channel=item.channel,
            action="scraper",
            title=titulo,
            url=url
        ))

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/ver/buscar?s=" + texto
    item.extra = "search"
    if texto != '':
        return scraper(item)


def scraper(item):
    logger.info()
    itemlist = []
    url_next_page = ""
    global i
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<a class="thumb cluetip".*?href="([^"]+)".*?src="([^"]+)" alt="([^"]+)".*?"res">([^"]+)</span>'
    patron = scrapertools.find_multiple_matches(data, patron)
    if len(patron) > 20:
        if item.next_page != 20:
            url_next_page = item.url
            patron = patron[:20]
            next_page = 20
            item.i = 0
        else:
            patron = patron[item.i:][:20]
            next_page = 20
            url_next_page = item.url
    for url, thumb, title, cuality in patron:
        title = re.sub(r"Imagen", "", title)
        titulo = "[COLOR floralwhite]" + title + "[/COLOR]" + " " + "[COLOR crimson][B]" + cuality + "[/B][/COLOR]"
        title = re.sub(r"!|\/.*", "", title).strip()

        if item.extra != "search":
            item.i += 1
        itemlist.append(item.clone(action="findvideos", title=titulo, url=url, thumbnail=thumb,
                                   contentTitle=title, contentType="movie", library=True))

    ## Paginación
    if url_next_page:
        itemlist.append(item.clone(title="[COLOR crimson]Siguiente >>[/COLOR]", url=url_next_page, next_page=next_page,
                                   thumbnail="http://imgur.com/w3OMy2f.png", i=item.i))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    duplicated = []
    data = httptools.downloadpage(item.url).data
    data_post = scrapertools.find_single_match(data, "var dataid=\{id:(.*?),slug:'([^']+)',imdb:'([^']+)'")
    if data_post:
        get = '?id=%s&slug=%s&imdb=%s' % (data_post[0], data_post[1], data_post[2])
        
        #sub = '%s/subti/%s.srt' % (host, data_post[2])
        json_data = httptools.downloadpage(host + '/core/api.php%s' % get).json
        video_list = json_data['lista']
        for videoitem in video_list:
            video_base_url = host + '/ajax/verpelis1.php'
            if video_list[videoitem] != None:
                video_lang = video_list[videoitem]
                logger.error(video_lang)
                languages = ['latino', 'spanish', 'subtitulos', 'subtitulosp']
                for lang in languages:
                    if lang not in video_lang:
                        continue
                    if video_lang[lang] != None:
                        if not isinstance(video_lang[lang], int):
                            video_id = video_lang[lang][0]["video"]
                            server = video_lang[lang][0]["servidortxt"].lower()
                            if not "ultra" in server:
                                servert = "[COLOR cyan][B]" + server.capitalize() + " [/B][/COLOR]"
                                extra = ""
                            else:
                                servert = "[COLOR yellow][B]Gvideo [/B][/COLOR]"
                                extra = "yes"
                            quality = video_lang[lang][0]["calidad"]
                            get = "?imdb=%s&video=%s&version=%s" % (data_post[2], video_id, lang)
                            embed = httptools.downloadpage(video_base_url + get).data
                            url = scrapertools.find_single_match(embed, 'window.location="([^"]+)"')

                            title = servert + lang_title.get(lang, lang)
                            itemlist.append(Item(
                                channel=item.channel,
                                action="play",
                                title=title,
                                url=url,
                                server=server,
                                fanart=item.fanart,
                                thumbnail=item.thumbnail,
                                contentTitle=item.contentTitle
                                ))
        if item.library and config.get_videolibrary_support() and len(itemlist) > 0:
            infoLabels = {'tmdb_id': item.infoLabels['tmdb_id'],
                          'title': item.infoLabels['title']}
            itemlist.append(Item(channel=item.channel, title="Añadir esta película a la videoteca",
                                 action="add_pelicula_to_library", url=item.url, infoLabels=infoLabels,
                                 text_color="0xFFf7f7f7",
                                 thumbnail='http://imgur.com/gPyN1Tf.png'))
    else:
        itemlist.append(
            Item(channel=item.channel, action="", title="[COLOR red][B]Upps!..Archivo no encontrado...[/B][/COLOR]",
                 thumbnail=item.thumbnail))
    return itemlist


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host + '/ver/'
        elif categoria == 'terror':
            item.url = host + "/categoria/de-terror.htm"
        elif categoria == 'castellano':
            item.url = host + "/ver/espanol/"

        elif categoria == 'latino':
            item.url = host + "/ver/latino/"
        else:
            return []

        itemlist = scraper(item)
        if itemlist[-1].title == "[COLOR crimson]Siguiente >>[/COLOR]":
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
