import pulp
from enum import Enum, auto
from typing import Dict, List, Tuple, Optional, Union, Any, cast
import json


# -----------------------
# Enums
# -----------------------
class Muscle(Enum):
    # Pectoral complex
    PEC_CLAVICULAR = auto()     # upper / clavicular head of pec major
    PEC_STERNAL = auto()        # sternal (mid/lower) head of pec major

    # Scapular protractors / stabilizers
    SERRATUS_ANTERIOR = auto()
    PECTORAL_MINOR = auto()     # rarely used directly but included for completeness

    # Trapezius / upper-back & scapular retractors
    TRAP_UPPER = auto()
    TRAP_MIDDLE = auto()
    TRAP_LOWER = auto()
    RHOMBOIDS = auto()
    LEVATOR_SCAPULAE = auto()

    # Rotator cuff & adjacent stabilizers (important for posterior shoulder work)
    SUPRASPINATUS = auto()
    INFRASPINATUS = auto()
    TERES_MINOR = auto()
    SUBSCAPULARIS = auto()

    # Large arm movers
    LATS = auto()
    TERES_MAJOR = auto()
    ANT_DELTOID = auto()
    LAT_DELTOID = auto()        # middle deltoid
    POST_DELTOID = auto()

    # Elbow flexors / forearm
    BICEPS_LONG = auto()
    BICEPS_SHORT = auto()
    BRACHIALIS = auto()
    BRACHIORADIALIS = auto()
    FOREARM_FLEXORS = auto()
    FOREARM_EXTENSORS = auto()

    # Triceps heads
    TRICEPS_LONG = auto()
    TRICEPS_LATERAL = auto()
    TRICEPS_MEDIAL = auto()

    # Thigh / knee extensors
    RECTUS_FEMORIS = auto()
    VASTUS_LATERALIS = auto()
    VASTUS_MEDIALIS = auto()
    VASTUS_INTERMEDIUS = auto()

    # Hamstrings (split)
    HAM_BICEPS_FEMORIS = auto()
    HAM_SEMITENDINOSUS = auto()
    HAM_SEMIMEMBRANOSUS = auto()

    # Hip / gluteal complex
    GLUTE_MAX = auto()
    GLUTE_MED = auto()
    GLUTE_MIN = auto()
    TENSOR_FASCIAE_LATAE = auto()

    # Hip adductors group (split)
    ADDUCTOR_MAGNUS = auto()
    ADDUCTOR_LONGUS = auto()
    GRACILIS = auto()

    # Calf / plantarflexors
    GASTROC_MED = auto()
    GASTROC_LAT = auto()
    SOLEUS = auto()

    # Ankle dorsiflexor
    TIBIALIS_ANTERIOR = auto()

    # Core (split)
    RECTUS_ABDOMINIS = auto()
    EXTERNAL_OBLIQUE = auto()
    INTERNAL_OBLIQUE = auto()
    TRANSVERSUS_ABDOMINIS = auto()
    ERECTOR_SPINAE = auto()

    # Neck (kept as general)
    NECK = auto()

    # Generic / fallback (if you still want aggregated groups)
    # NOTE: keep these only if your solver expects them; otherwise remove.
    # FOREARMS_GENERIC = auto()
    # QUADS_GENERIC = auto()


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
# Load config
# -----------------------
# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

# Parse tunables
SETS_PER_INSTANCE: Dict[DayCategory, float] = {
    DayCategory[cat]: val
    for cat, val in config["sets_per_instance"].items()
}
THRESHOLD: float = config["threshold"]
DEVIATION_SUM_WEIGHT: float = config["deviation_sum_weight"]
PAIRS_PER_DAY = {
    DayCategory[cat]: val
    for cat, val in config["supersets_per_day"].items()
}
DAYS_PER_CATEGORY = {
    DayCategory[cat]: val
    for cat, val in config["days_per_category"].items()
}
PAIRS_PER_CATEGORY = {cat: PAIRS_PER_DAY[cat] * DAYS_PER_CATEGORY[cat] for cat in PAIRS_PER_DAY}
DAY_REQUIREMENTS = {cat: PAIRS_PER_CATEGORY[cat] * 2 for cat in PAIRS_PER_CATEGORY}


def get_max_usage_for_category(cat: DayCategory) -> int:
    """Get the maximum times an exercise can be used in the given category"""
    return DAYS_PER_CATEGORY[cat]


