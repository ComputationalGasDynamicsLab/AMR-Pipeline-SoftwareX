# Mesh Adaptation for 3D Cases

This folder contains a standalone, manual demonstration of the
mean-free-path-based mesh adaptation procedure for 3D DSMC cases. The
example geometry is a cylinder in a 3D box domain.

The procedure is identical in structure to the 2D case
(see `Mesh_adaptation_for_2d_cases/`), but the file sizes, mesh sizes,
and run times are substantially larger. The 3D case is intended as a
reference for full-scale problems; for development, debugging, or
quick experimentation the 2D case should be used first.

---

## Files

| File | Purpose |
|------|---------|
| `3d_cylinder_adaptive_mesh.geo` | Gmsh geometry file for the 3D cylinder, with boundary tags and the AMR background-field setup. |
| `Amr_3d_case.sh` | Shell driver that runs Gmsh, the DSMC solver, and the field extractor in sequence for the 3D case. |
| `csv_to_pos_3d_case.py` | Python (pvpython) script that exports the 3D mean-free-path field and converts it to Gmsh `.pos` format. |
| `Modified 3D Cylinder Geometry/` | Subfolder containing an alternative geometry described by a STEP file, plus a Python helper for variants of the cylinder body. See its own README. |
| `Step 1: Generate Pos & CSV file.md` | Explanation of the field extraction step, with the pvpython code block. |
| `Step 2: Import POS file in Gmsh.md` | Explanation of how the `.pos` file is consumed by Gmsh in 3D. |
| `Step 3: Run DSMC Simulation with New Mesh.md` | Explanation of the re-run on the refined 3D mesh. |

---

## Workflow

The procedure follows the same five steps as the 2D case:

1. **Run the baseline DSMC simulation** on a uniform initial mesh.
2. **Extract the mean-free-path field** from the simulation output using
   `csv_to_pos_3d_case.py`. This produces both a CSV with
   `(x, y, z, mean_free_path)` per grid point and a Gmsh `.pos` file
   that uses the `SP(x, y, z){h}` PostView format.
3. **Generate the refined 3D mesh** by running Gmsh on the `.geo` file.
   The `.geo` merges the `.pos` file as a background scalar field and
   Gmsh uses it to set the local cell size.
4. **Re-run the DSMC simulation** on the refined mesh.
5. **Iterate** by returning to step 2 with the new PVD output.

The full automated equivalent is `all_run.sh` at the repository root.
For 3D work the automated loop is the recommended path because the per-
iteration bookkeeping is more involved than in 2D.

---

## Resource considerations

3D adaptive runs require substantially more memory and compute time than
their 2D counterparts. Cell counts after a few AMR iterations can grow
into the millions, particularly when the sizing field is driven by
sharp features such as shocks or boundary layers.

Before launching a long 3D run, the following checks are recommended:

- Confirm that the available memory is at least 8 GB for early iterations
  and 32 GB or more for late iterations.
- Estimate the expected cell count using the sizing-field bounds
  (`sizing_min`, `sizing_max`) and the domain volume.
- Run a single AMR iteration first and inspect the cell-count growth
  before committing to a multi-iteration loop.

---

## Notes

`csv_to_pos_3d_case.py` is the 3D variant of the original DSMC-only
extractor. The repository root contains a newer universal version,
`final.py`, which handles both 2D and 3D meshes uniformly and also
supports the OpenFOAM gradient-based workflow. New work should use
`final.py`; the 3D-specific script in this folder is kept for archival
reference.
