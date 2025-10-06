"""
VRP Instance representation
Handles problem data including customers, depot, distances, and constraints.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import json


class VRPInstance:
    """
    Represents a Vehicle Routing Problem instance with support for multiple constraints.
    """
    
    def __init__(self, name: str = "vrp_instance"):
        self.name = name
        self.dimension = 0
        self.capacity = 0
        self.depot = 0
        
        # Basic data
        self.node_coords: Dict[int, Tuple[float, float]] = {}
        self.demands: Dict[int, int] = {}
        self.distance_matrix: np.ndarray = None
        
        # Time windows (optional)
        self.time_windows: Dict[int, Tuple[int, int]] = {}
        self.service_times: Dict[int, int] = {}
        
        # Fleet constraints (optional)
        self.vehicle_count = 1
        self.vehicle_capacities: List[int] = []
        self.vehicle_types: Dict[int, str] = {}
        
        # Dynamic traffic (optional)
        self.time_slots = 1
        self.dynamic_distances: List[np.ndarray] = []
        
        # Collection points (optional)
        self.collection_points: Dict[int, int] = {}  # customer -> collection point
        
    def add_customer(self, customer_id: int, x: float, y: float, demand: int,
                     time_window: Optional[Tuple[int, int]] = None,
                     service_time: int = 0,
                     collection_point: Optional[int] = None):
        """Add a customer to the instance."""
        self.node_coords[customer_id] = (x, y)
        self.demands[customer_id] = demand
        
        if time_window:
            self.time_windows[customer_id] = time_window
            
        if service_time > 0:
            self.service_times[customer_id] = service_time
            
        if collection_point is not None:
            self.collection_points[customer_id] = collection_point
            
        self.dimension = max(self.dimension, customer_id + 1)
    
    def set_depot(self, depot_id: int, x: float, y: float):
        """Set the depot location."""
        self.depot = depot_id
        self.node_coords[depot_id] = (x, y)
        self.demands[depot_id] = 0
        
    def calculate_distance_matrix(self):
        """Calculate Euclidean distance matrix between all nodes."""
        nodes = sorted(self.node_coords.keys())
        n = len(nodes)
        self.distance_matrix = np.zeros((n, n))
        
        for i, node_i in enumerate(nodes):
            for j, node_j in enumerate(nodes):
                if i != j:
                    x1, y1 = self.node_coords[node_i]
                    x2, y2 = self.node_coords[node_j]
                    distance = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)
                    self.distance_matrix[i][j] = distance
    
    def set_fleet(self, vehicle_count: int, capacity: int = None, 
                  capacities: List[int] = None):
        """Configure the fleet of vehicles."""
        self.vehicle_count = vehicle_count
        
        if capacity is not None:
            self.capacity = capacity
            self.vehicle_capacities = [capacity] * vehicle_count
        elif capacities is not None:
            self.vehicle_capacities = capacities[:vehicle_count]
        else:
            self.vehicle_capacities = [100] * vehicle_count  # Default capacity
    
    def get_distance(self, from_node: int, to_node: int, time_slot: int = 0) -> float:
        """Get distance between two nodes, considering dynamic traffic if applicable."""
        if self.dynamic_distances and time_slot < len(self.dynamic_distances):
            return self.dynamic_distances[time_slot][from_node][to_node]
        elif self.distance_matrix is not None:
            return self.distance_matrix[from_node][to_node]
        else:
            # Fallback to Euclidean distance
            x1, y1 = self.node_coords[from_node]
            x2, y2 = self.node_coords[to_node]
            return np.sqrt((x1 - x2)**2 + (y1 - y2)**2)
    
    def is_feasible_time_window(self, customer: int, arrival_time: int) -> bool:
        """Check if arrival time respects customer's time window."""
        if customer not in self.time_windows:
            return True
        
        early, late = self.time_windows[customer]
        return early <= arrival_time <= late
    
    def get_waiting_time(self, customer: int, arrival_time: int) -> int:
        """Calculate waiting time if arriving before time window opens."""
        if customer not in self.time_windows:
            return 0
        
        early, _ = self.time_windows[customer]
        return max(0, early - arrival_time)
    
    def to_dict(self) -> Dict:
        """Convert instance to dictionary for serialization."""
        return {
            'name': self.name,
            'dimension': self.dimension,
            'capacity': self.capacity,
            'depot': self.depot,
            'node_coords': self.node_coords,
            'demands': self.demands,
            'time_windows': self.time_windows,
            'service_times': self.service_times,
            'vehicle_count': self.vehicle_count,
            'vehicle_capacities': self.vehicle_capacities,
            'collection_points': self.collection_points
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'VRPInstance':
        """Create instance from dictionary."""
        instance = cls(data['name'])
        instance.dimension = data['dimension']
        instance.capacity = data['capacity']
        instance.depot = data['depot']
        instance.node_coords = {int(k): v for k, v in data['node_coords'].items()}
        instance.demands = {int(k): v for k, v in data['demands'].items()}
        instance.time_windows = {int(k): tuple(v) for k, v in data.get('time_windows', {}).items()}
        instance.service_times = {int(k): v for k, v in data.get('service_times', {}).items()}
        instance.vehicle_count = data.get('vehicle_count', 1)
        instance.vehicle_capacities = data.get('vehicle_capacities', [])
        instance.collection_points = {int(k): v for k, v in data.get('collection_points', {}).items()}
        instance.calculate_distance_matrix()
        return instance
    
    def save(self, filepath: str):
        """Save instance to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, filepath: str) -> 'VRPInstance':
        """Load instance from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)