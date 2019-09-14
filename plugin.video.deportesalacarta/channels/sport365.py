# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para Sport365
#------------------------------------------------------------

import base64
import re
import datetime
import urllib
from HTMLParser import HTMLParser

from core import httptools
from core import jsontools
from core import scrapertools
from core import logger
from core import config
from core.item import Item
from lib import jscrypto
from platformcode import platformtools

host = "http://www.sport365.live/es/home"


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone(title="Agenda/Directos", action="entradas", url="http://www.sport365.live/es/events/-/1/-/-/60", fanart="http://i.imgur.com/bCn8lHB.jpg?1"))
    itemlist.append(item.clone(title="Redifusiones", action="entradas", url="http://www.sport365.live/es/events/-/2/-/-/60", fanart="http://i.imgur.com/bCn8lHB.jpg?1"))
    itemlist.append(item.clone(title="Agenda por idioma", action="idiomas", url="http://www.sport365.live/es/sidebar", fanart="http://i.imgur.com/bCn8lHB.jpg?1"))

    itemlist.append(item.clone(title="", action=""))
    itemlist.append(item.clone(title="Configurar canal...", action="configuracion", fanart="http://i.imgur.com/bCn8lHB.jpg?1",
                               text_color="gold"))

    return itemlist


def configuracion(item):
    from platformcode import platformtools
    ret = platformtools.show_channel_settings()
    return ret


def agendaglobal(item):
    itemlist = []
    try:
        item.channel = "sport365"
        item.url = "http://www.sport365.live/es/events/-/1/-/-/60"
        item.thumbnail="http://i.imgur.com/hJ2vhip.png"
        item.fanart="http://i.imgur.com/bCn8lHB.jpg?1"
        itemlist = entradas(item)
        for item_global in itemlist:
            if item_global.action == "":
                itemlist.remove(item_global)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def entradas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)

    key_save = config.get_setting("key_cryp", "sport365")
    if not key_save:
        key = getkey()
    else:
        key = base64.b64decode(key_save)

    colores_val = ['', 'yellow', 'blue', 'chocolate', 'violet', 'orange']
    color = colores_val[config.get_setting("resaltar_spanish", "sport365")]

    fechas = scrapertools.find_multiple_matches(data, '<td colspan=9[^>]+>(\d+\.\d+\.\d+)<')
    if "Redifusiones" in item.title and not fechas:
        itemlist.append(item.clone(action="", title="No hay ninguna emisión prevista actualmente"))
        return itemlist

    for i, f in enumerate(fechas):
        delimit = '</table>'
        if i != len(fechas) - 1:
            delimit = fechas[i+1]
        bloque = scrapertools.find_single_match(data, '%s<(.*?)%s' % (f, delimit))
        patron = 'onClick=.*?,\s*"([^"]+)".*?<td rowspan=2.*?src="([^"]+)".*?<td rowspan=2.*?>(\d+:\d+)<' \
                 '.*?<td.*?>([^<]+)<.*?<td.*?>(.*?)/td>.*?<tr.*?<td colspan=2.*?>([^<]+)<'
        matches = scrapertools.find_multiple_matches(bloque, patron)
        for url, thumb, hora, title, datos, deporte in matches:
            evento = title.replace("-", "vs")
            text_color = "red"
            if "green-big.png" in thumb:
                text_color = "green"
            if "/" in deporte:
                deporte = deporte.split(" /", 1)[0]
            if "<span" in datos:
                calidad, idioma = scrapertools.find_single_match(datos, '>([^<]+)</span>([^<]+)<')
                datos = "%s/%s/%s" % (deporte, calidad.replace("HQ", "HD"), idioma)
                if idioma == "Español" and color:
                    text_color = color
            else:
                datos = "%s/%s" % (deporte, datos[:-1])
                if "Español" in datos and color:
                    text_color = color


            fecha = f.replace(".", "/")

            url = jsontools.load_json(base64.b64decode(url))
            try:
                url = jscrypto.decode(url["ct"], key, url["s"].decode("hex"))
            except:
                key = getkey(True)
                url = jscrypto.decode(url["ct"], key, url["s"].decode("hex"))
            url = "http://www.sport365.live" + url.replace('\\/','/').replace('"',"")
            horas, minutos = hora.split(":")
            dia, mes, year = fecha.split("/")
            fecha_evento = datetime.datetime(int(year), int(mes), int(dia),
                                             int(horas), int(minutos))
            fecha_evento = fecha_evento + datetime.timedelta(hours=1)
            hora = fecha_evento.strftime("%H:%M")
            date = fecha_evento.strftime("%d/%m")
            if len(fechas) == 1:
                title = "[COLOR %s]%s - %s [/COLOR][COLOR darkorange](%s)[/COLOR]" % (text_color, hora, title, datos)
            else:
                title = "[COLOR %s][%s] %s - %s[/COLOR] [COLOR darkorange](%s)[/COLOR]" % (text_color, date, hora, title, datos)
            itemlist.append(item.clone(action="findvideos", title=title, url=url, date=date, time=hora, evento=evento, deporte=deporte, context="info_partido",
                                       info=datos))

    return itemlist


