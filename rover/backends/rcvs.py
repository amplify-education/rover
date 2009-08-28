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

class CVSFactory(RoverItemFactory):
    
    def __init__(self):
        # TODO: doc me
        self._aliases = None

    def get_rover_items(self, config_line):
        """
        @param config_line: tuple of strings representing the 
            rover config line, i.e. (module, revision, vcs)
        @return: a list of RoverItems that this rover
          config line would check out. list will usually
          be 1 item long, but may be more in the case
          of e.g. CVS aliases
        """
        module, revision = config_line[:2]
        if self._is_alias(module):
            raise Exception("bad module (CVS aliases not allowed): %s" % module)
        out = []
        out.append(CVSItem(module, revision))

        return out

    def _is_alias(self, module):
        """
        determine if a module is a CVS alias
        @param module: string
        @return:       boolean
        """
        aliases = self._get_modules_content()
        if module in aliases:
            return True
        return False
                
    def _handle_excludes(self, modules):
        """
        return a list of module strings which is the set of
        postitive modules (those without a leading !), each
        of which has appended to it a space-separated list of
        negative modules. only append negative modules if they
        are child paths of the positive module in question.
        """
        excludes = [module for module in modules if module.startswith('!')]
        includes = [module for module in modules if not module.startswith('!')]

        out = []
        for include in includes:
            line = include
            for exclude in excludes:
                if exclude[1:].startswith(include):
                    line += ' ' + exclude
            out.append(line)

        return out

    def _get_modules_content(self):
        if self._aliases is None:
            cmd = 'cvs -Q -d %s checkout -p -A CVSROOT/modules' % os.environ['CVSROOT']
            exitcode, aliases = util.tee_silent(cmd)
            self._aliases = '\n'.join(aliases)
        return self._get_aliases()

    def _get_aliases(self):
        if type(self._aliases) in types.StringTypes:
            # parse the CVSROOT/modules string into
            # a dictionary keyed by alias name
            self._aliases = re.sub(r'#.*', '', self._aliases)  # kill all comments
            self._aliases = re.sub(r'\r\n', r'\n', self._aliases)  # kill all comments

            aliases = {}
            modules_re = re.compile( r'(?P<module_name>\w+) \-a (?P<module_contents>.*?[^\\]\n)', re.DOTALL )
            module_matches = modules_re.finditer(self._aliases)
            for module_match in module_matches:
                aliases[module_match.group('module_name')] = re.sub( r'[\s\\]+', ' ',  module_match.group('module_contents') ).strip().split()

            self._aliases = aliases

        return self._aliases

class CVSItem(RoverItem):
    
    def __init__(self, module, revision):
        """
        @param config_item: tuple of at least 3 elements
        """
        self.module = module
        self.revision = revision
        self.excludes = []

        if ' !' in module:
            self.module, self.excludes = self.module.split(' !', 1)
            self.excludes = map(lambda x: x.strip('!'), self.excludes.split())

    def checkout(self, checkout_dir, checkout_mode, verbose=True, test_mode=False):
        """
        check out stuff
        TODO: add comments
        """
        cmd = ['cvs']

        if not verbose:
            cmd.append('-Q')

        update_mode = True
        # if the path exists, but it's not a cvs working copy, 
        # we need to checkout instead of updating.  
        # that's why we append 'CVS' to the path
        module_dir = os.path.join(checkout_dir, self.get_path(), 'CVS')
        if os.path.exists(module_dir):
            cmd.append('update -d')
            if checkout_mode == 'clean':
                cmd.append('-C')
        else:
            cmd.append('checkout')
            update_mode = False

        cmd.append('-P')  # prune empty dirs

        if self.revision.lower() == 'head':
            cmd.append('-A')  # Reset sticky tags
        else:
            cmd.append('-r ' + self.revision)  # revision, if not head
            

        # build the command specification
        if update_mode:
            # we can't easily exclude things from the checkout here, 
            cmd.append(self.module)
        else:
            # when checkouting, put the module path first,
            # then use !directory/path to exclude portions
            cmd.append(self.module)
            cmd.extend(['!%s' % exclude for exclude in self.excludes])
        
        return_code, out = util.execute(cmd, cwd=checkout_dir, verbose=verbose, test_mode=test_mode, return_out=True)

        if return_code != 0:
            # sometimes CVS screws up when replacing old files. the known
            # erroring case is when a file exists in the local filesystem
            # that was not in the previously-checked-out rover config (branch,
            # etc) but is in the currently-being-checked-out config.
            #
            # in this case, we try to identify those files which are in the way,
            # move them out of the way, and issue the command again one time.
            in_the_way = re.compile( r"move away `?([^;]+)'; it is in the way" )
            for line in out:
                m = in_the_way.search(line)
                if m:
                    dirname, filename = os.path.split(m.group(1))

                    # FIXME: Do we want to append the date/time as well?
                    #        Otherwise, only one backup is allowed
                    # back up the file as .rover.<filename>
                    old = os.path.abspath( os.path.join( checkout_dir, dirname, filename ) )
                    new = os.path.abspath( os.path.join( checkout_dir, dirname, '.%s.rover' % filename ) )

                    #if verbose:
                    print "* Backing up %(old)s to %(new)s" % locals()

                    shutil.move(old, new)

            out = util.execute(cmd, cwd=checkout_dir, verbose=verbose, test_mode=test_mode)

    def get_path(self):
        """
        return most specific path which contains all things relative to checkout_dir
        """
        return self.module

    def exclude(self, path):
        """
        do what you need to do so that expand() works right
        """
        if not path in self.excludes:
            self.excludes.append(path)

    def expand(self):
        """
        return list of rover items
        """
        return [self]

    def narrow(self, path):
        """
        return a *new* RoverItem which checks out the more-specific
        path from the same area of the repository as this RoverItem
        would.

        This is logically equivalent to checking out this RoverItem,
        and then deleting all but path and its children from the
        checked-out directory.
        """
        narrowed = CVSItem(path, self.revision)
        for exclude in self.excludes:
            narrowed.exclude(exclude)

        return narrowed

    def requires(self, path):
        """
        returns True if the path will be checked out by this item or cannot
        be removed, False if otherwise.  if the path is included by this item,
        or is critical to version control, it is required.
        if the path is not version controlled, the behavior is undefined.
        """
        head, tail = os.path.split(path)
        if tail == 'CVS':
            # a 'CVS' directory is required only if its parent is also required
            return self.requires(head)
        if path.startswith(self.module):
            # children are required unless explicitly excluded
            for exclude in self.excludes:
                if path.startswith(exclude):
                    return False
            return True
        if self.module.startswith(path):
            # parents are always required
            return True
        return False

    def force_revision(self, revision):
        self.revision = revision

    def __repr__(self):
        """
        return a string suitable for serialization into a rover manifest

        use newlines ('\n') if this RoverItem represents multiple
        checkout operations
        """
        items = self.expand()
        out = []
        for item in items:
            module = [item.module] + item.excludes
            out.append("%s, %s, cvs" % (' !'.join(module), item.revision))
        return '\n'.join(out)

    def __eq__(self, other):
        if self.module != other.module:
            return False
        if self.revision != other.revision:
            return False
        if self.excludes != other.excludes:
            return False
        return True
    
    def __ne__(self, other):
        return not self.__eq__(other)

