from espn_api.football import League
import pandas as pd
import numpy as np
import my_secrets
import matplotlib.pyplot as plt
import scienceplots

plt.style.use('science')

league = League(league_id=my_secrets._league_id,
                year=2025,
                espn_s2=my_secrets._espn_s2,
                swid=my_secrets._swid,
                fetch_league=True)

ps = dict()
# intiliaze the scores dictionary 
for team in league.teams:
    ps[team.team_name] = dict()
    ps[team.team_name]['proj_points'] = 0.0
    ps[team.team_name]['score'] = 0.0 
    ps[team.team_name]['total_points'] = 0.0 
    ps[team.team_name]['exp_wins'] = 0.0
    ps[team.team_name]['act_wins'] = team.wins

Nteams = len(league.teams)

for week_num in range(1,10):
    matchups = league.box_scores(week_num)
    # get everyones scores for the week 
    for match in matchups:
        for team,score,lineup in zip(
            [match.home_team,match.away_team],
            [match.home_score, match.away_score],
            [match.home_lineup, match.away_lineup]):
            ps[team.team_name]['score'] = score
            ps[team.team_name]['total_points'] += score
            for player in lineup:
                if player.slot_position == 'BE': continue
                ps[team.team_name]['proj_points'] += player.projected_points
    
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

# Expected Wins Figure
fig,ax = plt.subplots(1,1,figsize=(10,8))

ax.set_ylabel('Expected Wins')
ax.set_xlabel('Actual Wins')
ax.set_xlim([0, 10])
ax.set_ylim([0, 10])
cax = ax.scatter(psdf['act_wins'],
           psdf['exp_wins'],
           c=(psdf['act_wins']-psdf['exp_wins']),
           cmap='coolwarm')

ax.plot([0,10],[0,10],'k--')

# zoomed inset 
x1, x2, y1, y2 = 4.5, 6.5, 4.75, 6
axins = ax.inset_axes(
    bounds=[0.6, 0.05, 0.3, 0.3],
    xlim=(x1, x2), ylim=(y1,y2))

axins.scatter(psdf['act_wins'],
           psdf['exp_wins'],
           c=(psdf['act_wins']-psdf['exp_wins']),
           cmap='coolwarm')

ax.indicate_inset_zoom(axins,edgecolor='black')
for team in league.teams:
    roangle = 40
    if team.team_name == 'Team Tripp': roangle = 20
    ax.annotate(team.team_name,
                [psdf['act_wins'][team.team_name],psdf['exp_wins'][team.team_name]],
                rotation=roangle)
    axins.annotate(team.team_name,
                [psdf['act_wins'][team.team_name],psdf['exp_wins'][team.team_name]],
                rotation=roangle)

ax.annotate('Unlucky Halfspace',[3,9],size='x-large',weight='heavy')
ax.annotate('Lucky Halfspace', [3,1.5],size='x-large',weight='heavy')

cbar = fig.colorbar(cax,ticks=[-2.5, 1])
cbar.ax.set_yticklabels(['Fucked by schedule', 'Helped by schedule'])

fig.savefig('exp_wins.png')

# Underperformance Figure 
fig,ax = plt.subplots(1,1,figsize=(10,8))
ax.set_ylabel('Projected Points')
ax.set_xlabel('Actual Points')
cax = ax.scatter(psdf['total_points'],
                 psdf['proj_points'],
                 c=(psdf['total_points']-psdf['proj_points']),
                 cmap='coolwarm')
ax.plot([800, 1400],[800, 1400],'k--')

# zoomed inset 
x1, x2, y1, y2 = 1150, 1225, 1150, 1225 
axins = ax.inset_axes(
    bounds=[0.6, 0.05, 0.3, 0.3],
    xlim=(x1, x2), ylim=(y1,y2))

axins.scatter(psdf['total_points'],
           psdf['proj_points'],
           c=(psdf['total_points']-psdf['proj_points']),
           cmap='coolwarm')

ax.indicate_inset_zoom(axins,edgecolor='black')
for team in league.teams:
    roangle = 40
    if team.team_name == 'Stinky Red Dogs': roangle = 60
    ax.annotate(team.team_name,
                [psdf['total_points'][team.team_name],psdf['proj_points'][team.team_name]],
                rotation=roangle)
    axins.annotate(team.team_name,
                [psdf['total_points'][team.team_name],psdf['proj_points'][team.team_name]],
                rotation=roangle-40)

ax.annotate('Unlucky Halfspace',[900,1350],size='x-large',weight='heavy')
ax.annotate('Lucky Halfspace', [900,850],size='x-large',weight='heavy')

cbar = fig.colorbar(cax,ticks=[-150, 50])
cbar.ax.set_yticklabels(['Fooled by ESPN', 'Spites lizard people'])
fig.savefig('Underperformance.png')


