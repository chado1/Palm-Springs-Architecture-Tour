from math import radians, sin, cos, sqrt, atan2
import requests
import polyline
import time
from functools import lru_cache
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Cache for route calculations
@lru_cache(maxsize=1000)
def get_cached_route(start_lat, start_lng, end_lat, end_lng):
    """Cached version of get_walking_route."""
    return get_walking_route((start_lat, start_lng), (end_lat, end_lng))

def get_walking_route(start_coord, end_coord):
    """Get walking route between two points using OSRM."""
    # Use straight-line distance for very close points (< 100m)
    direct_dist = calculate_distance(start_coord[0], start_coord[1], end_coord[0], end_coord[1])
    if direct_dist < 0.1:  # 100 meters
        return {
            'distance': direct_dist,
            'duration': direct_dist * 720,
            'geometry': None
        }

    base_url = "http://router.project-osrm.org/route/v1/foot"
    url = f"{base_url}/{start_coord[1]},{start_coord[0]};{end_coord[1]},{end_coord[0]}"
    params = {
        'overview': 'full',
        'geometries': 'polyline'
    }
    
    try:
        response = requests.get(url, params=params, timeout=2)
        data = response.json()
        
        if data.get('code') == 'Ok' and data.get('routes'):
            route = data['routes'][0]
            return {
                'distance': route['distance'] / 1000,
                'duration': route['duration'],
                'geometry': route['geometry']
            }
    except Exception as e:
        logger.error(f"Error getting route: {str(e)}")
    
    # Fallback to straight-line distance
    return {
        'distance': direct_dist,
        'duration': direct_dist * 720,
        'geometry': None
    }

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate the straight-line distance between two points."""
    R = 6371  # Earth's radius in kilometers
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def find_nearest_neighbor(current, unvisited, max_distance, total_distance=0):
    """Find the nearest unvisited location that keeps the route under max_distance."""
    if not unvisited:
        return None, 0
    
    min_cost = float('inf')
    best_next = None
    best_distance = 0
    
    # First try straight-line distance to filter candidates
    candidates = sorted(unvisited, 
                       key=lambda x: calculate_distance(current['lat'], current['lng'], 
                                                      x['lat'], x['lng']))[:5]
    
    for location in candidates:
        route = get_cached_route(current['lat'], current['lng'],
                               location['lat'], location['lng'])
        if not route:
            continue
        
        potential_distance = total_distance + route['distance']
        if len(unvisited) == 1:
            route_back = get_cached_route(location['lat'], location['lng'],
                                        candidates[0]['lat'], candidates[0]['lng'])
            if route_back:
                potential_distance += route_back['distance']
        
        if potential_distance > max_distance:
            continue
        
        if route['distance'] < min_cost:
            min_cost = route['distance']
            best_next = location
            best_distance = route['distance']
    
    return best_next, best_distance

def create_walking_loop(locations: List[Dict[str, Any]], max_distance: float) -> Dict:
    """Create a single optimized walking loop."""
    if not locations:
        return None
    
    route = [locations[0]]
    unvisited = locations[1:]
    total_distance = 0
    segments = []
    
    current = locations[0]
    while unvisited:
        next_location, distance = find_nearest_neighbor(current, unvisited, max_distance, total_distance)
        if not next_location:
            break
        
        route_info = get_cached_route(current['lat'], current['lng'],
                                    next_location['lat'], next_location['lng'])
        
        segments.append({
            'start': current,
            'end': next_location,
            'distance': route_info['distance'],
            'polyline': route_info['geometry']
        })
        
        route.append(next_location)
        unvisited.remove(next_location)
        total_distance += distance
        current = next_location
    
    # Add final segment back to start
    if len(route) > 1:
        route_info = get_cached_route(current['lat'], current['lng'],
                                    route[0]['lat'], route[0]['lng'])
        if route_info:
            segments.append({
                'start': current,
                'end': route[0],
                'distance': route_info['distance'],
                'polyline': route_info['geometry']
            })
            total_distance += route_info['distance']
    
    return {
        'locations': route,
        'segments': segments,
        'distance': total_distance
    }

def optimize_route(locations: List[Dict[str, Any]], max_distance: float = 4.8):  # Default 3 miles ≈ 4.8 km
    """Create multiple walking loops, each under the specified max distance."""
    if not locations:
        return {'routes': [], 'route_segments': [], 'total_distance': 0}
    
    remaining = locations.copy()
    routes = []
    all_segments = []
    total_distance = 0
    
    while remaining:
        # Sort remaining locations by proximity to city center
        center_lat = sum(loc['lat'] for loc in remaining) / len(remaining)
        center_lng = sum(loc['lng'] for loc in remaining) / len(remaining)
        
        # Only sort the first few locations to improve performance
        remaining.sort(key=lambda x: calculate_distance(
            x['lat'], x['lng'], center_lat, center_lng
        ))
        
        route = create_walking_loop(remaining[:10], max_distance)  # Only consider closest 10 locations
        if not route or not route['locations']:
            break
        
        route_index = len(routes)  # Get current route index
        routes.append({
            'locations': route['locations'],
            'distance': route['distance']
        })
        
        # Add route_index to each segment
        for segment in route['segments']:
            segment['route_index'] = route_index
        all_segments.extend(route['segments'])
        
        total_distance += route['distance']
        
        # Remove used locations
        for loc in route['locations']:
            if loc in remaining:
                remaining.remove(loc)
    
    return {
        'routes': routes,
        'route_segments': all_segments,
        'total_distance': total_distance
    }
