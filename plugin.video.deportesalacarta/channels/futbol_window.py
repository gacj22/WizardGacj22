# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Distributed under the terms of GNU General Public License v3 (GPLv3)
# http://www.gnu.org/licenses/gpl-3.0.html
# ------------------------------------------------------------

import re
import datetime
import urllib
import re
import os
import traceback

import xbmcgui, xbmc

from thesportsdb import thesportsdb
from core import config
from core import httptools
from core import logger
from core import scrapertools
from core import jsontools
from core import channeltools
from platformcode import platformtools

texto_busqueda = ""
main_window = None
window_club = None
window_liga = None
window_match = None
window_players = None
window_thumb = None
window_select = None
change_team = False


def ventana(item):
    global main_window
    main_window = SportsWindow("SportsWindow.xml", config.get_runtime_path())
    if item.url_home:
        return main_window.Start(item, maximiza=item.maximiza, url_home=item.url_home, url_away=item.url_away)
    else:
        return main_window.Start(item, maximiza=item.maximiza)

def ventana_liga(item):
    global window_liga
    window_liga = Liga("MatchWindow.xml", config.get_runtime_path())
    return window_liga.Start(item.url, item.thumbnail, item.liga)


class SportsWindow(xbmcgui.WindowXMLDialog):
    def Start(self, item, caption="Información del encuentro", maximiza=False, name1tsdb="", name1tf="", name2tsdb="", name2tf="",team1=None, team2=None, data1="", data2="", datadirecto="", url_home="", url_away="", home_teams_tsdb=[], home_teams_transf=[], away_teams_tsdb=[], away_teams_transf=[], fuentes=None):
        self.caption = caption
        self.item = item
        self.maximiza = maximiza
        self.fanart = "http://i.imgur.com/l070p5c.jpg"
        self.home_team = team1
        self.away_team = team2
        self.home_name = ""
        self.away_name = ""
        self.url_home = url_home
        self.url_away = url_away
        self.data_chant = ""
        self.data_home = data1
        self.data_away = data2
        self.data_directo = datadirecto
        self.songs = []
        self.indice_song = 0
        self.loop = False
        self.botones = []
        self.focus = -1
        self.index_fanart = 0
        self.index_fanart2 = 0
        self.picture = False
        loading = None

        if not name1tsdb:
            loading = platformtools.dialog_progress("Cargando info de equipos...", "Recopilando datos de TheSportsDB")
            loading.update(20, "Recopilando datos de TheSportsDB")

        self.fecha = self.item.date
        self.hora = self.item.time

        self.nameh, self.namea = self.item.evento.split(" vs ")
        self.nameh = self.nameh.strip()
        self.namea = self.namea.strip()
        self.home_name = self.nameh
        self.away_name = self.namea
        if name1tsdb:
            self.home_name_tsdb = name1tsdb
            self.home_name_tf = name1tf
            self.away_name_tsdb = name2tsdb
            self.away_name_tf = name2tf
            self.home_teams_tsdb = home_teams_tsdb
            self.home_teams_transf = home_teams_transf
            self.away_teams_tsdb = away_teams_tsdb
            self.away_teams_transf = away_teams_transf
        else:
            # Se busca en el fichero futbol_window_data.json si hay un nombre disponible
            # asociado al nombre de cada equipo y se sustituye para su posterior búsqueda
            file_json = os.path.join(config.get_runtime_path(), 'channels', 'futbol_window_data.json')
            data_json = jsontools.load_json(open(file_json).read())
            try:
                name_provisional = re.sub(r'(?i) de ', ' ', self.home_name).lower()
                if data_json[name_provisional]["tsdb"]:
                    self.home_name_tsdb = data_json[name_provisional]["tsdb"]
                else:
                    self.home_name_tsdb = self.home_name[:]
                if data_json[name_provisional]["tf"]:
                    self.home_name_tf = data_json[name_provisional]["tf"]
                else:
                    self.home_name_tf = self.home_name[:]
            except:
                self.home_name_tsdb = self.home_name[:]
                self.home_name_tf = self.home_name[:]

            try:
                name_provisional = re.sub(r'(?i) de ', ' ', self.away_name).lower()
                if data_json[name_provisional]["tsdb"]:
                    self.away_name_tsdb = data_json[name_provisional]["tsdb"]
                else:
                    self.away_name_tsdb = self.away_name[:]
                if data_json[name_provisional]["tf"]:
                    self.away_name_tf = data_json[name_provisional]["tf"]
                else:
                    self.away_name_tf = self.away_name[:]
            except:
                self.away_name_tsdb = self.away_name[:]
                self.away_name_tf = self.away_name[:]
        
        # Fuentes según el skin, si es un skin diferente se abre el archivo Fonts.xml del skin
        # y se extrae el nombre correcto para cada tamaño de fuente de forma estimada (puede fallar)
        
        skin = xbmc.getSkinDir()
        if not fuentes:
            self.fonts = get_fonts(skin)
        else:
            self.fonts = fuentes

        # Búsqueda en thesportsdb
        api = thesportsdb.Api(key="1")
        if not self.home_team and not self.away_team:
            try:
                self.home_teams_tsdb = api.Search().Teams(team=self.home_name_tsdb)
                self.home_team = self.home_teams_tsdb[0]
            except:
                pass
            try:
                self.away_teams_tsdb = api.Search().Teams(team=self.away_name_tsdb)
                self.away_team = self.away_teams_tsdb[0]
            except:
                pass

        if loading:
            loading.update(40, "Recopilando datos de Transfermarkt")
        if not self.data_home:
            # Buscamos equipos local y visitante en transfermarkt
            try:
                if not self.url_home:
                    data = httptools.downloadpage("http://www.transfermarkt.es/schnellsuche/ergebnis/schnellsuche?query=%s&x=0&y=0" % urllib.quote(self.home_name_tf.replace("%2B", "+")), cookies=False).data
                    bloque = scrapertools.find_single_match(data, '<div class="table-header">Buscar resultados: Clubes(.*?)<div class="keys"')
                    self.home_teams_transf = scrapertools.find_multiple_matches(bloque, '<td class="zentriert suche-vereinswappen"><img src="([^"]+)".*?alt="([^"]+)".*?href="([^"]+)"')
                    next_page = scrapertools.find_single_match(bloque, '<li class="naechste-seite"><a href="([^"]+)"')
                    if next_page:
                        next_page = "http://www.transfermarkt.es"+next_page.replace("&amp;", "&")
                        self.home_teams_transf.append(["http://i.imgur.com/iJrWkdL.jpg", "[COLOR green]Página siguiente >>[/COLOR]", next_page])
                    if self.home_teams_transf:
                        self.url_home = "http://www.transfermarkt.es" + self.home_teams_transf[0][2]
                        self.data_home = httptools.downloadpage(self.url_home, cookies=False).data
                        self.data_home = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","", self.data_home)
                        self.galeria_home = "http://www.transfermarkt.es"+scrapertools.find_single_match(self.data_home, '<a href="([^"]+)"><div class="kartei-button second-kartei kartei-number-3">')
                    else:
                        self.data_home = "None"
                        self.galeria_home = ""
                else:
                    self.home_teams_transf = []
                    self.data_home = httptools.downloadpage(self.url_home, cookies=False).data
                    self.data_home = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","", self.data_home)
                    self.galeria_home = "http://www.transfermarkt.es"+scrapertools.find_single_match(self.data_home, '<a href="([^"]+)"><div class="kartei-button second-kartei kartei-number-3">')
            except:
                self.home_teams_transf = []
                self.data_home = "None"
                self.galeria_home = ""

            try:
                if not self.url_away:
                    data = httptools.downloadpage("http://www.transfermarkt.es/schnellsuche/ergebnis/schnellsuche?query=%s&x=0&y=0" % urllib.quote(self.away_name_tf.replace("%2B", "+")), cookies=False).data
                    bloque = scrapertools.find_single_match(data, '<div class="table-header">Buscar resultados: Clubes(.*?)<div class="keys"')
                    self.away_teams_transf = scrapertools.find_multiple_matches(bloque, '<td class="zentriert suche-vereinswappen"><img src="([^"]+)".*?alt="([^"]+)".*?href="([^"]+)"')
                    next_page = scrapertools.find_single_match(bloque, '<li class="naechste-seite"><a href="([^"]+)"')
                    if next_page:
                        next_page = "http://www.transfermarkt.es"+next_page.replace("&amp;", "&")
                        self.away_teams_transf.append(["http://i.imgur.com/iJrWkdL.jpg", "[COLOR green]Página siguiente >>[/COLOR]", next_page])
                    if self.away_teams_transf:
                        self.url_away = "http://www.transfermarkt.es" + self.away_teams_transf[0][2]
                        self.data_away = httptools.downloadpage(self.url_away, cookies=False).data
                        self.data_away = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","", self.data_away)
                        self.galeria_away = "http://www.transfermarkt.es"+scrapertools.find_single_match(self.data_away, '<a href="([^"]+)"><div class="kartei-button second-kartei kartei-number-3">')
                    else:
                        self.data_away = "None"
                        self.galeria_away = ""
                else:
                    self.away_teams_transf = []
                    self.data_away = httptools.downloadpage(self.url_away, cookies=False).data
                    self.data_away = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","", self.data_away)
                    self.galeria_away = "http://www.transfermarkt.es"+scrapertools.find_single_match(self.data_away, '<a href="([^"]+)"><div class="kartei-button second-kartei kartei-number-3">')
            except:
                self.away_teams_transf = []
                self.data_away = "None"
                self.galeria_away = ""
        else:
            self.galeria_home = "http://www.transfermarkt.es"+scrapertools.find_single_match(self.data_home, '<a href="([^"]+)"><div class="kartei-button second-kartei kartei-number-3">')
            self.galeria_away = "http://www.transfermarkt.es"+scrapertools.find_single_match(self.data_away, '<a href="([^"]+)"><div class="kartei-button second-kartei kartei-number-3">')

        # Info de entrenador, escudos y estadio
        try:
            bloque_manager = scrapertools.find_single_match(self.data_home, '<p class="text">(?:<span>|)(Entrenador|Cuerpo técnico)(.*?)</ul>')
            manager = scrapertools.find_multiple_matches(bloque_manager[1], '<div class="container-foto text-center">.*?src="([^"]+)" title="([^"]+)"')
            if manager:
                if "Entrenador" in bloque_manager[0]:
                    self.manager_home = manager[-1][1]
                    self.manager_home_thumb = "http:"+manager[-1][0]
                else:
                    self.manager_home = manager[0][1]
                    self.manager_home_thumb = "http:"+manager[0][0]
            if not self.manager_home:
                self.manager_home = self.home_team.strManager
        except:
            self.manager_home = ""
            self.manager_home_thumb = ""
        try:
            bloque_manager = scrapertools.find_single_match(self.data_away, '<p class="text">(?:<span>|)(Entrenador|Cuerpo técnico)(.*?)</ul>')
            manager = scrapertools.find_multiple_matches(bloque_manager[1], '<div class="container-foto text-center">.*?src="([^"]+)" title="([^"]+)"')
            if manager:
                if "Entrenador" in bloque_manager[0]:
                    self.manager_away = manager[-1][1]
                    self.manager_away_thumb = "http:"+manager[-1][0]
                else:
                    self.manager_away = manager[0][1]
                    self.manager_away_thumb = "http:"+manager[0][0]
            if not self.manager_away:
                self.manager_away = self.away_team.strManager
        except:
            self.manager_away = ""
            self.manager_away_thumb = ""

        self.escudo_home = scrapertools.find_single_match(self.data_home, '<div class="dataBild">.*?src="([^"]+)"')
        if self.escudo_home:
            self.escudo_home = "http:"+self.escudo_home.replace("head", "originals")
        else:
            try:
                self.escudo_home = self.home_team.strTeamBadge
            except:
                self.escudo_home = ""
        self.escudo_away = scrapertools.find_single_match(self.data_away, '<div class="dataBild">.*?src="([^"]+)"')
        if self.escudo_away:
            self.escudo_away = "http:"+self.escudo_away.replace("head", "originals")
        else:
            try:
                self.escudo_away = self.away_team.strTeamBadge
            except:
                self.escudo_away = ""

        casa_name = scrapertools.find_single_match(self.data_home, '<h1 itemprop="name"><b>([^<]+)</b>')
        visit_name = scrapertools.find_single_match(self.data_away, '<h1 itemprop="name"><b>([^<]+)</b>')
        self.estadio = scrapertools.find_single_match(self.data_home, 'Estadio:.*?<a[^>]+>([^<]+)<')
        try:
            if self.home_team.strStadiumThumb:
                self.estadio_thumb = self.home_team.strStadiumThumb
            else:
                raise ValueError('Error controlado')
        except:
                if maximiza:
                    self.estadio_thumb = "http://www.skyhdwallpaper.com/wp-content/uploads/2014/09/Wonderful-Grass-Field-Wallpaper.jpg"
                else:
                    self.estadio_thumb = "http://i.imgur.com/rRxOXK4.png"

        if self.url_home and not self.home_teams_transf:
            self.home_teams_transf.append([self.escudo_home, casa_name, self.url_home])
        if self.url_away and not self.away_teams_transf:
            self.away_teams_transf.append([self.escudo_away, visit_name, self.url_away])
        # Se ajusta el nombre de los equipos según los datos
        if casa_name:
                self.home_name = casa_name
        else:
            try:
                self.home_name = self.home_team.strTeam
            except:
                pass

        if visit_name:
                self.away_name = visit_name
        else:
            try:
                self.away_name = self.away_team.strTeam
            except:
                pass

        try:
            self.home_jersey = self.home_team.strTeamJersey
        except:
            self.home_jersey = ""
        try:
            self.away_jersey = self.away_team.strTeamJersey
        except:
            self.away_jersey = ""

        if loading:
            loading.update(80, "Consultando eventos en directo...")

        # Comprobar si partido en juego e info
        self.url_directo = ""
        competicion_thumb = ""
        try:
            if self.item.marcador:
                patron = '<a title="([^"]+)" class="hervorgehobener_link" href="([^"]+)">[^<]+</a>(?: - <a[^>]+>[^<]+</a>|)<br />[^,]+,\s*' \
                         '('+item.date+') - (\d+):(\d+) Hora</div><div class="wappen"><div><a[^>]+><img src="[^"]*" title="[^"]*" alt="'+casa_name+'"[^>]+>' \
                         '</a></div><div><a[^>]+>[^<]+<\/a>(?:<br \/><span[^>]+>[^<]+<\/span>|)<\/div><\/div><div class="ergebnis">' \
                         '<a title="(?:Previa|Crónica|Ticker en vivo)" class="[^"]*" (?:id="[^"]*" |)href="([^"]+)">([^<]+)<\/a><\/div><div class="wappen"><div><a[^>]+><img src="[^"]*" title="[^"]*" ' \
                         'alt="'+visit_name+'"'
            else:
                patron = '<a title="([^"]+)" class="hervorgehobener_link" href="([^"]+)">[^<]+</a>(?: - <a[^>]+>[^<]+</a>|)<br />[^,]+,\s*' \
                         '(\d+/\d+/\d+) - (\d+):(\d+) Hora</div><div class="wappen"><div><a[^>]+><img src="[^"]*" title="[^"]*" alt="'+casa_name+'"[^>]+>' \
                         '</a></div><div><a[^>]+>[^<]+<\/a>(?:<br \/><span[^>]+>[^<]+<\/span>|)<\/div><\/div><div class="ergebnis">' \
                         '<a title="(?:Previa|Crónica|Ticker en vivo)" class="[^"]*" (?:id="[^"]*" |)href="([^"]+)">([^<]+)<\/a><\/div><div class="wappen"><div><a[^>]+><img src="[^"]*" title="[^"]*" ' \
                         'alt="'+visit_name+'"'

            matches = scrapertools.find_multiple_matches(self.data_home, patron)
            for competicion_name, competicion_url, fecha, hora, minutos, directo, status in matches:
                dia, mes, year = scrapertools.find_single_match(fecha, '(\d+)/(\d+)/(\d+)')
                month_item = scrapertools.find_single_match(self.fecha, '\d+/(\d+)')
                if mes and month_item and mes != month_item:
                    continue
                hora_s = hora+ ":" + minutos
                hora = int(hora)
                minutos = int(minutos)
                if directo:
                    if hora_s != self.hora:
                        self.hora = hora_s
                    patron = 'wettbewerb/'+competicion_url.rsplit('/',1)[1]+'"><img src="([^"]+)"'
                    competicion_thumb = scrapertools.find_single_match(self.data_home, patron)
                    if competicion_thumb:
                        competicion_thumb = "http:"+competicion_thumb.replace("mediumquad/", "originals/")
                    if status != "-:-":
                        self.marcador = status
                        self.estado = "Finalizado"
                        self.url_directo = "http://www.transfermarkt.es/" + directo
                    else:
                        dia, mes, year = scrapertools.find_single_match(fecha, '(\d+)/(\d+)/(\d+)')
                        fecha = datetime.datetime(int(year), int(mes), int(dia), hora, minutos)
                        fecha_actual = datetime.datetime.today()
                        if (fecha_actual < fecha and fecha_actual >= fecha - datetime.timedelta(hours=1)) or (fecha_actual >= fecha and fecha_actual - datetime.timedelta(hours=2, minutes=30) <= fecha):
                            if not self.data_directo:
                                self.url_directo = "http://www.transfermarkt.es/" + directo.replace("/spielbericht/index/spielbericht/", "ticker/begegnung/live/")
                                self.data_directo = httptools.downloadpage(self.url_directo).data
                            self.marcador = scrapertools.find_single_match(self.data_directo, '"ergebnis_h":"([^"]+)","ergebnis_g":"([^"]+)"')
                            if self.marcador:
                                self.marcador = self.marcador[0]+":"+self.marcador[1]
                            self.estado, self.minuto = scrapertools.find_single_match(self.data_directo, '"status":"([^"]+)","minute":"([^"]+)"')
                            if self.estado == "31":
                                self.estado = "Descanso"
                            elif self.estado == "100":
                                self.estado = "Finalizado"
                            elif self.estado == "0":
                                self.estado = "Por comenzar"
                            else:
                                self.estado = "En juego"
                        else:
                            if not self.data_directo:
                                self.marcador = "--:--"
                                self.estado = "Previa"
                                self.url_directo = "http://www.transfermarkt.es/" + directo.replace("/spielbericht/index/spielbericht/", "ticker/begegnung/live/")
        except:
            logger.info(traceback.format_exc())

        # Info y logo de liga de equipo local y visitante
        if competicion_thumb:
            self.nombre_ligal = competicion_name
            self.url_ligal = "http://www.transfermarkt.es" + competicion_url
            self.thumb_ligal = competicion_thumb
            self.nombre_ligav = competicion_name
            self.url_ligav = "http://www.transfermarkt.es" + competicion_url
            self.thumb_ligav = competicion_thumb
        else:
            self.nombre_ligal = ""
            self.nombre_ligav = ""

            try:
                self.url_ligal, self.thumb_ligal, self.nombre_ligal = scrapertools.find_single_match(self.data_home, '<div class="dataZusatzImage"><a href="([^"]+)"><img src="([^"]+)" title="([^"]+)"')
                if self.url_ligal:
                    self.url_ligal = "http://www.transfermarkt.es" + self.url_ligal
                if self.thumb_ligal:
                    self.thumb_ligal = "http:" + self.thumb_ligal.replace("mediumquad", "originals")
            except:
                logger.info(traceback.format_exc())

            try:
                self.url_ligav, self.thumb_ligav, self.nombre_ligav = scrapertools.find_single_match(self.data_away, '<div class="dataZusatzImage"><a href="([^"]+)"><img src="([^"]+)" title="([^"]+)"')
                if self.url_ligav:
                    self.url_ligav = "http://www.transfermarkt.es" + self.url_ligav
                if self.thumb_ligav:
                    self.thumb_ligav = "http:" + self.thumb_ligav.replace("mediumquad", "originals")
            except:
                pass
        
        # Fanarts de equipos thesportsdb, no siempre siguen un orden, así que se intenta con todos
        self.fanart_home = ""
        self.fanart_visit = ""
        self.list_fanartsh = {}
        self.list_fanartsv = {}
        try:
            if self.home_team.strTeamFanart1:
                self.fanart_home = self.home_team.strTeamFanart1
                self.list_fanartsh["0"] = self.home_team.strTeamFanart1
        except:
            pass
        try:
            if self.home_team.strTeamFanart2:
                if not self.fanart_home:
                    self.fanart_home = self.home_team.strTeamFanart2
                self.list_fanartsh[str(len(self.list_fanartsh))] = self.home_team.strTeamFanart2
        except:
            pass
        try:
            if self.home_team.strTeamFanart3:
                if not self.fanart_home:
                    self.fanart_home = self.home_team.strTeamFanart3
                self.list_fanartsh[str(len(self.list_fanartsh))] = self.home_team.strTeamFanart3
        except:
            pass
        try:
            if self.home_team.strTeamFanart4:
                if not self.fanart_home:
                    self.fanart_home = self.home_team.strTeamFanart4
                self.list_fanartsh[str(len(self.list_fanartsh))] = self.home_team.strTeamFanart4
        except:
            pass
        try:
            if self.away_team.strTeamFanart1:
                if not self.fanart_visit:
                    self.fanart_visit = self.away_team.strTeamFanart1
                self.list_fanartsv["0"] = self.away_team.strTeamFanart1
        except:
            pass
        try:
            if self.away_team.strTeamFanart2:
                if not self.fanart_visit:
                    self.fanart_visit = self.away_team.strTeamFanart2
                self.list_fanartsv[str(len(self.list_fanartsv))] = self.away_team.strTeamFanart2
        except:
            pass
        try:
            if self.away_team.strTeamFanart3:
                if not self.fanart_visit:
                    self.fanart_visit = self.away_team.strTeamFanart3
                self.list_fanartsv[str(len(self.list_fanartsv))] = self.away_team.strTeamFanart3
        except:
            pass
        try:
            if self.away_team.strTeamFanart4:
                if not self.fanart_visit:
                    self.fanart_visit = self.away_team.strTeamFanart4
                self.list_fanartsv[str(len(self.list_fanartsv))] = self.away_team.strTeamFanart4
        except:
            pass

        if loading:
            loading.close()
        # Muestra la ventana
        self.doModal()
        return

    def onInit(self):
        self.setCoordinateResolution(0)
        # Ventana por defecto no maximizada
        if not self.maximiza:
            # Ponemos el título y las imagenes
            self.addControl(xbmcgui.ControlLabel(393,194,1169,28,"[B]"+self.caption+"[/B]", self.fonts["12"], "0xFFFFA500", '', 0x00000002))
            self.btn_maximiza = xbmcgui.ControlButton(1430,188,50,42,'', "http://i.imgur.com/pZwP3mQ.png", "http://i.imgur.com/v9c9dRn.png")
            self.addControl(self.btn_maximiza)
            self.botones.append(self.btn_maximiza)
            self.botones.append(self.getControl(10003))
            # Ponemos el foco
            self.setFocus(self.btn_maximiza)
            
            # Fanart predefinido o de ambos si los tienen
            try:
                if self.fanart_home and self.fanart_visit:
                    self.fanart_predef = xbmcgui.ControlImage(364,229,1258,721,"", 0, '0x85FFFFFF')
                    self.addControl(self.fanart_predef)
                    self.fanart1 = xbmcgui.ControlImage(364,229,628,721,self.fanart_home, 0, '0x80FFFFFF')
                    self.addControl(self.fanart1)
                    self.fanart1b = xbmcgui.ControlButton(364,229,628,721, '', '')
                    self.addControl(self.fanart1b)
                    self.fanart2 = xbmcgui.ControlImage(993,229,629,721,self.fanart_visit, 0, '0x80FFFFFF')
                    self.addControl(self.fanart2)
                    self.fanart2b = xbmcgui.ControlButton(993,229,629,721,'', '')
                    self.addControl(self.fanart2b)
                else:
                    self.fanart_predef = xbmcgui.ControlImage(364,229,1258,721,self.fanart, 0, '0x85FFFFFF')
                    self.addControl(self.fanart_predef)
                    self.fanart1 = xbmcgui.ControlImage(364,229,628,721,"")
                    self.addControl(self.fanart1)
                    self.fanart1.setVisible(False)
                    self.fanart1b = xbmcgui.ControlButton(364,229,628,721, '', '')
                    self.addControl(self.fanart1b)
                    self.fanart1b.setVisible(False)
                    self.fanart2 = xbmcgui.ControlImage(993,229,629,721,"")
                    self.addControl(self.fanart2)
                    self.fanart2.setVisible(False)
                    self.fanart2b = xbmcgui.ControlButton(993,229,629,721,'', '')
                    self.addControl(self.fanart2b)
                    self.fanart2b.setVisible(False)
            except:
                logger.info(traceback.format_exc())

            # Botón siguiente fanart si hay más de uno
            visible = xbmc.getCondVisibility('[Control.IsVisible('+str(self.fanart1.getId())+')]')
            if len(self.list_fanartsh) > 1 or (self.list_fanartsh and not visible):
                self.next_fanart = xbmcgui.ControlButton(390,194, 30, 30, "", "http://i.imgur.com/4QHLvfy.png", "http://i.imgur.com/4QHLvfy.png")
                self.addControl(self.next_fanart)
                self.next_fanart.setAnimations([('focus', 'effect=zoom center=auto end=120%')])
            if len(self.list_fanartsv) > 1 or (self.list_fanartsv and not visible):
                self.next_fanart2 = xbmcgui.ControlButton(430,194, 30, 30, "", "http://i.imgur.com/lLPJAmX.png", "http://i.imgur.com/lLPJAmX.png")
                self.addControl(self.next_fanart2)
                self.next_fanart2.setAnimations([('focus', 'effect=zoom center=auto end=120%')])
            
            self.addControl(xbmcgui.ControlImage(520, 250, 950, 60,"http://i.imgur.com/QU4dmyO.png"))
            # Marcador si lo hay o boton VS
            try:
                if self.marcador:
                    self.btn_marcador = xbmcgui.ControlButton(955, 243, 96, 40, self.marcador, noFocusTexture='', focusTexture='', font=self.fonts["16"], textColor="0xFFDF0101", focusedColor="0xFF900E0E", alignment=0x00000002)
                    self.addControl(self.btn_marcador)
                    self.btn_marcador.setAnimations([('conditional','effect=zoom center=auto end=130% reversible=false time=1000 loop=true condition=Control.HasFocus('+str(self.btn_marcador.getId())+')',)])
                    if self.estado == "En juego":
                        self.addControl(xbmcgui.ControlLabel(950, 283, 100, 20, "Minuto: "+self.minuto, self.fonts["10"], "0xFF0101DF", "", 0x00000002))
                    else:
                        self.addControl(xbmcgui.ControlLabel(950, 283, 100, 20, self.estado, self.fonts["10"], "0xFF0101DF", "", 0x00000002))
            except:
                vs = xbmcgui.ControlButton(948, 260, 96, 43, '', "http://i.imgur.com/fLvgN8E.png", "http://i.imgur.com/fLvgN8E.png")
                self.addControl(vs)
                vs.setAnimations([('conditional','effect=slide start=550,0 delay=2000 time=4000 condition=true tween=elastic')])
                self.btn_marcador = xbmcgui.ControlButton(948, 260, 96, 43, '', "http://i.imgur.com/fLvgN8E.png", "http://i.imgur.com/fLvgN8E.png")
                self.addControl(self.btn_marcador)
                if self.url_directo:
                    self.btn_marcador.setAnimations([('conditional','effect=slide start=-550,0 delay=2000 time=4000 condition=true tween=elastic',),('focus','effect=zoom center=auto end=120% reversible=false')])
                else:
                    self.btn_marcador.setAnimations([('conditional','effect=slide start=-550,0 delay=2000 time=4000 condition=true tween=elastic')])
                    self.btn_marcador.setEnabled(False)

            # Nombre y botón de los equipos
            self.label_nombrel = xbmcgui.ControlButton(530, 265, 360, 50, "[B]"+self.home_name+"[/B]", noFocusTexture="", focusTexture="", font=self.fonts["24"], focusedColor="0xFFFFA500")
            self.addControl(self.label_nombrel)
            self.label_nombrel.setAnimations([('focus', 'effect=zoom center=auto start=70% end=100% time=500 reversible=false',)])
            self.label_nombrel.setVisibleCondition('[Control.HasFocus('+str(self.label_nombrel.getId())+')]', True)
            self.botones.append(self.label_nombrel)
            self.fadelabel_nombrel = xbmcgui.ControlFadeLabel(530, 265, 360, 50, self.fonts["24"], "0xFFFFA500")
            self.addControl(self.fadelabel_nombrel)
            self.fadelabel_nombrel.addLabel("[B]"+self.home_name+"[/B]")
            self.fadelabel_nombrel.setVisibleCondition('[!Control.IsVisible('+str(self.label_nombrel.getId())+')]')

            self.label_nombrev = xbmcgui.ControlButton(1120, 265, 340, 50, "[B]"+self.away_name+"[/B]", noFocusTexture="", focusTexture="", font=self.fonts["24"], focusedColor="0xFFFFA500", alignment=0x00000005)
            self.addControl(self.label_nombrev)
            self.label_nombrev.setAnimations([('focus', 'effect=zoom center=auto start=70% end=100% time=500 reversible=false',)])
            self.label_nombrev.setVisibleCondition('[Control.HasFocus('+str(self.label_nombrev.getId())+')]', True)
            self.botones.append(self.label_nombrev)
            self.fadelabel_nombrev = xbmcgui.ControlFadeLabel(1120, 265, 340, 50, self.fonts["24"], "0xFFFFA500", 0x00000001)
            self.addControl(self.fadelabel_nombrev)
            self.fadelabel_nombrev.addLabel("[B]"+self.away_name+"[/B]")
            self.fadelabel_nombrev.setVisibleCondition('[!Control.IsVisible('+str(self.label_nombrev.getId())+')]')
            try:
                self.botones.append(self.btn_marcador)
            except:
                pass
            # Imagenes del escudo local
            if self.escudo_home:
                self.image_escudo_l = xbmcgui.ControlButton(400,355,260,260,'', self.escudo_home.replace("/normal/", "/originals/"), self.escudo_home.replace("/normal/", "/originals/"))
                self.addControl(self.image_escudo_l)
                self.image_escudo_l.setAnimations([('conditional','effect=slide start=0,-180 time=3500 tween=bounce condition=true',),('unfocus', 'effect=zoom start=110% end=100% time=1000 tween=elastic easing=out reversible=false',), ('focus', 'effect=zoom center=auto start=80% end=105% time=700 reversible=false',)])
                self.botones.append(self.image_escudo_l)
            else:
                self.image_escudo_l = xbmcgui.ControlButton(400,355,260,260,'', "http://i.imgur.com/6MsPA85.png", "http://i.imgur.com/6MsPA85.png")
                self.addControl(self.image_escudo_l)
                self.image_escudo_l.setAnimations([('conditional','effect=slide start=0,-180 time=3500 tween=bounce condition=true',)])
                self.image_escudo_l.setEnabled(False)

            # Imagen/Botón del estadio, si no hay se pone una imagen predefinida
            self.stadium = xbmcgui.ControlButton(744, 331, 427, 252, '', self.estadio_thumb, self.estadio_thumb)
            self.addControl(self.stadium)
            self.stadium.setAnimations([('conditional', 'effect=zoom center=auto start=10% delay=1000 time=3000 condition=true',)])
            self.addControl(xbmcgui.ControlImage(730, 320, 525, 290, 'http://i.imgur.com/aNXoMwp.png'))
            self.addControl(xbmcgui.ControlImage(745, 332, 72, 75, self.escudo_home))

            # Botones play, stop, anterior y siguiente canticos
            self.suporter = xbmcgui.ControlButton(1180, 400, 70, 50, '', "http://i.imgur.com/pj2BkT0.png", "http://i.imgur.com/19nSg15.png")
            self.addControl(self.suporter)
            self.suporter.setVisibleCondition('[!Player.IsInternetStream]')
            self.stop = xbmcgui.ControlButton(1180, 400, 70, 50, '', "http://i.imgur.com/i6asmQZ.png", "http://i.imgur.com/61Nc2Km.png")
            self.addControl(self.stop)
            self.stop.setVisibleCondition('[!Control.IsVisible('+str(self.suporter.getId())+')]')
            self.prev_song = xbmcgui.ControlButton(1175, 345, 70, 50, '', "http://i.imgur.com/1ns7J4k.png", "http://i.imgur.com/dIiX0xG.png")
            self.addControl(self.prev_song)
            self.prev_song.setVisible(False)
            self.next_song = xbmcgui.ControlButton(1175, 445, 70, 50, '', "http://i.imgur.com/WREPdvx.png", "http://i.imgur.com/dPJTCBi.png")
            self.addControl(self.next_song)
            self.next_song.setVisible(False)
            self.botones.append(self.prev_song)
            self.botones.append(self.suporter)
            self.botones.append(self.stop)
            self.botones.append(self.next_song)
            self.no_songs = xbmcgui.ControlImage(1180, 400, 70, 50,"http://i.imgur.com/kwjinY9.png")
            self.addControl(self.no_songs)
            self.no_songs.setVisible(False)

            # Imagenes del escudo visitante
            if self.escudo_away:
                self.image_escudo_v = xbmcgui.ControlButton(1330, 355, 260,260,'', self.escudo_away.replace("/normal/", "/originals/"), self.escudo_away.replace("/normal/", "/originals/"))
                self.addControl(self.image_escudo_v)
                self.image_escudo_v.setAnimations([('conditional','effect=slide start=0,-180 time=3500 tween=bounce condition=true',),('unfocus', 'effect=zoom start=110% end=100% time=1000 tween=elastic easing=out reversible=false',), ('focus', 'effect=zoom center=auto start=80% end=105% time=700 reversible=false',)])
                self.botones.append(self.image_escudo_v)
            else:
                self.image_escudo_v = xbmcgui.ControlButton(1330, 355, 260,260,'', "http://i.imgur.com/Ccic8fk.png", "http://i.imgur.com/Ccic8fk.png")
                self.addControl(self.image_escudo_v)
                self.image_escudo_v.setAnimations([('conditional','effect=slide start=0,-180 time=3500 tween=bounce condition=true',)])
                self.image_escudo_v.setEnabled(False)


            # Imágenes de las camisetas
            try:
                self.camiseta_home = xbmcgui.ControlButton(600, 700, 245, 245, '', self.home_team.strTeamJersey, self.home_team.strTeamJersey)
                self.addControl(self.camiseta_home)
                self.camiseta_home.setAnimations([('conditional', 'effect=fade start=20% end=100% time=2000 condition=true',), ('focus', 'effect=zoom center=auto end=110% time=10',)])
                self.botones.append(self.camiseta_home)
            except:
                self.camiseta_home = xbmcgui.ControlButton(600, 700, 245, 245, '', "http://i.imgur.com/IDiQsfM.png", "http://i.imgur.com/IDiQsfM.png")
                self.addControl(self.camiseta_home)
                self.camiseta_home.setAnimations([('conditional', 'effect=fade start=20% end=100% time=2000 condition=true',), ('focus', 'effect=zoom center=auto end=110% time=10',)])
                self.botones.append(self.camiseta_home)

            try:
                self.camiseta_away = xbmcgui.ControlButton(1147, 700, 245, 245, '', self.away_team.strTeamJersey, self.away_team.strTeamJersey)
                self.addControl(self.camiseta_away)
                self.camiseta_away.setAnimations([('conditional', 'effect=fade start=20% end=100% time=2000 condition=true',), ('focus', 'effect=zoom center=auto end=110% time=10',)])
                self.botones.append(self.camiseta_away)
            except:
                self.camiseta_away = xbmcgui.ControlButton(1147, 700, 245, 245, '', "http://i.imgur.com/FDlMEWS.png", "http://i.imgur.com/FDlMEWS.png")
                self.addControl(self.camiseta_away)
                self.camiseta_away.setAnimations([('conditional', 'effect=fade start=20% end=100% time=2000 condition=true',), ('focus', 'effect=zoom center=auto end=110% time=10',)])
                self.botones.append(self.camiseta_away)
                
            # Nombre del estadio, se intenta con thesportsdb, sino se coge de transfermarkt
            try:
                self.addControl(xbmcgui.ControlImage(830, 620, 330, 95, "http://i.imgur.com/bg2ExYV.png"))
                label_stadium = xbmcgui.ControlFadeLabel(845,615,300,14,self.fonts["30"],"0xFFd1e33d",0x00000002)
                
                self.addControl(label_stadium)
                if self.estadio:
                    label_stadium.addLabel(self.estadio.upper())
                else:
                    if self.home_team.strStadium != "None":
                        label_stadium.addLabel(self.home_team.strStadium)
                    else:
                        label_stadium.addLabel("Estadio de " + self.home_name)
            except:
                logger.info(traceback.format_exc())
                label_stadium.addLabel("Estadio de " + self.home_name)

            # Imagen del silbato junto a fecha y hora
            self.addControl(xbmcgui.ControlImage(850,668,35,42,"http://i.imgur.com/W2oGJpZ.png"))
            if not self.fecha:
                self.fecha = "--/--"
            if not self.hora:
                self.hora = "--:--"
            self.fecha_hora = xbmcgui.ControlFadeLabel(896,657,195,14,self.fonts["30"],"0xFFd1e33d", 0x00000002)
            self.addControl(self.fecha_hora)
            self.fecha_hora.addLabel(self.fecha + "  -  "+self.hora)
            self.addControl(xbmcgui.ControlImage(1106,670,38,36,"http://i.imgur.com/YYx0S46.png"))
            self.addControl(xbmcgui.ControlImage(840, 625, 310, 85, "http://i.imgur.com/t6bVQ8c.png", 0, "0x80FFFFFF"))

            # Nombre de entrenador local y visitante e imagen si la hubiese
            try:
                if self.manager_home_thumb:
                    manager = xbmcgui.ControlImage(418,740,128,127, self.manager_home_thumb)
                else:
                    manager = xbmcgui.ControlImage(418,740,128,127, "http://tmssl.akamaized.net//images/portrait/medium/default.jpg?lm=1455618221")
                self.addControl(manager)
                manager.setAnimations([('conditional','effect=rotatex start=90 time=2500 condition=true tween=circle easing=in',)])
                self.addControl(xbmcgui.ControlImage(410,732, 140, 140, "http://i.imgur.com/e0wpSVU.png"))                    

                self.addControl(xbmcgui.ControlImage(370,875,230,60,"http://i.imgur.com/UHYt9Po.png"))
                label_manager1 = xbmcgui.ControlFadeLabel(457,881,130,30,self.fonts["10"],"0xFF000000", 0x00000002)
                self.addControl(label_manager1)
                if self.manager_home:
                    if self.manager_home.count(" ") == 1:
                        self.manager_home = re.sub(" ", "\n", self.manager_home, 1)
                    elif self.manager_home.count(" ") > 1:
                        self.manager_home = self.manager_home[::-1].replace(" ","\n",1)[::-1]
                    label_manager1.addLabel("[B]"+self.manager_home+"[/B]")
                else:
                    label_manager1.addLabel("[B]No\nDisponible[/B]")
            except:
                pass
            try:
                if self.manager_away_thumb:
                    manager = xbmcgui.ControlImage(1448,740,128,127, self.manager_away_thumb)
                else:
                    manager = xbmcgui.ControlImage(1448,740,128,127, "http://tmssl.akamaized.net//images/portrait/medium/default.jpg?lm=1455618221")
                self.addControl(manager)
                manager.setAnimations([('conditional','effect=rotatex start=90 time=2500 condition=true tween=circle easing=in',)])
                self.addControl(xbmcgui.ControlImage(1441, 732, 140, 140, "http://i.imgur.com/e0wpSVU.png"))
                
                self.addControl(xbmcgui.ControlImage(1386,875,230,60,"http://i.imgur.com/sn4MX4C.png"))
                label_manager2 = xbmcgui.ControlFadeLabel(1394,881,130,30,self.fonts["10"],"0xFF000000",0x00000002)
                self.addControl(label_manager2)
                if self.manager_away:
                    if self.manager_away.count(" ") == 1:
                        self.manager_away = re.sub(" ", "\n", self.manager_away, 1)
                    elif self.manager_away.count(" ") > 1:
                        self.manager_away = self.manager_away[::-1].replace(" ","\n",1)[::-1]
                    label_manager2.addLabel("[B]"+self.manager_away+"[/B]")
                else:
                    label_manager2.addLabel("[B]No\nDisponible[/B]")
            except:
                pass

            # Mensaje emergente al enfocar el botón de los nombres
            self.tip = xbmcgui.ControlFadeLabel(520, 223, 200, 30, self.fonts["10"], "0xFFFFA500")
            self.addControl(self.tip)
            self.tip.addLabel("¿Equipo incorrecto?")
            self.tip.setVisibleCondition('[Control.HasFocus('+str(self.label_nombrel.getId())+')]')
            self.tip2 = xbmcgui.ControlFadeLabel(1290, 223, 200, 30, self.fonts["10"], "0xFFFFA500")
            self.addControl(self.tip2)
            self.tip2.addLabel("¿Equipo incorrecto?")
            self.tip2.setVisibleCondition('[Control.HasFocus('+str(self.label_nombrev.getId())+')]')

            # Logo/s de liga/s
            self.logo_liga1 = None
            self.logo_liga2 = None
            if self.nombre_ligal or self.nombre_ligav:
                if self.nombre_ligal == self.nombre_ligav:
                    self.addControl(xbmcgui.ControlImage(925, 810, 130, 120,"http://i.imgur.com/f7MJBw3.png"))
                    self.logo_liga1 = xbmcgui.ControlButton(940, 820, 100, 95, '', self.thumb_ligal, self.thumb_ligal)
                    self.addControl(self.logo_liga1)
                    self.logo_liga1.setAnimations([('focus','effect=zoom center=auto start=70% time=600 reversible=false',)])
                    self.botones.append(self.logo_liga1)
                else:
                    if self.nombre_ligal:
                        self.addControl(xbmcgui.ControlImage(820, 810, 130, 120,"http://i.imgur.com/f7MJBw3.png"))
                        self.logo_liga1 = xbmcgui.ControlButton(835, 820, 100, 95, '', self.thumb_ligal, self.thumb_ligal)
                        self.addControl(self.logo_liga1)
                        self.logo_liga1.setAnimations([('focus','effect=zoom center=auto start=70% time=600 reversible=false',)])
                        self.botones.append(self.logo_liga1)
                    if self.nombre_ligav:
                        self.addControl(xbmcgui.ControlImage(1050, 810, 130, 120,"http://i.imgur.com/f7MJBw3.png"))
                        self.logo_liga2 = xbmcgui.ControlButton(1065, 820, 100, 95, '', self.thumb_ligav, self.thumb_ligav)
                        self.addControl(self.logo_liga2)
                        self.logo_liga2.setAnimations([('focus','effect=zoom center=auto start=70% time=600 reversible=false',)])
                        self.botones.append(self.logo_liga2)

            # Se añaden botones de fanarts si los hubiese para navegacion por teclado
            try:
                self.botones.append(self.next_fanart)
            except:
                pass
            try:
                self.botones.append(self.next_fanart2)
            except:
                pass

