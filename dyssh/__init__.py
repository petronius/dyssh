#!/usr/bin/env python
"""
An interative utility for running commands across multiple remote hosts using
SSH.

If a command is specified, dyssh will operate in batch mode. Without a command,
you will automatically be dropped into an interactive prompt.

At the prompt, there are several commands available. All interactive commands
(as opposed to commands to be sent to the remote hosts) are prefixed with a
colon. The :help command will display all available options.
"""


#Options:
#
#--auto-add-hosts              If this flag is set, unfamiliar host keys will be
#                              added automatically to the list of known hosts,
#                              instead of causing dyssh to abort the connection
#                              attempt. Generally, this is NOT something you want
#                              to do.
#--config=<path>               Specify a config file path other than the default
#                              path (~/.dysshrc).
#--hosts=host1[,host2[,...]]   Specify a list of hosts to pre-seed the host list
#                              with. See the example dysshrc configuration file
#                              for the formats available when specifying hosts.
#--interactive                 Specify an interactive session. This will cause
#                              sdsh to drop you into an interactive prompt after
#                              executing any specified command. By default, if
#                              a command is specified the program will exit
#                              automatically when it is complete.
#
#--help                        Display this information and exit.
__author__  = "Michael Schuller <michael.schuller@artlogic.net>"
__version__ = "0.0.1"
__license__ = "GNU Lesser General Public License (LGPL)"

try:
    import argparse
except ImportError:
    try:
        import optparse
    except ImportError:
        raise ImportError("Could not locate either the `optparse` or `argparse` modules.")

import os
import sys

import dyssh.config
import dyssh.connections
import dyssh.dispatcher

from dyssh.utils import sysexits
from dyssh.utils.terminal import error

__all__ = ["main",]

ARGS = {

    ('-a', '--auto-add-hosts'): {
        'help': 'If this flag is set, unfamiliar host keys will be added '
                'automatically to the list of known hosts, instead of causing '
                'dyssh to abort the connection attempt.',
    },
    ('command',): {
        'help': 'The command to run. If `--interactive` is specified, this '
                'command will run before starting the interactive prompt. If no'
                ' command is specified, an interactive prompt is the default '
                'behaviour.',
        'nargs': '?',
    },
    ('-s','--hosts'): {
        'help': 'A comma-seperated list of hosts to connect to on startup.',
    },
    ('-i','--interactive'): {
        'help': 'Specify an interactive session. Otherwise, by default, if a '
                'command is specified the program will exit automatically when'
                ' it is complete.',
        'action': "store_true",
    },
}

def main(command = None):
    """
    Main routine. Optionally accepts a <command> string as the first command to
    execute after connecting to the hosts.
    """

    connection_info = lambda x: error(text = x)
    connection_error = lambda x: error(text = x, lvl = 2)
    conns = dyssh.connections.Connections(dyssh.config.get('hosts'),
        info_output = connection_info,
        error_output = connection_error)
    dyssh.connections.set(conns)

    if dyssh.config.get('interactive') or not command:
        exitcode = dyssh.dispatcher.run_interactive(command)
    else:
        exitcode = dyssh.dispatcher.run(command)

    return exitcode


if __name__ == '__main__':

    if 'argparse' in globals():
        argparser = argparse.ArgumentParser(description = __doc__)
        for args, kwargs in ARGS.items():
            argparser.add_argument(*args, **kwargs)
        argv = argparser.parse_args()
    else:
        optparser = optparse.OptionParser(description = __doc__)
        # With the older optparse module, we have to get the positional
        # arguments manually.
        positional = []
        for args, kwargs in ARGS.items():
            if len(args) == 1 and not args[0].startswith('-'):
                positional.append(args[0])
            elif args[0].startswith('-'):
                optparser.add_option(*args, **kwargs)
        options, args = optparser.parse_args()
        # Add these to the options object so that config.update() checks them
        for k, v in zip(positional, args):
            if not hasattr(options, k):
                setattr(options, k, v)
        argv = options

    try:
        dyssh.config.update(argv)
    except ValueError, e:
        error('',' '.join(e.args))
        error('',__doc__)
        sys.exit(os.EX_USAGE)
        
    try:
        import atexit
        import readline
        histfile = os.path.join(dyssh.config.get('histfile'))
        try:
            readline.read_history_file(histfile)
        except IOError:
            pass
        atexit.register(readline.write_history_file, histfile)
    except ImportError:
        pass

    if hasattr(argv, 'command'):
        command = argv.command
    else:
        command = None

    exitcode = main(command)
    sys.exit(exitcode)