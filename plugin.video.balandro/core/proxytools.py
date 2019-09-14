# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# proxytools - Herramientas para proxies
# ------------------------------------------------------------

import os, time, re
from threading import Thread

from core import jsontools, filetools, httptools, scrapertools
from platformcode import config, logger, platformtools


opciones_provider = ['spys.one', 'proxy-list.download', 'proxyscrape.com', 'proxyservers.pro', 'lista_proxies.txt']
opciones_tipo = ['Cualquier tipo', 'Elite', 'Anonymous', 'Transparent']
opciones_pais = ['Cualquier país', 'ES', 'US', 'FR', 'DE', 'CZ', 'IT', 'CH', 'NL', 'MX', 'RU', 'HK', 'SG'] #TODO completar...


# Parámetros proxytools_ específicos del canal
def get_settings_proxytools(canal):
    provider = config.get_setting('proxytools_provider', canal, default='proxyscrape.com')
    tipo_proxy = config.get_setting('proxytools_tipo', canal, default='')
    pais_proxy = config.get_setting('proxytools_pais', canal, default='')
    max_proxies = config.get_setting('proxytools_max', canal, default=20)
    return provider, tipo_proxy, pais_proxy, max_proxies


# Diálogo principal para configurar los proxies de un canal concreto
def configurar_proxies_canal(canal, url):
    logger.info()
    
    while True:
        proxies = config.get_setting('proxies', canal, default='')
        provider, tipo_proxy, pais_proxy, max_proxies = get_settings_proxytools(canal)
        if provider == 'lista_proxies.txt':
            tipo_proxy = '-'
            pais_proxy = '-'
        else:
            tipo_proxy = opciones_tipo[0] if tipo_proxy == '' else tipo_proxy.capitalize()
            pais_proxy = opciones_pais[0] if pais_proxy == '' else pais_proxy

        acciones = []
        acciones.append(platformtools.listitem_to_select('Modificar proxies manualmente', proxies, ''))
        acciones.append(platformtools.listitem_to_select('Buscar proxies automáticamente', 'Iniciar búsqueda con los parámetros actuales'))
        acciones.append(platformtools.listitem_to_select('Parámetros para buscar proxies', '%s, %s, %s, %d' % (provider, tipo_proxy, pais_proxy, max_proxies), ''))

        ret = platformtools.dialog_select('Configurar proxies para %s' % canal.capitalize(), acciones, useDetails=True)
        if ret == -1: # pedido cancel
            break

        elif ret == 0:
            proxies = config.get_setting('proxies', canal, default='')

            new_proxies = platformtools.dialog_input(default=proxies, heading='Introduce el proxy a utilizar o varios separados por comas')
            if new_proxies is not None and new_proxies != proxies:
                config.set_setting('proxies', new_proxies, canal)
                break

        elif ret == 1:
            if _buscar_proxies(canal, url): break # si no se encuentran proxies válidos seguir para poder cambiar parámetros o entrar manualmente

        elif ret == 2:
            _settings_proxies_canal(canal)

    return True


# Diálogos para guardar las diferentes opciones de búsqueda
def _settings_proxies_canal(canal):
    
    provider, tipo_proxy, pais_proxy, max_proxies = get_settings_proxytools(canal)

    preselect = 0 if provider not in opciones_provider else opciones_provider.index(provider)
    ret = platformtools.dialog_select('Proveedor de lista de proxies', opciones_provider, preselect=preselect)
    if ret == -1: return False
    provider = opciones_provider[ret]
    config.set_setting('proxytools_provider', provider, canal)

    if provider != 'lista_proxies.txt':
        preselect = 0 if tipo_proxy.capitalize() not in opciones_tipo else opciones_tipo.index(tipo_proxy.capitalize())
        ret = platformtools.dialog_select('Tipo de anonimidad de los proxies', opciones_tipo, preselect=preselect)
        if ret == -1: return False
        tipo_proxy = '' if ret == 0 else opciones_tipo[ret].lower()
        config.set_setting('proxytools_tipo', tipo_proxy, canal)

        preselect = 0 if pais_proxy not in opciones_pais else opciones_pais.index(pais_proxy)
        ret = platformtools.dialog_select('País de los proxies', opciones_pais, preselect=preselect)
        if ret == -1: return False
        pais_proxy = '' if ret == 0 else opciones_pais[ret]
        config.set_setting('proxytools_pais', pais_proxy, canal)

    max_proxies = platformtools.dialog_numeric(0, 'Número máximo de proxies a analizar', '20')
    if max_proxies < 3 or max_proxies > 50: max_proxies = 20
    config.set_setting('proxytools_max', max_proxies, canal)

    return True


