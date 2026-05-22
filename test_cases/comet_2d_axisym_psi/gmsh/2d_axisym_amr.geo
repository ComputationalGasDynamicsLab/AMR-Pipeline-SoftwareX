
// 2D ramp geometry without cylinder
// points defining the domain with cut corner
Point(1) = {0,	  0,   0, 0.001};     // bottom-left corner
Point(2) = {0.04,  0,   0, 0.001};     // bottom edge (before ramp)
Point(3) = {0.04,    0.12, 0, 0.001};     // ramp end on right edge
Point(4) = {0, 0.12, 0, 0.001};     // right end of cylinder generatrix
Point(5) = {0, 0.001, 0, 0.001};     // top-right corner  
   // top-left corner

// lines defining the boundary
Line(1) = {1, 2};                    // symmetric axis (before ramp)
Line(2) = {2, 3};                    // ramp/diagonal wall
Line(3) = {3, 4};                    // cylinder generatrix
Line(4) = {4, 5};                    // right wall (after ramp)
Line(5) = {5, 1};                    // outlet (top)

// define 1d geometry
Curve Loop(1) = {1, 2, 3, 4, 5};

// define 2d geometry
Plane Surface(1) = {1};

// define model with physical boundaries
Physical Curve("symmetric_axis") = {1};
Physical Curve("wall") = {2};
Physical Curve("pressure_outlet") = {3,4};
Physical Curve("inlet") = {5};
Physical Surface("sim_domain") = {1};

Merge "mfp.pos";

Field[1] =PostView;          // treat the .pos data as a Gmsh Field
Field[1].ViewTag = 1;        

Mesh.MeshSizeFromPoints = 0;
Mesh.MeshSizeFromCurvature = 0;
Mesh.MeshSizeExtendFromBoundary = 0;

// Mesh sizing
Mesh.CharacteristicLengthMin = 0.0000005;
Mesh.CharacteristicLengthMax = 0.001;

// Finally, set the background field and generate mesh
Background Field = 1;

// meshing the geometry
Mesh 2;
