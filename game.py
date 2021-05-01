from typing import List, NamedTuple
import time
import random
import curses
from itertools import cycle
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
            result += [''.join(f.readlines())] * 2
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
    def __init__(self, space_x_speed=1, space_y_speed=1):
        self.space_frames = load_space_frames(SPACE_FRAME_FILES)
        self.space_frame_size = get_space_frame_size(SPACE_FRAME_FILES)
        self.space_x_speed = space_x_speed
        self.space_y_speed = space_y_speed

    @staticmethod
    def get_window_size(canvas) -> Extent:
      height, width =  canvas.getmaxyx()
      return Extent(width, height)

    def generate_stars(self, canvas) -> dict:
        window_extent = self.get_window_size(canvas)
        x_max, y_max = window_extent.dx - 1, window_extent.dy - 1
        min_stars_count = x_max * y_max // 20
        max_stars_count = x_max * y_max // 10
        stars_amount = random.randint(min_stars_count, max_stars_count)
        stars = dict()
        for _ in range(stars_amount):
            # Пределы по x (1, x_max - 1) и y (1, y_max - 1) - учет borders
            x, y = random.randint(1, x_max - 1), random.randint(1, y_max - 1)
            if (x, y) not in stars:
                delay = random.randint(0, MAX_STAR_DELAY)
                stars[(x, y)] = [random.choice(STAR_SYMBOLS), delay]
        return stars

    async def space_animation(self, canvas):
        window_extent = self.get_window_size(canvas)
        x_max, y_max = window_extent.dx - 1, window_extent.dy - 1
        x_pos, y_pos = x_max // 2, y_max // 2
        for frame in cycle(self.space_frames):
            y_direction, x_direction, _ = read_controls(canvas)
            y_pos += y_direction * self.space_y_speed
            x_pos += x_direction * self.space_x_speed
            if y_pos < 1:
                y_pos = 1
            if y_pos > y_max - 1 - self.space_frame_size.dy:
                y_pos = y_max - 1 - self.space_frame_size.dy

            if x_pos < 1:
                x_pos = 1
            if x_pos > x_max - 1 - self.space_frame_size.dx:
                x_pos = x_max - 1 - self.space_frame_size.dx

            draw_frame(canvas, y_pos, x_pos, frame)
            await asyncio.sleep(0)
            draw_frame(canvas, y_pos, x_pos, frame, negative=True)

    def run(self, canvas):
        canvas.nodelay(True)
        curses.curs_set(False)
        canvas.border()

        stars = self.generate_stars(canvas)
        coroutines = []
        for star_coords, attributes in stars.items():
            x, y = star_coords
            symbol, delay = attributes
            coroutines.append(star_blink(canvas, y, x, delay, symbol))
        coroutines.append(self.space_animation(canvas))
        
        while True:
            for coroutine in coroutines.copy():
                try:
                    coroutine.send(None)
                except StopIteration:
                    coroutines.remove(coroutine)
            if len(coroutines) == 0:
                break

            canvas.refresh()
            time.sleep(ANIMATION_DELAY)