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
import rover.config

from StringIO import StringIO


class RepoInfoTest(unittest.TestCase):
    def test_github_repo_info(self):
        repo = rover.config.RepoInfo("github, git, git://github.com/")
        self.assertEqual("github", repo.name)
        self.assertEqual("git", repo.vcs)
        self.assertEqual("git://github.com/", repo.uri)

    def test_repo_info_for_comment(self):
        "RepoInfo() for a commented line fails"
        try:
            repo = rover.config.RepoInfo("  # comment line")
        except Exception, x:
            self.assertEqual('Cannot initialize RepoInfo for commented line' \
                    , str(x))
        else:
            self.fail("Commented repo line should have thrown an exception")

    def test_repo_info_on_blank(self):
        "RepoInfo() for a blank line fails"
        try:
            repo = rover.config.RepoInfo("  ")
        except Exception, x:
            self.assertEqual('Cannot initialize RepoInfo for blank line' \
                    , str(x))
        else:
            self.fail("Blank repo line should have thrown an exception")


BASIC_REPOS_TEST_CASE = """
github, git, git://github.com/
  # verification comment
tigris, svn, svn://tigris.com/
sourceforge, cvs, :pserver:cvs.sourceforge.net:2401/cvsroot/
"""

class ParseRepoTest(unittest.TestCase):
    def test_empty_repofile(self):
        repos = rover.config.parse_repos(StringIO(''))
        self.assertEqual([], repos)

    def test_basic_parse_repos(self):
        repos = rover.config.parse_repos(StringIO(BASIC_REPOS_TEST_CASE))

        self.assertEqual(3, len(repos))

        self.assertEqual('github', repos[0].name)
        self.assertEqual('git', repos[0].vcs)
        self.assertEqual('git://github.com/', repos[0].uri)

        self.assertEqual('svn://tigris.com/', repos[1].uri)
        self.assertEqual('sourceforge', repos[2].name)

