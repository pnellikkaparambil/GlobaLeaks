# -*- coding: UTF-8
# settings: Define GLSettings, main class handling GlobaLeeaks runtime settings
# ******
from __future__ import print_function

import getpass
import glob
import grp
import logging
import os
import pwd
import re
from distutils import dir_util # pylint: disable=no-name-in-module
from optparse import OptionParser
from twisted.python.threadpool import ThreadPool

from cyclone.util import ObjectDict as OD

from globaleaks import __version__, DATABASE_VERSION
from globaleaks.utils.singleton import Singleton

this_directory = os.path.dirname(__file__)

possible_client_paths = [
    '/var/globaleaks/client',
    '/usr/share/globaleaks/client/',
    os.path.abspath(os.path.join(this_directory, '../../client/build/')),
    os.path.abspath(os.path.join(this_directory, '../../client/app/'))
]

verbosity_dict = {
    # do not exist anything above DEBUG, so is used a -1)
    'TIMEDEBUG': (logging.DEBUG - 1),
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

external_counted_events = {
    'new_submission': 0,
    'finalized_submission': 0,
    'anon_requests': 0,
    'file_uploaded': 0,
}


class GLSettingsClass(object):
    __metaclass__ = Singleton

    def __init__(self):
        # command line parsing utils
        self.parser = OptionParser()
        self.cmdline_options = None

        # version
        self.version_string = __version__

        # testing
        # This variable is to be able to hook/bypass code when unit-tests are runned
        self.testing = False

        # daemon
        self.nodaemon = False

        # thread pool size of 1
        self.orm_tp = ThreadPool(1, 1)

        self.bind_addresses = '127.0.0.1'

        # bind port
        self.bind_port = 8082

        # store name
        self.store_name = 'main_store'

        self.db_type = 'sqlite'
        self.initialize_db = True

        # debug defaults
        self.orm_debug = False
        self.log_requests_responses = -1
        self.requests_counter = 0
        self.loglevel = "CRITICAL"

        # files and paths
        self.root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.pid_path = '/var/run/globaleaks'
        self.working_path = '/var/globaleaks'

        self.client_path = '/usr/share/globaleaks/client'
        for path in possible_client_paths:
            if os.path.exists(path):
                self.client_path = path
                break

        self.set_ramdisk_path()

        self.authentication_lifetime = 3600
        self.RecentEventQ = []
        self.RecentAnomaliesQ = {}

        self.accept_submissions = True

        # statistical, referred to latest period
        # and resetted by session_management sched
        self.failed_login_attempts = 0

        # static file rules
        self.staticfile_regexp = r'(.*)'
        self.staticfile_overwrite = False

        # acceptable 'Host:' header in HTTP request
        self.accepted_hosts = "127.0.0.1, localhost"
        self.tor_address = None

        self.receipt_regexp = u'[0-9]{16}'

        # A lot of operations performed massively by globaleaks
        # should avoid to fetch continuously variables from the DB so that
        # it is important to keep this variables in memory
        #
        # Initialization is handled by db_refresh_memory_variables
        self.memory_copy = OD({
            'maximum_namesize': 128,
            'maximum_textsize': 4096,
            'maximum_filesize': 30,
            'allow_iframes_inclusion': False,
            'accept_tor2web_access': {
                'admin': True,
                'whistleblower': False,
                'custodian': False,
                'receiver': False,
                'unauth': True,
            },
        })


        # Default request time uniform value
        self.side_channels_guard = 0.150

        # SOCKS default
        self.socks_host = "127.0.0.1"
        self.socks_port = 9050

        self.notification_limit = 30
        self.jobs_operation_limit = 20

        self.user = getpass.getuser()
        self.group = getpass.getuser()
        self.uid = os.getuid()
        self.gid = os.getgid()
        self.start_clean = False
        self.devel_mode = False
        self.developer_name = ''
        self.disable_swap = False
        self.skip_wizard = False
        self.log_timing_stats = False

        # Number of failed login enough to generate an alarm
        self.failed_login_alarm = 5

        # Number of minutes in which a user is prevented to login in case of triggered alarm
        self.failed_login_block_time = 5

        # Alarm to be ignored: can be raise with the -A command line switch
        self.disk_alarm_threshold = 0

        # Limit for log sizes and number of log files
        # https://github.com/globaleaks/GlobaLeaks/issues/1578
        self.log_size = 10000000 # 10MB
        self.log_file_size = 1000000 # 1MB
        self.num_log_files = self.log_size / self.log_file_size

        # size used while streaming files
        self.file_chunk_size = 65535 # 1MB

        self.AES_key_size = 32
        self.AES_key_id_regexp = u'[A-Za-z0-9]{16}'
        self.AES_counter_nonce = 128 / 8
        self.AES_file_regexp = r'(.*)\.aes'
        self.AES_file_regexp_comp = re.compile(self.AES_file_regexp)
        self.AES_keyfile_prefix = "aeskey-"

        self.exceptions = {}
        self.exceptions_email_count = 0
        self.exceptions_email_hourly_limit = 20

        self.disable_mail_torification = False
        self.disable_mail_notification = False
        self.disable_backend_exception_notification = False
        self.disable_client_exception_notification = False

        self.enable_input_length_checks = True

        self.mail_counters = {}
        self.mail_timeout = 15 # seconds
        self.mail_attempts_limit = 3 # per mail limit

    def get_mail_counter(self, receiver_id):
        return self.mail_counters.get(receiver_id, 0)

    def increment_mail_counter(self, receiver_id):
        self.mail_counters[receiver_id] = self.mail_counters.get(receiver_id, 0) + 1

    def eval_paths(self):
        self.config_file_path = '/etc/globaleaks'
        self.pidfile_path = os.path.join(self.pid_path, 'globaleaks.pid')
        self.files_path = os.path.abspath(os.path.join(self.working_path, 'files'))

        self.db_path = os.path.abspath(os.path.join(self.working_path, 'db'))
        self.log_path = os.path.abspath(os.path.join(self.working_path, 'log'))
        self.submission_path = os.path.abspath(os.path.join(self.files_path, 'submission'))
        self.tmp_upload_path = os.path.abspath(os.path.join(self.files_path, 'tmp'))
        self.static_path = os.path.abspath(os.path.join(self.files_path, 'static'))
        self.static_db_source = os.path.abspath(os.path.join(self.root_path, 'globaleaks', 'db'))
        self.torhs_path = os.path.abspath(os.path.join(self.working_path, 'torhs'))

        self.db_schema = os.path.join(self.static_db_source, 'sqlite.sql')
        self.db_file_name = 'glbackend-%d.db' % DATABASE_VERSION
        self.db_file_path = os.path.join(os.path.abspath(os.path.join(self.db_path, self.db_file_name)))
        self.db_uri = self.make_db_uri(self.db_file_path)

        self.logfile = os.path.abspath(os.path.join(self.log_path, 'globaleaks.log'))
        self.httplogfile = os.path.abspath(os.path.join(self.log_path, "http.log"))

        # gnupg path is used by PGP as temporary directory with keyring and files encryption.
        self.pgproot = os.path.abspath(os.path.join(self.ramdisk_path, 'gnupg'))

        # If we see that there is a custom build of GLClient, use that one.
        custom_client_path = '/var/globaleaks/client'
        if os.path.exists(custom_client_path):
            self.client_path = custom_client_path

        self.appdata_file = os.path.join(self.client_path, 'data/appdata.json')
        self.fields_path = os.path.join(self.client_path, 'data/fields')
        self.field_attrs_file = os.path.join(self.client_path, 'data/field_attrs.json')

    def set_ramdisk_path(self):
        self.ramdisk_path = '/dev/shm/globaleaks'
        if not os.path.isdir('/dev/shm'):
            self.ramdisk_path = os.path.join(self.working_path, 'ramdisk')

    def set_devel_mode(self):
        self.devel_mode = True

        # is forced by -z, but unitTest has not:
        if not self.cmdline_options:
            self.developer_name = u"Random GlobaLeaks Developer"
        else:
            self.developer_name = unicode(self.cmdline_options.developer_name)

        self.pid_path = os.path.join(self.root_path, 'workingdir')
        self.working_path = os.path.join(self.root_path, 'workingdir')

        self.set_ramdisk_path()

    def set_client_path(self, glcp):
        self.client_path = os.path.abspath(os.path.join(self.root_path, glcp))

    def enable_debug_mode(self):
        import signal

        def start_pdb(signal, trace):
            import pdb

            pdb.set_trace()

        signal.signal(signal.SIGQUIT, start_pdb)

    def validate_tor_dir_struct(self, tor_dir):
        """
        Return False instead of quit(-1) because at the startup this struct
        can in fact be empty
        """
        if not os.path.isdir(tor_dir):
            self.print_msg("Invalid directory provided as -D argument (%s)" % self.cmdline_options.tor_dir)
            return False

        hostname_tor_file = os.path.join(tor_dir, 'hostname')
        if not os.path.isfile(hostname_tor_file):
            self.print_msg("Not found 'hostname' file as expected in Tor dir (-D %s): skipped" % tor_dir)
            return False

        return True

    def load_cmdline_options(self):
        """
        This function is called by runner.py and operate in cmdline_options,
        interpreted and filled in bin/startglobaleaks script.

        happen in startglobaleaks before the sys.argv is modified
        """
        self.nodaemon = self.cmdline_options.nodaemon

        if self.cmdline_options.disable_swap:
            self.disable_swap = True

        self.loglevel = verbosity_dict[self.cmdline_options.loglevel]

        self.bind_addresses = list(set(['127.0.0.1'] + self.cmdline_options.ip.replace(" ", "").split(",")))

        if not self.validate_port(self.cmdline_options.port):
            quit(-1)
        self.bind_port = self.cmdline_options.port

        self.accepted_hosts = list(set(self.bind_addresses + \
                                   self.cmdline_options.host_list.replace(" ", "").split(",")))

        self.disable_mail_torification = self.cmdline_options.disable_mail_torification
        self.disable_mail_notification = self.cmdline_options.disable_mail_notification
        self.disable_backend_exception_notification = self.cmdline_options.disable_backend_exception_notification
        self.disable_client_exception_notification = self.cmdline_options.disable_client_exception_notification

        if self.cmdline_options.disk_alarm_threshold:
            self.disk_alarm_threshold = self.cmdline_options.disk_alarm_threshold

        self.socks_host = self.cmdline_options.socks_host

        if not self.validate_port(self.cmdline_options.socks_port):
            quit(-1)
        self.socks_port = self.cmdline_options.socks_port

        self.side_channels_guard = self.cmdline_options.side_channels_guard / 1000.0

        if self.cmdline_options.ramdisk:
            self.ramdisk_path = self.cmdline_options.ramdisk

        if self.cmdline_options.tor_dir and self.validate_tor_dir_struct(self.cmdline_options.tor_dir):
            hostname_tor_file = os.path.join(self.cmdline_options.tor_dir, 'hostname')

            if not os.access(hostname_tor_file, os.R_OK):
                self.print_msg("Tor HS file in %s cannot be read" % hostname_tor_file)
                quit(-1)

            with file(hostname_tor_file, 'r') as htf:
                self.tor_address = htf.read(22)

        if self.cmdline_options.user and self.cmdline_options.group:
            self.user = self.cmdline_options.user
            self.group = self.cmdline_options.group
            self.uid = pwd.getpwnam(self.cmdline_options.user).pw_uid
            self.gid = grp.getgrnam(self.cmdline_options.group).gr_gid
        elif self.cmdline_options.user:
            # user selected: get also the associated group
            self.user = self.cmdline_options.user
            self.uid = pwd.getpwnam(self.cmdline_options.user).pw_uid
            self.gid = pwd.getpwnam(self.cmdline_options.user).pw_gid
        elif self.cmdline_options.group:
            # group selected: keep the current user
            self.group = self.cmdline_options.group
            self.gid = grp.getgrnam(self.cmdline_options.group).gr_gid
            self.uid = os.getuid()

        if self.uid == 0 or self.gid == 0:
            self.print_msg("Invalid user: cannot run as root")
            quit(-1)

        self.start_clean = self.cmdline_options.start_clean

        if self.cmdline_options.working_path:
            self.working_path = self.cmdline_options.working_path

        if self.cmdline_options.developer_name:
            self.print_msg("Enabling development mode for %s" % self.cmdline_options.developer_name)
            self.developer_name = unicode(self.cmdline_options.developer_name)
            self.set_devel_mode()
            self.orm_debug = self.cmdline_options.orm_debug
            self.log_timing_stats = self.cmdline_options.log_timing_stats
            self.log_requests_responses = self.cmdline_options.log_requests_responses

        self.skip_wizard = self.cmdline_options.skip_wizard

        self.api_prefix = self.cmdline_options.api_prefix

        if self.cmdline_options.client_path:
            self.set_client_path(self.cmdline_options.client_path)

        self.eval_paths()

        # special evaluation of client directory:
        indexfile = os.path.join(self.client_path, 'index.html')
        if os.path.isfile(indexfile):
            self.print_msg("Serving the client from directory: %s" % self.client_path)
        else:
            self.print_msg("Unable to find a directory where to load the client")
            quit(-1)

    def validate_port(self, inquiry_port):
        if inquiry_port >= 65535 or inquiry_port < 0:
            self.print_msg("Invalid port number ( > than 65535 can't work! )")
            return False
        return True

    def create_directory(self, path):
        """
        Create the specified directory;
        Returns True on success, False if the directory was already existing
        """
        if not os.path.exists(path):
            try:
                os.mkdir(path)
            except OSError as excep:
                self.print_msg("Error in creating directory: %s (%s)" % (path, excep.strerror))
                raise excep

            return True

        return False

    def create_directories(self):
        """
        Execute some consistency checks on command provided Globaleaks paths

        if one of working_path or static path is created we copy
        here the static files (default logs, and in the future pot files for localization)
        because here stay all the files needed by the application except the python scripts
        """
        for dirpath in [self.working_path,
                        self.db_path,
                        self.files_path,
                        self.submission_path,
                        self.tmp_upload_path,
                        self.torhs_path,
                        self.log_path,
                        self.ramdisk_path,
                        self.static_path]:
            self.create_directory(dirpath)

    def check_directories(self):
        for path in (self.working_path, self.root_path, self.client_path,
                     self.files_path, self.static_path, self.submission_path, self.log_path):
            if not os.path.exists(path):
                raise Exception("%s does not exist!" % path)

        # Directory with Write + Read access
        for rdwr in (self.working_path,
                     self.files_path, self.static_path, self.submission_path, self.log_path):
            if not os.access(rdwr, os.W_OK | os.X_OK):
                raise Exception("write capability missing in: %s" % rdwr)

        # Directory in Read access
        for rdonly in (self.root_path, self.client_path):
            if not os.access(rdonly, os.R_OK | os.X_OK):
                raise Exception("read capability missing in: %s" % rdonly)

    def fix_file_permissions(self, path=None):
        """
        Recursively updates file permissions on a given path.
        UID and GID default to -1, and mode is required
        """
        if not path:
            path = self.working_path

        # we need to avoid changing permissions to torhs directory and its files
        if path == os.path.join(self.working_path, 'torhs'):
            return

        try:
            if path != self.working_path:
                os.chown(path, self.uid, self.gid)
                os.chmod(path, 0700)
        except Exception as excep:
            self.print_msg("Unable to update permissions on %s: %s" % (path, excep))
            quit(-1)

        for item in glob.glob(path + '/*'):
            if os.path.isdir(item):
                self.fix_file_permissions(item)
            else:
                try:
                    os.chown(item, self.uid, self.gid)
                    os.chmod(item, 0700)
                except Exception as excep:
                    self.print_msg("Unable to update permissions on %s: %s" % (item, excep))
                    quit(-1)

    def remove_directories(self):
        if os.path.exists(self.working_path):
            dir_util.remove_tree(self.working_path, 0)

    def drop_privileges(self):
        if os.getgid() != self.gid:
            try:
                self.print_msg("switching group privileges since %d to %d" % (os.getgid(), self.gid))
                os.setgid(self.gid)
            except OSError as droperr:
                self.print_msg("unable to drop group privileges: %s" % droperr.strerror)
                quit(-1)

        if os.getuid() != self.uid:
            try:
                self.print_msg("switching user privileges since %d to %d" % (os.getuid(), self.uid))
                os.setuid(self.uid)
            except OSError as droperr:
                self.print_msg("unable to drop user privileges: %s" % droperr.strerror)
                quit(-1)

    def print_msg(self, *args):
        if not self.testing:
            print(*args)

    def cleaning_dead_files(self):
        """
        This function is called at the start of GlobaLeaks, in
        bin/globaleaks, and checks if the file present in
        temporally_encrypted_dir
            (XXX change submission now used to too much thing)
        """

        # temporary .aes files must be simply deleted
        for f in os.listdir(GLSettings.tmp_upload_path):
            path = os.path.join(GLSettings.tmp_upload_path, f)
            self.print_msg("Removing old temporary file: %s" % path)

            try:
                os.remove(path)
            except OSError as excep:
                self.print_msg("Error while evaluating removal for %s: %s" % (path, excep.strerror))

        # temporary .aes files with lost keys can be deleted
        # while temporary .aes files with valid current key
        # will be automagically handled by delivery sched.
        keypath = os.path.join(self.ramdisk_path, GLSettings.AES_keyfile_prefix)

        for f in os.listdir(GLSettings.submission_path):
            path = os.path.join(GLSettings.submission_path, f)
            try:
                result = GLSettings.AES_file_regexp_comp.match(f)
                if result is not None:
                    if not os.path.isfile("%s%s" % (keypath, result.group(1))):
                        self.print_msg("Removing old encrypted file (lost key): %s" % path)
                        os.remove(path)
            except Exception as excep:
                self.print_msg("Error while evaluating removal for %s: %s" % (path, excep))

    @staticmethod
    def make_db_uri(db_file_path):
        return 'sqlite:' + db_file_path + '?foreign_keys=ON'

# GLSettings is a singleton class exported once
GLSettings = GLSettingsClass()
