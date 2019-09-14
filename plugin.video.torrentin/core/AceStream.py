#!/usr/bin/python
# -*- coding: utf-8 -*-
# Originally coded by Nuismons (many thanks)
# Modified by ciberus for Torrentin Add-On
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

import urllib
import re
import sys
import os
import socket
import threading
import time
import random
import json
import hashlib

import xbmcgui
import xbmc
import xbmcvfs
import xbmcplugin
import xbmcaddon

__addon__ = xbmcaddon.Addon( id = 'plugin.video.torrentin' )
__cwd__        = __addon__.getAddonInfo('path')
addon_icon = os.path.join(__cwd__ , "icon.png")
#addon_icon = os.path.join(__cwd__ ,"resources","images","acestreamlogo.png")
aceport=int(__addon__.getSetting("portace"))
server_ip=__addon__.getSetting("iplocal")
if __addon__.getSetting("acelog")=='true': alog=True
else: alog=False
#if  __addon__.getSetting("save")=='true' and __addon__.getSetting("aceold")=="0": save=True
if  __addon__.getSetting("save")=='true': save=True
else: save=False

if (sys.platform == 'win32') or (sys.platform == 'win64'): pwin=True
else: pwin=False

# if  __addon__.getSetting("aceavisos")=='true': aceavisos = True
# else: aceavisos = False

showstats =  int(__addon__.getSetting("estadisticas"))

def show_Msg(heading, message, time = 3000, pic = addon_icon):
    try: xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "%s")' % (heading, message, time, pic))
    except: pass

class Logger():
    def __init__(self,Name):
        self.name=Name
        self.link=None
    def out(self,txt):
        if alog:
            print "%s:%s"%(self.name,txt)

class _TSPlayer(xbmc.Player):
    def __init__( self):
        self.log=Logger("TSPlayer")
        self.log.out('init')
        self.active=True
        self.link=None
        self.vod=True
        self.duration=None
        self.coms=[]
        self.pausado=False

    def onPlayBackPaused( self ):
        self.pausado=True
        self.log.out('paused')

#    def onPlayBackSeek( self ,time,offset):
#        xbmc.sleep(600)
#        self.pausado=True
#        self.log.out("Seek")

    def onPlayBackStarted( self ):
        #xbmc.executebuiltin('XBMC.ActivateWindow("fullscreenvideo")')
        self.log.out('started')
        if self.vod:
            try: 
                self.duration= int(xbmc.Player().getTotalTime()*1000)
                comm='DUR '+self.link.replace('\r','').replace('\n','')+' '+str(self.duration)
                self.coms.append(comm)
            except: pass
        
        comm='PLAYBACK '+self.link.replace('\r','').replace('\n','')+' 0'
        self.coms.append(comm)

    def onPlayBackResumed(self):
        self.pausado=False
        self.log.out("play resume")
        
    def onPlayBackEnded(self):
        self.log.out("play ended")
        self.active=False
        comm='PLAYBACK '+self.link.replace('\r','').replace('\n','')+' 100'
        self.coms.append(comm)

    def onPlayBackStopped(self):
        self.log.out("play stop")
        self.active=False

    def __del__(self):
        self.log.out('deleted')
    
