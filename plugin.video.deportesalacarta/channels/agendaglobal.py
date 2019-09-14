# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para Agenda Global
#------------------------------------------------------------

import os, re
import glob
import datetime
import time

from core import channeltools
from core import httptools
from core import scrapertools
from core import logger
from core import config
from core.item import Item
from platformcode import platformtools

__channel__ = "agendaglobal"


def mainlist(item):
    logger.info("deportesalacarta.channels.agendaglobal mainlist")
    itemlist = []
    fanart ="https://s6.postimg.org/cfotkfok1/agendafutbol.jpg"
    itemlist.append(Item(channel=__channel__, title="[COLOR yellowgreen]Marcadores[/COLOR]", action="marcador", url="http://www.transfermarkt.es/ticker/index/live", deporte="futbol", thumbnail="http://i.imgur.com/7ouQsE9.png", fanart=fanart))
    itemlist.append(Item(channel=__channel__, title="[COLOR teal]Agenda Futbolera Completa[/COLOR]", action="agenda", deporte="futbol", thumbnail="http://i.imgur.com/tvbCnV6.png", fanart=fanart))
    itemlist.append(Item(channel=__channel__, title="[COLOR green]      Partidos en juego[/COLOR]", action="agenda", deporte="futbol", thumbnail="https://s6.postimg.org/j05ufdno1/agendalive.png", fanart=fanart))
    itemlist.append(Item(channel=__channel__, title="[COLOR green]      Partidos de hoy[/COLOR]", action="agenda", deporte="futbol", thumbnail="https://s6.postimg.org/mgbqu5p1t/agendamatchoy.png",fanart=fanart))
    itemlist.append(Item(channel=__channel__, title="[COLOR green]      Partidos de mañana[/COLOR]", action="agenda", deporte="futbol", thumbnail="https://s6.postimg.org/lorgdxedt/agendanext.png",fanart=fanart))
    itemlist.append(Item(channel=__channel__, title="[COLOR green]      Filtrar por equipo[/COLOR]", action="filtro", filtro="equipo", deporte="futbol", thumbnail="https://s6.postimg.org/8m5h5ijv5/agendaequipo.png", fanart=fanart))
    itemlist.append(Item(channel=__channel__, title="[COLOR teal]Agenda Deportiva Completa[/COLOR]", action="agenda", thumbnail="http://i.imgur.com/T82CZ6S.png",fanart=fanart))
    itemlist.append(Item(channel=__channel__, title="[COLOR green]      Eventos en directo[/COLOR]", action="agenda", thumbnail="https://s6.postimg.org/890au3xg1/agendadeporteslive.png",fanart=fanart))
    itemlist.append(Item(channel=__channel__, title="[COLOR green]      Eventos de hoy[/COLOR]", action="agenda", thumbnail="https://s6.postimg.org/ljjk9vymp/agendadeportestoday.png",fanart=fanart))
    itemlist.append(Item(channel=__channel__, title="[COLOR green]      Eventos de mañana[/COLOR]", action="agenda", thumbnail="https://s6.postimg.org/hr4n7w8i9/agendadeportestomorrow.png",fanart=fanart))
    itemlist.append(Item(channel=__channel__, title="[COLOR green]      Filtrar por deporte[/COLOR]", action="filtro", filtro="deporte", thumbnail="https://s6.postimg.org/meap9nvv5/agendadeportesfiltrar.png",fanart=fanart))
    itemlist.append(Item(channel=__channel__, title="", action="", thumbnail=item.thumbnail,fanart=fanart))
    itemlist.append(Item(channel=__channel__, title="Configurar canales incluidos...", action="configuracion", text_color="gold", thumbnail=item.thumbnail,fanart=fanart, folder=False))

    return itemlist


def configuracion(item):
    logger.info("deportesalacarta.channels.agendaglobal configuracion")
    controls = []
    channels_path = os.path.join(config.get_runtime_path(), "channels", '*.xml')
    for infile in sorted(glob.glob(channels_path)):
        channel_name = os.path.basename(infile)[:-4]
        include = config.get_setting("include_in_agenda", channel_name)
        if include != "":
            params = channeltools.get_channel_parameters(channel_name)
            control = {'id': channel_name, 'type': "bool", 'label': params["title"], 
                       'default': include, 'enabled': True, 'visible': True}

            controls.append(control)

    return platformtools.show_channel_settings(list_controls=controls, callback="save", item=item,
                                               caption= "Canales incluidos en Agenda Global")


def save(item, values):
    canales = []
    for v in values:
        config.set_setting("include_in_agenda", values[v], v)
        if values[v]:
            canales.append(v)

    if not canales:
        config.set_setting("canales_incluidos", "ninguno", "agendaglobal")
    else:
        config.set_setting("canales_incluidos", ",".join(canales), "agendaglobal")


