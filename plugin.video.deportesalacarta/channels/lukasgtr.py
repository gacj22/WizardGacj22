# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para lukas-gtr
#------------------------------------------------------------

import re
import urlparse

from core import httptools
from core import config
from core import logger
from core import scrapertools
from core.item import Item
from platformcode import platformtools
from core import servertools

MAIN_HEADERS = []
MAIN_HEADERS.append( ["Accept","text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"] )
MAIN_HEADERS.append( ["Accept-Encoding","text/plain"] )
MAIN_HEADERS.append( ["Accept-Encoding","gzip, deflate"] )
MAIN_HEADERS.append( ["Accept-Language","es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3"] )
MAIN_HEADERS.append( ["Connection","keep-alive"] )
MAIN_HEADERS.append( ["Host","lukas-gtr.blogspot.com.es"] )
MAIN_HEADERS.append( ["Referer","http://lukas-gtr.blogspot.com.es/"] )
MAIN_HEADERS.append( ["User-Agent","Mozilla/5.0 (Windows NT 6.2; rv:23.0) Gecko/20100101 Firefox/23.0"] )

def convert_date(date):
    match = re.search('(\d{2}\/\d{2}\/\d{4})',date)
    if match:
        date = match.group(1)
    li = date.split('/')
    day,month,year = li[0],li[1],li[2]
    import datetime
    d = datetime.datetime(int(year), int(month), int(day))
    fmt = "%A, %d de %B de %Y"
    fm2 = "%H:%M"
    fch = d.strftime(fmt)
    datosdic = {'January':'Enero', 'February':'Febrero', 'March':'Marzo', 'April':'Abril', 'May':'Mayo', 'June':'Junio', 'July':'Julio', 'August':'Agosto', 'September':'Septiembre', 'October':'Octubre', 'November':'Noviembre', 'December':'Diciembre', 'Monday':'Lunes', 'Tuesday':'Martes', 'Wednesday':'Miércoles', 'Thursday':'Jueves', 'Friday':'Viernes', 'Saturday':'Sábado', 'Sunday':'Domingo'}
    for key, value in datosdic.iteritems():
        if key in fch:
            fch = fch.replace(key,value)
    return fch

def mainlist(item):
    logger.info("[lukasgtr.py] mainlist")
    itemlist = []
    item.thumbnail = 'http://i68.tinypic.com/wu1bvp.png'
    if item.url[0:7] != 'http://':
        item.url = 'http://lukas-gtr.blogspot.com.es'
    data = httptools.downloadpage(item.url).data
    matches = re.findall("post-title entry-title[\s\S]*?<a href='(.*?)'>\ *(.*?)\ *<[\s\S]*?<img\ alt.*?src=\"(.*?)\"",data)
    zgrid = []
    for url,title,thumb in matches:
        zrow = {}
        title = title.split
        title = ' '.join(title())
        match = re.search('\d{2}\/\d{2}\/\d{4}(.*)',title)
        if match:
            title = title.replace(match.group(1),'')
        else:
            title += ' ' + item.date
        title = title.replace(' : ',' - ')
        title2 = title.split(' - ')
        if len(title2)==1:
             title = title + ' - |'
             title = title.split(' - ')
             title[1] = title[0]
             title[0] = ''
        else:
             title = title2
        if len(title)>2:
            for tit in range(2, len(title)):
                title[1] += ' ' + title[tit]
        title[1] = title[1].decode('utf-8').upper().encode('utf-8')
        pt2 = title[1].split(' ')
        fulltitle = title[1].replace(pt2[len(pt2)-1],'')
        zrow['thumb'] = thumb
        zrow['event'] = title[0]
        zrow['match'] = str(title[1].replace(pt2[len(pt2)-1],'')).replace(' V. ',' vs ')
        zrow['date'] = pt2[len(pt2)-1]
        li = zrow['date'].split('/')
        day,month,year = li[0],li[1],li[2]
        zrow['datesort'] = '%s%s%s' %(year,month,day)
        zrow['url'] = url
        zgrid.append(zrow)
    if len(zgrid) > 0:
        zgrid = sorted(zgrid, key=lambda x: x['datesort'], reverse=True)
        date_old = ''
        for i in range(0,len(zgrid)):
            date = convert_date(zgrid[i]['date'])
            if date != date_old:
                date_old = date
                title = '[COLOR yellow]%s[/COLOR]'%date
                itemlist.append( Item( channel=item.channel, title=title, action="nada", url=None, thumbnail=item.thumbnail, folder=False ))
            title = zgrid[i]['event'] + ' ' + zgrid[i]['match'] + ' (' + zgrid[i]['date'] + ')'
            if zgrid[i]['event'] == '':
                title = '     [COLOR gold]%s[/COLOR]' %zgrid[i]['match']
            else:
                title = '     [COLOR deepskyblue]%s:[/COLOR] [COLOR gold]%s[/COLOR]' %(zgrid[i]['event'], zgrid[i]['match'])
            if ' vs ' in title:
                title = title.replace(" vs "," [COLOR orange]vs[/COLOR] ")
            fulltitle = zgrid[i]['match']
            url = zgrid[i]['url']
     
            itemlist.append( Item( channel=item.channel, title=title, fulltitle=fulltitle, action="findvideos", url=url, thumbnail=zgrid[i]['thumb'], folder=True ))
    match = re.search("a\ class='blog-pager-older-link'\ href='(.*?)'",data)
    if match:
        url = match.group(1)
        title = '[COLOR orange]>>> Siguiente página >>>[/COLOR]'
        itemlist.append( Item( channel=item.channel, title=title, date=zrow['date'], action="mainlist", url=url, thumbnail=item.thumbnail, folder=True ))
    return itemlist

