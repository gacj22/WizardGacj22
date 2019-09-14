# -*- coding: utf-8 -*-

import os
import re
import sys
import urllib
import time

from core import channeltools
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger

host = "http://tv-vip.com"


def mainlist(item):
    logger.info()
    item.viewmode = "movie"
    itemlist = []

    data = httptools.downloadpage(host + "/json/playlist/home/index.json")

    itemlist.append(Item(channel=item.channel, title="Películas", action="submenu",
                         thumbnail=host+"/json/playlist/peliculas/thumbnail.jpg",
                         fanart=host+"/json/playlist/peliculas/background.jpg"))
    itemlist.append(Item(channel=item.channel, title="Series", action="submenu",
                         thumbnail=host+"/json/playlist/series/poster.jpg",
                         fanart=host+"/json/playlist/series/background.jpg"))
    itemlist.append(Item(channel=item.channel, title="Versión Original", action="entradasconlistas",
                         url=host+"/json/playlist/version-original/index.json",
                         thumbnail=host+"/json/playlist/version-original/thumbnail.jpg",
                         fanart=host+"/json/playlist/version-original/background.jpg"))
    itemlist.append(Item(channel=item.channel, title="Documentales", action="entradasconlistas",
                         url=host+"/json/playlist/documentales/index.json",
                         thumbnail=host+"/json/playlist/documentales/thumbnail.jpg",
                         fanart=host+"/json/playlist/documentales/background.jpg"))
    itemlist.append(Item(channel=item.channel, title="Películas Infantiles", action="entradasconlistas",
                         url=host+"/json/playlist/peliculas-infantiles/index.json",
                         thumbnail=host+"/json/playlist/peliculas-infantiles/thumbnail.jpg",
                         fanart=host+"/json/playlist/peliculas-infantiles/background.jpg"))
    itemlist.append(Item(channel=item.channel, title="Series Infantiles", action="entradasconlistas",
                         url=host+"/json/playlist/series-infantiles/index.json",
                         thumbnail=host+"/json/playlist/series-infantiles/thumbnail.jpg",
                         fanart=host+"/json/playlist/series-infantiles/background.jpg"))
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search",
                         thumbnail="http://i.imgur.com/gNHVlI4.png", fanart="http://i.imgur.com/9loVksV.png"))

    return itemlist

def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "%20")
    if item.title == "Buscar...": item.extra = "local"
    item.url = host + "/video-prod/s/search?q=%s&n=100" % texto
    try:
        return busqueda(item, texto)
        # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def busqueda(item, texto):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = jsontools.load(data)
    for child in data["objectList"]:
        infolabels = {}
        infolabels['year'] = child['year']
        if child['tags']: infolabels['genre'] = ', '.join([x.strip() for x in child['tags']])
        infolabels['rating'] = child['rate'].replace(',', '.')
        infolabels['votes'] = child['rateCount']
        if child['cast']: infolabels['cast'] = child['cast'].split(",")
        infolabels['director'] = child['director']
        if 'playListChilds' not in child:
            infolabels['plot'] = child['description']
            type = "repo"
            contentTitle = child['name']
            title = child['name']
            infolabels['duration'] = child['duration']
            if child['height'] < 720:
               quality = "[B]  [SD][/B]"
            elif child['height'] < 1080:
               quality = "[B]  [720p][/B]"
            elif child['height'] < 2160:
               quality = "[B]  [1080p][/B]"
            elif child['height'] >= 2160:
               quality = "[B]  [4k][/B]"
            if child['name'] == "":
               title = child['id'].rsplit(".", 1)[0]
            else:
               title = child['name']
            if child['year']:
                title += " (" + child['year'] + ")"
            title += quality
        else:
            type = "playlist"
            infolabels['plot'] = "Contiene:\n" + "\n".join(child['playListChilds']) + "\n".join(child['repoChilds'])
            contentTitle = child['id']
            title = "[COLOR red][LISTA][/COLOR] " + child['id'].replace('-', ' ').capitalize() + " ([COLOR gold]" + \
                    str(child['number']) + "[/COLOR])"
        # En caso de búsqueda global se filtran los resultados
        if item.extra != "local":
            if "+" in texto: texto = "|".join(texto.split("+"))
            if not re.search(r'(?i)' + texto, title, flags=re.DOTALL): continue
        url = host + "/json/%s/%s/index.json" % (type, child["id"])
        # Fanart
        if child['hashBackground']:
            fanart = host + "/json/%s/%s/background.jpg" % (type, child["id"])
        else:
            fanart = host + "/json/%s/%s/thumbnail.jpg" % (type, child["id"])
        # Thumbnail
        if child['hasPoster']:
            thumbnail = host + "/json/%s/%s/poster.jpg" % (type, child["id"])
        else:
            thumbnail = fanart
        if type == 'playlist':
            itemlist.insert(0, Item(channel=item.channel, action="entradasconlistas", title=title,
                                    url=url, thumbnail=thumbnail, fanart=fanart, contentTitle=contentTitle,
                                    infoLabels=infolabels, viewmode="movie_with_plot", folder=True))
        else:
            itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url,
                                thumbnail=thumbnail, fanart=fanart, contentTitle=contentTitle, contentTitle=contentTitle,
                                context="05", infoLabels=infolabels, viewmode="movie_with_plot", folder=True))
    return itemlist


