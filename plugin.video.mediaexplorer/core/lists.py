# -*- coding: utf-8 -*-
from core import snipt
from core.libs import *


def mainlist(item):
    logger.trace()
    itemlist = list()

    # Mi lista
    snipt_username = settings.get_setting('snipt_username', __file__)
    snipt_apikey = settings.get_setting('snipt_apikey_password', __file__)
    snipt_id = settings.get_setting('snipt_id', __file__)

    if not (snipt_username and snipt_apikey and snipt_id):
        line1 = "Para utilizar las listas personales es necesario tener una cuenta registrada."
        line2 = "Introduzca sus datos, si ya esta registrado, unos nuevos o dejelos en blanco para crear una cuenta. " \
                "¿Desea configurar ahora su cuenta?"
        if platformtools.dialog_yesno('MediaExplorer - Mi Lista', line1, line2) and \
                platformtools.show_settings(title="Mi Lista", callback="config_callback"):
                    snipt_username = settings.get_setting('snipt_username', __file__)
                    snipt_apikey = settings.get_setting('snipt_apikey_password', __file__)
                    snipt_id = settings.get_setting('snipt_id', __file__)


    if not (snipt_username and snipt_apikey and snipt_id):
        itemlist.append(item.clone(
            action="config",
            label="Configurar Mi Lista",
            folder=False,
            category='all',
            type='setting'
        ))
        
    else:      
        # Comprobar si hemos de reconvertir la lista Friendpaste
        my_list_id = settings.get_setting('my_list_id', __file__)
        if  my_list_id:
            lista = httptools.downloadpage("https://friendpaste.com/%s/raw" % my_list_id).data
            if lista and (lista == 'lista_vacia'  or
                        (len(lista) > 15 and lista[0] == '[' and lista[-1] == ']' and
                         snipt.update(snipt_username, snipt_apikey, snipt_id, lista))):
                settings.pop_setting("my_list_id", __file__)
                settings.pop_setting("my_list_code", __file__)
                settings.pop_setting("remote_lists", __file__)

                    
        # Mi Lista
        lista = snipt.read(snipt_id)

        if lista and len(lista) > 10:
            label_extra = {"sublabel": " (ID: %s)" % snipt_id, "color": "color2", "value": "True"}
            action = "categories"
        else:
            label_extra = {"sublabel": " (ID: %s) -Vacia-" % snipt_id, "color": "color2", "value": "True"}
            action = None

        itemlist.append(item.clone(
            label="Mi lista",
            label_extra=label_extra,
            action=action,
            type="item",
            content_type='items',
            list_id=snipt_id,
            poster="http://www.codigos-qr.com/qr/php/qr_img.php?d=%s&s=4&e=" % snipt_id,
            context=[{'label': "Configurar 'Mi Lista'", "context_action": 'config'}]
        ))
        
        # Listas remotas
        remote_lists = settings.get_setting('snipt_remote_lists', __file__) or {}
        if remote_lists:
            itemlist.append(item.clone(
                type='label',
                label="Listas remotas:"
            ))
            
            itemlist_remotes = []
            for id, name in remote_lists.items():
                itemlist_remotes.append(item.clone(
                    label=name,
                    action="categories",
                    type="item",
                    content_type='items',
                    group=True,
                    context=[
                        {"label": "Eliminar lista", "context_action": 'remove_list'},
                        {"label": "Cambiar nombre", "context_action": 'rename_list'}
                    ],
                    list_id=id
                ))
            itemlist_remotes.sort(key=lambda x: x.label)
            itemlist.extend(itemlist_remotes)
    
        # Otras opciones
        itemlist.append(item.clone(
            type='label',
            label=""
        ))
        itemlist.append(item.clone(
            label="Añadir nueva lista",
            action="add_list",
            type="highlight"
        ))
    
    return itemlist


