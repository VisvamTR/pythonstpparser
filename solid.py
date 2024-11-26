from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_SOLID
import os

def load_step_file(file_path):
    # Initialize STEP reader
    step_reader = STEPControl_Reader()

    # Read the STEP file
    status = step_reader.ReadFile(file_path)

    # Check if reading is successful
    if status != 1:
        raise Exception(f"Error reading STEP file: {file_path}")

    # Transfer the contents to a shape
    step_reader.TransferRoots()
    return step_reader.Shape()

def calculate_overall_bounding_box(shape):
    # Create a bounding box for the entire shape
    bbox = Bnd_Box()
    brepbndlib.Add(shape, bbox)

    # Get bounding box dimensions and coordinates
    x_min, y_min, z_min, x_max, y_max, z_max = bbox.Get()
    return {
        "Width": x_max - x_min,
        "Height": y_max - y_min,
        "Depth": z_max - z_min,
        "BoundingBox": {
            "X_min": x_min, "Y_min": y_min, "Z_min": z_min,
            "X_max": x_max, "Y_max": y_max, "Z_max": z_max
        }
    }

def calculate_individual_solid_bounding_boxes(shape):
    # Initialize a list to hold bounding boxes for each solid
    solid_boxes = []
    explorer = TopExp_Explorer(shape, TopAbs_SOLID)

    while explorer.More():
        solid = explorer.Current()  # Get the current solid
        bbox = Bnd_Box()
        brepbndlib.Add(solid, bbox)  # Calculate bounding box for this solid
        x_min, y_min, z_min, x_max, y_max, z_max = bbox.Get()
        solid_boxes.append({
            "BoundingBox": {
                "X_min": x_min, "Y_min": y_min, "Z_min": z_min,
                "X_max": x_max, "Y_max": y_max, "Z_max": z_max
            },
            "Width": x_max - x_min,
            "Height": y_max - y_min,
            "Depth": z_max - z_min
        })
        explorer.Next()

    return solid_boxes

def count_solids(shape):
    # Count the number of solids in the shape
    solid_count = 0
    explorer = TopExp_Explorer(shape, TopAbs_SOLID)
    while explorer.More():
        solid_count += 1
        explorer.Next()
    return solid_count

def save_to_single_file(input_file, overall_bbox, solid_boxes, solid_count):
    # Save both overall and individual bounding boxes to a single text file
    base_name = os.path.splitext(input_file)[0]
    txt_file = f"{base_name}.txt"

    with open(txt_file, "w") as f:
        # Write overall bounding box details
        f.write(f"Number of Solids: {solid_count}\n\n")
        f.write("Overall Bounding Box Dimensions:\n")
        f.write(f"  Width: {overall_bbox['Width']}\n")
        f.write(f"  Height: {overall_bbox['Height']}\n")
        f.write(f"  Depth: {overall_bbox['Depth']}\n\n")
        f.write("Bounding Box Coordinates:\n")
        f.write(f"  X_min: {overall_bbox['BoundingBox']['X_min']}\n")
        f.write(f"  Y_min: {overall_bbox['BoundingBox']['Y_min']}\n")
        f.write(f"  Z_min: {overall_bbox['BoundingBox']['Z_min']}\n")
        f.write(f"  X_max: {overall_bbox['BoundingBox']['X_max']}\n")
        f.write(f"  Y_max: {overall_bbox['BoundingBox']['Y_max']}\n")
        f.write(f"  Z_max: {overall_bbox['BoundingBox']['Z_max']}\n\n")

        # Write individual solid bounding boxes
        f.write("Individual Solid Bounding Boxes:\n")
        for idx, solid in enumerate(solid_boxes):
            f.write(f"Solid {idx + 1}:\n")
            f.write(f"  Width: {solid['Width']}\n")
            f.write(f"  Height: {solid['Height']}\n")
            f.write(f"  Depth: {solid['Depth']}\n")
            f.write("  Bounding Box Coordinates:\n")
            f.write(f"    X_min: {solid['BoundingBox']['X_min']}\n")
            f.write(f"    Y_min: {solid['BoundingBox']['Y_min']}\n")
            f.write(f"    Z_min: {solid['BoundingBox']['Z_min']}\n")
            f.write(f"    X_max: {solid['BoundingBox']['X_max']}\n")
            f.write(f"    Y_max: {solid['BoundingBox']['Y_max']}\n")
            f.write(f"    Z_max: {solid['BoundingBox']['Z_max']}\n")
            f.write("\n")
    print(f"All bounding box details saved to {txt_file}")

def main():
    input_file = "stepfile.stp"  # Replace with your STEP file path
    shape = load_step_file(input_file)

    # Calculate overall bounding box
    overall_bbox = calculate_overall_bounding_box(shape)

    # Calculate individual bounding boxes for solids
    solid_boxes = calculate_individual_solid_bounding_boxes(shape)

    # Count the number of solids
    solid_count = count_solids(shape)

    # Save details to a single file
    save_to_single_file(input_file, overall_bbox, solid_boxes, solid_count)

if __name__ == "__main__":
    main()
