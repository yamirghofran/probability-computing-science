import simpy
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Dict
import json
from datetime import datetime
import os

@dataclass
class SimulationConfig:
    # Arrival parameters
    MEAN_ARRIVAL_TIME: float = 1/116  # minutes between arrivals (7000 passengers/hour)
    SIMULATION_TIME: float = 1440  # 24 hours in minutes
    
    # Passenger mix
    BUSINESS_CLASS_PROB: float = 0.05
    LUGGAGE_PROB: float = 0.7
    
    # Service times (minutes)
    CHECKIN_COUNTER_TIME_MEAN: float = 3
    CHECKIN_KIOSK_TIME_MEAN: float = 2
    SECURITY_TIME_MEAN: float = 0.5
    DETAILED_SECURITY_TIME_MEAN: float = 3
    BOARDING_TIME_MEAN: float = 1
    
    # Probabilities
    DETAILED_SECURITY_PROB: float = 0.1
    JOCKEY_PROB: float = 0.3
    
    # Resource counts
    REGULAR_COUNTERS: int = 275
    BUSINESS_COUNTERS: int = 20
    KIOSKS: int = 90
    REGULAR_SECURITY_LANES: int = 95
    BUSINESS_SECURITY_LANES: int = 10
    BOARDING_GATES: int = 118

class Metrics:
    def __init__(self):
        self.queue_lengths = {
            'checkin_regular': [],
            'checkin_business': [],
            'security_regular': [],
            'security_business': [],
            'boarding': []
        }
        self.utilization = {
            'regular_counters': [],
            'business_counters': [],
            'kiosks': [],
            'regular_security': [],
            'business_security': [],
            'boarding': []
        }
        self.timestamps = []
        
        # Tracking metrics
        self.completed_passengers = 0
        self.abandoned_passengers = 0
        self.current_passengers = 0
        self.throughput_per_hour = []
        
        # Queue metrics
        self.peak_queue_lengths = {
            'checkin_regular': {'length': 0, 'time': 0},
            'checkin_business': {'length': 0, 'time': 0},
            'security_regular': {'length': 0, 'time': 0},
            'security_business': {'length': 0, 'time': 0},
            'boarding': {'length': 0, 'time': 0}
        }
        
        # Wait time tracking
        self.all_wait_times = {
            'checkin_regular': [],
            'checkin_business': [],
            'security_regular': [],
            'security_business': [],
            'boarding': []
        }
        
        # SLA tracking
        self.queue_to_process = {
            'checkin_regular': 'checkin',
            'checkin_business': 'checkin',
            'security_regular': 'security',
            'security_business': 'security',
            'boarding': 'boarding'
        }
        self.sla_metrics = {
            'checkin': {'target': 20, 'met': 0, 'total': 0},
            'security': {'target': 15, 'met': 0, 'total': 0},
            'boarding': {'target': 10, 'met': 0, 'total': 0}
        }
        self.bottleneck_counts = {
            'checkin_regular': 0,
            'checkin_business': 0,
            'security_regular': 0,
            'security_business': 0,
            'boarding': 0
        }

    def update_peak_queue(self, queue_type: str, current_length: int, current_time: float):
        if current_length > self.peak_queue_lengths[queue_type]['length']:
            self.peak_queue_lengths[queue_type]['length'] = current_length
            self.peak_queue_lengths[queue_type]['time'] = current_time
            
    def record_wait_time(self, queue_type: str, wait_time: float):
        self.all_wait_times[queue_type].append(wait_time)
            
    def update_sla(self, process: str, wait_time: float):
        self.sla_metrics[process]['total'] += 1
        if wait_time <= self.sla_metrics[process]['target']:
            self.sla_metrics[process]['met'] += 1
            
    def get_sla_percentages(self):
        return {
            process: (metrics['met'] / metrics['total'] * 100 if metrics['total'] > 0 else 0)
            for process, metrics in self.sla_metrics.items()
        }
        
    def identify_bottleneck(self):
        queue_lengths = self.queue_lengths
        for queue_type in queue_lengths:
            if queue_lengths[queue_type] and queue_lengths[queue_type][-1] > 0:
                self.bottleneck_counts[queue_type] += 1
                
    def finalize_metrics(self, current_time: float, resources: dict):
        # Record final wait times for passengers still in queues
        for queue_type, resource in resources.items():
            if resource.queue:
                for req in resource.queue:
                    wait_time = current_time - req.arrival_time
                    self.record_wait_time(queue_type, wait_time)

