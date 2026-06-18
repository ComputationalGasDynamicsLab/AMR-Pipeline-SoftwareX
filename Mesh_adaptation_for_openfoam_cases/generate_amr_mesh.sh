#!/bin/bash
# ----------------------------------------------------------------------
# generate_amr_mesh.sh — OpenFOAM Mach 3 cylinder mesh-adaptation
#
# Produces the AMR mesh and then hands it to the OpenFOAM run wrapper,
# because OpenFOAM cannot read a Gmsh .msh directly — it needs a
# polyMesh.  Every parameter is read from amr_pipeline.input; the
# script itself does not need to be edited.
#
# The script:
#   1. Runs final.py under pvpython in 'gradient' mode to compute
#      |grad(p)| and write the sizing field mfp.pos.
#   2. Runs Gmsh on the AMR .geo, which reads mfp.pos as a background
#      field and produces the AMR mesh (.msh).
#   3. Calls the run wrapper run_openfoam_amr.sh, which converts that
#      mesh with gmshToFoam (writing openfoam_case/constant/polyMesh),
#      fixes the boundary patch types, and runs rhoCentralFoam.  The
#      step is skipped with a notice if OpenFOAM is not configured — the
#      Gmsh mesh is still produced.
#
# Step 3 reuses the same run_openfoam_amr.sh that the full pipeline
# (master_script/all_run.sh) uses, rather than duplicating gmshToFoam
# here.  See README.md.
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
echo " Mesh-only demo — OpenFOAM 2D Mach 3 cylinder"
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

# --- STEP 3: hand the mesh to the OpenFOAM run wrapper ----------------
# OpenFOAM cannot use the Gmsh .msh directly, so run_openfoam_amr.sh
# converts it to a polyMesh with gmshToFoam (and runs the solver).  We
# follow that wrapper here instead of duplicating the conversion.
WRAPPER="${SCRIPT_DIR}/run_openfoam_amr.sh"
FOAM_SOURCE=$(parse_conf foam_source "$INPUT_FILE" "")
echo "[STEP 3] Converting to OpenFOAM polyMesh via run_openfoam_amr.sh..."
CONVERTED=0
if [ ! -x "$WRAPPER" ]; then
    echo "[SKIP] run_openfoam_amr.sh not found next to this script."
elif [ -z "$FOAM_SOURCE" ] || [ ! -f "$FOAM_SOURCE" ]; then
    echo "[SKIP] OpenFOAM not configured: set 'foam_source' in $INPUT_FILE,"
    echo "       then run ./run_openfoam_amr.sh to convert and solve."
else
    "$WRAPPER"
    CONVERTED=1
fi

echo "============================================="
echo " Done."
echo " AMR mesh (Gmsh) : $SCRIPT_DIR/$SIM_MESH_AMR"
if [ "$CONVERTED" = "1" ]; then
    echo " OpenFOAM mesh   : $SCRIPT_DIR/openfoam_case/constant/polyMesh"
fi
echo " Open the .msh in Gmsh to compare against the uniform mesh."
echo "============================================="
