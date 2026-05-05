#!/usr/bin/env pvpython

import argparse
import csv
import re
from pathlib import Path
from paraview.simple import *  # noqa: F401,F403


def export_all_point_data(pvd_file, output_csv):
    # Load a PVD, sample last timestep, export all point data to CSV.
    reader = PVDReader(FileName=pvd_file)
    animationScene = GetAnimationScene()
    animationScene.UpdateAnimationUsingDataTimeSteps()
    if hasattr(reader, "TimestepValues") and reader.TimestepValues:
        last_time = reader.TimestepValues[-1]
        reader.UpdatePipeline(time=last_time)
        animationScene.GoToLast()

    cd2pd = CellDatatoPointData(Input=reader)
    cd2pd.UpdatePipeline()

    spreadsheet_view = CreateView("SpreadSheetView")
    Show(cd2pd, spreadsheet_view, "SpreadSheetRepresentation")
    spreadsheet_view.FieldAssociation = "Point Data"
    spreadsheet_view.Update()

    ExportView(output_csv, view=spreadsheet_view)
    print(f"[INFO] Exported ALL point data to CSV: {output_csv}")


def _normalize(name: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^0-9a-zA-Z]+", "_", name)).strip("_").lower()


def _find_index(header, target, fallbacks=None):
    fallbacks = fallbacks or []
    norm_map = {_normalize(h): i for i, h in enumerate(header)}
    for key in [_normalize(target), *_normalize_list(fallbacks)]:
        if key in norm_map:
            return norm_map[key]
    raise KeyError(target)


def _normalize_list(items):
    return [_normalize(x) for x in items]


def extract_coords_and_scalar(input_csv, filtered_csv, scalar_column="mean free path"):
    # Extract x, y, z and chosen scalar into a compact CSV (robust to space/underscore differences).
    with open(input_csv, newline="") as fin:
        reader = csv.reader(fin)
        header = next(reader)
        try:
            idx_x = _find_index(header, "coordinates_0", fallbacks=["x"])
            idx_y = _find_index(header, "coordinates_1", fallbacks=["y"])
            idx_z = _find_index(header, "coordinates_2", fallbacks=["z"])
            idx_scalar = _find_index(header, scalar_column, fallbacks=["mean free path", "mean_free_path"])
        except KeyError as e:
            raise RuntimeError(f"[ERROR] Required column missing: {e}") from e

        with open(filtered_csv, "w", newline="") as fout:
            writer = csv.writer(fout)
            writer.writerow(["x", "y", "z", "scalar"])
            for row in reader:
                try:
                    writer.writerow([row[idx_x], row[idx_y], row[idx_z], row[idx_scalar]])
                except Exception:
                    continue

    print(f"[INFO] Wrote filtered CSV with only coords and {scalar_column}: {filtered_csv}")


def convert_csv_to_pos(csv_file, pos_file, multiply_factor=1.0):
    # Convert CSV (x,y,z,value) to Gmsh POS.
    scalar_data = []
    with open(csv_file, newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # Skip header
        for row in reader:
            try:
                x, y, z, val = row[:4]
                x = float(x.strip())
                y = float(y.strip())
                z = float(z.strip())
                val = float(val.strip())
                scalar_data.append((x, y, z, val * multiply_factor))
            except Exception:
                continue

    with open(pos_file, "w") as f:
        f.write('View "MFP" {\n')
        for (x, y, z, val) in scalar_data:
            f.write(f"SP({x},{y},{z}){{{val}}};\n")
        f.write("};\n")

    print(f"[INFO] Wrote {len(scalar_data)} points to POS file: {pos_file}")


def main():
    parser = argparse.ArgumentParser(description="Export ParaView results to CSV and POS for AMR.")
    parser.add_argument("--pvd", required=True, help="Path to the PVD file to sample (latest timestep is used)")
    parser.add_argument("--raw-csv", default="gmsh/all_data.csv", help="Output CSV for full export")
    parser.add_argument("--filtered-csv", default="gmsh/filtered_mfp.csv", help="Filtered CSV with coords + scalar")
    parser.add_argument("--pos", default="gmsh/mfp.pos", help="Output POS file for Gmsh")
    parser.add_argument("--multiply-factor", type=float, default=1.0, help="Scale factor applied to POS values")
    parser.add_argument("--scalar-column", default=None, help="Column name to extract (preferred)")
    parser.add_argument("--mfp-column", default=None, help="Deprecated alias for --scalar-column")
    parser.add_argument("--results-root", default="", help="(Optional) results root for logging")
    parser.add_argument("--field-pattern", default="", help="(Optional) field pattern for logging")
    args = parser.parse_args()

    scalar_column = args.scalar_column or args.mfp_column or "mean free path"

    if args.results_root or args.field_pattern:
        print(
            "[INFO] Logging hints (reserved for external orchestration): "
            f"results_root={args.results_root!r}, field_pattern={args.field_pattern!r}"
        )

    for path in (args.raw_csv, args.filtered_csv, args.pos):
        parent = Path(path).expanduser().resolve().parent
        parent.mkdir(parents=True, exist_ok=True)

    export_all_point_data(args.pvd, args.raw_csv)
    extract_coords_and_scalar(args.raw_csv, args.filtered_csv, scalar_column=scalar_column)
    convert_csv_to_pos(args.filtered_csv, args.pos, multiply_factor=args.multiply_factor)


if __name__ == "__main__":
    main()
