import os
from cProfile import *
from pstats import *


def profile_algo(method, key=None):
    def wrapper(ref, *args, **kwargs):
        folder_path = os.getcwd()
        i = 1
        data_path = os.path.join(folder_path, f"Data\\{method.__name__}_profile_{1}.txt")
        while os.path.exists(data_path):
            i += 1
            data_path = os.path.join(folder_path, f"Data\\{method.__name__}_profile_{i}.txt")
        profiler = Profile()
        profiler.enable()
        while not ref.path_found:
            method(ref, *args, **kwargs)
        profiler.disable()
        profiler.create_stats()
        with open(data_path, "w", encoding="utf-8") as file:
            print(f"{method.__name__}, diago: {ref.diago}, RSR: {ref.apply_rsr}\n\n", file=file)
            stats = Stats(profiler, stream=file)
            stats.strip_dirs()
            stats.sort_stats(SortKey.CUMULATIVE)
            if key:
                stats.sort_stats(key)
            stats.print_stats()
    return wrapper


def std_profile(method, key=None):
    def wrapper(*args, **kwargs):
        folder_path = os.getcwd()
        i = 1
        data_path = os.path.join(folder_path, f"Data\\{method.__name__}_profile_{1}.txt")
        while os.path.exists(data_path):
            i += 1
            data_path = os.path.join(folder_path, f"Data\\{method.__name__}_profile_{i}.txt")
        profiler = Profile()
        profiler.enable()
        method(*args, **kwargs)
        profiler.disable()
        profiler.create_stats()
        with open(data_path, "w", encoding="utf-8") as file:
            stats = Stats(profiler, stream=file)
            stats.strip_dirs()
            stats.sort_stats(SortKey.CUMULATIVE)
            if key:
                stats.sort_stats(key)
            stats.print_stats()
    return wrapper
