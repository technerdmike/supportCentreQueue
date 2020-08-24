from app import app, db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from pathlib import Path


class User(UserMixin, db.Model):
    __tablename__ = 'User'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable = False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Queue(db.Model):
    __tablename__ = "Queue"

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    timestamp = db.Column(db.String(32), index=True, unique=True, nullable=False)
    studentID = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(32), nullable=False)
    selectedSubject = db.Column(db.String(32))


class Student(db.Model):
    __tablename__ = 'Student'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    firstName = db.Column(db.String(64), nullable=False)
    lastName = db.Column(db.String(64), nullable=False)
    gradeLevel = db.Column(db.Integer, nullable=False)


class Subject(db.Model):
    __tablename__ = 'Subject'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(32), nullable=False)
    code = db.Column(db.String(8), nullable=False)
    teachers = db.Column(db.Integer, nullable=False)


class History(db.Model):
    __tablename__ = "History"

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    studentID = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.String(32), index=True, unique=True, nullable=False)
    subject = db.Column(db.String(8), index=True, nullable=False)
    support = db.Column(db.String(32), index=True, nullable=False)
    location = db.Column(db.String(32), nullable=False)


class Settings(db.Model):
    __tablename__ = 'Settings'

    name = db.Column(db.String(128), primary_key=True, nullable=False)
    value = db.Column(db.String(128))


def getSettings():
    settingsQuery = Settings.query.all()
    customSettings = dict()
    if len(settingsQuery) > 0:
        for item in settingsQuery:
            customSettings.update({f'{item.name}': f'{item.value}'})
        if customSettings['closed'] == '1':
            customSettings.update({'closed': True})
        else:
            customSettings.update({'closed': False})
    return customSettings


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


if not Path(app.instance_path, 'app.db').is_file():
    db.create_all()
