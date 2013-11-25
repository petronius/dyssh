import curses
import sys
import time

stdscr = curses.initscr()

curses.noecho()
curses.cbreak()

stdscr.keypad(1)

def exit():
    curses.nocbreak()
    stdscr.keypad(0)
    curses.echo()
    curses.endwin()
    sys.exit()

begin_x = 20; begin_y = 7
height = 5; width = 40
win = curses.newwin(height, width, begin_y, begin_x)

time.sleep(10)
exit()
