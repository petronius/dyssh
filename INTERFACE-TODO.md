

+------------------------------------+
|[*host1][host2][host3][...]         |
+------------------------------------+
|A whole bunch                       |
| of shell output                    |
|  happens here.                     |
|                                    |
+------------------------------------+
|WARNING: Job 3 failed on host3 (27) |
+------------------------------------+
|<PS1> $ _                           |
+------------------------------------+
## Layout

* Some kind of vim-like status bar

* tabs for each server's output
* chain output together for continuous scrollback between commands to help
  simulate a normal SSH session for each host.

* History browser

## Execution

* Show  alerts about failing jobs in the status bar (job num, host, exit code)
* easy dropping into a real shell for each host (execute bash and do a `:join`)
* job summary screen
* switch prompt when running a ':' command to emphasise the difference (vim style)
* commands for using history, like !!, !2, etc.
* Conditional commands that use the last exitcode (to make up for a lack of '$?')
## Connections

* Heartbeat reconnection attempts
* Stashing and temporarily removal/addition of hosts (for temporary disconns or
  resolving errors across multiple hosts)

## Extras if I have time

* Colors!


* Command queuing mode (based on last exit)