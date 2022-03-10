"""The classes module stores the Node, Grid, Stat class and various classes used in the GUI,
it's purpose is to remove clutter from the gui module"""

from typing import *
import pygame as pg

import config as cfg

import constants as cst


# TODO: Use bitwise flags instead
class Node:
    """Object for representing every tile (node on the grid)"""

    # Those attributes will be used as instance attributes, but it was simpler to define them here since they
    # always start with the same values

    # Node flags:
    PATH = 1
    WALL = 2
    VISITED = 4
    SYM_RECT = 8
    BORDER = 16
    START = 32
    END = 64
    ALL_FLAGS = 127

    # is_path = False
    # is_wall = False
    # visited = False
    neighbors = None
    came_from = None
    # came_from_diago = False  # useless now i think
    cost_so_far = 0
    heuristic = 0
    priority = 0
    color = cst.BLACK

    # for RSR
    # sym_rect = None
    # is_sym_rect = False
    # is_border = False
    # is_start = False
    # is_end = False

    def __init__(self, column: int, row: int, position: Tuple[int, int], node_width: int, node_height: int) -> None:
        """ Create a Node object

        :param column: Column index of the node in the Grid.all_nodes
        :param row: Row index of the node in the Grid.all_nodes
        :param position: Top left position in pixels on the screen
        :param node_width: Width of the node's rect (to be filled when drawn)
        :param node_height: Height of the node's rect (to be filled when drawn)
        """

        self.position = position
        self.column = column
        self.row = row

        self.status = 0  # bitwise flags

        self.width = node_width
        self.height = node_height
        self.rect = pg.rect.Rect(self.position, (node_width, node_height))

    def update_color(self) -> None:
        """ Update the node's color according to its current status"""

        self.color = cst.BLACK
        if self.status & Node.START:
            self.color = cst.BLUE
        elif self.status & Node.END:
            self.color = cst.GREEN
        elif self.status & Node.PATH:
            self.color = cst.PURPLE
        elif self.status & Node.WALL:
            self.color = cst.WHITE
        elif self.status & Node.VISITED:
            self.color = cst.YELLOW
        elif self.status & Node.BORDER:
            self.color = cst.RED
        elif self.status & Node.SYM_RECT:
            self.color = cst.ORANGE

    # TODO: Change to a display method
    def get_fill(self) -> [Tuple[int, int, int, Optional[int]], pg.Rect]:
        """ Return information needed for filling to screen, use to append to dirty_fills

        :return: Color tuple and rect to be filled
        """

        self.update_color()

        return self.color, self.rect

    # TODO: Optimize this method
    def update_sym_rect_neighbors(self, grid: List[List['Node']]) -> None:
        """ For a Node in the border of a symmetry rectangle, change its neighbor in the symmetry rectangle for
        the next one that is a border (jump through rectangle)"""

        def cycle_node(direction: str, current: 'Node') -> Tuple['Node', int]:
            """ Increment neighbor's position in given direction until the neighbor is a border

            :param direction: current's direction key from initial node
            :param current: current neigbor of the initial node
            :return: final neighbor and cost multiplier (number of nodes from initial to final)
            """

            cost_multiplier = 1

            while current.status & Node.SYM_RECT:
                cost_multiplier += 1
                new_col, new_row = cst.CYCLE_MOVES[direction](current.column, current.row)
                current = grid[new_col][new_row]

            return current, cost_multiplier

        for direction, (neighbor, cost) in self.neighbors.items():
            if neighbor.status & Node.SYM_RECT:
                current, cost_mult = cycle_node(direction, neighbor)
                self.neighbors[direction] = current, cost * cost_mult

    def get_available_neighbors(self, grid) -> List[Tuple['Node', int]]:
        """ Return available (not walls and not visited) neighbors and their cost as a list.

        :return: List of adjacent node objects
        """

        neighbors = []

        for node, cost in self.neighbors.values():

            if not node.status & (Node.WALL | Node.VISITED):
                neighbors.append((node, cost))

        return neighbors

    def get_neighbors(self, grid: List[List['Node']], diago_allowed: bool = False) -> None:
        """ Sets a dict of all adjacent neighbors in the form neighbors["direction"] = node, cost

        :param grid: Grid on which the node is located
        :param diago_allowed: Sets if diagonal neighbors should be included, does not allow corner-cutting
        :return: None
        """

        # could definitely make this more compact, see update_sym_rect_neighbors()

        neighbors = {}

        try:
            neighbors["right"] = grid[self.column + 1][self.row], 1  # right
        except IndexError:
            pass
        try:
            neighbors["down"] = grid[self.column][self.row + 1], 1  # down
        except IndexError:
            pass

        if not self.row == 0:
            neighbors["up"] = grid[self.column][self.row - 1], 1  # up
        if not self.column == 0:
            neighbors["left"] = grid[self.column - 1][self.row], 1  # left

        if diago_allowed:

            try:
                if not neighbors["down"][0].status & Node.WALL\
                        and not neighbors["right"][0].status & Node.WALL:
                    neighbors["downright"] = grid[self.column + 1][self.row + 1], 1.41421  # botright
            except KeyError:
                pass
            try:
                if not neighbors["up"][0].status & Node.WALL\
                        and not neighbors["right"][0].status & Node.WALL:
                    neighbors["topright"] = grid[self.column + 1][self.row - 1], 1.41421  # topright
            except KeyError:
                pass

            try:
                if not neighbors["down"][0].status & Node.WALL\
                        and not neighbors["left"][0].status & Node.WALL:
                    neighbors["downleft"] = grid[self.column - 1][self.row + 1], 1.41421  # botleft
            except KeyError:
                pass
            try:
                if not neighbors["up"][0].status & Node.WALL\
                        and not neighbors["left"][0].status & Node.WALL:
                    neighbors["topleft"] = grid[self.column - 1][self.row - 1], 1.41421  # topleft
            except KeyError:
                pass

        self.neighbors = neighbors
        if self.status & Node.BORDER:
            self.update_sym_rect_neighbors(grid)


