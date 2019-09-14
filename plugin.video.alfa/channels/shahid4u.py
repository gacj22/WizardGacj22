# -*- coding: utf-8 -*-
# -*- Channel Shahi4u -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import tmdb
from channels import autoplay
from lib import jsunpack


IDIOMAS = {'default': 'default'}
list_language = IDIOMAS.values()
list_quality = ['1080p', '720p', '360p']
list_servers = ['uptobox', '1fichier', 'openload']

host = 'https://ww.shahid4u.net/'
host_alt = 'https://on.shahid4u.net'
channel = "shahid4u"

headers = {"X-Requested-With": "XMLHttpRequest"}

direct_link = False
thumb_separador = get_thumb("next.png")
thumb_buscar = get_thumb("search.png")

def mainlist(item):
    logger.info()
    itemlist = []
    '''try:
        data = httptools.downloadpage(host_alt).data
        rurl, ryear = scrapertools.find_single_match(data, '<a href="'+host_alt+'/category/(.*?)">.*?(\d{4})</a>')
    except:
        logger.error("Cambio en estructura, pagina inicial")
        pass'''
    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, url=host + "category/افلام-عربي/",
                        text_color="0xFF5AC0E0", text_bold=True, title="Arab Movies",
                        action="listall", thumbnail="https://cdn.countryflags.com/thumbs/egypt/flag-button-square-250.png",
                        plot="افلام عربي", extra="film"))
    
    itemlist.append(Item(channel=item.channel, title="Foreign Movies", text_color="0xFF5AC0E0",
                         text_bold=True,action="listall", url=host + "category/افلام-اجنبي/",
                         thumbnail="https://cdn.countryflags.com/thumbs/united-states-of-america/flag-button-square-250.png",
                         plot="افلام اجنبي", extra="film"))
    
    itemlist.append(Item(channel=item.channel, title="Indian Movies", text_color="0xFF5AC0E0",
                         text_bold=True,action="listall", url=host + "category/افلام-هندي/",
                         thumbnail="https://cdn.countryflags.com/thumbs/india/flag-button-square-250.png",
                         extra="film", plot="افلام هندي"))
    
    itemlist.append(Item(channel=item.channel, title="", folder=False, thumbnail=thumb_separador))
    '''try:
        itemlist.append(Item(channel=item.channel, title="Ramadan Series %s" % ryear, text_color="gold",
                             text_bold=True, action="listall", url=host + "category/%s" % rurl,
                             thumbnail="https://image.shutterstock.com/mosaic_250/0/0/1076175437.jpg",
                             extra="series", plot="مسلسلات رمضان %s" % ryear))
    except:
        pass'''
    itemlist.append(Item(channel=item.channel, text_color="yellow", text_bold=True,
                         title="Arab Series", action="listall", url= host + "category/مسلسلات-عربي/",
                         thumbnail="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSr9N_K93EFF4AqSjSVUbn1xbn83W7w3cyzwdOEeCTTO7MEP-Jk",
                         extra="film", plot="مسلسلات عربي"))
    
    itemlist.append(Item(channel=item.channel, text_color="yellow", text_bold=True,
                         title="Foreign Series", url=host + "category/مسلسلات-اجنبي/", action="listall",
                         thumbnail="https://images.bwwstatic.com/tvnetworklogos/sm114F1999-A8C7-2B48-4F38FD8410D047F0.jpg",
                         extra="film", plot="مسلسلات اجنبي"))
    
    itemlist.append(Item(channel=item.channel, text_color="yellow", text_bold=True,
                         title="Turkish Series", action="listall", url=host + "category/مسلسلات-تركية/",
                         thumbnail="https://www.alandroidnet.com/images/appsimages/app_image_5bcba3d52075d.png",
                         extra="film", plot="مسلسلات تركية"))
    
    itemlist.append(Item(channel=item.channel, text_color="yellow", text_bold=True,
                         title="Indian Series", action="listall", url=host + "category/مسلسلات-هندية/",
                         thumbnail="https://www.favcy.com/data/brand/logo/compressed/1526294822-2-56-india-tv-logo.png",
                         extra="film", plot="مسلسلات هندية"))
    
    itemlist.append(Item(channel=item.channel, text_color="yellow", text_bold=True,
     title="Anime Series", action="listall", url=host + "category/مسلسلات-انمي/",
      thumbnail="http://www.retornoanime.com/wp-content/uploads/2012/06/crunchyroll-logo.jpg",
       extra="film", plot="مسلسلات انمي"))
    
    itemlist.append(Item(channel=item.channel, text_color="yellow", text_bold=True,
                         title="TV Shows", action="listall", url=host + "category/برامج-تلفزيونية/",
                         thumbnail="https://is4-ssl.mzstatic.com/image/thumb/Purple124/v4/c2/eb/72/c2eb72ec-fb43-2b5d-55c8-f30606dbcb02/AppIcon-0-1x_U007emarketing-0-0-85-220-0-7.png/246x0w.jpg",
                         extra="film", plot="برامج تلفزيونية"))
    
    itemlist.append(Item(channel=item.channel, text_bold=True, title="Search...",
                         action="search", url=host + "search?s=", thumbnail=thumb_buscar,
                         extra="search", plot="البحث عن فيلم او مسلسل"))

    
    autoplay.show_option(item.channel, itemlist)

    return itemlist
    
