# -*- coding: utf-8 -*-
from core.libs import *


def get_video_url(item):
    logger.trace()
    itemlist = []
    if 'storage.googleapis.com' in item.url or 'storage.cloud.google.com' in item.url:
        # Google Cloud Storage
        itemlist.append(Video(url=item.url))

    else:
        # Google Drive y Google doc
        id = scrapertools.find_single_match(item.url, 'd/(.*?)$')
        try:
            # Video recodificado
            url = "https://docs.google.com/get_video_info?docid=" + id
            data = httptools.downloadpage(url, cookies=False, headers={"Referer": item.url})

            cookies = ''.join(scrapertools.find_multiple_matches(data.headers["set-cookie"],
                                                                 "(DRIVE_STREAM=[^;]+;|NID=[^;]+;)"))

            data = urllib.unquote_plus(urllib.unquote_plus(data.data.decode('unicode-escape')))

            videos_list = scrapertools.find_multiple_matches(scrapertools.find_single_match(data,
                                    'url_encoded_fmt_stream_map=(.*)'),
                                    'itag=(\d+)&url=(.*?)(?:;.*?quality=.*?(?:,|&)|&quality=.*?(?:,|&))')

            res = {'5': '240p', '6': '270p', '17': '144p', '18': '360p', '22': '720p', '34': '360p', '35': '480p',
                 '36': '240p', '37': '1080p', '38': '4k', '43': '360p', '44': '480p', '45': '720p', '46': '1080p',
                 '82': '360p [3D]', '83': '480p [3D]', '84': '720p [3D]', '85': '1080p [3D]', '100': '360p [3D]',
                 '101': '480p [3D]', '102': '720p [3D]',
                 '92': '240p', '93': '360p', '94': '480p', '95': '720p',
                 '96': '1080p', '132': '240p', '151': '72p', '133': '240p', '134': '360p', '135': '480p',
                 '136': '720p', '137': '1080p', '138': '4k', '160': '144p', '264': '1440p',
                 '298': '720p', '299': '1080p', '266': '2160p', '167': '360p', '168': '480p', '169': '720p',
                 '170': '1080p', '218': '480p', '219': '480p', '242': '240p', '243': '360p', '244': '480p',
                 '245': '480p', '246': '480p', '247': '720p', '248': '1080p', '271': '1440p', '272': '4K',
                 '302': '4k', '303': '1080p', '308': '1440p', '313': '4K', '315': '4K', '59': '480p'}

            for itag, url in videos_list:
                type = scrapertools.find_single_match(url, '&mime=video/([^&]+)')
                itemlist.append(Video(url=url+"|Cookie=" + cookies, res=res.get(itag), type=type))

        except:
            itemlist = []

        # Video original
        data = ''
        try:
            url = "https://drive.google.com/uc?export=download&id=%s" % id
            data = httptools.downloadpage(url).data

            data = scrapertools.find_single_match(data, 'href="(/uc\?export=download&confirm=[^&]+&id=[^"]+)"')
            data = httptools.downloadpage(urlparse.urljoin(url, data), only_headers=True, follow_redirects=False)
            url= data.headers['location']

            filename = httptools.downloadpage(url, only_headers=True, follow_redirects=False).headers['content-disposition']
            ext = scrapertools.find_single_match(filename, 'filename="[^"]+\.([^".]+)"')

            itemlist.append(Video(url=url, type=ext, res='Original'))

        except:
            if not itemlist:
                if scrapertools.find_single_match(data,'<title>Google Drive - Cuota superada</title>'):
                    return ResolveError(4)
                else:
                    return ResolveError(0)

    return itemlist
