import pulp
from enum import Enum, auto
from typing import Dict, List, Tuple, Optional, Union, Any, cast
import json


# -----------------------
# Enums
# -----------------------
class Muscle(Enum):
    # Pectoral complex
    PEC_CLAVICULAR = auto()  # upper / clavicular head of pec major
    PEC_STERNAL = auto()  # sternal (mid/lower) head of pec major

    # Scapular protractors / stabilizers
    SERRATUS_ANTERIOR = auto()
    PECTORAL_MINOR = auto()  # rarely used directly but included for completeness

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
    LAT_DELTOID = auto()  # middle deltoid
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

    # Neck (split into extensors and flexors)
    NECK_EXTENSORS = auto()
    NECK_FLEXORS = auto()


class Equipment(Enum):
    LEG_PRESS = auto()
    CHEST_PRESS = auto()
    LEG_CURL = auto()
    LAT_PULLDOWN = auto()
    SEATED_ROW = auto()
    CABLE = auto()
    BAND_LOW = auto()
    BAND_MED = auto()
    BAND_HIGH = auto()


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
EquipmentList = List[Equipment]
ExerciseData = Tuple[List[DayCategory], MuscleActivation, EquipmentList, int]
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
with open("config.json", "r") as f:
    config = json.load(f)

# Parse tunables
SETS_PER_INSTANCE: Dict[DayCategory, float] = {
    DayCategory[cat]: val for cat, val in config["sets_per_instance"].items()
}
THRESHOLD: float = config["threshold"]
DEVIATION_SUM_WEIGHT: float = config["deviation_sum_weight"]
UNDERSHOOT_WEIGHT_MULTIPLIER: float = config["undershoot_weight_multiplier"]
PAIRS_PER_DAY = {
    DayCategory[cat]: val for cat, val in config["supersets_per_day"].items()
}
DAYS_PER_CATEGORY = {
    DayCategory[cat]: val for cat, val in config["days_per_category"].items()
}
PAIRS_PER_CATEGORY = {
    cat: PAIRS_PER_DAY[cat] * DAYS_PER_CATEGORY[cat] for cat in PAIRS_PER_DAY
}
DAY_REQUIREMENTS = {cat: PAIRS_PER_CATEGORY[cat] * 2 for cat in PAIRS_PER_CATEGORY}


def get_max_usage_for_category(exercise_name: str, cat: DayCategory) -> int:
    """Get the maximum times an exercise can be used in the given category"""
    return min(DAYS_PER_CATEGORY[cat], EXERCISES[exercise_name][3])


# -----------------------
# Targets
# -----------------------
MUSCLE_TARGETS: MuscleTargetDict = {
    Muscle[muscle]: target for muscle, target in config["muscle_targets"].items()
}

EXERCISES: ExerciseDict = {}
for name, data in config["exercises"].items():
    cat_list = data["categories"]
    act_dict = data["activations"]
    equips_list = data["equipments"]
    limit = data["usage_limit_per_category"]
    categories = [DayCategory[cat] for cat in cat_list]
    activations: Dict[Muscle, float] = {Muscle[m]: val for m, val in act_dict.items()}
    equipment = [Equipment[m] for m in equips_list] if equips_list else []
    EXERCISES[name] = (categories, activations, equipment, limit)


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
    categories, acts, equipment, _ = EXERCISES[name]
    for m, val in acts.items():
        if val >= 0.1:
            vec[MUSCLE_INDEX[m]] = float(val)
    return vec


def get_exercise_equipment(exercise_name: ExerciseName) -> EquipmentList:
    """Return list of equipment used by an exercise"""
    categories, acts, equipment, _ = EXERCISES[exercise_name]
    return equipment


