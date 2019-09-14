# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Distributed under the terms of GNU General Public License v3 (GPLv3)
# http://www.gnu.org/licenses/gpl-3.0.html
# ------------------------------------------------------------
# Item is the object we use for representing data 
# --------------------------------------------------------------------------------

import base64
import copy
import os
import urllib
from HTMLParser import HTMLParser

from core import jsontools as json


class InfoLabels(dict):
    def __str__(self):
        return self.tostring(separador=',\r\t')

    def __setattr__(self, name, value):
        if name in ['IMDBNumber', 'code', 'imdb_id']:
            # Por compatibilidad hemos de guardar el valor en los tres campos
            super(InfoLabels, self).__setattr__('IMDBNumber', value)
            super(InfoLabels, self).__setattr__('code', value)
            super(InfoLabels, self).__setattr__('imdb_id', value)
        else:
            super(InfoLabels, self).__setattr__(name, value)

    #Python 2.4
    def __getitem__(self, key):
        try:
          return super(InfoLabels, self).__getitem__(key)
        except:
          return self.__missing__(key)
          
    def __missing__(self, key):
        '''
        Valores por defecto en caso de que la clave solicitada no exista.
        El parametro 'default' en la funcion obj_infoLabels.get(key,default) tiene preferencia sobre los aqui definidos.
        '''
        if key in ['rating']:
            # Ejemplo de clave q devuelve un str formateado como float por defecto
            return '0.0'
        elif key == 'mediatype':
            # "movie", "tvshow", "season", "episode"
            if 'tvshowtitle' in super(InfoLabels,self).keys():
                if 'episode' in super(InfoLabels,self).keys() and super(InfoLabels,self).__getitem__('episode') !="":
                    return 'episode'

                if 'episodeName' in super(InfoLabels,self).keys() and super(InfoLabels,self).__getitem__('episodeName') !="":
                    return 'episode'

                if 'season' in super(InfoLabels,self).keys() and super(InfoLabels,self).__getitem__('season') !="":
                    return 'season'
                else:
                    return 'tvshow'

            else:
                return 'movie'

        else:
            # El resto de claves devuelven cadenas vacias por defecto
            return ""

    def tostring(self, separador=', '):
        ls = []
        dic =  dict(super(InfoLabels, self).items())
        if 'mediatype' not in dic.keys():
            dic['mediatype'] = self.__missing__('mediatype')

        for i in sorted(dic.items()):
            i_str = str(i)[1:-1]
            if isinstance(i[0], str):
                old = i[0] + "',"
                new = i[0] + "':"
            else:
                old = str(i[0]) + ","
                new = str(i[0]) + ":"
            ls.append(i_str.replace(old, new, 1))

        return "{%s}" % separador.join(ls)



