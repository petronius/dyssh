
__all__ = [
    'get_terminal_size',
]


try:
    import console
    get_terminal_size = console.getTerminalSize
except ImportError:

    import os
    import fcntl
    import termios
    import struct

    def get_terminal_size(fd = 1):
        """
        Returns height and width of current terminal. First tries to get
        size via termios.TIOCGWINSZ, then from environment. Defaults to 25
        lines x 80 columns if both methods fail.
        """
        try:
            hw = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
        except:
            try:
                hw = (os.environ['LINES'], os.environ['COLUMNS'])
            except:
                hw = (25, 80)

        return hw