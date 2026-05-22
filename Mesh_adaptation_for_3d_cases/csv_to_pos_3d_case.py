#!/usr/bin/env pvpython

from paraview.simple import *
import csv

def export_spreadsheet_as_csv_four_columns(pvd_file, output_csv):
    reader = PVDReader(FileName=pvd_file)

    animationScene = GetAnimationScene()
    animationScene.UpdateAnimationUsingDataTimeSteps()
    if hasattr(reader, 'TimestepValues') and reader.TimestepValues:
        last_time = reader.TimestepValues[-1]
        reader.UpdatePipeline(time=last_time)
        animationScene.GoToLast()

    cd2pd = CellDatatoPointData(Input=reader)
    cd2pd.UpdatePipeline()

    spreadsheet_view = CreateView('SpreadSheetView')
    rep = Show(cd2pd, spreadsheet_view, 'SpreadSheetRepresentation')
    spreadsheet_view.FieldAssociation = "Point Data"
    spreadsheet_view.Update()

    spreadsheet_view.HiddenColumnLabels = [
        "Point ID", "Block Number", "Points", "Points_Magnitude",
        "accumulated particle", "accumulated particle_0", "accumulated particle_1",
        "accumulated particle_2", "accumulated particle_3", "accumulated particle_4",
        "accumulated particle_5", "accumulated particle_6", "accumulated particle_7",
        "accumulated particle_8", "accumulated particle_Magnitude", "cell_volume",
        "class_dim", "class_id", "coll_corr_factor", "coordinates_Magnitude",
        "dt/mean collision time", "dx/mean free path", "flow:density",
        "flow:particle per cell", "flow:pressure", "flow:temperature", "flow:temperature_0",
        "flow:temperature_1", "flow:temperature_2", "flow:temperature_3",
        "flow:temperature_4", "flow:temperature_5", "flow:temperature_Magnitude",
        "flow:velocity", "flow:velocity_0", "flow:velocity_1", "flow:velocity_2",
        "flow:velocity_3", "flow:velocity_4", "flow:velocity_5", "flow:velocity_Magnitude",
        "gids", "global", "global_serial", "initial particle per cell",
        "inlet particle per cell", "int_max_pair", "isOnMdlBdry", "local",
        "mean collision time", "nbad_collision", "npart_per_cell", "ntest_collision",
        "ntotal_collision", "ownership", "rank_lids", "safe", "sbar_id",
        "sigmacr_max", "total inlet particle"
    ]

    ExportView(output_csv, view=spreadsheet_view)
    print(f"[INFO] Exported spreadsheet to CSV: {output_csv}")


def convert_csv_to_pos(csv_file, pos_file, multiply_factor):
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
    pvd_files = [
        "/home/fahim.shahriyar/dsmc/NDAS/gmsh/3d_cases/3d_flow_over_cylinder/coarse_mesh/comet_result/field/3d_flow_over_cylinder_npart=1_ngroup=4_m1_g1.pvd"
    ]

    for pvd_file in pvd_files:
        file_identifier = pvd_file.split('/')[-1].replace('.pvd', '')

        output_csv = f"/home/fahim.shahriyar/dsmc/NDAS/gmsh/3d_cases/3d_flow_over_cylinder/coarse_mesh/gmsh_mesh_files/out_{file_identifier}.csv"
        pos_file = f"/home/fahim.shahriyar/dsmc/NDAS/gmsh/3d_cases/3d_flow_over_cylinder/coarse_mesh/gmsh_mesh_files/out_{file_identifier}.pos"

        export_spreadsheet_as_csv_four_columns(pvd_file, output_csv)
        convert_csv_to_pos(output_csv, pos_file, multiply_factor=20.0)
