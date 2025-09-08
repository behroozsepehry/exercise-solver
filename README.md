# Exercise Pair Optimizer

A solver that builds a time-efficient 6-day resistance-training plan (Upper A/B/C, Lower A/B/C) by selecting 12 upper and 12 lower exercise instances per week and grouping them into 6 supersets per category (2 supersets/day).

The solver models exercises and muscles, enforces a maximum overlap between superset partners, and chooses exercises so that weekly muscle activation targets are met (minimizing any shortfall).

---

## Key ideas

* Exercises are represented with continuous activation values (0.1–0.95) for each muscle group.
* Each chosen exercise instance contributes `SETS_PER_INSTANCE * activation` sets to a muscle's weekly volume (default SETS\_PER\_INSTANCE = 3.0, configurable).
* Exercises are classified as `upper`, `lower`, or `both`. "Both" exercises can be assigned to either category.
* Pairing constraint: each category (upper / lower) must form 6 unordered pairs (supersets). A pair is allowed only if the *overlap* (dot product of activation vectors) ≤ `THRESHOLD`.
* Objective: minimize the total shortfall `sum(max(0, target - achieved))` across all muscles.

---

## What's included

* `solve.py`: combined solver implemented with **integer linear programming** using PuLP and CBC.
* Exercise pool and muscle definitions embedded in the script. The exercise pool is compact and uses compound, time-efficient movements (machines, bands, and bodyweight).

---

## Requirements

* Python 3.8+
* [PuLP](https://pypi.org/project/PuLP/) (bundled CBC solver is used by default)

Install dependencies in a virtual environment:

```bash
python -m venv .venv
. .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install --upgrade pip
pip install pulp
```

---

## Quick start

1. Edit `solve.py` if you want to change targets or the exercise pool (see sections below).
2. Run the solver:

```bash
python solve.py
```

3. Output explained:

* **Counts**: how many times each exercise is used in the upper and lower schedules (sum = 12 each).
* **Expanded pairs**: list of 6 unordered superset pairs for upper and 6 for lower. (The solver returns pairs; you can arrange pairs across days as you prefer.)
* **Coverage vs targets**: weekly sets contributed to each muscle vs the target; a positive diff means over target; negative means shortfall.
* **Total shortfall sum**: the objective value (lower is better). Zero means all targets met.

---

## Important configuration variables

Open `solve.py` and edit the top of the file:

* `SETS_PER_INSTANCE` — how many sets each exercise instance represents (default `3.0`). Example: if you plan 4 sets per exercise and 7 training days per week, set `SETS_PER_INSTANCE = 4.0 * (7/7) = 4.0` (the solver expects a weekly contribution per instance; earlier runs used e.g. `4.6`).
* `THRESHOLD` — maximum allowed overlap for a pair to be allowed; default `0.5`. Increase to 0.6–0.7 to allow more pairings.
* `REQ_UP` / `REQ_LOW` — number of upper and lower instances required (defaults 12 each). Keep them equal to preserve your 6-day split.
* `MUSCLE_TARGETS` — dictionary mapping muscle → weekly target sets. Edit these to reflect your own programming targets.

---

## How to modify the exercise pool

Exercises are declared as a dictionary in the script with this shape:

```py
EXERCISES = {
  "Exercise Name": ("upper"|"lower"|"both", {Muscle.CHEST: 0.9, Muscle.LATS: 0.35, ...}),
  ...
}
```

* Category: use `"upper"`, `"lower"` or `"both"`.
* Activation values: continuous floats in `[0,1]`. Only activations ≥ `0.1` are included to keep the model tidy.
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

* If the CBC solver is slow or times out on your machine, try limiting solve time with `pulp.PULP_CBC_CMD(timeLimit=30)` or switch to another solver.
* If the model is infeasible, either relax `REQ_UP`/`REQ_LOW` (make them `>=` instead of `==`) or relax `THRESHOLD`, or add more exercises.
* Activations are estimates. If you disagree with a given exercise’s activation, tweak the numbers — the solver will reflect your judgment.

---
