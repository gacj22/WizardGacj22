# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para livetv
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os

from core import scrapertools
from core import logger
from core import config
import xbmc
from core.item import Item
from core import servertools
from core.scrapertools import decodeHtmlentities as dhe
import time
import datetime
from core import httptools

__channel__ = "lfootballws"

song = os.path.join(config.get_runtime_path(), 'music', 'queen-we-will-rock-you.mp3')
host ="http://lfootball.ws/"

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
    logger.info("deportesalacarta.lfootballws lista")
    itemlist = []
    check=xbmc.getInfoLabel('ListItem.Title')
    
    if item.channel != __channel__:
        item.channel = __channel__
    else:
        xbmc.executebuiltin('Notification([COLOR crimson][B]BIENVENIDOS A...[/B][/COLOR], [COLOR yellow][B]'+'livefootballws'.upper()+'[/B][/COLOR],4000,"http://4.bp.blogspot.com/-Jtkwjc049c0/T7CKiNujy-I/AAAAAAAARPc/llNdvg_8TWk/s1600/football_128x128.png")')
        xbmc.executebuiltin("Container.Update")
    
        if not xbmc.Player().isPlaying():
            xbmc.executebuiltin('xbmc.PlayMedia('+song+')')

        """
        Lo que ocurre con
        url = http://translate.googleusercontent.com/translate_c?depth=1&nv=1&rurl=translate.google.com&sl=ru&tl=es&u=http://lfootball.ws/&usg=ALkJrhgzJfI1TDn3BxGgPbjgAHHS7J0i9g
        Redirecciones:
        1. http://translate.google.com/translate?depth=1&nv=1&rurl=translate.google.com&sl=ru&tl=es&u=http://lfootball.ws/
        2. http://translate.googleusercontent.com/translate_p?nv=1&rurl=translate.google.com&sl=ru&tl=es&u=http://lfootball.ws/&depth=2&usg=ALkJrhgAAAAAVupk4tLINTbmU7JrcQdl0G4V3LtnRM1n
        3. http://translate.googleusercontent.com/translate_c?depth=2&nv=1&rurl=translate.google.com&sl=ru&tl=es&u=http://lfootball.ws/&usg=ALkJrhhhRDwHSDRDN4t27cX5CYZLFFQtmA
        Lo que significa que necesitamos una key nueva cada vez en el argumento "usg" y para llegar a la url 3 debemos hacer la petición 1 y 2 con 'follow_redirects=False' o con la convinación de 'follow_redirects=False' y 'header_to_get="location"'
        """
    
    #### Opción 1: 'follow_redirects=False'
    ## Petición 1
    url = "http://translate.google.com/translate?depth=1&nv=1&rurl=translate.google.com&sl=ru&tl=es&u=http://lfootball.ws/"
    data = dhe(httptools.downloadpage(url, follow_redirects=False).data)#.decode('cp1251').encode('utf8')
    ## Petición 2
    url = scrapertools.get_match(data, ' src="([^"]+)" name=c ')
    data = dhe(httptools.downloadpage(url, follow_redirects=False).data)#.decode('cp1251').encode('utf8')
    ## Petición 3
    url = scrapertools.get_match(data, 'URL=([^"]+)"')
    data = dhe(httptools.downloadpage(url).data)#.decode('cp1251').encode('utf8')
    
    """
        #### Opción 2: 'follow_redirects=False' y 'header_to_get="location"'
        ## Petición 1
        url = "http://translate.google.com/translate?depth=1&nv=1&rurl=translate.google.com&sl=ru&tl=es&u=http://lfootball.ws/"
        data = dhe( scrapertools.downloadpage(url,follow_redirects=False) )#.decode('cp1251').encode('utf8')
        ## Petición 2
        url = scrapertools.get_match(data, ' src="([^"]+)" name=c ')
        url = scrapertools.get_header_from_response(url, header_to_get="location")
        ## Petición 3
        data = dhe( scrapertools.cachePage(url ) )#.decode('cp1251').encode('utf8')
        """

    patronmain ='transmisión en vivo(.*?)traducción en línea'
    matchesmain = re.compile(patronmain,re.DOTALL).findall(data)
    for main in matchesmain:
        print "liveeee"
        print main
        patron = '<img class=img src=(.*?) alt.*?<img class=img src=(.*?) alt.*?<a class=link href=.*?&u=.*?href.*?&u=(.*?)&usg.*?title="(.*?)".*?<span class="nameCon clear">(.*?)</li>'
        matches = re.compile(patron,re.DOTALL).findall(main)
        for thumbnail, fanart,url,title,partido in matches:
            evento = re.compile('<span class="name fl"><span>(.*?)</span>').findall(partido)
            evento = " vs ".join(evento)
            title = "[COLOR chocolate][B]"+title +"[/B][/COLOR]" +" "+ "[COLOR crimson][B]EN VIVO!![/B][/COLOR]"
            print "lolo"
            print title
            print url
            fecha = datetime.datetime.today()
            fecha = fecha.strftime("%d/%m")
            time = "live"
            live="true"
            itemlist.append( Item(channel=__channel__, title=title,action="enlaces",url=url,thumbnail =urlparse.urljoin(host,thumbnail),fanart =urlparse.urljoin(host,fanart),fulltitle = title,date=fecha, time=time, evento=evento,context="info_partido", deporte="futbol",folder=True) )

    patronmain ='traducción en línea(.*?)traducción'
    matchesmain = re.compile(patronmain,re.DOTALL).findall(data)
    if len(matchesmain)==0 and live=="false":
        itemlist.append( Item(channel=__channel__, title="[COLOR orange][B]No hay encuentros previstos en estos momentos[/B][/COLOR]",thumbnail ="http://s6.postimg.org/619q91s41/comingsoon.png",fanart ="http://s6.postimg.org/7ucmxddap/soccer_field_desktop_20150703154119_5596ad1fde3e.jpg") )
    itemlist2 = []
    for main in matchesmain:
    
        patron = '<img class=img src=([^"]+) alt.*?src=([^"]+) '
        patron +='.*?<a class=link href=.*?&u=.*?href.*?&u=([^"]+)&usg.*?'
        patron +='title="([^<]+)".*?'
        patron +='<span class="nameCon clear">(.*?)</li><li class=fl>'
        
        matches = re.compile(patron,re.DOTALL).findall(main)
        
        if len(matches)==0 and not live:
           itemlist.append( Item(channel=__channel__, title="[COLOR orange][B]No hay encuentros previstos en estos momentos[/B][/COLOR]",thumbnail ="http://s6.postimg.org/619q91s41/comingsoon.png",fanart ="http://s6.postimg.org/7ucmxddap/soccer_field_desktop_20150703154119_5596ad1fde3e.jpg") )
        for thumbnail, fanart, url,title,liga_fecha in matches:
            if re.search(r'(?i)ha terminado|terminado>', liga_fecha):
                continue
            #liga = re.sub(r'<span.*?">|</span>|class=.*?>|<span>.*?<span|<span.*?|>|<a.*?','',liga)
            try:
                liga = scrapertools.get_match(liga_fecha,'<span class=liga><span>([^<]+)')
                liga = re.sub(r'de','',liga)
                fecha = re.sub(r'<span class=liga><span>.*?</span></span>|<span class="name fl"><span>.*?</span></span></span>|<span class=dopCon>.*?<span class=date><span>|<span class=date><span>|</span>|</a>|de|,|','',liga_fecha)
            except:
                liga=""
                fecha = scrapertools.find_single_match(liga_fecha,'<span class=dopCon><span class=date><span>([^<]+)</span>')
                if not fecha:
                    continue
            if "taza" in liga:
                liga="Cup"

            print "perraco"
            if "00:" in fecha:
               fecha = fecha.replace("00:","24:")
               print fecha
            info = "("+liga+")"

            time= re.compile('(\d+):(\d+)',re.DOTALL).findall(fecha)
            for horas, minutos in time:
                
                print "horas"
                print horas
                wrong_time =int(horas)
                value = 1
                correct_time = wrong_time - value
                correct_time = str(correct_time)
                ok_time = correct_time.zfill(2) +":"+ minutos
                fecha = re.sub(r'(\d+):(\d+)|el|de|,|<span class="nameCon clear">','',fecha).strip()
                
                print "joder"
                print fecha
                d_m = re.compile('([^<]+) (\d+)',re.DOTALL).findall(fecha)
                
                print "opcion a"
                print d_m
                if len(d_m)==0 :
                    d_m = re.compile('(\d+) ([^<]+)',re.DOTALL).findall(fecha)
                    print "pasa a opcion b"
                for x, y in d_m:
                    if x.isdigit():
                       xbmc.log( "opcion x=numero")
                       dia = x.strip()
                       mes = y.strip()
                       mes = translate(mes,"es")
                       mes = mes.title()
                       mes = re.sub(r'(?i)un |de |a |las ', '', mes)
                       mes = month_convert(mes)
                       mes = str(mes).zfill(2)
                       dia = str(dia).zfill(2)
                       xbmc.log(dia)
                       #xbmc.log(mes)
                       xbmc.log("pacoooo")
                    else:
                       xbmc.log( "opcion x = letras")
                       xbmc.log(str( d_m ))
                       mes = x.strip()
                       mes = translate(mes,"es")
                       mes = mes.title()
                       mes = re.sub(r'(?i)un |de |a |las ', '', mes)
                       mes = month_convert(mes)
                       mes = str(mes).zfill(2)
                       dia = y.strip()
                       dia = str(dia).zfill(2)
                       xbmc.log(dia)
                       xbmc.log(mes)
                       xbmc.log("pepeee")
                    dia_mes = (dia+"/"+mes)
                    date = dia_mes
                    time = ok_time
                    evento = re.compile('<span class="name fl"><span>(.*?)</span>').findall(liga_fecha)
                    evento = " vs ".join(evento)
                    partido = "[COLOR khaki][B]"+dia_mes+"[/B][/COLOR]" +"[COLOR yellow][B]"+" - "+ok_time+"[/B][/COLOR]"+"--"+"[COLOR chocolate][B]"+title +"[/B][/COLOR]"+" "+"[COLOR lightslategray]"+ info +"[/COLOR]"
                    
                    itemlist2.append( Item(channel=__channel__, title=partido,action="enlaces",url=url,thumbnail =urlparse.urljoin(host,thumbnail),fanart =urlparse.urljoin(host,fanart), fulltitle= "[COLOR chocolate][B]"+title +"[/B][/COLOR]",date=date, time=time, evento=evento, deporte="futbol",context="info_partido", folder=True) )
    itemlist2.reverse()
    itemlist.extend(itemlist2)
    
    return itemlist