class TSengine():
    def __init__(self):
        if xbmc.Player().isPlaying(): xbmc.Player().stop()
        self.log=Logger("TSEngine")
        self.push=Logger('OUT')
        self.alive=True
        self.progress = xbmcgui.DialogProgress()
        self.player=None
        self.files={}
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(3)
        self.progress.create("Torrentin - Cliente AceStream","Inicializando...")
        self.tsserv =None
        self.conn=False
        self.title=None
        self.filename=None
        self.mode=None
        self.url=None
        self.local=False
        self.saved=False
        self.pos=[25,50,75,100]
        self.save=False
        self.thumb=None
        l=False
        while xbmc.Player().isPlaying(): 
            l=True
            if xbmc.abortRequested:
                self.log.out("XBMC is shutting down")
                return False
            if self.progress.iscanceled():
                return False
            xbmc.sleep(300)
        
        #__addon__.setSetting('active','1')
        if l: xbmc.sleep(500)

    def ts_init(self):
        self.tsserv = TSServ(self._sock)
        self.tsserv.start()
        comm="HELLOBG"
        self.TSpush(comm)
        self.progress.update(0,"Esperando respuesta"," ")
        while not self.tsserv.version:
            if xbmc.abortRequested:
                self.log.out("XBMC is shutting down")
                return False
            if self.progress.iscanceled():
                return False
            time.sleep(1)
        ready='READY'
        if self.tsserv.key:
            sha1 = hashlib.sha1()
            pkey=self.tsserv.pkey
            sha1.update(self.tsserv.key+pkey)
            key=sha1.hexdigest()
            pk=pkey.split('-')[0]
            key="%s-%s"%(pk,key)
            ready='READY key=%s'% key
        if self.progress.iscanceled():
            self.err=1
            return False	
        self.TSpush(ready)
        return True
    
    def sm(self,msg):
        show_Msg('          ---===[ AceStream ]===---',msg)
    
    def connect(self):
        server_ip='127.0.0.1'
        servip=__addon__.getSetting('iplocal')
        aceport=int(__addon__.getSetting('portace'))
        self.log.out('Trying to connect')
        self.progress.update(0,'Intentando conectar',' ')
        if pwin:
            res=self.startWin()
            aceport=self.getWinPort()
            if not aceport: 
                res=self.startWin()
                if not res: return False
        else:
            self.log.out('try to connect to linux ace')
            self.log.out('Connecting to %s:%s'%(servip,aceport))
            try:
                self._sock.connect((servip, aceport))
                self.log.out('Connected to %s:%s'%(servip,aceport))
                return True
            except:
                res=self.startLin()
                if not res: return False
        i=30
        while (i>1):
            self.progress.update(0,'Esperando al motor acestream','%s'%i)
            try:
                if pwin: aceport=self.getWinPort()
                self._sock.connect((servip, aceport))
                self.log.out('Connected to %s:%s'%(servip,aceport))     
                i=0
                return True
            except:
                self.log.out('Failed to connect to %s:%s'%(servip,aceport))   
            if self.progress.iscanceled():
                return False
                break
            i=i-1
            xbmc.sleep(1000)
        self.sm('      No se puede conectar')
        return False

    def startLin(self):

        if not __addon__.getSetting("aceaviso"):
            __addon__.setSetting("aceaviso","1")
        aceaviso = __addon__.getSetting("aceaviso")
        if int(aceaviso) <4:
            if aceaviso == "1": contador = "Primera notificación"
            elif aceaviso == "2": contador = "Segunda notificación" 
            elif aceaviso == "3": contador = "Tercera y última notificación"
            xbmcgui.Dialog().ok("Torrentin ("+contador+")" , "La App AceStream no está en memoria, se intentará ejecutar","[COLOR yellow]>>> Cuando arranque dale a escape para volver al Kodi <<<[/COLOR]","Si no se ejecuta comprueba la versión que tienes instalada\ny cámbialo en la Configuración -> AceStream -> Versión.")
            __addon__.setSetting("aceaviso",   str(int(aceaviso)+1) )

        self.log.out('try to start Lin engine;;')
        import subprocess
        try:
            proc = subprocess.Popen(["acestreamengine","--client-console"])
        except:
            try:  proc = subprocess.Popen('acestreamengine-client-console')
            except: 
                try: 
                    subprocess.Popen(__addon__.getSetting('prog'))
                except:
                    try:
                        if __addon__.getSetting("aceold")=="0":  xbmc.executebuiltin('XBMC.StartAndroidActivity("org.acestream.engine")')
                        else: xbmc.executebuiltin('XBMC.StartAndroidActivity("org.acestream.media")')
                    except:
                        self.sm('          No Instalado')
                        self.log.out('Not Installed')
                        self.progress.update(0,'El motor AceStream no esta instalado','o no es la version configurada.')
                        return False
        self.log.out('Engine starting')
        return True
    
    def startWin(self):
        try:
            import _winreg
            t = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, 'Software\\TorrentStream')
            needed_value =  _winreg.QueryValueEx(t , 'EnginePath')[0]
            path= needed_value.replace('tsengine.exe','')
            self.log.out("Try to start %s"%needed_value)
            self.progress.update(0,'Iniciando el motor AceStream','')
            os.startfile(needed_value)
            self.log.out('TSEngine starting')
        except: 
            try:
                import _winreg
                t = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, 'Software\AceStream')
                needed_value =  _winreg.QueryValueEx(t , 'EnginePath')[0]
                path= needed_value.replace('ace_engine.exe','')
                self.log.out("Try to start %s"%needed_value)
                self.progress.update(0,'Iniciando el motor AceStream','')
                os.startfile(needed_value)
                self.log.out('ASEngine starting')
            except:
                self.sm('          No instalado')
                self.log.out('Not Installed')
                self.progress.update(0,'El motor AceStream no esta instalado','')
                return False
        return True

    def getWinPort(self):
        try:
            import _winreg
            t = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, 'Software\\TorrentStream')
            needed_value =  _winreg.QueryValueEx(t , 'EnginePath')[0]
            path= needed_value.replace('tsengine.exe','')
            pfile= os.path.join( path,'acestream.port')
            gf = open(pfile, 'r')
            aceport=int(gf.read())
        except: 
            try:
                import _winreg
                t = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, 'Software\\AceStream')
                needed_value =  _winreg.QueryValueEx(t , 'EnginePath')[0]
                path= needed_value.replace('ace_engine.exe','')
                pfile= os.path.join( path,'acestream.port')
                gf = open(pfile, 'r')
                aceport=int(gf.read())
            except:
                return False
        self.log.out('get aceport - %s'%aceport)
        return aceport

    def TSpush(self,command):
        self.push.out(command)
        try:
            self._sock.send(command+'\r\n')
        except: 
            self.push.out("!!!Error!!!")
    
    def get_link(self, index=0, title='', icon='', thumb=''):
