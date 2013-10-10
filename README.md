# dyssh

A simple interface for issuing commands to multiple remote servers over SSH.

## Usage

There are several command-line options, and dyssh supports interactive and non-
interactive modes (although for scripting there are probably better solutions).

Basic usage looks something like this:
```
$ dyssh [OPTIONS] [COMMAND]
```

Omitting COMMAND and/or specifying `--interactive` will drop you into an
interactive prompt. From there you can add/remove hosts and execute commands,
check the output of those commands, and, if necessary, connect to an individual
host interactively. This is especially useful for resolving issues/hung
processes.

At the interactive prompt, `:help` will show avaialbe dyssh commands. Anything
not prefixed by a `:` will be sent to the remote hosts.

At the system command line, `--help` will show you available options and flags.

## Limitations and known issues

This is an early, still-experimental program. Also note that there are already a
million variations on this kind of thing out there on the internet. I wrote this
largely for fun and to play with the
[paramiko](https://github.com/paramiko/paramiko) module, so it may not be as
reliable as some of the more mature tools that are available.

That said, here are the most important caveats:

* Each command is run in a new pseudo-terminal session, so environmental
  variables have to be re-set on each command execution. In an interactive
  session this is taken care of transparently using the `:env` command. At the
  command line, you can use the `--envvars` flag.
* I have no idea how this program will handle extremely large amounts of output.
  Probably by eating all of your memory and then failing. Brief tests with `yes`
  were uh ... problematic. (Lots of time waiting for the program to finish
  reading all the output from the pty, CRTL-C doing nothing to save you, that
  sort of thing.) This is something that I hope to devise a better approach to
  in future.

## Dependencies

* Python 2.5, 2.6, or 2.7
* The [Paramiko](https://github.com/paramiko/paramiko) Python module. Paramiko
  is available in the Python Package Index (using `pip` or `easy_install`) as
  well as in many Linux repositories (in Arch as `python2-paramiko` and Debian
  as `python-paramiko`).
* This program uses the `termios` module and makes a number of other POSIX
  assumptions, and so will not run on Windows without some modification. That
  said, I would welcome contributions in that regard.
* By default, I'm assuming you have the `less` pager installed on your system. 
  If you don't, you can change it, either by using the config file mechanism,
  setting a `--pager=<somepager>` option, or editing `config.py` directly.

This has been tested on OS X and Debian GNU/Linux.
