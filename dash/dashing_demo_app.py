import dash
import dash_core_components as dcc
import dash_html_components as html

app = dash.Dash()

app.layout = html.Div(children=[
    html.H1(children='Hello World'),

    html.Div(children='''
             Dash example
             '''),

    dcc.Graph(
        id='example-graph',
        figure={
            'data':[
                {'x': [1,2,3], 'y': [ 4, 1,2], 'type': 'bar', 'name': 'sf'},
                {'x': [1,2,3], 'y': [6, 3, 1], 'type': 'bar', 'name': 'dc'},],
            'layout': {'title': 'Dash data visualization'}
            })
        ]
                      )

