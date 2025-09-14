from flask import Flask, jsonify, render_template, request
import numpy as np
from utils import load_data_in_chunks, calculate_trip_metrics, process_trip_details, get_speed_distribution, detect_sharp_declines, detect_unusual_routes
import json 
import os


app = Flask(__name__,
    template_folder=os.path.abspath('frontend/templates'),
    static_folder=os.path.abspath('frontend/static'))

DATA_FILE = 'data/geo_locations_astana_hackathon'
CHUNK_SIZE = 10000


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/safety-metrics')
def get_safety_metrics():
    total_metrics = {
        'avg_speed': 0,
        'max_speed': 0,
        'high_speed_points': 0,
        'sharp_turns': 0,
        'total_trips': 0,
        'unusual_routes': 0,
        'sharp_declines': 0,
        'speed_distribution': None
    }
    chunk_count = 0
    for chunk in load_data_in_chunks(DATA_FILE, CHUNK_SIZE):
        metrics = calculate_trip_metrics(chunk)
        total_metrics['unusual_routes'] += detect_unusual_routes(chunk)
        total_metrics['sharp_declines'] += detect_sharp_declines(chunk)
        if chunk_count == 0:
            total_metrics['speed_distribution'] = get_speed_distribution(chunk)
        for key in ['avg_speed', 'high_speed_points']:
            total_metrics[key] = ((total_metrics[key] * chunk_count) + metrics[key]) / (chunk_count + 1)
        for key in ['max_speed', 'sharp_turns', 'total_trips']:
            total_metrics[key] += metrics[key]
        chunk_count += 1
    return jsonify(total_metrics)


@app.route('/api/trip-details')
def get_trip_details():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    first_chunk = next(load_data_in_chunks(DATA_FILE, CHUNK_SIZE))
    trip_details = process_trip_details(first_chunk)
    total = len(trip_details)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = trip_details[start:end]
    return jsonify({
        'trips': paginated,
        'total': total,
        'page': page,
        'per_page': per_page
    })


@app.route('/api/popular-routes')
def get_popular_routes():
    first_chunk = next(load_data_in_chunks(DATA_FILE, CHUNK_SIZE))
    routes = []
    lengths = []
    for trip_id in first_chunk['randomized_id'].unique():
        trip = first_chunk[first_chunk['randomized_id'] == trip_id]
        if len(trip) > 1:
            start = trip.iloc[0][['lat', 'lng']]
            end = trip.iloc[-1][['lat', 'lng']]
            routes.append({'start': (round(start['lat'], 4), round(start['lng'], 4)),
                           'end': (round(end['lat'], 4), round(end['lng'], 4))})
            # Calculate trip length
            lengths.append(float(np.sqrt((end['lat']-start['lat'])**2 + (end['lng']-start['lng'])**2)*111))
    from collections import Counter
    starts = [r['start'] for r in routes]
    ends = [r['end'] for r in routes]
    pairs = [(r['start'], r['end']) for r in routes]
    start_counts = Counter(starts).most_common(5)
    end_counts = Counter(ends).most_common(5)
    pair_counts = Counter(pairs).most_common(5)
    # Trip length histogram
    bins = [0, 1, 2, 5, 10, 20]
    hist, edges = np.histogram(lengths, bins=bins)
    return jsonify({
        'popular_starts': start_counts,
        'popular_ends': end_counts,
        'popular_pairs': pair_counts,
        'total_routes': len(routes),
        'length_histogram': {'bins': bins, 'counts': hist.tolist()}
    })


if __name__ == '__main__':
    app.run(debug=True)