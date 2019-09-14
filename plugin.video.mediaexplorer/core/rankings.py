# -*- coding: utf-8 -*-
from core.libs import *
from core import finder

def mainlist(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        type='label',
        label="Filmaffinity:"
    ))

    toyear = (datetime.datetime.now() - datetime.timedelta(455)).year
    itemlist.append(item.clone(
        action='top_filmaffinity',
        label='Mejores películas de esta decada (2010-%s)' % toyear,
        group=True,
        category='movie',
        content_type='movies',
        url='https://www.filmaffinity.com/es/topgen.php?genre=&fromyear=2010&toyear=%s&country=&nodoc&notvse' % toyear,
        page=0,
        description='TOP Filmaffinity: Mejores películas desde el 2010 al %s' % toyear,
        type='search'
    ))

    itemlist.append(item.clone(
        action='top_filmaffinity',
        label='Mejores películas de la historia',
        group=True,
        category='movie',
        content_type='movies',
        url='https://www.filmaffinity.com/es/topgen.php?genre=&country=&notvse=1&fromyear=&toyear=%s&nodoc=1' % toyear,
        page=0,
        description='TOP Filmaffinity: Mejores películas de la historia',
        type='search'
    ))

    itemlist.append(item.clone(type='label', label=""))
    itemlist.append(item.clone(
        type='label',
        group=True,
        label='Mejores películas por géneros (1980-%s): ' % toyear
    ))

    generos = {"AV": "Aventuras", "AC": "Acción", "AN": "Animación",
               "CO": "Comedias", "DR": "Dramaticas", "FAN": "Fantasía", "INT": "Intriga",
               "MU": "Musicales", "RO": "Románticas", "C-F": "Ciencia Ficción",
               "TE": "Terror", "BE": "Bélicas", "WE": "Western",
               "F-N": "Cine Negro", "INF": "Infantiles"}

    itemlist2 = list()
    for k,v in generos.items():
        itemlist2.append(item.clone(
            action='top_filmaffinity',
            label= '    %s' % v,
            group=True,
            category='movie',
            content_type='movies',
            url='https://www.filmaffinity.com/es/topgen.php?genre=%s&country=&notvse=1&fromyear=1980&toyear=%s&nodoc=1' % (k,toyear),
            page=0,
            description='Mejores películas por género: %s' % v,
            type='search'
        ))

    itemlist.extend(sorted(itemlist2, key=lambda i: i.label))

    return itemlist


def top_filmaffinity(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url,post={'from':item.page}).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<li ><ul>.*?src="([^"]+)".*?title="[^"]+">([^<]+)</a>\s?\((\d+).*?<div class="avg-rating">([^<]+)</div>'

    #logger.debug(scrapertools.find_multiple_matches(data,patron))
    for poster, title, year, rating in scrapertools.find_multiple_matches(data,patron):
        new_item = item.clone(
            action='search',
            title=title,
            label_extra={"sublabel": " (%s)", "color": "color3", "value": rating},
            query=title,
            poster=poster,
            type='movie',
            search_categories={'movie': True},
            content_type='movies',
            year=year
        )
        del new_item.page
        del new_item.description
        del new_item.url
        del new_item.name

        itemlist.append(new_item)

    # Obtener información en el listado
    dialog = platformtools.dialog_progress_bg('Obteniendo información de medios')
    for ready, total in mediainfo.get_itemlist_info(itemlist):
        dialog.update(ready * 100 / total, 'Obteniendo información de medios', '%s de %s' % (ready, total))
    dialog.close()

    itemlist = filter(lambda i: i.tmdb_id, itemlist)

    # Paginacion
    itemlist.append(item.clone(
        page=item.page + 30,
        type='next'
    ))

    return itemlist

def search(item):
    logger.trace()
    itemlist = finder.search(item)

    if item.tmdb_id:
        itemlist = filter(lambda i: i.tmdb_id == item.tmdb_id, itemlist)
        if len(itemlist) == 1 and itemlist[0].action == 'ungroup':
            itemlist = finder.ungroup(itemlist[0])

    return itemlist