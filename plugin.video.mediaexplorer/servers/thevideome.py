# -*- coding: utf-8 -*-
from core.libs import *

def get_video_url(item):
    logger.trace()
    itemlist = []

    location = httptools.downloadpage(item.url, follow_redirects=False, only_headers=True).headers.get("location", "")

    api_data = jsontools.load_json(httptools.downloadpage(
        "https://vev.io/api/serve/video/" + scrapertools.find_single_match(location, "embed/([A-z0-9]+)"),post={}).data)

    videos = api_data.get('qualities', {})
    if videos:
        for res, url in videos.items():
            itemlist.append(Video(url=url, res=res))

    elif api_data.get('code') == 400:
        return ResolveError(0)

    else:
        logger.debug(api_data)

    return itemlist