def settingCanal(item):
    return platformtools.show_channel_settings()

def findvideos(item):
    itemlist=[]
    data = httptools.downloadpage(item.url).data
    title = item.title.strip()
    itemlist.append( Item( channel=item.channel, title=title, action='nada', url='', thumbnail=item.thumbnail, folder=False ))
    if 'First Half' in data and 'Second Half' in data:
        matches = re.findall('mediumblue;">Channel.*?red;">(.*?)<[\s\S]*?Resolution.*?:\ *(.*?)<[\s\S]*?Bitrate.*?:\ *(.*?)<[\s\S]*?>Format.*?:\ *(.*?)<[\s\S]*?>Size.*?:\ *(.*?)<[\s\S]*?>Language.*?:.*?>(.*?)<[\s\S]*?First\ [Hh]alf[\s\S]*?<a href="(.*?)"[\s\S]*?Second\ [Hh]alf[\s\S]*?<a href="(.*?)"',data)
        for canal,resolucion,bitrate,formato,size,idioma,primera,segunda in matches:
            title = '     %s | %s | %s | %s' %(idioma,resolucion,canal,bitrate)
            itemlist.append( Item( channel=item.channel, title=title, action='nada', url='', thumbnail=item.thumbnail, folder=False ))
            title = '[COLOR tomato]          Primera Parte[/COLOR]'
            itemlist.append( Item( channel=item.channel, title=title, fulltitle=item.fulltitle, action='play', url=primera, thumbnail=item.thumbnail, folder=False ))
            title = '[COLOR tomato]          Segunda Parte[/COLOR]'
            itemlist.append( Item( channel=item.channel , title=title , fulltitle=item.fulltitle, action='play', url=segunda, thumbnail=item.thumbnail, folder=False ))
    elif 'Download' in data:
        matches = re.findall('mediumblue;">Channel.*?red;">(.*?)<[\s\S]*?Resolution.*?:\ *(.*?)<[\s\S]*?Bitrate.*?:\ *(.*?)<[\s\S]*?>Format.*?:\ *(.*?)<[\s\S]*?>Size.*?:\ *(.*?)<[\s\S]*?>Language.*?:.*?>(.*?)<[\s\S]*?Download[\s\S]*?<a href="(.*?)"',data)
        for canal,resolucion,bitrate,formato,size,idioma,download in matches:
            title = '     %s | %s | %s | %s' %(idioma,resolucion,canal,bitrate)
            itemlist.append( Item( channel=item.channel, title=title, action='nada', url='', thumbnail=item.thumbnail, folder=False ))
            title = '[COLOR tomato]          Ver Evento[/COLOR]'
            itemlist.append( Item( channel=item.channel, title=title, fulltitle=item.fulltitle, action='play', url=download, thumbnail=item.thumbnail, folder=False ))
    elif 'Full Match' in data:
        matches = re.findall('mediumblue;">Channel.*?red;">(.*?)<[\s\S]*?Resolution.*?:\ *(.*?)<[\s\S]*?Bitrate.*?:\ *(.*?)<[\s\S]*?>Format.*?:\ *(.*?)<[\s\S]*?>Size.*?:\ *(.*?)<[\s\S]*?>Language.*?:.*?>(.*?)<[\s\S]*?Full\ Match[\s\S]*?<a href="(.*?)"',data)
        for canal,resolucion,bitrate,formato,size,idioma,download in matches:
            title = '     %s | %s | %s | %s' %(idioma,resolucion,canal,bitrate)
            itemlist.append( Item( channel=item.channel , title=title, action='nada', url='', thumbnail=item.thumbnail, folder=False ))
            title = '[COLOR tomato]          Ver Partido[/COLOR]'
            itemlist.append( Item( channel=item.channel, title=title, fulltitle=item.fulltitle, action='play', url=download, thumbnail=item.thumbnail, folder=False ))
    return itemlist

def play(item):
    logger.info("deportesalacarta.channels.lukasgtr play")
    itemlist = servertools.find_video_items(data=item.url)
    for videoitem in itemlist:
        videoitem.title = item.fulltitle
        videoitem.fulltitle = item.fulltitle
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
    return itemlist

def nada(item):
    return None
