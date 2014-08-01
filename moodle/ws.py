## -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

# Moodle Package

import requests

_STAT_OK = 200

_END_AUTH = "login/token.php"

class WSError(Exception):
    """Base class for WS Exceptions"""

    def __init__(self, *args, **kwargs):
        super(WSError, self).__init__(*args, **kwargs)

class WSAuthError(WSError):
    """Class for WS Auth Exceptions"""

    def __init__(self, err):
        msg = "{:s}".format(err)
        super(WSAuthError, self).__init__(msg)


class WS(object):

    def __init__(self, host, service, token=None):
        super(WS, self).__init__()
        self.host = host
        self.service = service
        self.token = token

    def authenticate(self, user, password, error=False):
        url = "{:s}/{:s}".format(self.host, _END_AUTH)
        args = {'username': user, 'password': password, 'service': self.service}
        r = requests.get(url, params=args)
        r.raise_for_status()
        res = r.json()
        if 'error' in res:
            if error:
                raise WSAuthError(res['error'])
            else:
                return False
        else:
            self.token = r.json()['token']
            return True

    def is_authenticated(self):
        if self.token is None:
            return False
        else:
            return True
