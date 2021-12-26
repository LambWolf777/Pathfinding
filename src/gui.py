""" This module handles the user interface (GUI) for the pathfinding visualizer.
It handles the function for clicking on buttons, using input buttons, drawing walls on the grid and setting start/end nodes
It also creates all buttons when the module is ran
"""
import collections
import pickle
import os
import sys
import tkinter
from tkinter import filedialog
import random
from typing import *

import pygame as pg

import variables as var
import classes
import algo

folder_path = os.getcwd()

# This is for making the exe into a directory (go back to parent directory)
# folder_path_bits = os.getcwd().split("\\")[:-1]
# folder_path = "\\".join(folder_path_bits)

grid_path = os.path.join(folder_path, "Grids")

if not os.path.exists(grid_path):
    os.mkdir(grid_path)

# might be better to do a big background too, so we have borders around grid/screen
button_background_rect = pg.rect.Rect(0, 0, 205, var.window.get_height())
stats_background_rect = pg.rect.Rect(button_background_rect.width, var.window.get_height() - 125,
                                     var.window.get_width() - button_background_rect.width, 125)

# creating buttons #####################################################################################################

# black sheep of the buttons
ok_button_ = classes.Button((0, 0), "OK", var.white, var.blue, var.black)


def place_ok_button(position: Tuple[int, int]) -> None:
    """Place an OK button, (ex when no paths found, it is used for the user to dismiss the message)
    ts click events must be used in a separated menu, see no_path_found().

    :param position: topleft corner of the ok button
    :return: None
    """
    ok_button_.position = position
    ok_button_.rect = pg.rect.Rect(position, (ok_button_.rect.width, ok_button_.rect.height))
    var.dirty_blits.append(ok_button_.get_surface())


# grid placement buttons
start_node_button = classes.Button((15, 25), "Place Start", var.white, var.blue, var.black)

end_node_button = classes.Button((start_node_button.rect.right + 5, start_node_button.rect.top),
                                 "Place End", var.white, var.blue, var.black)

draw_walls_button = classes.Button((15, start_node_button.rect.bottom + 10), "Draw walls", var.white, var.blue,
                                   var.black)

erase_walls_button = classes.Button((draw_walls_button.rect.right + 5, draw_walls_button.rect.top),
                                    "Erase walls", var.white, var.blue, var.black)

random_walls_button = classes.Button((15, draw_walls_button.rect.bottom + 10),
                                     "Random walls", var.white, var.blue, var.black)

setup_buttons = [start_node_button, draw_walls_button, random_walls_button, erase_walls_button, end_node_button]

# algo buttons
bfs_button = classes.Button((0, 0), "Flood Fill", var.white, var.black, var.black, False)
bfs_button.is_activated = True  # default..
var.algo = "bfs"

astar_button = classes.Button((0, 0), "A*", var.white, var.black, var.black, False)

# jps_button = var.Button((0, 0), "Jump Search", var.white, var.blue, var.black, False)

dijkstra_button = classes.Button((0, 0), "Dijkstra", var.white, var.black, var.black, False)

algo_buttons = [bfs_button, astar_button, dijkstra_button]

dropdown_algo = classes.DropDownButton((15, random_walls_button.rect.bottom + 30), "Algo: ", algo_buttons)

# Checkboxes
# the bools should refer to their var variable...
diago_button = classes.Checkbox("Diagonal moves", (15, dropdown_algo.rect.bottom + 10), False)

apply_rsr_button = classes.Checkbox("Apply RSR", (15, diago_button.rect.bottom + 10), False)

display_moves_button = classes.Checkbox("Display moves", (15, apply_rsr_button.rect.bottom + 10), True)

# Those are here because i want them below display moves...
run_interval_button = classes.TextInputButton(var.run_interval, (15, display_moves_button.rect.bottom + 10), 40,
                                              "Run: ",
                                              var.run_interval["value"], var.black, var.white, var.blue, var.black)

