# -*- coding: utf-8 -*-

import os
import re
import sys
import urlparse
from time import sleep

from core import channeltools
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from platformcode import platformtools

host = 'https://www.megadede.com'
__channel__ = 'megadede'
parameters = channeltools.get_channel_parameters(__channel__)
fanart_host = parameters['fanart']
thumbnail_host = parameters['thumbnail']
color1, color2, color3 = ['0xFFB10021', '0xFFB10021', '0xFFB10004']


def login():
    url_origen = host+"/login?popup=1"
    try:
        data = httptools.downloadpage(url_origen).data
    except:
        data = httptools.downloadpage(url_origen, follow_redirects=False).data
    if '<span class="username">' in data:
         return True
    token = scrapertools.find_single_match(data, '<input name="_token" type="hidden" value="([^"]+)"')
    if 'Escribe los números de la imagen' in data:
        captcha_url = scrapertools.find_single_match(data, '<img src="([^"]+)" alt="captcha">')
        imagen_data = httptools.downloadpage(captcha_url).data
        ficheropng = os.path.join(config.get_data_path(), "captcha_megadede.png")
        outfile=open(ficheropng,'wb')
        outfile.write(imagen_data)
        outfile.close()
        img = xbmcgui.ControlImage(450,15,400,130,ficheropng)
        wdlg = xbmcgui.WindowDialog()
        wdlg.addControl(img)
        wdlg.show()
        sleep(1)
        kb = platformtools.dialog_numeric(0, "Escribe los números de la imagen")

        postcaptcha = ""
        if kb !='':
                solution = kb
                postcaptcha = "&captcha=" + str(solution)
        else:
             return False
        wdlg.close()
    else:
        postcaptcha=""
    post = "_token=" + str(token) + "&email=" + str(config.get_setting("megadedeuser", "megadede")) + \
           "&password=" + str(config.get_setting("megadedepassword", "megadede")) + postcaptcha\
           #+ "&app=2131296469"
    headers = {"User-Agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/66.0.3163.100 Safari/537.36", "Referer": host, "X-Requested-With": "XMLHttpRequest","X-CSRF-TOKEN":
        token}
    data = httptools.downloadpage(host+"/login", post=post, headers=headers).data
    if "redirect" in data:
        return True
    else:
        return False


def mainlist(item):
    logger.info()
    itemlist = []
    if not config.get_setting("megadedeuser", "megadede"):
        itemlist.append(
            Item(channel=item.channel, title="Habilita tu cuenta en la configuración e ingresar de nuevo al canal", action="settingCanal",
                 url=""))
    else:
        result = login()
        if not result:
            itemlist.append(Item(channel=item.channel, action="mainlist", title="Login fallido. Volver a intentar..."))
            return itemlist
        item.url = host
        item.fanart = fanart_host
        item.thumbnail = "https://s18.postimg.cc/r5cylu6rd/12_-_oi_RDsdv.png"
        itemlist.append(item.clone(title="Películas", action="menupeliculas", text_color=color3, text_blod=True))

        item.thumbnail = "https://s18.postimg.cc/ruvqy6zl5/15_-_9m9_Dp1m.png"
        itemlist.append(item.clone(title="Series", action="menuseries", text_color=color3, text_blod=True))

        itemlist.append(item.clone(title="Listas", action="menulistas", text_color=color3, text_blod=True, thumbnail = 'https://s18.postimg.cc/xj21p46ih/10_-_Uf7e_XHE.png'))

        itemlist.append(item.clone(title="", folder=False, thumbnail=thumbnail_host))
        item.thumbnail = ""
        itemlist.append(item.clone(channel=item.channel, action="settingCanal", title="Configuración...", url="", thumbnail='https://s18.postimg.cc/c9efeassp/3_-_QAHK2_Tc.png'))
    return itemlist


def settingCanal(item):
    return platformtools.show_channel_settings()


def menuseries(item):
    logger.info()
    itemlist = []
    item.url = host
    item.fanart = fanart_host
    item.text_color = None
    item.thumbnail = "https://s18.postimg.cc/ruvqy6zl5/15_-_9m9_Dp1m.png"
    itemlist.append(item.clone(action="peliculas", title="    Novedades", url= host + "/series", thumbnail='https://s18.postimg.cc/in3ihji95/11_-_WPg_H5_Kx.png'))
    itemlist.append(item.clone(action="generos", title="    Por géneros", url= host + "/series", thumbnail='https://s18.postimg.cc/p0slktaah/5_-_c_Nf_KRvm.png'))
    itemlist.append(
        item.clone(action="peliculas", title="    Siguiendo", url= host + "/series/following", thumbnail='https://s18.postimg.cc/68gqh7j15/7_-_tqw_AHa5.png'))
    itemlist.append(item.clone(action="peliculas", title="    Capítulos Pendientes",
                               url= host + "/series/mypending/0?popup=1", viewmode="movie", thumbnail='https://s18.postimg.cc/9s2o71w1l/2_-_3dbbx7_K.png'))
    itemlist.append(
        item.clone(action="peliculas", title="    Favoritas", url= host + "/series/favorites", thumbnail='https://s18.postimg.cc/n8zmpwynd/4_-_JGrig_Ep.png'))
    itemlist.append(
        item.clone(action="peliculas", title="    Pendientes", url= host + "/series/pending", thumbnail='https://s18.postimg.cc/4gnrmacix/13_-_cwl_TDog.png'))
    itemlist.append(item.clone(action="peliculas", title="    Terminadas", url= host + "/series/seen", thumbnail='https://s18.postimg.cc/5vpcay0qh/17_-_M2in_Fp_O.png'))
    itemlist.append(
        item.clone(action="peliculas", title="    Recomendadas", url= host + "/series/recommended", thumbnail='https://s18.postimg.cc/bwn182sih/14_-_fin32_Kp.png'))
    itemlist.append(item.clone(action="search", title="    Buscar...", url= host + "/series", thumbnaiil='https://s18.postimg.cc/s7n54ghvt/1_-_01_ZDYii.png'))
    itemlist.append(item.clone(title="", folder=False, thumbnail=thumbnail_host))
    itemlist.append(Item(channel=item.channel, action="settingCanal", title="Configuración...", url="", thumbnail='https://s18.postimg.cc/c9efeassp/3_-_QAHK2_Tc.png'))
    return itemlist


