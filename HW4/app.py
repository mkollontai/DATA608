import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import pandas as pd
import numpy as np


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

spc_url = ('https://data.cityofnewyork.us/resource/nwxe-4ae8.json?' +\
        '$select=spc_common,count(tree_id)' +\
        '&$group=spc_common').replace(' ', '%20')
spc = pd.read_json(spc_url).spc_common.unique()
spc[-1:] = ['Unlisted']

stw_url = ('https://data.cityofnewyork.us/resource/nwxe-4ae8.json?' +\
        '$select=steward,count(tree_id)' +\
        '&$group=steward').replace(' ', '%20')
stw = pd.read_json(stw_url).steward.unique()
stw[-1:] = ['Unknown']

boro = ['Bronx','Queens','Brooklyn','Manhattan','Staten Island']
boros = len(boro)    
pie_titles = [b for b in boro]
area_titles = [b + " Steward Effect" for b in boro]
stew = ['None', '1or2', '3or4', '4orMore']
hlth = ['Good', 'Fair', 'Poor']
color_dict = {'Good':'#14C968',
              'Fair':'#C99914',
              'Poor':'#A31A21',
              'Unknown':'#696463'}
  
app.layout = html.Div([
        
    dcc.Dropdown(
        id = 'Species',
        options=[{'label':spec, 'value':spec} for spec in spc],
        value = spc[0]
    ),
    
    #html.Label('Boroughs'),
    #dcc.Checklist(
    #    id = 'Boroughs',
    #    options=[
    #        {'label': 'Bronx', 'value': 'Bronx'},
    #        {'label': 'Queens', 'value': 'Queens'},
    #        {'label': 'Brooklyn', 'value': 'Brooklyn'},
    #        {'label': 'Manhattan', 'value': 'Manhattan'},
    #        {'label': 'Staten Island', 'value': 'Staten Island'}
    #    ],
    #    value=['Bronx','Queens','Brooklyn','Manhattan','Staten Island']
    #),
    
    dcc.Graph(id = 'nycHealth'),
    dcc.Graph(id = 'boroHealth'),
    dcc.Graph(id = 'StewardEffect')
])

@app.callback(
    [Output('nycHealth', 'figure'),
     Output('boroHealth', 'figure'),
     Output('StewardEffect', 'figure')],
    [Input('Species', 'value')]
)
def update_pies(species):
    
    
    url = ("https://data.cityofnewyork.us/resource/nwxe-4ae8.json?" +\
        "$select=boroname,steward,health,count(tree_id)" +\
        "&$where=spc_common='" + species +\
        "'&$group=boroname,steward,health").replace(' ', '%20')
    nyc_df = pd.read_json(url)
    nyc_df = nyc_df.dropna()
    nyc_df['health'] = pd.Categorical(nyc_df.health, categories = hlth, ordered = True)
    nyc_df=nyc_df.sort_values(by='health')
    nyc_df['boroname'] = pd.Categorical(nyc_df.boroname, categories = boro, ordered = True)
    nyc_df=nyc_df.sort_values(by='boroname')

    
    fig1 = px.pie(
            nyc_df,
            values = 'count_tree_id', 
            names = 'health', 
            title = 'Health breakdown of %i %s trees in NYC' % (nyc_df['count_tree_id'].sum(),species),
            color = 'health',
            color_discrete_map = color_dict
    )
    fig1.update(layout=dict(title=dict(x=0.5)))
    
    
    fig2 = make_subplots(
        rows = 1, 
        cols = boros, 
        subplot_titles = pie_titles,
        specs=[[{'type':'domain'}] * boros]
    )  
   
    for i in range(0,boros):
        boro_df = nyc_df[nyc_df['boroname']==boro[i]]#.groupby('health').agg({'count_tree_id' : 'sum'}).reset_index()
        colors = np.array(['']*len(boro_df['health']), dtype = object)
        for j in np.unique(boro_df['health']):
            colors[np.where(boro_df['health']==j)] = color_dict[str(j)]

        fig2.add_trace(
            go.Pie(
                values = boro_df['count_tree_id'], 
                labels = boro_df['health'],
                marker_colors = colors,
                title = {
                    'text' : '%i Trees' % (boro_df['count_tree_id'].sum()),
                    'position' : 'bottom center'
                },
                scalegroup ='one'
            ),
            row=1,
            col=i+1
        )
        
    fig3 = px.bar(
        nyc_df, 
        x="steward",
        y="count_tree_id",
        color="health",
        facet_col="boroname",
        color_discrete_map = color_dict
    )

    fig3.update_layout(
            barmode = 'relative', 
            barnorm = 'percent',
            xaxis={'categoryorder': 'array', 'categoryarray': stew}
    )
        
    return fig1, fig2, fig3 
    
if __name__ == '__main__':
    app.run_server(debug=True)
