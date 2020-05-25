from flask import Blueprint

bp = Blueprint('references', __name__, template_folder = 'templates')

from app.references import routes