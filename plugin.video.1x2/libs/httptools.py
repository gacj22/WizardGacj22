# -*- coding: utf-8 -*-
import cookielib
import gzip
import inspect
import ssl
import aes
import urlparse
from HTMLParser import HTMLParser
from StringIO import StringIO
from threading import Lock

from libs.tools import *


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

'''
def get_hash(url=None, data='', algorithm='md5', max_file_size= 104857600):
    import hashlib

    if url:
        url = url.split('|')[0]
        data = downloadpage(url).data
    if algorithm == "sha1":
        hash = hashlib.sha1()
    elif algorithm == "sha256":
        hash = hashlib.sha256()
    elif algorithm == "sha384":
        hash = hashlib.sha384()
    elif algorithm == "sha512":
        hash = hashlib.sha512()
    else:
        hash = hashlib.md5()
    
    total_read = 0
    ini_read = 0
    while True:
        total_read += 4096
        data = data[ini_read:total_read]

        if not data or total_read > max_file_size:
            break

        hash.update(data)
        ini_read = total_read

    return hash.hexdigest()
'''

def downloadpage(url, post=None, headers=None, timeout=None, follow_redirects=True, cookies=True, replace_headers=False,
                 add_referer=False, only_headers=False, bypass_cloudflare=True, bypass_testcookie=True, no_decode=False,
                 method=None):
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

    # Anti TestCookie
    if bypass_testcookie:

        if 'document.cookie="__test="+toHex(slowAES.decrypt(c,2,a,b))+"' in response['data']:
            a = re.findall('a=toNumbers\("([^"]+)"\)', response['data'])[0].decode("HEX")
            b = re.findall('b=toNumbers\("([^"]+)"\)', response['data'])[0].decode("HEX")
            c = re.findall('c=toNumbers\("([^"]+)"\)', response['data'])[0].decode("HEX")
            '''a = scrapertools.find_single_match(response['data'], 'a=toNumbers\("([^"]+)"\)').decode("HEX")
            b = scrapertools.find_single_match(response['data'], 'b=toNumbers\("([^"]+)"\)').decode("HEX")
            c = scrapertools.find_single_match(response['data'], 'c=toNumbers\("([^"]+)"\)').decode("HEX")'''
            arguments['bypass_testcookie'] = False
            if not type(arguments['cookies']) == dict:
                arguments['cookies'] = {'__test': aes.AESModeOfOperationCBC(a, b).decrypt(c).encode("HEX")}
            else:
                arguments['cookies']['__test'] = aes.AESModeOfOperationCBC(a, b).decrypt(c).encode("HEX")
            response = downloadpage(**arguments).__dict__

    # Anti Cloudflare
    if bypass_cloudflare:
        response = retry_if_cloudflare(response, arguments)
        

    return HTTPResponse(response)


def retry_if_cloudflare(response, args):
    cf = Cloudflare(response)
    if cf.is_cloudflare:
        #logger("cloudflare detectado, esperando %s segundos..." % cf.wait_time)
        auth_url = cf.get_url()
        #logger("Autorizando... url: %s" % auth_url)
        auth_args = args.copy()
        auth_args['url'] = auth_url
        auth_args['follow_redirects'] = False
        auth_args['headers'] = {'Referer': args['url']}
        resp = downloadpage(**auth_args)
        if resp.sucess:
            #logger("Autorización correcta, descargando página")
            args['bypass_cloudflare'] = False
            return downloadpage(**args).__dict__
        elif resp.code == 403 and resp.headers.get('cf-chl-bypass'):
            if [a[3] for a in inspect.stack()].count('retry_if_cloudflare') > 2:
                #logger("No se ha podido autorizar. Demasiados intentos")
                return response
            #logger("Reintentando...")
            return downloadpage(**args).__dict__
        else:
            #logger("No se ha podido autorizar")
            pass
    return response





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