def submenu(item):
    logger.info()
    itemlist = []
    if item.title == "Series":
        itemlist.append(Item(channel=item.channel, title="Nuevos Capítulos", action="episodios",
                             url=host+"/json/playlist/nuevos-capitulos/index.json",
                             thumbnail=host+"/json/playlist/nuevos-capitulos/background.jpg",
                             fanart=host+"/json/playlist/nuevos-capitulos/background.jpg"))
        itemlist.append(Item(channel=item.channel, title="Más Vistas", action="series",
                             url=host+"/json/playlist/top-series/index.json",
                             thumbnail=host+"/playlist/top-series/thumbnail.jpg",
                             fanart=host+"/json/playlist/top-series/background.jpg",
                             extra1="Series"))
        itemlist.append(Item(channel=item.channel, title="Últimas Series", action="series",
                             url=host+"/json/playlist/series/index.json",
                             thumbnail=item.thumbnail, fanart=item.fanart, extra1="Series"))
        itemlist.append(Item(channel=item.channel, title="Lista de Series A-Z", action="series",
                             url=host+"/json/playlist/series/index.json", thumbnail=item.thumbnail,
                             fanart=item.fanart, extra1="Series"))
    else:
        itemlist.append(Item(channel=item.channel, title="Novedades", action="entradas",
                             url=host+"/json/playlist/000-novedades/index.json",
                             thumbnail=host+"/json/playlist/ultimas-peliculas/thumbnail.jpg",
                             fanart=host+"/json/playlist/ultimas-peliculas/background.jpg"))
        itemlist.append(Item(channel=item.channel, title="Más vistas", action="entradas",
                             url=host+"/json/playlist/peliculas-mas-vistas/index.json",
                             thumbnail=host+"/json/playlist/peliculas-mas-vistas/thumbnail.jpg",
                             fanart=host+"/json/playlist/peliculas-mas-vistas/background.jpg"))
        itemlist.append(Item(channel=item.channel, title="Categorías", action="cat",
                             url=host+"/json/playlist/peliculas/index.json",
                             thumbnail=item.thumbnail, fanart=item.fanart))
        itemlist.append(Item(channel=item.channel, title="Películas 3D", action="entradasconlistas",
                             url=host+"/json/playlist/3D/index.json",
                             thumbnail=host+"/json/playlist/3D/thumbnail.jpg",
                             fanart=host+"/json/playlist/3D/background.jpg"))
    return itemlist