# -----------------------
# Targets
# -----------------------
MUSCLE_TARGETS: MuscleTargetDict = {
    Muscle[muscle]: target
    for muscle, target in config["muscle_targets"].items()
}

EXERCISES: ExerciseDict = {}
for name, (cat_list, act_dict, mach_list) in config["exercises"].items():
    categories = [DayCategory[cat] for cat in cat_list]
    activations: Dict[Muscle, float] = {
        Muscle[m]: val
        for m, val in act_dict.items()
    }
    machines = [Machine[m] for m in mach_list] if mach_list else []
    EXERCISES[name] = (categories, activations, machines)



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
    vec = [0.0] * M
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
    return sum(x * y for x, y in zip(a, b))


W: ExerciseMatrix = [[dot(VEC[i], VEC[j]) for j in range(E)] for i in range(E)]


def allowed_in_category(ex_name: str, cat: DayCategory) -> bool:
    return cat in EXERCISES[ex_name][0]


# -----------------------
# Assignment ILP Helper
# -----------------------
def assign_pairs_to_days(
    pairs_list: ExercisePairs, category_name: str, num_days: int, pairs_per_day: int
) -> DayAssignments:
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
        raise ValueError(
            f"Number of pairs {P} does not match num_days * pairs_per_day = {num_days * pairs_per_day}"
        )

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
    x = [
        [pulp.LpVariable(f"x_{p}_{d}", cat="Binary") for d in range(num_days)]
        for p in range(P)
    ]
    slack_conflicts = {}

    for p in range(P):
        assign_prob += (
            pulp.lpSum(x[p][d] for d in range(num_days)) == 1,
            f"assign_pair_{p}",
        )

    for d in range(num_days):
        assign_prob += (
            pulp.lpSum(x[p][d] for p in range(P)) == pairs_per_day,
            f"day_capacity_{d}",
        )

    # Relaxed conflicts
    for p1 in range(P):
        for p2 in range(p1 + 1, P):
            if p2 in conflicts[p1]:
                for d in range(num_days):
                    slack_var = pulp.LpVariable(
                        f"slack_conf_{p1}_{p2}_{d}", lowBound=0, cat="Continuous"
                    )
                    slack_conflicts[(p1, p2, d)] = slack_var
                    assign_prob += (
                        x[p1][d] + x[p2][d] <= 1 + slack_var,
                        f"conflict_{p1}_{p2}_{d}",
                    )

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
        print(
            f"Assignment allows {total_violations} shared exercises; use with caution."
        )
    else:
        print("Perfect conflict-free assignment.")

    return assignments


