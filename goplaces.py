import pandas as pd
import numpy as np
import webbrowser
import googlemaps
import gmplot
import polyline
from haversine import haversine

with open('.secret.key') as f:
    api_key = f.read().strip()

gmaps = googlemaps.Client(key=api_key)


def get_loc(current=True):
    """
    Initialize a location using one of two methods:
    current = True:
        Use data from cell towers, WiFi, and GPS
    current = False:
        Ask the user for a starting location
        This can be a string (search google maps)
        or a latitude-longitude coordinate
    --------
    returns a dictionary of the form:
    {'lat': 47.606269, 'lng': -122.334747}
    """
    output = None
    if current is True:
        output = gmaps.geolocate()['location']
    else:
        query = input('Where would you like to start?')
        coord_test = query.translate({ord(i):None for i in '()[]- ,.'})
        if (query.count(',') == 1 and coord_test.isnumeric()):
            coords = [float(x) for x in query.split(',')]
            output = {'lat' : coords[0], 'lng' : coords[1]}
        else:
            place = gmaps.find_place(query, input_type='textquery')
            place_id = place['candidates'][0]['place_id']
            output = gmaps.place(place_id)['result']['geometry']['location']
    return output


def get_topic():
    """Let the user choose which topic to build a walk around."""
    return input('What theme walk would you like to explore today?')


def build_list(loc=None, topic=None, n=10):
    """
    Given a location, topic, and number of stops, build a list (increasing
    dist from start location) of places to visit.
    """
    if loc = None:
        loc = get_loc()
    if topic = None:
        topic = get_topic()
    output = gmaps.places_nearby(
        loc, 
        keyword=topic, 
        rank_by='distance',
    )
    return output['results'][:n]


def lat_lng_list(one_way_json):
    """Parse the list of JSONs to extract individual locations."""
    return [x['geometry']['location'] for x in one_way_json]


def walk(dest_list, verbose=False):
    """
    Given a list of places to visit, return a JSON of the stops. 
    if verbose = True, also print out total walking dist & time.
    """

    if len(dest_list) > 10:
        print("There is a maximum of 10 stops per adventure.")
        dest_list = dest_list[:10]

    start, stop = dest_list[0], dest_list[-1]

    waypoints = None
    if len(dest_list) > 2:
        waypoints = dest_list[1:-1]

    directions_result = gmaps.directions(
        start, stop, mode="walking",
        waypoints=waypoints, optimize_waypoints=True
    )

    if verbose:
        dist = 0
        time = 0
        for leg in directions_result[0]['legs']:
            temp_dist = leg['distance']['value']
            temp_time = leg['duration']['value']
            print(f'+{temp_dist} m --and-- +{round(temp_time/60, 2)} min')
            dist += temp_dist
            time += temp_time
        print(f'total dist: {dist} m \nest time: {round(time / 60, 1)} min')

    return directions_result[0]


def autozoom(df, pix=1440):
    """
    Determine max dist in meters using Haversine Formula, then use that 
    to work backwards to an ideal zoom number for google maps plotting.
    https://groups.google.com/forum/#!topic/google-maps-js-api-v3/hDRO4oHVSeM
    """
    meters = haversine(
        (df['lat'].min(), df['lng'].min()), 
        (df['lat'].max(), df['lng'].max()), 
        unit='m'
    )
    zoom_nu = np.log2(
        156543.03392 * np.cos(np.radians(df['lat'].mean())) * pix / meters
    )
    return int(zoom_nu) - 1


def html_builder(loc, walk, tab=False):
    """
    Build an HTML file (saved to current folder as "mymap.html")
    """
    df = pd.DataFrame([dest['end_location'] for dest in walk['legs']])
    poly = np.array(
        polyline.decode(walk['overview_polyline']['points'])
    )
    zoom = autozoom(df)
    
    gmapit = gmplot.GoogleMapPlotter(loc['lat'], loc['lng'], zoom=zoom, apikey=api_key)
    gmapit.scatter(df['lat'], df['lng'], '#f542a1', size=8, marker=False)
    gmapit.plot(poly[:,0], poly[:,1])
    gmapit.draw("mymap.html")
    
    if tab:
        url = 'file:///Users/dakaspar/flatiron/meander_maker/mymap.html'
        webbrowser.open(url, new=2)
    pass


def all_the_things(loc=None, topic=None):
    """
    ApiError: INVALID_REQUEST
    ------????????????? not sure why
    Combine getting topic, location, and then output an html
    """
    if loc is None:
        loc = get_loc(False)
    if topic is None:
        topic = get_topic()
        
    one_way_json = build_list(loc, topic)
    dest_list = lat_lng_list(one_way_json)
    return loc, walk(dest_list)
    



