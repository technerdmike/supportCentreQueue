import os
from pathlib import Path

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'thispasswordneedschanging'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STATIC_FOLDER = str(Path(Path.cwd(), 'app', 'static'))
    ROOT_PATH = str(Path.cwd())