def enlaces(item):
    logger.info("deportesalacarta.livetv enlaces")
    itemlist = []

    if not xbmc.Player().isPlaying():
       xbmc.executebuiltin('xbmc.PlayMedia('+song+')')
   
    data = dhe(httptools.downloadpage(item.url).data).decode('cp1251').encode('utf8')
    

    patronenlaces =' <table class="live-table">(.*?)<h1 class="sectionName">'
    matchesenlaces = re.compile(patronenlaces,re.DOTALL).findall(data)
    if len(matchesenlaces)==0:
        try:
            check= scrapertools.get_match(data,'<div class="CD_text">Событие завершено</div>')
            title = "Partido finalizado".title()
            itemlist.append( Item(channel=__channel__, title="[COLOR bisque][B]"+title+"[/B][/COLOR]",thumbnail =item.thumbnail, fanart= item.fanart, folder=False) )
        except:
            title = "Los enlaces aparecerán media hora antes del encuentro".title()
            itemlist.append( Item(channel=__channel__, title="[COLOR orange][B]"+title+"[/B][/COLOR]",thumbnail =item.thumbnail, fanart="http://s6.postimg.org/nmba7vde9/wallpaper_football_warsaw_stadium_national_hobbi.jpg", folder=False) )


    for bloque_enlaces in matchesenlaces:
        patron = '<a href=.*?<a href=".*?".*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<a href="(.*?)"'
        matches = re.compile(patron,re.DOTALL).findall(bloque_enlaces)
        
        for velocidad,canal,url in matches:
            print "lobo"
            print url
            if "sop" in url:
                player= "[COLOR deepskyblue][B]Sopcast[/B][/COLOR]"
            else :
                player = "[COLOR palegreen][B]Acestream[/B][/COLOR]"
            title = "[COLOR mediumorchid][B]"+canal+"[/B][/COLOR]" +" "+"("+player+")"+" "+"("+"[COLOR moccasin][B]"+velocidad+"[/B][/COLOR]"+")"
            itemlist.append( Item(channel=__channel__, title=title,action="play",url = url,thumbnail =item.thumbnail, fanart= "http://s6.postimg.org/3sid4gz9t/Snchez_Pizjun_Borussia_opt.jpg", extra ="saliendo",fulltitle = item.fulltitle,folder=False) )

    return itemlist

def play(item):
    logger.info("deportesalacarta.lfootballws play")
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

def month_convert(mes):
    return{ 'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril':4, 'Mayo' : 5, 'Junio' : 6, 'Julio' : 7, 'Agosto' : 8, 'Septiembre' : 9, 'Octubre' : 10, 'Noviembre' : 11, 'Diciembre' : 12 }[mes]
