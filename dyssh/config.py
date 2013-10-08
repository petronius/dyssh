"""
Program configuration management. Command-line arguments, configration file
parameters, and changes made during the session all coalesce into the single
'config' dict provided by this module.
"""


import ConfigParser
import os

from utils.terminal import warn


config_filepath = os.path.expanduser('~') + '/.dysshrc'

config = {
    # Default values go here.
    'histfile': os.path.expanduser('~') + '/.dyssh-history',
    
    'local_hostname': 'local',
    'prompt': '%(remote_wd)s $',

    'default_hosts': [],
    'auto_add_hosts': False,
    'write_all_logs': False,

    'username': None,
    'password': None,
    'port': 22,

#    'send_interrupts': False,

#    'copy_prefix': '%(hostname)s-',
#    'timestamp_format': '%y%m%d-%H%M%S',
#    'log_file': '%(hostname)s/dyssh-%(hostname)s-%(timestamp)s.log',
#    'log_path': './',

    'pager': 'less -r',
    'job_timeout': .1, # seconds to wait for jobs to complete in interactive mode

    # Runtime options
    'interactive': False,
    'hosts': [],

    'working_directory': '~',

    'envvars': {},
    'envvar_format': """_dyssh='%(key)s'\ndeclare "$_dyssh=%(value)s"\n""",
    'get_path_format': '%(path)s/%(host)s.%(filename)s',
}


def update(*args):
    """
    Update the program configuration. *args should be a list of command-line
    arguments from sys.argv.

    This actually accepts any of the congfig options as command-line arguments,
    even the ones not specified in the __doc__ string of the main module file.
    """
    global config_filepath

    overrides = {}
    invalid_args = []

    for arg in args:

        if arg.startswith('--'):

            arg, _, val = arg.partition('=')
            argkey = arg.strip('-').replace('-', '_')

            # Options that set a value
            if argkey == 'config':
                config_filepath = val
                continue
            elif _ == '=' and argkey in config.keys():
                overrides[argkey] = val
                if argkey == 'hosts':
                    # Convert to a list
                    config[argkey] = [i.strip() for i in val.split(',')]
                elif argkey in ['config', 'histfile']:
                    # Expand '~' as necessary:
                    val = val.strip()
                    if val.startswith('~/'):
                        config[argkey] = os.path.expanduser('~') + val[2:]
                elif argkey in ['envvars']:
                    config[argkey] = val
                continue

            # Options which are just boolean flags
            elif argkey in config.keys():
                config[argkey] = True
                continue

        invalid_args.append(arg)

    if len(invalid_args):
        raise ValueError('Invalid arguments:', *invalid_args)

    try:

        conffile = open(config_filepath) or ''

        loaded_confs = ConfigParser.ConfigParser()
        loaded_confs.readfp(conffile)
        for section in loaded_confs.sections():
            config.update(loaded_confs.items(section))

        config.update(overrides)

    except (TypeError, IOError, OSError):
        warn('Unable to open configuration file: %s' % config.get('config'))

    for k, v in config.items():
        # Parse the envvars conf into a dict
        if k == 'envvars' and isinstance(v, basestring):
            envvars = {}
            v = v.split(';')
            for i in v:
                x, _, y = i.partition('=')
                envvars[x] = y
            config['envvars'] = envvars


def get(*args):
    """
    Convenience function to keep syntax clean. Returns config.get(*args) on the
    actual config dict.
    """
    return config.get(*args)