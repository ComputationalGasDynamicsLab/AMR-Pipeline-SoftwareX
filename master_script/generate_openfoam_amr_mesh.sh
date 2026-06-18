#!/bin/bash
# ----------------------------------------------------------------------
# generate_amr_mesh.sh — build the OpenFOAM AMR mesh in one step.
#
# One script, no COMET.  It turns the bundled OpenFOAM result into a
# ready-to-use OpenFOAM mesh:
#
#   1. final.py (pvpython) reads the bundled result and writes the
#      sizing field mfp.pos.            [skipped if pvpython is absent;
#                                         the bundled mfp.pos is used]
#   2. Gmsh reads mfp.pos as a background field and writes the AMR
#      mesh (.msh).                      [needs only Gmsh]
#   3. gmshToFoam converts that mesh into openfoam_case/constant/polyMesh
#      and the boundary patch types are set from boundary_fix.
#                                        [skipped if OpenFOAM is absent;
#                                         the .msh is still produced]
#
# Every value is read from amr_pipeline.input; the script is not edited.
# The full flow solve (rhoCentralFoam, multiple AMR loops) lives in the
# shared scripts under ../master_script/ — see README.md.
# ----------------------------------------------------------------------
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INPUT_FILE="${SCRIPT_DIR}/amr_pipeline.input"
FINAL_PY="${REPO_ROOT}/master_script/final.py"

if [ ! -f "$INPUT_FILE" ]; then
    echo "ERROR: amr_pipeline.input not found at $INPUT_FILE" >&2
    exit 1
fi

# --- Read a key=value entry from amr_pipeline.input -------------------
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

# --- Read every configurable value ------------------------------------
GMSH_BIN=$(parse_conf      gmsh_bin        "$INPUT_FILE" "")
PVPYTHON=$(parse_conf      pvpython        "$INPUT_FILE" "pvpython")
GEO_FILE_AMR=$(parse_conf  geo_file_amr    "$INPUT_FILE" "mach3_cylinder_amr.geo")
SIM_MESH_AMR=$(parse_conf  sim_mesh_amr    "$INPUT_FILE" "mach3_cylinder_amr.msh")
PVD_REL=$(parse_conf       pvd_file        "$INPUT_FILE" \
                           "precomputed_result/field/auto_field.pvd")
EXTRACTION_MODE=$(parse_conf extraction_mode "$INPUT_FILE" "gradient")
MFP_COLUMN=$(parse_conf    mfp_column      "$INPUT_FILE" "p_sizing")
POS_SCALE=$(parse_conf     pos_scale       "$INPUT_FILE" "1.0")
GRADIENT_FIELD=$(parse_conf gradient_field "$INPUT_FILE" "p")
SIZING_MIN=$(parse_conf    sizing_min      "$INPUT_FILE" "0.002")
SIZING_MAX=$(parse_conf    sizing_max      "$INPUT_FILE" "0.015")
SIZING_SCALE=$(parse_conf  sizing_scale    "$INPUT_FILE" "100.0")
RAW_CSV=$(parse_conf       raw_csv         "$INPUT_FILE" "all_data.csv")
FILTERED_CSV=$(parse_conf  filtered_csv    "$INPUT_FILE" "filtered_mfp.csv")
POS_FILE=$(parse_conf      pos_file        "$INPUT_FILE" "mfp.pos")
FOAM_SOURCE=$(parse_conf   foam_source     "$INPUT_FILE" "")
CASE_DIR_REL=$(parse_conf  case_dir        "$INPUT_FILE" "openfoam_case")
BOUNDARY_FIX=$(parse_conf  boundary_fix    "$INPUT_FILE" "")

CASE_DIR="${SCRIPT_DIR}/${CASE_DIR_REL}"

# --- Resolve gmsh (required) ------------------------------------------
if [ -z "$GMSH_BIN" ] || [ ! -x "$GMSH_BIN" ]; then
    if command -v gmsh >/dev/null 2>&1; then
        GMSH_BIN="$(command -v gmsh)"
    else
        echo "ERROR: gmsh binary not found.  Set 'gmsh_bin' in $INPUT_FILE." >&2
        exit 1
    fi
fi

cd "$SCRIPT_DIR"

echo "============================================="
echo " OpenFOAM AMR mesh — Mach 3 cylinder (no COMET)"
echo " Input file  : $INPUT_FILE"
echo " Output mesh : $SCRIPT_DIR/$SIM_MESH_AMR"
echo "============================================="

