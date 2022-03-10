from collections import deque
from time import perf_counter_ns
from typing import *
from sys import exit
import tkinter
from tkinter import filedialog
import os
from classes import Node
import pickle
import csv


def reduce_nodes(all_nodes):
    if isinstance(all_nodes, list):
        print("Converting grid to remove aberrant graphical data...")
        for x in range(len(all_nodes)):
            for y in range(len(all_nodes[x])):
                all_nodes[x][y] = SimpleNode(all_nodes[x][y])

        print("Converting ... 100%")
        return all_nodes
    else:
        node = SimpleNode(all_nodes)
        return node


def load_grid(grid_path):

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
            save_object = pickle.load(file)
            print("Validating Grid...")
            if grid_is_valid(save_object):
                print("Validation Successful!")
                return save_object, direct.split('/')[-1]
            else:
                print("Validation failed, this object is not compatible")
                return
    else: return


class Console:
    def __init__(self, grid: 'SimpleGrid', pathfinder: 'SimplePathFinder'):
        self.test = None
        self.input = None
        self.n_cycles = 0
        self.algos = []

        self.grid = grid
        self.pathfinder = pathfinder

        self.grid_path = os.path.join(os.getcwd(), "Grids")
        self.data_path = os.path.join(os.getcwd(), "Data")

    def select_grid(self):
        print("\nYou will need to select a .pickle file containing a valid grid/map made with the pathfinding visualiser")
        inp = input("Enter 'q' to quit or any key to continue\n")

        # problem if inp is not alpha?
        if inp.lower() == "q":
            exit()

        else:
            save_object = None
            while save_object is None:

                try:
                    save_object, self.grid.name = load_grid(self.grid_path)
                except TypeError: pass
                if save_object is not None:
                    self.grid.all_nodes = reduce_nodes(save_object["grid"])
                    self.grid.start = self.grid.all_nodes[save_object["start"].column][save_object["start"].row]
                    self.grid.end = self.grid.all_nodes[save_object["end"].column][save_object["end"].row]
                    break
                else:
                    print("\nYou need to select a pickle file containing a valid grid/map made with the main module \n"
                          "of the pathfinding visualiser")
                    inp = input("Enter 'q' to quit or any key to continue\n")

                    if inp.lower() == "q":
                        exit()

    def choose_test(self):
        while True:
            self.input = input("Enter '0' to do specific testing or '1' to run every test variations\n")

            if self.input == "0":
                self.test = self.specific
                return
            elif self.input == "1":
                self.test = self.all
                return

    def all(self):
        def main():
            csv_name = make_csv()
            set_cycles()
            run_all(csv_name)
            text = create_results(csv_name)
            save(text)

        def make_csv():
            csv_name = f"delete_me_{self.grid.name}.csv"
            header = "algo", "diago", "rsr", "neighbors_t", "rsr_t", "algo_t", "path_len"

            with open(csv_name, "w", newline="") as file:
                file_writer = csv.writer(file)
                file_writer.writerow(header)
            return csv_name

        def set_cycles():
            self.n_cycles = 0
            while not self.n_cycles > 0:
                inp = input("How many times do you want to run each variation?\n")
                if not inp.isdigit():
                    print("Entry must be positive integer")
                    continue
                else:
                    self.n_cycles = int(inp)

        diago_ = False, True
        apply_rsr_ = False, True
        algos_ = "bfs", "astar", "dijkstra"

        def run_all(csv_name):
            for diago in diago_:
                for apply_rsr in apply_rsr_:
                    self.pathfinder.apply_rsr = apply_rsr
                    self.pathfinder.diago = diago
                    self.pathfinder.init_search()
                    for algo in algos_:
                        if not (algo == "bfs" and apply_rsr is True):

                            self.pathfinder.algo = algo

                            self.pathfinder.init_search(False)

                            for n in range(self.n_cycles):

                                print(f"Running {algo.capitalize()}, diago: {diago}, RSR: {apply_rsr} "
                                      f"({n + 1}/{self.n_cycles})...")

                                self.pathfinder.run()

                                print(f"{algo.capitalize()} ({n + 1}/{self.n_cycles})... complete\n")
                                if n < self.n_cycles - 1:
                                    self.pathfinder.soft_reset()

                            info = algo, diago, apply_rsr, self.pathfinder.neighbors_prep_dt, \
                                self.pathfinder.rsr_prep_dt, \
                                self.pathfinder.algo_dt / self.n_cycles, len(self.pathfinder.shortest_path)

                            with open(csv_name, "a", newline="") as f:
                                file_writer = csv.writer(f)
                                file_writer.writerow(info)

                            self.pathfinder.soft_reset(timer=True)
                    self.pathfinder.soft_reset(neighbors=True, timer=True)

        def create_results(csv_name):

            with open(csv_name, "r") as file:
                file_reader = csv.reader(file)
                row_list = [row for row in file_reader]
                row_list = row_list[1:]

            row_list.sort(key=lambda x: float(x[5]))

            text = (f"\nPathfinding algorithm benchmarks made on grid '{self.grid.name}'\n\n"
                    f"Sorted by algorithm process time (preprocess not included):\n\n")

            for line in row_list:
                if line[0] == "astar":
                    text += f"A* algorithm: \n"
                elif line[0] == "bfs":
                    text += f"Breadth First Search algorithm: \n"
                elif line[0] == "dijkstra":
                    text += f"Dijkstra's algorithm: \n"

                text += (
                    f"\tDiagonal movement: {line[1]}, Rectangular Symmetry Reduction (RSR): {line[2]}\n"
                    f"\tSet neighbors in {round(float(line[3]), 2)} ms, Preprocessed RSR in {round(float(line[4]), 2)} ms\n"
                    f"\tFound a path of {line[6]} nodes in "
                    f"{round(float(line[5]), 2)} ms on average\n\n"
                )

            print(text)

            os.remove(csv_name)
            return text

        def save(text):
            inp = input("Do you wish to save test data to a file? y/n\n")

            save_name = None
            if inp.lower() == "y":

                while not save_name:
                    root = tkinter.Tk()
                    root.attributes("-alpha", 0)
                    save_name = filedialog.asksaveasfilename(initialdir=self.data_path, defaultextension=".txt",
                                                             parent=root)
                    root.update()
                    try:
                        root.destroy()
                    except:
                        pass

                with open(f"{save_name}", "w") as file:
                    file.write(text)

        main()

    # TODO
    def specific(self):
        def main():
            setup()
            run()
            save()

        stats = {"astar_time": 0, "astar_len": 0,
                 "bfs_time": 0, "bfs_len": 0,
                 "dijkstra_time": 0, "dijkstra_len": 0}

        def setup():
            while True:
                self.input = input("Do you wish to apply rectangular symmetry recduction? y/n\n")
                if self.input.lower() == "y":
                    self.pathfinder.apply_rsr = True
                    break
                elif self.input.lower() == "n":
                    self.pathfinder.apply_rsr = False
                    break
            while True:
                self.input = input("Allow diagonal movements between nodes? y/n\n")
                if self.input.lower() == "y":
                    self.pathfinder.diago = True
                    break
                elif self.input.lower() == "n":
                    self.pathfinder.diago = False
                    break
            self.pathfinder.init_search()

            while not self.algos:
                self.input = input("Please select what algorithm(s) you want to test:\n"
                            "0 - all algorithms\n"
                            "1 - Breadth first search algorithm (Not functionnal with RSR)\n"
                            "2 - A* algorithm\n"
                            "3 - Dijkstra's algorithm\n"
                            "('1-3' or '2, 3' or even '13' will run corresponding algorithms)\n")

                if "0" in self.input:
                    self.algos = ["bfs", "astar", "dijkstra"]
                else:
                    if "1" in self.input:
                        self.algos.append("bfs")
                    if "2" in self.input:
                        self.algos.append("astar")
                    if "3" in self.input:
                        self.algos.append("dijkstra")

            while not self.n_cycles > 0:
                self.input = input("How many times do you want to run each algorithm?\n")
                if not self.input.isdigit():
                    print("Entry must be integer")
                    continue
                else:
                    self.n_cycles = abs(int(self.input))

        def run():
            for algo in self.algos:
                self.pathfinder.algo = algo
                self.pathfinder.init_search(prep=False)
                for n in range(self.n_cycles):
                    print(f"Running {algo.capitalize()} ({n + 1}/{self.n_cycles})...")
                    self.pathfinder.run()
                    print(f"{algo.capitalize()} ({n + 1}/{self.n_cycles})... complete\n")

                    if n < self.n_cycles - 1:
                        self.pathfinder.soft_reset()
                stats[f"{algo}_time"] = self.pathfinder.algo_dt / self.n_cycles
                stats[f"{algo}_len"] = len(self.pathfinder.shortest_path)

                self.pathfinder.soft_reset(timer=True)

        def save():
            text = (f"Pathfinding algorithm benchmarks made on grid '{self.grid.name}'\n"
                    f"\n"
                    f"Diagonal movement (no corner cutting) allowed:    {self.pathfinder.diago}\n"
                    f"Rectangular Symetry Reduction (RSR) applied:      {self.pathfinder.apply_rsr}\n"
                    f"\n"
                    f"RSR preprocess time:                      {self.pathfinder.rsr_prep_dt / 10 ** 3} s\n"
                    f"Loading neighbors preprocess time:        {self.pathfinder.neighbors_prep_dt / 10 ** 3} s\n"
                    f"\n"
                    f"Each algorithm was tested  {self.n_cycles}  times\n\n"
                    f"\tA* algorithm: \n"
                    f"\tFound a path of {stats['astar_len']} nodes in "
                    f"{stats['astar_time']} ms on average\n"
                    f"\n"
                    f"\tBreadth First Search:  \n"
                    f"\tFound a path of {stats['bfs_len']} nodes in "
                    f"{stats['bfs_time']} ms on average\n"
                    f"\n"
                    f"\tDijkstra's Algorithm:  \n"
                    f"\tFound a path of {stats['dijkstra_len']} nodes in "
                    f"{stats['dijkstra_time']} ms on average\n")

            print(text)

            self.input = input("Do you wish to save test data to a file? y/n\n")

            save_name = None
            if self.input.lower() == "y":

                while not save_name:

                    root = tkinter.Tk()
                    root.attributes("-alpha", 0)
                    save_name = filedialog.asksaveasfilename(initialdir=self.data_path, defaultextension=".txt",
                                                             parent=root)
                    root.update()
                    try:
                        root.destroy()
                    except:
                        pass

                with open(f"{save_name}", "w") as file:
                    file.write(text)

        main()

    def main(self):
        self.select_grid()
        self.choose_test()
        self.test()


