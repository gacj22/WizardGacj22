# -*- coding: utf-8 -*-
from core.libs import *
import xbmcgui
import xbmc
import inspect


class SettingsWindow(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.controls = []
        self.title = ''
        self.callback = None
        self.item = None
        self.custom_button = None
        self.module = None
        self.return_value = None
        self.visible_controls = []
        skin = 'Estuary' if xbmc.getSkinDir() == 'skin.estuary' else 'Default'
        self.mediapath = os.path.join(sysinfo.runtime_path, 'resources', 'skins', skin, 'media')
        self.controls_width = 0
        self.controls_height = 0
        self.controls_pos_x = 0
        self.controls_pos_y = 0
        self.height_control = 35
        self.space = 5
        self.font = "font12"
        self.index = -1
        self.ok_enabled = False
        self.default_enabled = False
        self.custom_enabled = True
        self.init_values = dict()
        self.xx = 0

    def start(self, controls=None, title="Opciones", callback=None, item=None, custom_button=None, mod=None):
        logger.trace()
        if xbmcgui.getCurrentWindowDialogId() == 13000:
            return

        self.controls = controls
        self.title = title
        self.callback = callback
        self.item = item
        self.custom_button = custom_button

        if not mod:
            self.module = inspect.currentframe().f_back.f_back.f_code.co_filename
        else:
            self.module = mod

        if not self.controls:
            self.controls = moduletools.get_controls(self.module)
        else:
            self.controls = list(self.controls)

        if not self.controls:
            return None

        if self.title == '':
            self.title = 'Ajustes'

        self.doModal()

        return self.return_value

    def evaluate_conditions(self):
        for c in self.controls:
            c['control'].setEnabled(self.evaluate(self.controls.index(c), c.get('enabled', True)))
            c["show"] = self.evaluate(self.controls.index(c), c.get('visible', True))
            if not c["show"]:
                c['control'].setVisible(c["show"])

        self.visible_controls = [c for c in self.controls if c["show"]]

    def evaluate(self, index, cond):
        res = True

        if type(cond) == bool:
            return cond

        for neg, operator, c_id, value, next_op in re.compile(
                "(!)?(eq|gt|lt|set)?\(([^,]+),[\"']?([^)'\"]*)['\"]?\)[ ]*([+|])?").findall(cond):

            if not c_id.replace('-', '').isdigit():
                return False

            if index + int(c_id) < 0 or index + int(c_id) >= len(self.controls):
                return False

            control_value = self.controls[index + int(c_id)]['control'].getValue()

            operators = {
                'lt': lambda x, z: type(x) == int and type(z) == int and x < z,
                'gt': lambda x, z: type(x) == int and type(z) == int and x > z,
                'eq': lambda x, z: x == z,
                'set': lambda x, z: x == settings.get_setting(z, self.module)
            }

            if value == 'true':
                value = True

            elif value == 'false':
                value = False

            elif value.isdigit():
                value = int(value)

            res = operators[operator](control_value, value)

            if neg:
                res = not res

            if next_op == "|" and res is True:
                break

            if next_op == "+" and res is False:
                break

        return res

    def onInit(self):
        if int(xbmcgui.__version__.replace('.', '')) <= 2250:
            self.setCoordinateResolution(5)
        self.getControl(10002).setLabel(self.title)

        self.controls_width = self.getControl(10008).getWidth() - 25
        self.controls_height = self.getControl(10008).getHeight()
        self.controls_pos_x = self.getControl(10008).getPosition()[0] + self.getControl(10001).getPosition()[0] + 5
        self.controls_pos_y = self.getControl(10008).getPosition()[1] + self.getControl(10001).getPosition()[1] + 5

        self.getControl(10004).setEnabled(False)
        self.getControl(10005).setEnabled(False)
        self.getControl(10006).setEnabled(False)
        self.getControl(10007).setEnabled(False)

        self.check_custom_button()

        ids = []

        for c in self.controls:
            for k, v in c.items():
                if type(v) == str and re.match('^eval\((.*?)\)$', v):
                    c[k] = eval(re.match('^eval\((.*?)\)$', v).group(1))

                if type(v) == list:
                    for x, d in enumerate(v):
                        if type(d) == str and re.match('^eval\((.*?)\)$', d):
                            v[x] = eval(re.match('^eval\((.*?)\)$', d).group(1))

            if 'type' not in c:
                c['type'] = 'label'

            if c.get('id') and c.get('id') in ids:
                continue

            if c["type"] == "bool":
                if not c.get('label'):
                    continue
                if not c.get('id'):
                    continue
                if c.get('value') is None:
                    c['value'] = settings.get_setting(c['id'], self.module)
                if not c.get('default'):
                    c['default'] = False

                c["control"] = ControlRadioButton(
                    label=c["label"],
                    value=c.get('value', False),
                    color=c.get('color', '0xFFFFFFFF'),
                    window=self

                )

            elif c["type"] == 'text':
                if not c.get('label'):
                    continue
                if c.get('value') is None and c.get('id'):
                    c['value'] = settings.get_setting(c['id'], self.module)
                if not c.get('default'):
                    c['default'] = ''

                c["control"] = ControlEdit(
                    label=c["label"],
                    value=c.get('value', ''),
                    color=c.get('color', '0xFFFFFFFF'),
                    hidden=c.get('hidden', False),
                    window=self
                )

            elif c["type"] == 'file':
                if not c.get('label'):
                    continue
                if not c.get('id'):
                    continue
                if c.get('value') is None:
                    c['value'] = settings.get_setting(c['id'], self.module)
                if not c.get('default'):
                    c['default'] = ''

                c["control"] = ControlFile(
                    label=c["label"],
                    value=c.get('value', ''),
                    color=c.get('color', '0xFFFFFFFF'),
                    hidden=c.get('hidden', False),
                    window=self
                )

            elif c["type"] == 'folder':
                if not c.get('label'):
                    continue
                if not c.get('id'):
                    continue
                if c.get('value') is None:
                    c['value'] = settings.get_setting(c['id'], self.module)
                if not c.get('default'):
                    c['default'] = ''

                c["control"] = ControlFile(
                    label=c["label"],
                    value=c.get('value', ''),
                    color=c.get('color', '0xFFFFFFFF'),
                    hidden=c.get('hidden', False),
                    window=self,
                    mode = 1
                )

            elif c["type"] == 'list':
                if not c.get('label'):
                    continue
                if not c.get('id'):
                    continue
                if not type(c.get('lvalues')) == list:
                    continue
                if c.get('value') is None:
                    c['value'] = settings.get_setting(c['id'], self.module)
                if not c.get('default'):
                    c['default'] = 0

                if c.get('mode') == 'label':
                    if c.get('values'):
                        if not c['value'] in c['values']:
                            c['value'] = c['default']
                    else:
                        if not c['value'] in c['lvalues']:
                            c['value'] = c['default']

                c["control"] = ControlList(
                    label=c["label"],
                    value=c.get('value'),
                    lvalues=c['lvalues'],
                    values = c.get('values'),
                    mode=c.get('mode'),
                    color=c.get('color', '0xFFFFFFFF'),
                    window=self
                )

            elif c["type"] == 'label':
                if not c.get('label'):
                    continue
                c["control"] = ControlLabel(
                    label=c["label"],
                    color=c.get('color', '0xFFFFFFFF'),
                    window=self
                )
            if c.get('id'):
                ids.append(c.get('id'))

        self.controls = [c for c in self.controls if "control" in c]

        self.evaluate_conditions()

        self.dispose_controls(0)

        self.getControl(100011).setVisible(False)
        self.getControl(10004).setEnabled(True)
        self.getControl(10005).setEnabled(True)
        self.getControl(10006).setEnabled(True)
        self.getControl(10007).setEnabled(True)

        self.init_values = dict([
            (
                c['id'],
                c.get('value')
            )
            for c in self.controls if not c["type"] == "label" and c.get('id')
        ])
        self.ok_enabled = True
        self.check_custom_button()
        self.check_default()
        self.check_ok()

    def check_custom_button(self):
        types = [c['type'] for c in self.controls if not c['type'] == 'label']

        if self.custom_button:
            self.getControl(10007).setLabel(self.custom_button['label'])
            if not self.custom_enabled:
                self.getControl(10004).setPosition(self.getControl(10004).getPosition()[0] - 85,
                                                   self.getControl(10004).getPosition()[1])
                self.getControl(10005).setPosition(self.getControl(10005).getPosition()[0] - 85,
                                                   self.getControl(10005).getPosition()[1])
                self.getControl(10006).setPosition(self.getControl(10006).getPosition()[0] - 85,
                                                   self.getControl(10006).getPosition()[1])
                self.custom_enabled = True

        elif set(types) == set(['bool']):
            values = [c['control'].getValue() for c in self.controls if not c['type'] == 'label' and 'control' in c]
            if all(values):
                self.getControl(10007).setLabel('Ninguno')
            else:
                self.getControl(10007).setLabel('Todos')

            if not self.custom_enabled:
                self.getControl(10004).setPosition(self.getControl(10004).getPosition()[0] - 85,
                                                   self.getControl(10004).getPosition()[1])
                self.getControl(10005).setPosition(self.getControl(10005).getPosition()[0] - 85,
                                                   self.getControl(10005).getPosition()[1])
                self.getControl(10006).setPosition(self.getControl(10006).getPosition()[0] - 85,
                                                   self.getControl(10006).getPosition()[1])
                self.custom_enabled = True

        else:
            self.getControl(10007).setVisible(False)
            if self.custom_enabled:
                self.getControl(10004).setPosition(self.getControl(10004).getPosition()[0] + 85,
                                                   self.getControl(10004).getPosition()[1])
                self.getControl(10005).setPosition(self.getControl(10005).getPosition()[0] + 85,
                                                   self.getControl(10005).getPosition()[1])
                self.getControl(10006).setPosition(self.getControl(10006).getPosition()[0] + 85,
                                                   self.getControl(10006).getPosition()[1])
                self.custom_enabled = False

    def dispose_controls(self, index, focus=False, force=False):
        show_controls = self.controls_height / (self.height_control + self.space) - 1

        visible_count = 0

        if focus:
            if not index >= self.index or not index <= self.index + show_controls:
                if index < self.index:
                    new_index = index
                else:
                    new_index = index - show_controls
            else:
                new_index = self.index
        else:
            if index + show_controls >= len(self.visible_controls):
                index = len(self.visible_controls) - show_controls - 1
            if index < 0:
                index = 0
            new_index = index

        if self.index != new_index or force:
            for x, c in enumerate(self.visible_controls):
                if x < new_index or visible_count > show_controls or not c["show"]:
                    c['control'].setVisible(False)
                else:
                    c["y"] = self.controls_pos_y + (visible_count * self.height_control) + (visible_count * self.space)
                    visible_count += 1
                    c["control"].setPosition(self.controls_pos_x, c["y"])
                    c['control'].setVisible(True)

            # Calculamos la posicion y tamaño del ScrollBar
            hidden_controls = len(self.visible_controls) - show_controls - 1
            if hidden_controls < 0:
                hidden_controls = 0

            scrollbar_height = self.getControl(10009).getHeight() - (hidden_controls * 3)
            scrollbar_y = self.getControl(10009).getPosition()[1] + (new_index * 3)
            self.getControl(100010).setPosition(self.getControl(10009).getPosition()[0], scrollbar_y)
            self.getControl(100010).setHeight(scrollbar_height)

        self.index = new_index

        if focus:
            self.setFocus(self.visible_controls[index]["control"])

    def check_ok(self):
        if not self.callback:
            if self.init_values == dict([
                (
                        c['id'],
                        c['control'].getValue()
                )
                for c in self.controls if not c["type"] == "label" and c.get('id')
            ]):
                self.getControl(10004).setEnabled(False)
                self.ok_enabled = False
            else:
                self.getControl(10004).setEnabled(True)
                self.ok_enabled = True

    def check_default(self):
        def_values = dict([
            (
                c["id"],
                c.get("default")
            )
            for c in self.controls if not c["type"] == "label" and c.get('id')
        ])

        if def_values == dict([
            (
                    c['id'],
                    c['control'].getValue()
            )
            for c in self.controls if not c["type"] == "label" and c.get('id')
        ]):
            self.getControl(10006).setEnabled(False)
            self.default_enabled = False
        else:
            self.getControl(10006).setEnabled(True)
            self.default_enabled = True

    def getControl(self, cont_id):
        control = filter(lambda c: 'control' in c and cont_id in c['control'].getId(), self.controls)
        if control:
            return control[0]['control']

        return xbmcgui.WindowXMLDialog.getControl(self, cont_id)

    def onClick(self, cont_id):
        # Custom Button
        if cont_id == 10007:
            if not self.custom_button:
                values = [c['control'].getValue() for c in self.controls if not c['type'] == 'label']
                for c in self.controls:
                    if c["type"] == "bool":
                        c["control"].setValue(not all(values))

                self.check_custom_button()
                self.evaluate_conditions()
                self.dispose_controls(self.index, force=True)
                self.check_default()
                self.check_ok()
                return

            if self.custom_button.get('close'):
                self.close()

            for mod in sys.modules.values():
                if hasattr(mod, '__file__'):
                    f = os.path.splitext(mod.__file__)[0]
                    if f == os.path.splitext(self.module)[0]:
                        self.custom_button['values'] = dict([
                            (
                                c['id'],
                                c['control'].getValue()
                            )
                            for c in self.controls if not c['type'] == 'label' and c.get('id')
                        ])
                        self.custom_button = getattr(mod, self.custom_button['callback'])(self.item, self.custom_button)
                        self.check_custom_button()
                        for c in self.controls:
                            c["control"].setValue(self.custom_button['values'][c['id']])

                        self.evaluate_conditions()
                        self.dispose_controls(self.index, force=True)
                        self.check_default()
                        self.check_ok()

        # Valores por defecto
        if cont_id == 10006:
            for c in self.controls:
                if not c['type'] == 'label' and c.get('id'):
                    c["control"].setValue(c["default"])

            self.evaluate_conditions()
            self.dispose_controls(self.index, force=True)
            self.check_default()
            self.check_ok()
            self.check_custom_button()

        # Boton Cancelar y [X]
        if cont_id == 10003 or cont_id == 10005:
            self.close()

        # Boton Aceptar
        if cont_id == 10004:
            self.close()
            if self.callback:
                for mod in sys.modules.values():
                    if hasattr(mod, '__file__'):
                        f = os.path.splitext(mod.__file__)[0]
                        if f == os.path.splitext(self.module)[0]:
                            self.return_value = getattr(mod, self.callback)(self.item, dict([
                                (
                                    c['id'],
                                    c['control'].getValue()
                                )
                                for c in self.controls if not c['type'] == 'label' and c.get('id')
                            ]))
            else:
                values = dict([[c['id'],c['control'].getValue()] for c in self.controls if not c['type'] == 'label' and c.get('id')])
                settings.set_settings(values, self.module)

        # Controles
        control = self.getControl(cont_id)
        if hasattr(control, 'click'):
            control.click(cont_id)
            self.evaluate_conditions()
            self.dispose_controls(self.index, force=True)
            self.check_default()
            self.check_ok()
            self.check_custom_button()

    def onAction(self, raw_action):
        c_id = self.getFocusId()
        action = raw_action.getId()

        # Accion 1: Flecha izquierda
        if action == 1:
            # Si el foco no está en ninguno de los tres botones inferiores, y esta en un "list" cambiamos el valor
            if c_id not in [10004, 10005, 10006, 10007]:
                control = self.getControl(c_id)
                if hasattr(control, 'down'):
                    control.down()
                    self.evaluate_conditions()
                    self.dispose_controls(self.index, force=True)
                    self.check_default()
                    self.check_ok()
                    self.check_custom_button()

            # Si el foco está en alguno de los tres botones inferiores, movemos al siguiente
            else:
                if c_id == 10007 and self.default_enabled:
                    self.setFocusId(10006)

                elif c_id == 10007:
                    self.setFocusId(10005)

                if c_id == 10006:
                    self.setFocusId(10005)

                if c_id == 10005 and self.ok_enabled:
                    self.setFocusId(10004)

        # Accion 1: Flecha derecha
        elif action == 2:
            # Si el foco no está en ninguno de los tres botones inferiores, y esta en un "list" cambiamos el valor
            if c_id not in [10004, 10005, 10006, 10007]:
                control = self.getControl(c_id)
                if hasattr(control, 'up'):
                    control.up()
                    self.evaluate_conditions()
                    self.dispose_controls(self.index, force=True)
                    self.check_default()
                    self.check_ok()
                    self.check_custom_button()

            # Si el foco está en alguno de los tres botones inferiores, movemos al siguiente
            else:
                if c_id == 10004:
                    self.setFocusId(10005)

                if c_id == 10005 and self.default_enabled:
                    self.setFocusId(10006)
                elif c_id == 10005 and self.custom_enabled:
                    self.setFocusId(10007)

                if c_id == 10006 and self.custom_enabled:
                    self.setFocusId(10007)

        # Accion 4: Flecha abajo
        elif action == 4:
            # Si el foco no está en ninguno de los tres botones inferiores, bajamos el foco en los controles de ajustes
            if c_id not in [10004, 10005, 10006, 10007]:
                try:
                    focus_control = [self.visible_controls.index(c) for c in self.visible_controls
                                     if c["control"] == self.getFocus()][0]
                    focus_control += 1
                except Exception:
                    focus_control = 0

                while not focus_control == len(self.visible_controls) and (
                                self.visible_controls[focus_control]["type"] == "label"
                        or not self.visible_controls[focus_control]['control'].getEnabled()
                ):
                    focus_control += 1

                if focus_control >= len(self.visible_controls):
                    self.setFocusId(10005)
                    return

                self.dispose_controls(focus_control, True)

        # Accion 4: Flecha arriba
        elif action == 3:
            # Si el foco no está en ninguno de los tres botones inferiores, subimos el foco en los controles de ajustes
            if c_id not in [10003, 10004, 10005, 10006, 10007]:
                try:
                    focus_control = [self.visible_controls.index(c) for c in self.visible_controls
                                     if c["control"] == self.getFocus()][0]
                    focus_control -= 1

                    while not focus_control == -1 and (
                                    self.visible_controls[focus_control]["type"] == "label"
                            or not self.visible_controls[focus_control]['control'].getEnabled()
                    ):
                        focus_control -= 1

                    if focus_control < 0:
                        focus_control = 0
                except Exception:
                    focus_control = 0

                self.dispose_controls(focus_control, True)

            # Si el foco está en alguno de los tres botones inferiores, ponemos el foco en el ultimo ajuste.
            else:
                focus_control = len(self.visible_controls) - 1
                while not focus_control == -1 and (
                                self.visible_controls[focus_control]["type"] == "label"
                        or not self.visible_controls[focus_control]['control'].getEnabled()
                ):
                    focus_control -= 1
                if focus_control < 0:
                    focus_control = 0

                self.setFocus(self.visible_controls[focus_control]["control"])

        # Accion 104: Scroll arriba
        elif action == 104:
            self.dispose_controls(self.index - 1)

        # Accion 105: Scroll abajo
        elif action == 105:
            self.dispose_controls(self.index + 1)

        elif action in [10, 92]:
            self.close()

        elif action == 504:
            if self.xx > raw_action.getAmount2():
                if (self.xx - int(raw_action.getAmount2())) / (self.height_control + self.space):
                    self.xx -= (self.height_control + self.space)
                    self.dispose_controls(self.index + 1)
            else:
                if (int(raw_action.getAmount2()) - self.xx) / (self.height_control + self.space):
                    self.xx += (self.height_control + self.space)
                self.dispose_controls(self.index - 1)
            return

        elif action == 501:
            self.xx = int(raw_action.getAmount2())


class ControlLabel(xbmcgui.ControlLabel):
    def __new__(cls, **kwargs):
        b_kwargs = {'x': 0,
                    'y': -100,
                    'width': kwargs['window'].controls_width,
                    'height': kwargs['window'].height_control,
                    'label': kwargs['label'],
                    'font': kwargs['window'].font,
                    'textColor': kwargs['color'],
                    'alignment': 4

                    }

        return xbmcgui.ControlLabel.__new__(cls, **b_kwargs)

    def __init__(self, *args, **kwargs):
        kwargs["window"].addControl(self)
        self.setValue(kwargs['label'])
        self.enabled = True

    def click(self, c_id):
        pass

    def setEnabled(self, e):
        xbmcgui.ControlLabel.setEnabled(self, e)
        self.enabled = e

    def getEnabled(self):
        return self.enabled

    def getValue(self):
        return self.getLabel()

    def setValue(self, val):
        self.setLabel(str(val))

    def getId(self):
        return [xbmcgui.ControlLabel.getId(self)]


class ControlList(xbmcgui.ControlButton):
    def __new__(cls, **kwargs):
        b_kwargs = {
            'x': 0,
            'y': -100,
            'width': kwargs['window'].controls_width,
            'height': kwargs['window'].height_control,
            'label': kwargs['label'],
            'font': kwargs['window'].font,
            'textColor': kwargs['color'],
            'disabledColor': '',
            'alignment': 4,
            'focusTexture': os.path.join(kwargs['window'].mediapath, 'Controls', 'InputFO.png'),
            'noFocusTexture': os.path.join(kwargs['window'].mediapath, 'Controls', 'InputNF.png'),
        }
        return xbmcgui.ControlButton.__new__(cls, **b_kwargs)

    def __init__(self, *args, **kwargs):
        self.value = -1
        self.window = kwargs["window"]
        self.lvalues = kwargs['lvalues']
        self.values = kwargs['values']
        self.mode = kwargs['mode']
        self.enabled = True
        self.textControl = xbmcgui.ControlLabel(
            x=0,
            y=-100,
            width=kwargs['window'].controls_width / 2,
            height=kwargs['window'].height_control,
            label='',
            font=kwargs["window"].font,
            textColor=kwargs["color"],
            alignment=4 | 1
        )

        self.upButton = xbmcgui.ControlButton(
            x=0,
            y=-100,
            width=20,
            height=13,
            label='',
            font=kwargs["window"].font,
            textColor=kwargs["color"],
            alignment=4 | 1,
            focusTexture=os.path.join(self.window.mediapath, 'Controls', 'UpFO.png'),
            noFocusTexture=os.path.join(self.window.mediapath, 'Controls', 'UpNF.png')
        )

        self.downButton = xbmcgui.ControlButton(
            x=0,
            y=-100,
            width=20,
            height=13,
            label='',
            font=kwargs["window"].font,
            textColor=kwargs["color"],
            alignment=4 | 1,
            focusTexture=os.path.join(self.window.mediapath, 'Controls',
                                      'DownFO.png'),
            noFocusTexture=os.path.join(self.window.mediapath, 'Controls',
                                        'DownNF.png')
        )

        self.window.addControl(self)
        self.window.addControl(self.textControl)
        self.window.addControl(self.upButton)
        self.window.addControl(self.downButton)
        self.setValue(kwargs['value'])

    def click(self, c_id):
        if c_id == self.upButton.getId():
            self.up()
        if c_id == self.downButton.getId():
            self.down()

    def down(self):
        self.setValue((0, self.value - 1)[self.value > 0])

    def up(self):
        self.setValue((len(self.lvalues) - 1, self.value + 1)[self.value + 1 < len(self.lvalues)])

    def getId(self):
        return [xbmcgui.ControlButton.getId(self), self.textControl.getId(), self.upButton.getId(),
                self.downButton.getId()]

    def setEnabled(self, e):
        xbmcgui.ControlButton.setEnabled(self, e)
        self.textControl.setEnabled(e)
        self.upButton.setEnabled(e)
        self.downButton.setEnabled(e)
        self.enabled = e

    def setVisible(self, e):
        xbmcgui.ControlButton.setVisible(self, e)
        self.textControl.setVisible(e)
        self.upButton.setVisible(e)
        self.downButton.setVisible(e)

    def getEnabled(self):
        return self.enabled

    def setWidth(self, w):
        xbmcgui.ControlButton.setWidth(self, w)
        self.textControl.setWidth(w / 2)
        self.upButton.setWidth(w / 2)
        self.downButton.setWidth(w / 2)

    def setHeight(self, w):
        xbmcgui.ControlButton.setHeight(self, w)
        self.textControl.setHeight(w)
        self.upButton.setHeight(w)
        self.downButton.setHeight(w)

    def setPosition(self, x, y):
        xbmcgui.ControlButton.setPosition(self, x, y)
        self.textControl.setPosition(x + self.getWidth() - self.textControl.getWidth() - 35, y)
        self.upButton.setPosition(x + self.getWidth() - self.upButton.getWidth() - 10, y + 3)
        self.downButton.setPosition(x + self.getWidth() - self.downButton.getWidth() - 10, y + 19)

    def setValue(self, value):
        if self.mode == 'label' and type(value) == str:
            if self.values:
                index = self.values.index(value)
            else:
                index = self.lvalues.index(value)
        else:
            index = value or 0
        self.value = index
        self.textControl.setLabel(self.lvalues[index])

    def getValue(self):
        if self.mode == 'label':
            if self.values:
                return self.values[self.value]
            else:
                return self.lvalues[self.value]
        else:
            return self.value


class ControlRadioButton(xbmcgui.ControlRadioButton):
    def __new__(cls, **kwargs):
        b_kwargs = {
            'x': 0,
            'y': -100,
            'width': kwargs['window'].controls_width,
            'height': kwargs['window'].height_control,
            'label': kwargs['label'],
            'font': kwargs['window'].font,
            'textColor': kwargs['color'],
            'focusTexture': os.path.join(kwargs['window'].mediapath, 'Controls', 'InputFO.png'),
            'noFocusTexture': os.path.join(kwargs['window'].mediapath, 'Controls', 'InputNF.png'),
            'focusOnTexture': os.path.join(kwargs['window'].mediapath, 'Controls', 'RadioON.png'),
            'noFocusOnTexture': os.path.join(kwargs['window'].mediapath, 'Controls', 'RadioON.png'),
            'focusOffTexture': os.path.join(kwargs['window'].mediapath, 'Controls', 'RadioOFF.png'),
            'noFocusOffTexture': os.path.join(kwargs['window'].mediapath, 'Controls', 'RadioOFF.png'),

        }
        return xbmcgui.ControlRadioButton.__new__(cls, **b_kwargs)

    def __init__(self, *args, **kwargs):
        kwargs["window"].addControl(self)
        self.value = ''
        self.setValue(kwargs['value'])
        self.enabled = True

    def click(self, c_id):
        self.value = not self.value

    def setEnabled(self, e):
        xbmcgui.ControlRadioButton.setEnabled(self, e)
        self.enabled = e

    def getEnabled(self):
        return self.enabled

    def getValue(self):
        return self.value

    def setValue(self, val):
        self.setSelected(val)
        self.value = val

    def getId(self):
        return [xbmcgui.ControlButton.getId(self)]


class ControlEdit(xbmcgui.ControlButton):
    def __new__(cls, **kwargs):
        b_kwargs = {
            'x': 0,
            'y': -100,
            'width': kwargs['window'].controls_width,
            'height': kwargs['window'].height_control,
            'label': kwargs['label'],
            'font': kwargs['window'].font,
            'textColor': kwargs['color'],
            'disabledColor': '',
            'alignment': 4,
            'focusTexture': os.path.join(kwargs['window'].mediapath, 'Controls', 'InputFO.png'),
            'noFocusTexture': os.path.join(kwargs['window'].mediapath, 'Controls', 'InputNF.png'),
        }
        return xbmcgui.ControlButton.__new__(cls, **b_kwargs)

    def __init__(self, *args, **kwargs):
        self.isPassword = kwargs["hidden"]
        self.window = kwargs["window"]
        self.enabled = True
        self.text = ''
        self.textControl = xbmcgui.ControlLabel(
            x=0,
            y=-100,
            width=kwargs['window'].controls_width / 2,
            height=kwargs['window'].height_control,
            label='',
            font=kwargs["window"].font,
            textColor=kwargs["color"],
            alignment=4 | 1
        )

        self.window.addControl(self)
        self.window.addControl(self.textControl)
        self.setValue(kwargs['value'])

    def click(self, c_id):
        val = platformtools.dialog_input(self.text, '', self.isPassword)
        if val is not None:
            self.setValue(val)

    def getId(self):
        return [xbmcgui.ControlButton.getId(self), self.textControl.getId()]

    def setEnabled(self, e):
        xbmcgui.ControlButton.setEnabled(self, e)
        self.textControl.setEnabled(e)
        self.enabled = e

    def getEnabled(self):
        return self.enabled

    def setVisible(self, e):
        xbmcgui.ControlButton.setVisible(self, e)
        self.textControl.setVisible(e)

    def setWidth(self, w):
        xbmcgui.ControlButton.setWidth(self, w)
        self.textControl.setWidth(w / 2)

    def setHeight(self, w):
        xbmcgui.ControlButton.setHeight(self, w)
        self.textControl.setHeight(w)

    def setPosition(self, x, y):
        xbmcgui.ControlButton.setPosition(self, x, y)
        self.textControl.setPosition(x + self.getWidth() - self.textControl.getWidth() - 10, y)

    def setValue(self, text):
        self.text = text
        if self.isPassword:
            self.textControl.setLabel("*" * len(self.text))
        else:
            self.textControl.setLabel(self.text)

    def getValue(self):
        return self.text


class ControlFile(ControlEdit):
    def __init__(self, *args,  **kwargs):
        ControlEdit.__init__(self, *args,  **kwargs)
        self.mode = kwargs.get('mode', 0)

    def click(self, c_id):
        mode = platformtools.dialog_yesno(
            'Ajustes',
            'Como deseas elegir la ruta',
            nolabel='Escribir',
            yeslabel='Explorar'
        )
        if not mode:
            val = platformtools.dialog_input(self.text, '', self.isPassword)
            if val is not None:
                self.setValue(val)
        else:
            if self.mode == 0:
                heading = 'Selecciona un archivo'
            elif self.mode == 1:
                heading = 'Selecciona una carpeta'


            try:
                path = self.text
                if self.mode == 0:
                    path = filetools.dirname(path)
                files = filetools.listdir(path)
            except Exception:
                files = filetools.listdir(sysinfo.data_path)
                path = sysinfo.data_path

            drives = [chr(x) + ":\\" for x in range(65, 90) if os.path.exists(chr(x) + ":\\")]

            while True:
                if self.mode == 1:
                    files = filter(lambda x: filetools.isdir(filetools.join(path, x)), files)
                    files.insert(0, '[COLOR blue]...[/COLOR]')
                    files.insert(0, '[COLOR blue]Seleccionar[/COLOR]')
                    if len(drives):
                        files.insert(0, '[COLOR blue]Seleccionar disco...[/COLOR]')
                else:
                    files.insert(0, '[COLOR blue]...[/COLOR]')
                    if drives:
                        files.insert(0, '[COLOR blue]Seleccionar disco...[/COLOR]')


                index = platformtools.dialog_select(heading, files)
                # Has seleccionado cancelar, se guarda la carpeta en la que estabas
                if index == -1:
                    return

                # Has seleccionado '..' retrocedemos un directorio
                elif files[index] == '[COLOR blue]...[/COLOR]':
                    path = filetools.dirname(path)
                    files = filetools.listdir(path)

                elif files[index] == '[COLOR blue]Seleccionar disco...[/COLOR]':
                    index = platformtools.dialog_select('Selecciona el disco', drives)
                    path = drives[index]
                    files = filetools.listdir(path)

                elif files[index] == '[COLOR blue]Seleccionar[/COLOR]':
                    self.setValue(path)
                    return
                # Has seleccionado un archivo o carpeta
                else:
                    # Si es una carpeta entramos y mostramos los archivos que contiene
                    # Si es un archivo salimos de bucle, se guardara el archivo seleccionado
                    if filetools.isdir(filetools.join(path,files[index])):
                        path = filetools.join(path,files[index])
                        files = filetools.listdir(path)
                    else:
                        self.setValue(os.path.join(path, files[index]))
                        return
