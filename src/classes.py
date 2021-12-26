"""The var module stores the var used across the modules for the Visualizer, (gui, visualizer, algo)"""
from typing import *
import pygame as pg

import variables as var


class Node:
    """Object for representing every tile (node on the grid)"""

    is_path = False
    is_wall = False
    visited = False
    neighbors = None
    came_from = None
    came_from_diago = False  # useless now i think
    cost_so_far = 0
    heuristic = 0
    priority = 0
    color = var.black

    # for RSR
    sym_rect = None
    is_sym_rect = False
    is_border = False
    is_start = False
    is_end = False

    def __init__(self, column: int, row: int, position: Tuple[int, int], node_width: int, node_height: int) -> None:
        """Define node specific attributes"""

        self.position = position
        self.column = column
        self.row = row

        self.width = node_width
        self.height = node_height
        self.rect = pg.rect.Rect(self.position, (node_width, node_height))

    def update_color(self) -> None:
        """Return color according to current status"""

        self.color = var.black
        if self.is_start:
            self.color = var.blue
        elif self.is_end:
            self.color = var.green
        elif self.is_path:
            self.color = var.purple
        elif self.is_wall:
            self.color = var.white
        elif self.visited:
            self.color = var.yellow
        elif self.is_border:
            self.color = var.red
        elif self.is_sym_rect:
            self.color = var.orange

        # return self.color

    def get_fill(self) -> [Tuple[int, int, int, Optional[int]], pg.Rect]:
        """Return information needed for filling to screen, use to append to dirty_fills"""

        self.update_color()

        return self.color, self.rect

    def update_sym_rect_neighbors(self):
        # i shouldnt need to worry about going out of bounds, or hitting walls since the sym_rect
        # should stop before any of those

        def cycle_node(direction, current):

            cost_multiplier = 1

            while current.is_sym_rect:
                cost_multiplier += 1
                new_col, new_row = var.cycle_moves[direction](current.column, current.row)
                current = var.all_nodes[new_col][new_row]

            return current, cost_multiplier

        for direction, (neighbor, cost) in self.neighbors.items():
            if neighbor.is_sym_rect:
                current, cost_mult = cycle_node(direction, neighbor)
                self.neighbors[direction] = current, cost * cost_mult

    def get_available_neighbors(self) -> List[Tuple['Node', int]]:
        """
        Return available (not walls and not visited) neighbors and their cost as a list.

        :return: List of adjacent node objects
        """

        if self.is_border:  # if self is border...
            self.update_sym_rect_neighbors()

        neighbors = []
        for node, cost in self.neighbors.values():

            if not (node.is_wall or node.visited):
                neighbors.append((node, cost))

        return neighbors

    def get_neighbors(self, grid_: List[List['Node']], diago_allowed: bool = False) -> None:
        """Procedure:
        Create a dict of all adjacent neighbors in the form neighbors["direction"] = node, cost as an attribute.

        :param grid_: Grid on which the node is located
        :param diago_allowed: Sets if diagonal neighbors should be included, does not allow corner-cutting
        :return: None
        """

        # could definitely make this more compact, see update_sym_rect_neighbors()

        neighbors = {}

        try:
            neighbors["right"] = grid_[self.column + 1][self.row], 1  # right
        except IndexError:
            pass
        try:
            neighbors["down"] = grid_[self.column][self.row + 1], 1  # down
        except IndexError:
            pass

        if not self.row == 0:
            neighbors["up"] = grid_[self.column][self.row - 1], 1  # up
        if not self.column == 0:
            neighbors["left"] = grid_[self.column - 1][self.row], 1  # left

        if diago_allowed:

            try:
                if not neighbors["down"][0].is_wall and not neighbors["right"][0].is_wall:
                    neighbors["downright"] = grid_[self.column + 1][self.row + 1], 1.41421  # botright
            except KeyError:
                pass
            try:
                if not neighbors["up"][0].is_wall and not neighbors["right"][0].is_wall:
                    neighbors["topright"] = grid_[self.column + 1][self.row - 1], 1.41421  # topright
            except KeyError:
                pass

            try:
                if not neighbors["down"][0].is_wall and not neighbors["left"][0].is_wall:
                    neighbors["downleft"] = grid_[self.column - 1][self.row + 1], 1.41421  # botleft
            except KeyError:
                pass
            try:
                if not neighbors["up"][0].is_wall and not neighbors["left"][0].is_wall:
                    neighbors["topleft"] = grid_[self.column - 1][self.row - 1], 1.41421  # topleft
            except KeyError:
                pass

        self.neighbors = neighbors


