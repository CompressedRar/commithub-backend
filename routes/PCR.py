from flask import Blueprint, render_template, jsonify, request
from app import db
from utils.decorators import log_action, token_required
from models.User import Users
from models.PCR import PCR_Service
from models.Tasks import Tasks_Service
from utils import NewExcelHandler, FileStorage
import datetime
pcrs = Blueprint("pcrs", __name__, url_prefix="/api/v1/pcr")



@pcrs.route("/ipcr/<id>", methods = ["GET"])
@token_required()
def get_ipcr(id):
    return PCR_Service.get_ipcr(id)

@pcrs.route("/opcr/<id>", methods = ["GET"])
@token_required()
def get_opcr(id):
    return PCR_Service.get_opcr(id)

@pcrs.route("/master-opcr/", methods = ["GET"])
@token_required(allowed_roles=["administrator"])
def get_master_opcr():
    return PCR_Service.get_master_opcr()

@pcrs.route("/ipcr/approve/<id>", methods = ["POST"])
@token_required()
def approve_ipcr(id):
    return PCR_Service.approve_ipcr(id)

@pcrs.route("/ipcr/review/<id>", methods = ["POST"])
@token_required()
def review_ipcr(id):
    return PCR_Service.review_ipcr(id)

@pcrs.route("/ipcr/reject/<id>", methods = ["POST"])
@token_required()
def reject_ipcr(id):
    return PCR_Service.reject_ipcr(id)


@pcrs.route("/opcr/approve/<id>", methods = ["POST"])
@token_required()
def approve_opcr(id):
    return PCR_Service.approve_opcr(id)

@pcrs.route("/opcr/review/<id>", methods = ["POST"])
@token_required()
def review_opcr(id):
    return PCR_Service.review_opcr(id)


@pcrs.route("/ipcr/<id>", methods = ["DELETE"])
@token_required()
@log_action(action = "ARCHIVE", target="IPCR")
def archiv_ipcr(id):
    return PCR_Service.archive_ipcr(id)


@pcrs.route("/opcr/<id>", methods = ["DELETE"])
@token_required()
@log_action(action = "ARCHIVE", target="OPCR")
def archiv_opcr(id):
    return PCR_Service.archive_opcr(id)


@pcrs.route("/ipcr/<ipcr_id>&<user_id>", methods = ["PATCH"])
@token_required()
@log_action(action = "SUBMIT", target="IPCR")
def assign_ipcr(ipcr_id, user_id):
    return PCR_Service.assign_main_ipcr(ipcr_id, user_id)


@pcrs.route("/rating/<rating_id>", methods = ["PATCH"])
@token_required()
@log_action(action = "UPDATE", target="RATING")
def update_rating(rating_id):
    field = request.args.get("field")
    value = request.args.get("value")
    return PCR_Service.update_rating(rating_id, field, value)

@pcrs.route("/ipcr-pres/<ipcr_id>&<user_id>", methods = ["PATCH"])
@token_required()
def assign_pres_ipcr(ipcr_id, user_id):
    return PCR_Service.assign_pres_ipcr(ipcr_id, user_id)



@pcrs.route("/opcr/<opcr_id>&<dept_id>", methods = ["PATCH"])
@token_required()
@log_action(action = "SUBMIT", target="OPCR")
def assign_opcr(opcr_id, dept_id):
    return PCR_Service.assign_main_opcr(opcr_id, dept_id)

@pcrs.route("/opcr/reject/<opcr_id>", methods = ["PATCH"])
@token_required()
def reject_opcr(opcr_id):
    return PCR_Service.reject_opcr(opcr_id)


@pcrs.route("/ipcr/task/<main_task_id>&<batch_id>", methods = ["DELETE"])
@token_required()
def remove_task_from_ipcr(main_task_id, batch_id):
    return Tasks_Service.remove_output_by_main_task_id(main_task_id=main_task_id, batch_id=batch_id)


@pcrs.route("/ipcr/task/<main_task_id>&<batch_id>&<user_id>&<ipcr_id>", methods = ["POST"])
@token_required()
def add_task_to_ipcr(main_task_id, batch_id, user_id, ipcr_id):
    return Tasks_Service.create_task_for_ipcr(task_id=main_task_id, current_batch_id=batch_id , user_id=user_id, ipcr_id=ipcr_id)


@log_action(action = "DOWNLOAD", target="IPCR")
@token_required()
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
@token_required()
def get_supporting_documents(ipcr_id):
    return PCR_Service.get_ipcr_supporting_document(ipcr_id=ipcr_id)

@pcrs.route("/documents/<dept_id>", methods = ["GET"])
def collect_supporting_documents(dept_id):
    return PCR_Service.collect_all_supporting_documents_by_department(dept_id)

@pcrs.route("/opcr/documents/<opcr_id>", methods = ["GET"])
@token_required()
def get_supporting_documents_for_opcr(opcr_id):
    return PCR_Service.get_supporting_documents(opcr_id=opcr_id)

