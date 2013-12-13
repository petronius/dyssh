#!/usr/bin/env python
"""
An interative utility for running commands across multiple remote hosts using
SSH.

Usage: dyssh [OPTIONS] [COMMAND]

If a command is specified, dyssh will operate in batch mode. Without a command,
you will automatically be dropped into an interactive prompt.

Options:

--auto-add-hosts              If this flag is set, unfamiliar host keys will be
                              added automatically to the list of known hosts,
                              instead of causing dyssh to abort the connection
                              attempt. Generally, this is NOT something you want
                              to do.
--config=<path>               Specify a config file path other than the default
                              path (~/.dysshrc).
--hosts=host1[,host2[,...]]   Specify a list of hosts to pre-seed the host list
                              with. See the example dysshrc configuration file
                              for the formats available when specifying hosts.
--interactive                 Specify an interactive session. This will cause
                              sdsh to drop you into an interactive prompt after
                              executing any specified command. By default, if
                              a command is specified the program will exit
                              automatically when it is complete.

--help                        Display this information and exit.

At the prompt, there are several commands available. All interactive commands
(as opposed to commands to be sent to the remote hosts) are prefixed with a
colon. The :help command will display all available options.
"""

__author__  = "Michael Schuller <michael.schuller@artlogic.net>"
__version__ = "0.0.1"
__license__ = "GNU Lesser General Public License (LGPL)"


import os
import sys

import config
import connections
import dispatcher

from utils.terminal import error

__all__ = ["main",]


def main(command = None):
    """
    Main routine. Optionally accepts a <command> string as the first command to
    execute after connecting to the hosts.
    """

    connection_info = lambda x: error(text = x)
    connection_error = lambda x: error(text = x, lvl = 2)
    conns = connections.Connections(config.get('hosts'),
        info_output = connection_info,
        error_output = connection_error)
    connections.set(conns)

    if config.get('interactive') or not command:
        exitcode = dispatcher.run_interactive(command)
    else:
        exitcode = dispatcher.run(command)

    return exitcode


if __name__ == '__main__':

    argv = sys.argv[1:]

    if '--help' in argv:
        print __doc__
        sys.exit(os.EX_OK)

    command = None
    if len(argv) and not argv[-1].startswith('--'):
        command = argv[-1]
        argv = argv[:-1]
    elif not len(argv):
        argv = ['--interactive',]

    try:
        config.update(*argv)
    except ValueError, e:
        error('',' '.join(e.args))
        error('',__doc__)
        sys.exit(os.EX_USAGE)
        
    try:
        import atexit
        import readline
        histfile = os.path.join(config.get('histfile'))
        try:
            readline.read_history_file(histfile)
        except IOError:
            pass
        atexit.register(readline.write_history_file, histfile)
    except ImportError:
        pass

    exitcode = main(command)
    sys.exit(exitcode)