#        if __addon__.getSetting('save')=='true' and __addon__.getSetting('folder') and __addon__.getSetting("aceold")=="0": save=True
        if __addon__.getSetting('save')=='true' and __addon__.getSetting('folder'): save=True
        else: save=False
        self.save=save
        self.title=title
        self.log.out("play")
        self.tsserv.ind=index
        self.progress.update(89,'Iniciando reproduccion','',self.title)
        for k,v in self.files.iteritems():
            if v==index: self.filename=urllib.unquote(k).replace('/','_').replace('\\','_')
        try:    
            avail=os.path.exists(self.filename.decode('utf-8'))
        except:
            try:
                avail=os.path.exists(self.filername)
                self.filename=self.filename.encode('utf-8')
            except: self.filename='temp.avi'
        self.log.out('Starting file:%s'%self.filename)
        
        if self.save and __addon__.getSetting('folder'):
            try: self.filename=os.path.join(__addon__.getSetting('folder'),self.filename)
            except: 
                try:
                    self.filename=os.path.join(__addon__.getSetting('folder').decode('utf-8'),self.filename)
                except:
                    self.filename=None
                    self.save=False
        
        try: self.log.out('Get filename to save:%s'%self.filename)
        except: self.log.out('Get filename to save:%s'%self.filename.encode('utf-8'))
        try: tt=os.path.exists(self.filename.decode('utf-8'))
        except: tt=os.path.exists(self.filename)
        if self.save and tt:
            self.progress.update(89,"El video ya esta descargado","Iniciando reproductor en modo local")
            xbmc.sleep(1500)
            self.local=True
            try: self.tsserv.got_url=self.filename.decode('utf-8')
            except: self.tsserv.got_url=self.filename
            self.active=True
            self.progress.close()
            return self.tsserv.got_url
        spons=''
        if self.mode!='PID': spons=' 0 0 0'
        comm='START '+self.mode+ ' ' + self.url + ' '+ str(index) + spons
        self.TSpush(comm)
        self.progress.update(89,'Reproduccion en espera','')
        while not self.tsserv.got_url and not self.progress.iscanceled() and not self.tsserv.err:
            self.progress.update(int(self.tsserv.proc),self.tsserv.label,self.tsserv.line)
            xbmc.sleep(200)
            if xbmc.abortRequested:
                self.log.out("XBMC is shutting down")
                break
        if self.tsserv.err: self.sm('    Fallo al cargar fichero')
        self.progress.update(100,'Iniciando reproduccion','')
        
        xbmc.sleep(500)
        if self.tsserv.event and self.save:
            if not tt:
