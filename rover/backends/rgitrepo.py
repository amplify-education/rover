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
import types

from rover.backends.rover_interface import RoverItemFactory, RoverItem


class GitConnection(RoverItemFactory):
    def __init__(self, name, uri):
        self.name = name
        self.uri = uri
        # possibly add assertions on uri format here.
        # not sure if it's needed though.

    def get_rover_items(self, config_line):
        repo, branch = config_line[:2]
        out = [GitRepo(self.name, self.uri, repo, branch)]
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


class GitRepo(RoverItem):
    def __init__(self, conn, uri, repo, treeish):
        self.connection = conn
        self.uri = uri
        self.repository = repo
        self.treeish = treeish

        # Check for "excludes", because they're not allowed in git
        if ' !' in repo:
            raise Exception("excludes are not allowed in git: %s" % repo)


    def checkout(self, sh, checkout_dir, checkout_mode, verbose=True
            , test_mode=False):
        """Rover checkout = git clone

        sh => a shell through which rover should make system calls"""
        # passing in preserve_dirs will be much more in depth;
        # for now, assume its always true!

        # remove the .git extension from the checkout_dir
        repo, dot_git = os.path.splitext(self.repository)
        if dot_git.lower() != '.git':
            # extension isn't .git, use the original repo
            repo = self.repository

        # set checkout destination and git dir
        dest = os.path.join(checkout_dir, repo)
        git_dir = os.path.join(dest, '.git')

        # join the repo
        full_repo = os.path.join(self.uri, self.repository)

        if sh.exists(git_dir):
            self._pull(sh, full_repo, dest)
        else:
            self._clone(sh, full_repo, dest, verbose=verbose)

    def _clone(self, sh, full_repo, dest, verbose=True, test_mode=False):
        clone = ['git', 'clone']
        if not verbose:
            clone.append('-q')
        clone.append(full_repo)
        clone.append(dest)

        # if not test_mode and not os.path.exists(cwd):
        #    os.makedirs(cwd)
        sh.execute(clone, verbose=verbose, test_mode=test_mode)

        # Check out the branch in question!
        # os.chdir(dest) TODO: convert this to be done by sh

        co = ['git', 'checkout']
        if not verbose:
            co.append('-q')
        co.append(self.treeish)
        sh.execute(co, verbose=verbose, test_mode=test_mode)

    def _pull(self, sh, full_repo, dest):
        """For an existing repo, do a git pull
        """
        # get into the right directory first
        sh.push_dir(dest)

        # checkout the right branch
        co = ['git', 'checkout', self.treeish]
        sh.execute(co)

        # finally, do the pull
        pull = ['git', 'pull']
        sh.execute(pull)

        sh.pop_dir()


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
