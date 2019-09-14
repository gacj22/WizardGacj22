#!/usr/bin/python
# -*- coding: utf-8 -*-
#:-----------------------------------------------------------
# Torrentin - XBMC/Kodi AddOn
# por ciberus (algunas rutinas tomadas de la web)
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

import sys,os,xbmc,zipfile,xbmcaddon,xbmcvfs,xbmcgui
__addon__ = xbmcaddon.Addon( id = 'plugin.video.torrentin' )
__scriptid__   = __addon__.getAddonInfo('id')
__cwd__        = __addon__.getAddonInfo('path')
__language__   = __addon__.getLocalizedString
addonspath = xbmc.translatePath(os.path.join('special://home', 'addons'))

def ldlst(lista):
	list_folder=__addon__.getSetting('torrent_path')
	itemlist = {}
	if not os.path.isdir(list_folder): return itemlist
	f = open(os.path.join( list_folder ,  lista),"r")
	line = f.readline()
	if not line.startswith("#EXTM3U"): return itemlist
	for line in f:
		line=line.strip()
		if line.startswith('#EXTINF:'):
			canal = line.split(',')[-1]
		elif (len(line) != 0):
			if not line.startswith("acestream://"): line = "acestream://"+line
			itemlist[canal] = line
	f.close()
	return itemlist

def ldlstall():
	list_folder=__addon__.getSetting('torrent_path')
	itemlist = {}
	if not os.path.isdir(list_folder): return itemlist
	dirList=os.listdir( list_folder )
	for fname in dirList:
		if os.path.isdir(os.path.join( list_folder , fname )): continue
		if fname.endswith('.m3u'):
			f = open(os.path.join( list_folder ,  fname),"r")
			line = f.readline()
			if not line.startswith("#EXTM3U"): continue
			for line in f:
				line=line.strip()
				if line.startswith('#EXTINF:'):
					canal = line.split(',')[-1]
				elif (len(line) != 0):
					itemlist[canal] = line
			f.close()
	return itemlist

def renamer1():
	list_folder=__addon__.getSetting('ren_path1')
	lista = ""
	if not os.path.isdir(list_folder):
		lista = "Directorio para renombrar archivos no\nconfigurado o no se encuentra."
		return lista
	if __addon__.getSetting('askren1') == "true": confirm = "Activado"
	else: confirm = "Desactivado"
	if not xbmcgui.Dialog().yesno("Torrentin - Renombrar","[COLOR cyan]Sustituir ( ) por [ ] en el nombre de archivos[/COLOR]" , "[COLOR lime]Directorio: [COLOR yellow]" +  list_folder + "[/COLOR]" , "[COLOR cyan]Preguntar en cada uno antes de renombrar [COLOR yellow]" + confirm + "[/COLOR]" ,"Abandonar","Continuar"):
		return lista
	dirList=os.listdir( list_folder )
	for fname in dirList:
		if os.path.isdir(os.path.join( list_folder , fname )): continue
		if "(" in fname or ")" in fname:
			nuevo=fname
			nuevo = nuevo.replace("(","[").replace(")","]")
			if __addon__.getSetting('askren1') == "true":
				if xbmcgui.Dialog().yesno("Torrentin - Renombrar:",fname,"como:",nuevo):
					os.rename(os.path.join(list_folder , fname),os.path.join(list_folder , nuevo))
					lista += "= " + fname+"\n> " + nuevo + "\n"
			else:
				os.rename(os.path.join(list_folder , fname),os.path.join(list_folder , nuevo))
				lista += "= " + fname+"\n> " + nuevo + "\n"
	return lista

def renamer2():
	list_folder=__addon__.getSetting('ren_path2')
	lista = ""
	if not os.path.isdir(list_folder):
		lista = "Directorio para renombrar archivos no\nconfigurado o no se encuentra."
		return lista
	if __addon__.getSetting('askren2') == "true": confirm = "Activado"
	else: confirm = "Desactivado"
	if not xbmcgui.Dialog().yesno("Torrentin - Renombrar","[COLOR cyan]Quitar cadenas de texto pre-definidas en el nombre de archivos[/COLOR]" , "[COLOR lime]Directorio: [COLOR yellow]" +  list_folder + "[/COLOR]" , "[COLOR cyan]Preguntar en cada uno antes de renombrar [COLOR yellow]" + confirm + "[/COLOR]","Abandonar","Continuar"):
		return lista
	dirList=os.listdir( list_folder )
	strsup = __addon__.getSetting('stringsup').split("|")
	for fname in dirList:
		if os.path.isdir(os.path.join( list_folder , fname )): continue
		nuevo = fname
		for n in strsup:
			if n!="" and n in nuevo:
				nuevo = nuevo.replace(n,'')
		if nuevo != fname:
			if __addon__.getSetting('askren2') == "true":
				if xbmcgui.Dialog().yesno("Torrentin - Renombrar:",fname,"como:",nuevo):
					os.rename(os.path.join(list_folder , fname),os.path.join(list_folder , nuevo))
					lista += "= " + fname+"\n> " + nuevo + "\n"
			else:
				os.rename(os.path.join(list_folder , fname),os.path.join(list_folder , nuevo))
				lista += "= " + fname+"\n> " + nuevo + "\n"
	return lista

