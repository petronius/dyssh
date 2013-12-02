"""
Terminal utilities and formatting goodness.
"""

import sys
import warnings


COLORS = {
    #'black':   '0;30',    'bold black':  '1;30',
    #'white':   '1;37',    'bold white':  '0;37',
    #'blue':    '0;34',    'bold blue':   '1;34',
    #'green':   '0;32',    'bold green':  '1;32',
    #'cyan':    '0;36',    'bold cyan':   '1;36',
    'red':     '0;31',    'bold red':    '1;31',
    #'purple':  '0;35',    'bold purple': '1;35',
    'yellow':  '0;33',    'bold yellow': '1;33',
    'default': '0',       'bold':        '1;29',
}


def tocolor(text, color):
    """
    Set the color of <text> to <color> for printing to the terminal. <color> is
    a key in the COLORS dict.
    """
    text = str(text)
    rcolor = COLORS.get(color) or 0
    return "\001\033[%sm\002%s\001\033[0m\002" % (rcolor, text)


def error(prefix = '(dyssh) ', text  = '', lvl = 0, silent = 0):
    """
    Print a message to stderr. Error level determines what color to use for the
    message prefix.
    """
    
    if lvl == 0:
        color = 'bold'
    elif lvl == 1:
        color = 'bold yellow'
    elif lvl == 2:
        color = 'bold red'

    err = tocolor(prefix, color) + text
    if not silent:
        print >>sys.stderr, err
    return err
    

def warn(prefix = '(dyssh) ', text  = '', lvl = 0):
    """
    Issue a formatted warning message.
    """

    if lvl == 0:
        color = 'default'
    elif lvl == 1:
        color = 'yellow'
    elif lvl == 2:
        color = 'red'

    warnings.warn(tocolor(prefix, color) + text)


def format_columns(headers, output, padlength = 4):
    """
    Format <output> (a list of tuples) neatly underneath the titles provided by
    <headers>.
    """
    lines = []
    column_sizes = []
    for i, header in enumerate(headers):
        column_max = 0
        for col in output:
            s = str(col[i])
            ls = len(s)
            if ls > column_max:
                column_max = ls
        headerlen = len(header)
        if column_max < headerlen:
            column_max = headerlen
        column_max += padlength
        column_sizes.append(column_max)
    output_columns = [headers,] + output
    for line in output_columns:
        outline = ''
        for i, col in enumerate(line):
            col = str(col if col is not None else '')
            outline += col.ljust(column_sizes[i])
        lines.append(outline)
    return '\n'.join(lines)

