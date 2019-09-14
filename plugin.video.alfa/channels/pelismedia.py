# -*- coding: utf-8 -*-
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

__perfil__ = int(config.get_setting('perfil', 'pelismedia'))

# Fijar perfil de color
perfil = [['0xFFFFE6CC', '0xFFFFCE9C', '0xFF994D00'],
          ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E'],
          ['0xFF58D3F7', '0xFF2E9AFE', '0xFF2E64FE']]

if __perfil__ < 3:
	color1, color2, color3 = perfil[__perfil__]
else:
	color1 = color2 = color3 = ""

host="http://www.pelismedia.com"

def mainlist(item):
	logger.info()
	itemlist = []
	item.thumbnail = get_thumb('movies', auto=True)
	itemlist.append(item.clone(title="Películas:", folder=False, text_color="0xFFD4AF37", text_bold=True))
	itemlist.append(Item(channel = item.channel, title = "     Novedades", action = "peliculas", url = host,
                         thumbnail=get_thumb('newest', auto=True)))
	itemlist.append(Item(channel = item.channel, title = "     Estrenos", action = "peliculas", url = host + "/genero/estrenos/",
                         thumbnail=get_thumb('premieres', auto=True)))
	itemlist.append(Item(channel = item.channel, title = "     Por género", action = "genero", url = host,
                         thumbnail=get_thumb('genres', auto=True) ))
	item.thumbnail = get_thumb('tvshows', auto=True)
	itemlist.append(item.clone(title="Series:", folder=False, text_color="0xFFD4AF37", text_bold=True))
	itemlist.append(Item(channel = item.channel, title = "     Todas las series", action = "series", url = host + "/series/",
                         thumbnail=get_thumb('all', auto=True)))
	itemlist.append(Item(channel = item.channel, title = "     Nuevos episodios", action = "nuevos_episodios", url = host + "/episodio/",
                         thumbnail=get_thumb('new episodes', auto=True)))
	itemlist.append(Item(channel = item.channel, title = "Buscar...", action = "search", url = host, text_color="red", text_bold=True,
                         thumbnail=get_thumb('search', auto=True)))
	itemlist.append(item.clone(title="Configurar canal...", text_color="green", action="configuracion", text_bold=True))
	return itemlist

def configuracion(item):
	from platformcode import platformtools
	ret = platformtools.show_channel_settings()
	platformtools.itemlist_refresh()
	return ret

def newest(categoria):
	logger.info()
	itemlist = []
	item = Item()
	try:
		if categoria in ["peliculas", "latino"]:
			item.url = host
			itemlist = peliculas(item)
		elif categoria == 'terror':
			item.url = host + '/genero/terror/'
			itemlist = peliculas(item)
		elif categoria == "series":
			item.url = host + "/episodio/"
			itemlist = nuevos_episodios(item)
		if "Pagina" in itemlist[-1].title:
			itemlist.pop()

	# Se captura la excepción, para no interrumpir al canal novedades si un canal falla
	except:
		import sys
		for line in sys.exc_info():
			logger.error("{0}".format(line))
		return []

	return itemlist

def peliculas(item):
	logger.info()
	
	itemlist = []
	data = httptools.downloadpage(item.url).data

	data2 = scrapertools.find_single_match(data,'(?s)<div class="item_1.*?>(.*?)id="paginador">')

	# Se saca la info
	#(?s)class="ml-item.*?a href="([^"]+).*?img src="([^"]+).*?alt="([^"]+).*?class="year">(\d{4})</span>(.*?)<div
	patron = '(?s)class="ml-item.*?'					# base
	patron += 'a href="([^"]+).*?'						# url
	patron += 'img src="([^"]+).*?'						# imagen
	patron += 'alt="([^"]+).*?'							# titulo
	patron += 'class="year">(\d{4})'					# año
	patron += '</span>(.*?)<div'						# calidad
	matches = scrapertools.find_multiple_matches(data2, patron)

	scrapertools.printMatches(matches)
	for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedyear, scrapedquality in matches:
		if not "/series/" in scrapedurl:
			scrapedquality = scrapertools.find_single_match(scrapedquality, '<span class="calidad2">(.*?)</span>')
			itemlist.append(Item(action = "findvideos", channel = item.channel, title = scrapedtitle + " (" + scrapedyear + ") [" + scrapedquality + "]", contentTitle=scrapedtitle, thumbnail = scrapedthumbnail, url = scrapedurl, quality=scrapedquality, infoLabels={'year':scrapedyear}))
		else:
			if item.action == "search":
				itemlist.append(Item(action = "temporadas", channel = item.channel, title = scrapedtitle + " (" + scrapedyear + ")", contentSerieName=scrapedtitle, contentType="tvshow", thumbnail = scrapedthumbnail, url = scrapedurl, infoLabels={'year':scrapedyear}))


	# InfoLabels:
	tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

	# Pagina siguiente
	patron_siguiente='class="pag_b"><a href="([^"]+)'
	url_pagina_siguiente=scrapertools.find_single_match(data, patron_siguiente)

	if url_pagina_siguiente != "":
		pagina = ">>> Pagina: " + scrapertools.find_single_match(url_pagina_siguiente, '\d+')
		itemlist.append(Item(channel = item.channel, action = "peliculas", title = pagina, url = url_pagina_siguiente))

	return itemlist

