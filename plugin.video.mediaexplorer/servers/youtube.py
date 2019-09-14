# -*- coding: utf-8 -*-

from core.libs import *

fmt_value = {
    5: ['240p', 'flv'],
    6: ['240p', 'flv'],
    18: ['360p', 'mp4'],
    22: ['720p', 'mp4'],
    26: ['???', '???'],
    33: ['???', '???'],
    34: "['360p', 'flv']",
    35: ['480p', 'flv'],
    36: ['???', '3gpp'],
    37: ['1080p', 'mp4'],
    38: ['4k', 'mp4'],
    43: ['360p', 'webm'],
    44: ['480p', 'webm'],
    45: ['720p', 'webm'],
    46: ['1080p', 'webm'],
    59: ['480p', 'mp4'],
    78: ['480p', 'mp4'],
    82: ['360p', '3D'],
    83: ['480p', '3D'],
    84: ['720p', '3D'],
    85: ['1080p', '3D'],
    100: ['360p', '3D'],
    101: ['480p', '3D'],
    102: ['720p', '3D']
}


def get_video_url(item):
    logger.trace()
    itemlist = []

    video_id = scrapertools.find_single_match(item.url, 'v=([A-z0-9_-]{11})')

    url = 'http://www.youtube.com/get_video_info?video_id=%s&eurl=https://youtube.googleapis.com/v/%s&ssl_stream=1' % (
        video_id,
        video_id
    )
    data = httptools.downloadpage(url).data
    params = dict(urlparse.parse_qsl(data))

    if params.get('hlsvp'):
        itemlist.append(Video(type='Live', url=params['hlsvp']))
        return itemlist

    if params.get('dashmpd') and params.get('use_cipher_signature', '') != 'True':
        itemlist.append(Video(type='MPD', url=params['dashmpd'], mpd=True))

    js_signature = ""
    youtube_page_data = httptools.downloadpage("http://www.youtube.com/watch?v=%s" % video_id).data
    params = extract_flashvars(youtube_page_data)
    if params.get('url_encoded_fmt_stream_map'):
        data_flashvars = params["url_encoded_fmt_stream_map"].split(",")
        for url_desc in data_flashvars:
            url_desc_map = dict(urlparse.parse_qsl(url_desc))
            if not url_desc_map.get("url") and not url_desc_map.get("stream"):
                continue

            try:
                key = int(url_desc_map["itag"])
                if not fmt_value.get(key):
                    continue

                if url_desc_map.get("url"):
                    url = urllib.unquote(url_desc_map["url"])
                elif url_desc_map.get("conn") and url_desc_map.get("stream"):
                    url = urllib.unquote(url_desc_map["conn"])
                    if url.rfind("/") < len(url) - 1:
                        url += "/"
                    url += urllib.unquote(url_desc_map["stream"])
                elif url_desc_map.get("stream") and not url_desc_map.get("conn"):
                    url = urllib.unquote(url_desc_map["stream"])

                if url_desc_map.get("sig"):
                    url += "&signature=" + url_desc_map["sig"]
                elif url_desc_map.get("s"):
                    sig = url_desc_map["s"]
                    if not js_signature:
                        urljs = scrapertools.find_single_match(youtube_page_data, '"assets":.*?"js":\s*"([^"]+)"')
                        urljs = urljs.replace("\\", "")
                        if urljs:
                            if not re.search(r'https?://', urljs):
                                urljs = urlparse.urljoin("https://www.youtube.com", urljs)
                            data_js = httptools.downloadpage(urljs).data
                            from jsinterpreter import JSInterpreter
                            funcname = scrapertools.find_single_match(data_js, '\.sig\|\|([A-z0-9$]+)\(')
                            if not funcname:
                                funcname = scrapertools.find_single_match(data_js, '["\']signature["\']\s*,\s*'
                                                                                   '([A-z0-9$]+)\(')
                            jsi = JSInterpreter(data_js)
                            js_signature = jsi.extract_function(funcname)

                    signature = js_signature([sig])
                    url += "&signature=" + signature
                url = url.replace(",", "%2C")
                itemlist.append(Video(type=fmt_value[key][1], res=fmt_value[key][0], url=url))
            except:
                logger.error()


    return itemlist


def remove_additional_ending_delimiter(data):
    pos = data.find("};")
    if pos != -1:
        data = data[:pos + 1]
    return data


def normalize_url(url):
    if url[0:2] == "//":
        url = "http:" + url
    return url


def extract_flashvars(data):
    assets = 0
    flashvars = {}
    found = False

    for line in data.split("\n"):
        if line.strip().find(";ytplayer.config = ") > 0:
            found = True
            p1 = line.find(";ytplayer.config = ") + len(";ytplayer.config = ") - 1
            p2 = line.rfind(";")
            if p1 <= 0 or p2 <= 0:
                continue
            data = line[p1 + 1:p2]
            break
    data = remove_additional_ending_delimiter(data)

    if found:
        data = jsontools.load_json(data)
        if assets:
            flashvars = data["assets"]
        else:
            flashvars = data["args"]

    for k in ["html", "css", "js"]:
        if k in flashvars:
            flashvars[k] = normalize_url(flashvars[k])

    return flashvars