def _buscar_proxies(canal, url):
    if url == '': url = 'http://httpbin.org/ip'

    provider, tipo_proxy, pais_proxy, max_proxies = get_settings_proxytools(canal)

    # Obtener lista de proxies
    # ------------------------
    url_provider = ''

    # API: https://www.proxy-list.download/api/v1
    if provider == 'proxy-list.download':
        url_provider = 'https://www.proxy-list.download/api/v1/get'
        url_provider += '?type=' + ('https' if url.startswith('https') else 'http') # http, https, socks4, socks5
        if tipo_proxy != '': url_provider += '&anon=' + tipo_proxy
        if pais_proxy != '': url_provider += '&country=' + pais_proxy

        resp = httptools.downloadpage(url_provider)
        proxies = resp.data.split()

    # API: https://proxyscrape.com/api-documentation
    elif provider == 'proxyscrape.com':
        url_provider = 'https://api.proxyscrape.com/?request=displayproxies'
        url_provider += '&proxytype=http' # http, socks4, socks5
        # ~ url_provider += '&ssl=' + ('yes' if url.startswith('https') else 'no')
        url_provider += '&ssl=all' # para evitar ssl=no ya que hay poquísimos proxies !?
        if tipo_proxy != '': url_provider += '&anonymity=' + tipo_proxy
        if pais_proxy != '': url_provider += '&country=' + pais_proxy

        resp = httptools.downloadpage(url_provider)
        proxies = resp.data.split()

    elif provider == 'spys.one': 
        url_provider = 'http://spys.one/en/free-proxy-list/'
        url_post = 'xpp=0'
        if tipo_proxy == 'anonymous': url_post += 'xf1=3'
        elif tipo_proxy == 'transparent': url_post += 'xf1=2'
        elif tipo_proxy == 'elite': url_post += 'xf1=4'
        else: url_post += '&xf1=0'
        url_post += '&xf2=0&xf4=0&xf5=0'
        
        resp = httptools.downloadpage(url_provider, post=url_post)

        valores = {}
        numeros = scrapertools.find_multiple_matches(resp.data, '([a-z0-9]{6})=(\d{1})\^')
        for a, b in numeros:
            valores[a] = b

        proxies = []
        enlaces = scrapertools.find_multiple_matches(resp.data, '<font class=spy14>(\d+\.\d+\.\d+\.\d+).*?font>"(.*?)</script>')
        for prox, resto in enlaces:
            puerto = ''
            numeros = scrapertools.find_multiple_matches(resto, '\+\(([a-z0-9]{6})\^')
            for a in numeros: puerto += str(valores[a])
            proxies.append(prox+':'+puerto)

    elif provider == 'proxyservers.pro':
        url_provider = 'https://es.proxyservers.pro/proxy/list'
        if tipo_proxy != '': url_provider += '/anonymity/' + tipo_proxy
        if pais_proxy != '': url_provider += '/country/' + pais_proxy
        url_provider += '/protocol/' + ('https' if url.startswith('https') else 'http')

        resp = httptools.downloadpage(url_provider)
        
        chash = scrapertools.find_single_match(resp.data, "var chash\s*=\s*'([^']+)")
        def decode_puerto(t, e):
            a = []; r = []
            for n in range(0, len(t), 2): a.append(int('0x'+t[n:n+2], 16))
            for n in range(len(e)): r.append(ord(e[n]))
            for n, val in enumerate(a): a[n] = val ^ r[n % len(r)]
            for n, val in enumerate(a): a[n] = chr(val)
            return ''.join(a)

        proxies = []
        enlaces = scrapertools.find_multiple_matches(resp.data, '(\d+\.\d+\.\d+\.\d+)</a></td><td><span class="port" data-port="([^"]+)')
        for prox, puerto in enlaces:
            proxies.append(prox + ':' + decode_puerto(puerto, chash))
                                                          
    # fichero personal de proxies en userdata (separados por comas o saltos de línea)
    elif provider == 'lista_proxies.txt':
        proxies_file = os.path.join(config.get_data_path(), 'lista_proxies.txt')
        data = filetools.read(proxies_file)
        data = re.sub(r'(?m)^#.*\n?', '', data) # Quitar líneas que empiezen por #
        proxies = data.replace(' ', '').replace(';', ',').replace(',', '\n').split()

    else:
        proxies = []


    # Limitar proxies y validar formato
    # ---------------------------------
    proxies = filter(lambda x: re.match('\d+\.\d+\.\d+\.\d+\:\d+', x), proxies)

    if max_proxies: proxies = proxies[:max_proxies]
    # ~ logger.debug(proxies)


    # Testear proxies
    # ---------------
    proxies_info = testear_lista_proxies(url, proxies)


    # Guardar mejores proxies en la configuración del canal
    # -----------------------------------------------------
    selected = []
    for proxy, info in proxies_info:
        if not info['ok']: break
        selected.append(proxy)
        if len(selected) >= 3: break # se guardan los 3 más rápidos

    if len(selected) > 0:
        config.set_setting('proxies', ', '.join(selected), canal)
        logger.info('Actualizados proxies para %s : %s' % (canal, ', '.join(selected)))
        platformtools.dialog_notification('Buscar proxies', 'Actualizados proxies para [COLOR blue]%s[/COLOR]' % canal.capitalize())
    else:
        platformtools.dialog_notification('Buscar proxies', 'No se han encontrado proxies válidos.')


    # Apuntar resultados en proxies.log
    # ---------------------------------
    if config.get_setting('developer_mode', default=False):
        proxies_log = os.path.join(config.get_data_path(), 'proxies.log')

        txt_log = os.linesep + '%s Buscar proxies en %s para %s' % (time.strftime("%Y-%m-%d %H:%M"), provider, url) + os.linesep
        if url_provider != '': txt_log += url_provider + os.linesep

        num_ok = 0
        for proxy, info in proxies_info:
            txt_log += '%s ~ %s ~ %.2f segundos ~ %s ~ %d bytes' % (proxy, info['ok'], info['time'], info['code'], info['len']) + os.linesep
            if info['ok']: num_ok += 1

        txt_log += 'Búsqueda finalizada. Proxies válidos: %d' % (num_ok) + os.linesep

        with open(proxies_log, 'a') as f: f.write(txt_log); f.close()

    return True if len(selected) > 0 else False


