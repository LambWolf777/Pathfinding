import csv
import collections
import os
import time
import tkinter
from tkinter import filedialog
import pickle
from typing import *

import pygame as pg

from classes import Node

pg.quit()   # config starts a pg window... I was able to make it hidden so we dont see.

folder_path = os.getcwd()

grid_path = os.path.join(folder_path, "Grids")
data_path = os.path.join(folder_path, "Data")

if not os.path.exists(grid_path):
    os.mkdir(grid_path)
if not os.path.exists(data_path):
    os.mkdir(data_path)


# from bisect! did not want to update to python 3.10 just for that...
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


class SimpleNode:
    """Object for representing every tile (node on the grid)"""

    is_path = False
    visited = False
    neighbors = None
    came_from = None
    cost_so_far = 0
    heuristic = 0
    priority = 0

    # for RSR
    is_sym_rect = False
    is_border = False

    def __init__(self, node):

        self.is_start = node.is_start
        self.is_end = node.is_end

        self.is_wall = node.is_wall

        self.column = node.column
        self.row = node.row

    def __str__(self):
        return f"SimpleNode ({self.column}, {self.row})"

    def update_sym_rect_neighbors(self) -> None:
        """Update the neighbors and costs of a node in the border of a symmetry rectangle, allowing to jump over
        symmetrical pathing possibilities.
        """

        def cycle_node(direction_, current_):
            """Move in neighbors direction until hitting the other border"""

            cost_multiplier = 1

            cycle_moves = {"right": lambda col, row: (col + 1, row),
                           "left": lambda col, row: (col - 1, row),
                           "down": lambda col, row: (col, row + 1),
                           "top": lambda col, row: (col, row - 1),
                           "topright": lambda col, row: (col + 1, row - 1),
                           "topleft": lambda col, row: (col - 1, row - 1),
                           "downright": lambda col, row: (col + 1, row + 1),
                           "downleft": lambda col, row: (col - 1, row + 1)
                           }

            while current_.is_sym_rect:
                cost_multiplier += 1
                new_col, new_row = cycle_moves[direction_](current_.column, current_.row)
                current_ = all_nodes[new_col][new_row]

            return current_, cost_multiplier

        for direction, (neighbor, cost) in self.neighbors.items():
            if neighbor.is_sym_rect:
                current, cost_mult = cycle_node(direction, neighbor)

                self.neighbors[direction] = current, cost*cost_mult

    def get_available_neighbors(self) -> List[Tuple['SimpleNode', int]]:
        """
        Return available (not walls and not visited) neighbors and their cost as a list.

        :return: List of adjacent node objects
        """

        if self.is_border:
            self.update_sym_rect_neighbors()

        neighbors = []
        for node, cost in self.neighbors.values():

            if not (node.is_wall or node.visited):
                neighbors.append((node, cost))

        return neighbors

    def get_neighbors(self, grid_: List[List['SimpleNode']]) -> None:
        """Procedure:
        Create a dict of all adjacent neighbors in the form neighbors["direction"] = node, cost as an attribute.

        :param grid_: Grid on which the node is located
        :return: None
        """

        neighbors = {}

        try:
            neighbors["right"] = grid_[self.column + 1][self.row], 1      # right
        except IndexError: pass
        try:
            neighbors["down"] = grid_[self.column][self.row + 1], 1      # down
        except IndexError: pass

        if not self.row == 0:
            neighbors["top"] = grid_[self.column][self.row - 1], 1      # up
        if not self.column == 0:
            neighbors["left"] = grid_[self.column - 1][self.row], 1     # left

        if diago:
            try:
                if not neighbors["down"][0].is_wall and not neighbors["right"][0].is_wall:
                    neighbors["downright"] = grid_[self.column + 1][self.row + 1], 1.41421  # botright
            except KeyError:
                pass
            try:
                if not neighbors["top"][0].is_wall and not neighbors["right"][0].is_wall:
                    neighbors["topright"] = grid_[self.column + 1][self.row - 1], 1.41421  # topright
            except KeyError:
                pass

            try:
                if not neighbors["down"][0].is_wall and not neighbors["left"][0].is_wall:
                    neighbors["downleft"] = grid_[self.column - 1][self.row + 1], 1.41421  # botleft
            except KeyError:
                pass
            try:
                if not neighbors["top"][0].is_wall and not neighbors["left"][0].is_wall:
                    neighbors["topleft"] = grid_[self.column - 1][self.row - 1], 1.41421  # topleft
            except KeyError:
                pass

        self.neighbors = neighbors


