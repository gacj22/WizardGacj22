# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
#------------------------------------------------------------

import re
import datetime
import time
import urllib
from core import httptools
from core.scrapertools import *

from core import filetools
from core import config

host = "http://www.resultados-futbol.com/"

def get_matches(url):
    data = httptools.downloadpage(url, cookies=False).data
    data = re.sub(r"\n|\r|\t", '', data)
    
    now = datetime.datetime.today()
    prio = ["Primera Divisi\xc3\xb3n", "Segunda Divisi\xc3\xb3n", "Copa del Rey", "Premier League", "Serie A", "Bundesliga", "Champions League",
            "Mundial", "Eurocopa", "Supercopa Europa", "Mundial de Clubes", "Supercopa"]
    prio2 = ["Ligue 1", "Liga Portuguesa", "Liga Holandesa", "Europa League", "Clasificación Mundial Europa",
             "Clasificación Mundial Sudamérica", "EFL Cup", "FA Cup"]
    partidos = []
    bloques = find_multiple_matches(data, '<div class="title">.*?<a.*?>(.*?) »</a>(.*?)</table>')
    for liga, bloque in bloques:
        priority = 3
        if liga in prio:
            priority = 1
        elif "Clasificación Mundial Sudamérica" in liga or "Clasificación Mundial Europa" in liga or "Mundial Grupo" in liga \
            or "Eurocopa Grupo" in liga or "Clasificación Eurocopa" in liga or liga in prio2:
            priority = 2

        patron = '<div class="chk_hour"[^>]+>([^<]+)<.*?<td class="timer">.*?>(.*?)</span>.*?' \
                 'src="([^"]+)".*?<a[^>]+>([^<]+)<.*?<a href="([^"]+)".*?<div class="clase" data-mid="([^"]+)"[^>]*>' \
                 '(.*?)</div>.*?src="([^"]+)".*?<a[^>]+>([^<]+)<'
        matches = find_multiple_matches(bloque, patron)
        for hora, estado, t1thumb, team1, url, matchid, score, t2thumb, team2 in matches:
            h, m = hora.split(":")
            time_match = datetime.datetime(now.year, now.month, now.day, int(h), int(m))
            estado = htmlclean(estado).replace("\xc2\xa0", "")
            t1thumb = t1thumb.rsplit("?", 1)[0].replace("/small/", "/original/")
            t2thumb = t2thumb.rsplit("?", 1)[0].replace("/small/", "/original/")
            if "chk_hour" in score or "Aplazado" in estado:
                score = "-- : --"
            score = htmlclean(score)
            canal = find_single_match(bloque, '<td class="icons"><img src="([^"]+)"')
            if canal:
                canal = canal.replace(".gif", ".png")
                if not canal.startswith(host):
                    canal = host + canal
            partidos.append({"url": url, "hora": hora, "team1": team1, "team2": team2, "score": score,
                             "thumb1": t1thumb, "thumb2": t2thumb, "estado": estado, "liga": liga,
                             "priority": priority, "time_match": time_match, "matchid": matchid,
                             "canal": canal})

    partidos.sort(key=lambda p:(p['priority'], p["time_match"]))
    next = find_single_match(data, '<li class="nav2 navsig">\s*<a href="([^"]+)"')
    prev = find_single_match(data, '<li class="nav2 navant">\s*<a href="([^"]+)"')
    today = find_single_match(data, '<span class="titlebox date">([^<]+)</span>').replace("Partidos ", "")
    partidos.append({"next": next, "prev": prev, "today": today})

    return partidos

def get_minutos(url):
    data = httptools.downloadpage(url, cookies=False).data
    data = re.sub(r"\n|\r|\t", '', data)
    minuto = find_single_match(data, '<span class="jor-status.*?>([^<]+)<').replace("DIRECTO (", "").replace(")", "")

    return minuto

def refresh_score():
    from core import jsontools
    try:
        data = httptools.downloadpage("http://www.resultados-futbol.com/ajax/refresh_live.php").data
        data = jsontools.load_json(data)
        if not data:
            data = {}
        return data
    except:
        return {}

