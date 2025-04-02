"""
Модуль с колбек-функциями для приложения Dash.
Содержит логику обновления графиков и визуализаций.
"""
from typing import Dict, List, Any, Union

import pandas as pd
import plotly.express as px
from dash import callback, Output, Input

from data_processing import fill_missing_data, load_data


def register_callbacks(app) -> None:
    """
    Регистрирует все колбек-функции приложения Dash.
    
    Args:
        app: Экземпляр Dash приложения
    """
    df = load_data()
    
    @callback(
        Output('selected-year-store', 'data'),
        Input('year-slider', 'value')
    )
    def update_selected_year(selected_year: int) -> int:
        """
        Сохраняет выбранный год в хранилище.
        
        Args:
            selected_year: Год, выбранный пользователем
            
        Returns:
            Выбранный год
        """
        return selected_year

    @callback(
        Output('graph-content', 'figure'),
        Input('dropdown-selection', 'value'),
        Input('y-axis-selection', 'value')
    )
    def update_graph(
        selected_countries: List[str],
        y_axis: str
    ) -> Dict[str, Any]:
        """
        Обновляет линейный график в зависимости от выбранных стран и оси Y.
        
        Args:
            selected_countries: Список выбранных стран
            y_axis: Показатель для оси Y
            
        Returns:
            Объект фигуры Plotly для линейного графика
        """
        filtered_df = df[df.country.isin(selected_countries)]
        
        # На временном ряду не нужно заполнять пропуски, так как показываем динамику за все годы
        return px.line(
            filtered_df,
            x='year',
            y=y_axis,
            color='country',
            title=f'Динамика {y_axis}'
        )

    @callback(
        Output('bubble-chart', 'figure'),
        Input('x-axis-bubble', 'value'),
        Input('y-axis-bubble', 'value'),
        Input('size-bubble', 'value'),
        Input('selected-year-store', 'data')
    )
    def update_bubble_chart(
        x_axis: str,
        y_axis: str,
        size: str,
        selected_year: int
    ) -> Dict[str, Any]:
        """
        Обновляет пузырьковую диаграмму на основе выбранных параметров.
        
        Args:
            x_axis: Показатель для оси X
            y_axis: Показатель для оси Y
            size: Показатель для размера пузырьков
            selected_year: Выбранный год
            
        Returns:
            Объект фигуры Plotly для пузырьковой диаграммы
        """
        all_countries = df['country'].unique()
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
        fig.update_layout(showlegend=False)
        
        add_imputed_data_hover_info(fig, filtered_df, x_axis, y_axis, size)
        
        return fig

    @callback(
        Output('top-population-chart', 'figure'),
        Input('year-slider', 'value')
    )
    def update_top_population(selected_year: int) -> Dict[str, Any]:
        """
        Обновляет столбчатую диаграмму топ-15 стран по населению.
        
        Args:
            selected_year: Выбранный год
            
        Returns:
            Объект фигуры Plotly для столбчатой диаграммы
        """
        all_countries = df['country'].unique()
        filled_df = fill_missing_data(df, selected_year, all_countries)
        
        # Сортируем по популяции и берем только первые 15 записей
        top_countries = filled_df.sort_values('pop', ascending=False).head(15)
        
        hover_texts = create_population_hover_texts(top_countries)
        
        fig = px.bar(
            top_countries, 
            x='country', 
            y='pop', 
            title=f'Топ-15 стран по населению ({selected_year})', 
            text_auto=True,
            hover_data=None  # Отключаем стандартный hover
        )
        
        # Устанавливаем кастомные hover-тексты
        fig.update_traces(
            hovertemplate='%{customdata}<extra></extra>',
            customdata=hover_texts
        )
        
        add_imputed_data_annotations(fig, top_countries)
        
        return fig

    @callback(
        Output('continent-population-pie', 'figure'),
        Input('year-slider', 'value')
    )
    def update_continent_population(selected_year: int) -> Dict[str, Any]:
        """
        Обновляет круговую диаграмму распределения населения по континентам.
        
        Args:
            selected_year: Выбранный год
            
        Returns:
            Объект фигуры Plotly для круговой диаграммы
        """
        all_countries = df['country'].unique()
        filled_df = fill_missing_data(df, selected_year, all_countries)
        
        continent_data = prepare_continent_data(filled_df)
        
        fig = px.pie(
            continent_data, 
            names='continent', 
            values='pop', 
            title=f'Распределение населения по континентам ({selected_year})'
        )
        
        custom_hovers = create_continent_hover_texts(continent_data)
        
        # Применяем кастомные hovers
        fig.update_traces(
            hovertemplate="%{customdata}<extra></extra>",
            customdata=custom_hovers
        )
        
        # Если есть импутированные данные, добавляем примечание
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


