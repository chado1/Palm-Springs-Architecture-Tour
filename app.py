from flask import Flask, render_template, jsonify, request
import json
import os
from route_optimizer import optimize_route
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = app.logger

# Cache for storing locations data
_locations_cache = None

def load_locations():
    """Load locations from JSON file and cache them"""
    global _locations_cache
    if _locations_cache is None:
        try:
            with open('data/locations.json', 'r') as f:
                _locations_cache = json.load(f)
            logger.info(f"Loaded {len(_locations_cache)} locations from JSON")
        except Exception as e:
            logger.error(f"Error loading locations: {str(e)}")
            _locations_cache = []
    return _locations_cache

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/locations')
def get_locations():
    try:
        logger.info("Fetching locations and optimizing routes...")
        locations = load_locations()
        
        # Get max distance from query parameters (in kilometers)
        max_distance = float(request.args.get('maxDistance', 5))
        logger.info(f"Using max distance of {max_distance} km per route")
        
        # Optimize the routes with the specified max distance
        optimized = optimize_route(locations, max_distance=max_distance)
        
        logger.info(f"Routes optimized:")
        for i, route in enumerate(optimized['routes']):
            logger.info(f"Route {i+1}: {len(route['locations'])} stops, {route['distance']:.2f} km")
        logger.info(f"Total distance: {optimized['total_distance']:.2f} km")
        
        return jsonify(optimized)
        
    except Exception as e:
        logger.error(f"Error in get_locations: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
