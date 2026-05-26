// 3D cylinder geometry — AMR variant.
// Reads the local mesh-size field from mfp.pos (written by final.py
// after the previous solver run) and uses it as the Gmsh Background
// Field to drive cell sizing.
SetFactory("OpenCASCADE");
Geometry.OCCTargetUnit = "M";
Merge "3d_cylinder.step";

Physical Surface("inlet",  1) = {4};
Physical Surface("outlet", 2) = {3, 1, 7, 2, 6};
Physical Surface("wall",   3) = {5};
Physical Volume("sim_domain", 4) = {1};

// Load the AMR sizing field written by final.py.
Merge "mfp.pos";

Field[1] = PostView;
Field[1].ViewTag = 1;

// Disable Gmsh's other sizing heuristics so they don't fight the
// background field.
Mesh.MeshSizeFromPoints      = 0;
Mesh.MeshSizeFromCurvature   = 0;
Mesh.MeshSizeExtendFromBoundary = 0;
Mesh.ElementOrder            = 1;

// Use the loaded PostView as the source of truth for cell size.
Background Field = 1;

Mesh 3;
