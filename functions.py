import googlemaps

with open('.secret.key') as f:
    api_key = f.read().strip()

gmaps = googlemaps.Client(key=api_key)

def get_topic():
    """
    Let the user choose which topic to build a walk around.
    """
    return input('What theme walk would you like to explore today?')


def get_loc(current=True):
    """
    current = True: Attempt to determine the user location 
    current = False: Ask the user for a starting location.
    """
    if current is True:
        output = gmaps.geolocate()['location']
    else:
        query = input('Where would you like to start?')
        place_id = gmaps.find_place(query, input_type='textquery')['candidates'][0]['place_id']
        output = gmaps.place('ChIJydSuSkkUkFQRsqhB-cEtYnw')['result']['geometry']['location']
    return output


def walk(dest_list, verbose=False):
    """given a list of places to visit, return the walking dist & time"""

    if len(dest_list) > 10:
        return "There is a maximum of 10 stops per adventure."
    
    start, stop = dest_list[0], dest_list[-1]
    
    waypoints = None
    if len(dest_list) > 2:
        waypoints = dest_list[1:-1]
    
    directions_result = gmaps.directions(
        start, stop, mode="walking", waypoints=waypoints, optimize_waypoints=True
    )
    
    if verbose:
        dist = 0
        time = 0
        for leg in directions_result[0]['legs']:
            td = leg['distance']['value']
            tt = leg['duration']['value']
            print(f'+{td} m --and-- +{round(tt/60, 2)} min')
            dist += td
            time += tt
        print(f'total dist: {dist} m \nest time: {round(time / 60, 1)} min')
        
    return directions_result

