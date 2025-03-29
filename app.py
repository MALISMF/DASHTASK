from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logging.debug("Начало инициализации приложения")

# Подключение внешних CSS стилей
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = Dash(__name__, external_stylesheets=external_stylesheets)

# Определение серверного объекта для Gunicorn
server = app.server

# Загрузка данных с обработкой исключений
try:
    logging.debug("Начинаем загрузку данных")
    df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv')
    logging.debug(f"Данные успешно загружены, размер: {df.shape}")
except Exception as e:
    logging.error(f"Ошибка загрузки данных: {e}")
    # Создаем пустой DataFrame с необходимыми колонками в случае ошибки
    df = pd.DataFrame({
        'country': ['Example'],
        'continent': ['Example'],
        'year': [2007],
        'pop': [1000000],
        'gdpPercap': [5000],
        'lifeExp': [70]
    })

# Доступные числовые меры
numeric_columns = ['pop', 'gdpPercap', 'lifeExp']

# Получение списка доступных годов
available_years = sorted(df['year'].unique())
year_marks = {str(year): str(year) for year in available_years}

# Определение layout ПЕРЕД запуском сервера
app.layout = html.Div([
    html.H1(children='Сравнение стран по различным показателям', style={'textAlign': 'center'}),
    
    html.Div([
        html.H3('Выберите год для анализа:', style={'margin-bottom': '10px'}),
        dcc.Slider(
            id='year-slider',
            min=min(available_years),
            max=max(available_years),
            step=None,
            marks=year_marks,
            value=max(available_years),
        ),
    ], style={'padding': '20px'}),
    
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
        dcc.Dropdown(
            options=[{'label': col, 'value': col} for col in numeric_columns],
            value='gdpPercap',
            id='x-axis-bubble'
        ),
        dcc.Dropdown(
            options=[{'label': col, 'value': col} for col in numeric_columns],
            value='lifeExp',
            id='y-axis-bubble'
        ),
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

@callback(
    Output('graph-content', 'figure'),
    Input('dropdown-selection', 'value'),
    Input('y-axis-selection', 'value')
)
def update_graph(selected_countries, y_axis):
    dff = df[df.country.isin(selected_countries)]
    return px.line(dff, x='year', y=y_axis, color='country', title=f'Динамика {y_axis}')

@callback(
    Output('bubble-chart', 'figure'),
    Input('x-axis-bubble', 'value'),
    Input('y-axis-bubble', 'value'),
    Input('size-bubble', 'value'),
    Input('year-slider', 'value')
)
def update_bubble_chart(x_axis, y_axis, size, selected_year):
    filtered_df = df[df['year'] == selected_year]
    return px.scatter(
        filtered_df, 
        x=x_axis, 
        y=y_axis, 
        size=size, 
        color='country',
        hover_name='country',
        title=f'Пузырьковая диаграмма ({selected_year}): {x_axis} vs {y_axis}, размер - {size}'
    )

@callback(
    Output('top-population-chart', 'figure'),
    Input('year-slider', 'value')
)
def update_top_population(selected_year):
    # Сначала фильтруем по году
    year_df = df[df['year'] == selected_year]
    
    # Затем сортируем по популяции и берем только первые 15 записей
    top_countries = year_df.sort_values('pop', ascending=False).head(15)
    
    return px.bar(
        top_countries, 
        x='country', 
        y='pop', 
        title=f'Топ-15 стран по населению ({selected_year})', 
        text_auto=True
    )

@callback(
    Output('continent-population-pie', 'figure'),
    Input('year-slider', 'value')
)
def update_continent_population(selected_year):
    filtered_df = df[df['year'] == selected_year]
    continent_data = filtered_df.groupby('continent', as_index=False)['pop'].sum()
    return px.pie(
        continent_data, 
        names='continent', 
        values='pop', 
        title=f'Распределение населения по континентам ({selected_year})'
    )

# Добавляем запуск сервера только для локальной разработки
if __name__ == '__main__':
    app.run_server(debug=False)  # Отключаем debug режим для продакшена