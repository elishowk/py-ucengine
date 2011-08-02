__author__ = "mathieu@garambrogne.net"

from gevent import monkey
monkey.patch_all()


class UCUser(object):
    "A user"

    def __init__(self, name, credential=None, uid=None, auth=None, metadata=None):

        self.name = name
        self.credential = credential
        self.uid = uid
        self.auth = auth
        self.metadata = {'nickname' : name}
        if isinstance(metadata, dict):
            self.metadata.update(metadata)

    def __repr__(self):
        return "<UCUser name:%s>" % self.name
