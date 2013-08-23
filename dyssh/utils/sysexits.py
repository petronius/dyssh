"""
UC Berkley exit codes. Copied from a Debian sysexits.h file at some point. Used
for consistent program exists, and also as a handy set of internal error codes
for the dispatcher module.
"""

EX_OK           = 0     # No errors
#EX_GENERAL      = 1     # General, unspecified error
#
#EX__BASE        = 64

EX_USAGE        = 64    # Command line usage is incorrect
#EX_DATAERR      = 65    # Data format error
#EX_NOINPUT      = 66    # Missing input data
#EX_NOUSER       = 67    # Addressee unknown
#EX_NOHOST       = 68    # Host unknown
#EX_UNAVAILABLE  = 69    # Service unavailabe
#EX_SOFTWARE     = 70    # Internal software error
#EX_OSERR        = 71    # System/OS error
#EX_OSFILE       = 72    # Critical OS file missing
#EX_CANTCREAT    = 73    # Can't create (user) output file
#EX_IOERR        = 74    # IO Error (obvs)
#EX_TEMPFAIL     = 75    # Temporary failure, please retry (possibly after fixing
#                        # whatever is causing the error).
#EX_PROTOCOL     = 76    # Remote error in protocol
#EX_NOPERM       = 77    # Permission denied
#EX_CONFIG       = 78    # Configuration error
#
#EX__MAX         = 78