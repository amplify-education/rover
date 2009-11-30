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
import types
import re
import sys
from StringIO import StringIO
import unittest

from rover import Rover
import rover.util
import rover.backends.rcvs
import rover.backends.rsvn


def _list_as_rover_items(items):
    out = []
    for line in items:
        if line[2] == 'cvs':
            out.extend(rover.backends.rcvs.CVSFactory().get_rover_items(line))
        elif line[2] == 'svn':
            out.extend(rover.backends.rsvn.SVNFactory().get_rover_items(line))
    return out

def mock_os_walk_factory(dir):
    """
    factory function that returns the correct mock of os.walk given
    a particular directory structure
    """
    def mock_os_walk(main_dir, topdown=True, onerror=None):
        def _walk(root, struct):
            # struct is (name, (dir, dir, ...), (file, file, ...))
            # where either may be empty

            name, dirs, files = struct
            dirnames = [x[0] for x in dirs]
            _dirnames = list(dirnames)
            r = os.path.join(root, name)
            yield r, dirnames, files

            # recreate the 'dirs' list with only the
            # directories which remain in 'dirnames'
            # once the user has had a chance to diddle
            # the list
            _dirs = []
            for dirname in dirnames:
                _dirs.append(dirs[_dirnames.index(dirname)])

            for dir in _dirs:
                for x in _walk(r, dir):
                    yield x

        for x in _walk(main_dir, dir):
            yield x

    return mock_os_walk


class RoverParserTestCase(unittest.TestCase):
    
    def test_fails_on_unsupported_vcs(self):
        """
        tests that the parser fails if an unsupported vcs is specified
        """

        r = Rover('')
        r.parse_config(StringIO('acme/project9, HEAD, blah'))
        self.assert_(len(r.config_errors) > 0)
    
    def test_fails_on_formatting_error(self):
        """
        tests that the parser fails if a config line is formatted incorrectly
        (e.g. wrong number of items)
        """
        
        r = Rover('')
        r.parse_config(StringIO('acme/project9, HEAD'))
        self.assert_(len(r.config_errors) > 0)

    def test_fails_on_include(self):
        """
        tests that the parser fails on include lines (includes are no longer allowed)
        """
        
        r = Rover('')
        r.parse_config(StringIO('@include big_mess.csv'))
        self.assert_(len(r.config_errors) > 0)

    def test_config_parser_basics(self):
        """
        tests that the config parser does basic parsing correctly
        """
        
        s = StringIO("""acme/project9/foo, HEAD, cvs
acme/framework, FOO_BRANCH_B, cvs # comment

#
# comment2
acme/project9/module/rab, BAR_TAG_T, svn, http://example.com/trunk""")

        expected = _list_as_rover_items(
                   [('acme/project9/foo', 'HEAD', 'cvs'),
                    ('acme/framework', 'FOO_BRANCH_B', 'cvs'),
                    ('acme/project9/module/rab', 'BAR_TAG_T', 'svn', 'http://example.com/trunk')])
        
        self.assertEquals(expected, Rover('').parse_config(s))


