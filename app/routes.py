"""
title: URL routes for the app
"""

import logging
from flask import render_template, flash, redirect, url_for, request, make_response
from app import app, db, nav
from app.forms import LoginForm, SigninForm, ManualEntryForm, TeacherDash, TeachersAvailable, CenterOpen, \
    StudentReport, OnlineSigninForm, EnrollStudent, SiteSettings, UploadCSV, UploadPhotos, ChangeAdminPassword, \
    ChangeTeacherPassword, SetupPasswords
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Queue, Student, Subject, History, Settings, getSettings
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from datetime import datetime
from pathlib import Path
from csv import reader, writer
from zipfile import ZipFile
from pytz import utc, timezone
from os import remove
from io import StringIO


logging.basicConfig(filename=Path(app.config['ROOT_PATH'], 'info.log'), level=logging.INFO, format=f'{datetime.utcnow()}, %(levelname)s, %(message)s')

nav.Bar('top', [
    nav.Item('Dashboard', 'teachers'),
    nav.Item('Enter Student', 'manualentry'),
    nav.Item('Student Lookup', 'studentReport'),
    nav.Item('Teacher Settings', 'teacherSettings'),
    nav.Item('Admin Settings', 'adminSettings'),
    nav.Item('Logout', 'logout')
])

@app.context_processor
def customSettings():
    return getSettings()


@app.route('/')
def public():
    if len(Settings.query.all()) > 0:
        teachers = Subject.query.order_by(Subject.name).all()
        teacherList = []
        for teacher in teachers:
            if teacher.teachers != 0:
                teacherList.append({"subject": teacher.name, "available": teacher.teachers})
        return render_template('index.html', queueLength=len(Queue.query.all()), teachers=teacherList)
    else:
        return redirect(url_for('setup1'))


