# -*- coding: utf-8 -*-
from core.libs import *
import js2py


class Cloudflare:
    def __init__(self, response):
        self.timeout = 5
        self.domain = urlparse.urlparse(response["url"])[1]
        self.protocol = urlparse.urlparse(response["url"])[0]
        self.response = response

        pattern = r'var s,t,o,p,b,r,e,a,k,i,n,g,f, (?P<var>([^=]+)=\{"[^"]+":[^}]+\};).*?(?P<ops>\2.*?)' \
                  r'a.value = (?P<res>\(.*?\).toFixed\(\d+\);).*?, (?P<wait>\d+)\);.*?' \
                  r'<form id="challenge-form" action="(?P<auth_url>[^"]+)" method="get">.*?' \
                  r'<input type="hidden" name="s" value="(?P<s>[^"]+)[^<]+</input>[^<]+' \
                  r'<input type="hidden" name="jschl_vc" value="(?P<jschl_vc>[^"]+)[^<]+' \
                  r'<input type="hidden" name="pass" value="(?P<pass>[^"]+)"/>.*?' \
                  r'</form>\s+(<div style="display:none;visibility:hidden;" id="cf-dn-[^"]+">(?P<div>[^<]+)</div>)?'

        match = re.compile(pattern, re.DOTALL).search(response['data'])
        if match:
            self.js_data = {
                "auth_url": match.group('auth_url'),
                "params": {
                    "s": match.group('s'),
                    "jschl_vc": match.group('jschl_vc'),
                    "pass": match.group('pass'),
                },
                "res": match.group('res'),
                "div": match.group('div') or '',
                "var": match.group('var'),
                "ops": match.group('ops'),
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
        return self.response['code'] == 503 and bool(self.header_data or self.js_data)

    def get_url(self):
        # Metodo #1 (javascript)
        if self.js_data:
            ops = self.js_data['ops']

            ops = re.sub(
                r'function\(p\){return.*?\}\((.*?)\)\)\);',
                lambda x: str(ord(self.domain[int(js2py.eval_js(x.group(1)))])) + '));',
                ops
            )
            ops = re.sub(
                r'function\(p\){var p =.*?\}\(\)',
                self.js_data['div'],
                ops
            )
            jschl_answer = 'var t="%s";\nvar %s\n%s\n%s' % (self.domain, self.js_data["var"], ops, self.js_data['res'])
            self.js_data["params"]["jschl_answer"] = js2py.eval_js(jschl_answer)

            response = "%s://%s%s?%s" % (
                self.protocol,
                self.domain,
                self.js_data["auth_url"],
                urllib.urlencode(self.js_data["params"])
            )

            time.sleep(self.js_data["wait"])
            # For debug
            #self.save_html()
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

    def save_html(self):
        fname = self.js_data["params"]["jschl_answer"]
        data = self.response['data']
        data = data.replace("<a href='/'>x</a>", "<a href='%s://%s/'>x</a>" % (self.protocol, self.domain))
        data = data.replace('action="/cdn-cgi/l/chk_jschl"', 'action="%s://%s/cdn-cgi/l/chk_jschl"' % (self.protocol, self.domain))
        open(os.path.join(sysinfo.data_path, fname + '.html'), 'wb').write(data)
