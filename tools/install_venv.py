

# Adapted from installation script for the OpenStack Dashboard development
# virtualenv.

# Copyright 2012 OCC.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Installation script for the Tukey Middle-ware development virtualenv.
"""

import os
import subprocess
import sys

from optparse import OptionParser

# get local settings across packages
sys.path.append('local')
import local_settings



ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
VENV = os.path.join(ROOT, '.venv')
WITH_VENV = os.path.join(ROOT, 'tools', 'with_venv.sh')
PIP_REQUIRES = os.path.join(ROOT, 'tools', 'pip-requires')
TEST_REQUIRES = os.path.join(ROOT, 'tools', 'test-requires')


def die(message, *args):
    print >> sys.stderr, message % args
    sys.exit(1)


def run_command(cmd, redirect_output=True, check_exit_code=True, cwd=ROOT,
                die_message=None):
    """
    Runs a command in an out-of-process shell, returning the
    output of that command.  Working directory is ROOT.
    """
    if redirect_output:
        stdout = subprocess.PIPE
    else:
        stdout = None

    proc = subprocess.Popen(cmd, cwd=cwd, stdout=stdout)
    output = proc.communicate()[0]
    if check_exit_code and proc.returncode != 0:
        if die_message is None:
            die('Command "%s" failed.\n%s', ' '.join(cmd), output)
        else:
            die(die_message)
    return output


HAS_EASY_INSTALL = bool(run_command(['which', 'easy_install'],
                                    check_exit_code=False).strip())
HAS_VIRTUALENV = bool(run_command(['which', 'virtualenv'],
                                  check_exit_code=False).strip())


def check_dependencies():
    """Make sure virtualenv is in the path."""

    print 'Checking dependencies...'
    if not HAS_VIRTUALENV:
        print 'Virtual environment not found.'
        # Try installing it via easy_install...
        if HAS_EASY_INSTALL:
            print 'Installing virtualenv via easy_install...',
            run_command(['easy_install', 'virtualenv'],
                        die_message='easy_install failed to install virtualenv'
                                    '\ndevelopment requires virtualenv, please'
                                    ' install it using your favorite tool')
            if not run_command(['which', 'virtualenv']):
                die('ERROR: virtualenv not found in path.\n\ndevelopment '
                    ' requires virtualenv, please install it using your'
                    ' favorite package management tool and ensure'
                    ' virtualenv is in your path')
            print 'virtualenv installation done.'
        else:
            die('easy_install not found.\n\nInstall easy_install'
                ' (python-setuptools in ubuntu) or virtualenv by hand,'
                ' then rerun.')
    print 'dependency check done.'


def create_virtualenv(venv=VENV):
    """Creates the virtual environment and installs PIP only into the
    virtual environment
    """
    print 'Creating venv...',
    run_command(['virtualenv', '-q', '--no-site-packages', venv])
    print 'done.'
    print 'Installing pip in virtualenv...',
    if not run_command([WITH_VENV, 'easy_install', 'pip']).strip():
        die("Failed to install pip.")
    print 'done.'
    print 'Installing distribute in virtualenv...'
    pip_install('distribute>=0.6.24')
    print 'done.'


def pip_install(*args):
    args = [WITH_VENV, 'pip', 'install', '--upgrade'] + list(args)
    run_command(args, redirect_output=False)


def install_dependencies(venv=VENV):
    print "Installing dependencies..."
    print "(This may take several minutes, don't panic)"
    pip_install('-r', TEST_REQUIRES)
    pip_install('-r', PIP_REQUIRES)

    # Tell the virtual env how to "import dashboard"
    py = 'python%d.%d' % (sys.version_info[0], sys.version_info[1])
    pthfile = os.path.join(venv, "lib", py, "site-packages", "dashboard.pth")
    f = open(pthfile, 'w')
    f.write("%s\n" % ROOT)


def install_tukey():
    print 'Installing tukey-middleware module in development mode...'
    run_command([WITH_VENV, 'python', 'setup.py', 'develop'], cwd=ROOT)

def install_database():
    if local_settings.AUTH_DB_PASSWORD.strip(): 
        print 'Installing database requires sudo and psql tcp connections'
        cmd = ['tools/create_db.sh', local_settings.AUTH_DB_PASSWORD]
        run_command(cmd, cwd=ROOT)
    else:
        sys.stderr.write('Database not created.')
        sys.stderr.write('Password is blank:')
        sys.stderr.wirte('please set AUTH_DB_PASSWORD in local_settings file')

def create_log_dir():
    if not local_settings.LOG_DIR.strip():
        sys.stderr.write('No log directory created.')
        sys.stderr.write('Log directory is blank:')
        sys.stderr.wirte('please set LOG_DIR in local_settings file')
    elif not local_settings.USER.strip():
        sys.stderr.write('No log directory created.')
        sys.stderr.write('User is blank:')
        sys.stderr.wirte('please set USER in local_settings file')
    else: 
        print 'Creating log dir requires sudo'
        cmd = ['tools/create_log.sh', local_settings.LOG_DIR,
            local_settings.USER]
        run_command(cmd, cwd=ROOT)

def create_apache_config():
    print 'Creating and linking apache confs requires sudo'
    cmd = ['tools/create_apache.sh']
    run_command(cmd, cwd=ROOT)


def print_summary():
    summary = """
Tukey-middleware development environment setup is complete.

To activate the virtualenv for the extent of your current shell session you
can run:

$ source .venv/bin/activate
"""
    print summary


def main():
    # want to check if the user wants to install the apache stuff also.
    usage = "%prog [options]"

    parser = OptionParser(usage=usage)

    parser.add_option("-a", "--apache", dest="apache", action="store_true",
        help="install apache config files for middleware proxies", 
        default=True)

    parser.add_option("--no-apache", dest="apache", action="store_false")

    parser.add_option("-d", "--database", dest="database", action="store_true",
        help="install database config files for middleware proxies", 
        default=True)

    parser.add_option("--no-database", dest="database", action="store_false")

    parser.add_option("-l", "--logdir", dest="logdir", action="store_true",
        help="install logdir config files for middleware proxies", 
        default=True)

    parser.add_option("--no-logdir", dest="logdir", action="store_false")

    parser.add_option("--no-pip", dest="pip", action="store_false")

    (options, _) = parser.parse_args()

    if options.pip:
        check_dependencies()
        create_virtualenv()
        install_dependencies()
        
    # pretty sure this is not needed
    #install_tukey()
    if options.database:
        install_database()

    if options.database:
        create_log_dir()

    if options.apache:
        create_apache_config()

    print_summary()

if __name__ == '__main__':
    main()
