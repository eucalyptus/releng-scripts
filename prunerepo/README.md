prune-rpm-repo
==============

The prune-rpm-repo script walks through one or more directory trees and
removes RPM packages that are older than a certain date or packages where
more than a certain number of versions exist.  A retention policy in a
configuration file controls exactly how long each package is preserved.

SYNOPSIS
--------

``prune-rpm-repo [-nv] [--config FILE] [--debug] DIR ...``

Specify one or more directories for prune-rpm-repo to scan for packages.
It will consider them all at once, not independently -- running it
separately on several directories may preserve more than running it on
all of those directories at once.

### Options ###

``--config``
  location of a configuration file with the retention policy to use
  (see [CONFIGURATION](README.md/#configuration))

``--debug``
  show retention policy matches and other debugging information

``-n``
  don't actually remove packages (passive mode).  This implies ``-v``.

``-v``
  list the files that are deleted

CONFIGURATION
-------------

Configuration files control which packages prune-rpm-repo preserves based
on their modification times, as reported by ``stat(2)``, or by how many
versions of packages with the same name exist in the repository at once.
This is best illustrated with an example:

```YAML
preserve:
  - pattern: .*-image$
    min-versions: 5
  - pattern: eucalyptus
    min-versions: 10
    min-days: 30
  - pattern: .*
    min-versions: 1
    min-days: 90
```

Each of these rules preserves packages that match specific regular
expression patterns.  These patterns only have to match the beginning of
the packages' names, not the entirety, so ``foo`` will match ``foo``,
``foobar``, and ``foo-libs``.  The first rule that matches a package
wins; other rules are not considered regardless of whether or not
they match.  In the example above, only the latest five versions of
``eucalyptus-load-balancer-image`` are preserved, the latest ten versions
of ``eucalyptus-cloud`` packages in addition to those from within the
past 30 days are preserved, and only the latest version and those created
within the past 90 days are preserved for all other packages.

A default ``.*`` rule that preserves 1 million versions and packages less
than 10000 days old is implicitly added unless you provide your own.
This typically amounts to a rule that preserves all packages not matched
by another rule.

INSTALLATION
------------

This project's code consists of a single file that does not require
installation.  It does, however, require PyYAML, which is available from
PyPI and many distributions by that name, and other distributions as
``python-yaml``.

CONTRIBUTING & BUGS
-------------------

This project's source code can be found on GitHub at
http://github.com/eucalyptus/releng-scripts/prune-rpm-repo.  To obtain a copy of the
source code use the following command:

    git clone git://github.com/eucalyptus/releng-scripts

You can also file bugs or pull requests for the project on GitHub.
Please note that by submitting code to this project, you agree that code
will be licensed under the ISC license.  A copy of this license appears
in the [COPYING](COPYING) file that accompanies the source code.
