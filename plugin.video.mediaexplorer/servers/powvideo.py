# -*- coding: utf-8 -*-

import js2py
from core.libs import *


def get_video_url(item):
    logger.trace()
    itemlist = []

    referer = item.url.replace('iframe', 'preview')

    httptools.downloadpage(referer)
    data = httptools.downloadpage(item.url, headers={'referer': referer}).data

    if data == "File was deleted" in data:
        return ResolveError(0)
    elif 'Video is processing now.' in data:
        return ResolveError(1)

    unpacked = js2py.eval_js(
        scrapertools.find_single_match(data, "<script type=[\"']text/javascript[\"']>eval(.*?)</script>"))

    url = scrapertools.find_single_match(unpacked, "src:'([^']+\.mp4)")
    script = scrapertools.find_multiple_matches(data, '(var _[0-9a-z]+=.*?\n)')[1]
    script = re.compile("(_[0-9a-z]+)=\$(\[[^\]]+])\(_[0-9a-z]+,", re.IGNORECASE).sub(
        lambda x: x.group(1) + '=' + x.group(1) + x.group(2) + '(', script)

    data = {}

    def J(name, value):
        name = name.to_python()
        value = value.to_python()

        if name == 'body':
            return {'data': J}
        elif value:
            data[name] = value
        else:
            return data.get(name)

    a = js2py.EvalJs({'$': J})

    def _map(e, t, n):
        s = []
        for o in range(len(e)):
            i = t(e[o], o, n)
            s.append(i)
        return s

    a['$'].map = _map

    url = a.eval(script + "var source = new Array ({file:'%s'}); source.size(); source[0]['file']" % url)

    itemlist.append(Video(url=url))

    return itemlist