#------------Diseño Pantalla Completa-----------------------
        else:
            # Ponemos el background
            self.background = xbmcgui.ControlImage( -40, -40, 2000, 1195, self.estadio_thumb)
            self.addControl(self.background )  
           
           #self.addControl(xbmcgui.ControlImage(900, 400, 120, 67, "http://i.imgur.com/fLvgN8E.png"))

            # Imagenes del escudo local
            if self.escudo_home:
                self.table_teams = xbmcgui.ControlImage( 300, 345, 1250, 60, 'https://s6.postimg.org/3tdh37lox/tableteams.png')
                self.addControl(self.table_teams)
                self.versus=xbmcgui.ControlImage(895, 350, 100, 47  , "http://i.imgur.com/fLvgN8E.png")
                self.addControl(self.versus)
                self.versus.setAnimations([('conditional', 'effect=rotate start=100% end=0% time=1500 condition=true', ),('unfocus', 'effect=zoom start=110% end=100% time=1000 tween=elastic easing=out',), ('focus', 'effect=zoom start=80% end=110% time=700',)])
                self.marcador_d = xbmcgui.ControlImage( 878,344, 133, 60, 'http://s6.postimg.org/7vz4keu1d/marcador_d.png')
                
                self.table_teams.setAnimations([('conditional', 'effect=rotate start=100% end=0% time=1500 condition=true', ),('unfocus', 'effect=zoom start=110% end=100% time=1000 tween=elastic easing=out',), ('focus', 'effect=zoom start=80% end=110% time=700',)])
                
            
                self.image_escudo_l = xbmcgui.ControlButton(110,200,320,320,'', self.escudo_home.replace("/normal/", "/originals/"), self.escudo_home.replace("/normal/", "/originals/"))
                
                self.addControl(self.image_escudo_l)
                self.image_escudo_l.setAnimations([('conditional', 'effect=zoom start=20% end=100% time=1500 condition=true', ),('unfocus', 'effect=zoom start=110% end=100% time=1000 tween=elastic easing=out reversible=false',), ('focus', 'effect=zoom start=80% end=110% time=700 reversible=false',)])
                self.botones.append(self.image_escudo_l)
            else:
                self.table_teams = xbmcgui.ControlImage( 300, 345, 1250, 60, 'https://s6.postimg.org/3tdh37lox/tableteams.png')
                self.addControl(self.table_teams)
                self.versus=xbmcgui.ControlImage(895, 350, 100, 47  , "http://i.imgur.com/fLvgN8E.png")
                self.addControl(self.versus)
                self.versus.setAnimations([('conditional', 'effect=rotate start=100% end=0% time=1500 condition=true', ),('unfocus', 'effect=zoom start=110% end=100% time=1000 tween=elastic easing=out',), ('focus', 'effect=zoom start=80% end=110% time=700',)])
                self.marcador_d = xbmcgui.ControlImage( 878,344, 133, 60, 'http://s6.postimg.org/7vz4keu1d/marcador_d.png')
                
                self.table_teams.setAnimations([('conditional', 'effect=rotate start=100% end=0% time=1500 condition=true', ),('unfocus', 'effect=zoom start=110% end=100% time=1000 tween=elastic easing=out',), ('focus', 'effect=zoom start=80% end=110% time=700',)])
                self.image_escudo_l = xbmcgui.ControlButton(110,200,320,320,'', "http://i.imgur.com/6MsPA85.png", "http://i.imgur.com/6MsPA85.png")
                self.addControl(self.image_escudo_l)
                self.image_escudo_l.setAnimations([('conditional', 'effect=zoom start=20% end=100% time=1500 condition=true', )])
                self.image_escudo_l.setEnabled(False)

            # Nombre del equipo local
        
            #self.addControl(xbmcgui.ControlImage(895, 350, 100, 47, "http://i.imgur.com/fLvgN8E.png"))
            #self.addControl(self.table_horamatch )
            self.home_ncolored ="[COLOR floralwhite][B]"+self.home_name+"[/B][/COLOR]"
            self.label_nombrel = xbmcgui.ControlButton(440, 343, 417, 60, self.home_ncolored,noFocusTexture="", focusTexture="")
            self.addControl(self.label_nombrel)
            self.label_nombrel.setAnimations([('conditional', 'effect=rotatey start=100% end=0% time=2000 condition=true', ),('unfocus', 'effect=zoom start=110% end=100% time=500 tween=elastic easing=out reversible=false',), ('focus', 'effect=zoom start=70% end=100% time=500 reversible=false',)])
            self.botones.append(self.label_nombrel)
            self.fadelabel_nombrel = xbmcgui.ControlFadeLabel(440, 265, 360, 50)
            self.addControl(self.fadelabel_nombrel)
            self.fadelabel_nombrel.addLabel("[B]"+self.home_name+"[/B]")
            self.fadelabel_nombrel.setVisibleCondition('[!Control.IsVisible('+str(self.label_nombrel.getId())+')]')

            # Marcador si lo hay o boton VS

            try:
               if self.marcador:

                   if self.estado == "En juego" or self.estado=="Descanso":
                        self.addControl(self.marcador_d)
                        self.marcador_d.setAnimations([('conditional','effect=slide start=0,-700 delay=2000 time=2500 tween=bounce condition=true',)])

                        if self.estado == "Descanso":
                           self.time_m=xbmcgui.ControlLabel(893, 377, 100, 20, "Descanso", self.fonts["10"], "0xFF5ADF18", "", 0x00000002)
                        else:
                           self.time_m=xbmcgui.ControlLabel(890, 377, 100, 20, "Minuto: "+self.minuto, self.fonts["10"], "0xFFDF0101", "", 0x00000002)
                        self.addControl(self.time_m)
                        self.time_m.setAnimations([('conditional','effect=slide start=0,-700 delay=4500 time=1000  condition=true',)])
                        self.score_colored="[COLOR yellow][B]"+self.marcador+"[/B][/COLOR]"
                        self.btn_marcador=xbmcgui.ControlButton(900, 343, 90, 30, self.score_colored, noFocusTexture="", focusTexture="", font=self.fonts["24"], textColor="0xFFFFA500", alignment=0x00000002)
                        self.addControl(self.btn_marcador)
                        self.btn_marcador.setAnimations([('conditional','effect=slide start=0,-700 delay=4500 time=1000  condition=true',),('conditional','effect=fade center=auto end=130% reversible=false  time=1000 loop=true condition=Control.HasFocus('+str(self.btn_marcador.getId())+')',)])
                        self.previa=xbmcgui.ControlImage(842, 400, 200, 70, 'http://s6.postimg.org/3uiyhhzm9/live_score.png')
                        self.addControl(self.previa)
                        self.previa.setAnimations([('conditional', 'effect=slide center"auto" start=0,700  delay=4600 time=1500 tween=elastic condition=true', ),('conditional', 'effect=fade center"auto" start=20% end=100%  delay=2000 time=1500 condition=true', )])
                   elif self.estado == "Finalizado" :
                        self.addControl(self.marcador_d)
                        self.marcador_d.setAnimations([('conditional','effect=slide start=0,-700 delay=2000 time=2500 tween=bounce condition=true',)])
                       
                        self.score_colored="[COLOR yellow][B]"+self.marcador+"[/B][/COLOR]"
                        self.btn_marcador=xbmcgui.ControlButton(900, 346, 90, 30, self.score_colored, noFocusTexture="", focusTexture="", font=self.fonts["24"], textColor="0xFFFFA500", alignment=0x00000002)
                        self.addControl(self.btn_marcador)
                        self.btn_marcador.setAnimations([('conditional','effect=slide start=0,-700 delay=4500 time=1000  condition=true',),('conditional','effect=fade center=auto end=130% reversible=false  time=1000 loop=true condition=Control.HasFocus('+str(self.btn_marcador.getId())+')',)])
                        self.final=xbmcgui.ControlImage(850, 400, 200, 70, 'http://s6.postimg.org/9uyqez9n5/final.png')
                        self.addControl(self.final)
                        self.final.setAnimations([('conditional', 'effect=slide center"auto" start=0,700  delay=4600 time=1500 tween=elastic condition=true', ),('conditional', 'effect=fade center"auto" start=20% end=100%  delay=2000 time=1500 condition=true', )])
                    
                   else:
                        self.addControl(self.marcador_d)
                        self.marcador_d.setAnimations([('conditional','effect=slide start=0,-700 delay=2000 time=2500 tween=bounce condition=true',)])
                        self.btn_marcador = xbmcgui.ControlButton(890, 349, 110, 54,'','http://s6.postimg.org/dirt6w51t/0_0.png','http://s6.postimg.org/dirt6w51t/0_0.png')
                        self.addControl(self.btn_marcador)
                        self.btn_marcador.setAnimations([('conditional','effect=slide start=0,-700 delay=4500 time=1000  condition=true',),('conditional','effect=fade center=auto end=130% reversible=false  time=1000 loop=true condition=Control.HasFocus('+str(self.btn_marcador.getId())+')',)])
                        self.previa=xbmcgui.ControlImage(868, 410, 150, 40, 'http://s6.postimg.org/tfql3lxg1/preview.png')
                        self.addControl(self.previa)
                        self.previa.setAnimations([('conditional', 'effect=slide center"auto" start=0,700  delay=4600 time=1500 tween=elastic condition=true', ),('conditional', 'effect=fade center"auto" start=20% end=100%  delay=2000 time=1500 condition=true', )])
                   self.botones.append(self.btn_marcador)
            except:
                vs = xbmcgui.ControlButton(948, 260, 96, 43, '', "", "")
                self.addControl(vs)
                vs.setAnimations([('conditional','effect=slide start=550,0 delay=2000 time=4000 condition=true tween=elastic')])
                self.btn_marcador = xbmcgui.ControlButton(948, 260, 96, 43, '', "", "")
                self.addControl(self.btn_marcador)
                if self.url_directo:
                    self.btn_marcador.setAnimations([('conditional','effect=slide start=-550,0 delay=2000 time=4000 condition=true tween=elastic',),('focus','effect=zoom center=auto end=120% reversible=false')])
                else:
                    self.btn_marcador.setAnimations([('conditional','effect=slide start=-550,0 delay=2000 time=4000 condition=true tween=elastic')])
                    self.btn_marcador.setEnabled(False)
            # Imagen/Botón canticos
            self.suporter = xbmcgui.ControlButton(900, 80, 130, 100, '', "http://www.bocingol.com/appl/botiga/client/img/TR_2.png", "http://www.bocingol.com/appl/botiga/client/img/TR_2.png")
            self.addControl(self.suporter)
            #self.suporter.setVisibleCondition('[!Player.Playing]')
            self.suporter.setAnimations([('unfocus', 'effect=zoom start=110% end=100% time=1000 tween=elastic easing=out',), ('focus', 'effect=zoom start=80% end=110% time=700',), ('conditional', 'effect=zoom start=80% end=110% time=1500 condition=Player.IsInternetStream loop=true',)])
            self.stop = xbmcgui.ControlButton(924, 180, 50, 50, '', "http://s6.postimg.org/kobr3ze6p/sstopfocused.png", "http://s6.postimg.org/c9rj25nrl/sstop.png")

            self.addControl(self.stop)
            self.stop.setVisibleCondition('[Player.IsInternetStream]')
            self.prev_song = xbmcgui.ControlButton(850, 180, 50, 50, '',"http://s6.postimg.org/bf9ktv5ap/prevfocused.png" ,"http://s6.postimg.org/9r5u1h21d/prev.png")
            self.addControl(self.prev_song)
            self.prev_song.setVisibleCondition('[Player.Playing]')
            self.prev_song.setVisible(False)
            self.next_song = xbmcgui.ControlButton(1000, 180, 50, 50, '',"http://s6.postimg.org/rozqwrfyp/nextfocused.png", "http://s6.postimg.org/pryfefzwx/next.png")
            self.addControl(self.next_song)
            self.next_song.setVisibleCondition('[Player.Playing]')
            self.next_song.setVisible(False)
            self.botones.append(self.prev_song)
            self.botones.append(self.stop)
            self.botones.append(self.next_song)
            self.no_songs = xbmcgui.ControlImage(900, 80, 130, 100,"http://s6.postimg.org/kj2hdtjm9/no_song.png")
            self.addControl(self.no_songs)
            self.no_songs.setVisible(False)
            self.no_songs.setAnimations([('conditional', 'effect=zoom center=auto start=500% end=0% time=2000 condition=true',)])
            
            self.botones.append(self.suporter)

            #Nombre del equipo visitante
            self.away_ncolored ="[COLOR floralwhite][B]"+self.away_name+"[/B][/COLOR]"
            self.label_nombrev = xbmcgui.ControlButton(1070, 350, 350, 60, self.away_ncolored, noFocusTexture="", focusTexture="", alignment=0x00000001)
            self.addControl(self.label_nombrev)
            self.label_nombrev.setAnimations([('conditional', 'effect=rotatex start=100% end=0% time=2000 condition=true', ),('unfocus', 'effect=zoom start=110% end=100% time=500 tween=elastic easing=out reversible=false',), ('focus', 'effect=zoom start=70% end=100% time=500 reversible=false',)])
            self.botones.append(self.label_nombrev)
            self.fadelabel_nombrev = xbmcgui.ControlFadeLabel(910, 350, 530, 60)
            self.addControl(self.fadelabel_nombrev)
            self.fadelabel_nombrev.addLabel("[B]"+self.home_name+"[/B]")
            self.fadelabel_nombrev.setVisibleCondition('[!Control.IsVisible('+str(self.label_nombrel.getId())+')]')

            # Imagenes del escudo visitante
            if self.escudo_away:
                self.image_escudo_v = xbmcgui.ControlButton(1450, 200, 320,320,'', self.escudo_away.replace("/normal/", "/originals/"), self.escudo_away.replace("/normal/", "/originals/"))
                self.addControl(self.image_escudo_v)
                self.image_escudo_v.setAnimations([('conditional', 'effect=zoom start=20% end=100% time=1500 condition=true', ),('unfocus', 'effect=zoom start=110% end=100% time=1000 tween=elastic easing=out reversible=false',), ('focus', 'effect=zoom start=80% end=110% time=700 reversible=false',)])
                self.botones.append(self.image_escudo_v)
            else:
                self.image_escudo_v = xbmcgui.ControlButton(1450, 200, 320,320, '', "http://i.imgur.com/Ccic8fk.png", "http://i.imgur.com/Ccic8fk.png")
                self.addControl(self.image_escudo_v)
                self.image_escudo_v.setAnimations([('conditional', 'effect=zoom start=20% end=100% time=1500 condition=true', )])
                self.image_escudo_v.setEnabled(False)

            # Imágenes de las camisetas
            try:
                self.camiseta_home = xbmcgui.ControlButton(520, 650, 230, 245, '', self.home_team.strTeamJersey, self.home_team.strTeamJersey)
                self.addControl(self.camiseta_home)
                self.camiseta_home.setAnimations([('conditional', 'effect=fade start=20% end=100% time=2000 condition=true',), ('focus', 'effect=zoom end=110% time=10',)])
                self.botones.append(self.camiseta_home)
            except:
                self.camiseta_home = xbmcgui.ControlButton(513, 650, 230, 245, '', "http://i.imgur.com/IDiQsfM.png", "http://i.imgur.com/IDiQsfM.png")
                self.addControl(self.camiseta_home)
                self.camiseta_home.setAnimations([('conditional', 'effect=fade start=20% end=100% time=2000 condition=true',), ('focus', 'effect=zoom end=110% time=10',)])
                self.botones.append(self.camiseta_home)

            try:
                self.camiseta_away = xbmcgui.ControlButton(1150, 650, 230, 245, '', self.away_team.strTeamJersey, self.away_team.strTeamJersey)
                self.addControl(self.camiseta_away)
                self.camiseta_away.setAnimations([('conditional', 'effect=fade start=20% end=100% time=2000 condition=true',), ('focus', 'effect=zoom end=110% time=10',)])
                self.botones.append(self.camiseta_away)
            except:
                self.camiseta_away = xbmcgui.ControlButton(1158, 650, 230, 245, '', "http://i.imgur.com/FDlMEWS.png", "http://i.imgur.com/FDlMEWS.png")
                self.addControl(self.camiseta_away)
                self.camiseta_away.setAnimations([('conditional', 'effect=fade start=20% end=100% time=2000 condition=true',), ('focus', 'effect=zoom end=110% time=10',)])
                self.botones.append(self.camiseta_away)

            # Nombre de entrenador local y visitante e imagen si la hubiese
            try:
                if self.manager_home_thumb:
                    self.mister_circle= xbmcgui.ControlImage( 92,766,303,303, 'https://s6.postimg.org/kn9y0orrl/ringmister.png')
                    self.barra = xbmcgui.ControlImage( 300, 968, 500, 60, 'https://s6.postimg.org/84or6d5e9/barrae.png')
                    self.addControl(self.barra)
                    self.barra.setAnimations([('conditional', 'effect=slide start=100% end=0% time=2000 condition=true',)])
                    self.foto=xbmcgui.ControlImage(150,819,189,185, self.manager_home_thumb)
                    self.addControl(self.foto)
                    self.foto.setAnimations([('conditional', 'effect=slide start=500% end=0% time=2000 condition=true',)])
                    self.addControl(self.mister_circle)
                    self.mister_circle.setAnimations([('conditional', 'effect=slide start=500% end=0% time=2000 condition=true',)])
                if self.manager_home_thumb == "":
                    self.mister_circle= xbmcgui.ControlImage( 92,766,303,303, 'https://s6.postimg.org/kn9y0orrl/ringmister.png')
                    self.barra = xbmcgui.ControlImage( 300, 968, 500, 60, 'https://s6.postimg.org/84or6d5e9/barrae.png')
                    self.addControl(self.barra)
                    self.barra.setAnimations([('conditional', 'effect=slide start=100% end=0% time=2000 condition=true',)])
                    self.foto=xbmcgui.ControlImage(150,819,189,185, 'http://tmssl.akamaized.net//images/portrait/medium/default.jpg?lm=1455618221')
                    self.addControl(self.foto)
                    self.foto.setAnimations([('conditional', 'effect=slide start=500% end=0% time=2000 condition=true',)])
                    self.addControl(self.mister_circle)
                    self.mister_circle.setAnimations([('conditional', 'effect=slide start=500% end=0% time=2000 condition=true',)])
                
                if self.manager_home:
                   
                    self.Nombre_entrenadorc=" [COLOR black][B]"+self.manager_home+"[/B][/COLOR] "
                    self.nombre_entrenadorc = xbmcgui.ControlFadeLabel( 360,980, 1000, 400,self.fonts["12"])
                    self.addControl(self.nombre_entrenadorc)
                    self.nombre_entrenadorc.addLabel(self.Nombre_entrenadorc)
                    self.nombre_entrenadorc.setAnimations([('conditional', 'effect=rotatex start=100% end=0% time=2000 condition=true',)])
                if self.manager_home == "":
                    self.Nombre_entrenadorc=" [COLOR black][B]No Info[/B][/COLOR] "
                    self.nombre_entrenadorc = xbmcgui.ControlTextBox( 354,980, 1000, 400)
                    self.addControl(self.nombre_entrenadorc)
                    self.nombre_entrenadorc.setText( str(self.Nombre_entrenadorc) )
                    self.nombre_entrenadorc.setAnimations([('conditional', 'effect=rotatex start=100% end=0% time=2000 condition=true',)])
                
    
                    #self.manager_home = "[COLOR black][B]"+self.manager_home+"[/B][/COLOR]"
                    #self.getControl(10010).addLabel(self.manager_home)

            except:
                pass
            try:
                if self.manager_away_thumb:
                    self.mister_circle2= xbmcgui.ControlImage( 1493,766,303,303, 'https://s6.postimg.org/kn9y0orrl/ringmister.png')
                    self.barra2 = xbmcgui.ControlImage( 1100, 968, 500, 60, 'https://s6.postimg.org/84or6d5e9/barrae.png')
                    self.addControl(self.barra2)
                    self.barra2.setAnimations([('conditional', 'effect=slide start=100% end=0% time=2000 condition=true',)])
                    self.foto2=xbmcgui.ControlImage(1551,819,189,185, self.manager_away_thumb)
                    self.addControl(self.foto2)
                    self.foto2.setAnimations([('conditional', 'effect=slide start=-500% end=0% time=2000 condition=true',)])
                    self.addControl(self.mister_circle2)
                    self.mister_circle2.setAnimations([('conditional', 'effect=slide start=-500 end=0% time=2000 condition=true',)])
                if self.manager_away_thumb== "":
                    self.mister_circle2= xbmcgui.ControlImage( 1493,766,300,300, 'https://s6.postimg.org/kn9y0orrl/ringmister.png')
                    self.barra2 = xbmcgui.ControlImage( 1100, 968, 500, 60, 'https://s6.postimg.org/84or6d5e9/barrae.png')
                    self.addControl(self.barra2)
                    self.barra2.setAnimations([('conditional', 'effect=slide start=100% end=0% time=2000 condition=true',)])
                    self.foto2=xbmcgui.ControlImage(1551,819,189,185, 'http://tmssl.akamaized.net//images/portrait/medium/default.jpg?lm=1455618221')
                    self.addControl(self.foto2)
                    self.foto2.setAnimations([('conditional', 'effect=slide start=-500% end=0% time=2000 condition=true',)])
                    self.addControl(self.mister_circle2)
                    self.mister_circle2.setAnimations([('conditional', 'effect=slide start=-500 end=0% time=2000 condition=true',)])

                if self.manager_away:
                    
                    self.Nombre_entrenadorw=" [COLOR black][B]"+self.manager_away+"[/B][/COLOR] "
                    self.nombre_entrenadorw = xbmcgui.ControlFadeLabel(1210,980, 320, 400,self.fonts["12"],"0xFF000000",0x00000001)
                    self.addControl(self.nombre_entrenadorw)
                    self.nombre_entrenadorw.addLabel(self.Nombre_entrenadorw)
                    self.nombre_entrenadorw.setAnimations([('conditional', 'effect=rotatex start=100% end=0% time=2000 condition=true',)])
                if self.manager_away== "":
                    self.Nombre_entrenadorw=" [COLOR black][B]No Info[/B][/COLOR] "
                    self.nombre_entrenadorw = xbmcgui.ControlTextBox( 1410,980, 1000, 400)
                    self.addControl(self.nombre_entrenadorw)
                    self.nombre_entrenadorw.setText( str(self.Nombre_entrenadorw) )
                    self.nombre_entrenadorw.setAnimations([('conditional', 'effect=rotatex start=100% end=0% time=2000 condition=true',)])

            except:
                pass

            # Imagen del pito junto a fecha y hora
            self.pitorro=xbmcgui.ControlImage( 800,700, 40 , 40,"http://i.imgur.com/W2oGJpZ.png")
            if not self.fecha:
                self.fecha = "--/--"
            if not self.hora:
                self.hora = "--:--"
            self.fecha_hora_partido =self.fecha + "  -  "+self.hora
            self.table_horamatch = xbmcgui.ControlImage( 750, 650, 400, 100, 'https://s6.postimg.org/v6inxys9d/horamatch.png')
            self.wrongteam = xbmcgui.ControlImage( 440, 395, 250, 60, 'http://s6.postimg.org/qvr9yiidt/wrongteam.png')
            self.addControl(self.wrongteam)
            self.wrongteam.setVisibleCondition('[Control.HasFocus('+str(self.label_nombrel.getId())+')]')
            self.wrongteam.setAnimations([('conditional', 'effect=rotatex start=-30% end=0% time=1000  tween=elastic condition=Control.HasFocus('+str(self.label_nombrel.getId())+') ',)])
            self.tip = xbmcgui.ControlFadeLabel(470, 407, 190, 30, self.fonts["10"], "0xFFC61839")
            self.addControl(self.tip)
            self.tip.addLabel("[B]¿Equipo incorrecto?[/B]")
            self.tip.setVisibleCondition('[Control.HasFocus('+str(self.label_nombrel.getId())+')]')
            self.wrongteam2 = xbmcgui.ControlImage( 1200, 395, 250, 60, 'http://s6.postimg.org/qvr9yiidt/wrongteam.png')
            self.addControl(self.wrongteam2)
            self.wrongteam2.setVisibleCondition('[Control.HasFocus('+str(self.label_nombrev.getId())+')]')
            self.wrongteam2.setAnimations([('conditional', 'effect=rotatex start=-30% end=0% time=1000  tween=elastic condition=Control.HasFocus('+str(self.label_nombrev.getId())+') ',)])
            self.tip2 = xbmcgui.ControlFadeLabel(1230, 407, 190, 30, self.fonts["10"], "0xFFC61839")
            self.addControl(self.tip2)
            self.tip2.addLabel("[B]¿Equipo incorrecto?[/B]")
            self.tip2.setVisibleCondition('[Control.HasFocus('+str(self.label_nombrev.getId())+')]')
            self.addControl(self.table_horamatch )
            self.addControl(self.pitorro)
            try:
               if self.estadio:
                  self.Nombre_estadio=" [COLOR gold][B]"+self.estadio+"[/B][/COLOR] "
                  self.nombre_estadio = xbmcgui.ControlFadeLabel(750, 650,400, 150)
                  self.addControl(self.nombre_estadio)
                  self.nombre_estadio.addLabel(self.Nombre_estadio)
                  
               else:
                   try:
                  
                      self.Nombre_estadio=" [COLOR gold][B]"+self.home_team.strStadium+"[/B][/COLOR] "
                      self.nombre_estadio = xbmcgui.ControlFadeLabel(750, 650,400, 150)
                      self.addControl(self.nombre_estadio)
                      self.nombre_estadio.addLabel(self.Nombre_estadio)
                   
                   except:
                       self.nombree= " Estadio de " + self.home_name
                       self.Nombre_estadio=" [COLOR gold][B]"+self.nombree+"[/B][/COLOR] "
                       self.nombre_estadio = xbmcgui.ControlFadeLabel(750, 650,400, 150)
                       self.addControl(self.nombre_estadio)
                       self.nombre_estadio.addLabel(self.Nombre_estadio)
                  
            except:
                  logger.info(traceback.format_exc())
                  self.nombree= " Estadio de " + self.home_name
                  self.Nombre_estadio=" [COLOR gold][B]"+self.nombree+"[/B][/COLOR] "
                  self.nombre_estadio =xbmcgui.ControlFadeLabel(750, 650,400, 150)
                  self.addControl(self.nombre_estadio)
                  self.nombre_estadio.addLabel(self.Nombre_estadio)
                   
            self.Hora_partido=("[COLOR springgreen][B]"+self.fecha_hora_partido+"[/B][/COLOR]")
            self.hora_partido = xbmcgui.ControlTextBox( 880,700, 1000, 400)
            self.addControl(self.hora_partido)
            self.hora_partido.setText(self.Hora_partido)

            # Logo/s de liga/s
            self.logo_liga1 = None
            self.logo_liga2 = None
            if self.nombre_ligal or self.nombre_ligav:
                if self.nombre_ligal == self.nombre_ligav:
                    self.marco_liga=xbmcgui.ControlImage(808, 730, 260, 260,"http://s6.postimg.org/5jf6n391t/competitions.png")
                    self.addControl(self.marco_liga)
                    self.marco_liga.setAnimations([('conditional', 'effect=rotatex start=220% end=0% time=2000   condition=true tween=elastic ',)])
                    self.logo_liga1 = xbmcgui.ControlButton(890, 820, 100, 95, '', self.thumb_ligal, self.thumb_ligal)
                    self.addControl(self.logo_liga1)
                    self.logo_liga1.setAnimations([('conditional','effect=slide start=900,0  time=2500 condition=true tween=elastic'),('focus', 'effect=zoom center=auto start=80% end=105% time=700  tween=elastic easing=out reversible=false',)])
                    self.botones.append(self.logo_liga1)
                else:
                    if self.nombre_ligal:
                        self.marco_liga=xbmcgui.ControlImage(673, 730, 260, 260,"http://s6.postimg.org/5jf6n391t/competitions.png")
                        self.addControl(self.marco_liga)
                        self.marco_liga.setAnimations([('conditional', 'effect=rotatex start=220% end=0% delay=1200 time=2000   condition=true tween=elastic ',)])
                        self.logo_liga1 = xbmcgui.ControlButton(750, 820, 100, 95, '', self.thumb_ligal, self.thumb_ligal)
                        self.addControl(self.logo_liga1)
                        self.logo_liga1.setAnimations([('conditional','effect=slide start=-900,0  time=2500 condition=true tween=elastic'),('focus', 'effect=zoom center=auto start=80% end=105% time=700  tween=elastic easing=out reversible=false',)])
                        self.botones.append(self.logo_liga1)
                    if self.nombre_ligav:
                        self.marco_liga2=xbmcgui.ControlImage(982, 733, 260, 260,"http://s6.postimg.org/5kp4giavl/competitions2.png")
                        self.addControl(self.marco_liga2)
                        self.marco_liga2.setAnimations([('conditional', 'effect=rotatex start=220% end=0% delay=1200 time=2000   condition=true tween=elastic ',)])
                        self.logo_liga2 = xbmcgui.ControlButton(1067, 820, 100, 95, '', self.thumb_ligav, self.thumb_ligav)
                        self.addControl(self.logo_liga2)
                        self.logo_liga2.setAnimations([('conditional','effect=slide start=900,0  time=2500 condition=true tween=elastic'),('focus', 'effect=zoom center=auto start=80% end=105% time=700  tween=elastic easing=out reversible=false',)])
                        self.botones.append(self.logo_liga2)


    def onClick(self, id):
        # Boton Cancelar y [X]
        global window_club
        global main_window
        global window_liga
        global window_match
        global window_players
        if id == 10003:
            if xbmc.Player().isPlaying():
                xbmc.executebuiltin('xbmc.PlayMedia(Stop)')
            if self.picture:
                xbmc.executebuiltin('Action(Close,10002)')
            main_window.close()
            del main_window

        # Botones camisetas
        try:
            if id == self.camiseta_home.getId():
                window_players = Players("SportsWindow.xml", config.get_runtime_path())
                window_players.Start(self.data_home, self.galeria_home, self.escudo_home, self.home_jersey, self.home_team, fonts=self.fonts)
        except:
            pass
        try:
            if id == self.camiseta_away.getId():
                window_players = Players("SportsWindow.xml", config.get_runtime_path())
                window_players.Start(self.data_away, self.galeria_away, self.escudo_away, self.away_jersey, self.away_team, fonts=self.fonts)
        except:
            pass

        # Reproducción canticos: play, stop, siguiente, anterior
        try:
            if id == self.suporter.getId():
                if xbmc.Player().isPlaying():
                    xbmc.executebuiltin('xbmc.PlayMedia(Stop)')
                    xbmc.executebuiltin('Action(Select)')
                canticos(self, name=self.home_name)
        except:
            pass
        try:
            if id == self.stop.getId():
                canticos(self, type="stop")
        except:
            pass
        try:
            if id == self.next_song.getId():
                canticos(self, type="next")
        except:
            pass
        try:
            if id == self.prev_song.getId():
                canticos(self, type="prev")
        except:
            pass

        # Botones escudos, ventana club
        try:
            if id == self.image_escudo_l.getId():
                window_club = Club("ClubWindow.xml", config.get_runtime_path())
                window_club.Start(self.data_home, self.home_name, self.escudo_home, "Información del ", self.home_team, self.url_home, "", self.home_jersey, fonts=self.fonts)
        except:
            pass
        try:
            if id == self.image_escudo_v.getId():
                window_club = Club("ClubWindow.xml", config.get_runtime_path())
                window_club.Start(self.data_away, self.away_name, self.escudo_away, "Información del ", self.away_team, self.url_away, "", self.away_jersey, fonts=self.fonts)
        except:
            pass
        # Boton/es logos ligas
        try:
            if self.logo_liga1 and id == self.logo_liga1.getId():
                window_liga = Liga("MatchWindow.xml", config.get_runtime_path())
                window_liga.Start(self.url_ligal, self.thumb_ligal, self.nombre_ligal, fonts=self.fonts)
        except:
            pass
        try:
            if self.logo_liga2 and id == self.logo_liga2.getId():
                window_liga = Liga("MatchWindow.xml", config.get_runtime_path())
                window_liga.Start(self.url_ligav, self.thumb_ligav, self.nombre_ligav, fonts=self.fonts)
        except:
            pass

        # Botón marcado, abre ventana Match, previa, live o crónica de partido
        try:
            if id == self.btn_marcador.getId():
                if self.estado == "Finalizado":
                    window_match = Match("MatchWindow.xml", config.get_runtime_path())
                    window_match.Start(self.url_directo, self.escudo_home, self.home_name, self.escudo_away, self.away_name, self.marcador, fonts=self.fonts)
                elif self.estado == "Previa":
                    window_match = Match("MatchWindow.xml", config.get_runtime_path())
                    window_match.Start(self.url_directo, self.escudo_home, self.home_name, self.escudo_away, self.away_name, "0-0", fonts=self.fonts)
                else:
                    window_match = Match("MatchWindow.xml", config.get_runtime_path())
                    window_match.Start("", self.escudo_home, self.home_name, self.escudo_away, self.away_name, self.marcador, self.data_directo, fonts=self.fonts)
        except:
            pass

        # Botones equipo incorrecto
        try:
            if id == self.label_nombrel.getId():
                self.equipo_search("local")
        except:
            logger.info(traceback.format_exc())
        try:
            if id == self.label_nombrev.getId():
                self.equipo_search("visitante")
        except:
            logger.info(traceback.format_exc())

        # Boton para maximizar y cambiar el diseño
        try:
            if id == self.btn_maximiza.getId():
                self.stop1 = True
                self.stop2 = True
                if self.picture:
                    xbmc.executebuiltin('Action(Close,10002)')
                main_window.close()
                del main_window
                main_window = SportsWindow("SportsWindow.xml", config.get_runtime_path())
                main_window.Start(self.item, caption="Información del encuentro",
                             maximiza=True, name1tf=self.home_name_tf, name1tsdb=self.home_name_tsdb, name2tf=self.away_name_tf,
                             name2tsdb=self.away_name_tsdb, team1=self.home_team, team2=self.away_team, data1=self.data_home,
                             data2=self.data_away, datadirecto=self.data_directo, url_home=self.url_home, url_away=self.url_away,
                             home_teams_tsdb=self.home_teams_tsdb, home_teams_transf=self.home_teams_transf,
                             away_teams_tsdb=self.away_teams_tsdb, away_teams_transf=self.away_teams_transf, fuentes=self.fonts)
        except:
            pass

        # Botones fanart
        try:
            if id == self.next_fanart.getId():
                self.fanart_predef.setVisible(True)
                self.getControl(10002).setColorDiffuse("0xFFFFFFFF")
                if len(self.list_fanartsh) == 1:
                    if xbmc.getCondVisibility('[Control.IsVisible('+str(self.fanart1.getId())+')]'):
                        self.fanart1.setVisible(False)
                        self.fanart1b.setVisible(False)
                    else:
                        self.fanart1.setImage(self.list_fanartsh["0"])
                        self.fanart1.setVisible(True)
                        self.fanart1b.setVisible(True)
                else:
                    self.index_fanart += 1
                    if self.index_fanart != len(self.list_fanartsh):
                        self.fanart1.setImage(self.list_fanartsh[str(self.index_fanart)])
                        self.fanart1.setVisible(True)
                        self.fanart1b.setVisible(True)
                    else:
                        self.index_fanart = 0
                        self.fanart1.setImage(self.list_fanartsh[str(self.index_fanart)])
                        self.fanart1.setVisible(True)
                        self.fanart1b.setVisible(True)
        except:
            pass

        try:
            if id == self.next_fanart2.getId():
                self.fanart_predef.setVisible(True)
                self.getControl(10002).setColorDiffuse("0xFFFFFFFF")
                if len(self.list_fanartsv) == 1:
                    if xbmc.getCondVisibility('[Control.IsVisible('+str(self.fanart2.getId())+')]'):
                        self.fanart2.setVisible(False)
                        self.fanart2b.setVisible(False)
                    else:
                        self.fanart2.setImage(self.list_fanartsv["0"])
                        self.fanart2.setVisible(True)
                        self.fanart2b.setVisible(True)
                else:
                    self.index_fanart2 += 1
                    if self.index_fanart2 != len(self.list_fanartsv):
                        self.fanart2.setImage(self.list_fanartsv[str(self.index_fanart2)])
                        self.fanart2.setVisible(True)
                        self.fanart2b.setVisible(True)
                    else:
                        self.index_fanart2 = 0
                        self.fanart2.setImage(self.list_fanartsv[str(self.index_fanart2)])
                        self.fanart2.setVisible(True)
                        self.fanart2b.setVisible(True)
        except:
            pass

        try:
            if id == self.fanart1b.getId():
                if self.picture:
                    xbmc.executebuiltin('Action(Close,10002)')
                else:
                    self.picture = True
                self.fanart_predef.setVisible(False)
                self.fanart1.setVisible(False)
                self.fanart2.setVisible(False)
                self.getControl(10002).setColorDiffuse("0x95FF0000")
                xbmc.executebuiltin('ShowPicture('+self.list_fanartsh[str(self.index_fanart)]+')')
                
        except:
            pass
        try:
            if id == self.fanart2b.getId():
                if self.picture:
                    xbmc.executebuiltin('Action(Close,10002)')
                else:
                    self.picture = True
                self.fanart_predef.setVisible(False)
                self.fanart1.setVisible(False)
                self.fanart2.setVisible(False)
                self.getControl(10002).setColorDiffuse("0x95FF0000")
                xbmc.executebuiltin('ShowPicture('+self.list_fanartsv[str(self.index_fanart2)]+')')
        except:
            pass

        try:
            if id == self.stadium.getId():
                if self.picture:
                    xbmc.executebuiltin('Action(Close,10002)')
                    self.fanart_predef.setVisible(True)
                    self.fanart1.setVisible(True)
                    self.fanart2.setVisible(True)
                    self.getControl(10002).setColorDiffuse("0xFFFFFFFF")
                    self.picture = False
                else:
                    self.picture = True
                    self.fanart_predef.setVisible(False)
                    self.fanart1.setVisible(False)
                    self.fanart2.setVisible(False)
                    self.getControl(10002).setColorDiffuse("0x95FF0000")
                    xbmc.executebuiltin('ShowPicture('+self.estadio_thumb+')')
        except:
            pass

    # Función para lanzar ventana de seleccion/busqueda de equipo
    def equipo_search(self, equipo):
        if equipo == "local":
            lista_equipos_tsdb = self.home_teams_tsdb
            lista_equipos_tf = self.home_teams_transf
            original_name = self.nameh
        else:
            lista_equipos_tsdb = self.away_teams_tsdb
            lista_equipos_tf = self.away_teams_transf
            original_name = self.namea

        items = equipos_tsdb(lista_equipos_tsdb, actual=True)
        global window_select
        global change_team
        global main_window
        window_select = Select("DialogSelect.xml", config.get_runtime_path(), items=items, caption="Elige un equipo de la lista (TheSportsDB)", type="equipo", web="tsdb", name=original_name, fonts=self.fonts)
        window_select.doModal()
        items = equipos_transf(lista_equipos_tf, actual=True)
        window_select = Select("DialogSelect.xml", config.get_runtime_path(), items=items, caption="Elige un equipo de la lista (Transfermarkt)", type="equipo", web="tf", name=original_name, fonts=self.fonts)
        window_select.doModal()
        if change_team:
            if self.picture:
                xbmc.executebuiltin('Action(Close,10002)')
            xbmc.sleep(1000)
            main_window.close()
            del main_window
            platformtools.dialog_notification("Aplicando los cambios", "La ventana se reiniciará con la nueva información", sound=False)
            change_team = False
            ventana(self.item)


    def onAction(self, action):
        ACTION_MOVE_DOWN = 4
        ACTION_MOVE_LEFT = 1
        ACTION_MOVE_RIGHT = 2
        ACTION_MOVE_UP = 3

        global main_window
        if action == 92 or action == 10 or action == 110:
            if self.maximiza:
                if self.picture:
                    xbmc.executebuiltin('Action(Close,10002)')
                main_window.close()
                del main_window
                main_window = SportsWindow("SportsWindow.xml", config.get_runtime_path())
                main_window.Start(self.item, caption="Información del encuentro", maximiza=False,
                name1tsdb=self.home_name_tsdb, name1tf=self.home_name_tf, name2tsdb=self.away_name_tsdb, name2tf=self.away_name_tf, team1=self.home_team,
                team2=self.away_team, data1=self.data_home, data2=self.data_away, datadirecto=self.data_directo, url_home=self.url_home,
                url_away=self.url_away, home_teams_tsdb=self.home_teams_tsdb, home_teams_transf=self.home_teams_transf,
                away_teams_tsdb=self.away_teams_tsdb, away_teams_transf=self.away_teams_transf, fuentes=self.fonts)
            else:
                if xbmc.Player().isPlaying():
                    xbmc.executebuiltin('xbmc.PlayMedia(Stop)')
                if self.picture:
                    xbmc.executebuiltin('Action(Close,10002)')
                main_window.close()
                del main_window

        try:
            if action == ACTION_MOVE_RIGHT or action == ACTION_MOVE_DOWN:
                if self.focus < len(self.botones)-1:
                    self.focus += 1
                    if self.focus <= 1:
                        self.setFocus(self.botones[self.focus])
                    else:
                        while True:
                            id_focus = str(self.botones[self.focus].getId())
                            id_local = str(self.label_nombrel.getId())
                            id_visit = str(self.label_nombrev.getId())
                            if xbmc.getCondVisibility('[Control.IsVisible('+id_focus+')]') and id_focus != id_local and id_focus != id_visit:
                                self.setFocus(self.botones[self.focus])
                                break
                            elif id_focus == id_local or id_focus == id_visit:
                                self.setFocus(self.botones[self.focus])
                                break
                            self.focus += 1
                            if self.focus == len(self.botones):
                                break
        except:
            pass

        try:
            if action == ACTION_MOVE_LEFT or action == ACTION_MOVE_UP:
                if self.focus > 0:
                    self.focus -= 1
                    if self.focus <= 1:
                        self.setFocus(self.botones[self.focus])
                    else:
                        while True:
                            id_focus = str(self.botones[self.focus].getId())
                            id_local = str(self.label_nombrel.getId())
                            id_visit = str(self.label_nombrev.getId())
                            if xbmc.getCondVisibility('[Control.IsVisible('+id_focus+')]') and id_focus != id_local and id_focus != id_visit:
                                self.setFocus(self.botones[self.focus])
                                break
                            elif id_focus == id_local or id_focus == id_visit:
                                self.setFocus(self.botones[self.focus])
                                break
                            self.focus -= 1
                            if self.focus < 0:
                                break
        except:
            pass
                

