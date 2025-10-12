# Exercise Pair Optimizer

A solver that builds a time-efficient 7-day resistance-training plan (Upper Gym 1/2/3, Lower Gym 1/2/3, Upper Home, Lower Home) by selecting supersets based on pairs per day (Upper/Lower Gym: 2 supersets/day × 3 days = 6 total supersets = 12 instances; Upper/Lower Home: 3 supersets/day × 1 day = 3 total supersets = 6 instances), and automatically assigning these supersets to days while minimizing exercise repeats within the same day.

The solver models exercises and muscles, enforces a maximum overlap between superset partners, chooses exercises to meet weekly muscle activation targets (minimizing shortfall), and finally assigns pairs to days with minimal conflicts via integer linear programming (ILP), using slack variables to penalize unavoidable exercise repeats within days.

---

## Key ideas

* Exercises are represented with continuous activation values (0.1–0.95) for each muscle group.
* Each chosen exercise instance contributes sets based on `sets_per_instance[category] * activation` (from `config.json`) to a muscle's weekly volume.
* Exercises are classified by category: `UPPER_GYM`, `LOWER_GYM`, `UPPER_HOME`, `LOWER_HOME` based on configuration. Eligibility is specified per exercise in the config, allowing for separate versions (e.g., cable for gym, band for home) where needed.
* **Machine constraints**: Exercises specify which machines they use (chest press, leg press, cable, etc.). Pairs are only allowed if they don't share machines, reducing equipment adjustment time during workouts. Machines include: `"CHEST_PRESS"`, `"LEG_PRESS"`, `"LEG_CURL"`, `"LAT_PULLDOWN"`, `"SEATED_ROW"`, `"CABLE"`.
* Pairing constraint: each category forms pairs (supersets) where gym categories get 6 pairs (for 3 days × 2 pairs/day), home categories get 3 pairs (for 1 day × 3 pairs/day). A pair is allowed only if the *overlap* (dot product of activation vectors) ≤ `THRESHOLD` AND they don't share machines.
* Day assignment: After pairing, assign pairs to days (3 gym days + 1 home day per upper/lower, totaling 7 days) with 2 pairs/day for gym and 3 pairs/day for home, minimizing exercise repeats within a day. Conflicts are handled via ILP relaxation if needed.
* Objective: minimize weighted sum of absolute deviations from targets plus maximum absolute deviation (`DEVIATION_SUM_WEIGHT * sum_abs_deviations + max_abs_deviation`), measuring deviations in sets rather than percentages to treat all targets equally.

---

## What's included

* `solve.py`: combined ILP solver with **integrated day assignment** using PuLP and CBC.
* `config.json`: JSON configuration file containing all tunable parameters, muscle targets, and exercise definitions.
* `assign_pairs_to_days()` function: Additional ILP to assign pairs to days, handling conflicts with slacks for feasibility.
* **Machine constraint system**: Prevents pairing exercises that use the same equipment (chest press, leg press, cable machines, etc.) to reduce workout adjustment time.
* Exercise pool and muscle definitions loaded from `config.json`. The exercise pool is compact and uses compound, time-efficient movements (machines, bands, and bodyweight).

---

## Requirements