class SimpleGrid:
    def __init__(self):
        self.all_nodes = [[]]
        self.start = None
        self.end = None
        self.name = None


CYCLE_MOVES = {"right": lambda col, row: (col + 1, row),
               "left": lambda col, row: (col - 1, row),
               "down": lambda col, row: (col, row + 1),
               "up": lambda col, row: (col, row - 1),
               "topright": lambda col, row: (col + 1, row - 1),
               "topleft": lambda col, row: (col - 1, row - 1),
               "downright": lambda col, row: (col + 1, row + 1),
               "downleft": lambda col, row: (col - 1, row + 1)
               }


class SimpleNode:
    """Object for representing every tile (node on the grid)"""

    # Those attributes will be used as instance attributes, but it was simpler to define them here since they
    # always start with the same values

    is_path = False
    is_wall = False
    visited = False
    neighbors = None
    came_from = None
    cost_so_far = 0
    heuristic = 0
    priority = 0

    # for RSR
    sym_rect = None
    is_sym_rect = False
    is_border = False
    is_start = False
    is_end = False

    def __init__(self, node: Node) -> None:
        """ Create a Node object

        :param node: Node to be copied
        """
        self.column = node.column
        self.row = node.row
        self.is_wall = node.status & Node.WALL
        self.is_start = node.status & Node.START
        self.is_end = node.status & Node.END

    # TODO: Optimize this method
    def update_sym_rect_neighbors(self, grid: List[List['SimpleNode']]) -> None:
        """ For a Node in the border of a symmetry rectangle, change its neighbor in the symmetry rectangle for
        the next one that is a border (jump through rectangle)"""

        def cycle_node(direction: str, current: 'SimpleNode') -> Tuple['SimpleNode', int]:
            """ Increment neighbor's position in given direction until the neighbor is a border

            :param direction: current's direction key from initial node
            :param current: current neigbor of the initial node
            :return: final neighbor and cost multiplier (number of nodes from initial to final)
            """

            cost_multiplier = 1

            while current.is_sym_rect:
                cost_multiplier += 1
                new_col, new_row = CYCLE_MOVES[direction](current.column, current.row)
                current = grid[new_col][new_row]

            return current, cost_multiplier

        for direction, (neighbor, cost) in self.neighbors.items():
            if neighbor.is_sym_rect:
                current, cost_mult = cycle_node(direction, neighbor)
                self.neighbors[direction] = current, cost * cost_mult

    def get_available_neighbors(self) -> List[Tuple['SimpleNode', int]]:
        """ Return available (not walls and not visited) neighbors and their cost as a list.

        :return: List of adjacent node objects
        """

        neighbors = []

        for node, cost in self.neighbors.values():
            if not (node.is_wall or node.visited):
                neighbors.append((node, cost))

        return neighbors

    def get_neighbors(self, grid: List[List['SimpleNode']], diago_allowed: bool = False) -> None:
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
                if not neighbors["down"][0].is_wall and not neighbors["right"][0].is_wall:
                    neighbors["downright"] = grid[self.column + 1][self.row + 1], 1.41421  # botright
            except KeyError:
                pass
            try:
                if not neighbors["up"][0].is_wall and not neighbors["right"][0].is_wall:
                    neighbors["topright"] = grid[self.column + 1][self.row - 1], 1.41421  # topright
            except KeyError:
                pass

            try:
                if not neighbors["down"][0].is_wall and not neighbors["left"][0].is_wall:
                    neighbors["downleft"] = grid[self.column - 1][self.row + 1], 1.41421  # botleft
            except KeyError:
                pass
            try:
                if not neighbors["up"][0].is_wall and not neighbors["left"][0].is_wall:
                    neighbors["topleft"] = grid[self.column - 1][self.row - 1], 1.41421  # topleft
            except KeyError:
                pass

        self.neighbors = neighbors
        if self.is_border:  # if self is border...
            self.update_sym_rect_neighbors(grid)