class Players(xbmcgui.WindowXMLDialog):
    fanart = ""
    team = None
    thumbs = {}
    botones = []
    focus = -1

    def Start(self, data, url, escudo, camiseta="", team=None, caption="Jugadores", fonts=""):
        # Capturamos los parametros
        self.caption = caption
        self.team = team
        self.data = data
        self.url = url + "/page/"
        self.escudo = escudo
        self.camiseta = camiseta
        self.fonts = fonts
        
        # Fanart del equipo si existe, sino imagen predefinida
        try:
            self.fanart = team.strTeamFanart1
        except:
            pass
        if not self.fanart:
            self.fanart = "http://i.imgur.com/2FTkHud.jpg"

        # Extraemos la lista de jugadores con foto, nombre, edad y país
        self.players_team = []
        try:
            players = scrapertools.find_multiple_matches(self.data, '<div class=rn_nummer>([^<]+)<.*?src="([^"]+)" title="([^"]+)" alt="[^"]+" class="bilderrahmen-fixed".*?<td class="zentriert">.*?(\(\d+\)).*?src="([^"]+)"')
            i = 0
            for dorsal, thumb, name, age, country in players:
                if i > 29:
                    break
                name = name + " " + age 
                thumb = "http:" + thumb.replace("small/", "medium/")
                country = "http:" + country.replace("verysmall/", "originals/")
                dorsal = dorsal.rjust(2)
                self.players_team.append([name, thumb, country, dorsal])
                i += 1
        except:
            pass

        self.doModal()
        return

    def onInit(self):
        self.setCoordinateResolution(0)        

        # Ponemos el título y las imagenes
        self.addControl(xbmcgui.ControlLabel(413,194,1169,28,"[B]"+self.caption+"[/B]", self.fonts["12"], "0xFFFFA500", '', 0x00000002))
        self.addControl(xbmcgui.ControlImage(364,229,1258,721,self.fanart, 0, '0x85FFFFFF'))
        self.setFocus(self.getControl(10003))
        self.botones = []
        self.botones.append(self.getControl(10003))

        # Si hay datos de jugadores, se listan
        self.thumbs = {}
        if not self.players_team:
            self.addControl(xbmcgui.ControlLabel(630, 430, 900, 300, 'Plantilla en Construcción', font="font_MainMenu"))
        else:
            i = 0
            count = 1
            for name, thumb, country, dorsal in self.players_team:
                if i < 700:
                    self.addControl(xbmcgui.ControlImage(365, 250+i, 385, 45, "http://i.imgur.com/Yl0fq5O.png"))
                    jugador = xbmcgui.ControlButton(365, 235+i, 60, 70, '', thumb, thumb)
                    self.addControl(jugador)
                    jugador.setAnimations([('conditional','effect=slide start=-200,-200 delay=200 time=500 condition=true tween=circle easing=in',),('unfocus', 'effect=rotate center=auto start=0% end=360% time=1200',), ('focus', 'effect=zoom center=auto start=70% end=100% time=700 reversible=false',)])
                    self.botones.append(jugador)
                    if thumb:
                        self.thumbs[jugador.getId()] = thumb + "|" + self.url + str(count)
                    
                    fadelabel = xbmcgui.ControlFadeLabel(427, 257+i, 200, 50, self.fonts["10"])
                    self.addControl(fadelabel)
                    fadelabel.addLabel(name)
                    self.addControl(xbmcgui.ControlImage(698, 252+i, 35, 25, country))
                    if self.camiseta:
                        self.addControl(xbmcgui.ControlImage(625, 253+i, 45, 40, self.camiseta))
                    else:
                        self.addControl(xbmcgui.ControlImage(628, 253+i, 42, 40, self.escudo))
                    self.addControl(xbmcgui.ControlLabel(662, 262+i, 40, 30, dorsal, self.fonts["12"], "0xFF221c9a", "", 0x00000002))
                elif i >= 700 and i < 1400:
                    self.addControl(xbmcgui.ControlImage(765, 250+i-700, 385, 45, "http://i.imgur.com/Yl0fq5O.png"))
                    jugador = xbmcgui.ControlButton(765, 235+i-700, 60, 70, '', thumb, thumb)
                    self.addControl(jugador)
                    jugador.setAnimations([('conditional','effect=slide start=0,-200 delay=200 time=500 condition=true tween=circle easing=in',),('unfocus', 'effect=rotate center=auto start=0% end=360% time=1200',), ('focus', 'effect=zoom center=auto start=70% end=100% time=700 reversible=false',)])
                    self.botones.append(jugador)
                    if thumb:
                        self.thumbs[jugador.getId()] = thumb + "|" + self.url + str(count)
                    fadelabel = xbmcgui.ControlFadeLabel(827, 257+i-700, 200, 50, self.fonts["10"])
                    self.addControl(fadelabel)
                    fadelabel.addLabel(name)
                    self.addControl(xbmcgui.ControlImage(1098, 252+i-700, 35, 25, country))
                    if self.camiseta:
                        self.addControl(xbmcgui.ControlImage(1025, 253+i-700, 45, 40, self.camiseta))
                    else:
                        self.addControl(xbmcgui.ControlImage(1028, 253+i-700, 42, 40, self.escudo))
                    self.addControl(xbmcgui.ControlLabel(1062, 262+i-700, 40, 30, dorsal, self.fonts["12"], "0xFF221c9a", "", 0x00000002))
                elif i >= 1400:
                    self.addControl(xbmcgui.ControlImage(1160, 250+i-1400, 385, 45, "http://i.imgur.com/Yl0fq5O.png"))
                    jugador = xbmcgui.ControlButton(1160, 235+i-1400, 60, 70, '', thumb, thumb)
                    self.addControl(jugador)
                    jugador.setAnimations([('conditional','effect=slide start=200,-200 delay=200 time=500 condition=true tween=circle easing=in',),('unfocus', 'effect=rotate center=auto start=0% end=360% time=1200',), ('focus', 'effect=zoom center=auto start=70% end=100% time=700 reversible=false',)])
                    self.botones.append(jugador)
                    if thumb:
                        self.thumbs[jugador.getId()] = thumb + "|" + self.url + str(count)
                    fadelabel = xbmcgui.ControlFadeLabel(1222, 257+i-1400, 200, 50, self.fonts["10"])
                    self.addControl(fadelabel)
                    fadelabel.addLabel(name)
                    self.addControl(xbmcgui.ControlImage(1493, 252+i-1400, 35, 25, country))
                    if self.camiseta:
                        self.addControl(xbmcgui.ControlImage(1420, 253+i-1400, 45, 40, self.camiseta))
                    else:
                        self.addControl(xbmcgui.ControlImage(1423, 253+i-1400, 42, 40, self.escudo))
                    self.addControl(xbmcgui.ControlLabel(1457, 262+i-1400, 40, 30, dorsal, self.fonts["12"], "0xFF221c9a", "", 0x00000002))
                i += 70
                count += 1

    def onClick(self, id):
        # Boton Cancelar y [X]
        if id == 10003:
            global window_players
            window_players.close()
            del window_players
            
        # Si se clicka en una foto se abre retrato del jugador
        try:
            if self.thumbs.has_key(id):
                global window_thumb
                window_thumb = Thumb()
                window_thumb.Start('MyPics.xml', config.get_runtime_path(), thumbnail=self.thumbs[id], escudo=self.escudo, fuentes=self.fonts)
        except:
            pass

    def onAction(self, action):
        ACTION_MOVE_DOWN = 4
        ACTION_MOVE_LEFT = 1
        ACTION_MOVE_RIGHT = 2
        ACTION_MOVE_UP = 3

        if action == 92 or action == 10 or action == 110:
            global window_players
            window_players.close()
            del window_players

        if action == ACTION_MOVE_RIGHT or action == ACTION_MOVE_DOWN:
            if self.focus < len(self.botones)-1:
                self.focus += 1
                self.setFocus(self.botones[self.focus])

        if action == ACTION_MOVE_LEFT or action == ACTION_MOVE_UP:
            if self.focus > 0:
                self.focus -= 1
                self.setFocus(self.botones[self.focus])                
        