def add_imputed_data_hover_info(
    fig: Any,
    filtered_df: pd.DataFrame,
    x_axis: str,
    y_axis: str,
    size: str
) -> None:
    """
    Добавляет информацию о импутированных данных в подсказки при наведении.
    
    Args:
        fig: Объект фигуры Plotly
        filtered_df: Датафрейм с данными
        x_axis: Показатель для оси X
        y_axis: Показатель для оси Y
        size: Показатель для размера
    """
    if 'is_imputed' not in filtered_df.columns:
        return

    hovertemplate_base = (
        f'<b>%{{hovertext}}</b><br><br>'
        f'{x_axis}: %{{x}}<br>'
        f'{y_axis}: %{{y}}<br>'
        f'{size}: %{{marker.size}}<br>'
    )
    
    for i, point in enumerate(fig.data):
        country_name = point.name
        country_data = filtered_df[filtered_df['country'] == country_name]
        
        if not country_data.empty and country_data['is_imputed'].iloc[0]:
            # Для импутированных данных добавляем информацию об источнике
            original_year = country_data['original_year'].iloc[0]
            point.hovertemplate = f"{hovertemplate_base}<i>* Данные за {original_year}</i><extra></extra>"
        else:
            # Для оригинальных данных оставляем стандартный hover
            point.hovertemplate = f"{hovertemplate_base}<extra></extra>"


def create_population_hover_texts(top_countries: pd.DataFrame) -> List[str]:
    """
    Создает тексты подсказок для столбчатой диаграммы населения.
    
    Args:
        top_countries: Датафрейм с данными топ стран
        
    Returns:
        Список текстов подсказок
    """
    hover_texts = []
    for _, row in top_countries.iterrows():
        hover_text = (
            f"<b>{row['country']}</b><br><br>"
            f"Население: {int(row['pop']):,}"
        )
        
        if 'is_imputed' in top_countries.columns and row.get('is_imputed'):
            hover_text += f"<br><i>* Данные за {row.original_year}</i>"
        
        hover_texts.append(hover_text)
    
    return hover_texts


def add_imputed_data_annotations(fig: Any, top_countries: pd.DataFrame) -> None:
    """
    Добавляет аннотации для стран с импутированными данными.
    
    Args:
        fig: Объект фигуры Plotly
        top_countries: Датафрейм с данными топ стран
    """
    # Добавляем аннотации только для стран с импутированными данными
    for row in top_countries.itertuples():
        if hasattr(row, 'is_imputed') and row.is_imputed:
            fig.add_annotation(
                x=row.country,
                y=row.pop,
                text="*",
                showarrow=False,
                font=dict(size=20, color="red")
            )
    
    # Добавляем компактное примечание только если есть страны с импутированными данными
    has_imputed = ('is_imputed' in top_countries.columns and 
                  top_countries['is_imputed'].any())
    
    if has_imputed:
        fig.add_annotation(
            text="* - Данные за предыдущий доступный год",
            xref="paper", yref="paper",
            x=0.5, y=1,
            showarrow=False,
            font=dict(size=12),
            align="center"
        )


def prepare_continent_data(filled_df: pd.DataFrame) -> pd.DataFrame:
    """
    Подготавливает данные о континентах для круговой диаграммы.
    
    Args:
        filled_df: Датафрейм с данными
        
    Returns:
        Датафрейм с агрегированными данными по континентам
    """
    continent_data = filled_df.groupby('continent', as_index=False)['pop'].sum()
    
    # Считаем общее количество стран по континентам
    total_countries = (filled_df.groupby('continent')['country']
                      .nunique()
                      .reset_index(name='total_countries'))
    
    # Считаем количество импутированных стран по континентам
    if 'is_imputed' in filled_df.columns:
        imputed_countries = (
            filled_df[filled_df['is_imputed']]
            .groupby('continent')['country']
            .nunique()
            .reset_index(name='imputed_count')
        )
        # Объединяем с основными данными
        continent_data = pd.merge(continent_data, total_countries, on='continent', how='left')
        continent_data = pd.merge(continent_data, imputed_countries, on='continent', how='left')
        continent_data['imputed_count'] = continent_data['imputed_count'].fillna(0)
    else:
        continent_data = pd.merge(continent_data, total_countries, on='continent', how='left')
        continent_data['imputed_count'] = 0
    
    return continent_data


def create_continent_hover_texts(continent_data: pd.DataFrame) -> List[str]:
    """
    Создает тексты подсказок для круговой диаграммы континентов.
    
    Args:
        continent_data: Датафрейм с данными континентов
        
    Returns:
        Список текстов подсказок
    """
    custom_hovers = []

    for _, row in continent_data.iterrows():
        hover_text = (
            f"<b>{row['continent']}</b><br><br>"
            f"Население: {int(row['pop']):,}<br>"
            f"Данных за предыдущие года: {int(row['imputed_count'])} из "
            f"{int(row['total_countries'])}"
        )
        # Заменяем запятые на пробелы для лучшей читаемости чисел
        hover_text = hover_text.replace(',', ' ')
        custom_hovers.append(hover_text)
    
    return custom_hovers