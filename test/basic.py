import sys
import unittest
import os.path
sys.path.insert(1, os.path.abspath('src'))
from ucengine import UCEngine, User, UCError, Meeting
from uuid import uuid4

#import httplib
#httplib.HTTPConnection.debuglevel = 1

class TestBasic(unittest.TestCase):

    def setUp(self):
        #self.credentials = open("credentials.txt", "r")
        self.uce = UCEngine('http://localhost', 5280)
        self.participant = User('test', credential="test", auth="password", metadata={"somekey": "somevalue"})
        owner = User('admin')
        self.admin_session  = self.uce.connect(owner, 'admin', "password")
        self.admin_session.save(self.participant)
        self.session = self.uce.connect(self.participant, 'test', "password").loop()

    def tearDown(self):
        """
        Close sessions and delete the 'test' user
        """
        self.session.close()
        self.admin_session.delete(self.participant)
        self.admin_session.close()

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
        users =  self.admin_session.users()
        v = self.admin_session.user(users[0].uid)
        self.assertTrue(None != v)
    
    def test_create_and_delete_user(self):
        """
        creates, finds, and deletes a user
        """
        name = uuid4()
        bob = User(name, credential="pwd", auth="password")
        bob.metadata = {}
        bob.metadata['nickname'] = "Robert les grandes oreilles"
        bob.metadata['adict'] = { 'one': 2 }
        bob.metadata['alist'] = "'testing','data','encoding'"
        self.admin_session.save(bob)
        status, result = self.admin_session.find_user_by_name(name)
        self.assertEqual(status, 200)
        self.assertTrue(('metadata' in result['result']))
        self.assertEqual(result['result']['metadata']['alist'], "'testing','data','encoding'")
        self.assertTrue("adict" not in result['result']['metadata'])
        bob = User(name, credential="pwd", auth="password", uid=result['result']['uid'])
        self.admin_session.delete(bob)
        status, result = self.admin_session.find_user_by_name(name)
        self.assertEqual(status, 404)

    def test_modify_user(self):
        """
        Modify user's metadata multiple times and save
        """
        bob = User('Bob', credential="pwd", auth="password")
        bob.metadata = {}
        bob.metadata['nickname'] = "Robert les grandes oreilles"
        bob.metadata['adict'] = { 'one': 2 }
        bob.metadata['alist'] = "'testing','data','encoding'"
        self.admin_session.save(bob)
        status, result = self.admin_session.find_user_by_name('Bob')
        self.assertTrue(('metadata' in result['result']))
        self.assertEqual(result['result']['metadata']['alist'], "'testing','data','encoding'")
        self.assertEqual(result[u'result'][u'metadata'][u'nickname'], "Robert les grandes oreilles")
        # modifies only a metadata
        bob2 = User('Bob', metadata={'alist':""}, credential="pwd")
        self.admin_session.save(bob2)
        status, result = self.admin_session.find_user_by_name('Bob')
        self.assertEqual(result['result']['metadata']['alist'], "")
        # modifies NOTHING
        bob3 = User('Bob', credential="pwd")
        self.admin_session.save(bob3)
        status, result = self.admin_session.find_user_by_name('Bob')
        self.assertEqual(result['result']['metadata']['alist'], "")

    def test_modify_user_role(self):
        """
        Adds then deletes a role to an existing user
        Really basic since we cannot list user's roles with the current API
        """
        users = self.admin_session.users()
        self.admin_session.add_user_role( users[0].uid, "participant", "")
        self.admin_session.delete_user_role( users[0].uid, "participant", "")

    def test_meeting(self):
        """
        Creates then Gets a meeting called 'demo'
        """
        self.admin_session.save(Meeting("demo", {"toto": "toto"}))
        meeting = self.session.meeting('demo')
        self.assertTrue(None != meeting)

if __name__ == '__main__':
    unittest.main()