@log_action(action = "ARCHIVE", target="SUPPORTING_DOCS")
@token_required()
@pcrs.route("/ipcr/documents/<document_id>", methods = ["DELETE"])

def archive_supporting_documents(document_id):
    return PCR_Service.archive_document(document_id=document_id)

@pcrs.route("/generate_presigned_url", methods = ["POST"])
@token_required()
def generate_presigned_url():
    file_name = request.json["fileName"]
    file_type = request.json["fileType"]
    return FileStorage.generate_presigned_url(file_name = file_name, file_type = file_type)


@pcrs.route("/record", methods = ["POST"])
@token_required()
@log_action(action = "CREATE", target="SUPPORTING_DOCS")

def record_supporting_document():
    file_name = request.json["fileName"]
    file_type = request.json["fileType"]
    ipcr_id = request.json["ipcrID"]
    batch_id = request.json["batchID"]
    sub_task_id = request.json.get("subTaskID", None)

    return PCR_Service.record_supporting_document(file_name=file_name, file_type=file_type, ipcr_id=ipcr_id, batch_id=batch_id, sub_task_id=sub_task_id)

@pcrs.route("/record-opcr", methods = ["POST"])
@token_required()
def record_supporting_document_for_opcr():
    file_name = request.json["fileName"]
    file_type = request.json["fileType"]
    ipcr_id = request.json["ipcrID"]
    batch_id = request.json["batchID"]

    return PCR_Service.record_supporting_document(file_name=file_name, file_type=file_type, ipcr_id=ipcr_id, batch_id=batch_id)


@pcrs.route("/opcr/<dept_id>", methods = ["POST"])
@token_required()
def create_opcr(dept_id):
    ipcr_ids = request.json["ipcr_ids"]

    return PCR_Service.create_opcr(dept_id=dept_id, ipcr_ids=ipcr_ids)


@pcrs.route("/opcr/download/<opcr_id>", methods = ["GET"])
@token_required(allowed_roles=["administrator", "head"])
@log_action(action = "DOWNLOAD", target="OPCR")

def test_opcr(opcr_id):
    file_link = PCR_Service.generate_opcr(opcr_id=opcr_id)
    return jsonify(link = file_link), 200

@pcrs.route("/planned-opcr/download/<dept_id>", methods = ["GET"])
@token_required(allowed_roles=["administrator", "head"])
@log_action(action = "DOWNLOAD", target="OPCR")

def download_planned_opcr(dept_id):
    file_link = PCR_Service.generate_planned_opcr_by_department(department_id=dept_id)
    return jsonify(link = file_link), 200

@pcrs.route("/weighted-opcr/download/<opcr_id>", methods = ["GET"])
@token_required(allowed_roles=["administrator", "head"])
@log_action(action = "DOWNLOAD", target="OPCR")

def download_weighted_opcr(opcr_id):
    file_link = PCR_Service.generate_weighted_opcr(opcr_id)
    return jsonify(link = file_link), 200

@pcrs.route("/master-opcr/download/", methods = ["GET"])
@token_required(allowed_roles=["administrator"])
@log_action(action = "DOWNLOAD", target="MASTER OPCR")

def test_master_opcr():
    return PCR_Service.generate_master_opcr()




@pcrs.route("/ipcr/faculty/pending/<dept_id>", methods = ["GET"])
@token_required()
def get_ipcr_pending(dept_id):
    return PCR_Service.get_member_pendings(dept_id=dept_id)

@pcrs.route("/ipcr/faculty/reviewed", methods = ["GET"])
@token_required()
def get_ipcr_reviewed():
    return PCR_Service.get_member_reviewed()

@pcrs.route("/ipcr/faculty/approved", methods = ["GET"])
@token_required()
def get_ipcr_approved():
    return PCR_Service.get_member_approved()

@pcrs.route("/ipcr/head/pending", methods = ["GET"])
@token_required()
def get_head_pending():
    return PCR_Service.get_head_pendings()

@pcrs.route("/ipcr/head/reviewed", methods = ["GET"])
@token_required()
def get_head_reviewed():
    return PCR_Service.get_head_reviewed()

@pcrs.route("/ipcr/head/approved", methods = ["GET"])
@token_required()
def get_head_approved():
    return PCR_Service.get_head_approved()

@pcrs.route("/opcr/pending", methods = ["GET"])
@token_required()
def get_opcr_pending():
    return PCR_Service.get_opcr_pendings()

@pcrs.route("/opcr/reviewed", methods = ["GET"])
@token_required()
def get_opcr_reviewed():
    return PCR_Service.get_opcr_reviewed()

@pcrs.route("/opcr/approved", methods = ["GET"])
@token_required()
def get_opcr_approved():
    return PCR_Service.get_opcr_approved()


@pcrs.route("/planned-opcr/<dept_id>", methods = ["GET"])
def get_planned_opcr(dept_id):
    return PCR_Service.get_planned_opcr_by_department(dept_id)
