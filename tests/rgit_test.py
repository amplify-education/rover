import unittest

from rover.backends import rgit
from mock_shell import MockShell


class GitFactoryTest(unittest.TestCase):
    def setUp(self):
        self.fact = rgit.GitFactory()

    def test_get_rover_items(self):
        items = self.fact.get_rover_items(['git://github.com/wgen/rover.git'
                , 'master', 'git'])
        self.assertEquals(1, len(items))


class GitItemInitTest(unittest.TestCase):
    def test_git_syntax_init(self):
        item = rgit.GitItem('git://github.com/wgen/rover.git', 'master')

        self.assertEquals('git://github.com/wgen/rover.git', item.repository)
        self.assertEquals('master', item.refspec)
        # not sure what the repo path and repo name values are supposed to be
        self.assertEquals('git://github.com/', item.repo_path)
        self.assertEquals('/wgen/rover.git/', item.repo_name)

class GitItemCheckoutTest(unittest.TestCase):
    def setUp(self):
        self.sh = MockShell()
        self.item = rgit.GitItem('git://github.com/wgen/rover.git', 'master')

    def test_git_checkout(self):
        self.item.checkout(self.sh, 'dest', '')

        self.assertEquals(2, len(self.sh.history))

        output0 = ['git', 'clone'
                , 'git://github.com/wgen/rover.git'
                , 'dest/wgen/rover.git']
        history0 = self.sh.history[0]
        self.assertEquals(len(output0), len(history0))
        self.assertEquals(output0, history0)

        output1 = ['git', 'checkout', 'master']
        history1 = self.sh.history[1]
        self.assertEquals(len(output1), len(history1))
        self.assertEquals(output1, history1)

