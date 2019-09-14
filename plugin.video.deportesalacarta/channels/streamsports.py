# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para StreamSports
#------------------------------------------------------------
import os, re, xbmc
from core import scrapertools
from core import logger
from core import config
from core.item import Item
from core.scrapertools import decodeHtmlentities as dhe
from core import httptools

__channel__ = "streamsports"

host ="http://www.streamsports.co"
song = os.path.join(config.get_runtime_path(), 'music', 'Kasabian.mp3')


def mainlist(item):
    logger.info("deportesalacarta.channels.streamsports mainlist")
    itemlist = []
    #xbmc.executebuiltin('Container.Update(plugin://plugin.video.pelisalacarta/?action=listchannels)')
    #check =xbmc.getInfoLabel('Container.FolderPath')
    
    xbmc.executebuiltin('xbmc.PlayMedia('+song+')')

    itemlist.append(Item(channel=__channel__, title="Agenda/Directos", action="entradas", url=host, thumbnail="http://s6.postimg.org/as7g0t9qp/STREAMSPORTAGENDA.png",fanart="http://s6.postimg.org/5utvfp7rl/streamsportonairfan.jpg", folder=True))
    itemlist.append(Item(channel=__channel__, title="Fútbol", action="entradas", url=host+"/football/", thumbnail="http://s6.postimg.org/5w3t949ld/streamsportsfutbolthumb.png",fanart="http://s6.postimg.org/sm2y23ssx/streamsportsfutbolfan.jpg", folder=True))
    itemlist.append(Item(channel=__channel__, title="Baloncesto", action="entradas", url=host+"/basketball/", thumbnail="http://s6.postimg.org/cp465e0ep/streamsportbasketthumb.png",fanart="http://s6.postimg.org/rz41ckvwx/streamsportsbasketfan.jpg", folder=True))
    itemlist.append(Item(channel=__channel__, title="Más Deportes", action="categorias", url=host, thumbnail="http://i.imgur.com/3J5DbZA.png?1",fanart="http://s6.postimg.org/azzob2a35/streamsportsallfan.jpg", folder=True))

    return itemlist

def agendaglobal(item):
    itemlist = []
    try:
        item.channel = __channel__
        item.url = host
        item.thumbnail = "http://s6.postimg.org/as7g0t9qp/STREAMSPORTAGENDA.png"
        item.fanart = "http://s6.postimg.org/5utvfp7rl/streamsportonairfan.jpg"
        itemlist = entradas(item)
        if itemlist[-1].action == "entradas":
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def categorias(item):
    logger.info("deportesalacarta.channels.streamsports categorias")
    itemlist = []
    itemlist.append(Item(channel=__channel__, title="Fútbol Americano", action="entradas", url=host+"/americanfootball/", thumbnail=item.thumbnail, folder=True))

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)

    bloque = scrapertools.find_single_match(data, "<ul class='dropdown-menu'>(.*?)</ul>")
    patron = '<a href="([^"]+)">.*?alt="([^"]+)"' 
    matches = scrapertools.find_multiple_matches(bloque, patron)
    sports = {'Baseball':'Béisbol', 'Tennis':'Tenis', 'Boxing':'Boxeo',
              'Cycling':'Ciclismo', 'Motorsports':'Motor', 'Athletics':'Atletismo'}

    for scrapedurl, scrapedtitle  in matches:
        if scrapedtitle in sports:
            scrapedtitle = scrapedtitle.replace(scrapedtitle, sports[scrapedtitle])
        itemlist.append(Item(channel=__channel__, title=scrapedtitle, action="entradas", url=host+scrapedurl, thumbnail=item.thumbnail, folder=True))

    itemlist.sort(key=lambda item: item.title)
    return itemlist

