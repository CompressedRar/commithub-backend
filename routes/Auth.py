from flask import Blueprint, render_template
from app import db

auth = Blueprint("auth", __name__)

@auth.route("/")
def home():
    return "working now"