class Cloudflare:
    def __init__(self, response):
        self.timeout = 5
        self.domain = urlparse.urlparse(response["url"])[1]
        self.protocol = urlparse.urlparse(response["url"])[0]

        pattern = r'var s,t,o,p,b,r,e,a,k,i,n,g,f, ([^=]+)={"([^"]+)":' \
                  r'(?P<value>[^}]+).*?' \
                  r'(?:\1.\2(?P<op0>[+\-*/])=(?P<val0>[^;]+);)?' \
                  r'(?:\1.\2(?P<op1>[+\-*/])=(?P<val1>[^;]+);)?' \
                  r'(?:\1.\2(?P<op2>[+\-*/])=(?P<val2>[^;]+);)?' \
                  r'(?:\1.\2(?P<op3>[+\-*/])=(?P<val3>[^;]+);)?' \
                  r'(?:\1.\2(?P<op4>[+\-*/])=(?P<val4>[^;]+);)?' \
                  r'(?:\1.\2(?P<op5>[+\-*/])=(?P<val5>[^;]+);)?' \
                  r'(?:\1.\2(?P<op6>[+\-*/])=(?P<val6>[^;]+);)?' \
                  r'(?:\1.\2(?P<op7>[+\-*/])=(?P<val7>[^;]+);)?' \
                  r'(?:\1.\2(?P<op8>[+\-*/])=(?P<val8>[^;]+);)?' \
                  r'(?:\1.\2(?P<op9>[+\-*/])=(?P<val9>[^;]+);)?' \
                  r'a.value.*?, (?P<wait>\d+)\);.*?' \
                  r'<form id="challenge-form" action="(?P<auth_url>[^"]+)" method="get">[^<]+' \
                  r'<input type="hidden" name="jschl_vc" value="(?P<jschl_vc>[^"]+)[^<]+' \
                  r'<input type="hidden" name="pass" value="(?P<pass>[^"]+)"/>'

        match = re.compile(pattern, re.DOTALL).search(response['data'])
        if match:
            self.js_data = {
                "auth_url": match.group('auth_url'),
                "params": {
                    "jschl_vc": match.group('jschl_vc'),
                    "pass": match.group('pass'),
                },
                "value": match.group('value'),
                "op": [
                    [
                        match.group('op%s' % x),
                        match.group('val%s' % x)
                    ]
                    for x in range(9) if match.group('val%s' % x)
                ],
                "wait": int(match.group('wait')) / 1000,
            }
        else:
            self.js_data = dict()

        if response["headers"].get("refresh"):
            try:
                self.header_data = {
                    "auth_url": response["headers"]["refresh"].split("=")[1].split("?")[0],
                    "params": {
                        "pass": response["headers"]["refresh"].split("=")[2]
                    },
                    "wait": int(response["headers"]["refresh"].split(";")[0])
                }
            except Exception:
                self.header_data = dict()
        else:
            self.header_data = dict()

    @property
    def wait_time(self):
        if self.js_data:
            return self.js_data["wait"]
        else:
            return self.header_data["wait"]

    @property
    def is_cloudflare(self):
        return bool(self.header_data or self.js_data)

    def get_url(self):
        # Metodo #1 (javascript)
        if self.js_data:
            jschl_answer = self.decode(self.js_data["value"])
            #logger(self.js_data["op"])
            for op, v in self.js_data["op"]:

                jschl_answer = eval(str(jschl_answer) + op + str(self.decode(v)))

            self.js_data["params"]["jschl_answer"] = jschl_answer + len(self.domain)

            response = "%s://%s%s?%s" % (
                self.protocol,
                self.domain,
                self.js_data["auth_url"],
                urllib.urlencode(self.js_data["params"])
            )

            time.sleep(self.js_data["wait"])

            return response

        # Metodo #2 (headers)
        if self.header_data:
            response = "%s://%s%s?%s" % (
                self.protocol,
                self.domain,
                self.header_data["auth_url"],
                urllib.urlencode(self.header_data["params"])
            )

            time.sleep(self.header_data["wait"])

            return response

    def decode(self, data):
        t = time.time()
        timeout = False

        while not timeout:
            data = re.sub("\[\]", "''", data)
            data = re.sub("!\+''", "+1", data)
            data = re.sub("!''", "0", data)
            data = re.sub("!0", "1", data)

            if "(" in data:
                x, y = data.rfind("("), data.find(")", data.rfind("(")) + 1
                part = data[x + 1:y - 1]
            else:
                x = 0
                y = len(data)
                part = data

            val = ""

            if not part.startswith("+"):
                part = "+" + part

            for i, ch in enumerate(part):
                if ch == "+":
                    if not part[i + 1] == "'":
                        if val == "":
                            val = 0
                        if type(val) == str:
                            val = val + self.get_number(part, i + 1)
                        else:
                            val = val + int(self.get_number(part, i + 1))
                    else:
                        val = str(val)
                        val = val + self.get_number(part, i + 1) or "0"

            if type(val) == str:
                val = "'%s'" % val
            data = data[0:x] + str(val) + data[y:]

            timeout = time.time() - t > self.timeout

            if "+" not in data and "(" not in data and ")" not in data:
                return int(self.get_number(data))

    @staticmethod
    def get_number(text, start=0):
        ret = ""
        for ch in text[start:]:
            try:
                int(ch)
            except Exception:
                if ret:
                    break
            else:
                ret += ch
        return ret
