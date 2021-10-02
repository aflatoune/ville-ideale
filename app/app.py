import json
import pandas as pd
import dash
import dash_table as dt
import dash_bootstrap_components as dbc
import plotly.express as px

from dash import dcc
from dash import html
from dash.dependencies import Input, Output


with open("data/geo_info.geojson", encoding="utf-8") as f:
    gj = json.load(f)

d = {}
for sub_d in gj["features"]:
    d[sub_d["properties"]["code"]] = sub_d["properties"]["nom"]
d = pd.DataFrame.from_dict(d, orient="index")

city_info = pd.read_csv("data/city_info.csv", decimal=",",
                        sep=",", index_col=0).reset_index(drop=True)
city_info["code Insee"] = city_info["city"].map(lambda x: x[-5:])
city_info = pd.merge(city_info, d, how='left', left_on=[
                     'code Insee'], right_on=d.index)
city_info.rename(columns={0: "Commune",
                          "environment": "Environnement",
                          "transport": "Transports",
                          "security": "Sécurité",
                          "health": "Santé",
                          "leisure": "Sports et loisirs",
                          "culture": "Culture",
                          "education": "Enseignement",
                          "shop": "Commerces",
                          "quality_of_life": "Qualité de vie",
                          "average_score": "Note moyenne"},
                 inplace=True)

CRITERIA = city_info.columns[1:-2].to_list()
COLS = CRITERIA + ["Commune"]


app = dash.Dash(__name__)


app.layout = html.Div([
    html.H1("Trouvez la ville de vos rêves (dans la petite couronne)"),
    html.Div(
        className="map",
        children=[
            html.P(children=["Les notes sont issues du site ", html.A("ville-idéale.", href="https://www.ville-ideale.fr/")]),
            html.P("Critère :"),
            dcc.RadioItems(
                id='crit',
                options=[{"label": x, "value": x} for x in CRITERIA],
                value=CRITERIA[-1],
                labelStyle={'display': 'inline-block'}
            ),
            dcc.Graph(id="critmap")
        ]),
    html.Div(
        className="rank",
        children=[
            html.P("Classement des villes :"),
            dt.DataTable(
                id="rank_tbl",
                columns=[{"name": x, "id": x, 'editable': (
                    x == 'Commune')} for x in COLS],
                fixed_rows={'headers': True},
                style_cell={'textAlign': 'left'},
                style_cell_conditional=[{
                    "if": {'column_id': "Commune"},
                    'maxWidth': 50
                }],
                style_as_list_view=True,
                style_header_conditional=[{
                    'if': {'column_editable': True},
                    'backgroundColor': 'rgb(210, 212, 205)',
                    'color': 'black'
                }],
                page_current=0,
                page_size=10,
                page_action='custom',
                sort_action='custom',
                sort_mode='single',
                sort_by=[]
            )
        ]
    )
])


@app.callback(
    Output("critmap", "figure"),
    [Input("crit", "value")]
)
def display_critmap(crit):
    fig = px.choropleth(
        city_info, geojson=gj,
        color=crit,
        hover_name="Commune",
        locations="code Insee",
        featureidkey="properties.code",
        projection="mercator",
        color_continuous_scale=["red", "orange", "yellow", "green"]
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(hoverlabel=dict(
        bgcolor="white",
        font_size=14,
        font_family="Rockwell"
    ))
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.update_traces(hovertemplate=None)
    fig.data[0].marker.line.color = "black"
    return fig


@app.callback(
    Output("rank_tbl", "data"),
    Input("rank_tbl", "page_current"),
    Input("rank_tbl", "page_size"),
    Input("rank_tbl", "sort_by")
)
def update_table(page_current, page_size, sort_by):
    if len(sort_by):
        dff = city_info.sort_values(
            sort_by[0]['column_id'],
            ascending=sort_by[0]['direction'] == 'asc',
            inplace=False
        )
    else:
        dff = city_info

    return dff.iloc[
        page_current*page_size:(page_current + 1)*page_size
    ].to_dict('records')


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
