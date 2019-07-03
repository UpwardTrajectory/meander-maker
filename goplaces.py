import pandas as pd
import numpy as np
import ast
import webbrowser
import googlemaps
import gmplot
import polyline
import plotly_express as px
from haversine import haversine
from hdbscan import HDBSCAN

with open('.secret.key', 'r') as f:
    api_keys = ast.literal_eval(f.read().strip())

#plotly.offline.init_notebook_mode(connected=True)
px.set_mapbox_access_token(api_keys['mapbox'])
gmaps = googlemaps.Client(key=api_keys['googlemaps'])

def get_loc(current=True):
    """
    Initialize a location using one of two methods:
    ----------------
    current = True:
        Use data from cell towers, WiFi, and GPS
    current = False:
        Ask the user for a starting location
        This can be a string (search google maps, be specific)
        or a latitude-longitude coordinate
    ----------------
    returns a dictionary of the form:
    {'lat': 47.606269, 'lng': -122.334747}
    """
    output = None
    if current is True:
        output = gmaps.geolocate()['location']
    else:
        query = input('Where would you like to start?')
        coord_test = query.translate({ord(i):None for i in '()[]- ,.:;'})
        if (query.count(',') == 1 and coord_test.isnumeric()):
            coords = [float(x) for x in query.split(',')]
            output = {'lat' : coords[0], 'lng' : coords[1]}
        else:
            place = gmaps.find_place(query, input_type='textquery')
            place_id = place['candidates'][0]['place_id']
            output = gmaps.place(place_id)['result']['geometry']['location']
    return output


def get_topic():
    """Let the user choose which topic meander."""
    return input('What theme would you like to explore today?')


def populate_inputs(loc=None, topic=None):
    """
    If either location or topic don't exist yet, query the user to populate
    those inputs.
    """
    if loc is None:
        loc = get_loc(False)
    if topic is None:
        topic = get_topic()
    return loc, topic


def build_list(loc=None, topic=None, n=10):
    """
    --DEPRECIATED: USE build_df() INSTEAD--
    Given a location, topic, and number of stops, build a list (increasing
    dist from start location) of places to visit.
    """
    loc, topic = populate_inputs(loc, topic)
    output = gmaps.places_nearby(
        loc, 
        keyword=topic, 
        rank_by='distance',
    )
    return output['results'][:n]


def lat_lng_list(one_way_json):
    """
    --DEPRECIATED: USE build_df() INSTEAD--
    Parse the list of JSONs to extract individual lat / lng coordinates.
    --------
    returns a list of dictionaries of the form:
    [{'lat': 47.606269, 'lng': -122.334747}, ...]
    """
    return [x['geometry']['location'] for x in one_way_json]


def cluster(df, min_size=3, allow_single_cluster=True):
    """
    Use HDBSCAN --
    (Hierarchical Density-Based Spatial Clustering of Applications with Noise)
    to find the best clusters for the meander.
    """
    clusterer = HDBSCAN(
        min_cluster_size=min_size, 
        min_samples=3, 
        metric='haversine', 
        allow_single_cluster=allow_single_cluster
    )
    clusterer.fit(df[['lat', 'lng']])
    df['label'] = ['ABCDEFGHIJKLMN'[i] for i in clusterer.labels_]
    output = df.loc[df['label'] >= 'A']
    return output.sort_values('label').reset_index(drop=True)


def build_df(loc=None, topic=None, n=40):
    """
    Given a location, topic, and number of stops, build a df with cluster labels
    (increasing dist from start location) of places to visit.
    """
    loc, topic = populate_inputs(loc, topic)

    output = gmaps.places_nearby(
        loc, 
        keyword=topic, 
        rank_by='distance',
    )
    if 'next_page_token' in output.keys():
        import time
        time.sleep(2)
        next_page = gmaps.places_nearby(page_token=output['next_page_token'])
        output['results'].extend(query_result_next_page['results'])
    df = pd.DataFrame(
        [
            {'name': x['name'], 
             'rating': x['rating'],
             'user_ratings_total': x['user_ratings_total'],
             'lat': x['geometry']['location']['lat'], 
             'lng': x['geometry']['location']['lng']} 
        for x in output['results'][:n]
        ]
    )
    return cluster(df)


