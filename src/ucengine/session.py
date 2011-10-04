import urllib

from core import Eventualy, UCError

from user import User, Client
from meeting import Meeting, Channel


class Session(Eventualy):

    def __init__(self, uce, uid, sid):
        Eventualy.__init__(self)
        self.ucengine = uce
        self.uid = uid
        self.sid = sid

    #FIXME handling authentification
    def request(self, method, url, body={}, expect=200):
        pass

    def time(self):
        "What time is it"
        status, resp = self.ucengine.request('GET',
            '/time?%s' % urllib.urlencode({
                'uid': self.uid, 'sid': self.sid}))
        if status != 200:
            raise UCError(status, resp)
        return resp['result']

    def infos(self):
        "Infos about the server"
        status, resp = self.ucengine.request('GET',
            '/infos?%s' % urllib.urlencode({
            'uid': self.uid, 'sid': self.sid}))
        if status != 200:
            raise UCError(status, resp)
        return resp['result']

    def loop(self):
        "Listen the events"
        self.event_loop('/live?%s' % urllib.urlencode({
                'uid'   : self.uid,
                'sid'   : self.sid,
                'mode': 'longpolling'
                }))
        return self

    def close(self):
        "I'm leaving"
        status, resp = self.ucengine.request('DELETE',
            '/presence/%s?%s' % (self.sid, urllib.urlencode({
                'uid': self.uid,
                'sid': self.sid}))
                )
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
        values = {
            'start': data.start,
            'end': data.end,
            'metadata': data.metadata,
            'uid': self.uid,
            'sid': self.sid,
         }
        status, resp = self.ucengine.request('GET',
            '/meeting/all/%s?%s' % (data.name),
            urllib.urlencode({'uid':self.uid, 'sid': self.sid}))
        if status == 200:
            status, resp = self.ucengine.request('PUT',
                '/meeting/all/%s' % data.name,
                values)
            if not status == 200:
                raise UCError(status, resp)
        else:
            status, resp = self.ucengine.request('POST',
                '/meeting/all/',
                values)
            if not status == 201:
                raise UCError(status, resp)

    def _save_user(self, user):
        """
        create or update a user after a find by name
        """
        if user.uid is None:
            status, resp = self.find_user_by_name(user.name)
        else:
            status, resp = self.find_user_by_id(user.uid)

        if status == 404:
            status, resp = self.ucengine.request('POST',
                '/user?%s'%urllib.urlencode({
                    'uid': self.uid,
                    'sid': self.sid,
                    'name': user.name,
                    'auth': user.auth,
                    'credential': user.credential
                }),
                user.metadata
            )
            if not status == 201:
                raise UCError(status, resp)
            return
        # user exists
        if status == 200:
            # merges user data
            uid = resp['result']['uid']
            resp['result']['metadata'].update(user.metadata)
            status, resp = self.ucengine.request('PUT',
                '/user/%s?%s' % (uid, 
                    urllib.urlencode({
                        'uid': self.uid,
                        'sid': self.sid,
                        'name': user.name,
                        'auth': user.auth,
                        'credential': user.credential
                    })
                ),
                resp['result']['metadata']
            )
            if not status == 200:
                raise UCError(status, resp)
            return


    def add_user_role(self, uid, rolename, meeting):
        """
        Sets a role to a user into a meeting or all meetings
        """ 
        status, resp = self.ucengine.request('POST',
            '/user/%s/roles?%s' % (uid,
            urllib.urlencode({
                'role': rolename,
                'location': meeting,
                'uid': self.uid,
                'sid': self.sid
            }))
        )
        if status != 200:
            raise UCError(status, resp)

    def delete_user_role(self, uid, rolename, meeting):
        """
        Deletes a role to a user into a meeting or all meetings
        """ 
        if meeting !="":
            status, resp = self.ucengine.request('DELETE',
                '/user/%s/roles/%s/%s?%s' % (uid, rolename, meeting, urllib.urlencode({'uid':self.uid, 'sid': self.sid})),
            )
        else:
            status, resp = self.ucengine.request('DELETE',
                '/user/%s/roles/%s?%s' % (uid, rolename, urllib.urlencode({'uid':self.uid, 'sid': self.sid}))
            )
        if status != 200:
            raise UCError(status, resp)
    
    def find_user_by_id(self, uid):
        """
        Search user by ID
        """
        return self.ucengine.request('GET',
            '/find/user?%s' %urllib.urlencode({
                'by_uid': uid,
                'uid': self.uid,
                'sid': self.sid}))

    def find_user_by_name(self, name):
        """
        Search user by name
        """
        return self.ucengine.request('GET',
                '/find/user?%s' % urllib.urlencode({
                    'by_name': name,
                    'uid': self.uid,
                    'sid': self.sid}))

    def delete(self, data):
        "Delete a user or a meeting"
        if issubclass(data.__class__, Client):
            status, resp = self.ucengine.request('DELETE',
                '/user/%s?%s' % (data.uid, urllib.urlencode({'uid':self.uid, 'sid': self.sid})))
            if not status == 20:
                raise UCError(status, resp)

    def user(self, uid):
        "Get one user"
        status, resp = self.ucengine.request('GET',
            '/user/%s?%s' % ( uid,
                urllib.urlencode({
                    'uid': self.uid,
                    'sid': self.sid
                })
            )
        )
        if not status == 200:
            raise UCError(status, resp)
        return resp['result']

    def users(self):
        "Get all users"
        status, resp = self.ucengine.request('GET',
            '/user?%s' % urllib.urlencode({
                'uid': self.uid,
                'sid': self.sid
        }))
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
        "Get a mmeting"
        status, resp = self.ucengine.request('GET',
            '/meeting/all/%s?%s' % (name, urllib.urlencode({
                'uid': self.uid,
                'sid': self.sid
        })))
        if status == 404:
            return None
        if not status == 200:
            raise UCError(status, resp)
        m = resp['result']
        return Meeting(name,
            start = m['start_date'],
            end = m['end_date'],
            metadata = m['metadata'])