def get_info(url, reload=False):
    data = httptools.downloadpage(url, cookies=False).data
    data = re.sub(r"\n|\r|\t", '', data)
    
    jornada = find_single_match(data, '<div class="jornada".*?>([^<]+)</a>')
    fecha = find_single_match(data, '<span itemprop="startDate"[^>]+>([^<]+)<')
    minuto = find_single_match(data, '<span class="jor-status.*?>([^<]+)<').replace("DIRECTO (", "").replace(")", "")

    try:
        score1, score2 = find_multiple_matches(data, '<span class="claseR"[^>]+>(\d+)')
        hora = ""
    except:
        score1 = score2 = ""
        hora = find_single_match(data, '<span class="chk_hour".*?>([^<]+)<')

    try:
        t1am, t1roj = find_single_match(data, '<div class="te1"><span class="am">(\d+)</span><span class="ro">(\d+)')
        t2am, t2roj = find_single_match(data, '<div class="te2"><span class="am">(\d+)</span><span class="ro">(\d+)')
    except:
        t1am = t1roj = t2am = t2roj = "0"

    ref = find_single_match(data, 'Arbitro:\s*([^<]+)</span>').replace("\xc2\xa0", "")
    stadium = find_single_match(data, 'Estadio:\s*([^<]+)</span>').replace("\xc2\xa0", "")

    team1 = find_single_match(data, '<div class="team equipo1".*?<b itemprop="name" title="([^"]+)"')
    team2 = find_single_match(data, '<div class="team equipo2".*?<b itemprop="name" title="([^"]+)"')
    thumb1 = find_single_match(data, '<div class="team equipo1".*?src="([^"]+)"').replace("/medium/", "/original/").rsplit("?", 1)[0]
    thumb2 = find_single_match(data, '<div class="team equipo2".*?src="([^"]+)"').replace("/medium/", "/original/").rsplit("?", 1)[0]
    url1 = find_single_match(data, '<div class="team equipo1".*?href="([^"]+)"')
    if url1 and not url1.startswith(host):
        url1 = host[:-1] + url1
    url2 = find_single_match(data, '<div class="team equipo2".*?href="([^"]+)"')
    if url2 and not url2.startswith(host):
        url2 = host[:-1] + url2
    info = {"jornada": jornada, "fecha": fecha, "minuto": minuto, "ref": ref, "url1": url1, "url2": url2,
            "score1": score1, "score2": score2, "hora": hora, "estadio": stadium,
            "t1am": t1am, "t1roj": t1roj, "t2am": t2am, "t2roj": t2roj, "name1": team1, "name2": team2,
            "thumb1": thumb1, "thumb2": thumb2}

    img_stadium = find_single_match(data, '<div id="tab_match_stadium" class="dm_estadio dm_box hidden">\s*<img src="([^"]+)"').replace("?size=x85", "")
    asistencia = find_single_match(data, '<span itemprop="attendees">([^<]+)</span>')
    capacidad = find_single_match(data, '<li><strong>Capacidad:</strong>([^<]+)</li>')
    if capacidad:
        capacidad = "Capacidad: " + capacidad
    dimen = find_single_match(data, '<li><strong>Dimensiones:</strong>([^<]+)</li>')
    if dimen:
        dimen = "Dimensiones: " + dimen
    inagura = find_single_match(data, '<li><strong>Inaguraci.*?>([^<]+)</li>')
    if inagura:
        inagura = "Inauguración: " + inagura
    info["stadium"] = {"stadium": stadium, "img_stadium": img_stadium, "asistencia": asistencia, "capacidad": capacidad, "dimen": dimen, "inagura": inagura}
    
    info["cronica"] = []
    matches = find_multiple_matches(data, '<tr class="post post_cronica(.*?)</tr>')
    for content in matches:
        bold = False
        if "cronica_bold" in content:
            bold = True
        destaca = False
        if "cronica_important" in content:
            destaca = True
        time_ = find_single_match(content, 'class="cronica_time_value">([^<]+)<')
        text = find_single_match(content, '<div class="cronica_content">(.*?)</div>').replace("\xc2\xa0", "")
        ico = find_single_match(content, 'src="([^"]+)"')
        info["cronica"].append({"text": text, "time": time_, "ico": ico, "bold": bold, "destaca": destaca})

    info["team1"] = {}
    info["team1"]["formation"] = find_single_match(data, '<div class="team team1">.*?<small class="align-code">([^<]+)<')
    info["team1"]["once"] = []
    once = find_multiple_matches(data, 'id="dreamteam1"(.*?)</li>')
    if not once:
        bloque = find_single_match(data, '<div class="team team1">(.*?)</ul>')
        once = find_multiple_matches(bloque, '<li>\s*<small class="align-dorsal(.*?)</li>')
    for jug in once:
        name = find_single_match(jug, 'title="([^"]+)"')
        if not name:
            name = find_single_match(jug, 'href=.*?>(.*?)<')
        img = find_single_match(jug, 'src="([^"]+)"').replace("?size=38x&5", "")
        num = find_single_match(jug, '<span class="num".*?>(\d+)')
        if not num:
            num = find_single_match(jug, '<span class="align-dorsal.*?>(\d+)<')
        url = find_single_match(jug, 'href="([^"]+)"')
        #url = re.sub(r'/\d{4}/', '/', url)
        if url and not url.startswith(host):
            url = host[:-1] + url
        info["team1"]["once"].append({"name": name, "img": img, "num": num, "url": url})
    supl = find_multiple_matches(data, '<div class="team team1">.*?Suplentes(.*?)</ul>')
    info["team1"]["supl"] = []
    for bloque in supl:
        matches = find_multiple_matches(bloque, '<small class="align-dorsal ">(.*?)<.*?<a href="([^"]+)".*?>([^<]+)<')
        for num, url, name in matches:
            #url = re.sub(r'/\d{4}/', '/', url)
            if url and not url.startswith(host):
                url = host[:-1] + url
            info["team1"]["supl"].append({"num": num, "name": name, "url": url})

    info["team2"] = {}
    info["team2"]["formation"] = find_single_match(data, '<div class="team team2">.*?<small class="align-code">([^<]+)<')
    info["team2"]["once"] = []
    once = find_multiple_matches(data, 'id="dreamteam2"(.*?)</li>')
    if not once:
        bloque = find_single_match(data, '<div class="team team2">(.*?)</ul>')
        once = find_multiple_matches(bloque, '<li>\s*<small class="align-dorsal(.*?)</li>')
    for jug in once:
        name = find_single_match(jug, 'title="([^"]+)"')
        if not name:
            name = find_single_match(jug, 'href=.*?>(.*?)<')
        img = find_single_match(jug, 'src="([^"]+)"').replace("?size=38x&5", "")
        num = find_single_match(jug, '<span class="num".*?>(\d+)')
        if not num:
            num = find_single_match(jug, '<span class="align-dorsal.*?>(\d+)<')
        url = find_single_match(jug, 'href="([^"]+)"')
        #url = re.sub(r'/\d{4}/', '/', url)
        if url and not url.startswith(host):
            url = host[:-1] + url
        info["team2"]["once"].append({"name": name, "img": img, "num": num, "url": url})

    supl = find_multiple_matches(data, '<div class="team team2">.*?Suplentes(.*?)</ul>')
    info["team2"]["supl"] = []
    for bloque in supl:
        matches = find_multiple_matches(bloque, '<small class="align-dorsal ">(.*?)<.*?<a href="([^"]+)".*?>([^<]+)<')
        for num, url, name in matches:
            #url = re.sub(r'/\d{4}/', '/', url)
            if url and not url.startswith(host):
                url = host[:-1] + url
            info["team2"]["supl"].append({"num": num, "name": name, "url": url})

    sprites = {'1': 'gol', '2': 'anulado', '3': 'penalty_fallado', '4': 'lesion', '5': 'asistencia',
               '6': 'sale', '7': 'entra', '8': 'amarilla', '9': 'roja', '10': 'doble', '11': 'penalty',
               '12': 'propia', '13': 'poste'}
    info["eventos"] = []
    matches = find_multiple_matches(data, '<div class="evento"(.*?)</span></div></div>')
    for bloque in matches:
        minuto = find_single_match(bloque, '<b>minuto</b>\s*(\d+)\'')
        img = find_single_match(bloque, '<img src="([^"]+)"').replace("?size=38x&5", "")
        desc = find_single_match(bloque, '<small>(.*?)</a>')
        desc = htmlclean(desc)
        desc = re.compile("<h5[^>]*>",re.DOTALL).sub("", desc)
        equipo, evento = find_single_match(bloque, '<span class="(right|left) event_(\d+)">')
        equipo = equipo.replace("left", "l").replace("right", "v")
        url = find_single_match(bloque, '<a href="([^"]+)"')
        #url = re.sub(r'/\d{4}/', '/', url)
        if url and not url.startswith(host):
            url = host[:-1] + url
        try:
            evento = sprites[evento]
            evento = filetools.join(config.get_runtime_path(), 'resources', 'images', 'matchcenter', '%s.png' % evento)
        except:
            evento = ""

        info["eventos"].append({"minuto": minuto, "equipo": equipo, "evento": evento, "desc": desc, "img": img, "url": url})
    if info["eventos"]:
        info["eventos"].sort(key=lambda i:int(i["minuto"].zfill(2)))

    info["stats"] = []
    matches = find_multiple_matches(data, '<tr class="barstyle bar4">.*?>(\d+[%]*)<.*?<h6>([^<]+)<.*?>(\d+[%]*)<')
    for local, tipo, visit in matches:
        info["stats"].append({"l": local, "v": visit, "tipo": tipo})

    info["videos"] = []
    matches = find_multiple_matches(data, '<a target="[^"]*" href="([^"]+)" title="([^"]+)" class="list-title match-video-link">')
    for url, title in matches:
        url = url.replace("cc.sporttube.com/embed/", "www.sporttube.com/play/")
        info["videos"].append({"url": url, "title": title})

    info["news"] = []
    matches = find_multiple_matches(data, '<h2 class="ni-title"><a href="([^"]+)">([^<]+)<.*?<span class="ni-date">([^<]+)<')
    for url, title, date in matches:
        info["news"].append({"url": url, "title": title, "date": date})

    info["tv"] = []
    matches = find_multiple_matches(data, '<td class="dptvt_name">.*?src="([^"]+)" alt="([^"]+)".*?<td>([^<]+)<.*?<td>([^<]+)<')
    for logo, nombre, tipo, idioma in matches:
        if tipo == "WEB":
            continue
        logo = host + logo.replace(".gif", ".png")
        nombre = nombre + " / " + idioma
        info["tv"].append({'logo': logo, 'nombre': nombre})

    if url1 and not reload:
        info["coach1"], info["twitter1"], info["nombre_corto1"] = get_data_team(url1)
    if url2 and not reload:
        info["coach2"], info["twitter2"], info["nombre_corto2"] = get_data_team(url2)

    return info