def cat(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = jsontools.load(data)
    exception = ["peliculas-mas-vistas", "ultimas-peliculas"]
    for child in data["sortedPlaylistChilds"]:
        if child["id"] not in exception:
            url = host + "/json/playlist/%s/index.json" % child["id"]
            # Fanart
            if child['hashBackground']:
                fanart = host + "/json/playlist/%s/background.jpg" % child["id"]
            else:
                fanart = host + "/json/playlist/%s/thumbnail.jpg" % child["id"]
            # Thumbnail
            thumbnail = host + "/json/playlist/%s/thumbnail.jpg" % child["id"]
            title = child['id'].replace('-', ' ').capitalize().replace("Manga", "Animación/Cine Oriental")
            title += " ([COLOR gold]" + str(child['number']) + "[/COLOR])"
            itemlist.append(
                     Item(channel=item.channel, action="entradasconlistas", title=title, url=url,
                          thumbnail=thumbnail, fanart=fanart, folder=True))
    return itemlist


def entradas(item):
    logger.info()
    itemlist = []
    infolabels = {}
    if item.title == "Nuevos Capítulos":
        context = "5"
    else:
        context = "05"
    data = httptools.downloadpage(item.url).data
    data = jsontools.load(data)
    for child in data["sortedRepoChilds"]:
        infolabels['year'] = child['year']
        url = host + "/json/repo/%s/index.json" % child["id"]
        thumbnail = ""
        if child['hasPoster']:
            thumbnail = host + "/json/repo/%s/poster.jpg" % child["id"]
        if child['height'] < 720:
            quality = "[B]  [SD][/B]"
        elif child['height'] < 1080:
            quality = "[B]  [720p][/B]"
        elif child['height'] < 2160:
            quality = "[B]  [1080p][/B]"
        elif child['height'] >= 2160:
            quality = "[B]  [4k][/B]"
        contentTitle = child['name']
        title = child['name']
        if child['year']:
            title += " (" + child['year'] + ")"
        title += quality
        itemlist.append(Item(channel=item.channel, action="findvideos", server="", title=title, url=url,
                             thumbnail=thumbnail, contentTitle=contentTitle, infoLabels=infolabels,
                             contentTitle=contentTitle, context=context))
    tmdb.set_infoLabels(itemlist)
    return itemlist


def entradasconlistas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = jsontools.load(data)
    # Si hay alguna lista
    contentSerie = False
    contentList = False
    if data['playListChilds']:
        itemlist.append(Item(channel=item.channel, title="**LISTAS**", action="", text_color="red", text_blod=True,
                             folder=False))
        for child in data['sortedPlaylistChilds']:
            infolabels = {}
            infolabels['plot'] = "Contiene:\n" + "\n".join(child['playListChilds']) + "\n".join(child['repoChilds'])
            if child['seasonNumber'] and not contentList and re.search(r'(?i)temporada', child['id']):
                infolabels['season'] = child['seasonNumber']
                contentSerie = True
            else:
                contentSerie = False
                contentList = True
            title = child['id'].replace('-', ' ').capitalize() + " ([COLOR gold]" + str(child['number']) + "[/COLOR])"
            url = host + "/json/playlist/%s/index.json" % child["id"]
            thumbnail = host + "/json/playlist/%s/thumbnail.jpg" % child["id"]
            if child['hashBackground']:
                fanart = host + "/json/playlist/%s/background.jpg" % child["id"]
            else:
                fanart = host + "/json/playlist/%s/thumbnail.jpg" % child["id"]
            itemlist.append(Item(channel=item.channel, action="entradasconlistas", title=title,
                                 url=url, thumbnail=thumbnail, fanart=fanart, contentTitle=child['id'],
                                 infoLabels=infolabels, viewmode="movie_with_plot"))
    else:
        contentList = True

    if data["sortedRepoChilds"] and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel, title="**VÍDEOS**", action="", text_color="blue", text_blod=True,
                             folder=False))

    for child in data["sortedRepoChilds"]:
        infolabels = {}
        infolabels['plot'] = child['description']
        infolabels['year'] = data['year']
        if child['tags']: infolabels['genre'] = ', '.join([x.strip() for x in child['tags']])
        infolabels['rating'] = child['rate'].replace(',', '.')
        infolabels['votes'] = child['rateCount']
        infolabels['duration'] = child['duration']
        if child['cast']: infolabels['cast'] = child['cast'].split(",")
        infolabels['director'] = child['director']
        url = host + "/json/repo/%s/index.json" % child["id"]
        # Fanart
        if child['hashBackground']:
            fanart = host + "/json/repo/%s/background.jpg" % child["id"]
        else:
            fanart = host + "/json/repo/%s/thumbnail.jpg" % child["id"]
        # Thumbnail
        if child['hasPoster']:
            thumbnail = host + "/json/repo/%s/poster.jpg" % child["id"]
        else:
            thumbnail = fanart
        if child['height'] < 720:
            quality = "[B]  [SD][/B]"
        elif child['height'] < 1080:
            quality = "[B]  [720p][/B]"
        elif child['height'] < 2160:
            quality = "[B]  [1080p][/B]"
        elif child['height'] >= 2160:
            quality = "[B]  [4k][/B]"
        contentTitle = child['name']
        if child['name'] == "":
            title = child['id'].rsplit(".", 1)[0]
        else:
            title = child['name']
        if child['year']:
            title += " (" + child['year'] + ")"
        title += quality
        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url,
                             thumbnail=thumbnail, fanart=fanart, contentTitle=contentTitle, infoLabels=infolabels,
                             contentTitle=contentTitle, context="05", viewmode="movie_with_plot", folder=True))
    # Se añade item para añadir la lista de vídeos a la videoteca
    if data['sortedRepoChilds'] and len(itemlist) > 0 and contentList:
        if config.get_videolibrary_support():
            itemlist.append(Item(channel=item.channel, text_color="green", title="Añadir esta lista a la videoteca",
                                 url=item.url, action="listas"))
    elif contentSerie:
        if config.get_videolibrary_support():
            itemlist.append(Item(channel=item.channel, title="Añadir esta serie a la videoteca", url=item.url,
                                 action="series_library", contentTitle=data['name'], show=data['name'],
                                 text_color="green"))

    return itemlist


