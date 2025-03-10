"""
Passenger class for the Airport Passenger Processing Simulation.
"""

import random
import numpy as np
import simpy
from config import EARLY_ARRIVAL, PATIENCE, SERVICE_VARIATIONS, PRIORITY, QUEUE_SELECTION

class Passenger:
    """
    Represents a passenger in the airport simulation with attributes and behaviors.
    """
    id_counter = 0
    
    def __init__(self, env, passenger_class, arrival_time, flight_time):
        """
        Initialize a passenger with their attributes.
        
        Args:
            env: SimPy environment
            passenger_class: Passenger class (First, Business, Economy)
            arrival_time: Time of arrival at the airport
            flight_time: Scheduled flight departure time
        """
        Passenger.id_counter += 1
        self.id = Passenger.id_counter
        self.env = env
        self.passenger_class = passenger_class
        self.arrival_time = arrival_time
        self.flight_time = flight_time
        
        # Initialize tracking attributes
        self.check_in_start_time = None
        self.check_in_end_time = None
        self.security_start_time = None
        self.security_end_time = None
        self.boarding_start_time = None
        self.boarding_end_time = None
        self.missed_flight = False
        self.reneged = False
        self.balked = False
        
        # Initialize passenger-specific attributes
        self._initialize_attributes()
        
    def _initialize_attributes(self):
        """Initialize passenger-specific attributes based on configuration."""
        # Baggage
        self.num_bags = self._generate_baggage()
        
        # Group size
        self.group_size = self._generate_group_size()
        
        # Frequent flyer status
        self.is_frequent_flyer = random.random() < SERVICE_VARIATIONS["frequent_flyer"]["proportion"]
        
        # Queue selection strategy
        self.queue_strategy = self._assign_queue_strategy()
        
        # Patience threshold based on passenger class
        self.base_patience = PATIENCE["base_threshold"][self.passenger_class]
        
        # Priority level based on passenger class
        self.priority = PRIORITY[self.passenger_class]
        
    def _generate_baggage(self):
        """Generate random number of bags for the passenger."""
        # Distribution skewed towards fewer bags
        weights = [0.3, 0.4, 0.2, 0.1]  # 0, 1, 2, 3 bags
        return random.choices(range(SERVICE_VARIATIONS["baggage"]["max_bags"] + 1), weights=weights)[0]
    
    def _generate_group_size(self):
        """Generate random group size for the passenger."""
        # Most passengers travel alone or in pairs
        weights = [0.6, 0.25, 0.1, 0.03, 0.02]  # 1, 2, 3, 4, 5 people
        return random.choices(range(1, SERVICE_VARIATIONS["group"]["max_size"] + 1), weights=weights)[0]
    
    def _assign_queue_strategy(self):
        """Assign a queue selection strategy to the passenger."""
        strategies = list(QUEUE_SELECTION["strategies"].keys())
        weights = list(QUEUE_SELECTION["strategies"].values())
        return random.choices(strategies, weights=weights)[0]
    
    def get_service_time_modifier(self, stage):
        """
        Calculate service time modifier based on passenger attributes.
        
        Args:
            stage: The processing stage (check_in, security, boarding)
            
        Returns:
            float: Modifier to apply to base service time
        """
        modifier = 1.0
        
        # Baggage effect (mainly affects check-in)
        if stage == "check_in" and self.num_bags > 0:
            modifier += self.num_bags * SERVICE_VARIATIONS["baggage"]["time_per_bag"] / 5  # Normalized
        
        # Group size effect
        if self.group_size > 1:
            additional_members = self.group_size - 1
            modifier += additional_members * SERVICE_VARIATIONS["group"]["time_per_additional"] / 5  # Normalized
        
        # Frequent flyer effect (reduces time)
        if self.is_frequent_flyer:
            modifier *= (1 - SERVICE_VARIATIONS["frequent_flyer"]["time_reduction"])
        
        # Time pressure effect (passengers might rush when close to departure)
        time_to_departure = self.flight_time - self.env.now
        if time_to_departure < PATIENCE["time_pressure_threshold"]:
            modifier *= 0.9  # 10% faster when under time pressure
        
        return modifier
    
    def get_current_patience(self):
        """
        Calculate current patience threshold based on time to departure.
        
        Returns:
            float: Current patience threshold in minutes
        """
        patience = self.base_patience
        
        # Reduce patience when close to departure
        time_to_departure = self.flight_time - self.env.now
        if time_to_departure < PATIENCE["time_pressure_threshold"]:
            patience *= (1 - PATIENCE["time_pressure_reduction"])
        
        return patience
    
    def select_queue(self, queues, queue_lengths, service_rates):
        """
        Select a queue based on the passenger's strategy.
        
        Args:
            queues: List of available queues
            queue_lengths: Dictionary of queue lengths
            service_rates: Dictionary of service rates
            
        Returns:
            The selected queue
        """
        if self.queue_strategy == "shortest_queue":
            # Select the queue with the shortest length
            return min(queues, key=lambda q: queue_lengths.get(q, float('inf')))
        
        elif self.queue_strategy == "fastest_moving":
            # Select the queue with the fastest service rate
            return max(queues, key=lambda q: service_rates.get(q, 0))
        
        elif self.queue_strategy == "class_appropriate":
            # First/Business class passengers prefer premium queues
            if self.passenger_class in ["First", "Business"]:
                premium_queues = [q for q in queues if "premium" in str(q).lower() or "priority" in str(q).lower()]
                if premium_queues:
                    return premium_queues[0]
            
            # Default to shortest queue if no class-appropriate queue is found
            return min(queues, key=lambda q: queue_lengths.get(q, float('inf')))
        
        # Default fallback
        return queues[0] if queues else None
    
    def __str__(self):
        """String representation of the passenger."""
        return f"Passenger {self.id} ({self.passenger_class})" 