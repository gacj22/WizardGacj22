#!/usr/bin/python
# -*- coding: utf-8 -*-
# Torrentin - XBMC/Kodi Add-On
# Play torrent & magnet on Android (Windows only AceStream & plugins) and more....
# by ciberus
# You can copy, distribute, modify blablabla.....
# v. 0.6.2 - Abril 2018

################################################################
# Este AddOn de KODI no contiene enlaces internos o directos a material protegido por
# copyright de ningun tipo, ni siquiera es un reproductor de torrents, tan solo se encarga
# de hacer de puente de los enlaces que le llegan de otros AddOns y los re-envia a otros
# Add-Ons de kodi o Aplicaciones de android capaces de reproducir torrents o magnets
# sin descargarlos previamente.
# Es de distribucion libre, gratuita y de codigo abierto y nunca se ha obtenido ningun tipo
# de beneficio economico con el mismo.
################################################################

import sys,os,xbmc, xbmcaddon,urllib,xbmcgui,xbmcplugin,re,json,threading,time

__addon__ = xbmcaddon.Addon( id = 'plugin.video.torrentin' )
__author__     = __addon__.getAddonInfo('author')
__scriptid__   = __addon__.getAddonInfo('id')
__scriptname__ = __addon__.getAddonInfo('name')
__cwd__        = __addon__.getAddonInfo('path')
__version__    = __addon__.getAddonInfo('version')
__language__   = __addon__.getLocalizedString

sys.path.append( os.path.join( __addon__.getAddonInfo( 'path' ), 'core') )
sys.path.append( os.path.join( __addon__.getAddonInfo( 'path' ), 'resources','lib') )
if (sys.platform == 'win32') or (sys.platform == 'win64'): oswin = True
else: oswin = False
import torrents
import tools

if not __addon__.getSetting('torrent_path'):
    if xbmc.getCondVisibility('system.platform.Android'):
        if not os.path.exists("/mnt/sdcard/Torrents"):
            os.mkdir("/mnt/sdcard/Torrents")
        __addon__.setSetting('torrent_path',"/mnt/sdcard/Torrents")
    elif oswin:
        if not os.path.exists("C:\Torrents"):
            os.mkdir("C:\Torrents")
        __addon__.setSetting('torrent_path',"C:\Torrents\\")	
    else:
        while not __addon__.getSetting('torrent_path'):
            __addon__.openSettings()
            xbmc.sleep(300)
            if not __addon__.getSetting('torrent_path'): xbmcgui.Dialog().ok("Torrentin" , "El Add-On No funcionará hasta que no configures","el directorio principal de la biblioteca de torrents,","es OBLIGATORIO seleccionar un directorio.")
            xbmc.sleep(300)

gestores = {
1 : ["Custom" , __addon__.getSetting("tordowncust")],
2 : ["uTorrent","com.utorrent.client"],
3 : ["uTorrent Pro","com.utorrent.client.pro" ], 
4 : ["tTorrent","hu.tagsoft.ttorrent.lite"], 
5 : ["tTorrent Pro","hu.tagsoft.ttorrent.pro" ],
6 : ["BitTorrent","com.bittorrent.client"],
7 : ["Flud","com.delphicoder.flud"],
8 : ["Vuze","com.vuze.torrent.downloader"],
9 : ["aTorrent","com.mobilityflow.torrent"]
}

addons = {
"xbmctorrent" : "xbmct" ,
"stream" : "strm" ,
"kmediatorrent" : "kmed" ,
"pulsar" : "pulsar" ,
"quasar" : "quasar" ,
"elementum" : "elem" ,
"p2p-streams" : "p2p" ,
"torrenter" : "tter" ,
"yatp" : "yatp"
}

gestornames = gestores.get(int(__addon__.getSetting("tordown")),["",""])
menu = 25
#print "[Torrentin] v"+ __version__ + " by " + __author__ + " - SYS ARGV: " + str(sys.argv)

def main():
    uri=None
    funcion=None
    params=get_params()
    try: uri=urllib.unquote_plus(params["uri"])
    except: pass
    try: image=urllib.unquote_plus(params["image"])
    except: image = ""
    try: player=int(params["player"])
    except: player = int(__addon__.getSetting("directplayer"))
    try: funcion=urllib.unquote_plus(params["funcion"])
    except: primer(uri,player,image)
    try: funcionexe = globals()[funcion]
    except: funcionexe = None
    if funcionexe: funcionexe(uri,player,image)
    #print(">>>> URI: "+str(uri))
    #print(">>>> PLAYER: "+str(player))
    #print(">>>> IMAGEN: "+str(image))

def playfile(uri,player,image=""):
    #applaunch(uri,player,image)
    #return
    #Quitar el resto ya no es necesario porque no reproduce torrents de directorios ocultos. (temp de kodi). (YA NO SE USA), se reactiva por problemas con nombres de torrents y TSC
    destino = os.path.join(__addon__.getSetting('torrent_path') , "torrentin.torrent" )
    ok = copytorrent(uri.replace("file://",""),image)
    if ok:
        applaunch("file://"+destino,player,image)
    else: applaunch(uri,player,image)
    #else: mensaje('Error al copiar el fichero torrent.', 3000)

def playmagnet(magnet,player,imagen=""):
    if MagnetPlayers(player):
        res = xbmcgui.Dialog().yesno("Torrentin" , "El reproductor seleccionado no admite enlaces magnet","Elige los que aparecen en verde.","Cambiar de reproductor?")
        if res:
            player =menu
            player = askplayer(magnet,player,imagen)
            if MagnetPlayers(player):
                mensaje('Reproductor incorrecto para magnet', 3000)
                return
            applaunch(magnet,player,imagen)
    else:
        applaunch(magnet,player,imagen)

def playace(uri,player,imagen=""):
    if ChkAcePlayers(player):
        res = xbmcgui.Dialog().yesno("Torrentin" , "El reproductor seleccionado no admite enlaces acestream","Elige los que aparecen en verde.","Cambiar de reproductor?")
        if res:
            player =menu
            player = askplayer(uri,player,imagen)
    if player == 1:
        torrents.play_acelive(uri,imagen)
    elif player == 7 or player == 8:
        torrents.plexus(uri,player,imagen)
    elif player == 9:
        torrents.torrenter(uri,player,imagen)
    elif player == 16:
        xbmc.executebuiltin('XBMC.StartAndroidActivity("ru.vidsoftware.acestreamcontroller.free","android.intent.action.VIEW","","'+uri+'")')
    elif player == 17:
        xbmc.executebuiltin('XBMC.StartAndroidActivity("org.acestream","android.intent.action.VIEW","","'+uri+'")')
    else:
        mensaje('Reproductor incorrecto para AceLive', 3000)

def MagnetPlayers(player):
    if (player == 1 or player == 7 or  player ==8  or player == 17): return True
    else: return False

def ChkAcePlayers(player):
    if (player == 1 or player == 7 or  player ==8  or player == 9 or player == 16 or player == 17): return False
    else: return True

def applaunch(uri,player,imagen =""):
    if player == 1:
        torrents.play_torrent_from_file(uri.replace("file://",""),imagen)
    elif player == 2 or player == 3 or player == 4 or player == 5 or player == 6 or player == 11:
        torrents.SteeveClones(uri,player,imagen)
    elif player == 7 or player == 8:
        torrents.plexus(uri,player,imagen)
    elif player == 9:
        torrents.torrenter(uri,player,imagen)
    elif player == 10:
        torrents.yatp(uri,player,imagen)
    # 11 elementum
    elif player == 12:
        xbmc.executebuiltin('XBMC.StartAndroidActivity("com.mobilityflow.tvp","android.intent.action.VIEW","","'+uri+'")')
    elif player == 13:
        xbmc.executebuiltin('XBMC.StartAndroidActivity("com.mobilityflow.tvp.prof","android.intent.action.VIEW","","'+uri+'")')
    elif player == 14:
        xbmc.executebuiltin('XBMC.StartAndroidActivity("tv.bitx.media","android.intent.action.VIEW","","'+uri+'")')
    elif player == 15:
        xbmc.executebuiltin('XBMC.StartAndroidActivity("tv.bitfalcon.media","android.intent.action.VIEW","","'+uri+'")')
    elif player == 16:
        xbmc.executebuiltin('XBMC.StartAndroidActivity("ru.vidsoftware.acestreamcontroller.free","android.intent.action.VIEW","torrent","'+uri+'")')
    elif player == 17:
        xbmc.executebuiltin('XBMC.StartAndroidActivity("org.acestream","android.intent.action.VIEW","torrent","'+uri+'")')
    elif player == 18:
        xbmc.executebuiltin('XBMC.StartAndroidActivity("com.mtorrent.player.gp","android.intent.action.VIEW","torrent","'+uri+'")')
    elif player == 19:
        xbmc.executebuiltin('XBMC.StartAndroidActivity("com.mdc.mtorrent.player","android.intent.action.VIEW","","'+uri+'")')
    elif player == 20:
        if uri.startswith('file://'):
            uri = torrents.torrent_to_magnet(uri.replace("file://",""))
        if uri: xbmc.executebuiltin('XBMC.StartAndroidActivity("com.gamemalt.streamtorrentvideos","android.intent.action.VIEW","","'+uri+'")')
    elif player == 21:
        xbmc.executebuiltin('XBMC.StartAndroidActivity("com.torrent_player","android.intent.action.VIEW","torrent","'+uri+'")')
    elif player == 22:
        xbmc.executebuiltin('XBMC.StartAndroidActivity("org.itsasoftware.torrent.streaming","android.intent.action.VIEW","","'+uri+'")')
    elif player == 23:
        if uri.startswith('file://'):
            uri = torrents.torrent_to_magnet(uri.replace("file://",""))
        if uri: xbmc.executebuiltin('XBMC.StartAndroidActivity("rocks.turkeytorrent.player","android.intent.action.VIEW","","'+uri+'")')
    elif player == 24:
        xbmc.executebuiltin('XBMC.StartAndroidActivity("'+gestornames[1]+'","android.intent.action.VIEW","","'+uri+'")')

def copytorrent(origen,image):
#        if xbmcvfs.copy(origen,destino): return True
#        else: return False
        destino = os.path.join(__addon__.getSetting('torrent_path') , "torrentin.torrent" )
        try:
            f = open(origen, 'rb+')
            torrent_data=f.read()
            f.close
        except:
            return False
        xbmc.sleep(200)
        try:
            f = open(destino , "wb+")
            f.write(torrent_data)
            f.close()
        except:
            return False
        torrents.SaveImgLink(image)
        return True

def copymagnet(magnet,image):
    destino = os.path.join(__addon__.getSetting('torrent_path') , "torrentin.magnet" )
    destinoimg = os.path.join(__addon__.getSetting('torrent_path') , "torrentin.magnet.img" )
    if image.startswith("http:") or image == "":
        try:
            f = open(destino , "wb")
            f.write(magnet)
            f.close()
        except: return False
        if image !="":
            try:
                f = open(destinoimg , "wb")
                f.write(image)
                f.close()
            except: return False
        else:
            try:
                #default = os.path.join( __cwd__ ,"resources","images","magnetlogo.png") 
                f = open(destinoimg , "wb")
                f.write("http://i.imgur.com/H3xpR22.png")
                f.close()
            except: return False

def get_params():
      param=[]
      paramstring=sys.argv[2]
      if len(paramstring)>=2:
            params=sys.argv[2]
            cleanedparams=params.replace('?','')
            if (params[len(params)-1]=='/'):
                  params=params[0:len(params)-2]
            pairsofparams=cleanedparams.split('&')
            param={}
            for i in range(len(pairsofparams)):
                  splitparams={}
                  splitparams=pairsofparams[i].split('=')
                  if (len(splitparams))==2:
                        param[splitparams[0]]=splitparams[1]                 
      return param

def askplayer(uri,player,image):
    torrent_folder = __addon__.getSetting('torrent_path')
    torrent_folder2 = __addon__.getSetting('torrent_path_tvp')
    colorace = "lime"
    colornormal = "lime"
    colorall = "lime"
    guardar = True
    torr = True
    descargar = True
    tipo = "Torrent"
    if uri.startswith("magnet:"):
        colorace = "red"
        tipo = "Magnet"
    if uri.startswith("acestream://"):
        if __addon__.getSetting('aceplay') == "true": return 1
        colornormal = "red"
        guardar = False
        torr = False
        descargar = False
    try:
        if torrent_folder2 and (torrent_folder2 in uri or torrent_folder2 in image) : guardar = False 
        if not "torrentin.torrent" in uri and (torrent_folder in uri or torrent_folder in image): guardar = False
    except: pass
    if __addon__.getSetting("automenu") == "true": autoconf("1","","")
    info = torrents.torrent_info(uri , 0)
    players = [info]
    #players.append("[COLOR yellow]img: [/COLOR]"+image)
    if "RAR" in info:
        if __addon__.getSetting("quasar") == "true": players.append("[COLOR " + colornormal + "][add-on]    Quasar[/COLOR]")
    #if not "No Video" in info:
    elif info !="":
        if __addon__.getSetting("aces") == "true":    players.append("[COLOR " + colorace + "][engine]    AceStream[/COLOR]")
        if __addon__.getSetting("elem") == "true":    players.append("[COLOR " + colornormal + "][add-on]    Elementum[/COLOR]")
        if __addon__.getSetting("quasar") == "true": players.append("[COLOR " + colornormal + "][add-on]    Quasar[/COLOR]")
        if __addon__.getSetting("pulsar") == "true":  players.append("[COLOR " + colornormal + "][add-on]    Pulsar[/COLOR]")
        if __addon__.getSetting("yatp") == "true":     players.append("[COLOR " + colornormal + "][add-on]    Yet Another Torrent Player[/COLOR]")
        if __addon__.getSetting("tter") == "true":       players.append("[COLOR " + colorall + "][add-on]    Torrenter[/COLOR]")
        if __addon__.getSetting("kmed") == "true":   players.append("[COLOR " + colornormal + "][add-on]    KmediaTorrent[/COLOR]")
        if __addon__.getSetting("plexus") == "true": players.append("[COLOR " + colorace + "][add-on]    Plexus[/COLOR]")
        if __addon__.getSetting("xbmct") == "true":  players.append("[COLOR " + colornormal + "][add-on]    XBMCtorrent[/COLOR]")
        if __addon__.getSetting("strm") == "true":     players.append("[COLOR " + colornormal + "][add-on]    Stream[/COLOR]")
        if __addon__.getSetting("p2p") == "true":      players.append("[COLOR " + colorace + "][add-on]    p2p-Streams[/COLOR]")
        if xbmc.getCondVisibility('System.Platform.Android') and not ("No Video" or "RAR") in info: 
            if __addon__.getSetting("tvp") == "true":         players.append("[COLOR " + colornormal + "][app]          Torrent Video Player[/COLOR]")
            if __addon__.getSetting("tvpp") == "true":       players.append("[COLOR " + colornormal + "][app]          Torrent Video Player Pro[/COLOR]")
            if __addon__.getSetting("bitx") == "true":        players.append("[COLOR " + colornormal + "][app]          BitX[/COLOR]")
            if __addon__.getSetting("bfalc") == "true":      players.append("[COLOR " + colornormal + "][app]          BitFalcon[/COLOR]")
            if __addon__.getSetting("tsc") == "true":          players.append("[COLOR " + colorall + "][app]          Torrent Stream Controller[/COLOR]")
            if __addon__.getSetting("acep") == "true":       players.append("[COLOR " + colorace + "][app]          AcePlayer[/COLOR]")
            if __addon__.getSetting("mtorg") == "true":       players.append("[COLOR " + colornormal + "][app]          mTorrent (GP)[/COLOR]")
            if __addon__.getSetting("mtorm") == "true":       players.append("[COLOR " + colornormal + "][app]          mTorrent (MDC)[/COLOR]")
            if __addon__.getSetting("xtor") == "true":       players.append("[COLOR " + colornormal + "][app]          Xtorrent[/COLOR]")
            if __addon__.getSetting("tpl") == "true":       players.append("[COLOR " + colornormal + "][app]          Torrent Player[/COLOR]")
            if __addon__.getSetting("tvs") == "true":       players.append("[COLOR " + colornormal + "][app]          Torrent Video Streaming[/COLOR]")
            if __addon__.getSetting("turk") == "true":       players.append("[COLOR " + colornormal + "][app]          Turkey torrent video player[/COLOR]")
    if oswin: players.append("[COLOR deepskyblue][programa] Asociado a torrent/magnet/acestream (Win)[/COLOR]")
    #players.append("[COLOR orange]     ----====[  ExtendedInfo  ]====----[/COLOR]")
    if descargar and int(__addon__.getSetting("tordown")) != 0 and xbmc.getCondVisibility('System.Platform.Android') : players.append("[COLOR orange]     ----====[  Descargar con "+gestornames[0]+"  ]====----[/COLOR]")
    if guardar:
        players.append("[COLOR orange]     ----====[  Guardar el "+tipo+"  ]====----[/COLOR]")
    elif torr :
        #if tipo == "Torrent": 
        #players.append("[COLOR orange]     ----====[  Actualizar información extra  ]====----[/COLOR]")
        players.append("[COLOR orange]     ----====[  Borrar el "+tipo+"  ]====----[/COLOR]")
    if "RAR" in info:
        if not xbmcgui.Dialog().yesno("Torrentin" , "[COLOR red][B]¡¡¡ ATENCIÓN !!![/COLOR][/B][COLOR orange]    El vídeo está comprimido en RAR[/COLOR]","[COLOR orange]Solo Quasar es capaz de descargarlo y descomprimirlo.[/COLOR]","[COLOR lime]¿ Quieres continuar para guardarlo o descargarlo ?[/COLOR]"): return menu
    if "No Video" in info:
        if not xbmcgui.Dialog().yesno("Torrentin" , "[COLOR red][B]¡¡¡ ATENCIÓN !!![/COLOR][/B]","[COLOR orange]No se ha encontrado ningún archivo de video en el torrent.[/COLOR]","       [COLOR lime]¿ Quieres continuar para guardarlo o descargarlo ?[/COLOR]"): return menu
    seleccion = xbmcgui.Dialog().select("Torrentin - Seleccionar Reproductor", players)
    reproductor = players[seleccion]
    if seleccion != -1:
        if seleccion == 0:
            if xbmc.getCondVisibility('System.HasAddon(script.extendedinfo)'):
                einfo_torrent(uri,player,image)
            else:
                if xbmcgui.Dialog().yesno("Torrentin - Información del torrent" , info,"","","[COLOR lime]Menú[/COLOR]","[COLOR yellow]ExtendedInfo[/COLOR]"):
                    if xbmc.getCondVisibility('System.HasAddon(script.extendedinfo)'):
                        einfo_torrent(uri,player,image)
                    else:
                        xbmcgui.Dialog().ok("Torrentin - ExtendedInfo No encontrado" , "[COLOR yellow]Necesario AddOn externo para usar esta opción:[/COLOR]","[COLOR lime]AddOns -> Instalar desde repositorio -> KODI add-on repository -> Add-ons de programas -> ExtendedInfo Script\n[COLOR orange](despés de instalarlo configúralo para español).[/COLOR]")
                        principal(uri,player,image)
                else: principal(uri,player,image)
        elif "]    AceStream" in reproductor: return 1
        elif "]    XBMCtorrent" in reproductor: return 2
        elif "]    Stream" in reproductor: return 3
        elif "]    KmediaTorrent" in reproductor: return 4
        elif "]    Pulsar" in reproductor: return 5
        elif "]    Quasar" in reproductor: return 6
        elif "]    p2p-Streams" in reproductor: return 7
        elif "]    Plexus" in reproductor: return 8
        elif "]    Torrenter" in reproductor: return 9
        elif "]    Yet Another" in reproductor: return 10
        elif "]    Elementum" in reproductor: return 11
        elif "]          Torrent Video Player Pro" in reproductor: return 13
        elif "]          Torrent Video Player" in reproductor: return 12
        elif "]          BitX" in reproductor: return 14
        elif "]          BitFalcon" in reproductor: return 15
        elif "]          Torrent Stream Controller" in reproductor: return 16
        elif "]          AcePlayer" in reproductor: return 17
        elif "]          mTorrent (GP)" in reproductor: return 18
        elif "]          mTorrent (MDC)" in reproductor: return 19
        elif "]          Xtorrent" in reproductor: return 20
        elif "]          Torrent Player" in reproductor: return 21
        elif "]          Torrent Video Streaming" in reproductor: return 22
        elif "]          Turkey" in reproductor: return 23
        elif "[  Descargar" in reproductor: return 24
        elif "[  Guardar" in reproductor: guardar_torrent(uri,player,image)
        elif "[  Borrar" in reproductor:
            borrar_torrent(uri,player,image)
            return menu
        elif "[programa] Asociado" in reproductor:
            os.startfile(uri)
            return menu
        #elif "[  ExtendedInfo" in reproductor:
            #einfo_torrent(uri,player,image)
        #elif "[  Actualizar" in reproductor:
            #catalogar_torrent(uri)
            #return menu
        #return seleccion
        else: return menu
    else: return menu

