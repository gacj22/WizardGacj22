# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
# Canal para Allsports-TV
#------------------------------------------------------------
import re, random

from core import logger
from core import config
from core import scrapertools
from core.item import Item
from core import httptools
from core import servertools


__channel__ = "allsportstv"
host = "http://www.allsports-tv.com"


def login():
    logger.info()

    try:
        user = config.get_setting("userallsportstv", "allsportstv")
        password = config.get_setting("passwordallsportstv", "allsportstv")
        if user == "" or password == "":
            return False, "Usuario o contraseña en blanco. Revisa tus credenciales"
        data = httptools.downloadpage(host + "/forum").data
        
        if '_userdata["username"] = "%s' % user in data:
            return True, ""

        post = "username=%s&password=%s&autologin=on&redirect=&query=&login=Conectarse" % (user, password)
        data = httptools.downloadpage(host + "/login", post, headers={'Referer': 'http://www.allsports-tv.com/login'}).data
        if "Has escrito un nombre de usuario incorrecto" in data:
            logger.info("Error en el login")
            return False, "Error en el usuario y/o contraseña. Comprueba tus credenciales"
        else:
            logger.info("Login correcto")
            return True, ""
    except:
        import traceback
        logger.info(traceback.format_exc())
        return False, "Error durante el login. Comprueba tus credenciales"


def mainlist(item):
    logger.info()
    itemlist = []

    log_result, message = login()
    if not log_result:
        itemlist.append(item.clone(title="Para usar este canal es necesario registrarse en www.allsports-tv.com", action="", text_color="darkorange"))
        itemlist.append(item.clone(title=message, action="", text_color="darkorange"))

    data = httptools.downloadpage(host + "/forum").data

    matches = scrapertools.find_multiple_matches(data, '<div class="maintitle floated clearfix"><h2>([^<]+)<')
    for title in matches:
        if title == "Area de Discusion":
            continue
        itemlist.append(item.clone(title=title, action="subforo"))

    itemlist.append(item.clone(title="", action=""))
    itemlist.append(item.clone(title="Buscar...", action="search"))
    itemlist.append(item.clone(title="Configurar Canal...", action="configuracion", text_color="gold", folder=False))

    return itemlist

def configuracion(item):
    from platformcode import platformtools
    platformtools.show_channel_settings()
    import xbmc
    xbmc.executebuiltin("Container.Refresh")


def search(item,texto):
    logger.info()
    itemlist = []
    item.url = host + "/search?search_keywords="+texto
    item.action = "entradas"
    return entradas(item)


def subforo(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(host + "/forum").data

    title_foro = re.sub(r"\[[/]*COLOR(?: \w+\|)]", "", item.title)
    bloque = scrapertools.find_single_match(data, '<h2>%s</h2>(.*?)</table>' % title_foro)
    patron = '<h3 class="hierarchy"><a href="([^"]+)".*?>([^<]+)<.*?src="([^"]+)".*?>([^<]+)<'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for url, title, thumb, desc in matches:
        url = host + url
        itemlist.append(item.clone(title=title, action="entradas", url=url, thumbnail=thumb, plot=desc))

    return itemlist
    
def entradas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data

    bloque = scrapertools.find_single_match(data, '<h2>Temas</h2>(.*?)</table>')
    if not bloque:
        bloque = data
    patron = '<a class="topictitle" href="([^"]+)".*?>(.*?)</a>'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for url, title in matches:
        url = host + url
        title = scrapertools.htmlclean(title)
        itemlist.append(item.clone(title=title, action="findvideos", url=url, text_color="darkorange"))

    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)"><img class="sprite-arrow_subsilver_right"')
    if next_page:
        next_page = host + next_page
        itemlist.append(item.clone(title=">> Página Siguiente", url=next_page))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data

    posts = scrapertools.find_multiple_matches(data, '<div class="post-entry">(.*?)(?:class="signature_div"|class="post-footer)')
    for p in posts:
        if "Streamrip:" in p or "Idioma:" in p or "Ripper & Uploader:" in p:
            rip = scrapertools.find_single_match(p, 'StreamRip:(.*?)<br')
            lang = scrapertools.find_single_match(p, 'Idioma:(.*?)<br')
            duracion = scrapertools.find_single_match(p, 'Duración:(.*?)<br')
            thumbnails = scrapertools.find_multiple_matches(p, '<img src="([^"]+)"')

            title = "%s [%s] %s" % (rip, lang, duracion)
            title = re.sub(r"</font>\s*", "", title)
            if "Contraseña:" in p:
                password = scrapertools.find_single_match(p, 'Contraseña:.*?>(.*?)<')
                title += "  [COLOR red](Pass:%s)[/COLOR]" % password
            enlaces = servertools.findvideos(p)
            for e in enlaces:
                title_post = "%s - %s" % (e[2], title)
                url = e[1]
                server = e[2]
                thumb = ""
                if thumbnails:
                    thumb = thumbnails[random.randint(0, len(thumbnails)-1)]
                itemlist.append(item.clone(action="play", title=title_post, url=url, server=server, thumbnail=thumb, text_color="darkorange"))

    return itemlist