class Thumb(xbmcgui.WindowDialog):

    def Start( self, *args, **kwargs):
        self.thumb = kwargs.get("thumbnail")
        self.thumb, self.url = self.thumb.split("|")
        self.thumb = self.thumb.replace("small/", "originals/")
        self.escudo = kwargs.get("escudo")
        self.fonts = kwargs.get("fuentes")

        data = httptools.downloadpage(self.url).data
        self.img = "http:" + scrapertools.find_single_match(data, '<img src="([^"]+)" (?:title="[^"]+" alt="[^"]+"|alt="[^"]+" title="[^"]+") class="galerie-bild"')
        if "/images/galerie_bg.jpg" in self.img:
            self.img = self.img.replace("http:", "http://www.transfermarkt.es")
            self.img2 = "http:" + scrapertools.find_single_match(data, '<img src="([^"]+)" (?:title="[^"]+" alt="[^"]+"|alt="[^"]+" title="[^"]+") class="galerie-bild-fallback"')

        datos = []
        data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","", data)
        patron = 'class="posrela">.*?>([^<]+)</td></tr></table>.*?>.*?>([^<]+)</td>.*?src="([^"]+)".*?>(?:<br /><img src="([^"]+)"|)' \
                 '.*?>([^<]+)</td>.*?>([^<]+)</td>.*?>([^<]+)</td>.*?src="([^"]+)".*?>([^<]+)</td>.*?class="rechts hauptlink">([^<]+)<span(.*?)</span>'
        matches = scrapertools.find_multiple_matches(data, patron)
        for pos, edad, bandera, bandera2, altura, pie, fichado, antes, contrato, valor, flecha in matches:
            bandera = "http:"+bandera.replace("verysmall/","small/")
            if bandera2:
                bandera2 = "http:"+bandera2.replace("verysmall/","small/")
            antes = "http:"+antes.replace("verysmall/","medium/")
            if "green-arrow-ten" in flecha:
                flecha = "http://i.imgur.com/0g5VoWq.png"
            elif "red-arrow-ten" in flecha:
                flecha = "http://i.imgur.com/drFwxm4.png"
            elif "grey-block-ten" in flecha:
                flecha = "http://i.imgur.com/QtLf50y.png"
            datos.append([pos, edad, bandera, bandera2, altura, pie, fichado, antes, contrato, valor, flecha])

        self.setCoordinateResolution(0)
        # Imagen de fondo, escudo y jugador (botón para cerrar) de la galería o retrato
        # Primer if: fondo predefinido más retrato o imagen completa
        if self.img != "http:":
            if "/images/galerie_bg.jpg" in self.img:
                self.background = xbmcgui.ControlButton(455, 240, 1140, 820, '', 'Windows/DialogBack.png', 'Windows/DialogBack.png')
                self.addControl(self.background)
                self.addControl(xbmcgui.ControlImage(470, 260, 1110, 680, self.img))
                self.addControl(xbmcgui.ControlImage(920, 420, 420, 340, self.escudo))
                self.addControl(xbmcgui.ControlImage(868, 468, 204, 234, "http://i.imgur.com/xzAKeUV.png"))
                self.addControl(xbmcgui.ControlImage(870, 470, 200, 230, self.img2))
            else:
                self.background = xbmcgui.ControlButton(455, 240, 1140, 820, '', 'Windows/DialogBack.png', 'Windows/DialogBack.png')
                self.addControl(self.background)
                self.addControl(xbmcgui.ControlImage(470, 260, 1110, 680, self.img))
                self.addControl(xbmcgui.ControlImage(477, 285, 170, 160, self.escudo))
            if datos:
                self.addControl(xbmcgui.ControlImage(470, 940, 1110, 90, "http://i.imgur.com/Yk2dNuS.png"))
                for pos, edad, bandera, bandera2, altura, pie, fichado, antes, contrato, valor, flecha in datos:
                    fade = xbmcgui.ControlFadeLabel(475, 985, 210, 30, self.fonts["12"], "0xFF000000", 0x00000002)
                    self.addControl(fade)
                    fade.addLabel("[B]"+pos+"[/B]")
                    fade = xbmcgui.ControlFadeLabel(700, 990, 125, 30, self.fonts["10"], "0xFF000000", 0x00000002)
                    self.addControl(fade)
                    fade.addLabel(edad)
                    if bandera2:
                        self.addControl(xbmcgui.ControlImage(845,982,40,22, bandera))
                        self.addControl(xbmcgui.ControlImage(845,1007,40,22, bandera2))
                    else:
                        self.addControl(xbmcgui.ControlImage(845,990,40,30, bandera))
                    self.addControl(xbmcgui.ControlLabel(905,990,70,30,altura, self.fonts["10"], "0xFF000000"))
                    self.addControl(xbmcgui.ControlLabel(975,990,100,30,pie, self.fonts["10"], "0xFF000000",'',0x00000002))
                    fade = xbmcgui.ControlFadeLabel(1077,990,117,30, self.fonts["10"], "0xFF000000", 0x00000002)
                    self.addControl(fade)
                    fade.addLabel(fichado)
                    self.addControl(xbmcgui.ControlImage(1200,980,60,50, antes))
                    self.addControl(xbmcgui.ControlLabel(1270,990,130,30,contrato, self.fonts["10"], "0xFF000000", '', 0x00000002))
                    fade = xbmcgui.ControlFadeLabel(1430,990,120,30, self.fonts["10"], "0xFF000000", 0x00000001)
                    self.addControl(fade)
                    fade.addLabel(valor)
                    self.addControl(xbmcgui.ControlImage(1555,992,20,24,flecha))
        else:
            self.background = xbmcgui.ControlButton(455, 605, 400, 345, '', 'Windows/DialogBack.png', 'Windows/DialogBack.png')
            self.addControl(self.background)
            self.addControl(xbmcgui.ControlImage(470, 620, 370, 315, self.thumb))

        self.doModal()
        return

    def onClick(self, id):
        # Boton Cancelar y [X]
        if id == self.background.getId():
            global window_thumb
            window_thumb.close()
            del window_thumb

    def onAction(self, action):
        if action == 100 or action == 10 or action == 92 or action == 110:
            global window_thumb
            window_thumb.close()
            del window_thumb


class Club(xbmcgui.WindowXMLDialog):
    botones = []
    jornada1 = []
    jornada1_match = []
    jornada2 = []
    jornada2_match = []
    clasifi = []
    arrow_left1 = 0
    arrow_left2 = 0
    arrow_right1 = 0
    arrow_right2 = 0
    botones_focus = []
    focus = -1
    
    

    def Start(self, data, name, escudo, caption, equipo=None, url="", season="", camiseta="", fonts=""):
        # Capturamos los parametros
        self.caption = caption
        self.fonts = fonts
        self.url = url
        self.equipo = equipo
        self.camiseta = camiseta

        if self.url and not data:
            data = httptools.downloadpage(self.url).data
            self.data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","", data)
        else:
            self.data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","", data)
        self.escudo = escudo.replace("small/", "originals/")
        if not self.escudo:
            self.escudo = "http:"+scrapertools.find_single_match(self.data, '<div class="headerfoto">.*?src="([^"]+)"')
            self.escudo = self.escudo.replace("normal/", "originals/")

        self.name = name
        if not self.name:
            self.name = scrapertools.find_single_match(self.data, '<div class="headerfoto">.*?src=.*?alt="([^"]+)"')

        if season:
            self.caption += self.name + " - Temporada " + season.replace("Temp. ", "")
        else:
            self.caption += self.name + " - Temporada Actual"
        
        self.fanart = "http://i.imgur.com/R5sgUt6.jpg"

        # Url para fotos de jugadores en botón plantilla
        self.galeria = "http://www.transfermarkt.es"+scrapertools.find_single_match(self.data, '<a href="([^"]+)"><div class="kartei-button second-kartei kartei-number-3">')
        # Extraemos la info de la tabla cabecera
        try:
            bloque = scrapertools.find_single_match(self.data, '<div class="dataBottom">(.*?)<div class="dataBild">')
            datos = scrapertools.find_multiple_matches(bloque, '<span class="dataItem">(.*?)</span><span class="dataValue">(.*?)</span>')
            self.datos1 = []
            self.datos2 = []
            for title, value in datos:
                value = re.sub(r'>([\d\.]+ Asientos)', r'> \1', value)
                value = scrapertools.htmlclean(value)
                title = "[B]"+title + "[/B]   [COLOR dimgray]" + value + "[/COLOR]"
                if len(self.datos1) < 4:
                    self.datos1.append(title)
                else:
                    self.datos2.append(title)
            valor_total = scrapertools.find_single_match(data, '<div class="dataMarktwert">.*?>(.*?)</span>')
            if valor_total:
                valor_total = scrapertools.htmlclean(valor_total)
                self.datos2.append("[B]Valor de mercado total:[/B]  [COLOR dimgray]%s[/COLOR]" % valor_total)
        except:
            pass

        # Imagenes y numero de copas si los hay
        try:
            bloque = scrapertools.find_single_match(self.data, '<div class="dataErfolge hide-for-small">(.*?)<span class="dataErfolgMore">')
            datos = scrapertools.find_multiple_matches(bloque, 'src="([^"]+)".*?<span class="dataErfolgAnzahl">([^<]+)<')
            self.titulos = []
            for imagen, number in datos:
                imagen = imagen.replace("header/", "medium/")
                self.titulos.append(["http:"+imagen, number+"x"])
        except:
            pass

        # Extrae la info de partidos
        try:
            bloque = scrapertools.find_single_match(self.data, '<ul class="begegnungenVereinSlider slider-list">(.*?)</ul>')
            datos = scrapertools.find_multiple_matches(bloque, '<a title="([^"]+)".*?<a title="([^"]+)".*?br />([^<]+)<.*?href="([^"]+)".*?src="([^"]+)".*?alt="([^"]+)".*?<div class="ergebnis">.*?href="([^"]+)".*?>(.*?)<.*?href="([^"]+)".*?src="([^"]+)".*?alt="([^"]+)"')
            self.jornada1 = []
            self.jornada1_match = []
            self.jornada2 = []
            self.jornada2_match = []
            for liga, jornada, fecha, url1, escudo1, name1, url_match, result, url2, escudo2, name2 in datos:
                url1 = "http://www.transfermarkt.es" + url1
                url2 = "http://www.transfermarkt.es" + url2
                url_match = "http://www.transfermarkt.es" + url_match
                escudo1 = "http:"+escudo1.replace("normquad/", "originals/")
                escudo2 = "http:"+escudo2.replace("normquad/", "originals/")
                if result != "-:-":
                    self.jornada1.append([liga + "  -  " + jornada, fecha+"s"])
                    self.jornada1_match.append([escudo1, name1, result, escudo2, name2, url1, url2, url_match])
                else:
                    self.jornada2.append([liga + "  -  " + jornada, fecha+"s"])
                    self.jornada2_match.append([escudo1, name1, result, escudo2, name2, url1, url2, url_match])
        except:
            pass

        # Recuadro balance de temporadas
        try:
            self.balance = []
            bloque = scrapertools.find_single_match(self.data, '<div class="table-header">(Balance de temporada.*?)</div>.*?tbody>(.*?)</tbody>')
            self.head_balance = bloque[0]
            patron = 'href=.*?>([^<]+)</a></td><td class="rechts">(.*?)</td>'
            matches = scrapertools.find_multiple_matches(bloque[1], patron)
            for torneo, puesto in matches:
                if "<img src=" in puesto:
                    thumb = "http:"+scrapertools.find_single_match(puesto, 'src="([^"]+)"').replace("tiny/", "medium/")
                    puesto = "Campeón"
                else:
                    thumb = ""
                torneo = "[B]"+torneo+"[/B]"
                puesto = puesto.replace("Platz", "Plaza")
                self.balance.append([torneo, puesto, thumb])
        except:
            pass

        # Tabla de clasificacion
        try:
            self.header_tabla, bloque = scrapertools.find_single_match(self.data, '<div class="table-header">(Zona.*?)</div>(.*?)</table>')
            patron = '<td style="background-color:(?:#([^"]+)"|").*?>([^<]+)<.*?href="([^"]+)".*?src="([^"]+)"' \
                     '.*?href.*?>(.*?)</a>.*?<td class="zentriert">(.*?)</td>.*?>(.*?)</td>.*?>(\d+)'
            datos = scrapertools.find_multiple_matches(bloque, patron)
            self.clasifi = []
            for color, posicion, url, imagen, equipo, partidos, ventaja, puntos in datos:
                url = "http://www.transfermarkt.es" + url
                imagen = "http:"+imagen.replace("tiny/", "medium/")
                posicion = posicion.rjust(2)
                ventaja = ventaja.rjust(2)
                partidos = partidos.rjust(2)
                puntos = puntos.rjust(2)
                if color:
                    color = "0xFF" + color.upper()
                self.clasifi.append(([color, posicion, imagen, equipo, partidos, ventaja, puntos, url]))
        except:
            pass

        # Máximo goleador
        try:
            self.goleador = []
            patron = 'Máximos goleadores </div>.*?src="([^"]+)" title="([^"]+)".*?' \
                     '<td class="zentriert">(\d+)</td>.*?<td.*?>(\d+)</td><td.*?>(\d+)</td>'
            src, name, part, goles, asist = scrapertools.find_single_match(self.data, patron)
            src = "http:"+src.replace("small/", "medium/")
            self.goleador.append([src, "[B]"+name+"[/B]", part, goles, asist])
        except:
            pass

        # Recuadro para seleccionar temporadas
        self.items_temp = []
        self.selected = 0
        try:
            bloque = scrapertools.find_single_match(self.data, '<td>Elegir temporada</td>(.*?)</select>')
            temps = scrapertools.find_multiple_matches(bloque, '<option(.*?)value="([^"]+)">(.*?)</option>')
            i = 0
            for select, value, text in temps:
                if "selected" in select:
                    self.selected = i
                if not "saison" in self.url:
                    url_temp = self.url + "?saison_id=" + value
                else:
                    url_temp = self.url.rsplit("=",1)[0] + "="+value
                self.items_temp.append(["Temp. "+text, url_temp])
                i += 1
        except:
            pass

        # Recuadro entrenadores
        self.entrenador_datos = []
        try:
            bloque = scrapertools.find_single_match(self.data, '<p class="text">(?:<span>|)(?:Entrenador|Cuerpo técnico)(.*?)</ul>')
            bloque2 = scrapertools.find_multiple_matches(bloque, '<li class="slider-list">(.*?)</li>')
            for b in bloque2:
                patron = 'src="([^"]+)" title="([^"]+)".*?<div class="container-zusatzinfo">(.*?src="([^"]+)".*?)(?:<div class="container-zusatzinfo">(.*?)<div class="clearer">|<div class="clearer">)'
                matches = scrapertools.find_multiple_matches(b, patron)
                for thumb, name, info, country, partidos in matches:
                    thumb = "http:" + thumb
                    country = "http:" + country.replace("tiny/", "originals/")
                    info = info.replace("<br />", "\n")
                    info = scrapertools.remove_htmltags(info)
                    try:
                        if partidos:
                            partidos = partidos.replace("Balance de temporada</td>", "").replace("</td>", ": ")
                            partidos = scrapertools.remove_htmltags(partidos)
                            partidos = partidos.split(": ")[:-1]
                            stats = ""
                            for i, p in enumerate(partidos):
                                if i >= 0 and i <= len(partidos)/2 - 1:
                                    stats += "[B]"+p + ":[/B] " + partidos[(len(partidos)/2) + i]+"| "
                                
                            info += "\n"+stats
                    except:
                        pass
                    info = info.split("\n")
                    self.entrenador_datos.append([thumb, "[B]"+name+"[/B]", info, country])
        except:
            pass

        self.doModal()
        return

    def onInit(self):
        self.setCoordinateResolution(0)
        # Ponemos el foco
        self.setFocus(self.getControl(10003))

        # Ponemos el título y las imagenes
        self.addControl(xbmcgui.ControlLabel(343,195,1369,29,"[B]"+self.caption+"[/B]", self.fonts["12"], "0xFFFFA500", '', 0x00000002))
        self.addControl(xbmcgui.ControlImage(313,232,1458,716,self.fanart, 0, '0xFFFFFFFF'))
        
        self.botones_focus = []
        # Datos del club
        self.addControl(xbmcgui.ControlImage(320, 236, 1165, 258, 'http://i.imgur.com/nFGpvXl.png'))
        self.addControl(xbmcgui.ControlLabel(350, 244, 400, 20, "[B]"+self.name+"[/B]", self.fonts["12"], '0xFF000000'))
        escudo_header = xbmcgui.ControlImage(325, 284, 145, 157, self.escudo)
        self.addControl(escudo_header)
        escudo_header.setAnimations([('conditional', 'effect=rotatex start=300% end=360% time=1500 tween=bounce condition=true',)])

        i = 0
        for text in self.datos1:
            suma = 290 + i
            self.textbox1 = xbmcgui.ControlFadeLabel(570, suma, 350, 25, self.fonts["10"], '0xFF000000')
            self.addControl(self.textbox1)
            self.textbox1.addLabel(text)
            i += 28
        i = 0
        for text in self.datos2:
            suma = 290 + i
            self.textbox1 = xbmcgui.ControlFadeLabel(980, suma, 440, 25, self.fonts["10"], '0xFF000000')
            self.addControl(self.textbox1)
            self.textbox1.addLabel(text)
            i += 28

        # Fotitos de las copas
        i = 0
        for imagen, number in self.titulos:
            suma = 325 + i
            copa = xbmcgui.ControlButton(suma, 450, 40, 40, '', imagen, imagen)
            self.addControl(copa)
            copa.setAnimations([('focus','effect=zoom center='+str(suma+15)+',485 end=190% tween=elastic',)])
            self.addControl(xbmcgui.ControlLabel(suma+40, 467, 35, 40, number, self.fonts["10"], '0xFF000000'))
            i += 84

        # Botones temporada
        self.arribalist = 0
        self.abajolist = 0
        if self.items_temp:
            path_image = os.path.join(config.get_runtime_path(), 'resources', 'skins', 'Default', 'media', 'MatchWindow')        
            self.addControl(xbmcgui.ControlLabel(1514, 236, 170, 25, "[B]Temporadas[/B]", self.fonts["12"], '0xFF000000'))
            self.lista_temp = xbmcgui.ControlList(1515, 270, 160, 150, self.fonts["10"], '0xFF000000', 'MatchWindow/ItemNoFocus.png', 'MatchWindow/ItemFocus.png', '0xFF2E9AFE', 0, 0, 1, 0, 25, 0, 0x00000004)
            self.addControl(self.lista_temp)
            for item in self.items_temp:
                self.lista_temp.addItem(item[0])
            self.lista_temp.selectItem(self.selected)
            self.setFocus(self.lista_temp)
            self.botones_focus.insert(0, self.lista_temp)
            if len(self.items_temp) > 1:
                self.arribalist = xbmcgui.ControlButton(1676, 270, 30, 30, '', os.path.join(path_image, 'spinUp-Focus.png'), os.path.join(path_image, 'spinUp-noFocus.png'))
                self.addControl(self.arribalist)
                self.abajolist = xbmcgui.ControlButton(1676, 362, 30, 30, '', os.path.join(path_image, 'spinDown-Focus.png'), os.path.join(path_image, 'spinDown-noFocus.png'))
                self.addControl(self.abajolist)

        # Botón plantilla jugadores
        self.plantilla = xbmcgui.ControlButton(1510, 420, 230, 60, '', 'http://i.imgur.com/szeKHwA.png', 'http://i.imgur.com/szeKHwA.png')
        self.addControl(self.plantilla)
        self.plantilla.setAnimations([('conditional','effect=slide start=-800,20 delay=700 time=700 condition=true tween=back',),('focus','effect=rotate start=-270 end=-360 center=auto time=2000 tween=elastic reversible=false',)])
        self.botones_focus.insert(1, self.plantilla)

        # Recuadro balance temporada (no aparece en la actual)
        if self.balance:
            self.addControl(xbmcgui.ControlImage(1460, 498, 310, 70, "http://i.imgur.com/y5ATSGd.png"))
            fade = xbmcgui.ControlFadeLabel(1465, 503, 300, 30, self.fonts["12"], "0xFF000000")
            self.addControl(fade)
            fade.addLabel("[B]"+self.head_balance+"[/B]")
            i = 0
            for torneo, puesto, thumb in self.balance:
                suma = 568 + i
                self.addControl(xbmcgui.ControlImage(1460, suma, 310, 30, "http://i.imgur.com/YsODgtr.png"))
                fade1 = xbmcgui.ControlFadeLabel(1462, suma, 170, 30, self.fonts["10"], "0xFF000000")
                self.addControl(fade1)
                fade1.addLabel(torneo)
                if thumb:
                    fade2 = xbmcgui.ControlFadeLabel(1647, suma, 90, 30, self.fonts["10"], "0xFF000000", 0x00000001)
                    self.addControl(fade2)
                    fade2.addLabel(puesto)
                    self.addControl(xbmcgui.ControlImage(1739, suma, 30, 29, thumb))
                else:
                    fade2 = xbmcgui.ControlFadeLabel(1652, suma, 118, 30, self.fonts["10"], "0xFF000000", 0x00000001)
                    self.addControl(fade2)
                    fade2.addLabel(puesto)                        
                i += 30

        # Recuadro entrenadores/cuerpo tecnico
        self.botones_entrenador = []
        self.index_tecnico = 0
        if self.entrenador_datos:
            self.addControl(xbmcgui.ControlImage(1460, 750, 305, 195, "http://i.imgur.com/HrGJENI.png"))
            if len(self.entrenador_datos) > 1:
                self.prev_tecnico = xbmcgui.ControlButton(1465, 765, 20, 25, '', "http://i.imgur.com/wlZhSct.png", "http://i.imgur.com/wlZhSct.png")
                self.addControl(self.prev_tecnico)
                self.prev_tecnico.setAnimations([('focus','effect=zoom center=auto end=120%',)])
                self.prev_tecnico.setVisible(False)
                self.botones_focus.insert(2, self.prev_tecnico)
                self.next_tecnico = xbmcgui.ControlButton(1740, 765, 20, 25, '', "http://i.imgur.com/u5lRPOi.png", "http://i.imgur.com/u5lRPOi.png")
                self.addControl(self.next_tecnico)
                self.next_tecnico.setAnimations([('focus','effect=zoom center=auto end=120%',)])
                self.botones_focus.insert(2, self.next_tecnico)
            count = 0
            for thumb, name, info, country in self.entrenador_datos:
                img1 = xbmcgui.ControlImage(1463, 815, 82, 122, thumb)
                lbl1 = xbmcgui.ControlFadeLabel(1495, 760, 230, 20, self.fonts["12"], "0xFF258faf", 0x00000002)
                lbl2 = xbmcgui.ControlLabel(1554, 800, 150, 20, "[B]Nacionalidad: [/B]", self.fonts["10"], "0xFF000000")
                pais = xbmcgui.ControlImage(1710, 805, 30, 20, country)
                labels = []
                i = 0
                for line in info:
                    suma = 830 + i
                    lbinfo = xbmcgui.ControlFadeLabel(1554, suma, 210, 20, self.fonts["10"], "0xFF000000")
                    labels.append([lbinfo, line])
                    i += 22
                if count == 0:
                    self.addControl(img1)
                    self.addControl(lbl1)
                    lbl1.addLabel(name)
                    self.addControl(lbl2)
                    self.addControl(pais)
                    for label, line in labels:
                        self.addControl(label)
                        label.addLabel(line)
                self.botones_entrenador.append([img1, lbl1, lbl2, pais, labels, name])
                count += 1

        # Clasificacion
        if self.clasifi:
            self.addControl(xbmcgui.ControlImage(900, 498, 556, 380, 'http://i.imgur.com/tVpjjaI.png'))
            fadelabel = xbmcgui.ControlFadeLabel(940, 523, 520, 40, self.fonts["12"], '0xFF000000', 0x00000002)
            self.addControl(fadelabel)
            fadelabel.addLabel("[B]"+self.header_tabla+"[/B]")
            i = 0
            count = 0
            self.equipos_tabla = []
            self.botones = []
            for color, pos, img, equipo, part, vent, punt, url in self.clasifi:
                suma = 616 + i
                if color:
                    label_color = xbmcgui.ControlImage(904, suma-3, 43, 36, 'http://i.imgur.com/9SilWAJ.png', 0, color)
                    self.addControl(label_color)
                self.addControl(xbmcgui.ControlLabel(912, suma, 25, 25, pos, self.fonts["10"], '0xFF000000', '', 0x00000002))
                bt1 = xbmcgui.ControlButton(948, suma-4, 35, 35, '', img, img)
                self.addControl(bt1)
                bt1.setAnimations([('conditional', 'effect=rotate start=220% end=360% time=2500 condition=true',), ('focus', 'effect=zoom start=80% end=120%',)])
                self.botones.append(bt1)
                self.botones_focus.insert(4, bt1)
                fadelabel = xbmcgui.ControlFadeLabel(992, suma+2, 183, 35, font=self.fonts["10"], textColor='0xFF000000')
                self.addControl(fadelabel)
                fadelabel.addLabel("[B]"+equipo+"[/B]")
                fadelabel.setAnimations([('conditional', 'effect=rotate start=220% end=360% time=2500 condition=true',)])
                self.addControl(xbmcgui.ControlLabel(1223, suma+1, 25, 35, part, self.fonts["10"], '0xFF000000', '', 0x00000002))
                self.addControl(xbmcgui.ControlLabel(1323, suma+1, 25, 35, vent, self.fonts["10"], '0xFF000000', '', 0x00000002))
                self.addControl(xbmcgui.ControlLabel(1398, suma+1, 25, 35, punt, self.fonts["10"], '0xFF000000', '', 0x00000002))
                i += 38
                count += 1
                self.equipos_tabla.append(url)

        # Maximo goleador
        if self.goleador:
            self.addControl(xbmcgui.ControlImage(900,883,556,60, "http://i.imgur.com/dnwTAJv.png"))
            for src, name, part, goles, asist in self.goleador:
                self.addControl(xbmcgui.ControlImage(901,884,59,59,self.goleador[0][0]))
                fadelabel = xbmcgui.ControlFadeLabel(975,915,250,30, self.fonts["10"], "0xFF000000", 0x00000002)
                self.addControl(fadelabel)
                fadelabel.addLabel(self.goleador[0][1])
                self.addControl(xbmcgui.ControlLabel(1263,915, 40, 30, self.goleador[0][2], self.fonts["10"], "0xFF000000", '', 0x00000002))
                self.addControl(xbmcgui.ControlLabel(1333,915, 40, 30, self.goleador[0][3], self.fonts["10"], "0xFF000000", '', 0x00000002))
                self.addControl(xbmcgui.ControlLabel(1403,915, 40, 30, self.goleador[0][4], self.fonts["10"], "0xFF000000", '', 0x00000002))

        # Cuadro partido anterior
        self.controles1 = []
        self.equipos1 = []
        self.match = []
        self.button_matchs = {}
        if self.jornada1 and self.jornada1_match:
            for i in range(0, len(self.jornada1)):
                im1 = xbmcgui.ControlImage(320, 498, 570, 213, 'http://i.imgur.com/IgC4D90.png')
                lb1 = xbmcgui.ControlFadeLabel(450, 496, 320, 20, self.fonts["10"], '0xFF000000', 0x00000002)
                lb2 = xbmcgui.ControlLabel(440, 518, 340, 20, self.jornada1[i][1], self.fonts["10"], '0xFF000000', '', 0x00000002)
                self.button_matchs[str(i)] = xbmcgui.ControlButton(570, 603, 80, 40, "[B]"+self.jornada1_match[i][2]+"[/B]", font=self.fonts["24"], alignment=0x00000002, textColor='0xFF000000', noFocusTexture='', focusTexture='', focusedColor='0xFF2E9AFE')
                self.botones_focus.insert(4, self.button_matchs[str(i)])
                self.match.append([self.jornada1_match[i][7], self.jornada1_match[i][0], self.jornada1_match[i][1], self.jornada1_match[i][3], self.jornada1_match[i][4], self.jornada1_match[i][2]])
                lb3 = xbmcgui.ControlFadeLabel(332, 680, 220, 25, self.fonts["12"], '0xFF000000')
                if self.jornada1_match[i][1] != self.name:
                    equipo1 = xbmcgui.ControlButton(360, 559, 140, 125, '', self.jornada1_match[i][0], self.jornada1_match[i][0])
                    self.botones_focus.insert(4, equipo1)
                    self.equipos1.append([equipo1, self.jornada1_match[i][0], self.jornada1_match[i][1], self.jornada1_match[i][5]])
                else:
                    im2 = xbmcgui.ControlImage(360, 559, 140, 125, self.jornada1_match[i][0])
                    
                lb4 = xbmcgui.ControlFadeLabel(660, 680, 220, 25, self.fonts["12"], '0xFF000000', 0x00000001)
                if self.jornada1_match[i][4] != self.name:
                    equipo1 = xbmcgui.ControlButton(710, 559, 140, 125, '', self.jornada1_match[i][3], self.jornada1_match[i][3])
                    self.botones_focus.insert(5, equipo1)
                    self.equipos1.append([equipo1, self.jornada1_match[i][3], self.jornada1_match[i][4], self.jornada1_match[i][6]])
                else:
                    im2 = xbmcgui.ControlImage(710, 559, 140, 125, self.jornada1_match[i][3])
                self.controles1.append([lb1, lb2, im2, lb3, "[COLOR steelblue]"+self.jornada1_match[i][1]+"[/COLOR]", self.button_matchs[str(i)], lb4, "[COLOR firebrick]"+self.jornada1_match[i][4]+"[/COLOR]", equipo1, self.jornada1[i][0]])
                if i == len(self.jornada1)-1:
                    self.addControl(im1)
                    self.addControl(lb1)
                    lb1.addLabel(self.jornada1[i][0])
                    self.addControl(lb2)
                    self.addControl(self.button_matchs[str(i)])
                    self.addControl(lb3)
                    lb3.addLabel("[COLOR steelblue]"+self.jornada1_match[i][1]+"[/COLOR]")
                    self.addControl(im2)
                    self.addControl(lb4)
                    lb4.addLabel("[COLOR firebrick]"+self.jornada1_match[i][4]+"[/COLOR]")
                    self.addControl(equipo1)
                    equipo1.setAnimations([('focus', 'effect=zoom center=auto end=120%',)])

            self.arrow_left1 = xbmcgui.ControlButton(335, 493, 90, 60, '', "http://i.imgur.com/dUNqG1l.png", "http://i.imgur.com/dUNqG1l.png")
            self.addControl(self.arrow_left1)
            self.arrow_left1.setAnimations([('conditional', 'effect=zoom start=100% end=120% time=800 loop=true reversible=false condition=Control.HasFocus('+str(self.arrow_left1.getId())+')',)])
            self.botones_focus.insert(4, self.arrow_left1)
            self.arrow_right1 = xbmcgui.ControlButton(795, 493, 90, 60, '', "http://i.imgur.com/sfuXWBB.png", "http://i.imgur.com/sfuXWBB.png")
            self.addControl(self.arrow_right1)
            self.arrow_right1.setAnimations([('conditional', 'effect=zoom start=100% end=120% time=800 loop=true reversible=false condition=Control.HasFocus('+str(self.arrow_right1.getId())+')',)])
            self.arrow_right1.setVisible(False)
            self.botones_focus.insert(8, self.arrow_right1)
            self.index_anterior = len(self.controles1) - 1

        self.controles2 = []
        self.equipos2 = []
        self.match2 = []
        self.button_matchs2 = {}
        len_botones_focus = len(self.botones_focus)-len(self.botones)
        # Cuadro partido siguiente
        if self.jornada2 and self.jornada2_match:
            for i in range(0, len(self.jornada2)):
                im1 = xbmcgui.ControlImage(320, 728, 570, 213, 'http://i.imgur.com/IgC4D90.png')
                lb1 = xbmcgui.ControlFadeLabel(450, 726, 320, 20,  self.fonts["10"], '0xFF000000', 0x00000002)
                lb2 = xbmcgui.ControlLabel(440, 748, 340, 20, self.jornada2[i][1], self.fonts["10"], '0xFF000000', '', 0x00000002)

                self.button_matchs2[str(i)] = xbmcgui.ControlButton(570, 831, 80, 40, "[B]"+self.jornada2_match[i][2]+"[/B]", font=self.fonts["24"], alignment=0x00000002, textColor='0xFF000000', noFocusTexture='', focusTexture='', focusedColor='0xFF2E9AFE')
                self.botones_focus.insert(len_botones_focus, self.button_matchs2[str(i)])
                self.match2.append([self.jornada2_match[i][7], self.jornada2_match[i][0], self.jornada2_match[i][1], self.jornada2_match[i][3], self.jornada2_match[i][4], self.jornada2_match[i][2]])
                lb3 = xbmcgui.ControlFadeLabel(332, 910, 220, 25, self.fonts["12"], '0xFF000000')
                if self.jornada2_match[i][1] != self.name:
                    equipo2 = xbmcgui.ControlButton(360, 789, 140, 125, '', self.jornada2_match[i][0], self.jornada2_match[i][0])
                    self.botones_focus.insert(len_botones_focus, equipo2)
                    self.equipos2.append([equipo2, self.jornada2_match[i][0], self.jornada2_match[i][1], self.jornada2_match[i][5]])
                else:
                    im2 = xbmcgui.ControlImage(360, 789, 140, 125, self.jornada2_match[i][0])
                lb4 = xbmcgui.ControlFadeLabel(660, 910, 220, 25, self.fonts["12"], '0xFF000000', 0x00000001)
                if self.jornada2_match[i][4] != self.name:
                    equipo2 = xbmcgui.ControlButton(710, 789, 140, 125, '', self.jornada2_match[i][3], self.jornada2_match[i][3])
                    self.botones_focus.insert(len_botones_focus, equipo2)
                    self.equipos2.append([equipo2, self.jornada2_match[i][3], self.jornada2_match[i][4], self.jornada2_match[i][6]])
                else:
                    im2 = xbmcgui.ControlImage(710, 789, 140, 125, self.jornada2_match[i][3])

                self.controles2.append([lb1, lb2, im2, lb3, "[COLOR steelblue]"+self.jornada2_match[i][1]+"[/COLOR]", self.button_matchs2[str(i)], lb4, "[COLOR firebrick]"+self.jornada2_match[i][4]+"[/COLOR]", equipo2, self.jornada2[i][0]])
                if i == 0:
                    self.addControl(im1)
                    self.addControl(lb1)
                    lb1.addLabel(self.jornada2[i][0])
                    self.addControl(lb2)
                    self.addControl(self.button_matchs2[str(i)])
                    self.addControl(lb3)
                    lb3.addLabel("[COLOR steelblue]"+self.jornada2_match[i][1]+"[/COLOR]")
                    self.addControl(im2)
                    self.addControl(lb4)
                    lb4.addLabel("[COLOR firebrick]"+self.jornada2_match[i][4]+"[/COLOR]")
                    self.addControl(equipo2)
                    equipo2.setAnimations([('focus', 'effect=zoom center=auto end=120%',)])
                    
            self.arrow_left2 = xbmcgui.ControlButton(335, 723, 90, 60, '', "http://i.imgur.com/dUNqG1l.png", "http://i.imgur.com/dUNqG1l.png")
            self.addControl(self.arrow_left2)
            self.arrow_left2.setAnimations([('conditional', 'effect=zoom start=100% end=120% time=800 loop=true reversible=false condition=Control.HasFocus('+str(self.arrow_left2.getId())+')',)])
            self.arrow_left2.setVisible(False)
            self.botones_focus.insert(len_botones_focus, self.arrow_left2)
            self.arrow_right2 = xbmcgui.ControlButton(795, 723, 90, 60, '', "http://i.imgur.com/sfuXWBB.png", "http://i.imgur.com/sfuXWBB.png")
            self.addControl(self.arrow_right2)
            self.arrow_right2.setAnimations([('conditional', 'effect=zoom start=100% end=120% time=800 loop=true reversible=false condition=Control.HasFocus('+str(self.arrow_right2.getId())+')',)])
            self.botones_focus.insert(len_botones_focus+1, self.arrow_right2)
            self.index_posterior = 0

    def onDoubleClick(self, id):
        try:
            if id == self.lista_temp.getId():
                index = self.lista_temp.getSelectedPosition()
                global window_club
                window_club.close()
                del window_club
                window_club = Club('ClubWindow.xml', config.get_runtime_path())
                window_club.Start('', self.name, self.escudo, "Información del ", self.equipo, self.items_temp[index][1], self.items_temp[index][0], "", fonts=self.fonts)
        except:
            pass


    def onClick(self, id):
        global window_club
        global window_liga
        global window_match
        global window_players
        # Boton Cancelar y [X]
        if id == 10003:
            window_club.close()
            del window_club

        # Botón plantilla
        try:
            if id == self.plantilla.getId():
                window_players = Players("SportsWindow.xml", config.get_runtime_path())
                window_players.Start(self.data, self.galeria, self.escudo, self.camiseta, self.equipo, fonts=self.fonts)
        except:
            pass

        # Botones arriba/abajo temporada
        try:
            if id == self.arribalist.getId():
                pos = self.lista_temp.getSelectedPosition()
                if  pos > 0:
                    self.lista_temp.selectItem(pos-1)
        except:
            pass

        try:
            if id == self.abajolist.getId():
                pos = self.lista_temp.getSelectedPosition()
                if  pos < len(self.items_temp) - 1:
                    self.lista_temp.selectItem(pos+1)
        except:
            pass

        # Flecha anterior y siguiente entrenadores
        try:
            if id == self.prev_tecnico.getId():
                for i, c in enumerate(self.botones_entrenador):
                    if i == self.index_tecnico:
                        self.removeControls([c[0], c[1], c[2], c[3]])
                        for control, line in c[4]:
                            self.removeControl(control)
                    
                self.index_tecnico -= 1
                if self.index_tecnico == 0:
                    self.prev_tecnico.setVisible(False)
                if self.index_tecnico == len(self.botones_entrenador) - 2:
                    self.next_tecnico.setVisible(True)
                for i, c in enumerate(self.botones_entrenador):
                    if i == self.index_tecnico:
                        self.addControls([c[0], c[1], c[2], c[3]])
                        c[1].addLabel(c[5])
                        for c, line in c[4]:
                            self.addControl(c)
                            c.addLabel(line)
        except:
            pass

        try:
            if id == self.next_tecnico.getId():
                for i, c in enumerate(self.botones_entrenador):
                    if i == self.index_tecnico:
                        self.removeControls([c[0], c[1], c[2], c[3]])
                        for control, line in c[4]:
                            self.removeControl(control)
                    
                self.index_tecnico += 1
                if self.index_tecnico == len(self.botones_entrenador) - 1:
                    self.next_tecnico.setVisible(False)
                if self.index_tecnico == 1:
                    self.prev_tecnico.setVisible(True)
                for i, c in enumerate(self.botones_entrenador):
                    if i == self.index_tecnico:
                        self.addControls([c[0], c[1], c[2], c[3]])
                        c[1].addLabel(c[5])
                        for c, line in c[4]:
                            self.addControl(c)
                            c.addLabel(line)
        except:
            pass
        
        # Flecha anterior y siguiente partidos ya jugados
        try:
            if id == self.arrow_left1.getId():
                for i, c in enumerate(self.controles1):
                    if i == self.index_anterior:
                        self.removeControls([c[0], c[1], c[2], c[3], c[5], c[6], c[8]])
                self.index_anterior -= 1
                for i, c in enumerate(self.controles1):
                    if i == self.index_anterior:
                        self.addControls([c[0], c[1], c[2], c[3], c[5], c[6], c[8]])
                        c[0].addLabel(c[9])
                        c[3].addLabel(c[4])
                        c[6].addLabel(c[7])
                        c[8].setAnimations([('focus', 'effect=zoom center=auto end=120%',)])
                if self.index_anterior == 0:
                    self.arrow_left1.setVisible(False)
                if self.index_anterior == len(self.controles1) - 2:
                    self.arrow_right1.setVisible(True)
                self.arrow_right1.setAnimations([('conditional', 'effect=zoom start=100% end=120% time=800 loop=true reversible=false condition=Control.HasFocus('+str(self.arrow_right1.getId())+')',)])
        except:
            pass

        try:
            if id == self.arrow_right1.getId():
                for i, c in enumerate(self.controles1):
                    if i == self.index_anterior:
                        self.removeControls([c[0], c[1], c[2], c[3], c[5], c[6], c[8]])
                self.index_anterior += 1
                for i, c in enumerate(self.controles1):
                    if i == self.index_anterior:
                        self.addControls([c[0], c[1], c[2], c[3], c[5], c[6], c[8]])
                        c[0].addLabel(c[9])
                        c[3].addLabel(c[4])
                        c[6].addLabel(c[7])
                        c[8].setAnimations([('focus', 'effect=zoom center=auto end=120%',)])
                if self.index_anterior == 1:
                    self.arrow_left1.setVisible(True)

                if self.index_anterior == len(self.controles1) - 1:
                    self.arrow_right1.setVisible(False)
        except:
            pass

        # Flecha anterior y siguiente próximos partidos
        try:
            if id == self.arrow_right2.getId():
                for i, c in enumerate(self.controles2):
                    if i == self.index_posterior:
                        self.removeControls([c[0], c[1], c[2], c[3], c[5], c[6], c[8]])
                self.index_posterior += 1
                for i, c in enumerate(self.controles2):
                    if i == self.index_posterior:
                        self.addControls([c[0], c[1], c[2], c[3], c[5], c[6], c[8]])
                        c[0].addLabel(c[9])
                        c[3].addLabel(c[4])
                        c[6].addLabel(c[7])
                        c[8].setAnimations([('focus', 'effect=zoom center=auto end=120%',)])
                if self.index_posterior == 1:
                    self.arrow_left2.setVisible(True)

                if self.index_posterior == len(self.controles2) - 1:
                    self.arrow_right2.setVisible(False)
        except:
            pass

        try:
            if id == self.arrow_left2.getId():
                for i, c in enumerate(self.controles2):
                    if i == self.index_posterior:
                        self.removeControls([c[0], c[1], c[2], c[3], c[5], c[6], c[8]])
                self.index_posterior -= 1
                for i, c in enumerate(self.controles2):
                    if i == self.index_posterior:
                        self.addControls([c[0], c[1], c[2], c[3], c[5], c[6], c[8]])
                        c[0].addLabel(c[9])
                        c[3].addLabel(c[4])
                        c[6].addLabel(c[7])
                        c[8].setAnimations([('focus', 'effect=zoom center=auto end=120%',)])
                if self.index_posterior == 0:
                    self.arrow_left2.setVisible(False)
                if self.index_posterior == len(self.controles2) - 2:
                    self.arrow_right2.setVisible(True)
        except:
            pass

        # Abre nueva ventana de club al pinchar en los escudos de los próximos/anteriores partidos
        try:
            if id == self.equipos1[self.index_anterior][0].getId():
                window_club.close()
                del window_club
                window_club = Club("ClubWindow.xml", config.get_runtime_path())
                window_club.Start('', self.equipos1[self.index_anterior][2], self.equipos1[self.index_anterior][1], "Información del ", url=self.equipos1[self.index_anterior][3], fonts=self.fonts)
        except:
            pass
        try:
            if id == self.equipos2[self.index_posterior][0].getId():
                window_club.close()
                del window_club
                window_club = Club("ClubWindow.xml", config.get_runtime_path())
                window_club.Start('', self.equipos2[self.index_posterior][2], self.equipos2[self.index_posterior][1], "Información del ", url=self.equipos2[self.index_posterior][3], fonts=self.fonts)
        except:
            pass

        # Abre nueva ventana de club al pinchar en los escudos de la tabla de clasificación
        try:
            for i, equipo in enumerate(self.equipos_tabla):
                if self.botones[i].getId() == id:
                    window_club.close()
                    del window_club
                    window_club = Club("ClubWindow.xml", config.get_runtime_path())
                    window_club.Start('', '', '', "Información del ", url=self.equipos_tabla[i], fonts=self.fonts)
        except:
            pass
            
        # Botones ventana de partido anterior/siguiente
        try:
            for i, matches in enumerate(self.match):
                if self.button_matchs[str(i)].getId() == id:
                    window_match = Match("MatchWindow.xml", config.get_runtime_path())
                    window_match.Start(self.match[i][0], self.match[i][1], self.match[i][2], self.match[i][3], self.match[i][4], self.match[i][5], fonts=self.fonts)
        except:
            pass
        try:
            for i, matches in enumerate(self.match2):
                if self.button_matchs2[str(i)].getId() == id:
                    window_match = Match("MatchWindow.xml", config.get_runtime_path())
                    window_match.Start(self.match2[i][0], self.match2[i][1], self.match2[i][2], self.match2[i][3], self.match2[i][4], self.match2[i][5], fonts=self.fonts)
        except:
            pass

    def onAction(self, action):
        ACTION_MOVE_DOWN = 4
        ACTION_MOVE_LEFT = 1
        ACTION_MOVE_RIGHT = 2
        ACTION_MOVE_UP = 3
        global window_club
        if action == 92 or action == 10 or action == 110:
            window_club.close()
            del window_club

        try:
            if action == ACTION_MOVE_RIGHT or (action == ACTION_MOVE_DOWN and self.getFocus() != self.lista_temp):
                if self.focus < len(self.botones_focus)-1:
                    self.focus += 1
                    while True:
                        id_focus = str(self.botones_focus[self.focus].getId())
                        if xbmc.getCondVisibility('[Control.IsVisible('+id_focus+')]'):
                            self.setFocus(self.botones_focus[self.focus])
                            break
                        self.focus += 1
                        if self.focus == len(self.botones_focus):
                            break
        except:
            pass
        try:
            if action == ACTION_MOVE_LEFT or (action == ACTION_MOVE_UP and self.getFocus() != self.lista_temp):
                if self.focus > 0:
                    self.focus -= 1
                    while True:
                        id_focus = str(self.botones_focus[self.focus].getId())
                        if xbmc.getCondVisibility('[Control.IsVisible('+id_focus+')]'):
                            self.setFocus(self.botones_focus[self.focus])
                            break
                        self.focus -= 1
                        if self.focus < 0:
                            break
        except:
            pass
        try:
            if action == 7 and self.getFocus() == self.lista_temp:
                index = self.lista_temp.getSelectedPosition()
                window_club.close()
                del window_club
                window_club = Club('ClubWindow.xml', config.get_runtime_path())
                window_club.Start('', self.name, self.escudo, "Información del ", self.equipo, self.items_temp[index][1], self.items_temp[index][0], "", fonts=self.fonts)
        except:
            pass

    def onFocus(self, id):
        try:
            if id == self.abajolist.getId():
                self.setFocus(self.lista_temp)
        except:
            pass

        try:
            if id == self.arribalist.getId():
                self.setFocus(self.lista_temp)
        except:
            pass