class Button:
    """Basic Class for buttons, allows to set conditions to active, to be clicked, drawn, etc...
    is a clickable rectangle with text in it."""

    disabled_butt_color = var.dark_grey
    disabled_text_color = var.medium_grey

    def __init__(self, position: Tuple[int, int], text: AnyStr,
                 text_color: Union[Tuple[int, int, int], Tuple[int, int, int, int]],
                 active_color: Union[Tuple[int, int, int], Tuple[int, int, int, int]],
                 off_color: Union[Tuple[int, int, int], Tuple[int, int, int, int]],
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
        self.text_surface = var.text_font.render(self.text, True, self.get_colors()[1])  # the color will not update
        self.text_rect = self.text_surface.get_rect()
        self.rect = pg.rect.Rect(self.position, (self.text_rect.width + 10, self.text_rect.height + 10))
        self.surface = self.get_surface()

    def get_colors(self) -> [Union[Tuple[int, int, int], Tuple[int, int, int, int]],
                             Union[Tuple[int, int, int], Tuple[int, int, int, int]]]:
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

    def get_surface(self) -> [pg.Surface, [Union[int, float], Union[int, float]]]:
        """ Return necessary information to append to dirty_blits

        :return: Button completed surface, topleft corner coordinates
        """

        self.color = self.get_colors()[0]  # im not sure if calling this to blit when pressing
        # will update the color as well... indeed needed to call this funct
        self.text_surface = var.text_font.render(self.text, True, self.get_colors()[1])  # the color will not update

        surface = pg.surface.Surface((self.rect.width, self.rect.height), pg.SRCALPHA)

        if self.rounded is True:
            pg.draw.rect(surface, self.color, surface.get_rect(), border_radius=8)
        else:
            surface.fill(self.color)

        surface.blit(self.text_surface, (5, 5))

        return surface, self.position


class TextInputButton:  # for text buttons
    """ More intricate button, header and input box: "header: [Input_box]"
    Allows for user input, GUI will handle value confirmations, default and allowed values
    """

    disabled_butt_color = var.dark_grey
    disabled_text_color = var.medium_grey

    def __init__(self, _dict_: Dict, position: [Union[int, float], Union[int, float]],
                 input_width: int, text: AnyStr, variable: TypeVar,
                 headline_text_color: Tuple[int, int, int, Optional[int]],
                 text_color: Tuple[int, int, int, Optional[int]],
                 active_color: Tuple[int, int, int, Optional[int]],
                 off_color: Tuple[int, int, int, Optional[int]],
                 rounded: Optional[bool] = True) -> None:

        # rect made around text size + 5 all around
        """ Create the text input button

        :param _dict_: Contains min, max, default and initial values of the input
        :param position: topleft corner of the button
        :param input_width: input box width
        :param text: text for the HEADLINER
        :param variable: variable associated with the button (input will be passed to this variable)
                         *Since this variable is basically _dict_["value"], this parameter is useless
        :param headline_text_color: color for the headline text
        :param text_color: color for the input text
        :param active_color: color for the input box when active
        :param off_color: color for the input box when inactive
        """

        self.value = variable
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

        self.headline = var.text_font.render(text, True, headline_text_color)
        self.headline_rect = self.headline.get_rect()

        self.input_value = var.number_font.render(str(self.value), True, self.get_colors()[1])
        self.input_rect = pg.rect.Rect(0, 0, self.input_width, self.input_value.get_rect().h + 10)

        self.rect = pg.rect.Rect(self.position, (self.headline_rect.width + self.input_rect.width + 10,
                                                 self.headline_rect.height + 10))
        self.surface = self.get_surface()

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

    def get_surface(self, value: Optional[Union[str, int]] = None) -> Tuple[
        pg.Surface, Tuple[Union[int, float], Union[int, float]]]:
        """ Return necessary information to append to dirty_blits

        :return: completed surface, position (topleft)
        """

        if value:
            self.value = value

        self.color = self.get_colors()[0]

        self.input_value = var.number_font.render(str(self.value), True, self.get_colors()[1])
        self.input_rect = pg.rect.Rect(0, 0, self.input_width, self.input_value.get_rect().h + 10)  # duplicate

        surface = pg.surface.Surface((self.rect.width, self.rect.height), pg.SRCALPHA)
        surface.fill(var.light_grey, self.headline_rect)

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

        return surface, self.position


class Checkbox:
    """ Checkbox button, similar to Button, but as a checkbox (expected to stay active, whereas buttons are expected to
    be active only while used (ex: draw walls) and then turned off
    """

    disabled_check_color = var.medium_grey
    disabled_box_color = var.dark_grey
    text_color = box_color = var.black
    check_color = var.white

    def __init__(self, headline: str, position: Tuple[Union[int, float], Union[int, float]],
                 activated: bool = False) -> None:
        """ Create checkbox

        :param headline: Headline text, similar to input button headline, ex: "headline": [x]
        :param position: topleft corner position
        :param activated: boolean, True means active ... obviously
        """

        self.is_disabled = False
        self.position = position
        if activated:
            self.is_activated = True
        else:
            self.is_activated = False
        self.headline = headline
        self.headline_surface = var.text_font.render(self.headline, True, var.black)
        self.surface = pg.surface.Surface((self.headline_surface.get_width() + 30, self.headline_surface.get_height()),
                                          pg.SRCALPHA)

        self.rect = pg.rect.Rect(self.position, self.surface.get_size())

    def get_surface(self) -> Tuple[pg.Surface, Tuple[Union[int, float], Union[int, float]]]:
        """ Return necessary information to append to dirty_blits

        :return: completed surface, position (topleft)
        """

        check_color = self.check_color
        box_color = text_color = self.text_color

        if self.is_disabled:
            box_color = self.disabled_box_color
            check_color = self.disabled_check_color

        self.headline_surface = var.text_font.render(self.headline, True, text_color)
        self.surface = pg.surface.Surface((self.headline_surface.get_width() + 30,
                                           self.headline_surface.get_height()), pg.SRCALPHA)
        self.surface.fill(var.light_grey)
        self.surface.blit(self.headline_surface, (0, 0))

        # these should be circles but hey, who's looking
        pg.draw.rect(self.surface, box_color, (self.headline_surface.get_width() + 10, 0, 16, 16), border_radius=16)

        if self.is_activated:
            pg.draw.rect(self.surface, check_color, (self.headline_surface.get_width() + 14, 4, 8, 8),
                         border_radius=8)
        return self.surface, self.position


# now must implement it in GUI/handle buttons *** as first ran before checking other buttons, has prio
class DropDownButton:
    """ The most complicated button, this is a bit clunky since I did not plan on implementing it.
    Basically it has a headliner (like input buttons) and a dropdown box of other Button()
    (that were used separately before). When clicking on the DropDownButton surface, when it is not activated,
    It will activate and the box will dropdown, displaying all the available buttons. If a button is clicked, it will become the selected
    button and the box will close.
    When it is not activated only the selected button will be displayed, if None a generic "enter" text is displayed
    in the box.
    When activated, if clicking anywhere else on the screen, the box will close.
    To have a default button selected on startup, make it activated when the Button() is created.
    Do not set two Button active on startup, I do not want to go there... haha
    """

    color = var.black
    text_color = var.white
    header_color = var.black
    disabled_butt_color = var.dark_grey
    disabled_text_color = var.medium_grey
    disabled_header_color = var.dark_grey

    def __init__(self, position: Tuple[Union[int, float], Union[int, float]], text: str,
                 buttons_list: List[Button]) -> None:  # rect made around text size + 5 all around
        """ Create DropDownButton

        :param position: Topleft corner (x, y) of the surface
        :param text: Headline text, ("text": [Button ^]
        :param buttons_list: All Button() to be included in the dropdown, only one may be active at a time
        """

        self.buttons = buttons_list

        self.is_activated = False
        self.is_disabled = False

        self.position = position
        self.text = text
        self.text_surface = var.text_font.render(self.text, True, self.get_colors()[1])  # the color will not update
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

    def get_surface(self) -> Tuple[pg.Surface, Tuple[Union[int, float], Union[int, float]]]:
        """ Return completed surface and position for appending (as tuple) to dirty_blits.
        This surface as a variable height

        :return: surface, position
        """

        color, text_color, header_color = self.get_colors()

        self.text_surface = var.text_font.render(self.text, True, header_color, var.light_grey)

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
                surface.blit(button.get_surface()[0], position)

                button.position = self.position[0] + position[0], position[1] + self.position[1]
                button.rect = pg.rect.Rect((self.position[0] + position[0], position[1] + self.position[1]),
                                           (self.drop_down_size[0], self.text_rect.height + 10))

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
                    surface.blit(button.get_surface()[0], position)

        return surface, self.position


class Stat:
    def __init__(self, text: str, color: Tuple[int, int, int, Optional[int]],
                 position: Tuple[Union[int, float], Union[int, float]]):
        """ Create a statistic object (ex: "text": value), where the surface is a rendered text

        :param text: Descriptive text for the statistic
        :param color: Color for the text and value (whole str)
        :param position: topleft corner of the stat surface
        :return: None
        """

        self.header = text
        self.color = color
        self.position = position

    #     self.rect?

    def get_surface(self, value: Union[float, int]) -> Tuple[pg.Surface, Tuple[Union[int, float], Union[int, float]]]:
        """ Return completed stat surface (ex: "text": value), where the surface is a rendered text

        :param value: Value of the statistic
        :return: completed surface, position (topleft)
        """

        text_surface = var.text_font.render(self.header, True, self.color)
        value_surface = var.number_font.render(str(value), True, self.color)
        surface = pg.surface.Surface((text_surface.get_width() + value_surface.get_width(), text_surface.get_height()),
                                     pg.SRCALPHA)
        surface.blit(text_surface, (0, 0))
        surface.blit(value_surface, (text_surface.get_width(), 0))
        return surface, self.position
