from flask import Blueprint, render_template, jsonify, request
from app import db
import requests 
ai = Blueprint("ai", __name__, url_prefix="/api/v1/ai")