class RoverCleanTestCases(unittest.TestCase):
    """
    tests that Rover detects and removes the correct directories
    in clean and paranoid mode given a certain rover config
    and directory structure
    """

    def setUp(self):
        self.rover = Rover('')

    def test_removes(self):
        """
        test the basic case.  if a directory (say acme/spin) exists in the 
        local checkout, but is no longer in the rover config, it is removed.
        """
        input = _list_as_rover_items([
            ('acme/project9','HEAD','cvs'),
            ('acme/app','HEAD','cvs'),
            ])
        dirs = ['acme', [['app', [['CVS', [], []]], []],
                           ['project9', [['CVS', [], []],
                                   ['rab', [['CVS', [], []]], []]], 
                                  []],
                           ['spin', [['CVS', [], []]], []],
                           ['CVS', [], []]],
                          []]

        os.walk = mock_os_walk_factory(dirs)

        self.rover.config_items = input
        self.rover.resolve()
        output = self.rover._clean()
        expected = ['acme/spin']

        self.assertEquals(expected, output)

    def test_removes_excludes(self):
        """
        tests that when a directory is excluded with a ! it is removed
        """
        input = _list_as_rover_items([
            ('acme/project9 !acme/project9/rab','HEAD','cvs'),
            ('acme/app','HEAD','cvs'),
            ('acme/spin','HEAD','cvs'),
            ])
        dirs = ['acme', [['app', [['CVS', [], []]], []],
                           ['project9', [['CVS', [], []],
                                   ['rab', [['CVS', [], []]], []]], 
                                  []],
                           ['spin', [['CVS', [], []]], []],
                           ['CVS', [], []]],
                          []]

        os.walk = mock_os_walk_factory(dirs)

        self.rover.config_items = input
        self.rover.resolve()
        output = self.rover._clean()
        expected = ['acme/project9/rab']

        self.assertEquals(expected, output)
    
    def test_preserves_not_excluded(self):
        """
        tests that when a directory is excluded in some lines but
        not in others, it is preserved
        """
        input = _list_as_rover_items([
            ('acme/project9 !acme/project9/rab','HEAD','cvs'),
            ('acme/project9/rab','FOO_BRANCH','cvs'),
            ('acme/app','HEAD','cvs'),
            ('acme/spin','HEAD','cvs'),
            ])
        dirs = ['acme', [['app', [['CVS', [], []]], []],
                           ['project9', [['CVS', [], []],
                                   ['rab', [['CVS', [], []]], []]], 
                                  []],
                           ['spin', [['CVS', [], []]], []],
                           ['CVS', [], []]],
                          []]

        os.walk = mock_os_walk_factory(dirs)

        self.rover.config_items = input
        self.rover.resolve()
        output = self.rover._clean()
        expected = []

        self.assertEquals(expected, output)

    def test_mixed(self):
        """
        test with mixed cvs and svn
        """
        input = _list_as_rover_items([
            ('acme/project9','HEAD','cvs'),
            ('acme/app','HEAD','svn','http://example.com/svn'),
            ])
        dirs = ['acme', [['app', [['.svn', [], []]], []],
                           ['project9', [['CVS', [], []],
                                   ['rab', [['CVS', [], []]], []]], 
                                  []],
                           ['spin', [['.svn', [], []]], []],
                           ['CVS', [], []]],
                          []]

        os.walk = mock_os_walk_factory(dirs)

        self.rover.config_items = input
        self.rover.resolve()
        output = self.rover._clean()
        expected = ['acme/spin']

        self.assertEquals(expected, output)


