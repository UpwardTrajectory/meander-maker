import pandas as pd
import numpy as np
import time
import ast
import webbrowser
import googlemaps
import gmplot
import polyline
import plotly_express as px
from haversine import haversine
from hdbscan import HDBSCAN

with open(".secret.key", "r") as f:
    api_keys = ast.literal_eval(f.read().strip())

px.set_mapbox_access_token(api_keys["mapbox"])
gmaps = googlemaps.Client(key=api_keys["samesame_gmaps"])


def get_loc(query, current=True):
    """Initialize a location using one of two methods:
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
        output = gmaps.geolocate()["location"]
    else:
        coord_test = query.translate({ord(i): None for i in "{}()[]- ,.:;"})
        if query.count(",") == 1 and coord_test.isnumeric():
            coords = [float(x) for x in query.split(",")]
            output = {"lat": coords[0], "lng": coords[1]}
        else:
            place = gmaps.find_place(query, input_type="textquery")
            place_id = place["candidates"][0]["place_id"]
            output = gmaps.place(place_id)["result"]["geometry"]["location"]
    return output


def get_topic():
    """Let the user choose which topic to meander."""
    return input("What theme would you like to explore today?")


def populate_inputs(loc=None, topic=None):
    """If either location or topic don't exist yet, query the user to populate
    those inputs.
    """
    if loc is None:
        query = input("Where would you like to start?")
        loc = get_loc(query, current=False)
    if topic is None:
        topic = get_topic()
    return loc, topic


def cluster(df, min_size=4, allow_single_cluster=True):
    """Use HDBSCAN --
    (Hierarchical Density-Based Spatial Clustering of Applications with Noise)
    to find the best clusters for the meander.
    """
    clusterer = HDBSCAN(
        min_cluster_size=min_size,
        min_samples=3,
        metric="haversine",
        allow_single_cluster=allow_single_cluster,
    )
    clusterer.fit(df[["lat", "lng"]])
    df.loc[:, "label"] = ["ABCDEFGHIJKLMN"[i] for i in clusterer.labels_]
    return df.sort_values("label").reset_index(drop=True)


def build_df(loc=None, topic=None, n=60):
    """Given a location, topic, and number of stops, build a df with cluster
    labels (increasing dist from start location) of places to visit.
    """
    loc, topic = populate_inputs(loc, topic)

    output = gmaps.places_nearby(loc, keyword=topic, rank_by="distance")
    while len(output["results"]) < n and ("next_page_token" in output.keys()):
        time.sleep(2)
        next_page = gmaps.places_nearby(page_token=output["next_page_token"])
        output["results"].extend(next_page["results"])

    df = pd.DataFrame(
        [
            {
                "name": x["name"],
                "rating": x["rating"],
                "user_ratings_total": x["user_ratings_total"],
                "lat": x["geometry"]["location"]["lat"],
                "lng": x["geometry"]["location"]["lng"],
            }
            for x in output["results"][:n]
        ]
    )
    return cluster(df)


def meander(df, loc=None, mode="walking", verbose=False):
    """Given a list of places to visit, return a JSON of the stops.
    mode: Specifies the mode of transport to use when calculating directions.
         {"driving", "walking", "bicycling", "transit"}
    if verbose=True, also print out total meander dist & time.
    """
    if loc is None:
        loc = populate_inputs(loc, False)[0]
    # df = choose_cluster(df, loc, weights)[:10]

    start = df[["lat", "lng"]].iloc[0]
    stop = df[["lat", "lng"]].iloc[-1]
    wypnts = None
    if len(df) > 2:
        wypnts = df[["lat", "lng"]].iloc[1:-1].values.tolist()

    directions_result = gmaps.directions(
        start, stop, mode=mode, waypoints=wypnts, optimize_waypoints=True
    )
    if verbose:
        dist = 0
        time = 0
        for leg in directions_result[0]["legs"]:
            leg_dist = leg["distance"]["value"]
            leg_time = leg["duration"]["value"]
            print(f"+{leg_dist} m --and-- +{round(leg_time/60, 2)} min")
            dist += leg_dist
            time += leg_time
        print(f"total dist: {dist} m \nest time: {round(time / 60, 1)} min")
    return directions_result[0]


def mapbox(df):
    """Plot the locations from a df containing ['lat', 'lng', 'name'] in an
    interactive window.
    """
    zoom = autozoom(df) - 3
    output = px.scatter_mapbox(
        df,
        lat="lat",
        lon="lng",
        hover_name=["name", "rating"],
        zoom=zoom,
        color="label",
        width=600,
        height=600,
    )
    return output


def autozoom(df, pix=1440):
    """Determine max dist in meters using Haversine Formula, then use that
    to work backwards to an ideal zoom number for google maps plotting.
    https://groups.google.com/forum/#!topic/google-maps-js-api-v3/hDRO4oHVSeM
    ------------------------------------
    When actually calling this function:
        * subtract 1 inside google maps html_builder
        * subtract 3 inside mapbox
    """
    if len(df) < 2:
        return 3
    meters = haversine(
        (df["lat"].min(), df["lng"].min()),
        (df["lat"].max(), df["lng"].max()),
        unit="m"
    )
    zoom_num = np.log2(
        156543.03392 * np.cos(np.radians(df["lat"].mean())) * pix / meters
    )
    if zoom_num < 2:
        zoom_num = 2
    return int(zoom_num)


def html_builder(loc, meander, tab=False, save_file=False, flask_output=False):
    """Build an HTML file (saved to current folder as 'mymap.html')"""
    df = pd.DataFrame([dest["start_location"] for dest in meander["legs"]])
    df = df.append([meander["legs"][-1]["end_location"]], ignore_index=True)
    poly = np.array(polyline.decode(meander["overview_polyline"]["points"]))
    zoom = autozoom(df) - 1

    gmapit = gmplot.GoogleMapPlotter(
        df["lat"].mean(),
        df["lng"].mean(),
        zoom=zoom,
        apikey=api_keys["googlemaps"]
    )
    gmapit.scatter(df["lat"], df["lng"],
                   color="#f542a1", size=20, marker=False)
    gmapit.plot(poly[:, 0], poly[:, 1])

    if save_file is not False:
        gmapit.draw(save_file)

    if tab or flask_output:
        gmapit.draw("mymap.html")
    if tab is True:
        url = "file:///Users/dakaspar/flatiron/meander_maker/mymap.html"
        webbrowser.open(url, new=2)
    if flask_output is True:
        output = ""
        with open("mymap.html") as f:
            for line in f:
                output += line
        return output
    return


def haver_wrapper(row, loc):
    """Wrapper for haversine function that works on each row of a dataframe.
    Intenionally NOT vectorized b/c it works faster on small dataframes.
    """
    p1 = loc["lat"], loc["lng"]
    p2 = row["lat"], row["lng"]
    return haversine(p1, p2, unit="m")


def scale_param(param):
    """Clean the input from HTML and scale to become a better exponent"""
    return np.log2(float(param))


def cluster_metric(cluster, loc, weights=None):
    """Evaluate which cluster is best. Goals are to:
    MAXIMIZE: average rating & cluster size
    MINIMIZE: dist to first stop & total distance between stops
    ------------------------------------------
    weights is a dictionary passed from the website which controls
    exponential weights for the above variables
    weights = {
    "p_size": "4",
    "p_rating": "2",
    "p_min_dist": "2",
    "p_internal_dist": "8"
    }
    """
    size = len(cluster)
    if size < 2:
        return 1e-10
    if weights is None:
        weights = {
            "p_size": "5",
            "p_rating": "2",
            "p_min_dist": "2",
            "p_internal_dist": "4",
        }
    p_size = scale_param(weights["p_size"])
    p_rating = scale_param(weights["p_rating"])
    p_min_dist = scale_param(weights["p_min_dist"])
    p_internal_dist = scale_param(weights["p_internal_dist"])

    rating_avg = cluster["rating"].mean()
    min_dist = cluster["dist_to_loc"].min()
    max_dist = cluster["dist_to_loc"].max()
    numerator = size ** p_size * rating_avg ** p_rating
    denominator = (min_dist ** p_min_dist
                   * (max_dist - min_dist) ** p_internal_dist)
    return 10 ** 5 * numerator / denominator


def choose_cluster(df, loc, weights, mode="walking", verbose=False):
    """Accepts a df from build_df() and chooses the optimal cluster to meander.
    loc is the starting location of the search, which should be a dictionary of
    the form: {'lat': 47.606269, 'lng': -122.334747}
    """
    scores = {}
    poss_clusters = {}
    for i in set(df["label"].unique()) - set("N"):
        current_cluster = df.loc[df["label"] == i, :].copy()
        current_cluster["dist_to_loc"] = df.apply(
            lambda row: haver_wrapper(row, loc), axis=1
        )
        poss_clusters[i] = current_cluster
        scores[i] = round(cluster_metric(current_cluster, loc, weights), 4)

    if len(poss_clusters) == 0:
        output = df.sort_values("rating", ascending=False)[:10]
    else:
        key_of_best = max(scores, key=lambda k: scores[k])
        output = poss_clusters[key_of_best]

    if verbose:
        display(scores)
        display(mapbox(df))
        for current_cluster in poss_clusters.values():
            display(current_cluster)
    if len(output) > 10:
        forced_split = cluster(output, min_size=3, allow_single_cluster=False)
        if verbose:
            print("More than 10 choices: Recursively Forcing Split")
            display(forced_split)
        return choose_cluster(
            forced_split, loc, weights, mode, verbose=verbose
        )
    return output


def all_things(
        query, topic, weights, mode="walking",
        n=40, verbose=False, output="flask"):
    """Take in starting location (loc) and search word (topic) to find results
    from google maps, cluster them, pick the best cluster, then return
    something, based on the output parameter:
    DEFAULT: output='flask' (return string of html)
    output='tab' -OR- output='browser' (open a new tab and display the map)
    output='both' (return the string of html and also open a new tab)
    """
    if type(query) is dict:
        loc = query
    else:
        loc = get_loc(query, current=False)
    n = int(n)
    if type(weights) is str:
        weights = ast.literal_eval(weights)
    df = build_df(loc, topic, n)
    best_cluster = choose_cluster(df, loc, weights, verbose=verbose)
    wlk = meander(best_cluster, loc, mode=mode, verbose=verbose)

    output = output.lower()
    flask_output = True
    new_tab = True
    if output == "flask":
        new_tab = False
    elif output == "browser" or output == "tab":
        flask_output = False

    return {
        "html": html_builder(loc, wlk, tab=new_tab, flask_output=flask_output),
        "best_cluster": best_cluster,
    }
