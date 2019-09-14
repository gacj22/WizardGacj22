# -*- coding: utf-8 -*-
import xbmc
import xbmcplugin

from core.libs import *


def get_profile(category, item_type=None, key=None):
    """
    Obtiene los datos del perfil para la categoria, tipo de item y clave
    :param category:
    :param item_type:
    :param key:
    :return:
    """

    # Obtenemos el perfil cargado segun la configuración
    result = sysinfo.profile[category]

    # Seleccionamos el tipo de datos que deseamos del perfil (items, contents,...)
    if item_type:
        result = result.get(item_type, result.get('default'))

    # Seleccionamos el tipo concreo que necesitamos ('movies', 'tvshows', etc...)
    if key:
        result = result.get(key, {})

    return result


def set_viewmode(item):
    """
    Fija el tipo de vista y contenido para el item pasado, según el perfil seleccionado.
    :param item:
    :return:
    """
    logger.trace()

    content = get_profile('contents', item.content_type)

    logger.debug('Content: %s' % content.get('category', ''))
    logger.debug('View   : %s' % content.get('view', ''))

    xbmcplugin.setContent(int(sys.argv[1]), content.get('category', ''))
    xbmc.executebuiltin("Container.SetViewMode(%s)" % content.get('view', ''))


def set_art(item, parent_item, listitem):
    """
    Fija las imagenes en el listitem segun el typo de item y el tipo de vista (parent_item) segun el prefil seleccionado
        - El parent item se usa para decidir que imagenes se pasaran (icon, poster o thumb) en funcion del tipo de
          vistapara que no se vean deformadas.
        - El item se usa para especificar la ruta de las imagenes en el caso de que el tipo de item las tenga
          especificadas en el perfil como puede ser un item tipo 'search' que las imagenes son predeterminadas (lupa)
    Tambien se en carga de convertir las rutas relativas en una ruta absoluta siempre que la imagen sea local:
    :param item:
    :param parent_item:
    :param listitem:
    :return:
    """
    logger.trace()

    item = item.clone()

    # Obtenemos los perfiles del parent item y del item
    parent_art = get_profile('contents', parent_item.content_type, 'art')
    item_art = get_profile('types', item.type, 'art')

    logger.info('Content art: %s' % parent_art)
    logger.info('Item art: %s' % item_art)

    # Si el item tiene las imagenes fijadas en el perfil estas sobreescriben el contenido del item
    for name, path in item_art.items():
        setattr(item, name, path)
        logger.info('Set item param: %s: %s' % (name, path))

    # Fijamos los valores en el listitem
    for name, values in parent_art.items():
        # Se hace un eval ya que en el .json del perfil se puede usar parte de código python como puede ser:
        # icon: "eval(item.icon or item.poster)"
        # que pondria de imagen 'icon' el primero de los dos que contenga algo.
        if type(values) == str and re.match('^eval\((.*?)\)$', values):
            value = eval(re.match('^eval\((.*?)\)$', values).group(1))
        else:
            value = values

        if not value:
            continue

        if not value.startswith('http'):
            value = 'http://www.mediaexplorer.tk/media/%s' % value

        listitem.setArt({name: value})
        logger.info('Set art: %s: %s' % (name, value))


def set_item_info(item, listitem):
    """
    Fija la información del medio (infoLabels) al listitem, en función del tipo de item asigna unos u otros
    :param item:
    :param listitem:
    :return:
    """
    logger.trace()
    info = get_profile('types', item.type, 'info')

    # Asignamos tipo de contenido a video aunque no haya ningun label para asignar
    # Kodi 18 lo necesita para que funcione setResolvedUrl
    listitem.setInfo("video", {})

    # Asignamos uno por uno los diferentes infoLabels
    for name, values in info.items():
        # Se hace un eval para obtener el valor ya que este puede estar escrito en el perfil o ser una referencia a un
        # parametro del item:
        # 'mediatype': "movie"
        # 'title': "eval(item.title or item.label)"
        try:
            if type(values) == str and re.match('^eval\((.*?)\)$', values):
                value = eval(re.match('^eval\((.*?)\)$', values).group(1))
            else:
                value = values
        except Exception:
            value = ''
            logger.error()

        if not value:
            continue
        listitem.setInfo("video", {name: value})


