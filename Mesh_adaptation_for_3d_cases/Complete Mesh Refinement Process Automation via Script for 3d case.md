## Automation: Mesh Refinement and DSMC Simulation with `amr_3d.sh`

All the processes for mesh refinement and DSMC simulation can be run automatically using the `amr_3d.sh` script. By executing this script, the entire workflow—from initial simulation to mesh refinement and re-simulation—will be completed automatically in three iterations for a 3D cylinder case.

### Workflow Steps per Iteration

1. **Run the DSMC Simulation**  
   Executes the simulation using the initial `3d_cylinder.msh` mesh file.

2. **Archive Simulation Results**  
   After each run, the ParaView output folder (`comet_result/field`) is archived and saved as `3d_AMR<i>_result` for tracking each iteration’s results.

3. **Export Mean Free Path Data**  
   Runs `final_3d.py` using `pvpython` to automatically extract the mean free path data and generate `.csv` and `.pos` files.

4. **Generate Refined Mesh**  
   Calls Gmsh with the updated `.geo` file to create a refined mesh (`3d_Mesh_tmp.msh`) based on the newly extracted mean free path data.

5. **Backup and Update Mesh**  
   Saves the refined mesh as `3d_Mesh<i>.msh` for backup and updates `3d_cylinder.msh` for use in the next iteration.

After completing three iterations, you will have:
- **Backup meshes:** `3d_Mesh1.msh`, `3d_Mesh2.msh`, `Mesh3.msh`  
- **Archived outputs:** `3d_Mesh1_result`, `3d_Mesh2_result`, `3d_Mesh3_result`

Before running the simulation make sure to change the path location for the BASE_DIR, GMESH_DIR, CASE_SCRIPT, FINAL_PY, SIM_MESH, PV_OUTPUT_DIR, RESULT_ROOT, GEO_FILE & GMSH_BIN in the script.

### Running the Automated Workflow

After updating the path location in `amr_3d.sh` script to match your directory path address, run the full simulation and mesh‑refinement workflow by invoking:

```bash
./amr_3d.sh
```

---

### `amr_3d.sh` Script

```bash
#!/bin/bash
# --------------------------------------------------------------------------------
# Coded by Fahim Shahriyar under the supervision of De. Chonglin Zhang
#
# Performs 3 loops of:
#   1. Run MPI case using 3d_cylinder.msh
#   2. Archive ParaView output folder '.../comet_result/field' → '.../comet_result/AMR<i>_result'
#   3. Run final.py via pvpython (generates CSV and POS)
#   4. Run gmsh on 3d_cylinder.geo → AMR_tmp.msh
#   5. Save 3d_Mesh_tmp.msh as 3d_Mesh<i>.msh and update 3d_cylinder.msh
# --------------------------------------------------------------------------------

# —————————————————————————————————————————————————————————
# Configuration
# —————————————————————————————————————————————————————————
BASE_DIR="/home/fahim.shahriyar/dsmc/NDAS/gmsh/3d_cases/3d_flow_over_cylinder/coarse_mesh"
GMESH_DIR="${BASE_DIR}/gmsh_mesh_files"
CASE_SCRIPT="${BASE_DIR}/run_centos_gmsh_nparts=1_groupsize=1.sh"
FINAL_PY="${BASE_DIR}/final_3d.py"
SIM_MESH="${BASE_DIR}/3d_cylinder.msh"
PV_OUTPUT_DIR="${BASE_DIR}/comet_result/field"
RESULT_ROOT="${BASE_DIR}/comet_result"
GEO_FILE="3d_cylinder.geo"
GMSH_BIN="/home/fahim.shahriyar/gmsh/gmsh-4.11.1-Linux64/bin/gmsh"

# —————————————————————————————————————————————————————————
# Main loop: 3 iterations
# —————————————————————————————————————————————————————————
for i in 1 2 ; do
  echo
  echo "==============================================="
  echo " ITERATION $i"
  echo "==============================================="

  # 1) Run the case script
  cd "$BASE_DIR" || { echo "ERROR: cd $BASE_DIR"; exit 1; }
  echo "[1/$i] Running MPI case..."
  ./run_centos_gmsh_nparts=1_groupsize=1.sh
  if [ $? -ne 0 ]; then echo "ERROR: MPI case failed"; exit 1; fi

  # 2) Archive the ParaView output folder
  ARCHIVE_DIR="${RESULT_ROOT}/3d_Mesh${i}_result"
  echo "[2/$i] Archiving ParaView results → $ARCHIVE_DIR"
  rm -rf "$ARCHIVE_DIR"                  # remove old if exists
  cp -r "$PV_OUTPUT_DIR" "$ARCHIVE_DIR"  # copy entire field folder
  if [ $? -ne 0 ]; then echo "ERROR: Archiving failed"; exit 1; fi

  # 3) Run the Python exporter
  echo "[3/$i] Running pvpython on final_3d.py..."
  pvpython "$FINAL_PY"
  if [ $? -ne 0 ]; then echo "ERROR: pvpython failed"; exit 1; fi

  # 4) Generate a new mesh with Gmsh
  cd "$GMESH_DIR" || { echo "ERROR: cd $GMESH_DIR"; exit 1; }
  echo "[4/$i] Generating new mesh with Gmsh..."
  "$GMSH_BIN" "$GEO_FILE" -3 -o 3d_Mesh_tmp.msh
  if [ $? -ne 0 ]; then echo "ERROR: gmsh failed"; exit 1; fi

  # 5a) Backup the mesh
  BACKUP_MESH="3d_Mesh${i}.msh"
  echo "[5/$i] Saving backup mesh → $BACKUP_MESH"
  cp -f 3d_Mesh_tmp.msh "$BACKUP_MESH"
  if [ $? -ne 0 ]; then echo "ERROR: mesh backup failed"; exit 1; fi

  # 5b) Update simulation mesh
  echo "[5/$i] Updating simulation mesh → $SIM_MESH"
  cp -f 3d_Mesh_tmp.msh "$SIM_MESH"
  if [ $? -ne 0 ]; then echo "ERROR: updating SIM_MESH failed"; exit 1; fi

  echo "Iteration $i complete."
done

echo
echo "All 3 iterations finished."
echo "Backups in: $GMESH_DIR → 3d_Mesh1.msh, 3d_Mesh2.msh, 3d_Mesh3.msh"
echo "Archived results in: $RESULT_ROOT → 3d_Mesh1_result, 3d_Mesh2_result, 3d_Mesh3_result"