def categories(item):
    logger.trace()
    itemlist = list()
    movies = list()
    tvshows = list()

    lista = snipt.read(item.list_id)
    if lista and  lista[0] == '[' and lista[-1] == ']':
        for i in eval(lista):
            new_item = Item().fromurl(i)
            if new_item.type == 'movie':
                movies.append(new_item.clone())
            else:
                tvshows.append(new_item.clone())

        if item.label_extra: del item.label_extra
        if item.description: del item.description

        if movies:
            itemlist.append(item.clone(
                label='Películas (%s)' % (len(movies)),
                action='show_list',
                category='movie',
                group=True,
                poster='poster/movie.png',
                icon='icon/movie.png',
                thumb='thumb/movie.png',
                content_type='movies'))

        if tvshows:
            itemlist.append(item.clone(
                label='Series (%s)' % (len(tvshows)),
                action='show_list',
                category='tvshow',
                group=True,
                poster='poster/tvshow.png',
                icon='icon/tvshow.png',
                thumb='thumb/tvshow.png',
                content_type='tvshows'))

        if itemlist:
            itemlist.insert(0, Item(
                type='label',
                label=item.label,
                poster=item.poster
            ))


    elif item.list_id != settings.get_setting('snipt_id', __file__):
        # Lista eliminada o vacia
        if platformtools.dialog_yesno("Lista: %s" % item.label,
                                      "Esta lista parece que ha sido borrada o esta vacía.",
                                      "¿Desea eliminarla de su listado?"):
            remove_list(item)
            return

    return itemlist


def show_list(item):
    logger.trace()
    itemlist = list()

    my_list_id = settings.get_setting('snipt_id', __file__)

    lista = snipt.read(item.list_id)
    if lista and lista[0] == '[' and lista[-1] == ']':
        for i in eval(lista):
            new_item = Item().fromurl(i)
            if new_item.type == item.category:
                if item.list_id == my_list_id:
                    new_item.context = [{"label": 'Eliminar de Mi Lista',
                                         "context_channel": 'lists',
                                         "context_action": 'remove_from_my_list'}]

                itemlist.append(new_item.clone(list_id=item.list_id))

    return itemlist


def add_list(item):
    logger.trace()
    controls = [
        {
            'id': 'name',
            'type': "text",
            'label': 'Nombre:',
            'default': ''
        },
        {
            'id': 'id',
            'type': "text",
            'label': 'ID:',
            'default': ''
        }]

    if platformtools.show_settings(controls=controls, title="Añadir lista", callback="add_list_callback", item=item):
        platformtools.itemlist_refresh()


def add_list_callback(item, values):
    logger.trace()
    remote_lists = settings.get_setting('snipt_remote_lists', __file__) or {}
    my_list_id = settings.get_setting('snipt_id', __file__)

    if not values['name'] or not values['id']:
        platformtools.dialog_ok("Error al añadir la lista",
                                "Para añadir una lista es necesario un nombre y un ID válidos")
        return False

    if values['id'] not in remote_lists.keys() and values['id'] != my_list_id:
        lista = snipt.read(values['id'])

        if not lista:
            platformtools.dialog_ok("Error al añadir la lista: %s" % values['name'],
                                    "Esta lista ha sido borrada o el ID: %s es incorrecto." % values['id'])
            return False

        elif lista == '[]' and not platformtools.dialog_yesno("Añadir lista: %s" % values['name'],
                                                                       "Esta lista esta vacía.",
                                                                       "¿Desea añadirla igualmente a su listado?"):
            return False

        remote_lists[values['id']] = values['name']
        settings.set_setting('snipt_remote_lists', remote_lists, __file__)
        return True

    platformtools.dialog_ok("Error al añadir la lista", "ID duplicado:",
                            "Este ID pertenece a la lista '%s'" % remote_lists.get(values['id'], "Mi Lista"))


def remove_list(item):
    remote_lists = settings.get_setting('snipt_remote_lists', __file__)
    del remote_lists[item.list_id]
    settings.set_setting('snipt_remote_lists', remote_lists, __file__)
    platformtools.itemlist_refresh()


def rename_list(item):
    remote_lists = settings.get_setting('snipt_remote_lists', __file__)

    name = platformtools.dialog_input(remote_lists[item.list_id], 'Escribe el nombre de la lista')
    if name:
        remote_lists[item.list_id] = name

    settings.set_setting('snipt_remote_lists', remote_lists, __file__)
    platformtools.itemlist_refresh()


