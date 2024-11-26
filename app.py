from flask import Flask, render_template, request, send_from_directory, jsonify
import os
from werkzeug.utils import secure_filename
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_SOLID
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib

app = Flask(__name__)

# Path to store uploaded files and temporary converted files
UPLOAD_FOLDER = 'uploads'
USER_DOWNLOAD_FOLDER = 'downloads'  # Folder to save converted .txt files
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(USER_DOWNLOAD_FOLDER, exist_ok=True)

# Configure the app
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['USER_DOWNLOAD_FOLDER'] = USER_DOWNLOAD_FOLDER


@app.route('/')
def index():
    # Render the HTML page for file upload
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

    # Process the .stp file and get bounding box and solid count info
    solids_info, shape = process_step_file(file_path)
    if solids_info:
        # Save the results as a .txt file in the download folder
        txt_filename = f"{os.path.splitext(safe_filename)[0]}.txt"
        txt_file_path = os.path.join(USER_DOWNLOAD_FOLDER, txt_filename)
        save_as_txt(solids_info, txt_file_path, shape)

        # Return success and the filename for the frontend
        return jsonify({'success': True, 'filename': txt_filename})

    return jsonify({'success': False, 'error': 'Processing failed. Please try again.'})


def process_step_file(stp_path):
    """
    Process the STEP file to extract solid bounding boxes and solid count.
    """
    try:
        # Initialize STEP reader
        step_reader = STEPControl_Reader()
        status = step_reader.ReadFile(stp_path)
        if status != 1:
            raise Exception(f"Error reading STEP file: {stp_path}")

        # Transfer the contents to a shape
        step_reader.TransferRoots()
        shape = step_reader.Shape()

        # Get the bounding boxes for each solid
        solid_boxes = calculate_individual_solid_bounding_boxes(shape)

        # Get the solid count
        solid_count = count_solids(shape)

        # Combine the results into one output
        result = {
            "solid_count": solid_count,
            "solids": solid_boxes
        }

        return result, shape

    except Exception as e:
        print(f"Error during processing: {e}")
        return None, None


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


def calculate_overall_bounding_box(shape):
    """
    Calculate the bounding box for the entire shape (not just individual solids).
    """
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


def save_as_txt(solids_info, file_path, shape):
    """
    Save the bounding box and solid count information as a .txt file,
    including the overall bounding box of the entire shape.
    """
    try:
        with open(file_path, 'w') as f:
            # First, write the overall bounding box information
            overall_bbox = calculate_overall_bounding_box(shape)
            f.write(f"Overall Dimensions:\n")
            f.write(f"Width: {overall_bbox['Width']},\nHeight: {overall_bbox['Height']},\nDepth: {overall_bbox['Depth']}\n")
            f.write("\n")

            # Now write the solid-specific bounding boxes
            f.write(f"Solid Count: {solids_info['solid_count']}\n\n")
            for idx, solid in enumerate(solids_info['solids'], 1):
                f.write(f"Solid {idx} Bounding Box:\n")
                f.write(f"  X_min: {solid['BoundingBox']['X_min']}, X_max: {solid['BoundingBox']['X_max']}\n")
                f.write(f"  Y_min: {solid['BoundingBox']['Y_min']}, Y_max: {solid['BoundingBox']['Y_max']}\n")
                f.write(f"  Z_min: {solid['BoundingBox']['Z_min']}, Z_max: {solid['BoundingBox']['Z_max']}\n")
                f.write(f"  Width: {solid['Width']}, Height: {solid['Height']}, Depth: {solid['Depth']}\n")
                f.write("\n")
    except Exception as e:
        print(f"Error saving .txt file: {e}")


@app.route('/download/<filename>')
def download_file(filename):
    """
    Serves the converted .txt file for download from the USER_DOWNLOAD_FOLDER.
    """
    file_path = os.path.join(app.config['USER_DOWNLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_from_directory(app.config['USER_DOWNLOAD_FOLDER'], filename, as_attachment=True)
    return jsonify({'success': False, 'error': 'File not found'}), 404


if __name__ == '__main__':
    app.run(debug=True)
