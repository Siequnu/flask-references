from flask import render_template, flash, redirect, url_for, request, current_app, send_file, abort, session
from flask_login import current_user
from flask_login import login_required

from app import db
import app.models
from app.models import ReferenceUpload, User

import json

from app.references import bp
from app.references.forms import ReferencePasswordForm, StudentReferenceForm


# Log-in gateway to access the references portal
@bp.route("/gateway", methods=['GET', 'POST'])
def references_login():
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		return redirect (url_for('references.view_references'))
	form = ReferencePasswordForm()
	return render_template('references/references_login.html', title = 'Log-in to references', form=form)
	

# Compose a reference
@bp.route("/compose", methods=['POST'])
def compose_reference():
	form = StudentReferenceForm()
	form.student_info.choices = [(user.id, user.username) for user in User.query.all()]
	if request.values.get('password') and request.values.get('password') in current_app.config['SIGNUP_CODES']:	
		return render_template('references/compose_reference.html', title = 'Submit student reference', form=form)
	abort (403)

# Submit reference
@bp.route("/submit", methods=['POST'])
def submit_reference():
	if request.form.get('school_information') and request.form.get('school_information') is not None:
		form_contents = json.dumps(request.form)
		reference = ReferenceUpload(
			referee_name = request.form.get('referee_name'),
			referee_position = request.form.get('referee_position'),
			suitability = request.form.get('suitability'),
			school_information = request.form.get('school_information'),
			form_contents = form_contents,
			student_id = request.form.get('student_info'))
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
		references = db.session.query(ReferenceUpload, User).join(User, ReferenceUpload.student_id == User.id).all()
		return render_template('references/view_references.html', title = 'View references', references = references)
	
# View completed student reference
@bp.route("/view/<reference_id>")
@login_required
def view_completed_reference(reference_id):
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		reference = ReferenceUpload.query.get(reference_id)
		user = User.query.get(reference.student_id)
		form = StudentReferenceForm(obj=reference)
		return render_template('references/view_completed_reference.html', title = 'View completed reference', form = form, user = user)
	
# Delete a student reference
@bp.route("/delete/<reference_id>", methods=['GET', 'POST'])
@login_required
def delete_reference(reference_id):
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		reference = ReferenceUpload.query.get(reference_id)
		user = User.query.get(reference.student_id)
		form = app.user.forms.ConfirmationForm()
		confirmation_message = 'Are you sure you want to delete ' + user.username + "'s reference?"
		if form.validate_on_submit():
			ReferenceUpload.query.filter(ReferenceUpload.id==reference_id).delete()
			db.session.commit()
			flash('Reference deleted successfully.', 'success')
			return redirect(url_for('references.view_references'))
		return render_template('confirmation_form.html',
							   title='Delete reference',
							   confirmation_message = confirmation_message,
							   form=form)