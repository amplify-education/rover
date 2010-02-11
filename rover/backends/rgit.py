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
    def __init__(self, repository, refspec):
        self.repository = repository
        self.refspec = refspec

        # Detect the two forms as per git's documentation
        # TODO: Add support for local repos
        result = re.match("^(rsync|ssh|git|http|https|file)://(?:.*?)/(.*)(?:\.git)?$", repository)

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

        # Path doesn't exist, so we need to clone the repo
        if not os.path.exists( os.path.join(cwd, self.repo_name, '.git') ):
            cmd = ['git clone']

            # Don't do a checkout after the clone
            cmd.append('-n')
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

            cmd.append('%s:origin/%s' % (self.refspec, self.refspec))

            util.execute(cmd, cwd=git_dir, verbose=verbose, test_mode=test_mode)

        # Make sure the branch exists; we'll need the actual
        #   relative path to the branch; i.e., remotes/origin/a_branch
        #
        # Check to see if the local branch exists
        cmd = 'git branch -l --no-color'
        ret, output = util.execute(cmd, cwd=git_dir, test_mode=test_mode)

        new_branch = False
        refspec = self.refspec

        # Check to see if the local branch exists
        if not re.match("\W+%s$" % self.refspec, output):
            cmd = 'git branch -r --no-color'
            ret, output = util.execute(cmd, cwd=git_dir, test_mode=test_mode)

            # Make sure the remote version exists, too!
            # TODO: See if there's any git API functions to do this
            if not re.match("\W+origin/%s$" % self.refspec, output):
                raise Exception("branch '%s' could not be found in the repository" % self.refspec)

            new_branch = True
            refspec = "origin/%s" % refspec

        # Check out the branch in question!
        cmd = ['git checkout']

        if not verbose:
            cmd.append('-q')

        # If checkout_mode is clean, throw away local changes
        if checkout_mode == 'clean':
            cmd.append('-f')

        # Track this branch locally
        if new_branch:
            cmd.append('-t')

        cmd.append(refspec)

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
        return GITItem(path, self.revision)

    def __repr__(self):
        return ''
