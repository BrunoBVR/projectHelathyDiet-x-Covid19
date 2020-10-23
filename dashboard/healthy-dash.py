import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import pycountry

### Uncomment bellow to download data using kaggle API ###
#######################################################
# from kaggle.api.kaggle_api_extended import KaggleApi
# from zipfile import ZipFile
# api = KaggleApi()
# api.authenticate()
#
#
# api.dataset_download_files('mariaren/covid19-healthy-diet-dataset')
# zf = ZipFile('covid19-healthy-diet-dataset.zip')
# zf.extractall('data')
# zf.close()
#######################################################

kg_df_full = pd.read_csv('./data/Food_Supply_Quantity_kg_Data.csv')

# Cleaning data

# Let's drop the last column as it is just a unit information
kg_df = kg_df_full.drop('Unit (all except Population)', axis = 1)

## Taking care of Undernourished non numeric entries
kg_df.loc[kg_df_full['Undernourished'] == '<2.5', 'Undernourished'] = '2.0'
kg_df['Undernourished'] = pd.to_numeric(kg_df['Undernourished'])

## Rescaling food columns to sum to 100%
kg_df.iloc[:,1:24] = kg_df.iloc[:, 1:24] * 2

## Fill missing values with mean
kg_df = kg_df.fillna(kg_df.mean())

## Create 'Mortality' column
kg_df['Mortality'] = kg_df['Deaths']/kg_df['Confirmed']

## Create 'ObesityAboveAvg' column
kg_df['ObesityAboveAvg'] = (kg_df["Obesity"] > kg_df['Obesity'].mean()).astype(int)

## DF with COVID info
df_covid = kg_df[['Country','Confirmed','Deaths','Active','Mortality']]

## HOC and LOC df
df_high_ob = kg_df[kg_df.Obesity > kg_df['Obesity'].mean()]
df_low_ob = kg_df[kg_df.Obesity <= kg_df['Obesity'].mean()]

## Preparing countries dict for dropdown options
countries_options = []
for country in kg_df['Country']:
    my_dict = {}
    my_dict['label'] = str(country)
    my_dict['value'] = str(country)
    countries_options.append(my_dict)

## Features
food_groups = ['Alcoholic Beverages', 'Animal fats',
       'Aquatic Products, Other', 'Cereals - Excluding Beer', 'Eggs',
       'Fish, Seafood', 'Fruits - Excluding Wine', 'Meat',
       'Milk - Excluding Butter', 'Miscellaneous', 'Offals', 'Oilcrops',
       'Pulses', 'Spices', 'Starchy Roots', 'Stimulants', 'Sugar & Sweeteners',
       'Sugar Crops', 'Treenuts', 'Vegetable Oils', 'Vegetables']

## colors for bar graph
colors = ['IndianRed','DarkSeaGreen']

## Getting country ISO numbers
list_countries = kg_df['Country'].tolist()
d_country_code = {}  # To hold the country names and their ISO
for country in list_countries:
    try:
        country_data = pycountry.countries.search_fuzzy(country)
        # country_data is a list of objects of class pycountry.db.Country
        # The first item  ie at index 0 of list is best fit
        # object of class Country have an alpha_3 attribute
        country_code = country_data[0].alpha_3
        d_country_code.update({country: country_code})
    except:
        # print('could not add ISO 3 code for ->', country)
        # If could not find country, make ISO code ' '
        d_country_code.update({country: ' '})

d_country_code['Iran (Islamic Republic of)'] = 'IRN'
d_country_code['Korea, North'] = 'PRK'
d_country_code['Korea, South'] = 'KOR'
d_country_code['Taiwan*'] = 'TWN'
d_country_code['Venezuela (Bolivarian Republic of)'] = 'VEN'
# print(d_country_code) # Uncomment to check dictionary

# create a new column iso_alpha in the df
# and fill it with appropriate iso 3 code
for k, v in d_country_code.items():
    kg_df.loc[(kg_df.Country == k), 'iso_alpha'] = v


###############################################################################
################ START OF APP #################################################
###############################################################################
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY])