def filtro(item):
    logger.info("deportesalacarta.channels.agendaglobal filtros")
    text = ""
    text = config.get_setting("last_search_" + item.filtro, item.channel)
    texto = platformtools.dialog_input(default=text, heading=item.title)
    if texto is None:
        return

    config.set_setting("last_search_" + item.filtro, texto, item.channel)

    return search(item, texto)


def search(item, texto):
    logger.info("deportesalacarta.channels.agendaglobal filtros")
    item.filtro = texto
    return agenda(item)


def agenda(item):
    logger.info("deportesalacarta.channels.agendaglobal agenda")
    itemlist = []

    canales = config.get_setting("canales_incluidos", "agendaglobal")
    if canales:
        if canales == "ninguno":
            return itemlist
        channels_list = canales.split(",")
    else:
        channels_path = os.path.join(config.get_runtime_path(), "channels", '*.xml')
        channels_list = []
        for infile in sorted(glob.glob(channels_path)):
            channel_name = os.path.basename(infile)[:-4]
            if config.get_setting("include_in_agenda", channel_name):
                channels_list.append(channel_name)

    if not channels_list:
        return itemlist

    threads = []
    results = []
    len_list = len(channels_list)
    progreso = platformtools.dialog_progress("Recopilando eventos everywhere...", "")
    try:
        from threading import Thread
        t = Thread(target=agenda_search, args=[results, channels_list, item])
        t.setDaemon(True) 
        t.start()
        threads.append(t)
        try:
            pendiente =  len([th for th in threads if th.is_alive()])
        except:
            pendiente =  len([th for th in threads if th.isAlive()])

        while pendiente:
            try:
                pendiente =  len([th for th in threads if th.is_alive()])
            except:
                pendiente =  len([th for th in threads if th.isAlive()])
            porcentaje = (len_list - pendiente) * 100 / len_list
            progreso.update(porcentaje, "Paciencia. Quedan %s de %s canales........." % (str(pendiente), str(len_list)))
    except:
        import traceback
        logger.info(traceback.format_exc())
        try:
            agenda_search(results, channels_list, item, progreso)
        except:
            import traceback
            logger.info(traceback.format_exc())

    canal_actual = ""
    for item_a in results:
        try:
            if item.deporte == "futbol":
                if re.search(r'(?i)Futbol|Fútbol|Soccer', item_a.deporte) and not re.search(r'(?i)Playa|Beach|American|Sala', item_a.deporte):
                    live = False
                    if item_a.channel != canal_actual:
                        title_channel = channeltools.get_channel_parameters(item_a.channel)["title"]
                        canal_actual = item_a.channel

                    item_a.evento = re.sub(r'(?i)─|–|-', ' vs ', item_a.evento)
                    item_a.evento = item_a.evento.decode('utf-8').title()
                    item_a.evento = re.sub(r'(?i)vs', ' vs ', item_a.evento)
                    item_a.evento = re.sub(r'\s{2,}', ' ', item_a.evento)
                    
                    if item.filtro:
                        buscado = item.filtro
                        if not re.search(r'(?i)'+buscado, item_a.evento):
                            continue

                    if item_a.time == "live":
                        item_a.time = datetime.datetime.today().strftime("%H:%M")
                        live = True
                    if len(item_a.time) == 4:
                        item_a.time = "0" + item_a.time
                    if re.search(r'(/\d{4})', item_a.date):
                        item_a.date = re.sub(r'(/\d{4})', '', item_a.date)
                    if not re.search(r'(\d{2}/)', item_a.date):
                        item_a.date = "0" + item_a.date
                    if not re.search(r'(/\d{2})', item_a.date):
                        item_a.date = item_a.date.split("/")[0] + "/0" + item_a.date.split("/")[1]

                    # Sacamos la fecha y hora del item y la actual para saber si el evento ya ha comenzado
                    day, month = item_a.date.split("/")
                    hora_item = time.strptime(item_a.time, "%H:%M")
                    fecha_item = datetime.datetime(datetime.date.today().year, int(month), int(day), hora_item.tm_hour, hora_item.tm_min)
                    hora_actual = time.localtime()
                    fecha_actual = datetime.datetime(datetime.date.today().year, datetime.date.today().month, datetime.date.today().day,
                                                     hora_actual.tm_hour, hora_actual.tm_min)
                    dia_actual = datetime.date.today()
                    dia_item = datetime.date(datetime.date.today().year, int(month), int(day))

                    if fecha_item <= fecha_actual:
                        if "mañana" in item.title:
                            continue
                        # Comprobamos si ya ha finalizado el partido
                        if (fecha_item + datetime.timedelta(hours=2, minutes=30)) < fecha_actual:
                            continue
                        title = "[COLOR red]" + item_a.time + " [/COLOR]"
                    elif "mañana" in item.title:
                        dia_tomorrow = dia_actual + datetime.timedelta(days=1)
                        if dia_item == dia_tomorrow:
                            title = "[COLOR green]" + item_a.date + " " + item_a.time + " [/COLOR]"
                        else:
                            continue
                    else:
                        if "en juego" in item.title:
                            continue
                        elif "hoy" in item.title and dia_item != dia_actual:
                            continue
                        if "hoy" in item.title:
                            title = "[COLOR green]" + item_a.time + " [/COLOR]"
                        else:
                            title = "[COLOR green]" + item_a.date + " " + item_a.time + " [/COLOR]"

                    title += "[COLOR orange][B]"+item_a.evento + " [/B][/COLOR][COLOR lightblue]"
                    if item_a.info:
                        info = item_a.info.replace("Fútbol/", "")
                        info = unicode(info, 'utf-8')
                        title += "[COLOR blue](%s)[/COLOR]" % info

                    title += " [" + title_channel + "][/COLOR]"
                    if live:
                        title = title.replace(item_a.time, "LIVE  ")
                        
                    # Fecha para comparar los items
                    item_a.month = fecha_item.month
                    item_a.day = fecha_item.day
                    itemlist.append(item_a.clone(title=title, context="info_partido"))
            else:
                if not re.search(r'(?i)Futbol|Fútbol|Soccer', item_a.deporte):
                    live = False
                    if item_a.channel != canal_actual:
                        title_channel = channeltools.get_channel_parameters(item_a.channel)["title"]
                        canal_actual = item_a.channel

                    item_a.evento = item_a.evento.decode('utf-8').title()
                    item_a.deporte = item_a.deporte.decode('utf-8').title()
                    if item.filtro:
                        buscado = item.filtro
                        if not re.search(r'(?i)'+buscado, item_a.deporte):
                            continue

                    if item_a.time == "live":
                        item_a.time = datetime.datetime.today().strftime("%H:%M")
                        live = True

                    if len(item_a.time) == 4:
                        item_a.time = "0" + item_a.time
                    if re.search(r'(/\d{4})', item_a.date):
                        item_a.date = re.sub(r'(/\d{4})', '', item_a.date)
                    if not re.search(r'(\d{2}/)', item_a.date):
                        item_a.date = "0" + item_a.date
                    if not re.search(r'(/\d{2})', item_a.date):
                        item_a.date = item_a.date.split("/")[0] + "/0" + item_a.date.split("/")[1]

                    # Sacamos la fecha y hora del item y la actual para saber si el evento ya ha comenzado
                    day, month = item_a.date.split("/")
                    hora_item = time.strptime(item_a.time, "%H:%M")
                    fecha_item = datetime.datetime(datetime.date.today().year, int(month), int(day), hora_item.tm_hour, hora_item.tm_min)
                    hora_actual = time.localtime()
                    fecha_actual = datetime.datetime(datetime.date.today().year, datetime.date.today().month, datetime.date.today().day,
                                                     hora_actual.tm_hour, hora_actual.tm_min)
                    dia_actual = datetime.date.today()
                    dia_item = datetime.date(datetime.date.today().year, int(month), int(day))

                    if fecha_item <= fecha_actual:
                        if "mañana" in item.title:
                            continue
                        title = "[COLOR red]" + item_a.time + " [/COLOR]"
                    elif "mañana" in item.title:
                        dia_tomorrow = dia_actual + datetime.timedelta(days=1)
                        if dia_item == dia_tomorrow:
                            title = "[COLOR green]" + item_a.date + " " + item_a.time + " [/COLOR]"
                        else:
                            continue
                    else:
                        if "en directo" in item.title:
                            continue
                        elif "hoy" in item.title and dia_item != dia_actual:
                            continue
                        if "hoy" in item.title:
                            title = "[COLOR green]" + item_a.time + " [/COLOR]"
                        else:
                            title = "[COLOR green]" + item_a.date + " " + item_a.time + " [/COLOR]"
                    title += "[COLOR orange][B]" + item_a.evento + "[/B][/COLOR] [COLOR blue]("+item_a.deporte+")"
                    if item_a.info:
                        info = unicode(item_a.info, 'utf-8')
                        title = title[:-1] + "[COLOR blue]/%s)[/COLOR]" % info.replace(item_a.deporte+"/", "")
                    else:
                        title += "[/COLOR]"

                    title += " [COLOR lightblue][" + title_channel + "][/COLOR]"
                    if live:
                        title = title.replace(item_a.time, "LIVE  ")
                    # Fecha para comparar los items
                    item_a.month = fecha_item.month
                    item_a.day = fecha_item.day
                    itemlist.append(item_a.clone(title=title))
        except:
            import traceback
            logger.info(traceback.format_exc())

    itemlist.sort(key=lambda item: (item.month, item.day, item.time, item.title, item.channel))
    progreso.close()

    return itemlist

    
