"""
Sorts out whether command-line input should be going to the local program or the
remote hosts and acts accordingly.
"""

# TODO: output modes (first-host-and-diffs; etc.)


import sys
import pydoc
import StringIO
import textwrap
import traceback

import connections
import config

from utils import sysexits
from utils import terminal


# Debugging!
last_traceback = None


def run_interactive(command = ''):
    """
    Interactive command loop for the dyssh prompt.
    """
    global last_traceback

    if command:
        run(command)

    prompt = config.get('prompt', '').strip() + ' '
    prompt %= {
        'hostname': config.get('local_hostname'),
    }

    while True:
        try:
            command = raw_input(prompt)
            if command.startswith(':'):
                c, _, args = command[1:].partition(' ')
                possibles = []
                for fnc in globals().keys():
                    if fnc.startswith('cmd_'+c):
                        f = globals()[fnc]
                        possibles.append((f, args))
                if len(possibles) > 1:
                    terminal.error(text = 'Command is ambiguous', lvl = 1)
                    cmd_help(*[
                        p[0].__name__[4:] for p in possibles
                    ])
                elif len(possibles) == 1:
                    f, args = possibles[0]
                    args = filter(None, args.split(' '))
                    r = f(*args)
                    if r == sysexits.EX_USAGE:
                        cmd_help(f.__name__[4:])
                    elif r != sysexits.EX_OK:
                        terminal.error(text = "Error issuing command: %s" % r,
                            lvl = 1)
                else:
                    host = connections.conns._gethost(c[1:])
                    if host:
                        cmd_show(host)
                    else:
                        terminal.error(text = 'Invalid command.', lvl = 1)
            elif command:
                run(command)
        except Exception, e:
            last_traceback = traceback.format_exc()
            terminal.error(text = 'Error attempting to execute command: %s' % e,
                lvl = 2)
            print "Enter `:traceback` to print the last error traceback."

    return sysexits.EX_OK


def run(command = ''):
    """
    Run individual commands by passing them to the Connections object. Failures
    should be collected and dealt with here by checking the return codes of
    completed commands.
    """

    if not len(connections.conns.hosts):
        terminal.error(text = 'No hosts specified.')

    connections.conns.run_command_all(command)

    return sysexits.EX_OK


#
# Interactive commands.
#

def cmd_add(*args):
    """
    :add <host>           Add a host to the active host list. Optionally specify
                          more than one host.
    """
    if not args:
        return sysexits.EX_USAGE
    for i in args:
        connections.conns.add(i)
    return sysexits.EX_OK

#
#def cmd_flush(*args):
#
#    return sysexits.EX_OK
#
#
#def cmd_get(*args):
#
#    return sysexits.EX_OK


def cmd_help(*args):
    """
    :help <cmd>           Show interactive command help. <cmd> is optional.
    """
    # Builds the helps string out of the __doc__ strings of all cmd_* functions.
    output = ""
    keys = sorted(globals().keys())
    if len(args):
        keys = filter(lambda x: x[4:] in args, keys)
    for f in keys:
        if f.startswith('cmd_'):
            output += globals()[f].__doc__ or ''
    output = output.split('\n')
    output = filter(lambda x: x.strip(), output)
    output = '\n'.join(output)
    print '\n', textwrap.dedent(output), '\n'
    return sysexits.EX_OK


def cmd_history(*args):
    """
    :history <host>       Show the command history for <host>.
    """
    if len(args) == 1:
        history = connections.conns.get_history(args[0])
        if not history:
            terminal.error(text = "No history available for %s" % args[0])
        else:
            headers = ('', '')
            output = [ ('[%s]'% i, h.get('command')) for i, h in enumerate(history) ]
            print terminal.format_columns(headers, output), '\n'
    else:
        return sysexits.EX_USAGE
    return sysexits.EX_OK


def cmd_join(*args):
    """
    :join <host>          If there is an active command running on <host>,
                          connect to that host in an interactive terminal
                          session. When the session ends (either through exit,
                          disconnect, or error), you will return to the dyssh
                          prompt.
    """
    if len(args) == 1:
        connections.conns.join(args[0])
    else:
        return sysexits.EX_USAGE
    return sysexits.EX_OK


def cmd_kill(*args):
    """
    :kill <host>          Tells the running process for <host> to stop. When it
                          is successfully terminated, the exit status will be
                          set to -1. Note that stopping the local thread that
                          runs the job is not actually guaranteed to stop the
                          process on the remote host (although it should receive
                          a SIGHUP when the SSH session quits).
    """
    if len(args) == 1:
        connections.conns.kill(args[0])
    else:
        return sysexits.EX_USAGE
    return sysexits.EX_OK



