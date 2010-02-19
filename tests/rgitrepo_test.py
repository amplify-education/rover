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

from rover.backends import rgitrepo
from mock_shell import MockShell


class GitConnectionTest(unittest.TestCase):
    def setUp(self):
        self.conn = rgitrepo.GitConnection('wgen-github'
                , 'git://github.com/wgen/')

    def test_git_connection_init(self):
        self.assertEqual('wgen-github', self.conn.name)
        self.assertEqual('git://github.com/wgen/', self.conn.uri)

    def test_get_rover_items(self):
        items = self.conn.get_rover_items(['rover.git'
                , 'master', 'wgen-github'])
        self.assertEquals(1, len(items))
        repo = items[0]
        self.assertEquals('wgen-github', repo.connection)
        self.assertEquals('git://github.com/wgen/', repo.uri)
        self.assertEquals('rover.git', repo.repository)
        self.assertEquals('master', repo.treeish)


class GitRepoTest(unittest.TestCase):
    def test_git_repo_init(self):
        item = rgitrepo.GitRepo('wgen-github', 'git://github.com/wgen/'
                , 'rover.git', 'master')

        self.assertEquals('wgen-github', item.connection)
        self.assertEquals('git://github.com/wgen/', item.uri)
        self.assertEquals('rover.git', item.repository)
        self.assertEquals('master', item.treeish)


class GitItemCheckoutTest(unittest.TestCase):
    def setUp(self):
        self.sh = MockShell()
        self.item = rgitrepo.GitRepo('wgen-github', 'git://github.com/wgen/'
                , 'rover.git', 'master')

    def test_git_checkout_new_repo(self):
        self.item.checkout(self.sh, 'dest', '')

        #self.assertEquals(2, len(self.sh.history))
        print "history = <%s>" % str(self.sh.history)

        output1 = ['git', 'clone'
                , 'git://github.com/wgen/rover.git'
                , 'dest/rover']
        history1 = self.sh.history[1]
        self.assertEquals(output1, history1)

        output2 = ['git', 'checkout', 'master']
        history2 = self.sh.history[2]
        self.assertEquals(output2, history2)

    def test_git_checkout_pull(self):
        self.sh.undeflow_error = True
        self.sh.seed_result(1)
        self.item.checkout(self.sh, 'dest', '')

        print "history = %s" % str(self.sh.history)

        expectedChdir = 'push_dir(dest/rover)'
        expectedCheckout = ['git', 'checkout', 'master']
        expectedPull = ['git', 'pull']
        self.assertEquals(expectedChdir, self.sh.history[1])
        self.assertEquals(expectedCheckout, self.sh.history[2])
        self.assertEquals(expectedPull, self.sh.history[3])