def idiomas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    
    matches = scrapertools.find_multiple_matches(data, "<option value='([0-9]+)'>.*?\/\s*(.*?)<")
    for value, title in matches:
        url = "http://www.sport365.live/es/events/-/1/-/%s/60" % value
        if title == "Español":
            itemlist.insert(0, item.clone(action="entradas", url=url, title=title))
        else:
            itemlist.append(item.clone(action="entradas", url=url, title=title))
    
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)

    if "Las referencias de la transmisión van a ser publicadas" in data:
        itemlist.append(item.clone(title="Los enlaces estarán disponibles entre 5-10 minutos antes de que empiece", action=""))
        return itemlist

    key_save = config.get_setting("key_cryp", "sport365")
    if not key_save:
        key = getkey()
    else:
        key = base64.b64decode(key_save)

    matches = scrapertools.find_multiple_matches(data, "<span id='span_watch_links'.*?, '([^']+)'")
    if not matches:
        matches = scrapertools.find_multiple_matches(data, "<span id='span_code_links'.*?, '([^']+)'")
    h = HTMLParser()
    for i, url in enumerate(matches):
        url = jsontools.load_json(base64.b64decode(url))
        try:
            url = jscrypto.decode(url["ct"], key, url["s"].decode("hex"))
        except:
            key = getkey(True)
            url = jscrypto.decode(url["ct"], key, url["s"].decode("hex"))
        data_url = url.replace('\\/','/').replace("\\", "")
        data_url = h.unescape(data_url)

        url = scrapertools.find_single_match(data_url, 'src=[\'"](.*?)"')
        title = "[COLOR green]Stream %s - [/COLOR][COLOR darkorange](%s)[/COLOR]" % (i+1, item.info)
        itemlist.append(item.clone(action="play", url=url, title=title))

    return itemlist
    

