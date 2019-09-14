# -*- coding: utf-8 -*-
from core.libs import *

def get_video_url(item):
    logger.trace()
    itemlist = []
    
    id = scrapertools.find_single_match(item.url, '[^/]+//[^-]+/([a-z0-9]+)')
    data = httptools.downloadpage(item.url).data
    
    if 'uptobox' in item.url and "Streaming link:" in data:
        item.url = "http://uptostream.com/iframe/" + id
        data = httptools.downloadpage(item.url).data
    
    elif "Video not found" in data:
        item.url = "http://uptobox.com/" + id
        data = httptools.downloadpage(item.url).data
    
    if "Unfortunately, the file you want is not available." in data:
        return ResolveError(0)
    
    if 'uptobox' in item.url:
        matches = scrapertools.find_multiple_matches(data, '<input type="hidden".*?name="([^"]+)".*?value="([^"]*)">')
        post = dict([[k,v] for k,v in matches])
        data = httptools.downloadpage(item.url, post=post).data
        media = scrapertools.find_single_match(data, '<a href="([^"]+)">\s*<span class="button_upload green">')
        url_strip = urllib.quote(media.rsplit('/', 1)[1])
        url = media.rsplit('/', 1)[0] + "/" + url_strip
        itemlist.append(Video(url=url))
    else:
        subtitle = scrapertools.find_single_match(data, "kind='subtitles' src='//([^']+)'")
        if subtitle:
            subtitle = "http://" + subtitle
        
        media = scrapertools.find_multiple_matches(data, "<source src='//([^']+)' type='video/([^']+)' data-res='([^']+)' (?:data-default=\"true\" |)(?:lang='([^']+)'|)")
        for url, tipo, res, lang in media:
            media_url = "http://" + url
            itemlist.append(Video(url=url, res=res, lang=lang[:3]))
            
            
    return itemlist
