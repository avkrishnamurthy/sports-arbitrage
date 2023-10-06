from website.models import Odds, ArbitrageOpportunity, Games, Bookmakers
from website import db


def convert_odds_to_implied(us_odds):
    if us_odds < 0: return abs(us_odds) / (abs(us_odds) + 100)
    return 100 / (us_odds + 100)

def calculate_arbitrage(odds_1, odds_2):
    return (convert_odds_to_implied(odds_1)+convert_odds_to_implied(odds_2))

def get_odds():
    odds_list = []
    games = db.session.query(Games).all()
    for game in games:
        all_lines = game.odds_games
        if len(all_lines) > 0: odds_list.append(all_lines)
    return odds_list
        
        #home away ids, profit percentage
def find_arbitrage(odds_list):
    if not odds_list: return None
    arbitrage_opps = []
    for odds_game in odds_list:
        if not odds_game: continue
        for odds1, odds2 in zip(odds_game, odds_game[1:]):
            if not odds1 or not odds2: continue

            #book 1 home, book 2 away
            arbitrage_value = calculate_arbitrage(odds1.home_team_odds, odds2.away_team_odds)
            if arbitrage_value < 1:
                arbitrage_opp = ArbitrageOpportunity(game_id=odds1.game_id, home_team_odds_id=odds1.id, away_team_odds_id=odds2.id, profit_percentage=arbitrage_value-1)
                arbitrage_opps.append(arbitrage_opp)

            #book 1 away, book 2 home
            arbitrage_value = calculate_arbitrage(odds2.home_team_odds, odds1.away_team_odds)
            if arbitrage_value < 1:
                # print(arbitrage_value)
                arbitrage_opp = ArbitrageOpportunity(game_id=odds1.game_id, home_team_odds_id=odds2.id, away_team_odds_id=odds1.id, profit_percentage=1-arbitrage_value)
                arbitrage_opps.append(arbitrage_opp)
    return arbitrage_opps

def insert_arbitrage():
    odds_list = get_odds()
    arbitrage_opps = find_arbitrage(odds_list)
    db.session.add_all(arbitrage_opps)
    db.session.commit()

