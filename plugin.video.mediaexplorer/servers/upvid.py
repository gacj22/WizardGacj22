# -*- coding: utf-8 -*-
import base64
import js2py
from core.libs import *
from lib import aadecode


def get_video_url(item):
    logger.trace()
    itemlist = list()

    url = item.url
    data = httptools.downloadpage(url).data

    if 'File Not Found' in data:
        return ResolveError(0)

    headers = {'referer': url}
    for i in range(0, 3):
        if 'ﾟωﾟﾉ' in data:
            break
        else:
            url = scrapertools.find_single_match(data, '"iframe" src="([^"]+)')
            if not url:
                url = scrapertools.find_single_match(data, '<input type="hidden" id="link" value="([^"]+)')
        data = httptools.downloadpage(url, headers=headers).data

    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    try:
        text_decode = aadecode.decode(scrapertools.find_single_match(data, '(?s)<script>\s*ﾟωﾟ(.*?)</script>').strip())
        clave = scrapertools.find_single_match(text_decode, "func\.innerHTML\s?=[^(]+\('([^']+)")
        func = base64.b64decode(scrapertools.find_single_match(data, '<input type="hidden" value="([^"]+)" id="func"'))

        js = base64.b64decode(scrapertools.find_single_match(data, '<input type="hidden" value="([^"]+)" id="js"'))
        res = js2py.eval_js(re.sub(r'function (\w+)', 'function res', js))

        itemlist.append(
            Video(url=scrapertools.find_single_match(res(clave,func), "source.setAttribute\('src', '([^']+)'")))

        return itemlist
    except Exception, e:
        return e
