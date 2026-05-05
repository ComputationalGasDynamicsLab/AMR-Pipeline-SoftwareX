#!/usr/bin/env pvpython
"""
Generate contour images for Mach 3 supersonic cylinder AMR presentation.
Run with: pvpython generate_images.py
"""
import os, sys
from paraview.simple import *

paraview.simple._DisableFirstRenderCameraReset()

BASE = "/home/fahim.shahriyar/dsmc/openfoam_mach3_cylinder"
OUT  = os.path.join(BASE, "presentation", "images")
os.makedirs(OUT, exist_ok=True)

# VTU files: last timestep for each iteration
CASES = {
    "uniform": os.path.join(BASE, "comet_result/output_normal1_result/field/step_5_m1_g1/field_g0_m0.vtu"),
    "amr1":    os.path.join(BASE, "comet_result/output_amr1_result/field/step_5_m1_g1/field_g0_m0.vtu"),
    "amr2":    os.path.join(BASE, "comet_result/output_amr2_result/field/step_5_m1_g1/field_g0_m0.vtu"),
    "amr3":    os.path.join(BASE, "comet_result/output_amr3_result/field/step_5_m1_g1/field_g0_m0.vtu"),
}

# Consistent color ranges across all meshes
FIELD_RANGES = {
    "p":    (0, 960),
    "T":    (200, 900),
    "U":    (0, 1100),
}

FIELD_TITLES = {
    "p": "Pressure (Pa)",
    "T": "Temperature (K)",
    "U": "Velocity Magnitude (m/s)",
}

IMG_W, IMG_H = 1600, 900

def setup_view():
    """Create render view with consistent camera."""
    rv = CreateRenderView()
    rv.ViewSize = [IMG_W, IMG_H]
    rv.Background = [1.0, 1.0, 1.0]  # white background
    rv.OrientationAxesVisibility = 0
    rv.CenterAxesVisibility = 0
    # 2D XY view
    rv.CameraPosition = [0.5, 0.4, 2.0]
    rv.CameraFocalPoint = [0.5, 0.4, 0.0]
    rv.CameraViewUp = [0.0, 1.0, 0.0]
    rv.CameraParallelScale = 0.47
    rv.CameraParallelProjection = 1
    return rv

def save_mesh_image(vtu_path, name, rv):
    """Save mesh wireframe image."""
    reader = XMLUnstructuredGridReader(FileName=[vtu_path])
    reader.UpdatePipeline()

    # Slice at z=0.005 to get 2D cross-section
    sl = Slice(Input=reader)
    sl.SliceType = 'Plane'
    sl.SliceType.Origin = [0.5, 0.4, 0.005]
    sl.SliceType.Normal = [0, 0, 1]
    sl.UpdatePipeline()

    dp = Show(sl, rv)
    dp.Representation = 'Wireframe'
    dp.AmbientColor = [0.15, 0.15, 0.15]
    dp.DiffuseColor = [0.15, 0.15, 0.15]
    dp.LineWidth = 0.5

    rv.ResetCamera()
    rv.CameraPosition = [0.5, 0.4, 2.0]
    rv.CameraFocalPoint = [0.5, 0.4, 0.0]
    rv.CameraViewUp = [0.0, 1.0, 0.0]
    rv.CameraParallelScale = 0.47
    rv.CameraParallelProjection = 1
    Render()

    outpath = os.path.join(OUT, f"mesh_{name}.png")
    SaveScreenshot(outpath, rv, ImageResolution=[IMG_W, IMG_H])
    print(f"  Saved: {outpath}")

    Delete(dp)
    Delete(sl)
    Delete(reader)

