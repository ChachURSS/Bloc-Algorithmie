"""
Tabu Search Algorithm for VRP
Implements tabu search metaheuristic with aspiration criteria.
"""

import random
import time
from typing import List, Tuple, Dict, Any, Set
from ..vrp_instance import VRPInstance
from ..solution import Solution


class TabuSearch:
    """
    Tabu Search algorithm for Vehicle Routing Problem.
    """
    
    def __init__(self, instance: VRPInstance,
                 tabu_tenure: int = 20,
                 max_iterations: int = 1000,
                 max_no_improvement: int = 200):
        self.instance = instance
        self.tabu_tenure = tabu_tenure
        self.max_iterations = max_iterations
        self.max_no_improvement = max_no_improvement
        
        # Tabu list
        self.tabu_list: List[Tuple[int, int, int]] = []  # (move_type, param1, param2, iteration)
        
        # Statistics
        self.stats = {
            'iterations': 0,
            'best_cost_history': [],
            'current_cost_history': [],
            'tabu_violations': 0,
            'aspiration_acceptances': 0
        }
    
    def solve(self, initial_solution: Solution) -> Solution:
        """
        Solve VRP using Tabu Search.
        
        Args:
            initial_solution: Starting solution
            
        Returns:
            Best solution found
        """
        current_solution = initial_solution.copy()
        current_solution.calculate_cost()
        
        best_solution = current_solution.copy()
        
        iteration = 0
        no_improvement_count = 0
        
        start_time = time.time()
        
        while iteration < self.max_iterations and no_improvement_count < self.max_no_improvement:
            # Generate neighborhood
            neighbors = self._generate_neighborhood(current_solution)
            
            if not neighbors:
                break
            
            # Select best non-tabu move (or best move if aspiration criteria met)
            best_neighbor, move_info = self._select_best_move(neighbors, best_solution.total_cost)
            
            if best_neighbor is None:
                break
            
            # Update current solution
            current_solution = best_neighbor
            current_solution.calculate_cost()
            
            # Update best solution
            if current_solution.total_cost < best_solution.total_cost:
                best_solution = current_solution.copy()
                no_improvement_count = 0
            else:
                no_improvement_count += 1
            
            # Update tabu list
            self._update_tabu_list(move_info, iteration)
            
            # Record statistics
            self.stats['current_cost_history'].append(current_solution.total_cost)
            self.stats['best_cost_history'].append(best_solution.total_cost)
            
            iteration += 1
        
        self.stats['iterations'] = iteration
        self.stats['solve_time'] = time.time() - start_time
        
        return best_solution
    
    def _generate_neighborhood(self, solution: Solution) -> List[Tuple[Solution, Dict]]:
        """Generate neighborhood solutions with move information."""
        neighbors = []
        
        # Swap moves
        neighbors.extend(self._generate_swap_moves(solution))
        
        # Relocate moves
        neighbors.extend(self._generate_relocate_moves(solution))
        
        # 2-opt moves
        neighbors.extend(self._generate_2opt_moves(solution))
        
        return neighbors
    
    def _generate_swap_moves(self, solution: Solution) -> List[Tuple[Solution, Dict]]:
        """Generate all possible swap moves."""
        moves = []
        
        # Get all customers
        all_customers = []
        for route_idx, route in enumerate(solution.routes):
            for pos, customer in enumerate(route):
                if customer != self.instance.depot:
                    all_customers.append((route_idx, pos, customer))
        
        # Generate swap moves (limited to avoid explosion)
        max_swaps = min(50, len(all_customers) * (len(all_customers) - 1) // 2)
        swap_pairs = random.sample(
            [(i, j) for i in range(len(all_customers)) for j in range(i+1, len(all_customers))],
            min(max_swaps, len(all_customers) * (len(all_customers) - 1) // 2)
        )
        
        for i, j in swap_pairs:
            customer1 = all_customers[i]
            customer2 = all_customers[j]
            
            neighbor = solution.copy()
            route1_idx, pos1, cust1 = customer1
            route2_idx, pos2, cust2 = customer2
            
            # Perform swap
            neighbor.routes[route1_idx][pos1] = cust2
            neighbor.routes[route2_idx][pos2] = cust1
            neighbor.calculate_cost()
            
            move_info = {
                'type': 'swap',
                'customer1': cust1,
                'customer2': cust2,
                'route1': route1_idx,
                'route2': route2_idx
            }
            
            moves.append((neighbor, move_info))
        
        return moves
    
    def _generate_relocate_moves(self, solution: Solution) -> List[Tuple[Solution, Dict]]:
        """Generate relocate moves."""
        moves = []
        
        # Limit number of relocate moves
        max_relocates = 30
        move_count = 0
        
        for route_idx, route in enumerate(solution.routes):
            if move_count >= max_relocates:
                break
                
            for pos, customer in enumerate(route):
                if customer == self.instance.depot:
                    continue
                
                # Try relocating to other routes
                for target_route_idx in range(len(solution.routes)):
                    if move_count >= max_relocates:
                        break
                    
                    for target_pos in range(1, len(solution.routes[target_route_idx])):
                        neighbor = solution.copy()
                        
                        # Remove customer from source
                        neighbor.routes[route_idx].pop(pos)
                        
                        # Insert at target
                        if target_route_idx == route_idx and target_pos > pos:
                            target_pos -= 1  # Adjust for removal
                        
                        neighbor.routes[target_route_idx].insert(target_pos, customer)
                        neighbor.calculate_cost()
                        
                        move_info = {
                            'type': 'relocate',
                            'customer': customer,
                            'from_route': route_idx,
                            'to_route': target_route_idx,
                            'from_pos': pos,
                            'to_pos': target_pos
                        }
                        
                        moves.append((neighbor, move_info))
                        move_count += 1
                        
                        if move_count >= max_relocates:
                            break
        
        return moves
    
    def _generate_2opt_moves(self, solution: Solution) -> List[Tuple[Solution, Dict]]:
        """Generate 2-opt moves."""
        moves = []
        max_2opt = 20
        move_count = 0
        
        for route_idx, route in enumerate(solution.routes):
            if len(route) < 4 or move_count >= max_2opt:
                continue
            
            # Try a few random 2-opt moves per route
            for _ in range(min(5, len(route) - 3)):
                if move_count >= max_2opt:
                    break
                
                i = random.randint(1, len(route) - 3)
                j = random.randint(i + 1, len(route) - 2)
                
                neighbor = solution.copy()
                neighbor.routes[route_idx] = (route[:i] + 
                                            route[i:j+1][::-1] + 
                                            route[j+1:])
                neighbor.calculate_cost()
                
                move_info = {
                    'type': '2opt',
                    'route': route_idx,
                    'i': i,
                    'j': j
                }
                
                moves.append((neighbor, move_info))
                move_count += 1
        
        return moves
    
    def _select_best_move(self, neighbors: List[Tuple[Solution, Dict]], 
                         best_known_cost: float) -> Tuple[Solution, Dict]:
        """Select the best non-tabu move or apply aspiration criteria."""
        best_neighbor = None
        best_move_info = None
        best_cost = float('inf')
        
        for neighbor, move_info in neighbors:
            # Check if move is tabu
            is_tabu = self._is_tabu_move(move_info)
            
            # Aspiration criteria: accept tabu move if it improves best known solution
            aspiration = neighbor.total_cost < best_known_cost
            
            if not is_tabu or aspiration:
                if neighbor.total_cost < best_cost:
                    best_cost = neighbor.total_cost
                    best_neighbor = neighbor
                    best_move_info = move_info
                    
                    if aspiration and is_tabu:
                        self.stats['aspiration_acceptances'] += 1
            else:
                self.stats['tabu_violations'] += 1
        
        return best_neighbor, best_move_info
    
    def _is_tabu_move(self, move_info: Dict) -> bool:
        """Check if a move is in the tabu list."""
        move_type = move_info['type']
        
        for tabu_move in self.tabu_list:
            tabu_type, tabu_data, tabu_iteration = tabu_move
            
            if tabu_type != move_type:
                continue
            
            if move_type == 'swap':
                # Check if the same customers are being swapped
                if ((tabu_data['customer1'] == move_info['customer1'] and 
                     tabu_data['customer2'] == move_info['customer2']) or
                    (tabu_data['customer1'] == move_info['customer2'] and 
                     tabu_data['customer2'] == move_info['customer1'])):
                    return True
            
            elif move_type == 'relocate':
                # Check if same customer is being moved between same routes
                if (tabu_data['customer'] == move_info['customer'] and
                    tabu_data['from_route'] == move_info['to_route'] and
                    tabu_data['to_route'] == move_info['from_route']):
                    return True
        
        return False
    
    def _update_tabu_list(self, move_info: Dict, iteration: int):
        """Update the tabu list with the current move."""
        # Add reverse move to tabu list
        if move_info['type'] == 'swap':
            tabu_data = {
                'customer1': move_info['customer2'],
                'customer2': move_info['customer1']
            }
        elif move_info['type'] == 'relocate':
            tabu_data = {
                'customer': move_info['customer'],
                'from_route': move_info['to_route'],
                'to_route': move_info['from_route']
            }
        else:
            tabu_data = move_info.copy()
        
        self.tabu_list.append((move_info['type'], tabu_data, iteration))
        
        # Remove old tabu moves
        self.tabu_list = [(t, d, i) for t, d, i in self.tabu_list 
                         if iteration - i < self.tabu_tenure]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get algorithm statistics."""
        return self.stats.copy()