wait_time_button = classes.TextInputButton(var.run_delay, (run_interval_button.rect.right + 5,
                                                           display_moves_button.rect.bottom + 10),
                                           40, "Wait: ", var.run_delay["value"], var.black, var.white, var.blue,
                                           var.black)

checkbox_buttons = [diago_button, display_moves_button, apply_rsr_button]

# state button
reset_button = classes.Button((15, run_interval_button.rect.bottom + 30), "Reset Grid", var.white, var.blue, var.black)

reset_search_button = classes.Button((reset_button.rect.right + 5, reset_button.rect.top), "Reset Search", var.white,
                                     var.blue, var.black)

play_pause_button = classes.Button((15, reset_search_button.rect.bottom + 10), "Play/Pause", var.white, var.blue,
                                   var.black)

state_buttons = [reset_button, reset_search_button, play_pause_button]

# input buttons:
# i would put these at the top actually
# those dict should be attributes to call defaults and max/min more easily
grid_n_wide_button = classes.TextInputButton(var.n_nodes_wide, (15, play_pause_button.rect.bottom + 30), 50,
                                             "Nodes in width: ",
                                             var.n_nodes_wide["value"], var.black, var.white, var.blue, var.black)

grid_n_high_button = classes.TextInputButton(var.n_nodes_high, (15, grid_n_wide_button.rect.bottom + 10), 40,
                                             "Nodes in height: ",
                                             var.n_nodes_high["value"], var.black, var.white, var.blue, var.black)

brush_size_button = classes.TextInputButton(var.brush_size, (15, grid_n_high_button.rect.bottom + 10), 30,
                                            "Brush size: ",
                                            var.brush_size["value"], var.black, var.white, var.blue, var.black)

input_button_list = [grid_n_wide_button, grid_n_high_button, brush_size_button, run_interval_button, wait_time_button]

# External interactions buttons

save_grid_button = classes.Button((15, brush_size_button.rect.bottom + 30), "Save Grid", var.white, var.black,
                                  var.black)

load_grid_button = classes.Button((save_grid_button.rect.right + 5, save_grid_button.rect.top), "Load Grid", var.white,
                                  var.black, var.black)

save_button_list = [save_grid_button, load_grid_button]

# exit button
exit_button = classes.Button((15, load_grid_button.rect.bottom + 30), "Exit", var.white, var.black, var.black)

# add all to button list
button_list = [start_node_button, draw_walls_button, random_walls_button, erase_walls_button, end_node_button,
               dropdown_algo, diago_button, display_moves_button, apply_rsr_button, reset_button, reset_search_button,
               play_pause_button, grid_n_wide_button, grid_n_high_button, brush_size_button, run_interval_button,
               wait_time_button, save_grid_button, load_grid_button, exit_button]
########################################################################################################################

########################################################################################################################
# DROPDOWN buttons

dropdown_list = [dropdown_algo]


def init_buttons() -> None:
    """ Initial draw of the buttons

    :return: None
    """
    var.window.fill(var.light_grey, button_background_rect)

    for button in button_list:
        var.dirty_blits.append(button.get_surface())


def draw_grid() -> None:
    """ Draws the grid as a late fill (this function was made for covering the no paths found pop up window.
    It also makes the unused pixels from the grid dark gray as to prevent confusion, although it would be nice to find
    a better solution.

    :return: None
    """

    # ideally all nodes would get blitted here and the grd would be blitted to the window once per frame, altough idk
    var.late_fills.append(
        (var.dark_grey, pg.rect.Rect(var.all_nodes[0][0].position, (var.grid_width, var.grid_height))))

    for column in var.all_nodes:
        for node in column:
            var.late_fills.append(node.get_fill())


