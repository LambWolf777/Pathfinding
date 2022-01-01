""" This module handles the user interface (GUI) for the pathfinding visualizer.
It handles the function for clicking on buttons, using input buttons, displaying stats, popups and setting
start/end nodes
It also creates all buttons by the init_gui function
"""

from pickle import load, dump
from os import getcwd, mkdir
from os.path import join, exists
import tkinter
from tkinter import filedialog
from random import randrange
from typing import *

import pygame as pg

import config as cfg
import constants as cst
from classes import Button, DropDownButton, TextInputButton, Background, Checkbox, GridButton, StateButton, \
    AlgoButton, SystemButton, Stat, OkButton, Grid

folder_path = getcwd()

grid_path = join(folder_path, "Grids")

if not exists(grid_path):
    mkdir(grid_path)


def remove_from_root(*attributes, **kwargs) -> None:
    """ Removes the popup_gui from the root/parent Gui.
      Disable the grid from receiving input and redraw it to cover the popup

    necessary kwargs:
         - 'root': Parent/root Gui
         - 'child': Child Gui to remove from Parent

    :param attributes: Used to specify "grid" if it needs to be redrawn
    :param kwargs: See the necessary kwargs above
    :return: None
    """

    try:
        kwargs["root"].objects.remove(kwargs["child"])
        kwargs["root"].draw_all(*attributes)
    except KeyError: pass


