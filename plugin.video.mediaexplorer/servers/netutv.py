# -*- coding: utf-8 -*-
import random

from core.libs import *


def get_video_url(item):
    logger.trace()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    script = jswise(scrapertools.find_single_match(data, "<script>\s*;?(eval.*?)</script>"))
    data_ip = httptools.downloadpage('http://hqq.tv/player/ip.php?type=json&rand=%s' % str(random.random())[2:]).data

    params = {
        'iss': scrapertools.find_single_match(data_ip, 'iss="([^"]+)"'),
        'vid': scrapertools.find_single_match(script, "videokeyorig='([^']+)"),
        'at': scrapertools.find_single_match(script, "attoken='([^']+)")
    }

    url = 'https://hqq.tv/sec/player/embed_player_%s.php?%s' % (str(random.random())[2:], urllib.urlencode(params))
    data_player = httptools.downloadpage(url).data
    js_wise = jswise(scrapertools.find_single_match(data_player, "<script>\s*;?(eval.*?)</script>"))

    if not js_wise:  # reCaptcha
        site_key = scrapertools.find_single_match(data_player, "'sitekey' : '([^']+)'")
        result = platformtools.show_recaptcha(item.url, site_key)

        if not result:
            return ResolveError(7)

        params['g-recaptcha-response'] = result
        url = 'https://hqq.tv/sec/player/embed_player_%s.php?%s' % (str(random.random())[2:], urllib.urlencode(params))
        data_player = httptools.downloadpage(url).data
        js_wise = jswise(scrapertools.find_single_match(data_player, "<script>\s*;?(eval.*?)</script>"))

    variables = {k: v for (k, v) in scrapertools.find_multiple_matches(js_wise, 'var ([^\W]+)\s?=\s?"([^"]+)"')}
    unescape = urllib.unquote(
        ''.join(scrapertools.find_multiple_matches(data_player, 'document.write\(unescape\("([^"]+)"')))

    params = {
        'ver': 2,
        'b': 1,
        'vid': scrapertools.find_single_match(unescape, '&vid="\+encodeURIComponent\("([^"]+)'),
        'adb': '0',
        'at': scrapertools.find_single_match(unescape, 'var at = "([^"]+)"'),
        'ext': '.mp4.m3u8',
        'link_1': variables.get(scrapertools.find_single_match(unescape, '&link_1="\+encodeURIComponent\(([^\W]+)')),
        'server_2': variables.get(scrapertools.find_single_match(unescape, '&server_2="\+encodeURIComponent\(([^\W]+)'))
    }

    link_m3u8 = httptools.downloadpage("https://hqq.tv/player/get_md5.php?%s" % urllib.urlencode(params),
                                       headers={'Accept':'*/*'},
                                       follow_redirects=False,
                                       only_headers=True).headers.get('location', '')

    if not link_m3u8:
        return ResolveError(6)

    elif 'no_video.mp4' in link_m3u8:
        return ResolveError(1)

    else:
        itemlist.append(Video(url=link_m3u8, ext='m3u8'))
        return itemlist


def jswise(wise):
    def js_wise(code):
        w, i, s, e = code

        v0 = 0
        v1 = 0
        v2 = 0
        v3 = []
        v4 = []

        while True:
            if v0 < 5:
                v4.append(w[v0])
            elif v0 < len(w):
                v3.append(w[v0])
            v0 += 1
            if v1 < 5:
                v4.append(i[v1])
            elif v1 < len(i):
                v3.append(i[v1])
            v1 += 1
            if v2 < 5:
                v4.append(s[v2])
            elif v2 < len(s):
                v3.append(s[v2])
            v2 += 1
            if len(w) + len(i) + len(s) + len(e) == len(v3) + len(v4) + len(e):
                break

        v5 = "".join(v3)
        v6 = "".join(v4)
        v1 = 0
        v7 = []

        for v0 in range(0, len(v3), 2):
            v8 = -1
            if ord(v6[v1]) % 2:
                v8 = 1
            v7.append(chr(int(v5[v0:v0 + 2], 36) - v8))
            v1 += 1
            if v1 >= len(v4):
                v1 = 0
        return "".join(v7)

    # loop2unobfuscated
    ret = None
    while True:
        wise = re.search("var\s.+?\('([^']+)','([^']+)','([^']+)','([^']+)'\)", wise, re.DOTALL)
        if not wise:
            break
        ret = wise = js_wise(wise.groups())
    return ret

