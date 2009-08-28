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
import re
import shutil
import types

from rover import util
from rover.backends.rover_interface import RoverItemFactory, RoverItem

class GITFactory(RoverItemFactory):
    def __init__(self):
        pass

    def get_rover_items(self, config_line):
        module, revision = config_line[:2]
        out = [GITItem(module, revision)]
        return out

    def _is_alias(self, module):
        pass

    def _handle_excludes(self, modules):
        """
        Not used for git; git is all or none when checking
        out a repository.  Files cannot be cherrypicked!
        """
        pass

    def _get_modules_content(self):
        pass

    def _get_aliases(self):
        pass

class GITItem(RoverItem):
    def __init__(self, module, revision):
        self.module = module
        self.revision = revision
        self.repo_name, ignore = os.path.splitext( os.path.basename(module) )

    def checkout(self, checkout_dir, checkout_mode, verbose=True, test_mode=False):
        cwd = os.path.join(checkout_dir, self.repo_name)

        if not os.path.exists( os.path.join(cwd, '.git') ):
            cmd = ['git']
            if not verbose:
                cmd.append('-q')
            cmd.append('clone')
            cmd.append(self.module)

            if not test_mode and not os.path.exists(cwd):
                os.makedirs(cwd)

            util.execute(cmd, cwd=cwd, verbose=verbose,test_mode=test_mode)

        cmd = ['git']

        if not verbose:
            cmd.append('-q')

        cmd.append('checkout')
        cmd.append(self.revision)

        # If checkout_mode is clean, throw away local changes
        if checkout_mode == 'clean':
            cmd.append('-f')

        util.execute(cmd, cwd=cwd, verbose=verbose, test_mode=test_mode)

    def get_path(self):
        """
        return the path to the "module"; however, there is no module here,
        only the git checkout directory.  Therefor... check it all out into
        the working directory, until we can add a config option to specify
        otherwise.
        """
        return self.repo_name

    def exclude(self, path):
        # Does nothing, because you can't ignore
        # paths/files/whatever in git
        pass

    def expand(self):
        """
        return list of rover items
        """
        return [self]

    def narrow(self, path):
        return GITItem(path, self.revision)

    def __repr__(self):
        return ''
