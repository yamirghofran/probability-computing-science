"""
Arrival process for the Airport Passenger Processing Simulation.
"""

import random
import numpy as np
import simpy
from passenger import Passenger
from config import PASSENGER_CLASSES, HOURLY_ARRIVAL_RATES, EARLY_ARRIVAL

class ArrivalProcess:
    """
    Manages the arrival of passengers at the airport.
    """
    
    def __init__(self, env, check_in_stage, metrics_collector):
        """
        Initialize the arrival process.
        
        Args:
            env: SimPy environment
            check_in_stage: The check-in stage that passengers will proceed to
            metrics_collector: Metrics collector for recording statistics
        """
        self.env = env
        self.check_in_stage = check_in_stage
        self.metrics_collector = metrics_collector
        self.passengers_generated = 0
        
        # Initialize hourly arrival rates (can be modified by scenarios)
        self.hourly_arrival_rates = HOURLY_ARRIVAL_RATES.copy()
        
        # Start the arrival process
        self.process = env.process(self.run())
    
    def run(self):
        """
        Run the arrival process, generating passengers according to a time-dependent Poisson process.
        """
        while True:
            # Get current hour (0-23)
            current_hour = int((self.env.now / 60) % 24)
            
            # Get arrival rate for the current hour (passengers per hour)
            hourly_rate = self.hourly_arrival_rates[current_hour]
            
            # Convert to rate per minute
            rate_per_minute = hourly_rate / 60
            
            # Generate time until next arrival (exponential distribution)
            time_to_next = random.expovariate(rate_per_minute)
            
            # Wait until next arrival
            yield self.env.timeout(time_to_next)
            
            # Generate a passenger
            self.generate_passenger()
    
    def generate_passenger(self):
        """
        Generate a passenger with appropriate attributes and send them to check-in.
        """
        # Determine passenger class based on configured proportions
        passenger_class = self._determine_passenger_class()
        
        # Determine flight time (when the passenger's flight departs)
        # We'll generate flights throughout the day with some clustering
        flight_time = self._generate_flight_time()
        
        # Determine arrival time based on early arrival behavior
        arrival_time = self.env.now
        
        # Create passenger
        passenger = Passenger(self.env, passenger_class, arrival_time, flight_time)
        self.passengers_generated += 1
        
        # Send passenger to check-in
        self.env.process(self.check_in_stage.process_passenger(passenger))
        
        # Log arrival
        self._log_arrival(passenger)
    
    def _determine_passenger_class(self):
        """
        Determine the passenger's class based on configured proportions.
        
        Returns:
            str: Passenger class (First, Business, Economy)
        """
        classes = list(PASSENGER_CLASSES.keys())
        probabilities = list(PASSENGER_CLASSES.values())
        return random.choices(classes, weights=probabilities)[0]
    
    def _generate_flight_time(self):
        """
        Generate a flight departure time.
        
        Returns:
            float: Flight departure time in minutes from simulation start
        """
        # Current hour in the simulation
        current_hour = int((self.env.now / 60) % 24)
        
        # Generate a flight time that's at least 60 minutes in the future
        # with higher probability during peak hours
        
        # Peak hours have higher flight frequency
        peak_hours = [7, 8, 9, 12, 13, 16, 17, 18]
        
        # Generate a random hour for the flight, weighted towards peak hours
        if current_hour in peak_hours:
            # If we're in a peak hour, 70% chance the flight is in the next 3 hours
            if random.random() < 0.7:
                flight_hour = current_hour + random.randint(1, 3)
            else:
                flight_hour = (current_hour + random.randint(4, 12)) % 24
        else:
            # If not in peak hour, 40% chance the flight is in the next 3 hours
            if random.random() < 0.4:
                flight_hour = current_hour + random.randint(1, 3)
            else:
                # Higher chance of flight being during a peak hour
                flight_hour = random.choice(peak_hours)
        
        # Ensure flight_hour is within 0-23 range
        flight_hour = flight_hour % 24
        
        # Convert to simulation time
        current_day = int(self.env.now / (24 * 60))
        flight_day = current_day if flight_hour > current_hour else current_day + 1
        
        # Add random minutes within the hour
        flight_minute = random.randint(0, 59)
        
        # Calculate flight time in minutes from simulation start
        flight_time = (flight_day * 24 * 60) + (flight_hour * 60) + flight_minute
        
        # Ensure flight is at least 60 minutes in the future
        if flight_time - self.env.now < 60:
            flight_time += 24 * 60  # Add a day
        
        return flight_time
    
    def _log_arrival(self, passenger):
        """
        Log passenger arrival for metrics collection.
        
        Args:
            passenger: The generated passenger
        """
        # Calculate how early the passenger arrived before their flight
        early_arrival_time = passenger.flight_time - passenger.arrival_time
        
        # Log for metrics
        self.metrics_collector.passenger_data.append({
            'id': passenger.id,
            'class': passenger.passenger_class,
            'arrival_time': passenger.arrival_time,
            'flight_time': passenger.flight_time,
            'early_arrival_minutes': early_arrival_time,
            'bags': passenger.num_bags,
            'group_size': passenger.group_size,
            'frequent_flyer': passenger.is_frequent_flyer
        })
        
        # Record throughput (arrivals per hour)
        hour_bin = int(self.env.now / 60)
        self.metrics_collector.record_throughput(hour_bin, 1) 