def get_table(league):
    if not league.startswith("http"):
        league = "%s%s" % (host, league)
    data = httptools.downloadpage(league, cookies=False).data
    data = re.sub(r"\n|\r|\t", '', data)
    
    equipos = []
    liga2, liga = find_single_match(data, '<small class="temp".*?(?:>([^<]+)</h3>|<div class="botonlivs">).*?<h1 >([^<]+)</h1>')
    if liga2:
        liga += " - %s" % liga2

    temporadas = []
    bloque = find_single_match(data, '<div id="desplega_temporadas"(.*?)</ul>')
    matches = find_multiple_matches(bloque, '<li(.*?)><a href="([^"]+)">Temp. (\d+)')
    for estado, url, temp in matches:
        select = False
        if "act" in estado:
            select = True
        temp = "%s/%s" % (int(temp)-1, temp)
        temporadas.append({"url": url, "temp": temp, "select": select})

    patron = '<tr class="(?:impar|cmp)"><th class="([^"]+)">(\d+)</th>.*?src="([^"]+)".*?href=\'([^\']+)\'>([^<]+)<' \
             '.*?>(\d+)</td>.*?>(\d+)</td>.*?>(\d+)</td>.*?>(\d+)</td>.*?>(\d+)</td>.*?>(\d+)</td>' \
             '.*?>(\d+)</td>'
    matches = find_multiple_matches(data, patron)
    for color, pos, img, url, team, pts, pj, win, draw, lose, gf, gc in matches:
        img = img.replace("?size=37x&5", "").replace("small", "original")
        url = "%spartidos%s" % (host, url)
        if "-cha" in color:
            color = "green"
        elif "-prev" in color:
            color = "blue"
        elif "-uefa" in color:
            color = "red"
        elif "-desc" in color:
            color = "red_strong"
        else:
            color = "fo"
        equipos.append({"url": url, "team": team, "img": img, "pos": pos, "pts": pts, "pj": pj, "win": win,
                        "draw": draw, "lose": lose, "gf": gf, "gc": gc, "color": color, "liga": liga})

    return equipos, temporadas


def get_team_matches(team):
    data = httptools.downloadpage(team, cookies=False).data
    data = re.sub(r"\n|\r|\t", '', data)

    year1, year2 = find_single_match(data, '<span>Temporada (\d+)/(\d+)')
    meses = {'Ene': 1, 'Feb': 2, 'Mar': 3, 'Abr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Ago': 8,
           'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dic': 12}
    final = []
    next = []
    bloques = find_multiple_matches(data, '<div class="title"><img alt="(.*?)"(.*?)</table>')
    for torneo, bloque in bloques:
        patron = '<td class="time".*?>([^<]+)<.*?<td class="timer">.*?>([^<]+)</span.*?<td class="team-home">.*?<a.*?>([^<]+)<' \
             '.*?src="([^"]+)".*?href="([^"]+)".*?<div class="clase".*?>([^<]+)<.*?src="([^"]+)".*?<a.*?>([^<]+)<'
        matches = find_multiple_matches(bloque, patron)
        for fecha, status, team1, img1, url, score, img2, team2 in matches:
            img1 = img1.replace("?size=37x&5", "").replace("small", "original")
            img2 = img2.replace("?size=37x&5", "").replace("small", "original")
            status = status.replace("\xc2\xa0", "")
            dia, mes, year = fecha.split(" ")
            mes = meses[mes]
            if year == year1[2:]:
                year = year1
            else:
                year = year2
            fecha_ord = datetime.date(int(year), mes, int(dia))
            if "Finalizado" in status or "'" in status or "Aplazado" in status or "Des" in status:
                if "'" in status or "Des" in status:
                    score = "[COLOR red]%s[/COLOR]" % score
                final.append({"fecha": fecha, "team1": team1, "team2": team2, "img1": img1, "img2": img2,
                              "score": score, "url": url, "torneo": torneo, "fecha_ord": fecha_ord})
            else:
                next.append({"fecha": fecha, "team1": team1, "team2": team2, "img1": img1, "img2": img2,
                             "score": score, "url": url, "status": status, "torneo": torneo, "fecha_ord": fecha_ord})

    final.sort(key=lambda x:x["fecha_ord"])
    next.sort(key=lambda x:x["fecha_ord"])
    return final, next


def get_data_team(url):
    data = httptools.downloadpage(url, cookies=False).data
    data = re.sub(r"\n|\r|\t", '', data)
    coach = ""
    if not re.search(r'/(\d){4}', url):
        coach = find_single_match(data, 'name="managerNow" size="60" value="(.*?)"')
    nombre_corto = find_single_match(data, 'name="short_name" size="60" value="(.*?)"')
    twitter = find_single_match(data, 'name="twitter" size="60" value="(.*?)"')
    twitter = htmlclean(twitter)
    if twitter.startswith("@"):
        twitter = twitter[1:]

    return coach, twitter, nombre_corto


