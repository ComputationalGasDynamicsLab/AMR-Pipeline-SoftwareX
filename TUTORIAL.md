# Tutorial — Running the AMR Pipeline From Start to Finish

This tutorial walks a new user through the AMR pipeline from a clean
checkout of the repository all the way to viewing the final adapted
results in ParaView. It covers the bundled 2D Mach 3 cylinder test
case (the one in `test_cases/openfoam_2d_mach3_cylinder/`) end to end.
Once that case has been run successfully, adapting the same procedure
to a different geometry or to the COMET DSMC case is a small step.

The tutorial assumes a Linux machine. Every command shown here is one
that has been run on the development host. If a step looks different
on your system, that is worth investigating before continuing.

---

## 1. What You Need Before Starting

The pipeline is a set of bash and Python scripts that drive three
external tools. Make sure each one is installed and on your `$PATH`,
or that you have the absolute path written down.

| Tool | Tested version | What the pipeline uses it for |
|------|----------------|-------------------------------|
| Gmsh | 4.11.1 | Mesh generation from `.geo` files |
| OpenFOAM | v2406 | The CFD solver itself, plus `gmshToFoam` and `foamToVTK` |
| ParaView | 5.13.2 (MPI build) | `pvpython` runs the field-extraction script |
| Python 3 | 3.9 or newer | Inline boundary-fix script in the OpenFOAM wrapper |
| Bash | 4.0 or newer | The pipeline orchestrator |

A quick check that everything is reachable:

```bash
gmsh --version
pvpython --version
which rhoCentralFoam        # OpenFOAM solver
which gmshToFoam            # OpenFOAM mesh converter
which foamToVTK             # OpenFOAM VTK exporter
```

If any of these print "command not found", the corresponding tool is
not on your `$PATH`. You can either add it to `$PATH` or give the
absolute path to the pipeline through `amr_pipeline.input` (see
section 3 below).

---

## 2. Get the Repository

```bash
git clone https://github.com/ComputationalGasDynamicsLab/AMR-Pipeline-SoftwareX.git
cd AMR-Pipeline-SoftwareX
```

You should see this top-level layout:

```
AMR-Pipeline-SoftwareX/
├── README.md                          ← high-level overview
├── TUTORIAL.md                        ← this file
├── all_run.sh                         ← pipeline orchestrator
├── amr_pipeline.input                 ← single configuration file
├── final.py                           ← field extractor (pvpython)
├── csv_to_pos.py                      ← legacy DSMC extractor
├── build_pvd_from_steps.sh            ← .pvd helper
├── run_openfoam.sh                    ← OpenFOAM wrapper, baseline mesh
├── run_openfoam_amr.sh                ← OpenFOAM wrapper, AMR mesh
├── Mesh_adaptation_for_2d_cases/      ← standalone DSMC tutorials
├── Mesh_adaptation_for_3d_cases/
└── test_cases/
    ├── openfoam_2d_mach3_cylinder/    ← bundled CFD case (this tutorial)
    └── comet_2d_axisym_psi/           ← bundled DSMC case
```

Move into the bundled CFD test case:

```bash
cd test_cases/openfoam_2d_mach3_cylinder
ls
```

Expected listing:

```
2d_cylinder.msh        amr_pipeline.input    comet_result/
2d_cylinder_amr.msh    README.md             gmsh/
                                             openfoam_case/
```

The case folder is intentionally minimal: it contains only the
case-specific inputs (geometry, meshes, OpenFOAM `0.orig/system/constant`)
and the archived results from a previous verified run. The pipeline
scripts (`all_run.sh`, `run_openfoam.sh`, `run_openfoam_amr.sh`,
`final.py`, `build_pvd_from_steps.sh`) live once at the top of the
repository and are invoked through the relative paths set in this
case's `amr_pipeline.input`.

If you only want to inspect the bundled output, jump to section 8.

---

## 3. Edit the One Configuration File

Open `amr_pipeline.input`. The whole pipeline reads from this single
file. Change three lines to point at your local binaries:

```fortran
gmsh_bin    = /your/path/to/gmsh
pvpython    = /your/path/to/pvpython
foam_source = /your/path/to/OpenFOAM-v2406/etc/bashrc
```

Leave every other key at its default. The relevant defaults for this
case are:

