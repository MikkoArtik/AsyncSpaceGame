from typing import List, NamedTuple
import time
import random
import curses
from itertools import cycle
import asyncio

from curses_tools import draw_frame
from curses_tools import read_controls

from space_garbage import fill_orbit_with_garbage
from physics import update_speed
from fire_animation import fire


STAR_SYMBOLS = ('+', '*', '.', ':')
ANIMATION_DELAY = 0.1
MAX_STAR_DELAY = 50
SPACE_FRAME_FILES = ['spaceFrames/frame_0.txt', 'spaceFrames/frame_1.txt']
BORDER_SIZE = 1


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


async def sleep(ticks=1):
  for i in range(ticks):
    await asyncio.sleep(0)


async def star_blink(canvas, y_pos: int, x_pos: int, start_delay: int,
                     symbol='*'):
    await sleep(start_delay)
    while True:
        canvas.addstr(y_pos, x_pos, symbol, curses.A_DIM)
        await sleep(20)
        canvas.addstr(y_pos, x_pos, symbol)
        await sleep(3)
        canvas.addstr(y_pos, x_pos, symbol, curses.A_BOLD)
        await sleep(5)
        canvas.addstr(y_pos, x_pos, symbol)
        await sleep(3)


class MyGame:
    def __init__(self):
        self.space_frames = load_space_frames(SPACE_FRAME_FILES)
        self.space_frame_size = get_space_frame_size(SPACE_FRAME_FILES)
        self.space_x_speed = 0
        self.space_y_speed = 0
        self.space_coords = (0, 0)
        self.is_shot = False
        self.coroutines = []

    @staticmethod
    def get_window_size(canvas) -> Extent:
      height, width =  canvas.getmaxyx()
      return Extent(width, height)

    def generate_stars(self, canvas) -> dict:
        window_extent = self.get_window_size(canvas)
        x_max, y_max = window_extent.dx - 1, window_extent.dy - 1
        min_stars_count = x_max * y_max // 20
        max_stars_count = x_max * y_max // 10
        iter_amount = random.randint(min_stars_count, max_stars_count)
        stars = dict()
        for _ in range(iter_amount):
            x = random.randint(BORDER_SIZE, x_max - BORDER_SIZE)
            y = random.randint(BORDER_SIZE, y_max - BORDER_SIZE)
            if (x, y) not in stars:
                delay = random.randint(0, MAX_STAR_DELAY)
                stars[(x, y)] = [random.choice(STAR_SYMBOLS), delay]
        return stars

    async def space_animation(self, canvas):
        for frame in cycle(self.space_frames):
            x, y = self.space_coords
            draw_frame(canvas, y, x, frame)
            await sleep(1)
            draw_frame(canvas, y, x, frame, negative=True)

    async def add_fire(self, canvas):
      while True:
        if self.is_shot:
          self.coroutines.append(fire(canvas, self.space_coords[1], self.space_coords[0] + 2))
        await asyncio.sleep(0)

    def get_space_corrected_coords(self, extent: Extent, x: int, y: int) -> tuple:
        x_min, y_min = BORDER_SIZE, BORDER_SIZE
        x_max = extent.dx - 1 - BORDER_SIZE - self.space_frame_size.dx
        y_max = extent.dy - 1 - BORDER_SIZE - self.space_frame_size.dy

        x = x_min if x < x_min else x
        x = x_max if x > x_max else x

        y = y_min if y < y_min else y
        y = y_max if y > y_max else y
        return x, y

    def run(self, canvas):
        canvas.nodelay(True)
        curses.curs_set(False)

        stars = self.generate_stars(canvas)
        for star_coords, attributes in stars.items():
            x, y = star_coords
            symbol, delay = attributes
            self.coroutines.append(star_blink(canvas, y, x, delay, symbol))
        self.coroutines.append(self.space_animation(canvas))

        window_extent = self.get_window_size(canvas)
        x_max = window_extent.dx - 1 - BORDER_SIZE
        y_max = window_extent.dy - 1 - BORDER_SIZE
        self.space_coords = (x_max // 2, y_max // 2)
        
        self.coroutines.append(fill_orbit_with_garbage(canvas, self.coroutines))
        self.coroutines.append(self.add_fire(canvas))

        while True:
            canvas.border()
            y_direction, x_direction, is_shot = read_controls(canvas)
            self.is_shot = is_shot

            x, y = self.space_coords
            v_x, v_y = self.space_x_speed, self.space_y_speed

            v_y, v_x = update_speed(v_y, v_x, y_direction, x_direction)
            x += v_x
            y += v_y

            self.space_x_speed, self.space_y_speed = v_x, v_y
            self.space_coords = self.get_space_corrected_coords(window_extent, x, y)

            for coroutine in self.coroutines.copy():
                try:
                     coroutine.send(None)
                except StopIteration:
                     self.coroutines.remove(coroutine)
            if len( self.coroutines) == 0:
                break

            canvas.refresh()
            canvas.border()
            time.sleep(ANIMATION_DELAY)
