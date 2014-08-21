## -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

# Moodle Package


import string

import requests


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

    ## Auth Methods ##

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
            args.update(params)
        r = requests.post(url, params=args)
        r.raise_for_status()
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
            params['instanceid'] = int(cxt_instance_id)
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
            params['instanceid'] = int(cxt_instance_id)
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
        comment = comment[start:end].translate(string.maketrans("<", "?"))

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