def generate_grid() -> None:
    """ Generates the grid and then draws it using draw_grid(). Generate using parameters defined in config

    :return: None
    """

    # put this into a function..
    # GRID
    # cleanup all value (start node, end, all_nodes, etc)
    var.all_nodes = []

    var.grid_width = var.window.get_width() - button_background_rect.width - 25  # border
    var.grid_height = var.window.get_height() - stats_background_rect.height - 25  # border

    nodes_width = var.grid_width / var.n_nodes_wide["value"]
    nodes_height = var.grid_height / var.n_nodes_high["value"]

    start_height = 25  # + grid_height - nodes_height * var.n_nodes_high["value"]

    # var.all_nodes is the grid

    position_y = start_height - nodes_height
    position_x = button_background_rect.width - nodes_width

    for x_wide in range(var.n_nodes_wide["value"]):
        position_x += nodes_width
        column = []
        for y_high in range(var.n_nodes_high["value"]):
            position_y += nodes_height

            column.append(classes.Node(x_wide, y_high, (position_x, position_y), nodes_width, nodes_height))

        var.all_nodes.append(column)
        position_y = start_height - nodes_height

    draw_grid()


def handle_buttons(button: Union[classes.Button, classes.Checkbox, classes.TextInputButton,
                                 classes.DropDownButton] = None) -> None:
    """ Handle the working of all the buttons, including click detection and the actions to be taken when a specific
    button is clicked.
    It can flex into a clicking simulator when button is
    specified (only state buttons can be specified as of now)

    :param button: if set, simulates a click to specified button
    :return: None
    """

    def turn_off_button_list(list_: List[Union[classes.Button, classes.Checkbox, classes.TextInputButton,
                                               classes.DropDownButton]]) -> None:
        """ Set button.is_activated = False for all buttons in the list and append its surface and position to
        var.dirty_blits to be redrawn with its updated status

        :param list_: List of any button class instances with attribute self.is_activated
        :return: None
        """

        for _button_ in list_:
            if _button_.is_activated:
                _button_.is_activated = False
                var.dirty_blits.append(_button_.get_surface())

    def click_setup_button(butt: classes.Button) -> None:
        """ Handles clicks on buttons in  var.setup_buttons, (place start, place end, draw walls,
        erase walls, random walls)

        :param butt: clicked button in config.setup_button
        :return: None
        """

        if butt is random_walls_button:
            for column in var.all_nodes:
                for node in column:
                    if random.randrange(11) == 0:
                        if node is not var.start_node and node is not var.end_node:
                            node.is_wall = True
                            var.dirty_fills.append(node.get_fill())
        else:
            if butt.is_activated:
                butt.is_activated = False
                var.dirty_blits.append(butt.get_surface())
            else:
                turn_off_button_list(setup_buttons)
                butt.is_activated = True
                var.dirty_blits.append(butt.get_surface())

    def click_algo_button(butt: Union[classes.Button, classes.Checkbox, classes.TextInputButton,
                                      classes.DropDownButton]) -> None:
        """ Handles clicks on algo button

        :param butt: Clicked button in algo button
        :return: None
        """

        # turn_off_button_list(algo_buttons)  The blit is messing with my dropdown...
        for button in algo_buttons:
            button.is_activated = False

        butt.is_activated = True
        if butt is bfs_button:
            var.algo = "bfs"
        elif butt is astar_button:
            var.algo = "astar"
        elif butt is dijkstra_button:
            var.algo = "dijkstra"
        # elif butt is jps_button:
        #     var.algo = "jps"

    def click_checkbox(butt: classes.Checkbox) -> None:
        """ Handles click on a checkbox button

        :param butt: Clicked checkbox button
        :return: None
        """

        butt.is_activated = not butt.is_activated

        if butt is display_moves_button:
            var.display_steps = butt.is_activated

            wait_time_button.is_disabled = not butt.is_activated
            run_interval_button.is_disabled = not butt.is_activated

            var.dirty_blits.append(wait_time_button.get_surface())
            var.dirty_blits.append(run_interval_button.get_surface())

        elif butt is diago_button:
            var.diago_allowed = butt.is_activated

        elif butt is apply_rsr_button:
            var.apply_rsr = butt.is_activated

        var.dirty_blits.append(butt.get_surface())

    def click_state_button(butt: classes.Button) -> None:
        """ Handles click on state buttons

        :param butt: Clicked button in state button
        :return: None
        """

        if butt is reset_button or butt is reset_search_button:

            var.running = False

            if butt is not reset_search_button:
                if var.start_node is not None:
                    temp_start = var.start_node
                    var.start_node = None
                    var.dirty_fills.append(temp_start.get_fill())
                if var.end_node is not None:
                    temp_end = var.end_node
                    var.end_node = None
                    var.dirty_fills.append(temp_end.get_fill())

            var.path_found = False
            var.bfs_is_init = False
            var.astar_is_init = False
            var.shortest_path = []
            var.frontier = []
            var.to_be_removed = []
            var.current_node = None
            var.final_path = []
            var.current_path = []
            var.queue = collections.deque()
            var.newly_archived = []
            var.dijkstra_cost_so_far = 1
            var.nodes_to_reduct = None
            var.rsr_time = 0
            var.neighbor_time = 0
            var.start_runtime = 0
            var.end_runtime = 0
            var.run_timer = 0

            for column in var.all_nodes:
                for node in column:

                    # hoping this allows me to pickle the grid
                    node.neighbors = None
                    node.came_from = None
                    # YUH BEASTMODE

                    if node.update_color() is not var.black:

                        if butt is not reset_search_button:
                            node.is_wall = False
                            node.is_end = False
                            node.is_start = False

                        node.is_sym_rect = False
                        node.is_border = False
                        node.visited = False
                        node.is_path = False

                        var.dirty_fills.append(node.get_fill())

            # un disable buttons
            for any_button in button_list:
                if any_button is run_interval_button or any_button is wait_time_button:
                    wait_time_button.is_disabled = not display_moves_button.is_activated
                    run_interval_button.is_disabled = not display_moves_button.is_activated
                else:
                    any_button.is_disabled = False

                var.dirty_blits.append(any_button.get_surface())

        elif butt is play_pause_button and var.algo is not None \
                and var.start_node is not None and var.end_node is not None:
            var.running = not var.running
            # could add pause/unpause timers...

            # this could be a general algo_is_init bool
            if not var.astar_is_init and not var.bfs_is_init:

                for x_button in button_list:
                    if x_button not in state_buttons and x_button is not exit_button:
                        x_button.is_disabled = True
                        var.dirty_blits.append(x_button.get_surface())

                if not var.display_steps or var.run_interval["value"] == -1:
                    # update display to show disabled buttons, actually everything becomes unresponsive but well...
                    handle_display()
                    pg.display.flip()

                # this would be preprocessed when loading a map so I'm not including it in the timer
                var.preprocess_start_time = pg.time.get_ticks()

                for column in var.all_nodes:
                    for node in column:
                        node.get_neighbors(var.all_nodes, var.diago_allowed)

                var.preprocess_end_time = pg.time.get_ticks()
                var.neighbor_time = var.preprocess_end_time - var.preprocess_start_time

                if var.apply_rsr:
                    var.preprocess_start_time = pg.time.get_ticks()
                    algo.apply_RSR()
                    var.preprocess_end_time = pg.time.get_ticks()
                    var.rsr_time = var.preprocess_end_time - var.preprocess_start_time

                var.start_runtime = pg.time.get_ticks()

                algo.init_search(var.algo)

    def click_save_button(butt: classes.Button) -> None:
        """Open Tkinter dialog for selecting a directory and save/load accordingly,
        """

        tkinter.Tk().withdraw()

        if butt is save_grid_button:

            direct = filedialog.asksaveasfilename(initialdir=grid_path, defaultextension=".pickle")
            if direct:
                save_object = {"start": var.start_node, "end": var.end_node, "grid": var.all_nodes}

                with open(direct, "wb") as file:
                    pickle.dump(save_object, file)

        elif butt is load_grid_button:
            direct = filedialog.askopenfilename(initialdir=grid_path)
            if direct:
                with open(direct, "rb") as file:
                    save_object = pickle.load(file)
                    var.all_nodes = save_object["grid"]
                    var.start_node = save_object["start"]
                    var.end_node = save_object["end"]

                    # this is a little duplicate...
                    var.n_nodes_wide["value"] = len(var.all_nodes)
                    var.n_nodes_high["value"] = len(var.all_nodes[0])
                    grid_n_wide_button.value = len(var.all_nodes)
                    grid_n_high_button.value = len(var.all_nodes[0])
                    var.dirty_blits.append(grid_n_wide_button.get_surface())
                    var.dirty_blits.append(grid_n_high_button.get_surface())

                    # scale grid to screen, as well as possible, might make grid go out of borders
                    var.grid_width = var.window.get_width() - button_background_rect.width - 25  # border
                    var.grid_height = var.window.get_height() - stats_background_rect.height - 25  # border
                    nodes_width = var.grid_width / var.n_nodes_wide["value"]
                    nodes_height = var.grid_height / var.n_nodes_high["value"]

                    start_height = 25

                    # Substracting the first because it will be incremented during the loop
                    position_y = start_height - nodes_height
                    position_x = button_background_rect.width - nodes_width

                    for column in var.all_nodes:
                        position_x += nodes_width

                        for node in column:
                            position_y += nodes_height
                            node.height = nodes_height
                            node.width = nodes_width
                            node.position = (position_x, position_y)
                            node.rect = pg.rect.Rect(node.position, (node.width, node.height))

                        position_y = start_height - nodes_height

                    draw_grid()

    def click_input_button(butt: classes.TextInputButton) -> None:
        """ Handles clicks on input buttons

        :param butt:
        :return:
        """

        for buttons in input_button_list:
            confirm_input(buttons)
        butt.is_activated = True
        var.user_input = ""
        butt.value = var.user_input
        # noinspection PyArgumentList
        var.dirty_blits.append(butt.get_surface(var.user_input))

    def confirm_input(_button_):
        # this could be generalised using their dict of values

        if _button_.is_activated:
            _button_.is_activated = False

            if not (var.user_input.isdigit() and _button_.dict["min"] <= int(var.user_input) <= _button_.dict["max"]):
                if var.user_input.isdigit() and int(var.user_input) >= _button_.dict["max"]:
                    var.user_input = str(_button_.dict["max"])
                    _button_.dict["value"] = int(var.user_input)
                else:
                    try:
                        if _button_.dict["min"] <= int(var.user_input) <= _button_.dict["max"]:
                            _button_.dict["value"] = int(var.user_input)
                    except TypeError:
                        var.user_input = str(_button_.dict["default"])
                        _button_.dict["value"] = int(var.user_input)
                    except ValueError:
                        var.user_input = str(_button_.dict["default"])
                        _button_.dict["value"] = int(var.user_input)

            _button_.dict["value"] = int(var.user_input)
            _button_.value = var.user_input
            var.dirty_blits.append(_button_.get_surface(_button_.value))
            var.user_input = ""

            if _button_ is grid_n_high_button or _button_ is grid_n_wide_button:
                generate_grid()

    def check_dropdown_active():
        dropdown_active = False
        for menu in dropdown_list:
            if menu.is_activated:
                dropdown_active = True
                return dropdown_active
        return dropdown_active

    def handle_dropdown(click_):
        for menu in dropdown_list:
            if menu.is_activated:
                for button_ in menu.buttons:
                    if pg.rect.Rect.colliderect(click_, button_):
                        if menu is dropdown_algo:
                            click_algo_button(button_)

                menu.is_activated = False
                init_buttons()

    # main thread
    # allows to activate buttons from start
    if button:
        if button in state_buttons:
            click_state_button(button)
            return

    # will need to split this up with smaller function for each button... and allow calling reset_search, for example
    for event in var.event_list:
        if event.type == pg.MOUSEBUTTONDOWN:
            click = pg.rect.Rect(pg.mouse.get_pos(), (1, 1))

            if check_dropdown_active():
                handle_dropdown(click)

            else:

                for button in button_list:
                    if pg.rect.Rect.colliderect(button.rect, click):  # else input button confirm and off
                        if not button.is_disabled:

                            if button in setup_buttons:
                                click_setup_button(button)

                            elif button in algo_buttons:
                                # must make BFS true by default
                                click_algo_button(button)

                            elif button in checkbox_buttons:
                                click_checkbox(button)

                            elif button in state_buttons:
                                click_state_button(button)

                            elif button in input_button_list:
                                click_input_button(button)

                            elif button in dropdown_list:
                                button.is_activated = True
                                var.late_blits.append(button.get_surface())

                            elif button in save_button_list:
                                click_save_button(button)

                            elif button is exit_button:
                                pg.quit()
                                sys.exit()

                    elif not pg.rect.Rect.colliderect(button.rect, click) and button in input_button_list:
                        confirm_input(button)

        if event.type == pg.KEYDOWN:
            for input_button in input_button_list:
                if input_button.is_activated:

                    if event.key == pg.K_BACKSPACE:
                        if len(var.user_input) <= 1:
                            var.user_input = ""
                        else:
                            var.user_input = var.user_input[:-1]
                        input_button.value = var.user_input

                    elif event.key == pg.K_RETURN:
                        confirm_input(input_button)  # another for loop of input_buttons in here

                    else:
                        var.user_input += event.unicode
                        input_button.value = var.user_input

                    var.dirty_blits.append(input_button.get_surface(input_button.value))


