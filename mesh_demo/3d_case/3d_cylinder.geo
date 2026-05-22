// 3D cylinder geometry — baseline (uniform) mesh.
// No AMR sizing field; Gmsh meshes the geometry with its default
// characteristic-length settings.
SetFactory("OpenCASCADE");
Geometry.OCCTargetUnit = "M";
Merge "3d_cylinder.step";

Physical Surface("inlet",  1) = {4};
Physical Surface("outlet", 2) = {3, 1, 7, 2, 6};
Physical Surface("wall",   3) = {5};
Physical Volume("sim_domain", 4) = {1};

Mesh.ElementOrder = 1;
Mesh 3;