app.layout = html.Div([

    dbc.Card([
        dbc.CardImg(src="https://images.squarespace-cdn.com/content/v1/5919b0fd6b8f5b6a4a256b4e/1580488750529-30TFT9JN7P0XR5ZS4H8Y/ke17ZwdGBToddI8pDm48kH-KoR6KuuBcq9Z5xi422Q8UqsxRUqqbr1mOJYKfIPR7LoDQ9mXPOjoJoqy81S2I8N_N4V1vUb5AoIIIbLZhVYy7Mythp_T-mtop-vrsUOmeInPi9iDjx9w8K4ZfjXt2dsEF-sCd5QWO5hm7HfmdIziW4p77bAKWYf1JE4Sw1bIUW07ycm2Trb21kYhaLJjddA/1.31.20-Highlight.jpg",
            title="Image by Hearn Kirkwood",
            top = True,
            alt = "Healthy Diet",
            style={}),
        dbc.CardBody([
            html.H1("COVID-19 and a Healthy Diet",
                    style={'textAlign':'center'}),

            html.H3("Data exploration",
                style={'textAlign':'center'}),

            html.H6(["Made with ",
                     html.A('Dash', href = 'https://dash.plotly.com/',
                        style={'color':'#000000'},
                        target = '_blank)')],
                style={'textAlign':'right'}),

            html.H6("by Bruno Vieira Ribeiro",
                style={'textAlign':'right'}),

            html.P("bruno.ribeiro@ifb.edu.br, bruno64bits@gmail.com",
                style={'textAlign':'right'})
        ])
    ],
    color='primary',
    inverse=True),

    html.Br(),
    html.Br(),
############### COVID-19 distributions on countries
    dbc.Alert([
        dbc.Row([
            dbc.Col(html.H2("General COVID-19 Statistics"))
        ]),
        dbc.Row([
            dbc.Col(dcc.Markdown("""
            ### Slider:
            Use the slider to alter the display of the following four graphs.
            * Both left and right sliders are available.
            * You can select the range of countries to display COVID-19 information.
            * By `default`, the graphs show the first **ten** countries in descending order.
            """
            ), width={"size": 10, "offset":1})
        ])
    ], color = 'primary'),

    dbc.Row([
        dbc.Col(dcc.RangeSlider(id='slider',
            min = 1,
            max = len(countries_options),
            step = 1,
            marks = {i:str(i) for i in range(1,len(countries_options)) if i%10 == 0},
            value = [1,10])
            )
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id='confirmed'), width = {"size":5, "offset": 1}),

        dbc.Col(dcc.Graph(id='deaths'), width = {"size":5})
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id='active'), width = {"size":5, "offset": 1}),

        dbc.Col(dcc.Graph(id='mortality'), width = {"size":5})
    ]),

    html.Br(),
    html.Br(),
    html.Br(),
####################################################################

    dbc.Alert([
        dbc.Row([
            dbc.Col(html.H3('Choose the countries to display COVID-19 data:')),

            dbc.Col(dcc.Dropdown(id='covid-country-dd',
                options = countries_options,
                style={'color':'#000000'},
                value = ['Brazil'],
                multi = True,
                placeholder = 'Select countries.'
                )
            )
        ]),
    ]),

########################################## TABLE
    dbc.Row([
        dbc.Col(dash_table.DataTable(
            id = 'dt-covid',
            editable = True,
            data = df_covid[df_covid.Country.isin(['Brazil'])].to_dict('records'),
            page_size = len(df_covid[df_covid.Country.isin(['Brazil'])].index),
            style_header={
                'backgroundColor': 'rgb(0, 153, 92)',
                'fontWeight': 'bold',
                'color': 'white',
                'border': '1px solid black'
            },
            style_data={ 'border': '1px solid black' },

            ),
            width = {"size":8, "offset": 2}
        )
    ]),

    html.Br(),
    html.Hr(),

    dbc.Row([
        dbc.Col(dcc.Graph(id='deaths-v-conf',
            figure = (px.scatter(kg_df, x="Confirmed", y = "Deaths",size = "Active", hover_name='Country',
                 size_max=30, trendline = "ols", template="simple_white",
                 title='Deaths vs. Confirmed - Size corresponds to Active cases')) ),
            width = {"size":5, "offset": 1}
            ),

        dbc.Col(dcc.Graph(id='ob-v-deaths',
            figure = (px.scatter(kg_df, x="Deaths", y = "Obesity", size = "Mortality",
                hover_name='Country', log_x=False, size_max=30, template="simple_white",
                title='Obesity rate vs. Deaths - Size corresponds to Mortality'))
                .add_shape(
                        type="line",
                        x0=0,
                        y0=kg_df['Obesity'].mean(),
                        x1=kg_df['Deaths'].max(),
                        y1=kg_df['Obesity'].mean(),
                        line=dict(
                            color="crimson",
                            width=4
                        )
                    )
                ),
            width = {"size":5, "offset": 1}
            )
    ]),

    html.Br(),
    html.Br(),
