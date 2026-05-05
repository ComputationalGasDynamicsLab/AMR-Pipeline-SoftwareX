#!/bin/bash
# --------------------------------------------------------------------------------
# Coded by Fahim Shahriyar under the supervision of Dr. Chonglin Zhang
# --------------------------------------------------------------------------------

set -euo pipefail
IFS=$'\n\t'

# ----------------------------------------
# Simple args / autodetect
# ----------------------------------------
usage() {
  cat <<'USAGE'
Usage: ./run_wedge_amr_pipeline.sh [--base DIR]

Notes:
  - Defaults to current working directory if it contains gmsh/
  - Otherwise, tries the parent directory of this script
  - You can also: BASE_DIR=/path/to/experimental_PSI ./run_wedge_amr_pipeline.sh
USAGE
}

BASE_DIR="${BASE_DIR:-}"
if [[ ${#@} -gt 0 ]]; then
  case "$1" in
    --base) BASE_DIR="$2"; shift 2;;
    -h|--help) usage; exit 0;;
  esac
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -z "${BASE_DIR}" ]]; then
  if [[ -d "$(pwd)/gmsh" ]]; then
    BASE_DIR="$(pwd)"
  else
    CANDIDATE="${SCRIPT_DIR}"
    [[ -d "${SCRIPT_DIR}/../gmsh" ]] && CANDIDATE="${SCRIPT_DIR}/.."
    BASE_DIR="$(cd "$CANDIDATE" && pwd)"
  fi
fi
BASE_DIR="$(cd "$BASE_DIR" && pwd)"

# —————————————————————————————————————————————————————————
# Configuration
# —————————————————————————————————————————————————————————
# NOTE: keep autodetect; do NOT override BASE_DIR here
# BASE_DIR="/home/fahim.shahriyar/dsmc/experimental_PSI_3"
GMESH_DIR="${BASE_DIR}/gmsh"
CASE_SCRIPT="${BASE_DIR}/run_centos_gmsh_nparts=1_groupsize=1.sh"
CASE_SCRIPT_AMR="${BASE_DIR}/run_centos_gmsh_nparts=1_groupsize=1_amr.sh"
FINAL_PY="${BASE_DIR}/csv_to_pos.py"
SIM_MESH="${BASE_DIR}/wedge.msh"
SIM_MESH_AMR="${BASE_DIR}/wedge_amr.msh"
PV_OUTPUT_DIR="${BASE_DIR}/comet_result/field"
RESULT_ROOT="${BASE_DIR}/comet_result"
GEO_FILE="wedge.geo"
GEO_FILE_AMR="wedge_amr.geo"
GMSH_BIN="/home/fahim.shahriyar/gmsh/gmsh-4.11.1-Linux64/bin/gmsh"
LOG_DIR="${BASE_DIR}/logs"