direct = ""


def select_grid():
    global direct

    def grid_is_valid(save_obj):
        if isinstance(save_obj["start"], Node)\
           and isinstance(save_obj["end"], Node)\
           and isinstance(save_obj["grid"], list):
            try:
                if isinstance(save_obj["grid"][0], list)\
                   and isinstance(save_obj["grid"][0][0], Node):
                    return True
                else:
                    return False
            except IndexError:
                return False
        else:
            return False

    root2 = tkinter.Tk()

    # make root transparent
    root2.attributes("-alpha", 0)

    direct = filedialog.askopenfilename(initialdir=grid_path)

    root2.update()

    try:
        root2.destroy()
    except:pass

    if direct and direct.endswith((".pickle", ".P", ".p")):
        print("Loading grid...")
        with open(direct, "rb") as file:
            save_object_ = pickle.load(file)
            print("Validating Grid...")
            if grid_is_valid(save_object_):
                print("Validation Successful!")
                return save_object_
            else:
                print("Validation failed, this object is not compatible")
                return
    else: return


def reduce_nodes(grid):
    start_ = time.perf_counter_ns()
    print("Converting grid to remove aberrant graphical data...")
    for x in range(len(grid)):
        print(f"Converting ... {round(x*100/len(grid), 1)}%")
        for y in range(len(grid[x])):
            grid[x][y] = SimpleNode(grid[x][y])

    print("Converting ... 100%")
    end_ = time.perf_counter_ns()
    reduce__time = end_ - start_
    print(f"Converted the grid in {reduce__time*10**-9}s\n")

    return grid, reduce__time


def set_all_neighbors(grid_):

    start = time.perf_counter_ns()
    print("Getting the neighbors of each node in the grid")
    n_col = len(grid_)

    for column_no in range(len(grid_)):
        print(f"Getting neighbors ... {round(column_no*100/n_col, 1)}%")

        for node in grid_[column_no]:
            node.get_neighbors(grid_)

    print(f"Getting neighbors ... 100%")
    end = time.perf_counter_ns()
    neighbors_time = end - start
    print(f"Set all neighbors in {neighbors_time*10**-9}s\n")

    return neighbors_time


def apply_RSR() -> int:
    """Applies Rectangular symmetry reduction to all_nodes, regrouping any square of free nodes (not walls)
    together, square sides must be atleast 4 or it will be skipped.
    :return: time taken in nanoseconds"""

    # It would be nice to be able to prevent it from trying to apply RSR to nodes that have already been RSR'd...
    # But using a flat copy of var.all_nodes takes too much time to process.

    def symetryrectangle(start: SimpleNode, size: int):
        """Simulates an object creation by defining the nodes inside the square as borders or sym_rect if they are
        contained in the borders. This allows to skip neighbors when we are running our pathfinding algorithm.
        This applies on nodes in all_nodes.

        :param start: Top-left node of the square
        :param size: Length of a side of the square
        :return: None"""

        start_col = start.column
        start_row = start.row

        for row in range(size):
            for column in range(size):
                node = all_nodes[start_col + column][start_row + row]

                if row == 0 or row == size - 1 or column == 0 or column == size - 1:
                    node.is_border = True

                else:
                    node.is_sym_rect = True

    start = time.perf_counter_ns()
    for column in all_nodes:
        for node_ in column:
            if not (node_.is_wall or node_.is_border or node_.is_sym_rect or node_.is_start or node_.is_end):

                start_col, start_row = node_.column, node_.row
                size = 1
                hit_wall = False

                while not hit_wall:
                    size += 1

                    try:
                        for y in range(size):
                            node = all_nodes[start_col + size - 1][start_row + y]
                            if node.is_wall or node.is_border or node.is_sym_rect or node.is_start or node.is_end:
                                hit_wall = True
                                break
                        for x in range(size):
                            node = all_nodes[start_col + x][start_row + size - 1]
                            if node.is_wall or node.is_border or node.is_sym_rect or node.is_start or node.is_end:
                                hit_wall = True
                                break
                    except IndexError: break

                size -= 1
                if size >= 4:
                    symetryrectangle(node_, size)
    end = time.perf_counter_ns()
    return end-start


