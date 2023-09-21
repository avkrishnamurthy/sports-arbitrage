from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from website import db
import requests
import json
import os
from dotenv import load_dotenv



lines_ = Blueprint('lines', __name__, template_folder='templates', static_url_path='lines/', static_folder='static')

load_dotenv()

API_KEY = os.getenv("API_KEY")
MARKETS = "h2h"
TOGGLE_LIVE = True
REGIONS = "us"
ODDS_FORMAT = "american"
BOOKMAKERS = "fanduel,draftkings,betmgm,foxbet,barstool,pointsbetus,circasports,wynnbet,unibet_us,betus,twinspires,betonlineag"
SPORTS = [
    "basketball_nba",
    "americanfootball_nfl",
    "icehockey_nhl",
    "americanfootball_ncaaf",
    "baseball_mlb",
]


@lines_.route('/lines')
@login_required
def lines():
    return render_template("lines.html", user=current_user)


@lines_.route('/lines/sports')
@login_required
def sports():
    request_url = f"https://api.the-odds-api.com/v4/sports?apiKey={API_KEY}"
    data = requests.get(request_url)
    data = data.json()
    return data

@lines_.route('/lines/odds')
@login_required
def upcoming_odds():

    request_url = "https://api.the-odds-api.com/v4/sports/{sport}/odds/?regions={regions}&oddsFormat={odds_format}&markets={markets}&apiKey={api_key}".format(
        sport="upcoming",
        api_key=API_KEY,
        markets=MARKETS,
        regions=REGIONS,
        odds_format=ODDS_FORMAT,
    )
    data = requests.get(request_url)
    return data.json()