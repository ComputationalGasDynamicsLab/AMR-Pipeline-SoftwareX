# Steps to Follow to Generate Pos file for importing in Gmsh
The first step is to run the DSMC simulation using the initial coarse mesh. Once the simulation is completed, the mean free path (MFP) data must be extracted from the DSMC output.

Our objective is to import this mean free path data into Gmsh to enable mesh refinement. To automate this process, we use a Python script, which will be shared later. By executing the script—without the need to manually open ParaView—the mean free path data will be directly exported in both CSV and POS file formats. These files will then be used to guide the adaptive mesh refinement in Gmsh.

- **Generate .pos and .csv Files**
  - Run the Python script provided below.
  - **Before running the script:**
    - Update the PVD file path.
    - Set the output location where the `.pos` and `.csv` files will be saved.
    - Ensure the script is run in the same directory where the PVD file is located.
    - In the current script, a value corresponding to 5 mean free paths is used. If you wish to apply a different value, you can modify the multiply factor in the relevant section of the code as 
      shown below.
  - Use the following command in your terminal to execute the script:
  
        pvpython "filename.py"

---

## Python Code

The code below exports specific point data from a PVD file to a CSV file and then converts that CSV into a POS file using the Gmsh `SP(x,y,z){value}` syntax:

```python
#!/usr/bin/env pvpython

from paraview.simple import *
import csv

def export_spreadsheet_as_csv_four_columns(pvd_file, output_csv):
    """
    Loads a PVD file, applies a filter to get point data (via Cell Data to Point Data),
    creates a Spreadsheet View, then hides extra columns so that only:
      "Points:0", "Points:1", "Points:2", and "mean free path"
    remain before exporting to CSV.
    """
    # 1) Load the PVD file.
    reader = PVDReader(FileName=pvd_file)

    # 2) Update to the last time step if multiple exist.
    animationScene = GetAnimationScene()
    animationScene.UpdateAnimationUsingDataTimeSteps()
    if hasattr(reader, 'TimestepValues') and reader.TimestepValues:
        last_time = reader.TimestepValues[-1]
        reader.UpdatePipeline(time=last_time)
        animationScene.GoToLast()

    # 3) Apply Cell Data to Point Data.
    #    (If you want one row per cell without interpolation, replace this with CellCenters)
    cd2pd = CellDatatoPointData(Input=reader)
    cd2pd.UpdatePipeline()

    # 4) Create a Spreadsheet View.
    spreadsheet_view = CreateView('SpreadSheetView')

    # 5) Show the converted data in the Spreadsheet View.
    rep = Show(cd2pd, spreadsheet_view, 'SpreadSheetRepresentation')
    # Ensure we are displaying Point Data.
    spreadsheet_view.FieldAssociation = "Point Data"
    spreadsheet_view.Update()

    # 6) Hide all columns that are not desired.
    #    We want to keep only:
    #       "Points:0", "Points:1", "Points:2", and "mean free path"
    #    The list below hides many common extra columns. Adjust if necessary.
    spreadsheet_view.HiddenColumnLabels = [
        "Point ID",
        "Block Number",
        "Points",               # Composite coordinate column, if it appears.
        "Points_Magnitude",
        "accumulated particle",
        "accumulated particle_0",
        "accumulated particle_1",
        "accumulated particle_2",
        "accumulated particle_3",
        "accumulated particle_4",
        "accumulated particle_5",
        "accumulated particle_6",
        "accumulated particle_7",
        "accumulated particle_8",
        "accumulated particle_Magnitude",
        "cell_volume",
        "class_dim",
        "class_id",
        "coll_corr_factor",
        "coordinates_Magnitude",
        "dt/mean collision time",
        "dx/mean free path",
        "flow:density",
        "flow:particle per cell",
        "flow:pressure",
        "flow:temperature",
        "flow:temperature_0",
        "flow:temperature_1",
        "flow:temperature_2",
        "flow:temperature_3",
        "flow:temperature_4",
        "flow:temperature_5",
        "flow:temperature_Magnitude",
        "flow:velocity",
        "flow:velocity_0",
        "flow:velocity_1",
        "flow:velocity_2",
        "flow:velocity_3",
        "flow:velocity_4",
        "flow:velocity_5",
        "flow:velocity_Magnitude",
        "gids",
        "global",
        "global_serial",
        "initial particle per cell",
        "inlet particle per cell",
        "int_max_pair",
        "isOnMdlBdry",
        "local",
        "mean collision time",
        "nbad_collision",
        "npart_per_cell",
        "ntest_collision",
        "ntotal_collision",
        "ownership",
        "rank_lids",
        "safe",
        "sbar_id",
        "sigmacr_max",
        "total inlet particle"
    ]
    # Note: Do NOT hide "Points:0", "Points:1", "Points:2", or "mean free path".
    
    # 7) Export the view to CSV.
    ExportView(output_csv, view=spreadsheet_view)
    print(f"[INFO] Exported spreadsheet to CSV: {output_csv}")

def convert_csv_to_pos(csv_file, pos_file, multiply_factor=5.0):
    """
    Reads a CSV file (with header) containing four columns:
      x, y, z, mean free path
    and writes a POS file using the Gmsh SP(x,y,z){value} syntax.
    
    The mean free path value is multiplied by multiply_factor.
    """
    mfp_data = []
    with open(csv_file, newline='') as f:
        reader = csv.reader(f)
        next(reader, None)  # Skip header if present.
        for row in reader:
            # Expecting four columns: x, y, z, mean free path.
            try:
                x_str, y_str, z_str, val_str = row[:4]
                x = float(x_str.replace('a','').replace('b','').strip())
                y = float(y_str.replace('a','').replace('b','').strip())
                z = float(z_str.replace('a','').replace('b','').strip())
                val = float(val_str.replace('a','').replace('b','').strip())
                mfp_data.append((x, y, z, val * multiply_factor))
            except Exception as e:
                print(f"[WARNING] Skipping a row due to error: {e}\nRow: {row}")
    
    with open(pos_file, "w") as f:
        f.write('View "MFP" {\n')
        for (x, y, z, mfp) in mfp_data:
            f.write(f"SP({x},{y},{z}){{{mfp}}};\n")
        f.write("};\n")
    
    print(f"[INFO] Wrote {len(mfp_data)} points to POS file: {pos_file}")

# ------------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    # Update these paths as needed.
    pvd_file = "/home/fahim.shahriyar/dsmc/NDAS/important/coarse_mesh_uniform/comet_result/field/2d_flow_over_cylinder_npart=1_ngroup=4_m1_g4.pvd"
    output_csv = "/home/fahim.shahriyar/dsmc/NDAS/important/coarse_mesh_uniform/gmsh_mesh_files/out1.csv"
    pos_file = "/home/fahim.shahriyar/dsmc/NDAS/important/coarse_mesh_uniform/gmsh_mesh_files/out1.pos"
    
    # Step 1: Export the desired columns to CSV.
    export_spreadsheet_as_csv_four_columns(pvd_file, output_csv)
    
    # Step 2: Convert the CSV file to a POS file.
    #         (The multiply_factor multiplies the mean free path value by 5 in the POS file.)
    convert_csv_to_pos(output_csv, pos_file, multiply_factor=5.0)
 
