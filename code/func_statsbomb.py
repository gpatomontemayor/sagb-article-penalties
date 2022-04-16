"""
Transform the data from Statsbomb to the same format as the one in kaggle - see Readme.md
"""

import pandas as pd
import numpy as np
from general_func import *

def compid_str(comp_id, season):
    """
    In: comp_id as a number
    Out: competition name, for the index
    """
    if comp_id == '55':
        return 'euro2020'
    elif comp_id == '16':
        if season == '27':
            return 'ucl2016'
        elif season == '23':
            return 'ucl2012'
        elif season == '37':
            return 'ucl2005'

def get_international(df, comp_id, season):
    """
    In: dataframe with general data of games of the given competition id and season
    Out: dataframe with all the penalty shootouts of the competition id and season
    """
    comp_id = compid_str(comp_id, season)

    # Retrieveing all the games that ended up in a penalty shootout
    games = pd.concat([df[['match_id', 'match_date', 'home_score', 'away_score']], 
                       df['home_team'].apply(pd.Series)[['home_team_id', 'home_team_name']], 
                       df['away_team'].apply(pd.Series)[['away_team_id', 'away_team_name']],
                       df['competition_stage'].apply(pd.Series).rename({'id': 'comp_id', 'name': 'comp_name'}, axis = 1),
                       df['stadium'].apply(pd.Series)['country'].apply(pd.Series)[['name']].rename({'name': 'country'}, axis = 1)],
          axis = 1)
    games = games[(games['comp_name'] != "Group Stage") & (games['home_score'] == games['away_score'])]

    ps = pd.DataFrame()
    for i in games['match_id'].astype(str):
        # For this data, if the team played in the country it is a home team (since we only have Euro2020 and UCL Finals)
        stadium = games.loc[games['match_id'].astype(str) == i, 'country'].values[0]

        # Reading the data for each match
        match_data = '../data/open-data-master/data/events/'+ i + '.json'
        match = pd.read_json(match_data)

        # To later check if the goalkeeper was subbed or not
        player_pos = match[(match['period'] == 4) & (match['type'] == {'id': 19, 'name': 'Substitution'})]['position'].apply(pd.Series)
        
        # Focusing only in the penalties of the game
        match = pd.concat([match[match['period'] == 5]['type'].apply(pd.Series),
                match[match['period'] == 5]['possession_team'].apply(pd.Series)[['name']].rename({'name': 'Team'}, axis = 1),
                match[match['period'] == 5]['shot'].apply(pd.Series)],
               axis = 1)
        match = match[match['name'] == 'Shot']

        match = match[['Team', 'body_part', 'end_location', 'outcome']]

        match['Game_id'] = [comp_id + '_' + i] * len(match)

        match['Zone'] = match['end_location'].apply(get_zone)

        match['Foot'] = match['body_part'].apply(pd.Series)['id'].map({40: 'R', 38: 'L'})

        match['OnTarget'] = match['outcome'].apply(pd.Series)['id'].map({97: 1, 100: 1, 116: 0, 99: 0, 98: 0})

        match['Goal'] = match['outcome'].apply(pd.Series)['id'].map({97: 1, 100: 0, 116:0, 99: 0, 98: 0})

        match = match.drop(['body_part', 'outcome', 'end_location'], axis = 1)

        match['Penalty_Number'] = range(1, len(match)+1)

        match['Keeper'] = np.zeros(len(match))

        match['Elimination'] = computeElimination(match)

        match['Home'] = np.zeros(len(match))

        match.loc[match['Team'] == stadium, 'Home'] = np.ones(len(match[match['Team'] == stadium]))

        if not(player_pos.empty):
            if 1 in player_pos['id'].values:
                match['Keeper_changed'] = np.ones(len(match))
            else:
                match['Keeper_changed'] = np.zeros(len(match))
        else:
            match['Keeper_changed'] = np.zeros(len(match))

        if i == '2302764': # Missing data for one game, fixed it manually
            match.loc[4648] = ['AC Milan', 'ucl2005_2302764', 5, 'R', 1.0, 0.0, 9, 0, 1, 0, 0]

        ps = pd.concat([ps, match], axis = 0)
    return ps

def get_statsbomb():
    """
    Method that returns all penalty shooutouts from the data from StatsBomb
    """
    penalty_shootouts = pd.DataFrame()
    # Data of interest
    comps = {'55': ['43'], '16': ['27', '23', '37']}
    for comp_id, seasons in comps.items():
        for s in seasons:
            data = '../data/open-data-master/data/matches/' + comp_id + '/' + s + '.json'
            df = pd.read_json(data)
            # Appending to the general dataframe after transformations
            penalty_shootouts = pd.concat([penalty_shootouts, get_international(df, comp_id, s)], axis = 0)

    return penalty_shootouts