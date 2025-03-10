"""
Boarding stage for the Airport Passenger Processing Simulation.
"""

import random
import numpy as np
import simpy
from config import BOARDING, TIME_DEPENDENCY

class BoardingStage:
    """
    Represents the boarding stage with sequential boarding and capacity constraints.
    """
    
    def __init__(self, env, metrics_collector):
        """
        Initialize the boarding stage.
        
        Args:
            env: SimPy environment
            metrics_collector: Metrics collector for recording statistics
        """
        self.env = env
        self.metrics_collector = metrics_collector
        
        # Determine number of gates based on aircraft size
        self.aircraft_capacity = BOARDING["aircraft_capacity"]
        self.is_small_aircraft = self.aircraft_capacity <= BOARDING["small_aircraft_threshold"]
        self.num_gates = BOARDING["gates"]["small"] if self.is_small_aircraft else BOARDING["gates"]["large"]
        
        # Create resources for boarding gates
        self.gates = simpy.Resource(env, capacity=self.num_gates)
        
        # Track boarding status
        self.boarded_passengers = 0
        self.boarding_complete = False
        self.boarding_queue = {
            "First": [],
            "Business": [],
            "Economy": []
        }
        
        # Track queue lengths
        self.queue_length = 0
        
        # Start queue length monitoring
        self.env.process(self.monitor_queue_lengths())
        
        # Start boarding process
        self.env.process(self.run_boarding_process())
    
    def process_passenger(self, passenger):
        """
        Process a passenger for boarding.
        
        Args:
            passenger: The passenger to process
        """
        # Record boarding start time
        passenger.boarding_start_time = self.env.now
        
        # Check if flight is already full
        if self.boarded_passengers >= self.aircraft_capacity:
            # Flight is full, passenger missed the flight
            passenger.missed_flight = True
            self.metrics_collector.missed_flights += 1
            
            # Record boarding end time (even though they didn't board)
            passenger.boarding_end_time = self.env.now
            
            # Record passenger data
            self.metrics_collector.record_passenger_complete(passenger)
            return
        
        # Check if passenger's flight time has passed
        if self.env.now > passenger.flight_time:
            # Passenger missed the flight
            passenger.missed_flight = True
            self.metrics_collector.missed_flights += 1
            
            # Record boarding end time (even though they didn't board)
            passenger.boarding_end_time = self.env.now
            
            # Record passenger data
            self.metrics_collector.record_passenger_complete(passenger)
            return
        
        # Add passenger to appropriate boarding queue
        self.boarding_queue[passenger.passenger_class].append(passenger)
        self.queue_length += 1
        
        # Wait until passenger is called for boarding
        yield self.env.process(self._wait_for_boarding(passenger))
    
    def _wait_for_boarding(self, passenger):
        """
        Wait until the passenger is called for boarding.
        
        Args:
            passenger: The passenger waiting to board
        """
        # Wait until passenger is at the front of their class queue and it's their class's turn
        while True:
            # Check if passenger is at the front of their class queue
            if self.boarding_queue[passenger.passenger_class] and self.boarding_queue[passenger.passenger_class][0] == passenger:
                # Check if it's this class's turn to board
                if (passenger.passenger_class == "First") or \
                   (passenger.passenger_class == "Business" and not self.boarding_queue["First"]) or \
                   (passenger.passenger_class == "Economy" and not self.boarding_queue["First"] and not self.boarding_queue["Business"]):
                    # It's this passenger's turn to board
                    break
            
            # Wait a bit and check again
            yield self.env.timeout(1)
        
        # Remove passenger from queue
        self.boarding_queue[passenger.passenger_class].remove(passenger)
        self.queue_length -= 1
        
        # Request a gate
        with self.gates.request() as request:
            # Wait for a gate
            yield request
            
            # Process boarding
            service_time = self._calculate_service_time(passenger)
            yield self.env.timeout(service_time)
            
            # Passenger has boarded
            self.boarded_passengers += 1
            
            # Record boarding end time
            passenger.boarding_end_time = self.env.now
            
            # Record wait time for metrics
            wait_time = passenger.boarding_end_time - passenger.boarding_start_time
            self.metrics_collector.record_wait_time("boarding", "gate", wait_time, passenger.passenger_class)
            
            # Record passenger data
            self.metrics_collector.record_passenger_complete(passenger)
    
    def run_boarding_process(self):
        """
        Run the boarding process, managing the sequential boarding of different passenger classes.
        """
        while True:
            # Check if all passengers have boarded
            if self.boarded_passengers >= self.aircraft_capacity:
                # Reset for next flight
                self.boarded_passengers = 0
                self.boarding_complete = False
                
                # Wait for next flight
                yield self.env.timeout(60)  # 1 hour between flights
                continue
            
            # Wait a bit and check again
            yield self.env.timeout(5)
    
    def _calculate_service_time(self, passenger):
        """
        Calculate boarding service time based on passenger attributes.
        
        Args:
            passenger: The passenger being processed
            
        Returns:
            float: Service time in minutes
        """
        # Get base service time (uniform distribution)
        min_time = BOARDING["service_time"]["min"]
        max_time = BOARDING["service_time"]["max"]
        base_time = random.uniform(min_time, max_time)
        
        # Apply passenger-specific modifier
        modifier = passenger.get_service_time_modifier("boarding")
        service_time = base_time * modifier
        
        # Apply time-dependent modifiers
        
        # Staff fatigue effect
        if self.env.now > TIME_DEPENDENCY["staff_fatigue"]["threshold"]:
            service_time *= (1 + TIME_DEPENDENCY["staff_fatigue"]["efficiency_reduction"])
        
        # Peak period effect
        morning_peak = TIME_DEPENDENCY["peak_periods"]["morning"]
        evening_peak = TIME_DEPENDENCY["peak_periods"]["evening"]
        
        if (morning_peak["start"] <= self.env.now <= morning_peak["end"]) or \
           (evening_peak["start"] <= self.env.now <= evening_peak["end"]):
            service_time *= (1 + TIME_DEPENDENCY["peak_periods"]["service_time_increase"])
        
        return service_time
    
    def monitor_queue_lengths(self):
        """
        Periodically monitor and record queue lengths.
        """
        while True:
            # Record queue lengths
            self.metrics_collector.record_queue_length("boarding", "total", self.queue_length, self.env.now)
            self.metrics_collector.record_queue_length("boarding", "first", len(self.boarding_queue["First"]), self.env.now)
            self.metrics_collector.record_queue_length("boarding", "business", len(self.boarding_queue["Business"]), self.env.now)
            self.metrics_collector.record_queue_length("boarding", "economy", len(self.boarding_queue["Economy"]), self.env.now)
            
            # Record resource utilization
            gate_utilization = (self.gates.count / self.gates.capacity) if self.gates.capacity > 0 else 0
            self.metrics_collector.record_resource_utilization("boarding_gates", gate_utilization, self.env.now)
            
            # Wait for next monitoring interval
            yield self.env.timeout(5)  # Monitor every 5 minutes 