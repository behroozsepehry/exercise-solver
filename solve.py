import pulp
from enum import Enum, auto
from typing import Dict, List, Tuple, Optional, Union, Any, cast

# -----------------------
# Enums
# -----------------------
class Muscle(Enum):
    CHEST = auto()
    UPPER_BACK = auto()
    LATS = auto()
    ANT_DELTOID = auto()
    LAT_DELTOID = auto()
    POST_DELTOID = auto()
    BICEPS = auto()
    TRICEPS = auto()
    QUADS = auto()
    HAMSTRINGS = auto()
    GLUTES = auto()
    CALVES = auto()
    CORE = auto()
    OBLIQUES = auto()
    ERECTORS = auto()
    FOREARMS = auto()
    ADDUCTORS = auto()
    ABDUCTORS = auto()
    NECK = auto()

class Machine(Enum):
    LEG_PRESS = auto()
    CHEST_PRESS = auto()
    LEG_CURL = auto()
    LAT_PULLDOWN = auto()
    SEATED_ROW = auto()
    CABLE = auto()

class DayCategory(Enum):
    UPPER_GYM = auto()
    LOWER_GYM = auto()
    UPPER_HOME = auto()
    LOWER_HOME = auto()

MUSCLE_INDEX = {m: i for i, m in enumerate(Muscle)}

# -----------------------
# Type Definitions
# -----------------------
ExerciseName = str
MuscleActivation = Dict[Muscle, float]
MachineList = List[Machine]
ExerciseData = Tuple[List[DayCategory], MuscleActivation, MachineList]
ExerciseDict = Dict[ExerciseName, ExerciseData]
MuscleTargetDict = Dict[Muscle, float]
ExerciseVector = List[float]
ExerciseMatrix = List[List[float]]
LpVariableDict = Dict[Any, pulp.LpVariable]
ExerciseCounts = Dict[ExerciseName, int]
ExercisePairs = List[Tuple[ExerciseName, ExerciseName]]
DayAssignments = Dict[str, ExercisePairs]
CoverageDict = Dict[Muscle, float]

