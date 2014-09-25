"""
Sorts out whether command-line input should be going to the local program or the
remote hosts and acts accordingly.
"""

# TODO: output modes (first-host-and-diffs; etc.)
# TODO: :hold <host> / :hold pending / :hold all and :resume commands to stop
#       sending commands to one, still processing, or all hosts. :resume is
#       exactly the same, it just does the reverse.

import sys
import os
import pydoc
import signal
import StringIO
import textwrap
import traceback

import connections
import config
import ui

from utils import terminal

# Debugging!
last_traceback = None

def abort(signum, frame):
    raise Exception('Abort signal received.')


# Swallow CTRL-C in interactive mode
UI_SIGNAL_HANDLERS = {
    signal.SIGINT: lambda signum, frame: None,
    signal.SIGABRT: abort,
}

def register_signal_handlers():
    for k, v in UI_SIGNAL_HANDLERS.items():
        signal.signal(k, v)


def run_interactive(command = ''):
    """
    Interactive command loop for the dyssh prompt.
    """
    global last_traceback

    register_signal_handlers()

    if command:
        run(command)

    while True:
        try:
            prompt = config.get('prompt', '').strip() + ' '
            prompt %= {
                'hostname': config.get('local_hostname'),
                'local_wd': os.getcwd(),
                'remote_wd': config.get('working_directory'),
            }
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
                    if r == os.EX_USAGE:
                        cmd_help(f.__name__[4:])
                    elif r != os.EX_OK:
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
            ui.show_user_warning('Error attempting to execute command: %s' % e)
            ui.show_user_warning("Enter `:traceback` to print the last error traceback.")

    return os.EX_OK


def run(command = ''):
    """
    Run individual commands by passing them to the Connections object. Failures
    should be collected and dealt with here by checking the return codes of
    completed commands.
    """

    if not len(connections.conns.hosts):
        ui.show_user_warning('No hosts specified.')

    connections.conns.run_command_all(command)

    return os.EX_OK


#
# Interactive commands.
#

def cmd_add(*args):
    """
    :add <host>           Add a host to the active host list. Optionally specify
                          more than one host.
    """
    if not args:
        return os.EX_USAGE
    for i in args:
        connections.conns.add(i)
    return os.EX_OK


def cmd_cd(*args):
    """
    :cd <path>            Sets the 'working_directory' config option. This path
                          will be set as the working directory with the `cd`
                          command before executing any individual command on the
                          remote host.
    """
    if len(args) == 1:
        config.config['working_directory'] = args[0]
    else:
        return os.EX_USAGE
    return os.EX_OK


def cmd_get(*args):
    """
    :get <remote> <local> Copy the file at <remote> path for each remote host to
                          <local> path. Each file will be renamed (or placed in
                          a sub-directory) according to the value given by the
                          'get_path_template' config option.
    """
    if len(args) == 2:
        connections.conns.get_file_all(args[0], args[1])
    else:
        return os.EX_USAGE
    return os.EX_OK


