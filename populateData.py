import psycopg2
import uuid
from random import choice, uniform

# Initialize connection to SQL database
conn = psycopg2.connect(
    dbname="your_dbname",
    user="your_user",
    password="your_password",
    host="your_host"
)
cursor = conn.cursor()

# Function to generate random team names
def generate_team_names():
    teams = ['Washington 89ers', 'Chicago Jaguars', 'New York Knights', 'Los Angeles Suns', "Boston Blue Devils", "Las Vegas Tar Heels"]
    home_team = choice(teams)
    return home_team, choice([team for team in teams if team not in [home_team]])

# Function to generate mock arbitrage odds
def generate_arbitrage_odds():
    # Generate a random odds for bookmaker 1
    odds_bookmaker1_home = round(uniform(1.5, 3.0), 2) # For home team
    odds_bookmaker1_away = round(uniform(1.5, 3.0), 2) # For away team

    # Calculate odds for bookmaker 2 that ensure an arbitrage opportunity
    arb_condition = 1.01 # A bit over 1 to ensure arbitrage
    odds_bookmaker2_home = round(1 / (arb_condition - (1 / odds_bookmaker1_away)), 2)
    odds_bookmaker2_away = round(1 / (arb_condition - (1 / odds_bookmaker1_home)), 2)

    return odds_bookmaker1_home, odds_bookmaker1_away, odds_bookmaker2_home, odds_bookmaker2_away

# Function to insert data into the SQL database
def insert_data(game_id, sport_key, sport_title, home_team, away_team, odds):
    # Insert game data
    cursor.execute("""
    INSERT INTO games (id, sport_key, sport_title, commence_time, completed, home_team, away_team, last_update)
    VALUES (%s, %s, %s, CURRENT_TIMESTAMP, FALSE, %s, %s, CURRENT_TIMESTAMP)
    """, (game_id, sport_key, sport_title, home_team, away_team))

    # Insert odds for bookmaker 1
    cursor.execute("""
    INSERT INTO odds (game_id, bookmaker_id, sport_key, sport_title, home_team_odds, away_team_odds, last_update)
    VALUES (%s, 1, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    """, (game_id, sport_key, sport_title, odds[0], odds[1]))

    # Insert odds for bookmaker 2
    cursor.execute("""
    INSERT INTO odds (game_id, bookmaker_id, sport_key, sport_title, home_team_odds, away_team_odds, last_update)
    VALUES (%s, 2, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    """, (game_id, sport_key, sport_title, odds[2], odds[3]))

    conn.commit()

# Main function to handle the data generation and insertion
def main():
    sport_key = 'americanfootball_nfl'
    sport_title = 'NFL'
    for _ in range(10): # Generate 10 mock games
        game_id = str(uuid.uuid4())
        home_team, away_team = generate_team_names()
        odds = generate_arbitrage_odds()
        insert_data(game_id, sport_key, sport_title, home_team, away_team, odds)

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