# -----------------------
# Combined ILP Solver
# -----------------------
def solve_muscle_coverage() -> Tuple[
    str,
    Dict[DayCategory, ExerciseCounts],
    Dict[DayCategory, ExercisePairs],
    CoverageDict,
    float,
    float,
    float,
]:
    """
    Build and solve the ILP for muscle coverage with mixed-objective minimization.
    Minimizes weighted sum of percentage deviations plus maximum deviation across muscles.

    Returns:
        status: Solver status ('Optimal', 'Feasible', etc.)
        counts_dict: Exercise counts per category
        pairs_dict: Expanded superset pairs per category
        coverage: Muscle coverage vs targets
        total_deviation_sum: Sum of all percentage deviations
        max_deviation: Maximum percentage deviation (worst muscle)
        objective_value: Minimized objective value (weighted sum + max dev)
    """
    prob: pulp.LpProblem = pulp.LpProblem("muscle_coverage_solver", pulp.LpMinimize)

    # Define categories to process
    categories = list(DayCategory)

    # Exercise count variables per category
    c: Dict[DayCategory, LpVariableDict] = {}
    for cat in categories:
        max_usage = get_max_usage_for_category(cat)
        c[cat] = {
            e: pulp.LpVariable(
                f"c_{cat.name.lower()}_{e}",
                lowBound=0,
                upBound=min(DAY_REQUIREMENTS[cat], max_usage),
                cat="Integer",
            )
            for e in range(E)
        }

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
                if (
                    muscle_overlap_ok
                    and not machine_conflict
                    and allowed_in_category(EXERCISE_NAMES[i], cat)
                    and allowed_in_category(EXERCISE_NAMES[j], cat)
                ):
                    p[cat][(i, j)] = pulp.LpVariable(
                        f"p_{cat.name.lower()}_{i}_{j}",
                        lowBound=0,
                        upBound=min(
                            PAIRS_PER_CATEGORY[cat], get_max_usage_for_category(cat)
                        ),
                        cat="Integer",
                    )

    # Dummy objective for feasibility check
    dummy_obj = pulp.LpVariable("dummy", lowBound=0, cat="Continuous")

    # counts constraints per category
    for cat in categories:
        prob += (
            pulp.lpSum(c[cat][e] for e in range(E)) == DAY_REQUIREMENTS[cat],
            f"total_{cat.name.lower()}_instances",
        )

    # linking counts to pairs per category
    for cat in categories:
        for e in range(E):
            terms = []
            if (e, e) in p[cat]:
                terms.append(2 * p[cat][(e, e)])
            for f in range(0, e):
                if (f, e) in p[cat]:
                    terms.append(p[cat][(f, e)])
            for f in range(e + 1, E):
                if (e, f) in p[cat]:
                    terms.append(p[cat][(e, f)])
            prob += c[cat][e] == pulp.lpSum(terms), f"link_{cat.name.lower()}_{e}"

    # total pairs constraints per category
    for cat in categories:
        prob += (
            pulp.lpSum(p[cat].values()) == PAIRS_PER_CATEGORY[cat],
            f"total_{cat.name.lower()}_pairs",
        )

    # Percentage deviation constraints - minimize sum of percentage deviations from targets
    overshoot_deviations = {}
    undershoot_deviations = {}

    # Variable for maximum deviation
    max_dev_pct_slack = pulp.LpVariable("max_dev_pct_slack", lowBound=0, cat="Continuous")

    for m_idx, m in enumerate(Muscle):
        if MUSCLE_TARGETS[m] > 0:
            coverage_expr = pulp.lpSum(
                SETS_PER_INSTANCE[cat] * c[cat][e] * VEC[e][m_idx]
                for cat in categories for e in range(E)
            )
            target = MUSCLE_TARGETS[m]

            # Slack variables for overshoot and undershoot percentages
            over_pct_slack = pulp.LpVariable(f"over_pct_{m.name}", lowBound=0, cat="Continuous")
            under_pct_slack = pulp.LpVariable(f"under_pct_{m.name}", lowBound=0, cat="Continuous")

            overshoot_deviations[m] = over_pct_slack
            undershoot_deviations[m] = under_pct_slack

            # Constraints allowing deviation
            prob += (coverage_expr <= target + (over_pct_slack / 100) * target, f"over_dev_{m.name}")
            prob += (coverage_expr >= target - (under_pct_slack / 100) * target, f"under_dev_{m.name}")

            # Constraints for max deviation
            prob += (max_dev_pct_slack >= over_pct_slack, f"max_over_{m.name}")
            prob += (max_dev_pct_slack >= under_pct_slack, f"max_under_{m.name}")

    # Objective: minimize weighted sum of deviations plus max deviation
    dev_sum_expr = pulp.lpSum(overshoot_deviations.values()) + pulp.lpSum(undershoot_deviations.values())
    prob.setObjective(DEVIATION_SUM_WEIGHT * dev_sum_expr + max_dev_pct_slack)



    # Solve
    solver = pulp.PULP_CBC_CMD(msg=False)
    prob.solve(solver)

    status: str = pulp.LpStatus[prob.status]

    if status not in ("Optimal", "Feasible"):
        # Return empty dicts for infeasible case (but type says no Optional, assume always succeeds for now)
        empty_counts = {cat: {} for cat in categories}
        empty_pairs = {cat: [] for cat in categories}
        return status, empty_counts, empty_pairs, {}, 0.0, 0.0, 0.0

    # Build results per category
    counts_dict: Dict[DayCategory, ExerciseCounts] = {}
    pairs_dict: Dict[DayCategory, ExercisePairs] = {}

    for cat in categories:
        counts_dict[cat] = {
            EXERCISE_NAMES[e]: int(safe_value(c[cat][e]))
            for e in range(E)
            if safe_value(c[cat][e]) > 0
        }
        pairs_dict[cat] = []
        for (i, j), var in p[cat].items():
            q = int(safe_value(var))
            pairs_dict[cat].extend([(EXERCISE_NAMES[i], EXERCISE_NAMES[j])] * q)

    # Coverage calculation sum over all categories
    coverage: CoverageDict = {}
    for m_idx, m in enumerate(Muscle):
        cov = sum(
            SETS_PER_INSTANCE[cat] * int(safe_value(c[cat][e])) * VEC[e][m_idx]
            for cat in categories
            for e in range(E)
        )
        coverage[m] = cov

    # Calculate total sum of deviation percentages (this is the minimized objective)
    total_dev_pct_sum = sum(
        safe_value(overshoot_deviations[m]) + safe_value(undershoot_deviations[m])
        for m in overshoot_deviations
    )

    # Calculate maximum deviation percentage for any single muscle
    max_dev_pct = max(
        (coverage[m] - MUSCLE_TARGETS[m]) / MUSCLE_TARGETS[m] * 100
        for m in Muscle if MUSCLE_TARGETS[m] > 0
    ) if any(MUSCLE_TARGETS[m] > 0 for m in Muscle) else 0.0

    # Calculate objective value
    objective_value = safe_value(max_dev_pct_slack) + DEVIATION_SUM_WEIGHT * total_dev_pct_sum

    return status, counts_dict, pairs_dict, coverage, total_dev_pct_sum, max_dev_pct, objective_value


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
    status, counts_dict, pairs_dict, coverage, total_deviation_sum, max_deviation, objective_value = result

    print("\n=== COUNTS ===")
    for cat in counts_dict:
        supersets_per_day = PAIRS_PER_DAY[cat]
        days = DAYS_PER_CATEGORY[cat]
        total_instances = DAY_REQUIREMENTS[cat]
        total_supersets = PAIRS_PER_CATEGORY[cat]
        print(f"{cat.name.replace('_', ' ')} counts ({total_instances} instances, {total_supersets} supersets over {days} days at {supersets_per_day}/day):")
        for k, v in sorted(counts_dict[cat].items(), key=lambda x: -x[1]):
            print(f"  {k:40s} : {v}")
        print()

    print("\n=== EXPANDED PAIRS ===")
    for cat in pairs_dict:
        print(
            f"{cat.name.replace('_', ' ')} expanded pairs ({PAIRS_PER_CATEGORY[cat]} total supersets):"
        )
        for i, pair in enumerate(pairs_dict[cat], start=1):
            print(f" Pair {i:2d}: {pair[0]}  +  {pair[1]}")
        print()

    print("\n=== COVERAGE vs TARGETS (sets/week) ===")
    for m in Muscle:
        if MUSCLE_TARGETS[m] > 0:
            pct_dev = (coverage[m] - MUSCLE_TARGETS[m]) / MUSCLE_TARGETS[m] * 100
        else:
            pct_dev = 0.0
        print(
            f"  {m.name:20s} target {MUSCLE_TARGETS[m]:4.1f}   covered {coverage[m]:6.2f}   diff {coverage[m]-MUSCLE_TARGETS[m]:6.2f}   %dev {pct_dev:6.1f}%"
        )

    print(f"\nObjective = {DEVIATION_SUM_WEIGHT} * sum_devs({total_deviation_sum:.2f}%) + max_dev({max_deviation:.2f}%) = {objective_value:.2f}%")

    print(f"\nNote: THRESHOLD = {THRESHOLD}")
    print("SETS_PER_INSTANCE:")
    for cat, val in SETS_PER_INSTANCE.items():
        print(f"  {cat.name}: {val}")

    # ---------------------------
    # Assignment ILP: Assign pairs to days per category
    # ---------------------------
    assignments = {}
    for cat in pairs_dict:
        if pairs_dict[cat]:
            category_name = cat.name.lower()
            num_days = DAYS_PER_CATEGORY[cat]
            pairs_per_day = PAIRS_PER_DAY[cat]
            assignments[cat] = assign_pairs_to_days(
                pairs_dict[cat], category_name, num_days, pairs_per_day
            )

    print("\n=== ASSIGNMENT ===\n")
    print("## Workout Plan")
    print()

    for cat in assignments:
        if assignments[cat]:
            cat_name = cat.name.replace("_", " ")
            # Assuming consistent pairs_per_day for the category
            first_day_pairs = list(assignments[cat].values())[0]
            pairs_per_day = len(first_day_pairs)
            day_names = [str(i + 1) for i in range(len(assignments[cat]))]

            print(f"### {cat_name} Days:")
            header = (
                "| Workout Type | "
                + " | ".join(f"Superset {j+1}" for j in range(pairs_per_day))
                + " |"
            )
            print(header)
            print("|" + "|".join(["---"] * (pairs_per_day + 1)) + "|")
            for i, (k, pairs) in enumerate(assignments[cat].items()):
                day_label = f"{cat_name} {day_names[i]}"
                supersets = [f"{pair[0]}<br>{pair[1]}" for pair in pairs]
                row = f"| {day_label} | " + " | ".join(supersets) + " |"
                print(row)
            print()