#                self.saveposter()
                savecarat = self.saveposter()
                if showstats >= 1 and savecarat: self.sm('  Caratula descargada y guardada.')
                self.progress.update(0,"Guardando: "+self.title+"\n\nEl archivo esta completado en el cache del AceStream.\n\nSe seguira guardando hasta el final aunque cancele.\n\nEl boton cancelar solo cancela la reproduccion,\n\nque se iniciara cuando termine la grabacion.\n\nGuardando archivo, espere...."," ")
                try: comm='SAVE %s path=%s'%(self.tsserv.event[0]+' '+self.tsserv.event[1],urllib.quote(self.filename))
                except: comm='SAVE %s path=%s'%(self.tsserv.event[0]+' '+self.tsserv.event[1],urllib.quote(self.filename.encode('utf-8')))
                self.TSpush(comm)
                self.tsserv.event=None
                succ=True
                
                while not tt and not self.progress.iscanceled():
                    if xbmc.abortRequested or self.progress.iscanceled():
                        self.log.out("XBMC is shutting down")
                        succ=False
                        break
                    xbmc.sleep(200)
                    try: tt=os.path.exists(self.filename.decode('utf-8'))
                    except: tt=os.path.exists(self.filename)
                    
                if not succ: return False
                xbmc.sleep(1000)
            else: self.local=True
            try: self.tsserv.got_url=self.filename.decode('utf-8')
            except: self.tsserv.got_url=self.filename
            self.local=True
        self.active=True
        self.progress.close()
        return self.tsserv.got_url
     
    def play_url_ind(self, index=0, title='', icon='', thumb=''):
        self.log.out('play')
        self.player=_TSPlayer()
        if thumb == "": thumb = addon_icon
        self.thumb = thumb
        lnk=self.get_link(index,title,icon,thumb)
        if not lnk: return False
        self.player.link=lnk
        self.player.vod=True
        if self.progress:self.progress.close()
        item = xbmcgui.ListItem(title,iconImage="", thumbnailImage=self.thumb,path=lnk)
        #xbmcplugin.setResolvedUrl(int(sys.argv[1]),True,item)
        if self.local: 
            xbmcvfs.rename(lnk,lnk)
            xbmc.Player().play(lnk,item)
        else: 
            self.player.play(lnk,item)
            while self.player.active and not self.local: 
                self.loop()
                xbmc.sleep(300)
                if xbmc.abortRequested:
                    self.log.out("XBMC is shutting down")
                    break
            self.log.out('ended play')
      
    def loop(self):
        if self.local: return
        if showstats >= 1:
            if ( (self.player.pausado and (showstats == 2 or showstats ==4)) or (xbmc.getCondVisibility('Window.IsActive(videoosd)') and (showstats == 3 or showstats ==4)) ):
                show_Msg(self.tsserv.label,self.tsserv.line,1000)
                xbmc.sleep(700)
            elif self.player.pausado and showstats == 1:
                show_Msg(self.tsserv.label,self.tsserv.line,5000)
                self.player.pausado = False

        pos=self.pos
        if len(self.player.coms)>0:
            comm=self.player.coms[0]
            self.player.coms.remove(comm)
            self.TSpush(comm)
        if self.player.isPlaying():
            if self.player.getTotalTime()>0: cpos= int((1-(self.player.getTotalTime()-self.player.getTime())/self.player.getTotalTime())*100)
            else: cpos=0
            if cpos in pos: 
                pos.remove(cpos)
                comm='PLAYBACK '+self.player.link.replace('\r','').replace('\n','')+' %s'%cpos
                self.TSpush(comm)
        if self.tsserv.event and self.save:
            self.log.out('Try to save file in loop')
            try: comm='SAVE %s path=%s'%(self.tsserv.event[0]+' '+self.tsserv.event[1],urllib.quote(self.filename))
            except: comm='SAVE %s path=%s'%(self.tsserv.event[0]+' '+self.tsserv.event[1],urllib.quote(self.filename.encode('utf-8')))
            self.TSpush(comm)
            self.tsserv.event=None
            succ=True
            self.saved=True
            self.save=False
            savecarat = self.saveposter()

    def saveposter(self):
        if  __addon__.getSetting("saveposter")=="false": return False
        if self.thumb.startswith("http"):
            import torrents
            image_data = torrents.url_get(self.thumb)
            if image_data =="": return False
            if ".png" in self.thumb.lower(): ext=".png"
            elif ".gif" in self.thumb.lower(): ext=".gif"
            elif ".jpg" in self.thumb.lower(): ext= ".jpg"
            else: ext = ".img"
            try:
                f = open(self.filename.replace(".avi","").replace(".mp4","").replace("mkv","") + ext  , "wb+")
                f.write(image_data)
                f.close()
                return True
            except: return False
        else: return False

    def load_torrent(self, torrent, mode, host=server_ip, port=aceport ):
        self.mode=mode
        self.url=torrent
        if not self.connect(): 
            return False
        if not self.ts_init(): 
            self.sm('   Inicialización fallida')
            return False
        self.conn=True
        self.progress.update(0,"Descargando torrent","")
        if mode!='PID': spons=' 0 0 0'
        else: spons=''
        comm='LOADASYNC '+ str(random.randint(0, 0x7fffffff)) +' '+mode+' ' + torrent + spons
        self.TSpush(comm)
        while not self.tsserv.files and not self.progress.iscanceled():
            if xbmc.abortRequested:
                self.log.out("XBMC is shutting down")
                break
            if self.tsserv.err:
                self.log.out("Failed to load files")
                break
            xbmc.sleep(200)
        if self.progress.iscanceled(): 
            return False
        if not self.tsserv.files: 
            self.sm('    Fallo al cargar la lista de ficheros')
            return False
        self.filelist=self.tsserv.files
        self.file_count = self.tsserv.count
        self.files={}
        self.progress.update(89,'Cargando lista de ficheros','')
        if self.file_count>1:
            flist=json.loads(self.filelist)
            for list in flist['files']:
                self.files[urllib.unquote_plus(urllib.quote(list[0]))]=list[1]
        elif self.file_count==1:
            flist=json.loads(self.filelist)
            list=flist['files'][0]
            self.files[urllib.unquote_plus(urllib.quote(list[0]))]=list[1]
        self.progress.update(100,'Carga de datos completada','')
        return "Ok"

    def end(self):
        self.active=False
        comm='SHUTDOWN'
        if self.conn:self.TSpush(comm)
        self.log.out("Ending")
        try: self._sock.shutdown(socket.SHUT_WR)
        except: pass
        if self.tsserv: self.tsserv.active=False
        if self.tsserv: self.tsserv.join()
        self.log.out("end thread")
        self._sock.close()
        self.log.out("socket closed")
        if self.progress:self.progress.close()
        if showstats >= 3: self.sm("                           Detenido")

    def __del__(self):
        self.log.out('deleted')
        #__addon__.setSetting('active','0')
        
