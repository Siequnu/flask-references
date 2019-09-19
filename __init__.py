from flask import Blueprint

bp = Blueprint('references', __name__)

from app.references import routes