| Key | Value | What it controls |
|-----|-------|------------------|
| `loops` | `3` | Number of AMR iterations to run |
| `geo_file` | `2d_cylinder.geo` | Geometry for the baseline mesh |
| `geo_file_amr` | `2d_cylinder_amr.geo` | Geometry for the AMR mesh |
| `sim_mesh` | `2d_cylinder.msh` | Output filename of the baseline mesh |
| `sim_mesh_amr` | `2d_cylinder_amr.msh` | Output filename of each AMR mesh |
| `case_script` | `../../run_openfoam.sh` | Wrapper for the baseline run (lives at the repo root) |
| `case_script_amr` | `../../run_openfoam_amr.sh` | Wrapper for each AMR run (lives at the repo root) |
| `extraction_mode` | `gradient` | Use `|grad(field)|` to drive AMR |
| `gradient_field` | `p` | Field whose gradient drives refinement (pressure) |
| `sizing_min` | `0.002` | Smallest cell size in metres |
| `sizing_max` | `0.015` | Largest cell size in metres |
| `sizing_scale` | `100.0` | How sharply the mesh refines around the gradient |
| `solver` | `rhoCentralFoam` | OpenFOAM solver to invoke |
| `boundary_fix` | `frontAndBack:empty, wall:wall` | Patch types to set after `gmshToFoam` |

Section 4 of the top-level `README.md` explains every key in detail.

---

## 4. Understand What's About to Happen

Before starting the run, it helps to know what the pipeline will
actually do. For the bundled case, with `loops = 3`, the orchestrator
performs the following sequence:

1. **Iteration 1, baseline.**
   - Run Gmsh on `2d_cylinder.geo` → produces `2d_cylinder.msh`.
   - Run OpenFOAM on `2d_cylinder.msh` → produces VTK output.
   - Archive the result tree as `comet_result/output_normal1_result/`.
   - Run `pvpython final.py` to compute `|grad(p)|` and write
     `gmsh/mfp.pos`.
   - Run Gmsh on `2d_cylinder_amr.geo` (which reads `gmsh/mfp.pos` as
     a Gmsh `Background Field`) → produces `2d_cylinder_amr.msh`.
   - Run OpenFOAM on `2d_cylinder_amr.msh` → produces VTK output.
   - Archive the result tree as `comet_result/output_amr1_result/`.

2. **Iteration 2, AMR-only.**
   - Run `pvpython final.py` again on the iteration-1 AMR result.
   - Run Gmsh again on `2d_cylinder_amr.geo`.
   - Run OpenFOAM on the new `2d_cylinder_amr.msh`.
   - Archive as `comet_result/output_amr2_result/`.

3. **Iteration 3, AMR-only.** Same as iteration 2; archive as
   `comet_result/output_amr3_result/`.

At each iteration the orchestrator also keeps a numbered backup of the
mesh file under `gmsh/` (so you end up with `2d_cylinder1.msh`,
`2d_cylinder_amr1.msh`, `2d_cylinder_amr2.msh`,
`2d_cylinder_amr3.msh`). All intermediate meshes are preserved for
later inspection.

The total wall time on an eight-core desktop is roughly 80 minutes for
this case.

---

## 5. Launch the Pipeline

From inside `test_cases/openfoam_2d_mach3_cylinder/`, invoke the
orchestrator at the repository root:

```bash
../../all_run.sh
```

`all_run.sh` auto-detects the current working directory as the case
base, so all output is written into the test case folder. The OpenFOAM
wrapper scripts at the repository root are invoked automatically
through the `case_script` and `case_script_amr` keys in
`amr_pipeline.input`.

The orchestrator first prints a configuration summary so you can
confirm everything is wired up correctly. Look for lines like:

```
Using input file: /your/path/test_cases/openfoam_2d_mach3_cylinder/amr_pipeline.input
Auto-detected gmsh binary: /your/path/gmsh

Running pipeline with:
  Base dir            /your/path/test_cases/openfoam_2d_mach3_cylinder
  Gmsh binary         /your/path/gmsh
  Loops               3
  Geo                 .../gmsh/2d_cylinder.geo
  Geo AMR             .../gmsh/2d_cylinder_amr.geo
  Mesh                .../2d_cylinder.msh
  Mesh AMR            .../2d_cylinder_amr.msh
  Case script         .../run_openfoam.sh
  Case AMR            .../run_openfoam.sh
```

If anything in this summary looks wrong (most often a misspelt path),
press `Ctrl-C` and fix `amr_pipeline.input` before continuing.

If the summary looks right, the pipeline begins:

```
===============================================
 ITERATION 1 / 3
===============================================
Generating normal mesh with Gmsh...
Saving backup mesh → gmsh/2d_cylinder1.msh
Updating simulation mesh → 2d_cylinder.msh
Running MPI case for the normal mesh...
=============================================
 OpenFOAM AMR Pipeline — Baseline (uniform) Mesh Run
 Mesh:   .../2d_cylinder.msh
 Solver: rhoCentralFoam
=============================================
[STEP 1] gmshToFoam...
[STEP 2] Fixing boundaries...
[OK] Boundaries fixed
[STEP 3] Setting up initial conditions...
[STEP 4] Running rhoCentralFoam...
```

