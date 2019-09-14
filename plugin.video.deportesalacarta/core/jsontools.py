# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Distributed under the terms of GNU General Public License v3 (GPLv3)
# http://www.gnu.org/licenses/gpl-3.0.html
# ------------------------------------------------------------
# json_tools - JSON load and parse functions with library detection
# --------------------------------------------------------------------------------

import traceback
import logger

try:
  logger.info("Probando json incluido en el interprete")
  import json
except ImportError:
  logger.info("json incluido en el interprete **NO** disponible")
  
  try:
    logger.info("Probando simplejson incluido en el interprete")
    import simplejson as json
  except ImportError:
    logger.info("simplejson incluido en el interprete **NO** disponible")
    
    try:
      logger.info("Probando simplejson en el directorio lib")
      from lib import simplejson as json
    except ImportError:
      logger.info("simplejson en el directorio lib **NO** disponible")
      logger.error("No se ha encontrado un parser de JSON valido")
      json = None



def load_json(*args, **kwargs):
    if not "object_hook" in kwargs:
        kwargs["object_hook"] = to_utf8
        
    try:    
      value = json.loads(*args, **kwargs)
    except:
      logger.error("**NO** se ha podido cargar el JSON")
      value = {}
     
    return value



def dump_json(*args, **kwargs):
    if not kwargs:
        kwargs = {"indent":4, "skipkeys": True, "sort_keys": True, "ensure_ascii": False}

    try:    
      value = json.dumps(*args, **kwargs)
    except:
      logger.error("**NO** se ha podido cargar el JSON")
      value = ""
    return value


def to_utf8(dct):

    if isinstance(dct, dict):
        return dict((to_utf8(key), to_utf8(value)) for key, value in dct.iteritems())
    elif isinstance(dct, list):
        return [to_utf8(element) for element in dct]
    elif isinstance(dct, unicode):
        return dct.encode('utf-8')
    else:
        return dct


def xmlTojson(path_xml):
    """
    Lee un fichero xml y retorna un diccionario json

    Parametros:
    path_xml (str) -- Ruta completa al archivo XML que se desea leer.

    Retorna:
    Si el argumento path_xml no señala a un archivo XML valido retorna un diccionario vacio.
    En caso cortrario retorna un diccionario construido a partir de los campos del archivo XML.

    """

    import os
    ret = {}
    try:
        if os.path.exists(path_xml):
            infile = open(path_xml, "rb")
            data = infile.read()
            infile.close()
            ret = Xml2Json(data).result
    except:
        import traceback
        logger.info("deportesalacarta.core.jsontools xmlTojson ERROR al leer el fichero y/o crear el json de " + path_xml)
        logger.info("deportesalacarta.core.jsontools " + traceback.format_exc())

    return ret


class Xml2Json:
    # http://code.activestate.com/recipes/577494-convert-xml-into-json-python-dicts-and-lists-struc/
    # >>> Xml2Json('<doc><tag><subtag>data</subtag><t>data1</t><t>data2</t></tag></doc>').result
    # {u'doc': {u'tag': {u'subtag': u'data', u't': [u'data1', u'data2']}}}
    LIST_TAGS = ['COMMANDS']

    def __init__(self, data=None):
        # print "################## INIT"
        from xml.parsers.expat import ParserCreate
        self._parser = ParserCreate()
        self._parser.StartElementHandler = self.start
        self._parser.EndElementHandler = self.end
        self._parser.CharacterDataHandler = self.data
        self.result = None
        if data:
            self.feed(data)
            self.close()

    def feed(self, data):
        # print "################## FEED"
        self._stack = []
        self._data = ''
        self._parser.Parse(data, 0)

    def close(self):
        self._parser.Parse("", 1)
        del self._parser
        # print "################## CLOSE"
        self.result = to_utf8(self.result)

    def start(self, tag, attrs):
        assert attrs == {}
        assert self._data.strip() == ''
        # print "START", repr(tag)
        self._stack.append([tag])
        self._data = ''

    def end(self, tag):
        # print "END", repr(tag)
        last_tag = self._stack.pop()
        assert last_tag[0] == tag
        if len(last_tag) == 1:  # leaf
            data = self._data
        else:
            if tag not in Xml2Json.LIST_TAGS:
                # build a dict, repeating pairs get pushed into lists
                data = {}
                for k, v in last_tag[1:]:
                    if k not in data:
                        data[k] = v
                    else:
                        el = data[k]
                        if type(el) is not list:
                            data[k] = [el, v]
                        else:
                            el.append(v)
            else:  # force into a list
                data = [{k: v} for k, v in last_tag[1:]]
        if self._stack:
            self._stack[-1].append((tag, data))
        else:
            self.result = {tag: data}
        self._data = ''

    def data(self, data):
        # print "################## DATA"
        self._data = data
