# -*- coding: utf-8 -*-

from core.libs import *
import js2py


def get_video_url(item):
    logger.trace()
    itemlist = []

    data = httptools.downloadpage(item.url, headers={'Referer': item.referer}).data

    if 'Video is processing now' in data:
        return ResolveError(1)

    if data == "File was deleted":
        return ResolveError(0)

    unpacked = js2py.eval_js(
        scrapertools.find_single_match(data, "<script type=[\"']text/javascript[\"']>eval(.*?)</script>"))

    url = scrapertools.find_single_match(unpacked, '(http[^,]+\.mp4)')
    script = scrapertools.find_single_match(data, '(var _[0-9a-z]+=.*?\n)')
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
    url = a.eval(script + "var source = new Array ('%s'); source.size()[0];" % url)

    itemlist.append(Video(url=url))

    return itemlist