# —————————————————————————————————————————————————————————
# Main loop: 3 iterations
# —————————————————————————————————————————————————————————
for i in 1 2 3; do
  echo
  echo "==============================================="
  echo " ITERATION $i"
  echo "==============================================="
  
  mkdir -p "$LOG_DIR"
  rm -rf "$LOG_DIR"/*
  
  # Run gmsh on wedge.geo → wedge_tmp.msh
  cd "$GMESH_DIR" || { echo "ERROR: cd $GMESH_DIR"; exit 1; }
  echo "Generating new mesh with Gmsh..."
  "$GMSH_BIN" "$GEO_FILE" -3 -o wedge_tmp.msh 2>&1 | tee "$LOG_DIR/wedge_normal.txt"
  if [ $? -ne 0 ]; then echo "ERROR: gmsh failed"; exit 1; fi
  
  # Backup the mesh
  BACKUP_MESH="wedge${i}.msh"
  echo "Saving backup mesh → $BACKUP_MESH"
  cp -f wedge_tmp.msh "$BACKUP_MESH"
  if [ $? -ne 0 ]; then echo "ERROR: mesh backup failed"; exit 1; fi

  # Update simulation mesh
  echo "Updating simulation mesh → $SIM_MESH"
  cp -f wedge_tmp.msh "$SIM_MESH"
  if [ $? -ne 0 ]; then echo "ERROR: updating SIM_MESH failed"; exit 1; fi

  # Run the case script
  cd "$BASE_DIR" || { echo "ERROR: cd $BASE_DIR"; exit 1; }
  echo "Running MPI case for the normal mesh..."
  ./run_centos_gmsh_nparts=1_groupsize=1.sh 2>&1 | tee "$LOG_DIR/output_normal${i}.txt"
  if [ $? -ne 0 ]; then echo "ERROR: MPI case failed"; exit 1; fi

  # Archive the ParaView output folder
  ARCHIVE_DIR="${RESULT_ROOT}/output_normal_result"
  echo "Archiving ParaView results for normal mesh → $ARCHIVE_DIR"
  rm -rf "$ARCHIVE_DIR"
  cp -r "$PV_OUTPUT_DIR" "$ARCHIVE_DIR"
  if [ $? -ne 0 ]; then echo "ERROR: Archiving failed"; exit 1; fi

  # Run the Python exporter
  echo "converting csv file to pos file"
  pvpython "$FINAL_PY" 2>&1 | tee "$LOG_DIR/csv_2_pos.txt"
  if [ $? -ne 0 ]; then echo "ERROR: pvpython failed"; exit 1; fi

  # Generate a new adaptive mesh with Gmsh 
  cd "$GMESH_DIR" || { echo "ERROR: cd $GMESH_DIR"; exit 1; }
  echo "Generating new adaptive mesh with Gmsh..."
  "$GMSH_BIN" "$GEO_FILE_AMR" -3 -o wedge_amr_tmp.msh 2>&1 | tee "$LOG_DIR/wedge_amr.txt"
  if [ $? -ne 0 ]; then echo "ERROR: gmsh failed"; exit 1; fi

  # Backup the amr mesh
  BACKUP_MESH="wedge_amr${i}.msh"
  echo "Saving backup amr mesh → $BACKUP_MESH"
  cp -f wedge_amr_tmp.msh "$BACKUP_MESH"
  if [ $? -ne 0 ]; then echo "ERROR: mesh backup failed"; exit 1; fi

  # Update simulation amr mesh
  echo "Updating simulation mesh → $SIM_MESH_AMR"
  cp -f wedge_amr_tmp.msh "$SIM_MESH_AMR"
  if [ $? -ne 0 ]; then echo "ERROR: updating SIM_MESH_AMR failed"; exit 1; fi
  
  # Run the case script for amr mesh
  cd "$BASE_DIR" || { echo "ERROR: cd $BASE_DIR"; exit 1; }
  echo "Running MPI case for the amr mesh..."
  ./run_centos_gmsh_nparts=1_groupsize=1_amr.sh 2>&1 | tee "$LOG_DIR/output_amr${i}.txt"
  if [ $? -ne 0 ]; then echo "ERROR: MPI case failed"; exit 1; fi
  
  # Archive the ParaView output folder for AMR Result
  ARCHIVE_DIR="${RESULT_ROOT}/output_amr${i}_result"
  echo "Archiving ParaView results for amr meshes → $ARCHIVE_DIR"
  rm -rf "$ARCHIVE_DIR"
  cp -r "$PV_OUTPUT_DIR" "$ARCHIVE_DIR"
  if [ $? -ne 0 ]; then echo "ERROR: Archiving failed"; exit 1; fi

  echo "Simulation complete."
done

echo
echo "All 3 iterations finished."
echo "Backups in: $GMESH_DIR → wedge1.msh, wedge2.msh, wedge3.msh, wedge_amr1.msh, wedge_amr2.msh, wedge_amr3.msh"
echo "Archived results in: $RESULT_ROOT → output_normal_result, output_amr1_result, output_amr2_result, output_amr3_result"

