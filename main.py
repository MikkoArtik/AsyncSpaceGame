import time
import random
import curses
import asyncio

from fire_animation import fire
from sky_animation import stars_light

from curses_tools import draw_frame
from curses_tools import read_controls


SYMBOLS = ('+', '*', '.', ':')
AMIMATION_DELAY = 0.1
MIN_STARS_COUNT = 50
MAX_STARS_COUNT = 200

SPACE_FRAMES = []
SPACE_X_SIZE, SPACE_Y_SIZE = 5, 9
SPACE_X_SPEED, SPACE_Y_SPEED = 2, 2
with open('spaceFrames/frame_0.txt', 'r') as f:
  text = ''.join(f.readlines())
  SPACE_FRAMES.append(text)

with open('spaceFrames/frame_1.txt', 'r') as f:
  text = ''.join(f.readlines())
  SPACE_FRAMES.append(text)


async def blink(canvas, row, column, sleeping_time, symbol='*'):
  for _ in range(sleeping_time):
    await asyncio.sleep(0)
  while True:
    canvas.addstr(row, column, symbol, curses.A_DIM)
    for _ in range(20):
      await asyncio.sleep(0)

    canvas.addstr(row, column, symbol)
    for _ in range(3):
      await asyncio.sleep(0)

    canvas.addstr(row, column, symbol, curses.A_BOLD)
    for _ in range(5):
      await asyncio.sleep(0)

    canvas.addstr(row, column, symbol)
    for _ in range(3):
      await asyncio.sleep(0)


async def space_animation(canvas):
  canvas.nodelay(True)
  x_max, y_max = canvas.getmaxyx()
  row_pos, col_pos = x_max // 2, y_max // 2
  i = 0
  while True:
    rows_direction, columns_direction, _ = read_controls(canvas)
    row_pos += rows_direction * SPACE_X_SPEED
    col_pos += columns_direction * SPACE_Y_SPEED
    if row_pos < 1:
      row_pos = 1
    if row_pos > x_max - 2 - SPACE_Y_SIZE:
      row_pos = x_max - 2 - SPACE_Y_SIZE

    if col_pos < 1:
      col_pos = 1
    if col_pos > y_max - 2 - SPACE_X_SIZE:
      col_pos =  y_max - 2 - SPACE_X_SIZE

    draw_frame(canvas, row_pos, col_pos, SPACE_FRAMES[i])
    await asyncio.sleep(0)
    draw_frame(canvas, row_pos, col_pos, SPACE_FRAMES[i], negative=True)
    i = (i + 1) % 2


def random_stars(canvas):
  stars_amount = random.randint(MIN_STARS_COUNT, MAX_STARS_COUNT)
  x_max, y_max = canvas.getmaxyx()

  col_center = y_max // 2
  coords = []
  for i in range(stars_amount):
    row = random.randint(1, x_max-2)
    col = random.randint(1, y_max-2)
    coords.append((row, col))
  
  coroutines = [blink(canvas, coords[x][0], coords[x][1], random.randint(0, 20), random.choice(SYMBOLS)) for x in range(stars_amount)]
  # shot_coroutine = fire(canvas, x_max -1, col_center)
  space_coroutine = space_animation(canvas)
  canvas.border()
  curses.curs_set(False)
  while True:
    for coroutine in coroutines:
      try:
        coroutine.send(None)
      except StopIteration:
        coroutines.remove(coroutine)
    if len(coroutines) == 0:
      break

    # if shot_coroutine is not None:
    #   try:
    #     shot_coroutine.send(None)
    #   except StopIteration:
    #     shot_coroutine = None
    
    space_coroutine.send(None)
 
    canvas.refresh()
    time.sleep(AMIMATION_DELAY)


def sky(canvas):
  x_max, y_max = canvas.getmaxyx()
  col_center = y_max // 2
  coroutines = [stars_light(canvas), fire(canvas, x_max - 1, col_center)]
  while True:
    for coroutine in coroutines:
      try:
        coroutine.send(None)
      except StopIteration:
        coroutines.remove(coroutine)
    if len(coroutines) == 0:
      break



if __name__ == '__main__':
  curses.update_lines_cols()
  curses.wrapper(sky)