def display_init():  # make all dirty and genrate grid
    # fill stats background, then it will be handled by stats
    var.window.fill(var.light_grey)
    var.window.fill(var.light_grey, stats_background_rect)

    init_buttons()

    generate_grid()


def handle_display():
    # hard to handle order...
    # for now, blits come after fills, because fills are mostly background...
    for rect in var.early_fills:
        var.window.fill(rect[0], rect[1])

    for surface in var.early_blits:
        var.window.blit(surface[0], surface[1])

    for rect in var.dirty_fills:
        var.window.fill(rect[0], rect[1])

    for surface in var.dirty_blits:
        var.window.blit(surface[0], surface[1])

    for rect in var.late_fills:
        var.window.fill(rect[0], rect[1])

    for surface in var.late_blits:
        var.window.blit(surface[0], surface[1])

    var.early_blits.clear()
    var.early_fills.clear()
    var.dirty_blits.clear()
    var.dirty_fills.clear()
    var.late_blits.clear()
    var.late_fills.clear()

    # blit in dirtyblits
    # fill in dirtyfills


def handle_grid():
    if (start_node_button.is_activated and not start_node_button.is_disabled) or \
            (end_node_button.is_activated and not end_node_button.is_disabled) or \
            (draw_walls_button.is_activated and not draw_walls_button.is_disabled) or \
            (erase_walls_button.is_activated and not erase_walls_button.is_disabled):

        if pg.mouse.get_pressed()[0]:
            click = pg.rect.Rect(pg.mouse.get_pos(), (1, 1))
            if draw_walls_button.is_activated or erase_walls_button.is_activated:
                click = pg.rect.Rect(pg.mouse.get_pos(), (var.brush_size["value"], var.brush_size["value"]))

            for column in var.all_nodes:
                if click.center[0] - var.brush_size["value"] - column[0].width <= column[0].rect.center[0] \
                        <= click.center[0] + var.brush_size["value"] + column[0].width:
                    for node in column:
                        if pg.rect.Rect.colliderect(click, node):
                            if start_node_button.is_activated and not node.is_wall:
                                if var.start_node is not None:
                                    temp = var.start_node
                                    temp.is_start = False
                                    var.start_node = None
                                    var.dirty_fills.append(temp.get_fill())
                                var.start_node = node
                                var.start_node.is_start = True
                                var.dirty_fills.append(node.get_fill())

                            elif end_node_button.is_activated and not node.is_wall:
                                if var.end_node is not None:
                                    temp = var.end_node
                                    temp.is_end = False
                                    var.end_node = None
                                    var.dirty_fills.append(temp.get_fill())
                                var.end_node = node
                                var.end_node.is_end = True
                                var.dirty_fills.append(node.get_fill())

                            elif draw_walls_button.is_activated \
                                    and node is not var.start_node and node is not var.end_node:
                                node.is_wall = True
                                var.dirty_fills.append(node.get_fill())

                            elif erase_walls_button.is_activated \
                                    and node is not var.start_node and node is not var.end_node:
                                node.is_wall = False
                                var.dirty_fills.append(node.get_fill())

                            # MAKE ERASE WALLS BUTTON
                            # ALSO, RANDOM WALLS