def config(item):
    if item.list_id:
        line1 = 'Cualquier cambio que efectue puede hacer que pierda su lista actual.'
        line2= '¿Esta usted seguro de querer continuar?'
        if not platformtools.dialog_yesno('MediaExplorer - Mi Lista', line1, line2):
            return

    platformtools.show_settings(title="Mi Lista", callback="config_callback")
    platformtools.itemlist_refresh()


def config_callback(item, values):
    logger.trace()

    snipt_username = values['snipt_username']
    snipt_password = values['snipt_password']
    snipt_id = values['snipt_id']
    apikey = None

    if snipt_username and snipt_password:
        apikey = snipt.get_apikey(snipt_username, snipt_password)

    if not apikey:
        # Crear nueva cuenta de usuario
        ret = snipt.create_acount(snipt_username, snipt_password)
        if ret:
            snipt_username = ret[0]
            snipt_password = ret[1]
            apikey = ret[2]

    if apikey:
        if snipt_id:
            # Comprobamos q el ID es correcto
            for snipts in snipt.get_snipts(snipt_username, apikey):
                if str(snipts['id']) == values['snipt_id']:
                    snipt_id = values['snipt_id']
                    break
                else:
                    snipt_id = None

        if not snipt_id:
            # Creamos una lista nueva
            snipt_id = str(snipt.create(snipt_username, apikey, "[]", title='My list'))

        if snipt_id:
            # Guardamos
            settings.set_setting('snipt_username', snipt_username, __file__)
            settings.set_setting('snipt_password', snipt_password, __file__)
            settings.set_setting('snipt_apikey_password', apikey, __file__)
            settings.set_setting('snipt_id', snipt_id, __file__)
            return apikey

        else:
            error = "Error ID al recuperar o crear Mi Lista"

    else:
        error = "Error apikey al recuperar o crear la cuenta"

    logger.debug(error)
    platformtools.dialog_notification('MediaExplorer', error, 2)
    return None


# Funciones llamadas desde el menu contextual
def remove_from_my_list(item):
    logger.trace()

    my_list_id = settings.get_setting('snipt_id', __file__)
    if my_list_id:
        my_list = snipt.read(my_list_id)
        if my_list and my_list[0] == '[' and my_list[-1] == ']':
            my_list = eval(my_list)

            for i in my_list[:]:
                new_item = Item().fromurl(i)
                if new_item.url == item.url:
                    my_list.remove(i)

                    if not my_list:
                        my_list = "[]"

                    if snipt.update(settings.get_setting('snipt_username', __file__),
                                    settings.get_setting('snipt_apikey_password', __file__), my_list_id, str(my_list)):
                        platformtools.dialog_notification("Eliminar de Mi Lista",
                                                          "'%s' eliminada correctamente" % item.title)
                        platformtools.itemlist_refresh()
                        return

    platformtools.dialog_ok("Error al eliminar de Mi Lista",
                            "Ha sido imposible eliminar '%s' de Mi Lista" % item.title,
                            "Por favor, vuelva a intentarlo pasado unos minutos.")


def add_to_my_list(item):
    logger.trace()

    my_list_id = settings.get_setting('snipt_id', __file__)
    if my_list_id:
        my_list = snipt.read(my_list_id)
        if my_list and  my_list[0] == '[' and my_list[-1] == ']':
            my_list = eval(my_list)

            # Eliminar opciones del menu contextual
            if item.context_channel: del item.context_channel
            if item.context_action: del item.context_action

            if item.tourl() in my_list:
                # TODO de momento solo se comprueba a nivel de item. En el futuro podriamos comprobar codigos y permitir añadir varios canales a la misma serie o pelicula
                platformtools.dialog_notification("Añadir a Mi Lista",
                                                  "'%s' ya habia sido añadida anteriormente" % item.title, 1, 9000)
                return

            my_list.append(item.tourl())

            if snipt.update(settings.get_setting('snipt_username', __file__),
                                settings.get_setting('snipt_apikey_password', __file__), my_list_id, str(my_list)):
                platformtools.dialog_notification("Añadir a Mi Lista",
                                                  "'%s' añadida correctamente" % item.title)
                return

    platformtools.dialog_ok("Error al añadir a Mi Lista",
                            "Ha sido imposible añadir '%s' a Mi Lista" % item.title,
                            "Por favor, vuelva a intentarlo pasado unos minutos.")
