# -*- coding: utf-8 -*-
from core.libs import *
import xbmcgui


class InfoWindow(xbmcgui.WindowXMLDialog):
    @staticmethod
    def get_language(lng):
        # Cambiamos el formato del Idioma
        languages = {
            'aa': 'Afar', 'ab': 'Abkhazian', 'af': 'Afrikaans', 'ak': 'Akan', 'sq': 'Albanian', 'am': 'Amharic',
            'ar': 'Arabic', 'an': 'Aragonese', 'as': 'Assamese', 'av': 'Avaric', 'ae': 'Avestan', 'ay': 'Aymara',
            'az': 'Azerbaijani', 'ba': 'Bashkir', 'bm': 'Bambara', 'eu': 'Basque', 'be': 'Belarusian', 'bn': 'Bengali',
            'bh': 'Bihari languages', 'bi': 'Bislama', 'bo': 'Tibetan', 'bs': 'Bosnian', 'br': 'Breton',
            'bg': 'Bulgarian', 'my': 'Burmese', 'ca': 'Catalan; Valencian', 'cs': 'Czech', 'ch': 'Chamorro',
            'ce': 'Chechen', 'zh': 'Chinese',
            'cu': 'Church Slavic; Old Slavonic; Church Slavonic; Old Bulgarian; Old Church Slavonic', 'cv': 'Chuvash',
            'kw': 'Cornish', 'co': 'Corsican', 'cr': 'Cree', 'cy': 'Welsh', 'da': 'Danish', 'de': 'German',
            'dv': 'Divehi; Dhivehi; Maldivian', 'nl': 'Dutch; Flemish', 'dz': 'Dzongkha', 'en': 'English',
            'eo': 'Esperanto', 'et': 'Estonian', 'ee': 'Ewe', 'fo': 'Faroese', 'fa': 'Persian', 'fj': 'Fijian',
            'fi': 'Finnish', 'fr': 'French', 'fy': 'Western Frisian', 'ff': 'Fulah', 'Ga': 'Georgian',
            'gd': 'Gaelic; Scottish Gaelic', 'ga': 'Irish', 'gl': 'Galician', 'gv': 'Manx',
            'el': 'Greek, Modern (1453-)', 'gn': 'Guarani', 'gu': 'Gujarati', 'ht': 'Haitian; Haitian Creole',
            'ha': 'Hausa', 'he': 'Hebrew', 'hz': 'Herero', 'hi': 'Hindi', 'ho': 'Hiri Motu', 'hr': 'Croatian',
            'hu': 'Hungarian', 'hy': 'Armenian', 'ig': 'Igbo', 'is': 'Icelandic', 'io': 'Ido',
            'ii': 'Sichuan Yi; Nuosu', 'iu': 'Inuktitut', 'ie': 'Interlingue; Occidental',
            'ia': 'Interlingua (International Auxiliary Language Association)', 'id': 'Indonesian', 'ik': 'Inupiaq',
            'it': 'Italian', 'jv': 'Javanese', 'ja': 'Japanese', 'kl': 'Kalaallisut; Greenlandic', 'kn': 'Kannada',
            'ks': 'Kashmiri', 'ka': 'Georgian', 'kr': 'Kanuri', 'kk': 'Kazakh', 'km': 'Central Khmer',
            'ki': 'Kikuyu; Gikuyu', 'rw': 'Kinyarwanda', 'ky': 'Kirghiz; Kyrgyz', 'kv': 'Komi', 'kg': 'Kongo',
            'ko': 'Korean', 'kj': 'Kuanyama; Kwanyama', 'ku': 'Kurdish', 'lo': 'Lao', 'la': 'Latin', 'lv': 'Latvian',
            'li': 'Limburgan; Limburger; Limburgish', 'ln': 'Lingala', 'lt': 'Lithuanian',
            'lb': 'Luxembourgish; Letzeburgesch', 'lu': 'Luba-Katanga', 'lg': 'Ganda', 'mk': 'Macedonian',
            'mh': 'Marshallese', 'ml': 'Malayalam', 'mi': 'Maori', 'mr': 'Marathi', 'ms': 'Malay', 'Mi': 'Micmac',
            'mg': 'Malagasy', 'mt': 'Maltese', 'mn': 'Mongolian', 'na': 'Nauru', 'nv': 'Navajo; Navaho',
            'nr': 'Ndebele, South; South Ndebele', 'nd': 'Ndebele, North; North Ndebele', 'ng': 'Ndonga',
            'ne': 'Nepali', 'nn': 'Norwegian Nynorsk; Nynorsk, Norwegian', 'nb': 'Bokmål, Norwegian; Norwegian Bokmål',
            'no': 'Norwegian', 'oc': 'Occitan (post 1500)', 'oj': 'Ojibwa', 'or': 'Oriya', 'om': 'Oromo',
            'os': 'Ossetian; Ossetic', 'pa': 'Panjabi; Punjabi', 'pi': 'Pali', 'pl': 'Polish', 'pt': 'Portuguese',
            'ps': 'Pushto; Pashto', 'qu': 'Quechua', 'ro': 'Romanian; Moldavian; Moldovan', 'rn': 'Rundi',
            'ru': 'Russian', 'sg': 'Sango', 'rm': 'Romansh', 'sa': 'Sanskrit', 'si': 'Sinhala; Sinhalese',
            'sk': 'Slovak', 'sl': 'Slovenian', 'se': 'Northern Sami', 'sm': 'Samoan', 'sn': 'Shona', 'sd': 'Sindhi',
            'so': 'Somali', 'st': 'Sotho, Southern', 'es': 'Spanish', 'sc': 'Sardinian', 'sr': 'Serbian', 'ss': 'Swati',
            'su': 'Sundanese', 'sw': 'Swahili', 'sv': 'Swedish', 'ty': 'Tahitian', 'ta': 'Tamil', 'tt': 'Tatar',
            'te': 'Telugu', 'tg': 'Tajik', 'tl': 'Tagalog', 'th': 'Thai', 'ti': 'Tigrinya',
            'to': 'Tonga (Tonga Islands)', 'tn': 'Tswana', 'ts': 'Tsonga', 'tk': 'Turkmen', 'tr': 'Turkish',
            'tw': 'Twi', 'ug': 'Uighur; Uyghur', 'uk': 'Ukrainian', 'ur': 'Urdu', 'uz': 'Uzbek', 've': 'Venda',
            'vi': 'Vietnamese', 'vo': 'Volapük', 'wa': 'Walloon', 'wo': 'Wolof', 'xh': 'Xhosa', 'yi': 'Yiddish',
            'yo': 'Yoruba', 'za': 'Zhuang; Chuang', 'zu': 'Zulu'}

        return languages.get(lng, lng)

    def __init__(self, *args, **kwargs):
        self.title = ''
        self.item = None
        self.itemlist = list()
        self.index = -1
        self.return_value = None

    def start(self, item, title="Información del vídeo"):
        logger.trace()

        self.title = title

        if type(item) == list:
            self.itemlist = item
            self.index = 0
        else:
            self.itemlist = [item]
            self.index = 0

        self.doModal()

        return self.return_value

    def onInit(self):
        logger.trace()
        if int(xbmcgui.__version__.replace('.', '')) <= 2250:
            self.setCoordinateResolution(5)

        self.item = self.itemlist[self.index]

        self.getControl(10002).setLabel(self.title)
        self.getControl(10004).setImage(self.item.fanart or '')
        self.getControl(10005).setImage(self.item.poster or '')

        if self.item.type == "channel":
            self.getControl(10006).setLabel("Nombre:")
            self.getControl(10007).setLabel('%s' % self.item.name)
            self.getControl(10008).setLabel("Versión:")
            self.getControl(10009).setLabel('%s' % (self.item.version or 'N/A'))
            self.getControl(100010).setLabel("Contenido adultos:")
            self.getControl(100011).setLabel('%s' % (['No', 'Si'][self.item.adult]))
            self.getControl(100012).setLabel("Categorias:")
            self.getControl(100013).setLabel(', '.join(self.item.categories) or 'N/A')
            self.getControl(100014).setLabel("Búsqueda global:")
            self.getControl(100015).setLabel(', '.join(self.item.search) or 'No')
            self.getControl(100016).setLabel("Novedades:")
            self.getControl(100017).setLabel(', '.join(self.item.newest) or 'No')
            if self.item.min_version:
                self.getControl(100018).setLabel("Requisitos:")
                self.getControl(100019).setLabel(', '.join(self.item.min_version))
            #self.getControl(100020).setLabel("Más:")
            #self.getControl(100021).setLabel('%s' % (self.item.aired or 'N/A'))
            self.getControl(100022).setLabel("Cambios:")
            self.getControl(100023).setText('\n'.join(self.item.changes))


        # Cargamos los datos para el formato pelicula
        elif self.item.type == "movie":
            self.getControl(10006).setLabel("Título:")
            self.getControl(10007).setLabel('%s' % self.item.title)
            self.getControl(10008).setLabel("Título original:")
            self.getControl(10009).setLabel('%s' % (self.item.originaltitle or 'N/A'))
            self.getControl(100010).setLabel("Idioma original:")
            self.getControl(100011).setLabel('%s' % (self.get_language(self.item.language) or 'N/A'))
            self.getControl(100012).setLabel("Puntuación:")
            self.getControl(100013).setLabel('%s (%s)' % (self.item.rating or 'N/A', self.item.votes or 'N/A'))
            self.getControl(100014).setLabel("Lanzamiento:")
            self.getControl(100015).setLabel('%s' % (self.item.year or 'N/A'))
            self.getControl(100016).setLabel("Géneros:")
            self.getControl(100017).setLabel('%s' % (self.item.genre or 'N/A'))


        # Cargamos los datos para el formato serie
        else:
            self.getControl(10006).setLabel("Serie:")
            self.getControl(10007).setLabel('%s' % (self.item.tvshowtitle or self.item.title))
            self.getControl(10008).setLabel("Idioma original:")
            self.getControl(10009).setLabel('%s' % (self.get_language(self.item.language) or 'N/A'))
            self.getControl(100010).setLabel("Puntuación:")
            self.getControl(100011).setLabel('%s (%s)' % (self.item.rating or 'N/A', self.item.votes or 'N/A'))
            self.getControl(100012).setLabel("Géneros:")
            self.getControl(100013).setLabel('%s' % (self.item.genre or 'N/A'))

            if self.item.type == 'season':
                self.getControl(100014).setLabel("Título temporada:")
                self.getControl(100015).setLabel('%s' % (self.item.title or 'N/A'))
                self.getControl(100016).setLabel("Temporada:")
                self.getControl(100017).setLabel('%s de %s' % (self.item.season or 'N/A', self.item.seasons or 'N/A'))

            if self.item.type == 'episode':
                self.getControl(100014).setLabel("Título:")
                self.getControl(100015).setLabel('%s' % self.item.title)
                self.getControl(100016).setLabel("Temporada:")
                self.getControl(100017).setLabel('%s de %s' % (self.item.season or 'N/A', self.item.seasons or 'N/A'))
                self.getControl(100018).setLabel("Episodio:")
                self.getControl(100019).setLabel('%s de %s' % (self.item.episode or 'N/A', self.item.episodes or 'N/A'))
                self.getControl(100020).setLabel("Emisión:")
                self.getControl(100021).setLabel('%s' % (self.item.aired or 'N/A'))


        if self.item.type != 'channel':
            # Sinopsis
            if self.item.plot:
                self.getControl(100022).setLabel("Sinopsis:")
                self.getControl(100023).setText(self.item.plot)
            else:
                self.getControl(100022).setLabel("")
                self.getControl(100023).setText("")


        # Cargamos los botones si es necesario
        if len(self.itemlist) > 1:
            self.getControl(10001).setHeight(500)
        self.getControl(10024).setVisible(len(self.itemlist) > 1)  # Grupo de botones
        self.getControl(10025).setEnabled(self.index > 0)  # Anterior
        self.getControl(10026).setEnabled(self.index < len(self.itemlist) - 1)  # Siguiente
        self.getControl(100029).setLabel("(%s/%s)" % (self.index + 1, len(self.itemlist)))

        self.setFocus(self.getControl(10024))

    def onClick(self, id):
        logger.trace()

        if id == 10025 and self.index > 0:
            self.index -= 1
            self.onInit()

        elif id == 10026 and self.index < len(self.itemlist) - 1:
            self.index += 1
            self.onInit()

        elif id == 10028 or id == 10003 or id == 10027:
            self.close()

            if id == 10028:
                self.return_value = self.index
            else:
                self.return_value = None

    def onAction(self, action):
        logger.trace()

        action = action.getId()

        # Accion 1: Flecha izquierda
        if action == 1:
            if self.getFocusId() == 10028:
                self.setFocus(self.getControl(10027))

            elif self.getFocusId() == 10027:
                if self.index + 1 != len(self.itemlist):
                    # vamos al botón Siguiente
                    self.setFocus(self.getControl(10026))
                elif self.index > 0:
                    # vamos al botón Anterior ya que Siguiente no está activo (estamos al final de la lista)
                    self.setFocus(self.getControl(10025))

            elif self.getFocusId() == 10026:
                if self.index > 0:
                    # vamos al botón Anterior
                    self.setFocus(self.getControl(10025))

        # Accion 2: Flecha derecha
        elif action == 2:
            if self.getFocusId() == 10025:
                if self.index + 1 != len(self.itemlist):
                    # vamos al botón Siguiente
                    self.setFocus(self.getControl(10026))
                else:
                    # vamos al botón Cancelar ya que Siguiente no está activo (estamos al final de la lista)
                    self.setFocus(self.getControl(10027))

            elif self.getFocusId() == 10026:
                self.setFocus(self.getControl(10027))

            elif self.getFocusId() == 10027:
                self.setFocus(self.getControl(10028))

        # Pulsa ESC o Atrás, simula click en boton cancelar
        if action in [10, 92]:
            self.onClick(10027)
