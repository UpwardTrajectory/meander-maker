# Meander Maker

### [meander.datakaspar.com](https://meander.datakaspar.com)

[Slideshow Presentation](https://docs.google.com/presentation/d/1FJpiMcubybSbuHfuLMKDdqAZSo0YrzePHE2okCvVc_4/edit?usp=sharing)

It's time for an urban themed walk! Perhaps you'd like to efficiently visit the nearest group of bookstores, or build an itinerary for winetasting through a cluster of walkable tasting rooms. Of course there's always the good old-fashioned pub crawl. Anything is possible with Meander Maker!

### What you bring to the game:
 * Starting Location
 * Theme 
   * used to search Google Maps from your Start Location
   * examples include:
     * bookstores
     * wine tasting
     * free museums
     * women's shoes
     * parks
     * any category [Google Maps](https://maps.google.com) would recognize

     
### What the **Meander Maker** will do:
1. Search GoogleMaps for up to 60 matches near your starting location.
2. Break them into geographic clusters (and drop results that are "loners" aka far from everything else.)
3. Pick the "Best" cluster, based on:

   * High Ratings from google maps
   * High density within the cluster
   * short distance from current starting location
   * short distance within stops of the cluster  
    
    
4. Build the shortest transportation path between stops

   * Walking
   * Biking
   * Driving
   * Public Transit
   
   
5. You *can* already do this in Google Maps, but it this process requires knowing the names of the individual stops AND the order you would like to traverse them in before the route can be generated. Meander-Maker automates all of that.
![example.png](https://github.com/UpwardTrajectory/meander-maker/blob/master/readme_example.png?raw=true)

But Meander-Maker will do something like this:
![clusters of wine rooms](https://github.com/UpwardTrajectory/meander-maker/blob/master/readme_clusters.png?raw=true)  
And find the best cluster, then also return turn-by-turn directions.
 
### To Do:
 * Allow "veto" of individual locations, then re-build the path
 * Fix "Geo-locate" so that it will find the location the front-end client, instead of the AWS server
 * Preferred Length of your Adventure
   * accept multiple input restrictions, with sensible defaults
     * Number of stops (N=4)
     * Miles (dist=2)
     * Minutes of walking (mins=80)
   * Optional. If not given, will default to 4 stops, regardless of Length.
   * Automatically discerns whether the input is in miles or minutes.
