"""
Transform the data from the Statsbomb to the same format as the one in Kaggle - see Readme.md
"""

import pandas as pd
import numpy as np
import re
from general_func import computeElimination

def isKeeperChanged(subs, game_id):
    """
    In: Dataframe with the substitutions of a game and the game_id
    Out: 1 if the goalkeeper was subbed, otherwise 0"""

    # No subs means no keeper changes
    if len(subs) == 0:
        return 0

    # Get the data for the lineups
    mypath_lineup = '../data/lineups_api/lineup_' + game_id + '.json'
    game_lineup = pd.read_json(mypath_lineup)

    players = []
    # Substitutes of home and away teams
    players = game_lineup['substitutes'].values[0].copy()
    players.extend(game_lineup['substitutes'].values[1])

    # Append one column for each team_id and put them together in bench
    teams = [game_lineup['team'].apply(pd.Series).loc[0,'id']]*len(game_lineup['substitutes'].values[0])
    teams.extend([game_lineup['team'].apply(pd.Series).loc[1,'id']]*len(game_lineup['substitutes'].values[1]))
    bench = pd.DataFrame({'Player': players, 'Team_id': teams})
    bench[['Player_id', 'Player_name', 'Player_pos']] = bench['Player'].apply(pd.Series)['player'].apply(pd.Series)[['id', 'name', 'pos']]
    bench = bench.drop('Player', axis=1)

    # Look for the players in the bench that are goalkeepers
    bench_keepers = bench[bench['Player_pos'] == 'G']

    # Check if any of the subbed players is one of the benched goalkeepers
    if any(subs['assist'].apply(pd.Series)['name'].isin(bench_keepers)):
        return 1
    else:
        return 0

def getPenaltiesAPI(game_id, pen_type, games, teams_stadiums):
    """
    Method that returns the penalties for a game_id
    In: id of the game, how the penalties are saved, dataframe with all the games, dataframe with all stadiums
    Out: Penalties for the game_id
    """
    # Retrieving the information for the game
    mypath_game = '../data/games_api/' + game_id + '.json'
    game_events = pd.read_json(mypath_game)

    # Formating data
    game_events[['elapsed', 'Penalty_Number']] = game_events['time'].apply(pd.Series).fillna(0)
    game_events.drop('time', axis = 1, inplace=True)

    # Adding team_id and team_name
    game_events[['Team_id', 'Team']] = game_events['team'].apply(pd.Series)[['id', 'name']]
    game_events[['Zone', 'Foot', 'Keeper']] = [[0, '0', '0'] for x in range(len(game_events))]
    game_events['Keeper_changed'] = np.zeros(len(game_events))


    for i in game_events['Team_id'].unique():
        game_events.loc[game_events['Team_id'] == i, 'Keeper_changed'] = [
            isKeeperChanged(game_events[(game_events['type'] == 'subst') & (game_events['elapsed'] >= 110)],
            game_events['game_id'].values[0])] * len(game_events[game_events['Team_id'] == i])
    
    # Dictionary for formatting
    _dict = {'Missed Penalty': 0, 'Penalty': 1}

    # Filtering for penalties in the penalty shootouts and collecting the data
    game_events = game_events[game_events['elapsed'] == 120]
    if pen_type == 1:
        game_events = game_events[(game_events['type'] == 'Goal') & (game_events['comments'] == 'Penalty Shootout')].drop(['player', 'assist', 'comments', 'elapsed', 'type', 'team'], axis = 1)
    elif pen_type == 2:
        game_events = game_events[(game_events['type'] == 'Goal') & (game_events['detail'].str.contains('Penalty'))].drop(['player', 'assist', 'comments', 'elapsed', 'type', 'team'], axis = 1)
    else:
        game_events = game_events[(game_events['type'] == 'Goal') & (game_events['comments'] == 'Penalty Shootout')].drop(['player', 'assist', 'comments', 'elapsed', 'type', 'team'], axis = 1)
    
    # Adding other columns to get the same format
    game_events['Penalty_Number'] = range(1, len(game_events)+1)
    game_events = game_events.replace(to_replace={'detail': _dict}).rename({'detail': 'Goal', 'game_id': 'Game_id'}, axis = 1)
    game_events['Elimination'] = computeElimination(game_events)
    game_events['OnTarget'] = np.zeros(len(game_events)).astype(int)
    game_events.loc[game_events['Goal'] == 1, 'OnTarget'] = np.ones(len(game_events.loc[game_events['Goal'] == 1, :])).astype(int)
    
    # Setting up properly hometeam
    game_events['Home'] = np.zeros(len(game_events)).astype(int)
    home_team = games.loc[games['game_filename'] == game_events['Game_id'].head(1).values[0], 'teams'].apply(pd.Series)['home'].values[0]['id']
    if (teams_stadiums.loc[teams_stadiums['Team_id'] == home_team, 'Stadium_name'].head(1).values[0] == games.loc[games['game_filename'] == game_events['Game_id'].head(1).values[0], 'Stadium_name'].values[0]):
        game_events.loc[game_events['Team_id'] == home_team, 'Home'] = np.ones(len(game_events[game_events['Team_id'] == home_team])).astype(int)
    
    return game_events[['Game_id', 'Team', 'Zone', 'Foot', 'Keeper', 'OnTarget', 'Goal', 'Penalty_Number', 'Elimination', 'Home', 'Keeper_changed']].sort_values(by='Penalty_Number', ascending = True)

def getDataAPI():
    # Data for games and where the data is located
    where = pd.read_excel('../data/where_data_api.xlsx')
    games = pd.read_json('../data/api_football_games.json')
    games['game_filename'] =  games['season_id'] + '_' + games['fixture'].apply(pd.Series)['id'].astype(str)
    games[['Stadium_id', 'Stadium_name']] = games['fixture'].apply(pd.Series)['venue'].apply(pd.Series)[['id', 'name']]

    # Data for stadiums
    teams_stadiums = pd.read_json('../data/api_football_stadiums.json')
    teams_stadiums[['Team_id', 'Team_name']] = teams_stadiums['team'].apply(pd.Series)[['id', 'name']]
    teams_stadiums[['Stadium_id', 'Stadium_name']] = teams_stadiums['venue'].apply(pd.Series)[['id', 'name']]
    teams_stadiums.drop(['team', 'venue'], axis = 1, inplace=True)

    all_pens = pd.DataFrame()

    # Collecting data for all the 
    for i in games['game_filename'].values:
        league, season, _ = re.split(r'(\d{4})$', games.loc[games['game_filename'] == i, 'season_id'].values[0])
        pen_type = where.loc[where['comp_name'] == league, int(season)].values[0]
        new_pens = getPenaltiesAPI(i, pen_type, games, teams_stadiums)
        all_pens = pd.concat([all_pens, new_pens], axis=0)
        all_pens.index = range(len(all_pens))
    return all_pens

