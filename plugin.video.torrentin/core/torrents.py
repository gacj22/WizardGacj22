# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Torrentin - XBMC/Kodi AddOn
# por ciberus  - Para reproducir por AceStream .torrent descargados o locales y otros Add-Ons o App's
#------------------------------------------------------------
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

import sys,os,urllib,base64,xbmc,xbmcgui,xbmcaddon

__addon__ = xbmcaddon.Addon( id = 'plugin.video.torrentin' )
__cwd__        = __addon__.getAddonInfo('path')
original_torrentin_uri =""

def cargar():
            torrentfile = xbmcgui.Dialog().browse(1, 'Elegir .torrent en dispositivo local', 'video', '.torrent',True)
            if torrentfile != "":
                img=""
                try:
                    findimg= torrentfile.replace('.torrent','.png')
                    if os.path.isfile(findimg): img=findimg
                    findimg= torrentfile.replace('.torrent','.jpg')
                    if os.path.isfile(findimg): img=findimg
                except: pass
                return torrentfile,img
            else: return False,False

def browsear(dir,subdir=""):
	itemlist = {}
	if dir ==1: torr_folder= __addon__.getSetting('torrent_path')
	elif dir == 2:
		if __addon__.getSetting('torrent_path_tvp'):
			torr_folder=__addon__.getSetting('torrent_path_tvp')
		else:
			xbmcgui.Dialog().ok("Torrentin" , "Directorio secundario de torrents no configurado.")
			__addon__.openSettings()
			return itemlist
	if subdir is not None: torr_folder = subdir
	if not os.path.isdir(torr_folder):
		xbmcgui.Dialog().ok("Torrentin" , "ERROR, No se puede acceder al directorio.")
		return itemlist
	dirList=os.listdir( torr_folder )
	for fname in dirList:
		#if os.path.isdir(os.path.join( torr_folder , fname )) or fname.endswith('.meta.torrent') or fname.startswith("torrentin."): continue
		if fname.endswith('.meta.torrent') or fname.startswith("torrentin."): continue
		if os.path.isdir(os.path.join( torr_folder , fname )):
			img=''
			itemlist[os.path.join(torr_folder , fname)] = img
		if fname.endswith('.torrent'):
			img=""
			findimg= os.path.join( torr_folder ,  fname.replace('.torrent','.png'))
			if os.path.isfile(findimg): img=findimg
			findimg= os.path.join( torr_folder ,  fname.replace('.torrent','.jpg'))
			if os.path.isfile(findimg): img=findimg
			itemlist[os.path.join(torr_folder , fname)] = img
		if fname.endswith('.magnet'):
			img=""
			findimg= os.path.join( torr_folder ,  fname.replace('.magnet','.png'))
			if os.path.isfile(findimg): img=findimg
			findimg= os.path.join( torr_folder ,  fname.replace('.magnet','.jpg'))
			if os.path.isfile(findimg): img=findimg
			itemlist[os.path.join(torr_folder , fname)] = img
	return itemlist

def play_acelive(link,imagen=""):
	from AceStream import TSengine as tsengine
	videos = {}
	if imagen == "": imagen = os.path.join( __cwd__ ,"resources","images","acestreamlogo.png")
	TSplayer=tsengine()
	carga=TSplayer.load_torrent(link.replace("acestream://",""),'PID',port=int(__addon__.getSetting('portace')))
	if carga=='Ok':
		for k,v in TSplayer.files.iteritems():
			titulo = urllib.unquote(k)
			videos[titulo] = v
	if len(videos.keys()) == 1:
		savelink(link,titulo)
		TSplayer.play_url_ind(videos.get(titulo), titulo, None, imagen)
	elif len(videos.keys()) >= 2:
		seleccion = xbmcgui.Dialog().select("Seleccionar stream", videos.keys())
		if seleccion != -1: TSplayer.play_url_ind( videos.get(videos.keys()[seleccion]) , videos.keys()[seleccion] , None, imagen)
		else: show_Msg('Reproductor AceStream', 'Ningun stream elegido', 3000)    
	else: ok = xbmcgui.Dialog().ok("Reproductor AceStream" , "AceStream no ha podido cargar el stream")
	TSplayer.end()

