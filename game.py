from typing import List, NamedTuple, Tuple
import time
import random
from random import randint
import curses
from itertools import cycle
import asyncio

from curses_tools import draw_frame
from curses_tools import read_controls

from space_garbage import TRASH_FRAMES
from space_garbage import fly_garbage
from physics import update_speed
from fire_animation import fire


STAR_SYMBOLS = ('+', '*', '.', ':')
ANIMATION_DELAY = 0.1
MAX_STAR_DELAY = 50
SPACE_FRAME_FILES = ('spaceFrames/frame_0.txt', 'spaceFrames/frame_1.txt')
BORDER_SIZE = 1

GAME_OVER_FRAME = 'otherFrames/game_over.txt'
ONE_YEAR_DURATION_IN_SECONDS = 1.5

PHRASES = {
    1957: "First Sputnik",
    1961: "Gagarin flew!",
    1969: "Armstrong got on the moon!",
    1971: "First orbital space station Salute-1",
    1981: "Flight of the Shuttle Columbia",
    1998: 'ISS start building',
    2011: 'Messenger launch to Mercury',
    2020: "Take the plasma gun! Shoot the garbage!",
}


def load_space_frames(frame_files=SPACE_FRAME_FILES) -> List[str]:
    result = []
    for path in frame_files:
        with open(path) as f:
            result += [''.join(f.readlines())] * 2
    return result


class Extent(NamedTuple):
    dx: int
    dy: int


def load_game_over_frame(frame_file=GAME_OVER_FRAME):
    lines = []
    with open(frame_file, 'r') as f:
        for line in f:
            line = line.rstrip()
            lines.append(line)
    return lines