def renamer3():
	list_folder=__addon__.getSetting('ren_path3')
	lista = ""
	if not os.path.isdir(list_folder):
		lista = "Directorio para renombrar archivos no\nconfigurado o no se encuentra."
		return lista
	if __addon__.getSetting('askren3') == "true": confirm = "Activado"
	else: confirm = "Desactivado"
	if not xbmcgui.Dialog().yesno("Torrentin - Renombrar","[COLOR cyan]Sustituir . y _ por espacio en el nombre de archivos[/COLOR]" , "[COLOR lime]Directorio: [COLOR yellow]" +  list_folder + "[/COLOR]" , "[COLOR cyan]Preguntar en cada uno antes de renombrar [COLOR yellow]" + confirm + "[/COLOR]","Abandonar","Continuar"):
		return lista
	dirList=os.listdir( list_folder )
	for fname in dirList:
		if os.path.isdir(os.path.join( list_folder , fname )): continue
		nombre = fname.rsplit(".",1)[0]
		ext = fname.rsplit(".",1)[1]
		if "." in nombre or "_" in nombre:
			renombre=stripnew(nombre)
			if renombre == nombre: continue
			if __addon__.getSetting('askren3') == "true":
				if xbmcgui.Dialog().yesno("Torrentin - Renombrar:",fname,"como:",renombre + "." + ext):
					os.rename(os.path.join(list_folder , fname),os.path.join(list_folder , renombre + "." + ext))
					lista += "= " + fname+"\n> " + renombre + "." + ext + "\n"
			else:
				os.rename(os.path.join(list_folder , fname),os.path.join(list_folder , renombre + "." + ext))
				lista += "= " + fname+"\n> " + renombre + "." + ext + "\n"
	return lista

def renamer4():
	list_folder=__addon__.getSetting('ren_path4')
	lista = ""
	if not os.path.isdir(list_folder):
		lista = "Directorio para renombrar archivos no\nconfigurado o no se encuentra."
		return lista
	if __addon__.getSetting('askren4') == "true": confirm = "Activado"
	else: confirm = "Desactivado"
	if not xbmcgui.Dialog().yesno("Torrentin - Renombrar","[COLOR cyan]Quitar lo que haya entre parentesis y llaves en el nombre de archivos[/COLOR]" , "[COLOR lime]Directorio: [COLOR yellow]" +  list_folder + "[/COLOR]" , "[COLOR cyan]Preguntar en cada uno antes de renombrar [COLOR yellow]" + confirm + "[/COLOR]","Abandonar","Continuar"):
		return lista
	dirList=os.listdir( list_folder )
	for fname in dirList:
		if os.path.isdir(os.path.join( list_folder , fname )): continue
		nombre = fname.rsplit(".",1)[0]
		ext = fname.rsplit(".",1)[1]
		renombre=StripTags(nombre)
		if renombre == nombre: continue
		if __addon__.getSetting('askren4') == "true":
			if xbmcgui.Dialog().yesno("Torrentin - Renombrar:",fname,"como:",renombre + "." + ext):
				os.rename(os.path.join(list_folder , fname),os.path.join(list_folder , renombre + "." + ext))
				lista += "= " + fname+"\n> " + renombre + "." + ext + "\n"
		else:
			os.rename(os.path.join(list_folder , fname),os.path.join(list_folder , renombre + "." + ext))
			lista += "= " + fname+"\n> " + renombre + "." + ext + "\n"
	return lista

def stripnew(text):
	if not '[' in text and not '(' in text: return text.replace("."," ").replace("_"," ")
	texto = ''
	start = text.find("[")
	if start >= 0:
		texto=text[:start].replace("."," ").replace("_"," ") + text[start:]
	start = text.find("(")
	if start >= 0:
		texto=text[:start].replace("."," ").replace("_"," ") + text[start:]
	return texto

