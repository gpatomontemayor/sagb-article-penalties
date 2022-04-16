import pandas as pd
import numpy as np

def get_zone(lst):
    """
    Method to change into
    In: lst with (x,y,z) coordinates from end of shot
    Out: same way (1-9) as in kaggle depending on the zone
    """
    if lst[1] < 36 + 8/3:
        if lst[2] < 2.67/3:
            return 7
        elif 2.67/3 < lst[2] <= 2*2.67/3:
            return 4
        else:
            return 1
    elif (36+8/3 <= lst[1] < 36 + 2*8/3):
        if lst[2] < 1:
            return 8
        elif 2.67/3 <= lst[2] < 2*2.67/3:
            return 5
        else:
            return 2
    else:
        if lst[2] < 2.67/3:
            return 9
        elif 2.67/3 <= lst[2] < 2*2.67/3:
            return 6
        else:
            return 3

def isElimination(goalA, goalB, pen):
    """
    Algorithm to compute whether or not the penalty was facing elimination
    In: Number of goals scored by team A, by team B and penalty number
    Out: Whether or not the penalty was facing elimination (a miss/goal ends it)
    """
    if pen == 6:
        if goalA - goalB == 3:
            # Current score 3-0 for team A, a miss finishes
            return 1
        elif goalB - goalA == 2:
            # Current score 0-2 for team B, a goal finishes
            return 1
        return 0
    elif pen == 7:
        if goalA - goalB == 2:
            return 1
        elif goalB - goalA == 2:
            return 1
        return 0
    elif pen == 8:
        if goalA - goalB == 2:
            return 1
        elif goalB - goalA == 1:
            return 1
        return 0
    elif pen == 9:
        if goalA - goalB == 1:
            return 1
        elif goalB - goalA == 1:
            return 1
        return 0
    elif (pen % 2 == 0) & (pen >= 10):
        return 1
    return 0

def computeElimination(df):
    """
    In: dataframe for a game
    Out: array for which wether the penalty was facing elimination or not
    """
    elim = []
    for i in df['Penalty_Number'].values:
        elim.append(isElimination(np.sum(df.loc[(df['Penalty_Number'] < i) & (df['Penalty_Number'] % 2 == 1), 'Goal']),
        np.sum(df.loc[(df['Penalty_Number'] < i).values & (df['Penalty_Number'] % 2 == 0).values, 'Goal']), i))
    return elim