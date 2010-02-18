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



class MockShell(object):
    def __init__(self, underflow_error=False):
        """Create the mock shell object

        underflow_error => throw an error if there is insuffient input
                           in the mock_results list. Default is false
                           and 0 is returned in this case.
        """
        self.mock_results = list()
        self.history = list()
        self.underflow_error = underflow_error

    def seed_result(self, return_code, output=None):
        """Test function to seed a result into the shell.
        
        Results are queued and returned in the order they are added."""
        r = (return_code, output)
        self.mock_results.append(r)

    def _pop_result(self):
        """Pop and return a result from the queue."""
        if len(self.mock_results) == 0:
            if self.underflow_error:
                raise Exception("Insufficient mock result data")
            return (0, '')
        r = self.mock_results[0]
	return r

    def tee(self, cmd, cwd=None):
        """Mock version from rover.shell"""
        self.history.append(cmd)

    def tee_silent(self, cmd, cwd=None):
        """Mock version from rover.shell"""
        self.history.append(cmd)

    def run_silent(self, cmd, cwd=None):
        """Mock version from rover.shell"""
        self.history.append(cmd)

    def run(self, cmd, cwd=None):
        """Mock version from rover.shell"""
        self.history.append(cmd)

    def execute(self, cmd, cwd=None, verbose=False, test_mode=False
            , return_out=False):
        """Mock version from rover.shell"""
        self.history.append(cmd)


    def exists(self, path):
        self.history.append('exists(%s)' % path)
        return self._pop_result()

    def push_dir(self, dir):
        self.history.append("push_dir(%s)" % dir)

    def pop_dir(self):
        self.history.append("pop_dir")

    def move(self, old_file, new_file):
        """Mock version from rover.shell"""
        x = 'mv %s %s' % (old_file, new_file)
        self.history.append(x)

