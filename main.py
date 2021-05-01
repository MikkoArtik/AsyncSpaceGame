import curses

from game import MyGame


def main():
    curses.update_lines_cols()
    curses.wrapper(MyGame().run)


if __name__ == '__main__':
    main()