def get_player_info(player_url):
    data = httptools.downloadpage(player_url, cookies=False).data
    data = re.sub(r"\n|\r|\t", '', data)

    info = {}
    info["escudo"] = find_single_match(data, '<div class="img-shield">\s*<img src="([^"]+)"').replace("?size=120x&3", "")
    info["position"] = htmlclean(find_single_match(data, '<div class="info position">(.*?)</a>'))
    info["temp"] = find_single_match(data, '<div class="player-season">.*?<span>([^<]+)<')
    try:
        info["equipo"], info["liga"] = find_single_match(data, '<div class="inner_txt">.*?>([^<]+)</a>.*?>([^<]+)</a>')
    except:
        info["equipo"], info["liga"] = find_single_match(data, '<div class="inner temp-from">.*?>([^<]+)</a>.*?>([^<]+)</a>')
    info["nombre"] = find_single_match(data, '<dt>Completo</dt>\s*<dd>([^<]+)<')
    
    info["seasons"] = []
    bloque = find_single_match(data, '<ul id="selector_temporadas".*?</ul>')
    matches = find_multiple_matches(bloque, '<li><a href="([^"]+)" class="(.*?)">([^<]+)<')
    for url, select, season in matches:
        select = (select)
        info["seasons"].append({"url": url, "season": season, "select": select})

    info["ficha"] = []
    edad = find_single_match(data, '<dt>Edad</dt>\s*<dd>([^<]+)<').strip()
    if edad:
        info["ficha"].append("[B]Edad: [/B]" + edad)
    fecha_nac = find_single_match(data, '<dt>Fecha de nacimiento</dt>\s*<dd>([^<]+)<').strip()
    if fecha_nac:
        info["ficha"].append("[B]Fecha de Nacimiento: [/B]" + fecha_nac)

    lugar = find_single_match(data, '<dt>Lugar de.*?>([^<]+)</dd>').strip()
    if lugar:
        info["ficha"].append("[B]Nacido en: [/B]" + lugar)
    pais = find_single_match(data, '<dt>País.*?>([^<]+)</dd>').strip()
    if pais:
        info["ficha"].append("[B]País: [/B]" + pais)
    
    puesto = find_single_match(data, '<dt>Demarcación</dt>\s*<dd>([^<]+)<').strip()
    if puesto:
        info["ficha"].append("[B]Posición: [/B]" + puesto)

    nacion = find_single_match(data, '<dt>Nacionalidad</dt>\s*<dd>([^<]+)<').strip()
    if nacion:
        info["ficha"].append("[B]Nacionalidad: [/B]" + nacion)

    altura = find_single_match(data, '<dt>Altura</dt>\s*<dd>([^<]+)<').strip()
    if altura:
        info["ficha"].append("[B]Altura: [/B]" + altura)
    peso = find_single_match(data, '<dt>Peso</dt>\s*<dd>([^<]+)<').strip()
    if peso:
        info["ficha"].append("[B]Peso: [/B]" + peso)
    
    twitter = find_single_match(data, '<dt>Twitter</dt>.*?>([^<]+)</a>')
    if twitter.startswith("@"):
        twitter = twitter[1:]
    info["twitter"] = twitter

    info["stats"] = []
    tipo = ['pj', 'titu', 'compl', 'supl', 'minutos', 'tam', 'troj', 'asist', 'goles']
    bloque = find_single_match(data, 'class="u-lined">Estadísticas(.*?)</table>')
    bloques = find_multiple_matches(bloque, '<th class="name">(.*?)</tr>')
    for b in bloques:
        img = find_single_match(b, 'src="([^"]+)"')
        liga = find_single_match(b, '<span class="team-name">([^<]+)<')
        match = find_multiple_matches(b, '<td>([^<]+)</td>')
        info["stats"].append({'img': img, 'liga': liga})
        for i, m in enumerate(match):
            info["stats"][-1][tipo[i]] = m

    info["news"] = []
    matches = find_multiple_matches(data, '<h2 class="ni-title"><a href="([^"]+)">([^<]+)<.*?<span class="ni-date">([^<]+)<')
    for url, title, date in matches:
        info["news"].append({"url": url, "title": title, "date": date})

    info["trayectoria"] = []
    tipo = ['temp', 'div', 'edad', 'pj', 'titu', 'compl', 'entra', 'sale', 'tam', 'troj', 'goles', 'minutos']
    bloque = find_single_match(data, 'Trayectoria<(.*?)</table>')
    bloques = find_multiple_matches(bloque, '<th class="name">(.*?)</tr>')
    for b in bloques:
        equipo = find_single_match(b, '<span class="team-name">([^<]+)<')
        match = find_multiple_matches(b, '<td[^>]*>(.*?)</td>')
        info["trayectoria"].append({'equipo': equipo})
        for i, m in enumerate(match):
            info["trayectoria"][-1][tipo[i]] = m
    info["trayectoria"].reverse()

    info["historico"] = []
    if not info["trayectoria"]:
        bloque = find_single_match(data, '<div id="historico_box"(.*?)</script>')
        matches = find_multiple_matches(bloque, '<h6 class="title-name">.*?src="([^"]+)".*?<span>([^<]+)</span>(.*?)</ul>')
        for img, equipo, temps in matches:
            seasons = find_multiple_matches(temps, '<li><a.*?>([^<]+)<')
            info["historico"].append({'img': img, 'equipo': equipo, 'seasons': ", ".join(seasons)})

    info["titulos"] = []
    matches = find_multiple_matches(data, '<div class="player-title">\s*<h6 class="title-name">(.*?)</h6>(.*?)</ul>')
    for titulo, temps in matches:
        copa, veces = find_single_match(titulo, '(.*?)\s*<small class="bullet">(\d+)</small>')
        copa = copa.replace("Liga Inglesa", 'Premier League').replace("Liga Italiana", "Serie A") \
                   .replace("Liga Holandesa", "Eredivisie").replace("Liga Alemana", "Bundesliga")
        titulo = "%s (%s)" % (copa, veces)
        seasons = find_multiple_matches(temps, '<li>([^<]+)</li>')
        info["titulos"].append({'titulo': titulo, "seasons": ", ".join(seasons), 'copa': copa})

    info["efeme"] = []
    bloque = find_single_match(data, '<h6 class="title-name">(.*?)</dl>')
    matches = find_multiple_matches(bloque, '<dt>([^<]+)</dt>\s*<dd>(.*?)</dd>')
    for desc, value in matches:
        if "<" in value:
            value = htmlclean(value)
            part, percent = value.split(" ", 1)
            value = "%s (%s)" % (percent, part)
        info["efeme"].append({'desc': desc, 'value': value})

    info["fotos"] = []
    if '/fotos">Fotos</a' in data:
        data_foto = httptools.downloadpage(player_url+"/fotos", cookies=False).data
        data_foto = re.sub(r"\n|\r|\t", '', data_foto)
        matches = find_multiple_matches(data_foto, '<div class="itemimg first">.*?src="([^"]+)"')
        for img in matches:
            img = img.rsplit("?", 1)[0]
            info["fotos"].append(img)
    else:
        info["fotos"].append(find_single_match(data, '<div id="previewArea">\s*<img src="([^"]+)"').replace("?size=120x&3", ""))
    
    return info


def get_news(url=""):
    idiomas = [["es", "noticias"], ["www", "news"], ["fr", "infos"], ["pt", "noticias"]]
    idioma = idiomas[int(config.get_setting("matchcenter_news"))]
    if not url:
        url = "http://%s.besoccer.com/%s" % (idioma[0], idioma[1])
    data = httptools.downloadpage(url, cookies=False).data
    data = re.sub(r"\n|\r|\t", '', data)

    news = {}
    patron = '<div class="new-item ni-half">.*?href="([^"]+)".*?src="([^"]+)".*?>([^<]+)</a></h2>.*?' \
             '<span class="ni-date">(.*?)<.*?<p class="ni-subtitle">(.*?)</p>'
    matches = find_multiple_matches(data, patron)
    i = 0
    for url, thumb, title, date, subtitle in matches:
        url = "http://%s.besoccer.com%s" % (idioma[0], url)
        news[i] = {"url": url, "thumb": thumb, "title": title, "date": date, "subtitle": subtitle}
        i += 1

    next_page = find_single_match(data, '<a href="([^"]+)" aria-label="Next">\s*<i class="md md-chevron-right">')
    if next_page:
        next_page = "http://%s.besoccer.com%s" % (idioma[0], next_page)
        news["next_page"] = next_page

    return news


def get_portadas():
    data = httptools.downloadpage("http://www.diariosdefutbol.com/portadas-deportivos/", cookies=False).data
    data = re.sub(r"\n|\r|\t", '', data)

    portadas = []
    first = True
    patron = "<a class='group1' href='([^']+)'"
    matches = find_multiple_matches(data, patron)
    if not matches:
        data = httptools.downloadpage("http://movil.resultados-futbol.com/portadas", cookies=False).data
        data = re.sub(r"\n|\r|\t", '', data)
        bloque = find_single_match(data, '<div id="ct-widget-gallery"(.*?)</ul>')
        matches = find_multiple_matches(bloque, 'src="([^"]+)"')
        first = False
        
    for thumb in matches:
        if first:
            thumb = "http://www.diariosdefutbol.com" + thumb
        else:
            thumb = thumb.rsplit("?", 1)[0]
        portadas.append(thumb)

    return portadas


