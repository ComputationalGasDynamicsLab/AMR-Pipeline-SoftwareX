# Mesh Adaptation for 3D Cases — COMET DSMC Cylinder

This demo generates the AMR-refined 3D mesh for a flow over a 3D
cylinder using the local mean free path as the refinement criterion.
The COMET DSMC solver is **not** invoked; the demo uses a bundled
solver result from a previous run.

## What You Need on Your Machine

- Gmsh (4.11 or newer)
- ParaView (5.13 or newer, MPI build) — for `pvpython`

Nothing else. COMET is not required for this demo.

## Files in This Folder

| File | What it is |
|------|------------|
| `amr_pipeline.input` | **The one file you edit.** Contains the absolute paths to `gmsh` and `pvpython`, the names of the geometry, mesh, and intermediate files, and the extraction settings. |
| `generate_amr_mesh.sh` | The demo script. Reads every value from `amr_pipeline.input`, runs `final.py`, then runs Gmsh on `3d_cylinder_amr.geo` and writes the 3D AMR mesh. Does not need to be edited. |
| `3d_cylinder.step` | CAD source — STEP file describing the 3D domain. |
| `3d_cylinder.geo` | Baseline geometry — merges the STEP file, tags the boundaries, and meshes with default sizing. |
| `3d_cylinder_amr.geo` | Same geometry plus the lines that load `mfp.pos` as a Gmsh `Background Field`. |
| `3d_cylinder.msh` | Uniform 3D mesh used as the starting point. |
| `comet.input` | The COMET solver input that produced the bundled result, kept for reference. |
| `precomputed_result/field/auto_field.pvd` | ParaView collection that the demo's `final.py` invocation reads. |
| `precomputed_result/field/step_5000_m1_g1/field_g0_m0.vtu` | The actual field data from the bundled COMET run. |

## How to Run

From this folder:

```bash
# Edit amr_pipeline.input — set gmsh_bin and pvpython to your absolute paths
./generate_amr_mesh.sh
```

After the script finishes you will have:

| New file | What it is |
|----------|------------|
| `mfp.pos` | Gmsh PostView with `SP(x, y, z){h}` records. |
| `filtered_mfp.csv` | `(x, y, z, mean_free_path)` rows for inspection. |
| `all_data.csv` | Full point-data export from the bundled VTU. |
| `3d_cylinder_amr.msh` | The 3D AMR-refined mesh — the end product of the demo. |

Open the two meshes side by side in Gmsh to see the refinement:

```bash
gmsh 3d_cylinder.msh        # uniform starting mesh
gmsh 3d_cylinder_amr.msh    # AMR mesh from this demo
```

The 3D AMR step is heavier than the 2D one: writing the new mesh
typically takes thirty seconds to a minute and the resulting mesh can
be several times larger than the uniform mesh in cell count.

## To Run the Full Pipeline

This demo only generates one AMR mesh from a pre-computed result. To
run the **full** pipeline (uniform mesh → run COMET → extract sizing
field → AMR mesh → run COMET again, repeated for several iterations),
use the master script `all_run.sh` at the top of the repository. The
full pipeline requires the COMET DSMC solver to be installed.
