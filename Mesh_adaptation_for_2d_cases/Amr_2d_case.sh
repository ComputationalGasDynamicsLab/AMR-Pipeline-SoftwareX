#!/bin/bash
# --------------------------------------------------------------------------------
# coded by Fahim Shahriyar under the supervision of Dr Chonglin Zhang
#
# Performs 3 loops of:
#   1. Run MPI case using 2d_cylinder.msh
#   2. Archive ParaView output folder '.../comet_result/field' → '.../comet_result/AMR<i>_result'
#   3. Run final.py via pvpython (generates CSV and POS)
#   4. Run gmsh on 2d_cylinder.geo → Mesh_tmp.msh
#   5. Save Mesh_tmp.msh as Mesh<i>.msh and update 2d_cylinder.msh
# --------------------------------------------------------------------------------

# —————————————————————————————————————————————————————————
# Automatically determine BASE_DIR
# —————————————————————————————————————————————————————————
BASE_DIR="$(pwd)"
GMESH_DIR="${BASE_DIR}/gmsh_mesh_files"
CASE_SCRIPT="${BASE_DIR}/run_centos_gmsh_nparts=1_groupsize=4.sh"
FINAL_PY="${BASE_DIR}/final.py"
SIM_MESH="${BASE_DIR}/2d_cylinder.msh"
PV_OUTPUT_DIR="${BASE_DIR}/comet_result/field"
RESULT_ROOT="${BASE_DIR}/comet_result"
GEO_FILE="2d_cylinder.geo"
GMSH_BIN="${HOME}/gmsh/gmsh-4.11.1-Linux64/bin/gmsh"

# —————————————————————————————————————————————————————————
# Main loop: 3 iterations
# —————————————————————————————————————————————————————————
for i in 1 2 3 ; do
  echo
  echo "==============================================="
  echo " ITERATION $i"
  echo "==============================================="

  # 1) Run the case script
  cd "$BASE_DIR" || { echo "ERROR: cd $BASE_DIR"; exit 1; }
  echo "[1/$i] Running MPI case..."
  "$CASE_SCRIPT"
  if [ $? -ne 0 ]; then echo "ERROR: MPI case failed"; exit 1; fi

  # 2) Archive the ParaView output folder
  ARCHIVE_DIR="${RESULT_ROOT}/AMR${i}_result"
  echo "[2/$i] Archiving ParaView results → $ARCHIVE_DIR"
  rm -rf "$ARCHIVE_DIR"
  cp -r "$PV_OUTPUT_DIR" "$ARCHIVE_DIR"
  if [ $? -ne 0 ]; then echo "ERROR: Archiving failed"; exit 1; fi

  # 3) Run the Python exporter
  echo "[3/$i] Running pvpython on final.py..."
  pvpython "$FINAL_PY"
  if [ $? -ne 0 ]; then echo "ERROR: pvpython failed"; exit 1; fi

  # 4) Generate a new mesh with Gmsh
  cd "$GMESH_DIR" || { echo "ERROR: cd $GMESH_DIR"; exit 1; }
  echo "[4/$i] Generating new mesh with Gmsh..."
  "$GMSH_BIN" "$GEO_FILE" -2 -o Mesh_tmp.msh
  if [ $? -ne 0 ]; then echo "ERROR: gmsh failed"; exit 1; fi

  # 5a) Backup the mesh
  BACKUP_MESH="Mesh${i}.msh"
  echo "[5/$i] Saving backup mesh → $BACKUP_MESH"
  cp -f Mesh_tmp.msh "$BACKUP_MESH"
  if [ $? -ne 0 ]; then echo "ERROR: mesh backup failed"; exit 1; fi

  # 5b) Update simulation mesh
  echo "[5/$i] Updating simulation mesh → $SIM_MESH"
  cp -f Mesh_tmp.msh "$SIM_MESH"
  if [ $? -ne 0 ]; then echo "ERROR: updating SIM_MESH failed"; exit 1; fi

  echo "Iteration $i complete."
done

echo
echo "All 3 iterations finished."
echo "Backups in: $GMESH_DIR → Mesh1.msh, Mesh2.msh, Mesh3.msh"
echo "Archived results in: $RESULT_ROOT → AMR1_result, AMR2_result, AMR3_result"