# --- STEP 1: sizing field (optional; bundled mfp.pos is the fallback) -
echo "[STEP 1] Extracting sizing field with final.py..."
PV_OK=1
if [ "$PVPYTHON" != "pvpython" ] && [ ! -x "$PVPYTHON" ]; then
    if command -v pvpython >/dev/null 2>&1; then PVPYTHON="$(command -v pvpython)"; else PV_OK=0; fi
fi
PVD_FILE="${SCRIPT_DIR}/${PVD_REL}"
if [ "$PV_OK" = "1" ] && [ -f "$PVD_FILE" ] && [ -f "$FINAL_PY" ]; then
    EXTRA_ARGS=()
    if [ "$EXTRACTION_MODE" = "gradient" ] && [ -n "$GRADIENT_FIELD" ]; then
        EXTRA_ARGS+=(--gradient-field "$GRADIENT_FIELD")
    fi
    "$PVPYTHON" "$FINAL_PY" \
        --pvd "$PVD_FILE" --raw-csv "$SCRIPT_DIR/$RAW_CSV" \
        --filtered-csv "$SCRIPT_DIR/$FILTERED_CSV" --pos "$SCRIPT_DIR/$POS_FILE" \
        --multiply-factor "$POS_SCALE" --mfp-column "$MFP_COLUMN" \
        --extraction-mode "$EXTRACTION_MODE" --sizing-min "$SIZING_MIN" \
        --sizing-max "$SIZING_MAX" --sizing-scale "$SIZING_SCALE" "${EXTRA_ARGS[@]}"
else
    echo "[SKIP] pvpython/result not available — using the bundled $POS_FILE."
    [ -f "$SCRIPT_DIR/$POS_FILE" ] || { echo "ERROR: no $POS_FILE to fall back on." >&2; exit 1; }
fi

# --- STEP 2: AMR mesh with Gmsh ---------------------------------------
echo "[STEP 2] Generating AMR mesh with Gmsh..."
"$GMSH_BIN" "$GEO_FILE_AMR" -3 -o "$SIM_MESH_AMR"

# --- STEP 3: convert to OpenFOAM polyMesh (gmshToFoam) ----------------
# OpenFOAM cannot read the Gmsh .msh directly.  This mirrors the
# gmshToFoam + boundary-fix that ../master_script/run_openfoam_amr.sh
# performs, so the output drops straight into an OpenFOAM run.
echo "[STEP 3] Converting to OpenFOAM polyMesh with gmshToFoam..."
CONVERTED=0
if [ -n "$FOAM_SOURCE" ] && [ -f "$FOAM_SOURCE" ]; then
    export PATH="/usr/lib64/openmpi/bin:$PATH"
    export LD_LIBRARY_PATH="/usr/lib64/openmpi/lib:${LD_LIBRARY_PATH:-}"
    # shellcheck disable=SC1090
    source "$FOAM_SOURCE" 2>/dev/null || true
fi
if command -v gmshToFoam >/dev/null 2>&1 && [ -d "$CASE_DIR" ]; then
    rm -rf "$CASE_DIR/constant/polyMesh"
    ( cd "$CASE_DIR" && gmshToFoam "$SCRIPT_DIR/$SIM_MESH_AMR" > log.gmshToFoam 2>&1 )
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
    patch, btype = patch.strip(), btype.strip()
    txt = re.sub(rf'({re.escape(patch)}\s*\{{[^}}]*type\s+)\w+', rf'\1{btype}', txt)
txt = re.sub(r'\s*defaultFaces\s*\{[^}]*\}', '', txt)
with open(bfile, 'w') as f:
    f.write(txt)
print("[OK] polyMesh written and boundary patch types set")
PYEOF
    CONVERTED=1
else
    echo "[SKIP] OpenFOAM (gmshToFoam) not available."
    echo "       The Gmsh mesh $SIM_MESH_AMR is ready; set 'foam_source' in"
    echo "       $INPUT_FILE and re-run to obtain the polyMesh."
fi

echo "============================================="
echo " Done."
echo " AMR mesh (Gmsh) : $SCRIPT_DIR/$SIM_MESH_AMR"
if [ "$CONVERTED" = "1" ]; then
    echo " OpenFOAM mesh   : $CASE_DIR/constant/polyMesh"
fi
echo "============================================="
