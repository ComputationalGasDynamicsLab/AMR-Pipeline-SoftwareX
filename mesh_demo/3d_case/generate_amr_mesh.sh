#!/bin/bash
# ----------------------------------------------------------------------
# generate_amr_mesh.sh — 3D COMET cylinder demo
#
# Runs the mesh-adaptation step of the AMR pipeline only.  No solver is
# invoked.  Every parameter is read from amr_pipeline.input in this
# folder — the script itself does not need to be edited.
#
# The script:
#   1. Reads the bundled COMET solver result (path from amr_pipeline.input).
#   2. Runs final.py under pvpython to extract the chosen field and
#      write the Gmsh PostView file (mfp.pos).
#   3. Runs Gmsh on the AMR .geo, which reads mfp.pos as a background
#      field and produces the AMR mesh.
#
# Running the FULL pipeline (solver included, multiple AMR loops) needs
# the COMET DSMC code; see the top-level README.md for that workflow.
# ----------------------------------------------------------------------
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
INPUT_FILE="${SCRIPT_DIR}/amr_pipeline.input"
FINAL_PY="${REPO_ROOT}/master_script/final.py"

if [ ! -f "$INPUT_FILE" ]; then
    echo "ERROR: amr_pipeline.input not found at $INPUT_FILE" >&2
    exit 1
fi
if [ ! -f "$FINAL_PY" ]; then
    echo "ERROR: final.py not found at $FINAL_PY" >&2
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
GEO_FILE_AMR=$(parse_conf  geo_file_amr    "$INPUT_FILE" "3d_cylinder_amr.geo")
SIM_MESH_AMR=$(parse_conf  sim_mesh_amr    "$INPUT_FILE" "3d_cylinder_amr.msh")
PVD_REL=$(parse_conf       pvd_file        "$INPUT_FILE" \
                           "precomputed_result/field/auto_field.pvd")
EXTRACTION_MODE=$(parse_conf extraction_mode "$INPUT_FILE" "direct")
MFP_COLUMN=$(parse_conf    mfp_column      "$INPUT_FILE" "mean free path")
POS_SCALE=$(parse_conf     pos_scale       "$INPUT_FILE" "1.0")
GRADIENT_FIELD=$(parse_conf gradient_field "$INPUT_FILE" "")
SIZING_MIN=$(parse_conf    sizing_min      "$INPUT_FILE" "0.001")
SIZING_MAX=$(parse_conf    sizing_max      "$INPUT_FILE" "0.015")
SIZING_SCALE=$(parse_conf  sizing_scale    "$INPUT_FILE" "100.0")
RAW_CSV=$(parse_conf       raw_csv         "$INPUT_FILE" "all_data.csv")
FILTERED_CSV=$(parse_conf  filtered_csv    "$INPUT_FILE" "filtered_mfp.csv")
POS_FILE=$(parse_conf      pos_file        "$INPUT_FILE" "mfp.pos")

# --- Fall back to $PATH for gmsh and pvpython if not absolute ---------
if [ -z "$GMSH_BIN" ] || [ ! -x "$GMSH_BIN" ]; then
    if command -v gmsh >/dev/null 2>&1; then
        GMSH_BIN="$(command -v gmsh)"
    else
        echo "ERROR: gmsh binary not found.  Set 'gmsh_bin' in $INPUT_FILE." >&2
        exit 1
    fi
fi
if [ "$PVPYTHON" != "pvpython" ] && [ ! -x "$PVPYTHON" ]; then
    if command -v pvpython >/dev/null 2>&1; then
        PVPYTHON="$(command -v pvpython)"
    else
        echo "ERROR: pvpython binary not found.  Set 'pvpython' in $INPUT_FILE." >&2
        exit 1
    fi
fi

PVD_FILE="${SCRIPT_DIR}/${PVD_REL}"
if [ ! -f "$PVD_FILE" ]; then
    echo "ERROR: bundled PVD not found at $PVD_FILE" >&2
    exit 1
fi

cd "$SCRIPT_DIR"

echo "============================================="
echo " Mesh-only demo — 3D COMET cylinder"
echo " Input file     : $INPUT_FILE"
echo " Bundled result : $PVD_FILE"
echo " Output mesh    : $SCRIPT_DIR/$SIM_MESH_AMR"
echo "============================================="

echo "[STEP 1] Extracting field with final.py (mode: $EXTRACTION_MODE)..."
EXTRA_ARGS=()
if [ "$EXTRACTION_MODE" = "gradient" ] && [ -n "$GRADIENT_FIELD" ]; then
    EXTRA_ARGS+=(--gradient-field "$GRADIENT_FIELD")
fi
"$PVPYTHON" "$FINAL_PY" \
    --pvd              "$PVD_FILE" \
    --raw-csv          "$SCRIPT_DIR/$RAW_CSV" \
    --filtered-csv     "$SCRIPT_DIR/$FILTERED_CSV" \
    --pos              "$SCRIPT_DIR/$POS_FILE" \
    --multiply-factor  "$POS_SCALE" \
    --mfp-column       "$MFP_COLUMN" \
    --extraction-mode  "$EXTRACTION_MODE" \
    --sizing-min       "$SIZING_MIN" \
    --sizing-max       "$SIZING_MAX" \
    --sizing-scale     "$SIZING_SCALE" \
    "${EXTRA_ARGS[@]}"

echo "[STEP 2] Generating AMR mesh with Gmsh..."
"$GMSH_BIN" "$GEO_FILE_AMR" -3 -o "$SIM_MESH_AMR"

echo "============================================="
echo " Done."
echo " AMR mesh: $SCRIPT_DIR/$SIM_MESH_AMR"
echo " Open it in Gmsh to compare against the bundled uniform mesh."
echo "============================================="
