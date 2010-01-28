import unittest

from rover.backends import rgit


class GitFactoryTest(unittest.TestCase):
    def setUp(self):
        self.fact = rgit.GitFactory()

    def test_get_rover_items(self):
        items = self.fact.get_rover_items(['git://github.com/wgen/rover.git'
                , 'master', 'git'])
        self.assertEquals(1, len(items))


class GitItemTest(unittest.TestCase):
    def test_git_syntax_init(self):
        item = rgit.GitItem('git://github.com/wgen/rover.git', 'master')

        self.assertEquals('git://github.com/wgen/rover.git', item.repository)
        self.assertEquals('master', item.refspec)
        # not sure what the repo path and repo name values are supposed to be
        self.assertEquals('git://github.com/', item.repo_path)
        self.assertEquals('/wgen/rover.git/', item.repo_name)