The `rhoCentralFoam` step is the slow one. It typically takes
8–12 minutes on the baseline mesh and 15–25 minutes per AMR
iteration. While it runs, you can inspect the live OpenFOAM log:

```bash
tail -f openfoam_case/log.rhoCentralFoam
```

Each iteration ends with the result-archiving step:

```
[STEP 5] foamToVTK...
[STEP 6] Organising VTK output...
=============================================
 Done. 6 timesteps -> .../comet_result/field
=============================================
Archiving ParaView results for normal mesh → .../comet_result/output_normal1_result
Converting results to POS (source: .../auto_field.pvd)...
[INFO] Max p gradient magnitude: 184523.7
[INFO] Wrote 7218 points to POS file: gmsh/mfp.pos
Generating adaptive mesh with Gmsh...
Saving backup amr mesh → gmsh/2d_cylinder_amr1.msh
Updating simulation AMR mesh → 2d_cylinder_amr.msh
Running MPI case for the AMR mesh...
```

After the third iteration completes you should see:

```
All 3 iteration(s) finished.
Backups in: .../gmsh → 2d_cylinder{1..3} and 2d_cylinder_amr{1..3}
Archived results in: .../comet_result → output_normal{1..3}_result, output_amr{1..3}_result
```

---

## 6. Where the Output Lives

After a successful run the test-case folder contains, in addition to
the original files:

```
comet_result/
├── output_normal1_result/    ← baseline solution on the uniform mesh
├── output_amr1_result/       ← solution after the first refinement
├── output_amr2_result/       ← solution after the second refinement
└── output_amr3_result/       ← solution after the third refinement

gmsh/
├── 2d_cylinder.geo                 (geometry, unchanged)
├── 2d_cylinder_amr.geo             (AMR geometry, unchanged)
├── 2d_cylinder.msh                 (latest baseline mesh)
├── 2d_cylinder1.msh                (iteration 1 backup)
├── 2d_cylinder_amr1.msh            (AMR mesh after iteration 1)
├── 2d_cylinder_amr2.msh            (AMR mesh after iteration 2)
├── 2d_cylinder_amr3.msh            (AMR mesh after iteration 3)
├── 2d_cylinder_amr.msh             (latest AMR mesh = amr3.msh)
├── all_data.csv                    (full point-data export)
├── filtered_mfp.csv                (x, y, z, p_sizing extract)
└── mfp.pos                         (Gmsh background field)

logs/
├── output_normal1.txt
├── output_amr1.txt
├── output_amr2.txt
├── output_amr3.txt
└── csv_2_pos_*.txt                 (field-extraction logs)
```

Every intermediate state of the pipeline is preserved here. You can
diff any two iterations of the mesh, plot the cell-count growth, or
re-run just the field extraction on a previous result.

---

## 7. Visualising the Results

ParaView is the standard tool for inspecting the output. Open the
`.pvd` file in any of the archive directories:

```bash
paraview comet_result/output_amr3_result/field/auto_field.pvd
```

In the ParaView pipeline browser, click "Apply" then "Last frame" to
move to the converged solution. Colour the surface by `p` (pressure)
or `U` magnitude. The bow shock should appear as a sharp curved
feature ahead of the cylinder; the wake should extend around 0.3–0.4 m
downstream with two counter-rotating vortices.

To compare the baseline and final-iteration results side by side:

```bash
paraview \
  comet_result/output_normal1_result/field/auto_field.pvd \
  comet_result/output_amr3_result/field/auto_field.pvd
```

In the second view, switch the representation to "Surface with Edges"
to see the AMR cells. The difference between the two meshes — coarse
uniform on the left, refined around the shock and wake on the right —
is the whole point of the pipeline.

To open just the meshes (without the solution) in Gmsh:

```bash
gmsh gmsh/2d_cylinder.msh         # baseline mesh
gmsh gmsh/2d_cylinder_amr3.msh    # mesh after 3 AMR iterations
```

---

## 8. Inspect the Bundled Results Without Running

If you do not have OpenFOAM installed, or you simply want to confirm
the expected output before running the case yourself, ParaView alone
is enough. The repository ships with the archived results from a
previous verified run:

```bash
paraview test_cases/openfoam_2d_mach3_cylinder/comet_result/output_amr3_result/field/auto_field.pvd
```

