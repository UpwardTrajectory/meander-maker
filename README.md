# Meander Maker

It's time for an urban themed walk! Perhaps you'd like to efficiently visit the nearest 4 bookstores, or build an itinerary for winetasting through a cluster of walkable tasting rooms. Anything is possible with Meander Maker. 

### What you bring to the game:
 * Starting Location
   * Ending Location (optional. If none is given, it will assume the same as the Start)
 * Theme 
   * used to search Google Maps from your Start Location
   * examples include:
     * bookstores
     * wine tasting
     * free museums
     * parks
     * any category [Google Maps](https://maps.google.com) would recognize
 * Preferred Length of your adventure
   * Multiple Metrics available, with sensible defaults
     * Number of stops (N=4)
     * Miles (dist=2)
     * Minutes of walking (mins=80)
   * Optional. If not given, will default to 4 stops, regardless of Length.
   * Automatically discerns whether the input is in miles or minutes.
     
### What the **Meander Maker** will do:
 * Locate the 'Nearest Neighbors' that meet your search criteria
 * Build the shortest walking path between stops
 * You *can* already do this in Google Maps, but it this process requires knowing the names of the individual stops AND the order you would like to traverse them in before the route can be generated. Meander-Maker automates all of that.
![example.png](https://github.com/UpwardTrajectory/meander-maker/blob/master/example.png?raw=true)
 
### To Do:
 * Render the map w/ path overlay
   * Even better, export to Google Maps and begin the navigation
 * Allow "veto" of individual locations, then re-build the path