def borrar_torrent(uri,player,image):
    if os.path.isdir(uri.replace("file://","")):
        if xbmcgui.Dialog().yesno("Torrentin - Eliminar Directorio" , "[COLOR magenta]Dir: [/COLOR][COLOR cyan]" + uri.replace("file://","") + "[/COLOR]" , "[COLOR red]         ¡¡¡ ATENCION !!![/COLOR] - [COLOR yellow]Esta opción no se puede deshacer,[/COLOR]" , "[COLOR limegreen]¿Desea Eliminar el directorio y los torrents contenidos en el?[/COLOR]","Cancelar","Borrar"):
            import shutil
            try: shutil.rmtree(uri.replace("file://",""))
            except: pass
            xbmc.executebuiltin('Container.Refresh')
        return
    try:
        if uri.startswith("file://"):
            file = uri.replace("file://","")
            fileinfo = uri.replace("file://","").replace(".torrent",".info").replace(".magnet",".info")
            if os.path.isfile(file): os.remove(file)
            if os.path.isfile(fileinfo): os.remove(fileinfo)
        elif uri.startswith("magnet:"):
            file = image.replace('.jpg','.magnet')
            if os.path.isfile(file): os.remove(file)
            file = image.replace('.jpg','.info')
            if os.path.isfile(file): os.remove(file)
            file = image.replace('.png','.magnet')
            if os.path.isfile(file): os.remove(file)
            file = image.replace('.png','.info')
            if os.path.isfile(file): os.remove(file)
    except: pass
    if os.path.isfile(image): os.remove(image)
    xbmc.executebuiltin('Container.Refresh')

def mover_torrent(uri,player,image):
    if not oswin:
        dir = uri.rsplit("/",1)[0].replace("file://","")
        fichero = uri.rsplit("/",1)[1]
        if image != "": nimage=image.rsplit("/",1)[1]
    else:
        dir = uri.rsplit("\\",1)[0].replace("file://","")
        fichero = uri.rsplit("\\",1)[1]
        if image != "": nimage=image.rsplit("\\",1)[1]
    dirList=os.listdir( dir )
    if __addon__.getSetting('torrent_path').startswith(dir) or __addon__.getSetting('torrent_path_tvp').startswith(dir): list=[]
    else: list=[".."]
    for fname in dirList:
        if os.path.isdir(os.path.join(dir,fname)):
            list.append(fname)
    if len(list)!=0:
        dest = xbmcgui.Dialog().select("Selecciona directorio", list)
        if dest != -1:
            file = uri.replace("file://","")
            fileinfo = uri.replace("file://","").replace(".torrent",".info").replace(".magnet",".info")
            if os.path.isfile(file):
                os.rename(file,os.path.join(dir,list[dest],fichero))
            if os.path.isfile(fileinfo):
                os.rename(fileinfo,os.path.join(dir,list[dest],fichero.replace(".torrent",".info").replace(".magnet",".info")))
            if os.path.isfile(image):
                os.rename(image,os.path.join(dir,list[dest],nimage))
            xbmc.executebuiltin('Container.Refresh')
    else:
        xbmcgui.Dialog().ok("Torrentin - Mover torrent/magnet","[COLOR yellow]No hay ningún directorio aquí","tienes que crearlo antes de mover.[/COLOR]")
    
def guardar_magnet(uri,player,image,torr_folder,teclado=False):
    title =""
    try:
        title = uri.rsplit("dn=")[1] 
        title = title.rsplit("&")[0] 
        title = urllib.unquote_plus(title)
        title = title.replace("+"," ").replace("?","¿").replace("*","").replace(":",",")
        #title = unicode(title,'utf-8')
        #title = tools.latin1_to_ascii(title)
    except: pass
    if title == "" or teclado:
        keyboard = xbmc.Keyboard(title,"Magnet sin título, escríbelo, añade CapxTemp (#x##) si es Serie TV.")
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            title = keyboard.getText()
        else: return
    if title == "":
        xbmcgui.Dialog().ok("Torrentin" , "Tienes que escribir un nombre para el magnet.","Repite el proceso y escríbelo con el teclado,","añade CapxTemp (#x##) si es Serie TV.")
        if __addon__.getSetting('reopen') == "true": principal(uri,player,image)
        return
    global savetit
    global busca
    savetit=title
    busca=''
    if re.search("\d{1,2}[x]\d{2}",title) or re.search("Cap.\d+",title) or re.search("S\d{2}E\d{2}",title):
        poster,fanart,infoLabels=MetaTorrent(title,"tv",1)
    else: poster,fanart,infoLabels=MetaTorrent(title,"movie",1) 
    if poster != "" and fanart != "" and infoLabels != "":
        try:
            file = open(os.path.join(torr_folder,title + ".info"),"wb")
            file.write(poster + "|" + fanart + "|" + infoLabels['rating'] + "|" + infoLabels['votes'] + "|" + infoLabels['plot'] + "|" + infoLabels['genre'] + "|" + infoLabels['title'] + "|" + infoLabels['originaltitle'] + "|" + infoLabels['year'] + "|" + infoLabels['tmdb_id'] )
            file.close()
        except: pass
    try:
        f = open(os.path.join( torr_folder , title + ".magnet") , "wb")
        f.write(uri)
        f.close()
    except:
        mensaje('ERROR al guardar el magnet, revisa el nombre.', 3000)
        guardar_magnet(uri,player,image,torr_folder,True)
        return
    # Guardamos la caratula
    if image != "":
        image_data = ""
        if image.startswith("http"):
            image_data = torrents.url_get(image)
        else:
            try:
                f = open(image, "rb")
                image_data=f.read()
                f.close()
            except: pass
        if image_data =="":
            mensaje('ERROR al obtener la caratula.', 3000)
            try:
                f = open(os.path.join( __cwd__ ,"resources","images","magnetlogo.png") , "rb")
                image_data=f.read()
                f.close()
                f = open(os.path.join( torr_folder , title + ".png" ) , "wb")
                f.write(image_data)
                f.close()
                xbmc.sleep(2500)
                show_Msg('Magnet guardado (sin carátula)',title,2000)
            except: pass
            if __addon__.getSetting('reopen') == "true": principal(uri,player,image)
            return
        if ".png" in image.lower(): ext=".png"
        elif ".gif" in image.lower(): ext=".gif"
        elif ".jpg" in image.lower(): ext= ".jpg"
        else: ext = ".img"
        try:
            f = open(os.path.join( torr_folder , title + ext ) , "wb")
            f.write(image_data)
            f.close()
            xbmc.sleep(2500)
            show_Msg('Magnet y Carátula guardados:',title,2000,image)
        except:
            mensaje('ERROR al guardar la caratula.', 3000)
            if __addon__.getSetting('reopen') == "true": principal(uri,player,image)
            return
    else:
        try:
            f = open(os.path.join( __cwd__ ,"resources","images","magnetlogo.png") , "rb")
            image_data=f.read()
            f.close()
            f = open(os.path.join( torr_folder , title + ".png" ) , "wb")
            f.write(image_data)
            f.close()
            xbmc.sleep(2500)
            show_Msg('Magnet guardado (sin carátula)',title,2000)
        except:
            mensaje('ERROR al guardar la carátula.', 3000)
            if __addon__.getSetting('reopen') == "true": principal(uri,player,image)
            return
    if __addon__.getSetting('reopen') == "true": principal(uri,player,image)

def guardar_torrent(uri,player,image):
    carat = True
    if __addon__.getSetting("saveopt") == "0" : torr_folder = __addon__.getSetting('torrent_path')
    else:
        if __addon__.getSetting('torrent_path_tvp'):
            torr_folder=__addon__.getSetting('torrent_path_tvp')
        else:
            xbmcgui.Dialog().ok("Torrentin" , "Directorio secundario de torrents no configurado","Configúralo y vuelve a darle a Guardar")
            settings("","","")
            return
    if uri.startswith("magnet:"): 
        guardar_magnet(uri,player,image,torr_folder,False)
        return
    save = savetorrent(uri,image,torr_folder,1)
    if not save:
        res = xbmcgui.Dialog().yesno("Torrentin" , "Ha habido un error al guardar el torrent/caratula","Probablemente por algún caracter no válido","Reintentar con el teclado?")
        if res:
            save = savetorrent(uri,image,torr_folder,2)
            if not save: xbmcgui.Dialog().ok("Torrentin" , "Ha habido un error desconocido al guardar el torrent/caratula")
    else:
        xbmc.sleep(2500)
        if carat:
            if save.startswith("nocarat"):
                show_Msg("Torrent guardado (sin carátula): ", save.replace("nocarat",""),2000)
            else: show_Msg("Torrent y carátula guardados: ", save,2000,image)
        else: show_Msg("Torrent guardado (sin carátula): ", save.replace("nocarat",""),2000)
    if __addon__.getSetting('reopen') == "true": principal(uri,player,image)

def savetorrent(uri,image,torr_folder,modo):
    if uri.startswith("file://"): file = uri.replace("file://","")
    else: return False
    try:
        f = open(file , "rb")
        torrent_data=f.read()
        f.close()
    except: return False
    import base64
    import bencode
    import hashlib
    try:
        metadata = bencode.bdecode(torrent_data)
    except:
        pass
    try:
        title = metadata['info']['name']
    except:
        title = ""
        modo = 2
        pass
    title = title.replace(".avi","").replace(".mp4","").replace(".mkv","").replace("+"," ").replace("?","¿").replace("*","").replace(":",",")
    '''
    try:
        title = unicode(title,'utf-8')
        title = tools.latin1_to_ascii(title)
        #title = tools.StripTags(title)
    except: pass
    '''
    if modo == 2:
        keyboard = xbmc.Keyboard(title,"Torrent sin título, escríbelo, añade CapxTemp (#x##) si es Serie TV.")
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            title = keyboard.getText()
        else: return False
    if title=="": return False
    global savetit
    global busca
    savetit=title
    busca=''
    if re.search("\d{1,2}[x]\d{2}",title) or re.search("Cap.\d+",title) or re.search("S\d{2}E\d{2}",title):
        poster,fanart,infoLabels=MetaTorrent(title,"tv",1) 
    else: poster,fanart,infoLabels=MetaTorrent(title,"movie",1) 
    if poster != "" and fanart != "" and infoLabels != "":
        try:
            file = open(os.path.join(torr_folder,title + ".info"),"wb")
            file.write(poster + "|" + fanart + "|" + infoLabels['rating'] + "|" + infoLabels['votes'] + "|" + infoLabels['plot'] + "|" + infoLabels['genre'] + "|" + infoLabels['title'] + "|" + infoLabels['originaltitle'] + "|" + infoLabels['year'] + "|" + infoLabels['tmdb_id'] )
            file.close()
        except: pass
    try:
        f = open(os.path.join( torr_folder , title + ".torrent") , "wb")
        f.write(torrent_data)
        f.close()
    except: return False
    if image != "":
        image_data = ""
        if image.startswith("http"):
            image_data =torrents.url_get(image)
        else:
            try:
                f = open(image , "rb")
                image_data=f.read()
                f.close()
            except: pass
        if image_data =="": return "nocarat"+title
        if ".png" in image.lower(): ext=".png"
        elif ".gif" in image.lower(): ext=".gif"
        elif ".jpg" in image.lower(): ext= ".jpg"
        else: ext = ".img"
        try:
            f = open(os.path.join( torr_folder , title + ext ) , "wb")
            f.write(image_data)
            f.close()
        except: 
            os.remove(os.path.join( torr_folder , title + ext ))
            return "nocarat"+title
    else: return "nocarat"+title
    return title

