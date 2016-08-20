## -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

# Moodle Package


import string
import logging
import traceback

import requests


_END_AUTH = "login/token.php"
_END_REST = "webservice/rest/server.php"


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())


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

    ## Auth Methods ##

    def authenticate(self, user, password, service, error=False):
        self.username = user
        url = "{:s}/{:s}".format(self.host, _END_AUTH)
        args = {'username': user, 'password': password, 'service': service}
        try:
            r = requests.get(url, params=args)
        except requests.exceptions.SSLError as e:
            msg = "SSL verification failed for '{:s}': {:s}".format(self.host, e)
            raise WSError(msg)
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            msg = "Auth request to '{:s}' failed: {:s}".format(self.host, e)
            raise WSError(msg)
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
            args.update(params)
        try:
            r = requests.post(url, params=args)
        except requests.exceptions.SSLError as e:
            msg = "SSL verification failed for '{:s}': {:s}".format(self.host, e)
            raise WSError(msg)
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            msg = "Request to '{:s}' failed: {:s}".format(self.host, e)
            raise WSError(msg)
        res = r.json()
        if res:
            if 'exception' in res:
                msg = "{:s}: {:s}".format(res['errorcode'], res['message'])
                raise WSError(msg)
            else:
                return res
        else:
            return None

    ## Raw Endpoints ##

    @requires_auth
    def core_webservice_get_site_info(self):
        function = 'core_webservice_get_site_info'
        params = {}
        return self.make_request(function, params)

    @requires_auth
    def core_grades_get_grades(self, crs_id, component="", act_id=None, usr_ids = []):
        function = 'core_grades_get_grades'
        params = {}
        params['courseid'] = int(crs_id)
        if component:
            params['component'] = str(component)
        if act_id:
            params['activityid'] = int(act_id)
        if usr_ids:
            params.update(self._build_array('userids', usr_ids))
        return self.make_request(function, params)

    @requires_auth
    def core_user_get_users(self, criteria):
        function = 'core_user_get_users'
        params = {}
        params.update(self._build_tuple_array('criteria', criteria))
        return self.make_request(function, params)

    @requires_auth
    def core_enrol_get_enrolled_users(self, crs_id, options=None):
        function = 'core_enrol_get_enrolled_users'
        params = {}
        params['courseid'] = int(crs_id)
        if options:
            params.update(self._build_tuple_array('options', options, keyname='name'))
        return self.make_request(function, params)

    @requires_auth
    def core_files_get_files(self, cxt_id, component, itm_id, filearea, filepath, filename,
                             modified_ts=None, cxt_level=None, cxt_instanceid=None):
        function = 'core_files_upload'
        params = {}
        params['contextid'] = int(cxt_id)
        params['component'] = str(component)
        params['itemid'] = int(itm_id)
        params['filearea'] = str(filearea)
        params['filepath'] = str(filepath)
        params['filename'] = str(filename)
        if modified_ts:
            params['modified'] = int(modified_ts)
        if cxt_level:
            params['contextlevel'] = str(cxt_level)
        if cxt_instanceid:
            params['instanceid'] = int(cxt_instanceid)
        return self.make_request(function, params)

    @requires_auth
    def core_files_upload(self, itm_id, component, filearea, filepath, filename, filecontent,
                          cxt_id=None, cxt_level=None, cxt_instanceid=None):
        function = 'core_files_upload'
        params = {}
        params['itemid'] = int(itm_id)
        params['component'] = str(component)
        params['filearea'] = str(filearea)
        params['filepath'] = str(filepath)
        params['filename'] = str(filename)
        params['filecontent'] = str(filecontent) #Base64?
        if cxt_id:
            params['contextid'] = int(cxt_id)
        if cxt_level:
            params['contextlevel'] = str(cxt_level)
        if cxt_instanceid:
            params['instanceid'] = int(cxt_instanceid)
        return self.make_request(function, params)

    @requires_auth
    def mod_assign_get_assignments(self, crs_ids):
        function = 'mod_assign_get_assignments'
        params = {}
        params.update(self._build_array('courseids', crs_ids))
        return self.make_request(function, params)

    @requires_auth
    def mod_assign_get_grades(self, asn_ids):
        function = 'mod_assign_get_grades'
        params = {}
        params.update(self._build_array('assignmentids', asn_ids))
        return self.make_request(function, params)

    @requires_auth
    def mod_assign_save_grade(self, asn_id, usr_id, grade,
                              attempt=-1, addattempt=0, state="Graded", applyall=1,
                              comment="", comment_format=0, file_mgr=0):

        # For some reason, Moodle chokes on '<' in the comment field...
        comment = comment.translate(string.maketrans("<", "?"))

        function = 'mod_assign_save_grade'
        params = {}
        params['assignmentid'] = int(asn_id)
        params['userid'] = int(usr_id)
        params['grade'] = float(grade)
        params['attemptnumber'] = int(attempt)
        params['addattempt'] = int(addattempt)
        params['workflowstate'] = str(state)
        params['applytoall'] = int(applyall)
        params['plugindata[assignfeedbackcomments_editor][text]'] = str(comment)
        params['plugindata[assignfeedbackcomments_editor][format]'] = int(comment_format)
        params['plugindata[files_filemanager]'] = int(file_mgr)
        return self.make_request(function, params)

    ## Constructors ##
    @requires_auth
    def get_WSUser(self):
        return WSUser(self)

    ## Helpers ##
    def _build_array(self, key, vals):
        array = {}
        index = 0
        for val in vals:
            array['{:s}[{:d}]'.format(key, index)] = int(val)
            index += 1
        return array

    def _build_tuple_array(self, key, tuples, keyname='key', valuename='value'):
        array = {}
        index = 0
        for tup in tuples:
            array['{:s}[{:d}][{:s}]'.format(key, index, keyname)] = tup[0]
            array['{:s}[{:d}][{:s}]'.format(key, index, valuename)] = tup[1]
            index += 1
        return array


