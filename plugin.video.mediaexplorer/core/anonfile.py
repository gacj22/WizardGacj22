# -*- coding: utf-8 -*-
import mimetypes
import random

from core.libs import *


class FileUpload:
    def __init__(self, fieldname, data, filename=None):
        if isinstance(data, file):
            self.body = data.read()
            self.filename = filename or os.path.basename(data.name)
            self.mimetype = mimetypes.guess_type(data.name)[0]
        else:
            if os.path.isfile(data):
                self.body = open(data, 'rb').read()
                self.filename = filename or os.path.basename(data)
                self.mimetype = mimetypes.guess_type(data)[0]
            else:
                self.filename = filename
                self.body = data
                self.mimetype = 'text/plain'

        self.fieldname = fieldname
        self.length = len(self.body)
        self.boundary = '---------------------------%s' % random.randint(100000000000000, 999999999999999)
        self.headers = {
            'Conent-Length': self.length,
            'Content-Type': 'multipart/form-data; boundary=%s' % self.boundary
        }

    @property
    def post(self):
        data = [
            b'--%s' % self.boundary,
            b'Content-Disposition: file; name="%s"; filename="%s"' % (self.fieldname, self.filename),
            b'Content-Type: %s' % self.mimetype,
            b'',
            self.body,
            b'--%s--' % self.boundary
        ]

        return b'\r\n'.join(data)


def upload(path, filename=None):
    form = FileUpload('file', path, filename)

    response = httptools.downloadpage('https://anonfile.com/api/upload', post=form.post, headers=form.headers).data
    try:
        response = jsontools.load_json(response)
    except Exception:
        return False
    else:
        if response['status']:
            return response['data']['file']['metadata']['id']
        else:
            return False


def download(file_id, path):
    logger.trace()
    data = httptools.downloadpage('https://anonfile.com/%s' % file_id).data
    url = scrapertools.find_single_match(data, '<a type="button" id="download-url".*?href="([^"]+)">')
    logger.debug(url)
    response = httptools.downloadpage(url)
    if response.sucess:
        open(path, 'wb').write(response.data)
        return True
    else:
        return False
