"""Open one prepared UMD case in 3D Slicer: the owner's check tool. Readers never use Slicer.

Do not run this file with uv or python: 3D Slicer's own Python runs it. Start it with

    uv run --group prep python prep/umd_stack.py slicer case-03

The launcher passes the case in environment variables (Slicer would try to open extra
command-line arguments as files):
    NESHAT_T2, NESHAT_TRUTH, NESHAT_AI   the T2 image, the expert mask, the model's prediction
    NESHAT_POINT                         "R A S": the key point in patient mm (from private/map.csv)
    NESHAT_PERCENTILES                   "0.1 99.9": the same window as the phone slices

What you see: the T2 image with the phone's window, the expert mask ("Truth", filled) and the
model's prediction ("AI", outline only), in one large sagittal view centred on the key point.
The view is turned to the acquired slice plane ("Rotate to volume plane"), so it shows the same
slices as the phone, even on a tilted scan. Move through the slices with the arrow keys or the
slider above the view: each step is one phone slice. Hover over the image to see the segment
names (Truth cyst, AI cyst, ...) in the corner.

Self-test with synthetic files only: set NESHAT_SLICER_TEST to a report path and start Slicer
with --no-main-window. The view steps need a main window, so they are skipped; the script
writes what it loaded to the report and closes Slicer.
"""

import os
import traceback

import numpy as np
import slicer

LABELS = {1: "wall", 2: "cavity", 3: "myoma", 4: "cyst"}  # UMD mask labels


def load_case():
    """Load the image and both masks. Returns (volume node, [Truth node, AI node])."""
    volume = slicer.util.loadVolume(os.environ["NESHAT_T2"])
    volume.SetName("T2")
    low, high = np.percentile(slicer.util.arrayFromVolume(volume), [float(p) for p in os.environ["NESHAT_PERCENTILES"].split()])
    display = volume.GetDisplayNode()
    display.AutoWindowLevelOff()
    display.SetWindowLevel(high - low, (high + low) / 2)  # window = width, level = centre
    masks = []
    for name, variable in (("Truth", "NESHAT_TRUTH"), ("AI", "NESHAT_AI")):
        node = slicer.util.loadSegmentation(os.environ[variable])
        node.SetName(name)
        segmentation = node.GetSegmentation()
        for index in range(segmentation.GetNumberOfSegments()):
            segment = segmentation.GetNthSegment(index)
            segment.SetName(f"{name} {LABELS.get(segment.GetLabelValue(), segment.GetLabelValue())}")
        masks.append(node)
    masks[1].GetDisplayNode().SetVisibility2DFill(False)  # AI as an outline over the filled truth
    return volume, masks


def show(volume, point):
    """One large sagittal view on the T2 image, centred on the key point. The view is turned to
    the acquired slice plane, so each arrow-key step shows one phone slice, not a blend."""
    layout = slicer.app.layoutManager()
    layout.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpYellowSliceView)
    slicer.util.setSliceViewerLayers(background=volume, fit=True, rotateToVolumePlane=True)
    for view in ("Red", "Yellow", "Green"):  # the other views follow, for when the layout changes
        layout.sliceWidget(view).mrmlSliceNode().JumpSliceByCentering(*point)


def report(path, volume, masks):
    """Self-test only: write what loaded, then close Slicer."""
    display = volume.GetDisplayNode()
    lines = [f"volume {volume.GetName()} dims {volume.GetImageData().GetDimensions()}",
             f"window {display.GetWindow():.1f} level {display.GetLevel():.1f} auto {display.GetAutoWindowLevel()}",
             f"layout manager {'yes' if slicer.app.layoutManager() else 'none (views skipped)'}"]
    for node in masks:
        segmentation = node.GetSegmentation()
        names = [segmentation.GetNthSegment(i).GetName() for i in range(segmentation.GetNumberOfSegments())]
        lines.append(f"segmentation {node.GetName()}: {', '.join(names)}; 2D fill {node.GetDisplayNode().GetVisibility2DFill()}")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def main():
    test_report = os.environ.get("NESHAT_SLICER_TEST")
    try:
        volume, masks = load_case()
        if slicer.app.layoutManager() is not None:  # None when Slicer runs with no main window
            show(volume, [float(v) for v in os.environ["NESHAT_POINT"].split()])
        if test_report:
            report(test_report, volume, masks)
    except Exception:
        if not test_report:
            raise  # the owner sees the error in Slicer's Python console
        with open(test_report, "w", encoding="utf-8") as handle:
            handle.write("FAILED\n" + traceback.format_exc())
    if test_report:
        slicer.util.exit(0)


main()
