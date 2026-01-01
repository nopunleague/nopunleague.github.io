from espn_api.football import League
import pandas as pd
import numpy as np
import my_secrets
import matplotlib.pyplot as plt
from pprint import pprint
import scienceplots

plt.style.use('science')

years = [2021, 2022, 2023, 2024, 2025]

# intiliaze the scores dictionary 
ps = dict()
ps['team_id'] = []
ps['owner'] = []
ps['year'] = []
ps['week'] = []
ps['score'] = []

for year in years:
    print(year)
    league = League(league_id=my_secrets._league_id,
                    year=year,
                    espn_s2=my_secrets._espn_s2,
                    swid=my_secrets._swid,
                    fetch_league=True)
    cmp = league.currentMatchupPeriod
    pprint(cmp)
    for week_num in range(1,cmp):
        matchups = league.box_scores(week_num)
        # get everyones scores for the week 
        for match in matchups:
            for team,score in zip(
                [match.home_team,match.away_team],
                [match.home_score, match.away_score]):
                if team:
                    ps['team_id'].append(team.team_id)
                    ps['owner'].append(f'{team.owners[-1]['firstName']} {team.owners[-1]['lastName']}')
                    ps['year'].append(year)
                    ps['week'].append(week_num)
                    ps['score'].append(score)
                else:
                    print(f'{year}, {week_num}')
        
psdf = pd.DataFrame(ps)

#filter out 2 week games 
psdf = psdf[~((psdf['week']==15)&(psdf['year']==2021))]

pprint(psdf.sort_values(by='score',ascending=False).head(20).to_markdown())

pprint(psdf.sort_values(by='score').head(20).to_markdown())

pprint(psdf.groupby(['owner', 'year']).mean().to_markdown())

pprint(psdf.groupby(['owner', 'year']).mean().groupby('owner').mean().sort_values(by='score',ascending=False).to_markdown())
pprint(psdf.groupby(['owner', 'year']).mean().groupby('year').mean().sort_values(by='score',ascending=False).to_markdown())


