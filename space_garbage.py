import asyncio
from typing import NamedTuple
from random import random

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
                      'trashFrames/trash_small.txt',
                      'trashFrames/trash_xl.txt')

TRASH_FRAMES = [load_frame(x) for x in TRASH_FRAMES_FILES]


async def fly_garbage(canvas, column: int, garbage_frame: TrashFrame,
                      obstacle_id: int, obstacles: dict,
                      destoyed_obstacle_ids: set):
    """
    Animate garbage, flying from top to bottom.
    Сolumn position will stay same, as specified on start.
    """
    rows_number, columns_number = canvas.getmaxyx()

    corrected_column = column - garbage_frame.width - 1
    column = min(max(1, corrected_column), column)

    obstacles[obstacle_id] = Obstacle(0, column, garbage_frame.height,
                                      garbage_frame.width)

    speed = 0.01 + random()

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