def savelink(link,name):
	torrent_folder=__addon__.getSetting('torrent_path')
	if not link.startswith("acestream://"): return
	if __addon__.getSetting("savelive")== "true":
		fichero = os.path.join(torrent_folder,"Torrentin-Streams.m3u")
		if not os.path.isfile(fichero):
			try:
				f = open(fichero , "w+")
				f.write("#EXTM3U\n\n")
				f.close()
			except: pass
		try:
			f = open(fichero , "a")
			f.write("#EXTINF:-1," + name + "\n")
			f.write(link + "\n")
			f.close()
		except: pass

def play_torrent_from_file(fichero, imagen = ""):
	try:
		f = open(fichero, 'rb')
		data=f.read()
		f.close
	except:
		xbmcgui.Dialog().ok("Reproductor AceStream" , "No se ha podido cargar el fichero torrent")
		return
	check = acewarn(data)
	if not check:
		sel = xbmcgui.Dialog().yesno("Reproductor AceStream" , "AceStream tiene un error interno y no reproduce","correctamente videos de mas de 2Gb. contenidos","en archivos torrent multifichero.  Reproducir?")
		if not sel: return
	from AceStream import TSengine as tsengine
	videos = {}
	if imagen == "": imagen = os.path.join( __cwd__ ,"resources","images","acestreamlogo.png")
	TSplayer=tsengine()
	carga=TSplayer.load_torrent(base64.b64encode(data),'RAW',port=int(__addon__.getSetting('portace')))
	if carga=='Ok':
		for k,v in TSplayer.files.iteritems():
			titulo = urllib.unquote(k)
			videos[titulo] = v
	if len(videos.keys()) == 1:
		TSplayer.play_url_ind(videos.get(titulo), titulo, None, imagen)
	elif len(videos.keys()) >= 2:
		seleccion = xbmcgui.Dialog().select("Seleccionar Video", videos.keys())
		if seleccion != -1: TSplayer.play_url_ind( videos.get(videos.keys()[seleccion]) , videos.keys()[seleccion] , None, imagen)
		else: show_Msg('Reproductor AceStream', 'Ningun video elegido', 3000)    
	else: ok = xbmcgui.Dialog().ok("Reproductor AceStream" , "AceStream no ha podido cargar la lista de ficheros del torrent.")
	TSplayer.end()

def show_Msg(heading, message, time = 6000, pic = os.path.join(__cwd__ , "icon.png")):
    if __addon__.getSetting('nosound') == "true":
        try: xbmcgui.Dialog().notification(heading, message, pic, time, 0)
        except: pass
    else:
        try: xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "%s")' % (heading, message, time, pic))
        except:
            try: xbmcgui.Dialog().notification(heading, message, pic, time, 0)
            except: pass

def acewarn(torrent_data):
    if not xbmc.getCondVisibility('System.Platform.Android'): return True
    import bencode
    try:
        metadata = bencode.bdecode(torrent_data)
    except: return False
    multi = False
    bigsize = 0
    try: bigsize = int(metadata['info']["length"])
    except:
        multi = True
        size=0
        for file in metadata["info"]["files"]:
            size = int( file["length"])
            if size > bigsize: bigsize = size
    if bigsize > 2147483648 and multi: return False
    else: return True

def dltorrent(url , player="" , image=""):
    torrent_folder=__addon__.getSetting('torrent_path')
    global original_torrentin_uri
    original_torrentin_uri = url
    descarga = xbmcgui.DialogProgress()
    descarga.create("Torrentin","Descargando el torrent de:",url)
    descarga.update(0,"","","Esperando a la web del canal...")
    xbmc.sleep(100)
    torrent_data = url_get(url)
    if descarga.iscanceled():
        descarga.close()
        return False
    if torrent_data =="": 
        descarga.update(0,"","","ERROR al descargar el torrent !!!")
        xbmc.sleep(3000)
        descarga.close()
        return False
    descarga.update(30,"","","Torrent descargado")
    xbmc.sleep(100)
    try:
        f = open(os.path.join( torrent_folder , "torrentin.torrent" ) , "wb+")
        f.write(torrent_data)
        f.close()
        descarga.update(60,"","","Torrent descargado y guardado...")
        xbmc.sleep(100)
    except:
        descarga.update(50,"","","ERROR al guardar el torrent !!!")
        xbmc.sleep(3000)
        descarga.close()
        return False

    getimg = SaveImgLink(image)
    if getimg:
        descarga.update(100,"","","Torrent descargado y guardado con caratula.")
        xbmc.sleep(100)
        descarga.close()
        return True
    else:
        descarga.update(100,"","","Torrent descargado y guardado SIN caratula.")
        xbmc.sleep(200)
    descarga.close()
    return True

