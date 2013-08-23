"""
Managing connections to remote hosts. The main workhorse of this module is the
Connections class. When the program starts, an instance of this class is
initialized and placed into the 'conns' variable in this module, so that all
other modules can reference that instance.
"""

# TODO: detect wait for data from stdin and create interface for that.

import datetime
import paramiko
import select
import socket
import StringIO
import sys
import termios
import time
import tty

try:
    import multiprocessing
    Process = multiprocessing.Process
except:
    import threading
    Process = threading.Thread

import config

class Connections(object):
    """
    Class for managing the connections to all hosts through a single interface.
    """

    def __init__(self,
        host_list,
        info_output = lambda x: x,
        error_output = lambda x: x,
        debug_level = 0
    ):
        self.hosts = host_list
        self.hconn = {}
        self.info_output = info_output
        self.error_output = error_output
        self.debug = debug_level
        self.connect_all()
        self.killorders = {}
        
    def deltest(self):
        self.__del__()


    def _error(self, msg, lvl = -10):
        """
        Log error output using the function set with __init__().
        """
        if lvl <= self.debug:
            self.error_output(msg)


    def _gethost(self, host_name_or_number):
        """
        Given the host name or the index in the host list, return the actual
        key name being used internally by the Connections object. Returns `None`
        if the host doesn't exist.
        """
        host_name_or_number = str(host_name_or_number)
        if host_name_or_number.isdigit():
            idx = int(host_name_or_number)
            lsh = len(self.hosts)
            if lsh > idx and (0 - lsh) < idx:
                return self.hosts[idx]
        else:
            if host_name_or_number in self.hosts:
                return host_name_or_number
            else:
                possibles = []
                for h in self.hosts:
                    if host_name_or_number in h:
                        possibles.append(h)
                if len(possibles) > 1:
                    self._info("Host name is ambiguous")
                elif len(possibles) == 1:
                    return possibles[0]


    def _info(self, msg, lvl = 0):
        """
        Log informational/debug output using the function set with __init__().
        """
        if lvl <= self.debug:
            self.info_output(msg)


    def add(self, host):
        """
        Add <host> to the list of managed hosts. <host> may be either the host
        name or index.
        """
        if not host in self.hosts:
            self.hosts.append(host)
            self.connect(host)
        else:
            self._info('%s already in host list' % host)


    def clear_history(self, h):
        """
        Clear the command history of <host>.
        """
        host = self._gethost(h)
        if host:
            self.hconn[host]['history'] = []
        else:
            self._info("No such host in list: %s" % h)


    def clear_history_all(self):
        """
        Clear the command history of all hosts.
        """
        for host in self.hosts:
            self.clear_history(host)
            

    def connect(self, host):
        """
        Connect to a single host.
        """
        host = self._gethost(host)

        if not host:
            self._error("Connections.connect: Invalid host: %s" % host)
            return

        self.test(host)

        if not host in self.hconn.keys():
            self.hconn[host] = {}

        if not self.hconn.get(host, {}).get('connected'):

            if config.get('auto_add_hosts'):
                host_policy = paramiko.AutoAddPolicy
            else:
                host_policy = paramiko.RejectPolicy

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(host_policy())

            self._info('Connecting to %s' % host)

            try:

                client.load_system_host_keys()

                username = config.get('username')
                password = config.get('password')
                # If the hostname has been specified with non-default
                # connection details, use those.
                if '@' in host:
                    user_spec, _, host_spec = host.partition('@')
                else:
                    user_spec = ''
                    host_spec = host
                if user_spec:
                    username, _, password = user_spec.partition(':')
                hostname, _, port = host_spec.partition(':')
                client.connect(
                    hostname,
                    port or config.get('port'),
                    username,
                    password
                )
                connected = True
                e = None

            # Covers SSH connection issues, failed loading of host keys, or bad
            # hostnames
            except (paramiko.SSHException, IOError, socket.gaierror), e:
                # Note the connection failure, but we will still try to
                # connect to the rest of the hosts.
                self._error("Connecting to host %s failed: %s" % (host, e))
                connected = False

            self.hconn[host].update({
                'client': client,
                'connected': connected,
                'error': e
            })


    def connect_all(self):
        """
        Connect to any hosts that are disconnected.
        """
        for host in self.hosts:
            self.connect(host)


    def disconnect(self, host):
        """
        Disconnect a single host.
        """

        self.test(host)

        hostinfo = self.hconn.get(host, {})

        if hostinfo.get('connected'):

            client = hostinfo.get('client')
            client.close()
            self._info('Connection to host %s closed.' % host)


    def disconnect_all(self):
        """
        Disconnect from any hosts that are connected.
        """
        for host in self.hosts:
            self.disconnect(host)


    def get_history(self, host):
        """
        Get the command history for <host>.
        """
        host = self._gethost(host)
        if host in self.hconn.keys():
            return self.hconn[host].get('history')


    def items(self):
        """
        Return a list of (<host>, <hostinfo>) pairs, in the order they were
        added.
        """
        out = []
        for i in self.hosts:
            out.append((i, self.hconn.get(i)))
        return out


    def join(self, h):
        """
        Creates an interactive session with the pseudo-terminal running the job
        on <host>. Useful for resolving hung processes.

        This is based on the examples from the demos in the paramiko source,
        which can be found here:
        https://github.com/paramiko/paramiko/blob/60c6e94e7dd6d7ac65c88ce1231f55d311777a34/demos/interactive.py
        """
        host = self._gethost(h)
        if host:
            history = self.get_history(host)[-1]
            if history.get('exitcode') is -1:
                self._info("No pending job on %s" % host)
                return
            chan = history.get('chan')
            oldtty = termios.tcgetattr(sys.stdin)
            try:
                tty.setraw(sys.stdin.fileno())
                tty.setcbreak(sys.stdin.fileno())
                chan.settimeout(0.0)
                output = history.get('output')
                # output from before we `:join`ed the process
                if output:
                    oldoutput = ''
                    try:
                        while True:
                            o = output.read(1)
                            sys.stdout.write(o)
                            oldoutput += o
                    except socket.timeout:
                        pass
                while True:
                    r = select.select([chan, sys.stdin], [], [])[0]
                    if chan in r:
                        try:
                            x = chan.recv(1024)
                            if len(x) == 0:
                                oldoutput += '\n'
                                print ''
                                break
                            sys.stdout.write(x)
                            sys.stdout.flush()
                            oldoutput += x
                        except socket.timeout:
                            pass
                    if sys.stdin in r:
                        x = sys.stdin.read(1)
                        if len(x) == 0:
                            break
                        chan.send(x)
                        oldoutput += x
                if output:
                    # Set the output buffer back up so that we have it in the
                    # history
                    output = StringIO.StringIO()
                    output.write(oldoutput)
                    output.seek(0)
                    self.hconn[host]['history'][-1]['output'] = output
            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)
        else:
            self._info("No such host in list: %s" % h)


    def kill(self, h):
        """
        Stop the background thread for <host> if it is running.
        """
        host = self._gethost(h)
        status = dict(self.status())
        if host:
            if status.get(host) is None:
                self.killorders[host] = True
                self._info('Requested stop for job on %s' % host)
            else:
                self._info('%s has no pending jobs.' % host)
        else:
            self._info("No such host in list: %s" % h)


    def kill_all(self):
        """
        Stop any still-processing background threads.
        """
        for host in self.hosts:
            self.kill(host)


    def remove(self, h):
        """
        Remove <host> from the list of managed hosts. <host> may be either the
        host name or index.
        """
        host = self._gethost(h)
        if host:
            self.disconnect(host)
            self.hosts = filter(lambda x: x != host, self.hosts)
            if host in self.hconn.keys():
                del self.hconn[host]
        else:
            self._info("No such host in list: %s" % h)


    def run_command(self, host, command):
        """
        Run <command> on a single host.
        """

        self.test(host)
        hostinfo = self.hconn.get(host, {})

        if not 'history' in hostinfo.keys():
            hostinfo['history'] = []

        # Require a connection to continue. We will allow the user to interrupt
        # this and drop the host if they don't want to wait forever.
        if not hostinfo.get('connected'):
            self._info(
                'Host %s disconnected. Attempting automatic reconnection' % host
            )
            self.connect(host)
            if not hostinfo.get('connected'):
                self._error("Reconnection attempt to %s failed" % host)
                return

        client = self.hconn[host]['client']
        chan = client.get_transport().open_session()
        chan.get_pty()
        bufsize = -1

        stdin = chan.makefile('wb', bufsize)
        output = chan.makefile('rb', bufsize)
        chan.exec_command(command)
        
        history = {
            'output': output,
            'stdin': stdin,
            'exitcode': None,
            'timestamp': datetime.datetime.now(),
            'command': command,
            'chan': chan
        }
        self.hconn[host]['history'].append(history)

        # wait for completion
        while not chan.exit_status_ready():
            # check to see if a stop has been ordered
            if self.killorders.get(host):
                self.killorders[host] = None
                history['exitcode'] = -1
                chan.close()
                return

        history['exitcode'] = chan.recv_exit_status()


    def run_command_all(self, command):
        """
        Run <command> on each host. Adds the return values to the command
        history for that host.
        """

        self.jobs = []
        for host in self.hosts:
            self._info("Starting job on %s" % host)
            p = Process(target = self.run_command, args = (host, command))
            self.jobs.append((host, p))
            p.start()

        for host, p in self.jobs:
            time.sleep(config.get('job_timeout') or 0)
            isalive = p.isAlive() if hasattr(p, 'isAlive') else p.is_alive()
            if not isalive:
                self._info("Job on %s finished" % host)
            else:
                self._info("Job on %s still pending" % host)
                continue
            history = self.get_history(host)[-1]
            exitcode = history.get('exitcode')
            if exitcode is not 0:
                self._error("Error running job on %s (exit code %s)" % \
                    (host, exitcode))


    def status(self):
        """
        Get the status of the last job on each host, as a list of tuples in the
        format (host, exit_status)
        """
        r = []
        for host in self.hosts:
            history = self.get_history(host)[-1]
            r.append((host, history.get('exitcode')))
        return r


    def test(self, host):
        """
        Test whether the connection to <host> is still active and working.
        """
        
        hostinfo = self.hconn.get(host, {})

        if hostinfo.get('connected'):

            client = hostinfo.get('client')
            self._info('Testing host %s' % host)

            try:

                transport = client.get_transport()
                if not transport.active:
                    self._info('Host %s is not connected' % host)

                self._info('Host %s is connected' % host)

            except Exception, e: #?
                self.hconn[host].update({
                    'connected': False,
                    'error': e,
                    'chan': None,
                })


    def test_all(self):
        """
        Test supposedly open connections and make sure they are still alive.
        """

        for host in self.hosts:
            self.test(host)


conns = None # Initialized in __init__.py

def set(c):
    """
    Used by __init__.py to set the conns object in this module.
    """
    global conns
    conns = c