class Match(xbmcgui.WindowXMLDialog):
    thumbs = {}
    songs = []
    indice_song = 0
    loop = False
    botones = []
    focus = -1
    

    def Start(self, url, escudo1, name1, escudo2, name2, result, data="", fonts=""):
        # Capturamos los parametros
        self.caption = name1 + " " + result + " " + name2
        self.escudo1 = escudo1
        self.escudo2 = escudo2
        self.escudo1_mini = escudo1.replace("originals/", "smallquad/")
        self.escudo2_mini = escudo2.replace("originals/", "smallquad/")
        self.name1 = name1
        self.name2 = name2
        self.result = result
        self.fonts = fonts
        
        self.fanart = "http://i.imgur.com/R5sgUt6.jpg"
        if not data:
            data = httptools.downloadpage(url).data
            self.data = re.sub(r"\n|\r|\t|\s{2}","", data).replace("&nbsp;", " ")
            if not self.data:
                url = url.replace("ticker/begegnung/live/", "/spielbericht/index/spielbericht/")
                data = httptools.downloadpage(url).data
                self.data = re.sub(r"\n|\r|\t|\s{2}","", data).replace("&nbsp;", " ")
        else:
            self.data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","", data).replace("&nbsp;", " ")
        
        self.once_local = []
        self.once_visit = []
        self.form_local = ""
        self.form_visit = ""
        try:
            bloques = scrapertools.find_multiple_matches(self.data, '(Formación inicial:.*?)</div>(.*?)(?:<div class="unterueberschrift|<div class="clearer">)')
            for i, bloque in enumerate(bloques):
                if i == 0:
                    self.form_local = bloque[0]
                else:
                    self.form_visit = bloque[0]
                matches = scrapertools.find_multiple_matches(bloque[1], 'id="([^"]+)"><div class="(?:rn|ersatz-rn)".*?>(\d+)</div>.*?href=.*?>(.*?)</a>(.*?)(?:aufstellung|</tr>)')
                for id, number, name, actions in matches:
                    images = []
                    if not url:
                        eventos = scrapertools.find_single_match(self.data, 'spielverlauf_events=(.*?)last_event_id')
                        type = scrapertools.find_multiple_matches(eventos, '"subtype":"(gelb|gelbrot|rot|tor|wechsel)","tore_h":"[^"]*","tore_g":"[^"]*","spieler_id_1":"([^"]+)","spieler_id_2":"([^"]+)"')
                        for t, id1, id2 in type:
                            if t == "gelb" and id1 == id:
                                actions += "icon-gelbekarte|"
                            elif t == "gelbrot" and id1 == id:
                                actions += "icon-gelbrotekarte|"
                            elif t == "rot" and id1 == id:
                                actions += "icon-rotekarte|"
                            elif t == "tor" and id1 == id:
                                actions += "icon-tor-|"
                            elif t == "wechsel" and id1 == id:
                                actions += "icon-auswechslung|"
                            elif t == "wechsel" and id2 == id:
                                actions += "icon-einwechslung|"

                    if "icon-gelbekarte" in actions:
                        images.append("http://i.imgur.com/JdckMon.png")
                    if "icon-gelbrotekarte" in actions:
                        images.append("http://i.imgur.com/dN77hTk.png")
                    if "icon-rotekarte" in actions:
                        images.append("http://i.imgur.com/FWr3lIK.png")
                    if "icon-tor-" in actions:
                        count = actions.count("icon-tor-")
                        for j in range(0, count):
                            images.append("http://i.imgur.com/FvujX4h.png")
                    if "icon-eigentor" in actions:
                        count = actions.count("icon-eigentor")
                        for j in range(0, count):
                            images.append("http://i.imgur.com/EjG33NU.png")
                    if "icon-auswechslung" in actions:
                        images.append("http://i.imgur.com/0iNjFr1.png")
                    if "icon-einwechslung" in actions:
                        images.append("http://i.imgur.com/3c4JEcY.png")

                    name = scrapertools.unescape(name)
                    if i == 0:
                        self.once_local.append([number, name, images])
                    else:
                        self.once_visit.append([number, name, images])
        except:
            pass

        # 2ª manera de buscar alineaciones si no se han encontrado antes y existe la pestaña formación
        data_form = ""
        if not self.once_local:
            try:
                url_formacion = scrapertools.find_single_match(self.data, 'href="([^"]+)" class="megamenu">Formación</a>')
                if url_formacion:
                    data_form = httptools.downloadpage("http://www.transfermarkt.es"+url_formacion).data
                    data_form = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","", data_form)
                    bloques = scrapertools.find_multiple_matches(data_form, '(Formación inicial.*?)</div>(.*?)<div class="table-footer">')
                    banquillo = scrapertools.find_multiple_matches(data_form, '</a>Banquillo</div>(.*?)<div class="table-footer">')
                    for i, bloque in enumerate(bloques):
                        try:
                            bloque1 = bloque[1] + banquillo[i]
                        except:
                            bloque1 = bloque[1]
                        if i == 0:
                            self.form_local = bloque[0]
                        else:
                            self.form_visit = bloque[0]
                        matches = scrapertools.find_multiple_matches(bloque1, '<div class="rn_nummer">([^<]+)</div>.*?<a title="([^"]+)".*?</a>(.*?)</tr>')
                        for number, name, actions in matches:
                            images = []
                            if "sb-sprite sb-gelb" in actions:
                                images.append("http://i.imgur.com/JdckMon.png")
                            if "icon-gelbrotekarte" in actions:
                                images.append("http://i.imgur.com/dN77hTk.png")
                            if "sb-sprite sb-rot" in actions:
                                images.append("http://i.imgur.com/FWr3lIK.png")
                            if "sb-sprite sb-tor" in actions:
                                count = actions.count("sb-sprite sb-tor")
                                for j in range(0, count):
                                    images.append("http://i.imgur.com/FvujX4h.png")
                            if "sb-sprite sb-eigentor" in actions:
                                count = actions.count("icon-eigentor")
                                for j in range(0, count):
                                    images.append("http://i.imgur.com/EjG33NU.png")
                            if "sb-sprite sb-aus" in actions:
                                images.append("http://i.imgur.com/0iNjFr1.png")
                            if "sb-sprite sb-ein" in actions:
                                images.append("http://i.imgur.com/3c4JEcY.png")

                            name = scrapertools.unescape(name)
                            if i == 0:
                                self.once_local.append([number, name, images])
                            else:
                                self.once_visit.append([number, name, images])
            except:
                pass

        # 3ª manera de extraer la info de alineaciones cuando hay menos datos disponibles (suele ser en partidos muy antiguos)
        if not self.once_local:
            try:
                bloques = scrapertools.find_single_match(self.data, '<h2>Formación</h2>(.*?)</table>(.*?)</table>')
                bloques = [bloques[0], bloques[1]]
                for i, b in enumerate(bloques):
                    matches = scrapertools.find_multiple_matches(b, '<b>([^<]+)</b></td>(.*?)</td>')
                    for puesto, nombre in matches:
                        if puesto != "Entrenador":
                            nombre = scrapertools.remove_htmltags(nombre)
                            if "," in nombre:
                                nombres = nombre.split(", ")
                                for name in nombres:
                                    if i == 0:
                                        self.once_local.append(["-", name, ""])
                                    else:
                                        self.once_visit.append(["-", name, ""])
                            else:
                                if i == 0:
                                    self.once_local.append(["-", nombre, ""])
                                else:
                                    self.once_visit.append(["-", nombre, ""])
            except:
                pass
                            
        # Datos de entrenadores, se busca de dos maneras y en la página principal del partido
        # o en la de formación si se ha cargado anteriormente
        self.manager1 = ""
        self.manager2 = ""
        try:
            entrenadores = scrapertools.find_multiple_matches(self.data, '<div>Entrenador:</div></td><td><a title="([^"]+)"')
            if entrenadores:
                self.manager1 = scrapertools.unescape(entrenadores[0])
                self.manager2 = scrapertools.unescape(entrenadores[1])
        except:
            pass
        if not self.manager1:
            if data_form:
                entrenadores = scrapertools.find_multiple_matches(data_form, 'Entrenador</div>(.*?)</table>')
                
                    
            else:
                entrenadores = scrapertools.find_multiple_matches(self.data, 'Entrenador</b>(.*?)</table>')
            if entrenadores:
                if re.search(r'(?i)>\d+ años', entrenadores[0]):
                    self.manager1 = re.sub(r'(?i)(\d+ años)', r' - \1', entrenadores[0])
                else:
                    self.manager1 = entrenadores[0]
                self.manager1 = scrapertools.unescape(scrapertools.remove_htmltags(self.manager1))
                if re.search(r'(?i)>\d+ años', entrenadores[1]):
                    self.manager2 = re.sub(r'(?i)(\d+ años)', r' - \1', entrenadores[1])
                else:
                    self.manager2 = entrenadores[1]
                self.manager2 = scrapertools.unescape(scrapertools.remove_htmltags(self.manager2))

        # Recuadro de goles si los hay para partidos ya concluidos
        goles = scrapertools.find_single_match(self.data, '<h2>Goles(.*?)</ul>')
        self.goles_l = []
        self.goles_v = []
        if goles:
            matches = scrapertools.find_multiple_matches(goles, '<li class="sb-aktion-([^"]+)">.*?"sb-aktion-spielstand"><b>(.*?)</b>.*?src="([^"]+)".*?<div class="sb-aktion-aktion">(.*?)<div class="sb-aktion-wappen">')
            for equipo, result, thumb, plot in matches:
                plot = plot.replace("<br />", "\n")
                plot = scrapertools.remove_htmltags(plot)
                plot = scrapertools.unescape(plot)
                thumb = "http:"+thumb
                if equipo == "heim":
                    self.goles_l.append([thumb, "[B]"+result+"[/B]", plot])
                else:
                    self.goles_v.append([thumb, "[B]"+result+"[/B]", plot])

        # Sección gráfica de estadísticas, datos del estadio y del árbitro en caso de que los haya
        self.datos_partido_l = []
        self.datos_partido_v = []
        self.estadio_datos = ""
        self.arbitro_datos = ""
        self.estadio_thumb = ""
        self.arbitro_thumb = ""
        self.arbitro_countrythumb = ""
        self.arbitro_country = ""
        url_estadistica = scrapertools.find_single_match(self.data, '<a name="SubNavi" href="([^"]+)" class="megamenu">Estadística</a>')
        if url_estadistica:
            url_estadistica = "http://www.transfermarkt.es"+url_estadistica
            data_stat = httptools.downloadpage(url_estadistica).data
            data_stat = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","", data_stat)

            try:
                self.posesion2, self.posesion1 = scrapertools.find_single_match(data_stat, "renderTo':'yw1.*?'name'.*?'y':(\d+).*?'name'.*?'y':(\d+)")
            except:
                pass
            try:
                matches = scrapertools.find_multiple_matches(data_stat, '<li class="sb-statistik-heim">.*?style="width: (\d+).*?#([^;]+);".*?class="sb-statistik-zahl".*?color:\s*#([^;]+);">(\d+)<.*?<li class="sb-statistik-gast">.*?style="width: (\d+).*?#([^;]+);".*?class="sb-statistik-zahl".*?color:\s*#([^;]+);">(\d+)<')
                if matches:
                    for longitud1, color1, color2, valor1, longitud2, color3, color4, valor2 in matches:
                        color1 = "0xFF" + color1
                        if len(color2) == 3:
                            color2 = "0xFF" + color2 + color2
                        else:
                            color2 = "0xFF" + color2
                        color3 = "0xFF" + color3
                        if len(color4) == 3:
                            color4 = "0xFF" + color4 + color4
                        else:
                            color4 = "0xFF" + color4
                        valor1 = valor1.rjust(2)
                        valor2 = valor2.rjust(2)
                        self.datos_partido_l.append([longitud1, color1, valor1, color2])
                        self.datos_partido_v.append([longitud2, color3, valor2, color4])
            except:
                pass
            
            estadio = scrapertools.find_single_match(data_stat, '<th>Estadio:</th>.*?href.*?>(.*?)</a>')
            if estadio:
                self.estadio_datos += "[B]Estadio: [/B]" + estadio+"\n"
            asistencia = scrapertools.find_single_match(data_stat, '<th>Asistencia:</th><td.*?>(.*?)</td>')
            if asistencia:
                self.estadio_datos += "[B]Asistencia: [/B]" + scrapertools.remove_htmltags(asistencia)+"\n"
            capacidad = scrapertools.find_single_match(data_stat, '<th>Capacidad disponible:</th><td>(.*?)</td>')
            if capacidad:
                self.estadio_datos += "[B]Capacidad: [/B]" + capacidad
            self.estadio_thumb = scrapertools.find_single_match(data_stat, 'data-reveal-id="stadionbild"><img src="([^"]+)"')
            if self.estadio_thumb:
                self.estadio_thumb = "http:" + self.estadio_thumb
            else:
                self.estadio_thumb = "http://i.imgur.com/rRxOXK4.png"

            self.arbitro_thumb = scrapertools.find_single_match(data_stat, '<div class="person-box-foto"><img src="([^"]+)"')
            if self.arbitro_thumb:
                self.arbitro_thumb = "http:" + self.arbitro_thumb.replace("mediumfotos/", "spielerfotos/")
            else:
                self.arbitro_thumb = "http://i.imgur.com/1UMBKvT.jpg"

            arbitro_name = scrapertools.find_single_match(data_stat, '<div class="person-box-info">.*?href.*?>(.*?)</a>')
            if arbitro_name:
                self.arbitro_datos += "[B]Árbitro: [/B]" + arbitro_name
            arbitro_edad = scrapertools.find_single_match(data_stat, '<th>Edad:</th><td>(.*?)</td>')
            if arbitro_edad:
                self.arbitro_datos += "\n[B]Edad: [/B]" + arbitro_edad
            try:
                self.arbitro_countrythumb, self.arbitro_country = scrapertools.find_single_match(data_stat, '<th>Nacionalidad:</th><td><img src="([^"]+)" title="([^"]+)"')
                self.arbitro_countrythumb = "http:"+self.arbitro_countrythumb.replace("tiny/", "originals/")
            except:
                pass

        # Datos del partido: se muestra siempre si el evento no ha terminado, si ya
        # lo ha hecho y no hay estadísticas y si las hay se muestra al pulsar el botón "Datos/Live"
        self.datos_alt = []
        try:
            patron = 'sb-spielbericht-head.*?alt="([^"]+)".*?class="(?:sb|sbk)-datum.*?>(.*?)<(?:/div>|/p>)' \
                     '.*?p class="(?:sb|sbk)-zusatzinfos.*?>(.*?)</p>'
            matches = scrapertools.find_multiple_matches(self.data, patron)
            for torneo, fecha, info in matches:
                fecha = fecha.replace("<br />", "\n").replace(" hora", " horas")
                fecha = scrapertools.remove_htmltags(fecha)
                info = info.replace("<br />", "\n")
                info = scrapertools.remove_htmltags(info)
                info = fecha + "\n" + info.replace("Árbitro: abrir", "Árbitro: ------")
                self.datos_alt.append([torneo, info.split("\n")])
        except:
            pass

        # Extrae los mensajes del partido en vivo
        self.ticker_live = []
        self.data_t = ""
        try:
            bloque = scrapertools.find_single_match(self.data, 'tickernachrichten=(.*?\}\]);')
            if not bloque:
                url_ticker = scrapertools.find_single_match(self.data, 'href="([^"]+)" class="megamenu">Ticker en vivo</a>')
                if url_ticker:
                    self.data_t = httptools.downloadpage("http://www.transfermarkt.es"+url_ticker).data
                    self.data_t = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","", self.data_t).replace("&nbsp;", " ")
                    bloque = scrapertools.find_single_match(self.data_t, 'tickernachrichten=(.*?\}\]);')
            bloque = jsontools.load_json(bloque)
            for child in bloque:
                type = child["type"]
                if child["spielminute"] != "0":
                    label1 = "[B]Minuto "+child["spielminute"]+":[/B] "
                    label2 = child["message"]
                else:
                    label1 = ""
                    label2 = child["message"]
                if type == "start":
                    thumb = "http://i.imgur.com/hOBjZtI.png"
                elif type == "goal":
                    thumb = "http://i.imgur.com/PFzWFvv.png"
                elif type == "yellow card":
                    thumb = "http://i.imgur.com/CqPQWoc.png"
                elif "end" in type:
                    thumb = "http://i.imgur.com/Jmf3SO0.png"
                elif type == "substitution":
                    thumb = "http://i.imgur.com/Oo3sKyQ.png"
                elif type == "secondyellow card":
                    thumb = "http://i.imgur.com/kVNMxPb.png"
                elif type == "red card":
                    thumb = "http://i.imgur.com/1mfKDIN.png"
                elif "penalti a favor" in label2:
                    thumb = "http://i.imgur.com/tZ8bfp2.png"
                else:
                    thumb = ""
                self.ticker_live.insert(0, [label1, label2, thumb])
        except:
            pass
        
        # Si no ha encontrado alineaciones y ha buscado en la página del evento en vivo,
        # se vuelve a buscar en ella para sacarlas
        if not self.once_local and self.data_t:
            try:
                bloques = scrapertools.find_multiple_matches(self.data_t, '(Formación inicial:.*?)</div>(.*?)(?:<div class="unterueberschrift|<div class="clearer">)')
                for i, bloque in enumerate(bloques):
                    if i == 0:
                        self.form_local = bloque[0]
                    else:
                        self.form_visit = bloque[0]
                    matches = scrapertools.find_multiple_matches(bloque[1], 'id="([^"]+)"><div class="(?:rn|ersatz-rn)".*?>(\d+)</div>.*?href=.*?>(.*?)</a>(.*?)(?:aufstellung|</tr>)')
                    for id, number, name, actions in matches:
                        images = []
                        eventos = scrapertools.find_single_match(self.data_t, 'spielverlauf_events=(.*?)last_event_id')
                        type = scrapertools.find_multiple_matches(eventos, '"subtype":"(gelb|gelbrot|rot|tor|wechsel)","tore_h":"[^"]*","tore_g":"[^"]*","spieler_id_1":"([^"]+)","spieler_id_2":"([^"]+)"')
                        for t, id1, id2 in type:
                            if t == "gelb" and id1 == id:
                                actions += "icon-gelbekarte|"
                            elif t == "gelbrot" and id1 == id:
                                actions += "icon-gelbrotekarte|"
                            elif t == "rot" and id1 == id:
                                actions += "icon-rotekarte|"
                            elif t == "tor" and id1 == id:
                                actions += "icon-tor-|"
                            elif t == "wechsel" and id1 == id:
                                actions += "icon-auswechslung|"
                            elif t == "wechsel" and id2 == id:
                                actions += "icon-einwechslung|"

                        if "icon-gelbekarte" in actions:
                            images.append("http://i.imgur.com/JdckMon.png")
                        if "icon-gelbrotekarte" in actions:
                            images.append("http://i.imgur.com/dN77hTk.png")
                        if "icon-rotekarte" in actions:
                            images.append("http://i.imgur.com/FWr3lIK.png")
                        if "icon-tor-" in actions:
                            count = actions.count("icon-tor-")
                            for j in range(0, count):
                                images.append("http://i.imgur.com/FvujX4h.png")
                        if "icon-eigentor" in actions:
                            count = actions.count("icon-eigentor")
                            for j in range(0, count):
                                images.append("http://i.imgur.com/EjG33NU.png")
                        if "icon-auswechslung" in actions:
                            images.append("http://i.imgur.com/0iNjFr1.png")
                        if "icon-einwechslung" in actions:
                            images.append("http://i.imgur.com/3c4JEcY.png")

                        name = scrapertools.unescape(name)
                        if i == 0:
                            self.once_local.append([number, name, images])
                        else:
                            self.once_visit.append([number, name, images])
            except:
                pass

        self.doModal()
        return

    def onInit(self):
        self.setCoordinateResolution(0)
        # Ponemos el foco en el boton de cerrar [X]
        self.setFocus(self.getControl(10003))
        self.botones.append(self.getControl(10003))

        # Ponemos el título y las imagenes
        self.addControl(xbmcgui.ControlLabel(169,98,1216,29,"[B]"+self.caption+"[/B]", self.fonts["12"], "0xFFFFA500", '', 0x00000002))
        self.addControl(xbmcgui.ControlImage(138,147,1309,858,self.fanart, 0, '0xFFFFFFFF'))

        # Tabla de estadisticas
        if self.datos_partido_l:
            self.addControl(xbmcgui.ControlImage(536, 205, 500, 790, "http://i.imgur.com/Gw570rs.png"))
            self.addControl(xbmcgui.ControlImage(565, 250, 120, 120, self.escudo1))
            self.addControl(xbmcgui.ControlImage(885, 250, 120, 120, self.escudo2))
            self.addControl(xbmcgui.ControlLabel(725, 295, 100, 50, self.posesion1, "font13_title", '0xFF000000'))
            self.addControl(xbmcgui.ControlLabel(820, 295, 100, 50, self.posesion2, "font13_title", '0xFF000000'))

            # Lado izquierdo tabla
            medidas = [417, 493, 568, 644, 719, 795, 872, 947]
            for i, stat in enumerate(self.datos_partido_l):
                suma = medidas[i]
                
                valor = (int(stat[0])*217)/100
                if valor < 50:
                    valor = 50
                ancho = valor
                posx = 559 + 217 - valor
                if valor < 100:
                    posx = posx - 3
                self.addControl(xbmcgui.ControlImage(posx, suma, ancho, 40, "http://i.imgur.com/4YOGwmA.png", colorDiffuse=stat[1]))
                self.addControl(xbmcgui.ControlImage(posx-20, suma, 40, 40, "http://i.imgur.com/SlpAgz6.png"))
                self.addControl(xbmcgui.ControlImage(posx-16, suma+3, 32, 35, self.escudo1_mini))
                self.addControl(xbmcgui.ControlLabel(744, suma-3, 40, 40, stat[2], self.fonts["10"], stat[3], '', 0x00000004))

            # Lado derecho tabla
            for i, stat in enumerate(self.datos_partido_v):
                suma = medidas[i]
                
                valor = (int(stat[0])*217)/100
                posx = 797
                if valor < 50:
                    valor = 50
                ancho = valor
                if valor < 100:
                    posx = posx + 4
                
                self.addControl(xbmcgui.ControlImage(posx, suma, ancho, 40, "http://i.imgur.com/31Nzp34.png", colorDiffuse=stat[1]))
                self.addControl(xbmcgui.ControlImage(posx+ancho-20, suma, 40, 40, "http://i.imgur.com/SlpAgz6.png"))
                self.addControl(xbmcgui.ControlImage(posx+ancho-16, suma+3, 32, 35, self.escudo2_mini))
                self.addControl(xbmcgui.ControlLabel(811, suma-3, 40, 40, stat[2], self.fonts["10"], stat[3], '', 0x00000004))
            
            self.fondo_hide = xbmcgui.ControlImage(536, 205, 500, 790, "http://i.imgur.com/5fhlHBA.png")
            self.addControl(self.fondo_hide)
            self.fondo_hide.setVisible(False)

        # Datos principales del partido, principalmente para la previa
        suma = 0
        if self.datos_alt:
            fade = xbmcgui.ControlFadeLabel(565, 195, 471,40, self.fonts["16"], "0xFF221c9a")
            labels = []
            i = 0
            for line in self.datos_alt[0][1]:
                suma = 240 + i
                lab = xbmcgui.ControlFadeLabel(565,suma,471,25, self.fonts["12"], "0xFF000000")
                labels.append([lab, line])
                i += 26
            if not suma:
                suma = 430
            else:
                suma += 40
            escudo1 = xbmcgui.ControlImage(565, suma, 120, 120, self.escudo1)
            escudo2 = xbmcgui.ControlImage(885, suma, 120, 120, self.escudo2)
            if self.result:
                resultado = xbmcgui.ControlLabel(760, suma+30, 200, 40, "[B]"+self.result+"[/B]", self.fonts["16"], "0xFFDF0101")
            else:
                resultado = None
            if not self.datos_partido_l:
                self.addControl(fade)
                fade.addLabel(self.datos_alt[0][0])
                for lab, line in labels:
                    self.addControl(lab)
                    lab.addLabel(line)
                self.addControl(escudo1)
                self.addControl(escudo2)
                if self.result:
                    self.addControl(resultado)
            else:
                self.datos_alt_bt = [fade, escudo1, escudo2, resultado, self.datos_alt[0][0], labels]
        
        # Lista de items con los mensajes del partido en vivo
        if self.ticker_live:
            path_image = os.path.join(config.get_runtime_path(), 'resources', 'skins', 'Default', 'media', 'MatchWindow')
            if not suma:
                suma = 510
            else:
                suma += 130
            altura = 1047 - suma
            self.lista = xbmcgui.ControlList(536, suma, 500, altura, self.fonts["10"], '0xFF000000', 'MatchWindow/ItemNoFocus.png', 'MatchWindow/ItemFocus.png', '0xFF2E9AFE', 25, 25, 1, 0, 60, 0, 0x00000004)
            self.addControl(self.lista)
            self.lista.setVisible(False)
            self.botones.append(self.lista)
            for label1, label2, thumb in self.ticker_live:
                item = xbmcgui.ListItem(label1+label2)
                try:
                    item.setArt({"thumb":thumb})
                except:
                    item.setThumbnailImage(thumb)
                self.lista.addItem(item)
            if not self.datos_partido_l:
                self.lista.setVisible(True)

        if self.datos_partido_l and (self.datos_alt or self.ticker_live):
            self.img_stat = xbmcgui.ControlImage(536, 155, 200, 40, "http://i.imgur.com/VBiU06v.png")
            self.addControl(self.img_stat)
            self.btn_stat = xbmcgui.ControlButton(536, 155, 200, 40, 'Estadísticas', "http://i.imgur.com/4vjgkwr.png","",0,0,0x00000002,self.fonts["12"],"0xFFffff00","0xFFffff85")
            self.addControl(self.btn_stat)
            self.botones.append(self.btn_stat)
            self.img_ticker = xbmcgui.ControlImage(836, 155, 200, 40, "http://i.imgur.com/TWyhzcH.png")
            self.addControl(self.img_ticker)
            self.btn_ticker = xbmcgui.ControlButton(836, 155, 200, 40, 'Datos/Live', "http://i.imgur.com/TWyhzcH.png","", 0,0,0x00000002,self.fonts["12"],"0xFF9ae600","0xFFffff85")
            self.addControl(self.btn_ticker)
            self.botones.append(self.btn_ticker)
            self.btn_stat.setEnableCondition('[!Control.IsEnabled('+str(self.btn_ticker.getId())+')]')
            self.btn_ticker.setEnableCondition('[!Control.IsEnabled('+str(self.btn_stat.getId())+')]')
            
        
        # Alineación/Banquillo Local
        if self.form_local:
            fadelabel = xbmcgui.ControlFadeLabel(175, 143, 315, 30, self.fonts["12"], '0xFF000000')
            self.addControl(fadelabel)
            fadelabel.addLabel(self.form_local)
        if self.once_local:
            i = 0
            count = 0
            self.controls_forml = []
            for count, player in enumerate(self.once_local):
                if count == 11:
                    i = 0
                suma = 174 + i
                img1 = xbmcgui.ControlImage(152, suma+8, 40, 25, "http://i.imgur.com/uHF8dDM.png")
                self.addControl(img1)
                lb1 = xbmcgui.ControlLabel(158, suma+4, 32, 20, player[0], self.fonts["10"], alignment=0x00000002)
                self.addControl(lb1)
                fadelabel = xbmcgui.ControlFadeLabel(199, suma+5, 150, 20, self.fonts["10"], '0xFF6E6E6E')
                self.addControl(fadelabel)
                fadelabel.addLabel("[B]"+player[1]+"[/B]")
                if count > 10:
                    self.removeControls([img1, lb1, fadelabel])
                imgs = []
                if player[2]:
                    for j, img in enumerate(player[2]):
                        suma2 = 357 + j*23
                        img2 = xbmcgui.ControlImage(suma2, suma+12, 17, 15, img)
                        if count < 11:
                            self.addControl(img2)
                        imgs.append(img2)
                self.controls_forml.append([img1, lb1, fadelabel, player[1], imgs])
                i += 23
            # Flechas cambio alineación/banquillo
            self.plus = xbmcgui.ControlButton(500, 170, 30, 280,'', "http://i.imgur.com/PE0Fs8r.png", "http://i.imgur.com/PE0Fs8r.png")
            self.addControl(self.plus)
            self.plus.setAnimations([('conditional', 'effect=fade start=20 end=100 time=1200 loop=true reversible=false condition=Control.HasFocus('+str(self.plus.getId())+')',)])
            self.botones.append(self.plus)
            self.minus = xbmcgui.ControlButton(500, 170, 30, 280,'', "http://i.imgur.com/DmuBSvm.png", "http://i.imgur.com/DmuBSvm.png")
            self.botones.append(self.minus)
        if self.manager1:
            fadelabel = xbmcgui.ControlFadeLabel(213,448, 285, 20, self.fonts["10"], '0xFF000000')
            self.addControl(fadelabel)
            fadelabel.addLabel("[B]Entrenador: [/B]"+self.manager1)


        # Recuadro de goles local
        self.goles_thumb = []
        self.next = xbmcgui.ControlButton(167, 735, 320, 25, '', "http://i.imgur.com/jIMWvRE.png", "http://i.imgur.com/jIMWvRE.png")
        self.botones.append(self.next)
        self.prev = xbmcgui.ControlButton(167, 480, 320, 25, '', "http://i.imgur.com/2p5pOar.png", "http://i.imgur.com/2p5pOar.png")
        self.botones.append(self.prev)
        if self.goles_l:
            i = 0
            count = 1
            for thumb, result, plot in self.goles_l:
                suma = 510 + i
                cb = xbmcgui.ControlButton(167, suma+5, 45, 45, '', thumb, thumb)
                self.addControl(cb)
                self.botones.append(cb)
                cb.setAnimations([('focus','effect=zoom start=100% end=120% tween=bounce',)])
                label = xbmcgui.ControlLabel(220, suma+9, 40, 40, result, self.fonts["12"], '0xFF000000')
                self.addControl(label)
                fadelabel = xbmcgui.ControlFadeLabel(264, suma-2, 236, 40, self.fonts["10"], '0xFF000000')
                self.addControl(fadelabel)
                fadelabel.addLabel(plot)
                fadelabel.setScrolling(False)
                line = xbmcgui.ControlImage(169, suma+50, 320, 10, "http://i.imgur.com/Ot6e8Ry.png")
                self.addControl(line)
                line.setVisibleCondition('[!Control.HasFocus('+str(cb.getId())+')]')
                self.goles_thumb.append([cb, label, fadelabel, plot, False, line])
                if count == 4:
                    i = 0
                elif count == 5:
                    i += 55
                    self.removeControls([cb, label, fadelabel, line])
                    self.addControl(self.next)
                    self.next.setAnimations([('conditional', 'effect=fade start=20 end=100 time=1200 loop=true condition=Control.HasFocus('+str(self.next.getId())+')',)])
                elif count > 5:
                    i += 55
                    self.removeControls([cb, label, fadelabel, line])
                elif count == 8:
                    break
                else:
                    i += 55
                count += 1

        # Imagen/Botón de estadio y datos de este
        if self.estadio_thumb:
            self.estadio_thumb = xbmcgui.ControlImage(162, 764, 260, 160, self.estadio_thumb)
            self.addControl(self.estadio_thumb)
            self.estadio_thumb.setAnimations([('conditional', 'effect=fade start=0 end=100 time=2000 condition=true',)])
            # Botones play, stop, anterior y siguiente canticos
            self.suporter = xbmcgui.ControlButton(442, 820, 70, 50, '', "http://i.imgur.com/19nSg15.png", "http://i.imgur.com/pj2BkT0.png")
            self.addControl(self.suporter)
            self.suporter.setVisibleCondition('[!Player.IsInternetStream]')
            self.stop = xbmcgui.ControlButton(442, 820, 70, 50, '', "http://i.imgur.com/61Nc2Km.png", "http://i.imgur.com/i6asmQZ.png")
            self.addControl(self.stop)
            self.stop.setVisibleCondition('[!Control.IsVisible('+str(self.suporter.getId())+')]')
            self.prev_song = xbmcgui.ControlButton(442, 760, 70, 50, '', "http://i.imgur.com/dIiX0xG.png", "http://i.imgur.com/1ns7J4k.png")
            self.addControl(self.prev_song)
            self.prev_song.setVisible(False)
            self.next_song = xbmcgui.ControlButton(442, 880, 70, 50, '', "http://i.imgur.com/dPJTCBi.png", "http://i.imgur.com/WREPdvx.png")
            self.addControl(self.next_song)
            self.next_song.setVisible(False)
            self.botones.append(self.prev_song)
            self.botones.append(self.suporter)
            self.botones.append(self.stop)
            self.botones.append(self.next_song)
            self.no_songs = xbmcgui.ControlImage(442, 820, 70, 50,"http://i.imgur.com/kwjinY9.png")
            self.addControl(self.no_songs)
            self.no_songs.setVisible(False)
        if self.estadio_datos:
            fadelabel = xbmcgui.ControlFadeLabel(162, 925, 300, 160, self.fonts["10"], "0xFF000000")
            self.addControl(fadelabel)
            fadelabel.addLabel(self.estadio_datos)

        # Alineación/Banquillo Visitante
        if self.form_visit:
            fadelabel = xbmcgui.ControlFadeLabel(1071, 143, 320, 30, self.fonts["12"], '0xFF000000')
            self.addControl(fadelabel)
            fadelabel.addLabel(self.form_visit)
        if self.once_visit:
            i = 0
            count = 0
            self.controls_formv = []
            for count, player in enumerate(self.once_visit):
                if count == 11:
                    i = 0
                suma = 174 + i
                img1 = xbmcgui.ControlImage(1048, suma+8, 40, 25, "http://i.imgur.com/uHF8dDM.png")
                self.addControl(img1)
                lb1 = xbmcgui.ControlLabel(1054, suma+4, 32, 20, player[0], self.fonts["10"], alignment=0x00000002)
                self.addControl(lb1)
                fadelabel = xbmcgui.ControlFadeLabel(1095, suma+5, 150, 20, self.fonts["10"], '0xFF6E6E6E')
                self.addControl(fadelabel)
                fadelabel.addLabel("[B]"+player[1]+"[/B]")
                if count > 10:
                    self.removeControls([img1, lb1, fadelabel])
                imgs = []
                if player[2]:
                    for j, img in enumerate(player[2]):
                        suma2 = 1253 + j*23
                        img2 = xbmcgui.ControlImage(suma2, suma+12, 17, 15, img)
                        if count < 11:
                            self.addControl(img2)
                        imgs.append(img2)
                self.controls_formv.append([img1, lb1, fadelabel, player[1], imgs])
                i += 23
            # Flechas cambio alineación/banquillo
            self.plus2 = xbmcgui.ControlButton(1396, 170, 30, 280,'', "http://i.imgur.com/PE0Fs8r.png", "http://i.imgur.com/PE0Fs8r.png")
            self.addControl(self.plus2)
            self.plus2.setAnimations([('conditional', 'effect=fade start=20 end=100 time=1200 loop=true reversible=false condition=Control.HasFocus('+str(self.plus2.getId())+')',)])
            self.botones.append(self.plus2)
            self.minus2 = xbmcgui.ControlButton(1396, 170, 30, 280,'', "http://i.imgur.com/DmuBSvm.png", "http://i.imgur.com/DmuBSvm.png")
            self.botones.append(self.minus2)
        if self.manager2:
            fadelabel = xbmcgui.ControlFadeLabel(1109,448, 285, 20, self.fonts["10"], '0xFF000000')
            self.addControl(fadelabel)
            fadelabel.addLabel("[B]Entrenador: [/B]"+self.manager2)

        # Recuadro de goles visitante
        self.goles_thumb2 = []
        self.next2 = xbmcgui.ControlButton(1071, 735, 320, 25, '', "http://i.imgur.com/jIMWvRE.png", "http://i.imgur.com/jIMWvRE.png")
        self.prev2 = xbmcgui.ControlButton(1071, 480, 320, 25, '', "http://i.imgur.com/2p5pOar.png", "http://i.imgur.com/2p5pOar.png")
        self.botones.append(self.next2)
        self.botones.append(self.prev2)
        if self.goles_v:
            i = 0
            count = 1
            for thumb, result, plot in self.goles_v:
                suma = 510 + i
                cb = xbmcgui.ControlButton(1071, suma+5, 45, 45, '', thumb, thumb)
                self.addControl(cb)
                self.botones.append(cb)
                cb.setAnimations([('focus','effect=zoom start=100% end=120% tween=bounce',)])
                label = xbmcgui.ControlLabel(1122, suma+9, 40, 40, result, self.fonts["12"], '0xFF000000')
                self.addControl(label)
                fadelabel = xbmcgui.ControlFadeLabel(1162, suma-2, 238, 40, self.fonts["10"], '0xFF000000')
                self.addControl(fadelabel)
                fadelabel.addLabel(plot)
                fadelabel.setScrolling(False)
                line = xbmcgui.ControlImage(1073, suma+50, 320, 10, "http://i.imgur.com/Ot6e8Ry.png")
                self.addControl(line)
                line.setVisibleCondition('[!Control.HasFocus('+str(cb.getId())+')]')
                self.goles_thumb2.append([cb, label, fadelabel, plot, False, line])
                if count == 4:
                    i = 0
                elif count == 5:
                    i += 55
                    self.removeControls([cb, label, fadelabel, line])
                    self.addControl(self.next2)
                    self.next2.setAnimations([('conditional', 'effect=fade start=20 end=100 time=1200 loop=true reversible=false condition=Control.HasFocus('+str(self.next2.getId())+')',)])
                elif count > 5:
                    i += 55
                    self.removeControls([cb, label, fadelabel, line])
                elif count == 8:
                    break
                else:
                    i += 55
                count += 1

        # Foto y datos del árbitro
        if self.arbitro_datos:
            self.addControl(xbmcgui.ControlImage(1160, 803, 125, 125, self.arbitro_thumb))
            fadelabel = xbmcgui.ControlFadeLabel(1100, 928, 300, 60, self.fonts["10"], "0xFF000000")
            self.addControl(fadelabel)
            fadelabel.addLabel(self.arbitro_datos)
        if self.arbitro_countrythumb:
            if self.arbitro_datos and "\n" in self.arbitro_datos:
                altura = 976
            else:
                altura = 958
            self.addControl(xbmcgui.ControlLabel(1100, altura, 150, 30, "[B]Nacionalidad: [/B]", self.fonts["10"], "0xFF000000"))
            self.addControl(xbmcgui.ControlImage(1252, altura+4, 25, 20, self.arbitro_countrythumb))
            fadel = xbmcgui.ControlFadeLabel(1280, altura, 125, 20, self.fonts["10"], "0xFF000000")
            self.addControl(fadel)
            fadel.addLabel(self.arbitro_country)

    def onDoubleClick(self, click):
        if click == self.lista.getId():
            texto = ""
            for label1, label2, thumb in self.ticker_live:
                label = "[COLOR red]"+label1+"[/COLOR]"+label2
                texto += label + "\n"
            return xbmcgui.Dialog().textviewer("Evento en detalle", texto)

    def onClick(self, id):
        # Boton Cancelar y [X]
        if id == 10003:
            global window_match
            window_match.close()
            del window_match

        # Botones en el retrato de los goles para activar el texto adjunto
        try:
            for i, cb in enumerate(self.goles_thumb):
                if id == cb[0].getId():
                    fade = cb[2]
                    if cb[4]:
                        fade.setScrolling(False)
                        cb[4] = False
                    else:
                        fade.setScrolling(True)
                        cb[4] = True
        except:
            pass

        try:
            for i, cb in enumerate(self.goles_thumb2):
                if id == cb[0].getId():
                    fade = cb[2]
                    if cb[4]:
                        fade.setScrolling(False)
                        cb[4] = False
                    else:
                        fade.setScrolling(True)
                        cb[4] = True
        except:
            pass

        # Botones previo y anterior cuando hay más de 4 goles en un partido, recuadro local
        try:
            if id == self.next.getId():
                i = 0
                for cb, label, fadelabel, plot, state, line in self.goles_thumb:
                    if i < 4:
                        self.removeControls([cb, label, fadelabel, line])
                    else:
                        self.addControls([cb, label, fadelabel, line])
                        fadelabel.addLabel(plot)
                        fadelabel.setScrolling(False)
                        cb.setAnimations([('focus','effect=zoom start=100% end=120% tween=bounce',)])
                        line.setVisibleCondition('[!Control.HasFocus('+str(cb.getId())+')]')
                    i += 1
                self.removeControl(self.next)
                self.addControl(self.prev)
                self.prev.setAnimations([('conditional', 'effect=fade start=20 end=100 time=1200 loop=true reversible=false condition=Control.HasFocus('+str(self.prev.getId())+')',)])
        except:
            pass

        try:
            if id == self.prev.getId():
                i = 0
                for cb, label, fadelabel, plot, state, line in self.goles_thumb:
                    if i >= 4:
                        self.removeControls([cb, label, fadelabel, line])
                    else:
                        self.addControls([cb, label, fadelabel, line])
                        fadelabel.addLabel(plot)
                        fadelabel.setScrolling(False)
                        cb.setAnimations([('focus','effect=zoom start=100% end=120% tween=bounce',)])
                        line.setVisibleCondition('[!Control.HasFocus('+str(cb.getId())+')]')
                    i += 1
                self.removeControl(self.prev)
                self.addControl(self.next)
                self.next.setAnimations([('conditional', 'effect=fade start=20 end=100 time=1200 loop=true reversible=false condition=Control.HasFocus('+str(self.next.getId())+')',)])
        except:
            pass
        #Recuadro goles visitante
        try:
            if id == self.next2.getId():
                i = 0
                for cb, label, fadelabel, plot, state, line in self.goles_thumb2:
                    if i < 4:
                        self.removeControls([cb, label, fadelabel, line])
                    else:
                        self.addControls([cb, label, fadelabel, line])
                        fadelabel.addLabel(plot)
                        fadelabel.setScrolling(False)
                        cb.setAnimations([('focus','effect=zoom start=100% end=120% tween=bounce',)])
                    i += 1
                self.removeControl(self.next2)
                self.addControl(self.prev2)
                self.prev2.setAnimations([('conditional', 'effect=fade start=20 end=100 time=1200 loop=true reversible=false condition=Control.HasFocus('+str(self.prev2.getId())+')',)])
        except:
            pass

        try:
            if id == self.prev2.getId():
                i = 0
                for cb, label, fadelabel, plot, state, line in self.goles_thumb2:
                    if i >= 4:
                        self.removeControls([cb, label, fadelabel, line])
                    else:
                        self.addControls([cb, label, fadelabel, line])
                        fadelabel.addLabel(plot)
                        fadelabel.setScrolling(False)
                        cb.setAnimations([('focus','effect=zoom start=100% end=120% tween=bounce',)])
                    i += 1
                self.removeControl(self.prev2)
                self.addControl(self.next2)
                self.next2.setAnimations([('conditional', 'effect=fade start=20 end=100 time=1200 loop=true reversible=false condition=Control.HasFocus('+str(self.next2.getId())+')',)])
        except:
            pass

        # Botones para cambiar entre once inicial y banquillo: local
        try:
            if id == self.plus.getId():
                count = 0
                for img1, lb1, fadelabel, text, imgs in self.controls_forml:
                    if count < 11:
                        self.removeControls([img1, lb1, fadelabel])
                        for i in range(0, len(imgs)):
                            self.removeControl(imgs[i])
                    else:
                        self.addControls([img1, lb1, fadelabel])
                        fadelabel.addLabel("[B]"+text+"[/B]")
                        for i in range(0, len(imgs)):
                            self.addControl(imgs[i])
                    count += 1
                self.removeControl(self.plus)
                self.addControl(self.minus)
                self.minus.setAnimations([('conditional', 'effect=fade start=20 end=100 time=1200 loop=true reversible=false condition=Control.HasFocus('+str(self.minus.getId())+')',)])
        except:
            pass

        try:
            if id == self.minus.getId():
                count = 0
                for img1, lb1, fadelabel, text, imgs in self.controls_forml:
                    if count >= 11:
                        self.removeControls([img1, lb1, fadelabel])
                        for i in range(0, len(imgs)):
                            self.removeControl(imgs[i])
                    count += 1
                count = 0
                for img1, lb1, fadelabel, text, imgs in self.controls_forml:
                    if count < 11:
                        self.addControls([img1, lb1, fadelabel])
                        fadelabel.addLabel("[B]"+text+"[/B]")
                        for i in range(0, len(imgs)):
                            self.addControl(imgs[i])
                    count += 1
                self.removeControl(self.minus)
                self.addControl(self.plus)
                self.plus.setAnimations([('conditional', 'effect=fade start=20 end=100 time=1200 loop=true reversible=false condition=Control.HasFocus('+str(self.plus.getId())+')',)])
        except:
            pass
        # Botones para cambiar entre once inicial y banquillo: visitante
        try:
            if id == self.plus2.getId():
                count = 0
                for img1, lb1, fadelabel, text, imgs in self.controls_formv:
                    if count < 11:
                        self.removeControls([img1, lb1, fadelabel])
                        for i in range(0, len(imgs)):
                            self.removeControl(imgs[i])
                    else:
                        self.addControls([img1, lb1, fadelabel])
                        fadelabel.addLabel("[B]"+text+"[/B]")
                        for i in range(0, len(imgs)):
                            self.addControl(imgs[i])
                    count += 1
                self.removeControl(self.plus2)
                self.addControl(self.minus2)
                self.minus2.setAnimations([('conditional', 'effect=fade start=20 end=100 time=1200 loop=true reversible=false condition=Control.HasFocus('+str(self.minus2.getId())+')',)])
        except:
            pass

        try:
            if id == self.minus2.getId():
                count = 0
                for img1, lb1, fadelabel, text, imgs in self.controls_formv:
                    if count >= 11:
                        self.removeControls([img1, lb1, fadelabel])
                        for i in range(0, len(imgs)):
                            self.removeControl(imgs[i])
                    count += 1
                count = 0
                for img1, lb1, fadelabel, text, imgs in self.controls_formv:
                    if count < 11:
                        self.addControls([img1, lb1, fadelabel])
                        fadelabel.addLabel("[B]"+text+"[/B]")
                        for i in range(0, len(imgs)):
                            self.addControl(imgs[i])
                    count += 1
                self.removeControl(self.minus2)
                self.addControl(self.plus2)
                self.plus2.setAnimations([('conditional', 'effect=fade start=20 end=100 time=1200 loop=true reversible=false condition=Control.HasFocus('+str(self.plus2.getId())+')',)])
        except:
            pass

        # Botones para reprodución de cánticos: play, stop, siguiente, anterior
        try:
            if id == self.suporter.getId():
                if xbmc.Player().isPlaying():
                    xbmc.executebuiltin('xbmc.PlayMedia(Stop)')
                    xbmc.executebuiltin('Action(Select)')
                canticos(self, name=self.name1)
        except:
            pass
        try:
            if id == self.stop.getId():
                canticos(self, type="stop")
        except:
            pass
        try:
            if id == self.next_song.getId():
                canticos(self, type="next")
        except:
            pass
        try:
            if id == self.prev_song.getId():
                canticos(self, type="prev")
        except:
            pass

        # Botones cambio entre estadisticas y live
        try:
            if id == self.btn_stat.getId():
                self.btn_ticker.setEnabled(True)
                self.img_ticker.setImage("http://i.imgur.com/TWyhzcH.png")
                self.img_stat.setImage("http://i.imgur.com/VBiU06v.png")
                if self.datos_alt:
                    self.removeControls(self.datos_alt_bt[:3])
                    if self.datos_alt_bt[3]:
                        self.removeControl(self.datos_alt_bt[3])
                    for lab, line in self.datos_alt_bt[5]:
                        self.removeControl(lab)
                self.lista.setVisible(False)
                self.fondo_hide.setVisible(False)
        except:
            pass
        try:
            if id == self.btn_ticker.getId():
                self.btn_ticker.setEnabled(False)
                self.img_ticker.setImage("http://i.imgur.com/FO0VEek.png")
                self.img_stat.setImage("http://i.imgur.com/4vjgkwr.png")
                self.fondo_hide.setVisible(True)
                if self.datos_alt:
                    self.addControls(self.datos_alt_bt[:3])
                    if self.datos_alt_bt[3]:
                        self.addControl(self.datos_alt_bt[3])
                    self.datos_alt_bt[0].addLabel(self.datos_alt_bt[4])
                    for lab, line in self.datos_alt_bt[5]:
                        self.addControl(lab)
                        lab.addLabel(line)
                self.lista.setVisible(True)
        except:
            pass


    def onAction(self, action):
        ACTION_MOVE_DOWN = 4
        ACTION_MOVE_LEFT = 1
        ACTION_MOVE_RIGHT = 2
        ACTION_MOVE_UP = 3

        if action == 92 or action == 10 or action == 110:
            global window_match
            window_match.close()
            del window_match
        try:
            if self.ticker_live:
                if action == ACTION_MOVE_RIGHT or (action == ACTION_MOVE_DOWN and self.getFocus() != self.lista):
                    if self.focus < len(self.botones)-1:
                        self.focus += 1
                        while True:
                            id_focus = str(self.botones[self.focus].getId())
                            if xbmc.getCondVisibility('[Control.IsVisible('+id_focus+')]') and xbmc.getCondVisibility('[Control.IsEnabled('+id_focus+')]'):
                                self.setFocus(self.botones[self.focus])
                                break
                            self.focus += 1
                            if self.focus == len(self.botones):
                                break
            else:
                if action == ACTION_MOVE_RIGHT or action == ACTION_MOVE_DOWN:
                    if self.focus < len(self.botones)-1:
                        self.focus += 1
                        while True:
                            id_focus = str(self.botones[self.focus].getId())
                            if xbmc.getCondVisibility('[Control.IsVisible('+id_focus+')]') and xbmc.getCondVisibility('[Control.IsEnabled('+id_focus+')]'):
                                self.setFocus(self.botones[self.focus])
                                break
                            self.focus += 1
                            if self.focus == len(self.botones):
                                break
        except:
            pass
        try:
            if self.ticker_live:
                if action == ACTION_MOVE_LEFT or (action == ACTION_MOVE_UP and self.getFocus() != self.lista):
                    if self.focus > 0:
                        self.focus -= 1
                        while True:
                            id_focus = str(self.botones[self.focus].getId())
                            if xbmc.getCondVisibility('[Control.IsVisible('+id_focus+')]') and xbmc.getCondVisibility('[Control.IsEnabled('+id_focus+')]'):
                                self.setFocus(self.botones[self.focus])
                                break
                            self.focus -= 1
                            if self.focus < 0:
                                break
            else:
                if action == ACTION_MOVE_LEFT or action == ACTION_MOVE_UP:
                    if self.focus > 0:
                        self.focus -= 1
                        while True:
                            id_focus = str(self.botones[self.focus].getId())
                            if xbmc.getCondVisibility('[Control.IsVisible('+id_focus+')]') and xbmc.getCondVisibility('[Control.IsEnabled('+id_focus+')]'):
                                self.setFocus(self.botones[self.focus])
                                break
                            self.focus -= 1
                            if self.focus < 0:
                                break
        except:
            pass

        try:
            if action == 7 and self.getFocus() == self.lista:
                texto = ""
                for label1, label2, thumb in self.ticker_live:
                    label = "[COLOR red]"+label1+"[/COLOR]"+label2
                    texto += label + "\n"
                return xbmcgui.Dialog().textviewer("Evento en detalle", texto)
        except:
            pass

