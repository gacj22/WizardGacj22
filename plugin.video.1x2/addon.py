# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

from libs.tools import *


def mainmenu(item):
    itemlist = list()

    # Arenavision
    itemlist.append(item.clone(
        label='Arenavision',
        channel='arenavision',
        action='mainmenu',
        icon=os.path.join(image_path, 'arenavisionlogo1.png')
    ))

    # Sport365
    itemlist.append(item.clone(
        label='Sport365',
        channel='sport365',
        action='mainmenu',
        icon=os.path.join(image_path, 'sport365_logo.png')
    ))

    itemlist.append(item.clone(
        label='Ajustes',
        action='open_settings',
        plot='Menu de configuración'
    ))

    '''itemlist.append(item.clone(
        label='label',
        action=None
    ))'''


    return itemlist


def run(item):
    logger('run item: %s' % item, 'info')
    itemlist = list()
    channel = None

    if not item.action:
        logger("Item sin acción")
        return

    if item.channel and os.path.isfile(os.path.join(runtime_path, item.channel + '.py')):
        try:
            if item.channel in sys.modules:
                reload(sys.modules[item.channel])
            channel = __import__(item.channel, None, None, [item.channel])
        except:
            channel = None

    if hasattr(channel, item.action):
        result = getattr(channel, item.action)(item)
        if isinstance(result,list):
            itemlist = result
        elif isinstance(result, dict):
            if result['action'] == 'refresh':
                xbmc.executebuiltin("Container.Refresh")

            elif result['action'] == 'play':
                play(result)
                return
    else:
        if item.action == 'play':
            play({'VideoPlayer':'directo',
                  'url': item.url,
                  'titulo': item.title or item.label})
            return

        elif item.action == 'mainmenu':
            itemlist = mainmenu(item)

        elif item.action == 'open_settings':
            xbmcaddon.Addon(id=sys.argv[0][9:-1]).openSettings()

    if itemlist:
        for item in itemlist:
            listitem = xbmcgui.ListItem(item.label or item.title)
            listitem.setInfo('video', {'title': item.label or item.title, 'mediatype': 'video'})
            if item.plot:
                listitem.setInfo('video', {'plot': item.plot})
            for n,v in item.getart():
                listitem.setArt({n: v})

            if item.action == 'play':
                listitem.setProperty('IsPlayable', 'true')
                isFolder = False

            elif isinstance(item.isFolder, bool):
                isFolder = item.isFolder

            else:
                isFolder = True

            xbmcplugin.addDirectoryItem(
                handle=int(sys.argv[1]),
                url='%s?%s' % (sys.argv[0], item.tourl()),
                listitem=listitem,
                isFolder= isFolder,
                totalItems=len(itemlist)
            )

        xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)


def play(video_item):
    logger(video_item)

    listitem = xbmcgui.ListItem()
    listitem.setInfo('video', {'title': video_item['titulo']})
    listitem.setProperty('IsPlayable', 'true')

    if video_item['VideoPlayer'] == 'Directo':
        listitem.setPath(video_item['url'])

    elif video_item['VideoPlayer'] == 'plexus':
        url = 'plugin://program.plexus/?mode=1&url=acestream://%s&name=Arenavision %s' % \
              (video_item['url'], video_item['titulo'])
        listitem.setPath(url)

    elif video_item['VideoPlayer'] == 'InputStream':
        listitem.setProperty('inputstreamaddons', 'inputstream.adaptive')
        listitem.setMimeType('application/vnd.apple.mpegurl')
        listitem.setProperty('inputstream.adaptive.manifest_type', video_item['manifest_type'])
        listitem.setProperty('inputstream.adaptive.stream_headers', video_item['headers'])
        listitem.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
        listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
        listitem.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        listitem.setProperty('inputstream.adaptive.manifest_type', 'mpdURL')
        listitem.setProperty('inputstream.adaptive.license_key', 'sport_key')
        listitem.setProperty('inputstream.adaptive.license_key', 'licURL')
        listitem.setMimeType('application/dash+xml')
        listitem.setPath(video_item['url'])

    elif video_item['VideoPlayer'] == 'Streamlink':
        import streamlink.session
        session = streamlink.session.Streamlink()
        session.set_option("http-headers", video_item['headers'])
        streams = session.streams(video_item['url'])
        stream_url = streams['best'].to_url() + '|' + video_item['headers']
        listitem.setPath(stream_url)

    elif video_item['VideoPlayer'] == 'F4mtester':
            stream_url = 'plugin://plugin.video.f4mTester/?streamtype=HLSRETRY&url={0}&name={1}'.format(
                urllib.quote_plus(stream_url), urllib.quote_plus(orig_title))
            liz.setPath(stream_url)
            idle()
            try:
                xbmc.executebuiltin('RunPlugin(' + stream_url + ')')
            except BaseException:
                pass
            xbmcplugin.setResolvedUrl(addon_handle, False, liz)
            listitem.setPath(url)

    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)


if __name__ == '__main__':
    if sys.argv[2]:
        item = Item().fromurl(sys.argv[2])
    else:
        item = Item(action='mainmenu', icon=os.path.join(image_path, 'red_config.png'))

    run(item)