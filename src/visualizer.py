import sys
import pygame as pg
import variables as var
import gui
import algo


def main():

    if not var.display_is_init:
        gui.display_init()
        var.display_is_init = True

    while not var.done:
        var.event_list.clear()
        var.clock.tick()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                pg.quit()
                sys.exit()
            elif event.type == pg.KEYDOWN or event.type == pg.MOUSEBUTTONDOWN:
                var.event_list.append(event)

        gui.handle_buttons()

        gui.handle_grid()

        if var.running:

            algo.run()

        gui.handle_stats()

        gui.handle_display()

        pg.display.flip()


if __name__ == "__main__":
    main()

# TODO: make a tutorial or a help/? button to give out info about the programs and it's workings