class Background:
    """ Glorified rectangle that can have surfaces blitted to it"""

    def __init__(self, color: Tuple[int, int, int, Optional[int]], rect: pg.rect.Rect,
                 *args: Tuple[pg.Surface, Tuple[Union[int, float], Union[int, float]]]) -> None:
        """ Create Glorified rectangle that can have surfaces blitted to it.

        :param color: Base color of the rect
        :param rect: Rectangle for the Background
        :param args: All surface to be blitted on the Background, add as (surface, (pos_x, pos_y))
        """
        self.color = color
        self.rect = rect
        self.surface = pg.Surface((self.rect.width, self.rect.height))
        self.surface.fill(self.color)
        for surface, position in args:
            self.surface.blit(surface, position)

    def display(self, channel: List = cst.dirty_blits) -> None:
        """ Add blitting information the to specified to_display channel

        :param channel: Channel to add information to (early, late...)
        :return: None
        """
        channel.append((self.surface, self.rect))


class Button:
    """Basic Class for buttons, allows to set conditions to active, to be clicked, drawn, etc...
    is a clickable rectangle with text in it."""

    disabled_butt_color = cst.DARK_GREY
    disabled_text_color = cst.MEDIUM_GREY

    def __init__(self, position: Tuple[int, int], text: AnyStr,
                 text_color: Union[Tuple[int, int, int], Tuple[int, int, int, int]] = (255, 255, 255),
                 active_color: Union[Tuple[int, int, int], Tuple[int, int, int, int]] = (0, 0, 255),
                 off_color: Union[Tuple[int, int, int], Tuple[int, int, int, int]] = (0, 0, 0),
                 rounded: Optional[bool] = True) -> None:
        # rect made around text size + 5 all around

        """Create button with specific parameters, is a clickable rectangle with text in it.

        :param position: Topleft corner of the button
        :param text: String to display in button
        :param text_color: Color to display text in
        :param active_color: Button Color when it is active
        :param off_color: Button color when it is inactive
        :param rounded: Rounds the corners of the button if True
        """

        self.is_activated = False
        self.is_disabled = False
        self.rounded = rounded
        self.position = position
        self.base_text_color = text_color
        self.active_color = active_color
        self.off_color = off_color
        self.color = self.get_colors()[0]
        self.text = text
        self.text_surface = cst.text_font.render(self.text, True, self.get_colors()[1])  # the color will not update
        self.text_rect = self.text_surface.get_rect()
        self.rect = pg.rect.Rect(self.position, (self.text_rect.width + 10, self.text_rect.height + 10))

    def get_colors(self) -> [[int, int, int, Optional[int]], Tuple[int, int, int, Optional[int]]]:
        """ Return button and text colors according to activated status

        :return: Button color and text color as rgba tuples
        """

        color_ = self.off_color
        text_color_ = self.base_text_color

        if self.is_activated:
            color_ = self.active_color
            # could change text color when activated here
        if self.is_disabled:
            color_ = self.disabled_butt_color
            text_color_ = self.disabled_text_color
        return color_, text_color_

    def display(self, channel: List = cst.dirty_blits) -> None:
        """ Add blitting information the to specified to_display channel

        :param channel: Channel to add information to (early, late...)
        :return: None
        """

        self.color = self.get_colors()[0]  # im not sure if calling this to blit when pressing
        # will update the color as well... indeed needed to call this funct
        self.text_surface = cst.text_font.render(self.text, True, self.get_colors()[1])  # the color will not update

        surface = pg.surface.Surface((self.rect.width, self.rect.height), pg.SRCALPHA)

        if self.rounded is True:
            pg.draw.rect(surface, self.color, surface.get_rect(), border_radius=8)
        else:
            surface.fill(self.color)

        surface.blit(self.text_surface, (5, 5))

        channel.append((surface, self.position))


