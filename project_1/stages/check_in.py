"""
Check-in stage for the Airport Passenger Processing Simulation.
"""

import random
import numpy as np
import simpy
from config import CHECK_IN, TIME_DEPENDENCY, FEEDBACK

class CheckInStage:
    """
    Represents the check-in stage with traditional counters and self-service kiosks.
    """
    
    def __init__(self, env, security_stage, metrics_collector):
        """
        Initialize the check-in stage.
        
        Args:
            env: SimPy environment
            security_stage: The security stage that passengers will proceed to
            metrics_collector: Metrics collector for recording statistics
        """
        self.env = env
        self.security_stage = security_stage
        self.metrics_collector = metrics_collector
        
        # Create resources for traditional check-in counters
        self.first_business_counters = simpy.PriorityResource(env, capacity=CHECK_IN["traditional"]["first_business_counters"])
        self.economy_counters = simpy.Resource(env, capacity=CHECK_IN["traditional"]["economy_counters"])
        
        # Create resources for self-service kiosks
        self.kiosks = simpy.Resource(env, capacity=CHECK_IN["kiosk"]["number"])
        
        # Track queue lengths
        self.first_business_queue_length = 0
        self.economy_queue_length = 0
        self.kiosk_queue_length = 0
        
        # Track service rates for adaptive queue selection
        self.service_rates = {
            "first_business": 1.0 / CHECK_IN["traditional"]["service_time"]["mean"],
            "economy": 1.0 / CHECK_IN["traditional"]["service_time"]["mean"],
            "kiosk": 1.0 / CHECK_IN["kiosk"]["service_time"]["mean"]
        }
        
        # Start queue length monitoring
        self.env.process(self.monitor_queue_lengths())
    
    def process_passenger(self, passenger):
        """
        Process a passenger through check-in.
        
        Args:
            passenger: The passenger to process
        """
        # Record check-in start time
        passenger.check_in_start_time = self.env.now
        
        # Determine which check-in method to use
        check_in_method = self._select_check_in_method(passenger)
        
        # Process based on selected method
        if check_in_method == "traditional":
            yield from self._process_traditional(passenger)
        else:  # kiosk
            yield from self._process_kiosk(passenger)
        
        # Check for incomplete documents (feedback loop)
        if random.random() < FEEDBACK["incomplete_documents"]["probability"]:
            # Passenger needs to resolve document issues
            yield self.env.timeout(FEEDBACK["incomplete_documents"]["delay"])
            
            # Try check-in again (always use traditional for document issues)
            yield from self._process_traditional(passenger)
        
        # Record check-in end time
        passenger.check_in_end_time = self.env.now
        
        # Calculate wait time
        wait_time = passenger.check_in_end_time - passenger.check_in_start_time
        
        # Record wait time for metrics
        self.metrics_collector.record_wait_time("check_in", check_in_method, wait_time, passenger.passenger_class)
        
        # Proceed to security
        self.env.process(self.security_stage.process_passenger(passenger))
    
    def _select_check_in_method(self, passenger):
        """
        Select check-in method based on passenger class, queue lengths, and adaptive behavior.
        
        Args:
            passenger: The passenger to process
            
        Returns:
            str: Selected check-in method ("traditional" or "kiosk")
        """
        # First/Business class passengers always use traditional counters
        if passenger.passenger_class in ["First", "Business"]:
            return "traditional"
        
        # For Economy class, use adaptive selection
        # Start with base probabilities
        traditional_prob = CHECK_IN["initial_choice"]["traditional"]
        kiosk_prob = CHECK_IN["initial_choice"]["kiosk"]
        
        # Adjust based on queue lengths
        if self.economy_queue_length > self.kiosk_queue_length:
            # Economy queue is longer, increase probability of kiosk
            adjustment = min(CHECK_IN["adaptive_adjustment"], 0.4)  # Cap at 40% adjustment
            traditional_prob -= adjustment
            kiosk_prob += adjustment
        elif self.kiosk_queue_length > self.economy_queue_length:
            # Kiosk queue is longer, increase probability of traditional
            adjustment = min(CHECK_IN["adaptive_adjustment"], 0.4)  # Cap at 40% adjustment
            traditional_prob += adjustment
            kiosk_prob -= adjustment
        
        # Make selection based on adjusted probabilities
        if random.random() < traditional_prob:
            return "traditional"
        else:
            return "kiosk"
    
    def _process_traditional(self, passenger):
        """
        Process a passenger through traditional check-in.
        
        Args:
            passenger: The passenger to process
        """
        # Determine which counter to use based on passenger class
        if passenger.passenger_class in ["First", "Business"]:
            # First/Business class passengers use priority counters
            # Priority: First = 0, Business = 1
            priority = 0 if passenger.passenger_class == "First" else 1
            
            # Request counter with priority
            with self.first_business_counters.request(priority=priority) as request:
                # Update queue length
                self.first_business_queue_length += 1
                
                # Start reneging timer
                reneging_process = self.env.process(self._check_reneging(passenger, "first_business"))
                
                try:
                    # Wait for counter
                    yield request
                    
                    # Cancel reneging process if it's still active
                    if reneging_process.is_alive:
                        reneging_process.interrupt()
                    
                    # Update queue length
                    self.first_business_queue_length -= 1
                    
                    # Process at counter
                    service_time = self._calculate_service_time(passenger, "traditional")
                    yield self.env.timeout(service_time)
                    
                except simpy.Interrupt:
                    # Passenger reneged
                    self.first_business_queue_length -= 1
                    return
        else:
            # Economy class passengers use economy counters
            with self.economy_counters.request() as request:
                # Update queue length
                self.economy_queue_length += 1
                
                # Start reneging timer
                reneging_process = self.env.process(self._check_reneging(passenger, "economy"))
                
                try:
                    # Wait for counter
                    yield request
                    
                    # Cancel reneging process if it's still active
                    if reneging_process.is_alive:
                        reneging_process.interrupt()
                    
                    # Update queue length
                    self.economy_queue_length -= 1
                    
                    # Process at counter
                    service_time = self._calculate_service_time(passenger, "traditional")
                    yield self.env.timeout(service_time)
                    
                except simpy.Interrupt:
                    # Passenger reneged
                    self.economy_queue_length -= 1
                    return
    
    def _process_kiosk(self, passenger):
        """
        Process a passenger through self-service kiosk.
        
        Args:
            passenger: The passenger to process
        """
        # Request kiosk
        with self.kiosks.request() as request:
            # Update queue length
            self.kiosk_queue_length += 1
            
            # Start reneging timer
            reneging_process = self.env.process(self._check_reneging(passenger, "kiosk"))
            
            try:
                # Wait for kiosk
                yield request
                
                # Cancel reneging process if it's still active
                if reneging_process.is_alive:
                    reneging_process.interrupt()
                
                # Update queue length
                self.kiosk_queue_length -= 1
                
                # Check for balking (abandonment due to struggle)
                if random.random() < CHECK_IN["kiosk"]["balking_probability"]:
                    # Passenger abandons kiosk
                    passenger.balked = True
                    self.metrics_collector.balking_count += 1
                    
                    # Check for jockeying (switching to traditional counter)
                    if random.random() < CHECK_IN["kiosk"]["jockeying_probability"]:
                        # Switch to traditional counter
                        yield from self._process_traditional(passenger)
                        return
                    
                    # If no jockeying, just return (passenger will still proceed to security)
                    return
                
                # Process at kiosk
                service_time = self._calculate_service_time(passenger, "kiosk")
                yield self.env.timeout(service_time)
                
            except simpy.Interrupt:
                # Passenger reneged
                self.kiosk_queue_length -= 1
                return
    
    def _check_reneging(self, passenger, queue_type):
        """
        Check if a passenger will renege (abandon) the queue.
        
        Args:
            passenger: The passenger to check
            queue_type: The type of queue the passenger is in
        """
        # Get patience threshold for this passenger class
        patience_threshold = passenger.get_current_patience()
        
        # Wait for patience to run out
        try:
            start_time = self.env.now
            
            # Wait for the patience threshold
            yield self.env.timeout(patience_threshold)
            
            # If we get here, the passenger has run out of patience
            # Calculate reneging probability (increases linearly as wait approaches threshold)
            wait_time = self.env.now - start_time
            reneging_prob = wait_time / patience_threshold
            
            if random.random() < reneging_prob:
                # Passenger reneges
                passenger.reneged = True
                self.metrics_collector.reneging_count += 1
                
                # Interrupt the request process
                raise simpy.Interrupt("Passenger reneged")
                
        except simpy.Interrupt:
            # This is normal - it means the passenger got service before reneging
            pass
    
    def _calculate_service_time(self, passenger, check_in_type):
        """
        Calculate service time based on passenger attributes and time-dependent factors.
        
        Args:
            passenger: The passenger being processed
            check_in_type: Type of check-in ("traditional" or "kiosk")
            
        Returns:
            float: Service time in minutes
        """
        # Get base service time parameters
        if check_in_type == "traditional":
            mean = CHECK_IN["traditional"]["service_time"]["mean"]
            sd = CHECK_IN["traditional"]["service_time"]["sd"]
        else:  # kiosk
            mean = CHECK_IN["kiosk"]["service_time"]["mean"]
            sd = CHECK_IN["kiosk"]["service_time"]["sd"]
        
        # Generate base service time (gamma distribution)
        # Shape and scale parameters for gamma distribution
        shape = (mean / sd) ** 2
        scale = (sd ** 2) / mean
        base_time = np.random.gamma(shape, scale)
        
        # Apply passenger-specific modifier
        modifier = passenger.get_service_time_modifier("check_in")
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
            self.metrics_collector.record_queue_length("check_in", "first_business", self.first_business_queue_length, self.env.now)
            self.metrics_collector.record_queue_length("check_in", "economy", self.economy_queue_length, self.env.now)
            self.metrics_collector.record_queue_length("check_in", "kiosk", self.kiosk_queue_length, self.env.now)
            
            # Record resource utilization
            fb_utilization = (self.first_business_counters.count / self.first_business_counters.capacity) if self.first_business_counters.capacity > 0 else 0
            eco_utilization = (self.economy_counters.count / self.economy_counters.capacity) if self.economy_counters.capacity > 0 else 0
            kiosk_utilization = (self.kiosks.count / self.kiosks.capacity) if self.kiosks.capacity > 0 else 0
            
            self.metrics_collector.record_resource_utilization("check_in_first_business", fb_utilization, self.env.now)
            self.metrics_collector.record_resource_utilization("check_in_economy", eco_utilization, self.env.now)
            self.metrics_collector.record_resource_utilization("check_in_kiosk", kiosk_utilization, self.env.now)
            
            # Update service rates based on recent processing
            # (In a real implementation, this would be based on actual measurements)
            
            # Wait for next monitoring interval
            yield self.env.timeout(5)  # Monitor every 5 minutes 