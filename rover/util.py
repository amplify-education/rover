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

# utility functions related to command-line things

import os
import subprocess
import types

def tee(cmd, cwd=None):
    """
    executes a command, echoing output and buffering it
    for later use by the program. returns (exit_code, output)
    """
    pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd, shell=True)

    output = []

    while True:
        if pipe.poll() is not None:
            break

        x = pipe.stdout.readline()
        x = x.strip()
        print x
        output.append(x)

    # get any remaining output
    output += [line.strip() for line in pipe.stdout.readlines()]

    # if the command ends with a newline, don't
    # include that blank line in the output
    if len(output) > 0 and output[-1] == '':
        output = output[:-1]

    # return (exitcode, list of output+error lines)
    return pipe.poll(), output

def tee_silent(cmd, cwd=None):
    """
    executes a command, buffering it for later use by
    the program. returns (exit_code, output)
    """
    pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd, shell=True)

    output = []

    while True:
        if pipe.poll() is not None:
            break

        x = pipe.stdout.readline()
        x = x.strip()
        output.append(x)

    # get any remaining output
    output += [line.strip() for line in pipe.stdout.readlines()]

    # if the command ends with a newline, don't
    # include that blank line in the output
    if len(output) > 0 and output[-1] == '':
        output = output[:-1]

    # return (exitcode, list of output+error lines)
    return pipe.poll(), output

def run_silent(cmd, cwd=None):
    """
    executes a command. returns exit_code
    """
    pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd, shell=True)
    return pipe.wait()

def run(cmd, cwd=None):
    """
    executes a command, echoing output. returns exit_code
    """
    pipe = subprocess.Popen(cmd, cwd=cwd, shell=True)
    return pipe.wait()

def execute(cmd, cwd=None, verbose=False, test_mode=False, return_out=False):
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
            True: tee,
            False: run
        },
        False: {
            True: tee_silent,
            False: run_silent
        }
    }

    if not test_mode:
        return methods[verbose][return_out](cmd, cwd)
    elif return_out:
        return (0, [])
    else:
        return 0

