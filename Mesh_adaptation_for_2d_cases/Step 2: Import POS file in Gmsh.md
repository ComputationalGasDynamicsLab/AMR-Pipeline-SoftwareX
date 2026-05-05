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
  The script below is an example for a 2D flow over a cylinder simulation. The provided `.geo` script is tailored specifically for that case.

## Gmsh .geo Script 

```geo
// points
Point(1) = {0, 0, 0, 0.02};
Point(2) = {1, 0, 0, 0.02};
Point(3) = {1, 0.8, 0, 0.02};
Point(4) = {0, 0.8, 0, 0.02};
Point(5) = {0.5, 0.3, 0, 0.01};
Point(6) = {0.5, 0.4, 0, 0.01};
Point(7) = {0.5, 0.5, 0, 0.01};

// lines and circle
Line(1) = {1, 2};
Line(2) = {2, 3};
Line(3) = {3, 4};
Line(4) = {4, 1};
Circle(5) = {5, 6, 7};
Circle(6) = {7, 6, 5};

// define 1d geometry
Curve Loop(1) = {4, 1, 2, 3};
Curve Loop(2) = {5, 6};

// define 2d geometry
Plane Surface(1) = {1, 2};

// define model
Physical Curve("inlet") = {4};
Physical Curve("outlet") = {1, 2, 3};
Physical Curve("wall") = {6, 5};
Physical Surface("sim_domain") = {1};

Merge "out1.pos";

Field[1] = PostView;          // treat the .pos data as a Gmsh Field
Field[1].ViewTag = 1;         

Mesh.MeshSizeFromPoints = 0;
Mesh.MeshSizeFromCurvature = 0;
Mesh.MeshSizeExtendFromBoundary = 0;

// Finally, set the background field and generate mesh
Background Field = 1;
Mesh 2;
