## -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

# Moodle Package

import requests

_STAT_OK = 200

_END_AUTH = "login/token.php"
_END_REST = "webservice/rest/server.php"

### Exceptions ###

class WSError(Exception):
    """Base class for WS Exceptions"""

    def __init__(self, *args, **kwargs):
        super(WSError, self).__init__(*args, **kwargs)

class WSAuthError(WSError):
    """Class for WS Auth Exceptions"""

    def __init__(self, err):
        msg = "{:s}".format(err)
        super(WSAuthError, self).__init__(msg)


### Decorators ###

def requires_auth(func):
    def _wrapper(*args, **kwargs):
        if args[0].is_authenticated():
            return func(*args, **kwargs)
        else:
            raise WSAuthError("{:s}() requires authentication".format(func.__name__))
    return _wrapper


### Classes ###

class WS(object):

    def __init__(self, host, token=None):
        self.host = host
        self.token = token

    def authenticate(self, user, password, service, error=False):
        url = "{:s}/{:s}".format(self.host, _END_AUTH)
        args = {'username': user, 'password': password, 'service': service}
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

    ## Base Request ##

    @requires_auth
    def make_request(self, function, params=None):
        url = "{:s}/{:s}".format(self.host, _END_REST)
        args = {'moodlewsrestformat': 'json', 'wstoken': self.token, 'wsfunction': function}
        if params:
            args += params
        r = requests.post(url, params=args)
        r.raise_for_status()
        res = r.json()
        if 'exception' in res:
            msg = "{:s}: {:s}".format(res['errorcode'], res['message'])
            raise WSError(msg)
        else:
            return res

    ## Raw Endpoints ##

    @requires_auth
    def core_webservice_get_site_info(self):
        function = 'core_webservice_get_site_info'
        params = None
        return self.make_request(function, params)


    ## Constructors ##
    @requires_auth
    def get_WSUser(self):
        return WSUser(self)

class WSUser(WS):

    def __init__(self, ws):

        # Setup Connection
        self.host = ws.host
        self.token = ws.token

        # Get Data
        data = self.core_webservice_get_site_info()
        self.username = data['username']
        self.userid = data['userid']
        self.first = data['firstname']
        self.last = data['lastname']
        self.full = data['fullname']
        self.functions = data['functions']