def einfo_torrent(uri,player,image):
	title = torrents.torrent_info(uri , 1)
	if title=="":
		keyboard = xbmc.Keyboard(title,"No se ha encontrado ningún título en el torrent/magnet, introdúcelo...")
		keyboard.doModal()
		if (keyboard.isConfirmed()):
			title = keyboard.getText()
			if title=="": return
	if not title =="":
		global savetit
		global busca
		savetit=title
		busca=''
		if re.search("\d{1,2}[x]\d{2}",title) or re.search("Cap.\d+",title) or re.search("S\d{2}E\d{2}",title):
			poster,fanart,infoLabels=MetaTorrent(title,"tv",0) 
			if poster != "" and fanart != "" and infoLabels != "":
				xbmc.executebuiltin( "RunScript(script.extendedinfo,info=extendedtvinfo,id=%s" % infoLabels['tmdb_id']+")" )
				if xbmcgui.Dialog().yesno("Torrentin - ExtendedInfo" , "[COLOR limegreen]Espere, mostrando información extendida de la serie:[/COLOR]" , "[B][COLOR orange]" + infoLabels['title'] + " (" + infoLabels['year'] + ")[/COLOR][/B]","[COLOR cyan]" + infoLabels['genre'] + "\n[COLOR magenta]Valoración: " + infoLabels['rating'] + " (" + infoLabels['votes'] + " votos)[/COLOR]","Reproducir","Cancelar"):
					return
		else:
			poster,fanart,infoLabels=MetaTorrent(title,"movie",0) 
			if poster != "" and fanart != "" and infoLabels != "":
				#if xbmcgui.Dialog().yesno("Torrentin - Scraper" , "[COLOR limegreen]Película encontrada en TMDb:[/COLOR]" , "[B][COLOR yellow]" + infoLabels['title'] + " (" + infoLabels['year'] + ")[/COLOR][/B]","[COLOR cyan]" + infoLabels['genre'] + "\n[COLOR magenta]Valoración: " + infoLabels['rating'] + " (" + infoLabels['votes'] + " votos)[/COLOR]","Reproducir","ExtendedInfo"):
				xbmc.executebuiltin( "RunScript(script.extendedinfo,info=extendedinfo,id=%s" % infoLabels['tmdb_id']+")" )
				if xbmcgui.Dialog().yesno("Torrentin - ExtendedInfo" , "[COLOR limegreen]Espere, mostrando información extendida de la película:[/COLOR]" , "[B][COLOR yellow]" + infoLabels['title'] + " (" + infoLabels['year'] + ")[/COLOR][/B]","[COLOR cyan]" + infoLabels['genre'] + "\n[COLOR magenta]Valoración: " + infoLabels['rating'] + " (" + infoLabels['votes'] + " votos)[/COLOR]","Reproducir","Cancelar"):
					return
	#else:
		#show_Msg("ExtendedInfo","No se ha encontrado ningún título",1000)
	principal(uri,player,image)
	return

def MetaTorrent(title,tipo,modo):
	generos = {28:"Acción",12:"Aventura",16:"Animación",35:"Comedia",80:"Crimen",99:"Documental",18:"Drama",10751:"Familia",14:"Fantasía",36:"Historia",27:"Terror",10402:"Música",9648:"Misterio",10749:"Romance",878:"Ciencia ficción",10770:"Película de la televisión",53:"Suspense",10752:"Guerra",37:"Western"}
	resultados = []
	imagenes = []
	fans = []
	labels = []
	if tipo=="movie": tipoesp="[COLOR yellow](Película)[/COLOR] "
	else: tipoesp="[COLOR orange](Serie)[/COLOR] "
	striptitle=tools.StripTags(title)
	striptitle = re.sub("\A\d{2}\s",'',striptitle) #añadido por la mania de numerar pelis (DxTotal)
	striptitle = striptitle.replace(".DVD","").replace("HDTV","").replace(".XviD","").replace("Screener","").replace("screener","").replace(".MP3","").replace("DVDRIP","").replace("DVDRip","") #.replace("bluray","").replace("720p","").replace("1080p","").replace("x264","")
	striptitle = striptitle.replace("."," ").replace("_"," ").replace("-"," ")
	try:
		data = torrents.url_get("http://api.themoviedb.org/3/search/"+tipo+"?api_key=cc4b67c52acb514bdf4931f7cedfd12b&query=" + striptitle.replace(" ","%20") + "&language=es&include_adult=false")
	except:
		try:
			xbmc.sleep(500)
			data = torrents.url_get("http://api.themoviedb.org/3/search/"+tipo+"?api_key=cc4b67c52acb514bdf4931f7cedfd12b&query=" + striptitle.replace(" ","%20") + "&language=es&include_adult=false")
		except:
			mensaje(title + " Error al obtener info en TMDb",3000)
			return '','',''
	if data == "":
		mensaje(title + " Error, no hay datos de TMDb",3000)
		return '','',''
	datadict = json.loads(data)
	#numresultados=datadict['total_results']
	for s in datadict['results']:
		infoLabels = {}
		if tipo =="movie":
			infoLabels['originaltitle'] = s['original_title'].encode('utf-8')
			titulo = s['title'].encode('utf-8')
			year = s['release_date'].split('-')[0].encode('utf-8')
			resultados.append(titulo + ' (' + year + ')')
		else:
			infoLabels['originaltitle'] = s['original_name'].encode('utf-8')
			titulo = s['name'].encode('utf-8')
			year = s['first_air_date'].split('-')[0].encode('utf-8')
			resultados.append(titulo + ' (' + year + ')')
		if s['poster_path']: imagenes.append("https://image.tmdb.org/t/p/original" +  s['poster_path'].encode('utf-8'))
		else: imagenes.append(os.path.join(__cwd__,"resources","images","torrentlogo.png"))
		if s['backdrop_path']: fans.append("https://image.tmdb.org/t/p/original" +  s['backdrop_path'].encode('utf-8'))
		else: fans.append(os.path.join(__cwd__,"fanart.jpg"))
		if s['overview']: infoLabels['plot'] = s['overview'].encode('utf-8')
		else: infoLabels['plot'] =  'No hay sinopsis.'
		if s['vote_average']: infoLabels['rating'] = str(s['vote_average'])
		else: infoLabels['rating'] = "0"
		if s['vote_count']: infoLabels['votes'] = str(s['vote_count'])
		else: infoLabels['votes'] = "0"
		infoLabels['title'] = titulo
		infoLabels['year'] = year
		if s['genre_ids']:
			listageneros = json.loads(str(s['genre_ids']))
			genero = ""
			for g in listageneros:
				try: genero += generos.get(g) + " - "
				except: pass
			infoLabels['genre'] = genero.strip(" - ")
		else: infoLabels['genre'] = "Género no definido"
		if s['id']: infoLabels['tmdb_id'] = str(s['id'])
		else: infoLabels['tmdb_id'] = ""
		labels.append(infoLabels)
	if len(resultados)==1:
		if modo == 1:show_Msg(resultados[0] ,"Información extra añadida.",3000,imagenes[0])
		return imagenes[0],fans[0],labels[0]
	elif len(resultados)>1:
		resultados.insert(0, "[COLOR orange]---==[([COLOR yellow] Consultar en la web [COLOR orange])]==----[/COLOR]")
		resultados.insert(0, "[COLOR orange]---==[([COLOR yellow] Búsqueda manual [COLOR orange])]==----[/COLOR]")
		seleccion = xbmcgui.Dialog().select(tipoesp + savetit , resultados)
		if seleccion ==0:
			striptitle=savetit.replace("."," ").replace("_"," ").replace("-"," ")
			keyboard = xbmc.Keyboard(striptitle,tipoesp + savetit)
			keyboard.doModal()
			if (keyboard.isConfirmed()):
				striptitle = keyboard.getText()
				if striptitle=="": return '','',''
				nuevotitulo = MetaTorrent(striptitle,tipo,modo)
				return nuevotitulo
			else: return '','',''
		elif seleccion ==1:
			if xbmc.getCondVisibility('system.platform.Android'):
				if __addon__.getSetting('browser') == '0':
					xbmc.executebuiltin('XBMC.StartAndroidActivity("com.android.browser","android.intent.action.VIEW","","'+"https://www.themoviedb.org/search/"+tipo+"?query=" + striptitle.replace(" ","+")+'")')
				elif __addon__.getSetting('browser') == '1':
					xbmc.executebuiltin('XBMC.StartAndroidActivity("com.android.chrome","android.intent.action.VIEW","","'+"https://www.themoviedb.org/search/"+tipo+"?query=" + striptitle.replace(" ","+")+'")')
			elif xbmc.getCondVisibility('system.platform.windows'):
				os.startfile("https://www.themoviedb.org/search/"+tipo+"?query=" + striptitle.replace(" ","+"))
			else:
				mensaje('Opción disponible en Windows y Android', 3000)
			nuevotitulo = MetaTorrent(striptitle,tipo,modo)
			return nuevotitulo
		elif seleccion >1: #Ha seleccionado alguna
			nuevotitulo = resultados[seleccion]
			if modo == 1:  show_Msg(nuevotitulo , "Información extra añadida." ,3000,imagenes[seleccion-2])
			return imagenes[seleccion-2],fans[seleccion-2],labels[seleccion-2]
		else: # canceló
			return '','',''
	else:
		xbmc.sleep(100)
		reintentatitle = striptitle.rsplit(" ")
		quita = striptitle.rsplit(" ",1)[0]
		if len(reintentatitle) >1:
			nuevotitulo = MetaTorrent(quita,tipo,modo)
			return nuevotitulo
		else :
			xbmc.sleep(200)
			global busca
			if busca=='': striptitle2=savetit.replace("."," ").replace("_"," ").replace("-"," ")
			else: striptitle2=busca
			reintentatitle2 = striptitle2.split(" ")
			if len(reintentatitle2) >1:
				quita2 = striptitle2.split(" ",1)[1]
				busca = quita2
				nuevotitulo = MetaTorrent(quita2,tipo,modo)
				return nuevotitulo
			else :
				striptitle=savetit.replace("."," ").replace("_"," ").replace("-"," ")
		if xbmcgui.Dialog().yesno("Torrentin - Scraper" , "[COLOR magenta]La " + tipoesp + "[COLOR dodgerblue]" + striptitle  + "[/COLOR]","[COLOR magenta]No se encuentra en TMDb con ese nombre.[/COLOR]","[COLOR cyan]¿ Búsqueda manual ?[/COLOR]","Descartar","Teclado"):
			keyboard = xbmc.Keyboard(striptitle,tipoesp + savetit)
			keyboard.doModal()
			if (keyboard.isConfirmed()):
				striptitle = keyboard.getText()
				if striptitle =="": return '','',''
				nuevotitulo = MetaTorrent(striptitle,tipo,modo)
				return nuevotitulo
			else: return '','',''
		else:
			return '','',''

def autoconf(uri="",player="",image=""):
    for k,v in addons.iteritems():
        if  xbmc.getCondVisibility('System.HasAddon("plugin.video.' + k + '")'):  __addon__.setSetting(v,"true")
        else: __addon__.setSetting(v,"false")
    if  xbmc.getCondVisibility('System.HasAddon("program.plexus")'):  __addon__.setSetting("plexus","true")
    else: __addon__.setSetting("plexus","false")
    if not uri == "1": mensaje("AddOns del menú auto-configurados", 3000)

def settings(uri="",player="",image=""):
    __addon__.openSettings()
    if xbmc.getCondVisibility("System.HasAddon(plugin.video.pulsar)") and xbmc.getCondVisibility("System.HasAddon(plugin.video.quasar)"): xbmcgui.Dialog().ok("Torrentin" , "Los Add-Ons Pulsar y Quasar NO se pueden tener ", "instalados juntos en un mismo Kodi, ya que se crean","conflictos entre ellos, desinstala o inhabilita alguno de los dos.")
    xbmc.executebuiltin('Container.Refresh')

def chkprogram(name):
    if  xbmc.getCondVisibility('System.HasAddon("program.' + name + '")'): return False
    else:
        return xbmcgui.Dialog().yesno("Torrentin" , "El Add-On  "+name.upper()+"  está activado en el menú ","de reproductores y está deshabilitado o no instalado.","¿ Quieres desactivarlo en el menú de reproductores ?")

def chkplugin(name):
    if  xbmc.getCondVisibility('System.HasAddon("plugin.video.' + name + '")'): return False
    else:
        return xbmcgui.Dialog().yesno("Torrentin" , "El Add-On  "+name.upper()+"  está activado en el menú ","de reproductores y está deshabilitado o no instalado.","¿ Quieres desactivarlo en el menú de reproductores ?")

def dellst(uri="",player="",image=""):
    torrent_folder=__addon__.getSetting('torrent_path')
    if xbmcgui.Dialog().yesno("Torrentin" ,"","¿ Borrar todas las listas M3U ?"):
        lst = tools.chklst()
        for lista in lst:
            os.remove(os.path.join( torrent_folder , lista ))
            xbmc.executebuiltin('XBMC.Container.Update(%s,"")' % os.path.join( torrent_folder , lista ) )

def lst(uri="",player="",image=""):
    lst = tools.chklst()
    addon_handle = int(sys.argv[1])
    img=os.path.join( __cwd__ ,"resources","images","delete.png")
    li = xbmcgui.ListItem("[B][COLOR red]Borrar todas las listas[/COLOR][/B]",img,img)
    command = '%s?funcion=dellst&%s' % (sys.argv[0], sys.argv[2])
    li.setProperty('fanart_image',os.path.join(__cwd__,"fanart.jpg"))
    xbmcplugin.addDirectoryItem(addon_handle, command, li, True)
    for lista in lst:
        img=os.path.join( __cwd__ ,"resources","images","m3u.png")
        li = xbmcgui.ListItem("[B][COLOR orange]"+lista.replace(".m3u","")+"[/COLOR][/B]",img,img)
        command = '%s?funcion=lst2&uri=%s&%s' % (sys.argv[0], urllib.quote_plus(lista), sys.argv[2])
        li.setProperty('fanart_image',os.path.join(__cwd__,"fanart.jpg"))
        xbmcplugin.addDirectoryItem(addon_handle, command, li, True)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(addon_handle)

def lst2(uri="",player="",image=""):
    lista = tools.ldlst(uri)
    addon_handle = int(sys.argv[1])
    img=os.path.join( __cwd__ ,"resources","images","acestreamlogo.png")
    for k,v in lista.iteritems():
        li = xbmcgui.ListItem("[B][COLOR orange]"+k+"[/COLOR][/B]",img,img)
        command = '%s?funcion=principal&uri=%s' % (sys.argv[0], urllib.quote_plus(v))
        li.setProperty('fanart_image',os.path.join(__cwd__,"fanart.jpg"))
        xbmcplugin.addDirectoryItem(addon_handle, command, li, False)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(addon_handle)

def cargarlocal(uri="",player="",image=""):
    uri,image = torrents.cargar()
    if uri: principal("file://"+uri,player,image)

def browselocal(uri="",player="",image=""):
    lista = torrents.browsear(1,uri)
    addon_handle = int(sys.argv[1])
    defimg=os.path.join( __cwd__ ,"resources","images","torrentlogo.png")
    for k,v in lista.iteritems():
        if not oswin: titulo = k.split("/")[-1]
        else: titulo = k.split("\\")[-1]
        if k.endswith(".magnet"):
            tipoExt=".magnet"
            esdir = False
            if v == "": li = xbmcgui.ListItem("[B][COLOR lime]"+titulo.replace(tipoExt,'')+"  [COLOR green][/B](m)[/COLOR]",defimg,defimg)
            else: li = xbmcgui.ListItem("[B][COLOR lime]"+titulo.replace(tipoExt,'')+"  [COLOR green][/B](m)[/COLOR]",v,v)
            f = open(k , "rb")
            magnet_data=f.read()
            f.close()
            command = '%s?funcion=principal&uri=%s&image=%s' % (sys.argv[0], urllib.quote_plus(magnet_data),urllib.quote_plus(v))
        elif k.endswith(".torrent"):
            tipoExt=".torrent"
            esdir = False
            if v == "": li = xbmcgui.ListItem("[B][COLOR lime]"+titulo.replace(tipoExt,'')+"  [COLOR green][/B](t)[/COLOR]",defimg,defimg)
            else: li = xbmcgui.ListItem("[B][COLOR lime]"+titulo.replace(tipoExt,'')+"  [COLOR green][/B](t)[/COLOR]",v,v)
            command = '%s?funcion=principal&uri=%s&image=%s' % (sys.argv[0], urllib.quote_plus("file://"+k),urllib.quote_plus(v))
        else:
            tipoExt=".dirctorio"
            esdir=True
            img=os.path.join( __cwd__ ,"resources","images","torrentfolder.png")
            li = xbmcgui.ListItem("[B][COLOR yellow]"+titulo+"[/B][/COLOR]",img,img)
            command = '%s?funcion=browselocal&uri=%s' % (sys.argv[0], urllib.quote_plus(k))
        li.setProperty('fanart_image',os.path.join(__cwd__,"fanart.jpg"))
        commands = []
        if os.path.isfile(k.replace(tipoExt,".info")):
            fo = open(k.replace(tipoExt,".info"),"r")
            lines = fo.read().split("|")
            fo.close()
            infoLabels = {}
            if len(lines)>=9:
                img = lines[0]
                fan = lines[1]
                infoLabels['rating'] = lines[2]
                infoLabels['votes'] = lines[3]
                infoLabels['plot'] = lines[4] + "\n[COLOR lime]Valoración: " + lines[2] + "  (" + lines[3] + " votos)[/COLOR]"
                infoLabels['genre'] = lines[5]
                #infoLabels['sorttitle'] = lines[6]
                infoLabels['originaltitle'] = lines[7] + " - (Esp: " + lines[6] + ")"
                infoLabels['year'] = lines[8]
                if len(lines) == 10:
                    infoLabels['tmdb_id'] = lines[9]
                else: infoLabels['tmdb_id'] = ""
                li.setProperty('fanart_image',fan)
                li.setArt({'thumb': img, 'poster': img, 'fanart': fan})
            li.setInfo("video", infoLabels)
            commands.append(( '[COLOR lime]Actualizar Información Extra[/COLOR]',  'XBMC.RunPlugin(plugin://plugin.video.torrentin/?funcion=catalogar_torrent&uri=%s)' % urllib.quote_plus(k) ))
            if xbmc.getCondVisibility('System.HasAddon(script.extendedinfo)'):
                commands.append(("[COLOR yellow]ExtendedInfo[/COLOR]","XBMC.RunScript(script.extendedinfo,info=extendedinfo,name=%s,id=%s)" % (lines[6],infoLabels['tmdb_id']) ))
        else:
            if tipoExt != ".dirctorio": commands.append(( '[COLOR lime]Buscar Información Extra[/COLOR]',  'XBMC.RunPlugin(plugin://plugin.video.torrentin/?funcion=catalogar_torrent&uri=%s)' % urllib.quote_plus(k) ))
        commands.append(( '[COLOR red]Borrar el '+tipoExt.strip('.')+'[/COLOR]',  'XBMC.RunPlugin(plugin://plugin.video.torrentin/?funcion=borrar_torrent&uri=file://%s&image=%s)' % (urllib.quote_plus(k),urllib.quote_plus(v)) ))
        commands.append(( '[COLOR yellow]Crear Directorio[/COLOR]',  'XBMC.RunPlugin(plugin://plugin.video.torrentin/?funcion=crear_dir&uri=%s)' % urllib.quote_plus(k) ))
        if tipoExt != ".dirctorio":
            commands.append(( '[COLOR orange]Mover '+tipoExt.strip('.')+' a Directorio[/COLOR]',  'XBMC.RunPlugin(plugin://plugin.video.torrentin/?funcion=mover_torrent&uri=file://%s&image=%s)' % (urllib.quote_plus(k),urllib.quote_plus(v)) ))
        li.addContextMenuItems(commands, replaceItems=True)
        xbmcplugin.addDirectoryItem(addon_handle, command, li, esdir)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.setContent(addon_handle, 'movies')
    xbmcplugin.endOfDirectory(addon_handle)

