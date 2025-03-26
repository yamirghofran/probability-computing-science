# Airport Queuing System Simulation

## Overview
This project simulates a multi-stage airport passenger flow system, modeling how passengers navigate through check-in, security, and boarding processes. The simulation analyzes queue performance, resource utilization, and bottlenecks under various conditions.

## Scenario Description
The airport simulation models passengers moving through three sequential stages:

1. **Check-in Process**:
   - Passengers choose between regular counters, business counters, or self-service kiosks
   - Business class passengers have dedicated counters
   - Passengers with luggage must use staffed counters
   - Passengers may switch lines (jockey) if wait times are excessive

2. **Security Screening**:
   - Separate lanes for regular and business passengers
   - Random percentage of passengers require detailed security checks
   - Service times vary based on screening requirements

3. **Boarding Process**:
   - Final stage before passengers complete their journey
   - Simulated as a resource with multiple gates

## M/M/c Model Extension
This project extends the basic M/M/c queuing model in several ways:

1. **Network of Queues**: Rather than a single queue, passengers move through an interconnected network of three service stages.

2. **Customer Behaviors**:
   - **Jockeying**: Passengers can switch to shorter queues after waiting for a threshold time
   - **Service differentiation**: Different service times based on passenger attributes
   
3. **Customer Attributes**:
   - Business vs. economy class status
   - Luggage vs. no luggage
   - Random selection for detailed security screening

4. **Resource Selection Logic**:
   - Dynamic selection between kiosks vs. counters
   - Dedicated resources for premium passengers

## Technical Implementation Details

### Simulation Engine
The simulation is built using SimPy, a process-based discrete-event simulation framework. Key components include:

1. **Environment**: The SimPy environment tracks simulation time and manages event scheduling.

2. **Resources**: We use SimPy's Resource class to model service points with finite capacity:
   - Regular and business check-in counters
   - Self-service kiosks
   - Regular and business security lanes
   - Boarding gates

3. **Processes**: Each passenger is modeled as a SimPy process that moves through the system.

### Arrival Process
- Passengers arrive following a Poisson process with configurable arrival rate
- Arrival times between passengers are exponentially distributed
- The base configuration models 7000 passengers/hour (about 116 per minute)

### Service Times
- Service times at each station follow exponential distributions
- Mean service times are configurable parameters:
  - Check-in counter: 3 minutes
  - Self-service kiosk: 2 minutes
  - Basic security check: 0.5 minutes
  - Detailed security check: 3 additional minutes
  - Boarding: 1 minute

### Queue Selection and Jockeying
- Initial queue selection is based on passenger attributes and probabilistic decisions
- Jockeying logic evaluates:
  - Current wait time (must exceed threshold)
  - Alternative queue lengths
  - Estimated wait times in alternative queues
  - Only switches when expected wait time improvement exceeds 20%

### Metrics Collection
- The metrics system samples queue states at regular intervals (every 5 minutes)
- Collects timestamps for each passenger at each service point
- Calculates queue statistics, wait times, and resource utilization
- Identifies SLA compliance based on configurable targets

## Features
- Dynamic passenger arrivals following a Poisson process
- Passenger attributes (business class, luggage status)
- Queue-switching behavior (jockeying) based on wait times
- Comprehensive metrics collection:
  - Queue lengths
  - Wait times
  - Resource utilization
  - SLA compliance
  - Throughput tracking
  - Bottleneck identification

## Scenarios Tested
The simulation evaluates airport performance under multiple conditions:
- Base scenario (normal operations)
- High demand (doubled arrival rate)
- Low staffing levels
- High staffing levels
- Combined high demand with high staffing

## Metrics and Analysis
The simulation captures the following key metrics:

1. **Queue Performance**:
   - Average and maximum queue lengths
   - Average and maximum wait times
   - Peak queue periods

2. **Resource Utilization**:
   - Percentage utilization of each resource type
   - Under/over-utilization identification

3. **Service Level Agreements (SLAs)**:
   - Percentage of passengers processed within target times
   - Breakdown by process stage

4. **System Throughput**:
   - Completed passengers per hour
   - Total passenger completion rate
   
5. **Bottleneck Analysis**:
   - Identification of system constraints
   - Percentage of time each queue acts as bottleneck

## Results
For each scenario, the simulation produces:
- JSON data with detailed metrics
- Queue length visualizations
- Resource utilization charts
- Bottleneck analysis
- Service level agreement compliance

## Key Findings
The simulation reveals several important insights about airport operations:

- **Resource Allocation Impact**: Adding resources at bottleneck points has a greater impact than general staffing increases
- **Queue Dynamics**: Jockeying behavior helps balance queues but doesn't eliminate bottlenecks
- **Business Class Trade-offs**: Dedicated premium resources improve business class experience at the cost of regular passenger throughput
- **Peak Time Management**: System performance is most stressed during arrival spikes, requiring targeted resource allocation
- **Check-in Innovation**: Self-service kiosks significantly reduce check-in bottlenecks for eligible passengers

## Code Structure
The simulation is organized using object-oriented principles:

1. **SimulationConfig**: Dataclass holding all configurable parameters
2. **Metrics**: Class for tracking and calculating simulation statistics
3. **AirportSimulation**: Main simulation class that:
   - Initializes resources
   - Generates passenger arrivals
   - Implements queue selection logic
   - Manages passenger flow through the system
   - Records and visualizes metrics

## Running the Simulation
To run the simulation with the default scenarios:
```
python airport_simulation.py
```

Results will be saved in a timestamped directory under `./results/`. 