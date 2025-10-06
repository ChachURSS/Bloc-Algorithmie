"""
Dynamic Traffic Constraints for VRP
Handles time-dependent travel times and traffic conditions.
"""

import numpy as np
from typing import List, Dict, Tuple
from ..vrp_instance import VRPInstance
from ..solution import Solution


class DynamicTrafficConstraint:
    """
    Manages dynamic traffic constraints with time-dependent travel times.
    """
    
    def __init__(self, instance: VRPInstance, time_horizon: int = 24):
        self.instance = instance
        self.time_horizon = time_horizon  # Hours in a day
        self.time_slots = []  # List of time periods
        self.traffic_matrices = {}  # time_slot -> distance_matrix
        self.traffic_factors = {}  # time_slot -> traffic_factor
        
        self._initialize_traffic_patterns()
    
    def _initialize_traffic_patterns(self):
        """Initialize default traffic patterns."""
        # Define time slots (hourly)
        self.time_slots = list(range(self.time_horizon))
        
        # Define traffic factors based on typical urban patterns
        base_factors = {
            # Night hours (0-6): light traffic
            0: 0.8, 1: 0.8, 2: 0.8, 3: 0.8, 4: 0.8, 5: 0.9,
            # Morning rush (7-9): heavy traffic
            6: 1.0, 7: 1.4, 8: 1.6, 9: 1.3,
            # Mid-morning (10-11): moderate traffic
            10: 1.1, 11: 1.0,
            # Lunch time (12-13): moderate traffic
            12: 1.2, 13: 1.1,
            # Afternoon (14-16): light-moderate traffic
            14: 1.0, 15: 1.0, 16: 1.1,
            # Evening rush (17-19): heavy traffic
            17: 1.5, 18: 1.7, 19: 1.4,
            # Evening (20-23): decreasing traffic
            20: 1.2, 21: 1.0, 22: 0.9, 23: 0.8
        }
        
        self.traffic_factors = base_factors
        
        # Generate traffic matrices for each time slot
        if self.instance.distance_matrix is not None:
            for hour in self.time_slots:
                factor = self.traffic_factors.get(hour, 1.0)
                self.traffic_matrices[hour] = self.instance.distance_matrix * factor
    
    def get_travel_time(self, from_node: int, to_node: int, departure_time: float) -> float:
        """Get travel time considering traffic conditions."""
        # Determine time slot
        hour = int(departure_time) % self.time_horizon
        
        if hour in self.traffic_matrices:
            return self.traffic_matrices[hour][from_node][to_node]
        else:
            # Fallback to base distance
            return self.instance.get_distance(from_node, to_node)
    
    def calculate_route_time_with_traffic(self, route: List[int], start_time: float = 0) -> Dict:
        """Calculate detailed timing for a route considering traffic."""
        if len(route) < 2:
            return {'total_time': 0, 'arrival_times': [], 'travel_times': []}
        
        current_time = start_time
        arrival_times = [current_time]  # Start at depot
        travel_times = []
        
        for i in range(len(route) - 1):
            from_node = route[i]
            to_node = route[i + 1]
            
            # Get travel time considering current traffic
            travel_time = self.get_travel_time(from_node, to_node, current_time)
            travel_times.append(travel_time)
            
            # Update current time
            current_time += travel_time
            
            # Add service time if not depot
            if to_node != self.instance.depot:
                service_time = self.instance.service_times.get(to_node, 0)
                current_time += service_time
            
            arrival_times.append(current_time)
        
        return {
            'total_time': current_time - start_time,
            'arrival_times': arrival_times,
            'travel_times': travel_times,
            'final_time': current_time
        }
    
    def optimize_departure_times(self, solution: Solution) -> Dict[int, float]:
        """Optimize departure times for each route to minimize total time."""
        optimal_departures = {}
        
        for route_idx, route in enumerate(solution.routes):
            if len(route) <= 2:
                optimal_departures[route_idx] = 0
                continue
            
            best_time = float('inf')
            best_departure = 0
            
            # Try different departure times
            for departure_hour in range(0, self.time_horizon, 2):  # Every 2 hours
                route_info = self.calculate_route_time_with_traffic(route, departure_hour)
                
                if route_info['total_time'] < best_time:
                    best_time = route_info['total_time']
                    best_departure = departure_hour
            
            optimal_departures[route_idx] = best_departure
        
        return optimal_departures
    
    def calculate_traffic_cost(self, solution: Solution, departure_times: Dict[int, float] = None) -> float:
        """Calculate total cost considering dynamic traffic."""
        if departure_times is None:
            departure_times = {i: 0 for i in range(len(solution.routes))}
        
        total_cost = 0.0
        
        for route_idx, route in enumerate(solution.routes):
            start_time = departure_times.get(route_idx, 0)
            route_info = self.calculate_route_time_with_traffic(route, start_time)
            total_cost += route_info['total_time']
        
        return total_cost
    
    def get_traffic_report(self, hour: int) -> Dict:
        """Get traffic conditions report for a specific hour."""
        factor = self.traffic_factors.get(hour, 1.0)
        
        if factor < 0.9:
            condition = "Light Traffic"
        elif factor < 1.2:
            condition = "Normal Traffic"
        elif factor < 1.5:
            condition = "Heavy Traffic"
        else:
            condition = "Very Heavy Traffic"
        
        return {
            'hour': hour,
            'traffic_factor': factor,
            'condition': condition,
            'recommended': factor < 1.2
        }