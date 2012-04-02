import requests
import json
import urllib
from datetime import datetime
from session import Session
from core import UCError

VERSION = "0.6"

def safe_encode(data):
    """
    Safe dict transformations
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
    """
    Safe parameters encoding for user's metadata
    """
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

    def _get_url(self, path):
        """
        Utility
        """
        return "/".join(["%s:%s"%(self.host, self.port), "api", VERSION, path])

    def request(self, method, path, body=None, params=None, headers=None):
        """
        ask something to the server
        """
        if headers is None:
            headers = {
                "Content-type": "application/json",
                "Accept": "application/json"
            }
        if body is not None:
            body = json.dumps(body)
        if params is not None:
            params = recursive_urlencode(safe_encode(params))
        if method == "GET":
            resp = requests.get(self._get_url(path), params=params, data=body, headers=headers)
        if method == "POST":
            resp = requests.post(self._get_url(path), params=params, data=body, headers=headers)
        if method == "PUT":
            resp = requests.put(self._get_url(path), params=params, data=body, headers=headers)
        if method == "DELETE":
            resp = requests.delete(self._get_url(path), params=params, data=body, headers=headers)
        if resp.status_code==500:
            return resp.status_code, resp.text
        return resp.status_code, json.loads(resp.text)

    def connect(self, user, credential, auth="password"):
        status, resp = self.request('POST', 'presence', params={
            'name'              : user.name,
            'credential'        : credential,
            'auth'              : auth
        })
        if status == 201:
            return Session(self, resp['result']['uid'], resp['result']['sid'])
        else:
            raise UCError(status, resp)