class Liga(xbmcgui.WindowXMLDialog):
    botones = []
    focus = 0
    count_gol = 5
    count_zamora = 5
    

    def Start(self, url, logo, name, season="", fonts=""):
        #Capturamos los parametros
        self.caption = "Datos de "+name
        if not fonts:
            skin = xbmc.getSkinDir()
            self.fonts = get_fonts(skin)
        else:
            self.fonts = fonts
        self.url = url

        loading = platformtools.dialog_progress("Cargando info de liga...", "Recopilando datos de Transfermarkt")
        loading.update(30, "Consultando partidos y clasificación")
        if season:
            self.caption += " - Temporada " + season
            season = int(self.url.rsplit("=",1)[1])
        else:
            self.caption += " - Temporada Actual"
            season = datetime.datetime.today().year

        self.logo = logo
        self.name = name
        
        self.fanart = "http://i.imgur.com/R5sgUt6.jpg"
        data = httptools.downloadpage(self.url).data
        data = re.sub(r"\n|\r|\t|\s{2}","", data).replace("&nbsp;", " ")
        # Se repara la url por si viene de una redireccion
        url_check = scrapertools.find_single_match(data, '<meta property="og:url" content="([^"]+)"')
        if url_check != self.url:
            self.url = url_check
        
        # Temporadas disponibles para consultar
        self.items_temp = []
        self.selected = 0
        try:
            bloque = scrapertools.find_single_match(data, '<td>Elegir temporada:</td>(.*?)</select>')
            temps = scrapertools.find_multiple_matches(bloque, '<option(.*?)value="([^"]+)">(.*?)</option>')
            i = 0
            for select, value, text in temps:
                if "selected" in select:
                    self.selected = i
                if not "saison" in self.url:
                    url_temp = self.url + "?saison_id=" + value
                else:
                    url_temp = self.url.rsplit("=",1)[0] + "="+value
                self.items_temp.append([text, url_temp])
                i += 1
        except:
            pass

        # Extrae info principal de la liga/copa
        self.datos1 = []
        self.datos2 = []
        try:
            self.bandera = scrapertools.find_single_match(data, '<div class="flagge".*?src="([^"]+)"')
            if self.bandera:
                self.bandera = "http:"+self.bandera.replace("small/", "originals/")
            else:
                self.bandera = scrapertools.find_single_match(data, '<img src="([^"]+)" title="[^"]*" alt="[^"]*" class="flaggenrahmen"')
                if self.bandera:
                    self.bandera = "http:"+self.bandera.replace("small/", "originals/")
            bloque = scrapertools.find_single_match(data, '<div class="box-personeninfos">(.*?)</table></div></div>')
            datos = scrapertools.find_multiple_matches(bloque, '<th>(.*?)</th><td>(.*?)</td>')
        except:
            datos = ""

        if not datos:
            bloque = scrapertools.find_single_match(data, '<div class="dataContent">(.*?)<ul class="megamenu"')
            datos = scrapertools.find_multiple_matches(bloque, '<span class="dataItem">(.*?)</span><span class="dataValue">(.*?)</span>')
        if datos:
            self.copa = "http:"+scrapertools.find_single_match(data, '<div class="dataZusatzImage"><img src="([^"]+)"').replace("fix/", "originals/")
            try:
                for titulo, valor in datos:
                    titulo = titulo.replace("&oslash;", "ø").capitalize()
                    valor = valor.replace("Jugador", "jugadores")
                    valor = scrapertools.remove_htmltags(valor)
                    title = "[B]"+titulo+"[/B] [COLOR dimgray]" + valor.replace("  ", " ") +"[/COLOR]"
                    if len(self.datos1) < 5:
                        self.datos1.append(title)
                    else:
                        self.datos2.append(title)
            except:
                pass
                

        # Tabla de clasificacion
        try:
            self.clasifi = []
            self.header_tabla, bloque = scrapertools.find_single_match(data, '<div class="box tab-print"><div class="table-header">(.*?)</div>(.*?)</table>')
            patron = '<td.*?style="background-color:(?:#([^"]+)"|").*?>([^<]+)<(.*?)href="([^"]+)".*?src="([^"]+)"' \
                     '.*?href.*?>(.*?)</a>.*?<td class="zentriert">(.*?)</td>.*?>(.*?)</td>.*?>(\d+)'
            datos = scrapertools.find_multiple_matches(bloque, patron)
            for color, posicion, icon, url, img_equipo, equipo, partidos, ventaja, puntos in datos:
                url = "http://www.transfermarkt.es" + url.replace("spielplan/", "startseite/")
                img_equipo = "http:"+img_equipo.replace("tiny/", "medium/")
                posicion = posicion.rjust(2)
                ventaja = ventaja.rjust(2)
                partidos = partidos.rjust(2)
                puntos = puntos.rjust(2)
                icono = ""
                if color:
                    color = "0xFF" + color.upper()
                if "green-arrow-ten" in icon:
                    icono = "http://i.imgur.com/0g5VoWq.png"
                if "red-arrow-ten" in icon:
                    icono = "http://i.imgur.com/drFwxm4.png"
                if "grey-block-ten" in icon:
                    icono = "http://i.imgur.com/QtLf50y.png"
                if not color:
                    color = "0xFFFFFFFF"
                self.clasifi.append(([color, posicion, icono, img_equipo, equipo, partidos, ventaja, puntos, url]))
        except:
            logger.info(traceback.format_exc())

        self.rondas = []
        if not self.clasifi:
            try:
                bloque = scrapertools.find_multiple_matches(data, 'Sturm">.*?href=.*?>([^<]+)<(.*?)(?:tr class="bg_|<\/table>)')
                for ronda, partidos in bloque:
                    ronda = "[COLOR green][B]"+ronda+"[/B][/COLOR]"
                    self.rondas.append([ronda, "", "", "", "", "", ""])
                    patron = '<td class="hide-for-small">(.*?)</td>.*?</td>(.*?)<img src="([^"]+)".*?<a title="(Previa|Crónica|Ticker en vivo).*?href="([^"]+)">' \
                             '(.*?)</a>.*?<img src="([^"]+)".*?>(.*?)</tr>'
                    matches = scrapertools.find_multiple_matches(partidos, patron)
                    for fecha, home, thumb1, live, url, result, thumb2, visit in matches:
                        result = scrapertools.remove_htmltags(result)
                        thumb1 = "http:"+thumb1.replace("tiny/", "originals/")
                        thumb2 = "http:"+thumb2.replace("tiny/", "originals/")
                        equipo1 = scrapertools.remove_htmltags(home)
                        equipo1_t = scrapertools.remove_htmltags(home)
                        if "bg_gelb_20" in home:
                            equipo1_t = "[COLOR red]"+equipo1_t+"[/COLOR]"
                        equipo2 = scrapertools.remove_htmltags(visit)
                        equipo2_t = scrapertools.remove_htmltags(visit)
                        if "bg_gelb_20" in visit:
                            equipo2_t = "[COLOR red]"+equipo2_t+"[/COLOR]"
                        if live == "Ticker en vivo":
                            title = equipo1_t + " [B][COLOR red]"+result+"[/COLOR][/B] "+equipo2_t
                        else:
                            title = equipo1_t + " [B]"+result+"[/B] "+equipo2_t
                        url = "http://www.transfermarkt.es" + url
                        if fecha:
                            title += " | " + fecha
                        self.rondas.append([title, url, result, equipo1, thumb1, equipo2, thumb2])
            except:
                pass

        loading.update(60, "Buscando goleadores...")
        # Tabla pichichi
        try:
            self.datos_goles = []
            url_pichichi = scrapertools.find_single_match(data, 'href="([^"]+)">Trofeo Pichichi</a>')
            if not url_pichichi:
                url_pichichi = scrapertools.find_single_match(data, 'href="([^"]+)">Goleadores</a>')
            if url_pichichi:
                if "saison_id" in self.url and not "saison_id" in url_pichichi:
                    url_pichichi = url_pichichi+"/saison_id/"+self.url.rsplit("=",1)[1]
                data_pichichi = httptools.downloadpage("http://www.transfermarkt.es"+url_pichichi+"/plus/1").data
                data_pichichi = re.sub(r"\n|\r|\t|\s{2}","", data_pichichi).replace("&nbsp;", " ")
                bloque = scrapertools.find_single_match(data_pichichi, '<div class="kartei-button-bar">(.*?)</tbody>')
                if "Nac.</th>" in bloque:
                    patron = '<td class="zentriert">(\d+)</td>.*?<td.*?>.*?src="([^"]+)" title="([^"]+)"' \
                             '.*?<td>(.*?)</td>.*?<td class="zentriert"><img src="([^"]+)".*?' \
                             '(?:<img src="([^"]+)".*?<td class="zentriert">(\d+)<\/td>|<td class="zentriert">(\d+)<\/td>)' \
                             '.*?src="([^"]+)".*?>(\d+)</a></td><td class="zentriert">(\d+)</td><td class="zentriert">(\d+)</td>' \
                             '.*?>(\d+)</a>'
                    matches = scrapertools.find_multiple_matches(bloque, patron)
                    for pos, foto, nombre, puesto, bandera, bandera2, edad, edad2, club, partds, asist, penalt, goles in matches:
                        pos = pos.rjust(2)
                        partds = partds.rjust(2)
                        asist = asist.rjust(2)
                        goles = goles.rjust(2)
                        if foto:
                            foto = "http:" + foto
                        if bandera:
                            bandera = "http:" + bandera.replace("verysmall/", "originals/")
                        if bandera2:
                            bandera2 = "http:" + bandera2.replace("verysmall/", "originals/")
                        if club:
                            club = "http:" + club.replace("verysmall/", "medium/")
                        if edad2:
                            edad = edad2
                        year = datetime.datetime.today().year - season
                        edad = str(int(edad)-year)
                        nombre = "[B]"+nombre+"[/B] / [COLOR blue]"+puesto+"[/COLOR]"
                        self.datos_goles.append([pos, foto, nombre, bandera, bandera2, edad, club, partds, asist, penalt, goles])
        except:
            logger.info(traceback.format_exc())

        loading.update(80, "Escudriñando a los mejores porteros...")
        # Tabla Zamora
        try:
            self.datos_zamora = []
            patron = '<td class="zentriert">(\d+)</td>.*?<td.*?>.*?src="([^"]+)" title="([^"]+)"' \
                     '.*?<td>.*?>([^<]+)</a>.*?<td class="zentriert"><img src="([^"]+)".*?' \
                     '(?:<img src="([^"]+)".*?<td class="zentriert">(\d+)<\/td>|<td class="zentriert">(\d+)<\/td>)' \
                     '.*?<td class="zentriert">(\d+)</td>.*?<td class="zentriert">(.*?)</td>' \
                     '.*?<td class="zentriert">([^<]+)</td></tr>'
            url_zamora = scrapertools.find_single_match(data, 'href="([^"]+)">Trofeo Zamora</a>')
            if not url_zamora:
                url_zamora = scrapertools.find_single_match(data, 'href="([^"]+)">Partidos a cero</a>')
                patron = '<td class="zentriert">(\d+)</td>.*?<td.*?>.*?src="([^"]+)" title="([^"]+)"' \
                         '.*?<td>.*?>([^<]+)</a>.*?<td class="zentriert"><img src="([^"]+)".*?' \
                         '(?:<img src="([^"]+)".*?<td class="zentriert">.*?<a.*?>(\d+)<\/a>|<td class="zentriert".*?<a.*?>(\d+)<\/a>)' \
                         '.*?<td class="zentriert".*?<a.*?>(\d+)<\/a>.*?<td class="zentriert".*?<a.*?>(.*?)<\/a>' \
                         '.*?<td class="zentriert".*?>([^<]+)<\/a><\/td><\/tr>'
            if url_zamora:
                if "saison" in self.url:
                    url_zamora = url_zamora+"/saison_id/"+self.url.rsplit("=",1)[1]
                data_zamora = httptools.downloadpage("http://www.transfermarkt.es"+url_zamora+"/plus/1").data
                data_zamora = re.sub(r"\n|\r|\t|\s{2}","", data_zamora).replace("&nbsp;", " ")
                bloque = scrapertools.find_single_match(data_zamora, '<div class="kartei-button-bar">(.*?)</tbody>')
                matches = scrapertools.find_multiple_matches(bloque, patron)
                for pos, foto, nombre, club, bandera, bandera2, alinea, alinea2, porteria, goles, porcentaje in matches:
                    pos = pos.rjust(2)
                    if alinea2:
                        alinea = alinea2
                    alinea = alinea.rjust(2)
                    porteria = porteria.rjust(2)
                    goles = goles.rjust(2)
                    if foto:
                        foto = "http:" + foto
                    if bandera:
                        bandera = "http:" + bandera.replace("verysmall/", "originals/")
                    if bandera2:
                        bandera2 = "http:" + bandera2.replace("verysmall/", "originals/")
                    porcentaje = porcentaje.replace(",0", "")
                    nombre = "[B]"+nombre+"[/B] / [COLOR blue]"+club+"[/COLOR]"
                    self.datos_zamora.append([pos, foto, nombre, bandera, bandera2, alinea, porteria, goles, porcentaje])
        except:
            pass

        loading.close()
        self.doModal()
        return

    def onInit(self):
        self.setCoordinateResolution(0)
        # Ponemos el foco en el boton de cerrar [X]
        self.setFocus(self.getControl(10003))
        self.botones.append(self.getControl(10003))

        # Ponemos el título y las imagenes
        self.addControl(xbmcgui.ControlLabel(169,98,1216,29,"[B]"+self.caption+"[/B]", self.fonts["12"], "0xFFFFA500", '', 0x00000002))
        self.addControl(xbmcgui.ControlImage(138,147,1309,858,self.fanart, 0, '0xFFFFFFFF'))
        
        path_image = os.path.join(config.get_runtime_path(), 'resources', 'skins', 'Default', 'media', 'MatchWindow')
        
        # Botones temporada
        self.arribalist = 0
        self.abajolist = 0
        if self.items_temp:
            self.addControl(xbmcgui.ControlLabel(150, 170, 150, 25, "[B]Temporadas[/B]", self.fonts["10"], '0xFF000000'))
            self.lista_temp = xbmcgui.ControlList(150, 200, 100, 150, self.fonts["10"], '0xFF000000', 'MatchWindow/ItemNoFocus.png', 'MatchWindow/ItemFocus.png', '0xFF2E9AFE', 0, 0, 1, 0, 25, 0, 0x00000004)
            self.addControl(self.lista_temp)
            for item in self.items_temp:
                self.lista_temp.addItem(item[0])
            self.lista_temp.selectItem(self.selected)
            self.setFocus(self.lista_temp)
            self.botones.append(self.lista_temp)
            if len(self.items_temp) > 1:
                self.arribalist = xbmcgui.ControlButton(250, 200, 30, 30, '', os.path.join(path_image, 'spinUp-Focus.png'), os.path.join(path_image, 'spinUp-noFocus.png'))
                self.addControl(self.arribalist)
                self.abajolist = xbmcgui.ControlButton(250, 295, 30, 30, '', os.path.join(path_image, 'spinDown-Focus.png'), os.path.join(path_image, 'spinDown-noFocus.png'))
                self.addControl(self.abajolist)

        # Datos de la liga, cabecera
        self.addControl(xbmcgui.ControlImage(290, 151, 1040, 190, 'http://i.imgur.com/sf4NHnr.png'))
        self.addControl(xbmcgui.ControlImage(1288, 154, 36, 30, "http://i.imgur.com/QtLf50y.png"))
        self.addControl(xbmcgui.ControlImage(1290, 157, 32, 24, self.bandera))
        self.addControl(xbmcgui.ControlLabel(315, 153, 990, 20, "[B]"+self.name+"[/B]", self.fonts["12"], '0xFF000000', '', 0x00000002))
        logo = xbmcgui.ControlImage(294, 195, 127, 138, self.logo)
        self.addControl(logo)
        logo.setAnimations([('conditional', 'effect=rotatex start=300% end=360% time=1500 tween=bounce condition=true',)])

        # Imagen de la copa si la hubiese
        if self.copa != "http:":
            self.addControl(xbmcgui.ControlImage(770,188,120,150, self.copa, colorDiffuse="0x65FFFFFF"))
        i = 0
        for texto in self.datos1:
            suma = 200 + i
            self.textbox1 = xbmcgui.ControlFadeLabel(450, suma, 320, 20, self.fonts["10"], '0xFF000000')
            self.addControl(self.textbox1)
            self.textbox1.addLabel(texto)
            i += 22
        i = 0
        for texto in self.datos2:
            suma = 200 + i
            self.textbox1 = xbmcgui.ControlFadeLabel(900, suma, 380, 20, self.fonts["10"], '0xFF000000')
            self.addControl(self.textbox1)
            self.textbox1.addLabel(texto)
            i += 22
        
        # Botón lupa para buscar liga/copa
        self.search = xbmcgui.ControlButton(1340, 185, 100, 100, "", "http://i.imgur.com/a3TJQj8.png", "http://i.imgur.com/a3TJQj8.png")
        self.addControl(self.search)
        self.search.setAnimations([('focus','effect=zoom center=auto end=120%')])
        self.botones.append(self.search)
        self.addControl(xbmcgui.ControlLabel(1325, 285, 120, 40, "Buscar\nLiga/Copa", self.fonts["10"], "0xFF000000", '', 0x00000002))


        # Clasificacion
        if self.clasifi:
            self.botones_club = []
            self.controls_hide = []
            self.equipos_tabla = []
            self.next = xbmcgui.ControlButton(145, 950, 440, 25, '', "http://i.imgur.com/jIMWvRE.png", "http://i.imgur.com/jIMWvRE.png")
            self.prev = xbmcgui.ControlButton(142, 950, 440, 25, '', "http://i.imgur.com/2p5pOar.png", "http://i.imgur.com/2p5pOar.png")
            self.addControl(xbmcgui.ControlImage(145, 345, 440, 90, 'http://i.imgur.com/2vkcrHZ.png'))
            fadelabel = xbmcgui.ControlFadeLabel(160, 360, 410, 25, self.fonts["12"], '0xFF000000', 0x00000002)
            self.addControl(fadelabel)
            fadelabel.addLabel("[B]"+self.header_tabla+"[/B]")
            i = 0
            count = 1
            
            for color, pos, icono, thumb_equipo, equipo, part, vent, punt, url in self.clasifi:
                suma = 435 + i
                img1 = xbmcgui.ControlImage(145,suma, 440, 32, "http://i.imgur.com/PNpmpzB.png")
                label_color = xbmcgui.ControlImage(148, suma, 51, 30, 'http://i.imgur.com/9SilWAJ.png', 0, color)
                    
                lb1 = xbmcgui.ControlLabel(150, suma, 25, 29, pos, self.fonts["10"], '0xFF000000', '', 0x00000002)
                icon = xbmcgui.ControlImage(180,suma+7, 15, 17, icono)
                bt1 = xbmcgui.ControlButton(202, suma-1, 30, 29, '', thumb_equipo, thumb_equipo)
                fadelabel = xbmcgui.ControlFadeLabel(238, suma, 203, 29, self.fonts["10"], '0xFF000000')
                lb2 = xbmcgui.ControlLabel(458, suma, 25, 29, part, self.fonts["10"], '0xFF000000', '', 0x00000002)
                lb3 = xbmcgui.ControlLabel(500, suma, 30, 29, vent, self.fonts["10"], '0xFF000000', '', 0x00000001)
                lb4 = xbmcgui.ControlLabel(547, suma, 30, 34, punt, self.fonts["10"], '0xFF000000', '', 0x00000002)
                if count <= 16:
                    self.addControl(img1)
                    self.addControl(label_color)
                    self.addControl(icon)
                    self.addControl(lb1)
                    self.addControl(bt1)
                    bt1.setAnimations([('conditional', 'effect=rotate start=-290% end=0% time=2200 condition=true tween=circle',), ('focus', 'effect=zoom start=80% end=120%',)])
                    self.addControl(fadelabel)
                    fadelabel.addLabel("[B]"+equipo+"[/B]")
                    fadelabel.setAnimations([('conditional', 'effect=rotatey start=-40% end=0% time=2200 condition=true tween=elastic',)])                
                    self.addControl(lb2)
                    self.addControl(lb3)
                    self.addControl(lb4)
                    i += 32
                if count == 16:
                    i = 0
                elif count == 17:
                    i += 32
                    self.botones.append(self.next)
                    self.botones.append(self.prev)
                    self.addControl(self.next)
                    self.next.setAnimations([('conditional', 'effect=fade start=20 end=100 time=1200 loop=true reversible=false condition=Control.HasFocus('+str(self.next.getId())+')',)])
                elif count > 17:
                    i += 32

                count += 1
                self.botones.append(bt1)
                self.botones_club.append(bt1)
                self.controls_hide.append([img1, label_color, lb1, icon, bt1, fadelabel, lb2, lb3, lb4, "[B]"+equipo+"[/B]"])
                self.equipos_tabla.append([url, thumb_equipo])
        else:
            if self.rondas:
                self.addControl(xbmcgui.ControlLabel(145, 350, 460, 30, "[B]Partidos/Rondas[/B]", self.fonts["16"], "0xFF000000", "", 0x00000002))
                path_image = os.path.join(config.get_runtime_path(), 'resources', 'skins', 'Default', 'media', 'MatchWindow')
                self.lista_rondas = xbmcgui.ControlList(145, 400, 460, 630, self.fonts["10"], '0xFF000000', 'MatchWindow/ItemNoFocus.png', 'MatchWindow/ItemFocus.png', '0xFF2E9AFE', 25, 25, 1, 0, 60, 0, 0x00000004)
                self.addControl(self.lista_rondas)
                self.botones.append(self.lista_rondas)
                for label, url, result, equipo1, thumb1, equipo2, thumb2 in self.rondas:
                    item = xbmcgui.ListItem(label)
                    if url:
                        item.setProperty("url", url)
                    item.setProperty("result", result)
                    item.setProperty("local", equipo1)
                    item.setProperty("srclocal", thumb1)
                    item.setProperty("visit", equipo2)
                    item.setProperty("srcvisit", thumb2)
                    self.lista_rondas.addItem(item)

        # Cuadro Pichichi
        self.botones_goles = []
        if self.datos_goles:
            self.addControl(xbmcgui.ControlImage(620, 345, 710, 300, 'http://i.imgur.com/WkZuZz7.png'))
            i = 0
            count = 0
            for pos, foto, nombre, bandera, bandera2, edad, club, partds, asist, penalt, goles in self.datos_goles:
                if count % 5 == 0:
                    i = 0
                elif count != 0:
                    i += 51
                suma = 395 + i
                lbl1 = xbmcgui.ControlLabel(627, suma, 30, 20, pos, self.fonts["10"], "0xFF000000", "", 0x00000002)
                img1 = xbmcgui.ControlImage(664, suma-3, 40, 40, foto)
                lbl2 = xbmcgui.ControlFadeLabel(708, suma, 230, 20, self.fonts["10"], "0xFF000000")
                if bandera2:
                    img2 = xbmcgui.ControlImage(952, suma-3, 25, 17, bandera)
                    img3 = xbmcgui.ControlImage(952, suma+20, 25, 17, bandera2)
                else:
                    img2 = xbmcgui.ControlImage(952, suma+9, 25, 17, bandera)
                    img3 = None
                lbl3 = xbmcgui.ControlLabel(1000, suma+2, 30, 20, edad, self.fonts["10"], "0xFF000000", "", 0x00000002)
                img4 = xbmcgui.ControlImage(1043, suma-4, 37, 39, club)
                lbl4 = xbmcgui.ControlLabel(1098, suma+2, 35, 20, partds, self.fonts["10"], "0xFF000000", "", 0x00000002)
                lbl5 = xbmcgui.ControlLabel(1158, suma+2, 35, 20, goles, self.fonts["10"], "0xFF000000", "", 0x00000002)
                lbl6 = xbmcgui.ControlLabel(1220, suma+2, 35, 20, penalt, self.fonts["10"], "0xFF000000", "", 0x00000002)
                lbl7 = xbmcgui.ControlLabel(1280, suma+2, 35, 20, asist, self.fonts["10"], "0xFF000000", "", 0x00000002)
                if count < 5:
                    self.addControl(lbl1)
                    self.addControl(img1)
                    self.addControl(lbl2)
                    lbl2.addLabel(nombre)
                    self.addControl(img2)
                    if img3:
                        self.addControl(img3)
                    self.addControl(lbl3)
                    self.addControl(img4)
                    self.addControl(lbl4)
                    self.addControl(lbl5)
                    self.addControl(lbl6)
                    self.addControl(lbl7)
                elif count == 5:
                    self.btn_right = xbmcgui.ControlButton(1260, 642, 70, 29, '', "http://i.imgur.com/ruw8GDU.png", "http://i.imgur.com/ruw8GDU.png")
                    self.addControl(self.btn_right)
                    self.btn_right.setAnimations([('conditional','effect=zoom start=1260,642,70,29 end=1230,642,100,29 time=1000 loop=true tween=bounce condition=Control.HasFocus('+str(self.btn_right.getId())+')',)])
                    self.btn_left = xbmcgui.ControlButton(620, 642, 70, 29, '', "http://i.imgur.com/ayTdppD.png", "http://i.imgur.com/ayTdppD.png")
                    self.addControl(self.btn_left)
                    self.btn_left.setAnimations([('conditional','effect=zoom start=620,642,70,29 end=620,642,100,29 time=1000 loop=true tween=bounce condition=Control.HasFocus('+str(self.btn_left.getId())+')',)])
                    self.btn_left.setVisible(False)
                    self.botones.append(self.btn_left)
                    self.botones.append(self.btn_right)
                    
                self.botones_goles.append([lbl1, img1, lbl2, img2, img3, lbl3, img4, lbl4, lbl5, lbl6, lbl7, nombre])
                count += 1
            self.addControl(xbmcgui.ControlImage(1333,355,40,290,"http://i.imgur.com/qVkoKlg.png"))

        # Cuadro zamora
        self.botones_zamora = []
        if self.datos_zamora:
            self.addControl(xbmcgui.ControlImage(620, 680, 710, 300, 'http://i.imgur.com/9dfIasP.png'))
            i = 0
            count = 0
            for pos, foto, nombre, bandera, bandera2, alinea, porteria, goles, porcentaje in self.datos_zamora:
                if count % 5 == 0:
                    i = 0
                elif count != 0:
                    i += 51
                suma = 731 + i
                lbl1 = xbmcgui.ControlLabel(624, suma, 30, 20, pos, self.fonts["10"], "0xFF000000", "", 0x00000002)
                img1 = xbmcgui.ControlImage(660, suma-3, 40, 40, foto)
                lbl2 = xbmcgui.ControlFadeLabel(704, suma, 234, 20, self.fonts["10"], "0xFF000000")
                if bandera2:
                    img2 = xbmcgui.ControlImage(952, suma-3, 25, 17, bandera)
                    img3 = xbmcgui.ControlImage(952, suma+20, 25, 17, bandera2)
                else:
                    img2 = xbmcgui.ControlImage(952, suma+9, 25, 17, bandera)
                    img3 = None
                lbl3 = xbmcgui.ControlLabel(1002, suma+2, 35, 20, alinea, self.fonts["10"], "0xFF000000", "", 0x00000002)
                lbl4 = xbmcgui.ControlLabel(1078, suma+2, 35, 20, porteria, self.fonts["10"], "0xFF000000", "", 0x00000002)
                lbl5 = xbmcgui.ControlLabel(1183, suma+2, 35, 20, goles, self.fonts["10"], "0xFF000000", "", 0x00000002)
                lbl6 = xbmcgui.ControlLabel(1257, suma+2, 75, 20, porcentaje, self.fonts["10"], "0xFF000000", "", 0x00000002)
                if count < 5:
                    self.addControl(lbl1)
                    self.addControl(img1)
                    self.addControl(lbl2)
                    lbl2.addLabel(nombre)
                    self.addControl(img2)
                    if img3:
                        self.addControl(img3)
                    self.addControl(lbl3)
                    self.addControl(lbl4)
                    self.addControl(lbl5)
                    self.addControl(lbl6)
                elif count == 5:
                    self.btn_right2 = xbmcgui.ControlButton(1260, 978, 70, 29, '', "http://i.imgur.com/ruw8GDU.png", "http://i.imgur.com/ruw8GDU.png")
                    self.addControl(self.btn_right2)
                    self.btn_right2.setAnimations([('conditional','effect=zoom start=1260,978,70,29 end=1230,978,100,29 time=1000 loop=true tween=bounce condition=Control.HasFocus('+str(self.btn_right2.getId())+')',)])
                    self.btn_left2 = xbmcgui.ControlButton(620, 978, 70, 29, '', "http://i.imgur.com/ayTdppD.png", "http://i.imgur.com/ayTdppD.png")
                    self.addControl(self.btn_left2)
                    self.btn_left2.setAnimations([('conditional','effect=zoom start=620,978,70,29 end=620,978,100,29 time=1000 loop=true tween=bounce condition=Control.HasFocus('+str(self.btn_left2.getId())+')',)])
                    self.btn_left2.setVisible(False)
                    self.botones.append(self.btn_left2)
                    self.botones.append(self.btn_right2)
                    
                self.botones_zamora.append([lbl1, img1, lbl2, img2, img3, lbl3, lbl4, lbl5, lbl6, nombre])
                count += 1
            self.addControl(xbmcgui.ControlImage(1333,685,40,290,"http://i.imgur.com/HxmKOcn.png"))
            

    def onDoubleClick(self, id):
        try:
            if id == self.lista_temp.getId():
                index = self.lista_temp.getSelectedPosition()
                global window_liga
                window_liga.close()
                del window_liga
                window_liga = Liga('MatchWindow.xml', config.get_runtime_path())
                window_liga.Start(self.items_temp[index][1], self.logo, self.name, season=self.items_temp[index][0], fonts=self.fonts)
        except:
            pass

        try:
            if id == self.lista_rondas.getId():
                item = self.lista_rondas.getSelectedItem()
                url = item.getProperty("url")
                if url:
                    escudo1 = item.getProperty("srclocal")
                    escudo2 = item.getProperty("srcvisit")
                    equipo1 = item.getProperty("local")
                    equipo2 = item.getProperty("visit")
                    result = item.getProperty("result")
                    global window_match
                    window_match = Match('MatchWindow.xml', config.get_runtime_path())
                    window_match.Start(url, escudo1, equipo1, escudo2, equipo2, result, fonts=self.fonts)
        except:
            pass
    
    def onClick(self, id):
        # Boton Cancelar y [X]
        if id == 10003:
            global window_liga
            window_liga.close()
            del window_liga
        
        # Flecha arriba/abajo en lista temporadas
        try:
            if id == self.arribalist.getId():
                pos = self.lista_temp.getSelectedPosition()
                if  pos > 0:
                    self.lista_temp.selectItem(pos-1)
        except:
            pass

        try:
            if id == self.abajolist.getId():
                pos = self.lista_temp.getSelectedPosition()
                if  pos < len(self.items_temp) - 1:
                    self.lista_temp.selectItem(pos+1)
        except:
            pass

        # Botones escudos en clasificacion
        try:
            for i, boton in enumerate(self.botones_club):
                if id == boton.getId():
                    global window_club
                    window_club = Club("ClubWindow.xml", config.get_runtime_path())
                    window_club.Start('', '', self.equipos_tabla[i][1], "Información del ", url=self.equipos_tabla[i][0], fonts=self.fonts)
        except:
            pass

        # Botones previo y anterior en tabla clasificacion
        try:
            if id == self.next.getId():
                i = 0
                for img1, label_color, lb1, icon, bt1, fadelabel, lb2, lb3, lb4, equipo in self.controls_hide:
                    if i < 16:
                        self.removeControls([img1, label_color, lb1, icon, bt1, fadelabel, lb2, lb3, lb4])
                    else:
                        self.addControls([img1, label_color, lb1, icon, bt1, fadelabel, lb2, lb3, lb4])
                        fadelabel.addLabel(equipo)
                        bt1.setAnimations([('focus', 'effect=zoom start=80% end=120%',)])
                    i += 1
                self.removeControl(self.next)
                self.addControl(self.prev)
                self.prev.setAnimations([('conditional', 'effect=fade start=20 end=100 time=1200 loop=true reversible=false condition=Control.HasFocus('+str(self.prev.getId())+')',)])
        except:
            pass

        try:
            if id == self.prev.getId():
                i = 0
                for img1, label_color, lb1, icon, bt1, fadelabel, lb2, lb3, lb4, equipo in self.controls_hide:
                    if i >=16:
                        self.removeControls([img1, label_color, lb1, icon, bt1, fadelabel, lb2, lb3, lb4])
                    else:
                        self.addControls([img1, label_color, lb1, icon, bt1, fadelabel, lb2, lb3, lb4])
                        fadelabel.addLabel(equipo)
                        bt1.setAnimations([('focus', 'effect=zoom start=80% end=120%',)])
                    i += 1
                self.removeControl(self.prev)
                self.addControl(self.next)
                self.next.setAnimations([('conditional', 'effect=fade start=20 end=100 time=1200 loop=true reversible=false condition=Control.HasFocus('+str(self.next.getId())+')',)])
        except:
            pass

        # Boton anterior/siguiente pichichi
        try:
            if id == self.btn_right.getId():
                i = 1
                count = 0
                for lbl1, img1, lbl2, img2, img3, lbl3, img4, lbl4, lbl5, lbl6, lbl7, label in self.botones_goles:
                    if i > self.count_gol - 5 and i <= self.count_gol and count < 5:
                        if img3:
                            self.removeControls([lbl1, img1, lbl2, img2, img3, lbl3, img4, lbl4, lbl5, lbl6, lbl7])
                        else:
                            self.removeControls([lbl1, img1, lbl2, img2, lbl3, img4, lbl4, lbl5, lbl6, lbl7])
                        count += 1
                    elif i > self.count_gol and count < 10:
                        if img3:
                            self.addControls([lbl1, img1, lbl2, img2, img3, lbl3, img4, lbl4, lbl5, lbl6, lbl7])
                        else:
                            self.addControls([lbl1, img1, lbl2, img2, lbl3, img4, lbl4, lbl5, lbl6, lbl7])
                        lbl2.addLabel(label)
                        count += 1
                        self.count_gol += 1
                    i += 1
                if self.count_gol > 5 and self.count_gol < 11:
                    self.btn_left.setVisible(True)
                    
                if len(self.botones_goles) < self.count_gol + 1:
                    self.btn_right.setVisible(False)
        except:
            pass

        try:
            if id == self.btn_left.getId():
                i = 1
                count = 0
                if self.count_gol == len(self.botones_goles):
                    self.btn_right.setVisible(True)
                len_goles = self.count_gol
                for lbl1, img1, lbl2, img2, img3, lbl3, img4, lbl4, lbl5, lbl6, lbl7, label in self.botones_goles:
                    resta = 5 + (len_goles%5)
                    if resta == 5:
                        resta = 10
                    resta2 = len_goles%5
                    if not resta2:
                        resta2 = 5
                    if i > len_goles - resta and count < 5:
                        if img3:
                            self.addControls([lbl1, img1, lbl2, img2, img3, lbl3, img4, lbl4, lbl5, lbl6, lbl7])
                        else:
                            self.addControls([lbl1, img1, lbl2, img2, lbl3, img4, lbl4, lbl5, lbl6, lbl7])
                        lbl2.addLabel(label)
                        count += 1
                    elif i > len_goles - resta2 and i <= len_goles and count < 10:
                        if img3:
                            self.removeControls([lbl1, img1, lbl2, img2, img3, lbl3, img4, lbl4, lbl5, lbl6, lbl7])
                        else:
                            self.removeControls([lbl1, img1, lbl2, img2, lbl3, img4, lbl4, lbl5, lbl6, lbl7])
                        count += 1
                        self.count_gol -= 1
                    i += 1
                if self.count_gol == 5:
                    self.btn_left.setVisible(False)
        except:
            pass

        # Boton anterior/siguiente zamora
        try:
            if id == self.btn_right2.getId():
                i = 1
                count = 0
                for lbl1, img1, lbl2, img2, img3, lbl3, lbl4, lbl5, lbl6, label in self.botones_zamora:
                    if i > self.count_zamora - 5 and i <= self.count_zamora and count < 5:
                        if img3:
                            self.removeControls([lbl1, img1, lbl2, img2, img3, lbl3, lbl4, lbl5, lbl6])
                        else:
                            self.removeControls([lbl1, img1, lbl2, img2, lbl3, lbl4, lbl5, lbl6])
                        count += 1
                    elif i > self.count_zamora and count < 10:
                        if img3:
                            self.addControls([lbl1, img1, lbl2, img2, img3, lbl3, lbl4, lbl5, lbl6])
                        else:
                            self.addControls([lbl1, img1, lbl2, img2, lbl3, lbl4, lbl5, lbl6])
                        lbl2.addLabel(label)
                        count += 1
                        self.count_zamora += 1
                    i += 1
                if self.count_zamora > 5 and self.count_zamora < 11:
                    self.btn_left2.setVisible(True)

                if len(self.botones_zamora) < self.count_zamora + 1:
                    self.btn_right2.setVisible(False)
        except:
            pass

        try:
            if id == self.btn_left2.getId():
                i = 1
                count = 0
                if self.count_zamora == len(self.botones_zamora):
                    self.btn_right2.setVisible(True)
                len_goles = self.count_zamora
                for lbl1, img1, lbl2, img2, img3, lbl3, lbl4, lbl5, lbl6, label in self.botones_zamora:
                    resta = 5 + (len_goles%5)
                    if resta == 5:
                        resta = 10
                    resta2 = len_goles%5
                    if not resta2:
                        resta2 = 5
                    if i > len_goles - resta and count < 5:
                        if img3:
                            self.addControls([lbl1, img1, lbl2, img2, img3, lbl3, lbl4, lbl5, lbl6])
                        else:
                            self.addControls([lbl1, img1, lbl2, img2, lbl3, lbl4, lbl5, lbl6])
                        lbl2.addLabel(label)
                        count += 1
                    elif i > len_goles - resta2 and i<= len_goles and count < 10:
                        if img3:
                            self.removeControls([lbl1, img1, lbl2, img2, img3, lbl3, lbl4, lbl5, lbl6])
                        else:
                            self.removeControls([lbl1, img1, lbl2, img2, lbl3, lbl4, lbl5, lbl6])
                        count += 1
                        self.count_zamora -= 1
                    i += 1
                if self.count_zamora == 5:
                    self.btn_left2.setVisible(False)
        except:
            pass

        # Acción búsqueda liga
        try:
            if id == self.search.getId():
                texto = platformtools.dialog_input(heading="Introduce el nombre de la liga/copa o el país donde buscar")
                if texto:
                    texto = texto.strip()
                    data = httptools.downloadpage("http://www.transfermarkt.es/schnellsuche/ergebnis/schnellsuche?query=%s&x=0&y=0" % urllib.quote(texto.replace("%2B", "+"))).data
                    bloque = scrapertools.find_single_match(data, '<div class="table-header">Buscar resultados de competencias(.*?)<div class="keys"')
                    if bloque:
                        items = search_leagues(bloque)
                    else:
                        items = search_leagues("")
                    global window_select
                    window_select = Select("DialogSelect.xml", config.get_runtime_path(), items=items, caption="Elige una de las opciones", type="liga", ventana=self, fonts=self.fonts)
                    window_select.doModal()
        except:
            pass
           

    def onAction(self, action):
        ACTION_MOVE_DOWN = 4
        ACTION_MOVE_LEFT = 1
        ACTION_MOVE_RIGHT = 2
        ACTION_MOVE_UP = 3
        global window_liga
        if action == 92 or action == 10 or action == 110:
            window_liga.close()
            del window_liga
        try:
            if action == ACTION_MOVE_RIGHT or (action == ACTION_MOVE_DOWN and self.getFocus() != self.lista_temp and self.getFocus() != self.lista_rondas):
                if self.focus < len(self.botones)-1:
                    self.focus += 1
                    while True:
                        id_focus = str(self.botones[self.focus].getId())
                        if xbmc.getCondVisibility('[Control.IsVisible('+id_focus+')]'):
                            self.setFocus(self.botones[self.focus])
                            break
                        self.focus += 1
                        if self.focus == len(self.botones):
                            break
        except:
            pass
        try:
            if action == ACTION_MOVE_LEFT or (action == ACTION_MOVE_UP and self.getFocus() != self.lista_temp and self.getFocus() != self.lista_rondas):
                if self.focus > 0:
                    self.focus -= 1
                    while True:
                        id_focus = str(self.botones[self.focus].getId())
                        if xbmc.getCondVisibility('[Control.IsVisible('+id_focus+')]'):
                            self.setFocus(self.botones[self.focus])
                            break
                        self.focus -= 1
                        if self.focus < 0:
                            break
        except:
            pass

        try:
            if action == 7 and self.getFocus() == self.lista_temp:
                index = self.lista_temp.getSelectedPosition()
                window_liga.close()
                del window_liga
                window_liga = Liga('MatchWindow.xml', config.get_runtime_path())
                window_liga.Start(self.items_temp[index][1], self.logo, self.name, season=self.items_temp[index][0], fonts=self.fonts)
        except:
            pass

        try:
            if action == 7 and self.getFocus() == self.lista_rondas:
                item = self.lista_rondas.getSelectedItem()
                url = item.getProperty("url")
                if url:
                    escudo1 = item.getProperty("srclocal")
                    escudo2 = item.getProperty("srcvisit")
                    equipo1 = item.getProperty("local")
                    equipo2 = item.getProperty("visit")
                    result = item.getProperty("result")
                    global window_match
                    window_match = Match('MatchWindow.xml', config.get_runtime_path())
                    window_match.Start(url, escudo1, equipo1, escudo2, equipo2, result, fonts=self.fonts)
        except:
            pass

    def onFocus(self, id):
        try:
            if id == self.abajolist.getId():
                self.setFocus(self.lista_temp)
        except:
            pass
        try:
            if id == self.arribalist.getId():
                self.setFocus(self.lista_temp)
        except:
            pass

