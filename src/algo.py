""" The ALGO module holds the functions for running any of its available pathfinding algorithm (currently Breadth First
Search and A*) although some variables from the config modules are needed for it to make decisions
(diago_allowed, algo, path_found...).
It also holds the Symmetry rectangle class and the algorithm to preprocess a map with rectangular symetry reduction
(unfinished)
"""
import time
# import bisect
import pygame as pg
import gui
import variables as var
import classes


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


def run() -> None:
    """ Procedure to run the algorithm chosen by config.algo: str, according to display_steps: bool,
    run_interval["value"]: int and run_delay["value"]: int, Which are selected in the GUI and stored in config.
    Note: running display steps as True with run_interval = -1 will loop chosen algorithm until a path is found (or no path)
    and show visited nodes, whereas setting display steps to False will loop until path found (or no path) but won't show visited nodes.

    :return: None
    """
    # this could take a function as parameter, var.alg would be a function, not a string, and could be put as parameter
    # instead of a direct call

    def pick_algo() -> None:
        """Run the algorithm selected by var.algo"""
        if var.algo == "bfs" and var.bfs_is_init:
            first_search()
        elif var.algo == "astar" and var.astar_is_init:
            astar_()
        elif var.algo == "dijkstra" and var.bfs_is_init:
            dijkstra()

    if not var.path_found:

        if not var.display_steps or var.run_interval["value"] == -1:

            while not var.path_found:
                pick_algo()

        elif var.run_interval["value"] == 0 and var.run_delay["value"] == 0:
            pick_algo()

        elif var.run_interval["value"] == 0:
            pick_algo()
            pg.time.wait(var.run_delay["value"])

        elif var.run_delay["value"] == 0:
            if pg.time.get_ticks() > var.run_timer and not var.path_found:
                var.run_timer = pg.time.get_ticks()
                var.run_timer += var.run_interval["value"]

            while pg.time.get_ticks() < var.run_timer and not var.path_found:
                pick_algo()
        else:
            if pg.time.get_ticks() > var.run_timer and not var.path_found:
                pg.time.wait(var.run_delay["value"])
                var.run_timer = pg.time.get_ticks() + var.run_interval["value"]

            while pg.time.get_ticks() < var.run_timer and not var.path_found:
                pick_algo()

    elif var.path_found and var.shortest_path == []:
        gui.no_path_found()


def init_search(algo: str = "bfs") -> None:
    """ Initializes the algorithm chosen by algo (could change it to used var.algo...), depending on var.diago_allowed.
    Initialization consists of entering the first nodes in queue, setting the start node as visited.

    :param algo: chosen algorithm as a string (put var.algo as parameter)
    :return: None
    """

    var.current_node = var.start_node
    var.start_node.visited = True

    if algo == "bfs" or algo == "dijkstra":
        var.frontier.append(var.current_node)
        var.bfs_is_init = True

    elif algo == "astar":
        var.queue.append((var.current_node, var.current_node.priority))
        var.astar_is_init = True

    elif algo == "jps":
        pass


# I could probably find a better way to handle frontier management,
# have 2 queues and clear one while running the other and switch
def first_search() -> None:
    """ Does a breadth first search (flood fill) on var.all_nodes, requires parameters from config to be set

    :return: None
    """

    if len(var.frontier) == 0:
        var.path_found = True
        var.end_runtime = time.perf_counter_ns() / 10 ** 6
        return
    # display path not found in stats? or on grid?

    for node in var.to_be_removed:
        if node in var.frontier:  # dont need it actually
            var.frontier.remove(node)
    var.to_be_removed.clear()

    for node_no in range(len(var.frontier)):
        var.current_node = var.frontier[node_no]

        if var.current_node is var.end_node:

            var.shortest_path.append(var.current_node)
            previous_node = var.current_node.came_from
            while var.current_node is not var.start_node:
                var.current_node = previous_node
                var.shortest_path.append(var.current_node)
                previous_node = var.current_node.came_from
            var.shortest_path.reverse()
            var.path_found = True
            var.running = False
            # var.end_runtime = time.perf_counter_ns() / 10 ** 6
            var.end_runtime = pg.time.get_ticks()

            for node in var.shortest_path:
                node.is_path = True
                var.dirty_fills.append(node.get_fill())

        var.to_be_removed.append(var.current_node)

        if var.display_steps:
            var.dirty_fills.append(var.current_node.get_fill())

        for neighbor, cost in var.current_node.get_available_neighbors():
            # marking them visited instead of looking in frontier makes the algorithm 2-3 times faster
            neighbor.visited = True
            var.frontier.append(neighbor)
            neighbor.came_from = var.current_node


