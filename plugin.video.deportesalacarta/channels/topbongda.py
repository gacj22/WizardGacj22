# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para topbongda
#------------------------------------------------------------

import urllib2, re
import os

from core import scrapertools
from core import logger
from core import config
from core import jsontools
from core.item import Item
from core import servertools
import xbmc
from core.scrapertools import decodeHtmlentities as dhe
import datetime
from core import httptools
                
__channel__ = "topbongda"
song = os.path.join(config.get_runtime_path(), "music", 'Easy.mp3')




def agendaglobal(item):
    itemlist = []
    try:
        itemlist = mainlist(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

def mainlist(item):
    logger.info("deportesalacarta.topbongda mainlist")
    itemlist = []
    
    if item.extra != "next_page":
        item.url = "http://topbongda.com/?t=sap-dien-ra"#/wendy/ajax/home_matches/?page=1"
        if item.channel == __channel__:
            if not xbmc.Player().isPlaying():
                xbmc.executebuiltin('xbmc.PlayMedia('+song+')')
        else:
            item.channel = __channel__
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|&amp;","",data)
    
    #data = jsontools.load_json(data)

    patrondaygames = scrapertools.find_multiple_matches(data,'<div class="match-block mdl-shadow--2dp">.*?date_range</i>(.*?)<small>(.*?)</div></li></ul></div>')
    
    for fecha_partidos, bloque_partidos in patrondaygames:
        #LIVE
        patronlive ='<span class="time">(.*?)</span><span class="minute">(.*?)<i class="playing">.*?<strong>(.*?)</strong>.*?class="score">(.*?)</a>.*?</a><strong>(.*?)</strong>.*?<a href="([^"]+)".*?class="mdl-tooltip">(.*?)</div>'
        matcheslive=re.compile(patronlive,re.DOTALL).findall(bloque_partidos)
        for hora,minuto,team1,score,team2,url,league in matcheslive:
            # Eliminamos la coincidencia en bloque_partidos para evitar errores en el patron NO LIVE
            bloque_partidos = re.sub('<span class="time">'+hora, '', bloque_partidos)
            minuto=dhe(minuto.strip())
            minute = dhe(minuto.strip())
            if "HT" in minuto:
                minuto = "Descanso"
                minute = "60"
            elif "FT" in minuto:
                minuto = "Finalizado"
                minute = "90"
            elif "started" in minuto:
                minuto = "Por comenzar"
                minute = "0"
            minute = filter(lambda x: x.isdigit(), minute)

            # Calcula hora y fecha de comienzo del evento para la agenda global
            h, m = scrapertools.get_match(hora,'(\d+):(\d+)')
            tiempo = datetime.datetime(2000, 1, 1, int(h), int(m)) - datetime.timedelta(hours=4)
            tiempo = tiempo.time().strftime("%H:%M")

            fecha_actual = datetime.datetime.today() + datetime.timedelta(hours=5)
            fecha = fecha_actual - datetime.timedelta(hours=5, minutes=int(minute))
            fecha = fecha.strftime("%d/%m")
            
            if "HT" in minuto:
                minuto = "Descanso"
            if "FT" in minuto:
                minuto = "Finalizado"
            title =  "[COLOR chartreuse][B]"+team1+"[/B][/COLOR]"+"[COLOR yellowgreen]__[/COLOR]"+"[COLOR yellow][B]"+score+"[/B][/COLOR]"+"[COLOR yellowgreen]__[/COLOR]"+"[COLOR chartreuse][B]"+team2+"[/B][/COLOR]"
            title = "[COLOR olivedrab]([/COLOR]"+"[COLOR yellowgreen][B]"+minuto+"[B][/COLOR]"+"[COLOR olivedrab])[/COLOR]"+" "+title+" [COLOR crimson][B]LIVE!![/B][/COLOR] [COLOR yellowgreen]("+league+")[/COLOR]"
            url = re.sub(r"https/","http://",url)+"sopcast"
            url = re.sub(r"/ti-le","",url)
            evento = team1 + " vs " + team2
            
            itemlist.append( Item(channel=__channel__, title=title,action="enlaces",url = url,thumbnail="http://imgur.com/CS2Iy56.png",fanart="http://s6.postimg.org/bwlfc3fdd/topbongdafan.jpg", fulltitle= "[COLOR chartreuse][B]"+team1+" Vs "+team2+"[/B][/COLOR]",extra="LIVE",
                                  date=fecha, time=tiempo, evento=evento, deporte="futbol", folder=True, context="info_partido") )
        #NO LIVE
        patronnolive ='<div class="info"><span class="time">(\d+:\d+)</span><a href=".*?class="league">(.*?)</a>.*?<strong>(.*?)</strong>.*?<strong>(.*?)</strong>.*?<a href="([^"]+)"'
        matchesnolive=re.compile(patronnolive,re.DOTALL).findall(bloque_partidos)
        logger.info("maruhenda")
        logger.info (str(patrondaygames))
        for hora,league,team1,team2,url in matchesnolive:

            format_date = "%d/%m"
            format_time = "%H:%M"
            # Extraemos hora, minutos, dia, mes y año
            h, m = scrapertools.get_match(hora,'(\d+):(\d+)')
            fecha_actual = datetime.datetime.today() + datetime.timedelta(hours=6)
            if "Hôm Nay" in fecha_partidos:
                fecha_partidos = fecha_actual.strftime("%d/%m/%Y")
            elif "Ngày Mai" in fecha_partidos:
                fecha_partidos = fecha_actual + datetime.timedelta(days=1)
                fecha_partidos = fecha_partidos.strftime("%d/%m/%Y")

            day, month, year = scrapertools.get_match(fecha_partidos,'(\d+)/(\d+)/(\d+)')
            # Creamos el objeto con la fecha extraída
            date_change = datetime.datetime(int(year), int(month), int(day), int(h), int(m))
            # Le restamos 5 horas
            date_change = date_change - datetime.timedelta(hours=5)
            fecha = date_change.strftime("%d/%m/%Y")
            date = date_change.strftime(format_date)
            ok_time = date_change.strftime(format_time)

            if "Ngoại Hạng Anh" in league:
                league = "Premier League"
            if "Hạng Nhất Anh" in league:
                league = "Premier League"

            extra =ok_time+"|"+fecha
            evento = team1+" vs "+team2

            # Calculamos la diferencia horaria entre el evento y la hora actual para buscar enlaces
            # solo cuando falte menos de media hora para empezar el partido
            diferencia_hora = (date_change - datetime.datetime.today())
            if diferencia_hora.days == 0:
                hours, remainder = divmod(diferencia_hora.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                if hours == 0 and minutes <= 30:
                    url = re.sub(r"https/","http://",url)+"sopcast"
                    url = re.sub(r"/ti-le","",url)
            title = team1+" Vs "+team2
            title ="[COLOR chartreuse]"+ok_time+"[/COLOR]" +"[COLOR olivedrab]--[/COLOR]"+"[COLOR gold]"+date+"[/COLOR]"+" "+"[COLOR seagreen][B]"+title+"[/B][/COLOR]" + " "+"[COLOR olivedrab]([/COLOR]"+"[COLOR yellowgreen]"+league+"[/COLOR]"+"[COLOR olivedrab])[/COLOR]"
            title = dhe(title)
            
            itemlist.append( Item(channel=__channel__, title=title,action="enlaces",url = url ,thumbnail="http://www.apkrepo.com/wp-content/uploads/2016/03/com.adnkm_.soccerclockwidget.icon_.png",fanart="http://s6.postimg.org/bwlfc3fdd/topbongdafan.jpg", fulltitle= "[COLOR seagreen][B]"+team1+" Vs "+team2+"[/B][/COLOR]",extra=extra,
                                  date=date, time=ok_time, evento=evento, deporte="futbol", context="info_partido", folder=True) )
    
    return itemlist




def enlaces(item):
    logger.info("deportesalacarta.topbongda scraper")
    
    itemlist = []
    logger.info("esoquees")
    logger.info(item.url)
    item.url= "http://topbongda.com"+item.url
    # Descarga la página
    
    if "sopcast" in item.url:
        data = httptools.downloadpage(item.url).data
        try:
           eid = scrapertools.get_match(data,'http.get.*?eid=(.*?)"')
        
           url ="http://topbongda.com/xem-bong-da-truc-tuyen/api/link/?eid="+ eid
           
           data = httptools.downloadpage(url).data
           data = jsontools.load_json(data)
           sop = data['sop']
          
           if sop:
              tipo = "[COLOR aquamarine][B]Sopcast[/B][/COLOR]"
              thumbnail= "http://s6.postimg.org/v9z5ggmfl/sopcast.jpg"
            
              itemlist.append( Item(channel=__channel__,title=tipo.strip(), url="",action="mainlist",thumbnail=thumbnail, fanart= "http://s6.postimg.org/6756rs973/topbongda.jpg",folder=False) )
              for sop in data["sop"]:
                  no_sop = "false"
                  url = sop['url']
                  bibrate = sop['bitrate']
                  languaje =sop['language']
                  if languaje == '':
                      languaje ="Desconocido"
            
                  title = languaje.strip()
                  title = "[COLOR darkolivegreen][B]"+title+"[/B][/COLOR]"
                  if str(bibrate) != "0":
                     title = title +"  "+ "[COLOR palegreen]"+"("+str(bibrate)+" Kbps"+")"+"[/COLOR]"
                  itemlist.append( Item(channel=__channel__, title="        "+title,action="play",url =url,thumbnail= thumbnail,fanart="http://s6.postimg.org/6756rs973/topbongda.jpg",fulltitle = item.fulltitle, folder=True))
           else :
                 no_sop = "true"
           ace = data['ace']
           if ace:
               no_ace= "false"
               tipo = "[COLOR yellow][B]Acestream[/B][/COLOR]"
               thumbnail= "http://s6.postimg.org/c2c0jv441/torrent_stream_logo_300x262.png"
               itemlist.append( Item(channel=__channel__,title=tipo.strip(), url="",action="mainlist",thumbnail=thumbnail, fanart= "http://s6.postimg.org/6756rs973/topbongda.jpg",folder=False) )
               
               for ace in data["ace"]:
            
                   url = ace['url']
                   bibrate = ace['bitrate']
                   languaje =ace['language']
                   if languaje == '':
                      languaje ="Desconocido"
                   title = languaje.strip()
                   title = "[COLOR darkolivegreen][B]"+title+"[/B][/COLOR]"
            
            
                   if str(bibrate) != "0":
                      title = title +"  "+ "[COLOR palegreen]"+"("+str(bibrate)+" Kbps"+")"+"[/COLOR]"
                
                   itemlist.append( Item(channel=__channel__, title="        "+title,action="play",url =url,thumbnail= thumbnail,fanart="http://s6.postimg.org/6756rs973/topbongda.jpg",fulltitle = item.fulltitle, folder=True) )
           else :
                no_ace = "true"

           if no_sop == "true" and no_ace =="true":
              title ="No hay ningun enlace Sopcast / Acestream".title()
              itemlist.append( Item(channel=__channel__,title="[COLOR limegreen][B]"+title+"[/B][/COLOR]", url="",action="mainlist",fanart="http://s6.postimg.org/unwjdqopd/topbongdafannolink.jpg",thumbnail="http://s6.postimg.org/m6x12tk0h/topbongdathumbnolink.png", folder=False) )
              
        except:
            xbmc.executebuiltin('Action(Back)')
            xbmc.sleep(100)
            xbmc.executebuiltin('Notification([COLOR palegreen][B]Partido[/B][/COLOR], [COLOR yellow][B]'+'sin enlaces'.upper()+'[/B][/COLOR],4000,"http://s6.postimg.org/ke8bfk7f5/topbongda.png")')
        
        
    else:
        
        check_hour = scrapertools.get_match(item.extra.split("|")[0],'(\d)\d:\d+')

        from time import gmtime, strftime
        import time
        get_date=strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        
        ok_date_hour =re.compile('(\d+)-(\d+)-(\d+) (\d+:\d+:\d+)',re.DOTALL).findall(get_date)
        for year,mes,day,hour in ok_date_hour:
            current_day =day+"/"+mes+"/"+year
            current_hour = hour
        
        today =scrapertools.get_match(current_day,'(\d+)/\d+/\d+')
        dia_match = scrapertools.get_match(item.extra.split("|")[1],'(\d+)/\d+/\d+')
        check_day =int(dia_match) - int(today)
        
        check_match_hour = scrapertools.get_match(item.extra.split("|")[0],'(\d+):\d+')
        
        check_today_hour = scrapertools.get_match(current_hour,'(\d+):\d+')
        
        if item.extra.split("|")[1] == current_day or item.extra.split("|")[1] != current_day and check_day <= 2   :
            
            time= re.compile('(\d+):(\d+):(\d+)',re.DOTALL).findall(get_date)
            for h,m,s in time:
                hora=h
                min = m
                            
            time_match = re.compile('(\d+):(\d+)',re.DOTALL).findall(item.extra.split("|")[0])
            
            for h,m in time_match:
                check_time_match = scrapertools.get_match(h,'(\d)\d')
                if "0" in str(check_hour) and str(check_match_hour) <= str(check_today_hour)   or  str(check_match_hour) < str(check_today_hour) :
                    #check_day == 1 and
                    h = 24 + int(h)
                    
                hora_match = h
                min_match = m
                remaining = int(hora_match) - int(hora)
                
                if min != "00":
                    correct_min = (60 - int(min))*60
                    remaining = (int(remaining) -1)*3600
                    remaining = remaining + correct_min+(int(min_match)*60)
                else :
                    remaining = (remaining*3600)+ int(min_match)
                        
                        
                num=int(remaining)
                #dia =(int(num/84600))
                hor=(int(num/3600))
                minu=int((num-(hor*3600))/60)
                #seg=num-((hor*3600)+(minu*60))
                
                remaining= (str(hor)+"h "+str(minu)+"m ")
                if check_day == 0 and check_match_hour == check_today_hour :
                    remaining =  str(minu)+"m "
                if check_day == 1 and check_match_hour >= check_today_hour or check_day == 2  and check_match_hour <= check_today_hour:
                    
                    if check_match_hour == check_today_hour :
                        
                       remaining = "23h" +" "+ str(minu)+"m "
                    else:
                        if "0h" in remaining:
                           remaining = re.sub(r"0h","",remaining)
                        remaining = "1d" +" "+ remaining
            
                elif check_day == 2:
                    
                    remaining = "2d" + " "+remaining
                else:
                    remaining = remaining
                
        else:
            
            
            if check_day >=3 and str(check_match_hour) >= str(check_today_hour):
               remaining = str(day)+" dias"
            
            else:
               time= re.compile('(\d+):(\d+):(\d+)',re.DOTALL).findall(get_date)
               for h,m,s in time:
                   hora=h
                   min = m
               time_match = re.compile('(\d+):(\d+)',re.DOTALL).findall(item.extra.split("|")[0])
               for h,m in time_match:
                   check_time_match = scrapertools.get_match(h,'(\d)\d')
                   
                   h = 24 + int(h)
                   hora_match = h
                   min_match = m
                   remaining = int(hora_match) - int(hora)
                   if min != "00":
                      correct_min = (60 - int(min))*60
                      remaining = (int(remaining) -1)*3600
                      remaining = remaining + correct_min+(int(min_match)*60)
                   else :
                      remaining = (remaining*3600)+ int(min_match)*60
               
                   num=int(remaining)
                   dia =(int(num/84600))
                   hor=(int(num/3600))
                   minu=int((num-(hor*3600))/60)
                   remaining= "2d"+(str(hor)+"h "+str(minu)+"m ")

        no_link="Aun no hay enlaces"
        no_link = no_link.title()
        itemlist.append( Item(channel=__channel__,title="               "+"[COLOR springgreen]"+no_link+"[/COLOR]", url="",action="mainlist",fanart="http://s6.postimg.org/mktb5axsh/topbongdafantime.jpg",thumbnail="http://s6.postimg.org/ippx2qemp/topbongdathumbtime.png", folder=False) )
        itemlist.append( Item(channel=__channel__,title="                                            "+"[COLOR lawngreen]Disponibles en[/COLOR]"+"  "+"[COLOR palegreen][B]"+str(remaining)+"[/B][/COLOR]", url="",action="mainlist",fanart="http://s6.postimg.org/mktb5axsh/topbongdafantime.jpg",thumbnail="http://s6.postimg.org/ippx2qemp/topbongdathumbtime.png", folder=False) )
    return itemlist



def play(item):
    logger.info("deportesalacarta.topbongda play")
    itemlist = []

    xbmc.executebuiltin('xbmc.PlayMedia(Stop)')
    fulltitle = item.fulltitle
    
    # Se incluye el título en la url para pasarlo al conector
    url= item.url + "|" + fulltitle
    
    itemlist.append(Item(channel=__channel__, title=item.title, server="p2p", url=url, action="play", folder=False))
    
    return itemlist

def translate(to_translate, to_langage="auto", langage="auto"):
    ###Traducción atraves de Google
    '''Return the translation using google translate
        you must shortcut the langage you define (French = fr, English = en, Spanish = es, etc...)
        if you don't define anything it will detect it or use english by default
        Example:
        print(translate("salut tu vas bien?", "en"))
        hello you alright?'''
    agents = {'User-Agent':"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)"}
    before_trans = 'class="t0">'
    link = "http://translate.google.com/m?hl=%s&sl=%s&q=%s" % (to_langage, langage, to_translate.replace(" ", "+"))
    request = urllib2.Request(link, headers=agents)
    page = urllib2.urlopen(request).read()
    result = page[page.find(before_trans)+len(before_trans):]
    result = result.split("<")[0]
    return result

if __name__ == '__main__':
    to_translate = 'Hola como estas?'
    print("%s >> %s" % (to_translate, translate(to_translate)))
    print("%s >> %s" % (to_translate, translate(to_translate, 'fr')))
#should print Hola como estas >> Hello how are you
#and Hola como estas? >> Bonjour comment allez-vous?