class Gui:
    text_input = ""

    def __init__(self, dict_object: Dict[str,  Any], **kwargs: Any) -> None:
        """ Creates a gui window or screen, if a Gui object is added to its objects, it will pass down its click
        events to it recursively until used.

        Specific kwargs:
        - external=True  Allows clicks outside the Gui's objects
        - ext_close=True  Removes Gui from parent Gui on external clicks

        :param dict_object: all objects in dict_object MUST have a display() method and can have an is_clicked() method
            to handle clicks on Buttons (see classes.py for prefabricated classes to use)
        :param kwargs: add attributes to the gui, used for dependency injection.
        """
        self.objects = []
        self.events = []

        for name, obj in dict_object.items():
            setattr(self, name, obj)
            setattr(self, f"{obj.__class__}_group", [])
            self.objects.append(obj)

        for obj in self.objects:
            self.__dict__[f"{obj.__class__}_group"].append(obj)

        self.__dict__.update(kwargs)

    def draw_all(self, *attributes: str) -> None:
        """ Call display() method on all of its objects.

        :param attributes: Call the display() method on additional attributes of the gui
        :return: None
        """

        for obj in self.objects:
            obj.display()

        for key in attributes:
            self.__dict__[key].display()

    def handle_events(self, *additional: Any) -> None:
        """ Handle click and keyboard input events by redistributing to handle click or handle input methods.
        TYPING: *additional: (event.type, function(event, *args) -> None , *args), ...

        :param additional: Allows entering specific (event.type, function, (*args)) tuples to handle other events. The
        function will receive parameters (event, args). (I couldn't get the typing right...)
        :return: None
        """

        for event in self.events:
            if event.type == pg.MOUSEBUTTONDOWN:
                self.handle_clicks(pg.mouse.get_pos())
            elif event.type == pg.KEYDOWN:
                self.handle_input(event)

            for user_event, func, *args in additional:
                if event.type == user_event:
                    func(event, *args)

        self.events.clear()

    def handle_input(self, event: pg.event.Event):
        """ Process Keyboard user input, the entered text is stored as a class attribute.
         A TextInputButton must be activated for this function to run, once the Enter key is pressed,
         it's confirm_input(self.text_input) method will be called with the injected input.

        :param event: must be of type pg.KEYDOWN event
        :return: None
        """

        for button in self.objects:
            if button.__class__ is TextInputButton and button.is_activated:

                if event.key == pg.K_BACKSPACE:
                    if len(Gui.text_input) <= 1:
                        Gui.text_input = ""
                    else:
                        Gui.text_input = Gui.text_input[:-1]
                    button.dict["value"] = Gui.text_input

                elif event.key == pg.K_RETURN:
                    button.confirm_input(Gui.text_input)
                    Gui.text_input = ""

                else:
                    Gui.text_input += event.unicode
                    button.dict["value"] = Gui.text_input

                button.display()

    def handle_clicks(self, mouse_pos: Tuple[int, int], root: 'Gui' = None) -> bool:
        """ Handle clicking events, will recursively pass down click events to child Gui if one is in its objects
        (LIMITED TO ONE CHILD GUI). If any of its objects is clicked, the object's is_clicked() method will be called
        if it has one.

        :param mouse_pos: Coordinates of the cursor
        :param root: parent Gui, allows the child to remove itself from the parent's objects once terminated
        :return: True if click was used, else False
        """

        def check_priority() -> Union[DropDownButton, Gui]:
            """ Check if any of the Gui's objects require priority on clicks (currently only for DropDownButton and
            any child Gui that might be spawned during the program

            :return: object with priority
            """
            priority_to = None

            for obj in self.objects:
                if isinstance(obj, Gui):
                    priority_to = obj
            return priority_to

        def handle_priority(priority_obj: Union[DropDownButton, Gui]) -> bool:
            """ If priority object was found look if any clicks affect it, clicking outside of a DropDownButton's rect
            is allowed and clicks will be registered, but is forbidden for child Gui

            :param priority_obj: The object with priority
            :return: True if click was used, else False
            """
            used = False

            if isinstance(priority_obj, Gui):
                # Inject parent Gui dependency as root, to allow the child Gui to remove itself
                # from the parent's objects when it is terminated
                used = priority_obj.handle_clicks(mouse_pos, root=self)
                try:
                    if not used and not priority_obj.external:
                        used = True
                    if not used and priority_obj.ext_close:
                        priority_obj.src_butt.is_activated = False
                        remove_from_root(root=self, child=priority_obj)
                except AttributeError:
                    pass
            return used

        click = pg.Rect(mouse_pos, (1, 1))
        click_used = False
        prio = check_priority()
        if prio:
            click_used = handle_priority(prio)

        # Clicking outside the child-most Gui is forbidden
        if not click_used:
            for button in self.objects:
                try:
                    if not button.is_disabled:
                        if click.colliderect(button.rect):
                            click_used = True
                            button.is_clicked(gui=self, root=root)

                        elif button.is_activated and button.__class__ is TextInputButton:
                            button.confirm_input(self.text_input)
                except AttributeError:
                    pass
        return click_used