def series(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = jsontools.load(data)
    exception = ["top-series", "nuevos-capitulos"]
    for child in data["sortedPlaylistChilds"]:
        if child["id"] not in exception:
            infolabels = {}
            infolabels['plot'] = child['description']
            infolabels['year'] = child['year']
            if child['tags']: infolabels['genre'] = ', '.join([x.strip() for x in child['tags']])
            infolabels['rating'] = child['rate'].replace(',', '.')
            infolabels['votes'] = child['rateCount']
            if child['cast']: infolabels['cast'] = child['cast'].split(",")
            infolabels['director'] = child['director']
            infolabels['mediatype'] = "episode"
            if child['seasonNumber']: infolabels['season'] = child['seasonNumber']
            url = host + "/json/playlist/%s/index.json" % child["id"]
            # Fanart
            if child['hashBackground']:
                fanart = host + "/json/playlist/%s/background.jpg" % child["id"]
            else:
                fanart = host + "/json/playlist/%s/thumbnail.jpg" % child["id"]
            # Thumbnail
            if child['hasPoster']:
                thumbnail = host + "/json/playlist/%s/poster.jpg" % child["id"]
            else:
                thumbnail = fanart
            if item.extra1 == "Series":
                if child['name'] != "":
                    contentTitle = child['name']
                    contentTitle = contentTitle.replace('-', '')
                    title = child['name'] + " (" + child['year'] + ")"
                else:
                    title = contentTitle = child['id'].capitalize()
                if "Temporada" not in title:
                    title += "     [Temporadas: [COLOR gold]" + str(child['numberOfSeasons']) + "[/COLOR]]"
                elif item.title == "Más Vistas":
                    title = title.replace("- Temporada", "--- Temporada")
            else:
                if data['name'] != "":
                    contentTitle = data['name']
                    if child['seasonNumber']:
                        title = data['name'] + " --- Temporada " + child['seasonNumber'] + \
                               "  [COLOR gold](" + str(child['number']) + ")[/COLOR]"
                    else:
                        title = child['name'] + "  [COLOR gold](" + str(child['number']) + ")[/COLOR]"
                else:
                    contentTitle = data['id']
                    if child['seasonNumber']:
                        title = data['id'].capitalize() + " --- Temporada " + child['seasonNumber'] + \
                              "  [COLOR gold](" + str(child['number']) + ")[/COLOR]"
                    else:
                        title = data['id'].capitalize() + "  [COLOR gold](" + str(child['number']) + ")[/COLOR]"

            if not child['playListChilds']:
                action = "episodios"
            else:
                action = "series"
            itemlist.append(Item(channel=item.channel, action=action, title=title, url=url, server="",
                                 thumbnail=thumbnail, fanart=fanart, contentTitle=contentTitle, infoLabels=infolabels,
                                 contentSerieName=contentTitle, context="25", viewmode="movie_with_plot", folder=True))
            if len(itemlist) == len(data["sortedPlaylistChilds"]) and item.extra1 != "Series":
                itemlist.sort(key=lambda item: item.title, reverse=True)
                if config.get_videolibrary_support():
                    itemlist.append(Item(channel=item.channel, title="Añadir esta serie a la videoteca", url=item.url,
                                         action="add_serie_to_library", show=data['name'],
                                         text_color="green", extra="series_library"))
    if item.title == "Últimas Series": return itemlist
    if item.title == "Lista de Series A-Z": itemlist.sort(key=lambda item: item.contentTitle)
    if data["sortedRepoChilds"] and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel, title="**VÍDEOS RELACIONADOS/MISMA TEMÁTICA**", text_color="blue",
                             text_blod=True, action="", folder=False))
    for child in data["sortedRepoChilds"]:
        infolabels = {}
        if child['description']:
            infolabels['plot'] = data['description']
        else:
            infolabels['plot'] = child['description']
        infolabels['year'] = data['year']
        if not child['tags']:
            infolabels['genre'] = ', '.join([x.strip() for x in data['tags']])
        else:
            infolabels['genre'] = ', '.join([x.strip() for x in child['tags']])
        infolabels['rating'] = child['rate'].replace(',', '.')
        infolabels['duration'] = child['duration']
        if child['cast']: infolabels['cast'] = child['cast'].split(",")
        infolabels['director'] = child['director']
        url = host + "/json/repo/%s/index.json" % child["id"]
        if child['hashBackground']:
            fanart = host + "/json/repo/%s/background.jpg" % child["id"]
        else:
            fanart = host + "/json/repo/%s/thumbnail.jpg" % child["id"]
        # Thumbnail
        if child['hasPoster']:
            thumbnail = host + "/json/repo/%s/poster.jpg" % child["id"]
        else:
            thumbnail = fanart
        if child['height'] < 720:
            quality = "[B]  [SD][/B]"
        elif child['height'] < 1080:
            quality = "[B]  [720p][/B]"
        elif child['height'] < 2160:
            quality = "[B]  [1080p][/B]"
        elif child['height'] >= 2160:
            quality = "[B]  [1080p][/B]"
        contentTitle = child['name']
        if child['name'] == "":
            title = child['id'].rsplit(".", 1)[0]
        else:
            title = child['name']
        if child['year']:
            title += " (" + child['year'] + ")"
        title += quality
        itemlist.append(Item(channel=item.channel, action="findvideos", title=title, url=url,
                             server="", thumbnail=thumbnail, fanart=fanart, contentTitle=contentTitle, infoLabels=infolabels,
                             contentSerieName=contentTitle, context="25", viewmode="movie_with_plot", folder=True))
    if item.extra == "new":
        itemlist.sort(key=lambda item: item.title, reverse=True)
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    # Redirección para actualización de videoteca
    if item.extra == "series_library":
        itemlist = series_library(item)
        return itemlist
    data = httptools.downloadpage(item.url).data
    data = jsontools.load(data)
    # Se prueba un método u otro porque algunas series no están bien listadas
    if data["sortedRepoChilds"]:
        for child in data["sortedRepoChilds"]:
            if item.infoLabels:
                item.infoLabels['duration'] = str(child['duration'])
                item.infoLabels['season'] = str(data['seasonNumber'])
                item.infoLabels['episode'] = str(child['episode'])
                item.infoLabels['mediatype'] = "episode"
            #contentTitle = item.contentTitle + "|" + str(data['seasonNumber']) + "|" + str(child['episode'])
            # En caso de venir del apartado nuevos capítulos se redirige a la función series para mostrar los demás
            if item.title == "Nuevos Capítulos":
                url = host + "/json/playlist/%s/index.json" % child["season"]
                action = "series"
                extra = "new"
            else:
                url = host + "/json/repo/%s/index.json" % child["id"]
                action = "findvideos"
                extra = ""
            if child['hasPoster']:
                thumbnail = host + "/json/repo/%s/poster.jpg" % child["id"]
            else:
                thumbnail = host + "/json/repo/%s/thumbnail.jpg" % child["id"]
            try:
                title = contentTitle = child['name'].rsplit(" ", 1)[0] + " - " + child['name'].rsplit(" ", 1)[1]
            except:
                title = contentTitle = child['id']
            itemlist.append(item.clone(action=action, server="", title=title, url=url, thumbnail=thumbnail,
                                       fanart=item.fanart, contentTitle=contentTitle, contentSerieName=contentTitle, context="35",
                                       viewmode="movie", extra=extra, show=item.contentTitle, folder=True))
    else:
        for child in data["repoChilds"]:
            url = host + "/json/repo/%s/index.json" % child
            if data['hasPoster']:
                thumbnail = host + "/json/repo/%s/poster.jpg" % child
            else:
                thumbnail = host + "/json/repo/%s/thumbnail.jpg" % child
            title = contentTitle = child.capitalize().replace('_', ' ')
            itemlist.append(item.clone(action="findvideos", server="", title=title, url=url, thumbnail=thumbnail,
                                       fanart=item.fanart, contentTitle=contentTitle, contentSerieName=item.contentTitle,
                                       context="25", show=item.contentTitle, folder=True))
    # Opción de añadir a la videoteca en casos de series de una única temporada
    if len(itemlist) > 0 and not "---" in item.title and item.title != "Nuevos Capítulos":
        if config.get_videolibrary_support() and item.show == "":
            if "-" in item.title:
                show = item.title.split('-')[0]
            else:
                show = item.title.split('(')[0]
            itemlist.append(Item(channel=item.channel, title="Añadir esta serie a la videoteca", text_color="green",
                                 url=item.url, action="add_serie_to_library", show=show, extra="series_library"))
    return itemlist


