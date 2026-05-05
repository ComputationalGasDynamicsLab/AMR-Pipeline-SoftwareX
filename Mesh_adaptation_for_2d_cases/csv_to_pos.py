#!/usr/bin/env pvpython

from paraview.simple import *
import csv
import os

def export_all_point_data(pvd_file, output_csv):
    """
    Loads a PVD file, applies Cell Data to Point Data, and exports all point data to CSV.
    """
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

    ExportView(output_csv, view=spreadsheet_view)
    print(f"[INFO] Exported ALL point data to CSV: {output_csv}")

def extract_coords_and_mfp(input_csv, filtered_csv, mfp_column="mean free path"):
    """
    Extracts coordinates_0, coordinates_1, coordinates_2, and mean free path columns from a CSV.
    """
    with open(input_csv, newline='') as fin:
        reader = csv.reader(fin)
        header = next(reader)
        try:
            idx_x = header.index("coordinates_0")
            idx_y = header.index("coordinates_1")
            idx_z = header.index("coordinates_2")
            idx_mfp = header.index(mfp_column)
        except ValueError as e:
            raise RuntimeError(f"[ERROR] Required column missing: {e}")

        with open(filtered_csv, "w", newline='') as fout:
            writer = csv.writer(fout)
            writer.writerow(["x", "y", "z", "mean_free_path"])
            for row in reader:
                try:
                    writer.writerow([row[idx_x], row[idx_y], row[idx_z], row[idx_mfp]])
                except Exception as e:
                    print(f"[WARNING] Skipping malformed row: {row}")

    print(f"[INFO] Wrote filtered CSV with only coords and mean free path: {filtered_csv}")

def convert_csv_to_pos(csv_file, pos_file, multiply_factor=5.0):
    """
    Converts a CSV file with x, y, z, mean_free_path columns to a Gmsh POS file.
    """
    mfp_data = []
    with open(csv_file, newline='') as f:
        reader = csv.reader(f)
        next(reader, None)  # Skip header
        for row in reader:
            try:
                x, y, z, val = row[:4]
                x = float(x.strip())
                y = float(y.strip())
                z = float(z.strip())
                val = float(val.strip())
                mfp_data.append((x, y, z, val * multiply_factor))
            except Exception as e:
                print(f"[WARNING] Skipping a row due to error: {e}\nRow: {row}")

    with open(pos_file, "w") as f:
        f.write('View "MFP" {\n')
        for (x, y, z, mfp) in mfp_data:
            f.write(f"SP({x},{y},{z}){{{mfp}}};\n")
        f.write("};\n")

    print(f"[INFO] Wrote {len(mfp_data)} points to POS file: {pos_file}")

if __name__ == "__main__":
    # Automatically determine the base directory
    BASE_DIR = os.getcwd()

    # Construct full paths relative to BASE_DIR
    pvd_file = os.path.join(BASE_DIR, "comet_result", "field", "2d_flow_over_cylinder_npart=1_ngroup=4_m1_g4.pvd")
    raw_csv = os.path.join(BASE_DIR, "gmsh_mesh_files", "all_data.csv")
    filtered_csv = os.path.join(BASE_DIR, "gmsh_mesh_files", "filtered_mfp.csv")
    pos_file = os.path.join(BASE_DIR, "gmsh_mesh_files", "mfp.pos")

    multiply_factor = 5.0
    mfp_column_name = "mean free path"

    # Step 1: Export all point data from ParaView
    export_all_point_data(pvd_file, raw_csv)

    # Step 2: Filter out just x, y, z, and mean free path
    extract_coords_and_mfp(raw_csv, filtered_csv, mfp_column=mfp_column_name)

    # Step 3: Convert to POS format
    convert_csv_to_pos(filtered_csv, pos_file, multiply_factor=multiply_factor)
