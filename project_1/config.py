"""
Configuration parameters for the Airport Passenger Processing Simulation.
All parameters are based on the PRD requirements.
"""

import numpy as np

# Simulation parameters
RANDOM_SEED = 42
SIM_TIME = 24 * 60  # 24 hours in minutes
SIM_TIME_UNIT = "minutes"

# Passenger class distribution
PASSENGER_CLASSES = {
    "First": 0.05,    # 5% First Class
    "Business": 0.15, # 15% Business Class
    "Economy": 0.80   # 80% Economy Class
}

# Arrival process parameters
# Hourly arrival rates (passengers per hour)
HOURLY_ARRIVAL_RATES = {
    0: 30, 1: 20, 2: 10, 3: 5, 4: 10, 5: 30,      # 0:00 - 5:59
    6: 120, 7: 150, 8: 140, 9: 100, 10: 80, 11: 70, # 6:00 - 11:59
    12: 90, 13: 80, 14: 70, 15: 90, 16: 120, 17: 140, # 12:00 - 17:59
    18: 100, 19: 80, 20: 60, 21: 50, 22: 40, 23: 30  # 18:00 - 23:59
}

# Early arrival behavior (minutes before flight)
EARLY_ARRIVAL = {
    "First": {"mean": 120, "sd": 20},      # Normal distribution
    "Business": {"mean": 90, "sd": 25},    # Normal distribution
    "Economy": {"mean": 60, "sd": 30}      # Normal distribution
}

# Check-in stage parameters
CHECK_IN = {
    "traditional": {
        "first_business_counters": 2,
        "economy_counters": 8,
        "service_time": {
            "distribution": "gamma",
            "mean": 5,
            "sd": 2
        }
    },
    "kiosk": {
        "number": 6,
        "service_time": {
            "distribution": "gamma",
            "mean": 3,
            "sd": 1
        },
        "balking_probability": 0.1,  # 10% chance of abandoning kiosk
        "jockeying_probability": 0.5  # 50% chance of switching to traditional after balking
    },
    "initial_choice": {
        "traditional": 0.5,
        "kiosk": 0.5
    },
    "adaptive_adjustment": 0.1  # +10% to shorter queue
}

# Security screening parameters
SECURITY = {
    "priority_lane": {
        "servers": 2,
        "document_check_time": 1,  # mean in minutes
        "scanning_time": 2  # mean in minutes
    },
    "regular_lanes": {
        "servers": 5,
        "document_check_time": 1,  # mean in minutes
        "scanning_time": 2  # mean in minutes
    },
    "reneging_threshold": {
        "First": 10,  # minutes
        "Business": 15,  # minutes
        "Economy": 20  # minutes
    }
}

# Boarding process parameters
BOARDING = {
    "service_time": {
        "min": 0.5,  # minutes
        "max": 1.0   # minutes
    },
    "small_aircraft_threshold": 100,  # seats
    "aircraft_capacity": 150,  # seats
    "gates": {
        "small": 1,
        "large": 2
    }
}

# Network complexity elements
FEEDBACK = {
    "incomplete_documents": {
        "probability": 0.05,  # 5% of passengers
        "delay": 10  # minutes
    },
    "failed_security": {
        "probability": 0.02,  # 2% of passengers
        "additional_time": 5  # minutes
    }
}

# Time-dependent service rates
TIME_DEPENDENCY = {
    "staff_fatigue": {
        "threshold": 6 * 60,  # 6 hours in minutes
        "efficiency_reduction": 0.1  # 10% reduction
    },
    "peak_periods": {
        "morning": {"start": 6 * 60, "end": 9 * 60},  # 6-9 AM
        "evening": {"start": 16 * 60, "end": 19 * 60},  # 4-7 PM
        "service_time_increase": 0.2  # 20% increase
    }
}

# Customer behaviors
QUEUE_SELECTION = {
    "strategies": {
        "shortest_queue": 1/3,
        "fastest_moving": 1/3,
        "class_appropriate": 1/3
    }
}

PATIENCE = {
    "base_threshold": {
        "First": 10,  # minutes
        "Business": 15,  # minutes
        "Economy": 20  # minutes
    },
    "time_pressure_reduction": 0.5,  # 50% reduction
    "time_pressure_threshold": 30,  # minutes before departure
    "visible_progress_increase": 0.2,  # 20% increase
    "visible_progress_threshold": 5  # minutes
}

SERVICE_VARIATIONS = {
    "baggage": {
        "time_per_bag": 1,  # minutes
        "max_bags": 3
    },
    "frequent_flyer": {
        "proportion": 0.2,  # 20% of passengers
        "time_reduction": 0.2  # 20% reduction
    },
    "group": {
        "time_per_additional": 0.5,  # minutes
        "max_size": 5
    }
}

# Priority system
PRIORITY = {
    "First": "preemptive",
    "Business": "non-preemptive",
    "Economy": "fifo"
}

# Analysis scenarios
SCENARIOS = {
    "base": {
        "name": "Base Scenario",
        "description": "Default configuration"
    },
    "staffing_low": {
        "name": "Low Staffing",
        "description": "Reduced staff at all stages",
        "check_in_traditional_economy": 5,
        "security_regular_lanes": 4
    },
    "staffing_high": {
        "name": "High Staffing",
        "description": "Increased staff at all stages",
        "check_in_traditional_economy": 12,
        "security_regular_lanes": 8
    },
    "technology": {
        "name": "Technology Focus",
        "description": "More kiosks, express security",
        "kiosk_number": 10,
        "kiosk_choice_probability": 0.7,
        "security_scanning_time_reduction": 0.5
    },
    "high_demand": {
        "name": "Holiday Peak",
        "description": "50% more arrivals",
        "arrival_rate_multiplier": 1.5
    }
} 