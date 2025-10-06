"""
Time Window Constraints for VRP
Handles delivery time windows and service times.
"""

from typing import Dict, Tuple, List
from ..vrp_instance import VRPInstance
from ..solution import Solution


class TimeWindowConstraint:
    """
    Manages time window constraints for VRP.
    Supports hard and soft time windows with waiting times.
    """
    
    def __init__(self, instance: VRPInstance, allow_waiting: bool = True, 
                 max_waiting_time: float = 60.0):
        self.instance = instance
        self.allow_waiting = allow_waiting
        self.max_waiting_time = max_waiting_time
    
    def is_feasible(self, solution: Solution) -> bool:
        """Check if solution respects all time window constraints."""
        violations = self.get_violations(solution)
        return len(violations) == 0
    
    def get_violations(self, solution: Solution) -> List[str]:
        """Get list of time window violations."""
        violations = []
        
        for route_idx, route in enumerate(solution.routes):
            current_time = 0.0
            
            for i in range(len(route) - 1):
                from_node = route[i]
                to_node = route[i + 1]
                
                # Travel time
                travel_time = self.instance.get_distance(from_node, to_node)
                current_time += travel_time
                
                # Check time window for customer nodes
                if to_node != self.instance.depot and to_node in self.instance.time_windows:
                    early, late = self.instance.time_windows[to_node]
                    
                    if current_time > late:
                        # Late arrival - hard violation
                        violations.append(
                            f"Route {route_idx}: Late arrival at customer {to_node} "
                            f"(arrival: {current_time:.1f}, deadline: {late})"
                        )
                    elif current_time < early:
                        # Early arrival - check if waiting is allowed
                        waiting_time = early - current_time
                        if not self.allow_waiting:
                            violations.append(
                                f"Route {route_idx}: Early arrival at customer {to_node} "
                                f"(arrival: {current_time:.1f}, opens: {early})"
                            )
                        elif waiting_time > self.max_waiting_time:
                            violations.append(
                                f"Route {route_idx}: Excessive waiting at customer {to_node} "
                                f"(waiting: {waiting_time:.1f} > {self.max_waiting_time})"
                            )
                        else:
                            # Wait until time window opens
                            current_time = early
                    
                    # Add service time
                    service_time = self.instance.service_times.get(to_node, 0)
                    current_time += service_time
        
        return violations
    
    def calculate_time_cost(self, solution: Solution) -> float:
        """Calculate time-based cost including waiting times and violations."""
        total_cost = 0.0
        
        for route in solution.routes:
            route_cost = self._calculate_route_time_cost(route)
            total_cost += route_cost
        
        return total_cost
    
    def _calculate_route_time_cost(self, route: List[int]) -> float:
        """Calculate time cost for a single route."""
        if len(route) < 2:
            return 0.0
        
        current_time = 0.0
        time_cost = 0.0
        
        for i in range(len(route) - 1):
            from_node = route[i]
            to_node = route[i + 1]
            
            # Travel time
            travel_time = self.instance.get_distance(from_node, to_node)
            current_time += travel_time
            time_cost += travel_time
            
            # Handle time windows for customers
            if to_node != self.instance.depot and to_node in self.instance.time_windows:
                early, late = self.instance.time_windows[to_node]
                
                if current_time < early:
                    # Waiting time
                    waiting_time = early - current_time
                    if self.allow_waiting and waiting_time <= self.max_waiting_time:
                        current_time = early
                        time_cost += waiting_time * 0.5  # Reduced cost for waiting
                    else:
                        # Penalty for early arrival when waiting not allowed or excessive
                        time_cost += waiting_time * 2.0
                
                elif current_time > late:
                    # Penalty for late arrival
                    lateness = current_time - late
                    time_cost += lateness * 10.0  # High penalty for lateness
                
                # Service time
                service_time = self.instance.service_times.get(to_node, 0)
                current_time += service_time
                time_cost += service_time
        
        return time_cost
    
    def get_route_time_info(self, route: List[int]) -> Dict:
        """Get detailed timing information for a route."""
        if len(route) < 2:
            return {'total_time': 0, 'waiting_time': 0, 'service_time': 0, 'violations': []}
        
        current_time = 0.0
        total_waiting = 0.0
        total_service = 0.0
        violations = []
        schedule = []
        
        for i in range(len(route) - 1):
            from_node = route[i]
            to_node = route[i + 1]
            
            # Travel time
            travel_time = self.instance.get_distance(from_node, to_node)
            arrival_time = current_time + travel_time
            
            node_info = {
                'node': to_node,
                'arrival_time': arrival_time,
                'waiting_time': 0,
                'service_start': arrival_time,
                'service_time': 0,
                'departure_time': arrival_time
            }
            
            if to_node != self.instance.depot and to_node in self.instance.time_windows:
                early, late = self.instance.time_windows[to_node]
                
                if arrival_time < early:
                    # Waiting required
                    waiting_time = early - arrival_time
                    node_info['waiting_time'] = waiting_time
                    node_info['service_start'] = early
                    total_waiting += waiting_time
                    
                    if not self.allow_waiting:
                        violations.append(f"Early arrival at {to_node}")
                    elif waiting_time > self.max_waiting_time:
                        violations.append(f"Excessive waiting at {to_node}")
                
                elif arrival_time > late:
                    # Late arrival
                    violations.append(f"Late arrival at {to_node}")
                    node_info['service_start'] = arrival_time
                
                # Service time
                service_time = self.instance.service_times.get(to_node, 0)
                node_info['service_time'] = service_time
                node_info['departure_time'] = node_info['service_start'] + service_time
                total_service += service_time
                
                current_time = node_info['departure_time']
            else:
                current_time = arrival_time
            
            schedule.append(node_info)
        
        return {
            'total_time': current_time,
            'waiting_time': total_waiting,
            'service_time': total_service,
            'violations': violations,
            'schedule': schedule
        }