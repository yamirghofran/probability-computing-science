"""
Visualization tools for the Airport Passenger Processing Simulation.
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

def plot_queue_lengths(metrics_collector, save_path=None):
    """
    Plot queue lengths over time.
    
    Args:
        metrics_collector: MetricsCollector instance
        save_path: Path to save the plot (optional)
    """
    plt.figure(figsize=(12, 8))
    
    # Group queues by stage
    stages = {}
    for queue_id in metrics_collector.queue_lengths.keys():
        stage, name = queue_id.split('_', 1)
        if stage not in stages:
            stages[stage] = []
        stages[stage].append(queue_id)
    
    # Create subplots for each stage
    fig, axs = plt.subplots(len(stages), 1, figsize=(12, 4 * len(stages)))
    if len(stages) == 1:
        axs = [axs]
    
    for i, (stage, queues) in enumerate(stages.items()):
        for queue_id in queues:
            data = metrics_collector.queue_lengths[queue_id]
            if not data:
                continue
                
            times, lengths = zip(*data)
            axs[i].plot(times, lengths, label=queue_id)
        
        axs[i].set_title(f"{stage.capitalize()} Queue Lengths")
        axs[i].set_xlabel("Time (minutes)")
        axs[i].set_ylabel("Queue Length")
        axs[i].legend()
        axs[i].grid(True)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()

def plot_wait_times(metrics_collector, save_path=None):
    """
    Plot wait time distributions by passenger class.
    
    Args:
        metrics_collector: MetricsCollector instance
        save_path: Path to save the plot (optional)
    """
    # Prepare data
    wait_time_data = []
    for queue_id, data in metrics_collector.queue_wait_times.items():
        stage, name = queue_id.split('_', 1)
        for wait_time, passenger_class in data:
            wait_time_data.append({
                'stage': stage,
                'queue': name,
                'wait_time': wait_time,
                'passenger_class': passenger_class
            })
    
    if not wait_time_data:
        return
        
    df = pd.DataFrame(wait_time_data)
    
    # Create figure
    fig, axs = plt.subplots(1, 3, figsize=(15, 5))
    
    # Plot wait times by class
    for i, stage in enumerate(['check_in', 'security', 'boarding']):
        stage_data = df[df['stage'] == stage]
        if stage_data.empty:
            continue
            
        for passenger_class, color in zip(['First', 'Business', 'Economy'], ['green', 'blue', 'red']):
            class_data = stage_data[stage_data['passenger_class'] == passenger_class]
            if not class_data.empty:
                axs[i].hist(class_data['wait_time'], bins=20, alpha=0.5, label=passenger_class, color=color)
        
        axs[i].set_title(f"{stage.capitalize()} Wait Times")
        axs[i].set_xlabel("Wait Time (minutes)")
        axs[i].set_ylabel("Frequency")
        axs[i].legend()
        axs[i].grid(True)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()

def plot_resource_utilization(metrics_collector, save_path=None):
    """
    Plot resource utilization over time.
    
    Args:
        metrics_collector: MetricsCollector instance
        save_path: Path to save the plot (optional)
    """
    # Group resources by type
    resource_types = {}
    for resource_name in metrics_collector.resource_utilization.keys():
        resource_type = resource_name.split('_')[0]
        if resource_type not in resource_types:
            resource_types[resource_type] = []
        resource_types[resource_type].append(resource_name)
    
    # Create subplots for each resource type
    fig, axs = plt.subplots(len(resource_types), 1, figsize=(12, 4 * len(resource_types)))
    if len(resource_types) == 1:
        axs = [axs]
    
    for i, (resource_type, resources) in enumerate(resource_types.items()):
        for resource_name in resources:
            data = metrics_collector.resource_utilization[resource_name]
            if not data:
                continue
                
            times, utilizations = zip(*data)
            axs[i].plot(times, utilizations, label=resource_name)
        
        axs[i].set_title(f"{resource_type.capitalize()} Utilization")
        axs[i].set_xlabel("Time (minutes)")
        axs[i].set_ylabel("Utilization")
        axs[i].set_ylim(0, 1.1)
        axs[i].legend()
        axs[i].grid(True)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()

def plot_system_metrics(metrics_collector, save_path=None):
    """
    Plot overall system metrics.
    
    Args:
        metrics_collector: MetricsCollector instance
        save_path: Path to save the plot (optional)
    """
    system_metrics = metrics_collector.get_system_metrics()
    if not system_metrics:
        return
    
    # Create figure
    fig, axs = plt.subplots(2, 2, figsize=(12, 10))
    
    # Plot 1: Processing times by stage
    stages = ['check_in', 'security', 'boarding', 'total']
    times = [system_metrics.get(f'avg_{stage}_time', 0) for stage in stages]
    axs[0, 0].bar(stages, times)
    axs[0, 0].set_title("Average Processing Times")
    axs[0, 0].set_ylabel("Time (minutes)")
    axs[0, 0].grid(True)
    
    # Plot 2: Passenger outcomes
    outcomes = ['completed_passengers', 'missed_flight_rate', 'balking_rate', 'reneging_rate']
    values = [system_metrics.get(outcome, 0) for outcome in outcomes]
    axs[0, 1].bar(outcomes, values)
    axs[0, 1].set_title("Passenger Outcomes")
    axs[0, 1].set_ylabel("Count / Rate")
    axs[0, 1].grid(True)
    
    # Plot 3: Throughput over time
    if metrics_collector.throughput:
        times, counts = zip(*metrics_collector.throughput)
        axs[1, 0].plot(times, counts)
        axs[1, 0].set_title("Throughput Over Time")
        axs[1, 0].set_xlabel("Time (minutes)")
        axs[1, 0].set_ylabel("Passengers Processed")
        axs[1, 0].grid(True)
    
    # Plot 4: Class distribution of completed passengers
    if metrics_collector.passenger_data:
        df = pd.DataFrame(metrics_collector.passenger_data)
        completed = df[df['boarding_time'].notna()]
        class_counts = completed['class'].value_counts()
        axs[1, 1].pie(class_counts, labels=class_counts.index, autopct='%1.1f%%')
        axs[1, 1].set_title("Completed Passengers by Class")
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()

def create_visualization_report(metrics_collector, output_dir):
    """
    Create a comprehensive visualization report.
    
    Args:
        metrics_collector: MetricsCollector instance
        output_dir: Directory to save the visualizations
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate plots
    plot_queue_lengths(metrics_collector, os.path.join(output_dir, "queue_lengths.png"))
    plot_wait_times(metrics_collector, os.path.join(output_dir, "wait_times.png"))
    plot_resource_utilization(metrics_collector, os.path.join(output_dir, "resource_utilization.png"))
    plot_system_metrics(metrics_collector, os.path.join(output_dir, "system_metrics.png"))
    
    # Generate HTML report
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Airport Simulation Results</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2 {{ color: #333; }}
            .metrics-container {{ margin-bottom: 30px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .plot-container {{ margin: 20px 0; }}
            img {{ max-width: 100%; border: 1px solid #ddd; }}
        </style>
    </head>
    <body>
        <h1>Airport Passenger Processing Simulation Results</h1>
        
        <div class="metrics-container">
            <h2>System Metrics</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
    """
    
    # Add system metrics to the report
    system_metrics = metrics_collector.get_system_metrics()
    for metric, value in system_metrics.items():
        formatted_value = f"{value:.2f}" if isinstance(value, float) else str(value)
        html_content += f"""
                <tr>
                    <td>{metric.replace('_', ' ').title()}</td>
                    <td>{formatted_value}</td>
                </tr>
        """
    
    html_content += """
            </table>
        </div>
        
        <div class="plot-container">
            <h2>Queue Lengths Over Time</h2>
            <img src="queue_lengths.png" alt="Queue Lengths">
        </div>
        
        <div class="plot-container">
            <h2>Wait Times by Passenger Class</h2>
            <img src="wait_times.png" alt="Wait Times">
        </div>
        
        <div class="plot-container">
            <h2>Resource Utilization</h2>
            <img src="resource_utilization.png" alt="Resource Utilization">
        </div>
        
        <div class="plot-container">
            <h2>System Metrics</h2>
            <img src="system_metrics.png" alt="System Metrics">
        </div>
    </body>
    </html>
    """
    
    # Write HTML report
    with open(os.path.join(output_dir, "report.html"), "w") as f:
        f.write(html_content) 