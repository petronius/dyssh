"""
This is the sample configuration file for dyssh. You shoud copy it to ~/.dysshrc
and modify it according to your needs.

Note that this file will be run as a Python file, and therefore all the
restrictions (and possibilities) that indicates are in effect.

The one hard and fast requirement is that there is a dict named 'DYSSHRC' preset
in the global scope of the interpreted result.
"""

DYSSHRC = {
    ## Default hosts to connect to if none are specified.
    'hosts': [
#        'localhost',
#        'root@localhost',
#        '127.0.0.1',
#        'example.com',
#        'root@example.com',
    ],

    'prompt': '%(remote_wd)s $',
    'auto_add_hosts': False,
    'write_all_logs': False,
    'histfile': '~/.dyssh-history',

    # Set this option to 'true' to use CTL-C to interrupt jobs on remote hosts.
    'send_interrupts': False,

    # If set to 'true', commands must be terminated by a CTL-D on an empty line, to
    # allow for arbitrary multi-line input. Otherwise each line of input will be
    # treated as a distinct command.
    'multiline_input': False,
    
    # Sets a default username, port, and/or password for all hosts. Additionally,
    # you can specify these parameters in the actual host list, either using the
    # default_hosts parameter, above, or at the command line/interactive prompt. In
    # all cases, the following format applies to the host list/command line/interactive
    # prompt:
    #
    #     <username>:<password>@<hostname>:<port>
    #
    # All possible combinations for this syntax are as follows:
    #
    #     <hostname>
    #     <username>@<hostname>
    #     <username>:<password>@<hostname>
    #     :<password>@<hostname>               # Specify only a password; use the
    #                                          # default user name.
    #     <hostname>:<port>
    #     <username>@<hostname>:<port>
    #     <username>:<password>@<hostname>:<port>
    #     :<password>@<hostname>:<port>
    #
    #

    # Defaults when nothing is specified for a host:
    'username': '',
    'password': '',
    'port': 22,

    ##
    ## Shell options
    ##

    # The initial value (can be changed with the `:cd` command)
    'working_directory': '~',
    'envvars': {
        'MYVAR': 1,
        'OTHERVAR': 'A',
    },
    # The shell command used to set environmental variables right before a
    # command is run. Adjust this to match your login shell's language. (The
    # default should work fine under bash, and should also successfully
    # assimilate less-than-usual characters in the variable name.
    'envvar_format': r"""_dyssh='%(key)s'\ndeclare "$_dyssh=%(value)s"\n""",

    ##
    ## File options
    ##

    # Prefix to use when creating copies of files with the `:get` command.
    # dyssh will try to create missing directories.
    'get_path_format': '%(path)s/%(host)s.%(filename)s'
    
}
"""


[logging_and_output]

# pager = less -r -N

## The format string used by datetime.strftime when creating the log file name
timestamp_format = %y%m%d-%H%M%S

## The log file path relative to the root of the logging directory
log_file = %(hostname)s/dyssh-%(hostname)s-%(timestamp)s.log

## Base path for writing logs
log_path = ./

[interactive_mode]

# job_timeout = 0"""