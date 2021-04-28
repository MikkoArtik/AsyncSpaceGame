import time
import random
import curses
import asyncio

from fire_animation import fire


SYMBOLS = ('+', '*', '.', ':')
AMIMATION_DELAY = 0.1
MIN_STARS_COUNT = 50
MAX_STARS_COUNT = 200


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


def add_star(canvas):
  row_index, column_index = 5, 20
  while True:
    canvas.addstr(row_index, column_index, '*', curses.A_DIM)
    canvas.border()
    canvas.refresh()
    time.sleep(2)
    canvas.addstr(row_index, column_index, '*')
    canvas.refresh()
    time.sleep(0.3)
    canvas.addstr(row_index, column_index, '*', curses.A_BOLD)
    canvas.refresh()
    time.sleep(0.5)
    canvas.addstr(row_index, column_index, '*')
    canvas.refresh()
    time.sleep(0.3)


def draw(canvas):
  canvas.border()
  coroutine = blink(canvas, 5, 20)
  while True:
    try:
      coroutine.send(None)
    except StopIteration:
      break
    canvas.refresh()
    time.sleep(0.1)


def draw_five_stars(canvas):
  canvas.border()
  coroutines = []
  for i in range(5):
    coroutines.append(blink(canvas, 5, 20 + 2 * i))

  while True:
    for coroutine in coroutines:
      try:
        coroutine.send(None)
      except StopIteration:
        break
    canvas.refresh()
    time.sleep(AMIMATION_DELAY)


def random_stars(canvas):
  stars_amount = random.randint(MIN_STARS_COUNT, MAX_STARS_COUNT)
  row_max, col_max = canvas.getmaxyx()

  col_center = col_max // 2
  coords = []
  for i in range(stars_amount):
    row = random.randint(1, row_max-2)
    col = random.randint(1, col_max-2)
    coords.append((row, col))
  
  coroutines = [blink(canvas, coords[x][0], coords[x][1], random.randint(0, 20), random.choice(SYMBOLS)) for x in range(stars_amount)]
  shot_coroutine = fire(canvas, row_max -1, col_center)
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

    if shot_coroutine is not None:
      try:
        shot_coroutine.send(None)
      except StopIteration:
        shot_coroutine = None
 
    canvas.refresh()
    time.sleep(AMIMATION_DELAY)


if __name__ == '__main__':
  curses.update_lines_cols()
  curses.wrapper(random_stars)