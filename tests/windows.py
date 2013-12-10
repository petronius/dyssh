import collections
import curses

stdscr = curses.initscr()

def update_all():
    """
    Draw all pending updates to the screen.
    """
    curses.doupdate()

class Window(object):

    win = None
    stdscr = stdscr

    newwin = stdscr.subwin

    h = 0
    w = 0
    toprow = 0
    leftcol = 0

    hidden = False
    stackgroup = None
    writebuf = ''

    text_formatter = lambda self, x: x

    def __init__(self,
        size = (60, 80),
        offset = (0, 0),
        attributes = None,
        text_formatter = None):
            
        self.h, self.w = size
        self.toprow, self.leftcol = offset
        self.win = self.newwin(self.h, self.w, self.toprow, self.leftcol)
        self.win.idlok(1)
        self.win.scrollok(1)
        if attributes:
            self._set_attributes(*attributes)
        if text_formatter:
            self.text_formatter = text_formatter

    def _set_attributes(self, *attributes):
        if attributes:
            self.win.bkgdset(*attributes)

    def _refresh(self):
        self.win.redrawwin()
        self.win.noutrefresh()

    def _hide(self):
        self.hidden = True
        self._refresh()

    def _show(self):
        self.hidden = False
        self._refresh()

    def attron(self, *attributes):
        for attr in arributes:
            self.win.attron(attr)

    def attroff(self, *attributes):
        for attr in arributes:
            self.win.attroff(attr)

    def hide(self):
        self.hidden = False
        if self.writebuf:
            # Don't write the last trailing newline, self.write will put it
            # back.
            self.write(self.writebuf[:-1])
        self._refresh()

    def show(self):
        self._show()

    def write(self, *text):
        text = ' '.join([str(t) for t in text])
        text = self.text_formatter(text)
        if self.hidden:
            self.writebuf += text + '\n'
        else:
            text = ' '.join([str(t) for t in text])
            self.win.addstr(text + '\n')
            self._refresh()

    def settext(self, *text):
        text = ' '.join([str(t) for t in text])
        self.win.erase()
        self.win.addstr(0, 0, text)
        self._refresh()


class ScrollWindow(Window):

    scrollpos = 0
    newwin = curses.newpad

    def __init__(self,
        size = (60, 80),
        offset = (0, 0),
        scrollback = 500,
        attributes = None,
        stackgroup = None,
        text_formatter = None):
        
        self.h, self.w = size
        self.toprow, self.leftcol = offset
        self.win = self.newwin(self.h + scrollback, self.w)
        self.win.idlok(1)
        self.win.scrollok(1)
        if attributes:
            self._set_attributes(*attributes)
        if text_formatter:
            self.text_formatter = text_formatter
        if stackgroup:
            self.stackgroup = stackgroup
            self.stackgroup.append(self)

    def _refresh(self):
        if not self.hidden:
            self.win.redrawwin()
            self.win.noutrefresh(self.scrollpos, 0, self.toprow, self.leftcol, 
                self.h, self.w)

    def _hide(self):
        self.win.noutrefresh(self.scrollpos,0,0,0,0,0)
        self.hidden = True

    def hide(self):
        if self.stackgroup:
            self.stackgroup.to_bottom(self)
        else:
            self._hide()

    def show(self):
        if self.stackgroup:
            self.stackgroup.to_top(self)
        else:
            self._hide()
        
    def write(self, *text):
        text = ' '.join([str(t) for t in text])
        text = self.text_formatter(text)
        if self.hidden:
            self.writebuf += text + '\n'
        else:
            self.win.addstr(text + '\n')
            cursy, cursx = self.win.getyx()
            wintop = self.h + self.scrollpos
            if cursy > wintop:
                self.scroll(cursy - wintop)
            else:
                self._refresh()

    def scroll(self, linecount):
        self.scrollpos += linecount
        cursy, cursx = self.win.getyx()
        scrollmax = cursy - self.h
        if self.scrollpos < 0:
            self.scrollpos = 0
        elif self.scrollpos > scrollmax:
            self.scrollpos = scrollmax
        self._refresh()


class StackGroup(object):

    windows = collections.deque()

    def __init__(self, *args):
        # Insert in the order they were passed
        for win in args[::-1]:
            self.add(win)
        self.to_top(self.windows[-1])

    def __len__(self):
        return len(self.windows)

    def __getitem__(self, key):
        return self.windows[key]

    def __iter__(self):
        for win in self.windows:
            yield win

    def __contains__(self, item):
        return item in self.windows

    def to_top(self, win):
        if win in self.windows:
            self.windows.remove(win)
            for window in self.windows:
                window._hide()
            self.windows.append(win)
            win._show()
        else:
            raise KeyError(repr(win) + ' is not a member of ' + repr(self))

    def to_bottom(self, win):
        if win in self.windows:
            self.windows.remove(win)
            self.windows.appendleft(win)
            for window in self.windows:
                window._hide()
            self.windows[-1]._show()
        else:
            raise KeyError(repr(win) + ' is not a member of ' + repr(self))

    def add(self, win):
        """
        New items in the group are added to the bottom of the stack.
        """
        if win in self.windows:
            return
        if isinstance(win, Window):
            self.windows.appendleft(win)
            win._hide()
            # Remove from any pre-existing stackgroup
            if win.stackgroup:
                win.stackgroup.remove(win)
            # Set the current stackgroup
            win.stackgroup = self
        else:
            raise TypeError(repr(win)+' is not a '+repr(Window)+' instance')

    def remove(self, win):
        if win in self.windows:
            self.windows.remove(win)
            win.stackgroup = None
        else:
            raise KeyError(repr(win) + ' is not a member of ' + repr(self))
