__author__ = "mathieu@garambrogne.net"

import gevent


#FIXME one error per HTTP error : 400, 401, 404, 500
class UCError(Exception):
    "Standard error for ucengine server error"
    def __init__(self, code, value):
        self.code = code
        self.value = value

    def __str__(self):
        return "<UCError:%s %s>" % (self.code, self.value)


class Eventualy(object):
    "Dummy object implementing event loop"

    def __init__(self):
        self.callbacks = {}
        self.event_pid = None
        self.ucengine = None

    def callback(self, key, cback):
        "register a new callback"
        self.callbacks[key] = cback
        return self

    def event_loop(self, url, params):
        "launch the backround event listening"
        def _listen():
            if 'start' not in params:
                params['start'] = 0
            start = params['start']
            while True:
                status, resp = self.ucengine.request('GET',
                        "%s"%url, params=params)
                if status == 200:
                    for event in resp['result']:
                        start = event['datetime'] + 1
                        if event['type'] in self.callbacks:
                            gevent.spawn(self.callbacks[event['type']], event)
                        else:
                            pass
        self.event_pid = gevent.spawn(_listen)

    def event_stop(self):
        "stop the event loop"
        if self.event_pid is not None:
            self.event_pid.kill()