def series_library(item):
    logger.info()
    # Funcion unicamente para añadir/actualizar series a la libreria
    lista_episodios = []
    show = item.show.strip()
    data_serie = httptools.downloadpage(item.url).data
    data_serie = jsontools.load(data_serie)
    # Para series que en la web se listan divididas por temporadas
    if data_serie["sortedPlaylistChilds"]:
        for season_name in data_serie["sortedPlaylistChilds"]:
            url_season = host + "/json/playlist/%s/index.json" % season_name['id']
            data = httptools.downloadpage(url_season).data
            data = jsontools.load(data)
            if data["sortedRepoChilds"]:
                for child in data["sortedRepoChilds"]:
                    url = host + "/json/repo/%s/index.json" % child["id"]
                    contentTitle = child['name'].rsplit(" ", 1)[0] + " - " + child['name'].rsplit(" ", 1)[1]
                    try:
                        check_filename = scrapertools.get_season_and_episode(contentTitle)
                    except:
                        contentTitle += " " + str(data['seasonNumber']) + "x00"
                    lista_episodios.append(Item(channel=item.channel, action="findvideos", server="",
                                                title=contentTitle, extra=url, url=item.url, contentTitle=contentTitle,
                                                contentTitle=contentTitle, show=show))
            else:
                for child in data["repoChilds"]:
                    url = host + "/json/repo/%s/index.json" % child
                    contentTitle = child.capitalize().replace('_', ' ')
                    try:
                        check_filename = scrapertools.get_season_and_episode(contentTitle)
                    except:
                        contentTitle += " " + str(data['seasonNumber']) + "x00"
                    lista_episodios.append(Item(channel=item.channel, action="findvideos", server="",
                                                title=contentTitle, extra=url, url=item.url, contentTitle=contentTitle, 
                                                contentTitle=contentTitle, show=show))
    # Para series directas de una sola temporada
    else:
        data = data_serie
        if data["sortedRepoChilds"]:
            for child in data["sortedRepoChilds"]:
                url = host + "/json/repo/%s/index.json" % child["id"]
                contentTitle = child['name'].rsplit(" ", 1)[0] + " - " + child['name'].rsplit(" ", 1)[1]
                try:
                    check_filename = scrapertools.get_season_and_episode(contentTitle)
                except:
                    contentTitle += " 1x00"
                lista_episodios.append(Item(channel=item.channel, action="findvideos", server="", title=contentTitle,
                                            contentTitle=contentTitle, url=item.url, extra=url, contentTitle=contentTitle,
                                            show=show))
        else:
            for child in data["repoChilds"]:
                url = host + "/json/repo/%s/index.json" % child
                contentTitle = child.capitalize().replace('_', ' ')
                try:
                    check_filename = scrapertools.get_season_and_episode(contentTitle)
                except:
                    contentTitle += " 1x00"
                lista_episodios.append(Item(channel=item.channel, action="findvideos", server="", title=contentTitle,
                                            contentTitle=contentTitle, url=item.url, extra=url, contentTitle=contentTitle,
                                            show=show))
    return lista_episodios


