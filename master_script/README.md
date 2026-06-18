# Master Pipeline Scripts

This folder contains the orchestrator and the wrapper scripts that
together drive the **full** AMR pipeline — generate the uniform mesh,
run the solver, extract the sizing field, regenerate the mesh, and
repeat for the configured number of iterations.

Running the full pipeline **requires the COMET DSMC solver** (for
DSMC cases) or **OpenFOAM v2406** (for the OpenFOAM case). Without
those installed you cannot run anything here end-to-end. If you only
want to see the mesh-adaptation step work, use the mesh-only demos
under [`../Mesh_adaptation_for_2d_cases/`](../Mesh_adaptation_for_2d_cases/),
[`../Mesh_adaptation_for_3d_cases/`](../Mesh_adaptation_for_3d_cases/),
and [`../Mesh_adaptation_for_openfoam_cases/`](../Mesh_adaptation_for_openfoam_cases/)
instead — those need only Gmsh (and ParaView if you want to
regenerate the sizing field) and do not invoke any solver.

---

## Files

| File | What it is |
|------|------------|
| `all_run.sh` | The master orchestrator. Reads `amr_pipeline.input` and executes one or more AMR loops end-to-end. Calls the configured wrapper scripts for the solver and `final.py` for the field extraction. |
| `amr_pipeline.input` | Configuration template — every key the pipeline reads. Each test case under `../test_cases/` carries its own copy of this file with case-specific values. |
| `final.py` | Field-extraction script executed under `pvpython`. Two modes: `direct` (reads an existing scalar column such as the DSMC mean free path) and `gradient` (computes `|grad(field)|` and applies the sizing formula). |
| `csv_to_pos.py` | Original DSMC-only extractor retained for backward compatibility with older inputs. New cases should use `final.py`. |
| `run_openfoam.sh` | OpenFOAM wrapper for the baseline (uniform) mesh run. Calls `gmshToFoam`, fixes boundary patch types, runs the solver, exports VTK. |
| `run_openfoam_amr.sh` | OpenFOAM wrapper for AMR-mesh runs. Differs from `run_openfoam.sh` only in which mesh file it reads (`sim_mesh_amr` instead of `sim_mesh`). |
| `build_pvd_from_steps.sh` | Builds a ParaView `.pvd` collection from per-step VTU files. Called by `all_run.sh` when `pvd_create = true`. |

For DSMC runs, the case scripts (`case_script` and `case_script_amr`
in `amr_pipeline.input`) point at the COMET launchers
(`run_centos_gmsh_nparts=*_groupsize=*.sh`) that COMET supplies
separately. For OpenFOAM runs, they point at `run_openfoam.sh` and
`run_openfoam_amr.sh` in this folder.

---

## What You Need to Run the Full Pipeline

| Tool | Tested version | Purpose |
|------|----------------|---------|
| Gmsh | 4.11.1 | Mesh generation from `.geo` files |
| ParaView | 5.13.2 (MPI build) | `pvpython` for `final.py` |
| OpenFOAM | v2406 | Required for the OpenFOAM test case |
| **COMET DSMC** | (lab-internal) | **Required for every DSMC test case.** Maintained separately by the Computational Gas Dynamics Lab. |
| PUMI-PIC | (lab-internal) | Required only for partitioned (MPI-parallel) DSMC runs |
| Python 3 | 3.9 or newer | Inline boundary-fix script in the OpenFOAM wrapper |
| Bash | 4.0 or newer | The orchestrator language |

Without COMET, the DSMC cases cannot be run from scratch; without
OpenFOAM, the OpenFOAM case cannot be run from scratch. In either
situation, the mesh-only demos under the
`../Mesh_adaptation_for_*_cases/` folders are the alternative — they
reproduce the AMR mesh-generation step from a pre-computed solver
result that is bundled with the repository.

---

## How the Master Script Is Invoked

The master script is meant to be invoked **from inside a test case
folder**, not from this folder. Each test case under
`../test_cases/` keeps its own `amr_pipeline.input` with case-specific
values, and `all_run.sh` auto-detects the case folder from the
current working directory.

Typical workflow:

```bash
cd ../test_cases/openfoam_2d_mach3_cylinder
# Edit amr_pipeline.input: gmsh_bin, pvpython, foam_source
../../master_script/all_run.sh
```

```bash
cd ../test_cases/comet_2d_axisym_psi
# Edit amr_pipeline.input: gmsh_bin, pvpython, pumi_bin
../../master_script/all_run.sh
```

Both `case_script` and `case_script_amr` in the case's
`amr_pipeline.input` are relative paths that point back into this
folder (e.g. `../../master_script/run_openfoam.sh`).

For the full list of input-file keys, the workflow diagram, and the
sizing formula, see the top-level [`../README.md`](../README.md).