def play(item):
    itemlist = []

    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, '<iframe.*?src="([^"]+)"')
    if not url:
        platformtools.dialog_notification("Stream no disponible", "No es posible conectar con la emisión")
        return []
    elif "/matras.jpg" in data:
        platformtools.dialog_notification("Stream caído", "Inténtalo de nuevo pasados unos minutos")
        return []
    
    h = HTMLParser()
    url = h.unescape(url)
    data = httptools.downloadpage(url).data
    f = scrapertools.find_single_match(data, 'name="f" value="([^"]+)"')
    d = scrapertools.find_single_match(data, 'name="d" value="([^"]+)"')
    r = scrapertools.find_single_match(data, 'name="r" value="([^"]+)"')
    url_post = scrapertools.find_single_match(data, "'action',\s*'([^']+)'")
    if not url_post:
        platformtools.dialog_notification("Stream no disponible", "No es posible conectar con la emisión")
        return []

    post = {'r': r, 'd':d, 'f':f}
    post = urllib.urlencode(post)
    data = httptools.downloadpage(url_post, post).data
    try:
        get_links(data)
    except:
        pass

    key_save = config.get_setting("key_cryp", "sport365")
    if not key_save:
        key = getkey()
    else:
        key = base64.b64decode(key_save)
    data_crypto = scrapertools.find_single_match(data, "\};[A-z0-9]{43}\(.*?,.*?,\s*'([^']+)'")
    url = jsontools.load_json(base64.b64decode(data_crypto))
    try:
        url = jscrypto.decode(url["ct"], key, url["s"].decode("hex"))
    except:
        key = getkey(True)
        url = jscrypto.decode(url["ct"], key, url["s"].decode("hex"))  
        
    url = url.replace('\\/', '/').replace("\\", "").replace('"', "")
    headers_test = {'Referer': url_post, 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'}
    response = httptools.downloadpage(url, headers=headers_test, follow_redirects=False, only_headers=True, replace_headers=True)
    if response.code == 406:
        response = httptools.downloadpage(url, headers=headers_test, follow_redirects=False, only_headers=True, replace_headers=True, cookies=False)
    if response.code == 406:
        platformtools.dialog_notification("Stream no disponible", "No es posible conectar con la emisión")
        return []
    url += "ndex.m3u8|Referer=%s&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0" % url_post

    itemlist.append([".m3u8 [Sport365]", url])
    return itemlist


def getkey(overwrite=False):
    data = httptools.downloadpage(host).data

    js = scrapertools.find_multiple_matches(data, 'src="(http://s1.medianetworkinternational.com/js/[A-z0-9]{32}.js)')
    data_js = httptools.downloadpage(js[-1]).data

    str_wise = scrapertools.find_single_match(data_js, ".join\(''\);\}\('(.*?)\)\);")
    while True:
        result = decrypt(str_wise)
        if not "w,i,s,e" in result:
            break
        str_wise = scrapertools.find_single_match(result, ".join\(''\);\}\('(.*?)\)\);")

    
    key = scrapertools.find_single_match(result, 'return "([^"]+)"')
    key_save = config.get_setting("key_cryp", "sport365")
    if not key_save or overwrite:
        key_save = config.set_setting("key_cryp", base64.b64encode(key), "sport365")    

    return key


def decrypt(data):
    cadena1, cadena2, cadena3, cadena4 = data.split("','")
    cadena4 = cadena4.replace("'", "")
    j = 0
    c = 0
    i = 0
    list1 = []
    list2 = []
    while True:
        if j < 5:
            list2.append(cadena1[j])
        else:
            if j < len(cadena1):
                list1.append(cadena1[j])
        j += 1
        if c < 5:
            list2.append(cadena2[c])
        else:
            if c < len(cadena2):
                list1.append(cadena2[c])
        c += 1
        if i < 5:
            list2.append(cadena3[i])
        else:
            if i < len(cadena3):
                list1.append(cadena3[i])
        i += 1
        if (len(cadena1) + len(cadena2) + len(cadena3) + len(cadena4)) == (len(list1) + len(list2) + len(cadena4)):
            break
    cadena5 = "".join(list1)
    cadena6 = "".join(list2)
    c = 0
    resultado = []
    j = 0
    for j in range(0, len(list1), 2):
        operando = -1
        if (ord(cadena6[c]) % 2):
            operando = 1

        try:
            resultado.append(chr(int(cadena5[j:j+2], 36) - operando))
        except:
            pass
        c += 1
        if c >= len(list2):
            c = 0
    result = "".join(resultado)

    return result


def get_links(data):
    adshell = scrapertools.find_single_match(data, "<script src=[\"'](http://tags2.adshell.net.*?)['\"]")
    data_shell = httptools.downloadpage(adshell).data

    url = scrapertools.find_single_match(data_shell, ",url:'([^']+)'")
    headers = {'Referer': adshell}
    data = httptools.downloadpage(url, headers=headers).data