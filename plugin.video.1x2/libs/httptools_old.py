# -*- coding: utf-8 -*-
import cookielib
import gzip
import inspect
import ssl
import Queue
import urlparse

from libs.tools import *

from HTMLParser import HTMLParser
from StringIO import StringIO
from threading import Lock


cookies_lock = Lock()
cj = cookielib.MozillaCookieJar()
cookies_path = os.path.join(data_path, "cookies.dat")

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

def load_cookies():
    """
    Carga el fichero de cookies
    """
    cookies_lock.acquire()

    if os.path.isfile(cookies_path):
        try:
            cj.load(cookies_path, ignore_discard=True)
        except Exception:
            logger("El fichero de cookies existe pero es ilegible, se borra")
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
                 add_referer=False, only_headers=False, no_decode=False, method=None):
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

    :return: Resultado
    """
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

    #logger("Headers:")
    #logger(request_headers, 'info')

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

    # Opener
    opener = urllib2.build_opener(*handlers)

    # Contador
    inicio = time.time()

    # Request
    req = Request(url, post, request_headers, method=method)

    try:
        #logger("Realizando Peticion")
        handle = opener.open(req, timeout=timeout)
        #logger('Peticion realizada')

    except urllib2.HTTPError, handle:
        #logger('Peticion realizada con error')
        response["sucess"] = False
        response["code"] = handle.code
        response["error"] = handle.__dict__.get("reason", str(handle))
        response["headers"] = handle.headers.dict
        response['cookies'] = get_cookies(urlparse.urlparse(url)[1])
        if not only_headers:
            #logger('Descargando datos...')
            response["data"] = handle.read()
        else:
            response["data"] = ""
        response["time"] = time.time() - inicio
        response["url"] = handle.geturl()

    except Exception, e:
        #logger('Peticion NO realizada')
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
            #logger('Descargando datos...')
            response["data"] = handle.read()
        else:
            response["data"] = ""
        response["time"] = time.time() - inicio
        response["url"] = handle.geturl()

    #logger("Terminado en %.2f segundos" % (response["time"]))
    #logger("Response sucess     : %s" % (response["sucess"]))
    #logger("Response code       : %s" % (response["code"]))
    #logger("Response error      : %s" % (response["error"]))
    #logger("Response data length: %s" % (len(response["data"])))
    #logger("Response headers:")
    #logger(response['headers'])

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

    return HTTPResponse(response)


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