# TODO: alot of setter functions could be shifted into a get_data(gui) method by the pathfinder to unclutter this
#       module and remove some LOC...
def init_gui(pathfinder_obj: Any, grid_obj: Grid) -> Gui:
    """ Initialise the main Gui for the visualizer module, most dependency issues are fixed by injecting the
    necessary objects as arguments.
    First define the necessary functions for all buttons that will be added to the Gui.
     Second, create a dict of all the objects to be added to the Gui as "attribute": object.
     The dict is defined one line at a time because all Button's position depend on the previous ones
    Last we create the Gui from the dict, with pathfinder and grid added as kwargs.

    :param pathfinder_obj: Pathfinder object to link to the Gui (class is not typed to avoid import)
    :param grid_obj: Grid object to link to the Gui
    :return: Gui object
    """

    # Button functions for particular cases:
    def random_walls(self: GridButton) -> None:
        """ Function for the random walls button, 10% of the nodes in the grid will become walls

        :param self: random_walls button object. For GridButton, this parameter is always injected in is_clicked
        :return: None
        """
        self.is_activated = False
        for column in grid_obj.all_nodes:
            for node in column:
                if randrange(11) == 0:
                    if node is not grid_obj.start and node is not grid_obj.end:
                        node.is_wall = True
                        cst.dirty_fills.append(node.get_fill())

    def disp_moves_func(arg: bool) -> None:
        """ Function for the display moves Checkbox. Switches the bool of pathfinder.display_steps attribute.
         Disables the run interval and wait time buttons of the main_gui if display_steps if False, and display
         the buttons the show change.

        :param arg: display_moves_button.is_activated, For Checkboxes this parameter is always injected in is_clicked
        :return: None
        """
        pathfinder_obj.display = arg

        # if "wait_time_button" in gui.__dict__.keys() and "run_interval_button" in gui.__dict__.keys():
        try:
            main_gui_handler.wait_time_button.is_disabled = not arg
            main_gui_handler.run_interval_button.is_disabled = not arg

            main_gui_handler.wait_time_button.display()
            main_gui_handler.run_interval_button.display()
        except KeyError:
            pass

    def diago_func(arg: bool) -> None:
        """ Function for the diago_allowed Checkbox. Switches the bool of pathfinder.diago attribute.

        :param arg: diago_button.is_activated, For Checkboxes this parameter is always injected in is_clicked
        :return: None
        """
        pathfinder_obj.diago = arg

    def apply_rsr_func(arg: bool) -> None:
        """ Function for the apply_rsr Checkbox. Switches the bool of pathfinder.apply_rsr attribute.

        :param arg: apply_rsr_button.is_activated, For Checkboxes this parameter is always injected in is_clicked
        :return: None
        """
        pathfinder_obj.apply_rsr = arg

    def set_algo(self: AlgoButton) -> None:
        """ Set the pathfinder.algo attribute to the algorithm associated with the AlgoButton

        :param self: inject reference to self. For AlgoButton, this parameter is always injected in is_clicked
        :return: None
        """
        pathfinder_obj.algo = self.algo
        main_gui_handler.dropdown_algo.is_activated = False
        remove_from_root(root=main_gui_handler, child=algo_gui)

    def generate() -> None:
        """ Calls the generate method of the grid object, and injects the n_wide and n_high dependencies from
        the main_gui's grid_n_wide and grid_n_high TextInputButtons' values

        :return: None
        """
        grid_obj.generate(main_gui_handler.grid_n_wide_button.dict["value"],
                          main_gui_handler.grid_n_high_button.dict["value"])

    def play_pause(arg: bool = None) -> None:
        """ Switches the pathfinder.running attribute on and off on every press if run conditions are met.
         Call pathfinder.init_search methode if pathfinder.search_is_init is False.
         Disable Buttons that cannot be used during pathfinding

        :param arg: Not needed, but is included for the functions of other StateButtons
        :return: None
        """

        def disable_buttons() -> None:
            """ Disable Buttons that cannot be used during pathfinding

            :return: None
            """
            for obj in main_gui_handler.objects:
                if obj.__class__ is not StateButton and obj is not main_gui_handler.exit_button:
                    try:
                        obj.is_disabled = True
                    except AttributeError:
                        continue
                obj.display()

        def check_conditions() -> bool:
            """ Check that an algorithm is defined, the grid has a starting node and an ending node.
             If no end or start node is defined, adds a popup Gui to the main_gui

            :return: True if pathfinder is ready to run
            """
            if pathfinder_obj.algo:
                if grid_obj.start:
                    if grid_obj.end:
                        return True
                    else:
                        pg.event.post(pg.event.Event(cst.NO_END, announcement="No end Node!"))
                else:
                    pg.event.post(pg.event.Event(cst.NO_START, announcement="No start Node!"))
            return False

        if check_conditions():
            pathfinder_obj.running = not pathfinder_obj.running
            # could add pause/unpause timers...

            if not pathfinder_obj.search_is_init:
                disable_buttons()

                if not pathfinder_obj.display or main_gui_handler.run_interval_button.dict["value"] == -1:
                    # update display to show disabled buttons before pathfinder starts looping
                    handle_display()
                    pg.display.flip()

                pathfinder_obj.init_search()

    def reset(partial: bool = False) -> None:
        """ Stops the pathfinder, and reset all necessary attributes, also reset the grid.
         If partial, leaves walls, start and end nodes as is

         :param partial: True if resetting search, False if resetting grid
         :return: None"""

        pathfinder_obj.running = False

        if not partial:
            if grid_obj.start is not None:
                temp = grid_obj.start
                grid_obj.start = None
                temp.is_start = False
                cst.dirty_fills.append(temp.get_fill())
            if grid_obj.end is not None:
                temp = grid_obj.end
                grid_obj.end = None
                temp.is_end = False
                cst.dirty_fills.append(temp.get_fill())

        pathfinder_obj.search_is_init = False
        pathfinder_obj.dijkstra_cost_so_far = 0
        pathfinder_obj.running = False
        pathfinder_obj.path_found = False
        pathfinder_obj.frontier = []
        pathfinder_obj.queue.clear()
        pathfinder_obj.to_be_removed = []
        pathfinder_obj.shortest_path = []
        pathfinder_obj.run_timer = 0
        pathfinder_obj.start_time = 0
        pathfinder_obj.end_time = 0
        pathfinder_obj.neighbors_prep_dt = 0
        pathfinder_obj.rsr_prep_dt = 0
        pathfinder_obj.algo_dt = 0

        for column in grid_obj.all_nodes:
            for node in column:

                node.neighbors = None
                node.came_from = None

                if node.update_color() is not cst.BLACK:

                    if not partial:
                        node.is_wall = False
                        node.is_end = False
                        node.is_start = False

                    node.is_sym_rect = False
                    node.is_border = False
                    node.visited = False
                    node.is_path = False

                    cst.dirty_fills.append(node.get_fill())

        for obj in main_gui_handler.objects:
            try:
                obj.is_disabled = False
                obj.display()

            except AttributeError:  # (Backgrounds)
                continue

        main_gui_handler.run_interval_button.is_disabled = \
            main_gui_handler.run_interval_button.is_disabled = \
            not main_gui_handler.display_moves_button.is_activated

    # TODO: try resetting the focus to pygame
    def save() -> None:
        """ Save the Grid object as a Pickle file in the Grids folder (or other)

        :return: None
        """
        tkinter.Tk().withdraw()

        direct = filedialog.asksaveasfilename(initialdir=grid_path, defaultextension=".pickle")
        if direct:
            save_object = {"start": grid_obj.start, "end": grid_obj.end, "grid": grid_obj.all_nodes}

            with open(direct, "wb") as file:
                dump(save_object, file)

    def load_grid() -> None:
        """ Load a grid object from the Grids folder (or other), update values, scale the grid and
        show all changes

        :return: None
        """

        def scale_and_draw() -> None:
            """ Scale the grid object to fit current screen size, draw the grid

            :return: None
            """
            # scale grid to screen, as well as possible, might make grid go out of borders
            nodes_width = grid_obj.width / main_gui_handler.grid_n_wide_button.dict["value"]
            nodes_height = grid_obj.height / main_gui_handler.grid_n_high_button.dict["value"]

            start_height = 25

            # Substracting the first because it will be incremented during the loop
            position_y = start_height - nodes_height
            position_x = cfg.button_background_rect.width - nodes_width

            for column in grid_obj.all_nodes:
                position_x += nodes_width

                for node in column:
                    position_y += nodes_height
                    node.height = nodes_height
                    node.width = nodes_width
                    node.position = (position_x, position_y)
                    node.rect = pg.rect.Rect(node.position, (node.width, node.height))

                position_y = start_height - nodes_height

            grid_obj.display()

        def update_values(save_object: dict) -> None:
            """ Updates the attributes of the grid object and the values of the grid_n_wide and grid_n_high buttons
            and display changes
            
            :param save_object: save object loaded from pickle file
            :return: None
            """

            grid_obj.all_nodes = save_object["grid"]
            grid_obj.start = save_object["start"]
            grid_obj.end = save_object["end"]

            main_gui_handler.grid_n_wide_button.dict["value"] = len(grid_obj.all_nodes)
            main_gui_handler.grid_n_high_button.dict["value"] = len(grid_obj.all_nodes[0])
            main_gui_handler.grid_n_wide_button.display()
            main_gui_handler.grid_n_high_button.display()

        tkinter.Tk().withdraw()

        direct = filedialog.askopenfilename(initialdir=grid_path)
        if direct:
            with open(direct, "rb") as file:
                save_object_ = load(file)

                update_values(save_object_)

                scale_and_draw()

    def exit_func() -> None:
        """ Exit program.
        :return: None
        """
        pg.event.post(pg.event.Event(pg.QUIT))

    # creating GUI #####################################################################################################
    main_gui: Dict[str, Union[pg.Rect, GridButton, AlgoButton, Checkbox, DropDownButton, TextInputButton, StateButton,
                              SystemButton, Background]] = dict()

    # It's a bit ugly doing it like this but it's the only way I know to keep reference to the previous entry.
    # Also I wanted to make a flexible GUI object to be able to use it elsewhere (pop-ups)

    main_gui["button_background_rect"] = Background(cst.LIGHT_GREY, cfg.button_background_rect)

    # grid placement buttons
    main_gui["start_node_button"] = GridButton((15, 25), "Place Start")

    main_gui["end_node_button"] = GridButton((main_gui["start_node_button"].rect.right + 5,
                                              main_gui["start_node_button"].rect.top), "Place End")

    main_gui["draw_walls_button"] = GridButton((15, main_gui["start_node_button"].rect.bottom + 10),
                                               "Draw walls")

    main_gui["erase_walls_button"] = GridButton((main_gui["draw_walls_button"].rect.right + 5,
                                                 main_gui["draw_walls_button"].rect.top), "Erase walls")

    main_gui["random_walls_button"] = GridButton((15, main_gui["draw_walls_button"].rect.bottom + 10),
                                                 "Random walls", func=random_walls)

    # algo buttons
    algo_buttons = [AlgoButton((0, 0), "Flood Fill", "bfs", active_color=cst.BLACK, rounded=False, func=set_algo),
                    AlgoButton((0, 0), "A*", "astar", active_color=cst.BLACK, rounded=False, func=set_algo),
                    AlgoButton((0, 0), "Dijkstra", "dijkstra", active_color=cst.BLACK, rounded=False, func=set_algo)]
    algo_buttons[0].is_activated = True
    algo_gui = Gui({f"{button.algo}": button for button in algo_buttons}, external=True, ext_close=True)

    main_gui["dropdown_algo"] = DropDownButton((15, main_gui["random_walls_button"].rect.bottom + 30), "Algo: ",
                                               algo_buttons, child_gui=algo_gui)

    main_gui["diago_button"] = Checkbox("Diagonal moves", (15, main_gui["dropdown_algo"].rect.bottom + 10),
                                        False, diago_func)

    main_gui["apply_rsr_button"] = Checkbox("Apply RSR", (15, main_gui["diago_button"].rect.bottom + 10),
                                            False, apply_rsr_func)

    main_gui["display_moves_button"] = Checkbox("Display moves", (15, main_gui["apply_rsr_button"].rect.bottom + 10),
                                                True, disp_moves_func)

    main_gui["run_interval_button"] = TextInputButton({"min": -1, "max": 9999, "default": 0, "value": 0},
                                                      (15, main_gui["display_moves_button"].rect.bottom + 10), 40,
                                                      "Run: ")

    main_gui["wait_time_button"] = TextInputButton({"min": 0, "max": 9999, "default": 0, "value": 0},
                                                   (main_gui["run_interval_button"].rect.right + 5,
                                                   main_gui["display_moves_button"].rect.bottom + 10), 40, "Wait: ")

    main_gui["reset_button"] = StateButton((15, main_gui["run_interval_button"].rect.bottom + 30),
                                           "Reset Grid", reset)

    main_gui["reset_search_button"] = StateButton((main_gui["reset_button"].rect.right + 5,
                                                   main_gui["reset_button"].rect.top), "Reset Search", reset, True)

    main_gui["play_pause_button"] = StateButton((15, main_gui["reset_search_button"].rect.bottom + 10),
                                                "Play/Pause", play_pause)

    main_gui["grid_n_wide_button"] = TextInputButton({"min": 3, "max": cfg.window.get_width() - 205 - 25,
                                                      "default": 100, "value": 100},
                                                     (15, main_gui["play_pause_button"].rect.bottom + 30), 50,
                                                     "Nodes in width: ", func=generate)

    main_gui["grid_n_high_button"] = TextInputButton({"min": 3, "max": cfg.window.get_height() - 125 - 25,
                                                      "default": 100, "value": 100},
                                                     (15, main_gui["grid_n_wide_button"].rect.bottom + 10), 40,
                                                     "Nodes in height: ", func=generate)

    main_gui["brush_size_button"] = TextInputButton({"min": 1, "max": 200, "default": 1, "value": 1},
                                                    (15, main_gui["grid_n_high_button"].rect.bottom + 10), 30,
                                                    "Brush size: ")

    main_gui["save_grid_button"] = SystemButton((15, main_gui["brush_size_button"].rect.bottom + 30),
                                                "Save Grid", save)

    main_gui["load_grid_button"] = SystemButton((main_gui["save_grid_button"].rect.right + 5,
                                                 main_gui["save_grid_button"].rect.top), "Load Grid", load_grid)

    main_gui["exit_button"] = SystemButton((15, main_gui["load_grid_button"].rect.bottom + 30), "Exit", exit_func)

    main_gui_handler = Gui(main_gui, pathfinder=pathfinder_obj, grid=grid_obj)

    return main_gui_handler


