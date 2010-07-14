import os
import re
import subprocess

# The base version to use when installing from zip/tar file and not git repo
BASE_VERSION = 'v0.3.4'


def major():
    '''Parse the major version from the version string'''
    v = version()
    match = re.match("^v(\d+\.\d+)", v)
    return match.group(1)


def version():
    '''Report the version for this build'''
    try:
        import gitversion
        return gitversion.VERSION
    except:
        return VERSION


def make_gitversion():
    '''Write the version (as identified by git) to a file called version.py

    This version.py module will then be used to report the version.'''
    src_dir = os.path.dirname(__file__)
    version_path = os.path.join(src_dir, 'gitversion.py')
    git_describe = "git describe --match v*"
    proc = subprocess.Popen(git_describe, shell=True, stdout=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    with open(version_path, 'w') as gitver:
        gitver.write(stdout)