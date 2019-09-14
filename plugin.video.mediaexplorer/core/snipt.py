# -*- coding: utf-8 -*-
from core.libs import *


def get_apikey(username, password):
    logger.trace()

    data = httptools.downloadpage('https://snipt.net/login/').data
    post = {
        'csrfmiddlewaretoken': scrapertools.find_single_match(data, "name='csrfmiddlewaretoken' value='([^']+)'"),
        'username': username,
        'password': password,
        'next': ''
    }
    headers = {'Referer': 'https://snipt.net/login/'}

    data = httptools.downloadpage('https://snipt.net/login/', post=post, headers=headers).data

    if '<div class="alert alert-error">' in data:
        error = scrapertools.find_single_match(data, '<div class="alert alert-error">.*?([^<]+)')
        #logger.debug(data)
        logger.debug('Error: %s' % error.strip())
        return None
    else:
        return scrapertools.find_single_match(data, "window.api_key = '([^']+)")


def create(username, apikey, text, title="", lexer='text', public=True):
    logger.trace()

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'ApiKey %s:%s' % (username, apikey)
    }
    post = jsontools.dump_json({
        'title': title,
        'lexer': lexer,
        'code': text,
        'public': public
    })

    data = httptools.downloadpage(
        'https://snipt.net/api/private/snipt/',
        post=post,
        headers=headers
    ).data

    ret = jsontools.load_json(data)

    return ret.get('id', None)


def read(snipt_id, format='raw', username=None, apikey=None):
    logger.trace()

    headers = {'Content-Type': 'application/json'}

    if username and apikey:
        headers['Authorization'] = 'ApiKey %s:%s' % (username, apikey)
        data = httptools.downloadpage('https://snipt.net/api/private/snipt/%s/?format=json' % snipt_id, headers=headers)
    else:
        data = httptools.downloadpage('https://snipt.net/api/public/snipt/%s/?format=json' % snipt_id, headers=headers)

    if data.code != 200:
        return None

    data = jsontools.load_json(data.data)

    if format == 'raw':
        raw_url = 'https://snipt.net' + data['raw_url']
        return httptools.downloadpage(raw_url).data.strip()

    return data


def get_snipts(username, apikey):
    logger.trace()

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'ApiKey %s:%s' % (username, apikey)
    }

    data = httptools.downloadpage('https://snipt.net/api/private/snipt/', headers=headers)

    if data.code != 200:
        return None

    data = jsontools.load_json(data.data)

    return [{'title': s['title'], 'data': s['code'], 'id': s['id']} for s in data['objects']]


def update(username, apikey, snipt_id, text, title=None):
    logger.trace()

    url = 'https://snipt.net/api/private/snipt/%s/' % snipt_id

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'ApiKey %s:%s' % (username, apikey)
    }

    post = {
        'code': text,
        'tags': '',
    }

    if title is not None:
        post['title'] = title

    data = httptools.downloadpage(url, jsontools.dump_json(post), headers=headers, method='patch').data
    return data


def delete(username, apikey, snipt_id):
    logger.trace()

    url = 'https://snipt.net/api/private/snipt/%s/' % snipt_id
    headers = {'Authorization': 'ApiKey %s:%s' % (username, apikey)}

    data = httptools.downloadpage(url, headers=headers, method='delete')

    if data.code != 200:
        return False

    return True


def create_acount(username=None, password=None, email=None):
    import random
    import string

    apikey = ''
    letters = string.ascii_letters + string.digits

    if not username:
        username = ''.join(random.choice(letters) for i in range(12))
    if not password:
        password = ''.join(random.choice(letters) for i in range(12))
    if not email:
        email = username + '@' + ''.join(random.choice(letters) for i in range(6)) + '.com'

    data = httptools.downloadpage('https://snipt.net/register/').data
    crsf = scrapertools.find_single_match(data, "name='csrfmiddlewaretoken' value='([^']+)'")

    if not crsf:
        httptools.downloadpage('https://snipt.net/logout/')
        data = httptools.downloadpage('https://snipt.net/register/').data
        crsf = scrapertools.find_single_match(data, "name='csrfmiddlewaretoken' value='([^']+)'")

    post = {
        'csrfmiddlewaretoken': crsf,
        'username': username,
        'email': email,
        'password1': password,
        'password2': password
    }
    headers = {'Referer': 'https://snipt.net/register/'}

    data = httptools.downloadpage('https://snipt.net/register/', post=post, headers=headers).data
    #logger.debug(data)
    if 'A user with that username already exists' in data:
        logger.debug('Error al crear la cuenta: El usuario ya existe')

    elif "Signup complete! You're now logged in." in data:
        logger.debug('Cuenta creada con exito.')
        apikey = scrapertools.find_single_match(data, "window.api_key = '([^']+)")

    elif '<a href="/%s/">My snipts</a' % username in data:
        data = httptools.downloadpage('https://snipt.net/%s/' % username).data
        logger.debug('Cuenta creada con exito.')
        apikey = scrapertools.find_single_match(data, "window.api_key = '([^']+)")

    else:
        logger.debug('Error al crear la cuenta: Error desconocido')

    if apikey:
        return (username, password, apikey)
    else:
        return False
