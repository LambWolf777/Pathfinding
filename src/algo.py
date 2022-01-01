""" The ALGO module holds the functions for running any of its available pathfinding algorithm (currently Breadth First
Search and A*) although some variables from the config modules are needed for it to make decisions
(diago_allowed, algo, path_found...).
It also holds the Symmetry rectangle class and the algorithm to preprocess a map with rectangular symmetry reduction
(unfinished)
"""
from time import perf_counter_ns
from collections import deque
from typing import *
import pygame as pg

import constants as cst
import classes


def get_dt(func):
    """ Decorator to get time of execution"""
    def inner(*args, **kwargs):
        start = perf_counter_ns()
        func(*args, **kwargs)
        end = perf_counter_ns()
        return (end - start) / 10 ** 6
    return inner


class PathFinder:
    """Pathfinding tool to apply pathfinding algorithms and related methods to the grid specified in init"""

    running = False
    path_found = False
    search_is_init = False

    diago = False
    display = True
    apply_rsr = False

    algo = "bfs"

    dijkstra_cost_so_far = 0

    frontier = []
    queue = deque()  # for ASTAR
    to_be_removed = []
    shortest_path = []

    run_timer = 0

    neighbors_prep_dt = 0
    rsr_prep_dt = 0
    algo_dt = 0

    def __init__(self, grid: classes.Grid):
        """ Creates a Singleton pathfinder tool

        :param grid: associated grid object to apply pathfinding
        """
        self.grid = grid

    def build_path(self) -> List:
        """ Creates the path from end to start by recursively adding node.came_from from end to start and reversing
        the path"""

        self.path_found = True

        current = self.grid.end
        path = [current]

        while current is not self.grid.start:
            current = current.came_from
            path.append(current)

        path.reverse()

        
        for node in path:
            node.is_path = True
            cst.dirty_fills.append(node.get_fill())

        return path

    @get_dt
    def set_neighbors(self):
        for column in self.grid.all_nodes:
            for node in column:
                if not node.is_sym_rect and not node.is_wall:
                    node.get_neighbors(self.grid.all_nodes, self.diago)

    def init_search(self) -> None:
        """ Initializes all search algorithms, by setting neighbors on the grid and setting starting point and applying
        Rectangular Symmetry Reduction if activated.

        :return: None
        """

        algorithms = {
            "bfs": self.bfs,
            "astar": self.astar,
            "dijkstra": self.dijkstra
        }
        if isinstance(self.algo, str):
            self.algo = algorithms[self.algo]

        if self.apply_rsr:
            self.rsr_prep_dt = self.apply_RSR()

        self.neighbors_prep_dt = self.set_neighbors()

        # Init all algorithms
        self.grid.start.visited = True
        self.frontier.append(self.grid.start)
        self.queue.append((self.grid.start, self.grid.start.priority))

        self.search_is_init = True

    def check_done(self) -> bool:
        """ Checks if the queue/frontier is empty, if it is, post a no path found event and terminate processing
        timer.

        :return: path_found is used to say the algorithm's processing is done (in this case no path was found)
        """
        # This works since both are initialized and can only be empty if they were used
        if not self.frontier or not self.queue:
            pg.event.post(pg.event.Event(cst.NO_PATH, announcement="No path found!"))
            self.path_found = True
        return self.path_found

    def clean_frontier(self) -> None:
        """ Remove processed nodes from the frontier
        """
        for node in self.to_be_removed:
            if node in self.frontier:
                self.frontier.remove(node)
        self.to_be_removed.clear()

    def expand_frontier(self, node: classes.Node, costs: bool = False) -> None:
        """ Adds the available neighbors of the nodes to the frontier and marks the current node as visited

        :param node: current node
        :param costs: True if the algorithm needs to know the cost_so_far of each node (Dijkstra)
        :return:
        """

        for neighbor, cost in node.get_available_neighbors(self.grid.all_nodes):
            if costs:
                neighbor.cost_so_far = node.cost_so_far + cost
            neighbor.visited = True
            self.frontier.append(neighbor)
            neighbor.came_from = node

    @get_dt
    def bfs(self) -> None:
        """ Does a breadth first search (flood fill) on self.grid
         Not compatible with RSR (path will not be optimal)

        :return: None
        """

        if self.check_done():
            return

        self.clean_frontier()

        for node_no in range(len(self.frontier)):
            node = self.frontier[node_no]
            if node is self.grid.end:
                self.shortest_path = self.build_path()

            self.to_be_removed.append(node)

            if self.display:
                cst.dirty_fills.append(node.get_fill())

            self.expand_frontier(node)

    @get_dt
    def dijkstra(self) -> None:
        """ Dijkstra's Algorithm (weighted flood fill). This one could work with weighed graphs and is compatible
        with RSR

        :return: None
        """

        if self.diago:
            self.dijkstra_cost_so_far += 1.41422
        else:
            self.dijkstra_cost_so_far += 1

        if self.check_done():
            return

        self.clean_frontier()

        for node_no in range(len(self.frontier)):
            node = self.frontier[node_no]

            if not node.cost_so_far <= self.dijkstra_cost_so_far:
                continue

            if node is self.grid.end:
                self.shortest_path = self.build_path()

            if self.display:
                cst.dirty_fills.append(node.get_fill())

            self.to_be_removed.append(node)

            self.expand_frontier(node, True)

    @get_dt
    def astar(self) -> None:
        """ Does A* algorithm on self.grid
        Compatible with RSR

        :return: None
        """

        if self.check_done():
            return

        node = self.queue.popleft()[0]

        if self.display:
            cst.dirty_fills.append(node.get_fill())

        if node is self.grid.end:
            self.shortest_path = self.build_path()

        # I don't feel like it's worth wrapping this in another function, since no other algorithm uses it
        for neighbor, cost in node.get_available_neighbors(self.grid.all_nodes):
            neighbor.visited = True
            neighbor.came_from = node
            neighbor.cost_so_far = node.cost_so_far + cost

            if self.diago:
                # Eucledian distance, was not proving to be efficient, also paths are weirder
                # neighbor.heuristic = (((self.grid.end.row - neighbor.row)**2
                #                        + (self.grid.end.column - neighbor.column)**2) ** .5)

                # Thus we switch to diagonal (45 deg only) distance (octile, not chess)
                dx = abs(neighbor.column - self.grid.end.column)
                dy = abs(neighbor.row - self.grid.end.row)
                neighbor.heuristic = dx + dy + (1.41421 - 2) * min(dx, dy)
                # neighbor.heuristic = (dx + dy) - 0.5857864376269049 * min(dx, dy)

                # neighbor.heuristic = max(dx, dy) + 0.41421 * min(dx, dy)

            else:
                neighbor.heuristic = abs(self.grid.end.row - neighbor.row) + abs(self.grid.end.column - neighbor.column)

            # This is to reduce comparison between ints and floats while keeping some precision
            neighbor.priority = neighbor.cost_so_far + neighbor.heuristic

            index = bisect_left(self.queue, neighbor.priority, key=lambda x: x[1])
            self.queue.insert(index, (neighbor, neighbor.priority))

    def symmetry_rectangle(self, start: classes.Node, size: int) -> None:
        """Simulates an object creation by defining the nodes inside the square as borders or sym_rect if they are
        contained in the borders. This allows to skip neighbors when we are running our pathfinding algorithm.
        This applies on nodes in cst.all_nodes.

        :param start: Top-left node of the square
        :param size: Length of a side of the square
        :return: None"""

        for column in range(size):
            for row in range(size):
                node = self.grid.all_nodes[start.column + column][start.row + row]

                if row == 0 or row == size - 1 or column == 0 or column == size - 1:
                    node.is_border = True
                else:
                    node.is_sym_rect = True

                if self.display:
                    cst.dirty_fills.append(node.get_fill())

    @get_dt
    def apply_RSR(self) -> None:
        """Applies Rectangular symmetry reduction to self.grid, regrouping any square of free nodes (not walls)
        together, square sides must be atleast 4, or it will be skipped.
        :return: None"""

        # It would be nice to be able to prevent it from trying to apply RSR to nodes that have already been RSR'd...
        # But using a flat copy of cst.all_nodes takes too much time to process.
        # Also, it is slow even while the algorithms are running...

        for column in self.grid.all_nodes:
            for start in column:
                if not (start.is_wall or start.is_border or start.is_sym_rect or start.is_start or start.is_end):
                    start_col, start_row = start.column, start.row
                    size = 1
                    hit_wall = False

                    while not hit_wall:
                        size += 1

                        # Look at new border (lower and right)
                        try:
                            for add in range(size):
                                node = self.grid.all_nodes[start_col + size - 1][start_row + add]
                                if node.is_wall or node.is_border or node.is_sym_rect or node.is_start or node.is_end:
                                    hit_wall = True
                                    break

                                node = self.grid.all_nodes[start_col + add][start_row + size - 1]
                                if node.is_wall or node.is_border or node.is_sym_rect or node.is_start or node.is_end:
                                    hit_wall = True
                                    break
                        except IndexError:
                            break

                    size -= 1
                    if size >= 4:
                        self.symmetry_rectangle(start, size)

    def run(self, run_time: int = 0, wait_time: int = 0) -> None:
        """
        Procedure to run the algorithm chosen in init_search.
        Note: running display steps as True with run_interval = -1 will loop chosen algorithm until a path
        is found (or no path) and show visited nodes, whereas setting display steps to False will loop until a
        path is found (or no path) but won't show visited nodes.

        :param run_time: Define how much time the algorithm will spend searching before going to the next frame
        :param wait_time: Define time(ms) the algorithm will wait after searching before going to the next frame
        :return: None
        """

        if not self.path_found:

            if not self.display or run_time == -1:

                while not self.path_found:
                    self.algo_dt += self.algo()

            elif run_time == 0 and wait_time == 0:
                self.algo_dt += self.algo()

            elif run_time == 0:
                self.algo_dt += self.algo()
                pg.time.wait(wait_time)

            elif wait_time == 0:
                if pg.time.get_ticks() > self.run_timer and not self.path_found:
                    self.run_timer = pg.time.get_ticks()
                    self.run_timer += run_time

                while pg.time.get_ticks() < self.run_timer and not self.path_found:
                    self.algo_dt += self.algo()

            else:
                if pg.time.get_ticks() > self.run_timer and not self.path_found:
                    pg.time.wait(wait_time)
                    self.run_timer = pg.time.get_ticks() + run_time

                while pg.time.get_ticks() < self.run_timer and not self.path_found:
                    self.algo_dt += self.algo()


def init_pathfinder(grid: classes.Grid) -> PathFinder:
    """ Initialises the Singleton pathfinder object, needs an associated grid object to apply algorithms on
    :param grid: Grid object associated with the pathfinder
    :return: Pathfinder entity
    """
    return PathFinder(grid)


# from bisect! did not want to update to python 3.10 just for that... (Since only version 3.10 has key kwarg)
def bisect_left(a, x, lo=0, hi=None, *, key=None):
    """Return the index where to insert item x in list a, assuming a is sorted.
    The return value i is such that all e in a[:i] have e < x, and all e in
    a[i:] have e >= x.  So if x already appears in the list, a.insert(i, x) will
    insert just before the leftmost x already there.
    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched.
    """

    if lo < 0:
        raise ValueError('lo must be non-negative')
    if hi is None:
        hi = len(a)
    # Note, the comparison uses "<" to match the
    # __lt__() logic in list.sort() and in heapq.
    if key is None:
        while lo < hi:
            mid = (lo + hi) // 2
            if a[mid] < x:
                lo = mid + 1
            else:
                hi = mid
    else:
        while lo < hi:
            mid = (lo + hi) // 2
            if key(a[mid]) < x:
                lo = mid + 1
            else:
                hi = mid
    return lo