def cmd_list(*args):
    """
    :list                 List all hosts in the current hosts list.
    """
    output = []
    for idx, item in enumerate(connections.conns.items()):
        host, hostinfo = item
        output.append((
            '[%s]' % idx,
            host,
            hostinfo.get('connected'),
            hostinfo.get('exitcode')
        ))
    if not len(output):
        terminal.error(text = 'No hosts.')
        return sysexits.EX_OK
    headers = ('', 'Hostname', 'Connected', 'Last exit')
    print '\n', terminal.format_columns(headers, output), '\n'
    return sysexits.EX_OK

#
#def cmd_put(*args):
#
#    return sysexits.EX_OK


def cmd_remove(*args):
    """
    :remove <host>        Remove one or more hosts from the active host list.
                          Optionally specify more than one host.
    """
    if not args:
        return sysexits.EX_USAGE
    for i in args:
        connections.conns.remove(i)
    return sysexits.EX_OK


def cmd_timeout(*args):
    """
    :timeout <seconds>    Seconds to wait for jobs to complete before returning
                          to the interactive prompt. Jobs that time out will
                          continue to operate in the background, and can be
                          checked with either :status or by using :join.
    """
    
    if len(args) == 1 and args[0].isdigit():
        t = float(args[0])
        if t < 0:
            t = 0
        config.config['job_timeout'] = t
        terminal.error(text = "Timeout set to %s seconds" % t)
    else:
        return sysexits.EX_USAGE

    return sysexits.EX_OK

def cmd_show(*args):
    """
    :show <host>          Show the output of the last command for <host>.
    :<host>               A shortcut for `:show <host>`
    """
    if len(args) == 1:
        host = args[0]
        host = connections.conns._gethost(host)
        if not host:
            terminal.error(text = "No such host")
            return sysexits.EX_OK
        history = connections.conns.get_history(host)
        if not history:
            terminal.error(text = "No output available for %s" % host)
        else:
            last_history = history[-1]
            command = last_history.get('command')
            output = last_history.get('output')
            exitcode = last_history.get('exitcode')

            if exitcode is None:
                terminal.error(text = "Command still pending")
                return sysexits.EX_OK
            else:
                # This will block if the process isn't complete
                outlines = output.readlines()
                # Reset the output for later re-reading. If we've already
                # replaced the buffer with a StringIO we can just seek.
                try:
                    output.seek(0)
                except:
                    output = StringIO.StringIO()
                    output.writelines(outlines)
                    output.seek(0)
                last_history['output'] = output
            outstr = ''
            outstr += terminal.errorstr(text = terminal.tocolor(command, 'bold'))
            for line in outlines:
                outstr += terminal.errorstr(
                    '[%s]' % host,
                    line.strip('\n'),
                    1
                )
            outstr += terminal.errorstr(text = 'Exit code: %s' % exitcode)
            outstr = outstr.replace('\r\n', '\n')
            pydoc.pipepager(outstr, config.get('pager'))
    else:
        return sysexits.EX_USAGE

    return sysexits.EX_OK


def cmd_status(*args):
    """
    :status               Show the status of all jobs from the last command.
    """
    if not len(args):
        output = []
        for idx, item in enumerate(connections.conns.status()):
            host, exit_status = item
            if exit_status is None:
                exit_status = '(still pending)'
            elif exit_status is -1:
                exit_status = '-1 (stopped)'
            output.append((
                '[%s]' % idx,
                host,
                exit_status,
            ))
        headers = ('', 'Host', 'Exit code')
        print '\n', terminal.format_columns(headers, output), '\n'
    else:
        return sysexits.EX_USAGE

    return sysexits.EX_OK


def cmd_traceback(*args):
    global last_traceback
    print last_traceback
    return sysexits.EX_OK

#
#def cmd_flush(*args):
#
#    return sysexits.EX_OK
#
#
#def cmd_write(*args):
#
#    return sysexits.EX_OK


def cmd_quit(*args):
    """
    :quit                 Exit interactive mode and quit the program.
    """
    terminal.error(text = 'Stopping any running jobs ...')
    connections.conns.kill_all()
    terminal.error(text = 'Disconnecting from all remote hosts ...')
    connections.conns.disconnect_all()
    sys.exit(sysexits.EX_OK)