def save_contour_image(vtu_path, field, name, rv):
    """Save filled contour image for a scalar field."""
    reader = XMLUnstructuredGridReader(FileName=[vtu_path])
    reader.UpdatePipeline()

    # Slice at z=0.005
    sl = Slice(Input=reader)
    sl.SliceType = 'Plane'
    sl.SliceType.Origin = [0.5, 0.4, 0.005]
    sl.SliceType.Normal = [0, 0, 1]
    sl.UpdatePipeline()

    dp = Show(sl, rv)
    dp.Representation = 'Surface'

    if field == "U":
        # Compute velocity magnitude
        calc = Calculator(Input=sl)
        calc.ResultArrayName = 'Umag'
        calc.Function = 'mag(U)'
        calc.UpdatePipeline()
        Hide(sl, rv)
        dp2 = Show(calc, rv)
        dp2.Representation = 'Surface'
        ColorBy(dp2, ('POINTS', 'Umag'))
        dp2.RescaleTransferFunctionToDataRange(False, True)
        umag_lut = GetColorTransferFunction('Umag')
        umag_lut.RescaleTransferFunction(FIELD_RANGES["U"][0], FIELD_RANGES["U"][1])
        umag_lut.ApplyPreset('Rainbow Desaturated', True)
        umag_lut.NumberOfTableValues = 256
        # Color bar
        cb = GetScalarBar(umag_lut, rv)
        cb.Title = FIELD_TITLES["U"]
        cb.ComponentTitle = ''
        cb.TitleFontSize = 18
        cb.LabelFontSize = 14
        cb.ScalarBarLength = 0.4
        cb.Position = [0.85, 0.25]
        cb.TitleColor = [0, 0, 0]
        cb.LabelColor = [0, 0, 0]
        cb.Visibility = 1
        active_dp = dp2
        active_src = calc
    else:
        ColorBy(dp, ('POINTS', field))
        dp.RescaleTransferFunctionToDataRange(False, True)
        lut = GetColorTransferFunction(field)
        lut.RescaleTransferFunction(FIELD_RANGES[field][0], FIELD_RANGES[field][1])
        lut.ApplyPreset('Rainbow Desaturated', True)
        lut.NumberOfTableValues = 256
        # Color bar
        cb = GetScalarBar(lut, rv)
        cb.Title = FIELD_TITLES[field]
        cb.ComponentTitle = ''
        cb.TitleFontSize = 18
        cb.LabelFontSize = 14
        cb.ScalarBarLength = 0.4
        cb.Position = [0.85, 0.25]
        cb.TitleColor = [0, 0, 0]
        cb.LabelColor = [0, 0, 0]
        cb.Visibility = 1
        active_dp = dp
        active_src = sl

    rv.ResetCamera()
    rv.CameraPosition = [0.5, 0.4, 2.0]
    rv.CameraFocalPoint = [0.5, 0.4, 0.0]
    rv.CameraViewUp = [0.0, 1.0, 0.0]
    rv.CameraParallelScale = 0.47
    rv.CameraParallelProjection = 1
    Render()

    outpath = os.path.join(OUT, f"{field}_{name}.png")
    SaveScreenshot(outpath, rv, ImageResolution=[IMG_W, IMG_H])
    print(f"  Saved: {outpath}")

    # Cleanup
    HideAll(rv)
    cb.Visibility = 0
    if field == "U":
        Delete(dp2)
        Delete(calc)
    Delete(dp)
    Delete(sl)
    Delete(reader)

# --- Main ---
print("Generating images for Mach 3 Cylinder AMR Presentation...")
print(f"Output: {OUT}\n")

for case_name, vtu_file in CASES.items():
    print(f"Processing {case_name}...")
    if not os.path.exists(vtu_file):
        print(f"  WARNING: {vtu_file} not found, skipping")
        continue

    # Mesh image
    rv = setup_view()
    save_mesh_image(vtu_file, case_name, rv)
    Delete(rv)

    # Contour images
    for field in ["p", "T", "U"]:
        rv = setup_view()
        save_contour_image(vtu_file, field, case_name, rv)
        Delete(rv)

print("\nAll images generated successfully!")
print(f"Total: {len(os.listdir(OUT))} images in {OUT}")
