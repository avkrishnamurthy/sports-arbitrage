from . import db
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import func
from sqlalchemy import UniqueConstraint

class Person(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    username = db.Column(db.Text, unique=True)
    password = db.Column(db.Text)
    first_name = db.Column(db.String(150))

class Games(db.Model):
    id = db.Column(db.String(32), primary_key=True, nullable=False)
    sport_key = db.Column(db.Text, nullable=False)
    sport_title = db.Column(db.Text, nullable=False)
    commence_time = db.Column(db.DateTime(timezone=True), nullable=False)
    completed = db.Column(db.Boolean, nullable=False)
    home_team = db.Column(db.Text, nullable=False)
    away_team = db.Column(db.Text, nullable=False)
    home_team_score = db.Column(db.Integer, nullable=True)
    away_team_score = db.Column(db.Integer, nullable=True)
    last_update = db.Column(db.DateTime(timezone=True), nullable=True)

class Odds(db.Model):
    __table_args__ = (UniqueConstraint('game_id', 'bookmaker_id', name='_game_bookmaker_uc'), )
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    game_id = db.Column(db.String, db.ForeignKey('games.id'), nullable=False)
    bookmaker_id = db.Column(db.Integer, db.ForeignKey('bookmakers.id'), nullable=False)
    game = db.relationship('Games', backref='odds_games')
    bookmaker = db.relationship('Bookmakers', backref='odds_bookmakers')
    sport_key = db.Column(db.Text, nullable=False)
    sport_title = db.Column(db.Text, nullable=False)
    home_team_odds = db.Column(db.Integer, nullable=True)  
    away_team_odds = db.Column(db.Integer, nullable=True)  
    draw_odds = db.Column(db.Integer, nullable=True)       
    last_update = db.Column(db.DateTime(timezone=True), nullable=True)

class Bookmakers(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    key = db.Column(db.Text, nullable=False)
    title = db.Column(db.Text, nullable=False)


class ArbitrageOpportunity(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)

    game_id = db.Column(db.String, db.ForeignKey('games.id'), nullable=False)
    game = db.relationship('Games', backref='arbitrage_opportunities')

    home_team_odds_id = db.Column(db.Integer, db.ForeignKey('odds.id'), nullable=False)
    away_team_odds_id = db.Column(db.Integer, db.ForeignKey('odds.id'), nullable=False)
    home_odds = db.relationship('Odds', foreign_keys=[home_team_odds_id], backref='arbitrage_home_opportunities')
    away_odds = db.relationship('Odds', foreign_keys=[away_team_odds_id], backref='arbitrage_away_opportunities')

    profit_percentage = db.Column(db.Float, nullable=False)
    time_found = db.Column(db.DateTime(timezone=True), default=func.now())