class OkButton(Button):
    def __init__(self, position: Tuple[int, int], text: str = "OK",
                 func: Callable = lambda *arg: None):
        """ Creates an OK button with a function specified in parameters

        :param position: Top left corner position of the button
        :param text: text to display on button
        :param func: Function specific to the button, will be called with kwargs from the Gui in handle_clicks
        """
        super().__init__(position, text)
        self.func = func

    def is_clicked(self, **kwargs: [str, Any]) -> None:
        """ Function that will be called with kwargs from the Gui in handle_clicks when the button is clicked.
         Calls its self.func attribute with the Gui object calling it as argument if available in kwargs: func(gui)

        :param kwargs: Contains all the parameters to be passed to any is_clicked function
        :return: None
        """
        if kwargs["root"] and kwargs["gui"]:
            root_gui = kwargs["root"]
            child_gui = kwargs["gui"]
            self.func(root_gui, child_gui)


class GridButton(Button):
    """Subclass of Button in order to regroup Buttons by their purpose and generalise the is_clicked methode"""

    group = []

    def __init__(self, position: Tuple[int, int], text: AnyStr, func=lambda x: None):
        """ Creates a GridButton button with a function specified in parameters

                :param position: Top left corner position of the button
                :param text: text to display on button
                :param func: Function specific to the button, will be called with self and kwargs from is_clicked
        """
        super().__init__(position, text)
        self.func = func
        GridButton.group.append(self)

    def is_clicked(self, **kwargs: [str, Any]) -> None:
        """ Function that will be called with kwargs from the Gui in handle_clicks when the button is clicked.
                 Turns off every other GridButton except self, toggles self.is_activated, display changes
                 Calls its self.func attribute with itself as argument: func(self)

                :param kwargs: Contains all the parameters to be passed to any is_clicked function
                :return: None
        """
        for button in GridButton.group:
            if button.is_activated and button is not self:
                button.is_activated = False
                button.display()

        self.is_activated = not self.is_activated
        self.func(self)
        self.display()


class AlgoButton(Button):
    """Subclass of Button in order to regroup Buttons by their purpose and generalise the is_clicked methode"""

    group = []

    def __init__(self, position: Tuple[int, int], text: AnyStr, algo: str,
                 text_color: Union[Tuple[int, int, int], Tuple[int, int, int, int]] = (255, 255, 255),
                 active_color: Union[Tuple[int, int, int], Tuple[int, int, int, int]] = (0, 0, 255),
                 off_color: Union[Tuple[int, int, int], Tuple[int, int, int, int]] = (0, 0, 0),
                 rounded: Optional[bool] = True,
                 func: Callable[['AlgoButton'], None] = lambda self: None):
        """ Creates an AlgoButton with a function specified in parameters

                :param position: Top left corner position of the button
                :param text: text to display on button
                :param func: Function specific to the button, will be called with self kwargs in is_clicked
                """
        super().__init__(position, text, text_color, active_color, off_color, rounded)
        self.algo = algo
        self.func = func
        AlgoButton.group.append(self)

    def is_clicked(self, **kwargs) -> None:
        """ Function that will be called with kwargs from the Gui in handle_clicks when the button is clicked.
                 Turns off every other AlgoButton except self, activates self, display changes
                 Calls its self.func attribute with itself as argument: func(self)

                :param kwargs: Contains all the parameters to be passed to any is_clicked function
                :return: None
        """
        for button in AlgoButton.group:
            button.is_activated = False

        self.is_activated = True
        # should be updated since it's already in the blits queue

        self.func(self)


