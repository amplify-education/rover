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

class RoverItemFactory(object):

    def get_rover_items(self, config_line):
        """
        return a list of RoverItems that this rover
        config line would check out. list will usually
        be 1 item long, but may be more in the case
        of eg CVS aliases
        """
        pass

class RoverItem(object):

    def __init__(self, config_item):
        """
        @param config_item: tuple of at least 3 elements, (path, revision, 
        """
        pass

    def checkout(self, checkout_dir, checkout_mode, verbosity=1):
        """
        check out stuff
        TODO: add comments
        """
        pass

    def get_path(self):
        """
        return most specific path which contains all things relative to checkout_dir
        """
        pass

    def exclude(self, path):
        """
        do what you need to do so that expand() works right
        """
        pass

    def expand(self):
        """
        return list of rover items
        """
        pass

    def narrow(self, path):
        """
        return a *new* RoverItem which checks out the more-specific
        path from the same area of the repository as this RoverItem
        would.

        This is logically equivalent to checking out this RoverItem,
        and then deleting all but path and its children from the
        checked-out directory.
        """
        pass

    def __repr__(self):
        """
        return a string suitable for serialization into a rover manifest

        use newlines ('\n') if this RoverItem represents multiple
        checkout operations
        """
        pass