def listall(item):
    logger.info()
    itemlist = []
    titlelist = []

    clist1 = ["فيلم", "مسلسل", "انمي", "مشاهدة", "اون لاين"]
    clist2 = ["مترجم", "مدبلج", "HD"]

    data = httptools.downloadpage(item.url).data
    url_pagination = scrapertools.find_single_match(data, 
                    '<li class="active"><a href=".*?">(\d+)</a></li>')
    
    patron = 'content-box">\s*<a href="([^"]+)".*?'
    patron+= 'data-src="([^"]+)".*?<h3>(.*?)</h3></a>'
    
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        
        url = scrapedurl
        
        title = limpiar_titulo(scrapedtitle, clist1)
        
        season = scrapertools.find_single_match(scrapedtitle, ' S(?:0)(\d+)')

        thumbnail = scrapedthumbnail.replace('http://arblionz.com/', host)
        
        if " HD" in title:
            text_color = "0xFF5AC0E0"
        
        elif "مدبلج" in title:
            text_color = "yellow"
        else:
            text_color= ""
        
        if "مسلسل" in scrapedtitle or "انمي" in scrapedtitle or season:
            action = "episodes"
            
            if not '/episode/' in url and item.busqueda_:
                url += '/episodes'
            
            ep = scrapertools.find_single_match(scrapedtitle, 'الحلقة (\d+)')
            
            if ep:
                try:
                    title = title.split('الحلقة %s' % ep)[0] + 'الحلقة %s' % ep
                except:
                    pass
            
            scrapedinfo = scrapedtitle.split(' الحلقة ')
            title2 = scrapedinfo[0].replace("مسلسل ", "").replace("انمي ", "") 
            
            if "الموسم" in title2:
                title2 = title2.split(" الموسم ")[0]
            
            if title2 in titlelist:
                continue
            
            titlelist.append(title2)
            
            title2 = re.sub('S(?:0)(\d+)', '', title2).strip()
            
            if "اعلان" in scrapedtitle or direct_link == True:
                action = "findvideos"
            
            new_item = Item(channel=item.channel, text_color=text_color,
                             action=action, title=title, contentSerieName=title2,
                             url=url, thumbnail=thumbnail)
        
        else:
            
            y = scrapertools.find_single_match(scrapedtitle, '(\d{4})')
            
            if y < 1900 or y > 2025:
                y = "-"
            
            title2 = limpiar_titulo(title, clist2)
            
            new_item = Item(channel=item.channel, action="findvideos", text_color=text_color,
                             title=title, url=scrapedurl, contentTitle=title2, infoLabels={'year':y},
                             thumbnail=thumbnail, extra="film")
        
        itemlist.append(new_item)
    
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    
    if url_pagination:
        
        a = url_pagination
        n = int(a) + 1
        url_n = item.url+"?page=%s" % n
        
        if "?page=" in item.url:
            url_n = item.url.replace("?page=%s" % a, "?page=%s" % n)
        
        l = scrapertools.find_single_match(data, '<li><a href=.*?page=(\d+)" rel="next"')
        
        title = "<< الصفحة التالية (%s) من (%s)" % (n, l)
       
        itemlist.append(Item(channel=item.channel, action="listall", title=title, url=url_n,
                             thumbnail=thumb_separador, plot="Next page >> %s of %s" % (n, l)))
    return itemlist

