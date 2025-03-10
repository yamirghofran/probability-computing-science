# Airport Passenger Processing Simulation

A discrete-event simulation of airport passenger processing using SimPy, modeling the flow of passengers through arrival, check-in, security screening, and boarding stages.

## Features

- Realistic passenger arrival patterns using time-dependent Poisson processes
- Multiple passenger classes (First, Business, Economy) with different behaviors
- Complex network behaviors including feedback loops and probabilistic routing
- Adaptive customer decision-making strategies
- Detailed performance metrics for analysis
- Multiple scenarios for comparative analysis

## Setup

1. Install dependencies:
```
pip install -r requirements.txt
```

2. Run the simulation with default (base) scenario:
```
python airport_simulation.py
```

3. Run a specific scenario:
```
python airport_simulation.py --scenario staffing_high
```

4. Run all scenarios and generate a comparison report:
```
python airport_simulation.py --all
```

## Available Scenarios

- **base**: Default configuration
- **staffing_low**: Reduced staff at check-in and security
- **staffing_high**: Increased staff at all stages
- **technology**: More kiosks and express security
- **high_demand**: 50% more arrivals (holiday peak)

## Project Structure

- `airport_simulation.py`: Main simulation runner
- `config.py`: Configuration parameters
- `passenger.py`: Passenger class definition
- `DESIGN_CHOICES.md`: Documentation of design choices and assumptions
- `stages/`: Processing stage implementations
  - `arrival.py`: Passenger arrival process
  - `check_in.py`: Check-in stage (traditional counters and kiosks)
  - `security.py`: Security screening process
  - `boarding.py`: Boarding process
- `utils/`: Utility functions
  - `metrics.py`: Performance metrics collection and analysis
  - `visualization.py`: Data visualization tools

## Results

The simulation generates comprehensive results for each scenario, including:

- Queue lengths over time
- Wait times by passenger class and processing stage
- Resource utilization
- System throughput
- Passenger outcomes (completed, missed flight, balked, reneged)

Results are saved in the `results/` directory with a timestamp, and include:
- CSV files with detailed metrics
- Visualizations of key metrics
- HTML report summarizing the results
- Comparison report when running all scenarios

## Key Findings

Based on the simulation results:

1. **Staffing Levels**: Increasing staff at check-in and security (staffing_high scenario) provides the best overall performance with the lowest average total time and missed flight rate.

2. **High Demand**: During peak periods (high_demand scenario), the system becomes significantly strained, leading to much longer processing times and higher missed flight rates, despite achieving the highest throughput.

3. **Technology Adoption**: While technology adoption (more kiosks, express security) doesn't necessarily improve throughput, it can help balance the load between different processing stages.

4. **Bottlenecks**: Check-in is typically the most time-consuming stage, suggesting that improvements in this area would have the greatest impact on overall system performance.

## Customization

You can customize the simulation by modifying the parameters in `config.py`, including:

- Passenger class distribution
- Arrival rates
- Service times
- Resource capacities
- Feedback loop probabilities
- Patience thresholds

## Documentation

For more information about the design choices and assumptions made in the simulation, see the `DESIGN_CHOICES.md` file. 