class RoverResolverTestCase(unittest.TestCase):

    def setUp(self):
        self.rover = Rover('')


    def test_is_not_destructive(self):
        """
        tests that if the config has no overrides, that it comes
        out exactly as input
        """

        input = _list_as_rover_items([
            ('acme/project9','HEAD','cvs'),
            ('acme/app','HEAD','cvs'),
            ('acme/framework','HEAD','cvs'),
            ('acme/project9/module/api','project9_dev_03_b','cvs'),
            ('acme/project9/module/pk','ACME_LIVE_T','cvs'),
            ])
        
        self.rover.config_items = input
        self.rover.resolve()
        output = self.rover.config_items

        self.assertEquals(input, output)

    def test_overrides_are_removed(self):
        """
        tests that overridden whole directories are removed
        """

        input = _list_as_rover_items([
            ('acme/project9','HEAD','cvs'),
            ('acme/app','HEAD','cvs'),
            ('acme/framework','HEAD','cvs'),
            ('acme/project9','project9_foo_b','cvs'),
            ])

        expected = _list_as_rover_items([
            ('acme/app','HEAD','cvs'),
            ('acme/framework','HEAD','cvs'),
            ('acme/project9','project9_foo_b','cvs'),
            ])
        
        self.rover.config_items = input
        self.rover.resolve()
        output = self.rover.config_items

        self.assertEquals(expected, output)

    def test_dir_overrides_subdir_but_not_file(self):
        """
        tests that a directory checked out later overrides subdirectories
        of itself that are checked out earlier. also checks that directories
        whose name is a prefix of a file do not override the checkout for
        that file
        """

        input = _list_as_rover_items([
            ('acme/project9','HEAD','cvs'),
            ('acme/app','HEAD','cvs'),
            ('acme/framework','HEAD','cvs'),
            ('acme/project9','project9_foo_b','cvs'),
            ('acme/project9/module.conf','bar','cvs'),
            ('acme/project9/module/api','project9_dev_03_b','cvs'),
            ('acme/project9/module','project9_module_b','cvs'),
            ])

        expected = _list_as_rover_items([
            ('acme/app','HEAD','cvs'),
            ('acme/framework','HEAD','cvs'),
            ('acme/project9 !acme/project9/module !acme/project9/module/api !acme/project9/module.conf','project9_foo_b','cvs'),
            ('acme/project9/module.conf','bar','cvs'),
            ('acme/project9/module','project9_module_b','cvs'),
            ])
       
        self.rover.config_items = input
        self.rover.resolve()
        output = self.rover.config_items

        self.assertEquals(expected, output)

    def test_dir_overrides_file_in_dir(self):
        """
        tests that a directory checked out later overrides a single
        file checked out that lives in that directory
        """

        input = _list_as_rover_items([
            ('acme/project9','HEAD','cvs'),
            ('acme/app','HEAD','cvs'),
            ('acme/framework','HEAD','cvs'),
            ('acme/project9','project9_foo_b','cvs'),
            ('acme/project9/module.conf','bar','cvs'),
            ('acme/project9/module/api','project9_dev_03_b','cvs'),
            ('acme/project9/module/pk','ACME_LIVE_T','cvs'),
            ('acme/project9','project9_module_b','cvs'),
            ])

        expected = _list_as_rover_items([
            ('acme/app','HEAD','cvs'),
            ('acme/framework','HEAD','cvs'),
            ('acme/project9','project9_module_b','cvs'),
            ])
        
        self.rover.config_items = input
        self.rover.resolve()
        output = self.rover.config_items

        self.assertEquals(expected, output)
    
    def test_works_with_cvs_excludes(self):
        """
        tests that modules are replaced correctly, even in the presence
        of cvs excludes
        """

        input = _list_as_rover_items([
            ('acme/project9','HEAD','cvs', ''),
            ('acme/app','HEAD','cvs', ''),
            ('acme/framework','HEAD','cvs', ''),
            ('acme/project9 !acme/project9/module/api','project9_foo_b','cvs', ''),
            ('acme/project9/module.conf','bar','cvs', ''),
            ('acme/project9/module/api','project9_dev_03_b','cvs', ''),
            ('acme/project9/module/pk','ACME_LIVE_T','cvs', ''),
            ('acme/project9 !acme/project9/module/rab','project9_module_b','cvs', ''),
            ])

        expected = _list_as_rover_items([
            ('acme/app','HEAD','cvs', ''),
            ('acme/framework','HEAD','cvs', ''),
            ('acme/project9 !acme/project9/module/rab','project9_module_b','cvs', ''),
            ])
        
        self.rover.config_items = input
        self.rover.resolve()
        output = self.rover.config_items

        self.assertEquals(expected, output)

    def test_is_not_destructive_with_cvs_exclude_self(self):
        """
        test that a child module does not cause a parent module to be replaced
        if the parent module excludes a match of the child module
        """

        input = _list_as_rover_items([
            ('acme !acme/foo/bar','HEAD','cvs', ''),
            ('acme/foo/bar','HEAD','cvs', ''),
            ])
        
        self.rover.config_items = input
        self.rover.resolve()
        output = self.rover.config_items

        self.assertEquals(input, output)
    
    def test_is_not_destructive_with_cvs_exclude_parent(self):
        """
        test that a child module does not cause a parent module to be replaced
        if the parent module excludes a match of the child module
        """

        input = _list_as_rover_items([
            ('acme !acme/foo/bar/baz','HEAD','cvs', ''),
            ('acme/foo/bar','HEAD','cvs', ''),
            ])
        
        self.rover.config_items = input
        self.rover.resolve()
        output = self.rover.config_items

        self.assertEquals(input, output)
    
    def test_works_with_svn_and_cvs(self):
        """
        tests that overrides happen correctly when cvs and svn checkouts are mixed
        """

        input = _list_as_rover_items([
            ('acme/project9','HEAD','cvs'),
            ('acme/framework','HEAD','svn', 'http://example.com/trunk'),
            ('acme/project9/module/api','project9_dev_03_b','svn', 'http://example.com/trunk'),
            ])

        expected = _list_as_rover_items([
            ('acme/project9 !acme/project9/module/api','HEAD','cvs'),
            ('acme/framework','HEAD','svn', 'http://example.com/trunk'),
            ('acme/project9/module/api','project9_dev_03_b','svn', 'http://example.com/trunk'),
            ])
        
        self.rover.config_items = input
        self.rover.resolve()
        output = self.rover.config_items

        self.assertEquals(input, output)

    def test_only_excludes_once(self):
        """
        tests that excludes only get added to the checkout path once
        """

        input = _list_as_rover_items([
            ('acme/project9', 'HEAD', 'cvs'),
            ('acme/project9/etc', 'foo_b', 'cvs'),
            ('acme/project9/etc', 'bar_b', 'cvs'),
            ])

        expected = _list_as_rover_items([
            ('acme/project9 !acme/project9/etc','HEAD','cvs'),
            ('acme/project9/etc', 'bar_b', 'cvs'),
            ])
        
        self.rover.config_items = input
        self.rover.resolve()
        output = self.rover.config_items

        self.assertEquals(expected, output)

    def test_reports_clobbers(self):
        """
        tests that clobbered files are properly detected and reported
        """

        input = _list_as_rover_items([
            ('acme/project9', 'HEAD', 'cvs'),
            ('acme/project9/etc', 'foo_b', 'cvs'),
            ('acme/project9/etc', 'bar_b', 'cvs'),
            ])

        expected = _list_as_rover_items([
            ('acme/project9 !acme/project9/etc','HEAD','cvs'),
            ('acme/project9/etc', 'bar_b', 'cvs'),
            ])
        
        self.rover.config_items = input
        self.rover.resolve()

        self.assert_(len(self.rover.clobbers) > 0)