def search(item, texto):
    itemlist = []
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    
    if texto != '':
        try:
            item.busqueda_ = True
            return listall(item)
        except:
            itemlist.append(item.clone(url='', title='No match found...', action=''))
            return itemlist

def episodes(item):
    
    logger.info()
    itemlist = []
    infoLabels = item.infoLabels
    add = ""
    
    data = httptools.downloadpage(item.url).data
    if not '/episode/' in item.url:
        patron = 'content-box">\s*<a href="([^"]+)"'
        item.url = scrapertools.find_single_match(data, patron)
        data = httptools.downloadpage(item.url).data

    url_pagination = scrapertools.find_single_match(data, '<li class="active"><a href=".*?">(\d+)</a></li>')
    head = data.split("</head>")[0]
    season = scrapertools.find_single_match(head, ' S(?:0)(\d+)')
    
    title = item.title.split("الحلقة")[0]
    
    bloq = scrapertools.find_single_match(data, '> باقى الحلقات</h2>(.*?)</div>')
    matches = re.compile('<a href="([^"]+)" class=.*?><h3>الحلقة <span>', re.DOTALL).findall(bloq)
    
    if len(matches) > 100: add = "00"
    
    text_color = "blue"
    
    for url in matches:
        #title = url.replace("-", " ").replace("مسلسل ", "").replace("انمي ", "").replace("مشاهدة ", "")
        #title = title.split("episode/")[1]
        if 'كامل' in url:
            continue
        episode = scrapertools.find_single_match(url, 'الحلقة-(\d+)')
        
        if add:
            if len(episode) == 1: episode = add+episode
            elif len(episode) == 2: episode = "0"+episode
        else:
            if len(episode) == 1: episode = "0"+episode
        
        if not season:
            season = 1
        
        if "مدبلج" in url:
            text_color = "yellow"
        
        infoLabels['episode'] = episode
        infoLabels['season'] = season
        
        itemlist.append(Item(channel=item.channel, text_color=text_color, action="findvideos",title="(%sx%s) " % (season, episode) + title, contentSerieName=item.contentSerieName, url=url, thumbnail=item.thumbnail, infoLabels=infoLabels))
    
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True, idioma_busqueda='en')
    
    itemlist.sort(key=lambda x: x.title)
    
    if url_pagination:
        a = url_pagination
        n = int(a) + 1
        url_n = item.url+"?page=%s" % n
        
        if "?page=" in item.url:
            url_n = item.url.replace("?page=%s" % a, "?page=%s" % n)
        
        l = scrapertools.find_single_match(data, '<li><a href=.*?page=(\d+)" rel="next"')
        
        title = "<< الصفحة التالية (%s) من (%s)" % (n, l)
        
        itemlist.append(Item(channel=item.channel, action="listall", title=title, url=url_n,
                             thumbnail=thumb_separador, plot="Next page >> %s of %s" % (n, l)))
    return itemlist

