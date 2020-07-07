from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
# from werkzeug.utils import secure_filename
# from flask_uploads import *


db = SQLAlchemy()

def create_app():


    app = Flask(__name__)

    # text_files = UploadSet('text_files', TEXT)

    # ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

    app.config['SECRET_KEY'] = 'thisismysecretkeydontstealit' # used for sessions. needed for authentiation cookies
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
    # app.config['UPLOADED_FILES_DEST'] = 'static/uploads'

    app.config['UPLOAD_FOLDER'] = 'app/'

    # configure_uploads(app, text_files)

    db.init_app(app)

    # flask_login creates a login when the user is logged in and in the cookie we have the user_id
    # flask_login uses the user_loader to know which user session is currently active

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # import bluprint

    from .auth import auth as auth_blueprint # paths for login, sign up, log out
    app.register_blueprint(auth_blueprint)

    from .main import main as main_blueprint # index and profile
    app.register_blueprint(main_blueprint)


    return app
