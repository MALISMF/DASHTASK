"""
Модуль определения пользовательского интерфейса (layout) для приложения Dash.
Содержит функции создания основных компонентов визуализации.
"""
from typing import Dict, List, Any

from dash import html, dcc
import pandas as pd

from data_processing import load_data


def create_layout() -> html.Div:
    """
    Создает основной макет приложения с графиками и элементами управления.
    
    Returns:
        html.Div: Контейнер с компонентами пользовательского интерфейса
    """
    df = load_data()
    
    available_years = sorted(df['year'].unique())
    numeric_columns = ['pop', 'gdpPercap', 'lifeExp']
    max_year = max(available_years)
    
    layout = html.Div([
        create_header(),
        create_year_selector(available_years),
        
        # Скрытый компонент для хранения выбранного года
        dcc.Store(id='selected-year-store', data=max_year),
        
        create_time_series_section(df, numeric_columns),
        create_bubble_chart_section(numeric_columns),
        create_population_charts_section()
    ])

    return layout


def create_header() -> html.H1:
    """
    Создает заголовок приложения.
    
    Returns:
        html.H1: Элемент заголовка
    """
    return html.H1(
        children='Сравнение стран по различным показателям',
        style={'textAlign': 'center'}
    )


def create_year_selector(available_years: List[int]) -> html.Div:
    """
    Создает селектор года с помощью слайдера.
    
    Args:
        available_years: Список доступных годов в данных
        
    Returns:
        html.Div: Контейнер с элементами выбора года
    """
    year_marks = {str(year): str(year) for year in available_years[::5]}
    
    return html.Div([
        html.H3('Выберите год для анализа:', style={'margin-bottom': '10px'}),
        dcc.Slider(
            id='year-slider',
            min=min(available_years),
            max=max(available_years),
            step=1,
            marks=year_marks,
            value=max(available_years),
        ),
    ], style={'padding': '20px'})


def create_time_series_section(
    df: pd.DataFrame,
    numeric_columns: List[str]
) -> html.Div:
    """
    Создает секцию с графиком временного ряда.
    
    Args:
        df: Датафрейм с данными
        numeric_columns: Список числовых колонок для выбора метрики
        
    Returns:
        html.Div: Контейнер с компонентами временного ряда
    """
    country_options = [
        {'label': country, 'value': country} for country in df.country.unique()
    ]
    
    metric_options = [
        {'label': col, 'value': col} for col in numeric_columns
    ]
    
    return html.Div([
        html.H2('Временной ряд по странам', style={'textAlign': 'center'}),
        dcc.Dropdown(
            options=country_options,
            value=['Canada'],
            multi=True,
            id='dropdown-selection'
        ),
        dcc.Dropdown(
            options=metric_options,
            value='pop',
            id='y-axis-selection'
        ),
        dcc.Graph(id='graph-content'),
    ])


def create_bubble_chart_section(numeric_columns: List[str]) -> html.Div:
    """
    Создает секцию с пузырьковой диаграммой.
    
    Args:
        numeric_columns: Список числовых колонок для выбора осей и размера
        
    Returns:
        html.Div: Контейнер с компонентами пузырьковой диаграммы
    """
    metric_options = [
        {'label': col, 'value': col} for col in numeric_columns
    ]
    
    return html.Div([
        html.H2('Пузырьковая диаграмма', style={'textAlign': 'center'}),
        html.H3('Ось X'),
        dcc.Dropdown(
            options=metric_options,
            value='gdpPercap',
            id='x-axis-bubble'
        ),
        html.H3('Ось Y'),
        dcc.Dropdown(
            options=metric_options,
            value='lifeExp',
            id='y-axis-bubble'
        ),
        html.H3('Размер'),
        dcc.Dropdown(
            options=metric_options,
            value='pop',
            id='size-bubble'
        ),
        dcc.Graph(id='bubble-chart'),
    ])


def create_population_charts_section() -> html.Div:
    """
    Создает секцию с графиками распределения населения.
    
    Returns:
        html.Div: Контейнер с графиками населения
    """
    return html.Div([
        create_top_population_chart(),
        create_continent_population_chart()
    ])


def create_top_population_chart() -> html.Div:
    """
    Создает секцию с графиком топ-15 стран по населению.
    
    Returns:
        html.Div: Контейнер с графиком
    """
    return html.Div([
        html.H2('Топ-15 стран по населению', style={'textAlign': 'center'}),
        dcc.Graph(id='top-population-chart'),
    ])


def create_continent_population_chart() -> html.Div:
    """
    Создает секцию с круговой диаграммой распределения населения по континентам.
    
    Returns:
        html.Div: Контейнер с круговой диаграммой
    """
    return html.Div([
        html.H2(
            'Распределение населения по континентам',
            style={'textAlign': 'center'}
        ),
        dcc.Graph(id='continent-population-pie')
    ])