def has_equipment_conflict(ex1: ExerciseName, ex2: ExerciseName) -> bool:
    """Check if two exercises share any equipment"""
    equipment1 = get_exercise_equipment(ex1)
    equipment2 = get_exercise_equipment(ex2)
    return bool(set(equipment1) & set(equipment2))


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

    # Precompute pair sum vectors
    pair_sum_vecs: List[ExerciseVector] = []
    for p in range(P):
        ex1, ex2 = pairs_list[p]
        v1 = exercise_vector(ex1)
        v2 = exercise_vector(ex2)
        pair_sum_vecs.append([a + b for a, b in zip(v1, v2)])

    # Compute overlaps
    D = [[0.0] * P for _ in range(P)]
    for p1 in range(P):
        for p2 in range(p1 + 1, P):
            D[p1][p2] = dot(pair_sum_vecs[p1], pair_sum_vecs[p2])

    # ILP
    assign_prob = pulp.LpProblem(f"{category_name.lower()}_assignment", pulp.LpMinimize)
    x = [
        [pulp.LpVariable(f"x_{p}_{d}", cat="Binary") for d in range(num_days)]
        for p in range(P)
    ]

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

    # Auxiliary for overlaps
    obj_terms = []
    for d in range(num_days):
        for p1 in range(P):
            for p2 in range(p1 + 1, P):
                z = pulp.LpVariable(f"z_{d}_{p1}_{p2}", cat="Binary")
                assign_prob += z <= x[p1][d]
                assign_prob += z <= x[p2][d]
                assign_prob += z >= x[p1][d] + x[p2][d] - 1
                obj_terms.append(D[p1][p2] * z)

    assign_prob.setObjective(pulp.lpSum(obj_terms))

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

    total_overlap = pulp.value(assign_prob.objective)
    print(
        f"{category_name} assignment minimizes total muscular overlaps between pairs on same days (total overlap: {total_overlap:.2f})."
    )

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
    float,
    float,
]:
    """
    Build and solve the ILP for muscle coverage with mixed-objective minimization.
    Minimizes weighted sum of absolute deviations (in sets) plus weighted maximum overshoot/undershoot deviations across muscles.
    Undershoot deviations are weighted more heavily than overshoot deviations.

    Returns:
        status: Solver status ('Optimal', 'Feasible', etc.)
        counts_dict: Exercise counts per category
        pairs_dict: Expanded superset pairs per category
        coverage: Muscle coverage vs targets
        sum_overshoot_deviations: Sum of overshoot deviations across all muscles (in sets)
        sum_undershoot_deviations: Sum of undershoot deviations across all muscles (in sets)
        max_overshoot: Maximum overshoot deviation across muscles (in sets)
        max_undershoot: Maximum undershoot deviation across muscles (in sets)
        objective_value: Minimized objective value (weighted sum + weighted max overshoot/undershoot, in sets)
    """
    prob: pulp.LpProblem = pulp.LpProblem("muscle_coverage_solver", pulp.LpMinimize)

    # Define categories to process
    categories = list(DayCategory)

    # Exercise count variables per category
    c: Dict[DayCategory, LpVariableDict] = {}
    for cat in categories:
        c[cat] = {
            e: pulp.LpVariable(
                f"c_{cat.name.lower()}_{e}",
                lowBound=0,
                upBound=min(
                    DAY_REQUIREMENTS[cat],
                    get_max_usage_for_category(EXERCISE_NAMES[e], cat),
                ),
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

                # Check equipment conflicts
                ex1_name = EXERCISE_NAMES[i]
                ex2_name = EXERCISE_NAMES[j]
                equipment_conflict = has_equipment_conflict(ex1_name, ex2_name)

                # Only allow pairing if both conditions are met
                if (
                    muscle_overlap_ok
                    and not equipment_conflict
                    and allowed_in_category(EXERCISE_NAMES[i], cat)
                    and allowed_in_category(EXERCISE_NAMES[j], cat)
                ):
                    p[cat][(i, j)] = pulp.LpVariable(
                        f"p_{cat.name.lower()}_{i}_{j}",
                        lowBound=0,
                        upBound=min(PAIRS_PER_CATEGORY[cat], 3),
                        cat="Integer",
                    )

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

    # Absolute deviation constraints - minimize sum of absolute deviations from targets (in sets)
    overshoot_deviations = {}
    undershoot_deviations = {}

    # Variables for maximum overshoot and undershoot deviations (in sets)
    max_overshoot_slack = pulp.LpVariable(
        "max_overshoot_slack", lowBound=0, cat="Continuous"
    )
    max_undershoot_slack = pulp.LpVariable(
        "max_undershoot_slack", lowBound=0, cat="Continuous"
    )

    for m_idx, m in enumerate(Muscle):
        if MUSCLE_TARGETS[m] > 0:
            coverage_expr = pulp.lpSum(
                SETS_PER_INSTANCE[cat] * c[cat][e] * VEC[e][m_idx]
                for cat in categories
                for e in range(E)
            )
            target = MUSCLE_TARGETS[m]

            # Slack variables for overshoot and undershoot in absolute sets
            over_abs_slack = pulp.LpVariable(
                f"over_abs_{m.name}", lowBound=0, cat="Continuous"
            )
            under_abs_slack = pulp.LpVariable(
                f"under_abs_{m.name}", lowBound=0, cat="Continuous"
            )

            overshoot_deviations[m] = over_abs_slack
            undershoot_deviations[m] = under_abs_slack

            # Constraints allowing absolute deviation in sets
            prob += (coverage_expr <= target + over_abs_slack, f"over_dev_{m.name}")
            prob += (coverage_expr >= target - under_abs_slack, f"under_dev_{m.name}")

            # Constraints for max overshoot and undershoot deviations
            prob += (max_overshoot_slack >= over_abs_slack, f"max_over_{m.name}")
            prob += (max_undershoot_slack >= under_abs_slack, f"max_under_{m.name}")

    # Objective: minimize weighted sum of absolute deviations plus weighted max overshoot/undershoot deviations
    dev_sum_expr = pulp.lpSum(overshoot_deviations.values()) + UNDERSHOOT_WEIGHT_MULTIPLIER * pulp.lpSum(
        undershoot_deviations.values()
    )
    prob.setObjective(DEVIATION_SUM_WEIGHT * dev_sum_expr + max_overshoot_slack + UNDERSHOOT_WEIGHT_MULTIPLIER * max_undershoot_slack)

    # Solve
    solver = pulp.PULP_CBC_CMD(msg=False)
    prob.solve(solver)

    status: str = pulp.LpStatus[prob.status]

    if status not in ("Optimal", "Feasible"):
        # Return empty dicts for infeasible case (but type says no Optional, assume always succeeds for now)
        empty_counts = {cat: {} for cat in categories}
        empty_pairs = {cat: [] for cat in categories}
        return status, empty_counts, empty_pairs, {}, 0.0, 0.0, 0.0, 0.0, 0.0

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

    # Calculate separate sums and maxima for overshoot and undershoot deviations
    sum_overshoot_deviations = sum(
        safe_value(overshoot_deviations[m]) for m in overshoot_deviations
    )
    sum_undershoot_deviations = sum(
        safe_value(undershoot_deviations[m]) for m in undershoot_deviations
    )

    # Calculate maximum overshoot and undershoot deviations
    max_overshoot = safe_value(max_overshoot_slack)
    max_undershoot = safe_value(max_undershoot_slack)

    # Calculate objective value (weighted abs sum + weighted max overshoot/undershoot deviations)
    objective_value = (
        max_overshoot + UNDERSHOOT_WEIGHT_MULTIPLIER * max_undershoot +
        DEVIATION_SUM_WEIGHT * (sum_overshoot_deviations + UNDERSHOOT_WEIGHT_MULTIPLIER * sum_undershoot_deviations)
    )

    return (
        status,
        counts_dict,
        pairs_dict,
        coverage,
        sum_overshoot_deviations,
        sum_undershoot_deviations,
        max_overshoot,
        max_undershoot,
        objective_value,
    )


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
    (
        status,
        counts_dict,
        pairs_dict,
        coverage,
        sum_overshoot_deviations,
        sum_undershoot_deviations,
        max_overshoot,
        max_undershoot,
        objective_value,
    ) = result

    print("\n=== COUNTS ===")
    for cat in counts_dict:
        supersets_per_day = PAIRS_PER_DAY[cat]
        days = DAYS_PER_CATEGORY[cat]
        total_instances = DAY_REQUIREMENTS[cat]
        total_supersets = PAIRS_PER_CATEGORY[cat]
        print(
            f"{cat.name.replace('_', ' ')} counts ({total_instances} instances, {total_supersets} supersets over {days} days at {supersets_per_day}/day):"
        )
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

    print(
        f"\nObjective = {DEVIATION_SUM_WEIGHT} * (sum_overshoot({sum_overshoot_deviations:.2f}) + {UNDERSHOOT_WEIGHT_MULTIPLIER} * sum_undershoot({sum_undershoot_deviations:.2f})) + max_overshoot({max_overshoot:.2f}) + {UNDERSHOOT_WEIGHT_MULTIPLIER} * max_undershoot({max_undershoot:.2f}) = {objective_value:.2f} sets"
    )

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
