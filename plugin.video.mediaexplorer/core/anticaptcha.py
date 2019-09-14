# -*- coding: utf-8 -*-
import base64

from core.libs import *


class Anticaptcha:
    image_to_text = 0
    no_captcha = 1
    recaptcha = 2
    fun_captcha = 3

    def __init__(self):
        self.client_key = settings.get_setting('client_key_password', __file__)
        self.dialog = None

    def _request(self, url, post):
        post['clientKey'] = self.client_key

        data = jsontools.load_json(httptools.downloadpage(url, post=jsontools.dump_json(post)).data)
        if data.get('errorId'):
            logger.debug(data)

        return data

    def _get_queue_stats(self, _type):
        if _type == Anticaptcha.image_to_text:
            t = 0
        elif _type == Anticaptcha.no_captcha:
            t = 6
        else:
            return

        post = {
            'queueId': t
        }
        return self._request('https://api.anti-captcha.com/getQueueStats', post=post)

    def _get_task_result(self, taskid, noretry=False):
        post = {
            'taskId': taskid
        }
        data = self._request('https://api.anti-captcha.com/getTaskResult', post=post)

        if data.get('errorId'):
            raise Exception(data['errorDescription'])

        if not data.get('solution'):
            if noretry:
                return
            if self.dialog.iscanceled():
                return
            time.sleep(2)
            if self.dialog.iscanceled():
                return
            return self._get_task_result(taskid)
        else:
            return data['solution']

    def _create_task(self, _type, **kwargs):
        if _type == Anticaptcha.image_to_text:
            data = {
                'type': 'ImageToTextTask',
                'body': base64.b64encode(open(kwargs['file'], 'rb').read()),
                'phrase': kwargs['phrase'],
                'case': kwargs['case'],
                'numeric': kwargs['numeric'],
                'math': kwargs['math'],
                'minLength': kwargs['min_length'],
                'maxLength': kwargs['max_length']
            }
        elif _type == Anticaptcha.no_captcha:
            data = {
                'type': 'NoCaptchaTaskProxyless',
                'websiteURL': kwargs['url'],
                'websiteKey': kwargs['key']
            }

        elif _type == Anticaptcha.recaptcha:
            data = {
                'type': 'RecaptchaV1Task',
                'websiteURL': kwargs['url'],
                'websiteKey': kwargs['key']
            }
        else:
            raise Exception('Unknow type')

        post = {
            'task': data
        }

        data = self._request('https://api.anti-captcha.com/createTask', post=post)

        if data['errorId']:
            raise Exception(data['errorDescription'])
        else:
            return data['taskId']

    @staticmethod
    def sec_to_format(sec):
        return time.strftime('%M:%S', time.gmtime(sec))

    def solve_recaptcha(self, url, site_key):
        self.dialog = platformtools.dialog_progress('Anti Captcha', 'Solicitando solucion para reCAPTCHA...')
        try:
            taskid = self._create_task(_type=Anticaptcha.no_captcha, url=url, key=site_key)
            d = self._get_queue_stats(_type=Anticaptcha.no_captcha)

            estimado = int(d['speed'])
            start = time.time()
            expired = False
            while True:
                if self.dialog.iscanceled():
                    self.dialog.close()
                    return

                restante = estimado - int(time.time() - start)
                if restante >= 0:
                    time.sleep(1)

                    if expired:
                        self.dialog.update(
                            100 - (restante * 100 / estimado),
                            'Solicitando solucion para reCAPTCHA... OK',
                            'Esperando solución, esta tardando mas de lo esperado: %s' % (
                                self.sec_to_format(restante)
                            )
                        )
                    else:
                        self.dialog.update(
                            100 - (restante * 100 / estimado),
                            'Solicitando solucion para reCAPTCHA... OK',
                            'Esperando solución, tiempo aproximado: %s' % (
                                self.sec_to_format(restante)
                            )
                        )
                else:
                    try:
                        data = self._get_task_result(taskid, noretry=True)
                    except Exception, e:
                        self.dialog.update(
                            100,
                            'Solicitando solucion para reCAPTCHA... OK',
                            'Esperando solución... ERROR',
                            e.message
                        )
                        time.sleep(3)
                        self.dialog.close()
                        return

                    if data:
                        self.dialog.update(
                            100,
                            'Solicitando solucion para reCAPTCHA... OK',
                            'Esperando solución... OK'
                        )
                        time.sleep(1)
                        break
                    else:
                        expired = True
                        estimado = 5
                        start = time.time()

        except Exception, e:
            self.dialog.update(100, 'Solicitando solucion para reCAPTCHA... ERROR', e.message)
            time.sleep(3)
            self.dialog.close()
            return

        time.sleep(1)
        self.dialog.close()
        return data['gRecaptchaResponse']

    def solve_recaptcha_v1(self, url, site_key):
        taskid = self._create_task(_type=Anticaptcha.recaptcha, url=url, key=site_key)
        return self._get_task_result(taskid)['gRecaptchaResponse']

    def solve_image(self, path, phrase=False, case=False, numeric=0, math=False, min_length=0, max_lengh=0):
        taskid = self._create_task(_type=Anticaptcha.image_to_text, path=path, phrase=phrase, case=case,
                                   numeric=numeric, math=math, min_length=min_length, max_lengh=max_lengh)
        return self._get_task_result(taskid)

    def get_balance(self):

        data = self._request('https://api.anti-captcha.com/getBalance', post={})

        if data['errorId']:
            raise Exception(data['errorDescription'])
        else:
            return data['balance']


