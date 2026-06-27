import requests
import time
from google.transit import gtfs_realtime_pb2

FEEDS = {
    'ace': 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace',
    'nqrw': 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw',
    'g': 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-g',
    '1234567': 'https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs',
}

# Stop IDs for each station and direction
# N = northbound (to Manhattan), S = southbound
STATIONS = {
    'queens_plaza': {
        'R': {'stop_id': 'G08N', 'label': 'Queens Plaza'},
        'E': {'stop_id': 'G08N', 'label': 'Queens Plaza'},
    },
    'court_square': {
        '7': {'stop_id': '723N', 'label': 'Court Sq-23 St'},
        'G': {'stop_id': 'G22S', 'label': 'Court Sq-23 St'},
    }
}

def fetch_feed(url):
    response = requests.get(url, timeout=10)
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)
    return feed

def get_arrivals(feed, stop_id, route_id):
    arrivals = []
    now = time.time()
    for entity in feed.entity:
        if not entity.HasField('trip_update'):
            continue
        trip = entity.trip_update
        if trip.trip.route_id != route_id:
            continue
        for stop in trip.stop_time_update:
            if stop.stop_id == stop_id:
                t = stop.arrival.time if stop.arrival.time else stop.departure.time
                minutes = round((t - now) / 60)
                if 0 <= minutes <= 30:
                    arrivals.append({
                        'route': route_id,
                        'minutes': minutes,
                        'destination': trip.trip.trip_id
                    })
    return sorted(arrivals, key=lambda x: x['minutes'])

def get_queens_plaza():
    ace_feed = fetch_feed(FEEDS['ace'])
    nqrw_feed = fetch_feed(FEEDS['nqrw'])
    e_trains = get_arrivals(ace_feed, 'G08N', 'E')
    r_trains = get_arrivals(nqrw_feed, 'G08N', 'R')
    return [
        e_trains[0] if e_trains else None,
        r_trains[0] if r_trains else None
    ]

def get_court_square():
    feed_7 = fetch_feed(FEEDS['1234567'])
    feed_g = fetch_feed(FEEDS['g'])
    trains_7 = get_arrivals(feed_7, '723N', '7')
    trains_g = get_arrivals(feed_g, 'G22S', 'G')
    return [
        trains_7[0] if trains_7 else None,
        trains_g[0] if trains_g else None
    ]

if __name__ == '__main__':
    print('Queens Plaza:')
    for t in get_queens_plaza():
        if t:
            print(f"  {t['route']} train — {t['minutes']} min")
        else:
            print('  No data')

    print('Court Square:')
    for t in get_court_square():
        if t:
            print(f"  {t['route']} train — {t['minutes']} min")
        else:
            print('  No data')
