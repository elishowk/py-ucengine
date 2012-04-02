from core import Eventualy, UCError

from user import User, Client
from meeting import Meeting, Channel
import json
import urllib
from datetime import datetime

def safe_encode(data):
    """
    Safe parameters encoding for user's metadata
    """
    if isinstance(data, datetime):
        return data.isoformat()
    if isinstance(data, bool):
        return json.dumps(data)
    elif isinstance(data, dict):
        return dict(map(safe_encode, data.items()))
    elif isinstance(data, (list, tuple, set, frozenset)):
        return type(data)(map(safe_encode, data))
    elif isinstance(data, unicode):
        return data.encode('utf-8')
    else:
        return data

def recursive_urlencode(d):
    def recursion(d, base=None):
        pairs = []
        for key, value in d.items():
            if hasattr(value, 'values'):
                pairs += recursion(value, key)
            else:
                new_pair = None
                if base:
                    new_pair = "%s[%s]=%s" % (base, urllib.quote(str(key)), urllib.quote(str(value)))
                else:
                    new_pair = "%s=%s" % (urllib.quote(str(key)), urllib.quote(str(value)))
                pairs.append(new_pair)
        return pairs
    return '&'.join(recursion(d))

class Session(Eventualy):

    def __init__(self, uce, uid, sid):
        Eventualy.__init__(self)
        self.ucengine = uce
        self.uid = uid
        self.sid = sid

    def time(self):
        "What time is it"
        status, resp = self.ucengine.request('GET',
            'time', params= {
                'uid': self.uid, 'sid': self.sid})
        if status != 200:
            raise UCError(status, resp)
        return resp['result']

    def loop(self):
        "Listen the events"
        self.event_loop('live', params={
                'uid'   : self.uid,
                'sid'   : self.sid,
                'mode': 'longpolling'
                })
        return self

    def close(self):
        "I'm leaving"
        status, resp = self.ucengine.request('DELETE',
            'presence/%s' % self.sid, params={
                'uid': self.uid,
                'sid': self.sid})
        if status != 200:
            raise UCError(status, resp)
        self.event_stop()

    def save(self, data):
        "Save a user or a meeting"
        if issubclass(data.__class__, Client):
            self._save_user(data)
        if issubclass(data.__class__, Channel):
            self._save_meeting(data)

    def _save_meeting(self, data):
        status, resp = self.ucengine.request('GET',
            'meeting/%s'%data.name,
            params={'uid':self.uid, 'sid': self.sid}
        )
        if status == 200:
            status, resp = self.ucengine.request('PUT',
                'meeting/%s'%data.name,
                body={
                    'metadata': data.metadata,
                    'uid': self.uid,
                    'sid': self.sid,
                })
            if not status == 200:
                raise UCError(status, resp)
        else:
            status, resp = self.ucengine.request('POST',
                'meeting',
                body={
                    'name': data.name,
                    'metadata': data.metadata,
                    'uid': self.uid,
                    'sid': self.sid,
                })
            if not status == 201:
                raise UCError(status, resp)

    def _save_user(self, user):
        """
        create or update a user and its metadata
        """
        values = {}
        if user.name is not None: values['name']= user.name
        if user.auth is not None: values['auth']= user.auth
        if user.credential is not None: values['credential']= user.credential
        #if user.metadata is not None:
        #    values['metadata'] = recursive_urlencode(safe_encode(user.metadata))

        if user.uid is None:
            status, resp = self.find_user_by_name(user.name)
        else:
            status, resp = self.find_user_by_id(user.uid)

        if status == 404:
            values['uid'] = self.uid
            values['sid'] = self.sid
            status, resp = self.ucengine.request('POST',
                'user',
                params=values,
                body=user.metadata
            )
            if not status == 201:
                raise UCError(status, resp)
            return
        # user exists
        if status == 200:
            # merges user data
            uid = resp['result']['uid']
            if 'metadata' in values:
                resp['result']['metadata'].update(values['metadata'])
                del values['metadata']
            resp['result'].update(values)
            resp['result']['uid'] = self.uid
            resp['result']['sid'] = self.sid
            status, resp = self.ucengine.request('PUT',
                'user/%s' % uid,
                params={'uid': self.uid, 'sid': self.sid},
                body=resp['result']
            )
            if not status == 200:
                raise UCError(status, resp)
            return

    def add_user_role(self, uid, rolename, meeting):
        """
        Sets a role to a user into a meeting or all meetings
        """ 
        status, resp = self.ucengine.request('POST',
            'user/%s/roles' % uid,
            body={
                'role': rolename,
                'location': meeting,
                'uid': self.uid,
                'sid': self.sid
            }
        )
        if status != 200:
            raise UCError(status, resp)

    def delete_user_role(self, uid, rolename, meeting):
        """
        Deletes a role to a user into a meeting or all meetings
        """ 
        if meeting !="":
            status, resp = self.ucengine.request('DELETE',
                'user/%s/roles/%s/%s' % (uid, rolename, meeting), 
                params = {'uid':self.uid, 'sid': self.sid}
            )
        else:
            status, resp = self.ucengine.request('DELETE',
                'user/%s/roles/%s' % (uid, rolename),
                params = {'uid':self.uid, 'sid': self.sid}
            )
        if status != 200:
            raise UCError(status, resp)
    
    def find_user_by_id(self, uid):
        """
        Search user by ID
        """
        return self.ucengine.request('GET',
            'find/user', params={
                'by_uid': uid,
                'uid': self.uid,
                'sid': self.sid})

    def find_user_by_name(self, name):
        """
        Search user by name
        """
        return self.ucengine.request('GET',
                'find/user', params={
                    'by_name': name,
                    'uid': self.uid,
                    'sid': self.sid})

    def delete(self, data):
        "Delete a user"
        if issubclass(data.__class__, Client):
            status, resp = self.ucengine.request('DELETE',
                'user/%s'%data.uid,
                params={'uid':self.uid, 'sid': self.sid})

    def user(self, uid):
        "Get one user"
        status, resp = self.ucengine.request('GET',
            'user/%s' % uid, params= {
                    'uid': self.uid,
                    'sid': self.sid
                })

        if not status == 200:
            raise UCError(status, resp)
        return resp['result']

    def users(self):
        "Get all users"
        status, resp = self.ucengine.request('GET',
            'user', params={
                'uid': self.uid,
                'sid': self.sid
        })
        if not status == 200:
            raise UCError(status, resp)

        us = []
        for u in resp['result']:
            us.append(
                User(u['name'],
                    metadata = u['metadata'],
                    uid = u['uid'])
            )
        return us

    def meeting(self, name):
        "Get a meeting"
        status, resp = self.ucengine.request('GET',
            'meeting/%s' % name, params={
                'uid': self.uid,
                'sid': self.sid
        })
        if status == 404:
            return None
        if not status == 200:
            raise UCError(status, resp)
        m = resp['result']
        return Meeting(name, metadata = m['metadata'])