def genero(item):
	logger.info()
	itemlist = []
	data = httptools.downloadpage(item.url).data
	# Delimita la búsqueda a la lista donde estan los géneros
	data = scrapertools.find_single_match(data,'(?s)<ul id="menu-generos" class="">(.*?)</ul>')
	# Extrae la url y el género
	patron = '<a href="(.*?)">(.*?)</a></li>'
	matches = scrapertools.find_multiple_matches(data, patron)
	# Se quita "Estrenos" de la lista porque tiene su propio menu
	matches.pop(0)

	for scrapedurl, scrapedtitle in matches:
		itemlist.append(Item(action = "peliculas", channel = item.channel, title = scrapedtitle, url = scrapedurl))

	return itemlist

def series(item):
	logger.info()
	itemlist = []
	data = httptools.downloadpage(item.url).data
	# Se saca la info
	patron = '(?s)class="ml-item.*?'					# base
	patron += 'a href="([^"]+).*?'						# url
	patron += 'img src="([^"]+).*?'						# imagen
	patron += 'alt="([^"]+).*?'							# titulo
	patron += 'class="year">(\d{4})'					# año
	matches = scrapertools.find_multiple_matches(data, patron)

	#if config.get_setting('temporada_o_todos', 'pelisultra') == 0:
	if config.get_setting('temporada_o_todos', item.channel):
		accion="temporadas"
	else:
		accion="episodios"

	for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedyear in matches:
		itemlist.append(Item(action = accion, channel = item.channel, title = scrapedtitle + " (" + scrapedyear + ")", contentSerieName=scrapedtitle, contentType="tvshow", thumbnail = scrapedthumbnail, url = scrapedurl, infoLabels={'year':scrapedyear}))

	# InfoLabels:
	tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

	# Pagina siguiente
	patron_siguiente='class="pag_b"><a href="([^"]+)'
	url_pagina_siguiente=scrapertools.find_single_match(data, patron_siguiente)

	if url_pagina_siguiente != "":
		pagina = ">>> Pagina: " + scrapertools.find_single_match(url_pagina_siguiente, '\d+')
		itemlist.append(Item(channel = item.channel, action = "series", title = pagina, url = url_pagina_siguiente))

	return itemlist

def temporadas(item):
	logger.info()
	itemlist = []
	data = httptools.downloadpage(item.url).data
	# Extrae las temporadas
	patron = '<span class="se-t.*?>(.*?)</span>'
	matches = scrapertools.find_multiple_matches(data, patron)

	# Excepción para la serie Sin Límites
	if item.contentTitle == 'Amar sin límites':
		item.contentSerieName = "limitless"
		item.infoLabels['tmdb_id']=''

	for scrapedseason in matches:
		itemlist.append(item.clone(action = "episodios", title = "Temporada " + scrapedseason, contentSeason=scrapedseason))

	# InfoLabels:
	tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

	return itemlist

