# -*- coding: utf-8 -*-
from core.libs import *


def get_video_url(item):
    logger.trace()
    itemlist = list()

    url = item.url.replace("https://jetload.net/e/", "https://jetload.net/api/get_direct_video/")
    data = httptools.downloadpage(url).data

    try:
        params = jsontools.load_json(data)
        #logger.debug(params)
        params_type = params['type']
        params_file = params['file']
        params_server = params.get('server', dict())
    except:
        return ResolveError(6)

    if params_type == 'deleted':
        return ResolveError(0)

    if params_type == 'pending':
        return ResolveError(1)

    if params_file['file_subtitle']: # TODO subtitles
        #subtitles = httptools.downloadpage('https://jetload.net/api/get/subtitles/%s' % params_file['id']).data
        logger.debug('Jetload subtitle: %s' % url) # Only for debug

    if params_type == 'mp4':
        url = httptools.downloadpage('https://jetload.net/api/download', post={
            'file_name': '%s.mp4' % (params_file['file_name']),
            'srv': params_file['srv_id']
        }).data
        itemlist.append(Video(url=url, res='Original', type='mp4'))

    else:
        url = httptools.downloadpage('https://jetload.net/api/download', post={
            'file_name': '%s.%s' % (params_file['file_name'], params_file['file_ext']),
            'srv': params_file['srv_id']
        }).data
        itemlist.append(Video(url=url, res='Original', type=params_file['file_ext']))


    if params_file.get('encoding_status') == 'completed':
        if params_file.get('archive') == 1:
            url = params_server['hostname'] + '/v2/schema/archive/' + params_file['file_name']
        else:
            url = params_server['hostname'] + '/v2/schema/' + params_file['file_name']

        data = httptools.downloadpage(url+ '/master.m3u8').data
        for res, name, ext in scrapertools.find_multiple_matches(data, 'RESOLUTION=\d+x(\d+)(.*?)\.(\w+)'):
            #logger.debug('%s/%s.%s' % (url, name.strip(), ext))
            itemlist.append(Video(url='%s/%s.%s' %(url, name.strip(), ext), res=res + 'p', type=ext))


    return itemlist
