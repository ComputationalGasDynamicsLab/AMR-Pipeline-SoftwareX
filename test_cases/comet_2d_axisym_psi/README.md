# 2D Axisymmetric Plume–Surface Interaction — COMET DSMC Test Case

This is the reference DSMC test case for the mean-free-path AMR
workflow. It runs a 2D axisymmetric plume impinging on a flat surface,
solved with the in-house COMET DSMC code, with three AMR iterations
driven by the local mean free path.

## Physical setup

| Quantity | Value | Notes |
|---|---|---|
| Geometry | 2D axisymmetric domain | Plume nozzle exit and downstream impingement surface |
| Free-stream velocity | 323 m/s (axial) | `sml_vfx` in `comet.input` |
| Free-stream density | 7.12 × 10⁻³ kg/m³ | `sml_rho_inf` |
| Free-stream temperature | 252.2 K | `sml_T_inf` |
| Wall temperature | 300 K | `sml_T_wall` |
| Species | N₂ | `species_id1 = 2` |
| Maximum timesteps | 100 000 | `sml_maxStep` |
| Variable timestep | enabled | `sml_variable_time = .true.` |
| AMR driver | mean free path | `extraction_mode = direct`, `mfp_column = mean free path` |
| AMR loops | 3 | see `comet_result/output_amr{1,2,3}_result/` |

## Folder layout

The case includes the input file, the geometry, the meshes, the run
scripts, and the archived results from the three AMR iterations. A
reader can inspect the converged solution in ParaView without first
running the case.

| Path | What it is |
|---|---|
| `comet.input` | COMET solver input (BCs, species, sml parameters) |
| `amr_pipeline.input` | Configuration for the AMR pipeline driver (`all_run.sh`) |
| `all_run.sh` | Driver script that runs the three-iteration AMR loop |
| `final.py` | pvpython extractor — `direct` mode reads the mean-free-path field |
| `build_pvd_from_steps.sh` | Builds the `.pvd` index over per-step VTK output |
| `gmsh_generation.sh` | Runs Gmsh on `gmsh/2d_axisym.geo` to produce the baseline mesh |
| `2d_axisym.msh` | Initial uniform mesh used by the first run |
| `2d_axisym_amr.msh` | Final AMR mesh after the third loop |
| `gmsh/2d_axisym.geo` | Baseline geometry script |
| `gmsh/2d_axisym_amr.geo` | AMR geometry script — reads `mfp.pos` as the background field |
| `gmsh/2d_axisym{1,2,3}.msh`, `gmsh/2d_axisym_amr{1,2,3}.msh` | Per-iteration mesh backups |
| `gmsh/Experiment_Wedge.STEP` | CAD source for the geometry |
| `gmsh/mfp.pos` | Last Gmsh PostView background field (per-point mean free path) |
| `comet_result/output_normal1_result/` | Archived result from the baseline run |
| `comet_result/output_amr{1,2,3}_result/` | Archived results from each AMR iteration |

Each `output_*_result/` folder contains a `field/` subfolder with the
per-step `.vtu` files and a `.pvd` collection that ParaView reads as a
single time series.

## How to run

The bundled mesh and inputs are ready to use. To run the AMR loop from
scratch:

```bash
cd test_cases/comet_2d_axisym_psi
# Update binary paths in amr_pipeline.input (gmsh_bin, pvpython, pumi_bin)
./all_run.sh
```

To inspect the bundled results without running the solver:

```bash
paraview test_cases/comet_2d_axisym_psi/comet_result/output_amr3_result/field/auto_field.pvd
```

## What the AMR criterion does

The mean free path λ is the natural cell-size criterion for DSMC. After
each iteration, `final.py` (in `direct` mode) reads the `mean free
path` field from the latest VTU output and writes a Gmsh `.pos`
background field with `h(x, y, z) = λ(x, y, z)` (scaled by `pos_scale`,
default 1.0). The next Gmsh run uses that field to size the new mesh
so each cell is approximately one mean free path on a side. The
procedure is repeated for the configured number of iterations.

The number of cells grows where the gas is dense (near the plume core
and the impingement surface) and stays coarse where the gas is dilute
(in the far field). Comparing the meshes in `gmsh/2d_axisym1.msh`,
`2d_axisym_amr1.msh`, `2d_axisym_amr2.msh`, `2d_axisym_amr3.msh` shows
the progressive refinement.
