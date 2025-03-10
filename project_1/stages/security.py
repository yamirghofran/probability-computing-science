"""
Security screening stage for the Airport Passenger Processing Simulation.
"""

import random
import numpy as np
import simpy
from config import SECURITY, TIME_DEPENDENCY, FEEDBACK

class SecurityStage:
    """
    Represents the security screening stage with priority and regular lanes.
    """
    
    def __init__(self, env, boarding_stage, metrics_collector):
        """
        Initialize the security stage.
        
        Args:
            env: SimPy environment
            boarding_stage: The boarding stage that passengers will proceed to
            metrics_collector: Metrics collector for recording statistics
        """
        self.env = env
        self.boarding_stage = boarding_stage
        self.metrics_collector = metrics_collector
        
        # Create resources for priority lane
        self.priority_document_check = simpy.PriorityResource(env, capacity=SECURITY["priority_lane"]["servers"])
        self.priority_scanning = simpy.PriorityResource(env, capacity=SECURITY["priority_lane"]["servers"])
        
        # Create resources for regular lanes
        self.regular_document_check = simpy.Resource(env, capacity=SECURITY["regular_lanes"]["servers"])
        self.regular_scanning = simpy.Resource(env, capacity=SECURITY["regular_lanes"]["servers"])
        
        # Track queue lengths
        self.priority_document_queue_length = 0
        self.priority_scanning_queue_length = 0
        self.regular_document_queue_length = 0
        self.regular_scanning_queue_length = 0
        
        # Start queue length monitoring
        self.env.process(self.monitor_queue_lengths())
    
    def process_passenger(self, passenger):
        """
        Process a passenger through security screening.
        
        Args:
            passenger: The passenger to process
        """
        # Record security start time
        passenger.security_start_time = self.env.now
        
        # Determine which lane to use
        if passenger.passenger_class in ["First", "Business"]:
            lane_type = "priority"
        else:
            lane_type = "regular"
        
        # Process through the selected lane
        if lane_type == "priority":
            yield from self._process_priority_lane(passenger)
        else:
            yield from self._process_regular_lane(passenger)
        
        # Check for failed security (feedback loop)
        if random.random() < FEEDBACK["failed_security"]["probability"]:
            # Passenger requires secondary inspection
            yield self.env.timeout(FEEDBACK["failed_security"]["additional_time"])
        
        # Record security end time
        passenger.security_end_time = self.env.now
        
        # Calculate wait time
        wait_time = passenger.security_end_time - passenger.security_start_time
        
        # Record wait time for metrics
        self.metrics_collector.record_wait_time("security", lane_type, wait_time, passenger.passenger_class)
        
        # Proceed to boarding
        self.env.process(self.boarding_stage.process_passenger(passenger))
    
    def _process_priority_lane(self, passenger):
        """
        Process a passenger through the priority security lane.
        
        Args:
            passenger: The passenger to process
        """
        # Priority: First = 0, Business = 1
        priority = 0 if passenger.passenger_class == "First" else 1
        
        # Document check phase
        with self.priority_document_check.request(priority=priority) as request:
            # Update queue length
            self.priority_document_queue_length += 1
            
            # Start reneging timer
            reneging_process = self.env.process(self._check_reneging(passenger, "priority_document"))
            
            try:
                # Wait for document check
                yield request
                
                # Cancel reneging process if it's still active
                if reneging_process.is_alive:
                    reneging_process.interrupt()
                
                # Update queue length
                self.priority_document_queue_length -= 1
                
                # Process document check
                document_time = self._calculate_service_time(passenger, "document_check", "priority")
                yield self.env.timeout(document_time)
                
            except simpy.Interrupt:
                # Passenger reneged
                self.priority_document_queue_length -= 1
                return
        
        # Scanning phase
        with self.priority_scanning.request(priority=priority) as request:
            # Update queue length
            self.priority_scanning_queue_length += 1
            
            # Start reneging timer
            reneging_process = self.env.process(self._check_reneging(passenger, "priority_scanning"))
            
            try:
                # Wait for scanning
                yield request
                
                # Cancel reneging process if it's still active
                if reneging_process.is_alive:
                    reneging_process.interrupt()
                
                # Update queue length
                self.priority_scanning_queue_length -= 1
                
                # Process scanning
                scanning_time = self._calculate_service_time(passenger, "scanning", "priority")
                yield self.env.timeout(scanning_time)
                
            except simpy.Interrupt:
                # Passenger reneged
                self.priority_scanning_queue_length -= 1
                return
    
    def _process_regular_lane(self, passenger):
        """
        Process a passenger through the regular security lane.
        
        Args:
            passenger: The passenger to process
        """
        # Document check phase
        with self.regular_document_check.request() as request:
            # Update queue length
            self.regular_document_queue_length += 1
            
            # Start reneging timer
            reneging_process = self.env.process(self._check_reneging(passenger, "regular_document"))
            
            try:
                # Wait for document check
                yield request
                
                # Cancel reneging process if it's still active
                if reneging_process.is_alive:
                    reneging_process.interrupt()
                
                # Update queue length
                self.regular_document_queue_length -= 1
                
                # Process document check
                document_time = self._calculate_service_time(passenger, "document_check", "regular")
                yield self.env.timeout(document_time)
                
            except simpy.Interrupt:
                # Passenger reneged
                self.regular_document_queue_length -= 1
                return
        
        # Scanning phase
        with self.regular_scanning.request() as request:
            # Update queue length
            self.regular_scanning_queue_length += 1
            
            # Start reneging timer
            reneging_process = self.env.process(self._check_reneging(passenger, "regular_scanning"))
            
            try:
                # Wait for scanning
                yield request
                
                # Cancel reneging process if it's still active
                if reneging_process.is_alive:
                    reneging_process.interrupt()
                
                # Update queue length
                self.regular_scanning_queue_length -= 1
                
                # Process scanning
                scanning_time = self._calculate_service_time(passenger, "scanning", "regular")
                yield self.env.timeout(scanning_time)
                
            except simpy.Interrupt:
                # Passenger reneged
                self.regular_scanning_queue_length -= 1
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
    
    def _calculate_service_time(self, passenger, service_type, lane_type):
        """
        Calculate service time based on passenger attributes and time-dependent factors.
        
        Args:
            passenger: The passenger being processed
            service_type: Type of service (document_check or scanning)
            lane_type: Type of lane (priority or regular)
            
        Returns:
            float: Service time in minutes
        """
        # Get base service time
        if service_type == "document_check":
            if lane_type == "priority":
                mean = SECURITY["priority_lane"]["document_check_time"]
            else:  # regular
                mean = SECURITY["regular_lanes"]["document_check_time"]
            # Assume SD is 30% of mean for document check
            sd = 0.3 * mean
        else:  # scanning
            if lane_type == "priority":
                mean = SECURITY["priority_lane"]["scanning_time"]
            else:  # regular
                mean = SECURITY["regular_lanes"]["scanning_time"]
            # Assume SD is 40% of mean for scanning (more variable)
            sd = 0.4 * mean
        
        # Generate base service time (exponential distribution for simplicity)
        base_time = random.expovariate(1.0 / mean)
        
        # Apply passenger-specific modifier
        modifier = passenger.get_service_time_modifier("security")
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
            self.metrics_collector.record_queue_length("security", "priority_document", self.priority_document_queue_length, self.env.now)
            self.metrics_collector.record_queue_length("security", "priority_scanning", self.priority_scanning_queue_length, self.env.now)
            self.metrics_collector.record_queue_length("security", "regular_document", self.regular_document_queue_length, self.env.now)
            self.metrics_collector.record_queue_length("security", "regular_scanning", self.regular_scanning_queue_length, self.env.now)
            
            # Record resource utilization
            pd_utilization = (self.priority_document_check.count / self.priority_document_check.capacity) if self.priority_document_check.capacity > 0 else 0
            ps_utilization = (self.priority_scanning.count / self.priority_scanning.capacity) if self.priority_scanning.capacity > 0 else 0
            rd_utilization = (self.regular_document_check.count / self.regular_document_check.capacity) if self.regular_document_check.capacity > 0 else 0
            rs_utilization = (self.regular_scanning.count / self.regular_scanning.capacity) if self.regular_scanning.capacity > 0 else 0
            
            self.metrics_collector.record_resource_utilization("security_priority_document", pd_utilization, self.env.now)
            self.metrics_collector.record_resource_utilization("security_priority_scanning", ps_utilization, self.env.now)
            self.metrics_collector.record_resource_utilization("security_regular_document", rd_utilization, self.env.now)
            self.metrics_collector.record_resource_utilization("security_regular_scanning", rs_utilization, self.env.now)
            
            # Wait for next monitoring interval
            yield self.env.timeout(5)  # Monitor every 5 minutes 