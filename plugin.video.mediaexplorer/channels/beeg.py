# -*- coding: utf-8 -*-
from core.libs import *

url_api = settings.get_setting('url_api', __file__)


def get_api_url():
    logger.trace()

    global url_api

    data = httptools.downloadpage('http://beeg.com').data
    version = re.compile('var beeg_version = ([\d]+)').findall(data)[0]

    url_api = 'https://beeg.com/api/v6/%s' % version
    settings.set_setting('url_api', url_api, __file__)


def mainlist(item):
    logger.trace()
    get_api_url()
    itemlist = list()

    itemlist.append(item.clone(
        action='videos',
        label='Útimos videos',
        url=url_api + '/index/main/0/pc',
        content_type='videos'
    ))

    itemlist.append(item.clone(
        action='listcategorias',
        label='Listado categorias',
        url=url_api + '/index/main/0/pc',
        content_type='items'
    ))

    itemlist.append(item.clone(
        action='search',
        label='Buscar',
        content_type='items',
        category='adult',
        query=True
    ))

    return itemlist


def videos(item):
    logger.trace()
    itemlist = list()

    json_data = jsontools.load_json(httptools.downloadpage(item.url).data)

    for video in json_data['videos']:
        itemlist.append(item.clone(
            action='play',
            title=video['title'],
            url= '%s/video/%s?v=2&s=%s&e=%s' % (url_api, video['svid'], video['start'], video['end']),
            thumb='http://img.beeg.com/236x177/%s.jpg' % video['id'],
            folder=True,
            type='video'
        ))

    page = int(scrapertools.find_single_match(item.url, url_api + '/index/[^/]+/([0-9]+)/pc'))

    if json_data['pages'] - 1 > page:
        itemlist.append(item.clone(
            action='videos',
            url=item.url.replace('/' + str(page) + '/', '/' + str(page + 1) + '/'),
            type='next'
        ))

    return itemlist


def listcategorias(item):
    logger.trace()
    itemlist = list()

    json_data = jsontools.load_json(httptools.downloadpage(item.url).data)

    for tag in json_data['tags']:
        itemlist.append(item.clone(
            action='videos',
            label=tag['tag'].capitalize(),
            url=url_api + '/index/tag/0/pc?tag=' + tag['tag'],
            content_type='videos',
            type='item'
        ))

    return itemlist


def search(item):
    logger.trace()
    itemlist = list()

    item.url = url_api + '/suggest?q=%s' % item.query
    json_data = jsontools.load_json(httptools.downloadpage(item.url).data)

    for tag in json_data['items']:
        itemlist.append(item.clone(
            action='videos',
            label=tag['name'].capitalize(),
            url=url_api + '/index/tag/0/pc?tag=' + tag['name'],
            content_type='videos',
            type='item'
        ))

    return itemlist


def play(item):
    logger.trace()
    itemlist = list()

    json_data = jsontools.load_json(httptools.downloadpage(item.url).data)

    for key in json_data:
        video_list = re.compile('([0-9]+p)', re.DOTALL).findall(key)
        if video_list:
            video = video_list[0]
            if json_data[video] is not None:
                url = json_data[video].replace('{DATA_MARKERS}', 'data=pc.ES')

                if not url.startswith('https:'):
                    url = 'https:' + url

                itemlist.append(Video(url=url, res=video))

    return sorted(itemlist, key=lambda x: int(x.res[:-1]) if x.res else 0, reverse=True)
