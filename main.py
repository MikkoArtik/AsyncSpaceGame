import curses

from Game import MyGame


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(MyGame().run)
