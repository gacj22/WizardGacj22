# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para lukas-gtr
#------------------------------------------------------------

import re
import urlparse
import cookielib
import urllib,urllib2
import zlib, json
from urlparse import urlparse

from core import config
from core import httptools
from core import logger
from core import scrapertools
from core.item import Item
from platformcode import platformtools
from core import servertools

DEBUG = config.get_setting("debug")

CANALES = []
CANALES.append({"title":"AFICIÓN","base":"la_aficion_del_atletico_de_madrid-ivia-0-2-"})
CANALES.append({"title":"ENTREVISTAS","base":"entrevistas_del_atletico_de_madrid-ivia-0-1-"})
CANALES.append({"title":"GOLES","base":"goles_del_atletico_de_madrid-ivia-0-206-"})
CANALES.append({"title":"HISTORIA","base":"nuestra_historia_del_atletico_de_madrid-ivia-0-3-"})
CANALES.append({"title":"JUGADORES","base":"los_jugadores_del_atletico_de_madrid-ivia-0-639-"})
CANALES.append({"title":"REPORTAJES","base":"reportajes_del_atletico_de_madrid-ivia-0-7-"})

def mainlist(item):
    logger.info("[colchonero.py] mainlist")
    itemlist = []
    item.thumbnail = 'http://i67.tinypic.com/mlkqqo.jpg'
    if item.url[0:7] != 'http://':
        item.base = 'http://www.colchonero.com/ultimos_videos_del_atletico_de_madrid-ivia-1-0-'
        item.pag = "1"
        item.url = item.base + item.pag + '.htm'
        item.pags = ''
        item.tit = 'TODOS LOS VÍDEOS'
        #---- PARTIDOS ------
        title = '[COLOR blue][B]PARTIDOS[/B][/COLOR]'
        thumbnail = item.thumbnail
        itemlist.append( Item( channel=item.channel, title=title, action="partidos", thumbnail=item.thumbnail, folder=True ))
        #--------------------
        for chn in CANALES:
            tit = chn["title"]
            title = '[COLOR blue][B]%s[/B][/COLOR]' %tit
            base = 'http://www.colchonero.com/videos_de_%s' %chn["base"]
            pag = "1"
            url = base + pag + '.htm'
            pags = ''
            thumbnail = item.thumbnail
            itemlist.append( Item( channel=item.channel, title=title, action="mainlist", url=url, base=base, pag=pag, pags=pags, tit=tit,  thumbnail=item.thumbnail, folder=True ))
    else:
        title = '[COLOR blue][B]%s[/B] - Página %s[/COLOR]' %(item.tit,item.pag)
        itemlist.append( Item( channel=item.channel, title=title, action="nada", url=None, thumbnail=item.thumbnail, folder=False ))
    data = httptools.downloadpage(item.url).data
    if item.pags == '':
        matches = re.findall('htm\?pag=(\d+?)"',data)
        item.pags = matches[len(matches)-1]
    matches = re.findall('id="jPhotoVideo[\S\s]+?src="(.*?)"[\S\s]+?href="(.*?)"[\S\s]+?title="(.*?)>',data)
    br = True
    for thumb,url,title in matches:
        if br: color='red'
        else: color='white'
        fulltitle = title.replace('"','')
        title = '[COLOR %s][B]%s[/B][/COLOR]' %(color,title.replace('"',''))
        br = not br
        url = 'http://www.colchonero.com/%s' %url
        itemlist.append( Item( channel=item.channel, title=title, fulltitle=fulltitle, action='play', tipo="ytb", url=url, thumbnail=thumb, folder=True ))
    if item.pag != item.pags:
        pag = str(int(item.pag)+1)
        url = item.base + pag + '.htm'
        title = '[COLOR blue]>>> Ir a [B]%s[/B] - Página %s >>>[/COLOR]' %(item.tit,pag)
        itemlist.append( Item( channel=item.channel, title=title, action="mainlist", url=url, base=item.base, pag=pag, pags=item.pags, tit=item.tit,  thumbnail=item.thumbnail, folder=True ))
    return itemlist

def convert_date(date):
    match = re.search('(\d{2}\/\d{2}\/\d{4})',date)
    if match:
        date = match.group(1)
    li = date.split('/')
    day,month,year = li[0],li[1],li[2]
    import datetime
    d = datetime.datetime(int(year), int(month), int(day))
    #fmt = "%A, %d de %B de %Y"
    fmt = "%d de %B de %Y"
    fm2 = "%H:%M"
    fch = d.strftime(fmt)
    datosdic = {'January':'Enero', 'February':'Febrero', 'March':'Marzo', 'April':'Abril', 'May':'Mayo', 'June':'Junio', 'July':'Julio', 'August':'Agosto', 'September':'Septiembre', 'October':'Octubre', 'November':'Noviembre', 'December':'Diciembre', 'Monday':'Lunes', 'Tuesday':'Martes', 'Wednesday':'Miércoles', 'Thursday':'Jueves', 'Friday':'Viernes', 'Saturday':'Sábado', 'Sunday':'Domingo'}
    for key, value in datosdic.iteritems():
        if key in fch:
            fch = fch.replace(key,value)
    return fch

