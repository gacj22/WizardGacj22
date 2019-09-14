# -*- coding: utf-8 -*-
import cookielib
import gzip
import inspect
import ssl
import Queue
from HTMLParser import HTMLParser
from StringIO import StringIO

from core.cloudflare import Cloudflare
from core.libs import *

proxies_fault = list()

cookies_lock = Lock()
cj = cookielib.MozillaCookieJar()
cookies_path = os.path.join(sysinfo.data_path, "cookies.dat")

# Headers por defecto, si no se especifica nada
default_headers = dict()
default_headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:57.0) Gecko/20100101 Firefox/57.0"
default_headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
default_headers["Accept-Language"] = "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3"
default_headers["Accept-Charset"] = "UTF-8"
default_headers["Accept-Encoding"] = "gzip"

# No comprobar certificados
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context


def get_cloudflare_headers(url):
    """
    Añade los headers para cloudflare
    :param url: Url
    :type url: str
    """
    domain_cookies = cj._cookies.get("." + urlparse.urlparse(url)[1], {}).get("/", {})

    if "cf_clearance" not in domain_cookies:
        return url

    headers = dict()
    headers["User-Agent"] = default_headers["User-Agent"]
    headers["Cookie"] = "; ".join(["%s=%s" % (c.name, c.value) for c in domain_cookies.values()])

    return url + '|%s' % '&'.join(['%s=%s' % (k, v) for k, v in headers.items()])


def load_cookies():
    """
    Carga el fichero de cookies
    """
    cookies_lock.acquire()

    if os.path.isfile(cookies_path):
        try:
            cj.load(cookies_path, ignore_discard=True)
        except Exception:
            logger.info("El fichero de cookies existe pero es ilegible, se borra")
            os.remove(cookies_path)

    cookies_lock.release()


def save_cookies():
    """
    Guarda las cookies
    """
    cookies_lock.acquire()
    cj.save(cookies_path, ignore_discard=True)
    cookies_lock.release()


def get_cookies(domain):
    return dict((c.name, c.value) for c in cj._cookies.get("." + domain, {}).get("/", {}).values())