def run(algorithm):
    shortest_path = []

    def init_search(algorithm_: str = algorithm) -> None:
        """ Initializes the algorithm chosen by algo (could change it to used var.algo...), depending on var.diago_allowed.
        Initialization consists of entering the first nodes in queue, setting the start node as visited.

        :param algorithm_: chosen algorithm as a string (put var.algo as parameter)
        :return: None
        """

        global queue
        start_node.visited = True

        if algorithm_ == "bfs" or algorithm_ == "dij":
            frontier.append(start_node)

        elif algorithm_ == "astar":
            queue = collections.deque()
            queue.append((start_node, start_node.priority))

    def bfs():
        nonlocal shortest_path
        """ Does a breadth first search (flood fill) on var.all_nodes, requires parameters from config to be set

        :return: None
        """
        path_found = False

        to_be_removed = []

        while not path_found:

            if len(frontier) == 0:
                path_found = True
                break

            for node in to_be_removed:
                if node in frontier:  # dont need it actually
                    frontier.remove(node)
            to_be_removed.clear()

            for node_no in range(len(frontier)):
                current_node = frontier[node_no]

                if current_node is end_node:

                    shortest_path.append(current_node)
                    previous_node = current_node.came_from
                    while current_node is not start_node:
                        current_node = previous_node
                        shortest_path.append(current_node)
                        previous_node = current_node.came_from
                    shortest_path.reverse()
                    path_found = True
                    break

                to_be_removed.append(current_node)

                for neighbor, cost in current_node.get_available_neighbors():
                    neighbor.visited = True
                    frontier.append(neighbor)
                    neighbor.came_from = current_node


    def dij():
        nonlocal shortest_path
        to_be_removed = []
        path_found = False
        cost_so_far = 0
        """ Dijkstra (weighted flood fill) on var.all_nodes, requires parameters from config to be set

        :return: None
        """

        while not path_found:
            if diago:
                cost_so_far += 1.41421
            else:
                cost_so_far += 1

            if len(frontier) == 0 and len(queue) == 0:
                path_found = True
                break

            for node in to_be_removed:
                if node in frontier:
                    frontier.remove(node)
            to_be_removed.clear()

            for node_no in range(len(frontier)):

                current_node = frontier[node_no]

                if not current_node.cost_so_far <= cost_so_far:
                    continue

                if current_node is end_node:

                    shortest_path.append(current_node)
                    while current_node is not start_node:
                        current_node = current_node.came_from
                        shortest_path.append(current_node)
                    shortest_path.reverse()
                    path_found = True
                    break

                to_be_removed.append(current_node)

                for neighbor, cost in current_node.get_available_neighbors():
                    # marking them visited instead of looking in frontier makes the algorithm 2-3 times faster
                    neighbor.cost_so_far = current_node.cost_so_far + cost
                    neighbor.came_from = current_node
                    neighbor.visited = True
                    frontier.append(neighbor)

    def astar():
        """ Does A* algorithm on all_nodes

        ** Some results may vary slightly with A*, due to the fact that neighbors are not set in the same order as in
        the visualizer. This will be noticeable in case of priority equalities, the paths taken may differ. Which in turns
        leads to different path lengths, especially if using RSR which does not count he nodes skipped by symmetry in the
        path length. **

        :return: None
        """

        nonlocal shortest_path
        path_found = False

        while not path_found:
            if len(queue) == 0:
                path_found = True
                break

            # POP IS FASTER FROM THE END OF LIST. SEE COLLECTION.DEQUE, (bidirectionnal)
            current_node = queue.popleft()[0]

            if current_node is end_node:
                shortest_path.append(current_node)
                while current_node is not start_node:
                    current_node = current_node.came_from
                    shortest_path.append(current_node)
                shortest_path.reverse()
                path_found = True

            for neighbor, cost in current_node.get_available_neighbors():
                neighbor.visited = True

                neighbor.came_from = current_node

                neighbor.cost_so_far = current_node.cost_so_far + cost

                # this needs to be changed to chessboard distance (King), nah actually makes weird shit
                if diago:
                    # neighbor.heuristic = max(abs(var.end_node.row - neighbor.row), abs(var.end_node.column - neighbor.column))
                    neighbor.heuristic = (((end_node.row - neighbor.row) ** 2
                                           + (end_node.column - neighbor.column) ** 2) ** .5)

                else:
                    neighbor.heuristic = abs(end_node.row - neighbor.row) + abs(
                        end_node.column - neighbor.column)

                # prio is just for easier/faster access but idk if it does anything...
                # the int(100*()) allows us to compare ints to ints instead of floats to ints or wtv which is slower

                # Observed no major difference while placing/inserting

                prio = neighbor.priority = int(10000 * (neighbor.cost_so_far + neighbor.heuristic))
                # prio = neighbor.priority = neighbor.cost_so_far + neighbor.heuristic

                if len(queue) == 0:
                    queue.append((neighbor, neighbor.priority))

                # this should find intervals, not a direct value search
                else:
                    index = bisect_left(queue, prio, key=lambda x: x[1])
                    queue.insert(index, (neighbor, prio))

    init_search(algo)

    if algo == "bfs":
        bfs()
    elif algo == "astar":
        astar()
    elif algo == "dij":
        dij()

    return shortest_path


