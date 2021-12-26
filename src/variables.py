""" The variables module stores all cross-module variables and contants (unfortunately I did not CAPITALIZE constants)
"""
import sys
import os
import collections

import pygame as pg

# pygame generic

WINDOW_SIZE = (0, 0)

if os.path.basename(sys.modules["__main__"].__file__) == "terminal_testing.py":
    window = pg.display.set_mode(WINDOW_SIZE, flags=pg.HIDDEN)

else:
    # interesting thing, to call multiple flags:
    #     window = pg.display.set_mode(WINDOW_SIZE, flags=pg.SHOWN|pg.FULLSCREEN)
    window = pg.display.set_mode(WINDOW_SIZE)

clock = pg.time.Clock()

# fonts
pg.font.init()
big_text_font = pg.font.Font(pg.font.match_font("georgia"), 25)
text_font = pg.font.Font(pg.font.match_font("georgia"), 15)
number_font = pg.font.Font(pg.font.match_font("cambria"), 15)

# colors
black = (0, 0, 0)
white = (255, 255, 255)
light_grey = (200, 200, 200)
medium_grey = (125, 125, 125)
dark_grey = (50, 50, 50)
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
purple = (175, 0, 255)
yellow = (255, 255, 0)
turquoise = (0, 200, 200)
orange = (255, 150, 0, 255)

# would need to set the grid as a per pixel alpha surface
transparent_orange = (255, 150, 0, 100)

# name..?
event_list = []
user_input = ""
grid_width = 0
grid_height = 0
# state
running = False

# settings
algo = None
diago_allowed = False
display_steps = True
apply_rsr = False

# this can be used as a parameter to run() any algo, ex: run(algo) where algo = (BFS, diago = True, display = True)
# and run must identify the algo and run the appropriate function with needed parameters
start_node = None
end_node = None

# algo variables
path_found = False
bfs_is_init = False
astar_is_init = False
jps_is_init = False

dijkstra_cost_so_far = 1  # (first moves in init...)

shortest_path = []
all_nodes = []  # (grid)
final_path = []     # can fit multiple paths, end algo if len(final_path) == len(end_nodes)
frontier = []

queue = collections.deque()      # for ASTAR

to_be_removed = []

current_node = None

nodes_to_reduct = None

# button dicts
# unfortunately I hard to hard code the borders' sizes for n_nodes_
n_nodes_wide = {"min": 3, "max": window.get_width() - 205 - 25, "default": 100, "value": 100}    # windowwidth - button rect - border
n_nodes_high = {"min": 3, "max": window.get_height() - 125 - 25, "default": 100, "value": 100}   # window_h - stats height - border
brush_size = {"min": 1, "max": 200, "default": 1, "value": 1}
run_interval = {"min": -1, "max": 9999, "default": 100, "value": 0}
run_delay = {"min": 0, "max": 9999, "default": 0, "value": 0}


# display
dirty_fills = []        # background, rect, etc append as (color, rect)
dirty_blits = []        # most likely text, append as (surface, pos)
# exceptionnal cases
early_fills = []
early_blits = []
late_fills = []
late_blits = []


# Progression Bools:
done = False
display_is_init = False

# timers
run_timer = 0
stats_timer = 0

start_runtime = 0
end_runtime = 0

preprocess_start_time = 0
preprocess_end_time = 0

# stats
# what if im searching for multiple paths..? (for path length)
process_time = 0
rsr_time = 0
neighbor_time = 0

path_lenght = 0
active_paths = 0
archived_paths = 0
nodes_searched = 0
# fps = 0 not needed, taken from clock in handle stats


# for updating neighbors when using RSR:
cycle_moves = {"right": lambda col, row: (col + 1, row),
               "left": lambda col, row: (col - 1, row),
               "down": lambda col, row: (col, row + 1),
               "up": lambda col, row: (col, row - 1),
               "topright": lambda col, row: (col + 1, row - 1),
               "topleft": lambda col, row: (col - 1, row - 1),
               "downright": lambda col, row: (col + 1, row + 1),
               "downleft": lambda col, row: (col - 1, row + 1)
               }