# Testear una lista de proxies para una url determinada
# -----------------------------------------------------

def do_test_proxy(url, proxy, info):
    resp = httptools.downloadpage(url, use_proxy = {'http': proxy, 'https': proxy}, timeout=10, raise_weberror=False)

    info['ok'] = (type(resp.code) == int and resp.code >= 200 and resp.code < 400)
    if 'ERROR 404 - File not found' in resp.data \
       or 'HTTP/1.1 400 Bad Request' in resp.data \
       or '<title>Site Blocked</title>' in resp.data:
        info['ok'] = False
    info['time'] = resp.time
    info['len'] = len(resp.data)
    info['code'] = resp.code

def testear_lista_proxies(url, proxies=[]):
    threads = []
    proxies_info = {} # resultados de los tests

    num_proxies = float(len(proxies)) # float para calcular porcentaje

    progreso = platformtools.dialog_progress('Testeando proxies', '%d proxies a comprobar. Cancelar si tarda demasiado.' % num_proxies)

    for proxy in proxies:
        if proxy in proxies_info: continue # por si hay repetidos
        proxies_info[proxy] = {'ok': False, 'time': 0, 'len': 0, 'code': ''}
        t = Thread(target=do_test_proxy, args=[url, proxy, proxies_info[proxy]])
        t.setDaemon(True)
        t.start()
        threads.append(t)
        
        if progreso.iscanceled(): break

    pendent = [a for a in threads if a.isAlive()]
    while len(pendent) > 0:
        hechos = num_proxies - len(pendent)
        perc = int(hechos / num_proxies * 100)
        validos = sum([1 for proxy in proxies if proxies_info[proxy]['ok']])

        progreso.update(perc, 'Finalizado en %d de %d proxies. Válidos %d. Cancelar si tarda demasiado o ya hay varios válidos.' % (hechos, num_proxies, validos))

        if progreso.iscanceled(): break

        time.sleep(0.5)
        pendent = [a for a in threads if a.isAlive()]

    progreso.close()
    
    # Ordenar según proxy válido y tiempo de respuesta
    return sorted(proxies_info.items(), key=lambda x: (-x[1]['ok'], x[1]['time']))
