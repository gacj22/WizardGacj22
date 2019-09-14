########################################################################################################
#
#	Merlin Auto Cleaner
#
#	By Merlin Project
#
#	August 2016
#
########################################################################################################




import xbmc, xbmcaddon, xbmcgui, xbmcplugin, os, sys, xbmcvfs, glob
import shutil
import urllib2,urllib
import re
import uservar
import time
from datetime import date, datetime, timedelta
try:    from sqlite3 import dbapi2 as database
except: from pysqlite2 import dbapi2 as database
from string import digits

ADDON_ID       = uservar.ADDON_ID
ADDONTITLE     = uservar.ADDONTITLE
ADDON          = xbmcaddon.Addon(ADDON_ID)
VERSION        = ADDON.getAddonInfo('version')
USER_AGENT     = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
DIALOG         = xbmcgui.Dialog()
DP             = xbmcgui.DialogProgress()
HOME           = xbmc.translatePath('special://home/')
LOG            = xbmc.translatePath('special://logpath/')
PROFILE        = xbmc.translatePath('special://profile/')
ADDONS         = os.path.join(HOME, 'addons')
USERDATA       = os.path.join(HOME, 'userdata')
PLUGIN         = os.path.join(ADDONS, ADDON_ID)
PACKAGES       = os.path.join(ADDONS, 'packages')
ADDONDATA      = os.path.join(USERDATA, 'addon_data', ADDON_ID)
ADVANCED       = os.path.join(USERDATA, 'advancedsettings.xml')
SOURCES        = os.path.join(USERDATA, 'sources.xml')
FAVOURITES     = os.path.join(USERDATA, 'favourites.xml')
PROFILES       = os.path.join(USERDATA, 'profiles.xml')
THUMBS         = os.path.join(USERDATA, 'Thumbnails')
DATABASE       = os.path.join(USERDATA, 'Database')
FANART         = os.path.join(PLUGIN, 'fanart.jpg')
ICON           = os.path.join(PLUGIN, 'icon.png')
WIZLOG         = os.path.join(ADDONDATA, 'wizard.log')

def getS(name):
	try: return ADDON.getSetting(name)
	except: return False

def setS(name, value):
	try: ADDON.setSetting(name, value)
	except: return False

def openS():
	ADDON.openSettings();

def clearS(type):
	trakt   = {'exodus':'', 'salts':'', 'saltshd':'', 'royalwe':'', 'velocity':'', 'velocity':'', 'specto':'', 'trakt':'', 'keeptrakt':'false', 'traktlastsave':'2016-01-01'}
	debrid  = {'exodus':'', 'specto':'', 'urlresolver':'', 'keepdebrid':'false', 'debridlastsave':'2016-01-01'}
	build   = {'buildname':'', 'buildversion':'', 'buildtheme':'', 'latestversion':'', 'lastbuildcheck':'2016-01-01'}
	install = {'installed':'false', 'extract':'', 'errors':''}
	if type == 'trakt':
		for set in trakt:
			setS(set, trakt[set])
	if type == 'debrid':
		for set in debrid:
			setS(set, debrid[set])
	elif type == 'build':
		for set in build:
			setS(set, build[set])
		for set in install:
			setS(set, install[set])
	elif type == 'install':
		for set in install:
			setS(set, install[set])


def TextBoxes(heading,announce):
	class TextBox():
		WINDOW=10147
		CONTROL_LABEL=1
		CONTROL_TEXTBOX=5
		def __init__(self,*args,**kwargs):
			xbmc.executebuiltin("ActivateWindow(%d)" % (self.WINDOW, )) # activate the text viewer window
			self.win=xbmcgui.Window(self.WINDOW) # get window
			xbmc.sleep(500) # give window time to initialize
			self.setControls()
		def setControls(self):
			self.win.getControl(self.CONTROL_LABEL).setLabel(heading) # set heading
			try: f=open(announce); text=f.read()
			except: text=announce
			self.win.getControl(self.CONTROL_TEXTBOX).setText(str(text))
			return
	TextBox()
	while xbmc.getCondVisibility('Window.IsVisible(10147)'):
		time.sleep(.5)

def LogNotify(title,message,times=4000,icon=ICON):
	xbmc.executebuiltin('XBMC.Notification(%s, %s, %s, %s)' % (title , message , times, icon))

 
