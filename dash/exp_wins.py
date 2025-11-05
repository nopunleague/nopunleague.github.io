from espn_api.football import League
import pandas as pd
import numpy as np
import my_secrets
import matplotlib.pyplot as plt

league = League(league_id=my_secrets._league_id,
                year=2025,
                espn_s2=my_secrets._espn_s2,
                swid=my_secrets._swid,
                fetch_league=True)

ps = dict()
# intiliaze the scores dictionary 
for team in league.teams:
    ps[team.team_name] = dict()
    ps[team.team_name]['proj_score'] = 0.0
    ps[team.team_name]['score'] = 0.0 
    ps[team.team_name]['exp_wins'] = 0.0
    ps[team.team_name]['act_wins'] = team.wins

Nteams = len(league.teams)

for week_num in range(1,10):
    matchups = league.box_scores(week_num)
    # get everyones scores for the week 
    for match in matchups:
        for team,score in zip([match.home_team,match.away_team],[match.home_score, match.away_score]):
            ps[team.team_name]['score'] = score
    
    # using pandas I guess
    # find expected wins 
    psdf = pd.DataFrame(ps).T
    # Teams are columns and score lists are indices
    # sort by score 
    psdf = psdf.sort_values(by=['score'],ascending=False)
    for team in league.teams:
        rank = psdf.index.get_loc(team.team_name)
        exp_wins = (Nteams-rank)/Nteams
        ps[team.team_name]['exp_wins'] += exp_wins


psdf = pd.DataFrame(ps).T
print(psdf['exp_wins'])

fig,ax = plt.subplots(1,1)

ax.scatter(psdf['act_wins'],psdf['exp_wins'])

fig.savefig('exp_wins.png')




