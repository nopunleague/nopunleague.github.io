from espn_api.football import League
import pandas as pd
import numpy as np
import my_secrets

league = League(league_id=my_secrets._league_id,
                year=2025,
                espn_s2=my_secrets._espn_s2,
                swid=my_secrets._swid,
                fetch_league=True)

ps = dict()
positions = ["QB","RB","WR","TE","D/ST","K"]
# intiliaze the scores dictionary 
for team in league.teams:
    ps[team.team_name] = dict()
    for pos in positions:
        ps[team.team_name][pos] = []

for week_num in range(1,10):
    matchups = league.box_scores(week_num)
    for match in matchups:
        for team,lineup in zip([match.home_team,match.away_team],[match.home_lineup, match.away_lineup]):
            for player in lineup:
                # ignore bench players
                if player.slot_position == 'BE':
                    continue
                
                # append the socres for each position 
                ps[team.team_name][player.position].append(player.points)

# using pandas I guess
psdf = pd.DataFrame(ps)
# Teams are columns and score lists are indices
# calculate averages in place
# Also transpose
# Now score means are columns and teams are indices
psdf = psdf.map(lambda x: np.mean(x)).T

# sort for each position and print 
for pos in positions:
    print(f'{pos}')
    print('==================')
    posdf = psdf.sort_values(by=[pos],ascending=False)
    print(posdf[pos])
    print('\n\n')