def browselocaltvp(uri="",player="",image=""):
    lista = torrents.browsear(2,uri)
    addon_handle = int(sys.argv[1])
    defimg=os.path.join( __cwd__ ,"resources","images","torrentlogo.png")
    for k,v in lista.iteritems():
        if not oswin: titulo = k.split("/")[-1]
        else: titulo = k.split("\\")[-1]
        if k.endswith(".magnet"):
            tipoExt=".magnet"
            esdir = False
            if v == "": li = xbmcgui.ListItem("[B][COLOR limegreen]"+titulo.replace(tipoExt,'')+"  [COLOR forestgreen][/B](m)[/COLOR]",defimg,defimg)
            else: li = xbmcgui.ListItem("[B][COLOR limegreen]"+titulo.replace(tipoExt,'')+"  [COLOR forestgreen][/B](m)[/COLOR]",v,v)
            f = open(k , "rb")
            magnet_data=f.read()
            f.close()
            command = '%s?funcion=principal&uri=%s&image=%s' % (sys.argv[0], urllib.quote_plus(magnet_data),urllib.quote_plus(v))
        elif k.endswith(".torrent"):
            tipoExt=".torrent"
            esdir = False
            if v == "": li = xbmcgui.ListItem("[B][COLOR limegreen]"+titulo.replace(tipoExt,'')+"  [COLOR forestgreen][/B](t)[/COLOR]",defimg,defimg)
            else: li = xbmcgui.ListItem("[B][COLOR limegreen]"+titulo.replace(tipoExt,'')+"  [COLOR forestgreen][/B](t)[/COLOR]",v,v)
            command = '%s?funcion=principal&uri=%s&image=%s' % (sys.argv[0], urllib.quote_plus("file://"+k),urllib.quote_plus(v))
        else:
            tipoExt=".dirctorio"
            esdir=True
            img=os.path.join( __cwd__ ,"resources","images","torrent.png")
            li = xbmcgui.ListItem("[B][COLOR yellow]"+titulo+"[/B][/COLOR]",img,img)
            command = '%s?funcion=browselocaltvp&uri=%s' % (sys.argv[0], urllib.quote_plus(k))
        li.setProperty('fanart_image',os.path.join(__cwd__,"fanart.jpg"))
        commands = []
        if os.path.isfile(k.replace(tipoExt,".info")):
            fo = open(k.replace(tipoExt,".info"),"r")
            lines = fo.read().split("|")
            fo.close()
            infoLabels = {}
            if len(lines)>=9:
                img = lines[0]
                fan = lines[1]
                infoLabels['rating'] = lines[2]
                infoLabels['votes'] = lines[3]
                infoLabels['plot'] = lines[4] + "\n[COLOR limegreen]Valoración: " + lines[2] + "  (" + lines[3] + " votos)[/COLOR]"
                infoLabels['genre'] = lines[5]
                #infoLabels['sorttitle'] = lines[6]
                infoLabels['originaltitle'] = lines[7] + " - (Esp: " + lines[6] + ")"
                infoLabels['year'] = lines[8]
                if len(lines) == 10:
                    infoLabels['tmdb_id'] = lines[9]
                else: infoLabels['tmdb_id'] = ""
                li.setProperty('fanart_image',fan)
                li.setArt({'thumb': img, 'poster': img, 'fanart': fan})
            li.setInfo("video", infoLabels)
            commands.append(( '[COLOR limegreen]Actualizar Información Extra[/COLOR]',  'XBMC.RunPlugin(plugin://plugin.video.torrentin/?funcion=catalogar_torrent&uri=%s)' % urllib.quote_plus(k) ))
            if xbmc.getCondVisibility('System.HasAddon(script.extendedinfo)'):
                commands.append(("[COLOR yellow]ExtendedInfo[/COLOR]","XBMC.RunScript(script.extendedinfo,info=extendedinfo,name=%s,id=%s)" % (lines[6],infoLabels['tmdb_id']) ))
        else:
            if tipoExt != ".dirctorio": commands.append(( '[COLOR limegreen]Buscar Información Extra[/COLOR]',  'XBMC.RunPlugin(plugin://plugin.video.torrentin/?funcion=catalogar_torrent&uri=%s)' % urllib.quote_plus(k) ))
        commands.append(( '[COLOR red]Borrar el '+tipoExt.strip('.')+'[/COLOR]',  'XBMC.RunPlugin(plugin://plugin.video.torrentin/?funcion=borrar_torrent&uri=file://%s&image=%s)' % (urllib.quote_plus(k),urllib.quote_plus(v)) ))
        commands.append(( '[COLOR yellow]Crear Directorio[/COLOR]',  'XBMC.RunPlugin(plugin://plugin.video.torrentin/?funcion=crear_dir&uri=%s)' % urllib.quote_plus(k) ))
        if tipoExt != ".dirctorio":
            commands.append(( '[COLOR orange]Mover '+tipoExt.strip('.')+' a Directorio[/COLOR]',  'XBMC.RunPlugin(plugin://plugin.video.torrentin/?funcion=mover_torrent&uri=file://%s&image=%s)' % (urllib.quote_plus(k),urllib.quote_plus(v)) ))
        li.addContextMenuItems(commands, replaceItems=True)
        xbmcplugin.addDirectoryItem(addon_handle, command, li, esdir)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.setContent(addon_handle, 'movies')
    xbmcplugin.endOfDirectory(addon_handle)

def crear_dir(uri="",player="",image=""):
    if not oswin: dir = uri.rsplit("/",1)[0]
    else: dir = uri.rsplit("\\",1)[0]
    keyboard = xbmc.Keyboard("","Crear directorio en: " + dir)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        newdir = keyboard.getText()
        if newdir=="": return
    try: os.mkdir(os.path.join(dir,newdir))
    except:
        mensaje('Error al crear el directorio', 3000)
        return
    xbmc.executebuiltin('Container.Refresh')

def addconfig(uri="",player="",image=""):
	tools.addconfig(__scriptid__,'plugin.video.felisalagarta')
	tools.addconfig(__scriptid__,__addon__.getSetting('forkname'))
	tools.addconfig(__scriptid__,__addon__.getSetting('forkname2'))

def catalogar_torrent(uri="",player="",image=""):
	if uri.startswith("magnet:"):
		xbmcgui.Dialog().ok("Torrentin","[COLOR orange]No se puede actualizar la información extra de los magnets desde el menú de reproductores, usa el menú contextual.[/COLOR]","[COLOR lime](Tecla C o picado mantenido en el listado).[/COLOR]")
		return
	if not oswin:
		torr_folder =uri.rsplit("/",1)[0]
		title = uri.rsplit("/",1)[1].rsplit(".",1)[0]
	else:
		torr_folder = uri.rsplit("\\",1)[0]
		title = uri.rsplit("\\",1)[1].rsplit(".",1)[0]
	global savetit
	global busca
	savetit=title
	busca=''
	if re.search("\d{1,2}[x]\d{2}",title) or re.search("Cap.\d+",title) or re.search("S\d{2}E\d{2}",title):
		poster,fanart,infoLabels=MetaTorrent(title,"tv",1)
	else: poster,fanart,infoLabels=MetaTorrent(title,"movie",1) 
	if poster != "" and fanart != "" and infoLabels != "":
		try:
			file = open(os.path.join(torr_folder,title + ".info"),"wb")
			file.write(poster + "|" + fanart + "|" + infoLabels['rating'] + "|" + infoLabels['votes'] + "|" + infoLabels['plot'] + "|" + infoLabels['genre'] + "|" + infoLabels['title'] + "|" + infoLabels['originaltitle'] + "|" + infoLabels['year'] + "|" + infoLabels['tmdb_id'] )
			file.close()
		except: pass
	xbmc.executebuiltin('Container.Refresh')

def show_Msg(heading, message, time = 6000, pic = os.path.join(__cwd__ , "icon.png")):
    if __addon__.getSetting('nosound') == "true":
        try: xbmcgui.Dialog().notification(heading, message, pic, time, 0)
        except: pass
    else:
        try: xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "%s")' % (heading, message, time, pic))
        except:
            try: xbmcgui.Dialog().notification(heading, message, pic, time, 0)
            except: pass

def mensaje(mensaje,time):
    show_Msg('  ---===[ Torrentin ]===---',mensaje,time)

def principal(uri,player,image):
    torrent_folder=__addon__.getSetting('torrent_path')
    destino = os.path.join( torrent_folder , "torrentin.torrent" )
    bajado = False
    listitem = xbmcgui.ListItem(label="Torrentin", iconImage="", thumbnailImage="", path=str(sys.argv))
    xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)
    if int(xbmc.getInfoLabel("System.BuildVersion" )[0:2]) >= 13:
        if uri:
            if uri.startswith("http://") or uri.startswith("https://"):
                guarda = torrents.dltorrent(uri,player,image)
                if guarda:
                    uri = "file://"+destino
                    bajado = True
                else:
                    return
            elif uri.startswith("magnet:"): copymagnet(uri,image)
            if player == 0:
                if xbmcgui.Dialog().yesno("Torrentin" , torrents.torrent_info(uri , 0),"¿ Reproducir ?"): player = menu
                else: return
            if (oswin and player >=12): player = askplayer(uri,player,image)
            elif (not oswin and player==menu): player = askplayer(uri,player,image)
            if player == menu: return
            if bajado:
                applaunch(uri,player,image)
                return
            elif uri.startswith("file://"): playfile(uri,player,image)
            elif uri.startswith("magnet:"): playmagnet(uri,player,image)
            elif uri.startswith("acestream://"): playace(uri,player,image)
            else: mensaje('Enlace no valido', 3000)
        else: mensaje('Ningun enlace a reproducir', 3000)
    else: xbmcgui.Dialog().ok("Torrentin" , "Este Add-On no funciona en versiones Frodo","Actualiza tu XBMC....")

def primer(uri,player,image):
    if uri:
        principal(uri,player,image)
        return
    torrent_folder=__addon__.getSetting('torrent_path')
    destino = os.path.join( torrent_folder , "torrentin.torrent" )
    destinomag = os.path.join( torrent_folder , "torrentin.magnet" )
    fanartimage = os.path.join(__cwd__,"fanart.jpg")
    addon_handle = int(sys.argv[1])
    shortforkname = __addon__.getSetting('forkname').split('.')
    if len(shortforkname)==3: forkname=shortforkname[2]
    else: forkname=''
    shortforkname2 = __addon__.getSetting('forkname2').split('.')
    if len(shortforkname2)==3: forkname2=shortforkname2[2]
    else: forkname2=''

    if xbmc.getCondVisibility('System.HasAddon("plugin.video.felisalagarta")'):
        img=xbmc.translatePath(os.path.join('special://home', 'addons', 'plugin.video.felisalagarta','icon.png'))
        li = xbmcgui.ListItem("[B][COLOR khaki]Ir a canales torrent de felisalagarta[/COLOR][/B]",img,img)
        command = 'plugin://plugin.video.felisalagarta/?action=filterchannels&category=torrent&channel=channelselector&channel_type=torrent'
        li.setProperty('fanart_image',fanartimage)
        xbmcplugin.addDirectoryItem(addon_handle, command, li, True)        
    
    if xbmc.getCondVisibility('System.HasAddon("' + __addon__.getSetting('forkname') + '")') and tools.chkpchaddon(__addon__.getSetting('forkname')) == 1 and tools.ispelisfork(forkname):
    #if xbmc.getCondVisibility('System.HasAddon("' + __addon__.getSetting('forkname') + '")') and tools.ispelisfork(forkname):
        img=xbmc.translatePath(os.path.join('special://home', 'addons', __addon__.getSetting('forkname'),'icon.png'))
        li = xbmcgui.ListItem("[B][COLOR khaki]Ir a canales torrent de "+forkname+"[/COLOR][/B]",img,img)
        command = 'plugin://' + __addon__.getSetting('forkname') + '/?action=filterchannels&category=torrent&channel=channelselector&channel_type=torrent'
        li.setProperty('fanart_image',fanartimage)
        xbmcplugin.addDirectoryItem(addon_handle, command, li, True)        
    
    if xbmc.getCondVisibility('System.HasAddon("' + __addon__.getSetting('forkname2') + '")') and tools.chkpchaddon(__addon__.getSetting('forkname2')) == 1 and tools.ispelisfork(forkname2):
    #if xbmc.getCondVisibility('System.HasAddon("' + __addon__.getSetting('forkname2') + '")') and tools.ispelisfork(forkname2):
        img=xbmc.translatePath(os.path.join('special://home', 'addons', __addon__.getSetting('forkname2'),'icon.png'))
        li = xbmcgui.ListItem("[B][COLOR khaki]Ir a canales torrent de "+forkname2+"[/COLOR][/B]",img,img)
        command = 'plugin://' + __addon__.getSetting('forkname2') + '/?action=filterchannels&category=torrent&channel=channelselector&channel_type=torrent'
        li.setProperty('fanart_image',fanartimage)
        xbmcplugin.addDirectoryItem(addon_handle, command, li, True)        
    
    lst = tools.chklst()
    if len(lst) >=1:
        img=os.path.join( __cwd__ ,"resources","images","m3u.png")
        li = xbmcgui.ListItem("[B][COLOR orange]Listas AceLive M3U[/COLOR][/B]",img,img)
        command = '%s?funcion=lst&%s' % (sys.argv[0], sys.argv[2])
        li.setProperty('fanart_image',fanartimage)
        xbmcplugin.addDirectoryItem(addon_handle, command, li, True)

    if os.path.isfile (destino):
        img=os.path.join( __cwd__ ,"resources","images","torrentlogo.png")  # torrentin.png
        if os.path.isfile(os.path.join( torrent_folder , "torrentin.torrent.img")):
            f = open(os.path.join( torrent_folder , "torrentin.torrent.img") , "rb")
            img=f.read()
            f.close()
        li = xbmcgui.ListItem("[B][COLOR greenyellow]Reproducir último torrent[/COLOR][/B]",img,img)
        command = '%s?funcion=principal&uri=file://%s&image=%s' % (sys.argv[0], urllib.quote_plus(destino),urllib.quote_plus(img))
        li.setProperty('fanart_image',fanartimage)
        xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

    if os.path.isfile (destinomag):
        f = open(destinomag , "rb")
        magnet_data=f.read()
        f.close()
        img=os.path.join( __cwd__ ,"resources","images","magnetlogo.png")
        if os.path.isfile(os.path.join( torrent_folder , "torrentin.magnet.img")):
            f = open(os.path.join( torrent_folder , "torrentin.magnet.img") , "rb")
            img=f.read()
            f.close()
        li = xbmcgui.ListItem("[B][COLOR greenyellow]Reproducir último magnet[/COLOR][/B]",img,img)
        command = '%s?funcion=principal&uri=%s&image=%s' % (sys.argv[0], urllib.quote_plus(magnet_data),urllib.quote_plus(img))
        li.setProperty('fanart_image',fanartimage)
        xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

    img=os.path.join( __cwd__ ,"resources","images","torrentloader.png")
    li = xbmcgui.ListItem("[B][COLOR greenyellow]Reproducir un torrent local[/COLOR][/B]",img,img)
    command = '%s?funcion=cargarlocal&%s' % (sys.argv[0], sys.argv[2])
    li.setProperty('fanart_image',fanartimage)
    xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

    img=os.path.join( __cwd__ ,"resources","images","torrentfolder.png")
    li = xbmcgui.ListItem("[B][COLOR lime]Torrents (Principal)[/COLOR][/B]",img,img)
    command = '%s?funcion=browselocal&%s' % (sys.argv[0], sys.argv[2])
    li.setProperty('fanart_image',fanartimage)
    xbmcplugin.addDirectoryItem(addon_handle, command, li, True)

    if __addon__.getSetting('torrent_path_tvp') !="":
        img=os.path.join( __cwd__ ,"resources","images","torrent.png")	
        li = xbmcgui.ListItem("[B][COLOR limegreen]Torrents (Secundario)[/COLOR][/B]",img,img)
        command = '%s?funcion=browselocaltvp&%s' % (sys.argv[0], sys.argv[2])
        li.setProperty('fanart_image',fanartimage)
        xbmcplugin.addDirectoryItem(addon_handle, command, li, True)
    
    if __addon__.getSetting('pelis_path') != "":
        img=os.path.join( __cwd__ ,"resources","images","film-reels.png")	
        li = xbmcgui.ListItem("[B][COLOR yellowgreen]Películas[/COLOR][/B]",img,img)
        command = __addon__.getSetting('pelis_path')
        li.setProperty('fanart_image',fanartimage)
        xbmcplugin.addDirectoryItem(addon_handle, command, li, True)
 
    if __addon__.getSetting('ren_path5') != "":
        img=os.path.join( __cwd__ ,"resources","images","databasemovie.png")	
        li = xbmcgui.ListItem("[B][COLOR chartreuse]Películas (Renombradas)[/COLOR][/B]",img,img)
        if __addon__.getSetting("scraper") == "0": command = '%s?funcion=browselocalpelis&uri=%s&' % (sys.argv[0], urllib.quote_plus(__addon__.getSetting('ren_path5')) )
        else: command = __addon__.getSetting('ren_path5')
        li.setProperty('fanart_image',fanartimage)
        xbmcplugin.addDirectoryItem(addon_handle, command, li, True)

    img=os.path.join( __cwd__ ,"resources","images","tools.png")	
    li = xbmcgui.ListItem("[B][COLOR firebrick]Utilidades[/COLOR][/B]",img,img)
    command = '%s?funcion=submenu&%s' % (sys.argv[0], sys.argv[2])
    li.setProperty('fanart_image',fanartimage)
    xbmcplugin.addDirectoryItem(addon_handle, command, li, True)
    
    img=os.path.join( __cwd__ ,"resources","images","settings3d.png")
    li = xbmcgui.ListItem("[B][COLOR deepskyblue]Configuración[/COLOR][/B]",img,img)
    command = '%s?funcion=settings&%s' % (sys.argv[0], sys.argv[2])
    li.setProperty('fanart_image',fanartimage)
    li.addContextMenuItems([], replaceItems=True)
    xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

    xbmcplugin.endOfDirectory(addon_handle)

    autoparcheo = threading.Thread(target=autoparche())
    autoparcheo.setDaemon(True)
    autoparcheo.start()
 
