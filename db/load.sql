INSERT INTO games (
    id, 
    sport_key, 
    sport_title, 
    commence_time, 
    completed, 
    home_team, 
    away_team, 
    home_team_score, 
    away_team_score, 
    last_update
)
VALUES (
    'e588f3f61ef44746b18980633acsb312',
    'americanfootball_nfl',
    'NFL',
    CURRENT_TIMESTAMP,
    FALSE,
    'Washington 89ers',
    'Chicago Jaguars',
    NULL,
    NULL,
    CURRENT_TIMESTAMP
);

INSERT INTO odds (
    game_id, 
    bookmaker_id, 
    sport_key, 
    sport_title, 
    home_team_odds, 
    away_team_odds, 
    draw_odds, 
    last_update
)
VALUES (
    'e588f3f61ef44746b18980633acsb312',
    1,
    'americanfootball_nfl',
    'NFL',
    -180,
    110,
    NULL,
    CURRENT_TIMESTAMP
);

INSERT INTO odds (
    game_id, 
    bookmaker_id, 
    sport_key, 
    sport_title, 
    home_team_odds, 
    away_team_odds, 
    draw_odds, 
    last_update
)
VALUES (
    'e588f3f61ef44746b18980633acsb312',
    2,
    'americanfootball_nfl',
    'NFL',
    -400,
    700,
    NULL,
    CURRENT_TIMESTAMP
);