def handle_display() -> None:
    """ Does all the fills and blits to the window then clear channel, fills are made before blits.
     All the program's fill and blits orders are appended to one of the lists in cst.to_display
     (see constants.py module), for special cases there is an early and a late channel.

    :return: None
    """

    for group in cst.to_display:
        for i, j in group:
            if i.__class__ is pg.Surface:
                cfg.window.blit(i, j)
            else:
                cfg.window.fill(i, j)
        group.clear()


def pop_up(announcement: str) -> Gui:
    """ Creates a Pop-up window Gui with a single OK button to dismiss the message and remove the Gui from its parent
     Gui.
     Use as follows: from the main Gui, on event: main_Gui.objects.append(pop_up("hello"))

    :param announcement: Text to be displayed on the popup window
    :return: A Gui object representing the popup window
    """

    def ok_func(root: Gui, child: Gui) -> None:
        """ Removes the popup_gui from the root/parent Gui.
          Disable the grid from receiving input and redraw it to cover the popup

        :param root: Parent/root Gui
        :param child: Child Gui to remove from parent
        :return: None
        """
        root.grid.disabled = pg.time.get_ticks() + 100
        remove_from_root("grid", root=root, child=child)

    text_surf = cst.big_text_font.render(announcement, True, cst.RED)

    bg_width = 2 * text_surf.get_width()
    bg_height = 4 * text_surf.get_height()

    text_obj = (text_surf, ((bg_width - text_surf.get_width()) / 2, (bg_height - text_surf.get_height()) / 3))

    dimension_butt = Button((0, 0), "OK")
    ok_button = OkButton(((cfg.window.get_width() - dimension_butt.rect.w) / 2,
                          (cfg.window.get_height() - dimension_butt.rect.h) / 2 + 100 / 4), "OK", func=ok_func)

    background = Background(cst.DARK_GREY, pg.Rect(((cfg.window.get_width() - bg_width) / 2,
                                                    (cfg.window.get_height() - bg_height) / 2), (bg_width, bg_height)),
                            text_obj)

    popup = Gui({"popup_bg": background, "ok_butt": ok_button})
    popup.draw_all()

    return popup