# -----------------------
# Tunables
# -----------------------
SETS_PER_INSTANCE: float = 3.0*7/8
THRESHOLD: float = 0.2
DAY_REQUIREMENTS = {DayCategory.UPPER_GYM: 12, DayCategory.LOWER_GYM: 12, DayCategory.UPPER_HOME: 6, DayCategory.LOWER_HOME: 6}
PAIRS_PER_CATEGORY = {cat: DAY_REQUIREMENTS[cat] // 2 for cat in DAY_REQUIREMENTS}
DAYS_PER_CATEGORY = {DayCategory.UPPER_GYM: 3, DayCategory.LOWER_GYM: 3, DayCategory.UPPER_HOME: 1, DayCategory.LOWER_HOME: 1}
PAIRS_PER_DAY = {DayCategory.UPPER_GYM: 2, DayCategory.LOWER_GYM: 2, DayCategory.UPPER_HOME: 3, DayCategory.LOWER_HOME: 3}

def get_max_usage_for_category(cat: DayCategory) -> int:
    """Get the maximum times an exercise can be used in the given category"""
    return DAYS_PER_CATEGORY[cat]

# -----------------------
# Targets: default sets/week (adjustable)
# -----------------------
MUSCLE_TARGETS: MuscleTargetDict = {
    Muscle.CHEST: 12,
    Muscle.UPPER_BACK: 10,
    Muscle.LATS: 12,
    Muscle.ANT_DELTOID: 8,
    Muscle.LAT_DELTOID: 8,
    Muscle.POST_DELTOID: 8,
    Muscle.BICEPS: 8,
    Muscle.TRICEPS: 8,
    Muscle.QUADS: 12,
    Muscle.HAMSTRINGS: 10,
    Muscle.GLUTES: 12,
    Muscle.CALVES: 8,
    Muscle.CORE: 8,
    Muscle.OBLIQUES: 6,
    Muscle.ERECTORS: 6,
    Muscle.FOREARMS: 4,
    Muscle.ADDUCTORS: 6,
    Muscle.ABDUCTORS: 6,
    Muscle.NECK: 3
}

EXERCISES: ExerciseDict = {
    # Upper exercises (machine: only gym, cable/bodyweight: both gym and home)
    "Chest Press": ([DayCategory.UPPER_GYM], {
        Muscle.CHEST: 0.95, Muscle.ANT_DELTOID: 0.30, Muscle.TRICEPS: 0.40, Muscle.FOREARMS: 0.20
    }, [Machine.CHEST_PRESS]),
    "Push-ups": ([DayCategory.UPPER_HOME], {
        Muscle.CHEST: 0.88, Muscle.ANT_DELTOID: 0.25, Muscle.TRICEPS: 0.35, Muscle.CORE: 0.25
    }, []),
    "Chest Fly (cable/band)": ([DayCategory.UPPER_GYM, DayCategory.UPPER_HOME], {
        Muscle.CHEST: 0.85, Muscle.ANT_DELTOID: 0.20
    }, [Machine.CABLE]),
    "Row": ([DayCategory.UPPER_GYM], {
        Muscle.UPPER_BACK: 0.92, Muscle.LATS: 0.55, Muscle.BICEPS: 0.36, Muscle.POST_DELTOID: 0.28
    }, [Machine.SEATED_ROW]),
    "Face Pull (cable/band)": ([DayCategory.UPPER_GYM], {
        Muscle.POST_DELTOID: 0.85, Muscle.UPPER_BACK: 0.40, Muscle.LATS: 0.15
    }, [Machine.CABLE]),
    "Lat Pulldown (machine)": ([DayCategory.UPPER_GYM], {
        Muscle.LATS: 0.93, Muscle.UPPER_BACK: 0.35, Muscle.BICEPS: 0.30
    }, [Machine.LAT_PULLDOWN]),
    "Overhead Press (cable/band)": ([DayCategory.UPPER_GYM, DayCategory.UPPER_HOME], {
        Muscle.ANT_DELTOID: 0.82, Muscle.LAT_DELTOID: 0.36, Muscle.TRICEPS: 0.38, Muscle.CORE: 0.22
    }, [Machine.CABLE]),
    "Pike Push-ups (vertical press)": ([DayCategory.UPPER_GYM, DayCategory.UPPER_HOME], {
        Muscle.ANT_DELTOID: 0.72, Muscle.TRICEPS: 0.34, Muscle.CORE: 0.25
    }, []),
    "Lateral Raise (cable/band)": ([DayCategory.UPPER_GYM, DayCategory.UPPER_HOME], {
        Muscle.LAT_DELTOID: 0.92, Muscle.ANT_DELTOID: 0.15
    }, [Machine.CABLE]),
    "Biceps Curl (cable/band)": ([DayCategory.UPPER_GYM, DayCategory.UPPER_HOME], {
        Muscle.BICEPS: 0.92, Muscle.FOREARMS: 0.30
    }, [Machine.CABLE]),
    "Hammer Curl (cable/band)": ([DayCategory.UPPER_GYM, DayCategory.UPPER_HOME], {
        Muscle.BICEPS: 0.45, Muscle.FOREARMS: 0.92
    }, [Machine.CABLE]),
    "Tricep Kickback (cable/band)": ([DayCategory.UPPER_GYM, DayCategory.UPPER_HOME], {
        Muscle.TRICEPS: 0.90
    }, [Machine.CABLE]),
    "Overhead Triceps Extensions (cable/band)": ([DayCategory.UPPER_GYM, DayCategory.UPPER_HOME], {
        Muscle.TRICEPS: 0.90
    }, [Machine.CABLE]),
    "Band Shrug / Cable Shrug": ([DayCategory.UPPER_GYM, DayCategory.UPPER_HOME], {
        Muscle.NECK: 0.90, Muscle.UPPER_BACK: 0.40
    }, []),

    # Both-category exercises
    "Side Plank High Pull (cable/band)": ([DayCategory.UPPER_GYM, DayCategory.LOWER_GYM, DayCategory.UPPER_HOME, DayCategory.LOWER_HOME], {
        Muscle.OBLIQUES: 0.92, Muscle.LATS: 0.30, Muscle.UPPER_BACK: 0.30, Muscle.ANT_DELTOID: 0.18
    }, [Machine.CABLE]),
    "Glute Bridge + Band Pull-Apart": ([DayCategory.LOWER_GYM, DayCategory.LOWER_HOME], {
        Muscle.GLUTES: 0.92, Muscle.HAMSTRINGS: 0.30, Muscle.POST_DELTOID: 0.30, Muscle.ERECTORS: 0.28
    }, []),
    "Pallof Press (cable/band)": ([DayCategory.LOWER_GYM, DayCategory.LOWER_HOME], {
        Muscle.CORE: 0.92, Muscle.OBLIQUES: 0.35
    }, [Machine.CABLE]),

    # Lower exercises (machine: only gym, cable/bodyweight: both gym and home)
    "Leg Press": ([DayCategory.LOWER_GYM], {
        Muscle.QUADS: 0.95, Muscle.GLUTES: 0.45, Muscle.CORE: 0.28, Muscle.HAMSTRINGS: 0.15
    }, [Machine.LEG_PRESS]),
    "Leg Press (sumo/wide)": ([DayCategory.LOWER_GYM], {
        Muscle.ADDUCTORS: 0.65, Muscle.GLUTES: 0.70, Muscle.QUADS: 0.45
    }, [Machine.LEG_PRESS]),
    "Seated Leg Curl": ([DayCategory.LOWER_GYM], {
        Muscle.HAMSTRINGS: 0.95
    }, [Machine.LEG_CURL]),
    "Cable Pull-Through": ([DayCategory.LOWER_GYM, DayCategory.LOWER_HOME], {
        Muscle.GLUTES: 0.92, Muscle.HAMSTRINGS: 0.30, Muscle.ERECTORS: 0.28
    }, [Machine.CABLE]),
    "Mini-Band Lateral Walk": ([DayCategory.LOWER_GYM, DayCategory.LOWER_HOME], {
        Muscle.GLUTES: 0.80, Muscle.ABDUCTORS: 0.70
    }, []),
    "Calf Raise": ([DayCategory.LOWER_GYM], {
        Muscle.CALVES: 0.95
    }, [Machine.LEG_PRESS]),
    "Cable Woodchopper / Chop": ([DayCategory.LOWER_GYM, DayCategory.LOWER_HOME], {
        Muscle.OBLIQUES: 0.92, Muscle.CORE: 0.30
    }, [Machine.CABLE]),
    "Good Morning (cable/band)": ([DayCategory.LOWER_GYM, DayCategory.LOWER_HOME], {
        Muscle.ERECTORS: 0.90, Muscle.GLUTES: 0.25, Muscle.HAMSTRINGS: 0.20
    }, [Machine.CABLE]),

    # Newly added abductors-focused exercises
    "Banded Monster Walk": ([DayCategory.LOWER_GYM, DayCategory.LOWER_HOME], {
        Muscle.ABDUCTORS: 0.85, Muscle.GLUTES: 0.60
    }, []),

    "Band Supine Hip Abduction": ([DayCategory.LOWER_GYM, DayCategory.LOWER_HOME], {
        Muscle.ABDUCTORS: 0.92, Muscle.GLUTES: 0.35, Muscle.CORE: 0.25
    }, []),

    "Banded front squat": ([DayCategory.LOWER_HOME], {
        Muscle.QUADS: 0.70, Muscle.GLUTES: 0.45, Muscle.HAMSTRINGS: 0.20, Muscle.CORE: 0.20, Muscle.ERECTORS: 0.20
    }, []),

    "Banded front squat (sumo/wide)": ([DayCategory.LOWER_HOME], {
        Muscle.ADDUCTORS: 0.50, Muscle.GLUTES: 0.50, Muscle.QUADS: 0.35, Muscle.HAMSTRINGS: 0.20, Muscle.ERECTORS: 0.20
    }, []),
}

# Removed exercises (for reference, previously removed from main EXERCISES dict)
REMOVED_EXERCISES: ExerciseDict = {
    "Close-Grip Press": ([DayCategory.UPPER_GYM], {
        Muscle.TRICEPS: 0.62, Muscle.CHEST: 0.30, Muscle.ANT_DELTOID: 0.20
    }, [Machine.CHEST_PRESS]),
    "Dead Bug (band)": ([DayCategory.UPPER_GYM, DayCategory.LOWER_GYM, DayCategory.UPPER_HOME, DayCategory.LOWER_HOME], {
        Muscle.CORE: 0.90,
        Muscle.OBLIQUES: 0.85,
        Muscle.LAT_DELTOID: 0.20
    }, [Machine.CABLE]),
    "RDL (band) - double-leg": ([DayCategory.LOWER_GYM, DayCategory.LOWER_HOME], {
        Muscle.HAMSTRINGS: 0.92,
        Muscle.GLUTES: 0.88,
        Muscle.ERECTORS: 0.80,
        Muscle.CORE: 0.25
    }, []),
    "Chest-Supported Rear Delt Row": ([DayCategory.UPPER_GYM], {
        Muscle.UPPER_BACK: 0.85,
        Muscle.POST_DELTOID: 0.90,
        Muscle.BICEPS: 0.35
    }, [Machine.SEATED_ROW]),
    "Upright Cable Row": ([DayCategory.UPPER_GYM, DayCategory.UPPER_HOME], {
        Muscle.POST_DELTOID: 0.85,
        Muscle.NECK: 0.80,
        Muscle.UPPER_BACK: 0.20
    }, [Machine.CABLE]),
    "Copenhagen Plank (adductor focus)": ([DayCategory.LOWER_GYM, DayCategory.LOWER_HOME], {
        Muscle.ADDUCTORS: 0.92,
        Muscle.CORE: 0.25,
        Muscle.GLUTES: 0.20
    }, []),
    "Cable Standing Hip Abduction": ([DayCategory.LOWER_GYM, DayCategory.LOWER_HOME], {
        Muscle.ABDUCTORS: 0.90,
        Muscle.GLUTES: 0.30
    }, [Machine.CABLE]),
}

EXERCISE_NAMES: List[ExerciseName] = list(EXERCISES.keys())
E: int = len(EXERCISE_NAMES)
M: int = len(Muscle)

# -----------------------
# Helpers: vectors, overlap, allowed-in-category
# -----------------------
def safe_value(var: pulp.LpVariable, default: float = 0.0) -> float:
    """Safely extract value from LpVariable, return default if None"""
    val = pulp.value(var)
    if val is not None and not isinstance(val, pulp.LpVariable):
        return float(val)
    return default

def exercise_vector(name: ExerciseName) -> ExerciseVector:
    vec = [0.0]*M
    categories, acts, machines = EXERCISES[name]
    for m, val in acts.items():
        if val >= 0.1:
            vec[MUSCLE_INDEX[m]] = float(val)
    return vec

def get_exercise_machines(exercise_name: ExerciseName) -> MachineList:
    """Return list of machines used by an exercise"""
    categories, acts, machines = EXERCISES[exercise_name]
    return machines

def has_machine_conflict(ex1: ExerciseName, ex2: ExerciseName) -> bool:
    """Check if two exercises share any machines"""
    machines1 = get_exercise_machines(ex1)
    machines2 = get_exercise_machines(ex2)
    return bool(set(machines1) & set(machines2))

VEC: ExerciseMatrix = [exercise_vector(n) for n in EXERCISE_NAMES]
def dot(a: ExerciseVector, b: ExerciseVector) -> float:
    return sum(x*y for x,y in zip(a,b))
W: ExerciseMatrix = [[dot(VEC[i], VEC[j]) for j in range(E)] for i in range(E)]

def allowed_in_category(ex_name: str, cat: DayCategory) -> bool:
    return cat in EXERCISES[ex_name][0]

# -----------------------
# Assignment ILP Helper
# -----------------------
def assign_pairs_to_days(pairs_list: ExercisePairs, category_name: str, num_days: int, pairs_per_day: int) -> DayAssignments:
    """
    Solve ILP to assign pairs to days with constraints.
    pairs_list: list of (ex1, ex2) tuples
    category_name: 'Upper' or 'Lower'
    num_days: number of days to assign to
    pairs_per_day: number of pairs per day
    """
    if not pairs_list:
        return {}

    P = len(pairs_list)
    if P != num_days * pairs_per_day:
        raise ValueError(f"Number of pairs {P} does not match num_days * pairs_per_day = {num_days * pairs_per_day}")

    # Precompute conflicts
    pair_sets = [set(pair) for pair in pairs_list]
    conflicts = {p: [] for p in range(P)}
    for p1 in range(P):
        for p2 in range(p1 + 1, P):
            if pair_sets[p1] & pair_sets[p2]:
                conflicts[p1].append(p2)
                conflicts[p2].append(p1)

    # ILP
    assign_prob = pulp.LpProblem(f"{category_name.lower()}_assignment", pulp.LpMinimize)
    x = [[pulp.LpVariable(f"x_{p}_{d}", cat='Binary') for d in range(num_days)] for p in range(P)]
    slack_conflicts = {}

    for p in range(P):
        assign_prob += pulp.lpSum(x[p][d] for d in range(num_days)) == 1, f"assign_pair_{p}"

    for d in range(num_days):
        assign_prob += pulp.lpSum(x[p][d] for p in range(P)) == pairs_per_day, f"day_capacity_{d}"

    # Relaxed conflicts
    for p1 in range(P):
        for p2 in range(p1 + 1, P):
            if p2 in conflicts[p1]:
                for d in range(num_days):
                    slack_var = pulp.LpVariable(f"slack_conf_{p1}_{p2}_{d}", lowBound=0, cat='Continuous')
                    slack_conflicts[(p1,p2,d)] = slack_var
                    assign_prob += x[p1][d] + x[p2][d] <= 1 + slack_var, f"conflict_{p1}_{p2}_{d}"

    assign_prob.setObjective(pulp.lpSum(slack_conflicts.values()))

    # Solve
    solver = pulp.PULP_CBC_CMD(msg=False)
    assign_prob.solve(solver)
    status = pulp.LpStatus[assign_prob.status]

    if status not in ["Optimal", "Feasible"]:
        print(f"{category_name} assignment failed.")
        return {}

    # Extract
    assignments = {f"Day {d}": [] for d in range(num_days)}
    for p in range(P):
        for d in range(num_days):
            if safe_value(x[p][d]) > 0.5:
                assignments[f"Day {d}"].append(pairs_list[p])
                break

    total_violations = sum(pulp.value(v) for v in slack_conflicts.values())
    if total_violations > 0:
        print(f"Assignment allows {total_violations} shared exercises; use with caution.")
    else:
        print("Perfect conflict-free assignment.")

    return assignments


# -----------------------
# Combined ILP Solver
# -----------------------
def solve_muscle_coverage() -> Tuple[str, Dict[DayCategory, ExerciseCounts], Dict[DayCategory, ExercisePairs],
                                    CoverageDict, float]:
    """
    Build and solve the ILP for muscle coverage optimization.

    Returns:
        status: Solver status ('Optimal', 'Feasible', etc.)
        counts_dict: Exercise counts per category
        pairs_dict: Expanded superset pairs per category
        coverage: Muscle coverage vs targets
        total_shortfall: Total shortfall sum
    """
    prob: pulp.LpProblem = pulp.LpProblem("muscle_coverage_solver", pulp.LpMinimize)

    # Define categories to process
    categories = list(DayCategory)

    # Exercise count variables per category
    c: Dict[DayCategory, LpVariableDict] = {}
    for cat in categories:
        max_usage = get_max_usage_for_category(cat)
        c[cat] = {e: pulp.LpVariable(f"c_{cat.name.lower()}_{e}", lowBound=0, upBound=min(DAY_REQUIREMENTS[cat], max_usage), cat='Integer') for e in range(E)}

    # Pair variables per category
    p: Dict[DayCategory, LpVariableDict] = {cat: {} for cat in categories}
    for cat in categories:
        for i in range(E):
            for j in range(i, E):
                # Check muscle overlap
                muscle_overlap_ok = W[i][j] <= THRESHOLD + 1e-9

                # Check machine conflicts
                ex1_name = EXERCISE_NAMES[i]
                ex2_name = EXERCISE_NAMES[j]
                machine_conflict = has_machine_conflict(ex1_name, ex2_name)

                # Only allow pairing if both conditions are met
                if muscle_overlap_ok and not machine_conflict and allowed_in_category(EXERCISE_NAMES[i], cat) and allowed_in_category(EXERCISE_NAMES[j], cat):
                    p[cat][(i,j)] = pulp.LpVariable(f"p_{cat.name.lower()}_{i}_{j}", lowBound=0, upBound=min(PAIRS_PER_CATEGORY[cat], get_max_usage_for_category(cat)), cat='Integer')

    s: LpVariableDict = {m_idx: pulp.LpVariable(f"s_{m_idx}", lowBound=0, cat='Continuous') for m_idx in range(M)}

    # counts constraints per category
    for cat in categories:
        prob += pulp.lpSum(c[cat][e] for e in range(E)) == DAY_REQUIREMENTS[cat], f"total_{cat.name.lower()}_instances"

    # linking counts to pairs per category
    for cat in categories:
        for e in range(E):
            terms = []
            if (e,e) in p[cat]: terms.append(2 * p[cat][(e,e)])
            for f in range(0,e):
                if (f,e) in p[cat]: terms.append(p[cat][(f,e)])
            for f in range(e+1,E):
                if (e,f) in p[cat]: terms.append(p[cat][(e,f)])
            prob += c[cat][e] == pulp.lpSum(terms), f"link_{cat.name.lower()}_{e}"

    # total pairs constraints per category
    for cat in categories:
        prob += pulp.lpSum(p[cat].values()) == PAIRS_PER_CATEGORY[cat], f"total_{cat.name.lower()}_pairs"

    # coverage & shortfall: use SETS_PER_INSTANCE variable, sum over all categories
    for m_idx, m in enumerate(Muscle):
        coverage_expr = SETS_PER_INSTANCE * pulp.lpSum( c[cat][e] * VEC[e][m_idx] for cat in categories for e in range(E) )
        prob += s[m_idx] >= MUSCLE_TARGETS[m] - coverage_expr, f"shortfall_{m_idx}"

    prob += pulp.lpSum(s[m_idx] for m_idx in range(M)), "min_total_shortfall"

    # Solve
    solver = pulp.PULP_CBC_CMD(msg=False)
    prob.solve(solver)

    status: str = pulp.LpStatus[prob.status]

    if status not in ("Optimal", "Feasible"):
        # Return empty dicts for infeasible case (but type says no Optional, assume always succeeds for now)
        empty_counts = {cat: {} for cat in categories}
        empty_pairs = {cat: [] for cat in categories}
        return status, empty_counts, empty_pairs, {}, 0.0

    # Build results per category
    counts_dict: Dict[DayCategory, ExerciseCounts] = {}
    pairs_dict: Dict[DayCategory, ExercisePairs] = {}

    for cat in categories:
        counts_dict[cat] = {EXERCISE_NAMES[e]: int(safe_value(c[cat][e])) for e in range(E) if safe_value(c[cat][e]) > 0}
        pairs_dict[cat] = []
        for (i,j), var in p[cat].items():
            q = int(safe_value(var))
            pairs_dict[cat].extend( [(EXERCISE_NAMES[i], EXERCISE_NAMES[j])] * q )

    # Coverage calculation sum over all categories
    coverage: CoverageDict = {}
    for m_idx, m in enumerate(Muscle):
        cov = SETS_PER_INSTANCE * sum( int(safe_value(c[cat][e])) * VEC[e][m_idx] for cat in categories for e in range(E) )
        coverage[m] = cov

    total_shortfall: float = sum(max(0.0, MUSCLE_TARGETS[m] - coverage[m]) for m in Muscle)

    return status, counts_dict, pairs_dict, coverage, total_shortfall


# -----------------------
# Run solver and assign pairs to days
# -----------------------
result = solve_muscle_coverage()

status = result[0]
print("Solver status:", status)

if status not in ("Optimal", "Feasible"):
    print("No feasible solution found.")
else:
    # Unpack the successful results
    status, counts_dict, pairs_dict, coverage, total_shortfall = result

    print("\n=== COUNTS ===")
    for cat in counts_dict:
        print(f"{cat.name.replace('_', ' ')} counts ({DAY_REQUIREMENTS[cat]} total):")
        for k,v in sorted(counts_dict[cat].items(), key=lambda x:-x[1]):
            print(f"  {k:40s} : {v}")
        print()

    print("\n=== EXPANDED PAIRS ===")
    for cat in pairs_dict:
        print(f"{cat.name.replace('_', ' ')} expanded pairs ({PAIRS_PER_CATEGORY[cat]}):")
        for i,pair in enumerate(pairs_dict[cat], start=1):
            print(f" Pair {i:2d}: {pair[0]}  +  {pair[1]}")
        print()

    print("\n=== COVERAGE vs TARGETS (sets/week) ===")
    for m in Muscle:
        print(f"  {m.name:20s} target {MUSCLE_TARGETS[m]:4.1f}   covered {coverage[m]:6.2f}   diff {coverage[m]-MUSCLE_TARGETS[m]:6.2f}")

    print(f"\nTotal shortfall sum = {total_shortfall:.3f}")

    print(f"\nNote: SETS_PER_INSTANCE = {SETS_PER_INSTANCE}, THRESHOLD = {THRESHOLD}")

    # ---------------------------  
    # Assignment ILP: Assign pairs to days per category
    # ---------------------------  
    assignments = {}
    for cat in pairs_dict:
        if pairs_dict[cat]:
            category_name = cat.name.lower().replace('_', ' ')
            num_days = DAYS_PER_CATEGORY[cat]
            pairs_per_day = PAIRS_PER_DAY[cat]
            assignments[cat] = assign_pairs_to_days(pairs_dict[cat], category_name, num_days, pairs_per_day)

    print("\n=== ASSIGNMENT ===\n")
    print("## Workout Plan")
    print()

    for cat in assignments:
        if assignments[cat]:
            cat_name = cat.name.replace('_', ' ')
            # Assuming consistent pairs_per_day for the category
            first_day_pairs = list(assignments[cat].values())[0]
            pairs_per_day = len(first_day_pairs)
            day_names = [str(i + 1) for i in range(len(assignments[cat]))]

            print(f"### {cat_name} Days:")
            header = "| Workout Type | " + " | ".join(f"Superset {j+1}" for j in range(pairs_per_day)) + " |"
            print(header)
            print("|" + "|".join(["---"] * (pairs_per_day + 1)) + "|")
            for i, (k, pairs) in enumerate(assignments[cat].items()):
                day_label = f"{cat_name} {day_names[i]}"
                supersets = [f"{pair[0]}<br>{pair[1]}" for pair in pairs]
                row = f"| {day_label} | " + " | ".join(supersets) + " |"
                print(row)
            print()
