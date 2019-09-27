from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, SelectMultipleField, DateField, BooleanField, FormField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from flask_wtf.file import FileField, FileRequired
from app.models import Turma
	
	
class StudentReferenceForm(FlaskForm):
	referee_name = StringField('Your name:', validators=[DataRequired()])
	student_name = StringField('Student name:', validators=[DataRequired()])
	referee_position = StringField('What is your relation to the student?', validators=[DataRequired()])
	school_information = TextAreaField('School information:', validators=[DataRequired()])
	suitability = TextAreaField('Student suitability:', validators=[DataRequired()])
	submit = SubmitField('Submit reference')
	
class ReferencePasswordForm(FlaskForm):
	password = StringField('Log-in code:', validators=[DataRequired()])
	submit = SubmitField('Submit a reference...')
	
class EditedReferenceForm(FlaskForm):
	reference_upload_file= FileField(label='File:')
	description = StringField('Notes:')
	submit = SubmitField('Upload new reference')
