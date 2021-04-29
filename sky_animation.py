import time
import random
import curses
import asyncio


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


async def stars_light(canvas):
  stars_amount = random.randint(MIN_STARS_COUNT, MAX_STARS_COUNT)
  row_max, col_max = canvas.getmaxyx()

  coords = []
  for i in range(stars_amount):
    row = random.randint(1, row_max-2)
    col = random.randint(1, col_max-2)
    coords.append((row, col))
  
  coroutines = [blink(canvas, coords[x][0], coords[x][1], random.randint(0, 20), random.choice(SYMBOLS)) for x in range(stars_amount)]

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

    canvas.refresh()
    time.sleep(AMIMATION_DELAY)
