#!/usr/bin/env python
from distutils.core import setup, Command
from unittest import TextTestRunner, TestLoader, TestSuite
from glob import glob
from os.path import splitext, basename, join as pjoin, walk
from ConfigParser import ConfigParser
import os, sys

try:
    from pylint import lint
    #PyLinter
except:
    pass

"""
Build, clean and test the WMCore package.
"""

def generate_filelist():
    files = []
    for dirpath, dirnames, filenames in os.walk('./src/python/'):
        # skipping CVS directories and their contents
        pathelements = dirpath.split('/')
        result = []
        if not 'CVS' in pathelements:
            # to build up a list of file names which contain tests
            for file in filenames:
                if file.endswith('.py'):
                    filepath = '/'.join([dirpath, file]) 
                    files.append(filepath)
    return files

def lint_files(files):
    """
    lint a (list of) file(s) and return the results 
    """
    input = ['--rcfile=standards/.pylintrc', 
              '--output-format=parseable', 
              '--reports=n', ]
    input.extend(files)
    try:
        lint_result = lint.Run(input)
    except NameError:
        print "In order to run lint, you must have pylint installed"
        print "lint failure."
        sys.exit(1)
    return lint_result.linter.stats

class TestCommand(Command):
    """
    Handle setup.py test with this class - walk through the directory structure 
    and build up a list of tests, then build a test suite and execute it.
    
    TODO: Pull database URL's from environment, and skip tests where database 
    URL is not present (e.g. for a slave without Oracle connection)
    
    TODO: need to build a separate test runner for each test file, python is
          keeping the test objects around, which is keeping it from destroying
          filehandles, which is causing us to bomb out of a lot more tests than
          necessary. Or, people could learn to close their files themselves.
          either-or.
    """
    user_options = [ ]

    def initialize_options(self):
        self._dir = os.getcwd()

    def finalize_options(self):
        pass

    def run(self):
        '''
        Finds all the tests modules in test/python/WMCore_t, and runs them.
        '''
        testfiles = [ ]
        
        # Add the test and src directory to the python path
        testspypath = '/'.join([self._dir, 'test/python/'])
        srcpypath = '/'.join([self._dir, 'src/python/']) 
        sys.path.append(testspypath)
        sys.path.append(srcpypath)
        
        # Walk the directory tree
        for dirpath, dirnames, filenames in os.walk('./test/python/WMCore_t'):
            # skipping CVS directories and their contents
            pathelements = dirpath.split('/')
            if not 'CVS' in pathelements:
                # to build up a list of file names which contain tests
                for file in filenames:
                    if file not in ['__init__.py']:
                        if file.endswith('_t.py'):
                            testmodpath = pathelements[3:]
                            testmodpath.append(file.replace('.py',''))
                            testfiles.append('.'.join(testmodpath))
                            
        oldstdout = sys.stdout
        oldstderr = sys.stderr

        sys.stdout = None
        
        testsuite = TestSuite()
        failedTestFiles = []
        for test in testfiles:
            try:
                testsuite.addTest(TestLoader().loadTestsFromName(test))
            except Exception, e:
                failedTestFiles.append(test)
                #print "Could not load %s test - fix it!\n %s" % (test, e)
        #print "Running %s tests" % testsuite.countTestCases()
        
        t = TextTestRunner(verbosity = 1)
        result = t.run(testsuite)
        sys.stdout = oldstdout
        sys.stderr = oldstderr
        if not result.wasSuccessful():
            print "Tests unsuccessful. There were %s failures and %s errors"\
                      % (len(result.failures), len(result.errors))
            print "Failurelist:\n%s" % "\n".join(map(lambda x: \
                                                        "FAILURE: %s\n%s" % (x[0],x[1] ), result.failures))
            print "Errorlist:\n%s" % "\n".join(map(lambda x: \
                                                        "ERROR:   %s\n%s" % (x[0],x[1] ), result.errors))
            if len(failedTestFiles):
                print "The following tests failed to load: \n===============\n%s" %\
                    "\n".join(failedTestFiles)
             #"".join(' ', [result.failures[0],result.failures[1]]))
            #print "Errorlist:\n%s" % result.errors #"".join(' ', [result.errors[0],result.errors[1]]))
            print "Tests unsuccessful. There were %s failures and %s errors"\
                      % (len(result.failures), len(result.errors))
            print "FAILED: setup.py test" 
            sys.exit(1)
        else:
            print "Tests successful"
            if len(failedTestFiles):
                print "The following tests failed to load: \n===============\n%s" %\
                        "\n".join(failedTestFiles)
            print "PASSED: setup.py test"
            sys.exit(0)
        

        
            
class CleanCommand(Command):
    """
    Clean up (delete) compiled files
    """
    user_options = [ ]

    def initialize_options(self):
        self._clean_me = [ ]
        for root, dirs, files in os.walk('.'):
            for f in files:
                if f.endswith('.pyc'):
                    self._clean_me.append(pjoin(root, f))

    def finalize_options(self):
        pass

    def run(self):
        for clean_me in self._clean_me:
            try:
                os.unlink(clean_me)
            except:
                pass
            
class LintCommand(Command):
    """
    Lint all files in the src tree
    
    TODO: better format the test results, get some global result, make output 
    more buildbot friendly.    
    """
    
    user_options = [ ]
    
    def initialize_options(self):
        self._dir = os.getcwd()

    def finalize_options(self):
        pass
    
    def run(self):
        '''
        Find the code and run lint on it
        '''
        srcpypath = '/'.join([self._dir, 'src/python/'])
        sys.path.append(srcpypath) 
        
        result = []
        for filepath in generate_filelist(): 
            result.append(lint_files([filepath]))
            
