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