class RoverCvsAliasExpanderTestCase(unittest.TestCase):

    modules_content = r"""
acme_asdf_webapp -a                     \
!acme/asdf/web/site/introduction/videos \
acme/asdf/etc                           \
acme/asdf/src                           \
acme/asdf/test                          \
acme/asdf/web                           \
acme/asdf/test.xml                      \
acme/asdf/default.test.properties


# Added by satiani:
webapp_poc -a \
!acme/app/web \
!acme/asdf/web \
!acme/framework/web \
acme/app \
acme/asdf \
acme/framework 

acme_webapp -a \
acme/framework/build \
acme/framework/etc \
acme/framework/src/java \
acme/framework/web/etc \
acme/framework/web/site

recursive_alias -a \
acme_webapp \
webapp_poc
"""
    def setUp(self):
        self.cvs_fact = rover.backends.rcvs.CVSFactory()
        self.cvs_fact._aliases = self.modules_content

    def test_cvs_modules_parser(self):
        """
        tests parsing of CVSROOT/modules file
        """

        expected_modules = {'acme_asdf_webapp': ['!acme/asdf/web/site/introduction/videos', 'acme/asdf/etc', 'acme/asdf/src', 'acme/asdf/test', 'acme/asdf/web', 'acme/asdf/test.xml', 'acme/asdf/default.test.properties'],
                            'webapp_poc': ['!acme/app/web', '!acme/asdf/web', '!acme/framework/web', 'acme/app', 'acme/asdf', 'acme/framework'],
                            'acme_webapp': ['acme/framework/build', 'acme/framework/etc', 'acme/framework/src/java', 'acme/framework/web/etc', 'acme/framework/web/site'],
                            'recursive_alias': ['acme_webapp', 'webapp_poc']
                }
        
        self.assertEquals(expected_modules, self.cvs_fact._get_aliases())

    def test_alias_disabled(self):

        self.assertRaises(Exception, self.cvs_fact.get_rover_items, ('acme_asdf_webapp', 'HEAD', 'cvs'))

class RoverCvsntAliasExpanderTestCase(unittest.TestCase):

    modules_content = r"""
acme_asdf_webapp -a                     \
!acme/asdf/web/site/introduction/videos \
acme/asdf/etc                           \
acme/asdf/src                           \
acme/asdf/test                          \
acme/asdf/web                           \
acme/asdf/test.xml                      \
acme/asdf/default.test.properties


# Added by satiani:
webapp_poc -a \
!acme/app/web \
!acme/asdf/web \
!acme/framework/web \
acme/app \
acme/asdf \
acme/framework 

acme_webapp -a \
acme/framework/build \
acme/framework/etc \
acme/framework/src/java \
acme/framework/web/etc \
acme/framework/web/site

recursive_alias -a \
acme_webapp \
webapp_poc
"""
    modules_content = re.sub('\n', '\r\n', modules_content)
    def setUp(self):
        self.cvs_fact = rover.backends.rcvs.CVSFactory()
        self.cvs_fact._aliases = self.modules_content

    def test_cvs_modules_parser(self):
        """
        tests parsing of CVSROOT/modules file
        """

        expected_modules = {'acme_asdf_webapp': ['!acme/asdf/web/site/introduction/videos', 'acme/asdf/etc', 'acme/asdf/src', 'acme/asdf/test', 'acme/asdf/web', 'acme/asdf/test.xml', 'acme/asdf/default.test.properties'],
                            'webapp_poc': ['!acme/app/web', '!acme/asdf/web', '!acme/framework/web', 'acme/app', 'acme/asdf', 'acme/framework'],
                            'acme_webapp': ['acme/framework/build', 'acme/framework/etc', 'acme/framework/src/java', 'acme/framework/web/etc', 'acme/framework/web/site'],
                            'recursive_alias': ['acme_webapp', 'webapp_poc']
                }
        
        self.assertEquals(expected_modules, self.cvs_fact._get_aliases())
    
    def test_alias_disabled(self):

        self.assertRaises(Exception, self.cvs_fact.get_rover_items, ('acme_asdf_webapp', 'HEAD', 'cvs'))


