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

@pcrs.route("/master-opcr/", methods = ["GET"])
def get_master_opcr():
    return PCR_Service.get_master_opcr()

@pcrs.route("/ipcr/approve/<id>", methods = ["POST"])
def approve_ipcr(id):
    return PCR_Service.approve_ipcr(id)

@pcrs.route("/ipcr/review/<id>", methods = ["POST"])
def review_ipcr(id):
    return PCR_Service.review_ipcr(id)

@pcrs.route("/ipcr/reject/<id>", methods = ["POST"])
def reject_ipcr(id):
    return PCR_Service.reject_ipcr(id)


@pcrs.route("/opcr/approve/<id>", methods = ["POST"])
def approve_opcr(id):
    return PCR_Service.approve_opcr(id)

@pcrs.route("/opcr/review/<id>", methods = ["POST"])
def review_opcr(id):
    return PCR_Service.review_opcr(id)

@log_action(action = "ARCHIVE", target="IPCR")
@pcrs.route("/ipcr/<id>", methods = ["DELETE"])
def archiv_ipcr(id):
    return PCR_Service.archive_ipcr(id)

@log_action(action = "ARCHIVE", target="OPCR")
@pcrs.route("/opcr/<id>", methods = ["DELETE"])
def archiv_opcr(id):
    return PCR_Service.archive_opcr(id)

@log_action(action = "SUBMIT", target="IPCR")
@pcrs.route("/ipcr/<ipcr_id>&<user_id>", methods = ["PATCH"])
def assign_ipcr(ipcr_id, user_id):
    return PCR_Service.assign_main_ipcr(ipcr_id, user_id)

@log_action(action = "UPDATE", target="RATING")
@pcrs.route("/rating/<rating_id>", methods = ["PATCH"])
def update_rating(rating_id):
    field = request.args.get("field")
    value = request.args.get("value")
    return PCR_Service.update_rating(rating_id, field, value)

@pcrs.route("/ipcr-pres/<ipcr_id>&<user_id>", methods = ["PATCH"])
def assign_pres_ipcr(ipcr_id, user_id):
    return PCR_Service.assign_pres_ipcr(ipcr_id, user_id)


@log_action(action = "SUBMIT", target="OPCR")
@pcrs.route("/opcr/<opcr_id>&<dept_id>", methods = ["PATCH"])
def assign_opcr(opcr_id, dept_id):
    return PCR_Service.assign_main_opcr(opcr_id, dept_id)

@pcrs.route("/opcr/reject/<opcr_id>", methods = ["PATCH"])
def reject_opcr(opcr_id):
    return PCR_Service.reject_opcr(opcr_id)


@pcrs.route("/ipcr/task/<main_task_id>&<batch_id>", methods = ["DELETE"])
def remove_task_from_ipcr(main_task_id, batch_id):
    return Tasks_Service.remove_output_by_main_task_id(main_task_id=main_task_id, batch_id=batch_id)


@pcrs.route("/ipcr/task/<main_task_id>&<batch_id>&<user_id>&<ipcr_id>", methods = ["POST"])
def add_task_to_ipcr(main_task_id, batch_id, user_id, ipcr_id):
    return Tasks_Service.create_task_for_ipcr(task_id=main_task_id, current_batch_id=batch_id , user_id=user_id, ipcr_id=ipcr_id)


@log_action(action = "DOWNLOAD", target="IPCR")
@pcrs.route("/ipcr/download/<ipcr_id>", methods = ["GET"])
def download_ipcr(ipcr_id):

    file_url = NewExcelHandler.createNewIPCR_from_db(ipcr_id=ipcr_id, individuals={
        "review": {"name": "Arman Bitancur", "position": "Librarian II", "date": ""},
        "approve": {"name": "Arman Bitancur", "position": "Librarian II", "date": "" },
        "discuss": {"name": "Arman Bitancur", "position": "Librarian II", "date": "" },
        "assess": {"name": "Arman Bitancur", "position": "Librarian II", "date": "" },
        "final": {"name": "Arman Bitancur", "position": "Librarian II", "date": "" },
        "confirm": {"name": "Arman Bitancur", "position": "Librarian II", "date": "" }
    })

    return jsonify(link = file_url), 200

@pcrs.route("/ipcr/documents/<ipcr_id>", methods = ["GET"])
def get_supporting_documents(ipcr_id):
    return PCR_Service.get_ipcr_supporting_document(ipcr_id=ipcr_id)

@pcrs.route("/opcr/documents/<opcr_id>", methods = ["GET"])
def get_supporting_documents_for_opcr(opcr_id):
    return PCR_Service.get_supporting_documents(opcr_id=opcr_id)

@log_action(action = "ARCHIVE", target="SUPPORTING_DOCS")
@pcrs.route("/ipcr/documents/<document_id>", methods = ["DELETE"])
def archive_supporting_documents(document_id):
    return PCR_Service.archive_document(document_id=document_id)

@pcrs.route("/generate_presigned_url", methods = ["POST"])
def generate_presigned_url():
    file_name = request.json["fileName"]
    file_type = request.json["fileType"]
    return FileStorage.generate_presigned_url(file_name = file_name, file_type = file_type)

@log_action(action = "CREATE", target="SUPPORTING_DOCS")
@pcrs.route("/record", methods = ["POST"])
def record_supporting_document():
    file_name = request.json["fileName"]
    file_type = request.json["fileType"]
    ipcr_id = request.json["ipcrID"]
    batch_id = request.json["batchID"]

    return PCR_Service.record_supporting_document(file_name=file_name, file_type=file_type, ipcr_id=ipcr_id, batch_id=batch_id)

@pcrs.route("/record-opcr", methods = ["POST"])
def record_supporting_document_for_opcr():
    file_name = request.json["fileName"]
    file_type = request.json["fileType"]
    ipcr_id = request.json["ipcrID"]
    batch_id = request.json["batchID"]

    return PCR_Service.record_supporting_document(file_name=file_name, file_type=file_type, ipcr_id=ipcr_id, batch_id=batch_id)

@log_action(action = "CREATE", target="OPCR")
@pcrs.route("/opcr/<dept_id>", methods = ["POST"])
def create_opcr(dept_id):
    ipcr_ids = request.json["ipcr_ids"]

    return PCR_Service.create_opcr(dept_id=dept_id, ipcr_ids=ipcr_ids)

@log_action(action = "DOWNLOAD", target="OPCR")
@pcrs.route("/opcr/download/<opcr_id>", methods = ["GET"])
def test_opcr(opcr_id):
    file_link = PCR_Service.generate_opcr(opcr_id=opcr_id)
    return jsonify(link = file_link), 200

@log_action(action = "DOWNLOAD", target="MASTER OPCR")
@pcrs.route("/master-opcr/download/", methods = ["GET"])
def test_master_opcr():
    return PCR_Service.generate_master_opcr()




@pcrs.route("/ipcr/faculty/pending/<dept_id>", methods = ["GET"])
def get_ipcr_pending(dept_id):
    return PCR_Service.get_member_pendings(dept_id=dept_id)

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