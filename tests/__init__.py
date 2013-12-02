import curses
import os
import sys
import time

import consoleinfo

stdscr = curses.initscr()


curses.noecho()

stdscr.keypad(1)
stdscr.nodelay(1)
stdscr.timeout(0)

try:
    curses.curs_set(0)
except:
    if os.environ.get("TERM") == 'xterm-color':
        os.environ['TERM'] = 'xterm'
        curses.curs_set(0)

curses.cbreak()
curses.meta(1)

def exit():
    curses.nocbreak()
    stdscr.keypad(0)
    curses.echo()
    curses.endwin()
    sys.exit()


class Window(object):

    win = None
    stdscr = stdscr


class MainPadWindow(object):

    def __init__(self, clearspace = 2, maxscrollback = 10):
        height, width = consoleinfo.get_terminal_size()
        self.toprow = 0
        self.leftcol = 0
        self.h = height - clearspace
        self.w = width
        self.win = curses.newpad(self.h + maxscrollback, self.w)
        self.scrollpos = 0
        self.win.idlok(1)
        self.win.scrollok(1)

        self.scrollback = []
        self.scrollforward = []


    def addtext(self, text):
        self.win.addstr(text)
        cursy, cursx = self.win.getyx()
        wintop = self.h + self.scrollpos
        if cursy > wintop:
            self.scroll(cursy - wintop)
        else:
            self.refresh()

    def scroll(self, lines):
        self.scrollpos += lines
        cursy, cursx = self.win.getyx()
        scrollmax = cursy - self.h
        if self.scrollpos < 0:
            self.scrollpos = 0
        elif self.scrollpos > scrollmax:
            self.scrollpos = scrollmax
        self.refresh()

    def refresh(self):
        self.win.redrawwin()
        self.win.noutrefresh(self.scrollpos, 0, self.toprow, self.leftcol, self.h, self.w)


class StatusBar(object):

    def __init__(self, starthpos = 0, barheight = 1):
        height, width = consoleinfo.get_terminal_size()
        self.toprow = starthpos
        self.leftcol = 0
        self.h = barheight
        self.w = width
        self.win = curses.newwin(self.h, self.w, self.toprow, self.leftcol)
        self.win.bkgd(curses.A_REVERSE)

    def status(self, text):
        text = text.strip()
        self.win.erase()
        self.win.addstr(0,0, text)
        self.win.redrawwin()
        self.win.noutrefresh()



class CommandWindow(object):
    pass

height, width = consoleinfo.get_terminal_size()

#win = curses.newwin(height, width, 0, 0)

height, width = consoleinfo.get_terminal_size()
clearspace = 5

mainwindow = MainPadWindow(clearspace = clearspace)
statusbar = StatusBar(starthpos = height - clearspace + 2)

mainwindow.addtext('Ready.\n')
statusbar.status('(None)')
#stdscr.addstr("This is a Sample Curses Script\n\n")
#stdscr.addstr(height - 2, 0, "Test".ljust(width), curses.A_REVERSE)
c = 0

while True:
    curses.doupdate()
    event = stdscr.getch()
    if event and event > 0:
        statusbar.status(repr(event) + '\n')
    if event == ord("q"): break
    elif event == ord("p"):
        c += 1
        l = "Qui blandit praesent luptatum zzril: delenit augue duis dolore te feugait nulla facilisi nam. Ad minim veniam quis nostrud; exerci tation ullamcorper suscipit lobortis nisl ut aliquip. Modo typi qui, nunc nobis videntur parum clari fiant sollemnes in. Nunc putamus parum claram anteposuerit litterarum formas humanitatis per, seacula quarta decima et quinta decima eodem! Soluta nobis eleifend option congue nihil imperdiet doming. Ut wisi enim ex ea commodo consequat duis autem vel eum iriure dolor in hendrerit in! Odio dignissim liber tempor cum id quod mazim! Placerat facer possim assum typi non habent claritatem insitam. Iusto est usus legentis in iis qui facit eorum claritatem Investigationes demonstraverunt lectores legere me! Mutationem consuetudium lectorum, mirum est notare quam littera gothica quam."
        mainwindow.addtext('%s %s\n' % (c, l))
    elif event == curses.KEY_UP:
        mainwindow.scroll(-1)
    elif event == curses.KEY_DOWN:
        mainwindow.scroll(1)


curses.endwin()

exit()
