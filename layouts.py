from dash import html, dcc
import pandas as pd
from data_processing import load_data, fill_missing_data

def create_layout():
        
    # Загрузка данных 
    df = load_data()
    all_countries = df['country'].unique()

    # Доступные числовые меры
    numeric_columns = ['pop', 'gdpPercap', 'lifeExp']

    # Получение списка доступных годов
    available_years = sorted(df['year'].unique())
    year_marks = {str(year): str(year) for year in available_years[::5]}

    layout = html.Div([

        html.H1(children='Сравнение стран по различным показателям', style={'textAlign': 'center'}),
        
        html.Div([
            html.H3('Выберите год для анализа:', style={'margin-bottom': '10px'}),
            dcc.Slider(
                id='year-slider',
                min=min(available_years),
                max=max(available_years),
                step=1,
                marks=year_marks,
                value=max(available_years),
            ),
        ], style={'padding': '20px'}),

        html.Pre(filtered_df = fill_missing_data(df, 2007, all_countries).to_string()),

        #Скрытый компонент для хранения выбранного года на слайдере
        dcc.Store(id='selected-year-store', data=max(available_years)),
        
        html.Div([
            html.H2('Временной ряд по странам', style={'textAlign': 'center'}),
            dcc.Dropdown(
                options=[{'label': country, 'value': country} for country in df.country.unique()],
                value=['Canada'],
                multi=True,
                id='dropdown-selection'
            ),
            dcc.Dropdown(
                options=[{'label': col, 'value': col} for col in numeric_columns],
                value='pop',
                id='y-axis-selection'
            ),
            dcc.Graph(id='graph-content'),
        ]),
        
        html.Div([
            html.H2('Пузырьковая диаграмма', style={'textAlign': 'center'}),
            html.H3('Ось X'),
            dcc.Dropdown(
                options=[{'label': col, 'value': col} for col in numeric_columns],
                value='gdpPercap',
                id='x-axis-bubble'
            ),
            html.H3('Ось Y'),
            dcc.Dropdown(
                options=[{'label': col, 'value': col} for col in numeric_columns],
                value='lifeExp',
                id='y-axis-bubble'
            ),
            html.H3('Размер'),
            dcc.Dropdown(
                options=[{'label': col, 'value': col} for col in numeric_columns],
                value='pop',
                id='size-bubble'
            ),
            dcc.Graph(id='bubble-chart'),
        ]),
        
        html.Div([
            html.H2('Топ-15 стран по населению', style={'textAlign': 'center'}),
            dcc.Graph(id='top-population-chart'),
        ]),
        
        html.Div([
            html.H2('Распределение населения по континентам', style={'textAlign': 'center'}),
            dcc.Graph(id='continent-population-pie')
        ])
    ])

    return layout

