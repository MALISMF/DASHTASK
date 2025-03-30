from dash import callback, Output, Input
import plotly.express as px
from data_processing import fill_missing_data, load_data
import pandas as pd

def register_callbacks(app):
    df = load_data()

    # Колбэк для хранения выбранного года
    @callback(
    Output('selected-year-store', 'data'),
    Input('year-slider', 'value')
)
    def update_selected_year(selected_year):
        return selected_year

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
        Input('selected-year-store', 'data')
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
        fig.update_layout(showlegend=False)
        
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
                    point.hovertemplate = hovertemplate_base + f'<i>* Данные за {original_year}</i><extra></extra>'
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
        
        # Создаем кастомные hover-тексты
        hover_texts = []
        for i, row in top_countries.iterrows():
            hover_text = f"<b>{row['country']}</b><br>" + \
                        f"Население: {int(row['pop']):,}"
            
            if hasattr(row, 'is_imputed') and row.is_imputed:
                hover_text += f"<br><i>* Данные за {row.original_year}</i>"
            
            hover_texts.append(hover_text)
        
        fig = px.bar(
            top_countries, 
            x='country', 
            y='pop', 
            title=f'Топ-15 стран по населению ({selected_year})', 
            text_auto=True,
            hover_data=None  # Отключаем стандартный hover
        )
        
        # Устанавливаем кастомные hover-тексты
        fig.update_traces(hovertemplate='%{customdata}<extra></extra>', customdata=hover_texts)
        
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
            # Считаем общее количество стран по континентам
            total_countries = filled_df.groupby('continent')['country'].nunique().reset_index(name='total_countries')
            
            # Считаем количество импутированных стран по континентам
            imputed_countries = filled_df[filled_df['is_imputed']].groupby('continent')['country'].nunique().reset_index(name='imputed_count')
            
            # Объединяем с основными данными
            continent_data = pd.merge(continent_data, total_countries, on='continent', how='left')
            continent_data = pd.merge(continent_data, imputed_countries, on='continent', how='left')
            continent_data['imputed_count'] = continent_data['imputed_count'].fillna(0)
            
            # Добавляем информацию в hover с отношением импутированных стран к общему количеству
            continent_data['hover_info'] = continent_data.apply(
                lambda row:  f"Данных за предыдущие года: {int(row['imputed_count'])} из {int(row['total_countries'])}",
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