class StateButton(Button):
    """Subclass of Button in order to regroup Buttons by their purpose and generalise the is_clicked methode"""

    group = []

    def __init__(self, position: Tuple[int, int], text: AnyStr, func=lambda arg: None, arg=None):
        """ Creates a StateButton with a function and its arg specified in parameters

                :param position: Top left corner position of the button
                :param text: text to display on button
                :param func: Function specific to the button, will be called with self.arg and kwargs from is_clicked
                """
        super().__init__(position, text)
        self.func = func
        self.arg = arg
        StateButton.group.append(self)

    def is_clicked(self, **kwargs) -> None:
        """ Function that will be called with kwargs from the Gui in handle_clicks when the button is clicked.
                Calls self.func attribute with its arg attribute as argument: func(self.arg)

                :param kwargs: Contains all the parameters to be passed to any is_clicked function
                :return: None
        """

        self.func(self.arg)


class SystemButton(Button):
    """Subclass of Button in order to regroup Buttons by their purpose and generalise the is_clicked methode"""

    group = []

    def __init__(self, position: Tuple[int, int], text: AnyStr, func=lambda: None):
        """ Creates an OK button with a function specified in parameters

                :param position: Top left corner position of the button
                :param text: text to display on button
                :param func: Function specific to the button, will be called with kwargs from the Gui in handle_clicks
                """
        super().__init__(position, text)
        self.func = func
        SystemButton.group.append(self)

    def is_clicked(self, **kwargs) -> None:
        """ Function that will be called with kwargs from the Gui in handle_clicks when the button is clicked.
                Calls self.func attribute with no argument: func()

                :param kwargs: Contains all the parameters to be passed to any is_clicked function
                :return: None
        """

        self.func()