Likewise for the COMET DSMC case:

```bash
paraview test_cases/comet_2d_axisym_psi/comet_result/output_amr3_result/field/auto_field.pvd
```

Each `output_amr*_result/` directory contains the complete VTK time
series and a `.pvd` collection that ParaView opens directly. Comparing
the bundled `output_amr3_result/` against your own run is a simple way
to verify that your installation is producing the same answer.

---

## 9. Adapting the Pipeline to a New Geometry

Once the bundled case runs cleanly, adapting it to a different problem
is a small change. The minimum steps are:

1. **Write two `.geo` files**, one for the baseline mesh and one for
   the AMR mesh. The two files must produce meshes with the same
   physical-surface names. Look at
   `test_cases/openfoam_2d_mach3_cylinder/gmsh/2d_cylinder.geo` and
   `2d_cylinder_amr.geo` for the structure: the AMR file contains
   three extra lines (`Merge "mfp.pos";`, `Field[1] = PostView;`,
   `Background Field = 1;`) and disables Gmsh's other sizing
   heuristics.
2. **Build the OpenFOAM case directory** (`0.orig/`, `constant/`,
   `system/`) with the boundary names matching the `Physical Surface`
   names in your `.geo`.
3. **Edit `amr_pipeline.input`**:
   - Update `geo_file`, `geo_file_amr`, `sim_mesh`, `sim_mesh_amr` to
     your new filenames.
   - Update `boundary_fix` to map your patch names to OpenFOAM types
     (typical: `frontAndBack:empty, wall:wall`).
   - Pick a `gradient_field` and tune `sizing_min`, `sizing_max`, and
     `sizing_scale` to suit your problem.
4. **Run** `./all_run.sh` from the new case directory.

If your problem is DSMC rather than CFD, the changes are similar but
you point `case_script` and `case_script_amr` at the COMET-supplied
launchers and set `extraction_mode = direct`,
`mfp_column = mean free path`. The bundled `comet_2d_axisym_psi/` case
shows the structure.

---

## 10. Common Pitfalls

A few things that go wrong often enough to be worth flagging up front:

- **`gmshToFoam: parsing error`** — your `.geo` is producing a Gmsh
  v4 mesh file. OpenFOAM's `gmshToFoam` does not read v4 reliably as
  of v2406. Add `Mesh.MshFileVersion = 2.2;` to the `.geo`.
- **`paraview/simple.py not found`** — `pvpython` is from the OSMesa
  build of ParaView. Re-install ParaView using the MPI build.
- **The AMR mesh looks like the baseline mesh** — Gmsh did not read
  `mfp.pos`. Confirm that `geo_file_amr` contains `Merge "mfp.pos";`,
  `Field[1] = PostView;`, and `Background Field = 1;`, and that the
  pipeline actually wrote `gmsh/mfp.pos` after the previous iteration
  (check the size).
- **The solver crashes on iteration 2 or 3** — usually a mesh-quality
  issue. Increase `sizing_min` (try doubling it) and re-run.
- **`bc_typeN` is unknown** — the COMET BC type number does not match
  what is documented in the input file. The numeric mapping is in
  `comet_mesh.hpp`: 0=INLET, 1=DIFFUSIVE_WALL, 2=REFLECTIVE_WALL,
  3=SYMMETRIC_PLANE, 4=OUTLET, 5=PERIODIC, 6=PRESSURE_INLET.

For anything beyond these, the per-step logs in `logs/` and
`openfoam_case/log.*` are the first place to look. Each step of every
iteration writes its own log file, so it is usually clear at which
stage the failure occurred.

---

## 11. Where to Go From Here

- Read the top-level [`README.md`](README.md) for the complete list of
  configuration keys in `amr_pipeline.input`.
- Read the per-case READMEs for the bundled cases:
  [`test_cases/openfoam_2d_mach3_cylinder/README.md`](test_cases/openfoam_2d_mach3_cylinder/README.md)
  and
  [`test_cases/comet_2d_axisym_psi/README.md`](test_cases/comet_2d_axisym_psi/README.md).
- For the manual (non-automated) DSMC workflow with step-by-step
  Markdown notes per stage, see
  [`Mesh_adaptation_for_2d_cases/`](Mesh_adaptation_for_2d_cases/) and
  [`Mesh_adaptation_for_3d_cases/`](Mesh_adaptation_for_3d_cases/).
- The companion repository
  [`Mesh_adaptation_with_GMSH`](https://github.com/ComputationalGasDynamicsLab/Mesh_adaptation_with_GMSH)
  contains the same pipeline source code under active development.
