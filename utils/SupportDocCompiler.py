from models.PCR import Supporting_Document, Assigned_PCR
from flask import jsonify

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
    

def into_document():
    if not collect_by_department(1):
        return "There is no document to compile"
    

    


    



