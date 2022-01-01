""" The constants module stores all Constants for the program"""

import pygame as pg

NO_PATH = pg.USEREVENT + 1
NO_START = pg.USEREVENT + 2
NO_END = pg.USEREVENT + 3
pop_up_events = NO_PATH, NO_START, NO_END

# fonts
pg.font.init()
big_text_font = pg.font.Font(pg.font.match_font("georgia"), 25)
text_font = pg.font.Font(pg.font.match_font("georgia"), 15)
number_font = pg.font.Font(pg.font.match_font("cambria"), 15)

# colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LIGHT_GREY = (200, 200, 200)
MEDIUM_GREY = (125, 125, 125)
DARK_GREY = (50, 50, 50)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (175, 0, 255)
YELLOW = (255, 255, 0)
TURQUOISE = (0, 200, 200)
ORANGE = (255, 150, 0, 255)


# display
dirty_fills = []        # background, rect, etc append as (color, rect)
dirty_blits = []        # most likely text, append as (surface, pos)
# exceptional cases
early_fills = []
early_blits = []
late_fills = []
late_blits = []
to_display = [early_fills, early_blits, dirty_fills, dirty_blits, late_fills, late_blits]

# for updating neighbors when using RSR:
CYCLE_MOVES = {"right": lambda col, row: (col + 1, row),
               "left": lambda col, row: (col - 1, row),
               "down": lambda col, row: (col, row + 1),
               "up": lambda col, row: (col, row - 1),
               "topright": lambda col, row: (col + 1, row - 1),
               "topleft": lambda col, row: (col - 1, row - 1),
               "downright": lambda col, row: (col + 1, row + 1),
               "downleft": lambda col, row: (col - 1, row + 1)
               }