def meander(df, loc=None, mode='walking', verbose=False):
    """
    Given a list of places to visit, return a JSON of the stops.
    mode: Specifies the mode of transport to use when calculating directions.
         {"driving", "walking", "bicycling", "transit"}
    if verbose=True, also print out total meander dist & time.
    """
    loc = populate_inputs(loc, False)[0]
    df = choose_cluster(df, loc)[:10]

    start = df[['lat', 'lng']].iloc[0]
    stop = df[['lat', 'lng']].iloc[-1]
    wypnts = None
    if len(df) > 2:
        wypnts = df[['lat', 'lng']].iloc[1:-1].values.tolist()

    directions_result = gmaps.directions(
        start, stop, mode=mode,
        waypoints=wypnts, optimize_waypoints=True
    )
    if verbose:
        dist = 0
        time = 0
        for leg in directions_result[0]['legs']:
            leg_dist = leg['distance']['value']
            leg_time = leg['duration']['value']
            print(f'+{leg_dist} m --and-- +{round(leg_time/60, 2)} min')
            dist += leg_dist
            time += leg_time
        print(f'total dist: {dist} m \nest time: {round(time / 60, 1)} min')
    return directions_result[0]


def mapbox(df):
    """
    Plot the locations from a df containing ['lat', 'lng', 'name'] in an
    interactive window.
    """
    zoom = autozoom(df)
    output = px.scatter_mapbox(
        df, lat='lat', lon='lng', hover_name=['name', 'rating'], zoom=zoom,
        color='label', width=600, height=600
    )
    return output


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
    zoom_num = np.log2(
        156543.03392 * np.cos(np.radians(df['lat'].mean())) * pix / meters
    )
    return int(zoom_num) - 2


def html_builder(loc, meander, tab=False):
    """
    Build an HTML file (saved to current folder as "mymap.html")
    """
    df = pd.DataFrame([dest['end_location'] for dest in meander['legs']])
    poly = np.array(
        polyline.decode(meander['overview_polyline']['points'])
    )
    zoom = autozoom(df)
    
    gmapit = gmplot.GoogleMapPlotter(
        df['lat'].mean(), 
        df['lng'].mean(), 
        zoom=zoom, 
        apikey=api_keys['googlemaps']
    )
    gmapit.scatter(
        df['lat'], 
        df['lng'], 
        color='#f542a1', 
        size=20, 
        marker=False
    )
    gmapit.plot(poly[:,0], poly[:,1])
    gmapit.draw("mymap.html")
    
    if tab:
        url = 'file:///Users/dakaspar/flatiron/meander_maker/mymap.html'
        webbrowser.open(url, new=2)
    return


def haver_wrapper(row, loc):
    """
    Wrapper for haversine function that works on each row of a dataframe. 
    Intenionally NOT vectorized b/c it works faster on small dataframes.
    """
    p1 = loc['lat'], loc['lng']
    p2 = row['lat'], row['lng']
    return haversine(p1, p2, unit='m')
        
def cluster_metric(cluster, loc):
    """
    Evaluate which cluster is best. Goals are to:
    MINIMIZE: dist to first stop & total distance between stops
    MAXIMIZE: average rating & cluster size
    """
    size = len(cluster)
    lat_avg = cluster['lat'].mean()
    lng_avg = cluster['lng'].mean()
    rating_avg = cluster['rating'].mean()
    min_dist = cluster['dist_to_loc'].min()
    max_dist = cluster['dist_to_loc'].max()
    return 10**5 * size**1.2 * rating_avg / (min_dist * (max_dist - min_dist))


def choose_cluster(df, loc, mode='walking', verbose=False):
    """
    TODO: SettingWithCopyWarning still shows up
          Scale the "internal walking dist" to depend on mode of transport
    ---------------------
    Accepts a df from build_df() and chooses the optimal cluster to meander.
    loc is the starting location of the search, which should be a dictionary of
    the form: {'lat': 47.606269, 'lng': -122.334747}
    """
    scores = {}
    poss_clusters = {}
    for i in df['label'].unique():
        cluster = df.loc[df['label'] == i, :]
        cluster['dist_to_loc'] = df.apply(
            lambda row: haver_wrapper(row, loc), axis=1)
        poss_clusters[i] = cluster
        scores[i] = round(cluster_metric(cluster, loc), 4)
    
    best = max(scores, key=lambda k: scores[k])
    if verbose:
        display(scores)
        for cluster in poss_clusters.values():
            display(cluster)
    return poss_clusters[best]
