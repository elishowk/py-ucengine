import httplib
httplib.DEBUG=True
import urllib
import json
from datetime import datetime

from session import Session
from core import UCError

def safe_jsonify(data):
    """
    Safe jsonification
    """
    if isinstance(data, datetime):
        return data.isoformat()
    if isinstance(data, bool):
        return json.dumps(data)
    elif isinstance(data, dict):
        return dict(map(safe_jsonify, data.items()))
    elif isinstance(data, (list, tuple, set, frozenset)):
        return type(data)(map(safe_jsonify, data))
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

class UCEngine(object):
    "The Server"

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.users = []

    def request(self, method, path, body=None, expect=200):
        "ask something to the server"
        connection = httplib.HTTPConnection(self.host, self.port)
        #headers = {
            #"Content-type": "application/json",
            #"Accept": "application/json"
        #}
        if body != None:
            encodedbody = recursive_urlencode(safe_jsonify(body))
            connection.request(method, '/api/0.6%s' % path, encodedbody) #, headers)
        else:
            connection.request(method, '/api/0.6%s' % path)
        resp = connection.getresponse()
        raw = resp.read()
        try:
            response = json.loads(raw)
        except ValueError:
            response = None
        connection.close()
        #FIXME throw an error or return the response result
        return resp.status, response

    def connect(self, user, credential):
        status, resp = self.request('POST', '/presence/', {
            'name'               : user.name,
            'credential'         : credential,
            'metadata[nickname]' : user.name}
            )
        if status == 201:
            return Session(self, resp['result']['uid'], resp['result']['sid'])
        else:
            raise UCError(status, resp)