def cmd_help(*args):
    """
    :help [cmd]           Show interactive command help.
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
    ui.write('\n', textwrap.dedent(output), '\n')
    return os.EX_OK


def cmd_history(*args):
    """
    :history <host>       Show the command history for <host>.
    """
    if len(args) == 1:
        history = connections.conns.get_history(args[0])
        if not history:
            terminal.error(text = "No history available for %s" % args[0])
        else:
            headers = ('\n#', 'Command', 'Exit code')
            output = []
            for i, h in enumerate(history):
                output.append((
                    '%s' % i,
                    h.get('command'),
                    h.get('exitcode'),
                ))
            ui.write(terminal.format_columns(headers, output), '\n')
    else:
        return os.EX_USAGE
    return os.EX_OK


def cmd_join(*args):
    """
    :join <host>          If there is an active command running on <host>,
                          connect to that host in an interactive terminal
                          session. When the session ends (either through exit,
                          disconnect, or error), you will be returned to the
                          dyssh prompt.

                          You can disconnect manually by entering host key mode
                          (CTRL-A), and pressing CTRL-C.

                          All host-key mode commands are as follows:

                          CTRL-A    - Send CTRL-A to the remote host.
                          CTRL-B    - Raise a generic Exception. (Useful for
                                      debugging.) This will also have the side-
                                      effect of disconnecting the terminala and
                                      returning you to the dyssh prompt.
                          CTRL-C    - Disconnect the terminal from the virtual
                                      terminal that the process is running in
                                      (return to the dyssh prompt).
    """
    if len(args) == 1:
        connections.conns.join(args[0])
    else:
        return os.EX_USAGE
    return os.EX_OK


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
        return os.EX_USAGE
    return os.EX_OK



def cmd_list(*args):
    """
    :list                 List all hosts in the current hosts list.
    """
    output = []
    for idx, item in enumerate(connections.conns.items()):
        host, hostinfo = item
        try:
            exitcode = hostinfo.get('history', [])[-1].get('exitcode')
            if exitcode is None:
                exitcode = '(command still processing)'
        except IndexError:
            exitcode = '(no commands run)'
        output.append((
            '[%s]' % idx,
            host,
            hostinfo.get('connected'),
            exitcode,
        ))
    if not len(output):
        terminal.error(text = 'No hosts.')
        return os.EX_OK
    headers = ('', 'Hostname', 'Connected', 'Last exit')
    ui.write('\n', terminal.format_columns(headers, output), '\n')
    return os.EX_OK


def cmd_put(*args):
    """
    :put <local> <remote> Copy the file at <local> path for each remote host to
                          <remote> path.
    """
    if len(args) == 2:
        connections.conns.put_file_all(args[0], args[1])
    else:
        return os.EX_USAGE
    return os.EX_OK


def cmd_remove(*args):
    """
    :remove <host>        Remove one or more hosts from the active host list.
                          Optionally specify more than one host.
    """
    if not args:
        return os.EX_USAGE
    for i in args:
        connections.conns.remove(i)
    return os.EX_OK


def cmd_timeout(*args):
    """
    :timeout              Show the current value for the 'job_timeout' config
                          option.
    :timeout <seconds>    Set the current value for the 'job_timeout' config
                          option. Seconds to wait for jobs to complete before
                          returning to the interactive prompt. Jobs that time
                          out will continue to operate in the background, and
                          can be checked with either :status or by using :join.
    """
    
    if len(args) == 1 and args[0].isdigit():
        t = float(args[0])
        if t < 0:
            t = 0
        config.config['job_timeout'] = t
        terminal.error(text = "Timeout set to %s seconds" % t)
    elif len(args) == 0:
        ui.write(config.get('job_timeout'))
    else:
        return os.EX_USAGE

    return os.EX_OK


def cmd_env(*args):
    """
    :env format [FORMAT]  Show or set the format of environmental variable
                          declarations. Use '%(key)s' and '%(value)s' to specify
                          the substitutions in your string.
    :env list             List all environmental variables that are being set on
                          each command.
    :env set <VAR>=<VAL>  Before executing each command on a remote host
                          set the environmental variable <VAR> to the value
                          given by <VAL>.
    :env unset <VAR>      Before executing each command on a remote host
                          set the environmental variable <VAR> to the value
                          given by <VAL>.
    """
    envvars = config.get('envvars', {})
    if len(args) == 1 and args[0] == 'list':
        ui.write(terminal.format_columns(
            ('Variable', 'Value'),
            sorted(envvars.items())
        ))
    elif len(args) == 1 and args[0] == 'format':
        ui.write(config.get('envvar_format', ''))
    elif len(args) > 1 and args[0] == 'format':
        config.config['envvar_format'] = ' '.join(args[1:])
    elif len(args) > 1 and args[0] == 'set':
        k, _, v = ' '.join(args[1:]).partition('=')
        envvars[k] = v
    elif len(args) == 2 and args[0] == 'unset':
        k = args[1]
        if k in envvars:
            del envvars[k]
    else:
        return os.EX_USAGE
    config.config['envvars'] = envvars
    return os.EX_OK


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
            return os.EX_OK
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
                return os.EX_OK
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
            outstr += terminal.error(
                text = terminal.tocolor(command + '\n', 'bold'),
                silent = True
            )
            for line in outlines:
                outstr += terminal.error(
                    '[%s] ' % host,
                    line.strip('\n'),
                    1,
                    silent = True
                )
            outstr += terminal.error(
                text = 'Exit code: %s' % exitcode,
                silent = True
            )
            outstr = outstr.replace('\r', '\n')
            pydoc.pipepager(outstr, config.get('pager'))
    else:
        return os.EX_USAGE
    return os.EX_OK


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
        ui.write('\n', terminal.format_columns(headers, output), '\n')
    else:
        return os.EX_USAGE

    return os.EX_OK


def cmd_traceback(*args):
    global last_traceback
    ui.write(last_traceback)
    return os.EX_OK


def cmd_quit(*args):
    """
    :quit                 Exit interactive mode and quit the program.
    """
    terminal.error(text = 'Stopping any running jobs ...')
    connections.conns.kill_all()
    terminal.error(text = 'Disconnecting from all remote hosts ...')
    connections.conns.disconnect_all()
    sys.exit(os.EX_OK)