@app.route('/queue')
@login_required
def queue():
    queueList = Queue.query.all()
    displayList = []
    for item in queueList:
        studentID = str(item.studentID)
        displayList.append(f"{studentID[0]} **** {studentID[-2:]}")
    teachers = Subject.query.order_by(Subject.name).all()
    teacherList = []
    for teacher in teachers:
        if teacher.teachers != 0:
            teacherList.append({"subject": teacher.name, "available": teacher.teachers})
    return render_template('queue.html', students=displayList, teachers=teacherList)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('teachers'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for('teachers')
        return redirect(next_page)
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logging.info(f"{request.remote_addr} - - [APP] {current_user.username} has logged out.")
        logout_user()
    return redirect(url_for('login'))


@app.route('/signin', methods=['GET', 'POST'])
@login_required
def signin():
    form = SigninForm()
    if form.validate_on_submit():
        if getSettings()['closed']:
            logging.warning(f"[APP] {form.studentID.data - 200000000} attempted to register but the Queue was closed.")
            flash('Unfortunately, you were not added to the Queue.', 'warning')
            redirect(url_for('signin'))
        else:
            studentID = form.studentID.data - 200000000
            if Student.query.filter_by(id=studentID).first() is None:
                logging.warning(f"[APP] {studentID} scanned their student ID card but no information found")
                flash('Student information not found, please talk to a Tutorials Teacher', 'danger')
            elif Queue.query.filter_by(studentID=studentID).first() is not None:
                logging.warning(f"[APP] {studentID} attempted to scan their student ID and enter the queue multiple times.")
                flash('You can only sign into the Queue one subject at a time.', 'warning')
            else:
                logging.info(f"[APP] {studentID} added successfully to the queue.")
                db.session.add(Queue(timestamp=datetime.utcnow(), studentID=studentID, location='in-person'))
                db.session.commit()
            return redirect(url_for('signin'))
    return render_template('signin.html', form=form)


@app.route('/online', methods=['GET', 'POST'])
def onlineSignin():
    form = OnlineSigninForm()
    if form.validate_on_submit():
        if getSettings()['closed']:
            logging.warning(f"{request.remote_addr} - - [APP] {form.studentID.data} attempted to register but the Queue was closed.")
            flash('Unfortunately, you were not added to the Queue.', 'warning')
        elif Student.query.get(form.studentID.data) is None:
            logging.critical(f"{request.remote_addr} - - [APP] {form.studentID.data} attempted to register online but the student ID is not in the database.")
            flash(f"Uh-Oh! Student ID {form.studentID.data} not found. Please contact your teacher.", 'danger')
        elif Queue.query.filter_by(studentID=form.studentID.data).first() is not None:
            logging.warning(f"{request.remote_addr} - - [APP] {form.studentID.data} attempted to scan their student ID and enter the queue multiple times.")
            flash('You can only sign into the Queue one subject at a time.', 'warning')
        else:
            db.session.add(Queue(timestamp=datetime.utcnow(), studentID=form.studentID.data, location='online', selectedSubject=form.subject.data))
            db.session.commit()
            logging.info(f"{request.remote_addr} - - [APP] {form.studentID.data} added successfully to the queue.")
            flash('You have been successfully added to the Queue. Head to Google Chat.', 'success')
            return redirect(url_for('public'))
        return redirect(url_for('onlineSignin'))
    return render_template('online_signin.html', form=form)


@app.route('/manualentry', methods=['GET', 'POST'])
@login_required
def manualentry():
    form = ManualEntryForm()
    if form.validate_on_submit():
        if form.inPerson.data:
            db.session.add(Queue(timestamp=datetime.utcnow(), studentID=form.studentID.data, location='in-person'))
        elif form.online.data:
            db.session.add(Queue(timestamp=datetime.utcnow(), studentID=form.studentID.data, location='online'))
        else:
            logging.critical(f"{request.remote_addr} - - [APP] A teacher attempted to manually enter {form.studentID.data}, but something went wrong.")
            flash("Something went wrong!", 'danger')
            redirect(url_for('teachers'))
        logging.info(f"{request.remote_addr} - - [APP] {form.studentID.data} added successfully by a teacher to the queue.")
        db.session.commit()
        return redirect(url_for('teachers'))
    return render_template('manualentry.html', form=form)


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def teachers():
    form = TeacherDash()
    if form.validate_on_submit():
        if form.selectedSubject.data != "None":
            form.subject.data = form.selectedSubject.data
        if form.left.data:
            db.session.add(History(studentID=form.studentID.data, timestamp=form.timestamp.data, subject="N/A", support="left", location=form.location.data))
            db.session.delete(Queue.query.filter_by(timestamp=form.timestamp.data).first())
            logging.info(f"{request.remote_addr} - - [APP] {form.studentID.data} LEFT before being helped.")
            db.session.commit()
        elif form.subject.data == "":
            flash("Please Select a subject for the student helped.", 'danger')
        else:
            if form.helped.data:
                result = "helped"
                logging.info(f"{request.remote_addr} - - [APP] {form.studentID.data} HELPED.")
            elif form.notHelped.data:
                result = "notHelped"
                logging.info(f"{request.remote_addr} - - [APP] {form.studentID.data} NOT HELPED.")
            elif form.noResponse.data:
                result = 'noResponse'
                logging.info(f"{request.remote_addr} - - [APP] {form.studentID.data} NO RESPONSE.")
            else:
                logging.critical(f"{request.remote_addr} - - [APP] Something went wrong with {form.studentID.data} response.")
                result = "error"
            db.session.add(History(studentID=form.studentID.data, timestamp=form.timestamp.data, subject=form.subject.data, support=result, location=form.location.data))
            db.session.delete(Queue.query.filter_by(timestamp=form.timestamp.data).first())
            db.session.commit()
        return redirect(url_for('teachers'))

    queueList = Queue.query.all()
    queueNames = []
    subjectQuery = Subject.query.filter(Subject.code != 'N/A').all()
    subjectDict = {}
    for subject in subjectQuery:
        subjectDict.update({subject.code: subject.name})

    for item in queueList:
        student = Student.query.get(item.studentID)
        if student is None:
            queueNames.append({'timestamp': item.timestamp, 'studentID': item.studentID, 'firstName': "Unknown Name",
                               'lastName': item.studentID, 'location': item.location, 'selectedSubjectName': None, 'selectedSubjectCode': None})
        else:
            queueNames.append({'timestamp': item.timestamp, 'studentID': student.id, 'firstName': student.firstName,
                               'lastName': student.lastName, 'location': item.location, 'selectedSubjectName': None, 'selectedSubjectCode': None})
        if item.selectedSubject is not None:
            queueNames[-1].update({'selectedSubjectName': subjectDict[item.selectedSubject]})
            queueNames[-1].update({'selectedSubjectCode': item.selectedSubject})
    return render_template('dashboard.html', form=form, students=queueNames)


@app.route('/teacher-settings', methods=['GET', 'POST'])
@login_required
def teacherSettings():
    subjects = Subject.query.order_by(Subject.name).all()

    centerForm = CenterOpen()
    form = TeachersAvailable(subjectsAvailable=subjects)

    if centerForm.validate_on_submit() or form.validate_on_submit():
        if form.submit.data:
            for i in range(len(form.data['subjectsAvailable'])):
                if subjects[i].teachers != form.data['subjectsAvailable'][i]['numberMenu']:
                    logging.info(f'{request.remote_addr} - - [APP] {subjects[i].name} teachers are changed to {form.data["subjectsAvailable"][i]["numberMenu"]}')
                    subjects[i].teachers = form.data['subjectsAvailable'][i]['numberMenu']
            db.session.commit()
            flash("Available Teachers numbers are updated!", "success")
        elif form.clearAll.data:
            for i in range(len(form.data['subjectsAvailable'])):
                subjects[i].teachers = 0
            logging.info(f'{request.remote_addr} - - [APP] All teachers are removed from the Queue')
            db.session.commit()
        else:
            if centerForm.openButton.data:
                logging.info(f'{request.remote_addr} - - [APP] The Queue is set to OPEN')
                Settings.query.get("closed").value = False
                db.session.commit()
            elif centerForm.closeButton.data:
                logging.info(f'{request.remote_addr} - - [APP] The Queue is set to CLOSED')
                Settings.query.get("closed").value = True
                db.session.commit()
            else:
                logging.critical(f"{request.remote_addr} - - [APP] Something went wrong with the Queue trying to open or close")
                flash("Uh-Oh! Something went wrong!", 'danger')
        return redirect(url_for('teacherSettings'))
    else:
        for i in range(len(form.subjectsAvailable)):
            form.subjectsAvailable[i].numberMenu.data = int(subjects[i].teachers)

    return render_template('teacher-settings.html', form=form, centerForm=centerForm, names=subjects)


@app.route('/admin-settings', methods=['GET', 'POST'])
@login_required
def adminSettings():
    if current_user.username != 'admin':
        logging.warning(f"{request.remote_addr} - - [APP] unauthorized attempted access to Admin Settings")
        flash('You do not have adequate permissions to view the page', 'warning')
        return redirect(url_for('teachers'))
    else:
        studentForm = EnrollStudent()
        siteSettings = SiteSettings()
        uploadCSVform = UploadCSV()
        uploadZipForm = UploadPhotos()
        changeAdminPass = ChangeAdminPassword()
        changeTeacherPass = ChangeTeacherPassword()

        if studentForm.submit.data and studentForm.validate_on_submit():
            # Enroll a new student
            if Student.query.get(studentForm.studentID.data) is None:
                db.session.add(Student(id=studentForm.studentID.data, firstName=studentForm.firstName.data, lastName=studentForm.lastName.data, gradeLevel=studentForm.gradeLevel.data))
                db.session.commit()
                logging.info(f'{request.remote_addr} - - [APP] Successfully added {studentForm.firstName.data} {studentForm.lastName.data} to the database.')
                flash(f'Successfully added {studentForm.firstName.data} {studentForm.lastName.data} to the database.', 'success')
            else:
                logging.info(f'{request.remote_addr} - - [APP] {studentForm.firstName.data} {studentForm.lastName.data} is already in the database.')
                flash(f'{studentForm.firstName.data} {studentForm.lastName.data} is already in the database.', 'danger')
            return redirect(url_for('adminSettings'))
        elif siteSettings.saveChanges.data and siteSettings.validate_on_submit():
            # Update Site Settings
            if Settings.query.get('siteName').value != siteSettings.siteName.data:
                Settings.query.get('siteName').value = siteSettings.siteName.data
                logging.info(f'{request.remote_addr} - - [APP] Site Name updated to {siteSettings.siteName.data}')
            if Settings.query.get('institutionName').value != siteSettings.institutionName.data:
                Settings.query.get('institutionName').value = siteSettings.institutionName.data
                logging.info(f'{request.remote_addr} - - [APP] Institution Name updated to {siteSettings.institutionName.data}')
            if Settings.query.get('institutionAbbrev').value != siteSettings.institutionAbbrev.data:
                Settings.query.get('institutionAbbrev').value = siteSettings.institutionAbbrev.data
                logging.info(f'{request.remote_addr} - - [APP] Institution Abbreviation updated to {siteSettings.institutionAbbrev.data}')
            if Settings.query.get('color1').value != str(siteSettings.color1.data).upper():
                Settings.query.get('color1').value = str(siteSettings.color1.data).upper()
                logging.info(f'{request.remote_addr} - - [APP] Custom Color 1 changed to {str(siteSettings.color1.data).upper()}')
            if Settings.query.get('color2').value != str(siteSettings.color2.data).upper():
                Settings.query.get('color2').value = str(siteSettings.color2.data).upper()
                logging.info(f'{request.remote_addr} - - [APP] Custom Color 2 changed to {str(siteSettings.color2.data).upper()}')
            if Settings.query.get('colorBG').value != str(siteSettings.colorBG.data).upper():
                Settings.query.get('colorBG').value = str(siteSettings.colorBG.data).upper()
                logging.info(f'{request.remote_addr} - - [APP] Custom Color Background changed to {str(siteSettings.colorBG.data).upper()}')
            db.session.commit()

            # Update Site Logo
            if siteSettings.siteLogo.data is not None:
                logoFile = siteSettings.siteLogo.data
                filename = secure_filename('logo.png')
                filePath = Path(app.config['STATIC_FOLDER'], 'media', filename)
                logoFile.save(filePath)
                logging.info(f'{request.remote_addr} - - [APP] Logo image file updated')

            # Update Site Favicon
            if siteSettings.siteFavicon.data is not None:
                faviconFile = siteSettings.siteLogo.data
                filename = secure_filename('favicon.png')
                filePath = Path(app.config['STATIC_FOLDER'], 'media', filename)
                faviconFile.save(filePath)
                logging.info(f'{request.remote_addr} - - [APP] Favicon image file updated')

            return redirect(url_for('adminSettings'))
        elif uploadCSVform.submitUpload.data and uploadCSVform.validate_on_submit():
            # Upload Student information file
            newFile = uploadCSVform.csvFile.data
            filename = secure_filename(newFile.filename)
            filePath = Path(app.config['STATIC_FOLDER'], filename)
            newFile.save(filePath)

            csvFile = open(filePath, newline='')
            fileReader = reader(csvFile)
            newStudent = 0
            updateStudent = 0
            for row in fileReader:
                if len(row) > 0:
                    student = Student.query.get(row[0])
                    if student is None:
                        db.session.add(Student(id=row[0], firstName=row[1], lastName=row[2], gradeLevel=row[3]))
                        newStudent += 1
                    else:
                        doUpdate = False
                        if student.firstName != row[1]:
                            student.firstName = row[1]
                            doUpdate = True
                        if student.lastName != row[2]:
                            student.lastName = row[2]
                            doUpdate = True
                        if student.gradeLevel != int(row[3]):
                            student.gradeLevel = row[3]
                            doUpdate = True
                        if doUpdate:
                            updateStudent += 1
            db.session.commit()
            csvFile.close()
            remove(filePath)
            if newStudent == 0 and updateStudent == 0:
                logging.warning(f"{request.remote_addr} - - [APP] Student Information file uploaded but no changed detected")
                flash("No new changes detected", 'warning')
            else:
                logging.info(f"{request.remote_addr} - - [APP] Student Information file uploaded with changes")
                flash(f"{newStudent} new students added to and {updateStudent} students updated in database.", 'success')
            return redirect(url_for('adminSettings'))
        elif uploadZipForm.uploadZip.data and uploadZipForm.validate_on_submit():
            #Upload and extract student images from zip file.
            newFile = uploadZipForm.zipFile.data
            filename = secure_filename(newFile.filename)
            filePath = Path(app.config['STATIC_FOLDER'], filename)
            newFile.save(filePath)

            zipFile = ZipFile(filePath, 'r')
            zipFile.extractall(Path(app.config['STATIC_FOLDER'], 'students'))
            zipFile.close()
            remove(filePath)
            logging.info(f"{request.remote_addr} - - [APP] Successfully updated student photos")
            flash('Successfully updated student photos', 'success')
            return redirect(url_for('adminSettings'))
        elif changeAdminPass.submitAdminPassword.data and changeAdminPass.validate_on_submit():
            # Change 'admin' user password
            adminUser = User.query.filter_by(username="admin").first()
            if adminUser.check_password(changeAdminPass.updatePassword.currentPassword.data):
                adminUser.set_password(changeAdminPass.updatePassword.newPassword.data)
                db.session.commit()
                logout_user()
                logging.info(f"{request.remote_addr} - - [APP] Admin password successfully changed")
                flash("Successfully updated admin password. Please login again.", 'success')
            else:
                logging.warning(f"{request.remote_addr} - - [APP] Admin password not changed")
                flash("Admin Current Password is incorrect", 'danger')
            return redirect(url_for('adminSettings'))
        elif changeTeacherPass.submitTeacherPassword.data and changeTeacherPass.validate_on_submit():
            # Change 'teachers' user password
            teacherUser = User.query.filter_by(username="teachers").first()
            if teacherUser.check_password(changeTeacherPass.updatePassword.currentPassword.data):
                teacherUser.set_password(changeTeacherPass.updatePassword.newPassword.data)
                db.session.commit()
                logging.info(f"{request.remote_addr} - - [APP] Teachers password successfully changed")
                flash("Successfully updated teachers password.", 'success')
            else:
                logging.warning(f"{request.remote_addr} - - [APP] Teachers password not changed")
                flash("Teachers Current Password is incorrect", 'danger')
            return redirect(url_for('adminSettings'))
        return render_template('admin-settings.html', enrollStudent=studentForm, siteSettings=siteSettings,
                               uploadCSV=uploadCSVform, uploadZip=uploadZipForm, changeAdminPass=changeAdminPass,
                               changeTeacherPass=changeTeacherPass)


@app.route('/student-report', methods=['GET', 'POST'])
@login_required
def studentReport():
    form = StudentReport()
    results = []
    supportName = {'helped': 'HELPED', 'notHelped': 'NOT HELPED', 'left': 'LEFT', 'noResponse': 'NO RESPONSE'}

    if form.validate_on_submit():
        currentStudent = Student.query.get(form.studentID.data)
        logging.info(f"{request.remote_addr} - - [APP] A student report was generated for {form.studentID.data}")
        if currentStudent is None:
            studentName = {'first': form.studentID.data, 'last': ""}
        else:
            studentName = {'first': currentStudent.firstName, 'last': currentStudent.lastName}
        studentHistory = db.session.query(Subject, History).join(History, Subject.code == History.subject).filter_by(studentID=form.studentID.data).order_by(History.id.desc()).all()
        if len(studentHistory) == 0:
            flash(f'No records of {studentName["first"]} {studentName["last"]} attending tutorials', 'info')
            return redirect(url_for('studentReport'))
        else:
            for record in studentHistory:
                results.append({'timestamp': utc.localize(datetime.strptime(record.History.timestamp, '%Y-%m-%d %H:%M:%S.%f')).astimezone(timezone('America/Edmonton')).strftime('%Y-%m-%d %I:%M:%S %p'),
                                'location': record.History.location, 'subject': record.Subject.name, 'support': supportName[record.History.support]})
            return render_template('student-reports.html', form=form, results=results, studentName=studentName)

    return render_template('student-reports.html', form=form)


@app.route('/students/<int:studentID>')
@login_required
def studentInfo(studentID):
    student = Student.query.get(studentID)
    if student is not None:
        if Path('app', 'static', 'students', f'{student.id}.jpg').is_file():
            return render_template('student-info.html', student=student)
        else:
            logging.warning(f"{request.remote_addr} - - [APP] No image available for {student.firstName} {student.lastName}")
            flash(f'No image available for {student.firstName} {student.lastName}.', 'info')
    else:
        logging.warning(f'{request.remote_addr} - - [APP] No image available for student with ID {studentID}.')
        flash(f'{request.remote_addr} - - No image available for student with ID {studentID}.', 'info')
    return redirect(url_for('teachers'))


@app.route('/setup-1', methods=['GET', 'POST'])
def setup1():
    if len(Settings.query.all()) == 0:
        form = SetupPasswords()

        if form.validate_on_submit():
            db.session.add(User(username='admin', password_hash=generate_password_hash(form.newPassword.data)))
            db.session.commit()
            return redirect(url_for('setup2'))

        return render_template('setup1.html', form=form)
    else:
        return redirect(url_for('public'))


@app.route('/setup-2', methods=['GET', 'POST'])
def setup2():
    if len(Settings.query.all()) == 0:
        form = SetupPasswords()

        if form.validate_on_submit():
            db.session.add(User(username='teachers', password_hash=generate_password_hash(form.newPassword.data)))
            db.session.add(Settings(name='color1', value='007bff'))
            db.session.add(Settings(name='color2', value='6c757d'))
            db.session.add(Settings(name='colorBG', value='c0c0c0'))
            db.session.add(Settings(name='institutionName', value='Institution Name'))
            db.session.add(Settings(name='institutionAbbrev', value='Institution Abbreviation'))
            db.session.add(Settings(name='siteName', value='Site Name'))
            db.session.add(Settings(name='closed', value='1'))
            db.session.add(Subject(name="Not Applicable", code="N/A", teachers='0'))
            db.session.add(Subject(name="English", code="ELA", teachers='0'))
            db.session.add(Subject(name="Social Studies", code="SST", teachers='0'))
            db.session.add(Subject(name="Math", code="MAT", teachers='0'))
            db.session.add(Subject(name="Science", code="SCN", teachers='0'))
            db.session.add(Subject(name="Languages", code="LNG", teachers='0'))
            db.session.commit()
            return redirect(url_for('adminSettings'))
    else:
        return redirect(url_for('public'))

    return render_template('setup2.html', form=form)


@app.route('/csv-example')
def getCSV():
    row = StringIO()
    csvWriter = writer(row)
    csvWriter.writerow([12345678, 'firstName', 'lastName', 10])
    output = make_response(row.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=example.csv"
    output.headers["Content-type"] = "text/csv"
    return output
