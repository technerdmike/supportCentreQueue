from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, SelectField, FormField, FieldList
from wtforms.validators import DataRequired, NumberRange, Length, InputRequired, EqualTo
from app.models import Subject

# making the subject dropdown list
subjects = Subject.query.order_by(Subject.name).all()
subjectList = [("", '- Subject-')]
for subj in subjects:
    if subj.code != 'N/A':
        subjectList.append((subj.code, subj.name))


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class SigninForm(FlaskForm):
    studentID = IntegerField('Student ID',
                             validators=[NumberRange(min=210000000, max=299999999, message='Please scan a valid Student ID card.')],
                             render_kw={'autofocus': True})
    submit = SubmitField('Submit')


class OnlineSigninForm(FlaskForm):
    studentID = IntegerField('Student ID',
                             validators=[DataRequired(), NumberRange(min=10000000, max=99999999, message='Please enter a valid Student ID card.')],
                             render_kw={'autofocus': True})
    subject = SelectField('Subject', choices=subjectList, validators=[DataRequired()])
    submit = SubmitField('Submit')


class ManualEntryForm(FlaskForm):
    studentID = IntegerField('Student ID',
                             validators=[NumberRange(min=10000000, max=99999999, message='Please enter a valid Student ID card.')],
                             render_kw={'autofocus': True})
    inPerson = SubmitField('In Person')
    online = SubmitField('Online')


class TeacherDash(FlaskForm):
    helped = SubmitField('HELPED')
    notHelped = SubmitField("CAN'T HELP")
    left = SubmitField("LEFT")
    noResponse = SubmitField("NO RESPONSE")
    timestamp = StringField('timestamp')
    studentID = StringField('studentID')
    location = StringField('location')
    selectedSubject = StringField('selected subject')

    subject = SelectField('Subject', choices=subjectList, default="")


class TeacherRange(FlaskForm):
    numberMenu = SelectField(validators=[DataRequired()], choices=[0, 1, 2, 3, 4, 5], coerce=int, default=0)


class TeachersAvailable(FlaskForm):
    subjectsAvailable = FieldList(FormField(TeacherRange), min_entries=1)
    submit = SubmitField('Apply')
    clearAll = SubmitField('Clear All')


class CenterOpen(FlaskForm):
    openButton = SubmitField('Open')
    closeButton = SubmitField('Closed')


class StudentReport(FlaskForm):
    studentID = IntegerField("Student ID", validators=[NumberRange(min=10000000, max=99999999, message='Please enter a valid Student ID Number.')], render_kw={'autofocus': True})
    submit = SubmitField('Search')


class EnrollStudent(FlaskForm):
    studentID = IntegerField("Student ID", validators=[NumberRange(min=10000000, max=99999999, message='Please enter a valid Student ID Number.')])
    firstName = StringField('First Name', validators=[DataRequired()])
    lastName = StringField('Last Name', validators=[DataRequired()])
    gradeLevel = SelectField("Grade", choices=[(10, '10'), (11, '11'), (12, '12')], validators=[DataRequired()], coerce=int)
    submit = SubmitField('Enroll Student')


class SiteSettings(FlaskForm):
    color1 = StringField('Primary Color', validators=[DataRequired(), Length(min=6, max=6)])
    color2 = StringField('Secondary Color', validators=[DataRequired(), Length(min=6, max=6)])
    colorBG = StringField('Background Color', validators=[DataRequired(), Length(min=6, max=6)])
    institutionName = StringField('Institution Name', validators=[DataRequired()])
    institutionAbbrev = StringField('Institution Abbreviation', validators=[DataRequired()])
    siteName = StringField('Site Name', validators=[DataRequired()])
    siteLogo = FileField("Site Logo", validators=[FileAllowed(['png'], "Please upload a png file.")])
    siteFavicon = FileField("Site Favicon", validators=[FileAllowed(['png'], "Please upload a png file.")])
    saveChanges = SubmitField('Save Changes')


class UploadCSV(FlaskForm):
    csvFile = FileField('Student Information file', validators=[FileAllowed(['csv', 'text'], "Please upload a csv file"), FileRequired()])
    submitUpload = SubmitField('Upload CSV')


class UploadPhotos(FlaskForm):
    zipFile = FileField('Student Photos archive', validators=[FileAllowed(['zip'], "Please upload a zip file"), FileRequired()])
    uploadZip = SubmitField('Upload Zip')


class PasswordUpdate(FlaskForm):
    currentPassword = PasswordField("Current Password", validators=[DataRequired()])
    newPassword = PasswordField("New Password", validators=[InputRequired(), EqualTo('confirmPassword', message='Passwords do not match')])
    confirmPassword = PasswordField("Repeat New Password")


class ChangeAdminPassword(FlaskForm):
    updatePassword = FormField(PasswordUpdate)
    submitAdminPassword = SubmitField("Change Password")


class ChangeTeacherPassword(FlaskForm):
    updatePassword = FormField(PasswordUpdate)
    submitTeacherPassword = SubmitField("Change Password")


class SetupPasswords(FlaskForm):
    newPassword = PasswordField("Password", validators=[InputRequired(), EqualTo('confirmPassword', message='Passwords do not match')])
    confirmPassword = PasswordField("Repeat Password")
    submitPassword = SubmitField("Set Password")