def no_path_found():
    text_box_surf = pg.surface.Surface((225, 100), pg.SRCALPHA)
    text_box_surf.fill(var.dark_grey)
    text = var.big_text_font.render("No Paths Found!", True, var.red)
    text_box_surf.blit(text, ((text_box_surf.get_width() - text.get_width()) / 2,
                              (text_box_surf.get_height() - text.get_height()) / 2 - text_box_surf.get_height() / 4))

    var.window.blit(text_box_surf, ((var.window.get_width() - text_box_surf.get_width()) / 2,
                                    (var.window.get_height() - text_box_surf.get_height()) / 2))

    place_ok_button(((var.window.get_width() - ok_button_.rect.w) / 2,
                     (var.window.get_height() - ok_button_.rect.h) / 2 + text_box_surf.get_height() / 4))

    for event in var.event_list:
        if event.type == pg.MOUSEBUTTONDOWN:
            click = pg.rect.Rect(pg.mouse.get_pos(), (1, 1))
            if pg.rect.Rect.colliderect(click, ok_button_.rect):
                # handle_buttons(reset_search_button)
                draw_grid()
                var.running = False


# Creating stat objects ###############################################################################################

# hard coded because I didn't give them rect objects
process_time = classes.Stat("Process time (ms): ", var.black, (stats_background_rect.x + 15, stats_background_rect.y + 15))