def SaveImgLink(image=""):
    torrent_folder=__addon__.getSetting('torrent_path')
    #if os.path.isfile(os.path.join( torrent_folder , "torrentin.torrent.img")): os.remove(os.path.join( torrent_folder , "torrentin.torrent.img"))
    if image != "":
        f = open(os.path.join( torrent_folder , "torrentin.torrent.img") , "wb+")
        f.write(image)
        f.close()
        return True
    else:
        f = open(os.path.join( torrent_folder , "torrentin.torrent.img") , "wb+")
        f.write("http://i.imgur.com/Hllxyx4.png")
        f.close()
        return False

def url_get(url, params={}, headers={}):
    import urllib2
    from contextlib import closing
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:20.0) Gecko/20100101 Firefox/20.0"
    if params:
        import urllib
        url = "%s?%s" % (url, urllib.urlencode(params))
    req = urllib2.Request(url)
    req.add_header("User-Agent", USER_AGENT)
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with closing(urllib2.urlopen(req)) as response:
            data = response.read()
            if response.headers.get("Content-Encoding", "") == "gzip":
                import zlib
                return zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(data)
            return data
    except urllib2.HTTPError:
        return None

def plexus(uri,player="",image="",plugin=""):
    titulo = torrent_info(uri , 1)
    if titulo =="": titulo = "Torrentin video"
    if player == 7: clon = "plugin.video.p2p-streams"
    elif player == 8: clon = "program.plexus"
    xbmc.executebuiltin( "PlayMedia("+"plugin://"+clon+"/?url=%s&mode=1&iconimage=%s&name=%s" % (urllib.quote_plus(uri),urllib.quote_plus(image),urllib.quote_plus(titulo) )+")" )

def torrenter(uri,player="",image=""):
    if uri.startswith('file://'):uri = uri.replace("file://","")
    xbmc.executebuiltin( "PlayMedia(plugin://plugin.video.torrenter/?action=playSTRM&url=%s" % urllib.quote_plus(uri)+")" )

def yatp(uri,player="",image=""):
    if uri.startswith('file://'):uri = uri.replace("file://","")
    xbmc.executebuiltin( "PlayMedia(plugin://plugin.video.yatp/?action=play&torrent=%s" % urllib.quote_plus(uri)+")" )

def SteeveClones(uri,player="",image=""):
    plugin = 1
    if player == 2: clon = "xbmctorrent"
    elif player == 3: clon = "stream"
    elif player == 4: clon = "kmediatorrent"
    elif player == 5:
        clon2 = "pulsar"
        plugin = 2
    elif player == 6:
        clon2 = "quasar"
        plugin = 2
    elif player == 11:
    	clon2 = "elementum"
        plugin = 2
    if uri.startswith('magnet:'):
        if plugin == 1:
            xbmc.executebuiltin( "PlayMedia("+"plugin://plugin.video."+clon+"/play/%s" % urllib.quote_plus(uri)+")" )
        elif plugin == 2:
            xbmc.executebuiltin( "PlayMedia("+"plugin://plugin.video."+clon2+"/play?uri=%s" % urllib.quote_plus(uri)+")" )
    elif uri.startswith('file://'):
        global original_torrentin_uri
        magnet = torrent_to_magnet(uri.replace("file://",""))
        if not magnet:
            if original_torrentin_uri.startswith("http:"): 
                magnet = original_torrentin_uri
            else:
                show_Msg('          ---===[ Torrentin ]===---', 'Error al transformar torrent en magnet', 3000)    
                return
        if original_torrentin_uri.startswith("http:") and player == 6: magnet = original_torrentin_uri
        if plugin == 1:
            xbmc.executebuiltin( "PlayMedia("+"plugin://plugin.video."+clon+"/play/%s" % urllib.quote_plus(magnet)+")" )
        elif plugin == 2:
            xbmc.executebuiltin( "PlayMedia("+"plugin://plugin.video."+clon2+"/play?uri=%s" % urllib.quote_plus(magnet)+")" )
    else:
        show_Msg('          ---===[ Torrentin ]===---', 'Enlace no valido para el AddOn seleccionado', 3000)    