def mover():
	orig_folder=__addon__.getSetting('moveorig_path')
	dest_folder=__addon__.getSetting('movedest_path')
	lista = ""
	if not os.path.isdir(orig_folder) or not os.path.isdir(dest_folder):
		lista = "Directorio origen y/o destino no configurados\n o no se encuentran."
		return lista
	if __addon__.getSetting('askmov') == "true": confirm = "Activado"
	else: confirm = "Desactivado"
	if not xbmcgui.Dialog().yesno("Torrentin - Mover","[COLOR cyan]Mover todos los archivos de los directorios[/COLOR]" , "[COLOR lime]Origen: [COLOR yellow]" +  orig_folder + "[/COLOR]" ,
"[COLOR lime]Destino: [COLOR yellow]" + dest_folder + "[/COLOR]\n[COLOR cyan]Preguntar en cada uno antes de mover [COLOR yellow]" + confirm + "[/COLOR]","Abandonar","Continuar"):
		return lista
	dirList=os.listdir( orig_folder )
	for fname in dirList:
		if os.path.isdir(os.path.join( orig_folder , fname )): continue
		if __addon__.getSetting('askmov') == "true":
				if xbmcgui.Dialog().yesno("Torrentin - Mover:",os.path.join(orig_folder , fname),"a:",os.path.join(dest_folder , fname)):
					try:
						os.rename(os.path.join(orig_folder , fname),os.path.join(dest_folder , fname))
						lista += fname+"\n"
					except:
						xbmcvfs.copy(os.path.join(orig_folder , fname),os.path.join(dest_folder , fname))
						os.remove(os.path.join(orig_folder , fname))
						lista += fname+"\n"
		else:
				try:
					os.rename(os.path.join(orig_folder , fname),os.path.join(dest_folder , fname))
					lista += fname+"\n"
				except:
					xbmcvfs.copy(os.path.join(orig_folder , fname),os.path.join(dest_folder , fname))
					os.remove(os.path.join(orig_folder , fname))
					lista += fname+"\n"
	return lista

def backupkodi(bkp_folder):
	borra = False
	if not os.path.isdir(bkp_folder):
		xbmcgui.Dialog().ok("Torrentin" , "Las copias de seguridad usan el directorio",
                                                                  "principal de Torrentin si no se configura uno,",
                                                                  "el directorio configurado no se encuentra.")
		return '', borra
	from time import strftime
	if __addon__.getSetting('editbkpname') == "true":
		prefichero="BackupKodi"+strftime("(%d-%m-%y-%H%M)")
		keyboard = xbmc.Keyboard(prefichero,"Nombre del archivo (respeta la palabra 'Backup' del principio.")
		keyboard.doModal()
		if (keyboard.isConfirmed()):
			prefichero = keyboard.getText()
		else: return '', borra
		if prefichero == "" or not prefichero.startswith("Backup"):
			return '', borra
		fichero = os.path.join(bkp_folder,prefichero+".zip")
	else:
		fichero = os.path.join(bkp_folder,"BackupKodi"+strftime("(%d-%m-%y-%H%M)")+".zip")
	backup = xbmcgui.DialogProgress()
	backup.create("Torrentin","Salvando directorios de Kodi.")
	if xbmcgui.Dialog().yesno("Torrentin" , "[COLOR yellow]Antes de hacer el Backup se pueden borrar los[/COLOR]",
                                                                      "[COLOR yellow]directorios innecesarios (Textures y Packages)[/COLOR]",
                                                                      "[COLOR lime]Pulsa Si para borrarlos o No para copiarlos.[/COLOR]"):
		backup.update(10,"","Espera, No Canceles.","Borrando temporales, esto puede tardar...")
		borra = True
		tempdel()
		xbmc.sleep(500)
	backup.update(20,"","Espera, No Canceles.","Comprimiendo addons, esto puede tardar...")
	zip_dir(xbmc.translatePath(os.path.join('special://home','addons')), fichero,"w")
	backup.update(70,"","Espera, No Canceles.","Comprimiendo media, ya queda poco...")
	zip_dir(xbmc.translatePath(os.path.join('special://home','media')), fichero,"a")
	backup.update(75,"","Espera, No Canceles.","Comprimiendo system, ya queda poco...")
	zip_dir(xbmc.translatePath(os.path.join('special://home','system')), fichero,"a")
	backup.update(80,"","Espera, No Canceles.","Comprimiendo userdata, terminando...")
	zip_dir(xbmc.translatePath(os.path.join('special://home','userdata')), fichero,"a")
	backup.close()
	return fichero, borra

