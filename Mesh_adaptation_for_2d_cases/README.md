# Mesh Adaptation for 2D Cases

This folder contains a standalone, manual demonstration of the
mean-free-path-based mesh adaptation procedure for 2D DSMC cases. The
example geometry is a cylinder in a 2D rectangular domain.

The same procedure is automated end-to-end by `all_run.sh` at the
repository root. The standalone scripts in this folder are kept for
illustration: each step is short, self-contained, and exercised
individually so that the overall workflow can be inspected and modified.

---

## Files

| File | Purpose |
|------|---------|
| `2d_cylinder_adaptive_mesh.geo` | Gmsh geometry file. Defines the domain, the cylinder, the boundary tags, and the AMR background-field setup that reads from `mfp.pos`. |
| `Amr_2d_case.sh` | Shell driver that runs Gmsh, the DSMC solver, and the field extractor in sequence for the 2D case. |
| `csv_to_pos.py` | Python (pvpython) script that reads the DSMC PVD output, exports the mean-free-path field to a CSV, and writes a `.pos` file in the format Gmsh expects. |
| `Step 1: Generate Pos & CSV file.md` | Explanation of the field extraction step, with the pvpython code block. |
| `Step 2: Import POS file in Gmsh.md` | Explanation of how the `.pos` file is consumed by Gmsh through the `Background Field` mechanism. |
| `Step 3: Run DSMC Simulation with New Mesh.md` | Explanation of the re-run on the refined mesh. |

---

## Workflow

The procedure consists of five steps. The first two run the baseline
simulation; steps three through five form the adaptation loop and can be
repeated as many times as needed.

1. **Run the baseline DSMC simulation** on a uniform initial mesh.
2. **Extract the mean-free-path field** from the simulation output. The
   pvpython script `csv_to_pos.py` reads the PVD file, writes a CSV
   containing `(x, y, z, mean_free_path)` per grid point, and converts
   that CSV into the Gmsh `.pos` PostView format.
3. **Generate the refined mesh** by running Gmsh on the `.geo` file. The
   `.geo` merges the `.pos` file as a background scalar field, and Gmsh
   uses it to set the local cell size. After this step, the new mesh
   replaces the previous one.
4. **Re-run the DSMC simulation** on the refined mesh. The new solution
   is written to a fresh PVD file.
5. **Iterate** by returning to step 2 with the new PVD file.

The full automated equivalent of this loop is `all_run.sh`. For a
production workflow that loop is preferable, but the standalone scripts
in this folder are useful for understanding the underlying procedure or
for adapting individual steps to a different solver.

---

## Notes

The extraction script (`csv_to_pos.py`) is the original DSMC-only version.
The repository root contains a newer universal version, `final.py`, which
supports both the DSMC mean-free-path workflow and the OpenFOAM gradient-
based workflow. New work should use `final.py`; the older script is kept
in this folder for archival reference.

The `2d_cylinder_adaptive_mesh.geo` file demonstrates the minimum Gmsh
configuration required for AMR: the geometry, the patch tags, the
`Merge "mfp.pos"` directive, the `PostView` field setup, and the
`Background Field` assignment. The same pattern is used in the AMR `.geo`
files of the automated test cases.
