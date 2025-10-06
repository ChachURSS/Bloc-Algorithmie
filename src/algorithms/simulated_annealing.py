"""
Simulated Annealing Algorithm for VRP
Implements simulated annealing metaheuristic with various neighborhood operations.
"""

import random
import math
import time
from typing import List, Tuple, Dict, Any
from ..vrp_instance import VRPInstance
from ..solution import Solution


class SimulatedAnnealing:
    """
    Simulated Annealing algorithm for Vehicle Routing Problem.
    """
    
    def __init__(self, instance: VRPInstance, 
                 initial_temp: float = 1000.0,
                 final_temp: float = 1.0,
                 cooling_rate: float = 0.95,
                 max_iterations: int = 10000,
                 max_iterations_per_temp: int = 100):
        self.instance = instance
        self.initial_temp = initial_temp
        self.final_temp = final_temp
        self.cooling_rate = cooling_rate
        self.max_iterations = max_iterations
        self.max_iterations_per_temp = max_iterations_per_temp
        
        # Statistics
        self.stats = {
            'iterations': 0,
            'accepted_moves': 0,
            'improving_moves': 0,
            'temperature_reductions': 0,
            'best_cost_history': [],
            'current_cost_history': []
        }
    
    def solve(self, initial_solution: Solution) -> Solution:
        """
        Solve VRP using Simulated Annealing.
        
        Args:
            initial_solution: Starting solution
            
        Returns:
            Best solution found
        """
        current_solution = initial_solution.copy()
        current_solution.calculate_cost()
        
        best_solution = current_solution.copy()
        
        temperature = self.initial_temp
        iteration = 0
        
        start_time = time.time()
        
        while temperature > self.final_temp and iteration < self.max_iterations:
            # Inner loop for current temperature
            for _ in range(self.max_iterations_per_temp):
                # Generate neighbor solution
                neighbor = self._generate_neighbor(current_solution)
                neighbor.calculate_cost()
                
                # Calculate acceptance probability
                delta = neighbor.total_cost - current_solution.total_cost
                
                if delta < 0 or random.random() < math.exp(-delta / temperature):
                    # Accept the move
                    current_solution = neighbor
                    self.stats['accepted_moves'] += 1
                    
                    if delta < 0:
                        self.stats['improving_moves'] += 1
                        
                        # Update best solution
                        if neighbor.total_cost < best_solution.total_cost:
                            best_solution = neighbor.copy()
                
                # Record statistics
                self.stats['current_cost_history'].append(current_solution.total_cost)
                self.stats['best_cost_history'].append(best_solution.total_cost)
                
                iteration += 1
                
                if iteration >= self.max_iterations:
                    break
            
            # Cool down
            temperature *= self.cooling_rate
            self.stats['temperature_reductions'] += 1
        
        self.stats['iterations'] = iteration
        self.stats['solve_time'] = time.time() - start_time
        self.stats['final_temperature'] = temperature
        
        return best_solution
    
    def _generate_neighbor(self, solution: Solution) -> Solution:
        """Generate a neighbor solution using local search operators."""
        neighbor = solution.copy()
        
        # Choose a random neighborhood operator
        operators = ['swap', 'relocate', 'two_opt', 'cross_exchange']
        weights = [0.3, 0.3, 0.2, 0.2]  # Operator selection probabilities
        
        operator = random.choices(operators, weights=weights)[0]
        
        if operator == 'swap':
            self._swap_customers(neighbor)
        elif operator == 'relocate':
            self._relocate_customer(neighbor)
        elif operator == 'two_opt':
            self._two_opt(neighbor)
        elif operator == 'cross_exchange':
            self._cross_exchange(neighbor)
        
        return neighbor
    
    def _swap_customers(self, solution: Solution):
        """Swap two customers in the solution."""
        if len(solution.routes) < 1:
            return
        
        # Get all customers (excluding depot)
        all_customers = []
        for route_idx, route in enumerate(solution.routes):
            for pos, customer in enumerate(route):
                if customer != self.instance.depot:
                    all_customers.append((route_idx, pos, customer))
        
        if len(all_customers) < 2:
            return
        
        # Select two random customers
        customer1, customer2 = random.sample(all_customers, 2)
        route1_idx, pos1, cust1 = customer1
        route2_idx, pos2, cust2 = customer2
        
        # Perform swap
        solution.routes[route1_idx][pos1] = cust2
        solution.routes[route2_idx][pos2] = cust1
    
    def _relocate_customer(self, solution: Solution):
        """Relocate a customer to a different position."""
        if len(solution.routes) < 1:
            return
        
        # Select source customer
        source_route_idx = random.randint(0, len(solution.routes) - 1)
        source_route = solution.routes[source_route_idx]
        
        # Find customers in source route (excluding depot)
        customer_positions = [i for i, c in enumerate(source_route) 
                            if c != self.instance.depot]
        
        if not customer_positions:
            return
        
        source_pos = random.choice(customer_positions)
        customer = source_route[source_pos]
        
        # Remove customer from source route
        solution.routes[source_route_idx].pop(source_pos)
        
        # Select target route and position
        target_route_idx = random.randint(0, len(solution.routes) - 1)
        target_route = solution.routes[target_route_idx]
        
        # Insert at random position (avoiding depot positions)
        if len(target_route) <= 2:  # Only depot-depot
            target_pos = 1
        else:
            target_pos = random.randint(1, len(target_route) - 1)
        
        solution.routes[target_route_idx].insert(target_pos, customer)
    
    def _two_opt(self, solution: Solution):
        """Apply 2-opt improvement to a random route."""
        if not solution.routes:
            return
        
        route_idx = random.randint(0, len(solution.routes) - 1)
        route = solution.routes[route_idx]
        
        if len(route) < 4:  # Need at least 4 nodes for 2-opt
            return
        
        # Select two edges to swap
        i = random.randint(1, len(route) - 3)
        j = random.randint(i + 1, len(route) - 2)
        
        # Reverse the segment between i and j
        solution.routes[route_idx] = (route[:i] + 
                                    route[i:j+1][::-1] + 
                                    route[j+1:])
    
    def _cross_exchange(self, solution: Solution):
        """Exchange segments between two routes."""
        if len(solution.routes) < 2:
            return
        
        # Select two different routes
        route1_idx, route2_idx = random.sample(range(len(solution.routes)), 2)
        route1 = solution.routes[route1_idx]
        route2 = solution.routes[route2_idx]
        
        # Select segments to exchange (excluding depot)
        if len(route1) <= 2 or len(route2) <= 2:
            return
        
        # Route 1 segment
        start1 = random.randint(1, len(route1) - 2)
        end1 = random.randint(start1, len(route1) - 2)
        segment1 = route1[start1:end1+1]
        
        # Route 2 segment
        start2 = random.randint(1, len(route2) - 2)
        end2 = random.randint(start2, len(route2) - 2)
        segment2 = route2[start2:end2+1]
        
        # Create new routes
        new_route1 = route1[:start1] + segment2 + route1[end1+1:]
        new_route2 = route2[:start2] + segment1 + route2[end2+1:]
        
        solution.routes[route1_idx] = new_route1
        solution.routes[route2_idx] = new_route2
    
    def get_stats(self) -> Dict[str, Any]:
        """Get algorithm statistics."""
        return self.stats.copy()