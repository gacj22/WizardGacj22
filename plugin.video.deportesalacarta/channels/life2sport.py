# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para life2sport
#------------------------------------------------------------
import re, datetime

from core import httptools
from core import logger
from core import config
from core import scrapertools
from core import servertools
from core.item import Item
from core.scrapertools import decodeHtmlentities as dhe

__channel__ = "life2sport"
host = "http://www.life2sport.com/"


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone(title="Agenda/Directos Fútbol", url=host, action="agenda", fanart="http://i.imgur.com/wjjQ1PN.jpg"))
    itemlist.append(item.clone(title="Agenda/Directos Deportes", url=host, action="agenda", fanart="http://i.imgur.com/wjjQ1PN.jpg"))
    itemlist.append(item.clone(title="Partidos - Fútbol - Novedades", url=host + "category/online-video/football", action="entradas", fanart="http://i.imgur.com/wjjQ1PN.jpg"))
    itemlist.append(item.clone(title="Partidos - Fútbol - Competiciones", url=host, action="indices", fanart="http://i.imgur.com/wjjQ1PN.jpg"))
    itemlist.append(item.clone(title="Eventos - Deportes", url=host, action="indices", fanart="http://i.imgur.com/wjjQ1PN.jpg"))

    return itemlist


def agendaglobal(item):
    itemlist = []
    try:
        item.channel = __channel__
        item.url = host
        item.thumbnail = "http://i.imgur.com/xfZ3TS4.png"
        item.fanart = "http://i.imgur.com/wjjQ1PN.jpg"
        itemlist = agenda(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def agenda(item):
    logger.info()
    itemlist = []
    
    data = translate(item.url)

    listas = {}
    i = 0
    bloques = scrapertools.find_multiple_matches(data, ',\s*(\d+)\s*de\s*(\w+).*?<(.*?)</table>')
    for dia, mes, bloque in bloques:
        mes = month_convert(mes.capitalize())
        mes = str(mes).zfill(2)
        dia = dia.zfill(2)
        patron = '<td.*?u=(%s[^&]+)&.*?<strong>\s*(\d+:\d+).*?title="([^"]+)"' \
                 '.*?>([^<]+)</span></a></span></span>\s*</td>' % host
        matches = scrapertools.find_multiple_matches(bloque, patron)
        listas[str(i)] = []
        for url, hora, sport, partido in matches:
            if re.search(r"(?i)Fútbol.|Futbol.", sport):
                if "Deportes" in item.title:
                    continue
                deporte = "futbol"
            else:
                if "Deportes" not in item.title:
                    continue
                deporte = scrapertools.find_single_match(sport, '([^\.]+)\.')
                if deporte == "NB":
                    deporte = "NBA"

            if " - " not in partido:
                partido = re.sub(r"(?i)\s*emisión de\s*|\s*emision directa\s*|s*en línea\s*|\s*en linea\s*|\s*directa\s*", "", sport)
            else:
                partido = partido.replace(" - ", " vs ")

            horas, minutos = hora.split(":")
            fecha_actual = datetime.datetime.today()
            fecha_partido = datetime.datetime(fecha_actual.year, int(mes), int(dia),
                                              int(horas), int(minutos))
            fecha_partido = fecha_partido - datetime.timedelta(hours=1)
            hora = fecha_partido.strftime("%H:%M")
            date = fecha_partido.strftime("%d/%m")

            if fecha_partido <= fecha_actual:
                if (fecha_partido + datetime.timedelta(hours=2, minutes=30)) < fecha_actual:
                    continue
                scrapedtitle = "[B][COLOR red]"+date+" "+hora+"[/COLOR][COLOR darkorange] " + partido + "[/COLOR][/B]"
            else:
                scrapedtitle = "[B][COLOR green]"+date+" "+hora+"[/COLOR][COLOR darkorange] " + partido + "[/COLOR][/B]"

            listas[str(i)].append(item.clone(title=scrapedtitle, action="findlives", url=url, date=date, time=hora, evento=partido, deporte=deporte, context="info_partido"))
        listas[str(i)].sort(key=lambda item: (item.date, item.time))
        i += 1
    
    if not listas:
        itemlist.append(item.clone(title="No hay partidos programados en la agenda", action=""))
    else:
        for i in range(0, len(listas)):
            itemlist.extend(listas[str(i)])

    return itemlist


def entradas(item):
    logger.info()
    itemlist = []
    
    data = translate(item.url)

    patron = 'rel=bookmark title="([^"]+)".*?src=([^\s]+).*?href=.*?u=(%s[^&]+)&' % host
    matches = scrapertools.find_multiple_matches(data, patron)
    for evento, thumbnail, url in matches:
        evento = re.sub(r"(?i)redondo|redonda|ronda", "jornada", evento)
        title = "[COLOR blue]%s[/COLOR]" % evento
        itemlist.append(item.clone(title=title, action="findvideos", url=url, thumbnail=thumbnail))

    next_page = scrapertools.find_single_match(data, '<link rel=next href=([^\s]+)')
    if next_page:
        itemlist.append(item.clone(title=">> Página Siguiente", url=next_page))
    
    return itemlist


def indices(item):
    logger.info()
    itemlist = []

    if "Deportes" in item.title:
        categorias = [["Baloncesto", [["NBA", "nba"], ["Euroliga", "euroleague"], ["Eurocup", "europa-cup-fiba"],
                    ["Eurobasket 2015", "evrobasket-2015"]]], ["NFL", "american-football"],
                    ["Hockey", "hockey"], ["Tenis", "tennis-online"], ["Formula 1", "drugie-vidy/formula-1"],
                    ["MotoGP", "moto-gp"], ["Balonmano", "drugie-vidy/gandbol"], ["Fútbol Sala", "mini-football"],
                    ["Voleybol", "drugie-vidy/volleyball"], ["Artes Marciales", "edinoborstva-novosti"],
                    ["Ciclismo", "drugie-vidy/velosport"], ["Atletismo", "legkaya-atletika"],
                    ["Deportes de Invierno", "drugie-vidy/zimnie-vidy-sporta"], ["Gimnasia", "drugie-vidy/gimnastika"]]
    else:
        categorias = [["Liga BBVA", "futbol-ispaniya"], ["Premier League", "futbol-angliya"], ["Champions League", "liga-chempionov"],
                 ["Europa League", "liga-evropy"], ["Bundesliga", "futbol-germaniya"], ["Serie A", "futbol-italiya"],
                 ["Ligue 1", "futbol-franciya"], ["Liga Rusa", "futbol-rossiya"], ["Liga Ucraniana", "futbol-ukraina"],
                 ["Clasificacion Mundial 2018", "otbor-na-chm-2018"], ["Euro 2016", "evro-2016"], ["Clasificación Euro 2016", "otbor-na-evro-2016"],
                 ["Copa América 2016", "copa-amrica-2016-kubok-ameriki-2016"], ["Amistosos", "tovarishheskie-matchi"]]

        thumbs = {'Liga Ucraniana':'upl','Liga Rusa':'russia','Premier League':'apl','Liga BBVA':'La_Liga','Serie A':'serie_a',
                  'Bundesliga':'bundesliga','Ligue 1':'ligue-1','Champions League':'lch','Europa League':'le'}

    for key, value in categorias:
        if "Deportes" not in item.title:
            url = "%scategory/online-video/football/%s" % (host, value)
            thumb = item.thumbnail
            if thumbs.get(key):
                thumb = "http://www.myfootball.ws/DPYrOE/table/new2/%s.png" % thumbs[key]
            itemlist.append(item.clone(title=key, url=url, action="entradas", thumbnail=thumb))
        else:
            if type(value) is list:
                itemlist.append(item.clone(title=key, action=""))
                for k, v in value:
                    url = "%scategory/online-video/basketbol/%s" % (host, v)
                    title = "     %s" % k
                    itemlist.append(item.clone(title=title, url=url, action="entradas"))
            else:
                url = "%scategory/online-video/%s" % (host, value)
                itemlist.append(item.clone(title=key, url=url, action="entradas"))

    return itemlist


def findlives(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    patron = '<a href="(sop://[^"]+)".*?</a>.*?<strong>&nbsp;\(([^\)]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    if matches:
        itemlist.append(item.clone(title="[COLOR blue]Sopcast[/COLOR]", action=""))
        for url, canal in matches:
            scrapedtitle = "   [COLOR darkorange]" + item.evento + " [/COLOR][COLOR blue][" + canal + "][/COLOR]"
            itemlist.append(item.clone(title=scrapedtitle, action="play", server="p2p", url=url))
    patron = '<a href="(acestream://[^"]+)".*?</a>.*?<strong>&nbsp;\(([^\)]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    if matches:
        itemlist.append(item.clone(title="[COLOR red]Acestream[/COLOR]", action=""))
        for url, canal in matches:
            scrapedtitle = "   [COLOR darkorange]" + item.evento + " [/COLOR][COLOR red][" + canal + "][/COLOR]"
            itemlist.append(item.clone(title=scrapedtitle, action="play", server="p2p", url=url))

    if not itemlist:
        itemlist.append(item.clone(title="No hay enlaces disponibles. Inténtalo de nuevo más tarde", text_color="gold", action=""))

    return itemlist


def play(item):
    logger.info()
    itemlist = []

    if item.server == "p2p":
        fulltitle = "[COLOR darkorange]"+item.evento+"[/COLOR]"
        url = item.url+"|"+fulltitle
        itemlist.append(item.clone(url=url))
    else:
        itemlist.append(item.clone())
    
    return itemlist


def translate(url_translate):
    #### Opción 1: 'follow_redirects=False'
    ## Petición 1
    url = "http://translate.google.com/translate?depth=1&nv=1&rurl=translate.google.com&sl=ru&tl=es&u=" + url_translate
    data = dhe(httptools.downloadpage(url, follow_redirects=False).data)
    ## Petición 2
    url = scrapertools.get_match(data, ' src="([^"]+)" name=c ')
    data = dhe(httptools.downloadpage(url, follow_redirects=False).data)
    ## Petición 3
    url = scrapertools.get_match(data, 'URL=([^"]+)"')
    data = dhe(httptools.downloadpage(url).data)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    
    return data

def month_convert(mes):
    try:
        return { 'January': 1, 'February': 2, 'March': 3, 'April':4, 'May' : 5, 'June' : 6, 'July' : 7, 'August' : 8, 'September' : 9, 'October' : 10, 'November' : 11, 'December' : 12 }[mes]
    except:
        return { 'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril':4, 'Mayo' : 5, 'Junio' : 6, 'Julio' : 7, 'Agosto' : 8, 'Septiembre' : 9, 'Octubre' : 10, 'Noviembre' : 11, 'Diciembre' : 12 }[mes]