def openURL(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', USER_AGENT)
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	return link


def removeFolder(path):
	log("Deleting Folder: %s" % path)
	try: shutil.rmtree(path,ignore_errors=True, onerror=None)
	except: return False

def removeFile(path):
	log("Deleting File: %s" % path)
	try:    os.remove(path)
	except: return False


def emptyfolder(folder):
	total = 0
	for root, dirs, files in os.walk(folder, topdown=True):
		dirs[:] = [d for d in dirs if d not in EXCLUDES]
		file_count = 0
		file_count += len(files) + len(dirs)
		if file_count == 0:
			shutil.rmtree(os.path.join(root))
			total += 1
			log("Empty Folder: %s" % root)
	return total

def log(log):
	xbmc.log("[%s]: %s" % (ADDONTITLE, log))
	if not os.path.exists(ADDONDATA): os.makedirs(ADDONDATA)
	if not os.path.exists(WIZLOG): f = open(WIZLOG, 'w'); f.close()
	with open(WIZLOG, 'r+') as f:
		line = "[%s %s] %s" % (datetime.now().date(), str(datetime.now().time())[:8], log)
		content = f.read()
		f.seek(0, 0)
		f.write(line.rstrip('\r\n') + '\n' + content)

def addonId(add):
	return xbmcaddon.Addon(id=add)

def addonInfo(add, info):
	addon = addonId(add)
	return addon.getAddonInfo(info)


def clearPackages(over=None):
	if os.path.exists(PACKAGES):
		try:	
			for root, dirs, files in os.walk(PACKAGES):
				file_count = 0
				file_count += len(files)
				# Count files and give option to delete
				if file_count > 0:
					if over: yes=1
					else: yes=DIALOG.yesno("Delete Package Cache Files", str(file_count) + " files found", "Do you want to delete them?", nolabel='No, Cancel',yeslabel='Yes, Remove')
					if yes:
						for f in files:	os.unlink(os.path.join(root, f))
						for d in dirs: shutil.rmtree(os.path.join(root, d))
						LogNotify(ADDONTITLE,'[COLOR aqua]Packages Purged:[/COLOR] [COLOR white]Success[/COLOR]!')
				else: LogNotify(ADDONTITLE,'[COLOR aqua]Packages:[/COLOR] [COLOR white]None Found![/COLOR]')
		except: LogNotify(ADDONTITLE,'[COLOR aqua]Packages:[/COLOR] [COLOR red]Error[/COLOR]!')
	else: LogNotify(ADDONTITLE,'[COLOR aqua]Packages:[/COLOR] [COLOR white]None Found![/COLOR]')

def clearCache():
	PROFILEADDONDATA = os.path.join(PROFILE,'addon_data')
	cachelist = [
		(PROFILEADDONDATA),
		(ADDONDATA),
		(os.path.join(HOME,'cache')),
		(os.path.join(HOME,'temp')),
		(os.path.join('/private/var/mobile/Library/Caches/AppleTV/Video/', 'Other')),
		(os.path.join('/private/var/mobile/Library/Caches/AppleTV/Video/', 'LocalAndRental')),
		(os.path.join(ADDONDATA,'script.module.simple.downloader')),
		(os.path.join(ADDONDATA,'plugin.video.itv','Images')),
		(os.path.join(PROFILEADDONDATA,'script.module.simple.downloader')),
		(os.path.join(PROFILEADDONDATA,'plugin.video.itv','Images'))]
		
	delfiles = 0

	for item in cachelist:
		if os.path.exists(item) and not item in [ADDONDATA, PROFILEADDONDATA]:
			for root, dirs, files in os.walk(item):
				file_count = 0
				file_count += len(files)
				if file_count > 0:
					for f in files:
						if not f in ['kodi.log', 'tvmc.log', 'spmc.log', 'xbmc.log']:
							try:
								os.unlink(os.path.join(root, f))
							except:
								pass
						else: log('Ignore Log File: %s' % f)
					for d in dirs:
						try:
							shutil.rmtree(os.path.join(root, d))
							delfiles += 1
							log("[COLOR white][Success]  %s Files Removed From %s [/COLOR]" % (str(file_count), os.path.join(item,d)))
						except:
							log("[COLOR red][Failed] To Wipe Cache In: %s [/COLOR]" % os.path.join(item,d))
		else:
			for root, dirs, files in os.walk(item):
				for d in dirs:
					if 'cache' in d.lower():
						try:
							shutil.rmtree(os.path.join(root, d))
							delfiles += 1
							log("[COLOR white][Success] Wiped %s [/COLOR]" % os.path.join(item,d))
						except:
							log("[COLOR red][Failed] To Wipe Cache In: %s [/COLOR]" % os.path.join(item,d))

	LogNotify(ADDONTITLE,'[COLOR aqua]Cache:[/COLOR] [COLOR white] %s Items Removed[/COLOR]' % delfiles)






















































































































































































































































































########################################################################################################
#
#	Merlin Auto Cleaner
#
#	By Merlin Project
#
#	August 2016
#
########################################################################################################
