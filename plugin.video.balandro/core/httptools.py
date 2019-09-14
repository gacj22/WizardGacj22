# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# httptools
# --------------------------------------------------------------------------------


# Fix para error de validación del certificado del tipo:
# [downloadpage] Response code: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:661)>
# [downloadpage] Response error: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:661)
# Fix desde la página: https://stackoverflow.com/questions/27835619/urllib-and-ssl-certificate-verify-failed-error
#-----------------------------------------------------------------------
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context
#-----------------------------------------------------------------------


import inspect
import cookielib
import gzip
import os
import time
import urllib
import urllib2
import urlparse
from StringIO import StringIO
from threading import Lock

from platformcode import config, logger
from platformcode.config import WebErrorException

from core.cloudflare import Cloudflare

## Obtiene la versión del addon
__version = config.get_addon_version()

cookies_lock = Lock()

cj = cookielib.MozillaCookieJar()
ficherocookies = os.path.join(config.get_data_path(), "cookies.dat")

# Headers por defecto, si no se especifica nada
default_headers = dict()
# ~ default_headers["User-Agent"] = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3163.100 Safari/537.36"
default_headers["User-Agent"] = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3163.100 Safari/537.36"
default_headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
default_headers["Accept-Language"] = "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3"
default_headers["Accept-Charset"] = "UTF-8"
default_headers["Accept-Encoding"] = "gzip"

# Tiempo máximo de espera para downloadpage, si no se especifica nada
HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT = config.get_setting('httptools_timeout', default=15)
if HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT == 0: HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT = None


def get_user_agent():
    return default_headers["User-Agent"]

def get_url_headers(url):
    if "|" in url: return url

    # ~ domain_cookies = cj._cookies.get("." + urlparse.urlparse(url)[1], {}).get("/", {})
    domain = urlparse.urlparse(url)[1]
    domain_cookies = cj._cookies.get("." + domain, {}).get("/", {})
    domain_cookies.update(cj._cookies.get(domain, {}).get("/", {}))

    # ~ if not "cf_clearance" in domain_cookies: return url

    headers = dict()
    headers["User-Agent"] = default_headers["User-Agent"]
    headers["Cookie"] = "; ".join(["%s=%s" % (c.name, c.value) for c in domain_cookies.values()])

    return url + "|" + "&".join(["%s=%s" % (h, urllib.quote(headers[h], safe='')) for h in headers])


def load_cookies():
    cookies_lock.acquire()
    if os.path.isfile(ficherocookies):
        logger.info("Leyendo fichero cookies")
        try:
            cj.load(ficherocookies, ignore_discard=True)
        except:
            logger.info("El fichero de cookies existe pero es ilegible, se borra")
            os.remove(ficherocookies)
    cookies_lock.release()


def save_cookies():
    cookies_lock.acquire()
    logger.info("Guardando cookies...")
    cj.save(ficherocookies, ignore_discard=True)
    cookies_lock.release()

def save_cookie(nombre, valor, dominio, ruta='/', tiempo=86400):
    cookie = cookielib.Cookie(version=0, name=nombre, value=valor, expires=time.time()+tiempo, port=None, port_specified=False, domain=dominio, domain_specified=True, domain_initial_dot=False, path=ruta, path_specified=True, secure=True, discard=False, comment=None, comment_url=None, rest={'HttpOnly': False}, rfc2109=False)
    cj.set_cookie(cookie)
    save_cookies()


load_cookies()

