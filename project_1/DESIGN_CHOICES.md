# Design Choices for Airport Passenger Processing Simulation

This document explains the key design choices and assumptions made in the implementation of the airport passenger processing simulation.

## 1. Simulation Framework

### SimPy as Discrete-Event Simulation Engine
We chose SimPy as the simulation framework because it provides a powerful and flexible way to model discrete-event systems. SimPy's process-based approach allows us to model passengers as individual entities with their own attributes and behaviors, which is essential for capturing the complex interactions in an airport environment.

### Object-Oriented Design
The simulation is structured using an object-oriented approach with separate classes for each processing stage (arrival, check-in, security, boarding) and for passengers. This design makes the code modular, maintainable, and extensible, allowing for easy modification of individual components without affecting the entire system.

## 2. Passenger Modeling

### Passenger Attributes
Passengers are modeled with various attributes that influence their behavior and processing times:
- **Class**: First, Business, or Economy, with different proportions (5%, 15%, 80%)
- **Baggage**: Random number of bags (0-3) with a distribution skewed towards fewer bags
- **Group Size**: Random group size (1-5) with most passengers traveling alone or in pairs
- **Frequent Flyer Status**: 20% of passengers are frequent flyers with reduced processing times
- **Queue Selection Strategy**: Each passenger has a strategy for selecting queues (shortest, fastest-moving, or class-appropriate)
- **Patience Threshold**: Class-dependent patience thresholds for waiting in queues

### Service Time Distributions
- **Check-in**: Gamma distribution was chosen for service times because it provides a realistic right-skewed distribution that better represents the variability in check-in processing times compared to exponential or normal distributions.
- **Security**: Exponential distribution was used for simplicity while still capturing the randomness of security processing times.
- **Boarding**: Uniform distribution was used for boarding times as the process is more standardized with less variability.

## 3. Queue and Resource Management

### Priority Queues
We implemented priority queues for First and Business class passengers using SimPy's PriorityResource. First class passengers have higher priority (0) than Business class passengers (1), allowing them to be served first when resources become available.

### Adaptive Queue Selection
Economy class passengers adaptively choose between traditional counters and kiosks based on observed queue lengths. The probability of choosing a particular queue type is adjusted dynamically based on the current queue lengths, with a cap on the adjustment to prevent extreme swings.

### Reneging (Queue Abandonment)
Passengers have class-dependent patience thresholds and may abandon queues if their wait exceeds these thresholds. The probability of reneging increases linearly as the wait time approaches the threshold, modeling increasing impatience.

## 4. Network Complexity Elements

### Feedback Loops
- **Incomplete Documents**: 5% of passengers return to check-in after a 10-minute delay to resolve document issues.
- **Failed Security**: 2% of passengers require secondary inspection, adding 5 minutes to their security processing time.

### Time-Dependent Service Rates
- **Staff Fatigue**: Service times increase by 10% after 6 hours of simulation time to model staff fatigue.
- **Peak Periods**: Service times increase by 20% during peak periods (6-9 AM and 4-7 PM) to model increased congestion and complexity.

### Balking and Jockeying
- **Balking**: 10% of passengers abandon kiosks due to difficulties.
- **Jockeying**: 50% of passengers who balk from kiosks switch to traditional counters.

## 5. Metrics Collection and Analysis

### Comprehensive Metrics
The simulation collects a wide range of metrics:
- Queue lengths over time
- Wait times by passenger class and processing stage
- Resource utilization
- System throughput
- Passenger outcomes (completed, missed flight, balked, reneged)

### Visualization
The simulation generates visualizations of key metrics to facilitate analysis:
- Queue length plots over time
- Wait time distributions by passenger class
- Resource utilization over time
- System performance metrics

## 6. Scenario Analysis

### Configurable Scenarios
The simulation supports multiple scenarios to evaluate different operational strategies:
- **Base**: Default configuration
- **Staffing Low**: Reduced staff at check-in and security
- **Staffing High**: Increased staff at all stages
- **Technology**: More kiosks and express security
- **High Demand**: 50% more arrivals (holiday peak)

### Comparative Analysis
The simulation generates a comparison report that evaluates the performance of different scenarios based on key metrics such as average processing times, missed flight rates, and throughput.

## 7. Assumptions and Simplifications

### Flight Scheduling
- Flights are generated throughout the day with higher frequency during peak hours.
- Each flight has a fixed capacity (150 passengers by default).
- Boarding for a new flight begins immediately after the previous flight is full.

### Service Processes
- Check-in and security are modeled as sequential processes with no parallel activities.
- Boarding is modeled as a sequential process by passenger class (First → Business → Economy).
- Service times are influenced by passenger attributes but do not account for all possible real-world factors.

### Passenger Behavior
- Passengers arrive according to a time-dependent Poisson process.
- Passengers have perfect information about queue lengths for decision-making.
- Passengers do not interact with each other except through competition for resources.

## 8. Future Enhancements

### Potential Improvements
- **Dynamic Staffing**: Adjust staff levels based on queue lengths and time of day.
- **Group Processing**: Model groups of passengers being processed together rather than individually.
- **Flight Delays**: Incorporate flight delays and their impact on passenger behavior.
- **Physical Layout**: Model the physical layout of the airport and passenger movement between stages.
- **Staff Breaks**: Model staff breaks and shift changes.

### Validation
- The simulation results should be validated against real-world data to ensure accuracy.
- Sensitivity analysis should be performed to understand the impact of parameter variations.

## 9. Implementation Notes

### Random Seed
A fixed random seed is used for reproducibility, allowing for consistent results across multiple runs of the same scenario.

### Monitoring Interval
Queue lengths and resource utilization are monitored every 5 minutes of simulation time to balance data collection with performance.

### Output Format
Results are saved in both CSV format for detailed analysis and visualized in an HTML report for easy interpretation. 