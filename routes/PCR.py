from flask import Blueprint, render_template, jsonify, request
from app import db
from utils.decorators import log_action
from models.User import Users
from models.PCR import PCR_Service
pcrs = Blueprint("pcrs", __name__, url_prefix="/api/v1/pcr")



@pcrs.route("/ipcr/<id>", methods = ["GET"])
def get_ipcr(id):
    return PCR_Service.get_ipcr(id)

@pcrs.route("/ipcr/<ipcr_id>&<user_id>", methods = ["PATCH"])
def assign_ipcr(ipcr_id, user_id):
    return PCR_Service.assign_main_ipcr(ipcr_id, user_id)




