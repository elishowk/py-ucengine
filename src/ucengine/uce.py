import requests
import json
from session import Session
from core import UCError

VERSION = "0.6"


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
        if method == "GET":
            resp = requests.get(self._get_url(path), params=params, data=body, headers=headers)
        if method == "POST":
            resp = requests.post(self._get_url(path), params=params, data=body, headers=headers)
        if method == "PUT":
            resp = requests.put(self._get_url(path), params=params, data=body, headers=headers)
        if method == "DELETE":
            resp = requests.delete(self._get_url(path), params=params, data=body, headers=headers)
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

