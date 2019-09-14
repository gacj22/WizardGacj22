# -*- coding: utf-8 -*-

""" plexus-streams  (c)  2014 enen92 fightnight

	This file contains the function that brigdes the addon to the acecore.py file

	Functions:

	load_local_torrent() -> Load a local .torrent file
	acestreams(name,iconimage,chid) -> Wrapper to Plexus acestreams(name, iconimage, chid)

"""

import xbmc,xbmcgui,urllib
from utils.pluginxbmc import settings
from history import add_to_history

def load_local_torrent():
	if settings.getSetting('player') == "1": xbmc.executebuiltin('RunPlugin("plugin://program.plexus/?mode=6")')
	elif settings.getSetting('player') == "0": xbmc.executebuiltin('RunPlugin("plugin://plugin.video.torrentin/?funcion=cargarlocal")')
'''
	torrent_file = xbmcgui.Dialog().browse(1, translate(600028), 'video', '.torrent')
	if torrent_file:
		if xbmc.getCondVisibility('system.platform.windows'):
			acestreams("Local .torrent ("+str("file:\\" + torrent_file) +")","",'file:\\' + torrent_file)
		else:
			acestreams("Local .torrent ("+str("file://" + torrent_file) +")","",'file://' + torrent_file)
	else: pass
'''

def acestreams(name, iconimage, chid):
	print("Call acestreams with name: " + str(name)  + " chid = " + str(chid))

	if settings.getSetting('addon_history') == "true":
		try: add_to_history(name, chid, iconimage)
		except: pass

	if not chid.startswith("acestream://"):
		chid = "acestream://" + chid

	plexusURI = 'plugin://program.plexus/?url={CHURL}&mode=1&name={CHNAME}'.format(
				CHURL  = urllib.quote(chid, safe = ''),
				CHNAME = urllib.quote(name, safe = ''))
	torrentinURI = 'plugin://plugin.video.torrentin/?uri={CHURL}&mode=1&name={CHNAME}'.format(
				CHURL  = urllib.quote(chid, safe = ''),
				CHNAME = urllib.quote(name, safe = ''))

	if iconimage:
		plexusURI += "&iconimage={CHICON}".format(CHICON = urllib.quote(iconimage, safe=''))
		torrentinURI += "&image={CHICON}".format(CHICON = urllib.quote(iconimage, safe=''))

	print('Executing: PlayMedia("{0}")'.format(plexusURI))

	if settings.getSetting('player') == "1": xbmc.executebuiltin('PlayMedia("{0}")'.format(plexusURI))
	elif settings.getSetting('player') == "0": xbmc.executebuiltin('PlayMedia("{0}")'.format(torrentinURI))