def torrent_to_magnet(file):
    try:
        f = open(file , "rb")
        torrent_data=f.read()
        f.close()
    except:
        return False
    import base64
    import bencode
    import hashlib
    try:
        metadata = bencode.bdecode(torrent_data)
    except: return False
    hashcontents = bencode.bencode(metadata['info'])
    digest = hashlib.sha1(hashcontents).digest()
    b32hash = base64.b32encode(digest)
    params = {
        'dn': metadata['info']['name'],
        'tr': metadata['announce'],
    }
    paramstr = urllib.urlencode(params)
    return 'magnet:?%s&%s' % ('xt=urn:btih:%s' % b32hash, paramstr)

def torrent_info(uri , infotype):
    if uri.startswith("file://"): file = uri.replace("file://","")
    elif uri.startswith("magnet:"):
        title = ""
        try:
            title = uri.rsplit("dn=")[1] 
            title = title.rsplit("&")[0] 
            title = urllib.unquote_plus(title)
        except: pass
        if title != "":
            if infotype == 0: return "[COLOR yellow]Magnet:  [/COLOR][COLOR magenta] Nombre: [/COLOR][COLOR cyan]"+ title + "  [/COLOR][COLOR magenta] Enlace: [/COLOR][COLOR orange]"+uri+"[/COLOR]  (Click aqui para ExtendedInfo)"
            elif infotype == 1: return title
        else:
            if infotype == 0: return "[COLOR yellow]Magnet:  [/COLOR][COLOR magenta] Enlace: [/COLOR][COLOR cyan]"+uri+"[/COLOR]"
            elif infotype == 1: return ''
    elif uri.startswith("acestream://"):
        if infotype == 0: return "[COLOR yellow]AceLive:   [/COLOR][COLOR magenta]Enlace: [/COLOR][COLOR cyan]"+uri+"[/COLOR]"
        elif infotype == 1: return ''
    else: return "Enlace no valido para reproducir con Torrentin"
    try:
        f = open(file, "rb")
        torrent_data=f.read()
        f.close()
    except:
        return "[COLOR red]No hay informacion o nombre de fichero no valido (renombralo a mano).[/COLOR]"
    if torrent_data == "": return "[COLOR red]No hay informacion, posible torrent corrupto o nombre de fichero no valido.[/COLOR]"
    import base64
    import bencode
    import hashlib
    try:
        metadata = bencode.bdecode(torrent_data)
    except:
        if infotype == 0: return "[COLOR red]No se puede extraer la informacion de torrent, metadatos con formato no standard, pero se puede descargar o reproducir con la mayoria de los reproductores.[/COLOR]"
        elif infotype == 1: return ''
    try:
        bigsize = int(metadata['info']["length"])
        ttype = "(torrent monofichero)"
        title = metadata['info']['name']
        tipo, torrentname = chkvideo(title)
    except:
        ttype = "(torrent multifichero)"
        bigsize=0
        for file in metadata["info"]["files"]:
            title = "/".join(file["path"]).strip("'")
            size = int( file["length"])
            if size > bigsize:
                bigsize = size
                tipo, torrentname = chkvideo(title)
    if bigsize > 1073741824: sizegb = "%0.2f Gb)[/COLOR] " % (bigsize/1073741824.0)
    else: sizegb = str(bigsize/1048576)+" Mb)[/COLOR] "
    if bigsize > 2147483648 and ttype =="(M)" and xbmc.getCondVisibility('System.Platform.Android'):
        sizecol = "  [COLOR red]("+sizegb
    else:
        sizecol = "  [COLOR lime]("+sizegb
    if infotype == 0: return "[COLOR yellow]Torrent:   [/COLOR][COLOR magenta]Video: [/COLOR][COLOR orange]" + tipo +"[/COLOR]" +  sizecol + "[COLOR magenta] Nombre: [/COLOR][COLOR cyan]"+ torrentname + "  [/COLOR][COLOR orange]" + ttype + "[/COLOR]  (Click aqui para ExtendedInfo)"
    elif infotype == 1: return torrentname

def chkvideo(title):
    ext = title.split('.')[-1]
    torrentname = title.rsplit(".",1) [0]
    if ext.lower() in ['rar','avi','mp4','mkv','flv','mov','vob','wmv','ogm','asx','mpg','mpeg','avc','vp3','fli','flc','m4v','iso','divx']:
        tipo = ext.upper()
    else:
            tipo = "No Video"
    return tipo, torrentname

