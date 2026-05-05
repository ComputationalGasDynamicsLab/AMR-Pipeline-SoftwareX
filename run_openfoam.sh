#!/bin/bash
# ----------------------------------------------------------------------
# OpenFOAM run script for the AMR pipeline.
#
# Reads ALL configuration from amr_pipeline.input — no editing needed.
# Handles both the baseline (uniform-mesh) run on the first iteration
# and the AMR-mesh runs on subsequent iterations:
#
#   ./run_openfoam.sh --baseline     uses the mesh named by 'sim_mesh'
#   ./run_openfoam.sh                uses the mesh named by 'sim_mesh_amr'
#
# The orchestrator (all_run.sh) calls this script with --baseline on
# iteration 1 and without arguments on iterations 2 onward.  A user
# running the script by hand will most often want the AMR form (no
# arguments), since that is what is needed once an AMR mesh has been
# produced.
# ----------------------------------------------------------------------
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_FILE="${SCRIPT_DIR}/amr_pipeline.input"

# --- Parse a key=value entry from amr_pipeline.input -----------------
parse_conf() {
    local key="$1" file="$2" default="$3"
    local val
    val=$(grep -E "^\s*${key}\s*=" "$file" 2>/dev/null \
          | head -1 \
          | sed 's/^[^=]*=\s*//' \
          | sed 's/\s*[!#].*//' \
          | xargs)
    echo "${val:-$default}"
}

if [ ! -f "$INPUT_FILE" ]; then
    echo "ERROR: amr_pipeline.input not found at $INPUT_FILE" >&2
    exit 1
fi

# --- Decide which mesh to use ----------------------------------------
# Three sources, in order of priority:
#   1. CLI flag '--baseline' (manual override)
#   2. AMR_MESH_MODE environment variable set by all_run.sh
#   3. Default: AMR mode (uses sim_mesh_amr)
MODE="${AMR_MESH_MODE:-amr}"
if [ "${1:-}" = "--baseline" ]; then
    MODE="baseline"
elif [ -n "${1:-}" ]; then
    echo "Unknown argument: $1" >&2
    echo "Usage: $0 [--baseline]" >&2
    exit 1
fi

if [ "$MODE" = "baseline" ]; then
    MESH_KEY="sim_mesh"
    MODE_LABEL="Baseline (uniform) Mesh Run"
else
    MESH_KEY="sim_mesh_amr"
    MODE_LABEL="AMR Mesh Run"
fi

# --- Read all config from the input file -----------------------------
FOAM_SOURCE=$(parse_conf foam_source     "$INPUT_FILE" "")
SOLVER=$(parse_conf      solver          "$INPUT_FILE" "rhoCentralFoam")
CASE_DIR_REL=$(parse_conf case_dir       "$INPUT_FILE" "openfoam_case")
BOUNDARY_FIX=$(parse_conf boundary_fix   "$INPUT_FILE" "")
FOAM_SIGFPE_VAL=$(parse_conf foam_sigfpe "$INPUT_FILE" "false")
MESH_NAME=$(parse_conf   "$MESH_KEY"     "$INPUT_FILE" "")

CASE_DIR="${SCRIPT_DIR}/${CASE_DIR_REL}"

if [ -z "$MESH_NAME" ]; then
    echo "ERROR: '$MESH_KEY' not set in $INPUT_FILE" >&2
    exit 1
fi
if [ -f "${SCRIPT_DIR}/${MESH_NAME}" ]; then
    MESH_FILE="${SCRIPT_DIR}/${MESH_NAME}"
else
    MESH_FILE="${SCRIPT_DIR}/gmsh/${MESH_NAME}"
fi

# --- Source OpenFOAM environment -------------------------------------
export PATH="/usr/lib64/openmpi/bin:$PATH"
export LD_LIBRARY_PATH="/usr/lib64/openmpi/lib:${LD_LIBRARY_PATH:-}"
if [ -n "$FOAM_SOURCE" ]; then
    source "$FOAM_SOURCE" 2>/dev/null || true
fi
[ "$FOAM_SIGFPE_VAL" = "true" ] || [ "$FOAM_SIGFPE_VAL" = "false" ] && \
    export FOAM_SIGFPE="$FOAM_SIGFPE_VAL"

echo "============================================="
echo " OpenFOAM AMR Pipeline — ${MODE_LABEL}"
echo " Mesh:   ${MESH_FILE}"
echo " Solver: ${SOLVER}"
echo "============================================="

cd "$CASE_DIR"

# 1. Clean previous run
rm -rf processor* constant/polyMesh VTK log.* postProcessing
ls -d [0-9]* 2>/dev/null | grep -v "0.orig" | xargs rm -rf 2>/dev/null || true

# 2. Convert Gmsh mesh to OpenFOAM polyMesh format
echo "[STEP 1] gmshToFoam..."
gmshToFoam "$MESH_FILE" > log.gmshToFoam 2>&1

# 3. Fix boundary types (data-driven from amr_pipeline.input boundary_fix)
echo "[STEP 2] Fixing boundaries..."
python3 - "$CASE_DIR/constant/polyMesh/boundary" "$BOUNDARY_FIX" <<'PYEOF'
import sys, re
bfile = sys.argv[1]
rules_str = sys.argv[2] if len(sys.argv) > 2 else ""
with open(bfile) as f:
    txt = f.read()
for rule in rules_str.split(","):
    rule = rule.strip()
    if ":" not in rule:
        continue
    patch, btype = rule.split(":", 1)
    patch = patch.strip()
    btype = btype.strip()
    txt = re.sub(
        rf'({re.escape(patch)}\s*\{{[^}}]*type\s+)\w+',
        rf'\1{btype}',
        txt
    )
txt = re.sub(r'\s*defaultFaces\s*\{[^}]*\}', '', txt)
with open(bfile, 'w') as f:
    f.write(txt)
print("[OK] Boundaries fixed")
PYEOF

# 4. Copy initial conditions
echo "[STEP 3] Setting up initial conditions..."
cp -r 0.orig 0

# 5. Run solver
echo "[STEP 4] Running ${SOLVER}..."
$SOLVER > log.${SOLVER} 2>&1
echo "[OK] Solver exit: $?"

# 6. Convert results to VTK
echo "[STEP 5] foamToVTK..."
foamToVTK > log.foamToVTK 2>&1

# 7. Reorganise the VTK output into the layout expected by the pipeline
#    (comet_result/field/step_*/field_g0_m0.vtu)
echo "[STEP 6] Organising VTK output..."
RESULT_DIR="${SCRIPT_DIR}/comet_result/field"
rm -rf "$RESULT_DIR"
mkdir -p "$RESULT_DIR"
idx=0
for d in $(ls -d "$CASE_DIR"/VTK/*/ 2>/dev/null | sort -t_ -k3 -n); do
    [ -d "$d" ] || continue
    mkdir -p "$RESULT_DIR/step_${idx}_m1_g1"
    [ -f "$d/internal.vtu" ] && \
        cp "$d/internal.vtu" "$RESULT_DIR/step_${idx}_m1_g1/field_g0_m0.vtu"
    idx=$((idx + 1))
done

echo "============================================="
echo " Done. $idx timesteps -> $RESULT_DIR"
echo "============================================="
