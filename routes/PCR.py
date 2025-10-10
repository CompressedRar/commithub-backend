from flask import Blueprint, render_template, jsonify, request
from app import db
from utils.decorators import log_action
from models.User import Users
from models.PCR import PCR_Service
from models.Tasks import Tasks_Service
from utils import NewExcelHandler, FileStorage
import datetime
pcrs = Blueprint("pcrs", __name__, url_prefix="/api/v1/pcr")



@pcrs.route("/ipcr/<id>", methods = ["GET"])
def get_ipcr(id):
    return PCR_Service.get_ipcr(id)

@pcrs.route("/opcr/<id>", methods = ["GET"])
def get_opcr(id):
    return PCR_Service.get_opcr(id)

@pcrs.route("/ipcr/approve/<id>", methods = ["POST"])
def approve_ipcr(id):
    return PCR_Service.approve_ipcr(id)

@pcrs.route("/ipcr/review/<id>", methods = ["POST"])
def review_ipcr(id):
    return PCR_Service.review_ipcr(id)

@pcrs.route("/opcr/approve/<id>", methods = ["POST"])
def approve_opcr(id):
    return PCR_Service.approve_opcr(id)

@pcrs.route("/opcr/review/<id>", methods = ["POST"])
def review_opcr(id):
    return PCR_Service.review_opcr(id)

@pcrs.route("/ipcr/<id>", methods = ["DELETE"])
def archiv_ipcr(id):
    return PCR_Service.archive_ipcr(id)

@pcrs.route("/opcr/<id>", methods = ["DELETE"])
def archiv_opcr(id):
    return PCR_Service.archive_opcr(id)

@pcrs.route("/ipcr/<ipcr_id>&<user_id>", methods = ["PATCH"])
def assign_ipcr(ipcr_id, user_id):
    return PCR_Service.assign_main_ipcr(ipcr_id, user_id)

@pcrs.route("/ipcr/task/<main_task_id>&<batch_id>", methods = ["DELETE"])
def remove_task_from_ipcr(main_task_id, batch_id):
    return Tasks_Service.remove_output_by_main_task_id(main_task_id=main_task_id, batch_id=batch_id)


@pcrs.route("/ipcr/task/<main_task_id>&<batch_id>&<user_id>&<ipcr_id>", methods = ["POST"])
def add_task_to_ipcr(main_task_id, batch_id, user_id, ipcr_id):
    return Tasks_Service.create_task_for_ipcr(task_id=main_task_id, current_batch_id=batch_id , user_id=user_id, ipcr_id=ipcr_id)



@pcrs.route("/ipcr/download/<ipcr_id>", methods = ["GET"])
def download_ipcr(ipcr_id):

    file_url = NewExcelHandler.createNewIPCR_from_db(ipcr_id=ipcr_id, individuals={
        "review": {"name": "Arman Bitancur", "position": "Librarian II", "date": datetime.datetime(2025, 1, 15) },
        "approve": {"name": "Arman Bitancur", "position": "Librarian II", "date": datetime.datetime(2025, 1, 15) },
        "discuss": {"name": "Arman Bitancur", "position": "Librarian II", "date": datetime.datetime(2025, 1, 15) },
        "assess": {"name": "Arman Bitancur", "position": "Librarian II", "date": datetime.datetime(2025, 1, 15) },
        "final": {"name": "Arman Bitancur", "position": "Librarian II", "date": datetime.datetime(2025, 1, 15) },
        "confirm": {"name": "Arman Bitancur", "position": "Librarian II", "date": datetime.datetime(2025, 1, 15) }
    })

    return jsonify(link = file_url), 200

@pcrs.route("/ipcr/documents/<ipcr_id>", methods = ["GET"])
def get_supporting_documents(ipcr_id):
    return PCR_Service.get_ipcr_supporting_document(ipcr_id=ipcr_id)

@pcrs.route("/ipcr/documents/<document_id>", methods = ["DELETE"])
def archive_supporting_documents(document_id):
    return PCR_Service.archive_document(document_id=document_id)

@pcrs.route("/generate_presigned_url", methods = ["POST"])
def generate_presigned_url():
    file_name = request.json["fileName"]
    file_type = request.json["fileType"]
    return FileStorage.generate_presigned_url(file_name = file_name, file_type = file_type)

@pcrs.route("/record", methods = ["POST"])
def record_supporting_document():
    file_name = request.json["fileName"]
    file_type = request.json["fileType"]
    ipcr_id = request.json["ipcrID"]
    batch_id = request.json["batchID"]

    return PCR_Service.record_supporting_document(file_name=file_name, file_type=file_type, ipcr_id=ipcr_id, batch_id=batch_id)

@pcrs.route("/opcr/<dept_id>", methods = ["POST"])
def create_opcr(dept_id):
    ipcr_ids = request.json["ipcr_ids"]

    return PCR_Service.create_opcr(dept_id=dept_id, ipcr_ids=ipcr_ids)

@pcrs.route("/opcr/download/<opcr_id>", methods = ["GET"])
def test_opcr(opcr_id):
    file_link = PCR_Service.generate_opcr(opcr_id=opcr_id)
    return jsonify(link = file_link), 200

@pcrs.route("/master-opcr/download/", methods = ["GET"])
def test_master_opcr():
    file_link = PCR_Service.generate_master_opcr()
    return jsonify(link = file_link), 200




@pcrs.route("/ipcr/faculty/pending", methods = ["GET"])
def get_ipcr_pending():
    return PCR_Service.get_member_pendings()

@pcrs.route("/ipcr/faculty/reviewed", methods = ["GET"])
def get_ipcr_reviewed():
    return PCR_Service.get_member_reviewed()

@pcrs.route("/ipcr/faculty/approved", methods = ["GET"])
def get_ipcr_approved():
    return PCR_Service.get_member_approved()

@pcrs.route("/ipcr/head/pending", methods = ["GET"])
def get_head_pending():
    return PCR_Service.get_head_pendings()

@pcrs.route("/ipcr/head/reviewed", methods = ["GET"])
def get_head_reviewed():
    return PCR_Service.get_head_reviewed()

@pcrs.route("/ipcr/head/approved", methods = ["GET"])
def get_head_approved():
    return PCR_Service.get_head_approved()

@pcrs.route("/opcr/pending", methods = ["GET"])
def get_opcr_pending():
    return PCR_Service.get_opcr_pendings()

@pcrs.route("/opcr/reviewed", methods = ["GET"])
def get_opcr_reviewed():
    return PCR_Service.get_opcr_reviewed()

@pcrs.route("/opcr/approved", methods = ["GET"])
def get_opcr_approved():
    return PCR_Service.get_opcr_approved()