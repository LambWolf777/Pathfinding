""" The ALGO module holds the functions for running any of its available pathfinding algorithm (currently Breadth First
Search and A*) although some variables from the config modules are needed for it to make decisions
(diago_allowed, algo, path_found...).
It also holds the Symmetry rectangle class and the algorithm to preprocess a map with rectangular symetry reduction
(unfinished)
"""
import time
# import bisect
import pygame as pg
import GUI
import config as cfg


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
    # this could take a function as parameter, cfg.alg would be a function, not a string, and could be put as parameter
    # instead of a direct call

    def pick_algo() -> None:
        """Run the algorithm selected by cfg.algo"""
        if cfg.algo == "bfs" and cfg.bfs_is_init:
            first_search()
        elif cfg.algo == "astar" and cfg.astar_is_init:
            astar_()
        elif cfg.algo == "dijkstra" and cfg.bfs_is_init:
            dijkstra()

    if not cfg.path_found:

        if not cfg.display_steps or cfg.run_interval["value"] == -1:

            while not cfg.path_found:
                pick_algo()

        elif cfg.run_interval["value"] == 0 and cfg.run_delay["value"] == 0:
            pick_algo()

        elif cfg.run_interval["value"] == 0:
            pick_algo()
            pg.time.wait(cfg.run_delay["value"])

        elif cfg.run_delay["value"] == 0:
            if pg.time.get_ticks() > cfg.run_timer and not cfg.path_found:
                cfg.run_timer = pg.time.get_ticks()
                cfg.run_timer += cfg.run_interval["value"]

            while pg.time.get_ticks() < cfg.run_timer and not cfg.path_found:
                pick_algo()
        else:
            if pg.time.get_ticks() > cfg.run_timer and not cfg.path_found:
                pg.time.wait(cfg.run_delay["value"])
                cfg.run_timer = pg.time.get_ticks() + cfg.run_interval["value"]

            while pg.time.get_ticks() < cfg.run_timer and not cfg.path_found:
                pick_algo()

    elif cfg.path_found and cfg.shortest_path == []:
        GUI.no_path_found()


def init_search(algo: str = "bfs") -> None:
    """ Initializes the algorithm chosen by algo (could change it to used cfg.algo...), depending on cfg.diago_allowed.
    Initialization consists of entering the first nodes in queue, setting the start node as visited.

    :param algo: chosen algorithm as a string (put cfg.algo as parameter)
    :return: None
    """

    cfg.current_node = cfg.start_node
    cfg.start_node.visited = True

    if algo == "bfs" or algo == "dijkstra":
        cfg.frontier.append(cfg.current_node)
        cfg.bfs_is_init = True

    elif algo == "astar":
        cfg.queue.append((cfg.current_node, cfg.current_node.priority))
        cfg.astar_is_init = True

    elif algo == "jps":
        pass


# I could probably find a better way to handle frontier management,
# have 2 queues and clear one while running the other and switch
def first_search() -> None:
    """ Does a breadth first search (flood fill) on cfg.all_nodes, requires parameters from config to be set

    :return: None
    """

    if len(cfg.frontier) == 0:
        cfg.path_found = True
        cfg.end_runtime = time.perf_counter_ns() / 10**6
        return
    # display path not found in stats? or on grid?

    for node in cfg.to_be_removed:
        if node in cfg.frontier:  # dont need it actually
            cfg.frontier.remove(node)
    cfg.to_be_removed.clear()

    for node_no in range(len(cfg.frontier)):
        cfg.current_node = cfg.frontier[node_no]

        if cfg.current_node is cfg.end_node:

            cfg.shortest_path.append(cfg.current_node)
            previous_node = cfg.current_node.came_from
            while cfg.current_node is not cfg.start_node:
                cfg.current_node = previous_node
                cfg.shortest_path.append(cfg.current_node)
                previous_node = cfg.current_node.came_from
            cfg.shortest_path.reverse()
            cfg.path_found = True
            cfg.running = False
            # cfg.end_runtime = time.perf_counter_ns() / 10 ** 6
            cfg.end_runtime = pg.time.get_ticks()

            for node in cfg.shortest_path:
                node.is_path = True
                cfg.dirty_fills.append(node.get_fill())

        cfg.to_be_removed.append(cfg.current_node)

        if cfg.display_steps:
            cfg.dirty_fills.append(cfg.current_node.get_fill())

        for neighbor, cost in cfg.current_node.get_available_neighbors():
            # marking them visited instead of looking in frontier makes the algorithm 2-3 times faster
            neighbor.visited = True
            cfg.frontier.append(neighbor)
            neighbor.came_from = cfg.current_node


