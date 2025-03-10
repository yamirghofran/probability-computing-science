"""
Airport Passenger Processing Simulation.

This is the main simulation runner that ties all components together.
"""

import os
import random
import numpy as np
import simpy
import argparse
from datetime import datetime

# Import configuration
from config import RANDOM_SEED, SIM_TIME, SCENARIOS, HOURLY_ARRIVAL_RATES

# Import stages
from stages.arrival import ArrivalProcess
from stages.check_in import CheckInStage
from stages.security import SecurityStage
from stages.boarding import BoardingStage

# Import utilities
from utils.metrics import MetricsCollector
from utils.visualization import create_visualization_report

def run_simulation(scenario_name="base", output_dir="results"):
    """
    Run the airport passenger processing simulation.
    
    Args:
        scenario_name: Name of the scenario to run
        output_dir: Directory to save results
    """
    print(f"Running simulation with scenario: {scenario_name}")
    
    # Set random seed for reproducibility
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    
    # Create SimPy environment
    env = simpy.Environment()
    
    # Create metrics collector
    metrics_collector = MetricsCollector()
    
    # Create stages in reverse order (boarding -> security -> check-in -> arrival)
    # This is necessary because each stage needs a reference to the next stage
    boarding_stage = BoardingStage(env, metrics_collector)
    security_stage = SecurityStage(env, boarding_stage, metrics_collector)
    check_in_stage = CheckInStage(env, security_stage, metrics_collector)
    arrival_process = ArrivalProcess(env, check_in_stage, metrics_collector)
    
    # Apply scenario-specific configuration
    apply_scenario_config(scenario_name, arrival_process, check_in_stage, security_stage, boarding_stage)
    
    # Run the simulation
    env.run(until=SIM_TIME)
    
    # Update final time
    metrics_collector.update_time(env.now)
    
    # Create output directory if it doesn't exist
    scenario_output_dir = os.path.join(output_dir, scenario_name)
    os.makedirs(scenario_output_dir, exist_ok=True)
    
    # Save metrics to CSV
    metrics_collector.save_metrics_to_csv(os.path.join(scenario_output_dir, "metrics"))
    
    # Create visualization report
    create_visualization_report(metrics_collector, scenario_output_dir)
    
    # Print summary
    print_summary(metrics_collector, scenario_name)
    
    return metrics_collector

def apply_scenario_config(scenario_name, arrival_process, check_in_stage, security_stage, boarding_stage):
    """
    Apply scenario-specific configuration to the simulation components.
    
    Args:
        scenario_name: Name of the scenario to apply
        arrival_process: ArrivalProcess instance
        check_in_stage: CheckInStage instance
        security_stage: SecurityStage instance
        boarding_stage: BoardingStage instance
    """
    if scenario_name not in SCENARIOS:
        print(f"Warning: Scenario '{scenario_name}' not found. Using base scenario.")
        return
    
    scenario = SCENARIOS[scenario_name]
    
    # Apply scenario-specific configuration
    if scenario_name == "staffing_low":
        # Reduce staff at check-in and security
        check_in_stage.economy_counters = simpy.Resource(check_in_stage.env, capacity=scenario.get("check_in_traditional_economy", 5))
        security_stage.regular_document_check = simpy.Resource(security_stage.env, capacity=scenario.get("security_regular_lanes", 4))
        security_stage.regular_scanning = simpy.Resource(security_stage.env, capacity=scenario.get("security_regular_lanes", 4))
    
    elif scenario_name == "staffing_high":
        # Increase staff at check-in and security
        check_in_stage.economy_counters = simpy.Resource(check_in_stage.env, capacity=scenario.get("check_in_traditional_economy", 12))
        security_stage.regular_document_check = simpy.Resource(security_stage.env, capacity=scenario.get("security_regular_lanes", 8))
        security_stage.regular_scanning = simpy.Resource(security_stage.env, capacity=scenario.get("security_regular_lanes", 8))
    
    elif scenario_name == "technology":
        # More kiosks, express security
        check_in_stage.kiosks = simpy.Resource(check_in_stage.env, capacity=scenario.get("kiosk_number", 10))
        # Adjust security scanning time (in the service time calculation)
        # This is handled dynamically in the _calculate_service_time method
    
    elif scenario_name == "high_demand":
        # Increase arrival rate by modifying the arrival process
        arrival_multiplier = scenario.get("arrival_rate_multiplier", 1.5)
        
        # Create a new dictionary with increased arrival rates
        increased_rates = {}
        for hour, rate in HOURLY_ARRIVAL_RATES.items():
            increased_rates[hour] = rate * arrival_multiplier
        
        # Update the arrival process with the new rates
        arrival_process.hourly_arrival_rates = increased_rates

