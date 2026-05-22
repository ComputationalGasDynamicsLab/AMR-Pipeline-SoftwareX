# Introduction to Gmsh

Gmsh is an open-source 3D finite element mesh generator with integrated pre- and post-processing capabilities.  
It allows for automated mesh generation through scripting and supports various mesh types, making it a versatile tool for engineering and scientific simulations.

# Use .pos File in Gmsh

- **Move the .pos File:**  
  Once the `.pos` file is generated, move it to the directory containing your `.geo` script.

- **Modify Your .geo File:**  
  In your `.geo` file, include the following:
  - **Merge Command:** Use the `Merge` command to include the `.pos` file.
  - **Mesh Sizing:** Apply the `PostView` Field to control the mesh sizing.
  - **Additional Mesh Fields:** Incorporate the following mesh fields to avoid over-refinement inside entities due to small boundary mesh sizes:
    - `Mesh.MeshSizeFromPoints`
    - `Mesh.MeshSizeFromCurvature`
    - `Mesh.MeshSizeExtendFromBoundary`

- **Gmsh Output and Script:**  
  The script below is an example for a 3D flow over a cylinder simulation. The provided `.geo` script is tailored specifically for that case.

## Gmsh .geo Script 

```geo
SetFactory("OpenCASCADE");
Geometry.OCCTargetUnit = "M";
Merge "3d_cylinder.step";
//+
Physical Surface("inlet", 1) = {4};
//+
Physical Surface("outlet", 2) = {3, 1, 7, 2, 6};
//+
Physical Surface("wall", 3) = {5};
//+
Physical Volume("sim_domain", 4) = {1};

Merge "out_3d_flow_over_cylinder_npart=1_ngroup=4_m1_g1.pos";

Field[1] =PostView;          // treat the .pos data as a Gmsh Field
Field[1].ViewTag = 1;         // 

Mesh.MeshSizeFromPoints = 0;
Mesh.MeshSizeFromCurvature = 0;
Mesh.MeshSizeExtendFromBoundary = 0;


// Finally, set the background field and generate mesh
Background Field = 1;

Mesh 3;
RefineMesh;
RefineMesh;
RefineMesh;

