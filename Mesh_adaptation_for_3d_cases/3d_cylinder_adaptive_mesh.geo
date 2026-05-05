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

Mesh.CharacteristicLengthMax = 0.01;

// Finally, set the background field and generate mesh
Background Field = 1;

Mesh 3;

