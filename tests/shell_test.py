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

import os
import types
import re
import sys
import unittest

import rover.shell


class ShellTestCase(unittest.TestCase):
    def setUp(self):
        self.shell = rover.shell.Shell()

    def test_constructor(self):
        self.assertFalse(self.shell.verbose)
        self.assertFalse(self.shell.quiet)

    def test_return_codes(self):
        """
        test that return codes are returned and work correctly
        """
        returncode = self.shell.run_silent("true")
        self.assertEquals(returncode, 0)

        returncode = self.shell.run("true")
        self.assertEquals(returncode, 0)

        returncode, output = self.shell.tee_silent("true")
        self.assertEquals(returncode, 0)

        returncode, output = self.shell.tee("true")
        self.assertEquals(returncode, 0)


        returncode = self.shell.run_silent("false")
        self.assertEquals(returncode, 1)

        returncode = self.shell.run("false")
        self.assertEquals(returncode, 1)

        returncode, output = self.shell.tee_silent("false")
        self.assertEquals(returncode, 1)

        returncode, output = self.shell.tee("false")
        self.assertEquals(returncode, 1)

    def test_capture_tee_output(self):
        """
        test that the tee method captures output
        """
        returncode, out = self.shell.tee('echo "."')
        self.assertEquals(out, ['.'])
        self.assertEquals(returncode, 0)

    def test_capture_tee_silent_output(self):
        """
        test that the tee_silent method captures output
        """
        returncode, out = self.shell.tee_silent('echo "."')
        self.assertEquals(out, ['.'])
        self.assertEquals(returncode, 0)

    def test_execute(self):
        """
        make sure the verbose and return_out keyword args
        do what we expect them to do
        """
        returncode, out = self.shell.execute('echo "."', verbose=True
                , return_out=True)
        self.assertEquals(out, ['.'])
        self.assertEquals(returncode, 0)

        returncode = self.shell.execute('echo "."', verbose=True
                , return_out=False)
        self.assertEquals(returncode, 0)

        returncode, out = self.shell.execute('echo "."', verbose=False
                , return_out=True)
        self.assertEquals(out, ['.'])
        self.assertEquals(returncode, 0)

        returncode = self.shell.execute('echo "."', verbose=False
                , return_out=False)
        self.assertEquals(returncode, 0)

    def test_testmode(self):
        """
        make sure test_mode=True doesn't execute the command
        """
        returncode, out = self.shell.execute('echo "."', verbose=True
                , return_out=True, test_mode=True)
        self.assertEquals(out, [])
        self.assertEquals(returncode, 0)

    def test_push_pop_dir(self):
        """Pushing and popping a directory works as expected

        Depends on not being in the root directory"""
        pwd = os.path.abspath(os.getcwd())
        one_level_down, topdir = os.path.split(pwd)

        self.shell.push_dir('..')
        self.assertEqual(one_level_down, os.path.abspath(os.getcwd()))

        self.shell.pop_dir()
        self.assertEqual(pwd, os.path.abspath(os.getcwd()))



if __name__ == '__main__':
    unittest.main()