def submenu(uri="",player="",image=""):
    fanartimage = os.path.join(__cwd__,"fanart.jpg")
    addon_handle = int(sys.argv[1])

    img=os.path.join( __cwd__ ,"resources","images","interact.png")
    li = xbmcgui.ListItem("[B][COLOR lime]Buscar actualizaciones del Torrentin[/COLOR][/B]",img,img)
    command = '%s?funcion=chkupdate&uri=%s' % (sys.argv[0], sys.argv[2])
    li.setProperty('fanart_image',fanartimage)
    xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

    img=os.path.join( __cwd__ ,"resources","images","setting.png")
    li = xbmcgui.ListItem("[B][COLOR lime]Auto-seleccionar los addons a mostrar en el menú[/COLOR][/B]",img,img)
    command = '%s?funcion=autoconf&uri=%s' % (sys.argv[0], sys.argv[2])
    li.setProperty('fanart_image',fanartimage)
    xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

    if xbmc.getCondVisibility('system.platform.Android'):
        img=os.path.join( __cwd__ ,"resources","images","iconrar.png")
        li = xbmcgui.ListItem("[B][COLOR lime]Ejecutar RAR (rarlab)[/COLOR][/B]",img,img)
        command = '%s?funcion=exerar&uri=%s' % (sys.argv[0], sys.argv[2])
        li.setProperty('fanart_image',fanartimage)
        xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

    img=os.path.join( __cwd__ ,"resources","images","filmrename.png")
    li = xbmcgui.ListItem("[B][COLOR chartreuse]Renombrador de películas [COLOR yellow]cambia a: Título de la película (año)[/COLOR][/B]",img,img)
    command = '%s?funcion=renombrador5&uri=%s' % (sys.argv[0], sys.argv[2])
    li.setProperty('fanart_image',fanartimage)
    xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

    img=os.path.join( __cwd__ ,"resources","images","filetools.png")
    li = xbmcgui.ListItem("[B][COLOR yellow]Utilidades de archivos[/COLOR][/B]",img,img)
    command = '%s?funcion=menurenombradores&uri=%s' % (sys.argv[0], sys.argv[2])
    li.setProperty('fanart_image',fanartimage)
    xbmcplugin.addDirectoryItem(addon_handle, command, li, True)

    img=os.path.join( __cwd__ ,"resources","images","parches.png")
    li = xbmcgui.ListItem("[B][COLOR yellow]Parches para otros AddOns[/COLOR][/B]",img,img)
    command = '%s?funcion=menuparches&uri=%s' % (sys.argv[0], sys.argv[2])
    li.setProperty('fanart_image',fanartimage)
    xbmcplugin.addDirectoryItem(addon_handle, command, li, True)

    img=os.path.join( __cwd__ ,"resources","images","kodi.png")
    li = xbmcgui.ListItem("[B][COLOR yellow]Mantenimiento de Kodi[/COLOR][/B]",img,img)
    command = '%s?funcion=menumantenimiento&uri=%s' % (sys.argv[0], sys.argv[2])
    li.setProperty('fanart_image',fanartimage)
    xbmcplugin.addDirectoryItem(addon_handle, command, li, True)

    img=os.path.join( __cwd__ ,"resources","images","configmorado.png")
    li = xbmcgui.ListItem("[B][COLOR deepskyblue]Configurar directorios y opciones (pestaña Utilidades)[/COLOR][/B]",img,img)
    command = '%s?funcion=settings&uri=%s' % (sys.argv[0], sys.argv[2])
    li.setProperty('fanart_image',fanartimage)
    xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

    xbmcplugin.endOfDirectory(addon_handle)

def menuparches(uri="",player="",image=""):
    fanartimage = os.path.join(__cwd__,"fanart.jpg")
    addon_handle = int(sys.argv[1])
    shortforkname = __addon__.getSetting('forkname').split('.')
    if len(shortforkname)==3: forkname=shortforkname[2]
    else: forkname=''
    shortforkname2 = __addon__.getSetting('forkname2').split('.')
    if len(shortforkname2)==3: forkname2=shortforkname2[2]
    else: forkname2=''

    if tools.chkpchaddon(__addon__.getSetting('forkname')) == 0:
        if tools.ispelisfork(forkname) and xbmc.getCondVisibility('System.HasAddon("'+__addon__.getSetting('forkname')+'")'):
            img=os.path.join( __cwd__ ,"resources","images","tirita.png")
            li = xbmcgui.ListItem("[B][COLOR orange]Parchear "+forkname+" para auto-reproducir con Torrentin (Automático)[/COLOR][/B]",img,img)
            command = '%s?funcion=pchaddon&uri=%s' % (sys.argv[0], __addon__.getSetting('forkname'))
            li.setProperty('fanart_image',fanartimage)
            xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

            img=os.path.join( __cwd__ ,"resources","images","tirita.png")
            li = xbmcgui.ListItem("[B][COLOR orange]Parchear "+forkname+" para obtener las carátulas (No automático)[/COLOR][/B]",img,img)
            command = '%s?funcion=pchaddon2&uri=%s' % (sys.argv[0], __addon__.getSetting('forkname'))
            li.setProperty('fanart_image',fanartimage)
            xbmcplugin.addDirectoryItem(addon_handle, command, li, False)
    else: 
        if xbmc.getCondVisibility('System.HasAddon("'+__addon__.getSetting('forkname')+'")'):
            img=os.path.join( __cwd__ ,"resources","images","tirita.png")
            li = xbmcgui.ListItem("[B][COLOR orange]Des-Parchear "+forkname+"[/COLOR][/B]",img,img)
            command = '%s?funcion=pchaddon&uri=%s' % (sys.argv[0], __addon__.getSetting('forkname'))
            li.setProperty('fanart_image',fanartimage)
            xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

    if tools.chkpchaddon(__addon__.getSetting('forkname2')) == 0:
        if tools.ispelisfork(forkname2) and xbmc.getCondVisibility('System.HasAddon("'+__addon__.getSetting('forkname2')+'")'):
            img=os.path.join( __cwd__ ,"resources","images","tirita.png")
            li = xbmcgui.ListItem("[B][COLOR orange]Parchear "+forkname2+" para auto-reproducir con Torrentin (Automático)[/COLOR][/B]",img,img)
            command = '%s?funcion=pchaddon&uri=%s' % (sys.argv[0], __addon__.getSetting('forkname2'))
            li.setProperty('fanart_image',fanartimage)
            xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

            img=os.path.join( __cwd__ ,"resources","images","tirita.png")
            li = xbmcgui.ListItem("[B][COLOR orange]Parchear "+forkname2+" para obtener las carátulas (No automático)[/COLOR][/B]",img,img)
            command = '%s?funcion=pchaddon2&uri=%s' % (sys.argv[0], __addon__.getSetting('forkname2'))
            li.setProperty('fanart_image',fanartimage)
            xbmcplugin.addDirectoryItem(addon_handle, command, li, False)
    else: 
        if xbmc.getCondVisibility('System.HasAddon("'+__addon__.getSetting('forkname2')+'")'):
            img=os.path.join( __cwd__ ,"resources","images","tirita.png")
            li = xbmcgui.ListItem("[B][COLOR orange]Des-Parchear "+forkname2+"[/COLOR][/B]",img,img)
            command = '%s?funcion=pchaddon&uri=%s' % (sys.argv[0], __addon__.getSetting('forkname2'))
            li.setProperty('fanart_image',fanartimage)
            xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

    if xbmc.getCondVisibility('System.HasAddon("plugin.video.plexus-streams")'):
        if tools.chkps() == 0:
            img=os.path.join( __cwd__ ,"resources","images","tirita.png")
            li = xbmcgui.ListItem("[B][COLOR orange]Parchear plexus-streams para poder reproducir con Torrentin[/COLOR][/B]",img,img)
            command = '%s?funcion=pchplexusstreams&uri=%s' % (sys.argv[0], sys.argv[2])
            li.setProperty('fanart_image',fanartimage)
            xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

    if xbmc.getCondVisibility('System.HasAddon("program.plexus")'):
        if not tools.chkpchplexus():
            img=os.path.join( __cwd__ ,"resources","images","tirita.png")
            li = xbmcgui.ListItem("[B][COLOR orange]Parchear plexus (0.1.4, 0.1.6a y 0.1.7) para poder poder reproducir con Torrentin[/COLOR][/B]",img,img)
            command = '%s?funcion=pchplexus&uri=%s' % (sys.argv[0], sys.argv[2])
            li.setProperty('fanart_image',fanartimage)
            xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

    if xbmc.getCondVisibility('System.HasAddon("plugin.video.kmediatorrent")'):
        if not tools.chkpchkmedia():
            img=os.path.join( __cwd__ ,"resources","images","tirita.png")
            li = xbmcgui.ListItem("[B][COLOR orange]Parchear KmediaTorrent (2.3.7) para poner caché en FAT32 y completar .avi antes de reproducirlos[/COLOR][/B]",img,img)
            command = '%s?funcion=pchkmedia&uri=%s' % (sys.argv[0], sys.argv[2])
            li.setProperty('fanart_image',fanartimage)
            xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

    xbmcplugin.endOfDirectory(addon_handle)

def menurenombradores(uri="",player="",image=""):
    fanartimage = os.path.join(__cwd__,"fanart.jpg")
    addon_handle = int(sys.argv[1])
    '''
    img=os.path.join( __cwd__ ,"resources","images","filmrename.png")
    li = xbmcgui.ListItem("[B][COLOR chartreuse]Renombrador de películas [COLOR yellow]cambia a: Título de la película (año)[/COLOR][/B]",img,img)
    command = '%s?funcion=renombrador5&uri=%s' % (sys.argv[0], sys.argv[2])
    li.setProperty('fanart_image',fanartimage)
    xbmcplugin.addDirectoryItem(addon_handle, command, li, False)
    '''
    img=os.path.join( __cwd__ ,"resources","images","move.png")
    li = xbmcgui.ListItem("[B][COLOR khaki]Movedor de archivos [COLOR yellow]mueve archivos de un directorio a otro[/COLOR][/B]",img,img)
    command = '%s?funcion=movedor&uri=%s' % (sys.argv[0], sys.argv[2])
    li.setProperty('fanart_image',fanartimage)
    xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

    img=os.path.join( __cwd__ ,"resources","images","rename.png")
    li = xbmcgui.ListItem("[B][COLOR sandybrown]Renombrador de archivos [COLOR yellow]cambia ( ) por [ ][/COLOR][/B]",img,img)
    command = '%s?funcion=renombrador1&uri=%s' % (sys.argv[0], sys.argv[2])
    li.setProperty('fanart_image',fanartimage)
    xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

    img=os.path.join( __cwd__ ,"resources","images","rename.png")
    li = xbmcgui.ListItem("[B][COLOR sandybrown]Renombrador de archivos [COLOR yellow]elimina cadenas de texto[/COLOR][/B]",img,img)
    command = '%s?funcion=renombrador2&uri=%s' % (sys.argv[0], sys.argv[2])
    li.setProperty('fanart_image',fanartimage)
    xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

    img=os.path.join( __cwd__ ,"resources","images","rename.png")
    li = xbmcgui.ListItem("[B][COLOR sandybrown]Renombrador de archivos [COLOR yellow]cambia . y _ por espacio en el nombre[/COLOR][/B]",img,img)
    command = '%s?funcion=renombrador3&uri=%s' % (sys.argv[0], sys.argv[2])
    li.setProperty('fanart_image',fanartimage)
    xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

    img=os.path.join( __cwd__ ,"resources","images","rename.png")
    li = xbmcgui.ListItem("[B][COLOR sandybrown]Renombrador de archivos [COLOR yellow]quita [ ] y ( ) y lo de dentro[/COLOR][/B]",img,img)
    command = '%s?funcion=renombrador4&uri=%s' % (sys.argv[0], sys.argv[2])
    li.setProperty('fanart_image',fanartimage)
    xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

    img=os.path.join( __cwd__ ,"resources","images","configmorado.png")
    li = xbmcgui.ListItem("[B][COLOR deepskyblue]Configurar directorios y opciones (pestaña Utilidades)[/COLOR][/B]",img,img)
    command = '%s?funcion=settings&uri=%s' % (sys.argv[0], sys.argv[2])
    li.setProperty('fanart_image',fanartimage)
    xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

    xbmcplugin.endOfDirectory(addon_handle)

def menumantenimiento(uri="",player="",image=""):
    fanartimage = os.path.join(__cwd__,"fanart.jpg")
    addon_handle = int(sys.argv[1])
    img=os.path.join( __cwd__ ,"resources","images","clean.png")
    li = xbmcgui.ListItem("[B][COLOR orange]Limpieza de cachés de imágenes, addons y temporales de Kodi[/COLOR][/B]",img,img)
    command = '%s?funcion=cleankodi&uri=%s' % (sys.argv[0], sys.argv[2])
    li.setProperty('fanart_image',fanartimage)
    xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

    img=os.path.join( __cwd__ ,"resources","images","backuprestore.png")
    li = xbmcgui.ListItem("[B][COLOR lime]Hacer una copia de seguridad completa de Kodi[/COLOR][/B]",img,img)
    command = '%s?funcion=bkpkodi&uri=%s' % (sys.argv[0], sys.argv[2])
    li.setProperty('fanart_image',fanartimage)
    xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

    img=os.path.join( __cwd__ ,"resources","images","backuprestore.png")
    li = xbmcgui.ListItem("[B][COLOR lime]Restaurar una copia de seguridad completa de Kodi[/COLOR][/B]",img,img)
    command = '%s?funcion=restkodi&uri=%s' % (sys.argv[0], sys.argv[2])
    li.setProperty('fanart_image',fanartimage)
    xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

    img=os.path.join( __cwd__ ,"resources","images","configmorado.png")
    li = xbmcgui.ListItem("[B][COLOR deepskyblue]Configurar directorios y opciones (pestaña Utilidades)[/COLOR][/B]",img,img)
    command = '%s?funcion=settings&uri=%s' % (sys.argv[0], sys.argv[2])
    li.setProperty('fanart_image',fanartimage)
    xbmcplugin.addDirectoryItem(addon_handle, command, li, False)

    xbmcplugin.endOfDirectory(addon_handle)