def get_agenda(url="deporte", data_canales=""):
    data = httptools.downloadpage("http://www.futbolenlatv.com/%s" % url, cookies=False).data
    data = re.sub(r"\n|\r|\t", '', data)

    if not data_canales:
        data_canales = httptools.downloadpage("http://www.futbolenlatv.com/canal", cookies=False).data
        data_canales = re.sub(r"\n|\r|\t", '', data_canales)

    eventos = []
    bloques = find_multiple_matches(data, 'class="(?:hidden-md hidden-lg|) dia-partido">([^<]+)<(.*?)(?:<tr class="">|</table>)')
    for dia, bloque in bloques:
        patron = '<tr class="event-row hidden-xs">.*?<td class="hora">([^<]+)<.*?url\(\'([^\']+)\'' \
                 '.*?<span title="([^"]+)"(.*?)</ul>(.*?)<td class="canales">(.*?)</ul>'
        matches = find_multiple_matches(bloque, patron)
        dia = decodeHtmlentities(dia)
        if matches:
            eventos.append({dia: []})
        for hora, icono, titulo, subtitle, info, canales in matches:
            subtitle1 = find_single_match(subtitle, '<li class="detalles-jornada">([^<]+)<')
            subtitle2 = find_single_match(subtitle, '<li class="detalles-detalles" title="([^"]+)"')
            if subtitle2:
                subtitle1 += " - " + subtitle2

            subtitle = decodeHtmlentities(subtitle1)
            titulo = decodeHtmlentities(titulo)

            info_evento = []
            patron = '<td class="local">.*?<span title="([^"]+)".*?<img src="([^"]+)".*?<img src="([^"]+)".*?<span title="([^"]+)"'
            match = find_single_match(info, patron)
            if not match:
                patron = '<td colspan="2" class="evento">(.*?)</td>'
                match = [find_single_match(info, patron)]
            for elem in match:
                elem = elem.replace("<br />", "\n")
                if "/img/32/" in elem:
                    elem = elem.replace("/img/32/", "/img/")
                elem = decodeHtmlentities(elem)
                info_evento.append(elem)

            canales_l = []
            patron = '<li class.*?title="([^"]+)"'
            match = find_multiple_matches(canales, patron)
            for canal in match:
                canal_search = canal.replace("(", "\(").replace(")", "\)")
                src = find_single_match(data_canales, 'src="([^"]+)" alt="%s"' % canal_search).replace("/img/32/", "/img/")
                src = urllib.quote(decodeHtmlentities(src), safe=":/")
                canal = decodeHtmlentities(canal)
                canales_l.append([canal, src])
            icono = icono.replace("/img/32/", "/img/")
            icono = urllib.quote(decodeHtmlentities(icono), safe=":/")
            eventos[-1][dia].append({'hora': hora, 'icono': icono, 'titulo': titulo, 'subtitle': subtitle,
                                     'info_evento': info_evento, 'canales': canales_l})

    return eventos, data_canales


def get_live_moto(url=""):
    from core import jsontools
    gp = ""
    numero = ""
    if not url:
        data = jsontools.load_json(httptools.downloadpage("http://api.stats.foxsports.com.au/3.0/api/scoreboard/profiles/foxsports_motorsport.json;masthead=foxsports?userkey=A00239D3-45F6-4A0A-810C-54A347F144C2").data)
        data = data[0]["series_scoreboards"]
        for v in data:
            if v["series"]["name"] == "MotoGP":
                urls = []
                for value in v["scoreboards"]:
                    url_ = "http://api.stats.foxsports.com.au/3.0/api/sports/motor/meetings/%s/sessions.json?userkey=A00239D3-45F6-4A0A-810C-54A347F144C2" % value["score"]["meeting"]["id"]
                    urls.append([url_, value["score"]["match_status"], value["score"]["meeting"]["name"], value["score"]["round"]["number"]])
        urls.reverse()
        for u in urls:
            if u[1] not in ["Complete", "Pre Meeting"]:
                url = u[0]
                gp = u[2]
                numero = str(u[3])
                break

        if not url:
            for u in urls:
                if u[1]  == "Complete":
                    url = u[0]
                    gp = u[2]
                    numero = str(u[3])
                    break
            
    sessions = {}
    data = httptools.downloadpage(url).data
    if not '"status":"Ended"' in data and gp:
        for u in urls:
            if u[1]  == "Complete":
                url = u[0]
                gp = u[2]
                numero = str(u[3])
                break
        data = httptools.downloadpage(url).data

    data = jsontools.load_json(data).get("series_sessions")
    for v in data:
        sessions[v["name"]] = []
        for value in v["sessions"]:
            sessions[v["name"]].append({'status': value["status"], 'name': value["supplier_session_code"],
                                        'laps': value["laps"], 'id': value["id"], 'remain': value.get("remaining_laps", 0)})
                        
    return url, sessions, gp, numero


def get_live_details_moto(id, drivers=True):
    from core import jsontools

    pilotos = {}
    if drivers:
        data = jsontools.load_json(httptools.downloadpage("http://api.stats.foxsports.com.au/3.0/api/sports/motor/sessions/%s/drivers.json?userkey=A00239D3-45F6-4A0A-810C-54A347F144C2" % id).data)["sessions_drivers"]
        for v in data:
            pilotos[v["number"]] = {'team': v["vehicle"], 'name': unicode(v["drivers"][0]["short_name"], 'utf-8'), 'number': v["number"],
                                    'id': v["drivers"][0]["id"], 'full': unicode(v["drivers"][0]["full_name"], 'utf-8'),
                                    'birth': v["drivers"][0]["date_of_birth"], 'team_name': v["team"]["name"],
                                    'h': v["drivers"][0]["height_cm"], 'w': v["drivers"][0]["weight_kg"]}

    datos = []
    data = jsontools.load_json(httptools.downloadpage("http://api.stats.foxsports.com.au/3.0/api/sports/motor/sessions/%s/leaderboard.json?userkey=A00239D3-45F6-4A0A-810C-54A347F144C2" % id).data)["stats"]
    for v in data:
        sectors = []
        for s in v["sectors_with_time_and_status"]:
            sectors.append(s["status"])
        datos.append({'number': v["number"], "laptime": v["last_lap"]["time"], "status_lap": v["last_lap"]["status"],
                       'bestlap': v["best_lap"]["time"], 'lap': v["current_lap_number"], 'pit': v["pit_lane_status"],
                       'gap': v["gap_to_next"], 'gap_t': v["gap_to_lead"], 'sectors': sectors, 'pos': v["position"].replace("DNF", "100"),
                       'grid': v["grid_position"]})

    datos.sort(key=lambda it:int(it['pos']))

    return pilotos, datos


def get_data_piloto(data, piloto, mode):
    if not data:
        data = httptools.downloadpage("http://www.motogp.com/es/riders/%s" % mode).data
    thumb = find_single_match(data, '(?i)title="%s".*?><img alt="[^"]*" src="([^"]+)"' % piloto.encode("utf-8"))
    if not thumb:
        name_p = quita_tildes(piloto.encode("utf-8"))
        thumb = find_single_match(data, '(?i)title="%s".*?><img alt="[^"]*" src="([^"]+)"' % name_p)
    if not thumb:
        thumb = "http://www.motogp.com/en/api/rider/photo/grid/old/0000"
    moto = thumb.replace("/grid/", "/bike/")

    return thumb, moto, data


def get_comments_motos(url="motogp", race=""):
    comments = []
    if url == "motogp":
        n = "73058"
    elif url == "moto2":
        n = "73059"
    else:
        n = "73060"
    data = httptools.downloadpage("http://www.rtve.es/deportes/module/motor/%s/en-directo/narracion/%s/%s/rd" % (url, n, race)).data

    iconos = {'3_3': 'adelantamiento_v1', '3_2': 'adelantamiento_v1', '1_5': 'abandono', '7_2': 'reloj',
              '11_8': 'bandera_finish', '14_1': 'bandera_amarilla', '13_4': 'accidente', '14_3': 'bandera_roja',
              '14_4': 'bandera_verde', '2_1': 'boxes', '14_5': 'safety_car', '8_3': 'lluvia'}
    bloque = find_single_match(data, '<ul class="minutoaminuto motor">(.*?)</ul>')
    matches = find_multiple_matches(bloque, '<div class="parcial">\s*(.*?)</div>.*?<span class="evento_([^"]+)".*?' \
                                            '<div class="narracion">.*?<span>([^<]+)<')
    for vuelta, icono, msg in matches:
        msg = msg.replace("Vuelta rápide", "Vuelta rápida")
        vuelta = htmlclean(vuelta).strip()
        ico = ""
        if iconos.get(icono):
            ico = "http://www.irtve.es/css/rtve.deportes/rtve.deportes.resultados/i/eventos-motor/%s.png" % iconos[icono]
        comments.append([vuelta, msg, ico])

    return comments


