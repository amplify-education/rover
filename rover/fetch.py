#!/usr/bin/env python
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

#vi:sts=4 ts=4 sw=4 expandtab

import os
import sys
from optparse import OptionParser

from rover import Rover

def main():
    parser = OptionParser("""usage: %prog [options] config[@revision] [config[@revision]] ...

        Rover accepts one or more 'config' arguments, which are file names 
        or paths to specific config files. The files will be concatenated in
        the order they are specified and treated as a single file. A revison
        can be added optionally after the '@', and that revision will be
        forced for all modules in that config file.""")
    parser.add_option('-p', '--preserve-dirs',
                      action="store_true",
                      dest="preserve_dirs",
                      help="(git only) preserve path to git repository; i.e., git@github.com:outer/space/plan9.git will be checked out to `outer/space/plan9/' instead of just `plan9/', which is default git behavior.")
    parser.add_option('-v', '--verbose',
                      action='store_true',
                      dest='verbose',
                      help='Print lots of stuff')
    parser.add_option('-q', '--quiet',
                      action='store_false',
                      dest='verbose',
                      default=False,
                      help='Only print commands being issued (default)')
    parser.add_option('-t', '--test-mode',
                      action='store_true',
                      dest='test_mode',
                      default=False,
                      help="Build and display commands, but don't issue them")
    parser.add_option('-m', '--mode',
                      action='store',
                      dest='checkout_mode',
                      default='preserve',
                      help="Must be one of {'paranoid', 'clean', 'preserve'}.  Paranoid wipes out the entire source directory before doing a fresh checkout, clean performs an update but reverts all modified files to the repository version, and preserve performs an update while attempting to preserve local modifications.  Preserve is the default.")
    parser.add_option('-d','--checkout-dir',
                      action='store',
                      dest='checkout_dir',
                      default=os.getcwd(),
                      help='Root dir, relative to working dir, that Rover will check out to.  Defaults to current directory.')
    parser.add_option('-f','--manifest',
                      action='store',
                      dest='manifest_filename',
                      default=None,
                      help='File in which to store list of all directories & branches checked out')
    parser.add_option('-x', '--exclude',
                      action='append',
                      dest='excludes',
                      default=[],
                      help='Files or directories to not check out. Specify full path, eg, `src/test.java`... May specify multiple paths.')
    parser.add_option('-i', '--include',
                      action='append',
                      dest='includes',
                      default=[],
                      help='Files or directories to check out. Specify full path, eg, `src/test.java`. May specify multiple paths. If specified, only files or directories matched will be checked out.')
    opts, args = parser.parse_args()

    if len(args) < 1:
        parser.print_help()
        sys.exit(-1)

    try:
        r = Rover(config_names=args, checkout_mode=opts.checkout_mode, checkout_dir=opts.checkout_dir)
        r.set_verbose(opts.verbose)
        r.set_test_mode(opts.test_mode)
        r.set_manifest(opts.manifest_filename)
        r.set_excludes(opts.excludes)
        r.set_includes(opts.includes)
        r.set_preserve_dirs(opts.preserve_dirs)
    except Exception, e:
        parser.print_help()
        print
        parser.set_usage('')
        parser.error(e)

    r.run()

