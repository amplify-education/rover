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
import subprocess
import types
import shutil


class Shell(object):
    "Shell class for executing commands on the system"
    def __init__(self):
        """Initialize the shell object"""
        self.dirstack = list()
        self.quiet = False
        self.verbose = False

    def tee(self, cmd, cwd=None):
        """
        executes a command, echoing output and buffering it
        for later use by the program. returns (exit_code, output)
        """
        pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE
                , stderr=subprocess.STDOUT, cwd=cwd, shell=True)

        output = []
        while True:
            if pipe.poll() is not None:
                break

            x = pipe.stdout.readline().strip()
            if x:
                print x
                output.append(x)

        # get any remaining output
        output += [line.strip() for line in pipe.stdout.readlines()]

        # if the command ends with a newline, don't
        # include that blank line in the output
        if output and output[-1] == '\n':
            output = output[:-1]

        # return (exitcode, list of output+error lines)
        return pipe.poll(), output

    def tee_silent(self, cmd, cwd=None):
        """
        executes a command, buffering it for later use by
        the program. returns (exit_code, output)
        """
        pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE
                , stderr=subprocess.STDOUT, cwd=cwd, shell=True)

        output = []
        while True:
            if pipe.poll() is not None:
                break

            x = pipe.stdout.readline()
            x = x.strip()
            if x:
                output.append(x)

        # get any remaining output
        output += [line.strip() for line in pipe.stdout.readlines()]

        # if the command ends with a newline, don't
        # include that blank line in the output
        if output and output[-1] == '\n':
            output = output[:-1]

        # return (exitcode, list of output+error lines)
        return pipe.poll(), output

    def run_silent(self, cmd, cwd=None):
        """
        executes a command. returns exit_code
        """
        pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE
                , stderr=subprocess.STDOUT, cwd=cwd, shell=True)
        return pipe.wait()

    def run(self, cmd, cwd=None):
        """
        executes a command, echoing output. returns exit_code
        """
        pipe = subprocess.Popen(cmd, cwd=cwd, shell=True)
        return pipe.wait()

    def execute(self, cmd, cwd=None, verbose=False, test_mode=False
            , return_out=False):
        """
        uses either tee, run, tee_silent, or run_silent
        """
        if type(cmd) in (types.ListType, types.TupleType):
            cmd = ' '.join(cmd)

        if test_mode:
            print "TEST MODE:",
        else:
            print "EXECUTING:",

        print "[%s] [%s]" % (cwd, cmd)

        # map by [verbose][return_out]
        methods = {
            True: {
                True: self.tee,
                False: self.run
            },
            False: {
                True: self.tee_silent,
                False: self.run_silent
            }
        }

        if not test_mode:
            return methods[verbose][return_out](cmd, cwd)
        elif return_out:
            return (0, [])
        else:
            return 0

    def exists(self, path):
        """Check if a file exists
        """
        return os.path.exists(path)

    def push_dir(self, new_dir):
        """Push the current directory onto the stack and change to a new one
        """
        self.dirstack.append(os.path.abspath(os.getcwd()))
        os.chdir(new_dir)

    def pop_dir(self):
        """Pop a directory off the stack and change to it."""
        dir = self.dirstack.pop()
        os.chdir(dir)

    def move(self, old_file, new_file):
        """Rename a file."""
        shutil.move(old_file, new_file)

