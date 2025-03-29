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

# Функция для заполнения недостающих данных за год последними доступными данными
def fill_missing_data(dataframe, selected_year, countries):
    """
    Для каждой страны из списка проверяет наличие данных за выбранный год.
    Если данных нет, берет данные за ближайший предыдущий год.
    """
    result_df = pd.DataFrame()
    
    for country in countries:
        # Фильтруем данные только для текущей страны
        country_data = dataframe[dataframe['country'] == country]
        
        # Проверяем, есть ли данные за выбранный год
        year_data = country_data[country_data['year'] == selected_year]
        
        if len(year_data) > 0:
            # Данные за выбранный год есть, используем их
            # Добавим колонку is_imputed со значением False, чтобы обозначить оригинальные данные
            year_data = year_data.copy()
            year_data['is_imputed'] = False
            year_data['original_year'] = selected_year
            result_df = pd.concat([result_df, year_data])
        else:
            # Данных за выбранный год нет, ищем ближайший предыдущий год
            available_years = sorted(country_data['year'].unique())
            previous_years = [year for year in available_years if year < selected_year]
            
            if previous_years:  # Если есть предыдущие годы
                latest_available_year = max(previous_years)
                latest_data = country_data[country_data['year'] == latest_available_year].copy()
                
                # Отмечаем, что данные восстановлены и содержат источник данных
                latest_data['is_imputed'] = True
                latest_data['original_year'] = latest_available_year
                latest_data['data_source'] = f'Данные за {latest_available_year}'
                
                # Меняем год на выбранный, чтобы он отображался корректно
                latest_data['year'] = selected_year
                
                result_df = pd.concat([result_df, latest_data])
                logging.debug(f"Для страны {country} на год {selected_year} используются данные за {latest_available_year}")
    
    return result_df

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
    
    # На временном ряду не нужно заполнять пропуски, так как показываем динамику за все годы
    return px.line(dff, x='year', y=y_axis, color='country', title=f'Динамика {y_axis}')

@callback(
    Output('bubble-chart', 'figure'),
    Input('x-axis-bubble', 'value'),
    Input('y-axis-bubble', 'value'),
    Input('size-bubble', 'value'),
    Input('year-slider', 'value')
)
def update_bubble_chart(x_axis, y_axis, size, selected_year):
    # Находим все страны в датасете
    all_countries = df['country'].unique()
    
    # Заполняем пропущенные данные
    filtered_df = fill_missing_data(df, selected_year, all_countries)
    
    fig = px.scatter(
        filtered_df, 
        x=x_axis, 
        y=y_axis, 
        size=size, 
        color='country',
        hover_name='country',
        title=f'Пузырьковая диаграмма ({selected_year}): {x_axis} vs {y_axis}, размер - {size}'
    )
    
    # Добавляем информацию об источнике данных в hover только для импутированных данных
    if 'is_imputed' in filtered_df.columns:
        # Создаем пользовательский hover для каждой точки
        hovertemplate_base = '<b>%{hovertext}</b><br><br>' + \
                             f'{x_axis}: %{{x}}<br>' + \
                             f'{y_axis}: %{{y}}<br>' + \
                             f'{size}: %{{marker.size}}<br>'
        
        for i, point in enumerate(fig.data):
            country_name = point.name
            country_data = filtered_df[filtered_df['country'] == country_name]
            
            if not country_data.empty and country_data['is_imputed'].iloc[0]:
                # Для импутированных данных добавляем информацию об источнике
                original_year = country_data['original_year'].iloc[0]
                point.hovertemplate = hovertemplate_base + f'Источник: данные за {original_year}<extra></extra>'
            else:
                # Для оригинальных данных оставляем стандартный hover
                point.hovertemplate = hovertemplate_base + '<extra></extra>'
    
    return fig

@callback(
    Output('top-population-chart', 'figure'),
    Input('year-slider', 'value')
)
def update_top_population(selected_year):
    # Находим все страны в датасете
    all_countries = df['country'].unique()
    
    # Заполняем пропущенные данные
    filled_df = fill_missing_data(df, selected_year, all_countries)
    
    # Затем сортируем по популяции и берем только первые 15 записей
    top_countries = filled_df.sort_values('pop', ascending=False).head(15)
    
    fig = px.bar(
        top_countries, 
        x='country', 
        y='pop', 
        title=f'Топ-15 стран по населению ({selected_year})', 
        text_auto=True
    )
    
    # Добавляем аннотации только для стран с импутированными данными
    for i, row in enumerate(top_countries.itertuples()):
        if hasattr(row, 'is_imputed') and row.is_imputed:
            fig.add_annotation(
                x=row.country,
                y=row.pop,
                text="*",
                showarrow=False,
                font=dict(size=20, color="red")
            )
    
    # Добавляем компактное примечание только если есть страны с импутированными данными
    if 'is_imputed' in top_countries.columns and top_countries['is_imputed'].any():
        # Получаем список стран с импутированными данными
        imputed_countries = top_countries[top_countries['is_imputed']].copy()
        
        # Создаем компактное примечание
        fig.add_annotation(
            text="* - Данные за предыдущий доступный год",
            xref="paper", yref="paper",
            x=0.5, y=1,
            showarrow=False,
            font=dict(size=12),
            align="center"
        )
    
    return fig

@callback(
    Output('continent-population-pie', 'figure'),
    Input('year-slider', 'value')
)
def update_continent_population(selected_year):
    # Находим все страны в датасете
    all_countries = df['country'].unique()
    
    # Заполняем пропущенные данные
    filled_df = fill_missing_data(df, selected_year, all_countries)
    
    continent_data = filled_df.groupby('continent', as_index=False)['pop'].sum()
    
    # Если есть импутированные данные, добавляем в hover
    if 'is_imputed' in filled_df.columns:
        # Считаем количество импутированных стран по континентам
        imputed_countries = filled_df[filled_df['is_imputed']].groupby('continent').size().reset_index(name='imputed_count')
        
        # Объединяем с основными данными
        continent_data = pd.merge(continent_data, imputed_countries, on='continent', how='left')
        continent_data['imputed_count'] = continent_data['imputed_count'].fillna(0)
        
        # Добавляем информацию в hover, только если есть импутированные страны
        continent_data['hover_info'] = continent_data.apply(
            lambda row: f"{row['continent']}<br>Население: {int(row['pop'])}" + 
                       (f"<br>Импутировано стран: {int(row['imputed_count'])}" if row['imputed_count'] > 0 else ""),
            axis=1
        )
    
    fig = px.pie(
        continent_data, 
        names='continent', 
        values='pop', 
        title=f'Распределение населения по континентам ({selected_year})',
        hover_data=['hover_info'] if 'hover_info' in continent_data.columns else None
    )
    
    # Если есть импутированные данные, добавляем компактное примечание
    has_imputed = 'is_imputed' in filled_df.columns and filled_df['is_imputed'].any()
    
    if has_imputed:
        fig.add_annotation(
            text="Примечание: Для некоторых стран использованы данные за ближайший предыдущий год",
            xref="paper", yref="paper",
            x=0.5, y=-0.1,
            showarrow=False,
            font=dict(size=12),
            align="center"
        )
    
    return fig

# Добавляем запуск сервера только для локальной разработки
if __name__ == '__main__':
    app.run_server(debug=False)  # Отключаем debug режим для продакшена