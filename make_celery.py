from website import create_app

#File used to configure celery workers
flask_app = create_app()
celery_app = flask_app.extensions["celery"]