def agenda_search(results, channels_list, item, progreso=None):
    len_list = len(channels_list)
    for i, channel_name in enumerate(channels_list):
        try:
            exec "from channels import " + channel_name + " as channel"
            if progreso:
                porcentaje = i * (100/len_list)
                progreso.update(porcentaje, "Ahora estamos en...... %s" % channel_name.capitalize(),
                            "Paciencia. Quedan %s de %s canales........." % (str(len_list-(i)), str(len_list)))
            results.extend(channel.agendaglobal(item))
        except:
            import traceback
            logger.info(traceback.format_exc())


def marcador(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","", data)

    fecha = scrapertools.find_single_match(data, 'Begegnungen (\d+/\d+/\d+)')
    itemlist.append(item.clone(title="----- [I]"+fecha+"[/I]  -----", action=""))
    bloques = scrapertools.find_multiple_matches(data, '<table class="livescore">.*?src="([^"]+)" title="([^"]+)".*?href="([^"]+)".*?>(.*?)</table>')
    for thumb_liga, liga, url_liga, bloque in bloques:
        thumb_liga = "http:"+thumb_liga.replace("small/", "originals/")
        title = "[COLOR blue][B]"+liga+"[/B][/COLOR]"
        url_liga = "http://www.transfermarkt.es"+url_liga
        itemlist.append(Item(channel="futbol_window", title=title, thumbnail=thumb_liga, url=url_liga, liga=liga, action="ventana_liga", folder=False))

        patron = '<span class="spielzeitpunkt">(.*?)</span>.*?src="([^"]+)".*?<span class="vereinsname">.*?href="([^"]+)"' \
                 '.*?>([^<]+)</a>.*?<a title="(Previa|Crónica|Ticker en vivo).*?>([^<]+)</a>' \
                 '.*?<span class="vereinsname">.*?href="([^"]+)".*?>([^<]+)</a>'
        matches = scrapertools.find_multiple_matches(bloque, patron)
        for hora, thumb_home, url_home, home, tipo, result, url_away, away in matches:
            if "live-ergebnis" in hora:
                hora = scrapertools.find_single_match(hora+"<", '<span.*?>([^<]+)<')
            url_home = "http://www.transfermarkt.es" + url_home.replace("spielplan/", "startseite/")
            url_away = "http://www.transfermarkt.es" + url_away.replace("spielplan/", "startseite/")
            thumb_home = "http:" + thumb_home.replace("small/", "originals/")
            if "'" in hora:
                title = "     [COLOR red][%s][/COLOR] [COLOR darkorange]%s [COLOR red]%s[/COLOR] %s[/COLOR]" % (hora.replace("Descanso'", "Descanso"), home, result, away)
            elif "-:-" in result:
                title = "     [COLOR green][%s][/COLOR] [COLOR darkorange]%s [COLOR green]%s[/COLOR] %s[/COLOR]" % (hora, home, result, away)
            else:
                title = "     [COLOR gold][%s][/COLOR] [COLOR darkorange]%s [COLOR gold]%s[/COLOR] %s[/COLOR]" % (hora, home, result, away)
                
            itemlist.append(Item(channel="futbol_window", action="ventana", title=title, url_home=url_home, url_away=url_away, thumbnail=thumb_home,
                            evento=home+" vs "+away, date=fecha, time=hora, deporte="futbol", marcador="si", context="info_partido", folder=False))

    next_page = "http://www.transfermarkt.es"+scrapertools.find_single_match(data, '<a class="bx-next" href="([^"]+)"')
    year, month, day = scrapertools.find_single_match(next_page, 'datum/(\d+)-(\d+)-(\d+)')
    title = "[COLOR green]Siguiente día (%s/%s/%s)[/COLOR]" % (day, month, year)
    itemlist.append(item.clone(title=title, url=next_page, action="marcador"))
    prev_page = "http://www.transfermarkt.es"+scrapertools.find_single_match(data, '<a class="bx-prev" href="([^"]+)"')
    year, month, day = scrapertools.find_single_match(prev_page, 'datum/(\d+)-(\d+)-(\d+)')
    title = "[COLOR red]Día anterior (%s/%s/%s)[/COLOR]" % (day, month, year)
    itemlist.append(item.clone(title=title, url=prev_page, action="marcador"))
    itemlist.append(item.clone(title="[COLOR gold]Ir a una fecha concreta[/COLOR]", extra=fecha, action="fecha"))
    
    return itemlist


def fecha(item):
    fecha = platformtools.dialog_numeric(1, heading="Introduce la fecha", default=item.extra)
    if fecha:
        fecha = fecha.replace(" ", "0")
        dia, mes, year = fecha.split("/")
        item.url = "http://www.transfermarkt.es/live/index/datum/%s-%s-%s" % (year, mes, dia)
        return marcador(item)