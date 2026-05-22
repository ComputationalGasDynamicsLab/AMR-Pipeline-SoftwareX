# AMR-Pipeline-SoftwareX

Reproducibility package for the SoftwareX submission:

> *Automated mean-free-path-based AMR for rarefied gas flow simulations.*
> Shahriyar, F., Diallo, A., Zhang, C. (in preparation, 2026).

The repository is the automated adaptive mesh refinement (AMR) pipeline
described in the paper, packaged with two reference test cases and the
archived results from previous runs of those cases. A reader can
reproduce both reference cases end-to-end, or inspect the bundled
results without running the solver.

The pipeline uses [Gmsh](https://gmsh.info/) as the mesh generator and
is solver-agnostic. Two solver families are demonstrated here:

- **DSMC** simulations driven by the local mean free path
- **CFD** simulations driven by the gradient of a chosen scalar field
  (pressure, density, temperature)

Each AMR loop runs the solver, extracts a per-point sizing field from
the result, regenerates the mesh from the original geometry, and re-runs
the solver on the refined mesh.

---

## 1. Repository Layout

```
.
├── README.md                          ← this file
├── TUTORIAL.md                        ← end-to-end walkthrough
│
├── master_script/                     ← full-pipeline scripts (solver required)
│   ├── README.md
│   ├── all_run.sh                     ← pipeline orchestrator
│   ├── amr_pipeline.input             ← configuration template
│   ├── final.py                       ← field extraction (pvpython)
│   ├── csv_to_pos.py                  ← legacy DSMC-only extractor
│   ├── build_pvd_from_steps.sh        ← helper for building .pvd time series
│   ├── run_openfoam.sh                ← OpenFOAM wrapper, baseline mesh
│   └── run_openfoam_amr.sh            ← OpenFOAM wrapper, AMR mesh
│
├── mesh_demo/                         ← mesh-only demos (NO solver needed)
│   ├── 2d_case/                       ← COMET 2D cylinder demo
│   ├── 3d_case/                       ← COMET 3D cylinder demo
│   └── openfoam_case/                 ← OpenFOAM 2D Mach 3 cylinder demo
│
├── Mesh_adaptation_for_2d_cases/      ← standalone manual 2D DSMC tutorial
├── Mesh_adaptation_for_3d_cases/      ← standalone manual 3D DSMC tutorial
│
└── test_cases/                        ← full reproducible cases (solver required)
    ├── openfoam_2d_mach3_cylinder/    ← reproducible 2D CFD case (Mach 3 cylinder)
    └── comet_2d_axisym_psi/           ← reproducible 2D DSMC case (plume–surface)
```

The two folders under `test_cases/` are the focus of the
reproducibility package. Each folder is self-contained: it has the
geometry, the meshes, the solver input, the run script, and the
archived results from a verified previous run.

| Path | What it is |
|------|------------|
| `master_script/` | **Full-pipeline scripts.** Contains the orchestrator `all_run.sh`, the field extractor `final.py`, the OpenFOAM wrappers, and the configuration template `amr_pipeline.input`. Running the full pipeline (solver in the loop, multiple AMR iterations) requires either the **COMET DSMC solver** (for DSMC cases) or **OpenFOAM v2406** (for the OpenFOAM case). See [`master_script/README.md`](master_script/README.md). |
| `mesh_demo/` | **Mesh-only demos.** Three small subfolders (2D COMET cylinder, 3D COMET cylinder, OpenFOAM 2D Mach 3 cylinder) each bundle a uniform mesh and a pre-computed solver result, and ship a one-script driver that runs the field-extraction step and produces the AMR-refined mesh. **No solver is needed** — only Gmsh and ParaView's `pvpython`. See [`mesh_demo/README.md`](mesh_demo/README.md). |
| `Mesh_adaptation_for_2d_cases/` and `Mesh_adaptation_for_3d_cases/` | Standalone DSMC examples that show the manual (non-automated) workflow step by step. Useful for understanding the underlying procedure. |
| `test_cases/openfoam_2d_mach3_cylinder/` | Self-contained 2D CFD test case with bundled results. Mach 3 cylinder at 50 km altitude, `rhoCentralFoam`, three AMR loops driven by `|grad(p)|`. Driven by `master_script/all_run.sh`. |
| `test_cases/comet_2d_axisym_psi/` | Self-contained 2D DSMC test case with bundled results. Axisymmetric plume–surface impingement, three AMR loops driven by mean free path. Driven by `master_script/all_run.sh`. |

---

## 2. Quick Start

There are two ways to use this repository, depending on what you have
installed and what you want to see.

### Option A — Run a mesh-only demo (no solver required)

The fastest entry point. Three demos under `mesh_demo/` ship a uniform
mesh and a pre-computed solver result, and produce the AMR-refined
mesh in seconds without invoking COMET or OpenFOAM. Only Gmsh and
ParaView's `pvpython` are needed.

```bash
cd mesh_demo/2d_case          # or 3d_case, or openfoam_case
# Edit gmsh_bin and pvpython paths in amr_pipeline.input
./generate_amr_mesh.sh
```

After the script finishes, `<case>_amr.msh` in the same folder is the
AMR-refined mesh. Open it in Gmsh side by side with the bundled
uniform mesh to see the refinement. Full details are in
[`mesh_demo/README.md`](mesh_demo/README.md).

### Option B — Reproduce a full pipeline run (solver required)

The two cases under `test_cases/` are full reproducible packages with
the solver in the loop and three AMR iterations. Each has its own
`README.md`. Running them needs OpenFOAM v2406 (for the OpenFOAM case)
or the COMET DSMC solver (for the COMET case).

#### Reproduce the 2D OpenFOAM case

```bash
cd test_cases/openfoam_2d_mach3_cylinder
# Edit the binary paths in amr_pipeline.input:
#   gmsh_bin, pvpython, foam_source
../../master_script/all_run.sh
```

Three AMR iterations on a Mach 3 cylinder at 50 km altitude, total wall
time around 80 minutes on 8 cores.

#### Reproduce the 2D COMET DSMC case

```bash
cd test_cases/comet_2d_axisym_psi
# Edit the binary paths in amr_pipeline.input:
#   gmsh_bin, pvpython, pumi_bin
../../master_script/all_run.sh
```

#### Inspect the bundled results without running the solver

Both test cases ship with the archived results from a verified previous
run. Open the final iteration in ParaView:

```bash
paraview test_cases/openfoam_2d_mach3_cylinder/comet_result/output_amr3_result/field/auto_field.pvd
paraview test_cases/comet_2d_axisym_psi/comet_result/output_amr3_result/field/auto_field.pvd
```

This is the recommended way to verify the pipeline output before
running it yourself.

---

## 3. Pipeline Architecture

The pipeline is structured around a single orchestrator (`all_run.sh`)
and a set of pluggable wrapper scripts that implement the solver-
specific work. The orchestrator is unaware of the solver: it only
requires the wrapper to produce VTK output at a fixed path.

```
.geo  ──►  Gmsh  ──►  .msh  ──►  Solver wrapper  ──►  VTK files
                                                           │
                                                           ▼
                                              pvpython final.py
                                                           │
                                                           ▼
                                                 sizing field (.pos)
                                                           │
                                                           ▼
.geo (AMR)  ──►  Gmsh + Background Field  ──►  refined .msh  ──►  Solver  ──► …
```

Two `.geo` files are used per case:

- The baseline `.geo`: generates the initial mesh on the first iteration.
  No background field, fixed characteristic length range.
- The AMR `.geo`: identical geometry, but reads the `.pos` background
  field written by `final.py` and uses it to control local cell size.
  Used on every iteration after the first.

Communication between the solver and Gmsh is through a single file,
`mfp.pos`, written in Gmsh's PostView format. This format consists of
scalar points `SP(x, y, z){h}` that specify the desired local mesh size
at each grid point. Gmsh interpolates between the points using its
`Background Field` mechanism.

---

## 4. Configuration

All pipeline behaviour is controlled by `amr_pipeline.input`. The file
uses a simple namelist-style format:

```fortran
&amr_input
  loops              = 3
  gmsh_bin           = /path/to/gmsh
  pvpython           = /path/to/pvpython
  ...
/
```

Every key has a default value. Users only need to set the keys they
want to override.

### 4.1 Pipeline Settings

| Key | Description |
|-----|-------------|
| `loops` | Number of AMR iterations. The first iteration runs the baseline mesh; subsequent iterations refine. Default: `3`. |
| `base_dir` | Working directory. Auto-detected from the script location if unset. |
| `gmsh_bin` | Absolute path to the Gmsh binary. Auto-detected from `$PATH` if unset. |
| `pvpython` | Absolute path to ParaView's `pvpython`. Must be the MPI build of ParaView; the OSMesa build lacks several filters used by `final.py`. |

### 4.2 Geometry and Mesh

| Key | Description |
|-----|-------------|
| `geo_file` | Gmsh `.geo` file used for the baseline mesh on iteration 1. |
| `geo_file_amr` | Gmsh `.geo` file used for iterations 2 onward. Must merge the `.pos` background field. |
| `sim_mesh` | Output filename of the baseline mesh. |
| `sim_mesh_amr` | Output filename of each AMR mesh. |
| `start_amr_mesh` | Optional. Path to an existing AMR mesh to use as the starting point, skipping the baseline run. |

### 4.3 Solver Wrapper Scripts

| Key | Description |
|-----|-------------|
| `case_script` | Wrapper script invoked for the baseline mesh run. |
| `case_script_amr` | Wrapper script invoked for AMR mesh runs. |
| `final_py` | Path to the field-extraction script. Default: `final.py`. |

For DSMC runs, the case scripts are the COMET-supplied launchers
(`run_centos_gmsh_nparts=1_groupsize=1.sh` and the AMR variant). For
OpenFOAM runs, they are `run_openfoam.sh` and `run_openfoam_amr.sh`.

### 4.4 Field Extraction

| Key | Description |
|-----|-------------|
| `extraction_mode` | `direct` reads an existing scalar column (DSMC mean-free-path workflow). `gradient` computes `|grad(field)|` and applies the sizing formula (CFD workflow). |
| `gradient_field` | Scalar field whose gradient is computed. Required when `extraction_mode = gradient`. Typical values: `p`, `rho`, `T`. |
| `mfp_column` | Column name read from the CSV by `final.py`. In `direct` mode this is typically `mean free path`; in `gradient` mode it is `<gradient_field>_sizing` (e.g. `p_sizing`). |
| `pos_scale` | Multiplier applied to every value before writing the `.pos` file. Default: `1.0`. |

### 4.5 Sizing Formula (Gradient Mode)

In `gradient` mode the per-point cell size is computed as

```
h(x) = h_min + (h_max − h_min) / (1 + α · |grad f(x)| / max |grad f|)
```

The three free parameters are:

| Key | Description |
|-----|-------------|
| `sizing_min` | Lower bound `h_min` on the cell size, in metres. |
| `sizing_max` | Upper bound `h_max` on the cell size, in metres. |
| `sizing_scale` | Dimensionless steepness `α`. Larger values produce sharper refinement around high-gradient regions. Default: `100.0`. |

In high-gradient regions the formula yields `h ≈ h_min`; in smooth
regions it yields `h ≈ h_max`. Setting `α = 0` produces a uniform mesh
at `h_max`; setting `α → ∞` approaches a step function.

### 4.6 OpenFOAM Settings

These keys are read by the OpenFOAM wrapper scripts and are ignored in
DSMC runs.

| Key | Description |
|-----|-------------|
| `foam_source` | Absolute path to the OpenFOAM `etc/bashrc` to source. |
| `solver` | Name of the OpenFOAM solver binary. Examples: `rhoCentralFoam`, `sonicFoam`, `simpleFoam`. |
| `case_dir` | Path to the OpenFOAM case directory, relative to `base_dir`. Must contain `0.orig/`, `constant/`, and `system/`. |
| `boundary_fix` | Comma-separated list of `patch:type` rules applied to `constant/polyMesh/boundary` after `gmshToFoam`. Required because Gmsh writes all patches as type `patch`. Example: `frontAndBack:empty, wall:wall`. |
| `foam_sigfpe` | If `true`, OpenFOAM traps floating-point exceptions; if `false`, the solver is allowed to push through transient numerical artefacts. AMR runs are typically more stable with `false`. |

### 4.7 Output and Archiving

| Key | Description |
|-----|-------------|
| `result_root` | Root directory for archived results. Default: `<base_dir>/comet_result`. |
| `pv_output_dir` | Glob pattern matching the solver's per-iteration output directories. Default: `field*`. |
| `log_dir` | Directory for pipeline logs. Default: `<base_dir>/logs`. |
| `pvd_create` | If `true`, the orchestrator builds a `.pvd` collection from per-step VTU files at the end of each iteration. |
| `pvd_pattern` | Glob used by the PVD builder to find VTU files. Default: `field*.vtu`. |
| `raw_csv` | Path to the full point-data export from `pvpython`. Default: `gmsh/all_data.csv`. |
| `filtered_csv` | Path to the filtered `(x, y, z, sizing)` CSV. Default: `gmsh/filtered_mfp.csv`. |
| `pos_file` | Path to the Gmsh `.pos` background view consumed by the AMR `.geo` file. Default: `gmsh/mfp.pos`. |

---

## 5. Workflow Summary

For each iteration `i = 1 … loops`, the orchestrator performs the
following sequence:

1. **Mesh generation.** Gmsh runs the appropriate `.geo` file
   (`geo_file` for `i = 1`, `geo_file_amr` thereafter) and produces a
   `.msh` file. A numbered backup is saved under `gmsh/`.
2. **Solver run.** The orchestrator calls the configured wrapper
   script. For OpenFOAM, the wrapper converts the mesh, fixes boundary
   types, copies `0.orig/` to `0/`, runs the solver, and exports the
   result to VTK.
3. **Result archiving.** The complete result tree is copied into a per-
   iteration archive directory (e.g. `comet_result/output_amr1_result/`).
4. **PVD assembly.** A `.pvd` time-series file is built from the per-
   step VTU files, so that `pvpython` can open the result as a single
   dataset.
5. **Field extraction.** `pvpython final.py` reads the latest timestep,
   either reads an existing scalar column (`direct` mode) or computes a
   gradient and applies the sizing formula (`gradient` mode), and
   writes `gmsh/mfp.pos`.
6. **Mesh regeneration.** Gmsh runs `geo_file_amr`, which reads
   `mfp.pos` as a `Background Field` and produces a refined mesh for
   iteration `i + 1`.

After `loops` iterations, the final mesh and result are left in place
at the standard locations (`gmsh/<sim_mesh_amr>` and
`comet_result/output_amr<loops>_result/`), and all intermediate states
are preserved as numbered backups.

---

## 6. Software Requirements

The pipeline shells out to the following external tools. Versions
listed are those tested on the development host (CentOS Stream 9, GCC
11.5).

| Tool | Tested version | Purpose |
|------|----------------|---------|
| Gmsh | 4.11.1 | Mesh generation |
| OpenFOAM | v2406 | CFD solver |
| ParaView | 5.13.2 (MPI build) | Field extraction via `pvpython` |
| Python | 3.9 or newer | Boundary-patch fix script in the OpenFOAM wrapper |
| Bash | 4.0 or newer | Orchestrator language |

For DSMC runs the COMET solver is also required. COMET is maintained
separately by the Computational Gas Dynamics Lab.

---

## 7. Where to Go Next

- The mesh-only demos (no solver needed): [`mesh_demo/`](mesh_demo/)
  with subfolders [`2d_case/`](mesh_demo/2d_case/),
  [`3d_case/`](mesh_demo/3d_case/), and
  [`openfoam_case/`](mesh_demo/openfoam_case/).
- The reproducible 2D CFD case: [`test_cases/openfoam_2d_mach3_cylinder/`](test_cases/openfoam_2d_mach3_cylinder/)
- The reproducible 2D DSMC case: [`test_cases/comet_2d_axisym_psi/`](test_cases/comet_2d_axisym_psi/)
- The standalone manual DSMC tutorials: [`Mesh_adaptation_for_2d_cases/`](Mesh_adaptation_for_2d_cases/) and [`Mesh_adaptation_for_3d_cases/`](Mesh_adaptation_for_3d_cases/)