def downloadpage(url, post=None, headers=None, timeout=None, follow_redirects=True, cookies=True, replace_headers=False,
                 add_referer=False, only_headers=False, bypass_cloudflare=True, bypass_testcookie=True, no_decode=False,
                 use_proxy=False, method=None):
    """
    Descarga una página web y devuelve los resultados
    :type url: str
    :type post: dict, str
    :type headers: dict, list
    :type timeout: int
    :type follow_redirects: bool
    :type cookies: bool, dict
    :type replace_headers: bool
    :type add_referer: bool
    :type only_headers: bool
    :type bypass_cloudflare: bool
    :type use_proxy: bool or str (IP:PORT)
    :return: Resultado
    """
    logger.trace()
    arguments = locals().copy()

    response = {}

    # Post tipo dict
    if type(post) == dict:
        post = urllib.urlencode(post)

    # Url quote
    url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")

    # Headers por defecto, si no se especifica nada
    request_headers = default_headers.copy()

    # Headers pasados como parametros
    if headers is not None:
        if not replace_headers:
            request_headers.update(dict(headers))
        else:
            request_headers = dict(headers)

    # Referer
    if add_referer:
        request_headers["Referer"] = "/".join(url.split("/")[:3])

    logger.info("Headers:")
    logger.info(request_headers)

    # Handlers
    handlers = list()
    handlers.append(urllib2.HTTPHandler(debuglevel=False))

    # No redirects
    if not follow_redirects:
        handlers.append(NoRedirectHandler())
    else:
        handlers.append(HTTPRedirectHandler())

    # Dict con cookies para la sesión
    if type(cookies) == dict:
        for name, value in cookies.items():
            if not type(value) == dict:
                value = {'value': value}
            ck = cookielib.Cookie(
                version=0,
                name=name,
                value=value.get('value', ''),
                port=None,
                port_specified=False,
                domain=value.get('domain', urlparse.urlparse(url)[1]),
                domain_specified=False,
                domain_initial_dot=False,
                path=value.get('path', '/'),
                path_specified=True,
                secure=False,
                expires=value.get('expires', time.time() + 3600 * 24),
                discard=True,
                comment=None,
                comment_url=None,
                rest={'HttpOnly': None},
                rfc2109=False
            )
            cj.set_cookie(ck)

    if cookies:
        handlers.append(urllib2.HTTPCookieProcessor(cj))

    # Proxy
    if use_proxy:
        proxy_aut = settings.get_setting('proxy_aut')
        proxy_man = settings.get_setting('proxy_man') or "198.27.67.35:3128"

        if isinstance(use_proxy, str):
            # uso del proxy forzado
            handlers.append(urllib2.ProxyHandler({'http': use_proxy, 'https': use_proxy}))

        elif settings.get_setting('proxy_tipo') != 1:
            # seleccion del proxy manual
            handlers.append(urllib2.ProxyHandler({'http': proxy_man, 'https': proxy_man}))

        elif proxy_aut:
            # seleccion del proxy automatica: prefijado
            handlers.append(urllib2.ProxyHandler({'http': proxy_aut, 'https': proxy_aut}))

        else:
            # seleccion del proxy automatica: busqueda
            proxy_aut = search_proxies()
            if proxy_aut:
                handlers.append(urllib2.ProxyHandler({'http': proxy_aut, 'https': proxy_aut}))
            else:
                use_proxy = False

    # Opener
    opener = urllib2.build_opener(*handlers)

    # Contador
    inicio = time.time()

    # Request
    req = Request(url, post, request_headers, method=method)

    try:
        logger.info("Realizando Peticion")
        handle = opener.open(req, timeout=timeout)
        logger.info('Peticion realizada')

    except urllib2.HTTPError, handle:
        logger.info('Peticion realizada con error')
        response["sucess"] = False
        response["code"] = handle.code
        response["error"] = handle.__dict__.get("reason", str(handle))
        response["headers"] = handle.headers.dict
        response['cookies'] = get_cookies(urlparse.urlparse(url)[1])
        if not only_headers:
            logger.info('Descargando datos...')
            response["data"] = handle.read()
        else:
            response["data"] = ""
        response["time"] = time.time() - inicio
        response["url"] = handle.geturl()

    except Exception, e:
        logger.info('Peticion NO realizada')
        response["sucess"] = False
        response["code"] = e.__dict__.get("errno", e.__dict__.get("code", str(e)))
        response["error"] = e.__dict__.get("reason", str(e))
        response["headers"] = {}
        response['cookies'] = get_cookies(urlparse.urlparse(url)[1])
        response["data"] = ""
        response["time"] = time.time() - inicio
        response["url"] = url

    else:
        response["sucess"] = True
        response["code"] = handle.code
        response["error"] = None
        response["headers"] = handle.headers.dict
        response['cookies'] = get_cookies(urlparse.urlparse(url)[1])
        if not only_headers:
            logger.info('Descargando datos...')
            response["data"] = handle.read()
        else:
            response["data"] = ""
        response["time"] = time.time() - inicio
        response["url"] = handle.geturl()

    logger.info("Terminado en %.2f segundos" % (response["time"]))
    logger.info("Response sucess     : %s" % (response["sucess"]))
    logger.info("Response code       : %s" % (response["code"]))
    logger.info("Response error      : %s" % (response["error"]))
    logger.info("Response data length: %s" % (len(response["data"])))
    logger.info("Response headers:")
    logger.info(response['headers'])

    # Guardamos las cookies
    if cookies:
        save_cookies()

    # Gzip
    if response["headers"].get('content-encoding') == 'gzip':
        response["data"] = gzip.GzipFile(fileobj=StringIO(response["data"])).read()

    if not no_decode:
        try:
            response["data"] = HTMLParser().unescape(unicode(response["data"], 'utf8')).encode('utf8')
        except Exception:
            pass

    # Anti TestCookie
    if bypass_testcookie:

        if 'document.cookie="__test="+toHex(slowAES.decrypt(c,2,a,b))+"' in response['data']:
            a = scrapertools.find_single_match(response['data'], 'a=toNumbers\("([^"]+)"\)').decode("HEX")
            b = scrapertools.find_single_match(response['data'], 'b=toNumbers\("([^"]+)"\)').decode("HEX")
            c = scrapertools.find_single_match(response['data'], 'c=toNumbers\("([^"]+)"\)').decode("HEX")
            arguments['bypass_testcookie'] = False
            if not type(arguments['cookies']) == dict:
                arguments['cookies'] = {'__test': aes.AESModeOfOperationCBC(a, b).decrypt(c).encode("HEX")}
            else:
                arguments['cookies']['__test'] = aes.AESModeOfOperationCBC(a, b).decrypt(c).encode("HEX")
            response = downloadpage(**arguments).__dict__

    # Anti Cloudflare
    if bypass_cloudflare:
        response = retry_if_cloudflare(response, arguments)
        
    # Proxy Retry
    if use_proxy:
        response = retry_if_proxy_error(response, arguments)

    return HTTPResponse(response)


def retry_if_cloudflare(response, args):
    cf = Cloudflare(response)
    if cf.is_cloudflare:
        logger.info("cloudflare detectado, esperando %s segundos..." % cf.wait_time)
        auth_url = cf.get_url()
        logger.info("Autorizando... url: %s" % auth_url)
        auth_args = args.copy()
        auth_args['url'] = auth_url
        auth_args['follow_redirects'] = False
        auth_args['headers'] = {'Referer': args['url']}
        resp = downloadpage(**auth_args)
        if resp.sucess:
            logger.info("Autorización correcta, descargando página")
            args['bypass_cloudflare'] = False
            return downloadpage(**args).__dict__
        elif resp.code == 403 and resp.headers.get('cf-chl-bypass'):
            if [a[3] for a in inspect.stack()].count('retry_if_cloudflare') > 2:
                logger.info("No se ha podido autorizar. Demasiados intentos")
                return response
            logger.info("Reintentando...")
            return downloadpage(**args).__dict__
        else:
            logger.info("No se ha podido autorizar")
    return response


