import os
import re
import argparse
import subprocess

# inputs:
#   1. RESULTS_DIR
#   2. CONTENT_DIR
#   3. GPG_KEY_ID
#   4. copy_source(checkbox, true or false)
#   5. copy_debuginfo(checkbox, true or false)
#   5. PROMOTED_NUMBER
#   6. platforms
#   7. architectures???

class Results(object):
    """
    Build a list of all RPMs in results, user will pass in a directory which we build our list from
    """
    def __init__(self, results):
        self.results = results
        self.filedict = {}

    def getresults(self):
        self.filedict = self.handle_directory()
        return self.filedict

    def handle_directory(self):
        srcrpms = [f for f in os.listdir(self.results) if re.match(r'.*src.*rpm', f)]
        debugrpms = [f for f in os.listdir(self.results) if re.match(r'.*debuginfo.*rpm', f)]
        el6rpms = [f for f in os.listdir(self.results) if (re.match(r'.*el6.*rpm', f)
                                                      and not re.match(r'.*debuginfo.*rpm', f)
                                                      and not re.match(r'.*src.*rpm', f))]
        el7rpms = [f for f in os.listdir(self.results) if (re.match(r'.*el7.*rpm', f)
                                                      and not re.match(r'.*debuginfo.*rpm', f)
                                                      and not re.match(r'.*src.*rpm', f))]

        if srcrpms:
            if debug:
                print "found the following src rpms: {0}".format(srcrpms)
        if el6rpms:
            if debug:
                print "found the following el6 rpms: {0}".format(el6rpms)
        if el7rpms:
            if args.debug:
                print "found the following el7 rpms: {0}".format(el7rpms)
        if debugrpms:
            if args.debug:
                print "found the following debuginfo rpms: {0}".format(debugrpms)

        self.filedict['srcrpms'] = srcrpms
        self.filedict['el6rpms'] = el6rpms
        self.filedict['el7rpms'] = el7rpms
        self.filedict['debugrpms'] = debugrpms

        return self.filedict

def pretty(d, indent=0):
    for key, value in d.iteritems():
        print '\t' * indent + str(key)
        if isinstance(value, dict):
            pretty(value, indent+1)
        else:
            print '\t' * (indent+1) + str(value)

class Artifactory(object):
    """
    Handle all artifact operations

    This includes:
    1. creating directory structure
    2. signing RPMs
    3. copying to Yum repo location
    """
    def __init__(self, platforms, results, gpg_key_id, promoted_num, copy_source, copy_debuginfo):
        self.platforms = platforms
        self.results = results
        self.gpg_key_id = gpg_key_id
        self.promoted_num = promoted_num
        self.copy_source = copy_source
        self.copy_debuginfo = copy_debuginfo

    def create_pkg_dirs(self):
        for ver in [6, 7]:
            print "version: {0}".format(ver)
            path = 'packages/rhel/' + str(ver)
            if not os.path.exists(path):
                print "creating dir: " + path
                os.makedirs(path)
            for tree in ['x86_64', 'source']:
                print "dir: " + tree
                if not os.path.exists(path + '/' + tree):
                    print "creating dir: " + path + '/' + tree
                    os.makedirs(path + '/' + tree)

    def create_links(self, mydict):
        path = None
        item = None
        arch = "x86_64"

        for key, value in mydict.iteritems():
            if key is "srcrpms" and copy_source is not False:
                print "working on srcrpms"
                for item in value:
                    #print "item: " + item
                    for ver in [6, 7]:
                        el = "el" + str(ver)
                        if el in item:
                            path = "packages/rhel/" + str(ver) + "/source" + "/" + item
                            print "os.link(" + results + item + ', ' + path + ')'
                            os.link(results + item, path)
            if key is "debugrpms" and copy_debuginfo is not False:
                print "working on debugrpms"
                for item in value:
                   #print "item: " + item
                    for ver in [6, 7]:
                        el = "el" + str(ver)
                        if el in item:
                            path = "packages/rhel/" + str(ver) + "/" + arch + "/" + item
                            print "os.link(" + results + item + ', ' + path + ')'
                            os.link(results + item, path)
            if key is "el6rpms":
                    print "working on el6rpms"
                    for item in value:
                        path = "packages/rhel/6/" + arch + "/" + item
                        print "os.link(" + results + item + ', ' + path + ')'
                        os.link(results + item, path)
            if key is "el7rpms":
                    print "working on el7rpms"
                    for item in value:
                        print "item: " + item
                        path = "packages/rhel/7/" + arch + "/" + item
                        print "os.link(" + results + item + ', ' + path + ')'
                        os.link(results + item, path)

    def createrepo(self):
        print "in createrepo"
        for ver in [6, 7]:
            for dir in ['source', 'x86_64']:
                path = "packages/rhel/" + str(ver) +  "/" + dir
                args = [ '/usr/bin/createrepo', '--no-database', path ]
                print "running /usr/bin/createrepo --no-database" + path
                subprocess.check_call(args)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--no_copy_source", action="store_false",
                        help="toggle copying source RPMs to Yum repo (default=true)")
    parser.add_argument("-g", "--no_copy_debuginfo", action="store_false",
                        help="toggle copying debuginfo RPMs to Yum repo (default=true)")
    parser.add_argument("--debug", default=False, action='store_true')

    args = parser.parse_args()

    debug = args.debug
    copy_source = args.no_copy_source
    copy_debuginfo = args.no_copy_debuginfo

    results = os.getenv('RESULTS_DIR')
    content = os.environ.get('CONTENT_DIR')
    platforms = os.environ.get('platforms')
    gpg_key_id = os.environ.get('GPG_KEY_ID')
    promoted_num = os.environ.get('PROMOTED_NUMBER')

    if not results:
        raise ValueError("Environment variable not set: RESULTS_DIR")
    if not content:
        raise ValueError("Environment variable not set: CONTENT_DIR")
    if not platforms:
        raise ValueError("Environment variable not set: platforms")
    #if not promoted_num:
    #    raise ValueError("Environment variable not set: PROMOTED_NUMBER")

    resobj = Results(results)
    rpmdict = resobj.getresults()

    print "\nprinting dict:\n"
    pretty(rpmdict)

    afobj = Artifactory(platforms, results, gpg_key_id, promoted_num, copy_source, copy_debuginfo)
    afobj.create_pkg_dirs()
    afobj.create_links(rpmdict)
    afobj.createrepo()