def findvideos(item):
    logger.info()
    
    itemlist = []
    downlist = []
    server = ""
    
    watch = item.url.replace("film/", "watch/").replace("episode/", "watch/").replace("post/", "watch/")
    #down = item.url.replace("film/", "download/").replace("episode/", "download/")
    
    data = httptools.downloadpage(watch).data
    data = re.sub(r"\n|\r|\t|\s{2}", "", data)
    
    #referer=down
    try:
        ajax, fid =scrapertools.find_single_match(data, 'url: "(.*?)=(\d+)"')
    except:
        ajax = ""
        fid = ""
        data2 = ""
    if ajax:
        try:
            data2 = httptools.downloadpage(host+'ajaxCenter?_action=getdownloadlinks&postId=%s' % fid,
                                           headers=headers).data
    
        except:
            data2 = ""
    
    matches = scrapertools.find_multiple_matches(data, 'data-embedd="([^"]+)".*?<(.*?) class="server_.*?">(.*?)</li>')
    
    for source, thumbnail, server in matches:
        #server = server.lower()
        thumbnail = scrapertools.find_single_match(thumbnail, 'img src="([^"]+)"')
        
        if "vidbom" in server.lower():
            continue
        
        if not thumbnail:
            thumbnail = item.thumbnail
        
        if len(source) < 3:
            source = ajax+"=%s&serverid=%s" % (fid, source)
        else:
            server = servertools.get_server_from_url(source)
        
        title = server.capitalize().replace("</span>", "")
        url = source
        
        itemlist.append(Item(channel=item.channel, url=url, title=title, action='play', thumbnail=thumbnail, infoLabels=item.infoLabels))

    data2 = re.sub(r"\n|\r|\t|\s{2}", "", data2)
    
    matches_ = scrapertools.find_multiple_matches(data2, '<h3 class=(.*?)</div>')
    
    for data in matches_:
        quality = scrapertools.find_single_match(data, '> سيرفرات تحميل (.*?)</h3>')
        matches = scrapertools.find_multiple_matches(data, '<td>(\w+)</td>.*?<a href="([^"]+)" target')
        
        for server, source in matches:
            
            server = server.lower()
            server= server.replace("1fichier", "onefichier").replace("uploaded", "uploadedto")
            title = server.capitalize()
            
            if quality:
                title = "[COLOR=blue][%s][/COLOR] " % quality +title
            
            itemlist.append(Item(channel=item.channel, url=source, title=title, action='play', infoLabels=item.infoLabels, server=server))

    matches2 = scrapertools.find_multiple_matches(data2, '<a class="LiQuality" target="_NEW" href="([^"]+)">(.*?)</a')
    
    for url, title in matches2:

        itemlist.append(Item(channel=item.channel, url=url, title=title, action='play', infoLabels=item.infoLabels))
    
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title)
    if not data2:
        itemlist.reverse()
    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra == 'film':
        
        itemlist.append(Item(channel=item.channel, title="Añadir a la Videoteca", text_color="yellow",
                             action="add_pelicula_to_library", url=item.url, thumbnail = item.thumbnail,
                             contentTitle = item.contentTitle
                             ))

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist

def play(item):
    logger.info("play: %s" % item.url)
    itemlist = []
    
    
    if 'shah' in item.url:
        
        data = httptools.downloadpage(item.url, headers=headers).data
        item.url = data
        
        if "vidhd" in item.title.lower():
            
            data = httptools.downloadpage(item.url).data
            
            packed = scrapertools.find_single_match(data, "<script type=[\"']text/javascript[\"']>(eval.*?)</script>")
            unpacked = jsunpack.unpack(packed)

            item.url = scrapertools.find_single_match(unpacked, 'file:"([^"]+)"')
            item.server = "directo"
        
        elif item.title.lower() == "ok":
            item.server="okru"
        else:
            item.server=item.title.lower()
        
        itemlist.append(item.clone())
    
    else:
        if "vidhd" in item.url:
            
            data = httptools.downloadpage(item.url).data
            
            packed = scrapertools.find_single_match(data, "<script type=[\"']text/javascript[\"']>(eval.*?)</script>")
            unpacked = jsunpack.unpack(packed)

            item.url = scrapertools.find_single_match(unpacked, 'file:"([^"]+)"')
            item.server = "directo"
        
        itemlist.append(item.clone())
    
    return itemlist

def limpiar_titulo(title, _list):

    for rep in _list:
        title= title.replace(rep, "").strip()
    
    title = re.sub('\s*(\d{4})$', '', title)
    return title