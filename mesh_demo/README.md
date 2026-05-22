# Mesh Adaptation Demo

This folder contains three small, self-contained demonstrations of the
AMR mesh-adaptation step alone. Each demo bundles:

- the geometry (`.geo` files for the baseline and AMR meshes),
- a **uniform mesh** that the demo starts from (`.msh`),
- a **pre-computed solver result** in `precomputed_result/`,
- a one-script driver `generate_amr_mesh.sh` that takes the bundled
  result, runs the field-extraction step, and produces the **AMR
  mesh** with Gmsh.

The point of the demo is that **you do not need to run the simulation
yourself**. Producing the AMR mesh from the bundled result takes
seconds and only requires Gmsh and ParaView's `pvpython`. The original
solver run (COMET DSMC or OpenFOAM) that produced the bundled result
took hours.

If you want to run the **full** AMR pipeline — generate the uniform
mesh, run the solver, extract the sizing field, regenerate the mesh,
and repeat for several iterations — use the master script
`all_run.sh` at the top of the repository. Running the full pipeline
requires the COMET DSMC solver for the COMET demos and OpenFOAM v2406
for the OpenFOAM demo; the demos in this folder do not.

---

## What's in Each Subfolder

| Subfolder | Solver | Geometry | Notes |
|-----------|--------|----------|-------|
| `2d_case/` | COMET DSMC | 2D flow over a cylinder | Mean-free-path-driven AMR |
| `3d_case/` | COMET DSMC | 3D flow over a cylinder | Mean-free-path-driven AMR |
| `openfoam_case/` | OpenFOAM `rhoCentralFoam` | 2D Mach 3 cylinder at 50 km altitude | Pressure-gradient-driven AMR |

Each subfolder has its own `README.md` with the full file layout and
the run command for that case.

---

## How to Run a Demo

Each subfolder has its own `amr_pipeline.input` that holds every
configurable value — the binary paths, the geometry and mesh
filenames, the field-extraction settings, and the names of the
intermediate files. **You edit the input file, not the script.** The
procedure is the same for all three subfolders:

```bash
cd mesh_demo/<case_folder>
# Edit amr_pipeline.input — set gmsh_bin and pvpython to your absolute
# paths.  Everything else has sensible defaults.
./generate_amr_mesh.sh
```

After the script finishes, the new AMR-refined mesh is in the same
folder as `<case>_amr.msh`. Open it in Gmsh side by side with the
bundled uniform mesh to see the refinement:

```bash
gmsh 2d_cylinder.msh        # the uniform starting mesh
gmsh 2d_cylinder_amr.msh    # the AMR-refined mesh produced by the demo
```

The demo also writes two intermediate files for inspection:

- `mfp.pos` — the Gmsh PostView that drives the cell sizing
- `filtered_mfp.csv` — `(x, y, z, value)` rows, one per grid point in
  the bundled solver result

---

## What the Demo Script Does

`generate_amr_mesh.sh` is the same procedure in every subfolder, with
small differences in the extraction-mode arguments. Internally it:

1. Reads the bundled `precomputed_result/field/auto_field.pvd` from
   this case folder.
2. Invokes `pvpython final.py` (the script lives at the repository
   root) on that PVD. For COMET cases the extractor runs in `direct`
   mode and reads the `mean free path` field that COMET writes
   natively. For the OpenFOAM case it runs in `gradient` mode,
   computes `|grad(p)|`, and converts it into a sizing field with the
   formula

   ```
   h(x) = h_min + (h_max − h_min) / (1 + α · |grad p|/max |grad p|)
   ```

   with `h_min = 0.002 m`, `h_max = 0.015 m`, `α = 100`.
3. Writes `mfp.pos` in Gmsh PostView format (`SP(x, y, z){h}` records).
4. Runs Gmsh on the AMR `.geo` file. The `.geo` merges `mfp.pos` as a
   `Background Field` so the local cell size honours the sizing values
   at each grid point.
5. Writes the AMR mesh (`<case>_amr.msh`) into the same folder.

That is the whole AMR-mesh-generation step of the pipeline.

---

## How This Differs from the Full Pipeline

| | This demo | Full pipeline (`../all_run.sh`) |
|--|-----------|--------------------------------|
| Generates the **uniform** mesh? | No (bundled) | Yes (Gmsh on `<case>.geo`) |
| Runs the **solver**? | No (bundled result is used as-is) | Yes (COMET or OpenFOAM) |
| Extracts the **sizing field**? | Yes | Yes |
| Generates the **AMR mesh**? | Yes (single iteration only) | Yes (per loop) |
| Number of AMR loops | 1 (mesh-only) | Configurable, typically 3 |
| Required external tools | Gmsh + ParaView (`pvpython`) | Gmsh + ParaView + COMET (or OpenFOAM) |
| Wall time | seconds | minutes to hours |
| Where to run from | `mesh_demo/<case_folder>/` | `test_cases/<case_folder>/` |

For the full pipeline runs with bundled archived results from a
verified previous execution, see the cases under
[`../test_cases/`](../test_cases/).
