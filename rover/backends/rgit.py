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
import rover.shell
import subprocess
import types
from distutils import version

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
        result = re.match("^(?:rsync|ssh|git|http|https)://(?:.*?)/(.*)(?:\.git)?$", repository)

        # If its not one of the above, it has to be SSH as follows
        if result is None:
            result = re.match("^(?:.*?@?).*:(.*?)(?:\.git)?$", repository)

        # If result is still none, we weren't able to match anything...
        if result is None:
            raise Exception("malformed git connection string `%s'; please see `git clone --help' for supported connection strings." % repository)

        # Separate repo and path
        self.repo_path, self.repo_name = os.path.split( result.groups()[0] )

        # Check for "excludes", because they're not allowed in git
        if ' !' in repository:
            raise Exception("excludes are not allowed in git: %s" % repository)

    def checkout(self, sh, checkout_dir, checkout_mode, verbose=True
            , test_mode=False):
        """Rover checkout = git clone; git checkout

        sh => a shell through which rover should make system calls"""

        # When checking out in git, it will take the last name in the connection
        #   string, and then extra it to $CWD/<name>.  Because we might want this
        #   to behave otherwise, i.e.:
        #
        #       git://github.com/WgenAdmin/rover => WgenAdmin/rover
        #
        #   ...we'll implement a "preserve directory structure" option.  For now,
        #   we always assume its true.  However, in the future, we'll have this
        #   as either a config or command line option.
        #
        preserve_dirs = True
        if preserve_dirs:
            cwd = os.path.join(checkout_dir, self.repo_path)
        else:
            cwd = checkout_dir

        git_dir = os.path.join(cwd,self.repo_name)

        if not os.path.exists( os.path.join(cwd, self.repo_name, '.git') ):
            cmd = ['git clone']
            cmd.append('-n')
            if not verbose:
                cmd.append('-q')
            cmd.append(self.repository)

            if not test_mode and not os.path.exists(cwd):
                os.makedirs(cwd)

            sh.execute(cmd, cwd=cwd, verbose=verbose,test_mode=test_mode)
        else:
            # under clean mode, reset local changes
            if checkout_mode == 'clean':
                # First, reset to our latest commit; this can be VERY dangerous
                #   if you have uncommitted changes in your tree!
                sh.execute("git reset --hard", verbose=verbose, test_mode=test_mode)

                # Then get rid of any lingering local changes (i.e., untracked)
                #   This is incredibly dangerous if you're using rover in a
                #   development environment; make sure you've committed changes!
                sh.execute("git clean -fd", verbose=verbose, test_mode=test_mode)

            # Finally, fetch the changes... we'll do a checkout later, because
            #   we have to treat remote branches, local branches, and tags, in
            #   special ways.
            cmd = ['git fetch']
            if not verbose:
                cmd.append('-q')

            sh.execute(cmd, cwd=git_dir, verbose=verbose, test_mode=test_mode)

        # We need to get git version information because of several changes in
        #   the CLI that began in in 1.6.6.
        stdoutput, stderror = subprocess.Popen("git --version", shell=True, stdout=subprocess.PIPE).communicate()
        match = re.match("^git version (\d+(?:\.\d+)+)$", stdoutput)

        if not match:
            print stderror
            raise Exception("`git --version' ended with return code %d." % proc.returncode)

        git_version = version.LooseVersion(match.group(1))
        cmd = ['git checkout']
        if not verbose:
            cmd.append('-q')

        # This can happen with certain untracked files; since we don't want to
        #   fail, we'll force new files to be updated, even with local mods
        cmd.append("-f")

        # As of 1.6.6, we can now use a much easier method of checking out
        #   branches AND tags! Basically, it treats it as if it were a local
        #   branch, but will automatically fetch and track it if not
        #
        if git_version >= version.LooseVersion("1.6.6") or \
           self.find_local_branch(self.refspec, git_dir, sh):
            cmd.append(self.refspec)
        # Is it remote?
        elif self.find_remote_branch(self.refspec, git_dir, sh):
            cmd.append("--track -b %s origin/%s" % (self.refspec,self.refspec))
        # Is it a tag?
        elif self.find_tag(self.refspec, git_dir, sh):
            cmd.append("--track -b %s %s" % (self.refspec, self.refspec))
        # Option D: None of the above
        else:
            raise Exception("branch '%s' does not exist for repository '%s'" % (self.refspec,self.repository))

        sh.execute(cmd, cwd=git_dir, verbose=verbose, test_mode=test_mode)

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
        raise Exception("excludes are not allowed in git: %s" % self.repository)
        pass

    def expand(self):
        """
        return list of rover items
        """
        return [self]

    def narrow(self, path):
        return GitItem(path, self.revision)

    def find_tag(self, refspec, directory, sh):
        return self.__ref_parse('refs/tags/%s' % refspec, directory, sh)

    def find_local_branch(self, refspec, directory, sh):
        return self.__ref_parse('refs/heads/%s' % refspec, directory, sh)

    def find_remote_branch(self, refspec, directory, sh):
        return self.__ref_parse('refs/remotes/origin/%s' % refspec, directory, sh)

    def __ref_parse(self, refpath, directory, sh):
        """
        will parse through the git repository, checking for the selected refpath,
        and then return True if it exists or False otherwise
        """
        cmd = "git for-each-ref '%s'" % refpath
        ret, output = sh.tee_silent(cmd, cwd=directory)

        if ret:
            raise Exception("Error while executing '%s': %s" % (cmd, output))
        return len(output) != 0

    def __repr__(self):
        return ''
