# Exercise Pair Optimizer

A solver that builds a time-efficient 7-day resistance-training plan (Upper Gym 1/2/3, Lower Gym 1/2/3, Upper Home, Lower Home) by selecting 12 gym and 6 home exercise instances per upper/lower category (total 36 instances), grouping them into supersets (6 pairs for gym categories, 3 pairs for home categories), and automatically assigning these supersets to days while minimizing exercise repeats within the same day.

The solver models exercises and muscles, enforces a maximum overlap between superset partners, chooses exercises to meet weekly muscle activation targets (minimizing shortfall), and finally assigns pairs to days with minimal conflicts via integer linear programming (ILP), using slack variables to penalize unavoidable exercise repeats within days.

---

## Key ideas

* Exercises are represented with continuous activation values (0.1–0.95) for each muscle group.
* Each chosen exercise instance contributes `SETS_PER_INSTANCE * activation` sets to a muscle's weekly volume (default SETS_PER_INSTANCE, configurable).
* Exercises are classified by category: `UPPER_GYM`, `LOWER_GYM`, `UPPER_HOME`, `LOWER_HOME` based on equipment type. Exercises using machines (chest press, leg press, cable only indirectly) are gym-only, while cable and bodyweight exercises are eligible for both gym and home categories.
* **Machine constraints**: Exercises specify which machines they use (chest press, leg press, cable, etc.). Pairs are only allowed if they don't share machines, reducing equipment adjustment time during workouts.
* Pairing constraint: each category forms pairs (supersets) where gym categories get 6 pairs (for 3 days × 2 pairs/day), home categories get 3 pairs (for 1 day × 3 pairs/day). A pair is allowed only if the *overlap* (dot product of activation vectors) ≤ `THRESHOLD` AND they don't share machines.
* Day assignment: After pairing, assign pairs to days (3 gym days + 1 home day per upper/lower, totaling 7 days) with 2 pairs/day for gym and 3 pairs/day for home, minimizing exercise repeats within a day. Conflicts are handled via ILP relaxation if needed.
* Objective: minimize total shortfall `sum(max(0, target - achieved))` across all muscles, plus assignment penalties if conflicts exist.

---

## What's included

* `solve.py`: combined ILP solver with **integrated day assignment** using PuLP and CBC.
* `assign_pairs_to_days()` function: Additional ILP to assign pairs to days, handling conflicts with slacks for feasibility.
* **Machine constraint system**: Prevents pairing exercises that use the same equipment (chest press, leg press, cable machines, etc.) to reduce workout adjustment time.
* Exercise pool and muscle definitions embedded in the script. The exercise pool is compact and uses compound, time-efficient movements (machines, bands, and bodyweight).

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

1. Edit `solve.py` if you want to change targets or the exercise pool (see sections below).
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
* **Total shortfall sum**: the objective value (lower is better). Zero means all targets met.
* **Assignment**: Day-by-day superset pairs for Upper Gym 1/2/3, Lower Gym 1/2/3, Upper Home, Lower Home with 2 supersets per gym day and 3 supersets per home day, minimizing exercise repeats within days (with penalties if unavoidable).

---

## Important configuration variables

Open `solve.py` and edit the top of the file:

* `SETS_PER_INSTANCE` — how many sets each exercise instance represents (see code for default). Example: if you plan 4 sets per exercise and 7 training days per week, set `SETS_PER_INSTANCE = 4.0 * (7/7) = 4.0` (the solver expects a weekly contribution per instance; earlier runs used e.g. values).
* `THRESHOLD` — maximum allowed overlap for a pair to be allowed (see code for default). Increase to e.g. 0.6–0.7 to allow more pairings.
* `DAY_REQUIREMENTS` — dictionary specifying required instances per category: Upper Gym/Lower Gym (12 each), Upper Home/Lower Home (6 each). Adjust to change total volume.
* `DAYS_PER_CATEGORY` — dictionary specifying training days per category: 3 for gym categories, 1 for home categories (total 7 days).
* `PAIRS_PER_DAY` — dictionary specifying pairs (supersets) per day: 2 for gym, 3 for home.
* `get_max_usage_for_category(category)` — function returning max usage of an exercise in the given category (defaults to DAYS_PER_CATEGORY value).
* `MUSCLE_TARGETS` — dictionary mapping muscle → weekly target sets. Edit these to reflect your own programming targets.

---

## How to modify the exercise pool

Exercises are declared as a dictionary in the script with this shape:

```py
EXERCISES = {
  "Exercise Name": ([DayCategory.UPPER_GYM, DayCategory.LOWER_GYM, ...], {Muscle.CHEST: 0.9, Muscle.LATS: 0.35, ...}, [Machine.CHEST_PRESS, Machine.CABLE]),
  ...
}
```

* Categories: List of eligible `DayCategory` (UPPER_GYM, LOWER_GYM, UPPER_HOME, LOWER_HOME). Machines restrict eligibility: exercise using machines (chest press, leg press) are gym-only; cable and bodyweight exercises are gym and home eligible.
* Activation values: continuous floats in `[0,1]`. Only activations ≥ `0.1` are included to keep the model tidy.
* **Machine specification**: List the machines this exercise uses in brackets. Use an empty list `[]` for bodyweight/free-weight exercises. Machines include: `Machine.CHEST_PRESS`, `Machine.LEG_PRESS`, `Machine.LEG_CURL`, `Machine.LAT_PULLDOWN`, `Machine.SEATED_ROW`, `Machine.CABLE`.
* If two exercise names are redundant (identical activations), prefer merging them into one canonical entry.

Adding or removing an exercise is straightforward — the ILP will adapt.

---

## Tips to reduce shortfall or change program behavior

* Increase `SETS_PER_INSTANCE` to raise total weekly capacity per chosen exercise.
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
* If the model is infeasible, either relax `DAY_REQUIREMENTS` values (make them `>=` instead of `==` in a custom version) or relax `THRESHOLD`, or add more exercises.

### Machine constraints
* **Machine conflicts**: The solver now prevents pairing exercises that use the same equipment. This may make some pairings impossible if you have limited exercise variety.
* **Adjusting constraints**: If you get poor results due to machine constraints, consider:
  - Adding more exercises to your pool that use different machines
  - Temporarily commenting out machine specifications for some exercises
  - Relaxing `THRESHOLD` to allow more pairing flexibility

### Exercise data
* Activations are estimates. If you disagree with a given exercise's activation, tweak the numbers — the solver will reflect your judgment.
* For assignment issues, check if THRESHOLD is too restrictive or exercises have high overlap; the solver penalizes conflicts but may not find perfect schedules in all cases.