# this need profiling, its unbelievably slow with RSR
def dijkstra() -> None:
    """ Dijkstra (weighted flood fill) on var.all_nodes, requires parameters from config to be set

    :return: None
    """

    if var.diago_allowed:
        var.dijkstra_cost_so_far += 1.41421
    else:
        var.dijkstra_cost_so_far += 1

    if len(var.frontier) == 0 and len(var.queue) == 0:
        var.path_found = True
        var.end_runtime = time.perf_counter_ns() / 10 ** 6
        return
    # display path not found in stats? or on grid?

    for node in var.to_be_removed:
        if node in var.frontier:  # dont need it actually, but sometimes i do it seems, lol
            var.frontier.remove(node)
    var.to_be_removed.clear()

    """for skipped in var.queue:
        if skipped.cost_so_far <= var.dijkstra_cost_so_far:
            skipped.visited = True
            var.frontier.append(skipped)
            var.queue.remove(skipped)"""

    for node_no in range(len(var.frontier)):

        var.current_node = var.frontier[node_no]

        if not var.current_node.cost_so_far <= var.dijkstra_cost_so_far:
            continue

        if var.current_node is var.end_node:

            var.shortest_path.append(var.current_node)
            previous_node = var.current_node.came_from
            while var.current_node is not var.start_node:
                var.current_node = previous_node
                var.shortest_path.append(var.current_node)
                previous_node = var.current_node.came_from
            var.shortest_path.reverse()
            var.path_found = True
            var.running = False
            # var.end_runtime = time.perf_counter_ns() / 10 ** 6
            var.end_runtime = pg.time.get_ticks()

            for node in var.shortest_path:
                node.is_path = True
                var.dirty_fills.append(node.get_fill())

        var.to_be_removed.append(var.current_node)

        if var.display_steps:
            var.dirty_fills.append(var.current_node.get_fill())

        for neighbor, cost in var.current_node.get_available_neighbors():
            # marking them visited instead of looking in frontier makes the algorithm 2-3 times faster
            neighbor.cost_so_far = var.current_node.cost_so_far + cost
            neighbor.came_from = var.current_node
            neighbor.visited = True
            var.frontier.append(neighbor)


def astar_() -> None:       # display_steps
    """ Does A* algorithm on var.all_nodes, requires some parameter in config to be set

    :return: None
    """

    # while not var.path_found:     # doing one cycle per frame reeeally slows it down...
    if len(var.queue) == 0:
        var.path_found = True
        var.end_runtime = time.perf_counter_ns() / 10 ** 6
        return

    # Now this is the biggest time consumer
    # POP IS FASTER FROM THE END OF LIST. SEE COLLECTION.DEQUE, (bidirectionnal)
    # import collections
    # collections.deque()
    # HOLY FUCK THATS FAST, went from 1.2s to 0.002s on a 500x500 snowed in grid
    var.current_node = var.queue.popleft()[0]

    if var.current_node is var.end_node:
        var.shortest_path.append(var.current_node)
        while var.current_node is not var.start_node:
            var.current_node = var.current_node.came_from
            var.shortest_path.append(var.current_node)
        var.shortest_path.reverse()
        var.path_found = True
        var.running = False
        # var.end_runtime = time.perf_counter_ns() / 10 ** 6
        var.end_runtime = pg.time.get_ticks()

        for node in var.shortest_path:
            node.is_path = True
            var.dirty_fills.append(node.get_fill())

    for neighbor, cost in var.current_node.get_available_neighbors():
        neighbor.visited = True
        if var.display_steps:
            var.dirty_fills.append(neighbor.get_fill())

        neighbor.came_from = var.current_node

        neighbor.cost_so_far = var.current_node.cost_so_far + cost

        # this needs to be changed to chessboard distance (King), nah actually makes weird shit
        if var.diago_allowed:
