from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

class Person(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    username = db.Column(db.Text, unique=True)
    password = db.Column(db.Text)
    first_name = db.Column(db.String(150))

class Games(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    sport_key = db.Column(db.Text, nullable=False)
    sport_title = db.Column(db.Text, nullable=False)
    commence_time = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    completed = db.Column(db.Boolean, nullable=False)
    home_team = db.Column(db.Text, nullable=False)
    away_team = db.Column(db.Text, nullable=False)
    home_team_score = db.Column(db.Integer, nullable=False)
    away_team_score = db.Column(db.Integer, nullable=False)
    last_update = db.Column(db.Text, nullable=False)

    @staticmethod
    def get_games_matching_sport(sport_key):
        rows = app.db.execute('''
                              SELECT * FROM games WHERE sport_key=:sport_key
                              ''',
                              sport_key=sport_key
                              )
        return [Games(*row) for row in rows]
    

    @staticmethod
    def add_games(id, sport_key, sport_title, commence_time, completed, home_team, away_team, home_team_score, away_team_score, last_update):
        rows = app.db.execute('''INSERT INTO games (id, sport_key, sport_title, commence_time, completed, home_team, away_team, home_team_score, away_team_score, last_update)
        VALUES (:id, :sport_key, :sport_title, :commence_time, :completed, :home_team, :away_team, :home_team_score, :away_team_score, :last_update)
        ON CONFLICT (id)
        DO UPDATE SET
            sport_key = EXCLUDED.sport_key,
            sport_title = EXCLUDED.sport_title,
            commence_time = EXCLUDED.commence_time,
            completed = EXCLUDED.completed,
            home_team = EXCLUDED.home_team,
            away_team = EXCLUDED.away_team,
            home_team_score = EXCLUDED.home_team_score,
            away_team_score = EXCLUDED.away_team_score,
            last_update = EXCLUDED.last_update
        WHERE games.last_update IS NULL OR games.last_update < EXCLUDED.last_update;''',
        id = id,
        sport_key=sport_key, 
        sport_title=sport_title,
        commence_time=commence_time, 
        completed=completed, 
        home_team=home_team, 
        away_team=away_team, 
        home_team_score=home_team_score, 
        away_team_score=away_team_score, 
        last_update=last_update
        )
        return [Games(*row) for row in rows]