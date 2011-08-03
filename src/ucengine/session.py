import urllib

from core import Eventualy, unicode_urlencode, UCError
from user import UCUser
from meeting import Meeting

class Session(Eventualy):

    def __init__(self, uce, uid, sid):
        Eventualy.__init__(self)
        self.ucengine = uce
        self.uid = uid
        self.sid = sid

    def time(self):
        "What time is it"
        status, resp = self.ucengine.request('GET',
            '/time?%s' % urllib.urlencode({
                'uid': self.uid, 'sid': self.sid}))
        assert status == 200, UCError(status, resp)
        return resp['result']

    def infos(self):
        "Infos about the server"
        status, resp = self.ucengine.request('GET',
            '/infos?%s' % urllib.urlencode({
            'uid': self.uid, 'sid': self.sid}))
        assert status == 200, UCError(status, resp)
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
        if issubclass(data.__class__, UCUser):
            self._save_user(data)
        if issubclass(data.__class__, Meeting):
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
            unicode_urlencode(values))
            assert status == 200, UCError(status, resp)
        else:
            status, resp = self.ucengine.request('POST',
            '/meeting/all/',
            unicode_urlencode(values))
            assert status == 201, UCError(status, resp)

    def _save_user(self, user):
        """
        create or update a user after a find by name
        """
        values = user.__dict__

        if user.uid is None:
            status, resp = self.ucengine.request('GET',
                '/find/user/?%s' % urllib.urlencode({
                    'by_name': user.name,
                    'uid': self.uid,
                    'sid': self.sid}))
        else:
            status, resp = self.ucengine.request('GET',
                '/find/user/?%s' % urllib.urlencode({
                    'by_id': user.uid,
                    'uid': self.uid,
                    'sid': self.sid}))
        # user exists
        if status == 200:
            # merges user data
            uid = resp['result']['uid']
            resp['result'].update(values)
            resp['result']['uid'] = self.uid
            resp['result']['sid'] = self.sid
            status, resp = self.ucengine.request('PUT',
                '/user/%s' % uid,
                unicode_urlencode(resp['result'])
            )
            assert (status == 200), UCError(status, resp)
        elif status == 404:
            values['uid'] = self.uid
            values['sid'] = self.sid
            status, resp = self.ucengine.request('POST',
                '/user',
                unicode_urlencode(values)
            )
            assert (status == 201), UCError(status, resp)


    def delete(self, data):
        "Delete a user or a meeting"
        if issubclass(data.__class__, UCUser):
            status, resp = self.ucengine.request('DELETE',
                '/user/%s?%s' % (data.uid, urllib.urlencode({'uid':self.uid, 'sid': self.sid})))
            assert status == 200, UCError(status, resp)


    def users(self):
        "Get all users"
        status, resp = self.ucengine.request('GET',
            '/user?%s' % urllib.urlencode({
                'uid': self.uid,
                'sid': self.sid
        }))
        assert status == 200, UCError(status, resp)

        us = []
        for u in resp['result']:
            us.append(
                UCUser(u['name'],
                    metadata = u['metadata'],
                    uid = u['uid'])
            )
        return us