#            neighbor.heuristic = max(abs(var.end_node.row - neighbor.row), abs(var.end_node.column - neighbor.column))
            neighbor.heuristic = (((var.end_node.row - neighbor.row) ** 2
                                   + (var.end_node.column - neighbor.column) ** 2) ** .5)

        else:
            neighbor.heuristic = abs(var.end_node.row - neighbor.row) + abs(var.end_node.column - neighbor.column)

        # prio is just for easier/faster access but idk if it does anything...
        # the int(100*()) allows us to compare ints to ints instead of floats to ints or wtv which is slower

        # Observed no major difference while placing/inserting

        # If im using *100 and int, i dont need to round the square roots beforehand, i will already keep .01 precision
        prio = neighbor.priority = int(10000 * (neighbor.cost_so_far + neighbor.heuristic))
        # prio = neighbor.priority = neighbor.cost_so_far + neighbor.heuristic

        if len(var.queue) == 0:
            var.queue.append((neighbor, neighbor.priority))

        # this should find intervals, not a direct value search
        else:
            index = bisect_left(var.queue, prio, key=lambda x: x[1])
            var.queue.insert(index, (neighbor, prio))


def symetryrectangle(start: classes.Node, size: int):
    """Simulates an object creation by defining the nodes inside the square as borders or sym_rect if they are
    contained in the borders. This allows to skip neighbors when we are running our pathfinding algorithm.
    This applies on nodes in var.all_nodes.

    :param start: Top-left node of the square
    :param size: Length of a side of the square
    :return: None"""

    start_col = start.column
    start_row = start.row

    for row in range(size):
        for column in range(size):
            node = var.all_nodes[start_col + column][start_row + row]

            if row == 0 or row == size - 1 or column == 0 or column == size - 1:
                node.is_border = True
                # var.all_nodes[self.start_col + column][self.start_row + row].sym_rect = self  # not sure i need it

            else:
                node.is_sym_rect = True

            if var.display_steps:
                # this is what is eating a lot of time...
                # on the first run, it takes very minimal time: 0.300 s for 45 000 nodes
                # on the second and subsequent runs, it takes around 2 s for 45 000 nodes... idk why
                var.dirty_fills.append(node.get_fill())


def apply_RSR() -> None:
    """Applies Rectangular symmetry reduction to var.all_nodes, regrouping any square of free nodes (not walls)
    together, square sides must be atleast 4 or it will be skipped.
    :return: None"""

    # It would be nice to be able to prevent it from trying to apply RSR to nodes that have already been RSR'd...
    # But using a flat copy of var.all_nodes takes too much time to process.

    for column in var.all_nodes:
        for node_ in column:
            if not (node_.is_wall or node_.is_border or node_.is_sym_rect or node_.is_start or node_.is_end):

                start_col, start_row = node_.column, node_.row
                size = 1
                hit_wall = False

                while not hit_wall:
                    size += 1

                    try:
                        for y in range(size):
                            node = var.all_nodes[start_col + size - 1][start_row + y]
                            if node.is_wall or node.is_border or node.is_sym_rect or node.is_start or node.is_end:
                                hit_wall = True
                                break
                        for x in range(size):
                            node = var.all_nodes[start_col + x][start_row + size - 1]
                            if node.is_wall or node.is_border or node.is_sym_rect or node.is_start or node.is_end:
                                hit_wall = True
                                break
                    except IndexError: break

                size -= 1
                if size >= 4:
                    symetryrectangle(node_, size)