def findvideos(item):
    logger.info()
    itemlist = []
    # En caso de llamarse a la función desde una serie de la videoteca
    if item.extra.startswith("http"): item.url = item.extra
    data = httptools.downloadpage(item.url).data
    data = jsontools.load(data)
    id = urllib.quote(data['id'])
    for child in data["profiles"].keys():
        videopath = urllib.quote(data["profiles"][child]['videoUri'])
        for i in range(0, len(data["profiles"][child]['servers'])):
            url = data["profiles"][child]['servers'][i]['url'] + videopath
            size = "  " + data["profiles"][child]["sizeHuman"]
            resolution = " [" + (data["profiles"][child]['videoResolution']) + "]"
            title = "Ver vídeo en " + resolution.replace('1920x1080', 'HD-1080p')
            if i == 0:
                title += size + " [COLOR purple]Mirror " + str(i + 1) + "[/COLOR]"
            else:
                title += size + " [COLOR green]Mirror " + str(i + 1) + "[/COLOR]"
            # Para poner enlaces de mayor calidad al comienzo de la lista
            if data["profiles"][child]["profileId"] == "default":
                itemlist.insert(i, item.clone(action="play", server="directo", title=title, url=url,
                                              viewmode="list", extra=id, folder=False))
            else:
                itemlist.append(item.clone(action="play", server="directo", title=title, url=url,
                                           viewmode="list", extra=id, folder=False))
    itemlist.append(item.clone(channel="trailertools", action="buscartrailer", title="Buscar Tráiler",
                               text_color="magenta"))
    if len(itemlist) > 0 and item.extra == "":
        if config.get_videolibrary_support():
            itemlist.append(Item(channel=item.channel, title="Añadir enlaces a la videoteca", text_color="green",
                                      url=item.url, action="add_pelicula_to_library",
                                      infoLabels={'title':item.contentTitle}, extra="findvideos", contentTitle=item.contentTitle))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    uri = scrapertools.find_single_match(item.url, '(/transcoder[\w\W]+)')
    s = scrapertools.find_single_match(item.url, r'http.*?://(.*?)\.')
    uri_request = host + "/video2-prod/s/uri?uri=%s&s=%s&_=%s" % (uri, s, int(time.time()))
    data = httptools.downloadpage(uri_request).data
    data = jsontools.load(data)
    if data['s'] == None:
        data['s'] = ''
    # url = item.url.replace(".tv-vip.com/transcoder/", ".%s/e/transcoder/") % (data['b']) + "?tt=" + str(data['a']['tt']) + \
    #       "&mm=" + data['a']['mm'] + "&bb=" + data['a']['bb']
    url = item.url.replace(".tv-vip.com/transcoder/", ".pelisipad.com/s/transcoder/") + "?tt=" + str(
        data['a']['tt']) + \
          "&mm=" + data['a']['mm'] + "&bb=" + data['a']['bb']

    url += "|User-Agent=%s" % httptools.get_user_agent

    itemlist.append(item.clone(action="play", server="directo", url=url, folder=False))

    return itemlist