neighbor_preprocess_time = classes.Stat("Neighbors Preprocess (ms): ", var.black,
                                    (stats_background_rect.x + 15, stats_background_rect.y + 35))

rsr_preprocess_time = classes.Stat("RSR Preprocess (ms): ", var.black,
                               (stats_background_rect.x + 15, stats_background_rect.y + 55))

fps_stat = classes.Stat("FPS: ", var.black, (stats_background_rect.x + 250, stats_background_rect.y + 15))

path_length = classes.Stat("Path length: ", var.black, (stats_background_rect.x + 250, stats_background_rect.y + 35))


def handle_stats():
    if pg.time.get_ticks() > var.stats_timer:
        # i should do a class for this, so i can have rects

        var.stats_timer += 200

        # update stats values in var

        # append stats to dirty
        var.dirty_fills.append((var.light_grey, stats_background_rect))

        ############# for most stats, check if running before blitting ###################
        #### when we will hit reset, we will reinit EVERYTHING making the useless stats disappear #####

        # process_time = 0 # must start a timer when clicking run
        if var.path_found:
            var.process_time = var.end_runtime - var.start_runtime
        else:
            var.process_time = pg.time.get_ticks() - var.start_runtime

        var.dirty_blits.append(process_time.get_surface(var.process_time))

        var.dirty_blits.append(rsr_preprocess_time.get_surface(var.rsr_time))

        var.dirty_blits.append(neighbor_preprocess_time.get_surface(var.neighbor_time))

        var.dirty_blits.append(fps_stat.get_surface(round(var.clock.get_fps(), 1)))

        var.dirty_blits.append(path_length.get_surface(len(var.shortest_path)))