################## SELECT AXIS
    dbc.Alert([
        dbc.Row([
            dbc.Col(dcc.Markdown("""
            ### Create your graph:
            Create your own scatter plot figure by selecting a variable for the x and y axis.
            You can also choose the variable to represent the size of points in the graph.
            """), width={"size": 10}
            )
        ]),
    ]),


    dbc.Row([
        dbc.Col([html.Label('Choose values for x-axis and y-axis:'),
        dcc.RadioItems(id='x-axis',
            options=[
                {'label': 'Deaths  ', 'value': 'Deaths'},
                {'label': 'Confirmed  ', 'value': 'Confirmed'},
                {'label': 'Active  ', 'value': 'Active'},
                {'label': 'Obesity  ', 'value': 'Obesity'}
            ],
            value = 'Confirmed',
            labelStyle={'display': 'inline-block'},
            inputStyle={"margin-left": "20px"}),
            dcc.RadioItems(id='y-axis',
            options=[
                {'label': 'Deaths', 'value': 'Deaths'},
                {'label': 'Confirmed', 'value': 'Confirmed'},
                {'label': 'Active', 'value': 'Active'},
                {'label': 'Obesity', 'value': 'Obesity'}
            ],
            value = 'Deaths',
            labelStyle={'display': 'inline-block'},
            inputStyle={"margin-left": "20px"}),

            html.Br(),

            html.Label('Choose values for the size of points:'),
            dcc.RadioItems(id='points-size',
                options=[
                    {'label': 'Deaths  ', 'value': 'Deaths'},
                    {'label': 'Confirmed  ', 'value': 'Confirmed'},
                    {'label': 'Active  ', 'value': 'Active'},
                    {'label': 'Obesity  ', 'value': 'Obesity'}
                ],
                value = 'Active',
                labelStyle={'display': 'inline-block'},
                inputStyle={"margin-left": "20px"})

        ],width={"size":4,"offset":2}),

        dbc.Col(dcc.Graph(id='custom-graph'), width={"size":6}
        )
    ]),

    dbc.Alert([
        dbc.Row([
            dbc.Col(dcc.Markdown('''
            ## Distribution of food intake by group.

            * Color scale refers to countries with Obesity rate above (1) or bellow (0) average.
            * The `count` value is measured in percentage of total food intake.
            * Vertical lines correspond to median value for each group.

            '''))
        ]),
    ]),


    dbc.Row([
        dbc.Col(dcc.Graph(id='animal-products',
            figure = (px.histogram(kg_df, x = "Animal Products", nbins=50,
                      color = "ObesityAboveAvg") )
                      .add_shape(
                              # Mean value of Vegetal Products intake in low obesity countries
                                  type="line",
                                  x0=df_low_ob['Animal Products'].median(),
                                  y0=0,
                                  x1=df_low_ob['Animal Products'].median(),
                                  y1=12,
                                  line=dict(
                                      color="darkblue",
                                      width=4
                                  ),
                          )
                    .add_shape(
                                # Mean value of Animal Products intake in high obesity countries
                                    type="line",
                                    x0=df_high_ob['Animal Products'].median(),
                                    y0=0,
                                    x1=df_high_ob['Animal Products'].median(),
                                    y1=12,
                                    line=dict(
                                        color="crimson",
                                        width=4
                                    ),
                            )
                ),

            width = {"size":6}
            ),

        dbc.Col(dcc.Graph(id='vegetal-products',
            figure = (px.histogram(kg_df, x = "Vegetal Products", nbins=50,
                      color = "ObesityAboveAvg") )
                      .add_shape(
                              # Mean value of Vegetal Products intake in low obesity countries
                                  type="line",
                                  x0=df_low_ob['Vegetal Products'].median(),
                                  y0=0,
                                  x1=df_low_ob['Vegetal Products'].median(),
                                  y1=12,
                                  line=dict(
                                      color="darkblue",
                                      width=4
                                  ),
                          )
                    .add_shape(
                                # Mean value of Animal Products intake in high obesity countries
                                    type="line",
                                    x0=df_high_ob['Vegetal Products'].median(),
                                    y0=0,
                                    x1=df_high_ob['Vegetal Products'].median(),
                                    y1=12,
                                    line=dict(
                                        color="crimson",
                                        width=4
                                    ),
                            )

                ),
            width = {"size":6}
            )
    ]),
    html.Br(),

    dbc.Alert([
        dbc.Row([
            dbc.Col(dcc.Markdown('''
            ## Number of Deaths by COVID-19 in different Obesity rate values.

            * In the **left** graph we see the distribution for countries with `Obesity rate bellow the mean value` for all other countries.
            * In the **right** graph, the same distribution is shown for countries with `Obesity rate above the mean value`.
            '''))
        ]),
    ]),


    dbc.Row([
        dbc.Col(dcc.Graph(id='death-obesity',
            figure = (px.bar(kg_df, x = "Country", y ="Deaths", facet_col = "ObesityAboveAvg"))
            .update_xaxes(matches=None,categoryorder="total descending")
            ))
    ]),
    html.Br(),
    html.Br(),