class RoverSVNTestCase(unittest.TestCase):

    def setUp(self):
        self.old_list_contents = rover.backends.rsvn.list_contents

        def new_list_contents(path, root):
            return self.list_contents[path]

        rover.backends.rsvn.list_contents = new_list_contents

    def tearDown(self):
        rover.backends.rsvn.list_contents = self.old_list_contents
    
    def test_svn_exclude_naive(self):

        self.list_contents = {}
        self.list_contents['acme/project9/module'] = ['pk', 'cli', 'rab', 'api']

        r = Rover('')
        r.config_items = _list_as_rover_items(
                         [('acme/project9/module', 'HEAD', 'svn', 'http://foo.com'),
                          ('acme/project9/module/rab', 'HEAD', 'svn', 'http://bar.com')])
        r.resolve()
        
        expected = _list_as_rover_items(
                   [('acme/project9/module/pk', 'HEAD', 'svn', 'http://foo.com'),
                    ('acme/project9/module/cli', 'HEAD', 'svn', 'http://foo.com'),
                    ('acme/project9/module/api', 'HEAD', 'svn', 'http://foo.com'),
                    ('acme/project9/module/rab', 'HEAD', 'svn', 'http://bar.com')])
       
        self.assertEquals(r.config_items, expected)
    
    def test_svn_exclude_dir_and_file(self):

        self.list_contents = {}
        self.list_contents['acme/project9/module'] = ['pk', 'cli', 'rab', 'test', 'test.xml']

        r = Rover('')
        r.config_items = _list_as_rover_items(
                         [('acme/project9/module', 'HEAD', 'svn', 'http://foo.com'),
                          ('acme/project9/module/test', 'HEAD', 'svn', 'http://bar.com')])
        r.resolve()
        
        expected = _list_as_rover_items(
                   [('acme/project9/module/pk', 'HEAD', 'svn', 'http://foo.com'),
                    ('acme/project9/module/cli', 'HEAD', 'svn', 'http://foo.com'),
                    ('acme/project9/module/rab', 'HEAD', 'svn', 'http://foo.com'),
                    ('acme/project9/module/test.xml', 'HEAD', 'svn', 'http://foo.com'),
                    ('acme/project9/module/test', 'HEAD', 'svn', 'http://bar.com')])
       
        self.assertEquals(r.config_items, expected)
        