def entradas(item):
    logger.info("deportesalacarta.channels.streamsports entradas")
    itemlist = []
    sports = {'Football':'Fútbol','Baseball':'Béisbol', 'Tennis':'Tenis', 'Boxing':'Boxeo', 'American Football':'Fútbol Americano',
              'Basketball':'Baloncesto','Cycling':'Ciclismo', 'Motorsports':'Motor', 'Athletics':'Atletismo', 'Others': 'Otros'}

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    data = dhe(data)
    logger.info(data)

    bloque = scrapertools.find_single_match(data, '<tbody>(.*?)</tbody>')
    patron = '<tr>.*?<img.*?src="([^"]+)" alt="([^"]+)"' \
             '.*?class="date">.*?,\s*([A-z]+)\s*(\d+).*?<span class=\'(timepast|time)\'>' \
             '<span class="hours">(.*?)</span>(.*?)</span>.*?title.*?title.*?>([^<]+)<' \
             '.*?<strong>(.*?)</strong>.*?<strong>(.*?)</strong>' \
             '.*?href="([^"]+)"'
    matches = scrapertools.find_multiple_matches(bloque, patron)

    for thumb, deporte, mes, dia, live, hora, minutos, torneo, equipo1, equipo2, scrapedurl  in matches:
        import datetime
        from time import strptime
        mes = str(strptime(mes,'%b').tm_mon)
        minutos = minutos.replace(":", "")
        fecha_partido = datetime.datetime(datetime.datetime.today().year, int(mes), int(dia), int(hora), int(minutos))
        fecha_partido = fecha_partido + datetime.timedelta(hours=1)
        fecha_actual = datetime.datetime.today()
        time = fecha_partido.strftime("%H:%M")
        date = fecha_partido.strftime("%d/%m")

        hora = time
        fecha = "["+date+"] "

        if fecha_partido <= fecha_actual: scrapedtitle = "[COLOR red][B]"+fecha+time+"[/B][/COLOR]"
        else: scrapedtitle = "[COLOR green][B]"+fecha+time+"[/B][/COLOR]"
        if (equipo1 or equipo2) != "N/A":
            evento_item = equipo1
            if equipo2:
                evento_item += " vs "+equipo2
            partido = " [COLOR darkorange][B]"+evento_item+"[/B][/COLOR]"
            scrapedtitle += partido
        else:
            partido = ""

        if deporte in sports: deporte = deporte.replace(deporte, sports[deporte])
        if item.url == host:
            scrapedtitle += " [COLOR blue]("+deporte+"-"+torneo+")[/COLOR]"
        else:
            scrapedtitle += " [COLOR blue]("+torneo+")[/COLOR]"
        
        itemlist.append( Item(channel=__channel__, title=scrapedtitle, action="findvideos", url=host+scrapedurl, thumbnail=host+thumb, fanart= item.fanart,fulltitle=scrapedtitle,
                              match=partido, competicion=deporte+"-"+torneo, folder=True, context="info_partido", date=date, time=time, evento=evento_item, deporte=deporte))

    return itemlist

def findvideos(item):
    logger.info("deportesalacarta.channels.streamsports play")
    itemlist = []
    if item.match == "": item.match = "[COLOR darkorange]"+item.competicion+"[/COLOR]"

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)
    bloque = scrapertools.find_single_match(data, '<h4 class="streamTypes" id="p2p">(.*?)</table>')

    if bloque != "":
        bloques = scrapertools.find_multiple_matches(bloque, '(<td>[^<]+<span style="font-size:10px">.*?</span></span></td>)')
        for match in bloques:
            patron = '<td>(.*?)<.*?<td>(.*?)<.*?<td>(.*?)<.*?<a href="([^"]+)"'
            matches = scrapertools.find_multiple_matches(match, patron)
            for bitrate, server, idioma, scrapedurl in matches:
                if not scrapedurl.startswith("acestream") and not scrapedurl.startswith("sop"): continue
                server = "[COLOR blue]"+server.strip()+"[/COLOR] "
                bitrate = " [COLOR green]("+bitrate.strip()+")[/COLOR]"
                idioma = " [COLOR gold]("+idioma.strip()+")[/COLOR]"
                scrapedtitle = server + item.match + bitrate + idioma
                scrapedurl= scrapedurl + "|" + item.match
        
                itemlist.append(Item(channel=__channel__, title=scrapedtitle, url=scrapedurl, action="play", idioma=idioma, thumbnail=item.thumbnail, fanart= item.fanart,folder=False))
        itemlist.sort(key=lambda item: item.idioma, reverse=True)

    if "No Sopcast/Acestream streams added yet" in data or len(itemlist) == 0:
        itemlist.append(Item(channel=__channel__, title="[COLOR yellow]No hay enlaces disponibles. Inténtalo más tarde[/COLOR]", url="", action="", thumbnail=item.thumbnail,fanart= "http://s6.postimg.org/8wp93eaa9/streamsportsnolinks.jpg", folder=False))

    return itemlist


def play(item):
    xbmc.executebuiltin('xbmc.PlayMedia(Stop)')
    itemlist = []
    itemlist.append(Item(channel=__channel__, title=item.title, server="p2p", url=item.url, action="play", folder=False))

    return itemlist
