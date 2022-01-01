""" The config module set the initial variables for the program, mainly depending on the size of the display"""

from os.path import basename
from sys import modules
import pygame as pg

clock = pg.time.Clock()

WINDOW_SIZE = (0, 0)

if basename(modules["__main__"].__file__) == "terminal_testing.py":
    window = pg.display.set_mode(WINDOW_SIZE, flags=pg.HIDDEN)

else:
    # interesting thing, to call multiple flags:
    #     window = pg.display.set_mode(WINDOW_SIZE, flags=pg.SHOWN|pg.FULLSCREEN)
    window = pg.display.set_mode(WINDOW_SIZE)

button_background_rect = pg.Rect(0, 0, 205, window.get_height())

stats_background_rect = pg.Rect(button_background_rect.width, window.get_height() - 125,
                                window.get_width() - button_background_rect.width, 125)

grid_width = window.get_width() - button_background_rect.width - 25  # border
grid_height = window.get_height() - stats_background_rect.height - 25  # border
