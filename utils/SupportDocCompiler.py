
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Inches
import requests
import os
from io import BytesIO
import io
from utils.FileStorage import upload_file
import random
from itertools import groupby
from flask import send_file


def collect_by_department(dept_id):
    from models.PCR import Supporting_Document
    from models.System_Settings import System_Settings

    settings = System_Settings.get_default_settings()

    try:
        all_supporting_documents = Supporting_Document.query.filter_by(period = settings.current_period_id).all()

        filtered_documents = []

        for document in all_supporting_documents:
            print("COMparing docs", document.ipcr.user.department.id, dept_id)
            if str(document.ipcr.user.department.id) == dept_id and document.status:
                print("Meron")
                filtered_documents.append(document.to_dict())

        return filtered_documents
    except Exception as e:
        print("Error in collecting document")
        return []


def collect_by_ipcr(ipcr_id):
    from models.PCR import Supporting_Document, IPCR
    from models.System_Settings import System_Settings

    settings = System_Settings.get_default_settings()

    try:
        ipcr = IPCR.query.get(ipcr_id)
        

        if not ipcr:
            print("no ipcrs")
            return []
        
        documents = ipcr.supporting_documents
        
        if not documents:
            return []
    
        filtered_documents = []

        for document in documents:
            if document.status:
                print("Meron")
                filtered_documents.append(document.to_dict())

        return filtered_documents
    except Exception as e:
        print("Error in collecting document", e)
        return []
    

def into_document(documents):
    if not documents:
        return None

    doc = DocxTemplate("excels/template(1).docx")
    
    # 1. Sort the data by task_name first (Required for groupby)
    documents.sort(key=lambda x: x.get('task_name', 'Unassigned'))

    grouped_data = []

    # 2. Group documents by task_name
    for task_name, items in groupby(documents, key=lambda x: x.get('task_name', 'Unassigned')):
        task_entries = []
        
        for doc_data in items:
            file_type = doc_data.get('file_type', '').lower()
            if any(ext in file_type for ext in ['jpg', 'jpeg', 'png', 'gif']):
                try:
                    response = requests.get(doc_data['download_url'])
                    image_stream = BytesIO(response.content)

                    task_entries.append({
                        "task_name": doc_data["task_name"],
                        "title": doc_data['title'],
                        "event_date": doc_data['event_date'].strftime('%Y-%m-%d') if doc_data['event_date'] else "N/A",
                        "description": doc_data['desc'],
                        "image": InlineImage(doc, image_stream, width=Inches(5))
                    })
                except Exception as e:
                    print(f"Error processing image: {e}")
                    continue
        
        # Only add the task if it contains valid images
        if task_entries:
            print("TASK ENTRIES", task_entries)
            grouped_data.append({
                "task_name": task_name,
                "entries": task_entries
            })

    if not grouped_data:
        return None

    # 3. Create the Context
    context = {
        "tasks": grouped_data  # This is now a nested list
    }

    # 4. Render and Save
    
    id_rand = random.randint(1, 999999)
    doc.render(context)
    output_path = f"excels/docs/compiled_report_dept_{id_rand}.docx"
    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0) # Go to the start of the file

    return send_file(
        file_stream,
        as_attachment=True,
        download_name="Report.docx",
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    