def restorekodi(bkp_folder):
	if not os.path.isdir(bkp_folder):
		xbmcgui.Dialog().ok("Torrentin" , "Las copias de seguridad usan el directorio",
                                                                  "principal de Torrentin si no se configura uno,",
                                                                  "el directorio configurado no se encuentra.")
		return ''
	backups = []
	dirList=os.listdir( bkp_folder )
	for fname in dirList:
		if os.path.isdir(os.path.join( bkp_folder , fname )): continue
		if fname.endswith('.zip') and fname.startswith("Backup"):
			backups.append(fname)
	if len(backups)==0:
		xbmcgui.Dialog().ok("Torrentin" , "No se encuentra ningun fichero de copia",
                                                                 "de seguridad en el directorio principal.")
		return ''
	seleccion = xbmcgui.Dialog().select("Selecciona un fichero de Backup" , backups)
	if seleccion == -1: return ""
	fichero_seleccionado = backups[seleccion]
	if not fichero_seleccionado.startswith("BackupKodi("):
		if not xbmcgui.Dialog().yesno("Torrentin" , "El fichero seleccionado no tiene el nombre",
                                                                                 "standard de copia de seguridad creado por",
                                                                                 "Torrentin, seguro que quieres restaurarlo?","Abandonar","Continuar"):
			return ''
	fichero = os.path.join(bkp_folder,fichero_seleccionado)
	if os.path.isfile(fichero):
		dirkodi = xbmc.translatePath('special://home')
		backup = zipfile.ZipFile(fichero, 'r')
		backup.extractall(dirkodi)
	else:
		xbmcgui.Dialog().ok("Torrentin" , "Fichero de copia de seguridad no encontrado.",
                                                                 "Para restaurar un backup hay que crearlo antes.")
		return ''
	return fichero

def tempdel():
	import shutil
	if xbmc.getCondVisibility('system.platform.android'):
		if os.path.isfile(xbmc.translatePath(os.path.join('special://home','userdata','Database','Textures13.db'))):
			try: os.remove(xbmc.translatePath(os.path.join('special://home','userdata','Database','Textures13.db')))
			except: pass
		if os.path.isdir(xbmc.translatePath(os.path.join('special://home','temp'))):
			try: shutil.rmtree(xbmc.translatePath(os.path.join('special://home','temp')))
			except: pass
	if os.path.isdir(xbmc.translatePath(os.path.join('special://home','userdata','Thumbnails'))):
		try: shutil.rmtree(xbmc.translatePath(os.path.join('special://home','userdata','Thumbnails')))
		except: pass
	if os.path.isdir(xbmc.translatePath(os.path.join('special://home','addons','packages'))):
		try: shutil.rmtree(xbmc.translatePath(os.path.join('special://home','addons','packages')))
		except: pass
	xbmc.sleep(10000)

def chklst():
	list_folder=__addon__.getSetting('torrent_path')
	listas  = []
	if not list_folder: return listas
	try:
		dirList=os.listdir( list_folder )
		for fname in dirList:
			if os.path.isdir(os.path.join( list_folder , fname )): continue
			if fname.endswith('.m3u'):
				listas.append(fname)
	except: pass
	return listas

