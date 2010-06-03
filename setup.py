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

from ez_setup import use_setuptools
use_setuptools()

import os
import re
import subprocess

from setuptools import setup, find_packages
from textwrap import dedent


def make_version():
    '''Write the version (as identified by git) to a file called version.py

    This version.py module will then be used to report the version.'''
    src_dir = os.path.dirname(__file__)
    version_path = os.path.join(src_dir, 'rover', 'version.py')
    git_describe = "'`git describe --match v*`'"
    cmd = "echo \"VERSION = %s\" > %s" % (git_describe, version_path)
    subprocess.call(cmd, shell=True)

def major_version(version):
    '''Parse the major version from the version string'''
    match = re.match("^v(\d+\.\d+)", version)
    return match.group(1)

make_version()

import rover.version

setup(
        name = "Rover",
        version = major_version(rover.version.VERSION),
        description="Automatically retrieves projects from various VCS",
        long_description = dedent("""\
                Rover simplifies the task of creating a project that draws
                from various different forms of version control systems (VCS).
                Currently, Rover supports cvs and svn, but has future plans
                for git.
        """),

        author = "Wireless Generation",
        author_email = "github@wgen.net",
        url = "http://github.com/wgen/rover",
        license = "MIT",
        keywords = "cvs svn git rover checkout vcs",



        packages = find_packages(exclude='tests'),
        setup_requires = [
            'setuptools-git >= 0.3',
        ],
        scripts = [
            'scripts/rover',
        ],
      )
