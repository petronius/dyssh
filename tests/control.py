
MODE_EDIT = 0
MODE_COMMAND = 1

WINDOW_MAIN = 0
WINDOW_COMMAND = 1
WINDOW_HOSTINFO = 2
WINDOW_HISTINFO = 3


class InterfaceControl(object):

    def __init__(self):
        pass

    def dispatch_command(self):
        pass

    def set_mode(self):
        # EDIT, COMMAND,
        pass

    def set_window(self):
        pass