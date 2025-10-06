"""
Capacity Constraints for VRP
Handles vehicle capacity and load constraints.
"""

from typing import List, Dict
from ..vrp_instance import VRPInstance
from ..solution import Solution


class CapacityConstraint:
    """
    Manages capacity constraints for VRP vehicles.
    """
    
    def __init__(self, instance: VRPInstance):
        self.instance = instance
    
    def is_feasible(self, solution: Solution) -> bool:
        """Check if solution respects all capacity constraints."""
        violations = self.get_violations(solution)
        return len(violations) == 0
    
    def get_violations(self, solution: Solution) -> List[str]:
        """Get list of capacity violations."""
        violations = []
        
        for route_idx, route in enumerate(solution.routes):
            route_load = self._calculate_route_load(route)
            vehicle_capacity = self._get_vehicle_capacity(route_idx)
            
            if route_load > vehicle_capacity:
                violations.append(
                    f"Route {route_idx}: Load {route_load} exceeds capacity {vehicle_capacity}"
                )
        
        return violations
    
    def _calculate_route_load(self, route: List[int]) -> int:
        """Calculate total load for a route."""
        return sum(self.instance.demands.get(customer, 0) 
                  for customer in route if customer != self.instance.depot)
    
    def _get_vehicle_capacity(self, vehicle_idx: int) -> int:
        """Get capacity for a specific vehicle."""
        if vehicle_idx < len(self.instance.vehicle_capacities):
            return self.instance.vehicle_capacities[vehicle_idx]
        return self.instance.capacity
    
    def calculate_load_penalty(self, solution: Solution) -> float:
        """Calculate penalty for capacity violations."""
        total_penalty = 0.0
        
        for route_idx, route in enumerate(solution.routes):
            route_load = self._calculate_route_load(route)
            vehicle_capacity = self._get_vehicle_capacity(route_idx)
            
            if route_load > vehicle_capacity:
                overload = route_load - vehicle_capacity
                total_penalty += overload * 1000  # High penalty per unit overload
        
        return total_penalty