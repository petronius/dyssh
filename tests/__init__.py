import curses
import curses.panel
import functools
import os
import sys
import time
import traceback

import consoleinfo
import text
import windows

# USE curses.wrapper(func,...)
def init():
    curses.noecho()

    windows.stdscr.keypad(1)
    windows.stdscr.nodelay(1)
    windows.stdscr.timeout(0)

    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()

    try:
        curses.curs_set(0)
    except:
        if os.environ.get("TERM") == 'xterm-color':
            os.environ['TERM'] = 'xterm'
            curses.curs_set(0)

    curses.cbreak()
    curses.meta(1)
    

def cleanup():
    curses.nocbreak()
    windows.stdscr.keypad(0)
    curses.echo()
    curses.endwin()


if __name__ == '__main__':

    init()

    out = None

    try:
        height, width = consoleinfo.get_terminal_size()
        clearspace = 5

        mainwindow = windows.ScrollWindow(size = (height - 5, width),
            scrollback = 500)

        hiddenwindow = windows.ScrollWindow(size = (height - 5, width),
            scrollback = 500)

        stackgroup = windows.StackGroup(mainwindow, hiddenwindow)

        statusbar = windows.Window(size = (1, width), offset = (height - 4, 0),
            attributes = (curses.A_NORMAL, curses.color_pair(6),))

        hiddenwindow.settext('Ready.')
        mainwindow.hide()
        statusbar.settext('(None)')

        #statusbar.text_formatter = lambda self, t: text.to_color(t, 'red')
        windows.update_all()

        c = 0

        while True:
            event = windows.stdscr.getch()
            
            if event and event > 0:
                statusbar.settext(str(event) + ' (' + (chr(event) if event < 256 else '') + ')')

            if event == ord("q"): break
            if event == ord('s'):
                if mainwindow.hidden:
                    mainwindow.show()
                else:
                    mainwindow.hide()
            elif event == ord("p"):
                c += 1
                l = ' test charlist'
                for window in stackgroup:
                    window.write('%s %s %s' % (repr(window), c, l))
            elif event == curses.KEY_UP:
                stackgroup[-1].scroll(-1)
            elif event == curses.KEY_DOWN:
                stackgroup[-1].scroll(1)
            elif event > 0 and event < 256 and chr(event) in [str(i) for i in range(10)]:
                for win in stackgroup:
                    pass

            windows.update_all()
    except:
        out = traceback.format_exc()
    finally:
        cleanup()

    if out:
        print out