class TextInputButton:  # for text buttons
    """ More intricate button, with header and input box.
    Allows for user input, GUI will handle value confirmations, default and allowed values
    """

    group = []
    disabled_butt_color = cst.DARK_GREY
    disabled_text_color = cst.MEDIUM_GREY

    def __init__(self, _dict_: Dict, position: [Union[int, float], Union[int, float]], input_width: int, text: AnyStr,
                 headline_text_color: Tuple[int, int, int, Optional[int]] = (0, 0, 0),
                 text_color: Tuple[int, int, int, Optional[int]] = (255, 255, 255),
                 active_color: Tuple[int, int, int, Optional[int]] = (0, 0, 255),
                 off_color: Tuple[int, int, int, Optional[int]] = (0, 0, 0),
                 rounded: Optional[bool] = True, func=lambda: None) -> None:

        # rect made around text size + 5 all around
        """ Create the text input button

        :param _dict_: Contains min, max, default and initial values of the input
        :param position: topleft corner of the button
        :param input_width: input box width
        :param text: text for the HEADLINER
        :param headline_text_color: color for the headline text
        :param text_color: color for the input text
        :param active_color: color for the input box when active
        :param off_color: color for the input box when inactive
        :param func: Function to be called after at the end of confirm_input
        """

        TextInputButton.group.append(self)

        self.dict = _dict_
        self.is_activated = False
        self.is_disabled = False
        self.position = position

        self.rounded = rounded
        self.base_text_color = text_color
        self.active_color = active_color
        self.off_color = off_color
        self.color = self.get_colors()[0]
        self.input_width = input_width

        self.headline = cst.text_font.render(text, True, headline_text_color)
        self.headline_rect = self.headline.get_rect()

        self.input_value = cst.number_font.render(str(self.dict["value"]), True, self.get_colors()[1])
        self.input_rect = pg.rect.Rect(0, 0, self.input_width, self.input_value.get_rect().h + 10)

        self.rect = pg.rect.Rect(self.position, (self.headline_rect.width + self.input_rect.width + 10,
                                                 self.headline_rect.height + 10))

        self.func = func

    def get_colors(self) -> Tuple[Tuple[int, int, int, Optional[int]], Tuple[int, int, int, Optional[int]]]:
        """ Return box color and text color (input text) according to button status

        :return: input box color and input text color
        """

        color_ = self.off_color
        text_color_ = self.base_text_color

        if self.is_activated:
            color_ = self.active_color
            # could change text color when activated here
        if self.is_disabled:
            color_ = self.disabled_butt_color
            text_color_ = self.disabled_text_color
        return color_, text_color_

    def display(self, value: Optional[Union[str, int]] = None, channel=cst.dirty_blits) -> None:
        """ Add blitting information the to specified to_display channel

        :param value: Add a value to change the button's value before displaying (permanent)
        :param channel: Channel to add information to (early, late...)
        :return: None
        """

        if not value:
            value = self.dict["value"]

        self.color = self.get_colors()[0]

        self.input_value = cst.number_font.render(str(value), True, self.get_colors()[1])
        self.input_rect = pg.rect.Rect(0, 0, self.input_width, self.input_value.get_rect().h + 10)  # duplicate

        surface = pg.surface.Surface((self.rect.width, self.rect.height), pg.SRCALPHA)
        surface.fill(cst.LIGHT_GREY, self.headline_rect)

        if self.rounded is True:
            pg.draw.rect(surface, self.color,
                         pg.rect.Rect(self.headline_rect.w, 0, self.input_rect.w, self.input_rect.h), border_radius=8)
        else:
            surface.fill(self.color, pg.rect.Rect(self.headline_rect.w, 0, self.input_rect.w, self.input_rect.h))

        surface.blit(self.headline, (0, 5))

        if self.is_activated:
            surface.blit(self.input_value, (self.headline_rect.w + 5, 5),
                         pg.rect.Rect(max(self.input_value.get_width() - (self.input_rect.w - 10), 0), 0,
                                      self.input_rect.w - 5, self.input_rect.h))
        else:
            surface.blit(self.input_value, (self.headline_rect.w + 5, 5))

        channel.append((surface, self.position))

    def confirm_input(self, text_input: str) -> None:
        """ Checks if the text_input is valid according to the button's dict, if it is, replace dict["value"].
         Else, fix the value accordingly and change it, display changes.
         Calls self.func()

        :param text_input: Input value
        :return: None
        """

        def fix_value(txt_input: str) -> int:
            """ Return min if input is lower than min
             Return max if input is higher than max
             If input is not comparable or is not numeric, return Default value

            :param txt_input: input value
            :return: Valid value
            """
            try:
                if int(txt_input) > self.dict["max"]:
                    return self.dict["max"]
                elif int(txt_input) < self.dict["min"]:
                    return self.dict["min"]
            except (TypeError, ValueError):
                return self.dict["default"]
            return int(txt_input)

        if self.is_activated:
            self.is_activated = False

            self.dict["value"] = fix_value(text_input)
            self.display(self.dict["value"])

            self.func()

    def is_clicked(self, **kwargs):
        """ Function that will be called with kwargs from the Gui in handle_clicks when the button is clicked.
            Activates the button (starts receiving input) and makes any activated TextInputButton confirm_input

            :param kwargs: Contains all the parameters to be passed to any is_clicked function
            :return: None
        """
        if "gui" in kwargs.keys():
            for button in TextInputButton.group:
                button.confirm_input(kwargs["gui"].text_input)
        self.is_activated = True
        self.dict["value"] = ""
        self.display()


class Checkbox:
    """ Checkbox button, similar to Button, but as a checkbox (expected to stay active, whereas buttons are expected to
    be active only while used (ex: draw walls) and then turned off
    """

    disabled_check_color = cst.MEDIUM_GREY
    disabled_box_color = cst.DARK_GREY
    text_color = box_color = cst.BLACK
    check_color = cst.WHITE

    def __init__(self, headline: str, position: Tuple[Union[int, float], Union[int, float]],
                 activated: bool = False, func=lambda active: None) -> None:
        """ Create checkbox

        :param headline: Headline text, similar to input button headline, ex: "headline": [x]
        :param position: topleft corner position
        :param activated: boolean, True means active ... obviously
        :param func: specific function to be called when clicked
        """

        self.is_disabled = False
        self.position = position
        if activated:
            self.is_activated = True
        else:
            self.is_activated = False
        self.headline = headline
        self.headline_surface = cst.text_font.render(self.headline, True, cst.BLACK)
        self.surface = pg.surface.Surface((self.headline_surface.get_width() + 30, self.headline_surface.get_height()),
                                          pg.SRCALPHA)

        self.rect = pg.rect.Rect(self.position, self.surface.get_size())
        self.func = func

    def display(self, channel=cst.dirty_blits) -> None:
        """ Add blitting information the to specified to_display channel

        :param channel: Channel to add information to (early, late...)
        :return: None
        """

        check_color = self.check_color
        box_color = text_color = self.text_color

        if self.is_disabled:
            box_color = self.disabled_box_color
            check_color = self.disabled_check_color

        self.headline_surface = cst.text_font.render(self.headline, True, text_color)
        self.surface = pg.surface.Surface((self.headline_surface.get_width() + 30,
                                           self.headline_surface.get_height()), pg.SRCALPHA)
        self.surface.fill(cst.LIGHT_GREY)
        self.surface.blit(self.headline_surface, (0, 0))

        # these should be circles but hey, who's looking
        pg.draw.rect(self.surface, box_color, (self.headline_surface.get_width() + 10, 0, 16, 16), border_radius=16)

        if self.is_activated:
            pg.draw.rect(self.surface, check_color, (self.headline_surface.get_width() + 14, 4, 8, 8),
                         border_radius=8)
        channel.append((self.surface, self.position))

    def is_clicked(self, **kwargs):
        """ Function that will be called with kwargs from the Gui in handle_clicks when the button is clicked.
            Toggles its activated status on/off
            Calls self.func attribute with self.is_activated as argument: func(self.is_activated)

            :param kwargs: Contains all the parameters to be passed to any is_clicked function
            :return: None
        """
        self.is_activated = not self.is_activated

        self.func(self.is_activated)

        self.display()


