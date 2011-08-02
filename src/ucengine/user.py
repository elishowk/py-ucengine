__author__ = "mathieu@garambrogne.net"

from gevent import monkey
monkey.patch_all()

import urllib

class User(object):
    "A user"
    def __init__(self, name, credential=None, uid=None, auth=None, metadata=None):
        self.name = name
        self.credential = credential
        self.uid = uid
        self.auth = auth
        self.metadata = {'nickname' : name}
        if metadata:
            self.metadata.update(metadata)

    def __repr__(self):
        return "<User name:%s>" % self.name
