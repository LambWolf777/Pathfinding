import sys
import pygame as pg
import config as cfg
import GUI
import ALGO


def main():

    if not cfg.display_is_init:
        GUI.display_init()
        cfg.display_is_init = True

    while not cfg.done:
        cfg.event_list.clear()
        cfg.clock.tick()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                pg.quit()
                sys.exit()
            elif event.type == pg.KEYDOWN or event.type == pg.MOUSEBUTTONDOWN:
                cfg.event_list.append(event)

        GUI.handle_buttons()

        GUI.handle_grid()

        if cfg.running:

            ALGO.run()

        GUI.handle_stats()

        GUI.handle_display()

        pg.display.flip()


if __name__ == "__main__":
    main()

# TODO: make a tutorial or a help/? button to give out info about the programs and it's workings