class AirportSimulation:
    def __init__(self, config: SimulationConfig):
        self.env = simpy.Environment()
        self.config = config
        self.metrics = Metrics()
        
        # Resources
        self.regular_counters = simpy.Resource(self.env, capacity=config.REGULAR_COUNTERS)
        self.business_counters = simpy.Resource(self.env, capacity=config.BUSINESS_COUNTERS)
        self.kiosks = simpy.Resource(self.env, capacity=config.KIOSKS)
        self.regular_security = simpy.Resource(self.env, capacity=config.REGULAR_SECURITY_LANES)
        self.business_security = simpy.Resource(self.env, capacity=config.BUSINESS_SECURITY_LANES)
        self.boarding_gates = simpy.Resource(self.env, capacity=config.BOARDING_GATES)

    def generate_service_time(self, mean_time: float) -> float:
        return random.expovariate(1.0 / mean_time)

    def checkin_process(self, passenger):
        is_business = passenger['is_business']
        has_luggage = passenger['has_luggage']

        if has_luggage or random.random() < 0.3:
            if is_business:
                resource = self.business_counters
                queue_type = 'checkin_business'
            else:
                resource = self.regular_counters
                queue_type = 'checkin_regular'
            service_time = self.generate_service_time(self.config.CHECKIN_COUNTER_TIME_MEAN)
        else:
            resource = self.kiosks
            queue_type = 'checkin_regular'
            service_time = self.generate_service_time(self.config.CHECKIN_KIOSK_TIME_MEAN)

        req = resource.request()
        req.arrival_time = self.env.now
        yield req
        wait_time = self.env.now - req.arrival_time
        self.metrics.record_wait_time(queue_type, wait_time)
        self.metrics.update_sla(self.metrics.queue_to_process[queue_type], wait_time)
        yield self.env.timeout(service_time)
        resource.release(req)

    def security_process(self, passenger):
        is_business = passenger['is_business']
        needs_detailed = random.random() < self.config.DETAILED_SECURITY_PROB

        if is_business:
            resource = self.business_security
            queue_type = 'security_business'
        else:
            resource = self.regular_security
            queue_type = 'security_regular'

        req = resource.request()
        req.arrival_time = self.env.now
        yield req
        wait_time = self.env.now - req.arrival_time
        self.metrics.record_wait_time(queue_type, wait_time)
        self.metrics.update_sla(self.metrics.queue_to_process[queue_type], wait_time)
        
        base_time = self.generate_service_time(self.config.SECURITY_TIME_MEAN)
        if needs_detailed:
            base_time += self.generate_service_time(self.config.DETAILED_SECURITY_TIME_MEAN)
        yield self.env.timeout(base_time)
        resource.release(req)

    def boarding_process(self, passenger):
        queue_type = 'boarding'
        resource = self.boarding_gates
        req = resource.request()
        req.arrival_time = self.env.now
        yield req
        wait_time = self.env.now - req.arrival_time
        self.metrics.record_wait_time(queue_type, wait_time)
        self.metrics.update_sla(self.metrics.queue_to_process[queue_type], wait_time)
        yield self.env.timeout(self.generate_service_time(self.config.BOARDING_TIME_MEAN))
        resource.release(req)

    def passenger_process(self, id: int):
        self.metrics.current_passengers += 1
        arrival_time = self.env.now
        
        try:
            passenger = {
                'id': id,
                'is_business': random.random() < self.config.BUSINESS_CLASS_PROB,
                'has_luggage': random.random() < self.config.LUGGAGE_PROB,
                'arrival_time': arrival_time
            }

            # Go through all processes
            yield from self.checkin_process(passenger)
            yield from self.security_process(passenger)
            yield from self.boarding_process(passenger)
            
            self.metrics.completed_passengers += 1
        except simpy.Interrupt:
            self.metrics.abandoned_passengers += 1
        finally:
            self.metrics.current_passengers -= 1

    def record_metrics(self):
        last_hour_completed = 0
        last_record_time = 0
        
        while True:
            current_time = self.env.now
            
            # Calculate hourly throughput
            if current_time >= last_record_time + 60:  # Every hour
                hourly_completed = self.metrics.completed_passengers - last_hour_completed
                self.metrics.throughput_per_hour.append(hourly_completed)
                last_hour_completed = self.metrics.completed_passengers
                last_record_time = current_time
            
            self.metrics.timestamps.append(current_time)
            
            # Record queue lengths and identify bottlenecks
            for queue_type, queue_obj in [
                ('checkin_regular', self.regular_counters),
                ('checkin_business', self.business_counters),
                ('security_regular', self.regular_security),
                ('security_business', self.business_security),
                ('boarding', self.boarding_gates)
            ]:
                queue_length = len(queue_obj.queue)
                self.metrics.queue_lengths[queue_type].append(queue_length)
                self.metrics.update_peak_queue(queue_type, queue_length, current_time)
                
                # Calculate real-time queue waits using request arrival times
                if queue_obj.queue:
                    current_waits = [current_time - req.arrival_time for req in queue_obj.queue]
                    self.metrics.all_wait_times[queue_type].append(np.mean(current_waits))
                
            # Record utilization
            self.metrics.utilization['regular_counters'].append(len(self.regular_counters.users) / self.config.REGULAR_COUNTERS)
            self.metrics.utilization['business_counters'].append(len(self.business_counters.users) / self.config.BUSINESS_COUNTERS)
            self.metrics.utilization['kiosks'].append(len(self.kiosks.users) / self.config.KIOSKS)
            self.metrics.utilization['regular_security'].append(len(self.regular_security.users) / self.config.REGULAR_SECURITY_LANES)
            self.metrics.utilization['business_security'].append(len(self.business_security.users) / self.config.BUSINESS_SECURITY_LANES)
            self.metrics.utilization['boarding'].append(len(self.boarding_gates.users) / self.config.BOARDING_GATES)
            
            # Identify bottlenecks
            self.metrics.identify_bottleneck()
            
            yield self.env.timeout(5)  # Record every 5 minutes

    def generate_arrivals(self):
        i = 0
        while True:
            yield self.env.timeout(random.expovariate(1.0 / self.config.MEAN_ARRIVAL_TIME))
            self.env.process(self.passenger_process(i))
            i += 1

    def run(self):
        # Create results directory with timestamp
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_dir = os.path.join("results", f"run_{self.timestamp}")
        os.makedirs(self.results_dir, exist_ok=True)
        self.env.process(self.generate_arrivals())
        self.env.process(self.record_metrics())
        self.env.run(until=self.config.SIMULATION_TIME)
        
        # Finalize metrics for passengers still in queues
        resources = {
            'checkin_regular': self.regular_counters,
            'checkin_business': self.business_counters,
            'security_regular': self.regular_security,
            'security_business': self.business_security,
            'boarding': self.boarding_gates
        }
        self.metrics.finalize_metrics(self.env.now, resources)

    def save_results(self, scenario_name: str):
        results = {
            'scenario': scenario_name,
            'config': self.config.__dict__,
            'metrics': {
                'queue_stats': {
                    queue: {
                        'avg_wait': np.mean(waits) if waits else 0,
                        'max_wait': np.max(waits) if waits else 0
                    }
                    for queue, waits in self.metrics.all_wait_times.items()
                },
                'avg_queue_lengths': {
                    queue: np.mean(lengths) 
                    for queue, lengths in self.metrics.queue_lengths.items()
                },
                'avg_utilization': {
                    resource: np.mean(utils) 
                    for resource, utils in self.metrics.utilization.items()
                },
                'throughput': {
                    'total_completed': self.metrics.completed_passengers,
                    'total_abandoned': self.metrics.abandoned_passengers,
                    'hourly_throughput': self.metrics.throughput_per_hour,
                    'avg_hourly_throughput': np.mean(self.metrics.throughput_per_hour) if self.metrics.throughput_per_hour else 0
                },
                'peak_queues': self.metrics.peak_queue_lengths,
                'sla_compliance': self.metrics.get_sla_percentages(),
                'bottlenecks': {
                    queue: count/len(self.metrics.timestamps) * 100
                    for queue, count in self.metrics.bottleneck_counts.items()
                }
            }
        }
        
        # Save JSON results
        filename = os.path.join(self.results_dir, f"results_{scenario_name}.json")
        with open(filename, 'w') as f:
            json.dump(results, f, indent=4)
        
        self.plot_metrics(scenario_name, self.results_dir)

    def plot_metrics(self, scenario_name: str, results_dir: str):
        # Plot queue lengths over time
        plt.figure(figsize=(12, 6))
        for queue, lengths in self.metrics.queue_lengths.items():
            plt.plot(self.metrics.timestamps, lengths, label=queue)
        plt.xlabel('Time (minutes)')
        plt.ylabel('Queue Length')
        plt.title(f'Queue Lengths Over Time - {scenario_name}')
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(results_dir, f'queue_lengths_{scenario_name}.png'))
        plt.close()
        
        # Plot utilization over time
        plt.figure(figsize=(12, 6))
        for resource, utils in self.metrics.utilization.items():
            plt.plot(self.metrics.timestamps, utils, label=resource)
        plt.xlabel('Time (minutes)')
        plt.ylabel('Utilization Rate')
        plt.title(f'Resource Utilization Over Time - {scenario_name}')
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(results_dir, f'utilization_{scenario_name}.png'))
        plt.close()