def print_summary(metrics_collector, scenario_name):
    """
    Print a summary of the simulation results.
    
    Args:
        metrics_collector: MetricsCollector instance
        scenario_name: Name of the scenario that was run
    """
    system_metrics = metrics_collector.get_system_metrics()
    
    print("\n" + "="*50)
    print(f"Simulation Summary - Scenario: {scenario_name}")
    print("="*50)
    
    print(f"\nPassenger Statistics:")
    print(f"  Total Passengers: {system_metrics.get('total_passengers', 0)}")
    print(f"  Completed Passengers: {system_metrics.get('completed_passengers', 0)}")
    print(f"  Missed Flight Rate: {system_metrics.get('missed_flight_rate', 0):.2%}")
    print(f"  Balking Rate: {system_metrics.get('balking_rate', 0):.2%}")
    print(f"  Reneging Rate: {system_metrics.get('reneging_rate', 0):.2%}")
    
    print(f"\nProcessing Times (minutes):")
    print(f"  Average Check-in Time: {system_metrics.get('avg_check_in_time', 0):.2f}")
    print(f"  Average Security Time: {system_metrics.get('avg_security_time', 0):.2f}")
    print(f"  Average Boarding Time: {system_metrics.get('avg_boarding_time', 0):.2f}")
    print(f"  Average Total Time: {system_metrics.get('avg_total_time', 0):.2f}")
    
    print(f"\nThroughput:")
    print(f"  Passengers Per Hour: {system_metrics.get('throughput_per_hour', 0):.2f}")
    
    print("\nResults saved to the 'results' directory.")
    print("="*50 + "\n")

def run_all_scenarios(output_dir="results"):
    """
    Run all defined scenarios and compare results.
    
    Args:
        output_dir: Directory to save results
    """
    results = {}
    
    # Run each scenario
    for scenario_name in SCENARIOS.keys():
        results[scenario_name] = run_simulation(scenario_name, output_dir)
    
    # Create comparison report
    create_comparison_report(results, output_dir)

def create_comparison_report(results, output_dir):
    """
    Create a report comparing the results of different scenarios.
    
    Args:
        results: Dictionary of MetricsCollector instances for each scenario
        output_dir: Directory to save the report
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create comparison report
    with open(os.path.join(output_dir, "scenario_comparison.txt"), "w") as f:
        f.write("="*50 + "\n")
        f.write("Scenario Comparison Report\n")
        f.write("="*50 + "\n\n")
        
        # Compare key metrics
        metrics_to_compare = [
            "total_passengers",
            "completed_passengers",
            "missed_flight_rate",
            "balking_rate",
            "reneging_rate",
            "avg_check_in_time",
            "avg_security_time",
            "avg_boarding_time",
            "avg_total_time",
            "throughput_per_hour"
        ]
        
        # Write metric comparison
        for metric in metrics_to_compare:
            f.write(f"{metric.replace('_', ' ').title()}:\n")
            for scenario_name, metrics_collector in results.items():
                system_metrics = metrics_collector.get_system_metrics()
                value = system_metrics.get(metric, 0)
                
                if "rate" in metric:
                    f.write(f"  {scenario_name}: {value:.2%}\n")
                elif "time" in metric:
                    f.write(f"  {scenario_name}: {value:.2f} minutes\n")
                else:
                    f.write(f"  {scenario_name}: {value}\n")
            f.write("\n")
        
        # Write conclusion
        f.write("="*50 + "\n")
        f.write("Conclusion\n")
        f.write("="*50 + "\n\n")
        
        # Compare overall performance
        best_scenario = min(results.items(), key=lambda x: x[1].get_system_metrics().get("avg_total_time", float('inf')))
        worst_scenario = max(results.items(), key=lambda x: x[1].get_system_metrics().get("avg_total_time", float('inf')))
        
        f.write(f"Best overall performance (lowest average total time): {best_scenario[0]}\n")
        f.write(f"Worst overall performance (highest average total time): {worst_scenario[0]}\n\n")
        
        # Compare missed flight rates
        best_missed_flight = min(results.items(), key=lambda x: x[1].get_system_metrics().get("missed_flight_rate", float('inf')))
        worst_missed_flight = max(results.items(), key=lambda x: x[1].get_system_metrics().get("missed_flight_rate", float('inf')))
        
        f.write(f"Best missed flight rate: {best_missed_flight[0]} ({best_missed_flight[1].get_system_metrics().get('missed_flight_rate', 0):.2%})\n")
        f.write(f"Worst missed flight rate: {worst_missed_flight[0]} ({worst_missed_flight[1].get_system_metrics().get('missed_flight_rate', 0):.2%})\n\n")
        
        # Compare throughput
        best_throughput = max(results.items(), key=lambda x: x[1].get_system_metrics().get("throughput_per_hour", 0))
        worst_throughput = min(results.items(), key=lambda x: x[1].get_system_metrics().get("throughput_per_hour", 0))
        
        f.write(f"Best throughput: {best_throughput[0]} ({best_throughput[1].get_system_metrics().get('throughput_per_hour', 0):.2f} passengers/hour)\n")
        f.write(f"Worst throughput: {worst_throughput[0]} ({worst_throughput[1].get_system_metrics().get('throughput_per_hour', 0):.2f} passengers/hour)\n")

def main():
    """
    Main entry point for the simulation.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Airport Passenger Processing Simulation")
    parser.add_argument("--scenario", type=str, default="base", help="Scenario to run")
    parser.add_argument("--all", action="store_true", help="Run all scenarios")
    parser.add_argument("--output", type=str, default="results", help="Output directory")
    args = parser.parse_args()
    
    # Create timestamp for output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(args.output, timestamp)
    
    # Run simulation
    if args.all:
        run_all_scenarios(output_dir)
    else:
        run_simulation(args.scenario, output_dir)

if __name__ == "__main__":
    main() 