class StatsHandler:
    def __init__(self, background: Background, increment: int = 200, **kwargs: Stat) -> None:
        """ Creates a Singleton Stats handler for displaying Stat objects on a Background
        (Background is important so the anti aliased text does not become opaque.

        :param background: Background object where the stats will be displayed (positioning is not automatic)
        :param increment: Delay between updates of the stats in ms
        :param kwargs: add stat objects as attributes of the stat handler ("attribute" = object) and in a list of stats
        """
        self.__dict__.update(kwargs)
        self.stats = [obj for obj in self.__dict__.values() if obj.__class__ is Stat]
        self.background = background
        self.chrono = 0
        self.increment = increment

    def display(self) -> None:
        """ Display all Stat object in self.stats.

        :return: None
        """
        self.background.display()
        for stat in self.stats:
            stat.display()

    def timer(self) -> bool:
        """ Handles timing of the stats handler

        :return: True if it's time to display
        """
        if pg.time.get_ticks() >= self.chrono:
            self.chrono += self.increment
            return True
        return False

    def main(self) -> None:
        """ Main loop of the stats handler, it's the only thing that needs to be called once it has been initialised

        :return: None
        """
        if self.timer():
            self.display()


def init_stats(pathfinder: Any) -> StatsHandler:
    """ Initialise the StatsHandler object, with injected dependency to the pathfinder to access stats values.
    First define the getter functions for the Stat objects
    Then Instantiate the Stat object as kwargs for the StatsHandler

    :param pathfinder: Pathfinder object of the program (Singleton) (class not typed to avoid import)
    :return: StatsHandler object
    """

    # defining stats getters
    def get_algo_dt() -> float:
        """ Get algorithm process time from the pathfinder or the time since it started processing"""
        return round(pathfinder.algo_dt, 2)

    def get_neighbor_dt() -> float:
        """ Get the time taken for preprocessing the grid's nodes' neighbors from the pathfinder"""
        return round(pathfinder.neighbors_prep_dt, 2)

    def get_rsr_dt() -> float:
        """ Get the time taken for preprocessing Rectangular Symmetry Reduction from the pathfinder"""
        return round(pathfinder.rsr_prep_dt, 2)

    def get_path_len() -> float:
        """ Get the lenght of the shortest path found by the pathfinder"""
        return len(pathfinder.shortest_path)

    def get_fps() -> float:
        """ Get the fps of the program"""
        return round(cfg.clock.get_fps(), 1)

    stat_handler = StatsHandler(
        background=Background(cst.LIGHT_GREY, cfg.stats_background_rect), increment=200,

        process_time=Stat("Process time (ms): ", cst.BLACK,
                          (cfg.stats_background_rect.x + 15, cfg.stats_background_rect.y + 15), get_algo_dt),

        neighbor_prep_time=Stat("Neighbors Preprocess (ms): ", cst.BLACK, (cfg.stats_background_rect.x + 15,
                                cfg.stats_background_rect.y + 35), get_neighbor_dt),

        rsr_prep_time=Stat("RSR Preprocess (ms): ", cst.BLACK,
                           (cfg.stats_background_rect.x + 15, cfg.stats_background_rect.y + 55), get_rsr_dt),

        fps_stat=Stat("FPS: ", cst.BLACK,
                      (cfg.stats_background_rect.x + 300, cfg.stats_background_rect.y + 15), get_fps),

        path_length=Stat("Path length: ", cst.BLACK,
                         (cfg.stats_background_rect.x + 300, cfg.stats_background_rect.y + 35), get_path_len))

    return stat_handler
