# Pathfinding
Pathfinding Algorithm visualizer and benchmarking

Welcome to my first completed python/pygame project!

Pretty much everything was made from scratch, I used Pygame to have access to graphics.
I coded the Gui without any external librairies, which turned out to be the biggest part of the project!

![Showcase](https://user-images.githubusercontent.com/5695316/147415947-da66abe9-56cc-4229-8d68-e8ca9b16875c.gif)

---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Things you should know when playing with my program:

  The visualizer is good for looking at algorithm's workings and is also the grid editor you need to use to make use of the TerminalTesting.
    For benchmarking you should use the TerminalTesting.exe or script to make more accurate benchmarks (no time is used for the graphical aspect).
  
  There will be process time discrepancies between A* and Beadth First Search when running with run:0, because A* processes only one node per frame this way.
  You can put run: -1 to make the program run the algorithm until a path is found (no other tasks executed) or uncheck 'display steps' or use any other run times, given in           milliseconds to adjust the behavior as needed.
  
  When running algorithms in the visualizer with a very large grid (say 1000X800 nodes) with run -1 or not displaying steps, the window might become unresponsive, use terminal         testing instead or allow the program to process events (0 <= run <= 9999 ms).
  
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Thank you!
  

  
  
  