def browselocalpelis(uri="",player="",image=""):
	generos = {28:"Acción",12:"Aventura",16:"Animación",35:"Comedia",80:"Crimen",99:"Documental",18:"Drama",10751:"Familia",14:"Fantasía",36:"Historia",27:"Terror",10402:"Música",9648:"Misterio",10749:"Romance",878:"Ciencia ficción",10770:"Película de la televisión",53:"Suspense",10752:"Guerra",37:"Western"}
	torrentindb = xbmc.translatePath(os.path.join('special://home','userdata','addon_data',__scriptid__,'renombradas'))
	if not os.path.isdir(torrentindb): os.mkdir(torrentindb)
	list_folder=uri
	if list_folder =="": 
		if xbmcgui.Dialog().yesno( "Torrentin", "[COLOR yellow]Esta opción del menú usa el directorio del  [COLOR dodgerblue]Renombrador de películas[COLOR yellow]  y no está configurado, además ignora las que no estén correctamente renombradas.[/COLOR]","[COLOR lime]¿Configurar directorio? (pestaña Utilidades)[/COLOR]"):
			__addon__.openSettings()
		return
	if not os.path.isdir(list_folder):
		mensaje("No se puede acceder al directorio.",2000)
		return
	addon_handle = int(sys.argv[1])
	xbmcplugin.setContent(addon_handle, 'movies')
	dirList=os.listdir( list_folder )
	result=0
	start = time.time()
	for fname in dirList:
		if os.path.isdir(os.path.join( list_folder , fname )):
			if __addon__.getSetting('incsubdir') == "true":
				li = xbmcgui.ListItem("[COLOR yellow][B]" + fname + "[/COLOR][/B]", iconImage="DefaultFolder.png", thumbnailImage="DefaultFolder.png")
				command = '%s?funcion=browselocalpelis&uri=%s&' % (sys.argv[0], urllib.quote_plus(os.path.join( list_folder , fname )) )
				li.setProperty('fanart_image',os.path.join(__cwd__,"fanart.jpg"))
				xbmcplugin.addDirectoryItem(addon_handle, command, li, True)
				continue
			else: continue
		infoLabels = {}
		nombre = fname.rsplit(".",1)[0]
		ext = fname.rsplit(".",1)[1]
		if re.search( '\(\d{4}\)', nombre[-6:]):
			yearfromtitle=nombre[-5:].replace(')','')
			title = nombre[:-6].replace("[Screener]","").strip()
		else: continue
		if not ext.lower() in ['avi','mp4','mkv','flv','mov','vob','wmv','ogm','asx','mpg','mpeg','avc','vp3','fli','flc','m4v','iso','divx']: continue
		if os.path.isfile(os.path.join(torrentindb,fname+".info")):
			img,fanartimage,infoLabels = checkpeli(fname)
		else:
			result = result +1
			if result == 38:
				while time.time()-start < 10:
					time.sleep(2)
				result=0
				start = time.time()
			try:
				data = torrents.url_get("http://api.themoviedb.org/3/search/movie?api_key=cc4b67c52acb514bdf4931f7cedfd12b&query=" + title.replace(" ","%20") + "&year=" + yearfromtitle  + "&language=es&include_adult=false")
			except:
				try:
					time.sleep(1)
					data = torrents.url_get("http://api.themoviedb.org/3/search/movie?api_key=cc4b67c52acb514bdf4931f7cedfd12b&query=" + title.replace(" ","%20") + "&year=" + yearfromtitle  + "&language=es&include_adult=false")
				except:
					mensaje(title + " Error al obtener info en TMDb",3000)
					continue
			if data == "":
				mensaje(title + " Error, no hay datos de TMDb",3000)
				continue
			datadict = json.loads(data)
			if datadict['total_results'] != 0:
				for s in datadict['results']:
					titul = s['title'].encode('utf-8').replace(":",",").replace("*","").replace("?","¿").replace("<","[").replace(">","]").replace('"',"'").replace("/","").replace("\\","").replace("|","")
					if datadict['total_results'] > 1 and not titul.strip() in title.strip(): continue
					infoLabels = {}
					if s['poster_path']: img = "https://image.tmdb.org/t/p/original" +  s['poster_path'].encode('utf-8')
					else: img  = os.path.join(__cwd__ , "icon.png")
					if s['backdrop_path']: fanartimage = "https://image.tmdb.org/t/p/original" +  s['backdrop_path'].encode('utf-8')
					else: fanartimage = os.path.join(__cwd__,"fanart.jpg")
					if s['vote_average']: infoLabels['rating'] = str(s['vote_average'])
					else: infoLabels['rating'] = "0"
					if s['vote_count']: infoLabels['votes'] = str(s['vote_count'])
					else: infoLabels['votes'] = "0"
					if s['overview']: infoLabels['plot'] = s['overview'].encode('utf-8') + "\n[COLOR cyan]Valoración: " + infoLabels['rating'] + "  (" + infoLabels['votes'] + " votos)\n[COLOR chartreuse]Video: " + ext + "[/COLOR]"
					else: infoLabels['plot'] = 'No hay sinopsis.' + "\n[COLOR cyan]Valoración: " + infoLabels['rating'] + "  (" + infoLabels['votes'] + " votos)[/COLOR]"
					infoLabels['sorttitle'] = title
					if s['original_title']: infoLabels['originaltitle'] = s['original_title'].encode('utf-8')
					infoLabels['year'] = yearfromtitle
					if s['genre_ids']:
						listageneros = json.loads(str(s['genre_ids']))
						genero = ""
						for g in listageneros:
							try: genero += generos.get(g) + " - "
							except: pass
						infoLabels['genre'] = genero.strip(" - ")
					else: infoLabels['genre'] = "Género no definido"
					if s['id']: infoLabels['tmdb_id'] = str(s['id'])
					else: infoLabels['tmdb_id'] = ""
			else:
				img,fanartimage,infoLabels = notfound(fname)
			if len(infoLabels) != 0:
				addpeli(fname,img,fanartimage,infoLabels)
			else:
				img,fanartimage,infoLabels = notfound(fname)
		li = xbmcgui.ListItem("[COLOR chartreuse][B]" + nombre + "  [COLOR cyan][" + infoLabels['rating'] + "][/COLOR][/B]", iconImage=img, thumbnailImage=img)
		moviefile = os.path.join( list_folder , fname )
		li.setProperty('fanart_image',fanartimage)
		li.setInfo("video", infoLabels)
		#li.setIconImage(img) #for isengard
		li.setArt({'thumb': img, 'poster': img, 'fanart': fanartimage})
		li.setProperty('Video', 'true')
		li.setProperty('IsPlayable', 'true')
		commands = []
		commands.append(( '[B][COLOR chartreuse]Actualizar información extra[/COLOR][/B]',  'XBMC.RunPlugin(plugin://plugin.video.torrentin/?funcion=recatalogar_peli&uri=%s)' % urllib.quote_plus(fname) ))
		commands.append(( '[B][COLOR red]Actualizar info. de todas[/COLOR][/B]',  'XBMC.RunPlugin(plugin://plugin.video.torrentin/?funcion=recatalogar_todas)' ))
		if xbmc.getCondVisibility('System.HasAddon(script.extendedinfo)'):
			commands.append(("[B][COLOR yellow]ExtendedInfo[/COLOR][/B]","XBMC.RunScript(script.extendedinfo,info=extendedinfo,name=%s,id=%s)" % (title,infoLabels['tmdb_id']) ))
		li.addContextMenuItems(commands, replaceItems=True)
		xbmcplugin.addDirectoryItem(addon_handle, moviefile, li, False)
	xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL)
	xbmcplugin.setContent(addon_handle, 'movies')
	xbmcplugin.endOfDirectory(addon_handle)

def notfound(name):
	infoLabels = {}
	img=os.path.join(__cwd__ , "icon.png")
	fanartimage=os.path.join(__cwd__,"fanart.jpg")
	infoLabels['rating']  = "0"
	infoLabels['votes'] = "0"
	infoLabels['plot'] = "No se ha encontrado la película " + name + " en TMDb.\n\nProbablemente la hayan renombrado en TMDb después de renombrar el archivo.\n\nIntenta renombrarla de nuevo (borrando un digito del año en el nombre del archivo y repitiendo el proceso del Renombrador de películas)."
	infoLabels['genre'] = " "
	infoLabels['sorttitle'] = ""
	infoLabels['originaltitle'] = ""
	infoLabels['year'] = ""
	infoLabels['tmdb_id'] = ""
	return img,fanartimage,infoLabels

def checkpeli(name):
	fo = open(xbmc.translatePath(os.path.join('special://home','userdata','addon_data',__scriptid__,'renombradas',name+".info")),"r")
	lines = fo.read().split("|")
	fo.close()
	if len(lines) >= 9:
		infoLabels = {}
		img = lines[0]
		fan= lines[1]
		infoLabels['rating'] = lines[2]
		infoLabels['votes'] = lines[3]
		#infoLabels['plot'] = lines[4]
		infoLabels['plot'] = lines[4]
		infoLabels['genre'] = lines[5]
		#infoLabels['sorttitle'] = lines[6]
		infoLabels['originaltitle'] = lines[7] + " - (Esp: " + lines[6] + ")"
		infoLabels['year'] = lines[8]
		if len(lines) == 10:
			infoLabels['tmdb_id'] = lines[9]
		else: infoLabels['tmdb_id'] = ""
		return img,fan,infoLabels
	else: return '','',''
	
def addpeli(name,poster,fanart,infoLabels):
	basedir = xbmc.translatePath(os.path.join('special://home','userdata','addon_data',__scriptid__,'renombradas'))
	file = open(os.path.join(basedir,name + ".info"),"w")
	file.write(poster + "|" + fanart + "|" + infoLabels['rating'] + "|" + infoLabels['votes'] + "|" + infoLabels['plot'] + "|" + infoLabels['genre'] + "|" + infoLabels['sorttitle'] + "|" + infoLabels['originaltitle'] + "|" + infoLabels['year'] + "|" + infoLabels['tmdb_id'])
	file.close()

def cleandb():
	basedir = xbmc.translatePath(os.path.join('special://home','userdata','addon_data',__scriptid__,'renombradas'))
	list_folder=__addon__.getSetting('ren_path5')
	if not os.path.isdir(basedir): return
	if not os.path.isdir(list_folder): return
	dirList=os.listdir(basedir)
	for fname in dirList:
		if not os.path.isfile(os.path.join(list_folder,fname.rsplit(".",1)[0])):
			try: os.remove(os.path.join(basedir,fname))
			except: pass
	mensaje("Base de datos limpiada.",2000)

def recatalogar_peli(uri="",player="",image=""):
	if os.path.isfile(xbmc.translatePath(os.path.join('special://home','userdata','addon_data',__scriptid__,'renombradas',uri+".info")) ):
		os.remove(xbmc.translatePath(os.path.join('special://home','userdata','addon_data',__scriptid__,'renombradas',uri+".info")) )
	xbmc.executebuiltin('Container.Refresh')

def recatalogar_todas(uri="",player="",image=""):
	if not xbmcgui.Dialog().yesno("Torrentin - scraper","[COLOR chartreuse]Actualizar información extra de todas las peliculas renombradas.[/COLOR]" , "[COLOR orange]Se borrará la base de datos y se buscarán todas en TMDB.[/COLOR]" ,"[COLOR red]¡ ATENCION !, Esto puede tardar bastante si hay muchas.[/COLOR]","Abandonar","Continuar"):
		return
	basedir = xbmc.translatePath(os.path.join('special://home','userdata','addon_data',__scriptid__,'renombradas'))
	dirList=os.listdir(basedir)
	for fname in dirList:
		try: os.remove(os.path.join(basedir,fname))
		except: pass
	xbmc.executebuiltin('Container.Refresh')

def exerar(uri="",player="",image=""):
    xbmc.executebuiltin('XBMC.StartAndroidActivity("com.rarlab.rar","android.intent.action.VIEW","rar","file:///null.rar")')

def pchaddon(uri="",player="",image=""):
    parche,crc = tools.pchaddon(2,uri)
    __addon__.setSetting('parche.'+uri,crc)
    shortforkname = uri.split('.')
    if len(shortforkname)==3: forkname=shortforkname[2]
    else: forkname=''
    if not player=="silent":
        if parche == 0:
            xbmcgui.Dialog().ok("Error al parchear" , "[COLOR red]El parche no se ha aplicado,[COLOR yellow] No está instalado [COLOR lime]"+forkname+"[/COLOR]","[COLOR yellow]o es versión antigua o fichero a parchear no encontrado.[/COLOR]","[COLOR aquamarine]Instala la última versión de [COLOR lime]"+forkname+"[COLOR aquamarine] y vuelve a parchear.[/COLOR]")
        elif parche == 1:
            xbmcgui.Dialog().ok("Torrentin" , "[COLOR yellow]El AddOn [COLOR aquamarine]"+forkname+"[COLOR lime] ha sido parcheado con éxito,[COLOR yellow] se añadirán las carátulas a los videos por torrent y se auto-arrancarán con Torrentin.[/COLOR]")
        elif parche == 2:
            xbmcgui.Dialog().ok("Torrentin" , "[COLOR yellow]El Addon [COLOR lime]"+forkname+"[COLOR yellow] ya ha sido parcheado anteriormente,[/COLOR]", "[COLOR aquamarine]se ha restaurado una copia de seguridad y el parche","ha sido eliminado.[/COLOR]")
        elif parche == 3:
            xbmcgui.Dialog().ok("Error al parchear" , "El parche no se ha aplicado, esta parche SOLO vale","para las versiones  4.1.x  y  4.2.x  de "+forkname,"Instala la última versión de "+forkname+" y vuelve a parchear.")
        xbmc.executebuiltin('Container.Refresh')
    else: xbmc.sleep(100)

def pchaddon2(uri="",player="",image=""):
    parche,crc = tools.pchaddon(1,uri)
    __addon__.setSetting('parche.'+uri,crc)
    shortforkname = uri.split('.')
    if len(shortforkname)==3: forkname=shortforkname[2]
    else: forkname=''
    if not player=="silent":
        if parche == 0:
            xbmcgui.Dialog().ok("Error al parchear" , "[COLOR red]El parche no se ha aplicado,[COLOR yellow] No está instalado [COLOR lime]"+forkname+"[/COLOR]","[COLOR yellow]o es versión antigua o fichero a parchear no encontrado.[/COLOR]","[COLOR aquamarine]Instala la última versión de [COLOR lime]"+forkname+"[COLOR aquamarine] y vuelve a parchear.[/COLOR]")
        elif parche == 1:
            xbmcgui.Dialog().ok("Torrentin" , "[COLOR yellow]El AddOn [COLOR aquamarine]"+forkname+"[COLOR lime] ha sido parcheado con éxito,[COLOR yellow] se añadirán las carátulas a los videos por torrent y se auto-arrancarán con Torrentin.[/COLOR]")
        elif parche == 2:
            xbmcgui.Dialog().ok("Torrentin" , "[COLOR yellow]El Addon [COLOR lime]"+forkname+"[COLOR yellow] ya ha sido parcheado anteriormente,[/COLOR]", "[COLOR aquamarine]se ha restaurado una copia de seguridad y el parche","ha sido eliminado.[/COLOR]")
        elif parche == 3:
            xbmcgui.Dialog().ok("Error al parchear" , "El parche no se ha aplicado, esta parche SOLO vale","para las versiones  4.1.x  y  4.2.x  de "+forkname,"Instala la última versión de "+forkname+" y vuelve a parchear.")
        xbmc.executebuiltin('Container.Refresh')
    else: xbmc.sleep(100)

def pchplexus(uri="",player="",image=""):
    parche , md5sum = tools.pchplexus()
    if parche:
        xbmcgui.Dialog().ok("Torrentin" , "Add-On plexus parcheado con éxito.","Ahora puedes  configurar Torrentin para reproducir los","videos por torrent y enlaces AceLive,\nabre la configuración del Plexus para seleccionar reproductor.")
        __addon__.setSetting('pchplexus',md5sum)
    else:
        xbmcgui.Dialog().ok("Error al parchear" , "La versión instalada no coincide con la del parche,","o no se han encontrado los ficheros de destino.","¿Esta instalado el Add-On plexus?")
        __addon__.setSetting('pchplexus','')
    if not uri == "silent": xbmc.executebuiltin('Container.Refresh')