def menupeliculas(item):
    logger.info()
    itemlist = []
    item.url = host
    item.fanart = fanart_host
    item.text_color = None
    item.thumbnail = "https://s18.postimg.cc/r5cylu6rd/12_-_oi_RDsdv.png"
    itemlist.append(item.clone(action="peliculas", title="    Novedades", url= host + "/pelis", thumbnail='https://s18.postimg.cc/in3ihji95/11_-_WPg_H5_Kx.png'))
    itemlist.append(item.clone(action="generos", title="    Por géneros", url= host + "/pelis", thumbnail='https://s18.postimg.cc/p0slktaah/5_-_c_Nf_KRvm.png'))
    itemlist.append(item.clone(action="peliculas", title="    Solo HD", url= host + "/pelis?quality=3", thumbnail='https://s18.postimg.cc/e17e95mfd/16_-_qmqn4_Si.png'))
    itemlist.append(
        item.clone(action="peliculas", title="    Pendientes", url= host + "/pelis/pending", thumbnail='https://s18.postimg.cc/4gnrmacix/13_-_cwl_TDog.png'))
    itemlist.append(
        item.clone(action="peliculas", title="    Recomendadas", url= host + "/pelis/recommended", thumbnail='https://s18.postimg.cc/bwn182sih/14_-_fin32_Kp.png'))
    itemlist.append(
        item.clone(action="peliculas", title="    Favoritas", url= host + "/pelis/favorites", thumbnail='https://s18.postimg.cc/n8zmpwynd/4_-_JGrig_Ep.png'))
    itemlist.append(item.clone(action="peliculas", title="    Vistas", url= host + "/pelis/seen", thumbnail='https://s18.postimg.cc/5vpcay0qh/17_-_M2in_Fp_O.png'))
    itemlist.append(item.clone(action="search", title="    Buscar...", url= host + "/pelis", thumbnail='https://s18.postimg.cc/s7n54ghvt/1_-_01_ZDYii.png'))
    itemlist.append(item.clone(title="", folder=False, thumbnail=thumbnail_host))
    item.thumbnail = ""
    itemlist.append(item.clone(channel=item.channel, action="settingCanal", title="Configuración...", url="", thumbnail='https://s18.postimg.cc/c9efeassp/3_-_QAHK2_Tc.png'))
    return itemlist


def menulistas(item):
    logger.info()
    itemlist = []
    item.url = host
    item.fanart = fanart_host
    item.text_color = None
    itemlist.append(
        item.clone(action="listas", tipo="populares", title="    Populares", url= host + "/listas", thumbnail='https://s18.postimg.cc/7aqwzrha1/8_-_3rn14_Tq.png'))
    itemlist.append(
        item.clone(action="listas", tipo="siguiendo", title="    Siguiendo", url= host + "/listas", thumbnail='https://s18.postimg.cc/4tf5sha89/9_-_z_F8c_UBT.png'))
    itemlist.append(
        item.clone(action="listas", tipo="tuslistas", title="    Tus Listas", url= host + "/listas"))
    itemlist.append(item.clone(title="", folder=False, thumbnail=thumbnail_host))
    item.thumbnail = ""
    itemlist.append(item.clone(channel=item.channel, action="settingCanal", title="Configuración...", url="", thumbnail='https://s18.postimg.cc/c9efeassp/3_-_QAHK2_Tc.png'))
    return itemlist


def generos(item):
    logger.info()
    tipo = item.url.replace( host + "/", "")
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data,
                                          '<select name="genre_id" class="selectpicker" title="Selecciona...">(.*?)</select>')
    patron = '<option  value="([^"]+)">([^<]+)</option>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    itemlist = []
    for id_genere, title in matches:
        title = title.strip()
        thumbnail = ""
        plot = ""
        url =  host + "/" + tipo + "?genre_id=" + id_genere
        itemlist.append(
            Item(channel=item.channel, action="peliculas", title=title, url=url, thumbnail=thumbnail, plot=plot,
                 contentTitle=title))
    return itemlist