def retry_if_proxy_error(response, args):
    # Evitar comprobaciones recurrentes
    if 'test_proxy' in [a[3] for a in inspect.stack()[1:]]:
        return response

    if not response['sucess'] and settings.get_setting('proxy_tipo') == 1:
        logger.info('La petición no se ha realizado correctamtente, comprobando proxy...')
        if not settings.get_setting('proxy_aut') or not test_proxy():
            logger.info('El proxy actual no funciona: %s' % settings.get_setting('proxy_aut'))
            if search_proxies(100):
                logger.info('Cambio de proxy automatico: %s' % settings.get_setting('proxy_aut'))
                return downloadpage(**args).__dict__
            else:
                logger.info('No se ha encontrado ningun proxy que funcione')
        else:
            logger.info('El proxy actual funciona correctamente: %s' % settings.get_setting('proxy_aut'))

    return response


def test_proxy(proxy=True, q=None, test_url='https://cloudflare.com'):
    # Probamos el proxy con una url que sepamos que funciona
    ret = httptools.downloadpage(test_url, use_proxy=proxy, timeout=2, only_headers=True).sucess

    if isinstance(q, Queue.Queue):
        if ret:
            logger.info('Multihilo: Proxy %s SI funciona' % proxy)
            q.put(proxy)
        else:
            logger.info('Multihilo: Proxy %s NO funciona' % proxy)
            proxies_fault.append(proxy)

    return ret


def search_proxies(max=None, test_url='https://cloudflare.com'):
    q = Queue.Queue()
    ret = None
    threads = list()

    proxy_aut_list = settings.get_setting('proxy_aut_list') or "proxyscrape.com"
    dialog_background = set([a[1].split(os.sep)[-1][:-2] + a[3] for a in inspect.stack()[1:]]) & {'finder.channel_search',
                                                                                          'newest.channel_search'}

    if dialog_background:
        dialog = platformtools.dialog_progress_bg('MediaExplorer: Buscando proxy', 'Iniciando búsqueda...')
        if not max or max > 30: max = 30
    else:
        dialog = platformtools.dialog_progress('MediaExplorer: Buscando proxy', 'Iniciando búsqueda...')

    if proxy_aut_list == 'proxyscrape.com':
        resp = downloadpage(
            'https://api.proxyscrape.com/?request=displayproxies&proxytype=http&timeout=100')
        proxies = resp.data.split()

    elif proxy_aut_list == 'proxy-list.download':
        resp = downloadpage('https://www.proxy-list.download/api/v1/get?type=http')
        proxies = resp.data.split()

    else:  # settings.get_setting('proxy_aut_list') == 'spys.me'
        resp = downloadpage('http://spys.me/proxy.txt')
        proxies = scrapertools.find_multiple_matches(resp.data, '(\d+\.\d+\.\d+\.\d+:\d+)')

    proxy_aut = settings.get_setting('proxy_aut')
    if proxy_aut:
        proxies_fault.append(proxy_aut)

    proxies = filter(lambda x: x not in proxies_fault, proxies)[:max]

    for x in range(0, len(proxies), 10):
        if not ret:
            for proxy in proxies[x:x + 10]:
                t = Thread(target=test_proxy, args=(proxy, q, test_url))
                t.daemon = True
                t.start()
                threads.append(t)

                if not dialog_background and dialog.iscanceled():
                    dialog.close()
                    return ret

            dialog.update((x + 1) * 100 / len(proxies),
                          'Buscando proxy en %s' % proxy_aut_list,
                          'Comprobando proxy del %s al %s de %s' % (x + 1, x + 10, len(proxies)))

            while [t for t in threads if t.isAlive()]:
                try:
                    ret = q.get(True, 1)
                    settings.set_setting('proxy_aut', ret)
                    break
                except Queue.Empty:
                    if not dialog_background and dialog.iscanceled():
                        dialog.close()
                        return ret

    dialog.close()
    return ret


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


class HTTPRedirectHandler(urllib2.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if 'Authorization' in req.headers:
            req.headers.pop('Authorization')
        return urllib2.HTTPRedirectHandler.redirect_request(self, req, fp, code, msg, headers, newurl)


class HTTPResponse:
    def __init__(self, response):
        self.sucess = None
        self.code = None
        self.error = None
        self.headers = None
        self.cookies = None
        self.data = None
        self.time = None
        self.url = None
        self.__dict__ = response


class Request(urllib2.Request):
    def __init__(self, *args, **kwargs):
        self.method = None
        if 'method' in kwargs:
            self.method = kwargs.pop('method')
        urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self):
        if self.method:
            return self.method.upper()

        if self.has_data():
            return "POST"
        else:
            return "GET"
