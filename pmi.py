from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.TDocStd import TDocStd_Application, TDocStd_Document
from OCC.Core.XCAFApp import XCAFApp_Application
from OCC.Core.XCAFDoc import XCAFDoc_DocumentTool
from OCC.Core.TCollection import TCollection_ExtendedString
from OCC.Core.TDF import TDF_LabelSequence
from OCC.Core.TDataStd import TDataStd_Name

def load_step_with_pmi(file_path):
    # Initialize the XCAF application
    app = XCAFApp_Application.GetApplication()

    # Create a new document handle for XCAF
    doc_type = TCollection_ExtendedString("XCAF")  # Specify the document type
    doc_handle = TDocStd_Document(doc_type)  # Create the document handle with type argument
    if doc_handle.IsNull():
        raise Exception("Failed to create a new XCAF document.")

    # Load the STEP file
    step_reader = STEPControl_Reader()
    status = step_reader.ReadFile(file_path)

    if status != 1:
        raise Exception(f"Error reading STEP file: {file_path}")

    # Transfer contents to XCAF document
    step_reader.Transfer(doc_handle)

    # Extract PMI annotations
    return extract_pmi_annotations(doc_handle)

def extract_pmi_annotations(doc_handle):
    label_tool = XCAFDoc_DocumentTool.LabelShapeTool(doc_handle.Main())
    annotations = []

    labels = TDF_LabelSequence()
    label_tool.GetFreeShapes(labels)

    print(f"Total labels found: {labels.Length()}")  # Debug: Print number of labels

    for i in range(labels.Length()):
        label = labels.Value(i + 1)
        name = TDataStd_Name().Get(label)
        if name:
            annotations.append(name)

    print(f"PMI annotations extracted: {annotations}")  # Debug: Print extracted annotations
    return annotations

def main():
    input_file = "stepfile.stp"  # Replace with your STEP file path
    pmi_annotations = load_step_with_pmi(input_file)

    # Output PMI annotations to a text file
    output_file = "pmi_annotations.txt"
    with open(output_file, 'w') as file:
        if pmi_annotations:
            file.write("PMI Annotations:\n")
            for annotation in pmi_annotations:
                file.write(f"- {annotation}\n")
        else:
            file.write("No PMI annotations found.\n")

    print(f"PMI annotations have been saved to {output_file}.")

if __name__ == "__main__":
    main()