def set_label_format(item):
    """
    Devuelve el label de un item (para mostrar en el listado) en funcion del perfil seleccionado y el tipo de item.
    Por ejemplo:
        labels: [
                    { "value": "item.title ",
                      "sublabel": "%s"
                    },
                    { "value": "[item.season, item.episode]",
                      "sublabel":"%dx%02f: "
                    },
                    { "value": "item.language",
                      "sublabel":"[%s] ",
                      "italics": True
                    },
                    { "value": "item.watched",
                      "sublabel":"(Visto)",
                      "color": "yellow",
                      "bold": True
                    },
                ]
    Cada tipo de item tiene definido en el perfil una lista (labels) de etiquetas que formaran el texto a mostrar.
    Cada etiqueta es un diccionario con los siguientes campos:
        - "value": Especifica la forma de obtener el valor. Puede ser:
            - 1 solo valor (fijado o obtenido del item)
            - Varios valores cada uno puede ser fijo o obtenido del item
            - Un booleano (fijado o obtenido del item). Si es True la subetiqueta se muestra, sino no.

        - "sublabel": Cadena de texto, incluyendo marcadores de posicion (placeholders), que se añadira al label
        del item. Por defecto, si se omite, se fija como "%s"

        - "color": Si se incluye colorea el sublabel con el color indicado. Puede ser un color estandar HTML (blue, red,
        orange, etc...), una cadena que representa un color mediante sus componentes en formato ‘0xAARRGGBB’ o un color
        declarado dentro del perfil en la etiqueta "colors" (diccionario nombre/valor).

        - "bold" y "italics": Boleanos (fijado o obtenido del item) opcionales que indican si el sublabel ha de estar
        en negrita y/o cursiva.


    :param item:
    :return:
    """
    logger.trace()

    # Obtenemos las diferentes etiquetas que mostrará el item
    labels = get_profile('types', item.type, 'labels')[:]

    # Si el item tiene un label_extra esta se añade al final de la etiqueta formateada por el perfil
    if item.label_extra:
        labels.append(item.label_extra)

    item_label = ''

    # Recorremos cada una de las etiquetas que están definidas en el perfil para este tipo de item
    for etiqueta in labels:
        try:
            if type(etiqueta['value']) == str and re.match('^eval\((.*?)\)$', etiqueta['value']):
                value = eval(re.match('^eval\((.*?)\)$', etiqueta['value']).group(1))
            else:
                value = etiqueta['value']
        except Exception:
            logger.error()
            continue

        # Contamos cuantos parametros se usan para obtener el formato de la sublabel (1, varios o ninguno)
        sublabel = etiqueta.get('sublabel', '%s')
        cant = sublabel.count('%') - (sublabel.count('%%') * 2)

        # Si es ninguno el valor se pasa a bool
        if cant == 0:
            value = bool(value)

        # Si es uno el valor se pasa a string en el caso que el valor obtenido fuera un list o dict:
        # Por ejemplo:
        #  - idioma: ['Español', 'Inglés'] - > 'Español, Inglés'
        elif cant == 1:
            if type(value) == list:
                v = []
                for i in value:
                    if isinstance(i, (Language, Quality)):
                        v.append(str(i))
                    else:
                        v.append(i)
                value = ', '.join(v)

            elif isinstance(value, (Language, Quality)):
                value = str(value)

        # Si son varios se hace la misma conversion anterior pero para cada uno de los valores obtenidos.
        else:
            for x, val in enumerate(value):
                if type(val) == list:
                    v = []
                    for i in val:
                        if isinstance(i, (Language, Quality)):
                            v.append(str(i))
                        else:
                            v.append(i)
                    val = ', '.join(v)

                elif isinstance(val, (Language, Quality)):
                    val = str(val)

                else:
                    val = val

                value[x] = val

        # Si existe un value valido
        if value or (value == 0 and not isinstance(value, bool)):
            # si es un bool y es True, muestra el sublabel
            if type(value) == bool and value:
                sublabel = sublabel

            # si es un list formatea el sublabel con todos los parametros
            elif type(value) == list:
                if all([v or isinstance(v, (int, float, bool)) for v in value]):
                    sublabel = sublabel % tuple(value)

            # Sino formate el sublabel con un solo parametro
            else:
                sublabel = sublabel % value

            # Si se incluye en la etiqueta, añadir cursiva/negrita al texto del sublabel
            italics = etiqueta.get('italics', False)
            if not isinstance(italics, bool):
                try:
                    italics = eval(italics)
                except Exception:
                    logger.error()
            if italics is True:
                sublabel = '[I]%s[/I]' % sublabel

            bold = etiqueta.get('bold', False)
            if not isinstance(bold, bool):
                try:
                    bold = eval(bold)
                except Exception:
                    logger.error()
            if bold is True:
                sublabel = '[B]%s[/B]' % sublabel

            color = etiqueta.get('color')
            if color:
                colors_profile = get_profile('colors')
                if color in colors_profile:
                    color = colors_profile[color]
                sublabel = '[COLOR %s]%s[/COLOR]' % (color, sublabel)

            # Añadimos el sublabel al label final
            item_label += sublabel

    # Si el item es parte de un grupo (item.group == True), le añade los los espacios a la izq para desplazarlo
    # (o lo que se haya definido en el perfil)
    if item.group:
        # group se especifica para los items que están agrupados debajo de un label (desplazados a la derecha)
        # Peliculas
        #   - Por genero
        #   - Buscar
        #   - etc...
        group = get_profile('group')
        item_label = group % item_label

    return item_label
