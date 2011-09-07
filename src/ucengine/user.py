__author__ = "mathieu@garambrogne.net"

class Client(object):
    "A simple client"


    def __init__(self, name, uid=None, credential=None, auth=None, metadata=None):
        self.name = name
        self.metadata = metadata
        self.credential = credential
        self.uid = uid
        self.auth = auth


class User(Client):
    "A user"
    def __init__(self, name, uid=None, credential=None, auth=None, metadata=None):
        if metadata is None:
            metadata = {}
        elif metadata.has_key('nickname'):
            metadata['nickname'] = name
        Client.__init__(self, name, uid, credential, auth, metadata)

    def __repr__(self):
        return "<User name:%s>" % self.name