def get_space_frame_size(frame_files=SPACE_FRAME_FILES) -> Extent:
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
        self.canvas = None

        self.space_frames = load_space_frames()
        self.space_frame_size = get_space_frame_size()
        self.game_over_frame = load_game_over_frame()
        self.space_x_speed = 0
        self.space_y_speed = 0
        self.space_coords = (0, 0)
        self.is_shot = False
        self.coroutines = []
        self.obstacles = dict()
        self.destroyed_obstacle_ids = set()
        self.is_space_died = False
        self.current_year = 1957

        self.__additional_canvas = None

    @property
    def window_size(self) -> Extent:
        height, width = self.canvas.getmaxyx()
        return Extent(width, height)

    @property
    def canvas_center_coords(self) -> Tuple[int, int]:
        height, width = self.canvas.getmaxyx()
        x_max = width - 1
        y_max = height - 1
        return x_max // 2, y_max // 2

    @property
    def garbage_delay_tics(self) -> int:
        if self.current_year < 1961:
            return -1
        elif self.current_year < 1969:
            return 20
        elif self.current_year < 1981:
            return 14
        elif self.current_year < 1995:
            return 10
        elif self.current_year < 2010:
            return 8
        elif self.current_year < 2020:
            return 6
        else:
            return 2

    def generate_stars(self) -> dict:
        window_extent = self.window_size
        x_max, y_max = window_extent.dx - 1, window_extent.dy - 1
        min_stars_count = x_max * y_max // 20
        max_stars_count = x_max * y_max // 10

        stars = dict()
        for _ in range(randint(min_stars_count, max_stars_count)):
            x = random.randint(BORDER_SIZE, x_max - BORDER_SIZE)
            y = random.randint(BORDER_SIZE, y_max - BORDER_SIZE)
            if (x, y) not in stars:
                delay = random.randint(0, MAX_STAR_DELAY)
                stars[(x, y)] = [random.choice(STAR_SYMBOLS), delay]
        return stars

    def get_space_corrected_coords(self, x: int, y: int) -> tuple:
        x_min, y_min = BORDER_SIZE, BORDER_SIZE
        x_max = self.window_size.dx - 1 - BORDER_SIZE - self.space_frame_size.dx
        y_max = self.window_size.dy - 1 - BORDER_SIZE - self.space_frame_size.dy

        x = x_min if x < x_min else x
        x = x_max if x > x_max else x

        y = y_min if y < y_min else y
        y = y_max if y > y_max else y
        return x, y

    async def space_animation(self):
        for frame in cycle(self.space_frames):
            x, y = self.space_coords
            for obstacle in self.obstacles.values():
                if obstacle.has_collision(y, x, self.space_frame_size.dy,
                                          self.space_frame_size.dx):
                    self.is_space_died = True
                    return

            draw_frame(self.canvas, y, x, frame)
            await sleep(1)
            draw_frame(self.canvas, y, x, frame, negative=True)

    async def add_fire(self):
        while True:
            if self.is_shot and self.current_year > 2019:
                coroutine = fire(self.canvas, self.space_coords[1],
                                 self.space_coords[0] + 2,
                                 self.obstacles, self.destroyed_obstacle_ids)
                self.coroutines.append(coroutine)
            await sleep(1)

    async def fill_orbit_with_garbage(self):
        id_val = 0
        while True:
            if self.garbage_delay_tics < 0:
                await sleep(1)
                continue
            else:
                await sleep(self.garbage_delay_tics)

            max_x = self.window_size.dx - BORDER_SIZE
            start_x = randint(1, max_x - 1)
            frame = random.choice(TRASH_FRAMES)

            coroutine = fly_garbage(self.canvas, start_x, frame, id_val,
                                    self.obstacles,
                                    self.destroyed_obstacle_ids)
            self.coroutines.append(coroutine)
            id_val += 1

    def get_game_over_text_position(self):
        canvas_x_mid, canvas_y_mid = self.canvas_center_coords
        label_width_mid = len(self.game_over_frame[1]) / 2
        label_height_mid = len(self.game_over_frame) / 2

        x_mid = int(canvas_x_mid - label_width_mid)
        y_mid = int(canvas_y_mid - label_height_mid)
        return x_mid, y_mid

    async def show_game_over(self):
        x_pos, y_pos = self.get_game_over_text_position()
        frame_text = '\n'.join(self.game_over_frame)
        while True:
            if self.is_space_died:
                draw_frame(self.canvas, y_pos, x_pos, frame_text)
            await asyncio.sleep(0)

    async def show_year_label(self):
        new_window = self.canvas.derwin(1, self.window_size.dx - 2, 1, 1)
        while not self.is_space_died:
            history_fact = PHRASES.get(self.current_year, '')
            text = f'Year: {self.current_year} {history_fact}'
            if history_fact:
                for _ in range(10):
                    draw_frame(new_window, 0, 0, text)
                    await sleep(1)
            else:
                draw_frame(new_window, 0, 0, text)
            await sleep(1)
            draw_frame(new_window, 0, 0, text, negative=True)

    def run(self, canvas):
        canvas.nodelay(True)
        curses.curs_set(False)

        self.canvas = canvas

        stars = self.generate_stars()
        for star_coords, attributes in stars.items():
            x, y = star_coords
            symbol, delay = attributes
            self.coroutines.append(star_blink(canvas, y, x, delay, symbol))

        self.space_coords = self.canvas_center_coords
        self.coroutines.append(self.space_animation())

        self.coroutines.append(self.fill_orbit_with_garbage())
        self.coroutines.append(self.add_fire())
        self.coroutines.append(self.show_game_over())
        self.coroutines.append(self.show_year_label())

        snap_index = 0
        while True:
            if not self.is_space_died:
                y_direction, x_direction, is_shot = read_controls(canvas)
                self.is_shot = is_shot and self.current_year > 2019

                x, y = self.space_coords
                v_x, v_y = self.space_x_speed, self.space_y_speed

                v_y, v_x = update_speed(v_y, v_x, y_direction, x_direction)
                x += v_x
                y += v_y

                self.space_x_speed, self.space_y_speed = v_x, v_y
                self.space_coords = self.get_space_corrected_coords(x, y)

            for coroutine in self.coroutines.copy():
                try:
                    coroutine.send(None)
                except StopIteration:
                    self.coroutines.remove(coroutine)
            if len(self.coroutines) == 0:
                break

            canvas.refresh()
            canvas.border()
            time.sleep(ANIMATION_DELAY)

            if not snap_index % (
                    ONE_YEAR_DURATION_IN_SECONDS / ANIMATION_DELAY):
                self.current_year += 1
            snap_index += 1