def latin1_to_ascii (unicrap):
    xlate={0xc0:'A', 0xc1:'A', 0xc2:'A', 0xc3:'A', 0xc4:'A', 0xc5:'A',
        0xc6:'Ae', 0xc7:'C',
        0xc8:'E', 0xc9:'E', 0xca:'E', 0xcb:'E',
        0xcc:'I', 0xcd:'I', 0xce:'I', 0xcf:'I',
        0xd0:'Th', 0xd1:'N',
        0xd2:'O', 0xd3:'O', 0xd4:'O', 0xd5:'O', 0xd6:'O', 0xd8:'O',
        0xd9:'U', 0xda:'U', 0xdb:'U', 0xdc:'U',
        0xdd:'Y', 0xde:'th', 0xdf:'ss',
        0xe0:'a', 0xe1:'a', 0xe2:'a', 0xe3:'a', 0xe4:'a', 0xe5:'a',
        0xe6:'ae', 0xe7:'c',
        0xe8:'e', 0xe9:'e', 0xea:'e', 0xeb:'e',
        0xec:'i', 0xed:'i', 0xee:'i', 0xef:'i',
        0xf0:'th', 0xf1:'n',
        0xf2:'o', 0xf3:'o', 0xf4:'o', 0xf5:'o', 0xf6:'o', 0xf8:'o',
        0xf9:'u', 0xfa:'u', 0xfb:'u', 0xfc:'u',
        0xfd:'y', 0xfe:'th', 0xff:'y',
        0xa1:'!', 0xa2:'{cent}', 0xa3:'{pound}', 0xa4:'{currency}',
        0xa5:'{yen}', 0xa6:'|', 0xa7:'{section}', 0xa8:'{umlaut}',
        0xa9:'{C}', 0xaa:'{a}', 0xab:'<<', 0xac:'{not}',
        0xad:'-', 0xae:'{R}', 0xaf:'_', 0xb0:'{degrees}',
        0xb1:'{+/-}', 0xb2:'{2}', 0xb3:'{3}', 0xb4:"'",
        0xb5:'{micro}', 0xb6:'{paragraph}', 0xb7:'*', 0xb8:'{cedilla}',
        0xb9:'{]}', 0xba:'{o}', 0xbb:'>>', 
        0xbc:'{1/4}', 0xbd:'{1/2}', 0xbe:'{3/4}', 0xbf:'-',
        0xd7:'-', 0xf7:'-'
        }

    r = ''
    for i in unicrap:
        if xlate.has_key(ord(i)):
            r += xlate[ord(i)]
        elif ord(i) >= 0x80:
            pass
        else:
            r += str(i)
    return r.replace(":","")

def zip_dir(path_dir, path_file_zip,mode):
    import contextlib
    with contextlib.closing(zipfile.ZipFile(path_file_zip, mode, zipfile.ZIP_DEFLATED)) as zip_file:
        try:
            for root, dirs, files in os.walk(path_dir):
                for file_or_dir in files + dirs:
                    if not file_or_dir.endswith(".pyo"):
                        zip_file.write(os.path.join(root, file_or_dir),os.path.relpath(os.path.join(root, file_or_dir),os.path.join(path_dir, os.path.pardir)))
        except:
            xbmcgui.Dialog().ok("Torrentin" , "Se ha producido un error al comprimir los ficheros","la copia de seguridad no se ha completado.")
            pass

def StripTags(text):
     finished = 0
     while not finished:
         finished = 1
         start = text.find("[")
         if start >= 0:
             stop = text[start:].find("]")
             if stop >= 0:
                 text = text[:start] + text[start+stop+1:]
                 finished = 0
     text = StripTags2(text)
     return text.strip()

def StripTags2(text):
     finished = 0
     while not finished:
         finished = 1
         start = text.find("(")
         if start >= 0:
             stop = text[start:].find(")")
             if stop >= 0:
                 text = text[:start] + text[start+stop+1:]
                 finished = 0
     return text.strip(".")

def ispelisfork(addon):
	if addon in ["pelisalacarta","alfa","mitvspain","felisalagarta"]: return True
	else: return False
   
def chkpchaddon(forkname):
	version = chkaddon(forkname)
	if version == "42": patchedfile = "platformtools"
	else: patchedfile = "xbmctools"
	origen = os.path.join(addonspath,forkname,"platformcode",patchedfile+".py.bkp")
	if os.path.isfile(origen):
		return 1
	else: return 0

def chkaddon(forkname):
	try:
		f = open(os.path.join(addonspath,forkname,"addon.xml"), 'r')
		AddOnId=f.read()
		f.close
	except:
		return "0"
	if forkname == "plugin.video.pelisalacarta":
		if '    version="4.1.' in AddOnId: return "41"
		elif '    version="4.0.' in AddOnId: return "40"
	return "42"

