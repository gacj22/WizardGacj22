# -*- coding: utf-8 -*-
from core.libs import *

HOST = 'https://www.porntube.com'

def mainlist(item):
    logger.trace()
    itemlist = list()

    itemlist.append(item.clone(
        action='videos',
        label='Útimos videos',
        type='item',
        url= HOST + '/videos?sort=date&hl=es',
        content_type='videos'
    ))

    itemlist.append(item.clone(
        action='videos',
        label='Los más valorados',
        type='item',
        url=HOST + '/videos?sort=rating&hl=es&time=month',
        content_type='videos'
    ))

    itemlist.append(item.clone(
        action='videos',
        label='Los más vistos',
        type='item',
        url=HOST + '/videos?sort=views&hl=es&time=month',
        content_type='videos'
    ))

    itemlist.append(item.clone(
        action='listcategorias',
        label='Categorias',
        type='item',
        url= HOST + "/api/tag/list?orientation=straight&hl=es&ssr=false",
        content_type='items'
    ))

    itemlist.append(item.clone(
        action='listcanales',
        label='Canales',
        type='item',
        url=HOST + "/api/channel/list?filter=%7B%7D&order=rating&ssr=false&orientation=straigh",
        content_type='items'
    ))

    itemlist.append(item.clone(
        action='listpornstar',
        label='PornStars',
        type='item',
        url=HOST + "/api/pornstar/list?filter=%7B%7D&ssr=false&orientation=straight",
        content_type='items'
    ))

    itemlist.append(item.clone(
        action='search',
        label='Buscar',
        type='search',
        content_type='videos',
        category='adult',
        query=True
    ))


    return itemlist

def listpornstar(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url, headers={'referer': HOST + '/pornstar?hl=es'}).data
    data = jsontools.load_json(data).get('pornstars',{}).get('_embedded',{}).get('items',[])
    logger.debug(data)

    for i in data:
        itemlist.append(item.clone(
            label=i['name'],
            url=HOST + '/pornstars/%s?hl=es' % i['slug'],
            poster= i['thumbUrl'],
            content_type='videos',
            action='videos'))

    return itemlist


def listcanales(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url, headers={'referer': HOST + '/channels?hl=es'}).data
    data = jsontools.load_json(data).get('channels',{}).get('_embedded',{}).get('items',[])

    for i in data:
        itemlist.append(item.clone(
            label=i['name'],
            url=HOST + '/channels/%s?hl=es' % i['slug'],
            poster= i['thumbUrl'],
            content_type='videos',
            action='videos'))

    return itemlist


def listcategorias(item):
    logger.trace()
    itemlist = list()

    data = httptools.downloadpage(item.url, headers={'referer': HOST + '/tags?hl=es'}).data
    data = jsontools.load_json(data).get('tags',{}).get('_embedded',{}).get('items',[])

    for i in data:
        itemlist.append(item.clone(
            label=i['name'],
            url=HOST + '/tags/%s?hl=es' % i['slug'],
            poster= i['thumbDesktop'],
            content_type='videos',
            action='videos'))

    return itemlist


def search(item):
    logger.trace()
    item.url = HOST + "/search?q=%s" % item.query.replace(' ', '+')
    return videos(item)


def videos(item):
    logger.trace()
    itemlist = list()
    threads = list()

    data = httptools.downloadpage(item.url).data
    logger.debug(data)

    patron = '<div class="video-item"><a title="([^"]+)" href="([^"]+)">'
    i = 0
    for title, url  in scrapertools.find_multiple_matches(data, patron):
        new_item = item.clone(
            pos = i,
            action='play',
            title= title,
            url= url,
            folder=False,
            type='video')

        t = Thread(target=get_info,
                   args=[new_item, itemlist])

        t.setDaemon(True)
        t.start()
        threads.append(t)
        i += 1


    while [t for t in threads if t.isAlive()]:
        time.sleep(0.5)

    itemlist = sorted(itemlist, key=lambda x: x.pos)

    next_page = scrapertools.find_single_match(data, '<li class="pagination-item next"><a href="([^"]+)"')
    if itemlist and next_page:
        itemlist.append(item.clone(
            action='videos',
            url=HOST + next_page,
            type='next'
        ))

    return itemlist


def get_info(item, itemlist):
    try:
        if item.query:
            name = scrapertools.find_single_match(item.url, '/videos/([^_]+)_')
            mediaId = item.url.split('_')[1]
        else:
            name, mediaId = scrapertools.find_single_match(item.url, '/videos/([^\?]+)\?hl=es').split('_')

        url = 'https://www.porntube.com/api/videos/%s?ssr=true&slug=%s&hl=es&orientation=straight' % (mediaId, name)
        result = jsontools.load_json(httptools.downloadpage(url).data)

        res = '+'.join([str(e['height']) for e in result['video']['encodings']])

        itemlist.append(item.clone(
                thumb=result['video']['masterThumb'],
                title=(item.title + ' [HD]') if result['video']['isHD'] else item.title,
                url='https://tkn.porntube.com/%s/desktop/%s' % (result['video']['mediaId'], res)
            ))

    except:
        pass


def play(item):
    logger.trace()
    itemlist = list()

    result= jsontools.load_json(httptools.downloadpage(item.url, headers={'origin': HOST}).data)

    for res in sorted(result.keys(),key=int, reverse=True):
        itemlist.append(Video(url=result[res]['token'], res='%sp' % res))

    return itemlist