####################################################################
    dbc.Alert([
        dbc.Row([
            dbc.Col(html.H3('Choose the countries to display distribution of food intake by category:')),

            dbc.Col(dcc.Dropdown(id='food-country-dd',
                options = countries_options,
                style={'color': '#000000'},
                value = 'Brazil',
                placeholder = 'Select country.'
                )
            )
        ]),
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id = 'food-pie'), width = {"size":7, 'offset':1}),

        dbc.Col(dcc.Graph(id='veg-v-animal'), width= {"size":4}
        )
    ]),

    html.Br(),
    html.Hr(),

    dbc.Alert([
        dbc.Row([
            dbc.Col(dcc.Markdown("""
            ## Visualizing impact Worldwide

            Bellow you can choose a variable to display it's value, by country,
            as a color scale in a `choropleth` map.
            """
            ))
        ]),
    ]),

    dbc.Row([
        dbc.Col([html.Label('Choose variable to display map color scale:'),
        dcc.RadioItems(id='food-cat',
            options=[
                {'label': 'Deaths  ', 'value': 'Deaths'},
                {'label': 'Confirmed  ', 'value': 'Confirmed'},
                {'label': 'Active  ', 'value': 'Active'},
                {'label': 'Obesity  ', 'value': 'Obesity'},
                {'label': 'Undernourished  ', 'value': 'Undernourished'},
                {'label': 'Animal Products  ', 'value': 'Animal Products'},
                {'label': 'Vegetal Products', 'value': 'Vegetal Products'}
            ],
            value = 'Obesity',
            labelStyle={'display': 'inline-block'},
            inputStyle={"margin-left": "20px"}),
        ],width={"size":10,"offset":2})
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id='map'))
    ]),

    dbc.Alert(id='ftext', color = "info"),

    dbc.Row([
        dbc.Col(dcc.Graph(id='obesity'), width = {"size":5, "offset": 1}),

        dbc.Col(dcc.Graph(id='under'), width = {"size":5})
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id='AP'), width = {"size":8, "offset": 2})
    ]),

###### WHITE SPACE
    html.Br(),
    html.Br(),
    html.Br(),

### REFs
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("References"),
                dbc.CardBody([
                    dbc.ListGroup([
                        dbc.ListGroupItem(
                            html.A("Original Kaggle data set",
                                href="https://www.kaggle.com/mariaren/covid19-healthy-diet-dataset",
                                target="_blank")
                        ),
                        dbc.ListGroupItem(
                            html.A("COVID-19 data from CSSE",
                                href="https://coronavirus.jhu.edu/map.html",
                                target="_blank")
                        ),
                        dbc.ListGroupItem(
                            html.A("Food and Agriculture Organization of the United Nations",
                                href="http://www.fao.org/faostat/en/#home",
                                target="_blank")
                        ),
                        dbc.ListGroupItem(
                            html.A("WHO - #HealthyAtHome",
                                href="https://www.who.int/campaigns/connecting-the-world-to-combat-coronavirus/healthyathome/healthyathome---healthy-diet",
                                target="_blank")
                        )

                    ])
                ])
            ],
            color='light'),
        width = {"size":4, "offset": 8}
        )
    ])

])


#########################################
###################### CALLBACK FUNCTIONS
#########################################
@app.callback(
    Output('confirmed','figure'),
    Output('deaths','figure'),
    Output('active','figure'),
    Output('mortality','figure'),
    [Input('slider','value')]
)
def update_covid(value):
    start = value[0]
    end = value[1]

    fig1 = px.bar(kg_df.sort_values('Confirmed', ascending = False)[start-1:end],
                    x = "Country", y ="Confirmed",
                    title="Confirmed Cases - Percentage of total population")

    fig2 = px.bar(kg_df.sort_values('Deaths', ascending = False)[start-1:end],
                    x = "Country", y ="Deaths",
                    title="Number of Deaths - Percentage of total population")

    fig3 = px.bar(kg_df.sort_values('Active', ascending = False)[start-1:end],
                    x = "Country", y ="Active",
                    title="Active Cases - Percentage of total population")

    fig4 = px.bar(kg_df.sort_values('Mortality', ascending = False)[start-1:end],
                    x = "Country", y ="Mortality",
                    title="Mortality")

    return fig1,fig2,fig3,fig4


