from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_navigation import Navigation
from flask_minify import minify
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.config.from_object(Config)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login'
nav = Navigation(app)
minify(app=app, html=True, js=False, cssless=True)

from app import routes, models, errors