def findvideos(item):
    itemlist=[]
    data = httptools.downloadpage(item.url).data
    title = '[B]%s[/B]' %item.title.strip()
    
    itemlist.append( Item( channel=item.channel, title=title, action='nada', url='', thumbnail=item.thumbnail, folder=False ))
    if 'First Half' in data and 'Second Half' in data:
        matches = re.findall('mediumblue;">Channel.*?red;">(.*?)<[\s\S]*?Resolution.*?:\ *(.*?)<[\s\S]*?Bitrate.*?:\ *(.*?)<[\s\S]*?>Format.*?:\ *(.*?)<[\s\S]*?>Size.*?:\ *(.*?)<[\s\S]*?>Language.*?:.*?>(.*?)<[\s\S]*?First\ [Hh]alf[\s\S]*?<a href="(.*?)"[\s\S]*?Second\ [Hh]alf[\s\S]*?<a href="(.*?)"',data)
        for canal,resolucion,bitrate,formato,size,idioma,primera,segunda in matches:
            title = '     %s | %s | %s | %s' %(idioma,resolucion,canal,bitrate)
            itemlist.append( Item( channel=item.channel, title=title, action='nada', url='', thumbnail=item.thumbnail, folder=False ))
            title = '[COLOR tomato]          [B]Primera Parte[/B]  (%s)[/COLOR]' %urlparse(primera)[1]
            itemlist.append( Item( channel=item.channel, title=title, fulltitle=item.fulltitle, action='play', tipo="dbr", url=primera, thumbnail=item.thumbnail, folder=False ))
            title = '[COLOR tomato]          [B]Segunda Parte[/B]  (%s)[/COLOR]' %urlparse(segunda)[1]
            itemlist.append( Item( channel=item.channel , title=title , fulltitle=item.fulltitle, action='play', tipo="dbr", url=segunda, thumbnail=item.thumbnail, folder=False ))
    if 'Download' in data:
        matches = re.findall('mediumblue;">Channel.*?red;">(.*?)<[\s\S]*?Resolution.*?:\ *(.*?)<[\s\S]*?Bitrate.*?:\ *(.*?)<[\s\S]*?>Format.*?:\ *(.*?)<[\s\S]*?>Size.*?:\ *(.*?)<[\s\S]*?>Language.*?:.*?>(.*?)<[\s\S]*?Download[\s\S]*?<a href="(.*?)"',data)
        for canal,resolucion,bitrate,formato,size,idioma,download in matches:
            title = '     %s | %s | %s | %s' %(idioma,resolucion,canal,bitrate)
            itemlist.append( Item( channel=item.channel, title=title, action='nada', url='', thumbnail=item.thumbnail, folder=False ))
            title = '[COLOR tomato]          [B]Ver Evento[/B]  (%s)[/COLOR]' %urlparse(download)[1]
            itemlist.append( Item( channel=item.channel, title=title, fulltitle=item.fulltitle, action='play', tipo="dbr", url=download, thumbnail=item.thumbnail, folder=False ))
    if 'Single Link' in data:
        matches = re.findall('mediumblue;">Channel.*?red;">(.*?)<[\s\S]*?Resolution.*?:\ *(.*?)<[\s\S]*?Bitrate.*?:\ *(.*?)<[\s\S]*?>Format.*?:\ *(.*?)<[\s\S]*?>Size.*?:\ *(.*?)<[\s\S]*?>Language.*?:.*?>(.*?)<[\s\S]*?Single\ Link[\s\S]*?<a href="(.*?)"',data)
        for canal,resolucion,bitrate,formato,size,idioma,download in matches:
            title = '     %s | %s | %s | %s' %(idioma,resolucion,canal,bitrate)
            itemlist.append( Item( channel=item.channel , title=title, action='nada', url='', thumbnail=item.thumbnail, folder=False ))
            title = '[COLOR tomato]          [B]Partido Completo[/B]  (%s)[/COLOR]' %urlparse(download)[1]
            itemlist.append( Item( channel=item.channel, title=title, fulltitle=item.fulltitle, action='play', tipo="dbr", url=download, thumbnail=item.thumbnail, folder=False ))
    elif 'Full Match' in data:
        matches = re.findall('mediumblue;">Channel.*?red;">(.*?)<[\s\S]*?Resolution.*?:\ *(.*?)<[\s\S]*?Bitrate.*?:\ *(.*?)<[\s\S]*?>Format.*?:\ *(.*?)<[\s\S]*?>Size.*?:\ *(.*?)<[\s\S]*?>Language.*?:.*?>(.*?)<[\s\S]*?Full\ Match[\s\S]*?<a href="(.*?)"',data)
        for canal,resolucion,bitrate,formato,size,idioma,download in matches:
            title = '     %s | %s | %s | %s' %(idioma,resolucion,canal,bitrate)
            itemlist.append( Item( channel=item.channel , title=title, action='nada', url='', thumbnail=item.thumbnail, folder=False ))
            title = '[COLOR tomato]          [B]Partido Completo[/B]  (%s)[/COLOR]' %urlparse(download)[1]
            itemlist.append( Item( channel=item.channel, title=title, fulltitle=item.fulltitle, action='play', tipo="dbr", url=download, thumbnail=item.thumbnail, folder=False ))
    return itemlist