def get_calendario_motos(season=""):
    circuitos = []

    data = httptools.downloadpage("http://www.motogp.com/es/calendar/").data
    bloques = find_multiple_matches(data, 'div class="event shadow_block official(.*?)</picture>')
    patron = '<div class="event_day">\s*(\d+).*?<div class="event_month">\s*(.*?)\s.*?' \
             'href="([^"]+)".*?>([^<]+)<.*?<span>(.*?)</span>.*?<span>(.*?)</span>.*?src="([^"]+)"'
    flags = {'UNITED STATES': 'United-States-of-America', 'GREAT BRITAIN': 'United-Kingdom',
             'CZECH REPUBLIC': 'Czech-Republic',}
    for b in bloques:
        matches = find_multiple_matches(b, patron)
        for day, month, url, title, circuit, country, img in matches:
            finish = False
            if 'finished">' in b:
                finish = True
            fecha = "%s %s" % (day, month)
            img = img.replace("/324x143", "/648x286")
            flag = flags.get(country, country.capitalize())
            country = "https://www.countries-ofthe-world.com/flags-normal/flag-of-%s.png" % flag
            circuitos.append([fecha, title, url, circuit, country, img, finish])

    return circuitos


def get_circuit_data(url, cat):
    circuit = {}
    data = httptools.downloadpage(url).data
    desc = find_single_match(data, '<div class="c-event__circuit-description">(.*?)</div>')
    desc = htmlclean(desc.replace("</p>", "\n").strip())
    records = find_multiple_matches(data, 'Récord del Circuito</div>.*?season">(\d+).*?rider_name">([^<]+)<.*?value">([^<]+)<')
    record = ""
    if records:
        try:
            if cat == "motogp":
                records = records[0]
            elif cat == "moto2":
                records = records[1]
            else:
                records = records[2]
            record = "%s (%s) %s" % (records[1], records[0], records[2])
        except:
            pass
    circuit["data"] = {'desc': desc, 'record': record}
    shortname = find_single_match(data, 'shortName="([^"]+)"')
    urls = find_multiple_matches(data, '(?i)data-tabContent="Results\s*%s\s(.*?)".*?href="([^"]+)"' % cat)
    sesiones = {'FP1': 'Libres 1', 'FP2': 'Libres 2', 'FP3': 'Libres 3', 'FP4': 'Libres 4', 'QP': 'Calificación', 'RAC': 'Carrera', 'WUP': 'Warm Up'}
    circuit["sesiones"] = []
    url = ""
    for sesion, url_s in urls:
        name = sesiones.get(sesion, sesion)
        if url_s == url:
            continue
        else:
            url = url_s
        circuit["sesiones"].insert(0, [name, sesion, url_s])

    if not urls:
        name_b = ""
        urls = find_multiple_matches(data, '(?i)<div class="c-schedule__table-cell">%s.*?"visible-xs">(.*?)<.*?' \
                                           '<span data-ini-time="([^\+]+).*?(?:<span data-end="([^\+]+)|</div>)' % cat)
        for sesion, fecha1, fecha2 in urls:
            name = sesiones.get(sesion, sesion)
            if name_b == name:
                continue
            else:
                name_b = name
            format = '%d-%m-%Y'
            format2 = '%H:%M'
            fecha1 = datetime.datetime(*(time.strptime(fecha1, '%Y-%m-%dT%H:%M:%S')[0:6]))
            if fecha2:
                fecha2 = datetime.datetime(*(time.strptime(fecha2, '%Y-%m-%dT%H:%M:%S')[0:6]))
                fecha = "%s --- De %s a %s" % (fecha1.strftime(format), fecha1.strftime(format2), fecha2.strftime(format2))
            else:
                fecha = "%s --- %s" % (fecha1.strftime(format), fecha1.strftime(format2))
            circuit["sesiones"].insert(0, [name, sesion, fecha])

    return circuit


def get_session_data(url):
    sesion = []

    data = httptools.downloadpage(url).data
    patron = '<td (?:align="right"|class="alignright")>(.*?)</td>.*?<td (?:align="right"|class="alignright")>(.*?)</td>.*?href="([^"]+)">([^<]+)</a>' \
             '.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<td.*?>(.*?)</td>.*?<td.*?>(.*?)</td>'
    matches = find_multiple_matches(data, patron)
    for pos, dato, url, name, country, team, marca, km, gap in matches:
        name = unicode(name, "utf8")
        if "/" in gap:
            gap = gap.split("/")[0]
        sesion.append({'pos': pos, 'dato': dato, 'name': name, 'country': country, 'team': team,
                        'marca': marca, 'km': km, 'gap': gap, 'url': url})

    return sesion


def get_piloto_data(url):
    driver = {}
    data = httptools.downloadpage(url).data
    
    driver['dorsal'] = find_single_match(data, '<span class="number">([^<]+)<')
    driver['nombre'] = find_single_match(data, '<p class="name">([^<]+)<')
    driver['country'] = find_single_match(data, '<div class="details floatl">.*?src="([^"]+)"')

    bloque_ficha = find_single_match(data, '<h4>Sumario</h4>(.*?)</table>')
    driver['ficha'] = []
    driver['head'] = []
    matches = find_multiple_matches(bloque_ficha, '<th scope="col">(.*?)</th>')
    for titulo in matches:
        driver['head'].append(titulo)
    driver['head'].append("Todo")
    matches = find_multiple_matches(bloque_ficha, '<th scope="row">(.*?)</th>(.*?)</tr>')
    for titulo, valor in matches:
        titulo = htmlclean(titulo)
        valor = find_multiple_matches(valor, '<td>(.*?)</td>')
        driver['ficha'].append([titulo, valor])

    bio = find_single_match(data, '<h4>Perfil</h4>(.*?)</div>')
    bio = htmlclean(bio)
    driver['bio'] = bio

    driver['stats'] = {}
    bloque = find_single_match(data, '<h4>Estadísticas</h4>(.*?)</table>')
    patron = '<td class="season">(.*?)</td><td class="season">(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td>' \
             '<td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td>'
    stats = find_multiple_matches(bloque, patron)
    for st in stats:
        driver['stats'][st[0]] = {'cat': st[1], 'salidas': st[2], 'uno': st[3], 'dos': st[4], 
                                  'tres': st[5], 'total': st[6].strip(), 'poles': st[7].strip(),
                                  'moto': st[8].strip(), 'puntos': st[9].strip(), 'pos': st[10].strip()}

    url_n = find_single_match(data, "var elementId\s*=\s*'([^']+)'")
    url_n = "http://www.motogp.com/es/ajax/get_content/?tt[]=rider&tv[]=%s&relevance=all&type=news&first_page=1" % url_n
    driver['news'] = url_n

    return driver


def get_piloto_news(url):
    from core import jsontools
    data = jsontools.load_json(httptools.downloadpage(url).data)["html"]

    news = []
    matches = find_multiple_matches(data, 'data-nid="([^"]+)".*?data-changed="([^"]+)".*?data-page="([^"]+)"' \
                                          '.*?src="([^"]+)".*?(?:<h1>|<h2>)(.*?)(?:</h1>|</h2>).*?<p class="summary.*?>(.*?)</p>')
    for nid, tstamp, url_n, img, title, desc in matches:
        img = img.replace("small.", "middle.")
        title = decodeHtmlentities(title)
        desc = decodeHtmlentities(desc)
        url_n = "http://www.motogp.com/%s" % url_n
        fecha = datetime.datetime.fromtimestamp(int(tstamp)).strftime('%d-%m-%Y')
        news.append([url_n, title, img, fecha, desc, nid, tstamp])

    next = ""
    if news:
        rider = find_single_match(url, 'tv\[\]=(\d+)')
        pos = find_single_match(url, 'pos=(\d+)')
        if pos:
            pos = str(int(pos) + 10)
        else:
            pos = "11"
        next = "http://www.motogp.com/es/ajax/get_content/?nid=%s&changed=%s&pos=%s&pin=0&no_components=false&num_per_page=10&tt[]=rider&tv[]=%s&relevance=all&type=news&" \
               % (news[-1][-2], news[-1][-1], pos, rider)

    return news, next
    

