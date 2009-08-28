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

import csv
import optparse
import sys

DEFAULT_TAG = "GENERIC_DEMO_T"

def parse_commandline():
	p = optparse.OptionParser("Usage: %prog [options] config_file\n\nGenerates cvs rtag statements to create a new tag from a\ngiven rover config file")
	p.add_option("-t", "--tag", dest="tag", help="name of new tag, default is \"%s\"" % DEFAULT_TAG, default=DEFAULT_TAG)
	(opts, args) = p.parse_args()
	if len(args) != 1:
		p.print_help()
		sys.exit(1)
	return (opts, args)
	
if __name__ == '__main__':
	(opts, args) = parse_commandline()
	rover_config = csv.reader(open(args[0]))
	for row in rover_config:
		if len(row) == 3 and (not row[0].startswith('#')):
			(dirname, old_tag, reponame) = row
			cmd = "cvs rtag -F -r %s %s %s" % (old_tag.strip(), opts.tag, dirname.strip())
			print cmd
