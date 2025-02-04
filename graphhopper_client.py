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
        """Enhanced route optimization using k-means clustering and nearest neighbor."""
        if not max_distance:
            return [points]
            
        if len(points) <= 2:
            return [points]

        # Phase 1: K-means clustering
        num_clusters = max(1, min(len(points) // 5, int(max_distance / 1000)))  # Balance cluster size with max distance
        clusters = self._cluster_points(points, num_clusters)
        
        tours = []
        for cluster_points in clusters:
            if not cluster_points:  # Skip empty clusters
                continue
                
            # Phase 2: Optimize within cluster using nearest neighbor
            current_tour = []
            unvisited = list(range(len(cluster_points)))
            current_distance = 0
            
            # Start with point closest to cluster center
            center = self._calculate_cluster_center(cluster_points)
            current_idx = self._find_closest_to_point(cluster_points, center)
            
            while unvisited:
                current_tour.append(cluster_points[current_idx])
                unvisited.remove(current_idx)
                
                if not unvisited:
                    break
                    
                # Find next closest point considering max distance
                next_idx = self._find_best_next_point(
                    cluster_points, current_idx, unvisited,
                    current_tour[0], current_distance, max_distance
                )
                
                if next_idx is None:
                    # Close current tour and start a new one if needed
                    if current_tour[0] != current_tour[-1]:
                        current_tour.append(current_tour[0])
                    tours.append(current_tour)
                    
                    if unvisited:  # If there are still points in this cluster
                        current_tour = []
                        current_distance = 0
                        current_idx = unvisited[0]
                        continue
                    break
                
                # Calculate new distance
                extra_distance = self._calculate_distance(
                    cluster_points[current_idx][0], cluster_points[current_idx][1],
                    cluster_points[next_idx][0], cluster_points[next_idx][1]
                )
                current_distance += extra_distance
                current_idx = next_idx
            
            # Close the final tour in this cluster
            if current_tour and current_tour[0] != current_tour[-1]:
                current_tour.append(current_tour[0])
            if current_tour:
                tours.append(current_tour)
        
        # Phase 3: Try to optimize tours
        tours = self._optimize_tour_assignments(tours, max_distance)
        
        return tours

    def _cluster_points(self, points: List[Tuple[float, float]], k: int) -> List[List[Tuple[float, float]]]:
        """Cluster points using k-means algorithm."""
        if len(points) <= k:
            return [[p] for p in points]
            
        # Initialize centroids randomly from existing points
        import random
        centroids = random.sample(points, k)
        
        max_iterations = 100
        for _ in range(max_iterations):
            # Assign points to nearest centroid
            clusters = [[] for _ in range(k)]
            for point in points:
                distances = [self._calculate_distance(point[0], point[1], c[0], c[1]) for c in centroids]
                closest = distances.index(min(distances))
                clusters[closest].append(point)
            
            # Calculate new centroids
            new_centroids = []
            for cluster in clusters:
                if not cluster:  # Skip empty clusters
                    new_centroids.append(centroids[len(new_centroids)])
                    continue
                center = self._calculate_cluster_center(cluster)
                new_centroids.append(center)
            
            # Check for convergence
            if all(self._calculate_distance(old[0], old[1], new[0], new[1]) < 1.0 
                   for old, new in zip(centroids, new_centroids)):
                break
            
            centroids = new_centroids
        
        return [c for c in clusters if c]  # Return only non-empty clusters

    def _calculate_cluster_center(self, points: List[Tuple[float, float]]) -> Tuple[float, float]:
        """Calculate the center point of a cluster."""
        if not points:
            return (0.0, 0.0)
        return (
            sum(p[0] for p in points) / len(points),
            sum(p[1] for p in points) / len(points)
        )

    def _find_closest_to_point(self, points: List[Tuple[float, float]], target: Tuple[float, float]) -> int:
        """Find index of point closest to target."""
        if not points:
            return -1
        distances = [self._calculate_distance(p[0], p[1], target[0], target[1]) for p in points]
        return distances.index(min(distances))

    def _find_best_next_point(self, points: List[Tuple[float, float]], current_idx: int,
                            unvisited: List[int], start_point: Tuple[float, float],
                            current_distance: float, max_distance: float) -> int:
        """Find best next point that doesn't exceed max_distance."""
        min_extra_distance = float('inf')
        best_idx = None
        
        for idx in unvisited:
            # Calculate distance to next point
            extra_distance = self._calculate_distance(
                points[current_idx][0], points[current_idx][1],
                points[idx][0], points[idx][1]
            )
            
            # Calculate distance back to start
            dist_back = self._calculate_distance(
                points[idx][0], points[idx][1],
                start_point[0], start_point[1]
            )
            
            total_extra = extra_distance + dist_back
            
            # Check if this would exceed max_distance
            if current_distance + total_extra <= max_distance and total_extra < min_extra_distance:
                min_extra_distance = total_extra
                best_idx = idx
        
        return best_idx

    def _optimize_tour_assignments(self, tours: List[List[Tuple[float, float]]], max_distance: float) -> List[List[Tuple[float, float]]]:
        """Try to optimize tour assignments by moving points between tours."""
        improved = True
        while improved:
            improved = False
            
            # Try to move points between tours
            for i, tour1 in enumerate(tours):
                if len(tour1) <= 2:  # Skip tours that are too small
                    continue
                    
                for j, tour2 in enumerate(tours):
                    if i == j:
                        continue
                        
                    # Try moving each point from tour1 to tour2
                    for idx1 in range(len(tour1) - 1):  # Skip last point (it's the same as first)
                        point = tour1[idx1]
                        
                        # Calculate current distances
                        old_dist1 = sum(self._calculate_distance(
                            tour1[k][0], tour1[k][1],
                            tour1[k+1][0], tour1[k+1][1]
                        ) for k in range(len(tour1)-1))
                        
                        old_dist2 = sum(self._calculate_distance(
                            tour2[k][0], tour2[k][1],
                            tour2[k+1][0], tour2[k+1][1]
                        ) for k in range(len(tour2)-1))
                        
                        # Try inserting at each position in tour2
                        for insert_pos in range(len(tour2)):
                            new_tour1 = tour1[:idx1] + tour1[idx1+1:]
                            new_tour2 = tour2[:insert_pos] + [point] + tour2[insert_pos:]
                            
                            # Ensure tours are closed
                            if new_tour1[0] != new_tour1[-1]:
                                new_tour1.append(new_tour1[0])
                            if new_tour2[0] != new_tour2[-1]:
                                new_tour2.append(new_tour2[0])
                            
                            # Calculate new distances
                            new_dist1 = sum(self._calculate_distance(
                                new_tour1[k][0], new_tour1[k][1],
                                new_tour1[k+1][0], new_tour1[k+1][1]
                            ) for k in range(len(new_tour1)-1))
                            
                            new_dist2 = sum(self._calculate_distance(
                                new_tour2[k][0], new_tour2[k][1],
                                new_tour2[k+1][0], new_tour2[k+1][1]
                            ) for k in range(len(new_tour2)-1))
                            
                            # Check if this improves the solution and respects max_distance
                            if (new_dist1 <= max_distance and new_dist2 <= max_distance and
                                new_dist1 + new_dist2 < old_dist1 + old_dist2):
                                tours[i] = new_tour1
                                tours[j] = new_tour2
                                improved = True
                                break
                        
                        if improved:
                            break
                    
                    if improved:
                        break
                
                if improved:
                    break
        
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