def get_content_news_piloto(url):
    data = httptools.downloadpage(url).data

    ante = find_single_match(data, '<p class="description hidden-xs hidden-sm">(.*?)</p>').strip()
    sub = find_multiple_matches(data, '<h2 class="update_subtitle">([^<]+)</h2>')
    subtitle = []
    for s in sub:
        subtitle.append(s.strip())
    text = find_multiple_matches(data, '<p>(.*?)</p>')
    cuerpo = []
    for c in text:
        cuerpo.append(htmlclean(c.strip()))

    noti = "[COLOR gray]%s[/COLOR]\n[B]%s[/B]%s" % (ante, "\n".join(subtitle), "\n\n".join(cuerpo))
    noti = re.sub(r' {2,}', '', noti)
    noti = re.sub(r'\n{3,}', '\n\n', noti)
    
    return noti


def get_data_f1(url="", live=False, data=""):
    from core import jsontools
    times = {}
    
    if not url:
        url = "http://www.sofascore.com/es/formula-1"
    if not data:
        data = httptools.downloadpage(url, cookies=False).data
    race = find_single_match(data, 'var activeRace\s*=\s*(\d+)')
    url = "http://www.sofascore.com/formula-1/race/%s/race/json" % race
        
    data_t = jsontools.load_json(httptools.downloadpage(url).data)
    times['active'] = 'race'
    qualify = data_t["qualifyingData"]
    data_t = data_t["activeRace"]
    times['circuit'] = {'name': data_t["circuitName"], 'length': data_t["circuitLength"], 'laps': data_t["laps"],
                        'lap_record': data_t["lapRecord"], 'country': data_t["country"], 'distance': data_t["raceDistance"],
                        'gp': data_t["name"]}
    times['current_lap'] = data_t["currentLap"]

    active = ""
    times["sessions"] = []
    sessions = ['practice1', 'practice2', 'practice3', 'qualifying1', 'qualifying2', 'qualifying3', 'race']
    for i, s in enumerate(sessions):
        if not data_t.get(s):
            times["sessions"].append({'type': s, 'status': '', 'drivers': [], 'time': ''})
            continue
        status = data_t[s]["status"]["type"]
        drivers = []
        for d in data_t[s]["drivers"]:
            drivers.append(d)
        times["sessions"].append({'type': s, 'status': status, 'drivers': drivers, 'time': data_t[s]["dateTimestamp"]})
        if not data_t[s]["drivers"] and not active:
            active = sessions[i]
            if i != 0:
                active = sessions[i-1]
            times['active'] = active
    times["sessions"].append({'type': 'qualifying', 'status': "", 'drivers': qualify, 'time': ''})

    return times


def get_calendario_f1(season=""):
    data = httptools.downloadpage("http://www.sofascore.com/es/formula-1/%s" % season).data
    data = re.sub(r"\n|\r|\t|\s{2,}", '', data)
    matches = find_multiple_matches(data, '<a class="pointer js-link" href="/es/formula-1/(\d+)"')
    seasons = []
    for s in matches:
        url = "http://www.sofascore.com/es/formula-1/%s" % s
        seasons.append([s, url])

    races = []
    flags = {'united-arab-emirates': 'United-Arab-Emirates', 'usa': 'United-States-of-America', 'great-britain': 'United-Kingdom',
             'south-korea': 'Korea-South'}
    patron = '<li class="cell--table.*?href="([^"]+)".*?flags--(.*?)".*?<div class="cell__content ff-medium u-fs15">' \
             '\s*(.*?)<.*?(?:data-format="d">(.*?)<.*?data-format="d M">(.*?)<|<span class="soficons soficons-icon-cup"></span>(.*?)<.*?</a>)'
    matches = find_multiple_matches(data, patron)
    for url, flag, race, date1, date2, winner in matches:
        url = "http://www.sofascore.com" + url
        flag = flags.get(flag, flag.capitalize())
        img = "https://www.countries-ofthe-world.com/flags-normal/flag-of-%s.png" % flag
        fecha = ""
        if date1:
            fecha = "%s\n - \n%s" % (date1, date2)
        races.append([url, img, race, fecha, winner])

    return seasons, races, data
            

def get_live_f1():
    from core import jsontools
    comments = []
    times = []

    data_c = httptools.downloadpage("http://directo.soymotor.com/directo_export_gp_comentarios.php").data
    patron = '<td class="vuelta_comentario"><b>(.*?)</b>.*?<td class="comentariosvuelta">(.*?)</td>'
    matches = find_multiple_matches(data_c, patron)
    for hora, msg in matches:
        if "script" in msg:
            continue
        msg = htmlclean(msg)
        comments.append([hora, msg])

    data_t = httptools.downloadpage("http://directo.soymotor.com/directo_export_gp_tiempos_json.php").data
    times = jsontools.load_json(data_t)
    datos = httptools.downloadpage("http://directo.soymotor.com/directo_export_gp_datos.php").data

    bandera = httptools.downloadpage("http://directo.soymotor.com/directo_export_gp_clima_bandera.php").data
    bandera = find_single_match(bandera, 'src="([^"]+)"')
    live = True
    if "bfinalizada" in bandera:
        live = False
    
    return comments, times, datos, bandera, live


def get_feed(data_=""):
    data = httptools.downloadpage("http://www.formula1.com/sp/static/f1/2017/serverlist/svr/serverlist.xml.js").data
    race_ = find_single_match(data, 'race:"([^"]+)"')
    session = find_single_match(data, '(?<!//)session:"([^"]+)"')
    race = "%s | %s" % (session, race_)

    if not data_:
        data_ = httptools.downloadpage("http://www.formula1.com/sp/static/f1/2017/live/%s/%s/all.js" % (race_, session)).data
    
    feed = {}
    header = {'Cookie': 'global[cookie_version]=1.1; local[chat]=a%3A1%3A%7Bs%3A3%3A%22key%22%3Bs%3A8%3A%223g7cfwh3%22%3B%7D'}
    data_p = httptools.downloadpage("http://f1.tfeed.net/dd.js", headers=header, cookies=False)
    if data_p.code == 404:
        httptools.downloadpage("https://f1.tfeed.net/fpong.php", headers=header, cookies=False).data
        data_p = httptools.downloadpage("http://f1.tfeed.net/dd.js", headers=header, cookies=False)
    data_p = find_single_match(data_p.data, 'ndd_f\((\[\[.*?)\);')
    if data_p:
        data_p = eval(data_p)
    else:
        return feed

    data_t = httptools.downloadpage("http://f1.tfeed.net/tt.js", headers=header, cookies=False)
    if data_t.code == 404:
        httptools.downloadpage("https://f1.tfeed.net/fpong.php", headers=header, cookies=False).data
        data_t = httptools.downloadpage("http://f1.tfeed.net/tt.js", headers=header, cookies=False)

    flag = find_single_match(data_t.data, '\[(\d+)')
    data_t = find_single_match(data_t.data, ',(\[\[.*?)\);')
    if data_t:
        data_t = eval(data_t)
        for i in range(len(data_p)):
            if not isinstance(data_t[i], list):
                break
            t = data_t[i]
            tyres = t[14]
            neuma = []
            for ty in tyres:
                neuma.append(get_tyres(ty[0]))
            color = find_single_match(data_, '"FullName":"%s","Color":"([^"]+)"' % data_p[i][0])
            feed[str(t[3])] = {'driver': data_p[i][0], 'status': t[0], 'laptime': t[2], 'gap': t[4],
                               'pits': t[6], 'tyres': neuma, 'pos': t[3]-data_p[i][2], 'speed': t[8],
                               'points': int(data_p[i][3]), 'bestlap': t[7], 'lap': t[1],
                               'interval': t[5], 'color': color}

    return feed, race, data_


