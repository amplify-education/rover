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

class GitFactory(RoverItemFactory):
    def __init__(self):
        pass

    def get_rover_items(self, config_line):
        module, revision = config_line[:2]
        out = [GitItem(module, revision)]
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

class GitItem(RoverItem):
    def __init__(self, repository, refspec):
        self.repository = repository
        self.refspec = refspec

        # Detect the two forms as per git's documentation
        # TODO: Add support for local repos
        result = re.match("^(rsync|ssh|git|http|https)://(?:.*?)/(.*)(?:\.git)?$", repository)

        # If its not one of the above, it has to be SSH as follows
        if result is None:
            result = re.match("^(?:.*?@?).*:(.*?)(?:\.git)?$", repository)


        # If result is still none, we weren't able to match anything...
        if result is None:
            raise Exception("malformed git connection string `%s'; please see `man git-clone' for supported connection strings." % repository)

        # Separate repo and path
        self.repo_path, self.repo_name = os.path.split( result.groups()[0] )

        # Check for "excludes", because they're not allowed in git
        if ' !' in repository:
            raise Exception("excludes are not allowed in git: %s" % repository)

    def checkout(self, checkout_dir, checkout_mode, verbose=True, test_mode=False):
        # passing in preserve_dirs will be much more in depth; for now, assume its
        #   always true!
        preserve_dirs = True
        if preserve_dirs:
            cwd = os.path.join(checkout_dir, self.repo_path)
        else:
            cwd = checkout_dir

        git_dir = os.path.join(cwd,self.repo_name)

        if not os.path.exists( os.path.join(cwd, self.repo_name, '.git') ):
            cmd = ['git']
            cmd.append('clone')
            if not verbose:
                cmd.append('-q')
            cmd.append(self.repository)

            if not test_mode and not os.path.exists(cwd):
                os.makedirs(cwd)

            util.execute(cmd, cwd=cwd, verbose=verbose,test_mode=test_mode)

        else:
            # under clean mode, reset local changes
            if checkout_mode == 'clean':
                # First, reset to revision
                util.execute("git reset --hard", verbose=verbose, test_mode=test_mode)

                # Then get rid of any lingering local changes that
                #   will disrupt our pull
                util.execute("git clean -fd", verbose=verbose, test_mode=test_mode)

            # Finally, do the pull!
            cmd = ['git pull']
            if not verbose:
                cmd.append('-q')

            util.execute(cmd, cwd=git_dir, verbose=verbose, test_mode=test_mode)


        # Check out the branch in question!
        cmd = ['git checkout']

        if not verbose:
            cmd.append('-q')

        # If checkout_mode is clean, throw away local changes
        if checkout_mode == 'clean':
            cmd.append('-f')

        # Checkout the remote branch, always... we don't care about
        #   local changes.  There should be NO local branches!
        #
        # FIXME: This will not work with tags!!!
        #
        cmd.append("origin/%s" % self.refspec)

        util.execute(cmd, cwd=git_dir, verbose=verbose, test_mode=test_mode)

    def get_path(self):
        """
        return the path to the "repository"; however, there is no repository here,
        only the git checkout directory.  Therefor... check it all out into
        the working directory, until we can add a config option to specify
        otherwise.
        """
        return self.repo_name

    def exclude(self, path):
        # git does not support excludes
        raise Exception("excludes are not allowed in git: %s" % repository)
        pass

    def expand(self):
        """
        return list of rover items
        """
        return [self]

    def narrow(self, path):
        return GitItem(path, self.revision)

    def __repr__(self):
        return ''
