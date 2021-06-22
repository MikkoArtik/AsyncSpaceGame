import asyncio

from typing import NamedTuple
from random import randint

from curses_tools import draw_frame
from obstacles import Obstacle
from explosion import explode


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


async def fly_garbage(canvas, column: int, garbage_frame: TrashFrame, obstacle_id: int, obstacles: dict, destoyed_obstacle_ids: set, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    corrected_column = column - garbage_frame.width - 1
    column = min(max(1, corrected_column), column)

    obstacles[obstacle_id] = Obstacle(0, column, garbage_frame.height, garbage_frame.width)

    row = 0
    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame.frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame.frame, negative=True)

        if obstacle_id in destoyed_obstacle_ids:
          destoyed_obstacle_ids.remove(obstacle_id)
          center_row = row + int(garbage_frame.height / 2)
          center_col = column + int(garbage_frame.width / 2)
          await explode(canvas, center_row, center_col)
          break

        row += speed
        obstacles[obstacle_id].row = row

    del obstacles[obstacle_id]
        

async def fill_orbit_with_garbage(canvas, coroutines, obstacles, destoyed_obstacle_ids: set,speed=0.5, max_delay=30):
  id_val = 0
  while True:
    delay = randint(0, max_delay)
    for _ in range(delay):
      await asyncio.sleep(0)

    max_x = canvas.getmaxyx()[1] - 2
    start_x = randint(1, max_x)
    frame_index = randint(0, len(TRASH_FRAMES) - 1)
    frame = TRASH_FRAMES[frame_index]
    
    coroutine = fly_garbage(canvas, start_x, frame, id_val, obstacles, destoyed_obstacle_ids, speed)
    coroutines.append(coroutine)
    id_val += 1