# Función para busqueda de ligas
def search_leagues(bloque):
    items = []
    if not bloque:
        item = xbmcgui.ListItem("[COLOR indianred]Sin resultados. Buscar de nuevo...[/COLOR]")
        try:
            item.setArt({"thumb":"http://i.imgur.com/a3TJQj8.png"})
        except:
            item.setThumbnailImage("http://i.imgur.com/a3TJQj8.png")
        item.setProperty("url","")
        item.setProperty("thumb","")
        items.append(item)
    else:
        patron = '<tr class="(?:even|odd)">\s*<td class="zentriert"><img src="([^"]+)".*?alt="([^"]+)".*?href="([^"]+)"'
        ligas = scrapertools.find_multiple_matches(bloque, patron)
        for src, alt, href in ligas:
            src = "http:"+src.replace("mediumsmall/", "originals/")
            href = "http://www.transfermarkt.es"+href
            item = xbmcgui.ListItem(alt)
            try:
                item.setArt({"thumb":src})
            except:
                item.setThumbnailImage(src)
            item.setProperty("url",href)
            item.setProperty("thumb",src)
            items.append(item)
        next_page = scrapertools.find_single_match(bloque, '<li class="naechste-seite"><a href="([^"]+)"')
        if next_page:
            icon = scrapertools.find_single_match(bloque, '<img src="([^"]+)" title="[^"]*" alt="[^"]*" class="flaggenrahmen"')
            icon = "http:"+icon.replace("verysmall/", "originals/")
            next_page = "http://www.transfermarkt.es"+next_page.replace("&amp;", "&")
            item = xbmcgui.ListItem("[COLOR green]Página siguiente >>[/COLOR]")
            try:
                item.setArt({"thumb":icon})
            except:
                item.setThumbnailImage(icon)
            item.setProperty("url", next_page)
            item.setProperty("thumb",icon)
            items.append(item)

    return items
    
    
