"""
Construction Heuristics for VRP
Implements greedy and savings algorithms for initial solution construction.
"""

import random
from typing import List, Tuple, Dict
from ..vrp_instance import VRPInstance
from ..solution import Solution


class GreedyConstruction:
    """
    Greedy construction heuristic for VRP.
    Builds routes by always selecting the nearest unvisited customer.
    """
    
    def __init__(self, instance: VRPInstance):
        self.instance = instance
    
    def construct(self) -> Solution:
        """Construct a solution using nearest neighbor heuristic."""
        solution = Solution(self.instance)
        unvisited = set(self.instance.demands.keys()) - {self.instance.depot}
        
        vehicle_id = 0
        while unvisited and vehicle_id < self.instance.vehicle_count:
            route = self._build_route(unvisited, vehicle_id)
            if route:
                solution.add_route(route)
                # Remove visited customers
                for customer in route:
                    if customer in unvisited:
                        unvisited.remove(customer)
            vehicle_id += 1
        
        # Handle remaining customers with additional vehicles if needed
        while unvisited:
            route = self._build_route(unvisited, len(solution.routes))
            if route:
                solution.add_route(route)
                for customer in route:
                    if customer in unvisited:
                        unvisited.remove(customer)
            else:
                # Force assignment of remaining customers
                remaining = list(unvisited)
                solution.add_route([self.instance.depot] + remaining[:1] + [self.instance.depot])
                unvisited.remove(remaining[0])
        
        solution.calculate_cost()
        return solution
    
    def _build_route(self, unvisited: set, vehicle_id: int) -> List[int]:
        """Build a single route for a vehicle."""
        route = [self.instance.depot]
        current_node = self.instance.depot
        current_load = 0
        current_time = 0.0
        
        # Get vehicle capacity
        vehicle_capacity = (self.instance.vehicle_capacities[vehicle_id] 
                          if vehicle_id < len(self.instance.vehicle_capacities) 
                          else self.instance.capacity)
        
        while unvisited:
            # Find nearest feasible customer
            best_customer = None
            best_distance = float('inf')
            
            for customer in unvisited:
                # Check capacity constraint
                demand = self.instance.demands.get(customer, 0)
                if current_load + demand > vehicle_capacity:
                    continue
                
                # Check time window constraint
                travel_time = self.instance.get_distance(current_node, customer)
                arrival_time = current_time + travel_time
                
                if not self.instance.is_feasible_time_window(customer, arrival_time):
                    # Check if we can wait
                    waiting_time = self.instance.get_waiting_time(customer, arrival_time)
                    if waiting_time > 100:  # Arbitrary limit for waiting
                        continue
                
                # Calculate distance
                distance = self.instance.get_distance(current_node, customer)
                if distance < best_distance:
                    best_distance = distance
                    best_customer = customer
            
            if best_customer is None:
                break  # No feasible customer found
            
            # Add customer to route
            route.append(best_customer)
            current_node = best_customer
            current_load += self.instance.demands.get(best_customer, 0)
            
            # Update time
            travel_time = self.instance.get_distance(route[-2], best_customer)
            current_time += travel_time
            current_time += self.instance.get_waiting_time(best_customer, current_time)
            current_time += self.instance.service_times.get(best_customer, 0)
            
            unvisited.remove(best_customer)
        
        # Return to depot
        if len(route) > 1:
            route.append(self.instance.depot)
        
        return route if len(route) > 2 else []


class SavingsAlgorithm:
    """
    Savings algorithm (Clarke-Wright) for VRP.
    Builds routes by merging customer pairs with highest savings.
    """
    
    def __init__(self, instance: VRPInstance):
        self.instance = instance
    
    def construct(self) -> Solution:
        """Construct solution using Clarke-Wright savings algorithm."""
        # Calculate savings for all customer pairs
        savings = self._calculate_savings()
        
        # Sort savings in descending order
        sorted_savings = sorted(savings.items(), key=lambda x: x[1], reverse=True)
        
        # Initialize routes (each customer in separate route)
        customers = list(self.instance.demands.keys())
        customers.remove(self.instance.depot)
        
        routes = {}  # customer -> route_id
        route_lists = {}  # route_id -> list of customers
        
        for i, customer in enumerate(customers):
            routes[customer] = i
            route_lists[i] = [customer]
        
        # Merge routes based on savings
        for (i, j), saving in sorted_savings:
            if saving <= 0:
                break
            
            route_i = routes[i]
            route_j = routes[j]
            
            # Skip if customers are already in the same route
            if route_i == route_j:
                continue
            
            # Check if merge is feasible
            if self._can_merge_routes(route_lists[route_i], route_lists[route_j], i, j):
                # Merge routes
                new_route = self._merge_routes(route_lists[route_i], route_lists[route_j], i, j)
                
                # Update data structures
                route_lists[route_i] = new_route
                for customer in route_lists[route_j]:
                    routes[customer] = route_i
                del route_lists[route_j]
        
        # Convert to solution format
        solution = Solution(self.instance)
        for route_customers in route_lists.values():
            if route_customers:
                route = [self.instance.depot] + route_customers + [self.instance.depot]
                solution.add_route(route)
        
        solution.calculate_cost()
        return solution
    
    def _calculate_savings(self) -> Dict[Tuple[int, int], float]:
        """Calculate savings for all customer pairs."""
        savings = {}
        customers = list(self.instance.demands.keys())
        customers.remove(self.instance.depot)
        
        depot = self.instance.depot
        
        for i in range(len(customers)):
            for j in range(i + 1, len(customers)):
                customer_i = customers[i]
                customer_j = customers[j]
                
                # Savings = distance(depot, i) + distance(depot, j) - distance(i, j)
                dist_depot_i = self.instance.get_distance(depot, customer_i)
                dist_depot_j = self.instance.get_distance(depot, customer_j)
                dist_i_j = self.instance.get_distance(customer_i, customer_j)
                
                saving = dist_depot_i + dist_depot_j - dist_i_j
                savings[(customer_i, customer_j)] = saving
        
        return savings
    
    def _can_merge_routes(self, route1: List[int], route2: List[int], 
                         customer_i: int, customer_j: int) -> bool:
        """Check if two routes can be merged."""
        # Check capacity constraint
        load1 = sum(self.instance.demands.get(c, 0) for c in route1)
        load2 = sum(self.instance.demands.get(c, 0) for c in route2)
        
        if load1 + load2 > self.instance.capacity:
            return False
        
        # Check if customers are at the ends of their routes
        if (customer_i != route1[0] and customer_i != route1[-1]) or \
           (customer_j != route2[0] and customer_j != route2[-1]):
            return False
        
        # Additional time window checks could be added here
        
        return True
    
    def _merge_routes(self, route1: List[int], route2: List[int], 
                     customer_i: int, customer_j: int) -> List[int]:
        """Merge two routes through customers i and j."""
        # Determine the correct order for merging
        if customer_i == route1[0] and customer_j == route2[0]:
            # Reverse route1 and concatenate
            return route1[::-1] + route2
        elif customer_i == route1[0] and customer_j == route2[-1]:
            # Reverse route1 and append to route2
            return route2 + route1[::-1]
        elif customer_i == route1[-1] and customer_j == route2[0]:
            # Direct concatenation
            return route1 + route2
        elif customer_i == route1[-1] and customer_j == route2[-1]:
            # Reverse route2 and append to route1
            return route1 + route2[::-1]
        else:
            # Fallback - simple concatenation
            return route1 + route2