# dyssh

A simple interface for issuing commands to multiple remote servers over SSH.

## Usage

There are several command-line options, and dyssh supports interactive and non-interactive modes (although for scripting there are probably better solutions).

Basic usage looks something like this:
```
$ dyssh [OPTIONS] [COMMAND]
```

Omitting COMMAND and/or specifying `--interactive` will drop you into an interactive prompt. From there you can add/remove hosts and execute commands, check the output of those commands, and, if necessary, connect to an individual host interactively. This is especially useful for resolving issues/hung processes.

At the interactive prompt, `:help` will show avaialbe dyssh commands. Anything not prefixed by a `:` will be sent to the remote hosts.

At the system command line, `--help` will show you available options and flags.

## Limitations and known issues

This is an early, still-experimental program. Also note that there are already a million variations on this kind of thing out there. I wrote this largely for fun and to play with the [paramiko](https://github.com/paramiko/paramiko) module, so it may not be up to snuff with some of the more mature tools out there.

That said, here are the most important caveats:

* Each command is run in a new pseudo-terminal session, so environmental variables and program outputs aren't available from one command to the next (this is on my to-do list to fix).
* I have no idea how this program will handle extremely large amounts of output. Probably by eating all of your memory and then failing. Brief tests with `yes` were uh ... problematic. (Lots of time waiting for the program to finish reading all the output from the pty, CRTL-C doing nothing to save you, that sort of thing.) This is something that I hope to devise a better approach to in future.

## Dependencies

* Python 2.5.x, 2.6.x, or 2.7.x
* [paramiko](https://github.com/paramiko/paramiko)
* This program utilizes termios and makes a couple of other *NIX-specific assumptions, and so will not run on Windows without some modification. That said, I would welcome contributions in that regard.
* By default, I'm assuming you have the `less` pager installed on your system. If you don't, you can change it, either by using the config file mechanism, setting a `--pager=<somepager>` option, or editing `config.py` directly.

This has been tested on OS X and Debian GNU/Linux.
