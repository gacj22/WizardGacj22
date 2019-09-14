# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
#------------------------------------------------------------

import re
import xbmcgui
import xbmc
import datetime
import eventdetails
from lib.matchcenter import marcadores
from core import filetools
from core import config


class Main(xbmcgui.WindowXMLDialog):
    
    def __init__( self, *args, **kwargs ):
        self.standalone = kwargs["standalone"]
        self.isRunning = True
        now = datetime.datetime.today()
        self.url = "http://www.resultados-futbol.com/livescore"
        self.hoy = True
        self.filtro = ""
        self.refresh_score = []
        self.onlive = False
        self.resultados = {}


    def onInit(self):
        self.setCoordinateResolution(2)

        xbmc.executebuiltin("ClearProperty(no-games,Home)")
        if not self.standalone:
            self.getControl(32540).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","goal.png"))
            self.reset_buttons(33503)
        else:
            self.getControl(32503).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","avisogol.gif"))
            self.getControl(32503).setVisible(False)
        xbmc.executebuiltin("SetProperty(loading-script-matchcenter-livescores,1,home)")
        self.livescoresThread()
        xbmc.executebuiltin("ClearProperty(loading-script-matchcenter-livescores,Home)")

        update_times = [0, 1, 2, 5, 10]
        livescores_update_time = update_times[int(config.get_setting("update_scores"))]
        i = 0
        if livescores_update_time:
            while self.isRunning:
                if not self.hoy:
                    self.isRunning = False
                if (float(i*200)/(livescores_update_time*60*1000)).is_integer() and i != 0:
                    if self.standalone and self.onlive:
                        new_scores = marcadores.refresh_score()
                        for key, value in new_scores.items():
                            for it in self.items:
                                if key == it.getProperty("matchid"):
                                    result = it.getProperty("result").replace(" ", "")
                                    if result == value:
                                        continue
                                    if result == "-":
                                        result = "0-0"

                                    self.resultados[it.getProperty("matchid")] = value.split("-")[0] + " - " + value.split("-")[1]
                                    if value == "0-0":
                                        continue
                                    if (value.split("-")[0] != result.split("-")[0]) and (value.split("-")[1] != result.split("-")[1]):
                                        result = "[COLOR red]%s[/COLOR] - [COLOR red]%s[/COLOR]" % (value.split("-")[0], value.split("-")[1])
                                    elif value.split("-")[0] != result.split("-")[0]:
                                        result = "[COLOR red]%s[/COLOR] - %s" % (value.split("-")[0], value.split("-")[1])
                                    else:
                                        result = "%s - [COLOR red]%s[/COLOR]" % (value.split("-")[0], value.split("-")[1])
                                    self.refresh_score.append("Goooooooool en el %s %s %s"
                                                              % (it.getProperty("hometeam_long"),
                                                                 result, it.getProperty("awayteam_long")))
                                    continue
                    self.livescoresThread()
                xbmc.sleep(200)
                i += 1


    def livescoresThread(self):
        self.getLivescores()
        self.setLivescores()
        return

    def getLivescores(self):
        self.livescoresdata = marcadores.get_matches(self.url)
        return

    def set_no_games(self):
        xbmc.executebuiltin("ClearProperty(loading-script-matchcenter-livescores,Home)")
        self.getControl(32541).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","baliza.png"))
        xbmc.executebuiltin("SetProperty(no-games,1,home)")
        return
        
    def setLivescores(self):
        if not self.standalone:
            self.getControl(33500).setText("")
            self.getControl(33501).setLabel("")
            self.getControl(33502).setLabel("")
        self.next = ""
        self.prev = ""

        fin = 0
        juego = 0
        por_empezar = 0
        self.onlive = False
        now = datetime.datetime.today()
        self.items = []
        if self.livescoresdata:
            try:
                today = datetime.datetime.now().date()
                t_check = self.livescoresdata[-1]["next"].rsplit("/", 1)[1]
                t_check = datetime.datetime(int(t_check[4:]), int(t_check[2:4]), int(t_check[:2])) - datetime.timedelta(days=1)
                self.hoy = (today == t_check.date())
            except:
                self.hoy = False

            for partido in self.livescoresdata:
                if not partido.get("liga"):
                    continue

                item = xbmcgui.ListItem(partido["url"])
                item.setProperty('league_and_round', partido["liga"])
                if self.resultados.get(partido["matchid"]):
                    result = self.resultados[partido["matchid"]]
                else:
                    result = partido["score"]
                item.setProperty('result', result)
                item.setProperty('home_team_logo', partido["thumb1"])
                item.setProperty('away_team_logo', partido["thumb2"])
                item.setProperty('hometeam_long', partido["team1"])
                item.setProperty('awayteam_long', partido["team2"])

                try:
                    if partido["score"] != "-- : --":
                        score = re.sub(r'\(\d+\)', '', partido["score"])
                        result1 = score.split(" - ")[0]
                        if "(" in result1:
                            result1 = result1.split("(", 1)[0]
                        if int(result1) > 0:
                            item.setProperty('has_home_goals',filetools.join(config.get_runtime_path(),"resources","images","matchcenter","goal.png"))
                        result2 = score.split(" - ")[1]
                        if ")" in result2:
                            result2 = result2.split(")", 1)[1]
                        if int(result2) > 0:
                            item.setProperty('has_away_goals',filetools.join(config.get_runtime_path(),"resources","images","matchcenter","goal.png"))
                except:
                    pass

                item.setProperty('starttime', partido["hora"])
                estado = partido["estado"]
                if re.search(r'(?i)Finalizado', estado) and self.hoy and partido["priority"] == 1:
                    try:
                        h, m = partido["hora"].split(":")
                        time_match = datetime.datetime(now.year, now.month, now.day, int(h), int(m))
                        diferencia = now - time_match
                        if diferencia.total_seconds() <= 7200:
                            estado = marcadores.get_minutos(partido["url"])
                    except:
                        pass

                item.setProperty('minute', str(self.translatematch(estado)))
                if re.search(r'(?i)Finalizado|Aplazado', estado):
                    fin += 1
                    if self.filtro != "" and self.filtro != "Finalizado":
                        continue
                    status = filetools.join(config.get_runtime_path(),"resources","images","matchcenter","redstatus.png")
                elif "'" in estado or "Des" in estado:
                    juego += 1
                    if self.filtro != "" and self.filtro != "En juego":
                        continue
                    status = filetools.join(config.get_runtime_path(),"resources","images","matchcenter","greenstatus.png")
                else:
                    por_empezar += 1
                    if self.filtro != "" and self.filtro != "Por empezar":
                        continue
                    status = filetools.join(config.get_runtime_path(),"resources","images","matchcenter","yellowstatus.png")
                item.setProperty('status', status)

                matchpercent = "0"
                item.setProperty('order', "-7")
                if "'" in estado:
                    try:
                        matchpercent = str(int((float(estado.replace("'",""))/90)*100))
                    except:
                        pass
                    if partido["priority"] == 1 or partido["priority"] == 2:
                        item.setProperty('order', estado.replace("'",""))
                else:
                    if re.search(r'(?i)Des', estado):
                        matchpercent = "50"
                        if partido["priority"] == 1 or partido["priority"] == 2:
                            item.setProperty('order', "45")
                    elif re.search(r'(?i)Aplazado', estado):
                        matchpercent = "0"
                        if partido["priority"] == 1:
                            item.setProperty('order', "-5")
                        elif partido["priority"] == 2:
                            item.setProperty('order', "-6")
                    elif re.search(r'(?i)Finalizado', estado):
                        matchpercent = "100" 
                        if partido["priority"] == 1:
                            item.setProperty('order', "-2")
                        elif partido["priority"] == 2:
                            item.setProperty('order', "-4")
                    else:
                        if partido["priority"] == 1:
                            item.setProperty('order', "-1")
                        elif partido["priority"] == 2:
                            item.setProperty('order', "-3")
                item.setProperty("matchpercent", matchpercent)
                item.setProperty("canal", partido["canal"])
                if self.standalone and partido["priority"] != 1:
                    continue
                elif self.standalone and partido["priority"] == 1:
                    item.setProperty("matchid", partido["matchid"])
                    if "'" in estado or re.search(r'(?i)Des', estado):
                        self.onlive = True
                    if not re.search(r"(?i)finalizado|aplazado|Des|'", estado):
                        estado = partido["hora"]
                        result = " - "
                    texto = "[COLOR darkorange]%s:[/COLOR] %s [COLOR white]%s[/COLOR] %s" % (estado, partido["team1"], result, partido["team2"])
                    item.setProperty("texto", texto)
                self.items.append(item)
        
        if self.items:
            self.items.sort(key=lambda it:int(it.getProperty('order')), reverse=True)

            if self.standalone:
                label = ""
                for it in self.items:
                    label += it.getProperty("texto") + "  |  "
                self.getControl(32500).setLabel(label)
                if self.refresh_score:
                    import threading
                    t = threading.Thread(target=self.aviso_gol)
                    t.setDaemon(True) 
                    t.start()
            if not self.standalone:
                self.getControl(32500).reset()
                xbmc.executebuiltin("ClearProperty(no-games,Home)")
                self.getControl(32500).addItems(self.items)
                self.setFocusId(32500)
                self.getControl(33500).setText(self.livescoresdata[-1]["today"])

                if len(self.items) <= 3:
                    self.getControl(32502).setWidth(955)

                if self.livescoresdata[-1]["prev"]:
                    self.getControl(33501).setLabel("<< Día Anterior")
                    self.prev = self.livescoresdata[-1]["prev"]
                if self.livescoresdata[-1]["next"]:
                    self.getControl(33502).setLabel("Día Siguiente >>")
                    self.next = self.livescoresdata[-1]["next"]

                self.getControl(33503).setLabel("Todos (%s)" % str(fin+juego+por_empezar))
                self.getControl(33504).setLabel("En Juego (%s)" % str(juego))
                self.getControl(33505).setLabel("Sin comenzar (%s)" % str(por_empezar))
                self.getControl(33506).setLabel("Finalizados (%s)" % str(fin))

        elif not self.standalone:
            self.getControl(32500).reset()
            self.set_no_games()

        return

    def aviso_gol(self):
        from random import randint
        images = ['balon_gol', 'gol_porteria', 'gol_corner']
        while self.refresh_score:
            self.getControl(32503).setImage(filetools.join(config.get_runtime_path(),"resources","images","matchcenter","%s.gif" % images[randint(0, 2)]))
            self.getControl(32502).setLabel(self.refresh_score[0])
            self.getControl(32503).setVisible(True)
            self.getControl(32502).setAnimations([('conditional', 'effect=slide end=-1000 time=15000 condition=true')])
            self.getControl(32503).setAnimations([('conditional', 'effect=slide end=-1000 time=15000 condition=true')])
            for i in range(0, 15):
                if i % 2 == 0:
                    self.getControl(32502).setLabel(self.refresh_score[0].replace("[COLOR white]", "[COLOR red]"))
                else:
                    self.getControl(32502).setLabel(self.refresh_score[0].replace("[COLOR red]", "[COLOR white]"))
                if not self.isRunning:
                    self.refresh_score = []
                    break
                xbmc.sleep(1000)
            if len(self.refresh_score) > 1:
                self.refresh_score = self.refresh_score[1:]
            else:
                self.refresh_score = []
            self.getControl(32503).setVisible(False)
            self.getControl(32502).setLabel("")

    def stopRunning(self):
        self.isRunning = False
        while self.refresh_score:
            xbmc.sleep(100)
        self.close()

    def onAction(self,action):
        if action.getId() == 92 or action.getId() == 10:
            self.stopRunning()

    def onClick(self,controlId):
        if not self.standalone:
            if controlId == 32500:
                select = self.getControl(32500).getSelectedItem()
                eventdetails.showDetails(select.getLabel(), select.getProperty('league_and_round'))
            if controlId == 33501 and self.prev:
                self.url = self.prev
                self.reset_buttons(33503)
                self.filtro = ""
                self.resultados = {}
                self.livescoresThread()
            if controlId == 33502 and self.next:
                self.url = self.next
                self.reset_buttons(33503)
                self.filtro = ""
                self.resultados = {}
                self.livescoresThread()
            if controlId == 33503:
                self.filtro = ""
                self.setLivescores()
                self.reset_buttons(33503)
            if controlId == 33504:
                self.filtro = "En juego"
                self.setLivescores()
                self.reset_buttons(33504)
            if controlId == 33505:
                self.filtro = "Por empezar"
                self.setLivescores()
                self.reset_buttons(33505)
            if controlId == 33506:
                self.filtro = "Finalizado"
                self.setLivescores()
                self.reset_buttons(33506)
        else:
            if controlId == 32501:
                self.close()
                main = Main('script-matchcenter-Livescores.xml', config.get_runtime_path(), standalone=False)
                main.doModal()
                del main

    def reset_buttons(self, bt_except):
        buttons = [33503, 33504, 33505, 33506]
        for b in buttons:
            if b == bt_except:
                self.getControl(b).setEnabled(False)
            else:
                self.getControl(b).setEnabled(True)

    def translatematch(self, string):
        if string.lower() == "finalizado": return "Finalizado"
        elif string.lower() == "des": return "Descanso"
        elif string.lower() == "aplazado": return "Aplazado"
        elif "'" in string: return string
        else: return "Por empezar"


def start(window, standalone=False):
    if xbmc.getCondVisibility("Player.HasMedia"):
        standalone = True
        script = 'script-matchcenter-Livescores-mini.xml'
        xbmc.executebuiltin("Dialog.Close(videoosd, true)")
    else:
        script = 'script-matchcenter-Livescores.xml'
    main = Main(script, config.get_runtime_path(), standalone=standalone)
    main.doModal()
    del main
    window.doModal()