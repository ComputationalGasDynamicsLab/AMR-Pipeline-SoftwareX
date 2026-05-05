#!/usr/bin/env pvpython

from paraview.simple import *
import csv
import math


def export_spreadsheet_as_csv_four_columns(pvd_file, output_csv):
    """
    Reads a PVD file, extracts the last timestep's point data, and exports
    a four-column CSV (x, y, z, mfp) using ParaView's spreadsheet view.
    """
    reader = PVDReader(FileName=pvd_file)
    scene = GetAnimationScene()
    scene.UpdateAnimationUsingDataTimeSteps()

    # Update to the last timestep
    if hasattr(reader, 'TimestepValues') and reader.TimestepValues:
        reader.UpdatePipeline(time=reader.TimestepValues[-1])
        scene.GoToLast()

    # Convert cell data to point data
    cd2pd = CellDatatoPointData(Input=reader)
    cd2pd.UpdatePipeline()

    # Create spreadsheet view and hide unwanted columns
    view = CreateView('SpreadSheetView')
    show = Show(cd2pd, view)
    view.FieldAssociation = 'Point Data'
    view.HiddenColumnLabels = [
        'Point ID',
        'Block Number',
        'Points',
        'Points_Magnitude',
        'dx/mean free path',
        'dt/mean collision time',
        'accumulated particle',
        'accumulated particle_0',
        'accumulated particle_1',
        'accumulated particle_2',
        'accumulated particle_3',
        'accumulated particle_4',
        'accumulated particle_5',
        'accumulated particle_6',
        'accumulated particle_7',
        'accumulated particle_8',
        'accumulated particle_Magnitude',
        'cell_volume',
        'class_dim',
        'class_id',
        'coll_corr_factor',
        'coordinates_Magnitude',
        'flow:density',
        'flow:particle per cell',
        'flow:pressure',
        'flow:temperature',
        'flow:temperature_0',
        'flow:temperature_1',
        'flow:temperature_2',
        'flow:temperature_3',
        'flow:temperature_4',
        'flow:temperature_5',
        'flow:temperature_Magnitude',
        'flow:velocity',
        'flow:velocity_0',
        'flow:velocity_1',
        'flow:velocity_2',
        'flow:velocity_3',
        'flow:velocity_4',
        'flow:velocity_5',
        'flow:velocity_Magnitude',
        'gids',
        'global',
        'global_serial',
        'initial particle per cell',
        'inlet particle per cell',
        'int_max_pair',
        'isOnMdlBdry',
        'local',
        'mean collision time',
        'nbad_collision',
        'npart_per_cell',
        'ntest_collision',
        'ntotal_collision',
        'ownership',
        'rank_lids',
        'safe',
        'sbar_id',
        'sigmacr_max',
        'total inlet particle'
    ]

    # Export to CSV
    ExportView(output_csv, view=view)
    print(f"[INFO] Exported spreadsheet to CSV: {output_csv}")


def convert_csv_to_pos(csv_file, pos_file, multiply_factor):
    """
    Reads a CSV of columns x, y, z, mfp and writes a Gmsh POS file:
      View "MFP" { SP(x,y,z){mfp}; ... };
    Rows with invalid or NaN mfp are silently skipped.
    """
    mfp_data = []
    skipped = 0

    with open(csv_file, newline='') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) < 4:
                skipped += 1
                continue
            x_str, y_str, z_str, val_str = row[:4]

            # Parse coordinates
            try:
                x = float(x_str.strip())
                y = float(y_str.strip())
                z = float(z_str.strip())
            except ValueError:
                skipped += 1
                continue

            # Parse mean free path
            try:
                val = float(val_str.strip())
                if math.isnan(val):
                    raise ValueError
            except ValueError:
                skipped += 1
                continue

            mfp_data.append((x, y, z, val * multiply_factor))

    # Write .pos file
    with open(pos_file, 'w') as f:
        f.write('View "MFP" {\n')
        for x, y, z, mfp in mfp_data:
            f.write(f"SP({x},{y},{z}){{{mfp}}};\n")
        f.write('};\n')

    print(f"[INFO] Wrote {len(mfp_data)} valid points to POS file: {pos_file}")
    if skipped:
        print(f"[INFO] Skipped {skipped} invalid rows.")


if __name__ == '__main__':
    pvd_files = [
        '/home/fahim.shahriyar/dsmc/NDAS/gmsh/3d_cases/3d_flow_over_cylinder/coarse_mesh_1/comet_result/field/3d_flow_over_cylinder_npart=1_ngroup=4_m1_g1.pvd'
    ]

    for pvd_file in pvd_files:
        ident = pvd_file.split('/')[-1].replace('.pvd', '')
        out_csv = f'/home/fahim.shahriyar/dsmc/NDAS/gmsh/3d_cases/3d_flow_over_cylinder/coarse_mesh_1/gmsh_mesh_files/out_{ident}.csv'
        out_pos = f'/home/fahim.shahriyar/dsmc/NDAS/gmsh/3d_cases/3d_flow_over_cylinder/coarse_mesh_1/gmsh_mesh_files/out_{ident}.pos'

        export_spreadsheet_as_csv_four_columns(pvd_file, out_csv)
        convert_csv_to_pos(out_csv, out_pos, multiply_factor=1.0)

