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

# template for rover.config package -- stores local configuration
# information for rover (eg the config directory)

import os

config_dir = os.path.abspath('.rover')

REPO_FILE_NAME = "REPOS"

class RepoInfo(object):
    """Structured data for a configured repo."""
    def __init__(self, repoline):
        print "repoline = '%s'" % repoline
        repoline = repoline.strip()
        if len(repoline) == 0:
            # blank line, fail
            raise Exception("Cannot initialize RepoInfo for blank line")
        elif repoline[0] == '#':
            # commented line, fail
            raise Exception("Cannot initialize RepoInfo for commented line")
        parts = repoline.split(',')

        self.name = parts[0].strip()
        self.vcs = parts[1].strip()
        self.uri = parts[2].strip()


def open_repofile(path):
    filename = os.path.join(path, REPO_FILE_NAME)
    return open(filename)

def parse_repos(repofile):
    """Get repos from an open file."""
    repos = []
    for line in repofile:
        line = line.strip()
        if len(line) == 0 or line[0] == '#':
            # blank or commented line, skip it
            continue
        repos.append(RepoInfo(line))
    return repos