def pchaddon(tipo,forkname):
	version = chkaddon(forkname)
	if version == "42": patchedfile = "platformtools"
	elif version == "41": patchedfile = "xbmctools"
	else: return 3 , ""
	
	origen = os.path.join(addonspath,forkname,"platformcode",patchedfile+".py")
	destino = os.path.join(addonspath,forkname,"platformcode",patchedfile+".py.pch")
	backup = os.path.join(addonspath,forkname,"platformcode",patchedfile+".py.bkp")
	parcheado = False
	try:
		fo = open(origen,"r")
		fd = open(destino,"w")
	except: return 0 , ""
	line = fo.readline()
	fd.writelines('# -*- coding: utf-8 -*-'+'\n'+'# Parcheado por Torrentin'+'\n')
	for line in fo:
		if line.startswith('# Parcheado por Torrentin'):
			parcheado = True
			break
		fd.writelines(line)
		if tipo == 2:
			if line.startswith('    if puedes:'):
				fd.writelines('        if item.server == "torrent":'+'\n')
				if version == "42":
					fd.writelines('            xbmc.executebuiltin("XBMC.RunPlugin(" + "plugin://plugin.video.torrentin/?uri=%s&image=%s" % (urllib.quote_plus(item.url) , urllib.quote_plus(item.thumbnail) ) + ")")'+'\n'+'            return opciones, video_urls, seleccion, True'+'\n')
				elif version == "41":
					fd.writelines('            xbmc.executebuiltin("XBMC.RunPlugin(" + "plugin://plugin.video.torrentin/?uri=%s&image=%s" % (urllib.quote_plus(item.url) , urllib.quote_plus(item.thumbnail) ) + ")")'+'\n'+'            return'+'\n')
		elif tipo == 1:
			if version == "42":
				if line.startswith('        mediaurl = urllib.quote_plus(item.url)'):
					fd.writelines('        if "torrentin" in torrent_options[seleccion][1]: xbmc.executebuiltin( "PlayMedia(" + torrent_options[seleccion][1] % mediaurl + urllib.quote_plus( item.thumbnail )+")" )' + '\n        else:')
			elif version == "41":
				if line.startswith('            mediaurl = urllib.quote_plus(item.url)'):
					fd.writelines('            if "torrentin" in torrent_options[seleccion][1]: xbmc.executebuiltin( "PlayMedia(" + torrent_options[seleccion][1] % mediaurl + urllib.quote_plus( item.thumbnail )+")" )' + '\n            else:')
	fo.close()
	fd.close()
	if not parcheado: #No estaba
		if os.path.isfile(origen): xbmcvfs.copy(origen , backup)
		if os.path.isfile(destino): xbmcvfs.copy(destino , origen)
		if os.path.isfile(destino): os.remove(destino)
		addconfig(__scriptid__,forkname)
		return 1, txtmd5(origen)
	else: #Si estaba
		if os.path.isfile(backup): xbmcvfs.copy(backup , origen)
		if os.path.isfile(backup): os.remove(backup)
		if os.path.isfile(destino): os.remove(destino)
		return 2 , ""

def chkpchplexus():
	destinoace = os.path.join(addonspath,"program.plexus","resources","plexus","acestream.py")
	if os.path.isfile(destinoace):
		md5sum = txtmd5(destinoace)
		if md5sum == "a222c9f91c1e83328156a5a468586334" or md5sum == "7c04391ab3b95b8bfa12d0f147e49f94":
			return True
		else: return False

def pchplexus():
	md5sum = ""
	try:
		f = open(os.path.join(addonspath,"program.plexus","addon.xml"), 'r')
		AddOnId=f.read()
		f.close
	except:
		return False , md5sum
	if 'version="0.1.4"' in AddOnId:
		destino = os.path.join(addonspath,"program.plexus","resources","settings.xml")
		if os.path.isfile(destino):
			if not xbmcvfs.copy(os.path.join(__cwd__ , "resources" , "parches" , "plexus" , "settings.xml") , destino) : return False , md5sum
		else: return False , md5sum
		destino = os.path.join(addonspath,"program.plexus","resources","plexus","acestream.py")
		if os.path.isfile(destino):
			if not xbmcvfs.copy(os.path.join(__cwd__ , "resources" , "parches" , "plexus" , "acestream.py") , destino) : return False , md5sum
			else: md5sum = txtmd5(destino) # a222c9f91c1e83328156a5a468586334
		else: return False , md5sum
		destino = os.path.join(addonspath,"program.plexus","resources","plexus","acecore.py")
		if os.path.isfile(destino):
			if not xbmcvfs.copy(os.path.join(__cwd__ , "resources" , "parches" , "plexus" , "acecore.py") , destino) : return False , md5sum
	elif 'version="0.1.6.a"' in AddOnId or 'version="0.1.7"' in AddOnId:
		destino = os.path.join(addonspath,"program.plexus","resources","settings.xml")
		if os.path.isfile(destino):
			if not xbmcvfs.copy(os.path.join(__cwd__ , "resources" , "parches" , "plexus" , "016a" , "settings.xml") , destino) : return False , md5sum
		else: return False , md5sum
		destino = os.path.join(addonspath,"program.plexus","resources","plexus","acestream.py")
		if os.path.isfile(destino):
			if not xbmcvfs.copy(os.path.join(__cwd__ , "resources" , "parches" , "plexus" , "016a" , "acestream.py") , destino) : return False , md5sum
			else: md5sum = txtmd5(destino)
		else: return False , md5sum
	else: return False , md5sum
	return True  , md5sum

