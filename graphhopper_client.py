import os
import requests
import polyline
import time
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from typing import List, Tuple, Dict, Any

logger = logging.getLogger(__name__)

class GraphhopperClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('GRAPHHOPPER_API_KEY')
        if not self.api_key:
            raise ValueError("Graphhopper API key is required. Set it in the constructor or GRAPHHOPPER_API_KEY environment variable.")
        
        self.base_url = "https://graphhopper.com/api/1"
        self.session = self._create_session()
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum time between requests in seconds
    
    def _create_session(self):
        session = requests.Session()
        retry_strategy = Retry(
            total=3,  # number of retries
            backoff_factor=1,  # wait 1, 2, 4 seconds between retries
            status_forcelist=[429, 500, 502, 503, 504]  # status codes to retry on
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session
    
    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits by waiting if needed."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            logger.debug(f"Rate limiting: waiting {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def get_route(self, points: List[Tuple[float, float]], return_to_start: bool = True) -> Dict[str, Any]:
        """Get a route through multiple points using Graphhopper API.
        
        Args:
            points: List of (latitude, longitude) tuples
            return_to_start: If True, add the first point at the end to create a loop
            
        Returns:
            dict: Route information including:
                - distance (meters)
                - duration (seconds)
                - geometry (encoded polyline)
                - instructions (list of navigation steps)
        """
        if not points:
            raise ValueError("At least one point is required")
        
        if len(points) < 2:
            raise ValueError("At least two points are required for a route")
            
        if return_to_start and points[0] != points[-1]:
            points = points + [points[0]]  # Add first point at the end
            
        endpoint = f"{self.base_url}/route"
        
        # Build parameters list properly
        params = []
        
        # Add points first
        for lat, lng in points:
            params.append(('point', f"{lat},{lng}"))
            
        # Add other parameters
        params.extend([
            ('vehicle', 'foot'),  # Use pedestrian/walking profile
            ('points_encoded', 'true'),
            ('instructions', 'true'),
            ('calc_points', 'true'),
            ('key', self.api_key)
        ])
        
        try:
            self._wait_for_rate_limit()
            
            # Make request with properly formatted parameters
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            if not data.get('paths'):
                raise ValueError("No route found")
                
            route = data['paths'][0]  # Get the first (and only) path
            return {
                'distance': route['distance'],  # meters
                'duration': route['time'] / 1000,  # convert to seconds
                'geometry': route['points'],  # encoded polyline
                'instructions': route.get('instructions', [])
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting route: {str(e)}")
            if hasattr(e.response, 'json'):
                try:
                    error_details = e.response.json()
                    logger.error(f"API error details: {error_details}")
                except:
                    pass
            raise

    def optimize_tour(self, points: List[Tuple[float, float]], max_distance: float = None) -> List[List[Tuple[float, float]]]:
        """Split points into optimal walking tours.
        
        Args:
            points: List of (latitude, longitude) tuples
            max_distance: Maximum distance per tour in meters (optional)
            
        Returns:
            List of tours, where each tour is a list of (latitude, longitude) tuples
        """
        if len(points) <= 2:
            return [points]
            
        # Use our enhanced route optimization
        return self._optimize_routes(points, max_distance)
            
    def _optimize_routes(self, points: List[Tuple[float, float]], max_distance: float = None) -> List[List[Tuple[float, float]]]:
        """Enhanced route optimization using nearest neighbor with route splitting."""
        if not max_distance:
            return [points]
            
        # Start with all points as unvisited
        unvisited = list(range(len(points)))
        tours = []
        
        while unvisited:
            # Start a new tour
            current_tour = []
            current_distance = 0
            current_point_idx = unvisited[0]  # Start with first unvisited point
            tour_points = set()
            
            while True:
                # Add current point to tour
                current_tour.append(points[current_point_idx])
                tour_points.add(current_point_idx)
                
                # Find nearest unvisited point that doesn't exceed max_distance
                min_extra_distance = float('inf')
                next_point_idx = None
                
                for idx in unvisited:
                    if idx in tour_points:
                        continue
                        
                    # Calculate additional distance if we add this point
                    extra_distance = self._calculate_distance(
                        points[current_point_idx][0], points[current_point_idx][1],
                        points[idx][0], points[idx][1]
                    )
                    
                    # Also consider distance back to start
                    dist_back = self._calculate_distance(
                        points[idx][0], points[idx][1],
                        current_tour[0][0], current_tour[0][1]
                    )
                    
                    total_extra = extra_distance + dist_back
                    
                    # Check if adding this point would exceed max_distance
                    if current_distance + total_extra <= max_distance and total_extra < min_extra_distance:
                        min_extra_distance = total_extra
                        next_point_idx = idx
                
                if next_point_idx is None:
                    break  # No more points can be added to this tour
                    
                # Update current point and distance
                current_distance += min_extra_distance
                current_point_idx = next_point_idx
            
            # Close the loop by returning to start
            if current_tour[0] != current_tour[-1]:
                current_tour.append(current_tour[0])
            
            # Add tour to list and remove visited points
            tours.append(current_tour)
            unvisited = [idx for idx in unvisited if idx not in tour_points]
            
            if len(tours) > 10:  # Safety check
                break
        
        # If we have leftover points, try to insert them into existing tours
        if unvisited:
            for idx in unvisited:
                point = points[idx]
                best_insertion = None
                min_extra_distance = float('inf')
                
                # Try to insert into each tour
                for tour_idx, tour in enumerate(tours):
                    # Calculate current tour distance
                    tour_distance = sum(
                        self._calculate_distance(
                            tour[i][0], tour[i][1],
                            tour[i+1][0], tour[i+1][1]
                        )
                        for i in range(len(tour)-1)
                    )
                    
                    # Try inserting at each position
                    for pos in range(len(tour)-1):
                        # Calculate extra distance if we insert here
                        extra_distance = (
                            self._calculate_distance(
                                tour[pos][0], tour[pos][1],
                                point[0], point[1]
                            ) +
                            self._calculate_distance(
                                point[0], point[1],
                                tour[pos+1][0], tour[pos+1][1]
                            ) -
                            self._calculate_distance(
                                tour[pos][0], tour[pos][1],
                                tour[pos+1][0], tour[pos+1][1]
                            )
                        )
                        
                        if tour_distance + extra_distance <= max_distance and extra_distance < min_extra_distance:
                            min_extra_distance = extra_distance
                            best_insertion = (tour_idx, pos+1)
                
                # Insert point into best position if found
                if best_insertion:
                    tour_idx, pos = best_insertion
                    tours[tour_idx].insert(pos, point)
                else:
                    # If we can't insert, create a new tour with just this point
                    tours.append([point, point])
        
        return tours

    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate the great circle distance between two points in meters."""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371000  # Earth's radius in meters
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c
        
        return distance
