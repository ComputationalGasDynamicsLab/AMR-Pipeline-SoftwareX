// 2D cylinder geometry — AMR variant.
// Same geometry as 2d_cylinder.geo, plus a background field loaded from
// mfp.pos (written by final.py after the previous solver run) that
// drives Gmsh's local cell sizing.

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

// 1D loops and 2D surface
Curve Loop(1) = {4, 1, 2, 3};
Curve Loop(2) = {5, 6};
Plane Surface(1) = {1, 2};

// Boundary tags
Physical Curve("inlet")    = {4};
Physical Curve("outlet")   = {1, 2, 3};
Physical Curve("wall")     = {6, 5};
Physical Surface("sim_domain") = {1};

// Load the AMR sizing field written by final.py.
Merge "mfp.pos";

Field[1] = PostView;
Field[1].ViewTag = 1;

// Disable Gmsh's other sizing heuristics so they don't fight the
// background field.
Mesh.MeshSizeFromPoints      = 0;
Mesh.MeshSizeFromCurvature   = 0;
Mesh.MeshSizeExtendFromBoundary = 0;

// Use the loaded PostView as the source of truth for cell size.
Background Field = 1;

Mesh 2;