# Mismos parámetros que downloadpage pero con el canal de dónde obtener los proxies como primer parámetro.
# Bucle con los proxies que tenga el canal hasta recibir respuesta válida
def downloadpage_proxy(canal, 
                       url, post=None, headers=None, timeout=None, follow_redirects=True, cookies=True, replace_headers=False,
                       add_referer=False, only_headers=False, bypass_cloudflare=True, count_retries=0, raise_weberror=True, 
                       use_proxy=None, use_cache=False, cache_duration=36000):

    proxies = config.get_setting('proxies', canal, default='').replace(' ', '')
    if ';' in proxies: # Si los proxies estan separados por ; orden aleatorio
        proxies = proxies.replace(',', ';').split(';')
        import random
        random.shuffle(proxies)
    else:
        proxies = proxies.split(',')
    if len(proxies) == 0: proxies = ['']

    proxy_ok = False
    for n, proxy in enumerate(proxies):
        use_proxy = None if proxy == '' else {'http': proxy, 'https': proxy}

        resp = downloadpage(url, use_proxy=use_proxy, raise_weberror=False,
                            post=post, headers=headers, timeout=timeout, follow_redirects=follow_redirects, cookies=cookies, 
                            replace_headers=replace_headers, add_referer=add_referer, only_headers=only_headers,
                            bypass_cloudflare=bypass_cloudflare, count_retries=count_retries, 
                            use_cache=use_cache, cache_duration=cache_duration)
        if (type(resp.code) == int and (resp.code < 200 or resp.code > 399)) or not resp.sucess: 
            if proxy != '': logger.info('El proxy %s NO responde adecuadamente. %s' % (proxy, resp.code))
        else:
            if 'ERROR 404 - File not found' in resp.data or '<title>Site Blocked</title>' in resp.data or 'HTTP/1.1 400 Bad Request' in resp.data:
                logger.info('Respuesta insuficiente con el proxy %s' % proxy)
            else:
                proxy_ok = True
                if proxy != '': logger.info('El proxy %s parece válido.' % proxy)
                if n > 0: # guardar el proxy que ha funcionado como primero de la lista si no lo está
                    del proxies[n]
                    new_proxies = proxy + ', ' + ', '.join(proxies)
                    config.set_setting('proxies', new_proxies, canal)
                break

    if not proxy_ok: 
        from platformcode import platformtools
        if use_proxy == None: 
            txt = 'Configura los proxies del canal.'
        else: 
            txt = 'Ninguno de los proxies ha funcionado.' if len(proxies) > 1 else 'El proxy no ha funcionado.'
        platformtools.dialog_notification('Sin respuesta en [COLOR blue]%s[/COLOR]' % canal, txt)

    return resp