def get_dt(func):
    """ Decorator to get time of execution in ms"""
    def inner(*args, **kwargs):
        start = perf_counter_ns()
        func(*args, **kwargs)
        end = perf_counter_ns()
        return (end - start) / 10 ** 6
    return inner


class SimplePathFinder:
    """Pathfinding tool to apply pathfinding algorithms and related methods to the grid specified in init"""

    running = False
    path_found = False
    search_is_init = False

    diago = False
    apply_rsr = False

    algo = "bfs"

    dijkstra_cost_so_far = 0

    frontier = []
    queue = deque()  # for ASTAR
    to_be_removed = []
    shortest_path = []

    neighbors_prep_dt = 0
    rsr_prep_dt = 0
    algo_dt = 0

    def __init__(self, grid: SimpleGrid):
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

        return path

    @get_dt
    def set_neighbors(self):
        for column in self.grid.all_nodes:
            for node in column:
                if not node.is_sym_rect and not node.is_wall:
                    node.get_neighbors(self.grid.all_nodes, self.diago)

    def soft_reset(self, neighbors=False, timer=False):
        self.search_is_init = False
        self.path_found = False
        if timer:
            self.algo_dt = 0
        if neighbors:
            self.rsr_prep_dt = 0
            self.neighbors_prep_dt = 0
        self.frontier = [self.grid.start]
        self.queue = deque()
        self.queue.append((self.grid.start, 0))
        self.to_be_removed = []
        self.shortest_path = []
        self.dijkstra_cost_so_far = 0

        for column in self.grid.all_nodes:
            for node in column:
                node.visited = False
                if neighbors:
                    node.is_border = False
                    node.is_sym_rect = False
                    node.neighbors = None

    def init_search(self, prep=True) -> None:
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

        if prep:
            if self.apply_rsr:
                self.rsr_prep_dt = self.apply_RSR()

            self.neighbors_prep_dt = self.set_neighbors()

        # Init all algorithms
        self.grid.start.visited = True
        self.frontier = [self.grid.start]
        self.queue = deque()
        self.queue.append((self.grid.start, self.grid.start.priority))

        self.search_is_init = True

    def check_done(self) -> bool:
        """ Checks if the queue/frontier is empty, if it is, post a no path found event and terminate processing
        timer.

        :return: path_found is used to say the algorithm's processing is done (in this case no path was found)
        """
        # This works since both are initialized and can only be empty if they were used
        if not self.frontier or not self.queue:
            self.path_found = True
        return self.path_found

    def clean_frontier(self) -> None:
        """ Remove processed nodes from the frontier
        """
        for node in self.to_be_removed:
            if node in self.frontier:
                self.frontier.remove(node)
        self.to_be_removed.clear()

    def expand_frontier(self, node: SimpleNode, costs: bool = False) -> None:
        """ Adds the available neighbors of the nodes to the frontier and marks the current node as visited

        :param node: current node
        :param costs: True if the algorithm needs to know the cost_so_far of each node (Dijkstra)
        :return:
        """

        for neighbor, cost in node.get_available_neighbors():
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

        if node is self.grid.end:
            self.shortest_path = self.build_path()

        # I don't feel like it's worth wrapping this in another function, since no other algorithm uses it
        for neighbor, cost in node.get_available_neighbors():
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

    def symmetry_rectangle(self, start: SimpleNode, size: int) -> None:
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

    # noinspection PyUnresolvedReferences
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

    def run(self) -> None:
        """
        Procedure to run the algorithm chosen in init_search.
        Note: running display steps as True with run_interval = -1 will loop chosen algorithm until a path
        is found (or no path) and show visited nodes, whereas setting display steps to False will loop until a
        path is found (or no path) but won't show visited nodes.

        :return: None
        """

        while not self.path_found:
            self.algo_dt += self.algo()


def init_pathfinder(grid: SimpleGrid) -> SimplePathFinder:
    """ Initialises the Singleton pathfinder object, needs an associated grid object to apply algorithms on
    :param grid: Grid object associated with the pathfinder
    :return: Pathfinder entity
    """
    return SimplePathFinder(grid)


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


if __name__ == "__main__":
    grid = SimpleGrid()
    pathfinder = init_pathfinder(grid)
    console = Console(grid, pathfinder)

    while True:
        console.main()