def search(item, texto):
    logger.info()
    item.tipo = item.url.replace(host + "/", "")
    item.url =  host + "/search/"
    texto = texto.replace(" ", "-")
    item.url = item.url + texto
    try:
        return buscar(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def buscar(item):
    logger.info()
    headers = {"X-Requested-With": "XMLHttpRequest"}
    data = httptools.downloadpage(item.url, headers=headers).data
    json_object = jsontools.load(data)
    data = json_object["content"]
    return parse_mixed_results(item, data)


def parse_mixed_results(item, data):
    itemlist = []
    patron = '<div class="media-dropdown mini dropdown model" data-value="([^"]+)"+'
    patron += '.*?<a href="([^"]+)"[^<]data-toggle="tooltip" data-container="body"+'
    patron += ' data-delay="500" title="([^"]+)"[^<]+'
    patron += '.*?src="([^"]+)"+'
    patron += '.*?<div class="year">([^<]+)</div>+'
    patron += '.*?<div class="value"><i class="fa fa-star"></i> ([^<]+)</div>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    if item.tipo == "lista":
        following = scrapertools.find_single_match(data, '<div class="follow-lista-buttons ([^"]+)">')
        data_id = scrapertools.find_single_match(data, 'data-model="10" data-id="([^"]+)">')
        if following.strip() == "following":
            itemlist.append(
                Item(channel='megadede', title="Dejar de seguir", idtemp=data_id, token=item.token, valor="unfollow",
                     action="megadede_check", url=item.url, tipo=item.tipo))
        else:
            itemlist.append(
                Item(channel='megadede', title="Seguir esta lista", idtemp=data_id, token=item.token, valor="follow",
                     action="megadede_check", url=item.url, tipo=item.tipo))

    for visto, scrapedurl, scrapedtitle, scrapedthumbnail, scrapedyear, scrapedvalue in matches:
        title = ""
        if visto.strip() == "seen":
            title += "[visto] "
        title += scrapertools.htmlclean(scrapedtitle)
        if scrapedyear != '':
            title += " (" + scrapedyear + ")"
        contentTitle = scrapedtitle
        if scrapedvalue != '':
            title += " (" + scrapedvalue + ")"
        thumbnail = urlparse.urljoin(item.url, scrapedthumbnail)
        fanart = thumbnail.replace("mediathumb", "mediabigcover")
        plot = ""
        if "/peli/" in scrapedurl or "/docu/" in scrapedurl:
            # sectionStr = "peli" if "/peli/" in scrapedurl else "docu"
            if "/peli/" in scrapedurl:
                sectionStr = "peli"
            else:
                sectionStr = "docu"
            referer = urlparse.urljoin(item.url, scrapedurl)
            url = urlparse.urljoin(item.url, scrapedurl)
            if item.tipo != "series":
                itemlist.append(Item(channel=item.channel, action="findvideos", title=title, extra=referer, url=url,
                                     thumbnail=thumbnail, plot=plot, contentTitle=contentTitle, fanart=fanart,
                                     contentType="movie", context=["buscar_trailer"]))
        else:
            referer = item.url
            url = urlparse.urljoin(item.url, scrapedurl)
            if item.tipo != "pelis":
                itemlist.append(Item(channel=item.channel, action="episodios", title=title, extra=referer, url=url,
                                     thumbnail=thumbnail, plot=plot, contentTitle=contentTitle, show=title, fanart=fanart,
                                     contentType="tvshow", context=["buscar_trailer"]))
    next_page = scrapertools.find_single_match(data,
                                               '<div class="onclick load-more-icon no-json" data-action="replace" data-url="([^"]+)">')
    if next_page != "":
        url = urlparse.urljoin(host, next_page).replace("amp;", "")
        itemlist.append(
            Item(channel=item.channel, action="pag_sig", token=item.token, title=">> Página siguiente",
                 extra=item.extra, url=url))
    try:
        import xbmcplugin
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    except:
        pass
    return itemlist


def siguientes(item):  # No utilizada
    logger.info()
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, '<h2>Siguiendo</h2>(.*?)<div class="box">')
    patron = '<div class="coverMini     shadow tiptip" title="([^"]+)">[^<]+'
    patron += '<img class="centeredPic centeredPicFalse"  onerror="[^"]+"  src="([^"]+)"[^<]+'
    patron += '<img src="/images/loading-mini.gif" class="loader"/>[^<]+'
    patron += '<div class="extra-info"><span class="year">[^<]+'
    patron += '</span><span class="value"><i class="icon-star"></i>[^<]+'
    patron += '</span></div>[^<]+'
    patron += '</div>[^<]+'
    patron += '</a>[^<]+'
    patron += '<a class="userepiinfo defaultLink" href="([^"]+)">(\d+)x(\d+)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    itemlist = []
    for scrapedtitle, scrapedthumbnail, scrapedurl, scrapedsession, scrapedepisode in matches:
        title = scrapertools.htmlclean(scrapedtitle)
        session = scrapertools.htmlclean(scrapedsession)
        episode = scrapertools.htmlclean(scrapedepisode)
        thumbnail = urlparse.urljoin(item.url, scrapedthumbnail)
        fanart = thumbnail.replace("mediathumb", "mediabigcover")
        plot = ""
        title = session + "x" + episode + " - " + title
        referer = urlparse.urljoin(item.url, scrapedurl)
        url = referer
        itemlist.append(
            Item(channel=item.channel, action="episodio", title=title, url=url, thumbnail=thumbnail, plot=plot,
                 contentTitle=title, show=title, fanart=fanart, extra=session + "|" + episode))
    return itemlist