class DropDownButton:
    """ The most complicated button, this is a bit clunky since I did not plan on implementing it.
    Basically it has a headliner (like input buttons) and a dropdown box of other Button()
    (that were used separately before). When clicking on the DropDownButton surface, when it is not activated,
    It will activate and the box will dropdown, displaying all the available buttons. If a button is clicked,
    it will become the selected button and the box will close.
    When it is not activated only the selected button will be displayed, if None a generic "enter" text is displayed
    in the box.
    When activated, if clicking anywhere else on the screen, the box will close.
    To have a default button selected on startup, make it activated when the Button() is created.
    Do not set two Button active on startup, I do not want to go there... haha
    """

    color = cst.BLACK
    text_color = cst.WHITE
    header_color = cst.BLACK
    disabled_butt_color = cst.DARK_GREY
    disabled_text_color = cst.MEDIUM_GREY
    disabled_header_color = cst.DARK_GREY

    group = []

    def __init__(self, position: Tuple[Union[int, float], Union[int, float]], text: str,
                 buttons_list: List[Union[GridButton, AlgoButton, Checkbox, TextInputButton, StateButton,
                                          SystemButton]],
                 child_gui: Any) -> None:  # rect made around text size + 5 all around
        """ Create DropDownButton

        :param position: Topleft corner (x, y) of the surface
        :param text: Headline text, ("text": [Button ^]
        :param buttons_list: All Button() to be included in the dropdown, only one may be active at a time
        :param child_gui: gui.Gui object to handle clicks on its buttons
        """

        DropDownButton.group.append(self)

        self.buttons = buttons_list
        self.child_gui = child_gui
        self.child_gui.__dict__["src_butt"] = self

        self.is_activated = False
        self.is_disabled = False

        self.position = position
        self.text = text
        self.text_surface = cst.text_font.render(self.text, True, self.get_colors()[1])  # the color will not update
        self.text_rect = self.text_surface.get_rect()

        self.drop_down_size = max(button.rect.width for button in self.buttons), \
            sum(button.rect.height for button in self.buttons)

        # noinspection PyTypeChecker
        self.rect = pg.rect.Rect(self.position, (self.text_rect.width + 10 + self.drop_down_size[0] + 10,
                                                 self.text_rect.height + 10))

    def get_colors(self) -> [Tuple[int, int, int, Optional[int]], Tuple[int, int, int, Optional[int]],
                             Tuple[int, int, int, Optional[int]]]:
        """ Return Box color, box text color, headeline text color (If a button is selected, its colors will override)
        according to DropDownButton status

        :return: Box color, box text color, headeline text color
        """

        if self.is_disabled:
            color = self.disabled_butt_color
            text_color = self.disabled_text_color
            header_color = self.disabled_header_color
        else:
            color = self.color
            text_color = self.text_color
            header_color = self.header_color

        return color, text_color, header_color

    def display(self, channel=cst.dirty_blits) -> None:
        """ Add blitting information the to specified to_display channel

        :param channel: Channel to add information to (early, late...)
        :return: None
        """

        color, text_color, header_color = self.get_colors()

        self.text_surface = cst.text_font.render(self.text, True, header_color, cst.LIGHT_GREY)

        if self.is_disabled:
            for button in self.buttons:
                button.is_disabled = True
        else:
            for button in self.buttons:
                button.is_disabled = False

        if self.is_activated:
            # this should print the list of associated buttons when clicking
            surface = pg.surface.Surface((self.rect.width, self.drop_down_size[1]), pg.SRCALPHA)

            surface.blit(self.text_surface, (0, 5))

            # noinspection PyTypeChecker
            surface.fill(color, pg.rect.Rect((self.text_rect.width + 10, 0), (self.drop_down_size[0] + 10,
                                                                              self.drop_down_size[1])))

            pg.draw.polygon(surface, text_color,
                            points=[(self.rect.width - 8, round(self.rect.height * 2 / 3)),
                                    (self.rect.width - 2, round(self.rect.height * 2 / 3)),
                                    (self.rect.width - 5, round(self.rect.height * 1 / 3))])

            position = [self.text_rect.width + 10, 0]

            for button in self.buttons:
                button.position = self.position[0] + position[0], position[1] + self.position[1]
                button.rect = pg.rect.Rect((self.position[0] + position[0], position[1] + self.position[1]),
                                           (self.drop_down_size[0], self.text_rect.height + 10))
                button.display(channel=cst.late_blits)

                position[1] += button.rect.height

        else:
            surface = pg.surface.Surface((self.rect.width, self.rect.height), pg.SRCALPHA)

            surface.blit(self.text_surface, (0, 5))

            # noinspection PyTypeChecker
            surface.fill(color, pg.rect.Rect(self.text_rect.width + 10, 0, self.drop_down_size[0] + 10,
                                             self.rect.height))

            pg.draw.polygon(surface, text_color,
                            points=[(self.rect.width - 8, round(self.rect.height * 1 / 3)),
                                    (self.rect.width - 2, round(self.rect.height * 1 / 3)),
                                    (self.rect.width - 5, round(self.rect.height * 2 / 3))])

            position = self.text_rect.width + 10, 0

            for button in self.buttons:
                if button.is_activated:
                    button.position = self.position[0] + position[0], position[1] + self.position[1]
                    button.rect = pg.rect.Rect((self.position[0] + position[0], position[1] + self.position[1]),
                                               (self.drop_down_size[0], self.text_rect.height + 10))
                    button.display(channel=cst.late_blits)

        channel.append((surface, self.position))

    def is_clicked(self, **kwargs):
        """ Function that will be called with kwargs from the Gui in handle_clicks when the button is clicked.
            Activates self, (in turn opening the dropdown menu and making its buttons clickable)

            :param kwargs: Contains all the parameters to be passed to any is_clicked function
            :return: None
            """
        self.is_activated = True
        kwargs["gui"].objects.append(self.child_gui)
        self.display()


