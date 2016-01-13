# (c) Copyright 2015-2016 Hewlett Packard Enterprise Development Company LP
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import datetime
import os
from os.path import basename, splitext, isdir, isfile
import shutil
import sys
import tempfile
import urllib

DEFAULT_SITE_CONFIG    = '/etc/mock/site-defaults.cfg'
DEFAULT_LOGGING_CONFIG = '/etc/mock/logging.ini'


class MockTemp(object):
    def __init__(self, logging, mock_opts=[]):
        # Create mock tempfiles
        self.logging = logging
        self.mock_opts = mock_opts
        self.config_tempdir = None
        self.config_tempfile = None

    def apply_config(self, config):
        self.cleanup()
        self.config = config
        self.config_tempdir = tempfile.mkdtemp(prefix='rpmfab-', dir='/tmp')
        self.config_tempfile = tempfile.NamedTemporaryFile(
            prefix='mock-', suffix='.cfg', dir=self.config_tempdir)

        # Write config file data to temp file
        self.logging.info("reading config file '%s'" % (self.config))
        config_file = urllib.urlopen(self.config)
        self.config_tempfile.write(config_file.read())
        self.config_tempfile.flush()
        config_file.close()
        self.logging.info("created temporary mock config '{0}'"
                          .format(self.config_tempfile.name))

        # Add default config files
        if isfile(DEFAULT_SITE_CONFIG):
            shutil.copy2(DEFAULT_SITE_CONFIG, self.config_tempdir)
        else:
            MockTemp._generate_default_config(self.config_tempdir)
        if isfile(DEFAULT_LOGGING_CONFIG):
            shutil.copy2(DEFAULT_LOGGING_CONFIG, self.config_tempdir)
        else:
            shutil.copy2('logging.ini', self.config_tempdir)

        MockTemp._set_old_filetime(self.config_tempfile.name)
        MockTemp._set_old_filetime(os.path.join(self.config_tempdir,
                                                'logging.ini'))
        MockTemp._set_old_filetime(os.path.join(self.config_tempdir,
                                                'site-defaults.cfg'))

        # Must set configdir to find temporary mock config file
        # Inserting at the front since newer versions of mock
        # require this.
        self.mock_opts.insert(0, '--configdir')
        self.mock_opts.insert(1, self.config_tempdir)
        self.chroot = splitext(basename(self.config_tempfile.name))[0]

    def cleanup(self):
        if self.config_tempfile:
            self.config_tempfile.close()
        if self.config_tempdir:
            shutil.rmtree(self.config_tempdir)

    @staticmethod
    def _set_old_filetime(file):
        """
        Set file time to a week ago.
        This should prevent mock from always rebuilding the cache.
        """
        today = datetime.date.today()
        week_ago = today - datetime.timedelta(weeks=1)
        utime_secs = week_ago.strftime('%s.%f')
        os.utime(file, (float(utime_secs), float(utime_secs)))

    @staticmethod
    def _generate_default_config(dir):
        config_filename = os.path.join(dir, 'site-defaults.cfg')
        f = open(config_filename, 'wb')
        f.write("""# Generated config file
# DO NOT EDIT
config_opts['plugin_conf']['yum_repo_enable'] = True
    """)
        f.close()
        return config_filename
