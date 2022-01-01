""" The visualizer module allows to run the map editor/algorithm visualizer.
It uses all the other modules except terminal_testing
"""

from sys import exit
import pygame as pg
import config as cfg
from constants import NO_PATH, NO_END, NO_START
import gui
import algo
from classes import Grid


def pop_up_func(event, root_gui):
    root_gui.objects.append(gui.pop_up(event.announcement))


def main():
    """
    Main loop of the visualizer program
    """

    allowed_events = [pg.KEYDOWN, pg.MOUSEBUTTONDOWN, NO_PATH, NO_END, NO_START]

    # Hard coded but it's okay
    grid = Grid(cfg.grid_width, cfg.grid_height, 100, 100)

    pathfinder = algo.init_pathfinder(grid)

    stat_handler = gui.init_stats(pathfinder)

    main_gui = gui.init_gui(pathfinder, grid)

    main_gui.draw_all("grid")

    while True:
        main_gui.events.clear()
        cfg.clock.tick()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                exit()
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                pg.quit()
                exit()
            elif event.type in allowed_events:
                main_gui.events.append(event)

        main_gui.handle_events((NO_PATH, pop_up_func, main_gui), (NO_END, pop_up_func, main_gui),
                               (NO_START, pop_up_func, main_gui))

        grid.handle_grid(main_gui)

        if pathfinder.running:
            pathfinder.run(main_gui.run_interval_button.dict["value"], main_gui.wait_time_button.dict["value"])

        stat_handler.main()

        gui.handle_display()

        pg.display.flip()


if __name__ == "__main__":
    main()

# TODO: make a tutorial or a help/? button to give out info about the programs and it's workings