class Stat:
    def __init__(self, text: str, color: Tuple[int, int, int, Optional[int]],
                 position: Tuple[Union[int, float], Union[int, float]],
                 getter: Callable = lambda: None):
        """ Create a statistic object (ex: "text": value), where the surface is a rendered text

        :param text: Descriptive text for the statistic
        :param color: Color for the text and value (whole str)
        :param position: topleft corner of the stat surface
        :param getter: Function for getting its stat value
        :return: None
        """
        self.getter = getter
        self.value = 0
        self.header = text
        self.color = color
        self.position = position

    def display(self, channel=cst.dirty_blits) -> None:
        """ Add blitting information the to specified to_display channel

        :param channel: Channel to add information to (early, late...)
        :return: None
        """

        self.get_value()

        text_surface = cst.text_font.render(self.header, True, self.color)
        value_surface = cst.number_font.render(str(self.value), True, self.color)
        surface = pg.surface.Surface((text_surface.get_width() + value_surface.get_width(), text_surface.get_height()),
                                     pg.SRCALPHA)
        surface.blit(text_surface, (0, 0))
        surface.blit(value_surface, (text_surface.get_width(), 0))
        channel.append((surface, self.position))

    def get_value(self):
        """ Updates self.value by calling self.getter"""
        self.value = self.getter()