class TSServ(threading.Thread):
    def __init__(self,_socket):
        self.pkey='n51LvQoTlJzNGaFxseRK-uvnvX-sD4Vm5Axwmc4UcoD-jruxmKsuJaH0eVgE'
        threading.Thread.__init__(self)
        self.log=Logger("TSServer")
        self.inc=Logger('IN')
        self.log.out("init")
        self.sock=_socket
        self.daemon = True
        self.active = True
        self.err = False
        self.buffer=65020   #130040
        self.temp=""
        self.msg=None
        self.version=None
        self.fileslist=None
        self.files=None
        self.key=None
        self.count=None
        self.ind=None
        self.got_url=None
        self.event=None
        self.proc=0
        self.label=''
        self.line=''
        self.pause=False

    def run(self):
        while self.active and not self.err:
            try:
                self.last_received=self.sock.recv(self.buffer)
            except: self.last_received=''
            ind=self.last_received.find('\r\n')
            cnt=self.last_received.count('\r\n')
            if ind!=-1 and cnt==1:
                self.last_received=self.temp+self.last_received[:ind]
                self.temp=''
                self.exec_com()
            elif cnt>1:
                fcom=self.last_received
                ind=1
                while ind!=-1:
                    ind=fcom.find('\r\n')
                    self.last_received=fcom[:ind]
                    self.exec_com()
                    fcom=fcom[(ind+2):]
            elif ind==-1: 
                self.temp=self.temp+self.last_received
                self.last_received=None
        self.log.out('Daemon Dead')
                
    def exec_com(self):
        self.inc.out(self.last_received)
        line=self.last_received
        comm=self.last_received.split(' ')[0]
        params=self.last_received.split(' ')[1::]
        self.msg=line
        if comm=='HELLOTS':
            try: self.version=params[0].split('=')[1]
            except: self.version='1.0.6'
            try: 
                if params[2].split('=')[0]=='key': self.key=params[2].split('=')[1]
            except: 
                try: self.key=params[1].split('=')[1]
                except: self.key=None
        elif comm=='LOADRESP':
            fil = line
            ll= fil[fil.find('{'):len(fil)]
            self.fileslist=ll
            json_files=json.loads(self.fileslist)
            try:
                aa=json_files['infohash']
                if json_files['status']==2:
                    self.count=len(json_files['files'])
                if json_files['status']==1:
                    self.count=1
                if json_files['status']==0:
                    self.count=None
                self.files=self.fileslist.split('\n')[0]
                self.fileslist=None
                self.log.out("files:%s"%self.files) 
            except:
                self.count=None
                self.fileslist=None
                self.err=True
        elif comm=='EVENT':
            if self.last_received.split(' ')[1]=='cansave':
                event=self.last_received.split(' ')[2:4]
                ind= event[0].split('=')[1]
                if int(ind)==int(self.ind): self.event=event
            if self.last_received.split(' ')[1]=='getuserdata':
                self.sock.send('USERDATA [{"gender": 1}, {"age": 3}]\r\n')
        elif comm=='START' or comm=='PLAY': 
            servip=__addon__.getSetting('iplocal')
            self.got_url=self.last_received.split(' ')[1].replace('127.0.0.1',servip)
            self.log.out('Get Link:%s'%self.got_url)
            self.params=self.last_received.split(' ')[2:]
            if 'stream=1' in self.params: self.log.out('Live Stream')
            else: self.log.out('VOD Stream')
        elif comm=='RESUME': self.pause=0
        elif comm=='PAUSE': self.pause=1   
        if comm=="STATUS": self.showStats(line)   
        
    def showStats(self,params):
        params=params.split(' ')[1]
        ss=re.compile('main:[a-z]+',re.S)
        s1=re.findall(ss, params)[0]
        st=s1.split(':')[1]
        self.proc=0
        self.label=" "
        self.line=" "
        if st=='idle':
            self.label='Esperando'
        elif st=='starting':
            self.label='Iniciando'
        elif st=='err':
            self.label='Error del motor acestream'
            self.err="dl"
        elif st=='check': 
            self.label='Comprobando'
            self.proc=int(params.split(';')[1])
        elif st=='prebuf': 
            self.proc=int( params.split(';')[1] )+0.1
            self.label='Pre-Cargando'
            self.line='Semillas: %s - Velocidad: %s Kb/s'%(params.split(';')[8],params.split(';')[5])  
        elif st=='loading':
            self.label='Cargando' 
        elif st=='dl':
            self.label='Descargando  (' + params.split(';')[1] + "%) - S: " + params.split(';')[6]
            self.line = 'Vel.Sub: %s Kb/s - Vel.Baj: %s Kb/s'%( params.split(';')[5] , params.split(';')[3] )
        elif st=='buf':
            self.label='Cargando Buffer  (' + params.split(';')[1] + "%) - S: " + params.split(';')[8]
            self.line = 'Vel.Sub: %s Kb/s - Vel.Baj: %s Kb/s'%( params.split(';')[7] , params.split(';')[5] )

    def end(self):
        self.active = False
        self.daemon = False
        self.log.out('Daemon Fully Dead')
 
