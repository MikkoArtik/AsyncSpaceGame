from typing import List, NamedTuple
import time
import random
import curses
import asyncio

from curses_tools import draw_frame
from curses_tools import read_controls


STAR_SYMBOLS = ('+', '*', '.', ':')
ANIMATION_DELAY = 0.1
MAX_STAR_DELAY = 50
SPACE_FRAME_FILES = ['spaceFrames/frame_0.txt', 'spaceFrames/frame_1.txt']


def load_space_frames(frame_files: List[str]) -> List[str]:
    result = []
    for path in frame_files:
        with open(path) as f:
            result.append(''.join(f.readlines()))
    return result


class Extent(NamedTuple):
    dx: int
    dy: int


def get_space_frame_size(frame_files: List[str]) -> Extent:
    max_x, max_y = 0, 0
    for path in frame_files:
        with open(path) as f:
            lines = f.readlines()
            max_line_size = max((len(x.rstrip()) for x in lines))
            max_y = max(max_y, len(lines))
            max_x = max(max_x, max_line_size)
    return Extent(max_x, max_y)


async def star_blink(canvas, y_pos: int, x_pos: int, start_delay: int,
                     symbol='*'):
    for _ in range(start_delay):
        await asyncio.sleep(0)

    while True:
        canvas.addstr(y_pos, x_pos, symbol, curses.A_DIM)
        for _ in range(20):
            await asyncio.sleep(0)

        canvas.addstr(y_pos, x_pos, symbol)
        for _ in range(3):
            await asyncio.sleep(0)

        canvas.addstr(y_pos, x_pos, symbol, curses.A_BOLD)
        for _ in range(5):
            await asyncio.sleep(0)

        canvas.addstr(y_pos, x_pos, symbol)
        for _ in range(3):
            await asyncio.sleep(0)


class MyGame:
    def __init__(self):
        self.space_frames = load_space_frames(SPACE_FRAME_FILES)
        self.space_frame_size = get_space_frame_size(SPACE_FRAME_FILES)

    @staticmethod
    def generate_stars(canvas) -> dict:
        y_max, x_max = canvas.getmaxyx()
        min_stars_count = x_max * y_max // 20
        max_stars_count = x_max * y_max // 10
        stars_amount = random.randint(min_stars_count, max_stars_count)
        stars = dict()
        while len(stars) != stars_amount:
            x, y = random.randint(1, x_max - 2), random.randint(1, y_max - 2)
            if (x, y) not in stars:
                delay = random.randint(0, MAX_STAR_DELAY)
                stars[(x, y)] = [random.choice(STAR_SYMBOLS), delay]
        return stars

    async def space_animation(self, canvas, x_speed=1, y_speed=1):
        canvas.nodelay(True)
        y_max, x_max = canvas.getmaxyx()
        y_pos, x_pos = y_max // 2, x_max // 2
        i = 0
        while True:
            y_direction, x_direction, _ = read_controls(canvas)
            y_pos += y_direction * x_speed
            x_pos += x_direction * y_speed
            if y_pos < 1:
                y_pos = 1
            if y_pos > y_max - 2 - self.space_frame_size.dy:
                y_pos = y_max - 2 - self.space_frame_size.dy

            if x_pos < 1:
                x_pos = 1
            if x_pos > x_max - 2 - self.space_frame_size.dx:
                x_pos = x_max - 2 - self.space_frame_size.dx

            draw_frame(canvas, y_pos, x_pos, self.space_frames[i])
            await asyncio.sleep(0)
            draw_frame(canvas, y_pos, x_pos, self.space_frames[i],
                       negative=True)
            i = (i + 1) % 2

    def run(self, canvas):
        stars = self.generate_stars(canvas)
        star_coroutines = []
        for star_coords, attributes in stars.items():
            x, y = star_coords
            symbol, delay = attributes
            star_coroutines.append(star_blink(canvas, y, x, delay, symbol))

        space_coroutine = self.space_animation(canvas)
        canvas.border()
        curses.curs_set(False)
        while True:
            for coroutine in star_coroutines:
                try:
                    coroutine.send(None)
                except StopIteration:
                    star_coroutines.remove(coroutine)
            if len(star_coroutines) == 0:
                break

            space_coroutine.send(None)

            canvas.refresh()
            time.sleep(ANIMATION_DELAY)