def downloadpage(url, post=None, headers=None, timeout=None, follow_redirects=True, cookies=True, replace_headers=False,
                 add_referer=False, only_headers=False, bypass_cloudflare=True, count_retries=0, raise_weberror=True, 
                 use_proxy=None, use_cache=False, cache_duration=36000):
    """
    Abre una url y retorna los datos obtenidos

    @param url: url que abrir.
    @type url: str
    @param post: Si contiene algun valor este es enviado mediante POST.
    @type post: str
    @param headers: Headers para la petición, si no contiene nada se usara los headers por defecto.
    @type headers: dict, list
    @param timeout: Timeout para la petición.
    @type timeout: int
    @param follow_redirects: Indica si se han de seguir las redirecciones.
    @type follow_redirects: bool
    @param cookies: Indica si se han de usar las cookies.
    @type cookies: bool
    @param replace_headers: Si True, los headers pasados por el parametro "headers" sustituiran por completo los headers por defecto.
                            Si False, los headers pasados por el parametro "headers" modificaran los headers por defecto.
    @type replace_headers: bool
    @param add_referer: Indica si se ha de añadir el header "Referer" usando el dominio de la url como valor.
    @type add_referer: bool
    @param only_headers: Si True, solo se descargarán los headers, omitiendo el contenido de la url.
    @type only_headers: bool
    @type raise_weberror: bool. Si False no se lanza WebErrorException si falla la descarga.
    @type use_proxy: dict. None o los parámetros que necesita urllib2.ProxyHandler(...) para descargar a través de un proxy.
    @type use_cache: bool. Si True se guardan los datos en caché y se devuelven si están vigentes.
    @type cache_duration: int. Duración del caché en caso de usarse. (por defecto 10 horas = 60 * 60 * 10)
    @return: Resultado de la petición
    @rtype: HTTPResponse

            Parametro               Tipo    Descripción
            ----------------------------------------------------------------------------------------------------------------
            HTTPResponse.sucess:    bool   True: Peticion realizada correctamente | False: Error al realizar la petición
            HTTPResponse.code:      int    Código de respuesta del servidor o código de error en caso de producirse un error
            HTTPResponse.error:     str    Descripción del error en caso de producirse un error
            HTTPResponse.headers:   dict   Diccionario con los headers de respuesta del servidor
            HTTPResponse.data:      str    Respuesta obtenida del servidor
            HTTPResponse.time:      float  Tiempo empleado para realizar la petición

    """
    response = {}

    # Si existe el fichero en la caché y no ha caducado, se devuelve su contenido sin hacer ninguna petición.
    # Solamente se tiene en cuenta la url, si se tuviera que usar con peticiones POST habría que adaptarlo.
    if use_cache:
        try:
            from hashlib import md5

            cache_path = os.path.join(config.get_data_path(), 'cache')
            if not os.path.exists(cache_path): os.makedirs(cache_path)
            cache_md5url = md5(url).hexdigest()
            cache_file = os.path.join(cache_path, cache_md5url)

            if os.path.isfile(cache_file):
                time_file = os.stat(cache_file).st_mtime
                time_now = time.time()
                if time_file + cache_duration >= time_now:
                    response["sucess"] = True
                    response["code"] = 200
                    response["error"] = None
                    response["headers"] = {}
                    response["url"] = url
                    with open(cache_file, 'r') as f: response["data"] = f.read()
                    response["time"] = time.time() - time_now
                    logger.info("Recuperado de caché %s la url %s" % (cache_md5url, url))
                    return type('HTTPResponse', (), response)
        except:
            pass

    # Headers por defecto, si no se especifica nada
    request_headers = default_headers.copy()

    # Headers pasados como parametros
    if headers is not None:
        if not replace_headers:
            request_headers.update(dict(headers))
        else:
            request_headers = dict(headers)

    if add_referer:
        request_headers["Referer"] = "/".join(url.split("/")[:3])

    url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")

    # Limitar tiempo de descarga si no se ha pasado timeout y hay un valor establecido en la variable global
    if timeout is None and HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT is not None: timeout = HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT

    logger.info("----------------------------------------------")
    logger.info("downloadpage Balandro: %s" %__version)
    logger.info("----------------------------------------------")
    if use_proxy: logger.info("Proxy: %s" % use_proxy)
    logger.info("Timeout: %s" % timeout)
    logger.info("URL: " + url)
    logger.info("Dominio: " + urlparse.urlparse(url)[1])
    if post:
        logger.info("Peticion: POST")
        logger.info(post)
    else:
        logger.info("Peticion: GET")
    logger.info("Usar Cookies: %s" % cookies)
    logger.info("Descargar Pagina: %s" % (not only_headers))
    logger.info("Fichero de Cookies: " + ficherocookies)
    logger.info("Headers:")
    for header in request_headers:
        logger.info("- %s: %s" % (header, request_headers[header]))

    if cookies:
        domain = urlparse.urlparse(url)[1]
        domain_cookies = cj._cookies.get("." + domain, {}).get("/", {})
        cks = "; ".join(["%s=%s" % (c.name, c.value) for c in domain_cookies.values()])
        if cks != '': logger.info('Cookies .' + domain + ' : ' + cks)
        domain_cookies = cj._cookies.get(domain, {}).get("/", {})
        cks = "; ".join(["%s=%s" % (c.name, c.value) for c in domain_cookies.values()])
        if cks != '': logger.info('Cookies ' + domain + ' : ' + cks)

    # Handlers
    handlers = [urllib2.HTTPHandler(debuglevel=False)]

    if not follow_redirects:
        handlers.append(NoRedirectHandler())

    if cookies:
        handlers.append(urllib2.HTTPCookieProcessor(cj))

    if use_proxy:
        handlers.append(urllib2.ProxyHandler(use_proxy))

    opener = urllib2.build_opener(*handlers)

    logger.info("Realizando Peticion")

    # Contador
    inicio = time.time()

    req = urllib2.Request(url, post, request_headers)

    try:
        if urllib2.__version__ == "2.4":
            import socket
            deftimeout = socket.getdefaulttimeout()
            if timeout is not None:
                socket.setdefaulttimeout(timeout)
            handle = opener.open(req)
            socket.setdefaulttimeout(deftimeout)
        else:
            handle = opener.open(req, timeout=timeout)

    except urllib2.HTTPError, handle:
        response["sucess"] = False
        response["code"] = handle.code
        response["error"] = handle.__dict__.get("reason", str(handle))
        response["headers"] = handle.headers.dict
        if not only_headers:
            response["data"] = handle.read()
        else:
            response["data"] = ""
        response["time"] = time.time() - inicio
        response["url"] = handle.geturl()

    except Exception, e:
        response["sucess"] = False
        response["code"] = e.__dict__.get("errno", e.__dict__.get("code", str(e)))
        response["error"] = e.__dict__.get("reason", str(e))
        response["headers"] = {}
        response["data"] = ""
        response["time"] = time.time() - inicio
        response["url"] = url

    else:
        response["sucess"] = True
        response["code"] = handle.code
        response["error"] = None
        response["headers"] = handle.headers.dict
        if not only_headers:
            response["data"] = handle.read()
        else:
            response["data"] = ""
        response["time"] = time.time() - inicio
        response["url"] = handle.geturl()

    logger.info("Terminado en %.2f segundos" % (response["time"]))
    logger.info("Response sucess: %s" % (response["sucess"]))
    logger.info("Response code: %s" % (response["code"]))
    logger.info("Response error: %s" % (response["error"]))
    logger.info("Response data length: %s" % (len(response["data"])))
    logger.info("Response headers:")
    for header in response["headers"]:
        logger.info("- %s: %s" % (header, response["headers"][header]))

    # Lanzar WebErrorException si la opción raise_weberror es True a menos que sea 503 de cloudflare o provenga de un server
    if type(response['code']) == int and response['code'] > 399 and raise_weberror:
        lanzar_error = True

        if response['code'] == 503: # Permitir 503 de cloudflare por si hay reintentos en anti-cloudflare
            for header in response['headers']:
                if 'cloudflare' in response['headers'][header]:
                    lanzar_error = False
                    break

        if lanzar_error:
            is_channel = inspect.getmodule(inspect.currentframe().f_back)
            if is_channel == None: is_channel = inspect.getmodule(inspect.currentframe().f_back.f_back)
            is_channel = str(is_channel).replace("/servers/","\\servers\\")
            if "\\servers\\" in is_channel or 'servertools' in is_channel:
                lanzar_error = False

        if lanzar_error:
            raise WebErrorException(urlparse.urlparse(url)[1])
        

    if cookies:
        save_cookies()

    logger.info("Encoding: %s" % (response["headers"].get('content-encoding')))
    if response["headers"].get('content-encoding') == 'gzip':
        try:
            response["data"] = gzip.GzipFile(fileobj=StringIO(response["data"])).read()
            logger.info("Descomprimido")
        except:
            logger.info("No se ha podido descomprimir")

    # Anti Cloudflare
    if bypass_cloudflare and count_retries < 2:
        cf = Cloudflare(response)
        if cf.is_cloudflare:
            count_retries += 1
            logger.info("cloudflare detectado, esperando %s segundos..." % cf.wait_time)
            auth_url = cf.get_url()
            logger.info("Autorizando... intento %d url: %s" % (count_retries, auth_url))
            # ~ debug_file = os.path.join(config.get_data_path(), 'cloudflare-info.txt')
            # ~ with open(debug_file, 'a') as myfile: myfile.write("Url: %s Intento %d auth_url: %s\n\n" % (url, count_retries, auth_url))

            resp_auth = downloadpage(auth_url, headers=request_headers, replace_headers=True, count_retries=count_retries, 
                                     use_proxy=use_proxy, raise_weberror=False)
            if count_retries == 1 and type(resp_auth.code) == int and resp_auth.code == 403: # repetir desde inicio con cookies recargadas
                load_cookies()
                return downloadpage(url, post=post, headers=headers, timeout=timeout, follow_redirects=follow_redirects, cookies=cookies, 
                                    replace_headers=replace_headers, add_referer=add_referer, only_headers=only_headers, 
                                    bypass_cloudflare=bypass_cloudflare, count_retries=1, raise_weberror=raise_weberror, 
                                    use_proxy=use_proxy, use_cache=use_cache, cache_duration=cache_duration)
            if resp_auth.sucess:
                logger.info("Autorización correcta, descargando página")
                resp = downloadpage(url=response["url"], post=post, headers=headers, timeout=timeout,
                                    follow_redirects=follow_redirects,
                                    cookies=cookies, replace_headers=replace_headers, add_referer=add_referer, 
                                    use_proxy=use_proxy, use_cache=use_cache, cache_duration=cache_duration)
                response["sucess"] = resp.sucess
                response["code"] = resp.code
                response["error"] = resp.error
                response["headers"] = resp.headers
                response["data"] = resp.data
                response["time"] = resp.time
                response["url"] = resp.url
            else:
                logger.info("No se ha podido autorizar")
                    
    # Guardar en caché si la respuesta parece válida (no parece not found ni bloqueado, al menos un enlace o json, al menos 1000 bytes)
    if use_cache and type(response['code']) == int and response['code'] >= 200 and response['code'] < 400 and response['data'] != '' \
       and len(response['data']) > 1000 \
       and 'ERROR 404 - File not found' not in response['data'] and '<title>Site Blocked</title>' not in response['data'] \
       and 'HTTP/1.1 400 Bad Request' not in response['data'] \
       and ('href=' in response['data'] or response['data'].startswith('{')):
        with open(cache_file, 'w') as f: f.write(response['data']); f.close()
        logger.info("Guardado en caché %s la url %s" % (cache_md5url, url))
        #TODO borrar ficheros en caché caducados ? o hacerlo en el servicio del addon ? o que sea responsabilidad del canal/servidor que use caché ?

    return type('HTTPResponse', (), response)


class NoRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        infourl = urllib.addinfourl(fp, headers, req.get_full_url())
        infourl.status = code
        infourl.code = code
        return infourl

    http_error_300 = http_error_302
    http_error_301 = http_error_302
    http_error_303 = http_error_302
    http_error_307 = http_error_302



# Devuelve un diccionario con las cookies pedidas con set-cookie en los headers de una descarga
def get_cookies_from_headers(headers):
    import re
    cookies = {}
    for h in headers:
        if h == 'set-cookie':
            cks = re.findall('(\w+)=([^;]+)', headers[h], re.DOTALL)
            for ck in cks:
                if ck[0].lower() not in ['path', 'domain', 'expires']:
                    cookies[ck[0]] = ck[1]
    return cookies
