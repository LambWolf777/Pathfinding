# Pathfinding
Pathfinding Algorithm visualizer and benchmarking

Welcome to my first completed python project!

---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Things you should know when playing with my program:

  The visualizer is good for looking at algorithm's workings and is also the grid editor you need to use to make use of the TerminalTesting.
    For benchmarking you should use the TerminalTesting.exe or script to make more accurate benchmarks (no time is used for the graphical aspect).
  
  There will be process time discrepancies between A* and Beadth First Search when running with run:0, because A* processes only one node per frame this way.
  You can put run: -1 to make the program run the algorithm until a path is found (no other tasks executed) or uncheck 'display steps' or use any other run times, given in           milliseconds to adjust the behavior as needed.
  
  When running algorithms in the visualizer with a very large grid (say 1000X800 nodes) with run -1 or not displaying steps, the window might become unresponsive, use terminal         testing instead or allow the program to process events (0 <= run <= 9999 ms).
  
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Feedback I am looking for:

(Sorry the code is not fully documented yet)
  
  -I would love some feedback on my general code structure, what is good practice, what I could've done better/differently
    (Here I know I should've placed my classes in a different module than config, and created the window in my GUI module, this caused me problems while doing the TerminalTesting module, since I wanted to import the node classe but it was opening a pygame window for a brief instant, I found a workaround or opening it hidden when __main__ was TerminalTesting.py).

  -If anybody knows pathfinding algorithms well and you want to look at my ALGO module and give me some feedback on my implementations, that would be very appreciated, especially my A* that feels a bit weird (and is almost always slower than BFS) especially without diagonal movements, it will start in a straight line. This started when I tried optimizing it and stopped sorting the queue on every loop, instead using the bisect function (from the bisect module) to only place the neighbor at the correct index in the queue according to it's priority.

  -My GUI! I did not use tkinter except for filedialogs, since this project is a learning experience above all, it was alot of fun learning how to go about handling all the buttons triggers, althought my GUI.handle_buttons feels really heavy, readability wise. Any feedback or different approaches are more than welcome!
 
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Thank you!
  

  
  
  