def chkps():
	destinoace = os.path.join(addonspath,"plugin.video.plexus-streams","resources","core","acestream.py")
	if os.path.isfile(destinoace):
		md5sum = txtmd5(destinoace)
		if md5sum == "5e06800233f5d49fa2e11353ef33533f":
			return 0
		elif md5sum == "63267830d43361a408e8b34695cbb073":
			return 1
	else: return 0
	
def pchplexusstreams():
	proceso = 0
	proceso2 = 0
	destinoset = os.path.join(addonspath,"plugin.video.plexus-streams","resources","settings.xml")
	if os.path.isfile(destinoset):
		md5sum = txtmd5(destinoset)
		if md5sum == "d9ff4538382826cb676f83fad177d8a9":
			proceso = 1
		elif md5sum == "bde9fe5ba3d7d0159f0c5b127a5e0181":
			proceso = 2
		else: proceso = 3
	else: proceso = 0

	destinoace = os.path.join(addonspath,"plugin.video.plexus-streams","resources","core","acestream.py")
	if os.path.isfile(destinoace):
		md5sum = txtmd5(destinoace)
		if md5sum == "5e06800233f5d49fa2e11353ef33533f":
			proceso2 = 1
		elif md5sum == "63267830d43361a408e8b34695cbb073":
			proceso = 2
		else: proceso = 3
	else: proceso = 0

	if proceso == 1 and proceso2 == 1:
		if not xbmcvfs.copy(os.path.join(__cwd__ , "resources" , "parches" , "plexus-streams" , "settings.xml") , destinoset) : return 0
		if not xbmcvfs.copy(os.path.join(__cwd__ , "resources" , "parches" , "plexus-streams" , "acestream.py") , destinoace) : return 0
		return proceso
	else: return proceso

#orig settings.xml  d9ff4538382826cb676f83fad177d8a9
#orig acestream.py  5e06800233f5d49fa2e11353ef33533f
#patched settings.xml  bde9fe5ba3d7d0159f0c5b127a5e0181
#patched acestream.py  63267830d43361a408e8b34695cbb073

def pchkmedia():
	md5sum = ""
	try:
		KmediaDir = "plugin.video.kmediatorrent"
		f = open(os.path.join(addonspath,KmediaDir,"addon.xml"), 'r')
		AddOnId=f.read()
		f.close
	except:
		try:
			KmediaDir = "plugin.video.kmediatorrent-2.3.7"
			f = open(os.path.join(addonspath,KmediaDir,"addon.xml"), 'r')
			AddOnId=f.read()
			f.close
		except:
			return False , md5sum
	#if AddOnId == "" : return False , md5sum

	destinoplayer = os.path.join(addonspath,KmediaDir,"resources","site-packages","kmediatorrent","player.py")
	if os.path.isfile(destinoplayer):
		md5sum = txtmd5(destinoplayer)
		if md5sum == "454d4618b8628aecf66c0bb7bf8d3662":
			return False , "1"

	if not 'version="2.3.7"' in AddOnId: return False , md5sum

	destino = os.path.join(addonspath,KmediaDir,"resources","settings.xml")
	if os.path.isfile(destino):
		if not xbmcvfs.copy(os.path.join(__cwd__ , "resources" , "parches" , "kmediatorrent" , "settings.xml") , destino) : return False , md5sum
	else: return False , md5sum

	#destinoplayer = os.path.join(addonspath,KmediaDir,"resources","site-packages","kmediatorrent","player.py")
	if os.path.isfile(destinoplayer):
		if not xbmcvfs.copy(os.path.join(__cwd__ , "resources" , "parches" , "kmediatorrent" , "player.py") , destinoplayer) : return False , md5sum
		else: md5sum = txtmd5(destinoplayer)

	else: return False , md5sum
	return True , md5sum

def chkpchkmedia():
	if os.path.isfile(os.path.join(addonspath,"plugin.video.kmediatorrent","resources","site-packages","kmediatorrent","player.py")):
		if txtmd5(os.path.join(addonspath,"plugin.video.kmediatorrent","resources","site-packages","kmediatorrent","player.py")) == "454d4618b8628aecf66c0bb7bf8d3662":
			return True
	elif os.path.isfile(os.path.join(addonspath,"plugin.video.kmediatorrent-2.3.7","resources","site-packages","kmediatorrent","player.py")):
		if txtmd5(os.path.join(addonspath,"plugin.video.kmediatorrent-2.3.7","resources","site-packages","kmediatorrent","player.py")) == "454d4618b8628aecf66c0bb7bf8d3662":
			return True
	else:
		return False

