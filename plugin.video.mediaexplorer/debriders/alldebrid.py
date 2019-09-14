# -*- coding: utf-8 -*-
from core.libs import *


def get_video_url(item):
    logger.trace()
    itemlist = list()

    account = settings.get_setting('account', __file__)
    user = settings.get_setting('user', __file__)
    password = settings.get_setting('password', __file__)

    if not account:
        return ResolveError(2)

    url = 'http://www.alldebrid.com/service.php?pseudo=%s&password=%s&link=%s&nb=0&json=true' % (
        user,
        password,
        item.url
    )

    data = jsontools.load_json(httptools.downloadpage(url).data)

    if data.get("link") and not data.get("error"):
        itemlist.append(Video(url=data["link"]))
    else:
        itemlist = ResolveError(data['error'])

    return itemlist