def get_driver_data(url):
    driver = {}
    data = httptools.downloadpage(url).data
    
    driver['dorsal'] = find_single_match(data, '<span class="dorsal">([^<]+)<')
    driver['nombre'] = find_single_match(data, '<span class="dorsal".*?>([^<]+)</h1>')
    driver['banner'] = find_single_match(data, '<span class="dorsal".*?src="([^"]+)"')

    images = [find_single_match(data, '<div class="seccion sec_especial">.*?src="([^"]+)"')]
    images.extend(find_multiple_matches(data, '<a class=\'cajax\' href="([^"]+)"'))
    driver['images'] = images
    bloque_ficha = find_single_match(data, '<div class="ficha-datos">(.*?)</div>')
    driver['ficha'] = []
    matches = find_multiple_matches(bloque_ficha, '<dt>(.*?)</dt>(.*?)</dl>')
    for titulo, valor in matches:
        titulo = htmlclean(titulo)
        valor = find_single_match(valor, '<dd>(.*?)</dd>')
        if valor:
            valor = htmlclean(valor)
        driver['ficha'].append([titulo, valor])

    title = find_single_match(data, '<div class="rotulo"><span>(.*?)</span>')
    bio = find_single_match(data, '<div class="cuerpo  mb mt">(.*?)<span class="readless">')
    bio = bio.replace('<span class="readmore">leer más</span>', '')
    bio = bio.replace('<strong>', '\n[B]').replace('</strong>', '[/B]').replace("</p>", "\n").replace("<br />", "\n\n")
    bio = htmlclean(bio)

    bio = re.sub(r'\r', '', bio)
    bio = re.sub(r'\n{3,7}', '\n', bio)
    driver['info'] = {'title': title, 'bio': bio}

    driver['stats'] = {}
    bloque = find_single_match(data, 'GPs</td></tr></thead>(.*?)</tbody>')
    patron = '<td class="tc">(\d+).*?<td class="tc">([^<]*)<.*?>([^<]+)</a>.*?<td>([^<]+)</td>.*?' \
             '<td>([^<]+)</td>.*?<td class="tc">([^<]*)<.*?<td class="tc">([^<]*)<.*?' \
             '<td class="tc">([^<]*)<.*?<td class="tc">([^<]*)<.*?<td class="tc">([^<]*)<.*?<td class="tc">([^<]*)<'
    stats = find_multiple_matches(bloque, patron)
    for st in stats:
        driver['stats'][st[0]] = {'pos': st[1], 'equipo': st[2], 'chasis': st[3], 'motor': st[4], 
                                  'neuma': st[5], 'vict': st[6].strip(), 'poles': st[7].strip(),
                                  'vr': st[8].strip(), 'puntos': st[9].strip(), 'gps': st[10].strip()}

    driver['news'] = find_single_match(data, '<div class="more-link">.*?href="([^"]+)"')

    return driver


def get_driver_news(url):
    data = httptools.downloadpage("http://soymotor.com%s" % url).data

    news = []
    matches = find_multiple_matches(data, '<span class="media ">.*?href="([^"]+)".*?title="([^"]+)"' \
                                          '.*?src="([^"]+)".*?<span class="fecha">\s*\|\s*(.*?)<')
    for url, title, img, fecha in matches:
        img = img.replace("small_video", "large")
        title = decodeHtmlentities(title)
        news.append([url, title, img, fecha])

    next = find_single_match(data, 'href="([^"]+)">siguiente')

    return news, next
    

def get_content_news(url):
    data = httptools.downloadpage(url).data

    ante = find_single_match(data, '<div class="antetitulo">(.*?)</div')
    sub = find_multiple_matches(data, '<h2 class="item">([^<]+)</h2>')
    cuerpo = find_single_match(data, '<div class="cuerpo  mb mt">(.*?)</div>')
    cuerpo = cuerpo.replace('<strong>', '[B]').replace('</strong>', '[/B]').replace("</p>", "\n").replace("<br />", "\n")
    cuerpo = htmlclean(cuerpo)

    noti = "[COLOR gray]%s[/COLOR]\n[B]%s[/B]\n%s" % (ante, "\n".join(sub), cuerpo)
    noti = re.sub(r' {2,}', '', noti)
    noti = re.sub(r'\n{3,}', '\n\n', noti)

    return noti


def get_data_pilotof1(data, piloto, data_driver):
    if not data:
        data = httptools.downloadpage("https://www.formula1.com/en/championship/drivers.html").data
    if not data_driver:
        data_driver = httptools.downloadpage("http://www.formula1.com/sp/static/f1/2017/updates/data/drivers_all.js").data
    nacido = find_single_match(data_driver, '%s.*?"DOB":"([^"]*)"' % piloto)
    lugar = find_single_match(data_driver, '%s.*?"POB":"([^"]*)"' % piloto)
    if lugar:
        nacido += " , %s" % lugar.replace("\u00c9", "É")
        
    piloto = piloto.rsplit(".", 1)[1]

    name = ""
    thumb = ""
    casco = ""
    equipo = ""
    matches = find_multiple_matches(data, '<h1 class="driver-name">(.*?)</h1>.*?<span>(.*?)</span>')
    for driver, team in matches:
        driver = decodeHtmlentities(driver)
        driver = quita_tildes(driver)
        if re.search(r'(?i)%s' % piloto, driver):
            name = re.sub(r'\s{2,}', ' ', driver)
            equipo = team
            break
    if name:
        thumb = "https://www.formula1.com/content/fom-website/en/championship/drivers/%s/_jcr_content/image.img.1920.medium.jpg" % name.replace(" ", "-").lower()
        casco = thumb.replace("/image.img", "/helmet.img")

    return thumb, casco, data, name, equipo, nacido, data_driver


def get_tyres(num):
    folder = filetools.join(config.get_runtime_path(), 'resources', 'images', 'matchcenter')
    if num == 0:
        return ''
    elif num == 1:
        return filetools.join(folder, 'super.png')
    elif num == 2:
        return filetools.join(folder, 'soft.png')
    elif num == 3:
        return filetools.join(folder, 'medium.png')
    elif num == 4:
        return filetools.join(folder, 'hard.png')
    elif num == 5:
        return filetools.join(folder, 'inter.png')
    elif num == 6:
        return filetools.join(folder, 'wet.png')
    elif num == 7:
        return filetools.join(folder, 'ultra.png')
    
def quita_tildes(title):
    title = title.replace("Á","A")
    title = title.replace("É","E")
    title = title.replace("Í","I")
    title = title.replace("Ó","O")
    title = title.replace("Ú","U")
    title = title.replace("á","a")
    title = title.replace("é","e")
    title = title.replace("í","i")
    title = title.replace("ó","o")
    title = title.replace("ú","u")
    title = title.replace("À","A")
    title = title.replace("È","E")
    title = title.replace("Ì","I")
    title = title.replace("Ò","O")
    title = title.replace("Ù","U")
    title = title.replace("à","a")
    title = title.replace("è","e")
    title = title.replace("ì","i")
    title = title.replace("ò","o")
    title = title.replace("ù","u")
    title = title.replace("ç","c")
    title = title.replace("Ç","C")
    title = title.replace("Ñ","ñ")
    title = title.replace("ö","o")
    title = title.replace("ä","a")
    title = title.replace("ï","i")
    title = title.replace("ë","e")
    title = title.replace("ü","u")
    return title