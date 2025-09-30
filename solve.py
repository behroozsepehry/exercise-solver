import pulp
from enum import Enum, auto

# -----------------------
# Tunables
# -----------------------
SETS_PER_INSTANCE = 4.6
REQ_UP = 12
REQ_LOW = 12
PAIRS_PER_CAT = REQ_UP // 2
THRESHOLD = 0.2

# -----------------------
# Muscles
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
    UPPER = auto()
    LOWER = auto()

MUSCLE_INDEX = {m: i for i, m in enumerate(Muscle)}

# -----------------------
# Targets: default sets/week (adjustable)
# -----------------------
MUSCLE_TARGETS = {
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

EXERCISES = {
    # Upper-only
    "Chest Press (machine/band)": ([DayCategory.UPPER], {
        Muscle.CHEST: 0.95, Muscle.ANT_DELTOID: 0.30, Muscle.TRICEPS: 0.40, Muscle.FOREARMS: 0.20
    }, [Machine.CHEST_PRESS]),
    "Push-ups (standard/incline/decline)": ([DayCategory.UPPER], {
        Muscle.CHEST: 0.88, Muscle.ANT_DELTOID: 0.25, Muscle.TRICEPS: 0.35, Muscle.CORE: 0.25
    }, []),
    "Cable / Band Chest Fly": ([DayCategory.UPPER], {
        Muscle.CHEST: 0.85, Muscle.ANT_DELTOID: 0.20
    }, [Machine.CABLE]),
    "Row (seated/band/all)": ([DayCategory.UPPER], {
        Muscle.UPPER_BACK: 0.92, Muscle.LATS: 0.42, Muscle.BICEPS: 0.36, Muscle.POST_DELTOID: 0.28
    }, [Machine.SEATED_ROW]),
    "Face Pull (band/cable)": ([DayCategory.UPPER], {
        Muscle.POST_DELTOID: 0.85, Muscle.UPPER_BACK: 0.40, Muscle.LATS: 0.15
    }, [Machine.CABLE]),
    "Lat Pulldown (machine)": ([DayCategory.UPPER], {
        Muscle.LATS: 0.93, Muscle.UPPER_BACK: 0.35, Muscle.BICEPS: 0.30
    }, [Machine.LAT_PULLDOWN]),
    "Overhead Press (cable/band)": ([DayCategory.UPPER], {
        Muscle.ANT_DELTOID: 0.82, Muscle.LAT_DELTOID: 0.36, Muscle.TRICEPS: 0.38, Muscle.CORE: 0.22
    }, [Machine.CABLE]),
    "Pike Push-ups (vertical press)": ([DayCategory.UPPER], {
        Muscle.ANT_DELTOID: 0.72, Muscle.TRICEPS: 0.34, Muscle.CORE: 0.25
    }, []),
    "Cable Lateral Raise": ([DayCategory.UPPER], {
        Muscle.LAT_DELTOID: 0.92, Muscle.ANT_DELTOID: 0.15
    }, [Machine.CABLE]),
    "Biceps Curl (band/cable)": ([DayCategory.UPPER], {
        Muscle.BICEPS: 0.92, Muscle.FOREARMS: 0.30
    }, [Machine.CABLE]),
    "Hammer / Neutral Curl": ([DayCategory.UPPER], {
        Muscle.BICEPS: 0.45, Muscle.FOREARMS: 0.92
    }, []),
    "Triceps (pushdown / overhead merged)": ([DayCategory.UPPER], {
        Muscle.TRICEPS: 0.92
    }, [Machine.CABLE]),
    "Close-Grip Press (machine/band)": ([DayCategory.UPPER], {
        Muscle.TRICEPS: 0.62, Muscle.CHEST: 0.30, Muscle.ANT_DELTOID: 0.20
    }, [Machine.CHEST_PRESS]),
    "Band Shrug / Cable Shrug": ([DayCategory.UPPER], {
        Muscle.NECK: 0.90, Muscle.UPPER_BACK: 0.30
    }, []),

    # Both-category
    "Side Plank High Pull (cable/band)": ([DayCategory.UPPER, DayCategory.LOWER], {
        Muscle.OBLIQUES: 0.92, Muscle.LATS: 0.30, Muscle.UPPER_BACK: 0.30, Muscle.ANT_DELTOID: 0.18
    }, [Machine.CABLE]),
    "Glute Bridge with abduction + Band Pull-Apart (combined)": ([DayCategory.LOWER], {
        Muscle.GLUTES: 0.82, Muscle.HAMSTRINGS: 0.28, Muscle.POST_DELTOID: 0.30, Muscle.ERECTORS: 0.25, Muscle.ABDUCTORS: 0.70
    }, []),
    "Pallof Press (band/cable)": ([DayCategory.LOWER], {
        Muscle.CORE: 0.92, Muscle.OBLIQUES: 0.35
    }, [Machine.CABLE]),

    # Lower-only (compound / efficient)
    "Leg Press / Front Squat (quad-dominant)": ([DayCategory.LOWER], {
        Muscle.QUADS: 0.95, Muscle.GLUTES: 0.45, Muscle.CORE: 0.28, Muscle.HAMSTRINGS: 0.15
    }, [Machine.LEG_PRESS]),
    "Leg Press (sumo/wide)": ([DayCategory.LOWER], {
        Muscle.ADDUCTORS: 0.65, Muscle.GLUTES: 0.70, Muscle.QUADS: 0.45
    }, [Machine.LEG_PRESS]),
    "Seated / Lying Leg Curl (machine)": ([DayCategory.LOWER], {
        Muscle.HAMSTRINGS: 0.95
    }, [Machine.LEG_CURL]),
    "Cable Pull-Through (both legs)": ([DayCategory.LOWER], {
        Muscle.GLUTES: 0.92, Muscle.HAMSTRINGS: 0.30, Muscle.ERECTORS: 0.28
    }, [Machine.CABLE]),
    "Mini-Band Lateral Walk (both legs)": ([DayCategory.LOWER], {
        Muscle.GLUTES: 0.80, Muscle.ABDUCTORS: 0.70
    }, []),
    "Calf Raise (leg press machine)": ([DayCategory.LOWER], {
        Muscle.CALVES: 0.95
    }, [Machine.LEG_PRESS]),
    "Cable Woodchopper / Chop": ([DayCategory.LOWER], {
        Muscle.OBLIQUES: 0.92, Muscle.CORE: 0.30
    }, [Machine.CABLE]),
    "Good Morning (band/cable)": ([DayCategory.LOWER], {
        Muscle.ERECTORS: 0.90, Muscle.GLUTES: 0.25, Muscle.HAMSTRINGS: 0.20
    }, [Machine.CABLE]),

    # Newly added abductors-focused exercises (compact set)
    "Banded Monster Walk (both legs)": ([DayCategory.LOWER], {
        Muscle.ABDUCTORS: 0.85, Muscle.GLUTES: 0.60
    }, []),
    "Cable Standing Hip Abduction (both legs)": ([DayCategory.LOWER], {
        Muscle.ABDUCTORS: 0.90, Muscle.GLUTES: 0.30
    }, [Machine.CABLE]),
    "Copenhagen Plank (adductor focus)": ([DayCategory.LOWER], {
        Muscle.ADDUCTORS: 0.92, Muscle.CORE: 0.25, Muscle.GLUTES: 0.20
    }, []),
    "Band Supine Hip Abduction": ([DayCategory.LOWER], {
        Muscle.ABDUCTORS: 0.92, Muscle.GLUTES: 0.35, Muscle.CORE: 0.25
    }, []),

    # Note: removed "Dead Bug", "RDL (band) - double-leg", "Chest-Supported Rear Delt Row", "Upright Cable Row"
}

EXERCISE_NAMES = list(EXERCISES.keys())
E = len(EXERCISE_NAMES)
M = len(Muscle)

# -----------------------
# Helpers: vectors, overlap, allowed-in-category
# -----------------------
def safe_value(var, default=0.0):
    """Safely extract value from LpVariable, return default if None"""
    val = pulp.value(var)
    return val if val is not None else default

def exercise_vector(name):
    vec = [0.0]*M
    categories, acts, machines = EXERCISES[name]
    for m, val in acts.items():
        if val >= 0.1:
            vec[MUSCLE_INDEX[m]] = float(val)
    return vec

def get_exercise_machines(exercise_name):
    """Return list of machines used by an exercise"""
    categories, acts, machines = EXERCISES[exercise_name]
    return machines

def has_machine_conflict(ex1, ex2):
    """Check if two exercises share any machines"""
    machines1 = get_exercise_machines(ex1)
    machines2 = get_exercise_machines(ex2)
    return bool(set(machines1) & set(machines2))

VEC = [exercise_vector(n) for n in EXERCISE_NAMES]
def dot(a,b): return sum(x*y for x,y in zip(a,b))
W = [[dot(VEC[i], VEC[j]) for j in range(E)] for i in range(E)]

def allowed_in_category(idx, cat):
    nm = EXERCISE_NAMES[idx]
    categories, acts, machines = EXERCISES[nm]
    return cat in categories

# -----------------------
# Assignment ILP Helper
# -----------------------
def assign_pairs_to_days(pairs_list, category_name):
    """
    Solve ILP to assign pairs to days with constraints.
    pairs_list: list of (ex1, ex2) tuples
    category_name: 'Upper' or 'Lower'
    """
    if not pairs_list:
        return {}

    P = len(pairs_list)
    D = 3
    if P != 6:
        print(f"Warning: {P} pairs for {category_name}, expected 6")

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
    x = [[pulp.LpVariable(f"x_{p}_{d}", cat='Binary') for d in range(D)] for p in range(P)]
    slack_conflicts = {}

    for p in range(P):
        assign_prob += pulp.lpSum(x[p][d] for d in range(D)) == 1, f"assign_pair_{p}"

    for d in range(D):
        assign_prob += pulp.lpSum(x[p][d] for p in range(P)) == 2, f"day_capacity_{d}"

    # Relaxed conflicts
    for p1 in range(P):
        for p2 in range(p1 + 1, P):
            if p2 in conflicts[p1]:
                for d in range(D):
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
    assignments = {f"Day {d}": [] for d in range(D)}
    for p in range(P):
        for d in range(D):
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
# Build combined ILP
# -----------------------
prob = pulp.LpProblem("combined_pairs_abductors_copenhagen", pulp.LpMinimize)

c_up = {e: pulp.LpVariable(f"c_up_{e}", lowBound=0, upBound=REQ_UP, cat='Integer') for e in range(E)}
c_low = {e: pulp.LpVariable(f"c_low_{e}", lowBound=0, upBound=REQ_LOW, cat='Integer') for e in range(E)}

MAX_PAIRS = REQ_UP // 2
p_up = {}
p_low = {}
for i in range(E):
    for j in range(i, E):
        # Check muscle overlap (existing)
        muscle_overlap_ok = W[i][j] <= THRESHOLD + 1e-9

        # Check machine conflicts (new)
        ex1_name = EXERCISE_NAMES[i]
        ex2_name = EXERCISE_NAMES[j]
        machine_conflict = has_machine_conflict(ex1_name, ex2_name)

        # Only allow pairing if both conditions are met
        if muscle_overlap_ok and not machine_conflict and allowed_in_category(i, DayCategory.UPPER) and allowed_in_category(j, DayCategory.UPPER):
            p_up[(i,j)] = pulp.LpVariable(f"p_up_{i}_{j}", lowBound=0, upBound=MAX_PAIRS, cat='Integer')
        if muscle_overlap_ok and not machine_conflict and allowed_in_category(i, DayCategory.LOWER) and allowed_in_category(j, DayCategory.LOWER):
            p_low[(i,j)] = pulp.LpVariable(f"p_low_{i}_{j}", lowBound=0, upBound=MAX_PAIRS, cat='Integer')

s = {m_idx: pulp.LpVariable(f"s_{m_idx}", lowBound=0, cat='Continuous') for m_idx in range(M)}

# counts constraints
prob += pulp.lpSum(c_up[e] for e in range(E)) == REQ_UP, "total_upper_instances"
prob += pulp.lpSum(c_low[e] for e in range(E)) == REQ_LOW, "total_lower_instances"

# linking counts to pairs
for e in range(E):
    terms = []
    if (e,e) in p_up: terms.append(2 * p_up[(e,e)])
    for f in range(0,e):
        if (f,e) in p_up: terms.append(p_up[(f,e)])
    for f in range(e+1,E):
        if (e,f) in p_up: terms.append(p_up[(e,f)])
    prob += c_up[e] == pulp.lpSum(terms), f"link_up_{e}"

for e in range(E):
    terms = []
    if (e,e) in p_low: terms.append(2 * p_low[(e,e)])
    for f in range(0,e):
        if (f,e) in p_low: terms.append(p_low[(f,e)])
    for f in range(e+1,E):
        if (e,f) in p_low: terms.append(p_low[(e,f)])
    prob += c_low[e] == pulp.lpSum(terms), f"link_low_{e}"

prob += pulp.lpSum(p_up.values()) == PAIRS_PER_CAT, "total_pairs_up"
prob += pulp.lpSum(p_low.values()) == PAIRS_PER_CAT, "total_pairs_low"

# coverage & shortfall: use SETS_PER_INSTANCE variable
for m_idx, m in enumerate(Muscle):
    coverage_expr = SETS_PER_INSTANCE * pulp.lpSum( (c_up[e] + c_low[e]) * VEC[e][m_idx] for e in range(E) )
    prob += s[m_idx] >= MUSCLE_TARGETS[m] - coverage_expr, f"shortfall_{m_idx}"

prob += pulp.lpSum(s[m_idx] for m_idx in range(M)), "min_total_shortfall"

# Solve
solver = pulp.PULP_CBC_CMD(msg=False)
prob.solve(solver)

# Print results once
status = pulp.LpStatus[prob.status]
print("Solver status:", status)

if status not in ("Optimal", "Feasible"):
    print("No feasible solution found.")
else:
    c_up_sol = {EXERCISE_NAMES[e]: int(safe_value(c_up[e])) for e in range(E) if safe_value(c_up[e]) > 0}
    c_low_sol = {EXERCISE_NAMES[e]: int(safe_value(c_low[e])) for e in range(E) if safe_value(c_low[e]) > 0}

    expanded_up_pairs = []
    for (i,j), var in p_up.items():
        q = int(safe_value(var))
        expanded_up_pairs.extend( [(EXERCISE_NAMES[i], EXERCISE_NAMES[j])] * q )

    expanded_low_pairs = []
    for (i,j), var in p_low.items():
        q = int(safe_value(var))
        expanded_low_pairs.extend( [(EXERCISE_NAMES[i], EXERCISE_NAMES[j])] * q )

    coverage = {}
    for m_idx, m in enumerate(Muscle):
        cov = SETS_PER_INSTANCE * sum( (int(safe_value(c_up[e])) + int(safe_value(c_low[e]))) * VEC[e][m_idx] for e in range(E) )
        coverage[m] = cov

    print("\n=== COUNTS ===")
    print("Upper counts (12 total):")
    for k,v in sorted(c_up_sol.items(), key=lambda x:-x[1]):
        print(f"  {k:40s} : {v}")
    print("\nLower counts (12 total):")
    for k,v in sorted(c_low_sol.items(), key=lambda x:-x[1]):
        print(f"  {k:40s} : {v}")

    print("\n=== EXPANDED PAIRS ===")
    print("Upper expanded pairs (6):")
    for i,pair in enumerate(expanded_up_pairs, start=1):
        print(f" Pair {i:2d}: {pair[0]}  +  {pair[1]}")
    print("Lower expanded pairs (6):")
    for i,pair in enumerate(expanded_low_pairs, start=1):
        print(f" Pair {i:2d}: {pair[0]}  +  {pair[1]}")

    print("\n=== COVERAGE vs TARGETS (sets/week) ===")
    for m in Muscle:
        print(f"  {m.name:20s} target {MUSCLE_TARGETS[m]:4.1f}   covered {coverage[m]:6.2f}   diff {coverage[m]-MUSCLE_TARGETS[m]:6.2f}")

    total_shortfall = sum(max(0.0, MUSCLE_TARGETS[m] - coverage[m]) for m in Muscle)
    print(f"\nTotal shortfall sum = {total_shortfall:.3f}")

    print(f"\nNote: SETS_PER_INSTANCE = {SETS_PER_INSTANCE}, THRESHOLD = {THRESHOLD}")

    # ---------------------------
    # Assignment ILP: Assign pairs to days
    # ---------------------------
    upper_assignments = assign_pairs_to_days(expanded_up_pairs, "Upper")
    lower_assignments = assign_pairs_to_days(expanded_low_pairs, "Lower")

    print("\n=== ASSIGNMENT ===\n")
    day_names = ["A", "B", "C"]
    print("## Workout Plan")
    print()

    print("### Upper Days:")
    print("| Workout Type | Superset 1 | Superset 2 |")
    print("|---|---|---|")
    for i, (k, pairs) in enumerate(upper_assignments.items()):
        day_label = f"Upper {day_names[i]}"
        sup1 = f"{pairs[0][0]}<br>{pairs[0][1]}"
        sup2 = f"{pairs[1][0]}<br>{pairs[1][1]}"
        print(f"| {day_label} | {sup1} | {sup2} |")
    print()

    print("### Lower Days:")
    print("| Workout Type | Superset 1 | Superset 2 |")
    print("|---|---|---|")
    for i, (k, pairs) in enumerate(lower_assignments.items()):
        day_label = f"Lower {day_names[i]}"
        sup1 = f"{pairs[0][0]}<br>{pairs[0][1]}"
        sup2 = f"{pairs[1][0]}<br>{pairs[1][1]}"
        print(f"| {day_label} | {sup1} | {sup2} |")
    print()
