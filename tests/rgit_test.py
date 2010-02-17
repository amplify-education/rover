#
# Copyright (c) 2009 Wireless Generation, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

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
        """Not sure what all this does, but I'm assuming that current
        behavior is correct and writing the tests to match that."""
        item = rgit.GitItem('git://github.com/wgen/rover.git', 'master')

        self.assertEquals('git://github.com/wgen/rover.git', item.repository)
        self.assertEquals('master', item.refspec)
        # not sure what the repo path and repo name values are supposed to be
        self.assertEquals('', item.repo_path)
        self.assertEquals('git', item.repo_name)

class GitItemCheckoutTest(unittest.TestCase):
    def setUp(self):
        self.sh = MockShell()
        self.item = rgit.GitItem('git://github.com/wgen/rover.git', 'master')

    def test_git_checkout(self):
        self.item.checkout(self.sh, 'dest', '')

        self.assertEquals(2, len(self.sh.history))

        output0 = ['git', 'clone'
                , 'git://github.com/wgen/rover.git']
        history0 = self.sh.history[0]
        self.assertEquals(output0, history0)

        output1 = ['git checkout', 'master']
        history1 = self.sh.history[1]
        self.assertEquals(output1, history1)