@app.callback(
    Output('dt-covid', 'columns'),
    Output('dt-covid', 'data'),
    Output('dt-covid', 'page_size'),
    [Input('covid-country-dd', 'value')]
)
def update_table(value):
    selected = list(value)
    columns=[
        {"name": i + "(% of population)", "id": i}
        if (i != "Country" and i != "Mortality") else
        {"name": i, "id": i}
        for i in df_covid[df_covid.Country.isin(selected)].columns
        ]

    data = df_covid[df_covid.Country.isin(selected)].to_dict('records')

    page_size = len(df_covid[df_covid.Country.isin(selected)].index)

    return columns, data, page_size

@app.callback(
    Output('custom-graph','figure'),
    [Input('x-axis','value'),
     Input('y-axis','value'),
     Input('points-size','value')]
)
def update_custom(xaxis, yaxis, psize):
    if psize != 'Obesity':
        fig = px.scatter(kg_df, x=xaxis, y = yaxis, size = psize, hover_name='Country',
                     size_max=30, trendline = "ols", template="simple_white")
    else:
        fig = px.scatter(kg_df, x=xaxis, y = yaxis, size = psize, hover_name='Country',
                     trendline = "ols", template="simple_white")

    return fig


@app.callback(
    Output('food-pie','figure'),
    [Input('food-country-dd', 'value')]
)
def update_pie(value):

    fig = px.pie(values = kg_df[food_groups][kg_df.Country == value].values.tolist()[0], names = food_groups,
             title='Food intake (in kg) ' + value)
    fig.update_traces(textposition='inside', textinfo='percent+label')

    return fig

@app.callback(
    Output('veg-v-animal', 'figure'),
    [Input('food-country-dd', 'value')]
)
def update_bar(value):
    fig = px.bar(kg_df[['Country','Animal Products', 'Vegetal Products']][kg_df.Country == value],
        x = 'Country', y = ['Animal Products', 'Vegetal Products'],
        barmode = 'group',
        color_discrete_sequence = colors,
        title ='% of Animal and Vegetal products intake (kg) <br> - '+value)

    return fig

@app.callback(
    Output('map','figure'),
    [Input('food-cat', 'value')]
)
def update_map(value):
    c_scale={
        'Deaths': 'balance',
        'Confirmed': 'balance',
        'Active': 'balance',
        'Obesity': 'Reds',
        'Undernourished': 'Reds',
        'Animal Products': 'Armyrose',
        'Vegetal Products': 'PRGn'
    }
    fig = px.choropleth(data_frame = kg_df,
            locations= "iso_alpha",
            color= value,
            hover_name= "Country",
            color_continuous_scale= c_scale[value],
            projection = 'natural earth',
            title = value +" worlwide"
            )
    return fig

@app.callback(
    Output('obesity','figure'),
    Output('under','figure'),
    Output('AP','figure'),
    [Input('map', 'clickData')]
)
def update_mapgraph(click):
    # Eliminate error when map not clicked!
    if click == None:
        return {},{},{}

    # List of features to output
    feat_list = ['Obesity', 'Undernourished', 'Animal Products']

    # Get name of clicked country
    country = click['points'][0]['hovertext']

    # List of return values
    R = []

    # Loop over g_list to create 4 bar plots
    for feat in feat_list:
        if feat == 'Obesity' or feat == 'Undernourished':
            TITLE = feat +" rate - Percentage of total population"
        else:
            TITLE = "% of " + feat + " intake (kg)"
        df1 = kg_df.sort_values(feat, ascending = False)

        ind = df1.index[df1.Country == country].tolist()

        colors = ['#ff0000' if i in ind else '#00cc44'
                  for i in range(len(df1))]

        fig1 = px.bar(kg_df,
                        x = "Country", y =feat,
                        title = TITLE)
        fig1.update_traces(marker_color = colors)
        fig1.update_xaxes(categoryorder="total descending")

        R.append(fig1)

    return R[0],R[1],R[2]




@app.callback(
    Output('ftext','children'),
    [Input('map', 'clickData')]
)
def test(click):
    if click == None:
        return 'Select a country by clicking on map.'
    else:
        return click['points'][0]['hovertext'] + ' selected - info in red.'


if __name__ == '__main__':
    app.run_server()
