from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from os import getenv
from flask_login import LoginManager
from sqlalchemy import text
from dotenv import load_dotenv
from flask_session import Session
from website.utils.utils import celery_init_app
from celery.schedules import crontab
db = SQLAlchemy()
sess = Session()
DB_NAME = "arbitrage_db"


def create_app():

    #Setting up flask app, database, sessions
    load_dotenv()
    app = Flask(__name__)
    app.config['SECRET_KEY'] = getenv('SECRET_KEY')
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = './.flask_session/'
    db_url = getenv('DATABASE_URL')
    db_url = db_url[:8]+'ql'+db_url[8:]
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    sess.init_app(app)
    db.init_app(app)

    #Registering components of our system
    from .auth.auth import auth
    from .home.home import home_
    from .lines.lines import lines_
    from .users.users import users_

    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(home_, url_prefix='/')
    app.register_blueprint(lines_, url_prefix='/')
    app.register_blueprint(users_, url_prefix='/')

    #Celery, Celery Beat, Redis configuration
    from .lines import the_odds_api
    #Configuration used to set redis as the message broker for our celery workers
    #Also setting the beat schedule that will orchestrate our celery workers to run every "x" minutes
    app.config.from_mapping(
        CELERY=dict(
            broker_url='redis://localhost:6379/0',
            result_backend='redis://localhost:6379/0',
            task_ignore_result=True,
            beat_schedule={
                "fetch-games-odds": {
                    "task": "website.lines.the_odds_api.insert_data",
                    "schedule": crontab(minute="*/5"),
                }
            },
        ),
    )

    celery_init_app(app)
    from .models import Person
    
    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    #Used for login_required decorator
    @login_manager.user_loader
    def load_user(id):
        return Person.query.get(int(id))

    return app

#Used for initial database, not needed anymore after postgres
# def create_database(app):
#     if not path.exists('website/' + DB_NAME):
#         db.create_all(app=app)
#         print('Created Database!')