def listas(item):
    logger.info()
    # Para añadir listas a la videoteca en carpeta CINE
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = jsontools.load(data)
    head = header_string + get_cookie_value()
    for child in data["sortedRepoChilds"]:
        infolabels = {}
        # Fanart
        if child['hashBackground']:
            fanart = host + "/json/repo/%s/background.jpg" % child["id"]
        else:
            fanart = host + "/json/repo/%s/thumbnail.jpg" % child["id"]
        # Thumbnail
        if child['hasPoster']:
            thumbnail = host + "/json/repo/%s/poster.jpg" % child["id"]
        else:
            thumbnail = fanart
        thumbnail += head
        fanart += head
        url = host + "/json/repo/%s/index.json" % child["id"]
        if child['name'] == "":
            title = scrapertools.slugify(child['id'].rsplit(".", 1)[0])
        else:
            title = scrapertools.slugify(child['name'])
        title = title.replace('-', ' ').replace('_', ' ').capitalize()
        infolabels['title'] = title
        try:
            from core import videolibrarytools
            new_item = item.clone(title=title, url=url, contentTitle=title, fanart=fanart, extra="findvideos",
                                  thumbnail=thumbnail, infoLabels=infolabels, category="Cine")
            videolibrarytools.library.add_movie(new_item)
            error = False
        except:
            error = True
            import traceback
            logger.error(traceback.format_exc())
    if not error:
        itemlist.append(Item(channel=item.channel, title='Lista añadida correctamente a la videoteca',
                             action="", folder=False))
    else:
        itemlist.append(Item(channel=item.channel, title='ERROR. Han ocurrido uno o varios errores en el proceso',
                            action="", folder=False))

    return itemlist