class RoverFilterTestCase(unittest.TestCase):

    def test_exclude_filter__bigger_filter(self):

        r = Rover('')
        r.set_excludes(['acme/app/test'])
        r.config_items = _list_as_rover_items(
                         [('acme/project9', 'HEAD', 'cvs'),
                          ('acme/app/src/java', 'HEAD', 'cvs'),
                          ('acme/app/test/java', 'HEAD', 'cvs')])

        r.apply_filters()

        expected = _list_as_rover_items(
                   [('acme/project9', 'HEAD', 'cvs'),
                    ('acme/app/src/java', 'HEAD', 'cvs')])

        self.assertEquals(r.config_items, expected)

    def test_exclude_filter__smaller_filter(self):

        r = Rover('')
        r.set_excludes(['acme/app/test/java/com/example/foo'])
        r.config_items = _list_as_rover_items(
                         [('acme/project9', 'HEAD', 'cvs'),
                          ('acme/app/src/java', 'HEAD', 'cvs'),
                          ('acme/app/test/java', 'HEAD', 'cvs')])

        r.apply_filters()

        expected = _list_as_rover_items(
                   [('acme/project9', 'HEAD', 'cvs'),
                    ('acme/app/src/java', 'HEAD', 'cvs'),
                    ('acme/app/test/java !acme/app/test/java/com/example/foo', 'HEAD', 'cvs')])

        self.assertEquals(r.config_items, expected)

    def test_include_filter__bigger_filter(self):

        r = Rover('')
        r.set_includes(['acme/app/test'])
        r.config_items = _list_as_rover_items(
                         [('acme/project9', 'HEAD', 'cvs'),
                          ('acme/app/src/java', 'HEAD', 'cvs'),
                          ('acme/app/test/java', 'HEAD', 'cvs')])

        r.apply_filters()

        expected = _list_as_rover_items(
                   [('acme/app/test/java', 'HEAD', 'cvs')])

        self.assertEquals(r.config_items, expected)

    def test_include_filter__smaller_filter(self):

        r = Rover('')
        r.set_includes(['acme/app/test/java/foo'])
        r.config_items = _list_as_rover_items(
                         [('acme/project9', 'HEAD', 'cvs'),
                          ('acme/app/src/java', 'HEAD', 'cvs'),
                          ('acme/app/test/java', 'HEAD', 'cvs')])

        r.apply_filters()

        expected = _list_as_rover_items(
                   [('acme/app/test/java/foo', 'HEAD', 'cvs')])

        self.assertEquals(r.config_items, expected)

    def test_mixed__no_overlap(self):

        r = Rover('')
        r.set_includes(['acme/app/test/java'])
        r.set_excludes(['acme/project9'])
        r.config_items = _list_as_rover_items(
                         [('acme/project9', 'HEAD', 'cvs'),
                          ('acme/app/src/java', 'HEAD', 'cvs'),
                          ('acme/app/test/java', 'HEAD', 'cvs')])

        r.apply_filters()

        expected = _list_as_rover_items(
                   [('acme/app/test/java', 'HEAD', 'cvs')])

        self.assertEquals(r.config_items, expected)

    def test_mixed__overlap__include_greater(self):

        r = Rover('')
        r.set_includes(['acme/app'])
        r.set_excludes(['acme/app/src/java/com/example/app/command'])
        r.config_items = _list_as_rover_items(
                         [('acme/project9', 'HEAD', 'cvs'),
                          ('acme/app/src/java', 'HEAD', 'cvs'),
                          ('acme/app/test/java', 'HEAD', 'cvs')])

        r.apply_filters()

        expected = _list_as_rover_items(
                   [('acme/app/src/java !acme/app/src/java/com/example/app/command', 'HEAD', 'cvs'),
                    ('acme/app/test/java', 'HEAD', 'cvs')])

        self.assertEquals(r.config_items, expected)


class RoverUtilTestCase(unittest.TestCase):

    def test_return_codes(self):
        """
        test that return codes are returned and work correctly
        """
        returncode = rover.util.run_silent("true")
        self.assertEquals(returncode, 0)

        returncode = rover.util.run("true")
        self.assertEquals(returncode, 0)

        returncode, output = rover.util.tee_silent("true")
        self.assertEquals(returncode, 0)

        returncode, output = rover.util.tee("true")
        self.assertEquals(returncode, 0)


        returncode = rover.util.run_silent("false")
        self.assertEquals(returncode, 1)

        returncode = rover.util.run("false")
        self.assertEquals(returncode, 1)

        returncode, output = rover.util.tee_silent("false")
        self.assertEquals(returncode, 1)

        returncode, output = rover.util.tee("false")
        self.assertEquals(returncode, 1)

    def test_capture_output(self):
        """
        test that the tee* methods capture output
        """
        returncode, out = rover.util.tee('echo "."')
        self.assertEquals(out, ['.'])
        self.assertEquals(returncode, 0)

        returncode, out = rover.util.tee_silent('echo "."')
        self.assertEquals(out, ['.'])
        self.assertEquals(returncode, 0)

    def test_execute(self):
        """
        make sure the verbose and return_out keyword args
        do what we expect them to do
        """
        returncode, out = rover.util.execute('echo "."', verbose=True, return_out=True)
        self.assertEquals(out, ['.'])
        self.assertEquals(returncode, 0)

        returncode = rover.util.execute('echo "."', verbose=True, return_out=False)
        self.assertEquals(returncode, 0)

        returncode, out = rover.util.execute('echo "."', verbose=False, return_out=True)
        self.assertEquals(out, ['.'])
        self.assertEquals(returncode, 0)

        returncode = rover.util.execute('echo "."', verbose=False, return_out=False)
        self.assertEquals(returncode, 0)

    def test_testmode(self):
        """
        make sure test_mode=True doesn't execute the command
        """
        returncode, out = rover.util.execute('echo "."', verbose=True, return_out=True, test_mode=True)
        self.assertEquals(out, [])
        self.assertEquals(returncode, 0)



if __name__ == '__main__':
    unittest.main()
