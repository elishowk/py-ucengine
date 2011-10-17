import sys
#import time
import unittest
import os.path
sys.path.insert(1, os.path.abspath('src'))
from ucengine import UCEngine, User, UCError

import httplib
httplib.HTTPConnection.debuglevel = 1

class TestBasic(unittest.TestCase):

    def setUp(self):
        self.uce = UCEngine('localhost', 5280)
        self.victor = User('participant')
        self.session = self.uce.connect(self.victor, 'pwd').loop()

    def tearDown(self):
        self.session.close()

    def test_presence(self):
        self.assertTrue(None != self.session.sid)

    def test_bad_presence(self):
        """
        Connects with bad credentials
        """
        thierry = User('thierry')
        try:
            self.uce.connect(thierry, '****')
        except UCError as e:
            self.assertEquals(404, e.code)
        else:
            self.assertTrue(False)

    def test_time(self):
        """
        Get server time
        """
        stime = self.session.time()
        self.assertEquals(int, type(stime))

    def test_get_user(self):
        """
        Get user by UID
        """
        owner = User('root')
        root_session = self.uce.connect(owner, 'root')
        users =  root_session.users()
        print users[0].uid
        v = root_session.user(users[0].uid)
        self.assertTrue(None != v)

    def test_modify_user(self):
        """
        Modifies some user metadata
        """
        owner = User('root')
        root_session = self.uce.connect(owner, 'root')
        bob = User('Bob', credential="pwd", auth="password")
        bob.metadata = {}
        bob.metadata['nickname'] = "Robert les grandes oreilles"
        bob.metadata['adict'] = { 'one': 2 }
        bob.metadata['alist'] = "'testing','data','encoding'"
        root_session.save(bob)
        status, result = root_session.find_user_by_name('Bob')
        self.assertTrue(('metadata' in result['result']))
        self.assertEqual(result['result']['metadata']['alist'], "'testing','data','encoding'")
        # modifies only a metadata
        bob2 = User('Bob', metadata={'alist':""}, credential="pwd")
        root_session.save(bob2)
        status, result = root_session.find_user_by_name('Bob')
        self.assertEqual(result['result']['metadata']['nickname'], "Robert les grandes oreilles")
        self.assertEqual(result['result']['metadata']['alist'], "")
        # modifies NOTHING
        bob3 = User('Bob', credential="pwd")
        root_session.save(bob3)
        status, result = root_session.find_user_by_name('Bob')
        self.assertEqual(result['result']['metadata']['nickname'], "Robert les grandes oreilles")
        self.assertEqual(result['result']['metadata']['alist'], "")

    def test_delete_user(self):
        """
        Modifies some user metadata
        """
        owner = User('root')
        root_session = self.uce.connect(owner, 'root')
        status, result = root_session.find_user_by_name("Bob")
        self.assertEqual(status, 200)
        bob = User("Bob", credential = "pwd", uid=result['result']['uid'])
        root_session.delete(bob)
        status, result = root_session.find_user_by_name("Bob")
        self.assertEqual(status, 404)

    def test_modify_user_role(self):
        """
        Adds then deletes a role to an existing user
        Really basic since we cannot list user's roles with the current API
        """
        owner = User('root')
        root_session = self.uce.connect(owner, 'root')
        users = root_session.users()
        root_session.add_user_role( users[3].uid, "participant", "")
        root_session.delete_user_role( users[3].uid, "participant", "")

    def test_meeting(self):
        """
        Get a meeting called 'demo'
        """
        meeting = self.session.meeting('demo')
        self.assertTrue(None != meeting)

if __name__ == '__main__':
    unittest.main()