def run_scenario(name: str, config_updates: Dict = None):
    config = SimulationConfig()
    if config_updates:
        for key, value in config_updates.items():
            setattr(config, key, value)
    
    sim = AirportSimulation(config)
    sim.run()
    sim.save_results(name)

if __name__ == "__main__":
    # Run different scenarios
    
    # Base scenario
    run_scenario("base")
    
    # High demand scenario
    run_scenario("high_demand", {
        "MEAN_ARRIVAL_TIME": (1/116.67)/2,  
    })
    
    # Low staff scenario
    run_scenario("low_staff", {
        "REGULAR_COUNTERS": 200,  
        "BUSINESS_COUNTERS": 10, 
        "REGULAR_SECURITY_LANES": 80, 
        "BUSINESS_SECURITY_LANES": 5, 
        "BOARDING_GATES": 110
    })
    
    # High staff scenario
    run_scenario("high_staff", {
        "REGULAR_COUNTERS": 350, 
        "BUSINESS_COUNTERS": 25, 
        "REGULAR_SECURITY_LANES": 140, 
        "BUSINESS_SECURITY_LANES": 10, 
        "BOARDING_GATES": 200
    })

    run_scenario("high_demand_high_staff", {
        "MEAN_ARRIVAL_TIME": (1/116.67)/2,  
        "REGULAR_COUNTERS": 550, 
        "BUSINESS_COUNTERS": 30, 
        "REGULAR_SECURITY_LANES": 180, 
        "BUSINESS_SECURITY_LANES": 15, 
        "BOARDING_GATES": 250
    })

