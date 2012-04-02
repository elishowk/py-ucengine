from core import Eventualy, UCError

from user import User, Client
from meeting import Meeting, Channel


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
        """
        Updates or creates a meeting
        """
        params = { 
            'uid':self.uid,
            'sid': self.sid }
        status, resp = self.ucengine.request('GET',
            'meeting/%s'%data.name,
            params=params
        )
        if status == 200:
            params.update({'metadata': data.metadata})
            status, resp = self.ucengine.request('PUT',
                'meeting/%s'%data.name,
                params=params)
            if not status == 200:
                raise UCError(status, resp)
        elif status == 404:
            params.update({
                'metadata': data.metadata,
                'name': data.name })
            status, resp = self.ucengine.request('POST',
                'meeting',
                params=params)
            if not status == 201:
                raise UCError(status, resp)

    def _save_user(self, user):
        """
        create or update a user and its metadata
        """
        values = {}
        values['uid'] = self.uid
        values['sid'] = self.sid
        if user.name is not None: values['name']= user.name
        if user.auth is not None: values['auth']= user.auth
        if user.credential is not None: values['credential']= user.credential
        if user.metadata is not None: values['metadata'] = user.metadata

        if user.uid is None:
            status, resp = self.find_user_by_name(user.name)
        else:
            status, resp = self.find_user_by_id(user.uid)
        # user does not exist
        if status == 404:
            status, resp = self.ucengine.request('POST',
                'user',
                params=values,
            )
            if not status == 201:
                raise UCError(status, resp)
            return
        # user exists
        if status == 200:
            # merges user data
            uid = resp['result']['uid']
            resp['result'].update(values)
            status, resp = self.ucengine.request('PUT',
                'user/%s' % uid,
                params=resp['result']
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