class Select(xbmcgui.WindowXMLDialog):
    def __init__( self, *args, **kwargs):
        self.items = kwargs.get("items")
        self.fonts = kwargs.get("fonts")
        self.caption = kwargs.get("caption")
        self.type = kwargs.get("type", "")
        self.web = kwargs.get("web", "")
        self.original_name = kwargs.get("name", "")
        self.ventana = kwargs.get("ventana", "")

    def onInit(self):
        try:
            self.control_list = self.getControl(6)
            self.getControl(5).setNavigation(self.control_list, self.control_list, self.control_list, self.control_list)
            self.getControl(3).setEnabled(0)
            self.getControl(3).setVisible(0)
        except:
            pass

        try:
            self.getControl(99).setVisible(False)
        except:
            pass
        self.getControl(1).setLabel("[COLOR orange]"+self.caption+"[/COLOR]")
        self.getControl(5).setLabel("[COLOR tomato][B]Cerrar[/B][/COLOR]")
        self.control_list.reset()
        self.control_list.addItems(self.items)
        self.setFocus(self.control_list)

    def onClick(self, id):
        # Boton Cancelar y [X]
        if id == 5:
            global window_select
            window_select.close()
            del window_select


    def onAction(self,action):
        if action == 92 or action == 110:
            global window_select
            window_select.close()
            del window_select

        try:
            if action == 7 or action == 100:
                if self.getFocusId() == 6 and self.type == "liga":
                    elegir_liga(self, self.ventana)
                elif self.getFocusId() == 6 and self.type == "equipo":
                    elegir_equipo(self)
        except:
            pass

# Acciones en caso de ventana búsqueda de ligas
def elegir_liga(self, ventana):
    global window_select
    item = self.control_list.getSelectedItem()
    name = item.getLabel()
    url = item.getProperty("url")
    logo = item.getProperty("thumb")
    if "Página siguiente" in name:
        data = httptools.downloadpage(url).data
        bloque = scrapertools.find_single_match(data, '<div class="table-header">Buscar resultados de competencias(.*?)<div class="keys"')
        if bloque:
            items = search_leagues(bloque)
            window_select.close()
            del window_select
            window_select = Select("DialogSelect.xml", config.get_runtime_path(), items=items, caption="Elige una liga o copa", type="liga", fonts=self.fonts)
            window_select.doModal()
        else:
            window_select.close()
            del window_select
    elif "Sin resultados" in name:
        window_select.close()
        del window_select
        texto = platformtools.dialog_input(heading="Introduce el nombre de la liga/copa o el país donde buscar")
        if texto:
            texto = texto.strip()
            data = httptools.downloadpage("http://www.transfermarkt.es/schnellsuche/ergebnis/schnellsuche?query=%s&x=0&y=0" % urllib.quote(texto.replace("%2B", "+"))).data
            bloque = scrapertools.find_single_match(data, '<div class="table-header">Buscar resultados de competencias(.*?)<div class="keys"')
            if bloque:
                items = search_leagues(bloque)
                window_select = Select("DialogSelect.xml", config.get_runtime_path(), items=items, caption="Elige una de las opciones", type="liga", fonts=self.fonts)
                window_select.doModal()
            else:
                items = search_leagues("")
    else:
        window_select.close()
        del window_select
        global window_liga
        window_liga.close()
        del window_liga
        window_liga = Liga("MatchWindow.xml", config.get_runtime_path())
        window_liga.Start(url, logo, name, fonts=self.fonts)

# Acciones en caso de ventana búsqueda de equipos
def elegir_equipo(self):
    item = self.control_list.getSelectedItem()
    name = item.getProperty("name")
    global texto_busqueda
    global window_select
    if not texto_busqueda:
        texto_busqueda = self.original_name
    # Búsqueda en thesportsdb
    if self.web == "tsdb":
        if name == "busqueda":
            texto_busqueda = platformtools.dialog_input(texto_busqueda, heading="Introduce el nombre correcto para buscarlo en TheSportsDB")
            if texto_busqueda:
                texto_busqueda = texto_busqueda.strip()
                api = thesportsdb.Api(key="1")
                lista_tsdb = api.Search().Teams(team=texto_busqueda)
                items = equipos_tsdb(lista_tsdb)
                window_select.close()
                del window_select
                window_select = Select("DialogSelect.xml", config.get_runtime_path(), items=items, caption="Elige un equipo de la lista (TheSportsDB)", type="equipo", web="tsdb", name=self.original_name, fonts=self.fonts)
                window_select.doModal()
            else:
                window_select.close()
                del window_select

        elif name != "noresult":
            window_select.close()
            del window_select
            save_data(name, self.original_name, "tsdb")
            platformtools.dialog_notification("Cambio guardado para TheSportsDB", self.original_name+" se sustituye por "+name, time=10000, sound=False)
    # Búsqueda en transfermarkt
    else:
        if name == "busqueda":
            if texto_busqueda:
                txtbusqueda = texto_busqueda
            else:
                txtbusqueda = self.original_name
            texto_busqueda = platformtools.dialog_input(txtbusqueda, "Introduce el nombre correcto para buscarlo en Transfermarkt")
            if texto_busqueda:
                texto_busqueda = texto_busqueda.strip()
                data = httptools.downloadpage("http://www.transfermarkt.es/schnellsuche/ergebnis/schnellsuche?query=%s&x=0&y=0" % urllib.quote(texto_busqueda.replace("%2B", "+"))).data
                bloque = scrapertools.find_single_match(data, '<div class="table-header">Buscar resultados: Clubes(.*?)<div class="keys"')
                lista_transf = scrapertools.find_multiple_matches(bloque, '<td class="zentriert suche-vereinswappen"><img src="([^"]+)".*?alt="([^"]+)".*?href="([^"]+)"')
                next_page = scrapertools.find_single_match(bloque, '<li class="naechste-seite"><a href="([^"]+)"')
                if next_page:
                    next_page = "http://www.transfermarkt.es"+next_page.replace("&amp;", "&")
                    lista_transf.append(["http://i.imgur.com/iJrWkdL.jpg", "[COLOR green]Página siguiente >>[/COLOR]", next_page])

                items = equipos_transf(lista_transf)
                window_select.close()
                del window_select
                window_select = Select("DialogSelect.xml", config.get_runtime_path(), items=items, caption="Elige un equipo de la lista (Transfermarkt)", type="equipo", web="tf", name=self.original_name, fonts=self.fonts)
                window_select.doModal()
            else:
                window_select.close()
                del window_select

        elif "Página siguiente" in name:
                data = httptools.downloadpage(item.getProperty("url")).data
                bloque = scrapertools.find_single_match(data, '<div class="table-header">Buscar resultados: Clubes(.*?)<div class="keys"')
                lista_transf = scrapertools.find_multiple_matches(bloque, '<td class="zentriert suche-vereinswappen"><img src="([^"]+)".*?alt="([^"]+)".*?href="([^"]+)"')
                next_page = scrapertools.find_single_match(bloque, '<li class="naechste-seite"><a href="([^"]+)"')
                if next_page:
                    next_page = "http://www.transfermarkt.es"+next_page.replace("&amp;", "&")
                    lista_transf.append(["http://i.imgur.com/iJrWkdL.jpg", "[COLOR green]Página siguiente >>[/COLOR]", next_page])
                items = equipos_transf(lista_transf)
                window_select.close()
                del window_select
                window_select = Select("DialogSelect.xml", config.get_runtime_path(), items=items, caption="Elige un equipo de la lista (Transfermarkt)", type="equipo", web="tf", name=self.original_name, fonts=self.fonts)
                window_select.doModal()
        elif name != "noresult":
            window_select.close()
            del window_select
            save_data(name, self.original_name, "tf")
            platformtools.dialog_notification("Cambio guardado para Transfermarkt", self.original_name+" se sustituye por "+name, sound=False)

# Creación de items para ventana busqueda thesportsdb
def equipos_tsdb(lista_items, actual=False):
    itemlist = []
    if lista_items:
        for i, team in enumerate(lista_items):
            if i == 0 and actual:
                item = xbmcgui.ListItem(team.strTeam+" [COLOR indianred](Equipo Actual)[/COLOR]")
            else:
                item = xbmcgui.ListItem(team.strTeam)
            if not team.strTeamBadge:
                try:
                    item.setArt({"thumb":"http://i.imgur.com/qOtFja7.png"})
                except:
                    item.setThumbnailImage("http://i.imgur.com/qOtFja7.png")
            else:
                try:
                    item.setArt({"thumb":team.strTeamBadge})
                except:
                    item.setThumbnailImage(team.strTeamBadge)
            item.setProperty("name", team.strTeam)
            itemlist.append(item)
    else:
        item = xbmcgui.ListItem("[COLOR blue]Sin resultados[/COLOR]")
        try:
            item.setArt({"thumb":"http://i.imgur.com/qOtFja7.png"})
        except:
            item.setThumbnailImage("http://i.imgur.com/qOtFja7.png")
        item.setProperty("name", "noresult")
        itemlist.append(item)
    item = xbmcgui.ListItem("Buscar manualmente en TheSportsDB")
    try:
        item.setArt({"thumb":"http://i.imgur.com/qOtFja7.png"})
    except:
        item.setThumbnailImage("http://i.imgur.com/qOtFja7.png")
    item.setProperty("name", "busqueda")
    itemlist.append(item)
    return itemlist

# Creación de items para ventana busqueda transfermarkt
def equipos_transf(lista_items, actual=False):
    itemlist = []
    if lista_items:
        i = 0
        for src, name, url in lista_items:
            if not src.startswith("http:"):
                src = "http:"+src.replace("small/", "originals/")
            if i == 0 and actual:
                item = xbmcgui.ListItem(name+"  [COLOR indianred](Equipo Actual)[/COLOR]")
            else:
                item = xbmcgui.ListItem(name)
            try:
                item.setArt({"thumb":src})
            except:
                item.setThumbnailImage(src)
            item.setProperty("name", name)
            item.setProperty("url", url)
            itemlist.append(item)
            i += 1
    else:
        item = xbmcgui.ListItem("Sin resultados")
        try:
            item.setArt({"thumb":"http://i.imgur.com/iJrWkdL.jpg"})
        except:
            item.setThumbnailImage("http://i.imgur.com/iJrWkdL.jpg")
        item.setProperty("name", "noresult")
        itemlist.append(item)
        
    item = xbmcgui.ListItem("Buscar manualmente en Transfermarkt")
    try:
        item.setArt({"thumb":"http://i.imgur.com/iJrWkdL.jpg"})
    except:
        item.setThumbnailImage("http://i.imgur.com/iJrWkdL.jpg")
    item.setProperty("name", "busqueda")
    itemlist.append(item)
    return itemlist

# Guarda los nuevos datos de equipo en fichero futbol_window_data.json
def save_data(name, original_name, web):
    name = re.sub(r'(?i) de ', ' ', name).lower()
    original_name = original_name.lower()
    file_json = os.path.join(config.get_runtime_path(), 'channels', 'futbol_window_data.json')
    try:
        with open(file_json, "r+") as f:
            data_json = jsontools.load_json(f.read())
            if not data_json:
                data_json = {}
            if data_json.has_key(original_name):
                data_json[original_name][web] = name
            else:
                data_json[original_name] = {}
                if web == "tsdb":
                    data_json[original_name]["tsdb"] = name
                    data_json[original_name]["tf"] = ""
                else:
                    data_json[original_name]["tf"] = name
                    data_json[original_name]["tsdb"] = ""
            data_write = jsontools.dump_json(data_json)
            f.seek(0)
            f.write(data_write)
            f.truncate()
        global change_team
        change_team = True
    except:
        logger.info(traceback.format_exc())


# Función para sacar los canticos del equipo local
def canticos(self, name="", type=""):
    name += " "
    name = re.sub(r"FC |CF |CA |AFC |1.FSV |1.FC |CFC |UC |SSC |SM |SC ", "", name)
    if not xbmc.Player().isPlaying() and not self.songs:
        data = httptools.downloadpage("http://fanchants.es/search/?query=%s&site=5" % urllib.quote(name)).data
        equipos = scrapertools.find_multiple_matches(data, '<strong>TEAMS</strong>.*?<a href="([^"]+)" title="([^"]+)"')
        for url, equipo in equipos:
            if re.search(r"(?i)"+"|".join(name.split(" ")), equipo):
                data = httptools.downloadpage(url).data
                break
        audio = scrapertools.find_single_match(data, '<a href="([^"]+)" class="audio"')
        try:
            self.data_chant = httptools.downloadpage(audio).data
        except:
            self.suporter.setVisible(False)
            self.stop.setVisible(False)
            self.no_songs.setVisible(True)
            return
        song = scrapertools.find_single_match(self.data_chant, '<source type="audio/mp3" src="([^"]+)"')
        self.songs.append("http://fanchants.es" + song)
        xbmc.executebuiltin('xbmc.PlayMedia('+self.songs[-1]+')')
        self.next_song.setVisible(True)
    elif not xbmc.Player().isPlaying() and self.songs:
        xbmc.executebuiltin('xbmc.PlayMedia('+self.songs[self.indice_song]+')')
    elif type == "stop":
        xbmc.executebuiltin('xbmc.PlayMedia(Stop)')
    elif type == "next":
        xbmc.executebuiltin('xbmc.PlayMedia(Stop)')
        if not self.loop:
            audio = scrapertools.find_single_match(self.data_chant, '<a id="player-next" href="([^"]+)"')
            if audio:
                self.data_chant = httptools.downloadpage(audio).data
                song = scrapertools.find_single_match(self.data_chant, '<source type="audio/mp3" src="([^"]+)"')
                song = "http://fanchants.es" + song
                if not song in self.songs:
                    self.songs.append(song)
                    self.indice_song += 1
                else:
                    self.indice_song = 0
                    self.loop = True
                if not xbmc.getCondVisibility('[Control.IsVisible('+str(self.prev_song.getId())+')]'):
                    self.prev_song.setVisible(True)
        else:
            if self.indice_song == len(self.songs) -1:
                self.indice_song = 0
            if not self.indice_song:
                self.prev_song.setVisible(False)
        xbmc.executebuiltin('xbmc.PlayMedia('+self.songs[self.indice_song]+')')
    elif type == "prev":
        xbmc.executebuiltin('xbmc.PlayMedia(Stop)')
        self.indice_song -= 1
        xbmc.executebuiltin('xbmc.PlayMedia('+self.songs[self.indice_song]+')')
        if self.indice_song <= 0:
            self.prev_song.setVisible(False)

def get_fonts(skin):
    data_font = ""
    fonts = {}
    if "confluence" in skin or "estuary" in skin or "refocus" in skin:
        fonts = {"10": "font10", "12": "font12", "16": "font16", "24": "font24_title", "30": "font30"}
    elif "aeonmq" in skin:
        fonts = {"10": "font_14", "12": "font_16", "16": "font_20", "24": "font_24", "30": "font_30"}
    elif "madnox" in skin:
        fonts = {"10": "Font_Reg22", "12": "Font_Reg26", "16": "Font_Reg32", "24": "Font_Reg38", "30": "Font_ShowcaseMainLabel2_Caps"}

    if not fonts:
        try:
            data_font = open(xbmc.translatePath(os.path.join('special://skin/1080i', 'Font.xml')), "r").read()
        except:
            try:
                data_font = open(xbmc.translatePath(os.path.join('special://skin/720p', 'Font.xml')), "r").read()
            except:
                pass

    if data_font:
        fuentes = scrapertools.find_multiple_matches(data_font, "<name>([^<]+)<\/name>(?:<![^<]+>|)\s*<filename>[^<]+<\/filename>\s*<size>(\d+)<\/size>")
        sizes = []
        try:
            for name, size in fuentes:
                size = int(size)
                sizes.append([size, name])
            sizes.sort()
            fonts["10"] = sizes[0][1].lower()
            check = False
            if not 12 in sizes:
                for size, name in sizes:
                    if size != fonts["10"]:
                        fonts["12"] = name.lower()
                        check = True
                        break
            for size, name in sizes:
                if size == 12 and not check:
                    fonts["12"] = name.lower()
                elif size == 16:
                    fonts["16"] = name.lower()
                elif size == 24:
                    fonts["24"] = name.lower()
                elif size == 30:
                    fonts["30"] = name.lower()
                    break
                elif size > 30 and size <= 33:
                    fonts["30"] = name.lower()
                    break
        except:
            pass
    if not fonts:
        fonts = {"10": "font10", "12": "font12", "16": "font16", "24": "font24", "30": "font30"}

    return fonts
