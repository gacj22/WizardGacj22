# -*- coding: utf-8 -*-
from core.libs import *

FP_URL = 'https://friendpaste.com'

def create(text, code="", title="", language="text", privacy="private", json=False):
    logger.trace()
    reason = 'Unknown error'
    try:
        code = code if code else int(time.time())
        payload = {
            "paste_snippet": text,
            "paste_language": language,
            "paste_title": title,
            "paste_code": code,
            "paste_privacy": privacy, # "open",  'public', 'private'
            "paste_password": code, # No funciona
            "psubmit": "Submit post"
        }
        req = urllib2.Request('%s/' % FP_URL, urllib.urlencode(payload), headers={'Accept': 'application/json'})
        r = urllib2.urlopen(req).read()

        if scrapertools.find_single_match(r, '<h2 class="errors">Something was wrong!</h2>'):
            data = scrapertools.find_single_match(r, '<ul class="errors">(.*?)<div')
            t = '| '.join(scrapertools.find_multiple_matches(data, '<ul><li>([^<]+)</li></ul>'))
            reason = t if t else reason
            raise ()

        else:
            r = jsontools.load_json(r)
            if not lock(r['id'], code):
                raise()

        return r if json else {'reason': None, 'id': r['id'], 'snippet': r['snippet']}

    except urllib2.HTTPError, e:
        return {'id': None, 'reason': '%s %s' %(e.code, e.msg), 'snippet': None}

    except:
        return {'id': None, 'reason': reason, 'snippet': None}


def read(id, json=False):
    logger.trace()
    try:
        req = urllib2.Request('%s/%s' % (FP_URL, id), headers={'Accept': 'application/json'})
        r = urllib2.urlopen(req).read()
        r = jsontools.load_json(r)

        return r if json else {'reason': None, 'id': r['id'], 'snippet':r['snippet']}
    except:
        return {'id': None, 'reason': 'Unknown', 'snippet': None}


def update(id, text, code="", title="", language="text", json=False):
    logger.trace()
    reason = 'Unknown error'
    try:
        if code and not unlock(id, code):
            reason= 'Impossible to unlock'
            raise()

        payload = {
            'paste_snippet': text,
            'paste_language': language,
            'paste_title': title,
            "psubmit": "Submit post"
        }

        req = urllib2.Request('%s/%s/edit' % (FP_URL, id), urllib.urlencode(payload), headers={'Accept': 'application/json'})
        r = urllib2.urlopen(req).read()

        if scrapertools.find_single_match(r,'<h2 class="errors">Something was wrong!</h2>'):
            data = scrapertools.find_single_match(r, '<ul class="errors">(.*?)<h2>Edit')
            t = '| '.join(scrapertools.find_multiple_matches(data, '<ul><li>([^<]+)</li></ul>'))
            reason = t if t else reason
            raise()
        else:
            r = jsontools.load_json(r)
            return r if json else {'reason': None, 'id': r['id'], 'snippet': r['snippet']}
    except:
            return {'id': None, 'reason': 'Unknown', 'snippet': None}

    finally:
        if code:
            lock(id, code)


def lock(id, code):
    try:
        payload = {
            "edit_code": code,
            "flock": "Lock"
        }

        req = urllib2.Request('%s/%s/lock' % (FP_URL, id), urllib.urlencode(payload))
        r = urllib2.urlopen(req).read()

        if scrapertools.find_single_match(r,'<li class="lock" title="Lock edit">'):
            r = urllib2.urlopen(req).read()

        if scrapertools.find_single_match(r,'class="errors"') or scrapertools.find_single_match(r,'<li class="lock" title="Lock edit">'):
            raise()

        return True
    except:
        return False


def unlock(id, code):
    try:
        payload = {
            "edit_code": code,
            "funlock": "Unlock"
        }

        req = urllib2.Request('%s/%s/unlock' % (FP_URL, id), urllib.urlencode(payload))
        r = urllib2.urlopen(req).read()

        if scrapertools.find_single_match(r,'<li class="lock" title="Unlock edit">'):
            r = urllib2.urlopen(req).read()

        if scrapertools.find_single_match(r,'class="errors"') or scrapertools.find_single_match(r,'<li class="lock" title="Unlock edit">'):
            raise()

        return True
    except:
        return False