* Python 3.8+
* [PuLP](https://pypi.org/project/PuLP/) (bundled CBC solver is used by default)

---

## Setup (One-time)

1. **Create virtual environment:**
```bash
python -m venv .venv
```

2. **Install dependencies:**
```bash
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install pulp
```

---

## Quick start

1. Edit `config.json` if you want to change targets or the exercise pool (see sections below).
2. Run the solver:
```bash
.\.venv\Scripts\python.exe solve.py
```

---

## Alternative: Using virtual environment activation (Optional)

If you prefer to activate the virtual environment:

1. **Activate the virtual environment:**
```bash
.\.venv\Scripts\activate
```

2. **Run the solver:**
```bash
python solve.py
```

**Note:** In this project, we typically skip the activation step and directly use `.\.venv\Scripts\python.exe` for both installing dependencies and running the script to avoid potential issues with virtual environment activation.

### Output explained

* **Counts**: how many times each exercise is used in each category: Upper Gym (12 total), Lower Gym (12 total), Upper Home (6 total), Lower Home (6 total).
* **Expanded pairs**: list of 6 unordered superset pairs for gym categories, 3 pairs for home categories per upper/lower.
* **Coverage vs targets**: weekly sets contributed to each muscle vs the target; a positive diff means over target; negative means shortfall.
* **Objective and total deviation sum**: shows `DEVIATION_SUM_WEIGHT * sum_abs_deviations + max_abs_deviation` value in sets (lower is better). Followed by the % deviation breakdown. Zero sets means all targets met exactly.
* **Assignment**: Markdown table for each category showing supersets per day, e.g.:

  ```

  ## Workout Plan

  ### Upper Gym Days:

  | Workout Type | Superset 1 | Superset 2 |

  | Upper Gym 1 | Ex1<br>Ex2 | Ex3<br>Ex4 |

  ```

  With 2 supersets per gym day, 3 for home day, minimizing exercise repeats (with penalties if unavoidable).

---

## Important configuration variables

Open `config.json` and edit the following keys:

* `"sets_per_instance"`: Object specifying sets per instance per category (e.g., `"UPPER_GYM": 2.5`), controls weekly contribution per exercise. Example: if you plan 4 sets per exercise and 7 training days per week, adjust values accordingly.
* `"threshold"`: Maximum muscle activation overlap for superset pairs (default 0.2). Increase to e.g. 0.6–0.7 to allow more pairings.
* `"supersets_per_day"`: Object specifying supersets (pairs) per category and day: 2 for gym days (3 days total = 6 supersets), 3 for home days (1 day total = 3 supersets). Adjust to change total volume (will compute total instances as supersets × 2).
* `"days_per_category"`: Object specifying training days per category: 3 for gym, 1 for home (total 7 days). Must be > 0 for feasible division in pairing logic.
* `"muscle_targets"`: Object mapping muscle names → weekly target sets. Edit to reflect your programming targets (see code for current values). Muscles with zero targets are still tracked but don't influence the objective.

---

## How to modify the exercise pool

Exercises are defined in `config.json`'s `"exercises"` object with this structure:

```json
"exercises": {
  "Exercise Name": [
    ["UPPER_GYM"],  // eligible categories
    {"PEC_STERNAL": 0.88, "ANT_DELTOID": 0.30, "TRICEPS_LONG": 0.36},  // activations
    ["CHEST_PRESS"]  // machines used
  ],
  ...
}
```

* Categories: Array of eligible category strings. Eligibility is specified per-exercise (not automatically based on equipment).
* Activation values: Object with floats in `[0,1]` for valid muscle names. Only activations ≥ `0.1` are considered to keep the model efficient.
* **Machine specification**: Array of machine strings. Use empty array `[]` for bodyweight/free-weight exercises. Machines include: `"CHEST_PRESS"`, `"LEG_PRESS"`, `"LEG_CURL"`, `"LAT_PULLDOWN"`, `"SEATED_ROW"`, `"CABLE"`.
* If muscle targets are zero (e.g., `"PECTORAL_MINOR": 0.0`), the muscle is still calculated but doesn't affect the objective (use for informational purposes).

Adding or removing an exercise is straightforward — the ILP will adapt.

---

## Tips to reduce shortfall or change program behavior

* Adjust `sets_per_instance` values (e.g., increase `"UPPER_GYM": 2.5` to 3.0) to raise total weekly capacity per chosen exercise in specific categories.
* Relax `THRESHOLD` to allow more pairings (more flexibility) — try `0.6` or `0.7`.
* Add a few compound exercises that emphasize under-covered muscles (e.g., upright rows, shrugs for neck/traps, monster walks or Copenhagen plank for abductors/adductors).
* If you want variety, add a secondary optimization stage to prefer diverse selections (minimize `sum(c_e^2)` or number of repeats) while keeping the shortfall optimal.

---

## Troubleshooting & notes

### Running the solver
* **Virtual environment issues (Windows)**: If you get "execution policy" errors, try running directly: `.\.venv\Scripts\python.exe solve.py`
* **Dependency issues**: Always use the virtual environment to avoid conflicts with system Python packages
* **Alternative execution**: You can also run `python solve.py` after activating the venv with `.\.venv\Scripts\activate`

### Solver performance
* If the CBC solver is slow or times out on your machine, try limiting solve time with `pulp.PULP_CBC_CMD(timeLimit=30)` or switch to another solver.
* If the model is infeasible, either relax `"supersets_per_day"` values in `config.json` (make them smaller, e.g., reduce gym from 2 to 2 with fewer days) or relax `"threshold"`, or add more exercises.

### Machine constraints
* **Machine conflicts**: The solver now prevents pairing exercises that use the same equipment. This may make some pairings impossible if you have limited exercise variety.
* **Adjusting constraints**: If you get poor results due to machine constraints, consider:
  - Adding more exercises to your pool that use different machines
  - Temporarily commenting out machine specifications for some exercises
  - Relaxing `THRESHOLD` to allow more pairing flexibility

### Exercise data
* Activations are estimates. If you disagree with a given exercise's activation values, edit them in `config.json`.
* For assignment issues, check if `"threshold"` is too restrictive (try increasing to 0.4–0.5) or exercises have high overlap; the solver penalizes conflicts but may not find perfect schedules in all cases.
