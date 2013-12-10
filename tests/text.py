
__all__ = [
    'COLORS',
    'FORMATS',
    'format',
    'format_columns',
]


COLORS = {
    'black':   '0;30',    'bold black':  '1;30',
    'white':   '1;37',    'bold white':  '0;37',
    'blue':    '0;34',    'bold blue':   '1;34',
    'green':   '0;32',    'bold green':  '1;32',
    'cyan':    '0;36',    'bold cyan':   '1;36',
    'red':     '0;31',    'bold red':    '1;31',
    'purple':  '0;35',    'bold purple': '1;35',
    'yellow':  '0;33',    'bold yellow': '1;33',
    'default': '0',       'bold':        '1;29',
}

FORMATS = {
    'normal': 0,
    'bold': 1,
    'dim': 2,
    'underline': 4,
    'blink': 5,
    'reverse': 7,
    'hidden': 8,
}

START_STYLE = '\001\033[%(style)sm\002'
reset_style = '\001\033[%(reset)sm\002'


def format(text, 
        color = None,
        background = None,
        styles = ()
    ):

    pass


def to_color(text, color):
    """
    Set the color of <text> to <color> for printing to the terminal. <color> is
    a key in the COLORS dict.
    """
    text = str(text)
    rcolor = COLORS.get(color) or 0
    return "\001\033[%sm\002%s\001\033[0m\002" % (rcolor, text)


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

