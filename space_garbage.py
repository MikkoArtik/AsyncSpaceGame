from typing import NamedTuple, List
from random import randint

from curses_tools import draw_frame
import asyncio


class TrashFrame(NamedTuple):
  frame: str
  width: int
  height: int


def load_frame(filename: str):
  width, height = 0, 0
  with open(filename, 'r') as f:
    result = []
    for line in f:
      line = line.rstrip()
      result.append(line)
      height += 1
      width = max(width, len(line))
  result = '\n'.join(result)
  return TrashFrame(result, width, height)


TRASH_FRAMES_FILES = ('trashFrames/duck.txt', 'trashFrames/hubble.txt',  
                      'trashFrames/lamp.txt', 'trashFrames/trash_large.txt', 
                      'trashFrames/trash_small.txt', 'trashFrames/trash_xl.txt')

TRASH_FRAMES = [load_frame(x) for x in TRASH_FRAMES_FILES]


async def fly_garbage(canvas, column: int, garbage_frame: TrashFrame, speed=0.5, delay=0):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    for _ in range(delay):
      await asyncio.sleep(0)

    rows_number, columns_number = canvas.getmaxyx()

    corrected_column = column - garbage_frame.width - 1
    column = min(max(1, corrected_column), column)

    row = 0

    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame.frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame.frame, negative=True)
        row += speed


async def fill_orbit_with_garbage(canvas, coroutines, speed=0.5, delay=10):
  while True:
    max_x = canvas.getmaxyx()[1] - 2
    start_x = randint(1, max_x)
    frame_index = randint(0, len(TRASH_FRAMES) - 1)
    delay = randint(0, 50)
    coroutine = fly_garbage(canvas, start_x, TRASH_FRAMES[frame_index], speed, delay)
    coroutines.append(coroutine)
    for _ in range(delay):
      await asyncio.sleep(0)