def pchplexusstreams(uri="",player="",image=""):
    parche = tools.pchplexusstreams()
    if parche == 0:
        xbmcgui.Dialog().ok("Error al parchear" , "El Add-On plexus-streams  no esta instalado","o no se encuentran los ficheros de destino","o no han podido copiarse los ficheros.")
        __addon__.setSetting("pchplexusstreams","Off")
    elif parche == 1:
        xbmcgui.Dialog().ok("Torrentin" , "Add-On plexus-streams parcheado con éxito.","Ahora puedes  configurar Torrentin o Plexus para ","reproducir los enlaces AceLive y torrents locales.")
        __addon__.setSetting("pchplexusstreams","On")
    elif parche == 2:
        xbmcgui.Dialog().ok("Torrentin" , "El Add-On plexus-streams ya ha sido parcheado anteriormente, no es necesario volver a parchearlo. Si quieres que reproduzca con Plexus o Torrentin abre su configuración y cámbialo.")
        __addon__.setSetting("pchplexusstreams","On")
    elif parche == 3:
        xbmcgui.Dialog().ok("Error al parchear" , "La versión instalada no coincide con la del parche o han","cambiado los ficheros de destino al actualizarse el add-on.","El parche no se ha aplicado.")
        __addon__.setSetting("pchplexusstreams","Off")
    if not uri == "silent": xbmc.executebuiltin('Container.Refresh')
'''
0 no esta insalado o no se encuentra o no se copia
1 parcheado
2 ya esta parcheado
3 no coincide
'''
def pchkmedia(uri="",player="",image=""):
    parche , md5sum = tools.pchkmedia()
    if parche:
        xbmcgui.Dialog().ok("Torrentin" , "Add-On KmediaTorrent parcheado con éxito.","Ahora  puedes  descargar  videos .avi completos antes","de reproducirlos y poner el caché en FAT32")
        __addon__.setSetting('pchkmedia',md5sum)
    else:
        xbmcgui.Dialog().ok("Error al parchear" , "La versión instalada no coincide con la del parche,","o no se han encontrado los ficheros de destino.","¿Esta instalado el Add-On KmediaTorrent?")
        __addon__.setSetting('pchkmedia','')
    xbmc.executebuiltin('Container.Refresh')

def renombrador1(uri="",player="",image=""):
    ren = tools.renamer1()
    if ren !="": xbmcgui.Dialog().ok("Torrentin - Archivos renombrados:",ren)
    else: xbmcgui.Dialog().ok("Torrentin - Renombrador ( ) > [ ]" , "[COLOR orange]Ningún archivo renombrado.[/COLOR]")

def renombrador2(uri="",player="",image=""):
    ren = tools.renamer2()
    if ren !="": xbmcgui.Dialog().ok("Torrentin - Archivos renombrados:",ren)
    else: xbmcgui.Dialog().ok("Torrentin - Renombrador: (quita textos)" , "[COLOR orange]Ningún archivo renombrado.[/COLOR]")

def renombrador3(uri="",player="",image=""):
    ren = tools.renamer3()
    if ren !="": xbmcgui.Dialog().ok("Torrentin - Archivos renombrados:",ren)
    else: xbmcgui.Dialog().ok("Torrentin - Renombrador: (. y _ > espacio)" , "[COLOR orange]Ningún archivo renombrado.[/COLOR]")

def renombrador4(uri="",player="",image=""):
    ren = tools.renamer4()
    if ren !="": xbmcgui.Dialog().ok("Torrentin - Archivos renombrados:",ren)
    else: xbmcgui.Dialog().ok("Torrentin - Renombrador: (quita) [tags]" , "[COLOR orange]Ningún archivo renombrado.[/COLOR]")

def renombrador5(uri="",player="",image=""):
    ren=""
    list_folder=__addon__.getSetting('ren_path5')
    if not os.path.isdir(list_folder):
        lista = "Directorio para renombrar películas no\nconfigurado o no se encuentra."
        return
    if __addon__.getSetting('askren5') == "true": confirm = "Activado"
    else: confirm = "Desactivado"
    if __addon__.getSetting('incsubdir') == "true": subdir = "Activado"
    else: subdir = "Desactivado"
    if __addon__.getSetting('prevren5') == "true":
        if not xbmcgui.Dialog().yesno("Torrentin - Renombrar","[COLOR cyan]Renombrar películas como [COLOR chartreuse]Título de la pelicula (año)[/COLOR]" , "[COLOR lime]Directorio: [COLOR yellow]" +  list_folder + "[/COLOR]" ,"[COLOR cyan]Incluir subdirectorios: [COLOR yellow]" + subdir + "\n[COLOR cyan]Preguntar cada una antes de renombrar: [COLOR yellow]" + confirm + "[/COLOR]","Abandonar","Continuar"):
            return
    if subdir == "Activado":
        dirList=os.listdir( list_folder )
        for fname in dirList:
            if os.path.isdir(os.path.join( list_folder , fname )):
                renom = renamer5(os.path.join( list_folder , fname))
                ren = ren+renom
    renom = renamer5(list_folder)
    ren = ren+renom
    if ren !="": xbmcgui.Dialog().ok("Torrentin - Archivos renombrados:",ren)
    else: xbmcgui.Dialog().ok("Torrentin - Renombrador: Título (año)" , "[COLOR orange]Ningún archivo renombrado.[/COLOR]")
    if __addon__.getSetting('cleantmdb') == "true" and __addon__.getSetting('scraper') == "0":
        if xbmcgui.Dialog().yesno("Torrentin - scraper" , "[COLOR lime]¿Limpiar la base de datos de TMDb?[/COLOR]"):
            cleandb()

def movedor(uri="",player="",image=""):
    mov = tools.mover()
    if mov !="": xbmcgui.Dialog().ok("Torrentin - Archivos movidos:",mov)
    else: xbmcgui.Dialog().ok("Torrentin - Movedor" , "[COLOR orange]Ningún archivo movido.[/COLOR]")

def bkpkodi(uri="",player="",image=""):
    if oswin:
        xbmcgui.Dialog().ok("Torrentin - Backup" , "ATENCION, esta opción no esta probada en windows.","Pueden producirse errores por bloqueo de ficheros","comprobar que los backups esten completos.")
    if __addon__.getSetting('bkpdest_path') == "":
        bkp_folder=__addon__.getSetting('torrent_path')
    else:
        bkp_folder=__addon__.getSetting('bkpdest_path')
    if not xbmcgui.Dialog().yesno("Torrentin - Backup" , "[COLOR yellow]Se va a hacer una copia de seguridad, se recomienda borrar los directorios caché de imágenes y addons o tardará mucho más.[/COLOR]","[COLOR cyan]Se guardará en: [COLOR lime]" + bkp_folder + "[/COLOR]","","Abandonar","Continuar"): return
    mov,borra = tools.backupkodi(bkp_folder)
    if borra: aviso = "[COLOR orange]Se borraron cachés, [COLOR yellow]reiniciar Kodi, se cerrará...[/COLOR]"
    else: aviso = ""
    if mov !="":
        xbmcgui.Dialog().ok("Torrentin - Backup" , "[COLOR lime]Configuración de Kodi salvada con éxito en:[/COLOR]" , mov , aviso)
        if borra:
            tools.forceclose()
            xbmc.executebuiltin('Quit')
    else: xbmcgui.Dialog().ok("Torrentin - Backup" , "Ha ocurrido un error al guardar los ficheros.")

def restkodi(uri="",player="",image=""):
    if __addon__.getSetting('bkpdest_path') == "":
        bkp_folder=__addon__.getSetting('torrent_path')
    else:
        bkp_folder=__addon__.getSetting('bkpdest_path')
    if not xbmcgui.Dialog().yesno("Torrentin - Restaurar" , "[COLOR yellow]Se va a restaurar una copia de seguridad creada previamente.[/COLOR]","[COLOR cyan]Desde: [COLOR lime]" + bkp_folder + "[/COLOR]","[COLOR orange]Se restaurará sobre el Kodi actual, es recomendable hacerlo sobre un Kodi limpio o recién instalado.[/COLOR]","Abandonar","Continuar"): return
    backup = xbmcgui.DialogProgress()
    backup.create("Torrentin","Restaurando directorios de Kodi.")
    backup.update(0,"","Espera, No Canceles.","Esto puede tardar...")
    mov = tools.restorekodi(bkp_folder)
    backup.close()
    if mov !="":
        req = 0
        while req == 0:
            xbmcgui.Dialog().ok("Torrentin - Restaurar" , "[COLOR lime]Backup restaurado con éxito.   [COLOR red]¡¡¡¡ ATENCIÓN !!!![/COLOR]","[COLOR orange]No cierre Kodi normalmente o no se restaurará bien, [COLOR yellow]se intentará un cierre forzado... (si no se consigue hay otras opciones que se mostrarán a continuación).[/COLOR]")
            tools.forceclose()
            if xbmc.getCondVisibility('system.platform.Android'):
                xbmcgui.Dialog().ok("Torrentin - Restaurar" ,  "[COLOR yellow]No se ha conseguido el cierre forzado de Kodi, se ha detectado que su sistema es Android y se intentará reiniciar el sistema de forma forzada, esta opción requiere que su dispositivo este 'rooteado' y le de permisos a Kodi en la ventana de SuperUsuario que le aparecerá.[/COLOR]")
                try: os.system("su -c 'reboot'")
                except: pass
            xbmcgui.Dialog().ok("Torrentin - Restaurar" ,  "[COLOR yellow]No se ha conseguido el cierre forzado de Kodi, [COLOR lime]desconecte la alimentación[COLOR yellow] o salga con ALT+TAB o CASA y después use un 'task-killer' para cerrarlo, si no tiene un 'task-killer' instalado y usa Android vaya a Ajustes del sistema->Aplicaciones->Kodi->Forzar cierre.[/COLOR]")
    else: xbmcgui.Dialog().ok("Torrentin - Restaurar" , "Ha ocurrido un error al restaurar los ficheros.")

def cleankodi(uri="",player="",image=""):
    try:
        size = 0
        sizethumb = tools.get_size(xbmc.translatePath(os.path.join('special://home','userdata','Thumbnails')))
        sizethumb = sizethumb + os.path.getsize(xbmc.translatePath(os.path.join('special://home','userdata','Database','Textures13.db')))
        sizepack =  tools.get_size(xbmc.translatePath(os.path.join('special://home','addons','packages')))
        sizetmp = tools.get_size(xbmc.translatePath(os.path.join('special://home','temp')))
        ocupado = "[COLOR yellow]Caché de imágenes: [/COLOR]" + tools.convert_size(sizethumb) + "\n[COLOR yellow]Caché de AddOns: [/COLOR]" + tools.convert_size(sizepack) + "\n[COLOR yellow]Archivos temporales: [/COLOR]" + tools.convert_size(sizetmp) + "\n[COLOR yellow]Total espacio ocupado: [/COLOR]" + tools.convert_size(sizethumb+sizepack+sizetmp)
    except:
        ocupado = "[COLOR yellow]No se pudo determinar el espacio ocupado por los cachés y temporales.[/COLOR]"
        pass
    if xbmcgui.Dialog().yesno("Torrentin - Limpiador" , ocupado,'','','Descartar','Limpiar'):
        clean = xbmcgui.DialogProgress()
        clean.create("Torrentin","Borrando directorios temporales de Kodi.")
        clean.update(0,"","Espera, No Canceles.","Esto puede tardar...")
        mov = tools.tempdel()
        clean.close()
        xbmcgui.Dialog().ok("Torrentin - Limpiador" , "[COLOR lime]Limpieza terminada con éxito.[/COLOR]","[COLOR red]           ¡¡¡¡ ATENCIÓN !!!![/COLOR]","[COLOR orange]Kodi necesita reiniciarse, [COLOR yellow]se cerrará...[/COLOR]")
        tools.forceclose()
        xbmc.executebuiltin('Quit')

def chkupdate(uri="",player="",image=""):
	descarga = xbmcgui.DialogProgress()
	descarga.create("Torrentin","Actualización del Add-On.")
	descarga.update(5,"","Espera, No Canceles.","Buscando actualizaciones...")
	xbmc.sleep(500)
	actual = __version__
	try: versionfile = torrents.url_get("https://bit.ly/torrentinactual").replace("\n","")
	except:
		descarga.close()
		navegar("[COLOR red]Ha ocurrido un error durante la actualización (1)","[COLOR orange]Tienes que buscar manuálmente la nueva versión.","[COLOR yellow]¿ Quieres ir al foro de htcmania para descargarla ?[/COLOR]")
		return
	remote = versionfile.split("|")[0]
	origen = versionfile.split("|")[1]
	if not remote.replace(".","").isdigit():
		descarga.close()
		navegar("[COLOR red]Ha ocurrido un error durante la actualización (2)","[COLOR orange]Tienes que buscar manuálmente la nueva versión.","[COLOR yellow]¿ Quieres ir al foro de htcmania para descargarla ?[/COLOR]")
		return

	if "beta" in actual or "rc" in actual:
		navegar("[COLOR lime]Estás usando una versión beta o RC:  " + actual ,"[COLOR cyan]No está disponible la actualización automática","de versiones beta, [COLOR yellow]¿ Quieres ir a htcmania para actualizar ?[/COLOR]")
		if xbmcgui.Dialog().yesno("Torrentin" , "[COLOR lime]Gracias por colaborar en el desarrollo del AddOn.","[COLOR yellow]Quieres cambiar la versión beta por la última","publicada y así poder actualizar automáticamente ?\n[COLOR orange](Te aparecerá versión 0.0.0 para que detecte la actualización)[/COLOR]"):
			actual = "0.0.0"
		else:
			actual = actual.split("~")[0]

	if int(remote.replace(".","")) > int(actual.replace(".","")):
		if xbmcgui.Dialog().yesno("Torrentin" , "[COLOR cyan]Versión instalada: " + actual,"[COLOR lime]Actualización disponible: " + remote,"[COLOR yellow]¿ Actualizar Torrentin ?[/COLOR]"):
			try:
				destino = os.path.join(xbmc.translatePath(os.path.join('special://home', 'addons')),"packages")
				descarga.update(10,"","Espera, No Canceles.","Obteniendo enlaces.")
				xbmc.sleep(500)
				prebajada = torrents.url_get(origen).replace("\n","")
				if not prebajada.startswith("http"):
					descarga.close()
					navegar("[COLOR red]Ha ocurrido un error durante la actualización (3)","[COLOR orange]Tienes que buscar manuálmente la nueva versión.","[COLOR yellow]¿ Quieres ir al foro de htcmania para descargarla ?[/COLOR]")
					return
				descarga.update(20,"","Espera, No Canceles.","Descargando actualización...")
				xbmc.sleep(500)
				bajada = torrents.url_get(prebajada)
				descarga.update(40,"","Espera, No Canceles.","Descargada, grabando...")
				xbmc.sleep(500)
				f = open(os.path.join( destino , "plugin.video.torrentin-" + remote + ".zip") , "wb")
				f.write(bajada)
				f.close()
				import zipfile
				update = zipfile.ZipFile(os.path.join( destino , "plugin.video.torrentin-" + remote + ".zip"), 'r')
				descarga.update(60,"","Espera, No Canceles.","Extrayendo ficheros...")
				xbmc.sleep(500)
				update.extractall(xbmc.translatePath(os.path.join('special://home', 'addons')))
				descarga.update(80,"","","Actualizando Add-Ons...")
				xbmc.sleep(500)
				xbmc.executebuiltin('Container.Refresh')
				xbmc.executebuiltin( 'UpdateLocalAddons' )
				descarga.update(100,"","Espera, No Canceles.","Terminado.")
				xbmc.sleep(2000)
				descarga.close()
				navegar("[COLOR lime]¡¡¡ Torrentin actualizado a la versión " + remote + " !!![/COLOR]","[COLOR yellow]¿ Quieres ir al foro de htcmania para ver la","información del AddOn o los reproductores ?[/COLOR]")
				xbmcgui.Dialog().ok("Torrentin - Actualizador" , "[COLOR lime]Actualización terminada con éxito.[/COLOR]","[COLOR red]           ¡¡¡¡ ATENCIÓN !!!![/COLOR]","[COLOR orange]Kodi necesita reiniciarse, [COLOR yellow]espere, se cerrará...[/COLOR]")
				#tools.forceclose()
				xbmc.executebuiltin('Quit')
			except:
				descarga.close()
				navegar("[COLOR red]Ha ocurrido un error durante la actualización (4)","[COLOR orange]Tienes que buscar manuálmente la nueva versión.","[COLOR yellow]¿ Quieres ir al foro de htcmania para descargarla ?[/COLOR]")
	elif int(remote.replace(".","")) < int(actual.replace(".","")):
		descarga.close()
		xbmcgui.Dialog().ok("Torrentin" , "[COLOR cyan]Versión actual: " + remote,"Versión instalada: " + actual,"[COLOR lime]Tu versión es más nueva que la última publicada.[/COLOR]")
	else:
		descarga.close()
		navegar("[COLOR cyan]Versión actual: " + remote,"Versión instalada: " + actual,"[COLOR lime]Tienes instalada la última versión.\n[COLOR yellow]¿ Quieres ir al foro para ver las instrucciones ?[/COLOR]")
	