def config(item):
    platformtools.show_settings()
    platformtools.itemlist_refresh()


def get_balance():
    ac = Anticaptcha()

    try:
        return "%s $" % round(ac.get_balance(), 2)
    except Exception:
        logger.error()
        return 'Rellena correctamente el campo "Clave (API Key)" y vuelve a abrir la ventana'


def add_item(itemlist):
    """
    Añade un Item nuevo a itemlist si las credenciales o el saldo de la cuenta Anti-captcha.com no son correctos
    :param itemlist: listado de Items
    :return: True si se ha añadido el item, False en caso contrario
    """
    ac = Anticaptcha()

    item = Item(
        type='highlight',
        action='config',
        channel='anticaptcha',
        poster='http://www.unitag.io/qreator/generate?crs=e2ZRfLkGhCcNX0uPU0VF3l2iWCU5iBS65XqQ37eAYrFw1DqSur4MlY3KDO2'
               'BDD2mBo8u49VJSRUN61r7kZGYhdTmk%252F7zrZPNv%252BvdL8%252F3FZQIsRoRa29g6JCo%252BMr1U9KIrE%252Bnsuv3ZYI6'
               'Py3tmkIQ8%252FknlSWIE9Y3nxNyvdUhaPOJao3Zvov5QhPFA6xJuurGLWWJrqCU8pXUJF5i7ftgiucEjRaq%252F9H38rlvTspPw'
               'v0Mx0v2sMBnfpMyzw8kV6n01MiUS5zTFlBYi25oK2yO9mBbDPiBty3uIWnQWdSB7JAiI%252BHGVfustIYDibtYCPU6AlRxYRQjIr'
               '2c9wCUaVwmbQ%253D%253D&crd=fhOysE0g3Bah%252BuqXA7NPQ%252FQ7YOZeJ7QtAg6rWBbVt0V%252FCuQwgrw5Epy2JqCjWT'
               'kxP7veJc2O2138fFevalfgDcfBb9zsUHWw6C37QCEY4KM%253D'
    )

    try:
        if ac.get_balance() < 0.0005:
            item.label = "Su saldo en Anti-captcha.com es demasiado bajo. "
            itemlist.append(item)
            return True
    except Exception:
        logger.error()
        item.label = "Es necesario disponer de una cuenta con saldo en Anti-captcha.com   "
        itemlist.append(item)
        return True

    return False

# Cambio de nombre del parametro
password = settings.pop_setting("client_key",  __file__)
if password:
    settings.set_setting("client_key_password", password, __file__)