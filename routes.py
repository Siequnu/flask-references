from flask import render_template, flash, redirect, url_for, request, current_app, send_file, abort, session
from flask_login import current_user
from flask_login import login_required

from app import db
import app.models

import json
import arrow
from dateutil import tz

from app.models import ReferenceUpload, ReferenceVersionDownload, ReferenceVersionUpload, User

from app.references import bp, models
from app.references.forms import ReferencePasswordForm, StudentReferenceForm, EditedReferenceForm

from flask_weasyprint import HTML, render_pdf


# Log-in gateway to access the references portal
@bp.route("/", methods=['GET', 'POST'])
def references_login():
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		return redirect (url_for('references.view_references'))
	form = ReferencePasswordForm()
	return render_template('references/references_login.html', title = 'Log-in to references', form=form)

# Administrator log-in redirect function
@bp.route("/login/admin")
@login_required
def admin_references_login():
	return redirect (url_for('references.view_references'))

# Compose a reference
@bp.route("/compose", methods=['GET', 'POST'])
def compose_reference():
	form = StudentReferenceForm()
	if request.values.get('password') and request.values.get('password') in current_app.config['SIGNUP_CODES'] or current_user.is_authenticated and app.models.is_admin(current_user.username):	
		return render_template('references/compose_reference.html', title = 'Submit student reference', form=form)
	abort (403)

# Submit reference
@bp.route("/submit", methods=['POST'])
def submit_reference():
	if request.form.get('school_information') and request.form.get('school_information') is not None:
		form_contents = json.dumps(request.form)
		reference = ReferenceUpload(
			referee_name = request.form.get('referee_name'),
			student_name = request.form.get('student_name'),
			referee_position = request.form.get('referee_position'),
			suitability = request.form.get('suitability'),
			school_information = request.form.get('school_information'),
			form_contents = form_contents)
		db.session.add(reference)
		db.session.commit()
		flash ('Your reference was submitted successfully', 'success')
		return redirect (url_for('main.index'))
	abort (403)
	
# Access student references
@bp.route("/admin")
@login_required
def view_references():
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		references = db.session.query(ReferenceUpload).all()
		return render_template('references/view_references.html', title = 'View references', references = references)
	
# View completed student reference
@bp.route("/view/<reference_id>")
@login_required
def view_completed_reference(reference_id):
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		reference = ReferenceUpload.query.get(reference_id)
		form = StudentReferenceForm(obj=reference)
		return render_template('references/view_completed_reference.html', title = 'View completed reference', reference = reference, form = form)
	
# View version history of a reference
@bp.route("/view/project/<reference_id>")
@login_required
def view_reference_project(reference_id):
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		original_reference = ReferenceUpload.query.get(reference_id)
		form = StudentReferenceForm(obj=original_reference)
		reference_project_uploads = db.session.query(ReferenceVersionUpload, User).join(User, ReferenceVersionUpload.user_id==User.id).filter(ReferenceVersionUpload.original_reference_id==reference_id).all()
		reference_project_array = []
		for reference, user in reference_project_uploads:
			reference_dict = reference.__dict__ # Convert SQL Alchemy object into dictionary
			reference_dict['humanized_timestamp'] = arrow.get(reference_dict['timestamp'], tz.gettz('Asia/Hong_Kong')).humanize()
			reference_project_array.append([reference_dict, user])
		print (reference_project_array)
		return render_template('references/view_reference_project.html',
							   title = 'View reference project',
							   original_reference = original_reference,
							   reference_project_array = reference_project_array,
							   form = form,
							   reference_id = reference_id)
	

@bp.route('/download/version/<reference_version_id>')
@login_required
def download_reference_version(reference_version_id):
	try:
		reference_version = ReferenceVersionUpload.query.get(reference_version_id)
	except:
		flash ('This reference version could not be found.', 'error')
		return redirect(url_for('references.view_references'))
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		return app.references.models.download_reference_version(reference_version_id)
	abort (403)

@bp.route('/delete/<reference_version_id>')
@login_required
def delete_reference_version(reference_version_id):
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		try:
			reference_version = ReferenceVersionUpload.query.get(reference_version_id)
			original_reference_id = reference_version.original_reference_id
		except:
			flash ('This reference could not be found.', 'error')
			return redirect(url_for('references.view_references'))
		if app.references.models.delete_reference_version(reference_version_id):
			flash ('Successfully deleted the reference version', 'success')
			return redirect(url_for('references.view_reference_project', reference_id = original_reference_id))
		else:
			flash ('This reference could not be deleted.', 'error')
			return redirect(url_for('references.view_references'))
	abort (403)

# Submit reference version
@bp.route("/<original_reference_id>/version/upload", methods=['GET', 'POST'])
def upload_new_reference_version (original_reference_id):
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		form = EditedReferenceForm ()
		if form.validate_on_submit():
			app.references.models.new_reference_version_from_form(form, original_reference_id)
			flash('New reference version successfully added library!', 'success')
			return redirect(url_for('references.view_references'))
		return render_template('references/upload_reference_version.html', title='Upload reference version', form=form)
	abort (403)
	
# Delete a student reference
@bp.route("/delete/<reference_id>", methods=['GET', 'POST'])
@login_required
def delete_reference(reference_id):
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		reference = ReferenceUpload.query.get(reference_id)
		form = app.user.forms.ConfirmationForm()
		confirmation_message = 'Are you sure you want to delete ' + reference.student_name + "'s reference?"
		if form.validate_on_submit():
			ReferenceUpload.query.filter(ReferenceUpload.id==reference_id).delete()
			db.session.commit()
			flash('Reference deleted successfully.', 'success')
			return redirect(url_for('references.view_references'))
		return render_template('confirmation_form.html',
							   title='Delete reference',
							   confirmation_message = confirmation_message,
							   form=form)
	

@bp.route('/view/pdf')
def reference_pdf(data, reference):
	return render_template('references/pdf_reference.html', data = data, reference = reference)
	
@bp.route('/view/pdf/<reference_id>', methods=['GET', 'POST'])
@login_required
def view_statement_pdf(reference_id):
	try:
		reference = ReferenceUpload.query.get(reference_id)
	except:
		abort (404)
	form = StudentReferenceForm(obj=reference)
	del form.submit # Don't show submit button on printed form
	del form.referee_name
	del form.referee_position
	html = reference_pdf(data = form.data, reference = reference)
	return render_pdf (HTML(string=html))