def navegar(uno,dos,tres):
	urlhtcm = "http://www.htcmania.com/showthread.php?t=995348"
	if xbmcgui.Dialog().yesno("Torrentin" , uno,dos,tres):
		if xbmc.getCondVisibility('system.platform.Android'):
			if __addon__.getSetting('browser') == '1':
				xbmc.executebuiltin('XBMC.StartAndroidActivity("com.android.chrome","android.intent.action.VIEW","","'+urlhtcm+'")')
			elif __addon__.getSetting('browser') == '0':
				xbmc.executebuiltin('XBMC.StartAndroidActivity("com.android.browser","android.intent.action.VIEW","","'+urlhtcm+'")')
		elif xbmc.getCondVisibility('system.platform.windows'):
			os.startfile(urlhtcm)
		else: xbmcgui.Dialog().ok("Torrentin" , "[COLOR cyan]Abre tu navegador y visita:[COLOR yellow]",urlhtcm,"[COLOR lime]o busca  torrentin  en Google y ve al primer enlace.[/COLOR]")
	
def renamer5(list_folder):
	#list_folder = unicode(list_folder,'utf-8')
	parent_folder=__addon__.getSetting('ren_path5')
	lista = ""
	global savetit
	dirList=os.listdir( list_folder )
	for fname in dirList:
		if os.path.isdir(os.path.join( list_folder , fname )): continue
		nombre = fname.rsplit(".",1)[0]
		ext = fname.rsplit(".",1)[1]
		if not ext.lower() in ['avi','mp4','mkv','flv','mov','vob','wmv','ogm','asx','mpg','mpeg','avc','vp3','fli','flc','m4v','iso','divx']: continue
		if re.search("\d{1,2}[x|X]\d{2}",nombre):
			if xbmcgui.Dialog().yesno("Torrentin - Renombrador de películas" , "[COLOR chartreuse]"+nombre+"[/COLOR]","[COLOR cyan]¿Seguro que esto es una película?[/COLOR]","[COLOR yellow]Tiene pinta de ser un capítulo de una serie de TV.\n[COLOR red][B]El renombrador solo funciona con películas.[/COLOR][/B]","Renombrar","Descartar"):
				continue
		screener=False
		if re.search("screener",nombre.lower()) and __addon__.getSetting('screener') == "true": screener=True
		savetit=nombre
		renombre = TMDb(nombre)
		if not renombre: break
		if renombre == nombre: continue
		renombre=renombre.replace(":",",").replace("*","").replace("?","¿").replace("<","[").replace(">","]").replace('"',"'").replace("/","").replace("\\","").replace("|","") #caracteres no permitidos en windows
		if screener and re.search( '\(\d{4}\)', renombre[-6:]):
			renomyear=renombre[-6:]
			renombre = renombre[:-6]+"[Screener] "+renomyear
		if __addon__.getSetting('askren5') == "true":
			if list_folder != parent_folder:
				if xbmcgui.Dialog().yesno("Torrentin - Renombrar y Mover:","[COLOR limegreen]Renombrar: [COLOR yellow]" + fname + "[/COLOR]","[COLOR cyan]Como: [COLOR chartreuse]" + renombre + "." + ext + "[/COLOR]","[COLOR cyan]Y mover a: [COLOR magenta]"+parent_folder+"[/COLOR]"):
					if os.path.isfile(os.path.join(parent_folder , renombre + "." + ext)):
						if xbmcgui.Dialog().yesno("Torrentin - Renombrar y Mover:","[COLOR red]ATENCION:  [COLOR chartreuse]" + renombre + "." + ext + "[/COLOR]","[COLOR magenta]Ya existe en: [COLOR cyan]"+parent_folder+"[/COLOR]","[COLOR yellow]¿Quieres sobre-escribir el archivo?[/COLOR]"):
							os.rename(os.path.join(list_folder , fname),os.path.join(parent_folder , renombre + "." + ext))
							lista += "= [COLOR yellow]" + fname+"[/COLOR]\n> [COLOR chartreuse]" + renombre + "." + ext + "[/COLOR]  [COLOR magenta](Movido)[/COLOR]\n"
					else: 
						os.rename(os.path.join(list_folder , fname),os.path.join(parent_folder , renombre + "." + ext))
						lista += "= [COLOR yellow]" + fname+"[/COLOR]\n> [COLOR chartreuse]" + renombre + "." + ext + "[/COLOR]  [COLOR magenta](Movido)[/COLOR]\n"
				else:
					if xbmcgui.Dialog().yesno("Torrentin - Renombrar sin Mover:","[COLOR yellow]" + fname + "[/COLOR]","[COLOR cyan]Como: [/COLOR]","[COLOR chartreuse]" + renombre + "." + ext + "[/COLOR]"):
						if os.path.isfile(os.path.join(list_folder , renombre + "." + ext)):
							if xbmcgui.Dialog().yesno("Torrentin - Renombrar y Mover:","[COLOR red]ATENCION:  [COLOR chartreuse]" + renombre + "." + ext + "[/COLOR]","[COLOR magenta]Ya existe en: [COLOR cyan]"+list_folder+"[/COLOR]","[COLOR yellow]¿Quieres sobre-escribir el archivo?[/COLOR]"):
								os.rename(os.path.join(list_folder , fname),os.path.join(list_folder , renombre + "." + ext))
								lista += "= [COLOR yellow]" + fname+"[/COLOR]\n> [COLOR chartreuse]" + renombre + "." + ext + "[/COLOR]\n"
						else:
								os.rename(os.path.join(list_folder , fname),os.path.join(list_folder , renombre + "." + ext))
								lista += "= [COLOR yellow]" + fname+"[/COLOR]\n> [COLOR chartreuse]" + renombre + "." + ext + "[/COLOR]\n"
			else:
				if xbmcgui.Dialog().yesno("Torrentin - Renombrar:","[COLOR yellow]" + fname + "[/COLOR]","[COLOR cyan]Como: [/COLOR]","[COLOR chartreuse]" + renombre + "." + ext + "[/COLOR]"):
					if os.path.isfile(os.path.join(list_folder , renombre + "." + ext)):
						if xbmcgui.Dialog().yesno("Torrentin - Renombrar y Mover:","[COLOR red]ATENCION:  [COLOR chartreuse]" + renombre + "." + ext + "[/COLOR]","[COLOR magenta]Ya existe en: [COLOR cyan]"+list_folder+"[/COLOR]","[COLOR yellow]¿Quieres sobre-escribir el archivo?[/COLOR]"):
							os.rename(os.path.join(list_folder , fname),os.path.join(list_folder , renombre + "." + ext))
							lista += "= [COLOR yellow]" + fname+"[/COLOR]\n> [COLOR chartreuse]" + renombre + "." + ext + "[/COLOR]\n"
					else:
						os.rename(os.path.join(list_folder , fname),os.path.join(list_folder , renombre + "." + ext))
						lista += "= [COLOR yellow]" + fname+"[/COLOR]\n> [COLOR chartreuse]" + renombre + "." + ext + "[/COLOR]\n"
		else: #NOPREG
			if os.path.isfile(os.path.join(parent_folder , renombre + "." + ext)):
				if xbmcgui.Dialog().yesno("Torrentin - Renombrar sin preguntar:","[COLOR red]ATENCION:  [COLOR chartreuse]" + renombre + "." + ext + "[/COLOR]","[COLOR magenta]Ya existe en: [COLOR cyan]"+parent_folder+"[/COLOR]","[COLOR yellow]¿Quieres sobre-escribir el archivo?[/COLOR]"):
					os.rename(os.path.join(list_folder , fname),os.path.join(parent_folder , renombre + "." + ext))
					lista += "= [COLOR yellow]" + fname+"[/COLOR]\n> [COLOR chartreuse]" + renombre + "." + ext + "[/COLOR]\n"
			else:
				os.rename(os.path.join(list_folder , fname),os.path.join(parent_folder , renombre + "." + ext))
				lista += "= [COLOR yellow]" + fname+"[/COLOR]\n> [COLOR chartreuse]" + renombre + "." + ext + "[/COLOR]\n"
			
	return lista

def TMDb(title):
	yearfromtitle = ""
	try:
		if re.search( '\(\d{4}\)', title[-6:]): #Se presupone que ya esta correctamente renombrada y se desecha, ojo NO usar parentesis en manual.
			return title
			#yearfromtitle=title[-5:].replace(')','')
			#title = title[:-6]
		if re.search( '\d{4}', title[-4:]):
			yearfromtitle=title[-4:]
			title = title[:-4]
		if re.search( '\[\d{4}\]', title[-6:]):
			yearfromtitle=title[-5:].replace(']','')
			title = title[:-6]
	except: pass
	resultados = []
	imagenes = []
	striptitle=tools.StripTags(title)
	striptitle = re.sub("\A\d{2}\s",'',striptitle) #añadido por la mania de numerar pelis (DxTotal)
	striptitle = striptitle.replace("DVDRIP","").replace("DVDRip","").replace(".DVD","").replace("HDTV","").replace(".XviD","").replace("Screener","").replace("screener","").replace(".MP3","")
	striptitle = striptitle.replace("."," ").replace("_"," ").replace("-"," ")
	try:
		data = torrents.url_get("http://api.themoviedb.org/3/search/movie?api_key=cc4b67c52acb514bdf4931f7cedfd12b&query=" + striptitle.replace(" ","%20") + "&year=" + yearfromtitle  + "&language=es&include_adult=false")
	except:
		try:
			xbmc.sleep(500)
			data = torrents.url_get("http://api.themoviedb.org/3/search/movie?api_key=cc4b67c52acb514bdf4931f7cedfd12b&query=" + striptitle.replace(" ","%20") + "&year=" + yearfromtitle  + "&language=es&include_adult=false")
		except:
			mensaje(title + " Error al obtener info en TMDb",2000)
			return title
	if data == "":
		mensaje(title + " Error, no hay datos de TMDb",3000)
		return title
	datadict = json.loads(data , encoding='utf-8')
	if datadict['total_results'] != 0:
		for s in datadict['results']:
			titulo = s['title'].encode('utf-8')
			year = s['release_date'].split('-')[0].encode('utf-8')
			resultados.append(titulo + " (" + year + ")")
			if s['poster_path']: imagenes.append("https://image.tmdb.org/t/p/original" +  s['poster_path'].encode('utf-8'))
			else: imagenes.append(os.path.join(__cwd__ , "icon.png"))
		if len(resultados)!=1:
			resultados.insert(0, "[COLOR orange]---==[([COLOR yellow] Consultar en la web [COLOR orange])]==----[/COLOR]")
			resultados.insert(0, "[COLOR orange]---==[([COLOR yellow] Búsqueda manual [COLOR orange])]==----[/COLOR]")
			seleccion = xbmcgui.Dialog().select(savetit , resultados)
		else:
			seleccion=0 # solo 1 se pilla
			show_Msg(resultados[0] ,"automático",9000,imagenes[0])
			return resultados[0]
		if seleccion != -1:
			if seleccion ==0: #Manual
				striptitle=savetit.replace("."," ").replace("_"," ").replace("-"," ")
				keyboard = xbmc.Keyboard(striptitle,savetit)
				keyboard.doModal()
				if (keyboard.isConfirmed()):
					striptitle = keyboard.getText()
					if striptitle=="" or  striptitle ==None: return title
					nuevotitulo = TMDb(striptitle)
					return nuevotitulo
			elif seleccion ==1: #web
				if xbmc.getCondVisibility('system.platform.Android'):
					if __addon__.getSetting('browser') == '0':
						xbmc.executebuiltin('XBMC.StartAndroidActivity("com.android.browser","android.intent.action.VIEW","","'+"https://www.themoviedb.org/search/movie?query=" + striptitle.replace(" ","+")+'")')
					elif __addon__.getSetting('browser') == '1':
						xbmc.executebuiltin('XBMC.StartAndroidActivity("com.android.chrome","android.intent.action.VIEW","","'+"https://www.themoviedb.org/search/movie?query=" + striptitle.replace(" ","+")+'")')
				elif xbmc.getCondVisibility('system.platform.windows'):
					os.startfile("https://www.themoviedb.org/search/movie?query=" + striptitle.replace(" ","+"))
				else:
					mensaje('Opción disponible en Windows y Android', 3000)
				nuevotitulo = TMDb(striptitle)
				return nuevotitulo
			else: #Ha seleccionado alguna
				nuevotitulo = resultados[seleccion]
				show_Msg(nuevotitulo , "manual" ,9000,imagenes[seleccion-2])
				return nuevotitulo
		else: # canceló
			return savetit
	else: #no hay resultados
		reintentatitle = striptitle.rsplit(" ")
		quita = striptitle.rsplit(" ",1)[0]
		if len(reintentatitle) >1:
			nuevotitulo = TMDb(quita)
			return nuevotitulo
		else :
			striptitle=savetit.replace("."," ").replace("_"," ").replace("-"," ")
		if xbmcgui.Dialog().yesno("Torrentin - Renombrador de películas" , "[COLOR yellow]" + striptitle  + "[/COLOR]","[COLOR magenta]No se encuentra en TMDb con ese nombre.[/COLOR]","[COLOR cyan]Búsqueda manual, puedes añadir espacio y año al final (sin parénesis) para refinar la búsqueda.[/COLOR]","Descartar","Teclado"):
			keyboard = xbmc.Keyboard(striptitle)
			keyboard.doModal()
			if (keyboard.isConfirmed()):
				striptitle = keyboard.getText()
				if striptitle =="": return title
				nuevotitulo = TMDb(striptitle)
				return nuevotitulo
		else: return savetit

def autoparche():
    findact()
    xbmc.sleep(10000) #Espera 30 segundos por si se estan actualizando los addons.
    if __addon__.getSetting('autopatch') == "true":
        shortforkname = __addon__.getSetting('forkname').split('.')
        if len(shortforkname)==3: forkname=shortforkname[2]
        else: forkname=''
        shortforkname2 = __addon__.getSetting('forkname2').split('.')
        if len(shortforkname2)==3: forkname2=shortforkname2[2]
        else: forkname2=''
        if xbmc.getCondVisibility('System.HasAddon("' + __addon__.getSetting('forkname') + '")'):
            if tools.chkpchaddon(__addon__.getSetting('forkname')) == 0 and tools.ispelisfork(forkname):
                mensaje("Auto-parche: "+forkname,2000)
                xbmc.sleep(2000)
                if __addon__.getSetting('autopatchtype') == "0": pchaddon(__addon__.getSetting('forkname'),"silent")
                else: pchaddon2(__addon__.getSetting('forkname'),"silent")
                xbmc.executebuiltin('Container.Refresh')
        if xbmc.getCondVisibility('System.HasAddon("' + __addon__.getSetting('forkname2') + '")'):
            if tools.chkpchaddon(__addon__.getSetting('forkname2')) == 0 and tools.ispelisfork(forkname2):
                mensaje("Auto-parche: "+forkname2,2000)
                xbmc.sleep(2000)
                if __addon__.getSetting('autopatchtype') == "0": pchaddon(__addon__.getSetting('forkname2'),"silent")
                else: pchaddon2(__addon__.getSetting('forkname2'),"silent")
                xbmc.executebuiltin('Container.Refresh')
    if __addon__.getSetting('autopatchpl') == "true":
        if xbmc.getCondVisibility("System.HasAddon(program.plexus)"):
            if not tools.chkpchplexus():
                mensaje("Auto-parche: plexus",2000)
                pchplexus("silent")
    if __addon__.getSetting('autopatchps') == "true":
        if xbmc.getCondVisibility("System.HasAddon(plugin.video.plexus-streams)"):
            if tools.chkps() == 0:
                mensaje("Auto-parche: plexus-streams",2000)
                pchplexusstreams("silent")
    return

def findact():
    if  __addon__.getSetting('autoupdate') == "true":
        ultimo =  __addon__.getSetting('autotimer')
        if ultimo == "": ultimo="0.00"
        if time.time() - float(ultimo) < 86400: #No han pasado 24 h
            return
        else:
            __addon__.setSetting('autotimer',str(time.time()))
        actual = __version__
        try: versionfile = torrents.url_get("https://raw.githubusercontent.com/surebic/plugin.video.torrentin/master/archives/version.txt").replace("\n","")
        except:
            mensaje("Error al comprobar actualizaciones",2000)
            return
        remote = versionfile.split("|")[0]
        if not remote.replace(".","").isdigit(): 
            return
        if "beta" in actual or "rc" in actual:
            mensaje("Torrentin beta, actualizar a mano.",2000)
            return
        if int(remote.replace(".","")) > int(actual.replace(".","")):
            chkupdate()

# EOF (02-2018)