def episodio(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    session = str(int(item.extra.split("|")[0]))
    episode = str(int(item.extra.split("|")[1]))
    patrontemporada = '<div class="checkSeason"[^>]+>Temporada ' + session + '<div class="right" onclick="controller.checkSeason(.*?)\s+</div></div>'
    matchestemporadas = re.compile(patrontemporada, re.DOTALL).findall(data)
    for bloque_episodios in matchestemporadas:
        patron = '<span class="title defaultPopup" href="([^"]+)"><span class="number">' + episode + ' </span>([^<]+)</span>(\s*</div>\s*<span[^>]*><span[^>]*>[^<]*</span><span[^>]*>[^<]*</span></span><div[^>]*><button[^>]*><span[^>]*>[^<]*</span><span[^>]*>[^<]*</span></button><div class="action([^"]*)" data-action="seen">)?'
        matches = re.compile(patron, re.DOTALL).findall(bloque_episodios)
        for scrapedurl, scrapedtitle, info, visto in matches:
            if visto.strip() == "active":
                visto_string = "[visto] "
            else:
                visto_string = ""
            numero = episode
            title = visto_string + session + "x" + numero + " " + scrapertools.htmlclean(scrapedtitle)
            thumbnail = ""
            plot = ""
            epid = scrapertools.find_single_match(scrapedurl, "id/(\d+)")
            url = host + "/links/viewepisode/id/" + epid
            itemlist.append(
                Item(channel=item.channel, action="findvideos", title=title, url=url, thumbnail=thumbnail, plot=plot,
                     contentTitle=title, fanart=item.fanart, show=item.show))
    itemlist2 = []
    for capitulo in itemlist:
        itemlist2 = findvideos(capitulo)
    return itemlist2


def peliculas(item):
    logger.info()
    headers = {"X-Requested-With": "XMLHttpRequest"}
    data = httptools.downloadpage(item.url, headers=headers).data
    json_object = jsontools.load(data)
    data = json_object["content"]
    return parse_mixed_results(item, data)


def episodios(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patrontemporada = '<ul.*?<li class="season-header" >([^<]+)<(.*?)\s+</ul>'
    matchestemporadas = re.compile(patrontemporada, re.DOTALL).findall(data)
    idserie = scrapertools.find_single_match(data, 'data-model="5" data-id="(\d+)"')
    token = scrapertools.find_single_match(data, '_token" content="([^"]+)"')
    if (config.get_platform().startswith("xbmc") or config.get_platform().startswith("kodi")):
        itemlist.append(Item(channel=item.channel, action="infosinopsis", title="INFO / SINOPSIS", url=item.url,
                             thumbnail=item.thumbnail, fanart=item.fanart, folder=False))
    for nombre_temporada, bloque_episodios in matchestemporadas:
        # Extrae los episodios
        patron_episodio = '<li><a href="#"(.*?)</a></li>'
        # patron  =  '<li><a href="#" data-id="([^"]*)".*?data-href="([^"]+)">\s*<div class="name">\s*<span class="num">([^<]+)</span>\s*([^<]+)\s*</div>.*?"show-close-footer episode model([^"]+)"'
        matches = re.compile(patron_episodio, re.DOTALL).findall(bloque_episodios)
        for data_episodio in matches:

            scrapeid = scrapertools.find_single_match(data_episodio, '<li><a href="#" data-id="([^"]*)"')
            scrapedurl = scrapertools.find_single_match(data_episodio, 'data-href="([^"]+)">\s*<div class="name">')
            numero = scrapertools.find_single_match(data_episodio, '<span class="num">([^<]+)</span>')
            scrapedtitle = scrapertools.find_single_match(data_episodio,
                                                          '<span class="num">.*?</span>\s*([^<]+)\s*</div>')
            visto = scrapertools.find_single_match(data_episodio, '"show-close-footer episode model([^"]+)"')

            title = nombre_temporada.replace("Temporada ", "").replace("Extras de la serie", "Extras 0").replace(" ",
                                                                                                                 "") + "x" + numero + " " + scrapertools.htmlclean(
                scrapedtitle)
            if visto.strip() == "seen":
                title = "[visto] " + title

            thumbnail = item.thumbnail
            fanart = item.fanart
            plot = ""
            url = host + scrapedurl
            itemlist.append(
                Item(channel=item.channel, action="findvideos", nom_serie=item.title, tipo="5", title=title, url=url,
                     thumbnail=thumbnail, plot=plot, contentTitle=title, fanart=fanart, show=item.show))


    if config.get_videolibrary_support():
        show = re.sub(r"\s\(\d+\)\s\(\d+\.\d+\)", "", item.show)
        itemlist.append(
            Item(channel='megadede', title="Añadir esta serie a la videoteca", url=item.url, token=token,
                 action="add_serie_to_library", extra="episodios###", show=show))
        itemlist.append(
            Item(channel='megadede', title="Descargar todos los episodios de la serie", url=item.url, token=token,
                 action="download_all_episodes", extra="episodios", show=show))
        itemlist.append(Item(channel='megadede', title="Marcar como Pendiente", tipo="5", idtemp=idserie, token=token,
                             valor="pending", action="megadede_check", show=show))
        itemlist.append(Item(channel='megadede', title="Marcar como Siguiendo", tipo="5", idtemp=idserie, token=token,
                             valor="following", action="megadede_check", show=show))
        itemlist.append(Item(channel='megadede', title="Marcar como Finalizada", tipo="5", idtemp=idserie, token=token,
                             valor="seen", action="megadede_check", show=show))
        itemlist.append(Item(channel='megadede', title="Marcar como Favorita", tipo="5", idtemp=idserie, token=token,
                             valor="favorite", action="megadede_check", show=show))
        itemlist.append(
            Item(channel='megadede', title="Quitar marca", tipo="5", idtemp=idserie, token=token, valor="nothing",
                 action="megadede_check", show=show))
        itemlist.append(
            Item(channel='megadede', title="Añadir a lista", tipo="5", tipo_esp="lista", idtemp=idserie, token=token,
                 action="megadede_check", show=show))
    return itemlist


def parse_listas(item, bloque_lista):
    logger.info()
    if item.tipo == "populares":
        patron = '<div class="lista(.*?)</div>\s*</h4>'
    else:
        patron = '<div class="lista(.*?)</h4>\s*</div>'
    matches = re.compile(patron, re.DOTALL).findall(bloque_lista)
    itemlist = []
    for lista in matches:
        scrapedurl = scrapertools.htmlclean(scrapertools.find_single_match(lista, '<a href="([^"]+)">[^<]+</a>'))
        scrapedtitle = scrapertools.find_single_match(lista, '<a href="[^"]+">([^<]+)</a>')
        scrapedfollowers = scrapertools.find_single_match(lista, 'Follow: <span class="number">([^<]+)')
        scrapedseries = scrapertools.find_single_match(lista, '<div class="lista-stat badge">Series: ([^<]+)')
        scrapedpelis = scrapertools.find_single_match(lista, '<div class="lista-stat badge">Pelis: ([^<]+)')
        title = scrapertools.htmlclean(scrapedtitle) + ' ('
        if scrapedpelis != '':
            title += scrapedpelis + ' pelis, '
        if scrapedseries != '':
            title += scrapedseries + ' series, '
        if scrapedfollowers != '':
            title += scrapedfollowers + ' seguidores'
        title += ')'
        url = urlparse.urljoin(host, scrapedurl)
        thumbnail = ""
        itemlist.append(
            Item(channel=item.channel, action="peliculas", token=item.token, tipo="lista", title=title, url=url))
    nextpage = scrapertools.find_single_match(bloque_lista,
                                              '<div class="onclick load-more-icon no-json" data-action="replace" data-url="([^"]+)"')
    if nextpage != '':
        url = urlparse.urljoin(host, nextpage)
        itemlist.append(Item(channel=item.channel, action="lista_sig", token=item.token, tipo=item.tipo,
                             title=">> Página siguiente", extra=item.extra, url=url))
    try:
        import xbmcplugin
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    except:
        pass
    return itemlist


def listas(item):
    logger.info()
    if item.tipo == "tuslistas":
        patron = 'Tus listas(.*?)>Listas que sigues<'
    elif item.tipo == "siguiendo":
        patron = '<h3>Listas que sigues</h3>(.*?)<h2>Listas populares</h2>'
    else:
        patron = '<div class="content">\s*<h2>Listas populares(.*?)</div>\s*</div>\s*</div>\s*</div>\s*</div>'
    data = httptools.downloadpage(item.url).data
    item.token = scrapertools.find_single_match(data, '_token" content="([^"]+)"').strip()
    bloque_lista = scrapertools.find_single_match(data, patron)
    return parse_listas(item, bloque_lista)


def lista_sig(item):
    logger.info()
    headers = {"X-Requested-With": "XMLHttpRequest"}
    data = httptools.downloadpage(item.url, headers=headers).data
    return parse_listas(item, data)


def pag_sig(item):
    logger.info()
    headers = {"X-Requested-With": "XMLHttpRequest"}
    data = httptools.downloadpage(item.url, headers=headers).data
    return parse_mixed_results(item, data)


def findvideos(item, verTodos=False):
    logger.info()
    data = httptools.downloadpage(item.url).data
    data_model = scrapertools.find_single_match(data, 'data-model="([^"]+)"')
    if not data_model:
        try:
            login()
            data = httptools.downloadpage(item.url).data
            data_model = scrapertools.find_single_match(data, 'data-model="([^"]+)"')
        except:
            pass
    data_id = scrapertools.find_single_match(data, 'data-id="([^"]+)"')
    trailer = "https://www.youtube.com/watch?v=" + scrapertools.find_single_match(data,
                                                                                  'data-youtube="([^"]+)" class="youtube-link')
    url = host + "/aportes/" + data_model + "/" + data_id + "?popup=1"
    data = httptools.downloadpage(url).data
    token = scrapertools.find_single_match(data, '_token" content="([^"]+)"')
    patron = 'target="_blank" (.*?)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    itemlist = []
    idpeli = data_id
    if (config.get_platform().startswith("xbmc") or config.get_platform().startswith("kodi")) and data_model == "4":
        itemlist.append(Item(channel=item.channel, action="infosinopsis", title="INFO / SINOPSIS", url=item.url,
                             thumbnail=item.thumbnail, fanart=item.fanart, folder=False))
        itemlist.append(Item(channel=item.channel, action="play", title="TRAILER", url=item.url, trailer=trailer,
                             thumbnail=item.thumbnail, fanart=item.fanart, folder=False))
    itemsort = []
    sortlinks = config.get_setting("megadedesortlinks",
                                   item.channel)  # 0:no, 1:valoracion, 2:idioma, 3:calidad, 4:idioma+calidad, 5:idioma+valoracion, 6:idioma+calidad+valoracion
    showlinks = config.get_setting("megadedeshowlinks", item.channel)  # 0:todos, 1:ver online, 2:descargar
    if sortlinks != '' and sortlinks != "No":
        sortlinks = int(sortlinks)
    else:
        sortlinks = 0
    if showlinks != '' and showlinks != "No":
        showlinks = int(showlinks)
    else:
        showlinks = 0
    for match in matches:
        jdown = scrapertools.find_single_match(match, '<span class="fa fa-download"></span>([^<]+)')
        if (showlinks == 1 and jdown != '') or (
                showlinks == 2 and jdown == ''):  # Descartar enlaces veronline/descargar
            continue
        idioma_1 = ""
        idiomas = re.compile('<img src="https://cd.*?/images/flags/([^"]+).png', re.DOTALL).findall(match)
        idioma_0 = idiomas[0]
        if len(idiomas) > 1:
            idioma_1 = idiomas[1]
            idioma = idioma_0 + ", SUB " + idioma_1
        else:
            idioma_1 = ''
            idioma = idioma_0
        calidad_video = scrapertools.find_single_match(match,
                                                       '<span class="fa fa-video-camera"></span>(.*?)</div>').replace(
            "  ", "").replace("\n", "")
        calidad_audio = scrapertools.find_single_match(match,
                                                       '<span class="fa fa-headphones"></span>(.*?)</div>').replace(
            "  ", "").replace("\n", "")
        thumb_servidor = scrapertools.find_single_match(match, '<img src="([^"]+)">')
        nombre_servidor = scrapertools.find_single_match(thumb_servidor, "hosts/([^\.]+).png")
        if jdown != '':
            title = "Download " + nombre_servidor + " (" + idioma + ") (Calidad " + calidad_video.strip() + ", audio " + calidad_audio.strip() + ")"
        else:
            title = "Ver en " + nombre_servidor + " (" + idioma + ") (Calidad " + calidad_video.strip() + ", audio " + calidad_audio.strip() + ")"
        valoracion = 0
        reports = scrapertools.find_single_match(match,
                                                 '<i class="fa fa-exclamation-triangle"></i><br/>\s*<span class="number" data-num="([^"]*)">')
        valoracion -= int(reports)
        title += " (" + reports + " reps)"
        url = urlparse.urljoin(item.url, scrapertools.find_single_match(match, 'href="([^"]+)"'))
        thumbnail = thumb_servidor
        plot = ""
        if sortlinks > 0:
            # orden1 para dejar los "downloads" detras de los "ver" al ordenar
            # orden2 segun configuración
            if sortlinks == 1:
                orden = valoracion
            elif sortlinks == 2:
                orden = valora_idioma(idioma_0, idioma_1)
            elif sortlinks == 3:
                orden = valora_calidad(calidad_video, calidad_audio)
            elif sortlinks == 4:
                orden = (valora_idioma(idioma_0, idioma_1) * 100) + valora_calidad(calidad_video, calidad_audio)
            elif sortlinks == 5:
                orden = (valora_idioma(idioma_0, idioma_1) * 1000) + valoracion
            elif sortlinks == 6:
                orden = (valora_idioma(idioma_0, idioma_1) * 100000) + (
                valora_calidad(calidad_video, calidad_audio) * 1000) + valoracion
            itemsort.append(
                {'action': "play", 'title': title, 'data_id': data_id, 'token': token, 'tipo': data_model, 'url': url,
                 'thumbnail': thumbnail, 'fanart': item.fanart, 'plot': plot, 'extra': item.url,
                 'contentTitle': item.contentTitle, 'orden1': (jdown == ''), 'orden2': orden})
        else:
            itemlist.append(
                Item(channel=item.channel, action="play", data_id=data_id, token=token, tipo=data_model, title=title,
                     url=url, thumbnail=thumbnail, fanart=item.fanart, plot=plot, extra=item.url,
                     contentTitle=item.contentTitle))

    if sortlinks > 0:
        numberlinks = config.get_setting("megadedenumberlinks", item.channel)  # 0:todos, > 0:n*5 (5,10,15,20,...)
        # numberlinks = int(numberlinks) if numberlinks != '' and numberlinks !="No" else 0
        if numberlinks != '' and numberlinks != "No":
            numberlinks = int(numberlinks)
        else:
            numberlinks = 0
        if numberlinks == 0:
            verTodos = True
        itemsort = sorted(itemsort, key=lambda k: (k['orden1'], k['orden2']), reverse=True)
        for i, subitem in enumerate(itemsort):
            if verTodos == False and i >= numberlinks:
                itemlist.append(
                    Item(channel=item.channel, action='findallvideos', title='Ver todos los enlaces', url=item.url,
                         extra=item.extra))
                break
            itemlist.append(
                Item(channel=item.channel, action=subitem['action'], title=subitem['title'], data_id=subitem['data_id'],
                     token=subitem['token'], tipo=subitem['tipo'], url=subitem['url'], thumbnail=subitem['thumbnail'],
                     fanart=subitem['fanart'], plot=subitem['plot'], extra=subitem['extra'],
                     contentTitle=subitem['contentTitle']))
    if data_model == "4":
        itemlist.append(
            Item(channel=item.channel, action="megadede_check", tipo="4", token=token, title="Marcar como Pendiente",
                 valor="pending", idtemp=idpeli))
        itemlist.append(
            Item(channel=item.channel, action="megadede_check", tipo="4", token=token, title="Marcar como Vista",
                 valor="seen", idtemp=idpeli))
        itemlist.append(
            Item(channel=item.channel, action="megadede_check", tipo="4", token=token, title="Marcar como Favorita",
                 valor="favorite", idtemp=idpeli))
        itemlist.append(Item(channel=item.channel, action="megadede_check", tipo="4", token=token, title="Quitar Marca",
                             valor="nothing", idtemp=idpeli))
        itemlist.append(
            Item(channel='megadede', title="Añadir a lista", tipo="4", tipo_esp="lista", idtemp=idpeli, token=token,
                 action="megadede_check"))
    return itemlist


def findallvideos(item):
    return findvideos(item, True)


def play(item):
    itemlist = []
    if "trailer" in item:
        url = item.trailer
        itemlist = servertools.find_video_items(data=url)
        for videoitem in itemlist:
            videoitem.title = item.title
            videoitem.contentTitle = item.contentTitle
            videoitem.thumbnail = item.thumbnail
            videoitem.channel = item.channel
        return itemlist
    else:
        logger.info("url=" + item.url)
        # Hace la llamada
        headers = {'Referer': item.extra}
        data = httptools.downloadpage(item.url, headers=headers).data
        url = scrapertools.find_single_match(data,
                                             '<a href="([^"]+)" target="_blank"><button class="btn btn-primary">visitar enlace</button>')
        url = urlparse.urljoin(host, url)
        headers = {'Referer': item.url}
        media_url = httptools.downloadpage(url, headers=headers, follow_redirects=False).headers.get("location")
        itemlist = servertools.find_video_items(data=media_url)
        for videoitem in itemlist:
            videoitem.title = item.title
            videoitem.contentTitle = item.contentTitle
            videoitem.thumbnail = item.thumbnail
            videoitem.channel = item.channel
        try:
            checkseen(item)
        except:
            pass
        return itemlist


def checkseen(item):
    logger.info(item)
    url_temp = ""
    if item.tipo == "8":
        url_temp = host + "/set/episode/" + item.data_id + "/seen"
        tipo_str = "series"
        headers = {"User-Agent":"Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/61.0.3163.100 Safari/537.36", "Referer": host + "/serie/",
                                "X-Requested-With": "XMLHttpRequest", "X-CSRF-TOKEN": item.token}
    else:
        url_temp = host + "/set/usermedia/" + item.tipo + "/" + item.data_id + "/seen"
        tipo_str = "pelis"
        headers = {"User-Agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko) "
                                 "Chrome/61.0.3163.100 Safari/537.36", "Referer": host + "/serie/",
                   "X-Requested-With": "XMLHttpRequest", "X-CSRF-TOKEN": item.token}
    data = httptools.downloadpage(url_temp, post="id=" + item.idtemp, headers=headers).data
    return True


def infosinopsis(item):
    logger.info()
    data = httptools.downloadpage(item.url).data
    scrapedtitle = scrapertools.find_single_match(data, '<div class="media-title">([^<]+)</div>')
    scrapedvalue = scrapertools.find_single_match(data, '<span class="value">([^<]+)</span>')
    scrapedyear = scrapertools.find_single_match(data,
                                                 '<strong>Fecha</strong>\s*<div class="mini-content">([^<]+)</div>').strip()
    scrapedduration = scrapertools.htmlclean(scrapertools.find_single_match(data,
                                                                            '<strong>Duración</strong>\s*<div class="mini-content">([^<]+)</div>').strip().replace(
        "   ", "").replace("\n", ""))
    scrapedplot = scrapertools.find_single_match(data, '<div class="plot expandable">([^<]+)<div').strip()
    generos = scrapertools.find_single_match(data, '<strong>Género</strong>\s*<ul>(.*?)</ul>')
    scrapedgenres = re.compile('<li>([^<]+)</li>', re.DOTALL).findall(generos)
    scrapedcasting = re.compile(
        '<a href="%s/star/[^"]+"><div class="text-main">([^<]+)</div></a>\s*<div class="text-sub">\s*([^<]+)</div>' %host,
        re.DOTALL).findall(data)
    title = scrapertools.htmlclean(scrapedtitle)
    plot = "[B]Año: [/B]" + scrapedyear
    plot += "  [B]Duración: [/B]" + scrapedduration
    plot += "  [B]Puntuación usuarios: [/B]" + scrapedvalue
    plot += "\n[B]Géneros: [/B]" + ", ".join(scrapedgenres)
    plot += "\n\n[B]Sinopsis:[/B]\n" + scrapertools.htmlclean(scrapedplot)
    plot += "\n\n[B]Casting:[/B]\n"
    for actor, papel in scrapedcasting:
        plot += actor + " (" + papel.strip() + ")\n"
    tbd = TextBox("DialogTextViewer.xml", os.getcwd(), "Default")
    tbd.ask(title, plot)
    del tbd
    return


try:
    import xbmcgui
    class TextBox(xbmcgui.WindowXML):
        """ Create a skinned textbox window """
        def __init__(self, *args, **kwargs):
            pass
        def onInit(self):
            try:
                self.getControl(5).setText(self.text)
                self.getControl(1).setLabel(self.title)
            except:
                pass
        def onClick(self, controlId):
            pass
        def onFocus(self, controlId):
            pass
        def onAction(self, action):
            if action == 7:
                self.close()
        def ask(self, title, text):
            self.title = title
            self.text = text
            self.doModal()
except:
    pass


def valora_calidad(video, audio):
    prefs_video = ['hdmicro', 'hd1080', 'hd720', 'hdrip', 'dvdrip', 'rip', 'tc-screener', 'ts-screener']
    prefs_audio = ['dts', '5.1', 'rip', 'line', 'screener']
    video = ''.join(video.split()).lower()
    if video in prefs_video:
        pts = (9 - prefs_video.index(video)) * 10
    else:
        pts = (9 - 1) * 10
    audio = ''.join(audio.split()).lower()
    if audio in prefs_audio:
        pts = (9 - prefs_audio.index(audio)) * 10
    else:
        pts = (9 - 1) * 10
    return pts


def valora_idioma(idioma_0, idioma_1):
    prefs = ['spanish', 'latino', 'catalan', 'english', 'french']
    if idioma_0 in prefs:
        pts = (9 - prefs.index(idioma_0)) * 10
    else:
        pts = (9 - 1) * 10
    if idioma_1 != '':  # si hay subtítulos
        idioma_1 = idioma_1.replace(' SUB', '')
        if idioma_1 in prefs:
            pts += 8 - prefs.index(idioma_1)
        else:
            pts += 8 - 1
    else:
        pts += 9  # sin subtítulos por delante
    return pts


def megadede_check(item):
    if item.tipo_esp == "lista":
        url_temp = host + "/listas/addmediapopup/" + item.tipo + "/" + item.idtemp + "?popup=1"
        data = httptools.downloadpage(url_temp).data
        patron = '<div class="lista model" data-model="10" data-id="([^"]+)">+'
        patron += '.*?<a href="/lista/[^"]+">([^<]+)</a>+'
        matches = re.compile(patron, re.DOTALL).findall(data)
        itemlist = []
        for id_lista, nombre_lista in matches:
            itemlist.append(Item(channel=item.channel, action="megadede_check", tipo=item.tipo, tipo_esp="add_list",
                                 token=item.token, title=nombre_lista, idlista=id_lista, idtemp=item.idtemp))
        if len(itemlist) < 1:
            itemlist.append(Item(channel=item.channel, action="", title="No tienes ninguna lista creada por ti!"))
        return itemlist
    else:
        if item.tipo == "10" or item.tipo == "lista":
            url_temp = host + "/set/lista/" + item.idtemp + "/" + item.valor
        else:
            if (item.tipo_esp == "add_list"):
                url_temp = host + "/set/listamedia/" + item.idlista + "/add/" + item.tipo + "/" + item.idtemp
            else:
                url_temp = host + "/set/usermedia/" + item.tipo + "/" + item.idtemp + "/" + item.valor
        if item.tipo == "5":
            tipo_str = "series"
        elif item.tipo == "lista":
            tipo_str = "listas"
        else:
            tipo_str = "pelis"
        headers = {"User-Agent":"Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/61.0.3163.100 Safari/537.36","Referer": host + "/" + tipo_str, "X-Requested-With": "XMLHttpRequest",
                   "X-CSRF-TOKEN": item.token}
        data = httptools.downloadpage(url_temp, post="id=" + item.idtemp, headers=headers).data.strip()
        dialog = platformtools
        dialog.ok = platformtools.dialog_ok
        if data == "1":
            if item.valor != "nothing":
                dialog.ok('SUCCESS', 'Marca realizada con éxito!')
            elif item.valor == "nothing":
                dialog.ok('SUCCESS', 'Marca eliminada con éxito!')
        elif item.valor == "unfollow":
            dialog.ok('SUCCESS', 'Has dejado de seguir esta lista!')
        elif item.valor == "follow":
            dialog.ok('SUCCESS', 'Has comenzado a seguir esta lista!')
        elif item.tipo_esp == "add_list":
            dialog.ok('SUCCESS', 'Añadido a la lista!')
        else:
            dialog.ok('ERROR', 'No se pudo realizar la acción!')