class Grid:
    all_nodes = [[]]
    start = None
    end = None

    def __init__(self, width, height, n_wide, n_high):
        """ The Grid.all_node attribute is a double list of nodes, or square tiles.
            Thus, all_node[column][row] or all_node[x][y]-> Node
        """
        self.width = width
        self.height = height
        self.disabled = 0

        self.generate(n_wide, n_high)

    def display(self):
        """ Draws the grid as a late fill (this function was made for covering the no paths found pop up window.
            It also makes the unused pixels from the grid dark gray as to prevent confusion, although it would be
            nice to find a better solution.

            :return: None
            """

        # ideally all nodes would get blitted here and the grid would be blitted to the window once per frame
        cst.late_fills.append(
            (cst.DARK_GREY, pg.rect.Rect(self.all_nodes[0][0].position, (cfg.grid_width, cfg.grid_height))))

        cst.dirty_fills.append((cst.LIGHT_GREY, pg.Rect(cfg.button_background_rect.width, 0, cfg.window.get_width()
                                                        - cfg.button_background_rect.width, 25)))
        cst.dirty_fills.append((cst.LIGHT_GREY, pg.Rect(cfg.button_background_rect.width + cfg.grid_width, 0,
                                                        25, cfg.window.get_height())))
        for column in self.all_nodes:
            for node in column:
                cst.late_fills.append(node.get_fill())

    def generate(self, n_wide, n_high):
        """ Generates the grid and then draws it using draw_grid(). Generate using parameters defined in config

            :return: None
            """

        # put this into a function..
        # GRID
        # cleanup all value (start node, end, all_nodes, etc)
        self.all_nodes = []

        nodes_width = self.width / n_wide
        nodes_height = self.height / n_high

        start_height = 25  # + grid_height - nodes_height * cst.n_nodes_high["value"]

        # position_y = start_height - nodes_height
        # position_x = cfg.button_background_rect.width - nodes_width

        position_y = start_height
        position_x = cfg.button_background_rect.width

        self.all_nodes = [[Node(x_wide, y_high, (position_x + nodes_width * x_wide,
                                                 position_y + nodes_height * y_high), nodes_width, nodes_height)
                           for y_high in range(n_high)] for x_wide in range(n_wide)]

        self.display()

    # TODO: split up into smaller functions.
    def handle_grid(self, gui):
        """ Handles the placement of end and start node and the drawing/erasing of walls.

        :param gui: Gui containing the GridButton
        :return: None
        """
        # It may be possible to directly localise the node instead of iterating

        if pg.time.get_ticks() > self.disabled:

            if (gui.start_node_button.is_activated and not gui.start_node_button.is_disabled) or \
                    (gui.end_node_button.is_activated and not gui.end_node_button.is_disabled) or \
                    (gui.draw_walls_button.is_activated and not gui.draw_walls_button.is_disabled) or \
                    (gui.erase_walls_button.is_activated and not gui.erase_walls_button.is_disabled):

                if pg.mouse.get_pressed()[0] and not gui.brush_size_button.is_activated:
                    click = pg.rect.Rect(pg.mouse.get_pos(), (1, 1))
                    brush_size = gui.brush_size_button.dict["value"]
                    if gui.draw_walls_button.is_activated or gui.erase_walls_button.is_activated:
                        click = pg.rect.Rect(pg.mouse.get_pos(), (brush_size, brush_size))

                    for column in self.all_nodes:
                        if click.center[0] - brush_size - column[0].width <= column[0].rect.center[0] \
                                <= click.center[0] + brush_size + column[0].width:
                            for node in column:
                                if pg.rect.Rect.colliderect(click, node):
                                    if gui.start_node_button.is_activated and not node.status & Node.WALL:
                                        if self.start:
                                            temp = self.start
                                            temp.status &= ~Node.START
                                            self.start = None
                                            cst.dirty_fills.append(temp.get_fill())
                                        self.start = node
                                        self.start.status |= Node.START
                                        cst.dirty_fills.append(node.get_fill())

                                    elif gui.end_node_button.is_activated and not node.status & Node.WALL:
                                        if self.end:
                                            temp = self.end
                                            temp.status &= ~Node.END
                                            self.end = None
                                            cst.dirty_fills.append(temp.get_fill())
                                        self.end = node
                                        self.end.status |= Node.END
                                        cst.dirty_fills.append(node.get_fill())

                                    elif gui.draw_walls_button.is_activated \
                                            and node is not self.start and node is not self.end:
                                        node.status |= Node.WALL
                                        cst.dirty_fills.append(node.get_fill())

                                    elif gui.erase_walls_button.is_activated \
                                            and node is not self.start and node is not self.end:
                                        node.status &= ~Node.WALL
                                        cst.dirty_fills.append(node.get_fill())