# this need profiling, its unbelievably slow with RSR
def dijkstra() -> None:
    """ Dijkstra (weighted flood fill) on cfg.all_nodes, requires parameters from config to be set

    :return: None
    """

    if cfg.diago_allowed:
        cfg.dijkstra_cost_so_far += 1.41421
    else:
        cfg.dijkstra_cost_so_far += 1

    if len(cfg.frontier) == 0 and len(cfg.queue) == 0:
        cfg.path_found = True
        cfg.end_runtime = time.perf_counter_ns() / 10**6
        return
    # display path not found in stats? or on grid?

    for node in cfg.to_be_removed:
        if node in cfg.frontier:  # dont need it actually, but sometimes i do it seems, lol
            cfg.frontier.remove(node)
    cfg.to_be_removed.clear()

    """for skipped in cfg.queue:
        if skipped.cost_so_far <= cfg.dijkstra_cost_so_far:
            skipped.visited = True
            cfg.frontier.append(skipped)
            cfg.queue.remove(skipped)"""

    for node_no in range(len(cfg.frontier)):

        cfg.current_node = cfg.frontier[node_no]

        if not cfg.current_node.cost_so_far <= cfg.dijkstra_cost_so_far:
            continue

        if cfg.current_node is cfg.end_node:

            cfg.shortest_path.append(cfg.current_node)
            previous_node = cfg.current_node.came_from
            while cfg.current_node is not cfg.start_node:
                cfg.current_node = previous_node
                cfg.shortest_path.append(cfg.current_node)
                previous_node = cfg.current_node.came_from
            cfg.shortest_path.reverse()
            cfg.path_found = True
            cfg.running = False
            # cfg.end_runtime = time.perf_counter_ns() / 10 ** 6
            cfg.end_runtime = pg.time.get_ticks()

            for node in cfg.shortest_path:
                node.is_path = True
                cfg.dirty_fills.append(node.get_fill())

        cfg.to_be_removed.append(cfg.current_node)

        if cfg.display_steps:
            cfg.dirty_fills.append(cfg.current_node.get_fill())

        for neighbor, cost in cfg.current_node.get_available_neighbors():
            # marking them visited instead of looking in frontier makes the algorithm 2-3 times faster
            neighbor.cost_so_far = cfg.current_node.cost_so_far + cost
            neighbor.came_from = cfg.current_node
            neighbor.visited = True
            cfg.frontier.append(neighbor)


def astar_() -> None:       # display_steps
    """ Does A* algorithm on cfg.all_nodes, requires some parameter in config to be set

    :return: None
    """

    # while not cfg.path_found:     # doing one cycle per frame reeeally slows it down...
    if len(cfg.queue) == 0:
        cfg.path_found = True
        cfg.end_runtime = time.perf_counter_ns() / 10**6
        return

    # Now this is the biggest time consumer
    # POP IS FASTER FROM THE END OF LIST. SEE COLLECTION.DEQUE, (bidirectionnal)
    # import collections
    # collections.deque()
    # HOLY FUCK THATS FAST, went from 1.2s to 0.002s on a 500x500 snowed in grid
    cfg.current_node = cfg.queue.popleft()[0]

    if cfg.current_node is cfg.end_node:
        cfg.shortest_path.append(cfg.current_node)
        while cfg.current_node is not cfg.start_node:
            cfg.current_node = cfg.current_node.came_from
            cfg.shortest_path.append(cfg.current_node)
        cfg.shortest_path.reverse()
        cfg.path_found = True
        cfg.running = False
        # cfg.end_runtime = time.perf_counter_ns() / 10 ** 6
        cfg.end_runtime = pg.time.get_ticks()

        for node in cfg.shortest_path:
            node.is_path = True
            cfg.dirty_fills.append(node.get_fill())

    for neighbor, cost in cfg.current_node.get_available_neighbors():
        neighbor.visited = True
        if cfg.display_steps:
            cfg.dirty_fills.append(neighbor.get_fill())

        neighbor.came_from = cfg.current_node

        neighbor.cost_so_far = cfg.current_node.cost_so_far + cost

        # this needs to be changed to chessboard distance (King), nah actually makes weird shit
        if cfg.diago_allowed:
#            neighbor.heuristic = max(abs(cfg.end_node.row - neighbor.row), abs(cfg.end_node.column - neighbor.column))
            neighbor.heuristic = (((cfg.end_node.row - neighbor.row)**2
                                   + (cfg.end_node.column - neighbor.column)**2)**.5)

        else:
            neighbor.heuristic = abs(cfg.end_node.row - neighbor.row) + abs(cfg.end_node.column - neighbor.column)

        # prio is just for easier/faster access but idk if it does anything...
        # the int(100*()) allows us to compare ints to ints instead of floats to ints or wtv which is slower

        # Observed no major difference while placing/inserting

        # If im using *100 and int, i dont need to round the square roots beforehand, i will already keep .01 precision
        prio = neighbor.priority = int(10000 * (neighbor.cost_so_far + neighbor.heuristic))
        # prio = neighbor.priority = neighbor.cost_so_far + neighbor.heuristic

        if len(cfg.queue) == 0:
            cfg.queue.append((neighbor, neighbor.priority))

        # this should find intervals, not a direct value search
        else:
            index = bisect_left(cfg.queue, prio, key=lambda x: x[1])
            cfg.queue.insert(index, (neighbor, prio))


def symetryrectangle(start: cfg.Node, size: int):
    """Simulates an object creation by defining the nodes inside the square as borders or sym_rect if they are
    contained in the borders. This allows to skip neighbors when we are running our pathfinding algorithm.
    This applies on nodes in cfg.all_nodes.

    :param start: Top-left node of the square
    :param size: Length of a side of the square
    :return: None"""

    start_col = start.column
    start_row = start.row

    for row in range(size):
        for column in range(size):
            node = cfg.all_nodes[start_col + column][start_row + row]

            if row == 0 or row == size - 1 or column == 0 or column == size - 1:
                node.is_border = True
                # cfg.all_nodes[self.start_col + column][self.start_row + row].sym_rect = self  # not sure i need it

            else:
                node.is_sym_rect = True

            if cfg.display_steps:
                # this is what is eating a lot of time...
                # on the first run, it takes very minimal time: 0.300 s for 45 000 nodes
                # on the second and subsequent runs, it takes around 2 s for 45 000 nodes... idk why
                cfg.dirty_fills.append(node.get_fill())


def apply_RSR() -> None:
    """Applies Rectangular symmetry reduction to cfg.all_nodes, regrouping any square of free nodes (not walls)
    together, square sides must be atleast 4 or it will be skipped.
    :return: None"""

    # It would be nice to be able to prevent it from trying to apply RSR to nodes that have already been RSR'd...
    # But using a flat copy of cfg.all_nodes takes too much time to process.

    for column in cfg.all_nodes:
        for node_ in column:
            if not (node_.is_wall or node_.is_border or node_.is_sym_rect or node_.is_start or node_.is_end):

                start_col, start_row = node_.column, node_.row
                size = 1
                hit_wall = False

                while not hit_wall:
                    size += 1

                    try:
                        for y in range(size):
                            node = cfg.all_nodes[start_col + size - 1][start_row + y]
                            if node.is_wall or node.is_border or node.is_sym_rect or node.is_start or node.is_end:
                                hit_wall = True
                                break
                        for x in range(size):
                            node = cfg.all_nodes[start_col + x][start_row + size - 1]
                            if node.is_wall or node.is_border or node.is_sym_rect or node.is_start or node.is_end:
                                hit_wall = True
                                break
                    except IndexError: break

                size -= 1
                if size >= 4:
                    symetryrectangle(node_, size)

