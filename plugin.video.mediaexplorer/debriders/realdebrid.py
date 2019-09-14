# -*- coding: utf-8 -*-
from core.libs import *


def get_video_url(item):
    logger.trace()
    itemlist = []
    headers = {}

    account = settings.get_setting('account', __file__)
    user = settings.get_setting('user', __file__)
    password = settings.get_setting('password', __file__)
    token = settings.get_setting('token', __file__)

    if not account:
        return ResolveError(2)

    if not token:
        token = get_token(user, password)

    post = {
        'link': item.url,
        'password': item.password
    }

    headers['Authorization'] = 'Bearer %s' % token
    data = jsontools.load_json(
        httptools.downloadpage('https://api.real-debrid.com/rest/1.0/unrestrict/link', post=post, headers=headers).data)

    if data.get('error') == 'bad_token':
        headers['Authorization'] = 'Bearer %s' % get_token(user, password)
        data = jsontools.load_json(
            httptools.downloadpage('https://api.real-debrid.com/rest/1.0/unrestrict/link', post=post,
                                   headers=headers).data)

    if data.get('download'):
        if data.get('alternative'):
            for link in data["alternative"]:
                itemlist.append(Video(url=link["download"]))
        else:
            itemlist.append(Video(url=data["download"]))
    else:
        itemlist = ResolveError(data['error'])

    return itemlist


def get_token(user, password):
    logger.trace()
    headers = {
        'referer': 'https://real-debrid.com/',
        'X-Requested-With': 'XMLHttpRequest'
    }

    params = {
        'pass': password,
        'time': time.time(),
        'user': user
    }
    data = jsontools.load_json(
        httptools.downloadpage('https://real-debrid.com/ajax/login.php?' + urllib.urlencode(params),
                               headers=headers).data)

    if data.get('cookie'):
        data = httptools.downloadpage('https://real-debrid.com/apitoken', headers=headers).data

        while Real.check(data):
            data = Real.decode(data)

        token = scrapertools.find_single_match(data, "value\s*=\s*'([^']+)'")
        settings.set_setting('token', token, __file__)
        return token
    else:
        logger.debug('Error al obtener el token')
        return ''


class Real(object):
    @staticmethod
    def check(string):
        import re
        return re.compile("eval\(function\(r,e,a,l.+?}\('([^']+)','([^']+)','([^']+)','([^']+)'\)\)").search(string)

    @staticmethod
    def decode(string):
        import re
        r, e, a, l = \
            re.compile("eval\(function\(r,e,a,l.+?}\('([^']+)','([^']+)','([^']+)','([^']+)'\)\)").findall(string)[0]
        x = 0
        y = 0
        z = 0
        t = []
        token = []
        while True:
            if x < 5:
                token.append(r[x])
            elif x < len(r):
                t.append(r[x])
            x += 1
            if y < 5:
                token.append(e[y])
            elif y < len(e):
                t.append(e[y])
            y += 1
            if z < 5:
                token.append(a[z])
            elif z < len(a):
                t.append(a[z])
            z += 1
            if len(r) + len(e) + len(a) + len(l) == len(t) + len(token) + len(l):
                break
        d = ''.join(t)
        k = ''.join(token)
        y = 0
        bearer = []
        for x in range(0, len(t), 2):
            c = -1
            if ord(k[y]) % 2:
                c = 1
            bearer.append(chr(int(d[x: x + 2], 32) - c))
            y += 1
            if y >= len(token):
                y = 0
        return ''.join(bearer)
