This folder contains the `gmsh` input file to generate the following mesh
- Sphere inside a 3D box for simulating 3D flow over cyliner.
- The four corner points of the rectangle are (0, 0), (1, 0), (1, 1), (0, 1).
- The cylinder has a radius of 0.1 and centered at (0.5, 0.4).

#### Download Gmsh
- User can download Gmsh binary files using the [download link](https://gmsh.info/bin/Linux/gmsh-4.11.1-Linux64.tgz)
- To do that, first choose a folder to store Gmsh file, and then perform the following commands:
```
wget https://gmsh.info/bin/Linux/gmsh-4.11.1-Linux64.tgz
tar xvf gmsh-4.11.1-Linux64.tgz
```
- The Gmsh binary file is in the following location:
```
gmsh-4.11.1-Linux64/bin/gmsh
```

#### Generate mesh using Gmsh
- To generate mesh, use the following command:
```
location_of_gmsh/gmsh 3d_cylinder.geo -3
```
- `location_of_gmsh` is the full path of `gmsh` binary.
- User can modify the `gmsh_generation.sh` script file (use proper `gmsh` binary location) and then 
use the following command to perform mesh generation:
```
./gmsh_generation.sh
``` 

#### Create PUMIPic mesh partition
We need to create PUMIPic mesh partition file to be able to run the simulation. To do that, use the
following command on Talon:
```
sbatch pumipic_partition_talon.sh
```
- This command submit the job to Talon GPU queue to perform the mesh partition.
- Currently, `print_classification` requires GPU device.
- The above may be relaxed once we build CPU only binary file.
- The relevant command in the `pumipic_partition.sh` script is the following line:
```
./installation_path_of_pumipic/print_classification 2d_cylinder.msh 2d_cylinder 4 200 1.0
```
- User need to use correct path of `print_classification` by specifying the fall file path of PUMIPic 
installation directory.

To create mesh partition file on Polaris, use the following command:
```
qsub pumipic_partition_polaris.sh
```

#### Start from gmsh `.msh` file to obtain PUMIPic mesh partition file `.ptn`.
- Use the following command to generate `dmg` and `smb` file. The input is `gmsh`
mesh file `.msh`:
```
from_gmsh none <in .msh> <out .smb> <out .dmg>
```

- Create PUMIPic partition file:
```
print_pumipic_partition <model> <mesh> <number of output parts> <partition file prefix>
```
