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
import sys
import time
import types
import urllib2

# module-relative import
import config
import rover.shell

from backends.rcvs import CVSFactory
from backends.rsvn import SVNFactory
from backends.rgit import GitFactory

class Rover:

    # maps the VCS field value to a RoverItemFactory
    factory_map = {
        'cvs': CVSFactory(),
        'svn': SVNFactory(),
        'git': GitFactory()
    }
    
    def __init__(self, config_names, checkout_mode='preserve', checkout_dir=os.getcwd()):
        self.config_names = config_names
        if type(self.config_names) in types.StringTypes:
            self.config_names = [self.config_names]
        self.checkout_mode = checkout_mode
        self.checkout_dir = os.path.abspath(os.path.expanduser(checkout_dir))

        # default values
        self.test_mode = False
        self.verbose = False
        self.manifest_filename = None
        self.includes = []
        self.excludes = []
        self.revision = None
        self.preserve_dirs = False

        self.config_lines = []
        self.config_items = []
        self.config_files = []
        self.config_errors = []
        
        self.clobbers = []

        self._validate()

    def set_preserve_dirs(self, preserve_dirs):
        self.preserve_dirs = preserve_dirs

    def set_verbose(self, verbose):
        self.verbose = verbose

    def set_test_mode(self, test_mode):
        self.test_mode = test_mode

    def set_manifest(self, manifest):
        self.manifest_filename = manifest

    def set_includes(self, includes):
        self.includes = includes

    def set_excludes(self, excludes):
        self.excludes = excludes

    def set_revision(self, revision):
        self.revision = revision

    def _validate(self):
        """
        raises an Exception if constructor options are in conflict
        """
        if self.checkout_mode not in ['paranoid', 'clean', 'preserve']:
            raise Exception("mode must be one of {'paranoid', 'clean', 'preserve'}")
        
    def process_config(self, config_name):
        revision = None
        if '@' in config_name:
            config_name, revision = config_name.split('@')

        if not config_name.endswith('.csv'):
            config_name = config_name + '.csv'

        # Opening config_dir has _never_ worked, apparently
        # Not even in the original version.  I think they
        # MEANT to just use config.config_dir, but who knows?
        #
        # In the future, we may want to have a ROVER_PATH env
        # var or something similar; or maybe default to /etc?
        #
        # Either way, moving it all into a nice little array
        # makes error handling much cleaner

        files = []
        # Use the ROVER_PATH variable first!
        if 'ROVER_PATH' in os.environ.keys():
            files.append( os.path.join(os.environ['ROVER_PATH'], config_name) )
        # Look in the current directory
        # FIXME: Do we necessarily WANT this, though?  Shouldn't we enforce
        #        that config files should be in a single place?
        files.append(config_name)
        # Look in the specified config directory, usually ./config/
        files.append(os.path.join(config.config_dir, config_name))

        # Find a working filename
        for filename in files:
            if os.path.isfile(filename):
                break

        try:
            file = open(filename)
        except IOError, e:
            print "Unable to open config file `%s'" % filename
            exit(1)

        config_items = self.parse_config(file)
        if revision:
            for item in config_items:
                item.force_revision(revision)

        self.config_items.extend(config_items)

    def save_manifest(self):
        """
        assumes self.manifest_filename is not None
        """
        manifest_filename = os.path.abspath(self.manifest_filename)
        manifest_dir = os.path.dirname(manifest_filename)

        if not os.path.exists(manifest_dir):
            os.makedirs(manifest_dir)

        fp = file(manifest_filename, 'w')
        fp.writelines(self.manifest())
        fp.close()

    def manifest(self):
        man = ['# Config: "%s"\n' % ' '.join(self.config_names),
               '# Created: %s\n\n' % time.asctime()]

        for item in self.config_items:
            man.append(str(item) + '\n')
        return man

    def parse_config(self, file):
        """
        validates config lines and parses them into rover items
        
        @param file: file object that points to a rover config file
        @return: list of rover items representing actual config lines
        """
        config_lines = []
        for line in file.readlines():
            comment_start = line.find('#')
            if comment_start >= 0:
                line = line[:comment_start]
            line = line.strip()
            if line:
                item = [x.strip() for x in line.split(',')]
                # TODO: better validation here; how?
                if len(item) < 3 or item[2] not in self.factory_map:
                    self.config_errors.append('invalid config line: "%s"' % line)
                else:
                    config_lines.append(tuple(item))
        # FIXME: Should this be closed here? Seems messy... its not
        #        really our file, so why are WE closing it?
        file.close()
       
        config_items = []
        for line in config_lines:
            # Get the RoverFactory that deals with the specified
            # version control system (cvs, svn, etc.)
            # NOTE: We can assume that there will always be a key
            #  that matches line[2], because this was checked in
            #  a previous step.
            fact = self.factory_map[line[2]]
            try:
                config_items.extend(fact.get_rover_items(line))
            except Exception, ex:
                self.config_errors.append("resolve error: %s" % ex)

        return config_items

    def _path_overrides(self, path, candidate):
        """
        return True if candidate overlays part or
        all of path, but nothing outside of path
        """
        return path == candidate or candidate.startswith(path + '/')
        
    def resolve(self):
        # TODO: comments
        items = [(item, item.get_path()) for item in self.config_items]

        # FIXME: Why are we reversing here?
        items.reverse()
        for idx, pair in enumerate(items):
            item, path = pair
            for candidate, cpath in items[idx+1:]:
                if self._path_overrides(path, cpath):
                    candidate._removeme = True
                    if path == cpath:
                        self.clobbers.append(candidate)
                elif self._path_overrides(cpath, path):
                    candidate.exclude(path)

        items.reverse()
        new_items = []
        for item, path in items:
            if getattr(item, '_removeme', False):
                continue
            new_items.extend(item.expand())


        self.config_items = new_items

    def checkout(self):
        """Checkout the repos gathered from the config file
        """
        # Create the shell object.  Eventually inject this as a param
        # for testability.
        sh = rover.shell.Shell()
        # Create the checkout directory if it doesn't exist
        if not os.path.exists(self.checkout_dir):
            os.makedirs(self.checkout_dir)
        # Checkout each item
        for item in self.config_items:
            if self.checkout_mode == 'paranoid':
                fullpath = os.path.join(self.checkout_dir, item.get_path())
                if os.path.exists(fullpath):
                    if self.test_mode:
                        print "[TEST MODE] REMOVING:", fullpath
                    else:
                        print "REMOVING:", fullpath
                        shutil.rmtree(fullpath, True)
            item.checkout(sh, self.checkout_dir, self.checkout_mode
                    , self.verbose, self.test_mode)


    def apply_filters(self):
        self._apply_includes()
        self._apply_excludes()

    def _apply_includes(self):
        """
        modify the set of rover items so that files and
        directories which are children of at least one of
        the specified inclusion filters will be checked out
        """
        if self.includes == []:
            return
        allowed_items = []
        for item in self.config_items:
            allowed = False
            path = item.get_path()
            for include in self.includes:
                if self._path_overrides(include, path):
                    # path is contained within exclude, so
                    # allow the item
                    allowed = True
                    break
                elif self._path_overrides(path, include):
                    # include is contained within path, so
                    # create a cloned config item for the
                    # include path (ie narrow the item)
                    # and don't include the original item
                    allowed_items.append(item.narrow(include))
                    break

            if allowed:
                allowed_items.append(item)
        
        self.config_items = allowed_items


    def _apply_excludes(self):
        """
        modify the set of rover items so that files and
        directories which match any of the excludes are
        not checked out
        """
        if self.excludes == []:
            return
        allowed_items = []
        for item in self.config_items:
            allowed = True
            path = item.get_path()
            for exclude in self.excludes:
                if self._path_overrides(exclude, path):
                    # path is contained within exclude, so
                    # don't allow the item at all
                    allowed = False
                    break
                elif self._path_overrides(path, exclude):
                    # exclude is contained within path, so
                    # exclude it from the item
                    item.exclude(exclude)

            if allowed:
                allowed_items.append(item)

        self.config_items = allowed_items


    def _clean(self):
        """
        returns the list of directories to be removed.
        walks the directory tree and builds a list of directories 
        that are required by the config items, putting all others 
        in the removes candidate list
        """
        removes = []
        keeps = []
        for root, dirnames, filenames in os.walk(self.checkout_dir):
            for dirname in dirnames:
                module = os.path.join(root, dirname)[len(self.checkout_dir):].strip('/')
                keep = False
                for item in self.config_items:
                    if item.requires(module):
                        keep = True
                        break
                if keep:
                    keeps.append(module)
                else:
                    removes.append(module)
                    dirnames.remove(dirname)
        return removes

    def clean(self):
        """
        recurse the checkout directory and remove all directories
        that are not checked out by the current rover config.  this
        is only guaranteed to work with directories that are under
        version control.  it is not guaranteed to preserve or delete
        locally created content, and should only be used in clean and
        paranoid modes.
        """
        removes = self._clean()
        for remove in removes:
            fullpath = os.path.join(self.checkout_dir, remove)
            if self.test_mode:
                print "[TEST MODE] REMOVING:", fullpath
            else:
                print "REMOVING:", fullpath
                shutil.rmtree(fullpath, True)

    def force_revision(self, revision):
        """
        force the given revision on all config items
        """
        for item in self.config_items:
            item.force_revision(revision)

    def warn(self, errors, fatal=False):
        if fatal:
            sys.stderr.write('\nERROR: Config errors:\n    ')
        else:
            sys.stderr.write('\nWARNING: clobbered config lines:\n    ')
        sys.stderr.write('\n    '.join([str(x) for x in errors]))
        sys.stderr.write('\n')
        if fatal:
            sys.exit(1)

    def run(self):
        """
        """
        # open and parse each config file into a list of tuples
        for config_name in self.config_names:
            self.process_config(config_name)
        if len(self.config_errors) > 0:
            self.warn(self.config_errors, fatal=True)
        self.resolve()
        if self.manifest_filename:
            self.save_manifest()
        if len(self.clobbers) > 0:
            self.warn(self.clobbers)
        self.apply_filters()
        self.checkout()
        if len(self.clobbers) > 0:
            self.warn(self.clobbers)