def partidos(item):
    itemlist = []
    thumbnail = item.thumbnail
    title = '[COLOR blue][B]PARTIDOS en Lukas-GTR[/B][/COLOR]'
    itemlist.append( Item( channel=item.channel, title=title, action="lukasgtr", thumbnail=item.thumbnail, folder=True ))
    title = '[COLOR blue][B]PARTIDOS en Footballia[/B][/COLOR]'
    itemlist.append( Item( channel=item.channel, title=title, action="futballia", thumbnail=item.thumbnail, folder=True ))
    return itemlist

def futballia(item):
    itemlist = []
    url = 'https://dl.dropboxusercontent.com/u/60677951/datptdfbl.data'
    data = httptools.downloadpage(url).data
    data = zlib.decompress(data)
    dicc = json.loads(data)
    for dats in dicc:
        if len(dats['urls'])>0:
            title = '[COLOR white][B]%s[/B][/COLOR]   [COLOR deepskyblue]%s %s (%s)[/COLOR]' %(dats['fecha'], dats['competicion'], dats['temporada'], dats['idioma'])
            itemlist.append( Item( channel=item.channel, title=title, action="nada", url=None, thumbnail=item.thumbnail, folder=False ))
            title = '     [COLOR gold]%s[/COLOR]' %dats['partido'].upper()
            if ' VS ' in title:
                title = title.replace(" VS "," [COLOR orange]vs[/COLOR] ")
            fulltitle = dats['partido']
            if len(dats['urls'])==1:
                url = 'http://footballia.net%s' %dats['urls'][0]
                import xbmc
                xbmc.log('XXURL='+url)
                itemlist.append( Item( channel=item.channel, title=title, fulltitle=fulltitle, action="play", tipo='fbl', url=url, thumbnail=item.thumbnail, folder=False ))
            else:
                num=0
                for urls in dats['urls']:
                    url = 'http://footballia.net%s' %urls
                    num += 1
                    title2 = '%s  [COLOR brown]Parte %s[/COLOR]' %(title,str(num))
                    itemlist.append( Item( channel=item.channel, title=title2, fulltitle=fulltitle, action="play", tipo='fbl', url=url, thumbnail=item.thumbnail, folder=False ))
    return itemlist

def lukasgtr(item):
    itemlist = []
    url = 'https://dl.dropboxusercontent.com/u/60677951/datptdatl.data'
    data = httptools.downloadpage(url).data
    data = zlib.decompress(data)
    dicc = json.loads(data)
    date_old = ''
    for dats in dicc['datos']:
        date = convert_date(dats['date'])
        if date != date_old:
            date_old = date
            title = '[COLOR white][B]%s[/B][/COLOR]   [COLOR deepskyblue]%s[/COLOR]' %(date, dats['event'])
            itemlist.append( Item( channel=item.channel, title=title, action="nada", url=None, thumbnail=item.thumbnail, folder=False ))
        title = dats['event'] + ' ' + dats['match'] + ' (' + dats['date'] + ')'
        title = '     [COLOR gold]%s[/COLOR]' %dats['match']
        if ' vs ' in title:
            title = title.replace(" vs "," [COLOR orange]vs[/COLOR] ")
        fulltitle = dats['match']
        url = dats['url']
        itemlist.append( Item( channel=item.channel, title=title, fulltitle=fulltitle, action="findvideos", url=url, thumbnail=dats['thumb'], folder=True ))
    return itemlist

def settingCanal(item):
    return platformtools.show_channel_settings()

def play(item):
    if item.tipo=="ytb":
        data = httptools.downloadpage(item.url).data
        item.url = 'http://www.youtube.com/watch?v=%s' %re.findall('\/embed\/(.*?)\?',data)[0]

    if item.tipo=="fbl":
        itemlist=[]
        itemlist.append(item.clone(action="play", url=item.url, server="directo"))
    else:
        itemlist = servertools.find_video_items(data=item.url)

    for videoitem in itemlist:
        videoitem.title = item.fulltitle
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist

def nada(item):
    return None