def episodios(item):
	logger.info()
	itemlist = []
	data = httptools.downloadpage(item.url).data
	patron = '(?s)class="episodiotitle">.*?a href="(.*?)">(.*?)</a>'
	matches = scrapertools.find_multiple_matches(data, patron)

	for scrapedurl, scrapedtitle in matches:
		# Saco el numero de capitulo de la url
		numero_capitulo=scrapertools.get_season_and_episode(scrapedurl)
		if numero_capitulo != "":
			temporada=numero_capitulo.split("x")[0]
			capitulo=numero_capitulo.split("x")[1]
		else:
			temporada="_"
			capitulo="_"

		if item.contentSeason and str(item.contentSeason) != temporada:
			continue

		itemlist.append(item.clone(action = "findvideos", title = numero_capitulo + " - " + scrapedtitle.strip(), url = scrapedurl, contentSeason=temporada, contentEpisodeNumber=capitulo))

		# if item.contentTitle.startswith('Temporada'):
			# if str(item.contentSeason) == temporada:
				# itemlist.append(item.clone(action = "findvideos", title = numero_capitulo + " - " + scrapedtitle.strip(), url = scrapedurl, contentSeason=temporada, contentEpisodeNumber=capitulo))
		# else:
			# itemlist.append(item.clone(action = "findvideos", title = numero_capitulo + " - " + scrapedtitle.strip(), url = scrapedurl, contentSeason=temporada, contentEpisodeNumber=capitulo))

	#episodios_por_pagina=20
	# if config.get_setting('episodios_x_pag', 'pelisultra').isdigit():
		# episodios_por_pagina=int(config.get_setting('episodios_x_pag', 'pelisultra'))
	# else:
		# episodios_por_pagina=20
		# config.set_setting('episodios_x_pag', '20', 'pelisultra')

	episodios_por_pagina= int(config.get_setting('episodios_x_pag', item.channel)) * 5 + 10

	if not item.page:
		item.page = 0

	itemlist_page = itemlist[item.page: item.page + episodios_por_pagina]

	if len(itemlist) > item.page + episodios_por_pagina:
		itemlist_page.append(item.clone(title = ">>> Pagina siguiente", page = item.page + episodios_por_pagina))

	# InfoLabels:
	tmdb.set_infoLabels_itemlist(itemlist_page, seekTmdb=True)

	return itemlist_page

def nuevos_episodios(item):
	logger.info()
	itemlist = []
	data = httptools.downloadpage(item.url).data
	patron = '(?s)<td class="bb">.*?'	# base
	patron += '<a href="(.*?)">'		# url
	patron += '(.*?)</a>.*?'			# nombre_serie
	patron += '<img src="(.*?)>.*?'		# imagen
	patron += '<h2>(.*?)</h2>'			# titulo
	matches = scrapertools.find_multiple_matches(data, patron)

	for scrapedurl, scrapedseriename, scrapedthumbnail, scrapedtitle in matches:
		numero_capitulo=scrapertools.get_season_and_episode(scrapedurl)
		if numero_capitulo != "":
			temporada=numero_capitulo.split("x")[0]
			capitulo=numero_capitulo.split("x")[1]
		else:
			temporada="_"
			capitulo="_"

		itemlist.append(Item(channel = item.channel, action = "findvideos", title = scrapedseriename +": " + numero_capitulo + " - " + scrapedtitle.strip(), url = scrapedurl, thumbnail = scrapedthumbnail, contentSerieName=scrapedseriename, contentSeason=temporada, contentEpisodeNumber=capitulo))

	# InfoLabels:
	tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

	# Pagina siguiente
	patron_siguiente='class="pag_b"><a href="([^"]+)'
	url_pagina_siguiente=scrapertools.find_single_match(data, patron_siguiente)

	if url_pagina_siguiente != "":
		pagina = ">>> Pagina: " + scrapertools.find_single_match(url_pagina_siguiente, '\d+')
		itemlist.append(Item(channel = item.channel, action = "nuevos_episodios", title = pagina, url = url_pagina_siguiente))

	return itemlist

def search(item, texto):
	logger.info()
	itemlist = []
	texto = texto.replace(" ", "+")
	try:
		item.url = host + "/?s=%s" % texto
		itemlist.extend(peliculas(item))
		return itemlist
	# Se captura la excepción, para no interrumpir al buscador global si un canal falla
	except:
		import sys
		for line in sys.exc_info():
			logger.error("%s" % line)
		return []
