from math import radians, sin, cos, sqrt, atan2
import requests
import polyline
import time
from functools import lru_cache
import logging
from typing import List, Dict, Any, Tuple
from graphhopper_client import GraphhopperClient

logger = logging.getLogger(__name__)

# Initialize Graphhopper client
graphhopper = GraphhopperClient()

def create_walking_loop(locations: List[Dict[str, Any]], max_distance: float = 4.8) -> Dict[str, Any]:
    """Create a single optimized walking loop.
    
    Args:
        locations: List of location dictionaries with lat/lng
        max_distance: Maximum distance in kilometers
        
    Returns:
        dict: Information about the route including points and total distance
    """
    if not locations:
        return {
            'locations': [],
            'total_distance': 0,
            'duration': 0,
            'geometry': None
        }
    
    # Extract coordinates
    points = [(loc['lat'], loc['lng']) for loc in locations]
    
    try:
        # Get route through all points
        route = graphhopper.get_route(points, return_to_start=True)
        
        return {
            'locations': locations,
            'total_distance': route['distance'] / 1000,  # Convert to km
            'duration': route['duration'],
            'geometry': route['geometry'],
            'instructions': route.get('instructions', [])
        }
    except Exception as e:
        logger.error(f"Error creating walking loop: {e}")
        return None

def optimize_route(locations: List[Dict[str, Any]], max_distance: float = 4.8) -> List[Dict[str, Any]]:
    """Create multiple walking loops, each under the specified max distance.
    
    Args:
        locations: List of location dictionaries with lat/lng
        max_distance: Maximum distance in kilometers for each loop
        
    Returns:
        list: List of route dictionaries, each containing points and total distance
    """
    if not locations:
        return []
    
    # Extract coordinates
    points = [(loc['lat'], loc['lng']) for loc in locations]
    
    try:
        # Convert max_distance from km to meters for the API
        max_distance_meters = max_distance * 1000
        
        # Get optimized tours
        tours = graphhopper.optimize_tour(points, max_distance_meters)
        
        routes = []
        for tour_points in tours:
            if len(tour_points) <= 1:  # Skip empty or single-point tours
                continue
                
            # Get the locations that correspond to these points
            tour_locations = []
            for point in tour_points[:-1]:  # Exclude the last point as it's the same as first
                for loc in locations:
                    if abs(loc['lat'] - point[0]) < 1e-6 and abs(loc['lng'] - point[1]) < 1e-6:
                        tour_locations.append(loc)
                        break
            
            if not tour_locations:  # Skip if no locations found
                continue
                
            # Get the detailed route for this tour
            route = create_walking_loop(tour_locations, max_distance)
            if route:
                # Check if route is within max distance (with 5% margin)
                if route['total_distance'] <= max_distance * 1.05:
                    routes.append(route)
                else:
                    # If route is too long, try to create a new route with fewer points
                    for i in range(len(tour_locations) - 1, 1, -1):
                        shorter_route = create_walking_loop(tour_locations[:i], max_distance)
                        if shorter_route and shorter_route['total_distance'] <= max_distance:
                            routes.append(shorter_route)
                            # Try to create another route with remaining points
                            remaining_route = create_walking_loop(tour_locations[i:], max_distance)
                            if remaining_route and remaining_route['total_distance'] <= max_distance:
                                routes.append(remaining_route)
                            break
        
        # If no valid routes were created, fall back to simple distance-based splitting
        if not routes:
            return _simple_distance_split(locations, max_distance)
            
        return routes
        
    except Exception as e:
        logger.error(f"Error optimizing routes: {e}")
        return _simple_distance_split(locations, max_distance)

def _simple_distance_split(locations: List[Dict[str, Any]], max_distance: float) -> List[Dict[str, Any]]:
    """Simple distance-based splitting fallback."""
    if not locations:
        return []
        
    routes = []
    remaining = list(locations)
    
    while remaining:
        # Start a new route with the first location
        current_locations = [remaining[0]]
        current_route = create_walking_loop(current_locations, max_distance)
        
        # Try adding more locations while staying under max_distance
        for loc in remaining[1:]:
            test_locations = current_locations + [loc]
            test_route = create_walking_loop(test_locations, max_distance)
            
            if test_route and test_route['total_distance'] <= max_distance:
                current_locations = test_locations
                current_route = test_route
            else:
                break
                
        # Add the route and remove used locations
        if current_route:
            routes.append(current_route)
            remaining = [loc for loc in remaining if loc not in current_locations]
        else:
            break
            
    return routes
