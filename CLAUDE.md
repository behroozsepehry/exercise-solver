# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Exercise Pair Optimizer - A Python application that builds time-efficient 7-day resistance-training workout plans using Integer Linear Programming (ILP). It selects exercise supersets (pairs) and assigns them to days while minimizing muscular overlaps and meeting weekly set targets.

## Commands

```bash
# Activate virtual environment (Windows - REQUIRED before running)
.\.venv\Scripts\activate

# Run the solver
.\.venv\Scripts\python.exe solve.py

# Install dependencies
.\.venv\Scripts\python.exe -m pip install pulp
```

**Important**: Always use the virtual environment. Never use global Python - the project depends on PuLP which is only installed in .venv.

## Architecture

### Two-Stage ILP Optimization

**Stage 1 (Pairing)**: Selects exercise instances and forms supersets
- Decision variables: exercise counts per category, pair counts
- Constraints: muscle overlap threshold, no shared equipment, usage limits
- Objective: minimize deviations from muscle targets (undershoot weighted 3x)

**Stage 2 (Assignment)**: Assigns pairs to specific days
- Objective: minimize muscular overlaps between supersets on the same day

### Key Data Structures

- `Muscle` enum: 57 muscle groups with weekly set targets
- `Equipment` enum: 10 equipment types (used for pairing constraints)
- `DayCategory` enum: UPPER_GYM, LOWER_GYM, UPPER_HOME, LOWER_HOME

### Coverage Calculation

```
coverage[muscle] = sum(sets_per_instance[category] * count[exercise] * activation[muscle])
```

## Configuration (config.json)

Key parameters:
- `threshold`: Maximum muscle activation overlap for valid superset pairs
- `sets_per_instance`: Sets per exercise per category
- `undershoot_weight_multiplier`: Prioritizes avoiding muscle shortfalls
- `muscle_targets`: Weekly set targets per muscle
- `exercises`: Database with categories, muscle activations (0.1-0.95), equipment, usage limits

## File Structure

- `solve.py`: Main solver (~650 lines) - contains enums, ILP formulation, output generation
- `config.json`: All exercises, muscle targets, and tuning parameters
- `workout_plan.md`: Generated output

## Development Rules

1. Always assess if README.md needs updating after changes to code or configuration
2. Exercises can be freely added/removed in config.json - the solver adapts automatically
3. Equipment conflicts (exercises sharing equipment) cannot form supersets
