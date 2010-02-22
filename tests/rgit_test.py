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
    def test_git_syntax_init_url(self):
        """
        Check to make sure data using a URL encoded string works
        """
        item = rgit.GitItem('git://github.com/wgen/foss/rover.git', 'master')

        self.assertEquals(item.repository, 'git://github.com/wgen/foss/rover.git')
        self.assertEquals(item.refspec, 'master')
        self.assertEquals(item.repo_path, 'wgen/foss')
        self.assertEquals(item.repo_name, 'rover.git')

    def test_git_syntax_init_ssh(self):
        """
        Check to make sure dating using an SSH encoded string works
        """
        item = rgit.GitItem('git@github.com:wgen/foss/rover.git', 'master')

        self.assertEquals(item.repository, 'git@github.com:wgen/foss/rover.git')
        self.assertEquals(item.refspec, 'master')
        self.assertEquals(item.repo_path, 'wgen/foss')
        self.assertEquals(item.repo_name, 'rover')

class GitItemCheckoutTest(unittest.TestCase):
    def setUp(self):
        self.sh = MockShell()
        self.item = rgit.GitItem('git://github.com/wgen/rover.git', 'master')

    # FIXME: This ONLY checks branch checkouts! Currently, no way of checking
    #   for tag or checkouts, although this is hard to test offline
    def test_git_checkout(self):
        # Check the number of commands run
        #   git clone ...
        #   git checkout ...
        #
        self.item.checkout(self.sh, 'dest', '', verbose=True, test_mode=True)
        self.assertEquals(2, len(self.sh.history))

        # Clone command, just parsing cmdline runs
        output0 = ['git clone', '-n', 'git://github.com/wgen/rover.git']
        history0 = self.sh.history[0]
        self.assertEquals(output0, history0)

        # Checkout the branch from the previous clone
        output1 = ['git checkout', '-f',  'master']
        history1 = self.sh.history[1]
        self.assertEquals(output1, history1)

    def test_git_exclude(self):
        self.assertRaises(Exception, self.item.exclude, "rover/backends")

unittest.main()
