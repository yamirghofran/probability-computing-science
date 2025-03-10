"""
Metrics collection and analysis for the Airport Passenger Processing Simulation.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

class MetricsCollector:
    """
    Collects and analyzes performance metrics for the airport simulation.
    """
    
    def __init__(self):
        """Initialize the metrics collector."""
        # Queue metrics
        self.queue_lengths = defaultdict(list)
        self.queue_wait_times = defaultdict(list)
        
        # Resource utilization
        self.resource_utilization = defaultdict(list)
        
        # Passenger metrics
        self.passenger_data = []
        
        # System metrics
        self.throughput = []
        self.missed_flights = 0
        self.balking_count = 0
        self.reneging_count = 0
        
        # Time tracking
        self.current_time = 0
    
    def record_queue_length(self, stage, queue_name, length, time):
        """
        Record the length of a queue at a specific time.
        
        Args:
            stage: Processing stage (check_in, security, boarding)
            queue_name: Name of the queue
            length: Current length of the queue
            time: Current simulation time
        """
        queue_id = f"{stage}_{queue_name}"
        self.queue_lengths[queue_id].append((time, length))
    
    def record_wait_time(self, stage, queue_name, wait_time, passenger_class):
        """
        Record the wait time for a passenger in a queue.
        
        Args:
            stage: Processing stage (check_in, security, boarding)
            queue_name: Name of the queue
            wait_time: Wait time in minutes
            passenger_class: Class of the passenger
        """
        queue_id = f"{stage}_{queue_name}"
        self.queue_wait_times[queue_id].append((wait_time, passenger_class))
    
    def record_resource_utilization(self, resource_name, utilization, time):
        """
        Record the utilization of a resource at a specific time.
        
        Args:
            resource_name: Name of the resource
            utilization: Current utilization (0-1)
            time: Current simulation time
        """
        self.resource_utilization[resource_name].append((time, utilization))
    
    def record_passenger_complete(self, passenger):
        """
        Record data for a passenger who has completed processing.
        
        Args:
            passenger: Passenger object with tracking attributes
        """
        # Calculate processing times
        check_in_time = (passenger.check_in_end_time - passenger.check_in_start_time) if passenger.check_in_end_time else None
        security_time = (passenger.security_end_time - passenger.security_start_time) if passenger.security_end_time else None
        boarding_time = (passenger.boarding_end_time - passenger.boarding_start_time) if passenger.boarding_end_time else None
        
        # Calculate total system time
        total_time = (passenger.boarding_end_time - passenger.arrival_time) if passenger.boarding_end_time else None
        
        # Record passenger data
        self.passenger_data.append({
            'id': passenger.id,
            'class': passenger.passenger_class,
            'arrival_time': passenger.arrival_time,
            'flight_time': passenger.flight_time,
            'check_in_time': check_in_time,
            'security_time': security_time,
            'boarding_time': boarding_time,
            'total_time': total_time,
            'missed_flight': passenger.missed_flight,
            'reneged': passenger.reneged,
            'balked': passenger.balked,
            'bags': passenger.num_bags,
            'group_size': passenger.group_size,
            'frequent_flyer': passenger.is_frequent_flyer
        })
        
        # Update system metrics
        if passenger.missed_flight:
            self.missed_flights += 1
        if passenger.reneged:
            self.reneging_count += 1
        if passenger.balked:
            self.balking_count += 1
    
    def record_throughput(self, time, count):
        """
        Record system throughput at a specific time.
        
        Args:
            time: Current simulation time
            count: Number of passengers processed in the last time period
        """
        self.throughput.append((time, count))
    
    def update_time(self, time):
        """Update the current simulation time."""
        self.current_time = time
    
    def get_queue_metrics(self):
        """
        Calculate queue-specific metrics.
        
        Returns:
            dict: Dictionary of queue metrics
        """
        metrics = {}
        
        for queue_id, data in self.queue_lengths.items():
            if not data:
                continue
                
            times, lengths = zip(*data)
            metrics[queue_id] = {
                'avg_length': np.mean(lengths),
                'max_length': max(lengths),
                'growth_rate': (lengths[-1] - lengths[0]) / (times[-1] - times[0]) if times[-1] > times[0] else 0
            }
        
        return metrics
    
    def get_wait_time_metrics(self):
        """
        Calculate wait time metrics.
        
        Returns:
            dict: Dictionary of wait time metrics
        """
        metrics = {}
        
        for queue_id, data in self.queue_wait_times.items():
            if not data:
                continue
                
            wait_times, classes = zip(*data)
            
            # Overall metrics
            metrics[queue_id] = {
                'avg_wait': np.mean(wait_times),
                'max_wait': max(wait_times),
                'percentile_90': np.percentile(wait_times, 90)
            }
            
            # Class-specific metrics
            for passenger_class in ['First', 'Business', 'Economy']:
                class_wait_times = [wt for wt, pc in data if pc == passenger_class]
                if class_wait_times:
                    metrics[f"{queue_id}_{passenger_class}"] = {
                        'avg_wait': np.mean(class_wait_times),
                        'max_wait': max(class_wait_times),
                        'percentile_90': np.percentile(class_wait_times, 90)
                    }
        
        return metrics
    
    def get_resource_utilization_metrics(self):
        """
        Calculate resource utilization metrics.
        
        Returns:
            dict: Dictionary of resource utilization metrics
        """
        metrics = {}
        
        for resource_name, data in self.resource_utilization.items():
            if not data:
                continue
                
            times, utilizations = zip(*data)
            metrics[resource_name] = {
                'avg_utilization': np.mean(utilizations),
                'max_utilization': max(utilizations),
                'min_utilization': min(utilizations),
                'variability': np.std(utilizations)
            }
        
        return metrics
    
    def get_system_metrics(self):
        """
        Calculate overall system metrics.
        
        Returns:
            dict: Dictionary of system metrics
        """
        # Create DataFrame from passenger data
        if not self.passenger_data:
            return {}
            
        df = pd.DataFrame(self.passenger_data)
        
        # Calculate throughput
        total_processed = len(df)
        completed = len(df[df['boarding_time'].notna()])
        
        # Calculate missed flight rate
        missed_flight_rate = self.missed_flights / total_processed if total_processed > 0 else 0
        
        # Calculate balking and reneging rates
        balking_rate = self.balking_count / total_processed if total_processed > 0 else 0
        reneging_rate = self.reneging_count / total_processed if total_processed > 0 else 0
        
        # Calculate average processing times
        avg_check_in = df['check_in_time'].mean()
        avg_security = df['security_time'].mean()
        avg_boarding = df['boarding_time'].mean()
        avg_total = df['total_time'].mean()
        
        return {
            'total_passengers': total_processed,
            'completed_passengers': completed,
            'throughput_per_hour': completed / (self.current_time / 60) if self.current_time > 0 else 0,
            'missed_flight_rate': missed_flight_rate,
            'balking_rate': balking_rate,
            'reneging_rate': reneging_rate,
            'avg_check_in_time': avg_check_in,
            'avg_security_time': avg_security,
            'avg_boarding_time': avg_boarding,
            'avg_total_time': avg_total
        }
    
    def get_all_metrics(self):
        """
        Get all metrics in a single dictionary.
        
        Returns:
            dict: All metrics
        """
        return {
            'queue_metrics': self.get_queue_metrics(),
            'wait_time_metrics': self.get_wait_time_metrics(),
            'resource_utilization': self.get_resource_utilization_metrics(),
            'system_metrics': self.get_system_metrics()
        }
    
    def save_metrics_to_csv(self, filename_prefix):
        """
        Save metrics to CSV files.
        
        Args:
            filename_prefix: Prefix for the CSV files
        """
        # Save passenger data
        if self.passenger_data:
            pd.DataFrame(self.passenger_data).to_csv(f"{filename_prefix}_passenger_data.csv", index=False)
        
        # Save queue lengths
        queue_length_data = []
        for queue_id, data in self.queue_lengths.items():
            for time, length in data:
                queue_length_data.append({
                    'queue': queue_id,
                    'time': time,
                    'length': length
                })
        if queue_length_data:
            pd.DataFrame(queue_length_data).to_csv(f"{filename_prefix}_queue_lengths.csv", index=False)
        
        # Save wait times
        wait_time_data = []
        for queue_id, data in self.queue_wait_times.items():
            for wait_time, passenger_class in data:
                wait_time_data.append({
                    'queue': queue_id,
                    'wait_time': wait_time,
                    'passenger_class': passenger_class
                })
        if wait_time_data:
            pd.DataFrame(wait_time_data).to_csv(f"{filename_prefix}_wait_times.csv", index=False)
        
        # Save resource utilization
        utilization_data = []
        for resource_name, data in self.resource_utilization.items():
            for time, utilization in data:
                utilization_data.append({
                    'resource': resource_name,
                    'time': time,
                    'utilization': utilization
                })
        if utilization_data:
            pd.DataFrame(utilization_data).to_csv(f"{filename_prefix}_resource_utilization.csv", index=False)
        
        # Save system metrics
        pd.DataFrame([self.get_system_metrics()]).to_csv(f"{filename_prefix}_system_metrics.csv", index=False) 