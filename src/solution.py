"""
Solution representation for VRP
Handles routes, costs, and solution validation.
"""

from typing import List, Dict, Tuple, Optional
import copy


class Solution:
    """
    Represents a solution to a Vehicle Routing Problem.
    """
    
    def __init__(self, instance=None):
        self.instance = instance
        self.routes: List[List[int]] = []  # List of routes, each route is a list of customer IDs
        self.total_cost: float = 0.0
        self.total_distance: float = 0.0
        self.total_time: float = 0.0
        self.feasible: bool = True
        self.violations: List[str] = []
        
        # Additional metrics
        self.vehicle_loads: List[int] = []
        self.route_distances: List[float] = []
        self.route_times: List[float] = []
        
    def add_route(self, route: List[int]):
        """Add a route to the solution."""
        if route and route[0] != self.instance.depot:
            route = [self.instance.depot] + route
        if route and route[-1] != self.instance.depot:
            route = route + [self.instance.depot]
        
        self.routes.append(route)
        
    def calculate_cost(self) -> float:
        """Calculate total cost of the solution."""
        if not self.instance:
            return 0.0
        
        total_cost = 0.0
        total_distance = 0.0
        total_time = 0.0
        self.route_distances = []
        self.route_times = []
        self.vehicle_loads = []
        
        for route in self.routes:
            route_cost, route_distance, route_time, route_load = self._calculate_route_metrics(route)
            total_cost += route_cost
            total_distance += route_distance
            total_time += route_time
            
            self.route_distances.append(route_distance)
            self.route_times.append(route_time)
            self.vehicle_loads.append(route_load)
        
        self.total_cost = total_cost
        self.total_distance = total_distance
        self.total_time = total_time
        
        return total_cost
    
    def _calculate_route_metrics(self, route: List[int]) -> Tuple[float, float, float, int]:
        """Calculate metrics for a single route."""
        if len(route) < 2:
            return 0.0, 0.0, 0.0, 0
        
        distance = 0.0
        time = 0.0
        load = 0
        current_time = 0.0
        
        for i in range(len(route) - 1):
            from_node = route[i]
            to_node = route[i + 1]
            
            # Calculate travel distance and time
            travel_distance = self.instance.get_distance(from_node, to_node)
            travel_time = travel_distance  # Assuming unit speed
            
            distance += travel_distance
            current_time += travel_time
            
            # Add service time and waiting time for customers
            if to_node != self.instance.depot:
                # Check time window constraints
                waiting_time = self.instance.get_waiting_time(to_node, current_time)
                current_time += waiting_time
                
                # Add service time
                service_time = self.instance.service_times.get(to_node, 0)
                current_time += service_time
                
                # Add demand to load
                load += self.instance.demands.get(to_node, 0)
        
        time = current_time
        cost = distance  # For basic VRP, cost equals distance
        
        return cost, distance, time, load
    
    def is_feasible(self) -> bool:
        """Check if solution is feasible under all constraints."""
        self.violations = []
        feasible = True
        
        # Check capacity constraints
        for i, route in enumerate(self.routes):
            route_load = sum(self.instance.demands.get(customer, 0) 
                           for customer in route if customer != self.instance.depot)
            
            vehicle_capacity = (self.instance.vehicle_capacities[i] 
                              if i < len(self.instance.vehicle_capacities) 
                              else self.instance.capacity)
            
            if route_load > vehicle_capacity:
                self.violations.append(f"Route {i}: Load {route_load} exceeds capacity {vehicle_capacity}")
                feasible = False
        
        # Check time window constraints
        for i, route in enumerate(self.routes):
            current_time = 0.0
            for j in range(len(route) - 1):
                from_node = route[j]
                to_node = route[j + 1]
                
                # Travel time
                travel_time = self.instance.get_distance(from_node, to_node)
                current_time += travel_time
                
                # Check time window for customer nodes
                if to_node != self.instance.depot:
                    if not self.instance.is_feasible_time_window(to_node, current_time):
                        self.violations.append(f"Route {i}: Time window violation at customer {to_node}")
                        feasible = False
                    
                    # Add waiting time and service time
                    current_time += self.instance.get_waiting_time(to_node, current_time)
                    current_time += self.instance.service_times.get(to_node, 0)
        
        # Check if all customers are served exactly once
        served_customers = set()
        for route in self.routes:
            for customer in route:
                if customer != self.instance.depot:
                    if customer in served_customers:
                        self.violations.append(f"Customer {customer} served multiple times")
                        feasible = False
                    served_customers.add(customer)
        
        all_customers = set(self.instance.demands.keys()) - {self.instance.depot}
        unserved = all_customers - served_customers
        if unserved:
            self.violations.append(f"Unserved customers: {unserved}")
            feasible = False
        
        self.feasible = feasible
        return feasible
    
    def copy(self) -> 'Solution':
        """Create a deep copy of the solution."""
        new_solution = Solution(self.instance)
        new_solution.routes = copy.deepcopy(self.routes)
        new_solution.total_cost = self.total_cost
        new_solution.total_distance = self.total_distance
        new_solution.total_time = self.total_time
        new_solution.feasible = self.feasible
        new_solution.violations = self.violations.copy()
        new_solution.vehicle_loads = self.vehicle_loads.copy()
        new_solution.route_distances = self.route_distances.copy()
        new_solution.route_times = self.route_times.copy()
        return new_solution
    
    def get_customer_route(self, customer: int) -> Optional[int]:
        """Get the route index that serves a given customer."""
        for i, route in enumerate(self.routes):
            if customer in route:
                return i
        return None
    
    def remove_customer(self, customer: int) -> bool:
        """Remove a customer from the solution."""
        route_idx = self.get_customer_route(customer)
        if route_idx is not None:
            self.routes[route_idx].remove(customer)
            return True
        return False
    
    def insert_customer(self, customer: int, route_idx: int, position: int):
        """Insert a customer at a specific position in a route."""
        if route_idx < len(self.routes):
            # Ensure position is valid (not at depot positions)
            if position == 0:
                position = 1
            elif position >= len(self.routes[route_idx]):
                position = len(self.routes[route_idx]) - 1
            
            self.routes[route_idx].insert(position, customer)
    
    def to_dict(self) -> Dict:
        """Convert solution to dictionary for serialization."""
        return {
            'routes': self.routes,
            'total_cost': self.total_cost,
            'total_distance': self.total_distance,
            'total_time': self.total_time,
            'feasible': self.feasible,
            'violations': self.violations,
            'vehicle_loads': self.vehicle_loads,
            'route_distances': self.route_distances,
            'route_times': self.route_times
        }
    
    def __str__(self) -> str:
        """String representation of the solution."""
        result = f"VRP Solution: {len(self.routes)} routes\n"
        result += f"Total Cost: {self.total_cost:.2f}\n"
        result += f"Total Distance: {self.total_distance:.2f}\n"
        result += f"Feasible: {self.feasible}\n"
        
        for i, route in enumerate(self.routes):
            customers = [str(c) for c in route]
            result += f"Route {i}: {' -> '.join(customers)}\n"
        
        if self.violations:
            result += f"Violations: {', '.join(self.violations)}\n"
        
        return result