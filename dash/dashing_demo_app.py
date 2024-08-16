import dash
import dash_core_components as dcc
import dash_html_components as html

from espn_api.football import League
import secrets

# prepare the espn data for this example
league = League(league_id=secrets._league_id,
                year=2023,
                espn_s2=secrets._espn_s2,
                swid=secrets._swid)

team_names = [x.team_name for x in league.teams]
n_acq = [x.acquisitions for x in league.teams]

app = dash.Dash()

app.layout = html.Div(children=[
    html.H1(children='No Pun League Advanced Statistics Dashboard'),

    html.Div(children='''
             This example plot shows the total number of trades and waiver wire acquisitions
             by team for the 2023 season. Hopefully this information will be useful to you as you
             prepare for  the 2024 draft. Some teams have apparently relied on in-season roster adjustment
             more than others. Did they completely biff the draft? Were they riddled by injuries? 
             '''),

    dcc.Graph(
        id='2023_acquisitions_by_team',
        figure={
            'data':[
                {'x': team_names, 'y': n_acq, 'type': 'bar', 'name': '2023'},],
            'layout': {'title': 'Waiver Wire and Trades by Team'}
            })
        ]
                      )