class WSUser(WS):

    def __init__(self, ws):

        # Check Args
        if not ws.is_authenticated():
            raise ValueError("'ws' must be authenticated")
        if not ws.host:
            raise ValueError("Requires 'ws' host")
        if not ws.token:
            raise ValueError("Requires 'ws' token")

        # Get Raw Data
        self.host = ws.host
        self.token = ws.token

        # Use core_webservice_get_site_info
        logger.debug("Trying core_webservice_get_site_info...")
        try:
            data = self.core_webservice_get_site_info()
        except Exception as e:
            output = "{}\n".format(e)
            output += traceback.format_exc()
            logger.error(output)
        else:
            logger.debug("data = {}".format(data))
            self.userid = data.get('userid', "")
            self.username = data.get('username', "")
            self.email = data.get('email', "")
            self.first = data.get('firstname', "")
            self.last = data.get('lastname', "")
            self.full = data.get('fullname', "")

        # Bail out early if all data is present
        if (getattr(self, 'userid', None) and \
            getattr(self, 'username', None) and \
            getattr(self, 'email', None) and \
            getattr(self, 'first', None) and \
            getattr(self, 'last', None) and \
            getattr(self, 'full', None)):
            return

        # Use core_user_get_users
        logger.debug("Trying core_user_get_users...")
        if getattr(self, 'userid', None):
            key = 'id'
            value = self.userid
        elif getattr(self, 'username', None):
            key = 'username'
            value = self.username
        elif getattr(ws, 'username', None):
            key = 'username'
            value = ws.username
        else:
            raise ValueError("Requires 'userid' or 'username' to continue")
        try:
            data = ws.core_user_get_users([(key, value)])
        except Exception as e:
            output = "{}\n".format(e)
            output += traceback.format_exc()
            logger.error(output)
        else:
            logger.debug("data = {}".format(data))
            users = data['users']
            if (len(users) > 1):
                raise ValueError("Multiple users returned")
            user = data['users'][0]
            logger.debug("user = {}".format(user))
            if not getattr(self, 'userid', None):
                self.userid = user['id']
            if not getattr(self, 'username', None):
                self.username = user['username']
            if not getattr(self, 'email', None):
                self.email = user.get('email', "")
            if not getattr(self, 'first', None):
                self.first = user.get('firstname', "")
            if not getattr(self, 'last', None):
                self.last = user.get('lastname', "")
            if not getattr(self, 'full', None):
                self.full = user.get('fullname', "")

        # Split fullname if necessary
        if not getattr(self, 'first', None):
            if getattr(self, 'full', ""):
                self.first = getattr(self, 'full', "").split()[0]
        if not getattr(self, 'last', None):
            if getattr(self, 'full', ""):
                self.last = getattr(self, 'full', "").split()[-1]

        # Raise error if missing key data
        if not getattr(self, 'token', None):
            raise ValueError("Missing 'token'")
        if not getattr(self, 'userid', None):
            raise ValueError("Missing 'userid'")
        if not getattr(self, 'username', None):
            raise ValueError("Missing 'username'")
        if not getattr(self, 'email', None):
            raise ValueError("Missing 'email'")

        # Return
        return