if __name__ == "__main__":
    # "init tk..." else the first file dialog appears behind terminal
    root = tkinter.Tk()
    root.attributes("-alpha", 0)
    # this prevents an error message of event handling
    root.update()
    try:
        root.destroy()
    except:
        pass

    running = True

    while running:
        all_nodes = None
        start_node = None
        end_node = None
        frontier = []
        queue = []

        start_timer = 0
        end_timer = 0

        reduce_time = 0
        set_neighbors_time = 0
        rsr_time = 0

        time_sum = {"bfs": 0, "astar": 0, "dij": 0,
                    "bfslen": 0, "astarlen": 0, "dijlen": 0}

        diago = False
        apply_rsr = False
        algos = []
        n_cycles = 0

        print("You will need to select a .pickle file containing a valid grid/map made with the main file \n"
              "of the pathfinding visualiser")
        inp = input("Enter 'q' to quit or any key to continue\n")

        # problem if inp is not alpha?
        if inp.lower() == "q":
            running = False
            break

        else:
            save_object = None
            while save_object is None:

                save_object = select_grid()
                if save_object is not None:
                    all_nodes = save_object["grid"]
                    start_node = save_object["start"]
                    end_node = save_object["end"]
                    break
                else:
                    print("You need to select a pickle file containing a valid grid/map made with the main module \n"
                          "of the pathfinding visualiser")
                    inp = input("Enter 'q' to quit or any key to continue\n")

                    if inp.lower() == "q":
                        running = False
                        break

            if running is False: break

        all_nodes, reduce_time = reduce_nodes(all_nodes)
        start_node = all_nodes[start_node.column][start_node.row]
        end_node = all_nodes[end_node.column][end_node.row]

        while True:

            inp = input("Enter '0' to do specific testing or '1' to run every test variations\n")

            if inp == "0" or inp == "1":
                break

        if inp == "0":
            while True:
                inp = input("Allow diagonal movements between nodes? y/n\n")

                if inp.lower() == "y":
                    diago = True
                    break
                elif inp.lower() == "n":
                    diago = False
                    break

            set_neighbors_time, grid = set_all_neighbors(all_nodes)

            # inp = input("Do you wish to apply Rectangular Symetry Redction (RSR) to the grid? y/n\n")
            #
            # if inp == "y":
            #     apply_rsr = True

            while not algos:
                inp = input("Please select what algorithm(s) you want to test:\n"
                            "0 - all algorithms\n"
                            "1 - Breadth first search algorithm (Not functionnal with RSR)\n"
                            "2 - A* algorithm\n"
                            "3 - Dijkstra's algorithm\n"
                            "('1-3' or '2, 3' or even '13' will run corresponding algorithms)\n")

                if "0" in inp:
                    algos = ["bfs", "astar", "dij"]
                else:
                    if "1" in inp:
                        algos.append("bfs")
                    if "2" in inp:
                        algos.append("astar")
                    if "3" in inp:
                        algos.append("dij")

            while not n_cycles > 0:
                inp = input("How many times do you want to run each algorithm?\n")
                if not inp.isdigit():
                    print("Entry must be integer")
                    continue
                else:
                    n_cycles = int(inp)

            inp = input("Do you wish to apply rectangular symmetry recduction? y/n\n")

            if inp.lower() == "y":
                apply_rsr = True

            if apply_rsr:
                rsr_time = apply_RSR()

            for algo in algos:
                for n in range(n_cycles):
                    print(f"Running {algo.capitalize()} ({n + 1}/{n_cycles})...")
                    start_timer = time.perf_counter_ns()
                    time_sum[f'{algo}len'] = (len(run(algo)))
                    end_timer = time.perf_counter_ns()
                    time_sum[algo] += end_timer - start_timer
                    print(f"{algo.capitalize()} ({n + 1}/{n_cycles})... complete\n")

                    # resetting
                    frontier = []
                    queue = []
                    for column in all_nodes:
                        for node in column:
                            node.visited = False

            inp = input("Do you wish to save test data to a file? y/n\n")

            save_name = None
            if inp.lower() == "y":

                while save_name is None or save_name == "":

                    root = tkinter.Tk()

                    root.attributes("-alpha", 0)

                    save_name = filedialog.asksaveasfilename(initialdir=data_path, defaultextension=".txt", parent=root)
                    root.update()
                    try:
                        root.destroy()
                    except:
                        pass

                with open(f"{save_name}", "w") as file:
                    file.write(
                        f"Pathfinding algorithm benchmarks made on grid '{direct.split('/')[-1]}'\n"
                        f"\n"
                        f"Diagonal movement (no corner cutting) allowed:    {diago}\n"
                        f"Rectangular Symetry Reduction (RSR) applied:      {apply_rsr}\n"
                        f"\n"
                        f"RSR preprocess time:                      {rsr_time / 10 ** 9} s\n"
                        f"Loading neighbors preprocess time:        {set_neighbors_time / 10 ** 9} s\n"
                        f"\n"
                        f"Each algorithm was tested  {n_cycles}  times\n\n"
                        f"\tA* algorithm: \n"
                        f"\tFound a path of {time_sum['astarlen']} nodes in {time_sum['astar'] / (n_cycles * 10 ** 6)} ms on average\n"
                        f"\n"
                        f"\tBreadth First Search:  \n"
                        f"\tFound a path of {time_sum['bfslen']} nodes in {time_sum['bfs'] / (n_cycles * 10 ** 6)} ms on average\n"
                        f"\n"
                        f"\tDijkstra's Algorithm:  \n"
                        f"\tFound a path of {time_sum['dijlen']} nodes in {time_sum['dij'] / (n_cycles * 10 ** 6)} ms on average\n"
                    )
            print(
                f"Pathfinding algorithm benchmarks made on grid '{direct.split('/')[-1]}'\n"
                f"\n"
                f"Diagonal movement (no corner cutting) allowed:    {diago}\n"
                f"Rectangular Symetry Reduction (RSR) applied:      {apply_rsr}\n"
                f"\n"
                f"RSR preprocess time:                      {rsr_time / 10 ** 9} s\n"
                f"Loading neighbors preprocess time:        {set_neighbors_time / 10 ** 9} s\n"
                f"\n"
                f"Each algorithm was tested  {n_cycles}  times\n\n"
                f"\tA* algorithm: \n"
                f"\tFound a path of {time_sum['astarlen']} nodes in {time_sum['astar'] / (n_cycles * 10 ** 6)} ms on average\n"
                f"\n"
                f"\tBreadth First Search:  \n"
                f"\tFound a path of {time_sum['bfslen']} nodes in {time_sum['bfs'] / (n_cycles * 10 ** 6)} ms on average\n"
                f"\n"
                f"\tDijkstra's Algorithm:  \n"
                f"\tFound a path of {time_sum['dijlen']} nodes in {time_sum['dij'] / (n_cycles * 10 ** 6)} ms on average\n"
            )

        else:

            csv_name = f"delete_me_{direct.split('/')[-1]}.csv"
            header = "algo", "diago", "rsr", "neighbors_t", "rsr_t", "algo_t", "path_len"

            with open(csv_name, "w", newline="") as file:
                file_writer = csv.writer(file)
                file_writer.writerow(header)

            while not n_cycles > 0:
                inp = input("How many times do you want to run each variation?\n")
                if not inp.isdigit():
                    print("Entry must be positive integer")
                    continue
                else:
                    n_cycles = int(inp)

            diago_ = False, True
            apply_rsr_ = False, True
            algos_ = "bfs", "astar", "dij"

            for diago in diago_:
                set_neighbors_time = set_all_neighbors(all_nodes)

                for apply_rsr in apply_rsr_:
                    if apply_rsr:
                        rsr_time = apply_RSR()
                    else:
                        rsr_time = 0
                        for column in all_nodes:
                            for node in column:
                                node.is_sym_rect = False
                                node.is_border = False

                    for algo in algos_:

                        for n in range(n_cycles):
                            print(
                                f"Running {algo.capitalize()}, diago: {diago}, RSR: {apply_rsr} ({n + 1}/{n_cycles})...")
                            start_timer = time.perf_counter_ns()
                            time_sum[f'{algo}len'] = (len(run(algo)))
                            end_timer = time.perf_counter_ns()
                            time_sum[algo] += end_timer - start_timer
                            print(f"{algo.capitalize()} ({n + 1}/{n_cycles})... complete\n")

                            # resetting
                            frontier = []
                            queue = []
                            for column in all_nodes:
                                for node in column:
                                    node.visited = False

                        line = algo, diago, apply_rsr, set_neighbors_time, rsr_time, time_sum[algo] / n_cycles, \
                               time_sum[f"{algo}len"]
                        with open(csv_name, "a", newline="") as file:
                            file_writer = csv.writer(file)
                            file_writer.writerow(line)

            with open(csv_name, "r") as file:
                file_reader = csv.reader(file)
                row_list = [row for row in file_reader]
                row_list = row_list[1:]

            row_list.sort(key=lambda x: float(x[5]))

            text = (f"Pathfinding algorithm benchmarks made on grid '{direct.split('/')[-1]}'\n\n"
                    f"***Please note that the path found by Breadth First Search with RSR is not optimal***\n\n"
                    f"Sorted by algorithm process time (preprocess not included):\n")

            for line in row_list:
                if line[0] == "astar":
                    text += f"A* algorithm: \n"
                elif line[0] == "bfs":
                    text += f"Breadth First Search algorithm: \n"
                elif line[0] == "dij":
                    text += f"Dijkstra's algorithm: \n"

                text += (
                    f"\tDiagonal movement: {line[1]}, Rectangular Symetry Reduction (RSR): {line[2]}\n"
                    f"\tSet neighbors in {int(line[3]) / 10 ** 6} ms, Preprocessed RSR in {int(line[4]) / 10 ** 6} ms\n"
                    f"\tFound a path of {line[6]} nodes in {float(line[5]) / (n_cycles * 10 ** 6)} ms on average\n\n"
                )

            print(text)

            os.remove(csv_name)

            inp = input("Do you wish to save test data to a file? y/n\n")

            save_name = None
            if inp.lower() == "y":

                while save_name is None or save_name == "":

                    root = tkinter.Tk()

                    root.attributes("-alpha", 0)

                    save_name = filedialog.asksaveasfilename(initialdir=data_path, defaultextension=".txt", parent=root)
                    root.update()
                    try:
                        root.destroy()
                    except:
                        pass

                with open(f"{save_name}", "w") as file:
                    file.write(text)
