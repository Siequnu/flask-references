from flask import send_from_directory, current_app
from flask_login import current_user

import app.models
from app import db
from app.models import ReferenceUpload, ReferenceVersionUpload, ReferenceVersionDownload
from app.files import models

from datetime import datetime, date
from dateutil import tz
import arrow, json, time

from app import executor

def new_reference_version_from_form (form, original_reference_id):
	file = form.reference_upload_file.data
	random_filename = app.files.models.save_file(file)
	original_filename = app.files.models.get_secure_filename(file.filename)

	new_reference_version = ReferenceVersionUpload (original_reference_id = original_reference_id,
					user_id = current_user.id,
					original_filename = original_filename,
					filename = random_filename,
					description = form.description.data,
					timestamp = datetime.now())

	db.session.add(new_reference_version)
	db.session.commit()
	
	# Generate thumbnail
	executor.submit(app.files.models.get_thumbnail, new_reference_version.filename)
	
	
def download_reference_version (reference_version_id):
	download = ReferenceVersionDownload(reference_version_id = reference_version_id,
										user_id = current_user.id,
										timestamp = datetime.now())
	db.session.add(download)
	db.session.commit()
	
	filename = ReferenceVersionUpload.query.get(reference_version_id).filename
	original_filename = ReferenceVersionUpload.query.get(reference_version_id).original_filename
	
	return send_from_directory(filename=filename, directory=current_app.config['UPLOAD_FOLDER'],
								   as_attachment = True, attachment_filename = original_filename)

def delete_reference_version (reference_version_id):
	try:
		ReferenceVersionUpload.query.filter_by(id=reference_version_id).delete()
		db.session.commit()
		return True
	except:
		return False
	