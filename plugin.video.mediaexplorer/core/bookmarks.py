# -*- coding: utf-8 -*-
from core.libs import *


def mainlist(item):
    logger.trace()
    itemlist = []

    # Buscamos solo favoritos de este plugin
    for name, thumb, data in read_bookmarks():
        if sys.argv[0] in data:
            url = scrapertools.find_single_match(data, '%s\?([^;]*)' % sys.argv[0]).replace("&quot", "")
            if not url: continue
            item = Item().fromurl(url)
            item.label = name.strip()
            item.type = 'item'
            item.group = False

            # Opciones menu contextual
            item.context = [
                {
                    "label": "Eliminar de favoritos",
                    "context_channel": 'bookmarks',
                    "context_action": 'del_bookmark',
                    "context_id": url
                },
                {
                    "label": "Renombrar",
                    "context_channel": 'bookmarks',
                    "context_action": 'rename_bookmark',
                    "context_id": url
                }
            ]

            itemlist.append(item)
        elif sysinfo.platform_name != 'kodi':
            item = Item().fromurl(data)
            item.label = name
            item.type = 'item'

            # Opciones menu contextual
            item.context = [
                {
                    "label": "Eliminar de favoritos",
                    "context_channel": 'bookmarks',
                    "context_action": 'del_bookmark',
                    "context_id": data
                },
                {
                    "label": "Renombrar",
                    "context_channel": 'bookmarks',
                    "context_action": 'rename_bookmark',
                    "context_id": data
                }
            ]

            itemlist.append(item)

    return itemlist


def read_bookmarks():
    bookmarks_list = []
    if os.path.exists(sysinfo.bookmarks_path):
        data = open(sysinfo.bookmarks_path, 'rb').read()

        matches = scrapertools.find_multiple_matches(data, "(<favourite.*?</favourite>)")
        for match in matches:
            name = scrapertools.find_single_match(match, 'name="([^"]*)"')
            thumb = scrapertools.find_single_match(match, 'thumb="([^"]*)"')
            data = scrapertools.find_single_match(match, '<favourite.*?>([^<>]*)</favourite>')
            bookmarks_list.append((name, thumb, data))

    return bookmarks_list


# Estas funciones solo se utilizan si la plataforma no proporciona metodos propios, como hace Kodi a partir de V17
def save_bookmarks(bookmarks_list):
    logger.trace()

    raw = '<favourites>' + chr(10)
    for name, thumb, data in bookmarks_list:
        raw += '    <favourite name="%s" thumb="%s">%s</favourite>' % (name, thumb, data) + chr(10)
    raw += '</favourites>' + chr(10)

    return filetools.write(sysinfo.bookmarks_path, raw)


def add_bookmark(item):
    logger.trace()

    bookmarks_list = read_bookmarks()

    new_item = item.clone(label=item.label)

    # TODO esto lo he puesto aqui pero no estoy muy seguro, ¿deberian clonarse estos atributos?
    if new_item.context_channel: del new_item.context_channel
    if new_item.context_action: del new_item.context_action
    if new_item.context_id: del new_item.context_id
    if new_item.context: del new_item.context

    if sysinfo.platform_name == 'kodi':
        data = "ActivateWindow(10025,&quot;%s?%s&quot;,return)" % (sys.argv[0], new_item.tourl())
    else:
        data = "%s" % new_item.tourl()

    if data in [f[2] for f in bookmarks_list]:
        # El item ya esta en Favoritos
        platformtools.dialog_notification("Favoritos", "Este elemento ya existe en favoritos")

    else:
        from platformcode import viewtools  # TODO ¿es correcto importar de platformcode?
        name = viewtools.set_label_format(new_item)

        if item.type == 'episode':
            thumb = new_item.thumb or new_item.poster
        else:
            thumb = new_item.poster
        if not thumb.startswith('http'):
            thumb = os.path.join(sysinfo.runtime_path, 'resources', 'images', *thumb.split('/'))

        bookmarks_list.append((name, thumb, data))

        if save_bookmarks(bookmarks_list):
            platformtools.dialog_notification("Favoritos", "%s se ha añadido a favoritos" % name)


def del_bookmark(item):
    logger.trace()

    bookmarks_list = read_bookmarks()
    for fav in bookmarks_list[:]:
        if "%s?%s" % (sys.argv[0], item.context_id) in fav[2] or item.context_id == fav[2]:
            bookmarks_list.remove(fav)

            if save_bookmarks(bookmarks_list):
                platformtools.dialog_notification("Favoritos", "%s se ha eliminado de favoritos" % fav[0])
                platformtools.itemlist_refresh()
            break



def rename_bookmark(item):
    logger.info()

    bookmarks_list = read_bookmarks()
    for i, fav in enumerate(bookmarks_list):
        if "%s?%s" % (sys.argv[0], item.context_id) in fav[2] or item.context_id == fav[2]:
            # abrir el teclado
            new_name = platformtools.dialog_input(fav[0], "Introduzca nuevo título")
            if new_name:
                bookmarks_list[i] = (new_name, fav[1], fav[2])

                if save_bookmarks(bookmarks_list):
                    platformtools.dialog_notification("Favoritos", "%s se ha renombrado como: %s"
                                                      % (fav[0], new_name))
                    platformtools.itemlist_refresh()
            break
