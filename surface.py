from flask import Flask, render_template, request, send_from_directory, jsonify
import os
from werkzeug.utils import secure_filename
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_EDGE
from OCC.Core.BRep import BRep_Tool
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.Geom import Geom_Plane, Geom_RectangularTrimmedSurface

app = Flask(__name__)

# Path to store uploaded files and temporary converted files
UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

# Configure the app
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_FOLDER'] = CONVERTED_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'})

    file = request.files['file']
    filename = file.filename

    if not filename:
        return jsonify({'success': False, 'error': 'No selected file'})

    # Validate file extension
    if not filename.lower().endswith('.stp'):
        return jsonify({'success': False, 'error': 'Invalid file extension. Please upload a .stp file.'})

    # Save the uploaded file
    safe_filename = secure_filename(filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
    file.save(file_path)

    # Convert the .stp file to .txt
    txt_filename = convert_to_txt(file_path, safe_filename)
    if txt_filename:
        return jsonify({'success': True, 'filename': txt_filename})

    return jsonify({'success': False, 'error': 'Conversion failed. Please try again.'})

# def extract_bounded_surfaces(shape):
#     explorer = TopExp_Explorer(shape, TopAbs_FACE)
#     surfaces = []
#
#     while explorer.More():
#         face = explorer.Current()
#         surface = BRep_Tool.Surface(face)
#         area = None
#         surface_type = surface.DynamicType().Name()
#
#         if isinstance(surface, Geom_RectangularTrimmedSurface):
#             u_min, u_max, v_min, v_max = surface.Bounds()
#             if u_min != u_max and v_min != v_max:
#                 area = (u_max - u_min) * (v_max - v_min)
#             else:
#                 area = "Invalid bounds"
#         elif isinstance(surface, Geom_Plane):
#             area = "Infinite"
#
#         edge_explorer = TopExp_Explorer(face, TopAbs_EDGE)
#         edge_count = 0
#         while edge_explorer.More():
#             edge_explorer.Next()
#             edge_count += 1
#
#         surfaces.append({
#             "Type": surface_type,
#             "Area": area if area is not None else "Infinite",
#             "EdgeCount": edge_count,
#             "Bounds": surface.Bounds()
#         })
#
#         explorer.Next()
#
#     return surfaces

def extract_bounded_surfaces(shape):
    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    surfaces = []

    while explorer.More():
        face = explorer.Current()
        surface = BRep_Tool.Surface(face)
        area = None
        surface_type = surface.DynamicType().Name()

        if isinstance(surface, Geom_RectangularTrimmedSurface):
            # Get actual trimmed surface using Surface.TrimmedSurface()
            trimmed_surface = surface.TrimmedSurface()
            if trimmed_surface:
                u_min, u_max, v_min, v_max = trimmed_surface.Bounds()
                if u_min != u_max and v_min != v_max:
                    area = (u_max - u_min) * (v_max - v_min)
                else:
                    area = "Invalid bounds"
            else:
                area = "Not a valid trimmed surface"
        elif isinstance(surface, Geom_Plane):
            area = "Infinite"

        edge_explorer = TopExp_Explorer(face, TopAbs_EDGE)
        edge_count = 0
        while edge_explorer.More():
            edge_explorer.Next()
            edge_count += 1

        surfaces.append({
            "Type": surface_type,
            "Area": area if area is not None else "Infinite",
            "EdgeCount": edge_count,
            "Bounds": surface.Bounds()
        })

        explorer.Next()

    return surfaces

def extract_dimensions(shape):
    """ Extracts the dimensions (bounding box) of the shape. """
    bbox = Bnd_Box()
    brepbndlib.Add(shape, bbox)

    # Get the min and max bounds of the shape
    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()

    # Return the dimensions (width, height, depth)
    return {
        "Width": xmax - xmin,
        "Height": ymax - ymin,
        "Depth": zmax - zmin
    }

def convert_to_txt(stp_path, original_filename):
    """
    Converts an .stp file to a .txt file by extracting information about solids, dimensions, and surfaces.
    """
    try:
        # Strip the .stp extension and create the .txt file name
        txt_filename = original_filename.rsplit('.', 1)[0] + '.txt'

        # Define the output .txt file path in the converted folder
        output_txt = os.path.join(app.config['CONVERTED_FOLDER'], txt_filename)

        # Initialize STEP reader and load the file
        step_reader = STEPControl_Reader()
        status = step_reader.ReadFile(stp_path)
        if status != 1:
            return None

        step_reader.TransferRoots()
        shape = step_reader.Shape()

        # Extract information about solids, dimensions, and surfaces
        with open(output_txt, 'w') as txt_file:
            # Write the dimensions of the solid (bounding box)
            dimensions = extract_dimensions(shape)
            txt_file.write("Solid Dimensions (Bounding Box):\n")
            txt_file.write(f"  Width: {dimensions['Width']}\n")
            txt_file.write(f"  Height: {dimensions['Height']}\n")
            txt_file.write(f"  Depth: {dimensions['Depth']}\n")

            # Surface information
            txt_file.write("\nSurface Information:\n")
            for idx, surface in enumerate(extract_bounded_surfaces(shape)):
                txt_file.write(f"\nSurface {idx + 1}:\n")
                txt_file.write(f"  Type: {surface['Type']}\n")
                txt_file.write(f"  Area: {surface['Area']}\n")
                txt_file.write(f"  Edge Count: {surface['EdgeCount']}\n")
                txt_file.write(f"  Bounds: {surface['Bounds']}\n")

        return txt_filename

    except Exception as e:
        print(f"Error during conversion: {e}")
        return None

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['CONVERTED_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_from_directory(app.config['CONVERTED_FOLDER'], filename, as_attachment=True)
    return jsonify({'success': False, 'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