class ReportCommand(Command):
    """
    Generate a simple html report for ease of viewing in buildbot
    
    To contain:
        average lint score
        % code coverage
        list of classes missing tests
        etc.
    """
    
    user_options = [ ]
    
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        """
        run all the tests needed to generate the report and make an
        html table
        """
        files = generate_filelist()
        
        error = 0 
        warning = 0
        refactor = 0
        convention = 0 
        statement = 0
        
        srcpypath = '/'.join([os.getcwd(), 'src/python/'])
        sys.path.append(srcpypath)

        cfg = ConfigParser()
        cfg.read('standards/.pylintrc')
        
        # Supress stdout/stderr
        err_bak = sys.stderr
        out_bak = sys.stdout
        sys.stderr = open('/dev/null', 'w')
        sys.stdout = open('/dev/null', 'w')
        
        # lint the code
        for stats in lint_files(files):
            error += stats['error']
            warning += stats['warning']
            refactor += stats['refactor']
            convention += stats['convention'] 
            statement += stats['statement']
        
        # and restore the stdout/stderr
        sys.stderr = err_bak
        sys.stdout = out_bak
        
        stats = {'error': error,
            'warning': warning,
            'refactor': refactor,
            'convention': convention, 
            'statement': statement}
        
        lint_score = eval(cfg.get('MASTER', 'evaluation'), {}, stats)
        coverage = 0 # TODO: calculate this
        testless_classes = [] # TODO: generate this
        
        print "<table>"
        print "<tr>"
        print "<td colspan=2><h1>WMCore test report</h1></td>"
        print "</tr>"
        print "<tr>"
        print "<td>Average lint score</td>"
        print "<td>%.2f</td>" % lint_score
        print "</tr>"
        print "<tr>"
        print "<td>% code coverage</td>"
        print "<td>%s</td>" % coverage
        print "</tr>"
        print "<tr>"
        print "<td>Classes missing tests</td>"
        print "<td>"
        if len(testless_classes) == 0:
            print "None"
        else:
            print "<ul>"
            for c in testless_classes:
                print "<li>%c</li>" % c
            print "</ul>"
        print "</td>"
        print "</tr>"
        print "</table>"
            
class CoverageCommand(Command):
    """
    Run code coverage tests    
    """
    
    user_options = [ ]
    
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass
    
    def run(self):
        """
        Determine the code's test coverage and return that as a float
        
        http://nedbatchelder.com/code/coverage/
        """
        return 0.0
    
class DumbCoverageCommand(Command):
    """
    Run a simple coverage test - find classes that don't have a unit test    
    """
    
    user_options = [ ]
    
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass
    
    def run(self):
        """
        Determine the code's test coverage in a dumb way and return that as a 
        float.
        """
        print "This determines test coverage in a very crude manner. If your"
        print "test file is incorrectly named it will not be counted, and" 
        print "result in a lower coverage score." 
        print '----------------------------------------------------------------'
        filelist = generate_filelist()
        tests = 0
        files = 0
        pkgcnt = 0
        dir = os.getcwd()
        pkg = {'name': '', 'files': 0, 'tests': 0}
        for f in filelist:
            testpath = '/'.join([dir, f])
            pth = testpath.split('./src/python/')
            pth.append(pth[1].replace('/', '_t/').replace('.', '_t.'))
            if pkg['name'] == pth[2].rsplit('/', 1)[0].replace('_t/', '/'):
                # pkg hasn't changed, increment counts
                pkg['files'] += 1
            else:
                # new package, print stats for old package
                pkgcnt += 1
                if pkg['name'] != '' and pkg['files'] > 0:
                    print 'Package %s has coverage %.1f percent' % (pkg['name'], 
                                (float(pkg['tests'])/float(pkg['files']) * 100))
                # and start over for the new package
                pkg['name'] = pth[2].rsplit('/', 1)[0].replace('_t/', '/')
                # do global book keeping
                files += pkg['files']
                tests += pkg['tests'] 
                pkg['files'] = 0 
                pkg['tests'] = 0
            pth[1] = 'test/python'
            testpath = '/'.join(pth)
            try: 
                os.stat(testpath)
                pkg['tests'] += 1
            except:
                pass
            
        coverage = (float(tests) / float(files)) * 100
        print '----------------------------------------------------------------'
        print 'Code coverage (%s packages) is %.2f percent' % (pkgcnt, coverage)
        return coverage
    
def getPackages(package_dirs = []):
    packages = []
    for dir in package_dirs:
        for dirpath, dirnames, filenames in os.walk('./%s' % dir):
            # Exclude things here
            if dirpath not in ['./src/python/', './src/python/IMProv']: 
                pathelements = dirpath.split('/')
                if not 'CVS' in pathelements:
                    path = pathelements[3:]
                    packages.append('.'.join(path))
    return packages

package_dir = {'WMCore': 'src/python/WMCore',
               'WMComponent' : 'src/python/WMComponent',
               'WMQuality' : 'src/python/WMQuality'}

setup (name = 'wmcore',
       version = '1.0',
       maintainer_email = 'hn-cms-wmDevelopment@cern.ch',
       cmdclass = {'test': TestCommand, 
                   'clean': CleanCommand, 
                   'lint': LintCommand,
                   'report': ReportCommand,
                   'coverage': CoverageCommand ,
                   'missing': DumbCoverageCommand },
       package_dir = package_dir,
       packages = getPackages(package_dir.values()),)