class Item(object):
    def __init__(self, **kwargs):
        '''
        Inicializacion del item
        '''

        # Creamos el atributo infoLabels
        self.__dict__["infoLabels"] = InfoLabels()
        if kwargs.has_key("infoLabels"):
            if isinstance(kwargs["infoLabels"], dict):
                self.__dict__["infoLabels"].update(kwargs["infoLabels"])
            del kwargs["infoLabels"]

        if kwargs.has_key("parentContent"):
            self.set_parent_content(kwargs["parentContent"])
            del kwargs["parentContent"]

        kw = copy.copy(kwargs)
        for k in kw:
            if k in ["contentTitle", "contentPlot", "contentSerieName", "show", "contentType", "contentEpisodeTitle",
                    "contentSeason", "contentEpisodeNumber", "contentThumbnail", "plot", "duration"]:
                self.__setattr__(k, kw[k])
                del kwargs[k]

        self.__dict__.update(kwargs)
        self.__dict__ = self.toutf8(self.__dict__)

    def __contains__(self, m):
        '''
        Comprueba si un atributo existe en el item
        '''
        return m in self.__dict__

    def __setattr__(self, name, value):
        '''
        Función llamada al modificar cualquier atributo del item, modifica algunos atributos en función de los datos modificados
        '''
        if name == "__dict__":
            for key in value:
                self.__setattr__(key, value[key])
            return


        # Descodificamos los HTML entities
        if name in ["title", "plot", "fulltitle", "contentPlot", "contentTitle"]: value = self.decode_html(value)

       # Al modificar cualquiera de estos atributos content...
        if name in ["contentTitle", "contentPlot", "contentSerieName", "contentType", "contentEpisodeTitle",
                    "contentSeason", "contentEpisodeNumber", "contentThumbnail", "show"]:
            #... marcamos hasContentDetails como "true"...
            self.__dict__["hasContentDetails"] = "true"
            #...y actualizamos infoLables
            if name == "contentTitle":
                self.__dict__["infoLabels"]["title"] = value
            elif name == "contentPlot":
                self.__dict__["infoLabels"]["plot"] = value
            elif name == "contentSerieName" or name == "show":
                self.__dict__["infoLabels"]["tvshowtitle"] = value
            elif name == "contentType":
                self.__dict__["infoLabels"]["mediatype"] = value
            elif name == "contentEpisodeTitle":
                self.__dict__["infoLabels"]["episodeName"] = value
            elif name == "contentSeason":
                self.__dict__["infoLabels"]["season"] = value
            elif name == "contentEpisodeNumber":
                self.__dict__["infoLabels"]["episode"] = value
            elif name == "contentThumbnail":
                self.__dict__["infoLabels"]["thumbnail"] = value

        elif name == "plot":
            self.__dict__["infoLabels"]["plot"] = value

        elif name == "duration":
            # String q representa la duracion del video en segundos
            self.__dict__["infoLabels"]["duration"] = str(value)

        # Al asignar un valor a infoLables
        elif name == "infoLabels":
            if isinstance(value, dict):
                value_defaultdict = InfoLabels(value)
                if value:
                    self.__dict__["infoLabels"].update(value_defaultdict)
                else:
                    self.__dict__["infoLabels"] = value_defaultdict

        else:
            super(Item, self).__setattr__(name, value)

    def __getattr__(self, name):
        '''
        Devuelve los valores por defecto en caso de que el atributo solicitado no exista en el item
        '''
        if name.startswith("__"): return super(Item, self).__getattribute__(name)

        # valor por defecto para folder
        if name == "folder":
            return True

        # valor por defecto para viewmode y contentChannel
        elif name in ["viewmode", "contentChannel"]:
            return "list"

        # Valor por defecto para hasContentDetails
        elif name == "hasContentDetails":
            return "false"

        elif name in ["contentTitle", "contentPlot", "contentSerieName", "show", "contentType", "contentEpisodeTitle",
                    "contentSeason", "contentEpisodeNumber", "contentThumbnail", "plot", "duration"]:
            if name == "contentTitle":
                return self.__dict__["infoLabels"]["title"]
            elif name == "contentPlot" or name == "plot":
                return self.__dict__["infoLabels"]["plot"]
            elif name == "contentSerieName" or name == "show":
                return self.__dict__["infoLabels"]["tvshowtitle"]
            elif name == "contentType":
                return self.__dict__["infoLabels"]["mediatype"]
            elif name == "contentEpisodeTitle":
                return self.__dict__["infoLabels"]["episodeName"]
            elif name == "contentSeason":
                return self.__dict__["infoLabels"]["season"]
            elif name == "contentEpisodeNumber":
                return self.__dict__["infoLabels"]["episode"]
            elif name == "contentThumbnail":
                return self.__dict__["infoLabels"]["thumbnail"]
            else:
                return self.__dict__["infoLabels"][name]

        # valor por defecto para el resto de atributos
        else:
            return ""

    def __str__(self):
        return '\r\t' + self.tostring('\r\t')

    def set_parent_content(self, parentContent):
        '''
        Rellena los campos contentDetails con la informacion del item "padre"
        '''
        # Comprueba que parentContent sea un Item
        if not type(parentContent) == type(self):
            return
        # Copia todos los atributos que empiecen por "content" y esten declarados y los infoLabels
        for attr in parentContent.__dict__:
            if attr.startswith("content") or attr == "infoLabels":
                self.__setattr__(attr, parentContent.__dict__[attr])

    def tostring(self, separator=", "):
        '''
        Genera una cadena de texto con los datos del item para el log
        Uso: logger.info(item.tostring())
        '''
        dic= self.__dict__.copy()

        # Añadimos los campos content... si tienen algun valor
        for key in ["contentTitle", "contentPlot", "contentSerieName", "contentType", "contentEpisodeTitle",
                    "contentSeason", "contentEpisodeNumber", "contentThumbnail", "plot"]:
            value = self.__getattr__(key)
            if value: dic[key]= value

        ls = []
        for var in sorted(dic):
            if isinstance(dic[var],str):
                valor = "'%s'" %dic[var]
            elif isinstance(dic[var],InfoLabels):
                if separator == '\r\t':
                    valor = dic[var].tostring(',\r\t\t')
                else:
                    valor = dic[var].tostring()
            else:
                valor = str(dic[var])

            ls.append(var + "= " + valor)

        return separator.join(ls)

    def tourl(self):
        """
        Genera una cadena de texto con los datos del item para crear una url, para volver generar el Item usar
        item.fromurl().

        Uso: url = item.tourl()
        """
        dump = json.dump_json(self.__dict__)
        # if empty dict
        if not dump:
            # set a str to avoid b64encode fails
            dump = ""
        return urllib.quote(base64.b64encode(dump))

    def fromurl(self, url):
        '''
        Genera un item a partir de una cadena de texto. La cadena puede ser creada por la funcion tourl() o tener
        el formato antiguo: plugin://plugin.video.pelisalacarta/?channel=... (+ otros parametros)
        Uso: item.fromurl("cadena")
        '''
        if "?" in url: url = url.split("?")[1]
        try:
            STRItem = base64.b64decode(urllib.unquote(url))
            JSONItem = json.load_json(STRItem, object_hook=self.toutf8)
            self.__dict__.update(JSONItem)
        except:
            url = urllib.unquote_plus(url)
            dct = dict([[param.split("=")[0], param.split("=")[1]] for param in url.split("&") if "=" in param])
            self.__dict__.update(dct)
            self.__dict__ = self.toutf8(self.__dict__)

        if 'infoLabels' in self.__dict__ and not isinstance(self.__dict__['infoLabels'],InfoLabels):
            self.__dict__['infoLabels'] = InfoLabels(self.__dict__['infoLabels'])

        return self

    def tojson(self, path=""):
        '''
        Crea un JSON a partir del item, para guardar archivos de favoritos, lista de descargas, etc...
        Si se especifica un path, te lo guarda en la ruta especificada, si no, devuelve la cadena json
        Usos: item.tojson(path="ruta\archivo\json.json")
              file.write(item.tojson())
        '''
        if path:
            open(path, "wb").write(json.dump_json(self.__dict__))
        else:
            return json.dump_json(self.__dict__)

    def fromjson(self, STRItem={}, path=""):
        '''
        Genera un item a partir de un archivo JSON
        Si se especifica un path, lee directamente el archivo, si no, lee la cadena de texto pasada.
        Usos: item = Item().fromjson(path="ruta\archivo\json.json")
              item = Item().fromjson("Cadena de texto json")
        '''
        if path:
            if os.path.exists(path):
                STRItem = open(path, "rb").read()
            else:
                STRItem = {}

        JSONItem = json.load_json(STRItem, object_hook=self.toutf8)
        self.__dict__.update(JSONItem)

        if 'infoLabels' in self.__dict__ and not isinstance(self.__dict__['infoLabels'], InfoLabels):
            self.__dict__['infoLabels'] = InfoLabels(self.__dict__['infoLabels'])

        return self

    def clone(self, **kwargs):
        '''
        Genera un nuevo item clonando el item actual
        Usos: NuevoItem = item.clone()
              NuevoItem = item.clone(title="Nuevo Titulo", action = "Nueva Accion")
        '''
        newitem = copy.deepcopy(self)
        if kwargs.has_key("infoLabels"):
            kwargs["infoLabels"] = InfoLabels(kwargs["infoLabels"])
        newitem.__dict__.update(kwargs)
        newitem.__dict__ = newitem.toutf8(newitem.__dict__)
        return newitem

    def decode_html(self, value):
        '''
        Descodifica las HTML entities
        '''
        try:
            unicode_title = unicode(value, "utf8", "ignore")
            return HTMLParser().unescape(unicode_title).encode("utf8")
        except:
            return value

    def toutf8(self, *args):
        '''
        Pasa el item a utf8
        '''
        if len(args) > 0:
            value = args[0]
        else:
            value = self.__dict__

        if type(value) == unicode:
            return value.encode("utf8")

        elif type(value) == str:
            return unicode(value, "utf8", "ignore").encode("utf8")

        elif type(value) == list:
            for x, key in enumerate(value):
                value[x] = self.toutf8(value[x])
            return value

        elif isinstance(value,dict):
            newdct = {}
            for key in value:
                v = self.toutf8(value[key])
                if type(key) == unicode:
                    key = key.encode("utf8")

                newdct[key] = v

            if len(args) > 0:
                if isinstance(value, InfoLabels):
                    return InfoLabels(newdct)
                else:
                    return newdct

        else:
            return value
