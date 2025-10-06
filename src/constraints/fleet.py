"""
Fleet Constraints for VRP
Handles heterogeneous fleet and vehicle type constraints.
"""

from typing import List, Dict, Set
from ..vrp_instance import VRPInstance
from ..solution import Solution


class FleetConstraint:
    """
    Manages fleet constraints including vehicle types and compatibility.
    """
    
    def __init__(self, instance: VRPInstance):
        self.instance = instance
        self.vehicle_types: Dict[int, str] = {}  # vehicle_id -> type
        self.type_capacities: Dict[str, int] = {}  # type -> capacity
        self.compatibility_matrix: Dict[int, Set[str]] = {}  # customer -> allowed vehicle types
    
    def set_vehicle_type(self, vehicle_id: int, vehicle_type: str, capacity: int):
        """Set type and capacity for a vehicle."""
        self.vehicle_types[vehicle_id] = vehicle_type
        self.type_capacities[vehicle_type] = capacity
    
    def set_customer_compatibility(self, customer_id: int, allowed_types: Set[str]):
        """Set which vehicle types can serve a customer."""
        self.compatibility_matrix[customer_id] = allowed_types
    
    def is_feasible(self, solution: Solution) -> bool:
        """Check if solution respects all fleet constraints."""
        violations = self.get_violations(solution)
        return len(violations) == 0
    
    def get_violations(self, solution: Solution) -> List[str]:
        """Get list of fleet constraint violations."""
        violations = []
        
        # Check vehicle type constraints
        for route_idx, route in enumerate(solution.routes):
            vehicle_type = self.vehicle_types.get(route_idx)
            
            if vehicle_type is None:
                continue
            
            # Check compatibility for each customer
            for customer in route:
                if customer == self.instance.depot:
                    continue
                
                allowed_types = self.compatibility_matrix.get(customer)
                if allowed_types and vehicle_type not in allowed_types:
                    violations.append(
                        f"Route {route_idx}: Customer {customer} cannot be served by vehicle type {vehicle_type}"
                    )
            
            # Check capacity for vehicle type
            route_load = sum(self.instance.demands.get(customer, 0) 
                           for customer in route if customer != self.instance.depot)
            vehicle_capacity = self.type_capacities.get(vehicle_type, self.instance.capacity)
            
            if route_load > vehicle_capacity:
                violations.append(
                    f"Route {route_idx}: Load {route_load} exceeds {vehicle_type} capacity {vehicle_capacity}"
                )
        
        return violations
    
    def get_compatible_vehicles(self, customer: int) -> Set[int]:
        """Get list of vehicles that can serve a customer."""
        compatible_vehicles = set()
        allowed_types = self.compatibility_matrix.get(customer, set(self.type_capacities.keys()))
        
        for vehicle_id, vehicle_type in self.vehicle_types.items():
            if vehicle_type in allowed_types:
                compatible_vehicles.add(vehicle_id)
        
        return compatible_vehicles
    
    def calculate_fleet_cost(self, solution: Solution) -> float:
        """Calculate cost based on vehicle types used."""
        total_cost = 0.0
        
        # Fixed costs per vehicle type
        type_fixed_costs = {
            'small': 100,
            'medium': 150,
            'large': 200
        }
        
        used_vehicles = set()
        for route_idx, route in enumerate(solution.routes):
            if len(route) > 2:  # Route has customers (not just depot-depot)
                used_vehicles.add(route_idx)
        
        for vehicle_id in used_vehicles:
            vehicle_type = self.vehicle_types.get(vehicle_id, 'medium')
            total_cost += type_fixed_costs.get(vehicle_type, 150)
        
        return total_cost