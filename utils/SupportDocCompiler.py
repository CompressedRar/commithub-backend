from models.PCR import Supporting_Document, Assigned_PCR
from flask import jsonify
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Inches
import requests
import os
from io import BytesIO
def collect_by_department(dept_id):
    from models.System_Settings import System_Settings

    settings = System_Settings.get_default_settings()

    try:
        all_supporting_documents = Supporting_Document.query.filter_by(period = settings.current_period_id).all()

        filtered_documents = []

        for document in all_supporting_documents:
            print("COMparing docs", document.ipcr.user.department.id, dept_id)
            if str(document.ipcr.user.department.id) == dept_id:
                filtered_documents.append(document.to_dict())

        return filtered_documents
    except Exception as e:
        print("Error in collecting document")
        return []
    

def into_document(dept_id):
    # 1. Fetch the filtered documents
    documents = collect_by_department(str(dept_id))
    
    if not documents:
        return "There is no document to compile"

    # 2. Initialize the Template
    # Ensure 'template.docx' exists in your project directory
    doc = DocxTemplate("template.docx")
    
    compiled_data = []
    summary_list = []

    for doc_data in documents:
        # We only want images
        file_type = doc_data.get('file_type', '').lower()
        if any(ext in file_type for ext in ['jpg', 'jpeg', 'png', 'gif']):
            
            try:
                # Fetch image from the download_url
                response = requests.get(doc_data['download_url'])
                image_stream = BytesIO(response.content)

                # Prepare the main content entry
                entry = {
                    "title": doc_data['title'],
                    "event_date": doc_data['event_date'].strftime('%Y-%m-%d') if doc_data['event_date'] else "N/A",
                    "description": doc_data['desc'],
                    # InlineImage requires the doc object and the image stream/path
                    "image": InlineImage(doc, image_stream, width=Inches(5)) 
                }
                compiled_data.append(entry)

                # Prepare the summary entry
                summary_list.append({
                    "title": doc_data['title'],
                    "event_date": entry['event_date']
                })
            except Exception as e:
                print(f"Error processing image {doc_data['file_name']}: {e}")

    if not compiled_data:
        return "No valid image documents found to compile."

    # 3. Create the Context for the Template
    context = {
        "documents": compiled_data,
        "summaries": summary_list
    }

    # 4. Render and Save
    doc.render(context)
    output_path = f"compiled_report_dept_{dept_id}.docx"
    doc.save(output_path)

    return f"Document successfully compiled: {output_path}"
    




    