def addconfig(pwd,fork):
	origen=__addon__.getSetting('prog')
	destino = os.path.join(addonspath, fork ,"channels")
	if os.path.isdir(origen) and os.path.isdir(destino):
		if os.path.isfile(os.path.join(origen,'config.zip')):
			zipfile.ZipFile(os.path.join(origen,'config.zip'), 'r').extractall(destino,pwd=pwd)
			xbmc.executebuiltin('XBMC.Notification('+fork+' , "All Ok.", 1500, ")')
			xbmc.sleep(2000)
			return
		dirList=os.listdir( origen )
		list=[]
		for fname in dirList:
			if fname.endswith("-config.zip"):
				list.append(fname)
		if len(list)!=0:
			s = xbmcgui.Dialog().select("Select config for " + fork, list)
			if s != -1:
				zipfile.ZipFile(os.path.join(origen,list[s]), 'r').extractall(destino,pwd=pwd)
				xbmc.executebuiltin('XBMC.Notification('+fork+' , "All Ok.", 1500, ")')
				xbmc.sleep(2000)

def recursive_overwrite(src, dest, ignore=None):
    import shutil
    if os.path.isdir(src):
        if not os.path.isdir(dest):
            os.makedirs(dest)
        files = os.listdir(src)
        if ignore is not None:
            ignored = ignore(src, files)
        else:
            ignored = set()
        for f in files:
            if f not in ignored:
                recursive_overwrite(os.path.join(src, f), 
                                    os.path.join(dest, f), 
                                    ignore)
    else:
        shutil.copyfile(src, dest)

def txtmd5(file):
    import hashlib
    md5 = hashlib.md5()
    f = open(file)
    for line in f:
        md5.update(line)
    f.close()
    #print "TORRENTIN_MD5: "+ file + "  " + md5.hexdigest()
    return md5.hexdigest()

def convert_size(size_bytes):
   import math
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

def get_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

#hashlib.md5(open(file,'rb').read()).hexdigest()

def forceclose():
    if xbmc.getCondVisibility('system.platform.android'):
        try: os._exit(1)
        except: pass
        try: os.system('adb shell am force-stop org.xbmc.kodi')
        except: pass
        try: os.system('adb shell am force-stop org.kodi')
        except: pass
        try: os.system('adb shell am force-stop org.xbmc.xbmc')
        except: pass
        try: os.system('adb shell am force-stop org.xbmc')
        except: pass     
        try: os.system('adb shell am force-stop com.semperpax.spmc')
        except: pass
        try: os.system('adb shell am force-stop com.spmc')
        except: pass
        try: os.system('adb shell am force-stop com.semperpax.spmc16')
        except: pass
        try: os.system('adb shell am force-stop com.spmc16')
        except: pass
        try: os.system('adb shell am force-stop org.xbmc.ftmc')
        except: pass

    elif xbmc.getCondVisibility('system.platform.windows'):
        try: os._exit(1)
        except: pass
        try:
            os.system('@ECHO off')
            os.system('tskill XBMC.exe')
        except: pass
        try:
            os.system('@ECHO off')
            os.system('tskill Kodi.exe')
        except: pass
        try:
            os.system('@ECHO off')
            os.system('TASKKILL /im Kodi.exe /f')
        except: pass
        try:
            os.system('@ECHO off')
            os.system('TASKKILL /im XBMC.exe /f')
        except: pass
                
    elif xbmc.getCondVisibility('system.platform.linux'):
        try: os._exit(1)
        except: pass
        try: os.system('killall XBMC')
        except: pass
        try: os.system('killall Kodi')
        except: pass
        try: os.system('killall -9 xbmc.bin')
        except: pass
        try: os.system('killall -9 kodi.bin')
        except: pass
        
    elif xbmc.getCondVisibility('system.platform.osx'):
        try: os._exit(1)
        except: pass
        try: os.system('killall -9 XBMC')
        except: pass
        try: os.system('killall -9 Kodi')
        except: pass

    else:
        try: os._exit(1)
        except: pass
        try: os.system('killall AppleTV')
        except: pass
        try: os.system('sudo initctl stop kodi')
        except: pass
        try: os.system('sudo initctl stop xbmc')
        except: pass
        
