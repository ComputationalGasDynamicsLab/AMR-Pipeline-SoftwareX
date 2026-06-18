# Mesh Adaptation for OpenFOAM Cases — Mach 3 Cylinder

Mach 3 flow over a 2D cylinder at 50 km altitude. The mesh is refined
from the **pressure gradient** `|grad(p)|`. **COMET is not needed** — a
converged `rhoCentralFoam` result is bundled in the folder.

## See the First AMR Mesh (one command)

The sizing field `mfp.pos` is bundled, so anyone can build and view the
first AMR mesh with **Gmsh alone**:

```bash
gmsh mach3_cylinder_amr.geo -3 -o mach3_cylinder_amr.msh
gmsh mach3_cylinder_amr.msh        # open it to see the refinement
```

Compare it with the uniform mesh `mach3_cylinder.msh`: the AMR mesh has
small cells along the bow shock and in the wake (large `|grad p|`) and
stays coarse in the free stream.

## One Script — Field → Mesh → OpenFOAM polyMesh

`generate_amr_mesh.sh` does the whole thing in one go, with no COMET. It
degrades gracefully, so it works at every tool level:

```bash
./generate_amr_mesh.sh
```

| Step | Needs | If the tool is missing |
|------|-------|------------------------|
| 1. `final.py` regenerates `mfp.pos` from the bundled result | ParaView (`pvpython`) | skipped — the bundled `mfp.pos` is used |
| 2. Gmsh writes the AMR mesh `mach3_cylinder_amr.msh` | Gmsh | required — this is the mesh you see |
| 3. `gmshToFoam` writes `openfoam_case/constant/polyMesh` | OpenFOAM v2406 | skipped — the `.msh` is still produced |

So an outside user with only Gmsh still gets the AMR mesh; a user with
OpenFOAM also gets the ready-to-run polyMesh. Step 3 mirrors the
`gmshToFoam` + boundary-fix that `../master_script/run_openfoam_amr.sh`
performs. Set `gmsh_bin`, `pvpython`, and `foam_source` in
`amr_pipeline.input` for your machine.

## Files in This Folder

| File | What it is |
|------|------------|
| `generate_amr_mesh.sh` | **The one script.** Field → AMR mesh → OpenFOAM polyMesh, reading everything from `amr_pipeline.input`. |
| `amr_pipeline.input` | The one file you edit (binary paths, geometry/mesh names, gradient field `p`, sizing parameters, and OpenFOAM settings). |
| `mach3_cylinder.geo` | Baseline geometry — rectangular domain with a cylinder, extruded one cell in z so OpenFOAM treats it as 2D. Tags `inlet`, `outlet`, `wall`, `frontAndBack`. |
| `mach3_cylinder_amr.geo` | Same geometry plus the lines that load `mfp.pos` as a Gmsh `Background Field`. |
| `mach3_cylinder.msh` | Uniform starting mesh. |
| `mach3_cylinder_amr.msh` | The AMR-refined mesh. |
| `mfp.pos` | Bundled sizing field (Gmsh PostView), so the AMR mesh builds with Gmsh alone. |
| `openfoam_case/` | OpenFOAM case directory: `0.orig/` (initial/boundary fields), `constant/` (thermophysical + turbulence models), `system/` (`controlDict`/`fvSchemes`/`fvSolution`). `gmshToFoam` fills in `constant/polyMesh`. |
| `precomputed_result/field/…` | The bundled converged `rhoCentralFoam` field that Step 1 reads. |

All the shared pipeline scripts — `all_run.sh`, `final.py`,
`run_openfoam.sh`, `run_openfoam_amr.sh` — live in
[`../master_script/`](../master_script/).

## Full Pipeline (OpenFOAM in the loop)

With OpenFOAM v2406 installed, run the complete AMR pipeline — uniform
mesh → `rhoCentralFoam` → extract `|grad(p)|` → AMR mesh → run again,
for `loops` iterations:

```bash
# Edit amr_pipeline.input: gmsh_bin, pvpython, foam_source
../master_script/all_run.sh
```

## Sizing Formula

```
h(x) = h_min + (h_max − h_min) / (1 + α · |grad p(x)| / max |grad p|)
```

with `h_min = 0.002 m`, `h_max = 0.015 m`, `α = 100`, set in
`amr_pipeline.input` as `sizing_min`, `sizing_max`, `sizing_scale`.
