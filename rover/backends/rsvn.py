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

from rover import shell
from rover.backends.rover_interface import RoverItemFactory, RoverItem

class SVNFactory(RoverItemFactory):

    def get_rover_items(self, config_line):
        """
        return a list of RoverItems that this rover
        config line would check out. list will usually
        be 1 item long, but may be more in the case
        of eg CVS aliases
        """
        module, revision, vcs, url = config_line

        return [SVNItem(module, revision, url)]


class SVNItem(RoverItem):
    
    def __init__(self, module, revision, url):
        """
        @param config_item: tuple of at least 3 elements
        """
        self.module = module
        self.revision = revision
        self.url = url
        self.excludes = []

    def checkout(self, checkout_dir, checkout_mode, verbose=True, test_mode=False):
        """
        check out stuff
        TODO: add comments
        """
        if self.excludes != []:
            raise Excepion('call expand before checkout')
        
        cmd = ['svn']

        if not verbose:
            cmd.append('-Q')

        sh = shell.Shell()
        update_mode = True
        if os.path.exists(os.path.join(checkout_dir, self.get_path())):
            if checkout_mode == 'clean':
                sub_cmd = ['svn revert -R']
                sub_cmd.append(os.path.join(checkout_dir, self.get_path()))
                return_code, out = sh.execute(sub_cmd, cwd=checkout_dir
                        , return_out=True, test_mode=test_mode)
            cmd.append('update')
            cmd.append(self.get_path())
        else:
            cmd.append('checkout')
            update_mode = False
            cmd.append(self.url + '/' + self.get_path())

        #cmd.append('-r ' + self.revision)  # revision, if not head


        cmd = ' '.join(cmd)
        return_code, out = sh.execute(cmd, cwd=checkout_dir
                , return_out=True, test_mode=test_mode)

    def get_path(self):
        """
        return most specific path which contains all things relative to checkout_dir
        """
        return self.module

    def exclude(self, path):
        """
        do what you need to do so that expand() works right
        """
        self.excludes.append(path)

    def expand(self):
        """
        return list of rover items
        """
        if self.excludes == []:
            return [self]
        modules = []
        for exclude in self.excludes:
            module = self.module.split('/')
            modules.extend(self._expand(module, exclude.split('/'), len(module)-1))
        self.excludes = []
        modules = [SVNItem(os.path.join(*module), self.revision, self.url) for module in modules]
        return modules

    def narrow(self, path):
        """
        return a *new* RoverItem which checks out the more-specific
        path from the same area of the repository as this RoverItem
        would.

        This is logically equivalent to checking out this RoverItem,
        and then deleting all but path and its children from the
        checked-out directory.
        """
        narrowed = SVNItem(path, self.revision, self.url)
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
        if tail == '.svn':
            # a '.svn' directory is required only if its parent is also required
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

    def _expand(self, module, exclude, depth):
        if module[depth] == exclude[depth]:
            if len(exclude)-1 == depth:
                return []
            elif len(module)-1 == depth:
                dirs = list_contents('/'.join(module), self.url)
                ret = []
                for dir in dirs:
                    dir = dir.strip('/')
                    new_module = module[:]
                    new_module.append(dir)
                    ret.extend(self._expand(new_module, exclude, depth+1))
                return ret
            else:
                return self._expand(module, exclude, depth+1)
        else:
            return [module]

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
            out.append("%s, %s, svn, %s" % (item.module, item.revision, item.url))
        return '\n'.join(out)

    def __eq__(self, other):
        if self.module != other.module:
            return False
        if self.revision != other.revision:
            return False
        if self.url != other.url:
            return False
        if self.excludes != other.excludes:
            return False
        return True
    
    def __ne__(self, other):
        return not self.__eq__(other)



def list_contents(path, root):
    """
    @return list of relative paths rooted at "root"
    """
    cmd = "svn ls %s/%s" % (root, path)
    sh = shell.Shell()
    code, out = sh.execute(cmd, return_out=True)
    dirs = out.strip().split('\n')
    return dirs

