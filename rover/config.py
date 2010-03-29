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
from StringIO import StringIO

config_dir = os.path.abspath('.rover')

REPO_FILE_NAME = "REPOS"


def find_config(config_name):
    """Given a config name, turn that into an existing config file

    return an absolute path to the existing config file
    raise an exception if the file is not found
    """
    # First check for a direct reference to actual filename
    path = os.path.abspath(config_name)
    if os.path.exists(path) and os.path.isfile(path):
        return path
    # Check for a direct reference to filename w/o '.csv'
    path = '%s.csv' % path
    if os.path.exists(path) and os.path.isfile(path):
        return path

    # Check for the file in the default config dir w/ '.csv' ext
    path = os.path.abspath(os.path.join(config_dir, config_name))
    if os.path.exists(path) and os.path.isfile(path):
        return path
    # Check for the full in the default dir after appending .csv
    path = '%s.csv' % path
    if os.path.exists(path) and os.path.isfile(path):
        return path

    # Check in ROVER_PATH last
    # This seems like a questionable model, may want to drop it
    if 'ROVER_PATH' in os.environ.keys():
        path = os.path.abspath(os.path.join(os.environ['ROVER_PATH'],
            config_name))
        if os.path.exists(path) and os.path.isfile(path):
            return path
        # Check for ROVER_PATH w/ .csv extension
        path = '%s.csv' % path
        if os.path.exists(path) and os.path.isfile(path):
            return path

    return None


def find_repos(config_filepath):
    """If given a path to a config file, finds a corresponding repofile
    """
    if not config_filepath or not os.path.exists(config_filepath):
        return None
    dir, file = os.path.split(config_filepath)
    repo_filename = os.path.join(dir, REPO_FILE_NAME)
    if not os.path.exists(repo_filename):
        return None
    return repo_filename


class RepoInfo(object):
    """Structured data for a configured repo."""
    def __init__(self, repoline):
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


def open_repofile(repo_filename):
    """Open the repofile, return an empty StringIO if it doesn't exist
    """
    if not (repo_filename and os.path.exists(repo_filename)):
        return StringIO('')
    return open(repo_filename)


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

